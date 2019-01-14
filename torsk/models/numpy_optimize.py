import logging
import numpy as np
import scipy as sp

logger = logging.getLogger(__name__)


def _extended_states(inputs, states):
    ones = np.ones([inputs.shape[0], 1], dtype=inputs.dtype)
    return np.concatenate([ones, inputs, states], axis=1).T


def _pseudo_inverse_svd(inputs, states, labels):
    train_length = inputs.shape[0]
    flat_inputs = inputs.reshape([train_length, -1])
    flat_labels = labels.reshape([train_length, -1])

    X = _extended_states(flat_inputs, states)

    U, s, Vh = sp.linalg.svd(X)
    L = flat_labels.T
    # condition = s[0] / s[-1]  # TODO: never used?

    scale = s[0]
    n = len(s[np.abs(s / scale) > 1e-4])  # Ensure condition number less than 10.000
    v = Vh[:n, :].T
    uh = U[:, :n].T

    wout = np.dot(np.dot(L, v) * (1 / s[:n]), uh)
    return wout


def _pseudo_inverse_lstsq(inputs, states, labels):
    X = _extended_states(inputs, states)

    wout, _, _, s = sp.linalg.lstsq(X.T, labels)
    condition = s[0] / s[-1]

    if(np.log2(np.abs(condition)) > 12):  # More than half of the bits in the data are lost
        logger.warning(
            f"Large condition number in pseudoinverse: {condition}"
            " losing more than half of the digits. Expect numerical blowup!")
        logger.warning(f"Largest and smallest singular values: {s[0]}  {s[-1]}")

    return wout.T


def pseudo_inverse(inputs, states, labels):
    return _pseudo_inverse_svd(inputs, states, labels)


def tikhonov(inputs, states, labels, beta):
    train_length = inputs.shape[0]
    flat_inputs = inputs.reshape([train_length, -1])
    flat_labels = labels.reshape([train_length, -1])

    X = _extended_states(flat_inputs, states)

    Id = np.eye(X.shape[0])
    A = np.dot(X, X.T) + beta + Id
    B = np.dot(X, flat_labels)

    # Solve linear system instead of calculating inverse
    wout = np.linalg.solve(A, B)
    return wout.T
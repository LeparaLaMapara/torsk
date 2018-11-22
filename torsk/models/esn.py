import pathlib

import numpy as np
import torch
import torch.nn as nn
from torch.nn.parameter import Parameter
from torch.nn.modules.rnn import RNNCellBase

from torsk import Params
from torsk.models.utils import dense_esn_reservoir, scale_weight
from torsk.models.sparse_esn import SparseESNCell


_module_dir = pathlib.Path(__file__).absolute().parent


def get_default_params():
    return Params(_module_dir / 'default_esn_params.json')


class ESNCell(RNNCellBase):
    """An Echo State Network (ESN) cell.

    Parameters
    ----------
    input_size : int
        Number of input features
    hidden_size : int
        Number of features in the hidden state
    spectral_radius : float
        Largest eigenvalue of the reservoir matrix
    in_weight_init : float
        Input matrix will be chosen from a random uniform like
        (-in_weight_init, in_weight_init)
    in_bias_init : float
        Input matrix will be chosen from a random uniform like
        (-in_bias_init, in_bias_init)


    Inputs
    ------
    input : torch.Tensor
        contains input features of shape (batch, input_size)
    state : torch.Tensor
        current hidden state of shape (batch, hidden_size)

    Outputs
    -------
    state' : torch.Tensor
        contains the next hidden state of shape (batch, hidden_size)
    """
    def __init__(
            self, input_size, hidden_size,
            spectral_radius, in_weight_init, in_bias_init, density):
        super(ESNCell, self).__init__()

        self.input_size = input_size
        self.hidden_size = hidden_size

        in_weight = torch.rand([hidden_size, input_size])
        in_weight = scale_weight(in_weight, in_weight_init)
        self.in_weight = Parameter(in_weight, requires_grad=False)

        res_weight = dense_esn_reservoir(
            dim=hidden_size, spectral_radius=spectral_radius,
            density=density, symmetric=False)
        self.res_weight = Parameter(
            torch.tensor(res_weight, dtype=torch.float32), requires_grad=False)

        in_bias = torch.rand([hidden_size])
        in_bias = scale_weight(in_bias, in_bias_init)
        self.in_bias = Parameter(torch.Tensor(in_bias), requires_grad=False)
        self.res_bias = self.register_parameter('res_bias', None)

    def forward(self, inputs, state):
        self.check_forward_input(inputs)
        self.check_forward_hidden(inputs, state)
        return self._backend.RNNTanhCell(
            inputs, state, self.in_weight, self.res_weight,
            self.in_bias, self.res_bias)


class ESN(nn.Module):
    """Complete ESN with output layer. Only supports batch=1 for now!!!

    Parameters
    ----------
    params : torsk.utils.Params
        The network hyper-parameters

    Inputs
    ------
    inputs : Tensor
        Inputs of shape (seq, batch, input_size)
    state : Tensor
        Initial state of the ESN with shape (batch, hidden_size)
    nr_predictions : int
        Number of steps to predict into the future

    Outputs
    -------
    outputs : Tensor
        Predicitons nr_predictions into the future
        shape (seq, batch, output_size)
    states' : Tensor
        Accumulated states of the ESN with shape (seq, batch, hidden_size)
    """
    def __init__(self, params):
        super(ESN, self).__init__()
        if params.input_size != params.output_size:
            raise ValueError(
                "Currently input and output dimensions must be the same.")

        if params.reservoir_representation == "dense":
            esn_cell = ESNCell
        elif params.reservoir_representation == "sparse":
            esn_cell = SparseESNCell

        self.esn_cell = esn_cell(
            input_size=params.input_size,
            hidden_size=params.hidden_size,
            spectral_radius=params.spectral_radius,
            in_weight_init=params.in_weight_init,
            in_bias_init=params.in_bias_init,
            density=params.density)

        self.out = nn.Linear(
            params.hidden_size + params.input_size + 1,
            params.output_size,
            bias=False)

        self.ones = torch.ones([1, 1])

    def forward(self, inputs, state, nr_predictions=0):
        if inputs.size(1) != 1:
            raise ValueError("Supports only batch size of one -.-")
        if nr_predictions == 0:
            return self._forward_states_only(inputs, state)
        else:
            return self._forward(inputs, state, nr_predictions)

    def _forward_states_only(self, inputs, state):
        states = []
        for inp in inputs:
            state = self.esn_cell(inp, state)
            states.append(state)
        return None, torch.stack(states, dim=0)

    def _forward(self, inputs, state, nr_predictions):
        outputs = []
        for inp in inputs:
            state = self.esn_cell(inp, state)
            ext_state = torch.cat([self.ones, inp, state], dim=1)
            output = self.out(ext_state)
            outputs.append(output)
        for ii in range(nr_predictions):
            inp = output
            state = self.esn_cell(inp, state)
            ext_state = torch.cat([self.ones, inp, state], dim=1)
            output = self.out(ext_state)
            outputs.append(output)
        return torch.stack(outputs, dim=0), None

    def train(self, inputs, states, labels, method='pinv', beta=None):
        """Train the output layer.

        Parameters
        ----------
        inputs : Tensor
            A batch of inputs with shape (batch, input_size)
        states : Tensor
            A batch of hidden states with shape (batch, hidden_size)
        labels : Tensor
            A batch of labels with shape (batch, output_size)
        """
        if len(inputs.size()) == 3:
            inputs = inputs.reshape([-1, inputs.size(2)])
            states = states.reshape([-1, states.size(2)])
            labels = labels.reshape([-1, labels.size(2)])

        if method == 'tikhonov':
            if beta is None:
                raise ValueError(
                    'For Tikhonov training the beta parameter cannot be None.')
            wout = tikhonov(inputs, states, labels, beta)

        elif method == 'pinv':
            if beta is not None:
                print('With pseudo inverse training the '
                      'beta parameter has no effect.')
            wout = pseudo_inverse(inputs, states, labels)

        else:
            raise ValueError(f'Unkown training method: {method}')

        assert wout.size() == self.out.weight.size()
        self.out.weight = Parameter(wout, requires_grad=False)


def _extended_states(inputs, states):
    ones = torch.ones([inputs.size(0), 1])
    return torch.cat([ones, inputs, states], dim=1).t()


def pseudo_inverse(inputs, states, labels):
    X = _extended_states(inputs, states)
    pinv = torch.pinverse(X)
    wout = torch.mm(labels.t(), pinv)
    return wout


def tikhonov(inputs, states, labels, beta):
    X = _extended_states(inputs, states)
    XT = X.t()
    XXT = torch.mm(X, XT)
    inv = torch.inverse(XXT + beta * torch.eye(XXT.size(0)))
    wout = torch.mm(labels.t(), torch.mm(XT, inv))
    return wout

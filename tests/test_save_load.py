import torsk
from torsk.numpy_accelerate import bh
from torsk.models.numpy_esn import NumpyESN


def test_numpy_save_load(tmpdir):

    params_string = """{
      "input_shape": [10, 10],
      "input_map_specs": [
        {"type":"pixels", "size":[10, 10], "input_scale":3}],
      "reservoir_representation": "dense",
      "spectral_radius" : 2.0,
      "density": 1e-1,

      "train_length": 800,
      "pred_length": 300,
      "transient_length": 100,
      "train_method": "pinv_svd",

      "dtype": "float64",
      "backend": "numpy",
      "debug": false,
      "imed_loss": true,
      "timing_depth": 1
    }
    """
    params_json = tmpdir.join("params.json")
    with open(params_json, "w") as dst:
        dst.write(params_string)

    params = torsk.Params(params_json)
    model = NumpyESN(params)
    inputs = bh.random.uniform(size=[2, 10, 10]).astype(bh.float64)
    state = bh.random.uniform(size=[100]).astype(bh.float64)

    _, out1 = model.forward(inputs, state)

    torsk.save_model(tmpdir, model)

    model = torsk.load_model(str(tmpdir))
    _, out2 = model.forward(inputs, state)

    assert bh.all(out1 == out2)


def test_numpy_sparse_save_load(tmpdir):
    params_string = """{
      "input_shape": [10, 10],
      "input_map_specs": [
        {"type":"conv", "size":[3, 3], "input_scale":3, "mode":"same",
            "kernel_type":"gauss"}],
      "reservoir_representation": "sparse",
      "spectral_radius" : 2.0,
      "density": 1e-1,

      "train_length": 800,
      "pred_length": 300,
      "transient_length": 100,
      "train_method": "pinv_svd",

      "dtype": "float64",
      "backend": "numpy",
      "debug": false,
      "imed_loss": true,
      "timing_depth": 1
    }
    """
    params_json = tmpdir.join("params.json")
    with open(params_json, "w") as dst:
        dst.write(params_string)

    params = torsk.Params(params_json)
    model = NumpyESN(params)
    inputs = bh.random.uniform(size=[2, 10, 10]).astype(bh.float64)
    state = bh.random.uniform(size=[100]).astype(bh.float64)

    _, out1 = model.forward(inputs, state)

    torsk.save_model(tmpdir, model)

    model = torsk.load_model(str(tmpdir))
    _, out2 = model.forward(inputs, state)

    assert bh.all(out1 == out2)


# def test_torch_save_load(tmpdir):
#     import torch
#     from torsk.models.torch_esn import TorchESN
#
#     params_string = """{
#       "input_shape": [10, 10],
#       "input_map_specs": [{"type":"pixels", "size":[10, 10], "input_scale":3}],
#
#       "reservoir_representation": "dense",
#       "spectral_radius" : 2.0,
#       "density": 1e-1,
#
#       "train_length": 800,
#       "pred_length": 300,
#       "transient_length": 100,
#       "train_method": "pinv_svd",
#
#       "dtype": "float32",
#       "backend": "torch",
#       "debug": false,
#       "imed_loss": true
#     }
#     """
#     params_json = tmpdir.join("params.json")
#     with open(params_json, "w") as dst:
#         dst.write(params_string)
#
#     params = torsk.Params(params_json)
#     model = TorchESN(params)
#     inputs = torch.rand(1, 10, 10)
#     state = torch.rand(1, 100)
#
#     _, out1 = model(inputs, state)
#
#     torsk.save_model(tmpdir, model)
#
#     model = torsk.load_model(str(tmpdir))
#     _, out2 = model(inputs, state)
#
#     assert np.all(out1.numpy() == out2.numpy())

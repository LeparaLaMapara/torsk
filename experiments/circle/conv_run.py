# coding: future_fstrings
import sys
import logging
import numpy as np
import matplotlib.pyplot as plt


import torsk
from torsk.data.utils import gauss2d_sequence, mackey_sequence, normalize, mackey_anomaly_sequence
from torsk.imed import imed_metric
from torsk.visualize import animate_double_imshow, write_double_video

np.random.seed(11)

# # Good!
#    {"type": "pixels", "size": [30, 30], "input_scale": 6.},
#     {"type": "conv", "size": [2, 2], "kernel_type":"gauss", "input_scale": 0.1},
#     {"type": "conv", "size": [5, 5], "kernel_type":"gauss", "input_scale": 1.},
#     {"type": "conv", "size": [10,10], "kernel_type":"gauss", "input_scale": 1.},
#     {"type": "conv", "size": [15, 15], "kernel_type":"gauss", "input_scale": 1.},
#     {"type": "conv", "size": [20, 20], "kernel_type":"gauss", "input_scale": 1.},
#     {"type": "conv", "size": [25, 25], "kernel_type":"gauss", "input_scale": 1.},        


params = torsk.Params()
params.input_map_specs = [
    {"type": "pixels", "size": [30, 30], "input_scale": 3.},
    {"type": "conv", "mode": "same", "size": [5, 5], "kernel_type":"gauss", "input_scale": 2.},
    {"type": "conv", "mode": "same", "size": [10,10], "kernel_type":"gauss", "input_scale": 1.5},
    {"type": "conv", "mode": "same", "size": [15, 15], "kernel_type":"gauss", "input_scale": 1.},
    {"type": "conv", "mode": "same", "size": [ 5, 5], "kernel_type":"random", "input_scale": 1.},
    {"type": "conv", "mode": "same", "size": [10, 10], "kernel_type":"random", "input_scale": 1.},
    {"type": "conv", "mode": "same", "size": [20, 20], "kernel_type":"random", "input_scale": 1.},
    {"type": "dct", "size": [15, 15], "input_scale": 1.},
#    {"type": "compose", "operations": [
        {"type": "gradient", "input_scale": 1.},
#        {"type": "pixels",   "size": [40,20]}
#        ]
#    },
    {"type": "gradient", "input_scale": 1.}
]

params.spectral_radius = 2.0
params.density = 0.05
params.input_shape = [30, 30]
params.train_length = 2000
params.pred_length = 200
params.transient_length = 200
params.dtype = "float64"
params.reservoir_representation = "sparse"
params.backend = "numpy"
params.train_method = "pinv_lstsq"
params.tikhonov_beta = 0.01
params.imed_loss = True
params.debug = False

params.anomaly_start = 2300
params.anomaly_step = 300

params.update(sys.argv[1:])

logger = logging.getLogger(__file__)
level = "DEBUG" if params.debug else "INFO"
logging.basicConfig(level=level)
logging.getLogger("matplotlib").setLevel("INFO")

if params.backend == "numpy":
    logger.info("Running with NUMPY backend")
    from torsk.data.numpy_dataset import NumpyImageDataset as ImageDataset
    from torsk.models.numpy_esn import NumpyESN as ESN
else:
    logger.info("Running with TORCH backend")
    from torsk.data.torch_dataset import TorchImageDataset as ImageDataset
    from torsk.models.torch_esn import TorchESN as ESN

logger.info(params)

logger.info("Creating circle dataset ...")
t = np.arange(0, 200*np.pi, 0.1)[:3000]
#x, y = np.sin(t), np.cos(0.3 * t)
x, y = np.sin(0.3 * t), np.cos(t)
# x = normalize(mackey_sequence(N=t.shape[0])) * 2 - 1
mackey, _ = mackey_anomaly_sequence(
    N=t.shape[0],
    anomaly_start=params.anomaly_start,
    anomaly_step=params.anomaly_step)
x = normalize(mackey) * 2 - 1

center = np.array([y, x]).T
images = gauss2d_sequence(center, sigma=0.5, size=params.input_shape)
dataset = ImageDataset(images, params, scale_images=True)

logger.info("Building model ...")
model = ESN(params)

logger.info("Training + predicting ...")
model, outputs, pred_labels = torsk.train_predict_esn(
    model, dataset, "/tmp/mackey_conv_small",
    steps=1, step_length=1, step_start=0)

write_double_video("circle-conv.mp4", pred_labels,outputs)

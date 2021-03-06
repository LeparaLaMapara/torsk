from setuptools import setup, find_packages

setup(
    name='torsk',
    description='Anomaly Detection in Chaotic Time Series based on an ESN',
    author='Niklas Heim',
    author_email='heim.niklas@gmail.com',
    packages=find_packages(),
    version=0.1,
    install_requires=[
        "bohrium",
        "click",
        "future-fstrings",
        "joblib",
        "marshmallow>=3.0.0b12",
        "matplotlib",
        "netCDF4",
        "numpy",
        "tqdm",
        "seaborn",
        "scikit-image",
        "scikit-optimize",
        "imageio",
        "imageio-ffmpeg",
        "convlstm @ git+https://github.com/nmheim/ConvLSTM_pytorch@master"
    ],
    entry_points='''
        [console_scripts]
        torsk=torsk.scripts.cli:cli
    ''',
    extras_require={
        "test": [
            "pytest",
            "pytest-cov",
            "pytest-flake8"
        ],
        "recommended": [
            "torch",
            "torchvision"
        ]
    }
)

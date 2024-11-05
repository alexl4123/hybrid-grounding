from setuptools import Extension, setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize("cython_nagg/cython/cython_helpers.pyx")
)



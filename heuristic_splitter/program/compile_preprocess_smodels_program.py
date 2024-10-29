from setuptools import Extension, setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize("preprocess_smodels_program.pyx")
)


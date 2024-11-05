from setuptools import Extension, setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize("cython_nagg/cython/generate_saturation_justification_helper_variables_part.pyx")
)



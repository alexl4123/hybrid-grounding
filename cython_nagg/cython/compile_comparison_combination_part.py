from setuptools import Extension, setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize("generate_comparison_combination_part.pyx")
)


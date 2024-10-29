from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize("heuristic_splitter/get_facts_cython.pyx")
)

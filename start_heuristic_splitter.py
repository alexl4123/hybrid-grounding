from heuristic_splitter import main
import sys

from memory_profiler import profile

#@profile
def start_func():
    main()

if __name__ == "__main__":
    start_func()


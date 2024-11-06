
# Header File
from libc.stdio cimport FILE

cdef (char**,int) convert_to_c_string_list(list string_list)

cdef void free_c_string_list(char** c_string_array, Py_ssize_t n)

cdef void print_string(char*** domain_array, int* index_array, int length_of_arrays, char* template_string, char* error_string, FILE* file_stream ) noexcept nogil



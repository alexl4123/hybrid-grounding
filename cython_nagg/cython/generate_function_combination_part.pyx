
import sys

from heuristic_splitter.domain_inferer import DomainInferer

from libc.stdio cimport printf, FILE, fdopen, fprintf, stdout, fflush, fclose
from libc.stdlib cimport malloc, free
from libc.string cimport strdup, strcpy
from cython.operator import dereference

from cython_nagg.cython.cython_helpers cimport convert_to_c_string_list, free_c_string_list, print_string


cdef void generate_function_combinations(
    char*** domain_array, int* length_array,
    int length_of_arrays, char* template_string, char* error_string,
    FILE* file_stream) noexcept nogil:

    cdef int* index_array = <int*>malloc(length_of_arrays * sizeof(int))
    cdef bint continue_loop
    cdef bint overflow
    cdef int index

    for index in range(length_of_arrays):
        index_array[index] = 0

    continue_loop = True
    while continue_loop is True:

        # Print important stuff
        print_string(domain_array, index_array, length_of_arrays, template_string, error_string, file_stream)

        overflow = True
        for index in range(length_of_arrays):
            if overflow is True:
                index_array[index] += 1
                if index_array[index] >= length_array[index]:
                    # If the first index overflows, then go to the second
                    overflow = True
                    index_array[index] = 0
                else:
                    overflow = False

        if overflow is True:
            # Only happens at the end, when all have been processed.
            continue_loop = False

def generate_function_combinations_caller(string_template, variable_domain_lists, output_fd = sys.stdout.fileno()):

    cdef int* length_array
    cdef char*** domain_array
    cdef int number_arguments
    cdef int index


    # Open the file descriptor as a FILE* stream
    cdef FILE* file_stream = fdopen(output_fd, "w")
    if file_stream is NULL:
        raise ValueError("Could not open file descriptor")

    domain_array = <char***>malloc(len(variable_domain_lists) * sizeof(char**))
    length_array = <int*>malloc(len(variable_domain_lists) * sizeof(int)) 
    number_arguments = len(variable_domain_lists)

    cdef char* string_template_char = <char*>malloc(sizeof(int) * len(string_template))
    error_string = "[ERROR] - Not arity implemented"
    cdef char* error_string_char = <char*>malloc(sizeof(int) * len(error_string))
    cdef bint exception_occurred = False
    exception = None

    if domain_array and length_array and string_template_char and error_string_char:
        index = 0
        for variable_domain_list in variable_domain_lists:
            
            try:
                c_array, length = convert_to_c_string_list(variable_domain_list)
            except Exception as ex:
                exception_occurred = True
                if exception is None:
                    exception = ex
                break
            
            domain_array[index] = c_array
            length_array[index] = length

            index += 1

        if exception_occurred is False:

            strcpy(string_template_char, string_template.encode('ascii'))
            strcpy(error_string_char, error_string.encode('ascii'))

            generate_function_combinations(domain_array, length_array, number_arguments,
                string_template_char, error_string_char, file_stream)
    else:
        exception_occurred = True
        exception = Exception(f"Memory allocation failed for string template {string_template}")

    # ------------ FREE MEMORY -----------
    index = 0
    for index in range(number_arguments):
        try:
            free_c_string_list(domain_array[index], length_array[index])
        except Exception as ex:
            exception_occurred = True
            if exception is None:
                exception = ex

    fflush(file_stream)
    fclose(file_stream)

    try:
        free(domain_array)
    except Exception as ex:
        exception_occurred = True
        if exception is None:
            exception = ex
    try:
        free(length_array)
    except Exception as ex:
        exception_occurred = True
        if exception is None:
            exception = ex
    try:
        free(string_template_char)
    except Exception as ex:
        exception_occurred = True
        if exception is None:
            exception = ex
    try:
        free(error_string_char)
    except Exception as ex:
        exception_occurred = True
        if exception is None:
            exception = ex

    if exception_occurred is True:
        raise exception

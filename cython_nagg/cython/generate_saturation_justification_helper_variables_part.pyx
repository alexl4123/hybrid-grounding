import sys

from heuristic_splitter.domain_inferer import DomainInferer

from libc.stdio cimport printf, FILE, fdopen, fprintf, stdout, fflush, fclose
from libc.stdlib cimport malloc, free
from libc.string cimport strdup, strcpy
from cython.operator import dereference

from cython_nagg.cython.cython_helpers cimport convert_to_c_string_list, free_c_string_list, print_string


cdef void print_string_starting_from_index_1(
    char*** domain_array, int* index_array,
    int length_of_arrays, char* template_string, char* error_string, FILE* file_stream) noexcept nogil:

    if length_of_arrays == 2: 
        fprintf(file_stream, template_string,domain_array[1][index_array[1]] )
    elif length_of_arrays == 3:
        fprintf(file_stream, template_string, domain_array[1][index_array[1]], domain_array[2][index_array[2]])
    elif length_of_arrays == 4:
        fprintf(file_stream, template_string, domain_array[1][index_array[1]], domain_array[2][index_array[2]], domain_array[3][index_array[3]])
    elif length_of_arrays == 5:
        fprintf(file_stream, template_string, domain_array[1][index_array[1]], domain_array[2][index_array[2]], domain_array[3][index_array[3]], domain_array[4][index_array[4]])
    elif length_of_arrays == 6:
        fprintf(file_stream, template_string, domain_array[1][index_array[1]], domain_array[2][index_array[2]], domain_array[3][index_array[3]], domain_array[4][index_array[4]], domain_array[5][index_array[5]])
    else:
        fprintf(file_stream, "%s", error_string)
        fprintf(file_stream, "\n<<<%d>>>\n", length_of_arrays)

cdef void generate_saturation_justification_helper_combinations(
    char*** domain_array, int* length_array, int length_of_arrays,
    char* template_string_0, char* template_string_1, char* template_string_2,
    char* error_string, FILE* file_stream) noexcept nogil:

    cdef int* index_array = <int*>malloc(length_of_arrays * sizeof(int))
    cdef bint continue_loop
    cdef bint overflow
    cdef int index
    cdef bint overflow_happened = False

    for index in range(length_of_arrays):
        index_array[index] = 0

    continue_loop = True
    cdef bint first_overflow = True


    fflush(stdout)
    fprintf(file_stream, "%s", template_string_0)

    while continue_loop is True:

        # Print important stuff
        print_string(domain_array, index_array, length_of_arrays, template_string_1, error_string, file_stream)

        overflow = True
        for index in range(length_of_arrays):
            if overflow is True:

                if index_array[index] + 1 >= length_array[index]:
                    # If the first index overflows, then go to the second

                    if first_overflow is True:
                        print_string_starting_from_index_1(domain_array, index_array,
                            length_of_arrays, template_string_2, error_string, file_stream)

                        first_overflow = False
                        overflow_happened = True


                    overflow = True
                    index_array[index] = 0
                else:
                    if first_overflow is True:
                        fprintf(file_stream, "%s",";")

                    index_array[index] += 1
                    overflow = False
                    first_overflow = True

        if overflow is True:
            # Only happens at the end, when all have been processed.
            continue_loop = False
        elif overflow_happened is True:
            # When an overflow happens, but not at the end.
            fprintf(file_stream, "%s", template_string_0)

        overflow_happened = False
    

    fflush(stdout)

def generate_saturation_justification_helper_variables_caller(string_template_0, string_template_1,
        string_template_2, variable_domain_lists, output_fd = sys.stdout.fileno()):

    # Open the file descriptor as a FILE* stream
    cdef FILE* file_stream = fdopen(output_fd, "w")
    if file_stream is NULL:
        raise ValueError("Could not open file descriptor")


    cdef int* length_array
    cdef char*** domain_array
    cdef int number_arguments
    cdef int index

    domain_array = <char***>malloc(len(variable_domain_lists) * sizeof(char**))
    length_array = <int*>malloc(len(variable_domain_lists) * sizeof(int)) 
    number_arguments = len(variable_domain_lists)

    cdef char* string_template_0_char = <char*>malloc(sizeof(int) * len(string_template_0))
    cdef char* string_template_1_char = <char*>malloc(sizeof(int) * len(string_template_1))
    cdef char* string_template_2_char = <char*>malloc(sizeof(int) * len(string_template_2))

    error_string = "[ERROR] - Not arity implemented"
    cdef char* error_string_char = <char*>malloc(sizeof(int) * len(error_string))
    cdef bint exception_occurred = False
    exception = None

    if domain_array and length_array and string_template_0_char and string_template_1_char and string_template_2_char and error_string_char:
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

            strcpy(string_template_0_char, string_template_0.encode('ascii'))
            strcpy(string_template_1_char, string_template_1.encode('ascii'))
            strcpy(string_template_2_char, string_template_2.encode('ascii'))

            strcpy(error_string_char, error_string.encode('ascii'))

            generate_saturation_justification_helper_combinations(domain_array, length_array, number_arguments,
                string_template_0_char, string_template_1_char, string_template_2_char, error_string_char, file_stream)

    else:
        exception_occurred = True
        exception = Exception(f"Memory allocation failed for string template {string_template_0}{string_template_1}{string_template_2}")

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
        free(string_template_0_char)
    except Exception as ex:
        exception_occurred = True
        if exception is None:
            exception = ex
    try:
        free(string_template_1_char)
    except Exception as ex:
        exception_occurred = True
        if exception is None:
            exception = ex
    try:
        free(string_template_2_char)
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

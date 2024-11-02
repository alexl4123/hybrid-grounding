

from heuristic_splitter.rule import Rule
from heuristic_splitter.domain_inferer import DomainInferer

from libc.stdio cimport printf
from libc.stdlib cimport malloc, free
from libc.string cimport strdup, strcpy
from cython.operator import dereference


cdef (char**,int) convert_to_c_string_list(list string_list):
    cdef int length = len(string_list)
    cdef char** c_string_array = <char**>malloc(length * sizeof(char*))
    cdef char* tmp_string

    if c_string_array == NULL:
        raise MemoryError("Unable to allocate memory for char**")

    cdef Py_ssize_t index
    for index in range(length):
        #c_string_array[index] = strdup(string_list[index].encode('ascii'))  # Convert each string to char*

        tmp_string = <char*>malloc(len(string_list[index]) * sizeof(int))
        strcpy(tmp_string, string_list[index].encode('ascii'))
        c_string_array[index] = tmp_string

        if c_string_array[index] == NULL:
            # Clean up already allocated strings if strdup fails
            for j in range(index):
                free(c_string_array[j])
            free(c_string_array)
            raise MemoryError("Unable to allocate memory for string")

    return c_string_array, length

cdef void free_c_string_list(char** c_string_array, Py_ssize_t n):
    for i in range(n):
        free(c_string_array[i])  # Free each string
    free(c_string_array)         # Free the array of pointers


cdef void generate_function_combinations(char*** domain_array, int* length_array, int length_of_arrays, char* template_string, char* error_string) noexcept nogil:

    cdef int* index_array = <int*>malloc(length_of_arrays * sizeof(int))
    cdef bint continue_loop
    cdef bint overflow
    cdef int index

    for index in range(length_of_arrays):
        index_array[index] = 0

    continue_loop = True
    while continue_loop is True:

        # Print important stuff
        if length_of_arrays == 1: 
            printf(template_string,domain_array[0][index_array[0]] )
        elif length_of_arrays == 2:
            printf(template_string, domain_array[0][index_array[0]], domain_array[1][index_array[1]])
        elif length_of_arrays == 3:
            printf(template_string, domain_array[0][index_array[0]], domain_array[1][index_array[1]], domain_array[2][index_array[2]])
        elif length_of_arrays == 4:
            printf(template_string, domain_array[0][index_array[0]], domain_array[1][index_array[1]], domain_array[2][index_array[2]], domain_array[3][index_array[3]])
        elif length_of_arrays == 5:
            printf(template_string, domain_array[0][index_array[0]], domain_array[1][index_array[1]], domain_array[2][index_array[2]], domain_array[3][index_array[3]], domain_array[4][index_array[4]])
        else:
            printf("%s", error_string)
            printf("\n<<<%d>>>\n", length_of_arrays)

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


def generate_satisfiability_part_function(function, rule, domain, string_template, variable_domain_lists):

    # Get relevant domain stuff (and convert to DSs)
    # ---> Need relevant domain -> variable domains -> convert to C data-structure -> 
    # Run loop -> How to:

    cdef int* length_array
    cdef char*** domain_array
    cdef int number_arguments
    cdef int index
    cdef char* string_template_char
    cdef char* error_string_char

    print(string_template)
    print("+++")
    print(variable_domain_lists)
    print("+++")

    domain_array = <char***>malloc(len(variable_domain_lists) * sizeof(char**))
    length_array = <int*>malloc(len(variable_domain_lists) * sizeof(int)) 
    number_arguments = len(variable_domain_lists)

    index = 0
    for variable_domain_list in variable_domain_lists:

        c_array, length = convert_to_c_string_list(variable_domain_list)
        
        domain_array[index] = c_array
        length_array[index] = length

        index += 1


    string_template_char = <char*>malloc(sizeof(int) * len(string_template))
    strcpy(string_template_char, string_template.encode('ascii'))

    error_string = "[ERROR] - Not arity implemented"
    error_string_char = <char*>malloc(sizeof(int) * len(error_string))
    strcpy(error_string_char, error_string.encode('ascii'))
    generate_function_combinations(domain_array, length_array, number_arguments, string_template_char, error_string_char)

    index = 0
    for index in range(number_arguments):
        free_c_string_list(domain_array[index], length_array[index])



        


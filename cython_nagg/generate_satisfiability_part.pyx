

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

cdef void print_string(
    char*** domain_array, int* index_array,
    int length_of_arrays, char* template_string, char* error_string ) noexcept nogil:

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



cdef void generate_function_combinations(
    char*** domain_array, int* length_array,
    int length_of_arrays, char* template_string, char* error_string) noexcept nogil:

    cdef int* index_array = <int*>malloc(length_of_arrays * sizeof(int))
    cdef bint continue_loop
    cdef bint overflow
    cdef int index

    for index in range(length_of_arrays):
        index_array[index] = 0

    continue_loop = True
    while continue_loop is True:

        # Print important stuff
        print_string(domain_array, index_array, length_of_arrays, template_string, error_string)

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

def generate_satisfiability_part_function(string_template, variable_domain_lists):

    cdef int* length_array
    cdef char*** domain_array
    cdef int number_arguments
    cdef int index
    cdef char* string_template_char
    cdef char* error_string_char

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

    free(length_array)



cdef bint char_is_int(char c) noexcept nogil:
    if c >= 48 and c <= 57:
        return True
    else:
        return False

cdef bint char_is_atom(char c) noexcept nogil:
    if char_is_int(c) is True:
        return True
    elif c >= 65 and c <= 90:
        # Is upper case letter
        return True
    elif c >= 97 and c <= 122:
        # Is lower case letter
        return True
    elif c == 95:
        # Is _ character
        return True
    else:
        return False

cdef int simple_comparison_holds_not_equal(char* str1, char* str2, int str1_len, int str2_len) noexcept nogil:
    # Return values: 1 -> holds, -1 -> does not hold, 0 -> undefined (has to be grounded)

    cdef int min_length
    cdef int index

    if str1_len != str2_len:
        return 1

    # min_length = str1_len = str2_len
    min_length = str1_len

    for index in range(min_length):
        if str1[index] != str2[index]:
            return 1

    return -1


cdef int simple_comparison_holds_equal(char* str1, char* str2, int str1_len, int str2_len) noexcept nogil:
    # Return values: 1 -> holds, -1 -> does not hold, 0 -> undefined (has to be grounded)

    cdef int min_length
    cdef int index

    if str1_len != str2_len:
        return -1

    # min_length = str1_len = str2_len
    min_length = str1_len

    for index in range(min_length):
        if str1[index] != str2[index]:
            return -1


    return 1



cdef int simple_comparison_holds_smaller(char* str1, char* str2, int str1_len, int str2_len) noexcept nogil:
    # Return values: 1 -> holds, -1 -> does not hold, 0 -> undefined (has to be grounded)

    cdef int min_length
    cdef int index
    cdef int tmp_index

    cdef bint str1_is_int = True
    cdef bint str2_is_int = True
    cdef bint str1_is_atom = True
    cdef bint str2_is_atom = True
    cdef bint temporary_evaluation = True

    if str1_len < str2_len:
        min_length = str1_len
    else:
        min_length = str2_len

    for index in range(min_length):
        if str1[index] >= str2[index]:
            temporary_evaluation = False
        
        if char_is_int(str1[index]) is False:
            str1_is_int = False
        if char_is_atom(str1[index]) is False:
            str1_is_atom = False
        if char_is_int(str2[index]) is False:
            str2_is_int = False
        if char_is_atom(str2[index]) is False:
            str2_is_atom = False

    if str1_len < str2_len:
        for index in range(str2_len - str1_len):
            tmp_index = index + str1_len

            if char_is_int(str2[tmp_index]) is False:
                str2_is_int = False
            if char_is_atom(str2[tmp_index]) is False:
                str2_is_atom = False
    if str2_len < str1_len:
        for index in range(str1_len - str2_len):
            tmp_index = index + str2_len
            
            if char_is_int(str1[tmp_index]) is False:
                str1_is_int = False
            if char_is_atom(str1[tmp_index]) is False:
                str1_is_atom = False
 
    if str1_is_int is True and str2_is_int is True:
        if temporary_evaluation is True:
            return 1
        else:
            return -1
    elif str1_is_atom is True and str2_is_atom is True:
        if temporary_evaluation is True:
            return 1
        else:
            return -1
    elif str1_is_int is True and str2_is_int is False:
        # Integer values are always smaller
        return 1
    elif str1_is_int is False and str2_is_int is True:
        return -1
    elif str1_is_atom is True and str2_is_atom is False:
        return 1
    elif str1_is_atom is False and str2_is_atom is True:
        return -1
    else:
        return 0


cdef int simple_comparison_holds_smaller_or_equal(char* str1, char* str2, int str1_len, int str2_len) noexcept nogil:
    # Return values: 1 -> holds, -1 -> does not hold, 0 -> undefined (has to be grounded)

    cdef int smaller_than    
    cdef int equal

    smaller_than = simple_comparison_holds_smaller(str1, str2, str1_len, str2_len)

    if smaller_than == 0:
        return 0
    elif smaller_than == 1:
        return 1

    equal = simple_comparison_holds_equal(str1, str2, str1_len, str2_len)

    if equal == 1:
        return 1
    else:
        return -1




cdef int simple_comparison_holds_greater(char* str1, char* str2, int str1_len, int str2_len) noexcept nogil:
    # Return values: 1 -> holds, -1 -> does not hold, 0 -> undefined (has to be grounded)

    cdef int smaller_than    
    cdef int equal

    smaller_than = simple_comparison_holds_smaller(str1, str2, str1_len, str2_len)

    if smaller_than == 0:
        return 0
    elif smaller_than == 1:
        return -1

    equal = simple_comparison_holds_equal(str1, str2, str1_len, str2_len)

    if equal == 1:
        return -1
    else:
        return 1


cdef int simple_comparison_holds_greater_or_equal(char* str1, char* str2, int str1_len, int str2_len) noexcept nogil:
    # Return values: 1 -> holds, -1 -> does not hold, 0 -> undefined (has to be grounded)

    cdef int smaller_than    
    cdef int equal

    smaller_than = simple_comparison_holds_smaller(str1, str2, str1_len, str2_len)

    if smaller_than == 0:
        return 0
    elif smaller_than == 1:
        return -1
    else:
        return 1

cdef void generate_comparison_combinations(
    char*** domain_array, int* length_array, int length_of_arrays,
    char* template_string, char* template_string_reduced,
    char* error_string, int** string_length_array,
    int (*comparison_function)(char*, char*, int, int) noexcept nogil, bint is_simple_comparison, int signum
    ) noexcept nogil:

    cdef int* index_array = <int*>malloc(length_of_arrays * sizeof(int))
    cdef bint continue_loop
    cdef bint overflow
    cdef int index
    cdef int value

    for index in range(length_of_arrays):
        index_array[index] = 0

    continue_loop = True
    while continue_loop is True:

        # Print important stuff
        if is_simple_comparison is True and length_of_arrays == 2:

            value = comparison_function(
                domain_array[0][index_array[0]], domain_array[1][index_array[1]],
                string_length_array[0][index_array[0]], string_length_array[1][index_array[1]])

            if value == 0:
                # Ground fully
                print_string(domain_array, index_array, length_of_arrays, template_string, error_string)

            elif value == 1 and signum > 0:
                # ..., not 1 != 1 -> Remove last part
                print_string(domain_array, index_array, length_of_arrays, template_string_reduced, error_string)

            elif value == 1 and signum < 0:
                # ..., not 1 = 1 -> Do not print rule!
                pass

            elif value == -1 and signum > 0:
                # ..., 1 != 1 -> Do not print rule!
                pass

            elif value == -1 and signum < 0:
                # ..., not 1 != 1 -> Remove last part
                print_string(domain_array, index_array, length_of_arrays, template_string_reduced, error_string)

        else:
            print_string(domain_array, index_array, length_of_arrays, template_string, error_string)

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

    free(index_array)

def generate_satisfiability_part_comparison(
    string_template, string_template_reduced,
    variable_domain_lists, comparison_operator_string,
    is_simple_comparison_, signum_
    ):
 
    # Keeps track of how many domain values there are per list:
    cdef int* length_array
    # The domain values
    cdef char*** domain_array
    # Keeps track of the lengths of strings of domain values
    cdef int** string_length_array 

    # Number of variables to be grounded (needd to compare domain values)
    cdef int number_arguments

    # Temporary definitions (initialized later)
    cdef int index

    cdef char* string_template_char
    cdef char* string_template_char_reduced

    cdef char* error_string_char

    number_arguments = len(variable_domain_lists)

    domain_array = <char***>malloc(number_arguments * sizeof(char**))
    length_array = <int*>malloc(number_arguments * sizeof(int))
    string_length_array = <int**>malloc(number_arguments * sizeof(int))


    cdef int (*comparison_function)(char*, char*, int, int) noexcept nogil
    cdef bint is_simple_comparison = is_simple_comparison_
    cdef int signum = signum_

    if domain_array and length_array and string_length_array:
        # MALLOC Succeeded

        index = 0
        for variable_domain_list in variable_domain_lists:

            c_array, length = convert_to_c_string_list(variable_domain_list)
            
            domain_array[index] = c_array
            length_array[index] = length

            string_length_array[index] = <int*>malloc(len(variable_domain_list) * sizeof(int))
            for domain_value_index in range(len(variable_domain_list)):
                domain_value = variable_domain_list[domain_value_index]
                string_length_array[index][domain_value_index] = <int>len(domain_value)

            index += 1

        string_template_char = <char*>malloc(sizeof(int) * len(string_template))
        strcpy(string_template_char, string_template.encode('ascii'))

        string_template_char_reduced = <char*>malloc(sizeof(int) * len(string_template_reduced))
        strcpy(string_template_char_reduced, string_template_reduced.encode('ascii'))

        error_string = "[ERROR] - Not arity implemented"
        error_string_char = <char*>malloc(sizeof(int) * len(error_string))
        strcpy(error_string_char, error_string.encode('ascii'))


        if comparison_operator_string == "=":
            comparison_function = simple_comparison_holds_equal
        elif comparison_operator_string == "!=":
            comparison_function = simple_comparison_holds_not_equal
        elif comparison_operator_string == "<":
            comparison_function = simple_comparison_holds_smaller
        elif comparison_operator_string == "<=":
            comparison_function = simple_comparison_holds_smaller_or_equal
        elif comparison_operator_string == ">":
            comparison_function = simple_comparison_holds_greater
        elif comparison_operator_string == ">=":
            comparison_function = simple_comparison_holds_greater_or_equal
        else:

            raise NotImplementedError(f"[ERROR] - Not implemented comparison operator {comparison_operator_string}")

        generate_comparison_combinations(
            domain_array, length_array, number_arguments,
            string_template_char, string_template_char_reduced, error_string_char,
            string_length_array, comparison_function, is_simple_comparison, signum
            )

    else:
        raise Exception("MALLOC failed for satisfiability part")

    index = 0
    for index in range(number_arguments):
        free_c_string_list(domain_array[index], length_array[index])


        free(string_length_array[index])

    free(length_array)
    free(string_length_array)

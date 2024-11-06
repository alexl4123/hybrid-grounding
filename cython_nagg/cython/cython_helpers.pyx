


from libc.stdio cimport FILE, fdopen, fprintf, stdout, fflush, fclose, printf

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
    int length_of_arrays, char* template_string, char* error_string, FILE* file_stream ) noexcept nogil:

    if length_of_arrays == 0:
        fprintf(file_stream, "%s", template_string)
    elif length_of_arrays == 1: 
        fprintf(file_stream, template_string,domain_array[0][index_array[0]])
    elif length_of_arrays == 2:
        fprintf(file_stream, template_string, domain_array[0][index_array[0]], domain_array[1][index_array[1]])
    elif length_of_arrays == 3:
        fprintf(file_stream, template_string, domain_array[0][index_array[0]], domain_array[1][index_array[1]], domain_array[2][index_array[2]])
    elif length_of_arrays == 4:
        fprintf(file_stream, template_string, domain_array[0][index_array[0]], domain_array[1][index_array[1]], domain_array[2][index_array[2]], domain_array[3][index_array[3]])
    elif length_of_arrays == 5:
        fprintf(file_stream, template_string, domain_array[0][index_array[0]], domain_array[1][index_array[1]], domain_array[2][index_array[2]], domain_array[3][index_array[3]], domain_array[4][index_array[4]])
    else:
        fprintf(file_stream, "%s", error_string)
        fprintf(file_stream, "\n<<<%d>>>\n", length_of_arrays)


def print_to_fd(int fd, char* string):

    # Open the file descriptor as a FILE* stream
    cdef FILE* file_stream = fdopen(fd, "w")
    if file_stream is NULL:
        raise ValueError("Could not open file descriptor")

    # Print to the file descriptor
    fprintf(file_stream, "%s", string)

    # Ensure data is flushed to the file descriptor
    fflush(file_stream)

    fclose(file_stream)


import io
cimport cython

from libc.string cimport strchr
from libc.stdlib cimport malloc, free
from cpython.dict cimport PyDict_SetItem, PyDict_Contains
from cpython.unicode cimport PyUnicode_FromString
from cpython.list cimport PyList_Append
from libc.string cimport strchr


cdef int char_to_int(int cur_char):
    # Converts a char to its integer representation
    # E.g., 48 is 0, 49 is 1, ...
    cdef int value_0 = 48 # ASCII value of 0 is 48
    return cur_char - value_0 # And values 0-9 are 48 to 57, e.g., 57-48 = 9 (check)

def preprocess_smodels_program(smodels_program_string, processed_heads_dict):
    # Keys for domain dict:
    cdef str tuples_size_string = "tuples_size"
    cdef str terms_string = "terms"
    cdef str terms_size_string = "terms_size"
    cdef unicode predicate_string

    # As IDLV is not able to handle #inf and #sup as input:
    cdef str sup_string = "#sup"
    cdef str inf_string = "#inf"
    cdef str sup_flag = "sup_flag"
    cdef str inf_flag = "inf_flag"

    # Prev char handling for detecting escape sequences:
    cdef int prev_char = -1
    cdef int prev_char_helper = -1
    cdef int number_added_terms = 0

    # Store the encoded byte string in a Python variable to extend its lifetime
    cdef bytes smodels_program_bytes = smodels_program_string.encode('utf-8')
    #cdef char* smodels_program_cstr = smodels_program_bytes
    #cdef char* line_start = smodels_program_cstr
    cdef char* line_start = smodels_program_bytes
    cdef char* newline_pos
    cdef int cur_char
    cdef int line_length
    cdef int i

    # Used Characters
    cdef int space_char = b" "[0]
    cdef int newline_char = b"\n"
    cdef int comment_char = b"%"[0]
    cdef int quotation_mark_char = b"\""[0]
    cdef int opening_bracket_char = b"("[0]
    cdef int closing_bracket_char = b")"[0]
    cdef int dot_char = b"."[0]
    cdef int comma_char = b","[0]
    cdef int backslash_char = b"\\"[0] # Backslash

    # Parsed number from strings:
    cdef int cur_number = 0

    # Python Datatypes:
    cdef list splits = []
    cdef list rules = []
    cdef dict literals_dict = {}
    cdef dict domain_dictionary = {}
    cdef dict total_domain = {}

    # Decision Bools
    cdef bint in_fact_id = True
    cdef bint in_fact_terms = False
    cdef bint current_fact_head_in_dict = False
    cdef bint last_char_is_space = False

    # Predicate String (for entire predicate)
    cdef int predicate_start_index = -1
    cdef int predicate_end_index = -1
    cdef bytearray predicate_bytearray
    cdef int predicate_length
    cdef int predicate_index

    # Head Atom Byte-Array (String)
    cdef int head_atom_start_index = -1
    cdef int head_atom_end_index = -1
    cdef bytearray head_atom_bytearray
    cdef int head_atom_index
    cdef int head_atom_length
    cdef unicode head_atom_string
    cdef bint head_atom_string_compiled = False

    # Term Bytearray (String)
    cdef int term_length = -1
    cdef int term_string_start_index = -1
    cdef int term_string_end_index = -1
    cdef int cur_index
    cdef bytearray term_bytearray
    cdef unicode term_string


    # Number of terms in fact
    cdef int current_fact_number_terms = 0
    # Nesting depth w.r.t. to ( and )
    cdef int current_head_nesting_depth = 0

    # Decision Bools
    cdef bint in_rules_part = True
    cdef bint in_domain_part = False

    cdef bint in_number = True
    cdef bint in_string = False

    while True:
        # Find the position of the next newline character
        newline_pos = strchr(line_start, ord('\n'))
        
        if newline_pos is NULL:
            # END
            break
        
        # Calculate the length of the current line
        line_length = newline_pos - line_start

        # SMODELS format distings blocks with a "0" line
        # Blocks are checked here:
        if line_length == 1 and line_start[0] == ord('0') and in_rules_part == True and in_domain_part == False:
            in_rules_part = False
            in_domain_part = True

            line_start = newline_pos + 1
            continue
        elif line_length == 1 and line_start[0] == ord('0') and in_rules_part == False and in_domain_part == True:
            in_domain_part = False

            line_start = newline_pos + 1
            continue
        elif in_rules_part == False and in_domain_part == False:

            line_start = newline_pos + 1
            continue


        if in_rules_part == True:
            # Iterate through each character in the line
            for i in range(line_length):
                cur_char = line_start[i]
                # Process cur_char as needed

                if cur_char == space_char:
                    PyList_Append(splits, cur_number)
                    cur_number = 0
                    last_char_is_space = True
                else:
                    cur_number = char_to_int(cur_char) + 10 * cur_number
                    last_char_is_space = False

            # Append last number
            if last_char_is_space is False:
                PyList_Append(splits, cur_number)

            PyList_Append(rules, splits)

            cur_number = 0
            splits = []
        elif in_domain_part == True:
            splits = [] # Reuse for parsing terms
            cur_number = 0 # Reuse for getting key number

            # Iterate through each character in the line
            for char_index in range(line_length):
                cur_char = line_start[char_index]

                prev_char = prev_char_helper
                prev_char_helper = cur_char
                # Process cur_char as needed

                if in_number == True and cur_char != space_char:
                    cur_number = char_to_int(cur_char) + 10 * cur_number
                elif in_number == True and cur_char == space_char:
                    in_number = False

                    head_atom_start_index = char_index + 1
                    predicate_start_index = char_index + 1

                elif in_fact_id is True: # In fact ID: I.e. in abcd(..,..) -> in abcd
                    if cur_char != opening_bracket_char:

                        continue
                    elif cur_char == opening_bracket_char: 
                        # At position "abc(" 
                        in_fact_id = False
                        in_fact_terms = True

                        head_atom_end_index = char_index

                        head_atom_length = head_atom_end_index - head_atom_start_index
                        head_atom_bytearray = bytearray(head_atom_length)
                        for head_atom_index in range(head_atom_length):
                            head_atom_bytearray[head_atom_index] = line_start[head_atom_start_index + head_atom_index]

                        head_atom_string = PyUnicode_FromString(head_atom_bytearray)

                        if PyDict_Contains(processed_heads_dict, head_atom_string):
                            current_fact_head_in_dict = True
                        head_atom_string_compiled = True


                        term_string_start_index = char_index + 1

                        # Number of terms increases:
                        current_fact_number_terms += 1

                        continue

                elif in_fact_terms is True and current_fact_head_in_dict is False: # Not in fact ID: I.e. in abcd(..,..) -> in (..,..)
                    # Nesting Depth ()
                    # String "..."
                    # Term splitter ","
                    if in_string is False:
                        if current_head_nesting_depth == 0 and cur_char == closing_bracket_char:
                            # Position "abc(.,..,..)"
                            in_fact_terms = False

                            term_string_end_index = char_index
                            term_length = term_string_end_index - term_string_start_index
                            term_bytearray = bytearray(term_length)
                            for cur_index in range(term_length):
                                term_bytearray[cur_index] = line_start[cur_index + term_string_start_index]

                            term_string = PyUnicode_FromString(term_bytearray)

                            if sup_string in term_string:
                                term_string = term_string.replace(sup_string, sup_flag)
                            if inf_string in term_string:
                                term_string = term_string.replace(inf_string, inf_flag)

                            splits.append(term_string)

                            continue
                        elif cur_char == comma_char and current_head_nesting_depth == 0:

                            term_string_end_index = char_index
                            term_length = term_string_end_index - term_string_start_index
                            term_bytearray = bytearray(term_length)
                            for cur_index in range(term_length):
                                term_bytearray[cur_index] = line_start[cur_index + term_string_start_index]

                            term_string = PyUnicode_FromString(term_bytearray)

                            if sup_string in term_string:
                                term_string = term_string.replace(sup_string, sup_flag)
                            if inf_string in term_string:
                                term_string = term_string.replace(inf_string, inf_flag)

                            splits.append(term_string)

                            term_string_start_index = char_index + 1

                            current_fact_number_terms += 1

                            continue

                        elif cur_char == closing_bracket_char:
                            current_head_nesting_depth -= 1

                            continue
                        elif cur_char == opening_bracket_char:
                            current_head_nesting_depth += 1

                            continue
                        elif cur_char == quotation_mark_char:
                            in_string = True

                            continue
                        else:
                            continue

                    else: # In String
                        if cur_char == quotation_mark_char and prev_char != backslash_char:
                            in_string = False

                            continue
                        else:

                            continue
                else: # Nothing to do
                    continue

            # ---------------------------------------------------
            # Parsing complete, add to domain, ...
            # ---------------------------------------------------
            if current_fact_number_terms == 0:
                head_atom_end_index = char_index + 1
            predicate_end_index = char_index + 1

            predicate_length = predicate_end_index - predicate_start_index
            predicate_bytearray = bytearray(predicate_length)
            for predicate_index in range(predicate_length):
                predicate_bytearray[predicate_index] = line_start[predicate_start_index + predicate_index]

            predicate_string = PyUnicode_FromString(predicate_bytearray)
            predicate_string = predicate_string.replace(sup_string, sup_flag)
            predicate_string = predicate_string.replace(inf_string, inf_flag)
            literals_dict[cur_number] = predicate_string

            if head_atom_string_compiled is False:
                head_atom_length = head_atom_end_index - head_atom_start_index
                head_atom_bytearray = bytearray(head_atom_length)
                for head_atom_index in range(head_atom_length):
                    head_atom_bytearray[head_atom_index] = line_start[head_atom_start_index + head_atom_index]

                head_atom_string = PyUnicode_FromString(head_atom_bytearray)

                if PyDict_Contains(processed_heads_dict, head_atom_string):
                    current_fact_head_in_dict = True

            if current_fact_number_terms == 0 and current_fact_head_in_dict is False:
                # Handle atom (0-arity)
                if head_atom_string not in domain_dictionary:
                    domain_dictionary[head_atom_string] = {
                        tuples_size_string:1,
                        terms_string:[],
                        terms_size_string:[],
                    }
                else:
                    domain_dictionary[head_atom_string][tuples_size_string] += 1

            elif current_fact_head_in_dict is False:
                # Handle predicate (>0-arity)

                if head_atom_string not in domain_dictionary:
                    # Add head atom to domain:
                    domain_dictionary[head_atom_string] = {
                        tuples_size_string:1,
                        terms_string:[], # TODO
                        terms_size_string:[],
                    }
                    for term_index in range(current_fact_number_terms):
                        domain_dictionary[head_atom_string][terms_string].append({splits[term_index]:True})
                        domain_dictionary[head_atom_string][terms_size_string].append(1)

                        if splits[term_index] not in total_domain:
                            total_domain[splits[term_index]] = True
                    
                else:
                    # Head atom already in domain:
                    for term_index in range(current_fact_number_terms):
                        if splits[term_index] not in domain_dictionary[head_atom_string][terms_string][term_index]:
                            domain_dictionary[head_atom_string][terms_string][term_index][splits[term_index]] = True
                            domain_dictionary[head_atom_string][terms_size_string][term_index] += 1

                        if splits[term_index] not in total_domain:
                            total_domain[splits[term_index]] = True
                    domain_dictionary[head_atom_string][tuples_size_string] += 1

            # Reset temporary variables:
            splits = []
            cur_number = 0

            head_atom_start_index = -1
            head_atom_end_index = -1

            current_fact_number_terms = 0

            head_atom_string_compiled = False
            in_fact_id = True
            in_fact_terms = False
            in_number = True

            current_fact_head_in_dict = False

            prev_char_helper = -1
            prev_char = -1

        # Move line_start to the start of the next line
        line_start = newline_pos + 1

    return rules, domain_dictionary, total_domain, literals_dict



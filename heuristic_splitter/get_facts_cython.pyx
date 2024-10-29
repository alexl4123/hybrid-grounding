
cimport cython
from libc.string cimport strchr
from libc.stdlib cimport malloc, free
from cpython.dict cimport PyDict_SetItem, PyDict_Contains
from cpython.unicode cimport PyUnicode_FromString
from cpython.list cimport PyList_Append

cdef bint char_is_in_a_z(int cur_char):
    return cur_char >= 97 and cur_char <= 122

cdef bint char_is_underscore(int cur_char):
    return cur_char == 95

cdef bint char_is_in_A_Z(int cur_char):
    return cur_char >= 65 and cur_char <= 90

cdef bint char_is_in_0_9(int cur_char):
    return cur_char >= 48 and cur_char <= 57

cdef bint char_is_valid_ID_char(int cur_char):
    return char_is_in_a_z(cur_char) is True or\
        char_is_in_A_Z(cur_char) is True or\
        char_is_in_0_9(cur_char) is True or\
        char_is_underscore(cur_char) is True

def get_facts_from_file_handle(f):
    cdef dict facts = {}
    cdef dict facts_heads = {}
    cdef list other_rules = []

    # These definitions are very important for efficiencies sake!
    # Otherwise it defaults back to python (performance loss of factor ~10)    
    cdef int index
    cdef bytes piece
    cdef int cur_char

    cdef int prev_char = -1
    cdef int prev_char_helper = -1

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
    cdef int t_char = b"t"[0]

    # Decision Bools
    cdef bint in_head = False
    cdef bint comment_line = False
    cdef bint in_string = False

    cdef bint is_fact = True
    cdef bint in_fact_id = False
    cdef bint in_fact_terms = False
    cdef bint current_fact_head_in_dict = False

    # Rule String (for other rules and complete fact)
    cdef int current_rule_size = 150
    cdef int current_rule_list_head = 0
    cdef bytearray current_rule_bytearray = bytearray(current_rule_size)
    cdef bytearray tmp_current_rule_bytearray 

    # Rule String (for fact-atom)
    cdef int current_fact_id_function_size = 30
    cdef int current_fact_id_list_head = 0
    cdef bytearray current_fact_id_bytearray = bytearray(current_fact_id_function_size)
    cdef bytearray tmp_current_fact_id_bytearray 

    # Number of terms in fact
    cdef int current_fact_number_terms = 0
    # Nesting depth w.r.t. to ( and )
    cdef int current_head_nesting_depth = 0

    while True:
        #piece = f.read(1024)
        #piece = f.read(2048)
        #piece = f.read(4096)
        piece = f.read(4096)

        if not piece:
            break
        
        for cur_char in piece:
            # Go through all characters in current buffer:

            if in_string is False:
                if cur_char == newline_char:
                    comment_line = False
                    continue

            # Prev chars needed for escape characters
            prev_char = prev_char_helper
            prev_char_helper = cur_char

            # --- Increasing Size of String if needed
            if current_rule_list_head >= current_rule_size:
                current_rule_size *= 2
                tmp_current_rule_bytearray = bytearray(current_rule_size)

                for index in range(current_rule_list_head):
                    tmp_current_rule_bytearray[index] = current_rule_bytearray[index]

                current_rule_bytearray = tmp_current_rule_bytearray

            if current_fact_id_list_head >= current_fact_id_function_size:
                current_fact_id_function_size *= 2
                tmp_current_fact_id_bytearray = bytearray(current_fact_id_function_size)

                for index in range(current_fact_id_list_head):
                    tmp_current_fact_id_bytearray[index] = current_fact_id_bytearray[index]

                current_fact_id_bytearray = tmp_current_fact_id_bytearray
            # ---
            # Ignore white space, newline, and commented-out code:
            if in_string is False:
                if cur_char == space_char:
                    if prev_char == t_char:
                        # E.g., in body: 'not a', then the space must not be removed!
                        current_rule_bytearray[current_rule_list_head] = cur_char
                        current_rule_list_head += 1
                        continue
                    else:
                        continue
                elif cur_char == comment_char:
                    comment_line = True
                    continue
                elif comment_line is True:
                    # Ignore all characters after a % until a new line
                    continue



            # Handle fact
            if is_fact is True:
                if current_fact_id_list_head > 0:
                    if in_fact_id is True: # In fact ID: I.e. in abcd(..,..) -> in abcd
                        if char_is_valid_ID_char(cur_char): # In fact ID: I.e., in abcd(..,..) -> in bcd (not in a)
                            current_fact_id_bytearray[current_fact_id_list_head] = cur_char
                            current_rule_bytearray[current_rule_list_head] = cur_char

                            current_fact_id_list_head += 1
                            current_rule_list_head += 1

                            continue
                        elif in_fact_id is True and cur_char == opening_bracket_char: 
                            # At position "abc(" 
                            in_fact_id = False
                            in_fact_terms = True

                            if PyDict_Contains(facts, PyUnicode_FromString(current_fact_id_bytearray)):
                                current_fact_head_in_dict = True

                            current_rule_bytearray[current_rule_list_head] = cur_char
                            current_rule_list_head += 1

                            # Number of terms increases:
                            current_fact_number_terms += 1

                            continue

                        elif in_fact_id is True and cur_char == dot_char:
                            # Fact "abc." finished:
                            if current_fact_head_in_dict is False:

                                PyDict_SetItem(facts_heads, PyUnicode_FromString(current_fact_id_bytearray), current_fact_number_terms)

                                current_fact_id_bytearray[current_fact_id_list_head] = cur_char
                                current_fact_id_list_head += 1

                                PyDict_SetItem(facts, PyUnicode_FromString(current_fact_id_bytearray), True)

                            current_fact_id_bytearray = bytearray(current_fact_id_function_size)
                            current_rule_bytearray = bytearray(current_rule_size)

                            current_fact_number_terms = 0
                            current_fact_id_list_head = 0
                            current_rule_list_head = 0
                            current_head_nesting_depth = 0


                            in_fact_id = False
                            current_fact_head_in_dict = False

                            continue
                        else:

                            current_rule_bytearray[current_rule_list_head] = cur_char
                            current_rule_list_head += 1

                            is_fact = False
                            in_fact_id = False
                            in_fact_terms = False

                            continue

                    elif in_fact_terms is True: # Not in fact ID: I.e. in abcd(..,..) -> in (..,..)
                        # Nesting Depth ()
                        # String
                        # ","
                        if in_string is False:
                            if current_head_nesting_depth == 0 and cur_char == closing_bracket_char:
                                # Position "abc(.,..,..)"
                                in_fact_terms = False
                            
                                current_rule_bytearray[current_rule_list_head] = cur_char
                                current_rule_list_head += 1

                                continue
                            elif cur_char == comma_char and current_head_nesting_depth == 0:
                                current_fact_number_terms += 1
                            
                                current_rule_bytearray[current_rule_list_head] = cur_char
                                current_rule_list_head += 1

                                continue

                            elif cur_char == closing_bracket_char:
                                current_head_nesting_depth -= 1
                            
                                current_rule_bytearray[current_rule_list_head] = cur_char
                                current_rule_list_head += 1

                                continue
                            elif cur_char == opening_bracket_char:
                                current_head_nesting_depth += 1
                            
                                current_rule_bytearray[current_rule_list_head] = cur_char
                                current_rule_list_head += 1

                                continue
                            elif cur_char == quotation_mark_char:
                                in_string = True
                            
                                current_rule_bytearray[current_rule_list_head] = cur_char
                                current_rule_list_head += 1

                                continue
                            else:
                                current_rule_bytearray[current_rule_list_head] = cur_char
                                current_rule_list_head += 1

                                continue

                        else: # In String
                            if cur_char == quotation_mark_char and prev_char != backslash_char:
                                in_string = False

                                current_rule_bytearray[current_rule_list_head] = cur_char
                                current_rule_list_head += 1

                                continue
                            else:
                                current_rule_bytearray[current_rule_list_head] = cur_char
                                current_rule_list_head += 1

                                continue

                    elif in_fact_terms is False and in_string is False and current_head_nesting_depth == 0 and cur_char == dot_char:
                        # Fact "abc(.,..,..)." finished:

                        if current_fact_head_in_dict is False:

                            PyDict_SetItem(facts_heads, PyUnicode_FromString(current_fact_id_bytearray), current_fact_number_terms)

                            current_fact_id_bytearray = bytearray(current_fact_id_function_size)


                        current_rule_bytearray[current_rule_list_head] = cur_char
                        current_rule_list_head += 1

                        PyDict_SetItem(facts, PyUnicode_FromString(current_rule_bytearray), True)
                        current_rule_bytearray = bytearray(current_rule_size)

                        current_fact_number_terms = 0
                        current_fact_id_list_head = 0
                        current_rule_list_head = 0

                        in_fact_id = False
                        current_fact_head_in_dict = False

                        continue
                    else:
                        is_fact = False
                        in_fact_id = False
                        in_fact_terms = False

                        current_rule_bytearray[current_rule_list_head] = cur_char
                        current_rule_list_head += 1

                        continue

                else: # In first character of the head (should be in [_a-z] for fact):
                    if char_is_in_a_z(cur_char) or char_is_underscore(cur_char):
                        current_fact_id_bytearray[current_fact_id_list_head] = cur_char
                        current_rule_bytearray[current_rule_list_head] = cur_char

                        current_fact_id_list_head += 1
                        current_rule_list_head += 1

                        in_fact_id = True
                        continue
                    else: # Definitely not a fact! 
                        is_fact = False
                        in_fact_id = False
                        in_fact_terms = False

                        current_rule_bytearray[current_rule_list_head] = cur_char
                        current_rule_list_head += 1

                        continue

            # ----------------------------------------------------------------------------    
            else: # Not a fact:
                if in_string is False:
                    if cur_char != quotation_mark_char and cur_char != dot_char:

                        current_rule_bytearray[current_rule_list_head] = cur_char
                        current_rule_list_head += 1
                    
                    elif cur_char == quotation_mark_char:

                        in_string = True

                        current_rule_bytearray[current_rule_list_head] = cur_char
                        current_rule_list_head += 1
                    elif cur_char == dot_char:
                        # H :- B_r^+, B_r^-. (finished rule)
                        # -> Append to other rules
                        current_rule_bytearray[current_rule_list_head] = cur_char
                        current_rule_list_head += 1
                    
                        PyList_Append(other_rules, PyUnicode_FromString(current_rule_bytearray))

                        current_rule_bytearray = bytearray(current_rule_size)
                        current_fact_id_bytearray = bytearray(current_fact_id_function_size)

                        current_fact_number_terms = 0
                        current_fact_id_list_head = 0
                        current_rule_list_head = 0

                        in_head = False
                        comment_line = False
                        in_string = False

                        is_fact = True
                        in_fact_id = False
                        in_fact_terms = False


                else: # In String:
                    if cur_char == quotation_mark_char and prev_char != backslash_char:
                        in_string = False

                        current_rule_bytearray[current_rule_list_head] = cur_char
                        current_rule_list_head += 1

                        continue
                    else:
                        current_rule_bytearray[current_rule_list_head] = cur_char
                        current_rule_list_head += 1

                        continue


    return facts, facts_heads, other_rules

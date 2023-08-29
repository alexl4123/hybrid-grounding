
import itertools
import clingo

from ..comparison_tools import ComparisonTools

from .aggregate_mode import AggregateMode

class RewritingAggregateStrategy:

    @classmethod
    def rewriting_aggregate_strategy(cls, aggregate_index, aggregate, variables_dependencies_aggregate, aggregate_mode, cur_variable_dependencies):

        str_type = aggregate["function"][1]
        str_id = aggregate["id"] 

        new_prg_list = []
        output_remaining_body = []

        if str_type == "sum":

            output_remaining_body.append(f"{str_type}_ag{str_id}(S{aggregate_index})")

            if aggregate["left_guard"]:
                guard = aggregate["left_guard"]
                output_remaining_body.append(f"{guard.term} {ComparisonTools.getCompOperator(guard.comparison)} S{aggregate_index}")
            if aggregate["right_guard"]:
                guard = aggregate["right_guard"]
                output_remaining_body.append(f"S{aggregate_index} {ComparisonTools.getCompOperator(guard.comparison)} {guard.term}")

            new_prg_list += cls._add_sum_aggregate_rules(aggregate)

        elif str_type == "count":

            count_name_ending = ""
            if len(variables_dependencies_aggregate) == 0:
                count_name_ending += "(1)"
            else:
                count_name_ending += f"({','.join(variables_dependencies_aggregate)})"

            # cls.cur_variable_dependencies 
            if aggregate["left_guard"]:
                left_name = f"not not_{str_type}_ag{str_id}_left{count_name_ending}"
                output_remaining_body.append(left_name)
            if aggregate["right_guard"]:
                right_name = f"not not not_{str_type}_ag{str_id}_right{count_name_ending}"
                output_remaining_body.append(right_name)

            new_prg_list += cls._add_count_aggregate_rules(aggregate, variables_dependencies_aggregate, aggregate_mode, cur_variable_dependencies)
        elif str_type == "min":
            (new_prg_list_tmp, output_remaining_body_tmp) = cls._add_min_max_aggregate_rules(aggregate, variables_dependencies_aggregate, cls._min_operator_functions, cls._min_remaining_body_functions, aggregate_mode, cur_variable_dependencies)
            new_prg_list += new_prg_list_tmp
            output_remaining_body += output_remaining_body_tmp
        elif str_type == "max":
            (new_prg_list_tmp, output_remaining_body_tmp) = cls._add_min_max_aggregate_rules(aggregate, variables_dependencies_aggregate, cls._max_operator_functions, cls._max_remaining_body_functions, aggregate_mode, cur_variable_dependencies)
            new_prg_list += new_prg_list_tmp
            output_remaining_body += output_remaining_body_tmp
        else: 
            assert(False) # Not Implemented

        return (new_prg_list, output_remaining_body)

    @classmethod
    def rewriting_no_body_aggregate_strategy(cls, aggregate, variables_dependencies_aggregate, aggregate_mode, cur_variable_dependencies):

        new_prg_list = []
        output_remaining_body = []

        str_type = aggregate["function"][1]
        str_id = aggregate["id"] 

        if str_type == "count":
            count_name_ending = ""
            if len(variables_dependencies_aggregate) == 0:
                count_name_ending += "(1)"
            else:
                count_name_ending += f"({','.join(variables_dependencies_aggregate)})"


            if aggregate["left_guard"]:
                left_name = f"not not_{str_type}_ag{str_id}_left{count_name_ending}"
                output_remaining_body.append(left_name)
            if aggregate["right_guard"]:
                right_name = f"not not not_{str_type}_ag{str_id}_right{count_name_ending}"
                output_remaining_body.append(right_name)

            new_prg_list += cls._add_count_aggregate_rules(aggregate, variables_dependencies_aggregate, aggregate_mode, cur_variable_dependencies)

        elif str_type == "min":
            (new_prg_list_tmp, output_remaining_body_tmp) = cls._add_min_max_aggregate_rules(aggregate, variables_dependencies_aggregate, cls._min_operator_functions, cls._min_remaining_body_functions, aggregate_mode, cur_variable_dependencies)
            new_prg_list += new_prg_list_tmp
            output_remaining_body += output_remaining_body_tmp
        elif str_type == "max":
            (new_prg_list_tmp, output_remaining_body_tmp) = cls._add_min_max_aggregate_rules(aggregate, variables_dependencies_aggregate, cls._max_operator_functions, cls._max_remaining_body_functions, aggregate_mode, cur_variable_dependencies)
            new_prg_list += new_prg_list_tmp
            output_remaining_body += output_remaining_body_tmp

        return (new_prg_list, output_remaining_body)

    #--------------------------------------------------------------------------------------------------------
    #------------------------------------ MIN-MAX-PART ------------------------------------------------------
    #--------------------------------------------------------------------------------------------------------

    @classmethod
    def _max_operator_functions(cls, operator_side, operator):
        if operator_side == "left":
            if operator == "<":
                new_operator = ">"
            elif operator == "<=":
                new_operator = ">="
            else:
                assert(False) # Not implemented
        elif operator_side == "right":
            if operator == "<":
                new_operator = ">="
            elif operator == "<=":
                new_operator = ">"
            else:
                assert(False) # Not implemented
        else:
            assert(False) 

        return new_operator


    @classmethod
    def _max_remaining_body_functions(cls, operator_side, head_count, name):
        if operator_side == "left":
            if head_count > 1:
                string =  f"not {name}"
            elif head_count == 1:
                string = f"{name}"
            else:
                assert(False)
        elif operator_side == "right":
            if head_count > 1:
                string = f"not not {name}"
            elif head_count == 1:
                string = f"not {name}"
        else:
            assert(False)

        return string

    @classmethod
    def _min_operator_functions(cls, operator_side, operator):
        if operator_side == "left":
            if operator == "<":
                new_operator = "<="
            elif operator == "<=":
                new_operator = "<"
            else:
                assert(False) # Not implemented
        elif operator_side == "right":
            if operator == "<":
                new_operator = "<"
            elif operator == "<=":
                new_operator = "<="
            else:
                assert(False) # Not implemented
        else:
            assert(False) 

        return new_operator

    @classmethod
    def _min_remaining_body_functions(cls, operator_side, head_count, name):
        if operator_side == "left":
            if head_count > 1:
                string =  f"not not {name}"
            elif head_count == 1:
                string = f"not {name}"
            else:
                assert(False)
        elif operator_side == "right":
            if head_count > 1:
                string = f"not {name}"
            elif head_count == 1:
                string = f"{name}"
        else:
            assert(False)

        return string


    @classmethod
    def _add_min_max_aggregate_rules(cls, aggregate, variable_dependencies, new_operator_functions, remaining_body_functions, aggregate_mode, cur_variable_dependencies):

        new_prg_list = []

        elements = aggregate["elements"]

        str_type = aggregate["function"][1]
        str_id = aggregate["id"] 

        remaining_body = []
        element_predicate_names = []

        left_head_names = []
        right_head_names = []

        for element_index in range(len(elements)):

            element = elements[element_index]
            element_dependent_variables = []

            for variable in element["condition_variables"]:
                if variable in variable_dependencies:
                    element_dependent_variables.append(variable)

            terms = element["terms"]

            if aggregate_mode == AggregateMode.REWRITING:

                element_predicate_name = f"body_{str_type}_ag{str_id}_{element_index}"

                terms_string = f"{','.join(terms + element_dependent_variables)}"

                element_body = f"{element_predicate_name}({terms_string})"
                body_string = f"{element_body} :- {','.join(element['condition'])}."

                new_prg_list.append(body_string)

                element_predicate_names.append(element_predicate_name)

            new_prg_list.append(f"#program {str_type}.")

            if len(element_dependent_variables) == 0:
                rule_head_ending = "(1)"
            else:
                rule_head_ending = f"({','.join(element_dependent_variables)})"

            if aggregate["left_guard"]:
                left_guard = aggregate["left_guard"]


                left_name = f"{str_type}_ag{str_id}_left"
                left_head_name = f"{left_name}_{element_index}{rule_head_ending}"

                left_guard_term = str(left_guard.term)
                count = int(left_guard_term) # Assuming constant

                operator = ComparisonTools.getCompOperator(left_guard.comparison)

                new_operator = new_operator_functions("left", operator)

                bodies = cls._add_min_max_aggregate_helper(element, element_index, new_operator, left_guard_term, element_predicate_names, element_dependent_variables, aggregate_mode, cur_variable_dependencies)


                rule_string = f"{left_head_name} :- {','.join(bodies)}."

                left_head_names.append(left_head_name)

                new_prg_list.append(rule_string)
            
            if aggregate["right_guard"]:
                right_guard = aggregate["right_guard"]

                right_name = f"{str_type}_ag{str_id}_right"
                right_head_name = f"{right_name}_{element_index}{rule_head_ending}"

                right_guard_term = str(right_guard.term)
                count = int(right_guard_term) # Assuming constant

                operator = ComparisonTools.getCompOperator(right_guard.comparison)

                new_operator = new_operator_functions("right", operator)

                bodies = cls._add_min_max_aggregate_helper(element, element_index, new_operator, right_guard_term, element_predicate_names, element_dependent_variables, aggregate_mode, cur_variable_dependencies)


                rule_string = f"{right_head_name} :- {','.join(bodies)}."
                
                right_head_names.append(right_head_name)

                new_prg_list.append(rule_string)


        if len(variable_dependencies) == 0:
            rule_head_ending = "(1)"
        else:
            rule_head_ending = f"({','.join(variable_dependencies)})"

        spawner_functions = []
        for variable in variable_dependencies:
            if variable in cur_variable_dependencies:
                cur_spawner_functions = cur_variable_dependencies[variable]
                for function in cur_spawner_functions:
                    spawner_functions.append(str(function))

        if len(left_head_names) > 1:
            left_intermediate_rule = f"not_{left_name}{rule_head_ending}"

            negated_head_strings = []
            for left_name in left_head_names:
                negated_head_strings.append(f"not {left_name}")

            helper_rule = f"{left_intermediate_rule} :- {','.join(spawner_functions + negated_head_strings)}."
            new_prg_list.append(helper_rule)
            remaining_body.append(remaining_body_functions("left",len(left_head_names),left_intermediate_rule))
        elif len(left_head_names) == 1:
            remaining_body.append(remaining_body_functions("left",len(left_head_names),left_head_names[0]))

        if len(right_head_names) > 1:
            right_intermediate_rule = f"not_{right_name}{rule_head_ending}"

            negated_head_strings = []
            for right_name in right_head_names:
                negated_head_strings.append(f"not {right_name}")

            helper_rule = f"{right_intermediate_rule} :- {','.join(spawner_functions + negated_head_strings)}."
            new_prg_list.append(helper_rule)

            remaining_body.append(remaining_body_functions("right",len(left_head_names),right_intermediate_rule))
        elif len(right_head_names) == 1:
            remaining_body.append(remaining_body_functions("right",len(left_head_names),right_head_names[0]))

        return (new_prg_list, remaining_body)
 
    @classmethod
    def _add_min_max_aggregate_helper(cls, element, element_index, new_operator, guard_term, element_predicate_names, element_dependent_variables, aggregate_mode, cur_variable_dependencies):

        bodies = []

        terms = []
        for term in element["terms"]:
            terms.append(f"{term}_{str(element_index)}")

        terms += element_dependent_variables

        if aggregate_mode == AggregateMode.REWRITING:
            body = f"{element_predicate_names[element_index]}({','.join(terms)}), {terms[0]} {new_operator} {guard_term}"
            bodies.append(body)

        elif aggregate_mode == AggregateMode.REWRITING_NO_BODY:

            new_conditions = []
            for condition in element["condition"]:
                if "arguments" in condition: # is a function

                    new_arguments = []
                    for argument in condition["arguments"]:
                        if "variable" in argument:
                            variable = argument['variable']
                            if str(variable) in element_dependent_variables:
                                new_arguments.append(str(variable))
                            else:
                                new_arguments.append(f"{str(variable)}_{element_index}")
                        elif "term" in argument:
                            new_arguments.append(f"{argument['term']}")
                        else:
                            assert(False) # Not implemented

                    condition_string = f"{condition['name']}"
                    if len(new_arguments) > 0:
                        condition_string += f"({','.join(new_arguments)})"

                    new_conditions.append(condition_string)

                elif "comparison" in condition: # is a comparison
                    comparison = condition["comparison"]

                    variable_assignments = {}

                    left = comparison.term
                    assert(len(comparison.guards) <= 1)
                    right = comparison.guards[0].term
                    comparison_operator = comparison.guards[0].comparison



                    for argument in ComparisonTools.get_arguments_from_operation(left):
                        if argument.ast_type == clingo.ast.ASTType.Variable:
                            if str(argument) in element_dependent_variables:
                                variable_assignments[str(argument)] = str(argument)
                            else:
                                variable_assignments[str(argument)] = f"{str(argument)}_{str(element_index)}"

                    for argument in ComparisonTools.get_arguments_from_operation(right):
                        if argument.ast_type == clingo.ast.ASTType.Variable:
                            if str(argument) in element_dependent_variables:
                                variable_assignments[str(argument)] = str(argument)
                            else:
                                variable_assignments[str(argument)] = f"{str(argument)}_{str(element_index)}"

                    instantiated_left = ComparisonTools.instantiate_operation(left, variable_assignments)
                    instantiated_right = ComparisonTools.instantiate_operation(right, variable_assignments)

                    new_conditions.append(ComparisonTools.comparison_handlings(comparison_operator, instantiated_left, instantiated_right))

                else:
                    assert(False) # Not implemented

            new_conditions.append(f"{terms[0]} {new_operator} {guard_term}")

            bodies += new_conditions

        return bodies
 
    #--------------------------------------------------------------------------------------------------------
    #------------------------------------ COUNT-PART --------------------------------------------------------
    #--------------------------------------------------------------------------------------------------------
                      

    @classmethod
    def _add_count_aggregate_rules(cls, aggregate, variable_dependencies, aggregate_mode, cur_variable_dependencies):
        
        new_prg_part = []

        str_type = aggregate["function"][1]
        str_id = aggregate["id"] 


        if aggregate_mode == AggregateMode.REWRITING:
            for element_index in range(len(aggregate["elements"])):
                
                element = aggregate["elements"][element_index]

                element_dependent_variables = []
                for variable in element["condition_variables"]:
                    if variable in variable_dependencies:
                        element_dependent_variables.append(variable)

                term_string = f"{','.join(element['terms'] + element_dependent_variables)}"

                body_string = f"body_{str_type}_ag{str_id}_{element_index}({term_string}) :- {','.join(element['condition'])}."
                new_prg_part.append(body_string)

        new_prg_part.append(f"#program {str_type}.")

        if aggregate["left_guard"]:
            left_guard = aggregate["left_guard"]

            left_name = f"{str_type}_ag{str_id}_left"

            count = int(str(left_guard.term)) # Assuming constant

            operator = ComparisonTools.getCompOperator(left_guard.comparison)
            if operator == "<":
                count += 1
            elif operator == "<=":
                count = count
            else:
                assert(False) # Not implemented

            rules_strings = cls._count_generate_bodies_and_helper_bodies(left_name, count, aggregate["elements"], str_type, str_id, variable_dependencies, aggregate_mode, cur_variable_dependencies)

            for rule_string in rules_strings:
                new_prg_part.append(rule_string)
        
        if aggregate["right_guard"]:
            right_guard = aggregate["right_guard"]

            right_name = f"{str_type}_ag{str_id}_right"

            count = int(str(right_guard.term)) # Assuming constant

            operator = ComparisonTools.getCompOperator(left_guard.comparison)
            if operator == "<":
                count = count
            elif operator == "<=":
                count += 1
            else:
                assert(False) # Not implemented

            rules_strings = cls._count_generate_bodies_and_helper_bodies(right_name, count,  aggregate["elements"], str_type, str_id, variable_dependencies, aggregate_mode, cur_variable_dependencies)

            for rule_string in rules_strings:
                new_prg_part.append(rule_string)

        return new_prg_part
                
    @classmethod
    def _count_generate_bodies_and_helper_bodies(cls, rule_head_name, count, elements, str_type, str_id, variable_dependencies, aggregate_mode, cur_variable_dependencies):

        rules_strings = []
        rules_head_strings = []

        combination_lists = []
        for index in range(count):
            combination_lists.append(list(range(len(elements))))

        combination_list = list(itertools.product(*combination_lists))
        refined_combination_list = []
        for combination in combination_list:
            cur = list(combination)
            cur.sort()

            if cur not in refined_combination_list:
                refined_combination_list.append(cur)

        for combination_index in range(len(refined_combination_list)):

            combination = refined_combination_list[combination_index]

            combination_variables = []
            terms = []
            bodies = []

            for index in range(count):

                element_index = combination[index]
                element = elements[element_index]


                element_dependent_variables = []
                for variable in element["condition_variables"]:
                    if variable in variable_dependencies:
                        element_dependent_variables.append(variable)
                        if variable not in combination_variables:
                            combination_variables.append(variable)


                new_terms = []
                for term in element["terms"]:
                    if cls.check_string_is_int(str(term)) == True:
                        new_terms.append(str(term))
                    else:
                        new_terms.append(f"{str(term)}_{str(element_index)}_{str(index)}")

                terms.append(new_terms)

                if aggregate_mode == AggregateMode.REWRITING:
                    terms_string = f"{','.join(new_terms + element_dependent_variables)}"

                    bodies.append(f"body_{str_type}_ag{str_id}_{element_index}({terms_string})") 

                elif aggregate_mode == AggregateMode.REWRITING_NO_BODY:

                    new_conditions = []

                    for condition in element["condition"]:

                        if "arguments" in condition:

                            new_condition = condition["name"]

                            new_args = []


                            for argument in condition["arguments"]:
                                if "variable" in argument:
                                    variable = argument["variable"]
                                    if variable in element_dependent_variables:
                                        new_args.append(f"{variable}")
                                    else:
                                        new_args.append(f"{variable}_{str(element_index)}_{str(index)}")
                                elif "term" in argument:
                                    new_args.append(f"{argument['term']}")

                            if len(new_args) > 0:
                                new_condition += f"({','.join(new_args)})"

                            new_conditions.append(new_condition)
                        elif "comparison" in condition:
                            comparison = condition["comparison"]

                            variable_assignments = {}

                            left = comparison.term
                            assert(len(comparison.guards) <= 1)
                            right = comparison.guards[0].term
                            comparison_operator = comparison.guards[0].comparison

                            for argument in ComparisonTools.get_arguments_from_operation(left):
                                if argument.ast_type == clingo.ast.ASTType.Variable:
                                    if str(argument) in element_dependent_variables:
                                        new_args.append(f"{str(argument)}")
                                    else:
                                        new_args.append(f"{str(argument)}_{str(element_index)}_{str(index)}")

                                    variable_assignments[str(argument)] = f"{str(argument)}_{str(element_index)}_{str(index)}"

                            for argument in ComparisonTools.get_arguments_from_operation(right):
                                if argument.ast_type == clingo.ast.ASTType.Variable:
                                    if str(argument) in element_dependent_variables:
                                        new_args.append(f"{str(argument)}")
                                    else:
                                        new_args.append(f"{str(argument)}_{str(element_index)}_{str(index)}")

                                    variable_assignments[str(argument)] = f"{str(argument)}_{str(element_index)}_{str(index)}"


                            instantiated_left = ComparisonTools.instantiate_operation(left, variable_assignments)
                            instantiated_right = ComparisonTools.instantiate_operation(right, variable_assignments)

                            new_conditions.append(ComparisonTools.comparison_handlings(comparison_operator, instantiated_left, instantiated_right))


                        else:
                            assert(False) # Not implemented

                    bodies.append(f"{','.join(new_conditions)}")

            helper_bodies = []
            for index_1 in range(len(terms)):
                for index_2 in range(index_1 + 1, len(terms)):

                    helper_body = "0 != "

                    if len(terms[index_1]) != len(terms[index_2]):
                        continue



                    term_length = min(len(terms[index_1]), len(terms[index_2])) 

                    term_combinations = [] 
                    for term_index in range(term_length):
                        first_term = terms[index_1][term_index]
                        second_term = terms[index_2][term_index]

                        if cls.check_string_is_int(first_term) == False and cls.check_string_is_int(second_term) == False: 
                            term_combinations.append(f"({first_term} ^ {second_term})")

                    helper_body = f"0 != {'?'.join(term_combinations)}"
                    helper_bodies.append(helper_body)

            if len(combination_variables) == 0:
                rule_head_ending = "(1)"
            else:
                rule_head_ending = f"({','.join(combination_variables)})"

            rule_head = f"{rule_head_name}_{combination_index}{rule_head_ending}"
   
            rules_head_strings.append(rule_head) 
            rules_strings.append(f"{rule_head} :- {','.join(bodies + helper_bodies)}.")
            # END OF FOR LOOP
            # -----------------

        count_name_ending = ""
        if len(variable_dependencies) == 0:
            count_name_ending += "(1)"
        else:
            count_name_ending += f"({','.join(variable_dependencies)})"

        spawner_functions = []
        for variable in variable_dependencies:
            if variable in cur_variable_dependencies:
                cur_spawner_functions = cur_variable_dependencies[variable]
                for function in cur_spawner_functions:
                    spawner_functions.append(str(function))

        negated_head_strings = []
        for head_string in rules_head_strings:
            negated_head_strings.append(f"not {head_string}")

        helper_rule = f"not_{rule_head_name}{count_name_ending} :- {','.join(spawner_functions + negated_head_strings)}."

        rules_strings.append(helper_rule)

        return (rules_strings)


    #--------------------------------------------------------------------------------------------------------
    #------------------------------------ SUM-PART ----------------------------------------------------------
    #--------------------------------------------------------------------------------------------------------
                      
    @classmethod
    def _add_sum_aggregate_rules(cls, aggregate):
        """
            Adds the necessary rules for the recursive sum aggregate.
        """

        new_prg_part = []

        str_type = aggregate["function"][1]
        str_id = aggregate["id"] 

        
        new_prg_part.append(f"#program {str_type}.")

        rule_string = f"{str_type}_ag{str_id}(S) :- "
       
        element_strings = []
        element_variables = [] 

        for element_id in range(len(aggregate["elements"])):
            element = aggregate["elements"][element_id]

            element_strings.append(f"{str_type}_ag{str_id}_elem{element_id}(S{element_id})")
            element_variables.append(f"S{element_id}")

        rule_string += ','.join(element_strings)

        rule_string += f", S = {'+'.join(element_variables)}."

        new_prg_part.append(rule_string)

        for element_id in range(len(aggregate["elements"])):

            element = aggregate["elements"][element_id]
            guard = aggregate["right_guard"]
            # Body
            body_head_def = f"body_ag{str_id}_elem{element_id}({','.join(element['terms'])})"
            body_head_def_terms = ','.join(element['terms'])

            # DRY VIOLATION START: DRY (Do Not Repeat) justification: Because it is only used here and writing a subroutine creates more overload than simply duplicating the code
            term_strings_temp = []
            for term_string in element['terms']:
                term_strings_temp.append(term_string + "1")
            body_head_1 = f"body_ag{str_id}_elem{element_id}({','.join(term_strings_temp)})"
            body_head_1_def_terms = ','.join(term_strings_temp)
             
            term_strings_temp = []
            for term_string in element['terms']:
                term_strings_temp.append(term_string + "2")
            body_head_2 = f"body_ag{str_id}_elem{element_id}({','.join(term_strings_temp)})"
            body_head_2_first = term_strings_temp[0]
            body_head_2_def_terms = ','.join(term_strings_temp)

            term_strings_temp = []
            for term_string in element['terms']:
                term_strings_temp.append(term_string + "3")
            body_head_3 = f"body_ag{str_id}_elem{element_id}({','.join(term_strings_temp)})"
            # DRY VIOLATION END

            if len(element['condition']) > 0:
                rule_string = f"{body_head_def} :- {','.join(element['condition'])}."
            else:
                rule_string = f"{body_head_def}."


            new_prg_part.append(rule_string)

            # Partial Sum Last

            rule_string = f"{str_type}_ag{str_id}_elem{element_id}(S) :- last_ag{str_id}_elem{element_id}({body_head_def_terms}), partial_{str_type}_ag{str_id}_elem{element_id}({body_head_def_terms},S)."
            new_prg_part.append(rule_string)

            # Partial Sum Middle

            rule_string = f"partial_{str_type}_ag{str_id}_elem{element_id}({body_head_2_def_terms},S2) :- next_ag{str_id}_elem{element_id}({body_head_1_def_terms},{body_head_2_def_terms}), partial_{str_type}_ag{str_id}_elem{element_id}({body_head_1_def_terms},S1), S2 = S1 + {body_head_2_first}, S2 <= {guard.term}."
            new_prg_part.append(rule_string)

            # Partial Sum First

            rule_string = f"partial_{str_type}_ag{str_id}_elem{element_id}({body_head_def_terms},S) :- first_ag{str_id}_elem{element_id}({body_head_def_terms}), S = {body_head_def_terms}."
            new_prg_part.append(rule_string)

            # not_last
            rule_string = f"not_last_ag{str_id}_elem{element_id}({body_head_1_def_terms}) :- {body_head_1}, {body_head_2}, {body_head_1} < {body_head_2}."
            new_prg_part.append(rule_string)

            # Last
            rule_string = f"last_ag{str_id}_elem{element_id}({body_head_def_terms}) :- {body_head_def}, not not_last_ag{str_id}_elem{element_id}({body_head_def_terms})."
            new_prg_part.append(rule_string)

            # not_next
            rule_string = f"not_next_ag{str_id}_elem{element_id}({body_head_1_def_terms}, {body_head_2_def_terms}) :- {body_head_1}, {body_head_2}, {body_head_3}, {body_head_1} < {body_head_3}, {body_head_3} < {body_head_2}."
            new_prg_part.append(rule_string)

            # next
            rule_string = f"next_ag{str_id}_elem{element_id}({body_head_1_def_terms}, {body_head_2_def_terms}) :- {body_head_1}, {body_head_2}, {body_head_1} < {body_head_2}, not not_next_ag{str_id}_elem{element_id}({body_head_1_def_terms}, {body_head_2_def_terms})."
            new_prg_part.append(rule_string)

            # not_first
            rule_string = f"not_first_ag{str_id}_elem{element_id}({body_head_2_def_terms}) :- {body_head_1}, {body_head_2}, {body_head_1} < {body_head_2}."
            new_prg_part.append(rule_string)

            # first
            rule_string = f"first_ag{str_id}_elem{element_id}({body_head_1_def_terms}) :- {body_head_1}, not not_first_ag{str_id}_elem{element_id}({body_head_1_def_terms})."
            new_prg_part.append(rule_string)

            return new_prg_part

    @classmethod
    def check_string_is_int(cls, string):
        try:
            a = int(string, 10)
            return True
        except ValueError:
            return False
import clingo

from .count_aggregate_helper import CountAggregateHelper

from .aggregate_mode import AggregateMode

class RSSum:

    @classmethod
    def _add_sum_aggregate_rules(cls, aggregate_dict, variable_dependencies, aggregate_mode, cur_variable_dependencies, guard_domain, operator_type, string_capsulation, guard_string, rule_positive_body, domain):
        
        new_prg_part_list = []
        new_prg_part_set = []

        str_type = aggregate_dict["function"][1]
        str_id = aggregate_dict["id"] 
        
        number_of_elements = len(aggregate_dict["elements"])

        original_rule_additional_body_literals = []

        if len(list(guard_domain)) == 1:
            guard_value = int(str(list(guard_domain)[0])) # Assuming constant

            cls._sum_single_domain_adder(aggregate_dict, aggregate_mode, str_type, str_id, variable_dependencies, operator_type, string_capsulation, guard_value, cur_variable_dependencies, original_rule_additional_body_literals, new_prg_part_list, new_prg_part_set, [], guard_string, rule_positive_body, domain)
        else:
            guard_domain_list = [int(value) for value in list(guard_domain)]

            for guard_value in guard_domain_list:
                always_add_variable_dependecies = [str(guard_value)]

                cls._sum_single_domain_adder(aggregate_dict, aggregate_mode, str_type, str_id, variable_dependencies, operator_type, string_capsulation, guard_value, cur_variable_dependencies, original_rule_additional_body_literals, new_prg_part_list, new_prg_part_set, always_add_variable_dependecies, guard_string, rule_positive_body, domain)
        return (new_prg_part_list, original_rule_additional_body_literals, list(set(new_prg_part_set)))
    
    @classmethod
    def _sum_single_domain_adder(cls, aggregate_dict, aggregate_mode, str_type, str_id, variable_dependencies, operator_type, string_capsulation, guard_value, cur_variable_dependencies, original_rule_additional_body_literals, new_prg_part_list, new_prg_part_set, always_add_variable_dependencies, guard_string, rule_positive_body, domain):

        max_element_head_length = 0
        skolem_constants = []

        for element_index in range(len(aggregate_dict["elements"])):

            element = aggregate_dict["elements"][element_index]

            if len(element["terms"]) > max_element_head_length:
                max_element_head_length = len(element["terms"])

        highest_integer_value = 0
        for domain_value in domain["0_terms"]:
            if CountAggregateHelper.check_string_is_int(str(domain_value)) == True:
                if int(domain_value) > highest_integer_value:
                    highest_integer_value = int(domain_value)

        for skolem_index in range(max_element_head_length):
            skolem_constants.append(str(int(highest_integer_value + 1 + skolem_index)))

        for element_index in range(len(aggregate_dict["elements"])):
            
            element = aggregate_dict["elements"][element_index]

            element_tuples = []

            for skolem_index in range(max_element_head_length):
                
                if skolem_index < len(element["terms"]):
                    element_tuples.append(element["terms"][skolem_index])
                else:
                    element_tuples.append(skolem_constants[skolem_index])


            element_dependent_variables = variable_dependencies.copy()

            for literal in always_add_variable_dependencies:
                element_dependent_variables.append(literal)

            term_string = f"{','.join(element_tuples + element_dependent_variables)}"

            if len(rule_positive_body) > 0:
                positive_body_string = ",".join([str(node) for node in rule_positive_body]) + ","
            else:
                positive_body_string = ""

            body_string = f"body_{str_type}_ag{str_id}({term_string}) :- {positive_body_string} {','.join(element['condition'])}."
            new_prg_part_set.append(body_string)


        sum = guard_value
        sum_predicate_name = f"{str_type}_ag{str_id}_{string_capsulation}"

        if operator_type in [">=",">","<=","<"]:
            if len(always_add_variable_dependencies) == 0:
                arguments = ""
                if len(variable_dependencies) == 0:
                    arguments += "(1)"
                else:
                    arguments += f"({','.join(variable_dependencies)})" 
            else:
                # Special case if guard is variable
                arguments = f"({','.join(variable_dependencies + [guard_string])})" 

            if operator_type == ">=" or operator_type == ">":
                # Monotone
                double_negated_sum_predicate = f"{sum_predicate_name}{arguments}"
                original_rule_additional_body_literals.append(double_negated_sum_predicate)
            elif operator_type == "<=" or operator_type == "<":
                # Anti-Monotone
                triple_negated_sum_predicate = f"not {sum_predicate_name}{arguments}"
                original_rule_additional_body_literals.append(triple_negated_sum_predicate)

            if operator_type == "<":
                sum = sum
            elif operator_type == ">=":
                sum = sum
            elif operator_type == ">":
                sum = sum + 1
            elif operator_type == "<=":
                sum = sum + 1
            else:
                assert(False) # Not implemented

            rules_strings = cls._sum_helper_level_2(sum_predicate_name, sum, aggregate_dict["elements"], str_type, str_id, variable_dependencies, aggregate_mode, cur_variable_dependencies, always_add_variable_dependencies, skolem_constants)

        elif operator_type == "!=":
            if len(always_add_variable_dependencies) == 0:
                arguments = ""
                if len(variable_dependencies) == 0:
                    arguments += "(1)"
                else:
                    arguments += f"({','.join(variable_dependencies)})" 
            else:
                # Special case if guard is variable
                arguments = f"({','.join(variable_dependencies + [guard_string])})" 

            double_negated_sum_predicate = f"not not_{sum_predicate_name}{arguments}"
            original_rule_additional_body_literals.append(double_negated_sum_predicate)

            #sum = int(str(list(guard_domain)[0])) # Assuming constant

            sum1 = sum
            sum2 = sum + 1

            rules_strings = cls._sum_helper_level_2(sum_predicate_name + "_1", sum1, aggregate_dict["elements"], str_type, str_id, variable_dependencies, aggregate_mode, cur_variable_dependencies, always_add_variable_dependencies, skolem_constants)
            rules_strings += cls._sum_helper_level_2(sum_predicate_name + "_2", sum2, aggregate_dict["elements"], str_type, str_id, variable_dependencies, aggregate_mode, cur_variable_dependencies, always_add_variable_dependencies, skolem_constants)

            if len(always_add_variable_dependencies) == 0:
                arguments = ""
                if len(variable_dependencies) == 0:
                    arguments += "(1)"
                else:
                    arguments += f"({','.join(variable_dependencies)})" 
            else:
                # Special case if guard is variable
                arguments = f"({','.join(variable_dependencies + [str(guard_value)])})" 

            intermediate_rule = f"not_{sum_predicate_name}{arguments} :- {sum_predicate_name}_1{arguments}, not {sum_predicate_name}_2{arguments}."

            rules_strings.append(intermediate_rule)

        elif operator_type == "=":
            if len(always_add_variable_dependencies) == 0:
                arguments = ""
                if len(variable_dependencies) == 0:
                    arguments += "(1)"
                else:
                    arguments += f"({','.join(variable_dependencies)})" 
            else:
                # Special case if guard is variable
                arguments = f"({','.join(variable_dependencies + [str(guard_string)])})" 
                    
            original_rule_additional_body_literals.append(f"{sum_predicate_name}_1{arguments}")
            original_rule_additional_body_literals.append(f"not {sum_predicate_name}_2{arguments}")

            sum1 = sum
            sum2 = sum + 1

            rules_strings = cls._sum_helper_level_2(sum_predicate_name + "_1", sum1, aggregate_dict["elements"], str_type, str_id, variable_dependencies, aggregate_mode, cur_variable_dependencies, always_add_variable_dependencies, skolem_constants)
            rules_strings += cls._sum_helper_level_2(sum_predicate_name + "_2", sum2, aggregate_dict["elements"], str_type, str_id, variable_dependencies, aggregate_mode, cur_variable_dependencies, always_add_variable_dependencies, skolem_constants)
            
        else:
            print(f"Operator Type {operator_type} currently not supported!")
            raise Exception("Not supported operator type for aggregate!")

        for rule_string in rules_strings:
            new_prg_part_list.append(rule_string)

    @classmethod
    def _sum_helper_level_2(cls, rule_head_name, sum, elements, str_type, str_id, variable_dependencies, aggregate_mode, cur_variable_dependencies, always_add_variable_dependencies, skolem_constants):

        rules_strings = []
        rules_head_strings = []

        for secondary_guard_value in range(1, sum + 1):
            tmp_rules_strings, tmp_rules_head_strings = cls._sum_generate_bodies_and_helper_bodies(rule_head_name, secondary_guard_value, sum, elements, str_type, str_id, variable_dependencies, aggregate_mode, cur_variable_dependencies, always_add_variable_dependencies, skolem_constants)

            rules_strings += tmp_rules_strings
            rules_head_strings += tmp_rules_head_strings

        return rules_strings
                
    @classmethod
    def _sum_generate_bodies_and_helper_bodies(cls, rule_head_name, current_number_of_predicate_tuples_considered, total_sum_value, elements, str_type, str_id, variable_dependencies, aggregate_mode, cur_variable_dependencies, always_add_variable_dependencies, skolem_constants):

        rules_strings = []
        rules_head_strings = []

        terms = []
        bodies = []

        for index in range(current_number_of_predicate_tuples_considered):
            tuple_variables = []

            for tuple_index in range(len(skolem_constants)):
                tuple_variables.append(f"TUPLEVARIABLE_{index}_{tuple_index}")

            terms.append(tuple_variables)
            terms_string = f"{','.join(tuple_variables + variable_dependencies + always_add_variable_dependencies)}"
            bodies.append(f"body_{str_type}_ag{str_id}({terms_string})") 

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

                    if CountAggregateHelper.check_string_is_int(first_term) == False and CountAggregateHelper.check_string_is_int(second_term) == False: 
                        term_combinations.append(f"({first_term} ^ {second_term})")

                helper_body = f"0 != {'?'.join(term_combinations)}"
                helper_bodies.append(helper_body)

        sum_up_list = [terms[index][0] for index in range(current_number_of_predicate_tuples_considered)]

        my_helper_sum = f"{total_sum_value} <= {'+'.join(sum_up_list)}"
        helper_bodies.append(my_helper_sum)

        if len(always_add_variable_dependencies) == 0:
            if len(variable_dependencies) == 0:
                rule_head_ending = "(1)"
            else:
                rule_head_ending = f"({','.join(variable_dependencies)})"
        else:
            rule_head_ending = f"({','.join(variable_dependencies + always_add_variable_dependencies)})"

        rule_head = f"{rule_head_name}{rule_head_ending}"

        rules_head_strings.append(rule_head) 
        rules_strings.append(f"{rule_head} :- {','.join(bodies + helper_bodies)}.")

        return (rules_strings, rules_head_strings)

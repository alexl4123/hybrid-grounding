
import sys

from heuristic_splitter.program_structures.rule import Rule
from heuristic_splitter.domain_inferer import DomainInferer

from cython_nagg.cython.generate_function_combination_part import generate_function_combinations_caller
from cython_nagg.cython.generate_comparison_combination_part import generate_comparison_combinations_caller
from cython_nagg.cython.generate_saturation_justification_helper_variables_part import generate_saturation_justification_helper_variables_caller


class GenerateJustifiabilityOldPartPreprocessor:

    def __init__(self, domain : DomainInferer, custom_printer, nagg_call_number = 0):

        self.domain = domain
        self.custom_printer = custom_printer

        self.nagg_call_number = nagg_call_number

        self.just_atom_string = "ujust_{nagg_call_number}"
        self.just_atom_rule_string = "ujust_{nagg_call_number}_{rule_number}_{number_head_variables}({cython_variable_identifier})"
        self.just_atom_rule_string_all_head_variables = "ujust_{nagg_call_number}_{rule_number}_0"
        self.just_atom_variable_string = "ujust_{nagg_call_number}_{rule_number}_{variable}({cython_variable_identifier})"

        self.variable_string = "VARIABLE"
        self.function_string = "FUNCTION"
        self.term_string = "TERM"
        self.binary_operation_string = "BINARY_OPERATION"
        self.comparison_string = "COMPARISON"


    def get_string_template_helper(self, argument, string_template, variable_index_dict, variable_index_value):

        if self.variable_string in argument:
            # VARIABLE (e.g., X):
            variable = argument[self.variable_string]
            if variable not in variable_index_dict:
                tmp_variable_index_value = f"%{variable_index_value}$s"
                variable_index_dict[variable] = tmp_variable_index_value
                variable_index_value += 1
            else:
                tmp_variable_index_value = variable_index_dict[variable]

            string_template += tmp_variable_index_value

        elif self.function_string in argument:
            # FUNCTION (e.g., p(X)):
            tmp_function = argument[self.function_string]

            variable_index_value, string_template = self.get_just_atom_string_template_helper(
                tmp_function, variable_index_dict=variable_index_dict,
                variable_index_value=variable_index_value, string_template=string_template)

        elif self.term_string in argument:
            # TERM (e.g., 1):
            string_template += argument[self.term_string]

        elif self.binary_operation_string in argument:
            # BINARY_OPERATION (e.g., 1 + 2)
            binary_operation = argument[self.binary_operation_string]

            variable_index_value, string_template = self.get_string_template_helper(
                binary_operation.arguments[0], variable_index_dict=variable_index_dict,
                variable_index_value=variable_index_value, string_template=string_template)

            string_template += binary_operation.operation

            variable_index_value, string_template = self.get_string_template_helper(
                binary_operation.arguments[1], variable_index_dict=variable_index_dict,
                variable_index_value=variable_index_value, string_template=string_template)

        else:
            print(f"[ERROR] - (Just Saturation Part) Unexpected argument in function arguments: {argument} in {function.name}")
            raise NotImplementedError(f"[ERROR] - (Just Saturation Part) Unexpected argument in function arguments: {argument} in {function.name}")

 
        return variable_index_value, string_template


    def get_just_atom_string_template_helper(self, function, variable_index_dict = {}, variable_index_value = 1, string_template = ""):

        string_template += function.name
        if len(function.arguments) > 0:

            string_template += "("

            index = 0
            for argument in function.arguments:

                variable_index_value, string_template, = self.get_string_template_helper(
                    argument, string_template,
                    variable_index_dict, variable_index_value)

                index += 1
                if index < len(function.arguments):
                        string_template += ","

            string_template += ")"

        return  variable_index_value, string_template


    def get_just_atom_string_template(self, function, rule_number, variable_index_dict = {}):

        if function.in_head is True:
            # For head-disentangling (for foundedness)
            clone = function.clone()
            clone.name = f"{function.name}_{self.nagg_call_number}_{rule_number}"

            _, string_template = self.get_just_atom_string_template_helper(clone,
                variable_index_dict=variable_index_dict)

            # Whenever the head does not exist it is justified (actually found).

        else:
            _, string_template = self.get_just_atom_string_template_helper(function,
                variable_index_dict=variable_index_dict)

            if function.signum > 0:
                # If literal whenever B_r^- predicate does not hold, it inches more towards justifiability
                string_template = "not " + string_template

        return variable_index_dict, string_template


    def get_just_comparison_string_template(self, comparison, rule_number):

        variable_index_dict = {}
        string_template = ""
        variable_index_value = 1

        variable_index_value, left_string_template = self.get_string_template_helper(
            comparison.arguments[0], variable_index_dict=variable_index_dict,
            string_template=string_template, variable_index_value=variable_index_value
            )

        variable_index_value, right_string_template = self.get_string_template_helper(
            comparison.arguments[1], variable_index_dict=variable_index_dict,
            string_template=string_template, variable_index_value=variable_index_value
            )

        string_template = left_string_template + comparison.operator + right_string_template

        if comparison.signum > 0:
            string_template = "not " + string_template

        return variable_index_dict, string_template

    def generate_saturation_justifiability_part(self, rule: Rule, variable_domain, rule_number, head_variables):

        head_literal = None
        for literal in rule.literals:
            if self.function_string in literal and literal[self.function_string].in_head is True:
                head_literal = literal[self.function_string]
                break

        if head_literal is None:
            print("[ERROR] - No head literal found in foundedness check!")
            raise Exception("[ERROR] - No head literal found in foundedness check!")

        # Guess variables part:
        for variable in variable_domain:
            if variable in head_variables:
                # Skip head variables:
                continue


            head_reachable_variables = []

            for head_variable in head_variables.keys():
                if rule.variable_no_head_graph.is_reachable_variables(head_variable, variable):
                    head_reachable_variables.append(head_variable)


            head_literal_variable_lookup = {}
            variables_identifiers = []
            variable_domain_lists  = []
            variable_strings = []

            variables_identifiers.append(f"%1$s")
            variable_domain_lists.append(variable_domain[variable])
            head_literal_variable_lookup[variable] = 1

            empty_variable_domain_found = False

            index = 2
            for head_variable in sorted(list(head_variables.keys())):

                if head_variable in head_reachable_variables:
                    variables_identifiers.append(f"%{index}$s")
                    variable_domain_lists.append(variable_domain[head_variable])
                    head_literal_variable_lookup[head_variable] = f"%{index - 1}$s"

                    if len(variable_domain[variable]) == 0:
                        empty_variable_domain_found = True

                    index += 1
                else:
                    # Not reachable head variables default string (anon-var, i.e., any):
                    head_literal_variable_lookup[head_variable] = "_"
 
            cur_just_atom_variable_string_instantiated = self.just_atom_variable_string.format(
                nagg_call_number = self.nagg_call_number,
                rule_number = rule_number,
                variable = variable,
                cython_variable_identifier = ",".join(variables_identifiers)
                )

            _, string_template = self.get_just_atom_string_template(head_literal, rule_number, variable_index_dict = head_literal_variable_lookup)

            guess_rule_start = "1{"
            guess_rule_choice_template = cur_just_atom_variable_string_instantiated
            guess_rule_end_instantiated = "}1:-" + string_template + ".\n"

            if empty_variable_domain_found is False: 
                generate_saturation_justification_helper_variables_caller(guess_rule_start, guess_rule_choice_template, guess_rule_end_instantiated, variable_domain_lists)
            else:
                raise NotImplementedError("EMPTY variable domain found for variable instantiation -> TODO -> Handle appropriately")


        unfoundedness_check_rules = {}

        # Standard Part:
        for literal in rule.literals:
            variable_index_dict = {}
            if self.function_string in literal:
                if literal[self.function_string].in_head is False:
                    variable_index_dict, atom_string_template = self.get_just_atom_string_template(literal[self.function_string], rule_number,
                        variable_index_dict={})
                else:
                    # Skip head literal
                    # --> Do not allow disjunctive head (for now)
                    continue

                arguments = literal["FUNCTION"].arguments
            elif "COMPARISON" in literal:
                variable_index_dict, atom_string_template = self.get_just_comparison_string_template(literal["COMPARISON"], rule_number)

                arguments = literal["COMPARISON"].arguments
            else:
                raise NotImplementedError(f"[ERROR] - Literal type not implemented {literal}")

            if len(arguments) > 0:

                reachable_head_variables = []
                reachable_head_variables_identifiers = []
                
                all_rule_variables = list(variable_index_dict.keys())
                variables_in_function = list(variable_index_dict.keys())

                for variable_in_function in variables_in_function:
                    if variable_in_function in head_variables:
                        reachable_head_variables.append(variable_in_function)
                        reachable_head_variables_identifiers.append(variable_index_dict[variable_in_function])
                        continue
                
                    for head_variable in head_variables:
                        if rule.variable_no_head_graph.is_reachable_variables(variable_in_function, head_variable) and head_variable not in all_rule_variables:
                            
                            all_rule_variables.append(head_variable)

                            reachable_head_variables.append(head_variable)
                            reachable_head_variables_identifiers.append(f"%{len(all_rule_variables)}$s")
                            variable_index_dict[head_variable] = f"%{len(all_rule_variables)}$s"

                # Instatiate the head of the rule:
                just_atom_rule_instantiated = self.just_atom_rule_string.format(
                    nagg_call_number = self.nagg_call_number,
                    rule_number = rule_number,
                    number_head_variables = "_".join(sorted(reachable_head_variables)),
                    cython_variable_identifier = ",".join(reachable_head_variables_identifiers)
                )

                unfoundedness_check_rules[",".join(sorted(reachable_head_variables))] = sorted(reachable_head_variables)

                variable_strings = []

                variable_domain_lists  = []
                for _ in range(len(all_rule_variables)):
                    variable_domain_lists.append(0)

                empty_variable_domain_found = False

                index = 0
                for variable_in_function in variables_in_function:

                    variable_identifiers = [variable_index_dict[variable_in_function]]
                    variable_domain_lists[index] = variable_domain[variable_in_function]
                    index += 1

                    if variable_in_function in head_variables:
                        continue


                    if len(variable_domain[variable_in_function]) == 0:
                        empty_variable_domain_found = True

                    for reachable_head_variable in sorted(reachable_head_variables):
                        variable_identifiers.append(variable_index_dict[reachable_head_variable])

                        
                    variable_strings.append(self.just_atom_variable_string.format(
                        nagg_call_number=self.nagg_call_number,
                        rule_number = rule_number,
                        variable = variable_in_function,
                        cython_variable_identifier = ",".join(variable_identifiers)
                    ))

                for reachable_head_variable in sorted(reachable_head_variables):
                    if reachable_head_variable in variables_in_function:
                        continue

                    variable_domain_lists[index] = variable_domain[reachable_head_variable]
                    index += 1

                    if len(variable_domain[reachable_head_variable]) == 0:
                        empty_variable_domain_found = True

                if empty_variable_domain_found is False:
                    # Everything 
                    if len(variable_strings) > 0:
                        full_string_template = just_atom_rule_instantiated + ":-" + ",".join(variable_strings) + "," + atom_string_template + ".\n"
                    else:
                        # When all variables are in the head.
                        full_string_template = just_atom_rule_instantiated + ":-" + atom_string_template + ".\n"

                    if "FUNCTION" in literal:
                        generate_function_combinations_caller(full_string_template, variable_domain_lists)
                    elif "COMPARISON" in literal:
                        comparison_operator = literal["COMPARISON"].operator
                        is_simple_comparison = literal["COMPARISON"].is_simple_comparison

                        # TODO -> Double check!
                        signum = literal["COMPARISON"].signum * (-1)

                        generate_comparison_combinations_caller(
                            full_string_template, full_string_template_reduced,
                            variable_domain_lists, comparison_operator, is_simple_comparison, signum)

                elif self.function_string in literal and literal[self.function_string].signum > 0:
                    # If domain is empty then is surely satisfied (and in B_r^+)
                    full_string_template = just_atom_rule_instantiated + "."
                    if self.custom_printer is not None:
                        self.custom_printer.custom_print(full_string_template)
                    else:
                        print(full_string_template)
            else:
                # 0-Ary atom:
                full_string_template = just_atom_rule_instantiated + ":-" +  atom_string_template + ".\n"

                unfoundedness_check_rules["_"] = []
                
               
                if self.custom_printer is not None:
                    self.custom_printer.custom_print(full_string_template)
                else:
                    print(full_string_template)


        # Print not being unfounded rules:
        variable_dict, string_head_template = self.get_just_atom_string_template(head_literal, rule_number, variable_index_dict = {})

        string_template = ":-" + "0 < #count{"


        for unfound_check_rule_index in range(len(list(unfoundedness_check_rules.keys()))):

            unfound_check_rule = list(unfoundedness_check_rules.keys())[unfound_check_rule_index]

            variable_list = unfoundedness_check_rules[unfound_check_rule]

            if len(variable_list) > 0:
                variable_strings = []
                for variable in variable_list:
                    variable_strings.append(variable_dict[variable])

                # Instatiate the head of the rule:
                just_atom_rule_instantiated = self.just_atom_rule_string.format(
                    nagg_call_number = self.nagg_call_number,
                    rule_number = rule_number,
                    number_head_variables = "_".join(sorted(variable_list)),
                    cython_variable_identifier = ",".join(variable_strings)
                )
            else:
                just_atom_rule_instantiated = self.just_atom_rule_string_all_head_variables.format(
                    nagg_call_number = self.nagg_call_number,
                    rule_number = rule_number,
                )


            string_template += "1:" + just_atom_rule_instantiated

            if unfound_check_rule_index < len(unfoundedness_check_rules) - 1:
                string_template += ";"

        string_template += "}," + string_head_template + ".\n"


        variable_domain_lists = []
        for variable in variable_dict:
            variable_domain_lists.append(variable_domain[variable])


        generate_function_combinations_caller(string_template, variable_domain_lists)
        


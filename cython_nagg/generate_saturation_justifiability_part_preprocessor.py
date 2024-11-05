
from heuristic_splitter.program_structures.rule import Rule
from heuristic_splitter.domain_inferer import DomainInferer

from cython_nagg.cython.generate_function_combination_part import generate_function_combinations_caller
from cython_nagg.cython.generate_comparison_combination_part import generate_comparison_combinations_caller



class GenerateSaturationJustifiabilityPartPreprocessor:

    def __init__(self, domain : DomainInferer, custom_printer, nagg_call_number = 0):

        self.domain = domain
        self.custom_printer = custom_printer

        self.nagg_call_number = nagg_call_number

        self.just_atom_string = "just_{nagg_call_number}"
        self.just_atom_rule_string = "just_{nagg_call_number}_{rule_number}"
        self.just_atom_literal_string = "just_{nagg_call_number}_{rule_number}_{literal_index}"
        self.just_atom_variable_string = "just_{nagg_call_number}_{rule_number}_{variable}({cython_variable_identifier})"

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
                tmp_variable_index_value = variable_index_value
                variable_index_dict[variable] = tmp_variable_index_value
                variable_index_value += 1
            else:
                tmp_variable_index_value = variable_index_dict[variable]

            string_template += f"%{tmp_variable_index_value}$s"

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


    def get_just_atom_string_template(self, function, rule_number):

        variable_index_dict = {} 
        if function.in_head is True:
            # For head-disentangling (for foundedness)
            clone = function.clone()
            clone.name = f"{function.name}_{self.nagg_call_number}_{rule_number}"

            _, string_template = self.get_just_atom_string_template_helper(clone,
                variable_index_dict=variable_index_dict)

            # Whenever the head does not exist it is justified (actually found).
            string_template = "not " + string_template

        else:
            _, string_template = self.get_just_atom_string_template_helper(function,
                variable_index_dict=variable_index_dict)

            if function.signum < 0:
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

        if comparison.signum < 0:
            string_template = "not " + string_template

        return variable_index_dict, string_template

    def generate_saturation_justifiability_part(self, rule: Rule, variable_domain, rule_number, head_variables):

        literal_index = 0

        literal_templates = []

        for literal in rule.literals:

            if self.function_string in literal:
                # FUNCTION (default)
                variable_index_dict, atom_string_template = self.get_just_atom_string_template(literal[self.function_string], rule_number)

                arguments = literal[self.function_string].arguments
            elif self.comparison_string in literal:
                # COMPARISON
                variable_index_dict, atom_string_template = self.get_just_comparison_string_template(literal[self.comparison_string], rule_number)

                arguments = literal[self.comparison_string].arguments
            else:
                raise NotImplementedError(f"[ERROR] - Literal type not implemented {literal}")

            if self.function_string in literal and literal[self.function_string].in_head is True:
                # IN HEAD FUNCTION
                full_string_template = self.just_atom_rule_string.format(
                    nagg_call_number=self.nagg_call_number,
                    rule_number = rule_number)
            else:
                literal_template = self.just_atom_literal_string.format(
                    nagg_call_number=self.nagg_call_number,
                    rule_number = rule_number,
                    literal_index = literal_index
                    )
                literal_templates.append(literal_template)
                full_string_template = literal_template

            if len(arguments) > 0:
                variable_strings = []

                variable_domain_lists  = []
                for _ in variable_index_dict.keys():
                    variable_domain_lists.append(0)

                empty_variable_domain_found = False

                for variable in variable_index_dict.keys():
                    position = variable_index_dict[variable]
                    index = position - 1
                    variable_domain_lists[index] = variable_domain[variable]

                    if len(variable_domain[variable]) == 0:
                        empty_variable_domain_found = True

                    variable_strings.append(self.just_atom_variable_string.format(
                        nagg_call_number=self.nagg_call_number,
                        rule_number = rule_number,
                        variable = variable,
                        cython_variable_identifier = f"%{position}$s"
                    ))

                if empty_variable_domain_found is False:
                    # Everything except the atom at the end
                    full_string_template_reduced = full_string_template + ":-" + ",".join(variable_strings) + ".\n"
                    # Everything 
                    full_string_template += ":-" + ",".join(variable_strings) + "," + atom_string_template + ".\n"

                    if self.function_string in literal:
                        # TODO
                        #generate_satisfiability_part_function(full_string_template, variable_domain_lists)
                        pass
                    elif self.comparison_string in literal:
                        comparison_operator = literal[self.comparison_string].operator
                        is_simple_comparison = literal[self.comparison_string].is_simple_comparison

                        signum = literal[self.comparison_string].signum

                        # TODO
                        #generate_satisfiability_part_comparison(
                        #    full_string_template, full_string_template_reduced,
                        #    variable_domain_lists, comparison_operator, is_simple_comparison, signum)
                elif literal.signum > 0:
                    # If domain is empty then is surely satisfied (and in B_r^+)
                    full_string_template += "."
                    if self.custom_printer is not None:
                        self.custom_printer.custom_print(full_string_template)
                    else:
                        print(full_string_template)
            else:
                # 0-Ary atom:
                full_string_template += ":-" +  atom_string_template + ".\n"

                if self.custom_printer is not None:
                    self.custom_printer.custom_print(full_string_template)
                else:
                    print(full_string_template)

            literal_index += 1

        for variable in head_variables:
            # Justifiability saturation only for head-variables:
            saturation_string_list = []
            for domain_value in variable_domain[variable]:

                cur_sat_variable_instantiated =  self.just_atom_variable_string.format(
                    nagg_call_number = self.nagg_call_number,
                    rule_number = rule_number,
                    variable = variable,
                    cython_variable_identifier = domain_value
                )

                saturation_string_list.append(cur_sat_variable_instantiated)

                saturation_string_2 = cur_sat_variable_instantiated +\
                    ":-" + self.just_atom_string.format(nagg_call_number=self.nagg_call_number) + "."

                if self.custom_printer is not None:
                    self.custom_printer.custom_print(saturation_string_2)
                else:
                    print(saturation_string_2)

            if len(saturation_string_list) > 0:
                saturation_string = "|".join(saturation_string_list) + "."
                if self.custom_printer is not None:
                    self.custom_printer.custom_print(saturation_string)
                else:
                    print(saturation_string)

        for variable in variable_domain:
            if variable in head_variables:
                # Skip head variables:
                continue

            just_atom_variable_string_helper = "just_h_{nagg_call_number}_{rule_number}_{variable}({cython_variable_identifier})"

            variables_identifiers = []
            variable_domain_lists  = []

            variables_identifiers.append(f"%1$$")
            variable_domain_lists.append(variable_domain[variable])

            index = 2
            for head_variable in sorted(list(head_variables.keys())):

                variables_identifiers.append(f"%{index}$")
                variable_domain_lists.append(variable_domain[head_variable])

                index += 1
 
            cur_just_atom_variable_stirng_helper_instantiated =  just_atom_variable_string_helper.format(
                nagg_call_number = self.nagg_call_number,
                rule_number = rule_number,
                variable = variable,
                cython_variable_identifier = ",".join(variables_identifiers)
            )           
            cur_just_atom_variable_stirng_instantiated = self.just_atom_variable_string.format(
                nagg_call_number = self.nagg_call_number,
                rule_number = rule_number,
                variable = variable,
                cython_variable_identifier = "%1$"
                )


            print(variable_domain_lists)
            print(cur_just_atom_variable_stirng_helper_instantiated)
            print(cur_just_atom_variable_stirng_instantiated)












                
    
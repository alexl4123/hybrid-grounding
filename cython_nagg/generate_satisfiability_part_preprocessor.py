
import os
import sys

from heuristic_splitter.program_structures.rule import Rule
from heuristic_splitter.domain_inferer import DomainInferer

from cython_nagg.cython.generate_function_combination_part import generate_function_combinations_caller
from cython_nagg.cython.generate_comparison_combination_part import generate_comparison_combinations_caller
from cython_nagg.cython.cython_helpers import printf_

class GenerateSatisfiabilityPartPreprocessor:

    def __init__(self, domain : DomainInferer, nagg_call_number = 0, full_ground = False):

        self.domain = domain

        self.nagg_call_number = nagg_call_number
        self.function_string = "FUNCTION"


        self.sat_atom_string = "sat_{nagg_call_number}"
        self.sat_atom_rule_string = "sat_{nagg_call_number}_{rule_number}"
        self.sat_atom_variable_string = "sat_{nagg_call_number}_{rule_number}_{variable}({cython_variable_identifier})"

        self.full_ground = full_ground

    def get_string_template_helper(self, argument, string_template, variable_index_dict, variable_index_value, full_ground):

        if "VARIABLE" in argument:
            variable = argument["VARIABLE"]
            if variable not in variable_index_dict:
                tmp_variable_index_value = variable_index_value
                variable_index_dict[variable] = tmp_variable_index_value
                variable_index_value += 1
            else:
                tmp_variable_index_value = variable_index_dict[variable]

            if full_ground is True:
                string_template += f"%{tmp_variable_index_value}$s"
            else:
                string_template += f"X{tmp_variable_index_value}"

        elif "FUNCTION" in argument:
            tmp_function = argument["FUNCTION"]

            variable_index_value, string_template = self.get_sat_atom_string_template_helper(
                tmp_function, full_ground, variable_index_dict=variable_index_dict,
                variable_index_value=variable_index_value, string_template=string_template)

        elif "TERM" in argument:
            string_template += argument["TERM"]

        elif "BINARY_OPERATION" in argument:
            binary_operation = argument["BINARY_OPERATION"]

            variable_index_value, string_template = self.get_string_template_helper(
                binary_operation.arguments[0], variable_index_dict=variable_index_dict,
                variable_index_value=variable_index_value, string_template=string_template,
                full_ground=full_ground)

            string_template += binary_operation.operation

            variable_index_value, string_template = self.get_string_template_helper(
                binary_operation.arguments[1], variable_index_dict=variable_index_dict,
                variable_index_value=variable_index_value, string_template=string_template,
                full_ground=full_ground)

        else:
            print(f"[ERROR] - Unexpected argument in function arguments: {argument} in {function.name}")
            raise NotImplementedError(f"[ERROR] - Unexpected argument in function arguments: {argument} in {function.name}")

 
        return variable_index_value, string_template


    def get_sat_atom_string_template_helper(self, function, full_ground, variable_index_dict = {}, variable_index_value = 1, string_template = ""):

        string_template += function.name
        if len(function.arguments) > 0:

            string_template += "("

            index = 0
            for argument in function.arguments:

                variable_index_value, string_template, = self.get_string_template_helper(
                    argument, string_template,
                    variable_index_dict, variable_index_value, full_ground)

                index += 1
                if index < len(function.arguments):
                        string_template += ","

            string_template += ")"

        return  variable_index_value, string_template


    def get_sat_atom_string_template(self, function, rule_number, full_ground):

        variable_index_dict = {} 
        if function.in_head is True:
            # For head-disentangling (for foundedness)
            clone = function.clone()
            clone.name = f"{function.name}_{self.nagg_call_number}_{rule_number}"

            _, string_template = self.get_sat_atom_string_template_helper(clone, full_ground,
                variable_index_dict=variable_index_dict)

        else:
            _, string_template = self.get_sat_atom_string_template_helper(function, full_ground,
                variable_index_dict=variable_index_dict)

            if function.signum > 0:
                # Rule is SAT whenever B_r^+ predicate does not hold.
                string_template = "not " + string_template

        return variable_index_dict, string_template


    def get_sat_comparison_string_template(self, comparison, rule_number, full_ground, variable_index_dict = {}, signum=None):

        string_template = ""
        variable_index_value = 1

        variable_index_value, left_string_template = self.get_string_template_helper(
            comparison.arguments[0], variable_index_dict=variable_index_dict,
            string_template=string_template, variable_index_value=variable_index_value, full_ground=full_ground
            )

        variable_index_value, right_string_template = self.get_string_template_helper(
            comparison.arguments[1], variable_index_dict=variable_index_dict,
            string_template=string_template, variable_index_value=variable_index_value, full_ground=full_ground
            )


        if (signum is None and comparison.signum < 0) or (signum is not None and signum < 0):
            string_template = left_string_template + comparison.operator + right_string_template
        else: # So: comparison.signum >= 0:
            # Negated one, as IDLV is unable to handle sth. like "not X1 != X2"
            string_template = left_string_template + comparison.negated_operator + right_string_template
        

        return variable_index_dict, string_template

    def generate_satisfiability_part(self, rule: Rule, variable_domain, rule_number):

        comparison_literals = []
        function_literals = []
        comparison_variable_dict = {}

        for literal in rule.literals:
            if "FUNCTION" in literal:
                function_literals.append(literal)
            elif "COMPARISON" in literal:
                comparison_literals.append(literal)

                variable_index_dict, atom_string_template = self.get_sat_comparison_string_template(literal["COMPARISON"], rule_number, self.full_ground,
                    variable_index_dict={}, signum=literal["COMPARISON"].signum)

                sorted_variable_list = sorted(list(variable_index_dict.keys()))
                comparison_variable_dict[",".join(sorted_variable_list)] = literal["COMPARISON"]

        ordered_literals = comparison_literals + function_literals

        function_associated_comparison = None
        function_associated_string_template = None

        for literal in ordered_literals:
            if "FUNCTION" in literal:
                variable_index_dict, atom_string_template = self.get_sat_atom_string_template(literal["FUNCTION"], rule_number, self.full_ground)

                sorted_variable_list = ",".join(sorted(list(variable_index_dict.keys())))
                if sorted_variable_list in comparison_variable_dict:
                    function_associated_comparison = comparison_variable_dict[sorted_variable_list]

                    # Invert Signum:
                    if function_associated_comparison.signum < 0:
                        tmp_signum = 1
                    else:
                        tmp_signum = -1

                    variable_index_dict_, function_associated_string_template = self.get_sat_comparison_string_template(function_associated_comparison, rule_number, self.full_ground,
                        variable_index_dict=variable_index_dict, signum=tmp_signum)

                    atom_string_template += "," + function_associated_string_template

                arguments = literal["FUNCTION"].arguments
            elif "COMPARISON" in literal:
                variable_index_dict, atom_string_template = self.get_sat_comparison_string_template(literal["COMPARISON"], rule_number, self.full_ground,
                    variable_index_dict={}, signum=literal["COMPARISON"].signum)

                arguments = literal["COMPARISON"].arguments
            else:
                raise NotImplementedError(f"[ERROR] - Literal type not implemented {literal}")

            full_string_template = self.sat_atom_rule_string.format(
                nagg_call_number=self.nagg_call_number,
                rule_number = rule_number)


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

                    if self.full_ground is True:
                        # Used with Cython (own print)
                        variable_name = f"%{position}$s"
                    else:
                        # Used with Gringo
                        variable_name = f"X{position}"

                    variable_strings.append(self.sat_atom_variable_string.format(
                        nagg_call_number=self.nagg_call_number,
                        rule_number = rule_number,
                        variable = variable,
                        cython_variable_identifier = variable_name
                    ))

                if empty_variable_domain_found is False:
                    # Everything except the atom at the end
                    full_string_template_reduced = full_string_template + ":-" + ",".join(variable_strings) + ".\n"
                    # Everything 
                    if len(variable_strings) > 0:
                        full_string_template += ":-" + ",".join(variable_strings) + "," + atom_string_template + ".\n"
                    else:
                        full_string_template += ":-" + atom_string_template + ".\n"

                    if "FUNCTION" in literal:
                        if self.full_ground is True:
                            generate_function_combinations_caller(full_string_template, variable_domain_lists)
                        else:
                            printf_(full_string_template.encode('ascii'))
                    elif "COMPARISON" in literal:
                        comparison_operator = literal["COMPARISON"].operator
                        is_simple_comparison = literal["COMPARISON"].is_simple_comparison

                        signum = literal["COMPARISON"].signum * (-1)

                        if self.full_ground is True:
                            generate_comparison_combinations_caller(
                                full_string_template, full_string_template_reduced,
                                variable_domain_lists, comparison_operator, is_simple_comparison, signum)
                        else:
                            printf_(full_string_template.encode('ascii'))

                elif self.function_string in literal and literal[self.function_string].signum > 0:
                    # If domain is empty then is surely satisfied (and in B_r^+)
                    full_string_template += ".\n"
                    printf_(full_string_template.encode("ascii"))
            else:
                # 0-Ary atom:
                full_string_template += ":-" +  atom_string_template + ".\n"

                full_string_template = "\n" + full_string_template
                printf_(full_string_template.encode("ascii"))

        for variable in variable_domain:
            saturation_string_list = []
            for domain_value in variable_domain[variable]:

                cur_sat_variable_instantiated =  self.sat_atom_variable_string.format(
                    nagg_call_number = self.nagg_call_number,
                    rule_number = rule_number,
                    variable = variable,
                    cython_variable_identifier = domain_value
                )

                saturation_string_list.append(cur_sat_variable_instantiated)

                saturation_string_2 = cur_sat_variable_instantiated +\
                    ":-" + self.sat_atom_string.format(nagg_call_number=self.nagg_call_number) + ".\n"

                printf_(saturation_string_2.encode("ascii"))

            if len(saturation_string_list) > 0:
                saturation_string = "|".join(saturation_string_list) + ".\n"
                printf_(saturation_string.encode("ascii"))
    
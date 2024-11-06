
import os
import sys

from heuristic_splitter.program_structures.rule import Rule
from heuristic_splitter.domain_inferer import DomainInferer

from cython_nagg.cython.generate_head_guesses_helper_part import generate_head_guesses_caller
from cython_nagg.cython.generate_function_combination_part import generate_function_combinations_caller
from cython_nagg.cython.cython_helpers import print_to_fd

class GenerateHeadGuesses:

    def __init__(self, domain : DomainInferer, nagg_call_number = 0, output_fd = sys.stdout.fileno()):


        self.output_fd = output_fd
        self.domain = domain

        self.nagg_call_number = nagg_call_number

        self.just_atom_string = "just_{nagg_call_number}"
        self.just_atom_rule_string = "just_{nagg_call_number}_{rule_number}"
        self.just_atom_literal_string = "just_{nagg_call_number}_{rule_number}_{literal_index}"
        self.just_atom_variable_string = "just_{nagg_call_number}_{rule_number}_{variable}({cython_variable_identifier})"

        self.variable_string = "VARIABLE"
        self.function_string = "FUNCTION"
        self.term_string = "TERM"
        self.binary_operation_string = "BINARY_OPERATION"


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

            variable_index_value, string_template = self.get_head_atom_template_helper(
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


    def get_head_atom_template_helper(self, function, variable_index_dict = {}, variable_index_value = 1, string_template = ""):

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


    def get_head_atom_template(self, function, rule_number, encapsulated_head_template = True):

        variable_index_dict = {} 
        if encapsulated_head_template is True:
            # For head-decoupling (for foundedness)
            clone = function.clone()
            clone.name = f"{function.name}_{self.nagg_call_number}_{rule_number}"

            _, string_template = self.get_head_atom_template_helper(clone,
                variable_index_dict=variable_index_dict)

        else:
            _, string_template = self.get_head_atom_template_helper(function,
                variable_index_dict=variable_index_dict)

        return variable_index_dict, string_template


    def generate_head_guesses_part(self, rule: Rule, variable_domain, rule_number, head_variables):

        literal_index = 0

        head_literal_template = None
        literal_templates = []

        for literal in rule.literals:

            if self.function_string in literal and literal[self.function_string].in_head is True:
                # IN HEAD FUNCTION
                variable_index_dict, atom_string_template_encapsulated = self.get_head_atom_template(literal[self.function_string],
                    rule_number, encapsulated_head_template=True)
                _, atom_string_template = self.get_head_atom_template(literal[self.function_string],
                    rule_number, encapsulated_head_template=False)

                arguments = literal[self.function_string].arguments
            else:
                # Only take into account head literals:
                continue

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

                    head_guess_rule_start = "{"
                    head_guess_rule_choice_template = atom_string_template_encapsulated
                    head_guess_rule_end = "}.\n"


                    generate_head_guesses_caller(
                        head_guess_rule_start, head_guess_rule_choice_template,
                        head_guess_rule_end, variable_domain_lists, os.dup(self.output_fd))


                    head_inference_template = atom_string_template + ":-" + atom_string_template_encapsulated  + ".\n"

                    generate_function_combinations_caller(head_inference_template, variable_domain_lists, os.dup(self.output_fd))

                else:
                    # Do nothing if there cannot exist a head!
                    pass
            else:
                # 0-Ary atom:

                head_guess = "{" + atom_string_template_encapsulated + "}."

                head_inference = atom_string_template + ":-" + atom_string_template_encapsulated + "."

                print_to_fd(os.dup(self.output_fd), head_guess.encode("ascii"))
                print_to_fd(os.dup(self.output_fd), head_inference.encode("ascii"))

            literal_index += 1

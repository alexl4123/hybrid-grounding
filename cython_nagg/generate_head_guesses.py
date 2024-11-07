
import os
import sys
from itertools import product

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

        self.tuples_size_string = "tuples_size"
        self.terms_string = "terms"
        self.terms_size_string = "terms_size"


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


    def generate_head_guesses_part(self, rule: Rule, variable_domain, rule_number, head_variables, variable_domain_including_sub_functions):

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

                self.get_head_domain(literal[self.function_string], self.domain.domain_dictionary, variable_domain_including_sub_functions)

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

    def get_head_domain_argument_helper(self, argument, function, domain_fragment, variable_domain):

        if self.variable_string in argument:
            # VARIABLE (e.g., X):

            variable = argument[self.variable_string]
            argument_domain = variable_domain[variable]

            argument_size = 0
            for key in argument_domain:
                if argument_domain[key] is True:
                    argument_size += 1

            domain_fragment.update(argument_domain)

        elif self.function_string in argument:
            # FUNCTION (e.g., p(X)):
            tmp_function = argument[self.function_string]
            
            argument_size = self.get_head_domain_helper(
                tmp_function, domain_fragment, variable_domain)

        elif self.term_string in argument:
            # TERM (e.g., 1):
            domain_fragment[argument[self.term_string]] = True

            argument_size = 1

        elif self.binary_operation_string in argument:
            # BINARY_OPERATION (e.g., 1 + 2)
            raise NotImplementedError("[ERROR] - Binary operation in head for BDG grounded rule not allowed!")
        else:
            print(f"[ERROR] - (Just Saturation Part) Unexpected argument in function arguments: {argument} in {function.name}")
            raise NotImplementedError(f"[ERROR] - (Just Saturation Part) Unexpected argument in function arguments: {argument} in {function.name}")

        return argument_size

 
    def get_head_domain_helper(self, function, domain_fragment, variable_domain):

        argument_size = 0
        if len(function.arguments) > 0:

            all_arguments = []

            if function.name in domain_fragment:
                if len(domain_fragment[function.name]) != len(function.arguments):
                    raise Exception("[ERROR] - Arity of current argument, and existing argument in domain must coincide.")

                for argument_index in range(len(function.arguments)):
                    all_arguments.append(domain_fragment[function.name][argument_index])

            else:
                for _ in range(len(function.arguments)):
                    all_arguments.append({})


            for argument_index in range(len(function.arguments)):

                argument = function.arguments[argument_index]

                self.get_head_domain_argument_helper(
                    argument, function, all_arguments[argument_index], variable_domain)


            domain_fragment[function.name] = all_arguments

            # Generate all child combinations:
            all_cleaned_arguments = []
            for argument_index in range(len(all_arguments)):
                clean_argument = []
                for argument_domain_item in all_arguments[argument_index]:
                    if all_arguments[argument_index][argument_domain_item] is True:
                        clean_argument.append(argument_domain_item)
                all_cleaned_arguments.append(clean_argument)
            combinations = product(*all_cleaned_arguments) 

            for combination in combinations:

                domain_item_string = f"{function.name}({','.join(list(combination))})"
                domain_fragment[domain_item_string] = True
                argument_size += 1
        else:
            pass

        return argument_size

    def get_head_domain(self, function, domain_dictionary, variable_domain):

        if function.name not in domain_dictionary:
            cur_dict = {
                self.tuples_size_string:1,
                self.terms_string:[],
                self.terms_size_string:[],
            }
            domain_dictionary[function.name] = cur_dict


        if len(domain_dictionary[function.name][self.terms_string]) == 0:
            for _ in range(len(function.arguments)):
                domain_dictionary[function.name][self.terms_string].append({})
                domain_dictionary[function.name][self.terms_size_string].append(0)

        tuple_size_approx = 1
        if len(function.arguments) > 0:

            for argument_index in range(len(function.arguments)):

                argument = function.arguments[argument_index]

                argument_size = self.get_head_domain_argument_helper(
                    argument, function, domain_dictionary[function.name][self.terms_string][argument_index], variable_domain)
                domain_dictionary[function.name][self.terms_size_string][argument_index] = argument_size

                tuple_size_approx *= argument_size

        # Tuple size approximation:
        domain_dictionary[function.name][self.tuples_size_string] = tuple_size_approx

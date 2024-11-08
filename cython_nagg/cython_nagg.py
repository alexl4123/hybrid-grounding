
import sys
import os

from heuristic_splitter.program_structures.rule import Rule
from heuristic_splitter.domain_inferer import DomainInferer

from cython_nagg.justifiability_type import JustifiabilityType

from cython_nagg.generate_satisfiability_part_preprocessor import GenerateSatisfiabilityPartPreprocessor
from cython_nagg.generate_saturation_justifiability_part_preprocessor import GenerateSaturationJustifiabilityPartPreprocessor
from cython_nagg.generate_head_guesses import GenerateHeadGuesses
from cython_nagg.generate_justifiability_old_part_preprocessor import GenerateJustifiabilityOldPartPreprocessor
from cython_nagg.cython.cython_helpers import printf_


class CythonNagg:

    def __init__(self, domain : DomainInferer,
        nagg_call_number = 0, justifiability_type = JustifiabilityType.UNFOUND):

        self.domain = domain

        self.nagg_call_number = nagg_call_number

        self.function_string = "FUNCTION"

        self.justifiability_type = justifiability_type

    def rewrite_rules(self, rules: [Rule]):

        rule_number = 0
        sat_atom_rules_list = []
        just_atom_rules_list = []

        satisfiability = GenerateSatisfiabilityPartPreprocessor(self.domain, self.nagg_call_number)
        if self.justifiability_type == JustifiabilityType.SATURATION:
            justifiability = GenerateSaturationJustifiabilityPartPreprocessor(self.domain, self.nagg_call_number)
        elif self.justifiability_type == JustifiabilityType.UNFOUND:
            justifiability = GenerateJustifiabilityOldPartPreprocessor(self.domain, self.nagg_call_number)

        head_guesses = GenerateHeadGuesses(self.domain, self.nagg_call_number)

        for rule in rules:

            variable_domain, head_variables, variable_domain_including_sub_functions = self.get_variable_domain(rule, self.domain.domain_dictionary)

            satisfiability.generate_satisfiability_part(rule, variable_domain, rule_number)

            sat_atom_rules_list.append(satisfiability.sat_atom_rule_string.format(
                nagg_call_number=self.nagg_call_number,
                rule_number = rule_number))

            if rule.is_constraint is False:
                head_guesses.generate_head_guesses_part(rule, variable_domain, rule_number, head_variables, variable_domain_including_sub_functions)

                justifiability.generate_justifiability_part(rule, variable_domain, rule_number, head_variables)

                if self.justifiability_type == JustifiabilityType.SATURATION:
                    just_atom_rules_list.append(justifiability.just_atom_rule_string.format(
                        nagg_call_number=self.nagg_call_number,
                        rule_number = rule_number))

            rule_number += 1

        sat_constraint = ":- not " + satisfiability.sat_atom_string.format(nagg_call_number=self.nagg_call_number) + ".\n"
        sat_rule = satisfiability.sat_atom_string.format(nagg_call_number=self.nagg_call_number) + ":-" + ",".join(sat_atom_rules_list) + ".\n"


        printf_(sat_constraint.encode("ascii"))
        printf_(sat_rule.encode("ascii"))

        if len(just_atom_rules_list) > 0: # and (implicit) justifiability_type == "SATURATION"
            just_constraint = ":- not " + justifiability.just_atom_string.format(nagg_call_number=self.nagg_call_number) + "."
            just_rule = justifiability.just_atom_string.format(nagg_call_number=self.nagg_call_number) + ":-" + ",".join(just_atom_rules_list) + "."


            printf_(just_constraint.encode("ascii"))
            printf_(just_rule.encode("ascii"))

    def recursive_intersection(self, dict1, dict2):

        return_dict = {}

        for key in dict1:

            if key in dict2 and dict1[key] == True:
                return_dict[key] = True
            elif key in dict2: # Is Function
                if len(dict1[key]) == len(dict2[key]):

                    return_dict[key] = []
                    for argument_index in range(len(dict1[key].keys())):

                        tmp_dict_1 = dict1[key][argument_index]
                        tmp_dict_2 = dict2[key][argument_index]

                        tmp_return_dict = self.recursive_intersection(tmp_dict_1, tmp_dict_2)
                        return_dict[key].append(tmp_return_dict)

        return return_dict

    def get_variable_domain_helper(self, function, domain_fragment, variable_domain,
        variable_domain_including_sub_functions=None,
        head_variable_inference = False):

        index = 0
        for argument in function.arguments:

            if head_variable_inference is False:
                if index >= len(domain_fragment):
                    # Happens for empty domain for example:
                    domain_fragment.append({})

                arg_domain_fragment = domain_fragment[index]

            if "VARIABLE" in argument:
                variable = argument["VARIABLE"]
                if variable not in variable_domain:
                    if head_variable_inference is False:
                        variable_domain[variable] = [key for key in arg_domain_fragment if arg_domain_fragment[key] == True]
                        variable_domain_including_sub_functions[variable] = arg_domain_fragment
                    else:
                        variable_domain[variable] = True
                else:
                    if head_variable_inference is False:
                        tmp_variable_domain = set([key for key in arg_domain_fragment if arg_domain_fragment[key] == True])
                        variable_domain[variable] = list(set(variable_domain[variable]).intersection(tmp_variable_domain))

                        # No recursive merge, as (correct recursive) merge would be rather expensive:
                        variable_domain_including_sub_functions[variable] = self.recursive_intersection(arg_domain_fragment, variable_domain_including_sub_functions[variable])

            elif self.function_string in argument:
                child_function = argument[self.function_string]
                if head_variable_inference is False:
                    if child_function.name in domain_fragment:
                        tmp_domain = domain_fragment[child_function.name]
                    else:
                        tmp_domain = []

                    self.get_variable_domain_helper(child_function, tmp_domain, variable_domain,
                        variable_domain_including_sub_functions=variable_domain_including_sub_functions,
                        head_variable_inference=head_variable_inference
                    )
                else:
                    self.get_variable_domain_helper(child_function, {}, variable_domain,
                        head_variable_inference=head_variable_inference
                    )
            else:
                # TODO -> Extend for e.g., comparisons, etc.
                pass

            index += 1

    
    def get_variable_domain(self, rule, domain):

        variable_domain = {}

        # Also including special sub-dicts for functions:
        variable_domain_including_sub_functions = {}
        head_variables = {}

        for literal in rule.literals:
            if self.function_string in literal:
                function = literal[self.function_string]
                if literal[self.function_string].in_head is False and literal[self.function_string].signum > 0:
                    # Only for B_r^+ domain inference occurs:
                    if function.name in domain and "terms" in domain[function.name]:
                        terms_domain = domain[function.name]["terms"]
                    elif rule.is_tight is True:
                        terms_domain = []
                    elif rule.is_tight is False:
                        # Approximate the domain
                        print("TODO -> Approx domain!")
                        raise NotImplementedError("TODO -> Approx. domain!")
                        pass

                    self.get_variable_domain_helper(function, terms_domain,
                        variable_domain, variable_domain_including_sub_functions=variable_domain_including_sub_functions,
                        head_variable_inference=False)
                elif literal[self.function_string].in_head is True:
                    # For H_r
                    self.get_variable_domain_helper(function, {},
                        head_variables, head_variable_inference=True)


        return variable_domain, head_variables, variable_domain_including_sub_functions



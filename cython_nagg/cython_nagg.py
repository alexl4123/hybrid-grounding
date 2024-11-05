
from heuristic_splitter.program_structures.rule import Rule
from heuristic_splitter.domain_inferer import DomainInferer

from cython_nagg.generate_satisfiability_part_preprocessor import GenerateSatisfiabilityPartPreprocessor
from cython_nagg.generate_saturation_justifiability_part_preprocessor import GenerateSaturationJustifiabilityPartPreprocessor
from cython_nagg.generate_head_guesses import GenerateHeadGuesses

class CythonNagg:

    def __init__(self, domain : DomainInferer, custom_printer, nagg_call_number = 0):

        self.domain = domain
        self.custom_printer = custom_printer

        self.nagg_call_number = nagg_call_number

        self.function_string = "FUNCTION"

    def rewrite_rules(self, rules: [Rule]):

        rule_number = 0
        sat_atom_rules_list = []
        just_atom_rules_list = []


        satisfiability = GenerateSatisfiabilityPartPreprocessor(self.domain, self.custom_printer, self.nagg_call_number)
        justifiability = GenerateSaturationJustifiabilityPartPreprocessor(self.domain, self.custom_printer, self.nagg_call_number)
        head_guesses = GenerateHeadGuesses(self.domain, self.custom_printer, self.nagg_call_number)

        for rule in rules:

            variable_domain, head_variables = self.get_variable_domain(rule, self.domain.domain_dictionary)

            satisfiability.generate_satisfiability_part(rule, variable_domain, rule_number)

            sat_atom_rules_list.append(satisfiability.sat_atom_rule_string.format(
                nagg_call_number=self.nagg_call_number,
                rule_number = rule_number))

            if rule.is_constraint is False:
                head_guesses.generate_head_guesses_part(rule, variable_domain, rule_number, head_variables)

                justifiability.generate_saturation_justifiability_part(rule, variable_domain, rule_number, head_variables)
                just_atom_rules_list.append(justifiability.just_atom_rule_string.format(
                    nagg_call_number=self.nagg_call_number,
                    rule_number = rule_number))

            rule_number += 1

        sat_constraint = ":- not " + satisfiability.sat_atom_string.format(nagg_call_number=self.nagg_call_number) + "."
        sat_rule = satisfiability.sat_atom_string.format(nagg_call_number=self.nagg_call_number) + ":-" + ",".join(sat_atom_rules_list) + "."

        if self.custom_printer is not None:
            self.custom_printer.custom_print(sat_constraint)
            self.custom_printer.custom_print(sat_rule)
        else:
            print(sat_constraint)
            print(sat_rule)


        if len(just_atom_rules_list) > 0:
            just_constraint = ":- not " + justifiability.just_atom_string.format(nagg_call_number=self.nagg_call_number) + "."
            just_rule = justifiability.just_atom_string.format(nagg_call_number=self.nagg_call_number) + ":-" + ",".join(just_atom_rules_list) + "."

            if self.custom_printer is not None:
                self.custom_printer.custom_print(just_constraint)
                self.custom_printer.custom_print(just_rule)
            else:
                print(just_constraint)
                print(just_rule)







    def get_variable_domain_helper(self, function, domain_fragment, variable_domain, head_variable_inference = False):

        index = 0
        for argument in function.arguments:

            if head_variable_inference is False:
                arg_domain_fragment = domain_fragment[index]

            if "VARIABLE" in argument:
                variable = argument["VARIABLE"]
                if variable not in variable_domain:
                    if head_variable_inference is False:
                        variable_domain[variable] = [key for key in arg_domain_fragment if arg_domain_fragment[key] == True]
                    else:
                        variable_domain[variable] = True
                else:
                    if head_variable_inference is False:
                        tmp_variable_domain = set([key for key in arg_domain_fragment if arg_domain_fragment[key] == True])
                        variable_domain[variable] = list(set(variable_domain[variable]).intersection(tmp_variable_domain))

            elif self.function_string in argument:
                child_function = argument[self.function_string]
                self.get_variable_domain_helper(child_function, domain_fragment[child_function.name], variable_domain)
            else:
                # TODO -> Extend for e.g., comparisons, etc.
                pass

            index += 1

    
    def get_variable_domain(self, rule, domain):

        variable_domain = {}
        head_variables = {}

        for literal in rule.literals:
            if self.function_string in literal:
                function = literal[self.function_string]
                if literal[self.function_string].in_head is False and literal[self.function_string].signum > 0:
                    # Only for B_r^+ domain inference occurs:
                    self.get_variable_domain_helper(function, domain[function.name]["terms"],
                        variable_domain, head_variable_inference=False)
                elif literal[self.function_string].in_head is True:
                    # For H_r
                    self.get_variable_domain_helper(function, {},
                        head_variables, head_variable_inference=True)


        return variable_domain, head_variables



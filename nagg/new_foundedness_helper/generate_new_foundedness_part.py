# pylint: disable=R0913,R1721
"""
Module for ensuring new foundedness.
"""
import itertools
import re

from ..comparison_tools import ComparisonTools
from .helper_part import HelperPart


class GenerateNewFoundednessPart:
    """
    Class for ensuring foundedness.
    """

    def __init__(
        self,
        rule_head,
        current_rule_position,
        custom_printer,
        domain_lookup_dict,
        safe_variables_rules,
        rule_variables,
        rule_comparisons,
        rule_predicate_functions,
        rule_literals_signums,
        current_rule,
        strongly_connected_components,
        ground_entire_output,
        unfounded_rules,
        cyclic_strategy,
        strongly_connected_components_heads,
        program_rules,
        additional_unfounded_rules,
        rule_variables_predicates,
    ):
        self.rule_head = rule_head
        self.current_rule_position = current_rule_position
        self.printer = custom_printer
        self.domain_lookup_dict = domain_lookup_dict
        self.safe_variables_rules = safe_variables_rules
        self.rule_variables = rule_variables
        self.rule_comparisons = rule_comparisons
        self.rule_literals = rule_predicate_functions
        self.rule_literals_signums = rule_literals_signums
        self.current_rule = current_rule
        self.rule_strongly_restricted_components = strongly_connected_components
        self.ground_entire_output = ground_entire_output
        self.unfounded_rules = unfounded_rules
        self.cyclic_strategy = cyclic_strategy
        self.rule_strongly_restricted_components_heads = (
            strongly_connected_components_heads
        )
        self.program_rules = program_rules
        self.rule_variables_predicates = rule_variables_predicates

        self.additional_unfounded_rules = additional_unfounded_rules

    def generate_foundedness_part(self):
        """
        Generates the FOUNDEDNESS-part.
        """
        # head
        h_args_len = len(self.rule_head.arguments)
        h_args = re.sub(r"^.*?\(", "", str(self.rule_head))[:-1].split(
            ","
        )  # all arguments (incl. duplicates / terms)
        h_args_nd = list(
            dict.fromkeys(h_args)
        )  # arguments (without duplicates / incl. terms)
        head_vars = list(
            dict.fromkeys([a for a in h_args if a in self.rule_variables])
        )  # which have to be grounded per combination


        self._generate_sat_variable_possibilities(head_vars)

        covered_subsets, current_function_symbol_index, founded_auxiliary_rule_body = self._generate_sat_comparisons(founded_auxiliary_rule_body=[], current_function_symbol_index=-1)

        founded_auxiliary_rule_body = self._generate_sat_functions(self.rule_head, covered_subsets, current_function_symbol_index, founded_auxiliary_rule_body)

        ######################################################################
        # Add rule found_r <- found_p1, ..., found_pn, not found_p(n+1), ... #
        ######################################################################

        founded_auxiliary_rule_body = list(set(founded_auxiliary_rule_body))

        if len(founded_auxiliary_rule_body) > 0:
            body_string = ",".join(founded_auxiliary_rule_body)
        else:
            body_string = ""
        
        rule_atom = f"found_r{self.current_rule_position}"

        self.printer.custom_print(
            f"{rule_atom} :- {body_string}."
        )

        self.unfounded_rules[rule_atom] = True




    def _generate_sat_variable_possibilities(self, head_variables):

        head_variable_literals = []
        # MOD
        # domaining per rule variable
        for head_variable in head_variables:
            values = HelperPart.get_domain_values_from_rule_variable(
                self.current_rule_position,
                head_variable,
                self.domain_lookup_dict,
                self.safe_variables_rules,
                self.rule_variables_predicates,
            )

            disjunction = ""

            for value in values:
                disjunction += f"f{self.current_rule_position}_{head_variable}({value}) | "

            if len(disjunction) > 0:
                disjunction = disjunction[:-3] + "."
                self.printer.custom_print(disjunction)

            head_variable_name = f"f{self.current_rule_position}_{head_variable}"

            for value in values:
                self.printer.custom_print(
                    f"{head_variable_name}({value}) :- found."
                )

            head_variable_with_variable = f"{head_variable_name}({head_variable})"

            head_variable_literals.append(head_variable_with_variable)

        if not self.ground_entire_output:
            self.generate_variable_possibilities_not_ground(head_variables, head_variable_literals)
        else:
            self.generate_variable_possibilities_ground(head_variables)

        
    def generate_variable_possibilities_ground(self, head_variables): 

        other_variables = [v for v in self.rule_variables if v not in head_variables] 

        variable_index_lookup = {}
        index_to_variable_lookup = {}
        dom_list = []

        index = 0
        for variable in head_variables:
            domain = HelperPart.get_domain_values_from_rule_variable(
                str(self.current_rule_position),
                variable,
                self.domain_lookup_dict,
                self.safe_variables_rules,
                self.rule_variables_predicates,
            )

            dom_list.append(domain)

            variable_index_lookup[variable] = index
            index_to_variable_lookup[index] = variable

            index += 1

        combinations = [p for p in itertools.product(*dom_list)]

        for combination in combinations:

            head_variable_literals = []
            head_instantiated_variables = []

            for combination_index in range(len(combination)):
                head_variable_literals.append(f"f{self.current_rule_position}_{index_to_variable_lookup[combination_index]}({combination[combination_index]})")
                head_instantiated_variables.append(combination[combination_index])

            if len(head_instantiated_variables) > 0:
                head_variable_string = "," + ",".join(head_instantiated_variables)
                head_literals_instantiated = " :- " + ",".join(head_variable_literals)
            else:
                head_variable_string = ""
                head_literals_instantiated = ""

            
            for other_variable in other_variables:

                values = HelperPart.get_domain_values_from_rule_variable(
                    self.current_rule_position,
                    other_variable,
                    self.domain_lookup_dict,
                    self.safe_variables_rules,
                    self.rule_variables_predicates,
                )
                
                parsed_variables = []
                for value in values:
                    parsed_variables.append(f"f'{self.current_rule_position}_{other_variable}({value}{head_variable_string})")

                self.printer.custom_print( 
                    "1{" + ";".join(parsed_variables) + "}1 " + head_literals_instantiated + "."
                )


        if len(head_variables) > 0:
            head_variable_empty_string = "," + ",".join(["_" for head_variable in head_variables])
        else:
            head_variable_empty_string = ""

        for other_variable in other_variables:

            values = HelperPart.get_domain_values_from_rule_variable(
                self.current_rule_position,
                other_variable,
                self.domain_lookup_dict,
                self.safe_variables_rules,
                self.rule_variables_predicates,
            )
            
            for value in values:
                self.printer.custom_print(
                    f"f{self.current_rule_position}_{other_variable}({value}) :- f'{self.current_rule_position}_{other_variable}({value}{head_variable_empty_string})."
                )

    def generate_variable_possibilities_not_ground(self, head_variables, head_variable_literals): 

        if len(head_variables) > 0:
            head_variable_string = "," + ",".join(head_variables)
            head_variable_empty_string = "," + ",".join(["_" for head_variable in head_variables])
        else:
            head_variable_string = ""
            head_variable_empty_string = ""


        other_variables = [v for v in self.rule_variables if v not in head_variables] 
        for variable in other_variables:  # other variables
            values = HelperPart.get_domain_values_from_rule_variable(
                self.current_rule_position,
                variable,
                self.domain_lookup_dict,
                self.safe_variables_rules,
                self.rule_variables_predicates,
            )
            
            not_head_variable_name = f"f{self.current_rule_position}_{variable}"

            parsed_variables = []
            for value in values:
                parsed_variables.append(f"f'{self.current_rule_position}_{variable}({value}{head_variable_string})")

            self.printer.custom_print( 
                "1{" + ";".join(parsed_variables) + "}1 :- " + ",".join(head_variable_literals) + "."
            )


            self.printer.custom_print(
                f"f{self.current_rule_position}_{variable}({variable}) :- f'{self.current_rule_position}_{variable}({variable}{head_variable_empty_string})."
            )




    def _generate_sat_comparisons(self,  current_function_symbol_index = -1, founded_auxiliary_rule_body = []):

        covered_subsets = {}  # reduce FOUND rules when compare-operators are pre-checked
        for f in self.rule_comparisons:
            current_function_symbol_index += 1
            # Not (yet) implemented for foundedness check

            left = f.term
            assert len(f.guards) <= 1
            right = f.guards[0].term
            comparison_operator = f.guards[0].comparison

            symbolic_arguments = ComparisonTools.get_arguments_from_operation(
                left
            ) + ComparisonTools.get_arguments_from_operation(right)

            arguments = []
            for symbolic_argument in symbolic_arguments:
                arguments.append(str(symbolic_argument))

            arguments_list = list(
                dict.fromkeys(arguments)
            )  # arguments (without duplicates / incl. terms)
            variables_list = list(
                dict.fromkeys([a for a in arguments if a in self.rule_variables])
            )  # which have to be grounded per combination
            dom_list = []
            for variable in variables_list:
                if (
                    str(self.current_rule_position) in self.safe_variables_rules
                    and variable
                    in self.safe_variables_rules[str(self.current_rule_position)]
                ):
                    domain = HelperPart.get_domain_values_from_rule_variable(
                        str(self.current_rule_position),
                        variable,
                        self.domain_lookup_dict,
                        self.safe_variables_rules,
                        self.rule_variables_predicates,
                    )

                    dom_list.append(domain)
                else:
                    dom_list.append(self.domain_lookup_dict["0_terms"])

            combinations = [p for p in itertools.product(*dom_list)]

            for c in combinations:
                variable_assignments = {}

                for variable_index in range(len(variables_list)):
                    variable = variables_list[variable_index]
                    value = c[variable_index]

                    variable_assignments[variable] = value

                interpretation_list = []
                for variable in arguments_list:
                    if variable in variables_list:
                        interpretation_list.append(
                            f"f{self.current_rule_position}_{variable}({variable_assignments[variable]})"
                        )

                left_eval = ComparisonTools.evaluate_operation(
                    left, variable_assignments
                )
                right_eval = ComparisonTools.evaluate_operation(
                    right, variable_assignments
                )

                sint = HelperPart.ignore_exception(ValueError)(int)
                left_eval = sint(left_eval)
                right_eval = sint(right_eval)

                safe_checks = left_eval is not None and right_eval is not None
                evaluation = safe_checks and ComparisonTools.compare_terms(
                    comparison_operator, int(left_eval), int(right_eval)
                )

                if not safe_checks or evaluation:
                    """
                    left_instantiation = ComparisonTools.instantiate_operation(
                        left, variable_assignments
                    )
                    right_instantiation = ComparisonTools.instantiate_operation(
                        right, variable_assignments
                    )
                    ComparisonTools.comparison_handlings(
                        comparison_operator, left_instantiation, right_instantiation
                    )
                    """
                    interpretation = f"{','.join(interpretation_list)}"

                    sat_atom = f"found_r{self.current_rule_position}{current_function_symbol_index}"

                    self.printer.custom_print(f"{sat_atom} :- {interpretation}.")

                    if sat_atom not in covered_subsets:
                        covered_subsets[sat_atom] = []

                    covered_subsets[sat_atom].append(interpretation_list)

                    founded_auxiliary_rule_body.append(f"{sat_atom}")

        return covered_subsets, current_function_symbol_index, founded_auxiliary_rule_body

    def _generate_sat_functions(self, head, covered_subsets, current_function_symbol_index = -1, founded_auxiliary_rule_body = []):

        for current_function_symbol in self.rule_literals:
            current_function_symbol_index += 1

            args_len = len(current_function_symbol.arguments)
            if args_len == 0:
                # This should be for an atom (not a predicate!)
                if self.rule_literals_signums[
                        self.rule_literals.index(current_function_symbol)
                    ]:
                    signum_string = "not"
                    sat_atom = f"found_r{self.current_rule_position}{current_function_symbol_index}"
                    current_function_symbol_string = f"{str(current_function_symbol)}"
                elif (
                    current_function_symbol is head
                ):
                    signum_string = "not"
                    sat_atom = f"found_r{self.current_rule_position}"

                    current_function_symbol_string = f"{str(current_function_symbol)}{self.current_rule_position}"
                else:
                    signum_string = ""
                    sat_atom = f"found_r{self.current_rule_position}{current_function_symbol_index}"
                    current_function_symbol_string = f"{str(current_function_symbol)}"


                self.printer.custom_print(
                    f"{sat_atom} :- {signum_string} {current_function_symbol_string}."
                )

                if current_function_symbol is not head:
                    founded_auxiliary_rule_body.append(f"{sat_atom}")
                continue

            arguments = re.sub(r"^.*?\(", "", str(current_function_symbol))[:-1].split(
                ","
            )  # all arguments (incl. duplicates / terms)
            current_function_variables = list(
                dict.fromkeys([a for a in arguments if a in self.rule_variables])
            )  # which have to be grounded per combination

            variable_associations = {}
            dom_list = []
            index = 0
            for variable in current_function_variables:
                values = HelperPart.get_domain_values_from_rule_variable(
                    self.current_rule_position,
                    variable,
                    self.domain_lookup_dict,
                    self.safe_variables_rules,
                    self.rule_variables_predicates,
                )
                dom_list.append(values)
                variable_associations[variable] = index
                index += 1

            combinations = [p for p in itertools.product(*dom_list)]

            for current_combination in combinations:
                current_function_arguments_string = ""

                if current_function_symbol is head:
                    sat_atom = f"found_r{self.current_rule_position}"
                else:
                    sat_atom = f"found_r{self.current_rule_position}{current_function_symbol_index}"

                (
                    sat_body_list,
                    sat_body_dict,
                    current_function_arguments_string,
                ) = self._generate_body_list(
                    arguments,
                    variable_associations,
                    current_combination,
                    current_function_arguments_string,
                )

                if (
                    self._check_covered_subsets(
                        sat_atom, covered_subsets, sat_body_dict
                    )
                    is True
                ):
                    continue

                self._print_sat_function_guess(
                    head,
                    current_function_symbol,
                    current_function_arguments_string,
                    sat_atom,
                    sat_body_list,
                )

            if current_function_symbol is not head:
                founded_auxiliary_rule_body.append(f"{sat_atom}")



        return founded_auxiliary_rule_body                

    def _check_covered_subsets(self, sat_atom, covered_subsets, sat_body_dict):
        if sat_atom in covered_subsets:  # Check for covered subsets
            possible_subsets = covered_subsets[sat_atom]
            found = False

            for possible_subset in possible_subsets:
                temp_found = True
                for possible_subset_predicate in possible_subset:
                    if possible_subset_predicate not in sat_body_dict:
                        temp_found = False
                        break

                if temp_found is True:
                    found = True
                    break

            if found is True:
                return True

        return False

    def _print_sat_function_guess(
        self,
        head,
        current_function_symbol,
        current_function_arguments_string,
        sat_atom,
        sat_body_list,
    ):
        if current_function_symbol is head:
            current_function_name = f"{current_function_symbol.name}{self.current_rule_position}"
        else:
            current_function_name = f"{current_function_symbol.name}"

        if len(current_function_arguments_string) > 0:
            current_function_string_representation = (
                f"{current_function_name}"
                + f"({current_function_arguments_string[:-1]})"
            )
        else:
            current_function_string_representation = f"{current_function_name}"

        if self.rule_literals_signums[
                self.rule_literals.index(current_function_symbol)
            ]:
            sat_predicate = f"not {current_function_string_representation}"
        elif (
            current_function_symbol is head
        ):
            sat_predicate = f"not {current_function_string_representation}"
        else:
            sat_predicate = f"{current_function_string_representation}"

        if len(sat_body_list) > 0:
            body_interpretation = ",".join(sat_body_list) + ","
        else:
            body_interpretation = ""

        self.printer.custom_print(
            f"{sat_atom} :- {body_interpretation}{sat_predicate}."
        )

    def _generate_body_list(
        self,
        arguments,
        variable_associations,
        current_combination,
        current_function_arguments_string,
    ):
        sat_body_list = []
        sat_body_dict = {}
        for argument in arguments:
            if argument in self.rule_variables:
                variable_index_combination = variable_associations[argument]
                body_sat_predicate = (
                    f"f{self.current_rule_position}_{argument}"
                    + f"({current_combination[variable_index_combination]})"
                )
                sat_body_list.append(body_sat_predicate)
                sat_body_dict[body_sat_predicate] = body_sat_predicate

                current_function_arguments_string += (
                    f"{current_combination[variable_index_combination]},"
                )
            else:
                current_function_arguments_string += f"{argument},"

        sat_body_list = list(set(sat_body_list))
        return sat_body_list, sat_body_dict, current_function_arguments_string

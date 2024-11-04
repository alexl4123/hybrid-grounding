
from heuristic_splitter.program_structures.rule import Rule
from heuristic_splitter.domain_inferer import DomainInferer

from cython_nagg.generate_satisfiability_part import generate_satisfiability_part_function, generate_satisfiability_part_comparison



class GenerateSatisfiabilityPartPreprocessor:

    def __init__(self, domain : DomainInferer, custom_printer, nagg_call_number = 0):

        self.domain = domain
        self.custom_printer = custom_printer

        self.nagg_call_number = nagg_call_number


        self.sat_atom_string = "sat_{nagg_call_number}"
        self.sat_atom_rule_string = "sat_{nagg_call_number}_{rule_number}"
        self.sat_atom_variable_string = "sat_{nagg_call_number}_{rule_number}_{variable}({cython_variable_identifier})"


    def get_string_template_helper(self, argument, string_template, variable_index_dict, variable_index_value):

        if "VARIABLE" in argument:
            variable = argument["VARIABLE"]
            if variable not in variable_index_dict:
                tmp_variable_index_value = variable_index_value
                variable_index_dict[variable] = tmp_variable_index_value
                variable_index_value += 1
            else:
                tmp_variable_index_value = variable_index_dict[variable]

            string_template += f"%{tmp_variable_index_value}$s"

        elif "FUNCTION" in argument:
            tmp_function = argument["FUNCTION"]

            variable_index_value, string_template = self.get_sat_atom_string_template_helper(
                tmp_function, variable_index_dict=variable_index_dict,
                variable_index_value=variable_index_value, string_template=string_template)

        elif "TERM" in argument:
            string_template += argument["TERM"]

        elif "BINARY_OPERATION" in argument:
            binary_operation = argument["BINARY_OPERATION"]

            variable_index_value, string_template = self.get_string_template_helper(
                binary_operation.arguments[0], variable_index_dict=variable_index_dict,
                variable_index_value=variable_index_value, string_template=string_template)

            string_template += binary_operation.operation

            variable_index_value, string_template = self.get_string_template_helper(
                binary_operation.arguments[1], variable_index_dict=variable_index_dict,
                variable_index_value=variable_index_value, string_template=string_template)

        else:
            print(f"[ERROR] - Unexpected argument in function arguments: {argument} in {function.name}")
            raise NotImplementedError(f"[ERROR] - Unexpected argument in function arguments: {argument} in {function.name}")

 
        return variable_index_value, string_template


    def get_sat_atom_string_template_helper(self, function, variable_index_dict = {}, variable_index_value = 1, string_template = ""):

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


    def get_sat_atom_string_template(self, function, rule_number):

        variable_index_dict = {} 
        if function.in_head is True:
            # For head-disentangling (for foundedness)
            clone = function.clone()
            clone.name = f"{function.name}_{self.nagg_call_number}_{rule_number}"

            _, string_template = self.get_sat_atom_string_template_helper(clone,
                variable_index_dict=variable_index_dict)

        else:
            _, string_template = self.get_sat_atom_string_template_helper(function,
                variable_index_dict=variable_index_dict)

            if function.signum > 0:
                # Rule is SAT whenever B_r^+ predicate does not hold.
                string_template = "not " + string_template

        return variable_index_dict, string_template


    def get_sat_comparison_string_template(self, comparison, rule_number):

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

        return variable_index_dict, string_template

    def generate_satisfiability_part(self, rule: Rule, variable_domain, rule_number):

        for literal in rule.literals:
            if "FUNCTION" in literal:
                variable_index_dict, atom_string_template = self.get_sat_atom_string_template(literal["FUNCTION"], rule_number)

                arguments = literal["FUNCTION"].arguments
            elif "COMPARISON" in literal:
                variable_index_dict, atom_string_template = self.get_sat_comparison_string_template(literal["COMPARISON"], rule_number)

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

                    variable_strings.append(self.sat_atom_variable_string.format(
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

                    if "FUNCTION" in literal:
                        generate_satisfiability_part_function(full_string_template, variable_domain_lists)
                    elif "COMPARISON" in literal:
                        comparison_operator = literal["COMPARISON"].operator
                        is_simple_comparison = literal["COMPARISON"].is_simple_comparison

                        signum = literal["COMPARISON"].signum

                        generate_satisfiability_part_comparison(
                            full_string_template, full_string_template_reduced,
                            variable_domain_lists, comparison_operator, is_simple_comparison, signum)
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
                    ":-" + self.sat_atom_string.format(nagg_call_number=self.nagg_call_number) + "."

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
    
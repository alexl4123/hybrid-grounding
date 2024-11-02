
from heuristic_splitter.rule import Rule
from heuristic_splitter.domain_inferer import DomainInferer
from cython_nagg.generate_satisfiability_part import generate_satisfiability_part_function

class CythonNagg:

    def __init__(self, domain : DomainInferer, custom_printer, nagg_call_number = 0):

        self.domain = domain
        self.custom_printer = custom_printer

        self.nagg_call_number = nagg_call_number

        self.sat_atom_string = "sat_{nagg_call_number}"
        self.sat_atom_rule_string = "sat_{nagg_call_number}_{rule_number}"
        self.sat_atom_variable_string = "sat_{nagg_call_number}_{rule_number}_{variable}({cython_variable_identifier})"

    def get_variable_domain_helper(self, function, domain_fragment, variable_domain):

        index = 0
        for argument in function.arguments:

            arg_domain_fragment = domain_fragment[index]

            if "VARIABLE" in argument:
                variable = argument["VARIABLE"]
                if variable not in variable_domain:
                    variable_domain[variable] = [key for key in arg_domain_fragment if arg_domain_fragment[key] == True]
                else:
                    tmp_variable_domain = set([key for key in arg_domain_fragment if arg_domain_fragment[key] == True])
                    variable_domain[variable] = list(set(variable_domain[variable]).intersection(tmp_variable_domain))

            elif "FUNCTION" in argument:
                child_function = argument["FUNCTION"]
                self.get_variable_domain_helper(child_function, domain_fragment[child_function.name], variable_domain)
            else:
                # TODO -> Extend for e.g., comparisons, etc.
                pass

            index += 1

    
    def get_variable_domain(self, rule, domain):

        variable_domain = {}

        for function in rule.functions:
            if function.in_head is False and function.signum > 0:
                # Only for B_r^+ domain inference occurs:
                self.get_variable_domain_helper(function, domain[function.name]["terms"], variable_domain)

        return variable_domain


    def get_string_template_helper(self, function, string_template, variable_index_dict, variable_index_value):

        string_template += function.name
        if len(function.arguments) > 0:

            string_template += "("

            index = 0
            for argument in function.arguments:
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

                    string_template += tmp_function.name

                    variable_index_value, string_template = self.get_string_template_helper(
                        tmp_function, string_template,
                        variable_index_dict, variable_index_value)

                elif "TERM" in argument:
                    string_template += argument["TERM"]

                else:
                    print(f"[ERROR] - Unexpected argument in function arguments: {argument} in {function.name}")
                    raise NotImplementedError(f"[ERROR] - Unexpected argument in function arguments: {argument} in {function.name}")

                index += 1
                if index < len(function.arguments):
                    string_template += ","
 
            string_template += ")"

        return variable_index_value, string_template


    def get_string_template(self, function):

        string_template = ""
        variable_index_dict = {}

        variable_index_value = 1

        # TODO -> Check if it is function -> Do something else for comparison  
        final_index_value, string_template = self.get_string_template_helper(
            function, string_template,
            variable_index_dict, variable_index_value)


        return variable_index_dict, string_template


    def get_sat_atom_string_template(self, function, rule_number):
        
        if function.in_head is True:
            # For head-disentangling (for foundedness)
            clone = function.clone()
            clone.name = f"{function.name}_{self.nagg_call_number}_{rule_number}"

            variable_index_dict, string_template = self.get_string_template(clone)

        else:
            variable_index_dict, string_template = self.get_string_template(function)

            if function.signum > 0:
                # Rule is SAT whenever B_r^+ predicate does not hold.
                string_template = "not " + string_template

        return variable_index_dict, string_template


    def generate_satisfiability_part_for_function(self, function, rule, variable_domain, rule_number):

        variable_index_dict, atom_string_template = self.get_sat_atom_string_template(function, rule_number)

        full_string_template = self.sat_atom_rule_string.format(
            nagg_call_number=self.nagg_call_number,
            rule_number = rule_number)


        if len(function.arguments) > 0:
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
                full_string_template += ":-" + ",".join(variable_strings) + "," + atom_string_template + ".\n"
                generate_satisfiability_part_function(full_string_template, variable_domain_lists)
            elif function.signum > 0:
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




    def generate_satisfiability_part(self, rule: Rule, variable_domain, rule_number):

        for function in rule.functions:
            self.generate_satisfiability_part_for_function(function, rule, variable_domain, rule_number)

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
    
    def rewrite_rules(self, rules: [Rule]):

        # TODO -> Implement variable inference and domain inference for SAT part!
        # --> Need to take nested functions into account!

        rule_number = 0
        sat_atom_rules_list = []
        for rule in rules:
            if rule.is_constraint is False:
                raise NotImplementedError("Foundedness and Head-Guess not (yet) implemented")

            variable_domain = self.get_variable_domain(rule, self.domain.domain_dictionary)
            self.generate_satisfiability_part(rule, variable_domain, rule_number)

            sat_atom_rules_list.append(self.sat_atom_rule_string.format(
                nagg_call_number=self.nagg_call_number,
                rule_number = rule_number))

            rule_number += 1

        sat_constraint = ":- not " + self.sat_atom_string.format(nagg_call_number=self.nagg_call_number) + "."
        sat_rule = self.sat_atom_string.format(nagg_call_number=self.nagg_call_number) + ":-" + ",".join(sat_atom_rules_list) + "."

        if self.custom_printer is not None:
            self.custom_printer.custom_print(sat_constraint)
            self.custom_printer.custom_print(sat_rule)
        else:
            print(sat_constraint)
            print(sat_rule)


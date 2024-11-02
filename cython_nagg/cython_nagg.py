
from heuristic_splitter.rule import Rule
from heuristic_splitter.domain_inferer import DomainInferer
from cython_nagg.generate_satisfiability_part import generate_satisfiability_part_function

class CythonNagg:

    def __init__(self, domain : DomainInferer, custom_printer):

        self.domain = domain
        self.custom_printer = custom_printer


    def generate_satisfiability_part_for_function(self, function, rule, domain):

        variable_domain_lists = []
        variables_in_function = {}

        atom_string_template = function.name

        terms_list = domain[function.name]["terms"]



        if len(function.arguments) > 0:

            variable_strings = []

            atom_string_template += "("

            variable_index = 1

            for argument_index in range(len(function.arguments)):

                argument = function.arguments[argument_index]

                if "VARIABLE" in argument:
                    variable = argument["VARIABLE"]
                    if variable not in variables_in_function:
                        variables_in_function[variable] = variable_index
                        variable_strings.append(f"sat_var_{variable}(%{variable_index}$s)")
                        atom_string_template += f"%{variable_index}$s"
                        
                        domain_list = list(terms_list[variable_index - 1].keys())
                        variable_domain_lists.append(domain_list)
                    else:
                        tmp_variable_index = variables_in_function[variable]
                        atom_string_template += f"%{tmp_variable_index}$s"

                        # If e.g., p(X,Y,X), then do intersection between variable domain X
                        # TODO -> Do this later rule wide

                        domain_list = list(terms_list[tmp_variable_index - 1].keys())
                        variable_domain_lists[tmp_variable_index - 1] = list(set(domain_list).intersection(set(terms_list[variable_index - 1])))

                    variable_index += 1
                else:
                    atom_string_template += f"%{variable_index}$s"

                if argument_index < len(function.arguments) - 1:
                    atom_string_template += ","

            atom_string_template += ")"

            string_template = f"sat :- {','.join(variable_strings)}, {atom_string_template}.\n"

            generate_satisfiability_part_function(function, rule, domain, string_template, variable_domain_lists)

        else:
            print("[ERROR] - Currently sat part for atom (0-ary-pred.) not implemented.")


    def generate_satisfiability_part(self, rule: Rule, domain: DomainInferer):

        # Preprocess/Convert to data-structures
        # Then print stuff

        for function in rule.functions:
            self.generate_satisfiability_part_for_function(function, rule, domain.domain_dictionary)


    
    def rewrite_rules(self, rules: [Rule]):

        # TODO -> Implement variable inference and domain inference for SAT part!
        # --> Need to take nested functions into account!

        for rule in rules:
            print(str(rule))

            if rule.is_constraint is False:
                raise NotImplementedError("Foundedness and Head-Guess not (yet) implemented")

            self.generate_satisfiability_part(rule, self.domain)







class VariableDomainSizeInferer:

    def __init__(self):
        self.function_string = "FUNCTION"

    def get_function_domain_size(self, function, domain_fragment, variable_domain):

        index = 0
        for argument in function.arguments:

            if index >= len(domain_fragment):
                # Happens for empty domain for example:
                domain_fragment.append({})

            arg_domain_fragment = domain_fragment[index]

            if "VARIABLE" in argument:
                variable = argument["VARIABLE"]

                if "__size__" in arg_domain_fragment:
                    tmp_var_domain_size = arg_domain_fragment["__size__"]
                else:
                    tmp_var_domain_size = len([key for key in arg_domain_fragment if arg_domain_fragment[key] == True])

                if variable not in variable_domain:
                    variable_domain[variable] = tmp_var_domain_size
                else:
                    if variable_domain[variable] < tmp_var_domain_size and tmp_var_domain_size > 0:
                        variable_domain[variable] = tmp_var_domain_size

            elif self.function_string in argument:
                child_function = argument[self.function_string]
                if child_function.name in domain_fragment:
                    tmp_domain = domain_fragment[child_function.name]
                else:
                    tmp_domain = []

                self.get_function_domain_size(child_function, tmp_domain, variable_domain)

            elif "BINARY_OPERATION" in argument:
                child_function = argument["BINARY_OPERATION"]
                if child_function.name in domain_fragment:
                    tmp_domain = domain_fragment[child_function.name]
                else:
                    tmp_domain = []

                self.get_function_domain_size(child_function, tmp_domain, variable_domain)


            else:
                pass

            index += 1


    def get_variable_domain_size(self, rule, domain):

        variable_domain_size = {}

        for literal in rule.literals:
            if self.function_string in literal:
                function = literal[self.function_string]
                if literal[self.function_string].in_head is False and literal[self.function_string].signum > 0:
                    # Only for B_r^+ domain inference occurs:
                    if function.name in domain and "terms" in domain[function.name]:
                        terms_domain = domain[function.name]["terms"]
                    elif "_total" in domain:
                        terms_domain = domain["_total"]["terms"]
                    else:
                        raise NotImplementedError("_total domain not found!")
                        pass

                    self.get_function_domain_size(function, terms_domain,
                        variable_domain_size)

        return variable_domain_size




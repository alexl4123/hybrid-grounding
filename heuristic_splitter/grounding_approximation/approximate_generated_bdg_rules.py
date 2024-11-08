
from heuristic_splitter.grounding_approximation.variable_domain_size_inferer import VariableDomainSizeInferer

class ApproximateGeneratedBDGRules:

    def __init__(self, domain_transformer, rule, graph_ds):

        self.domain_transformer = domain_transformer
        self.rule = rule
        self.graph_ds = graph_ds

        self.function_string = "FUNCTION"
        self.comparison_string = "COMPARISON"

        self.found_new_rules = 0
        self.found_old_rules = 0

        self.sat_rules = 0

    def approximate_bdg_sizes(self):

        # Necessary for variable intersections 
        processed_variables = {}

        domain = self.domain_transformer.domain_dictionary

        domain_size_inferer = VariableDomainSizeInferer()
        variable_domain_sizes = domain_size_inferer.get_variable_domain_size(self.rule, domain)

        head_variables = {}

        for literal in self.rule.literals:
            if self.function_string in literal:
                if literal[self.function_string].in_head is True and literal[self.function_string].signum > 0:
                    function = literal[self.function_string]
                    domain_size_inferer.get_function_domain_size(function, [], head_variables)

        # Variable guesses (and saturation)
        for variable in variable_domain_sizes:
            self.sat_rules += 2*variable_domain_sizes[variable]

        # Once for variable guesses and once for saturation
        # For the :- not sat. and sat :- sat_r1, ... rules
        self.sat_rules += 2

        self.approximate_literals_contributions(domain, variable_domain_sizes, domain_size_inferer, head_variables)

        if self.rule.is_constraint is False:
            # The complexity defining rules for new-foundedness (the aritiy+1 rules):
            head_combinations = 1
            for head_variable in head_variables.keys():
                head_combinations *= variable_domain_sizes[head_variable]

            # For the :- ufr1, ... rules (only one head atom considered (single rule))
            self.found_old_rules += head_combinations

            for rule_variable in variable_domain_sizes.keys():
                if rule_variable not in head_variables:
                    # Then body variable - needs to be instantiated fully
                    self.found_new_rules += 2 * (head_combinations * variable_domain_sizes[rule_variable]) 

                    # Guessing the ufound-variables
                    self.found_old_rules += head_combinations * variable_domain_sizes[rule_variable]
                else:
                    # In head variables:
                    # Once for variable guesses and once for saturation
                    self.found_new_rules += 2 * variable_domain_sizes[rule_variable]


            if self.rule.is_tight is False:
                # The following is an approximation of the needed additional rules for level-mapping overhead.

                scc_domain_sizes = 0
                for scc_element in list(self.rule.scc):
                    scc_element_predicate = self.graph_ds.index_to_predicate_lookup[scc_element]

                    if scc_element_predicate in domain:
                        domain_sizes = domain[scc_element_predicate]["terms_size"]

                        terms_size = 1
                        for domain_term_size in domain_sizes:
                            terms_size *= domain_term_size

                    else:
                        # Need to estimate as no (direct) supporting rule in the cycle occurs:
                        # And need to compute the arity
                        # Such a rule has to exist as it is in the SCC
                        scc_tmp_rule_index = self.graph_ds.node_to_rule_lookup[scc_element][0]

                        print(scc_tmp_rule_index)

                        scc_tmp_rule = self.rule_dictionary[scc_tmp_rule_index]
                        scc_tmp_rule_ast = scc_tmp_rule.ast_rule
                        print(scc_tmp_rule_ast)

                        if "head" in scc_tmp_rule_ast.child_keys:
                            old = getattr(node, "head")

                            tmp_pred_arity = len(scc_tmp_rule.arguments)

                            total_domain_size = len(self.domain_transformer.total_domain.keys())

                            combinations = 1
                            for _ in range(tmp_pred_arity):
                                combinations *= total_domain_size

                            terms_size = combinations
                            
                        else:
                            print("[ERROR] - This rule inside an SCC has to have a head by definition!")
                            print(scc_tmp_rule)

                            raise NotImplementedError()
                            
                    scc_domain_sizes += terms_size

                # Cubic approx. for orderings:
                cubic_approximation = scc_domain_sizes * scc_domain_sizes * scc_domain_sizes

                self.found_old_rules += cubic_approximation



            # For the :- not found.; found :- found_r1 (only 1 rule considered here) and found_r1 :- ...
            self.found_new_rules += 3

        self.found_new_rules += self.sat_rules
        self.found_old_rules += self.sat_rules

        return self.found_new_rules, self.found_old_rules

    def approximate_literals_contributions(self, domain, variable_domain_sizes, domain_size_inferer, head_variables):

        for literal in self.rule.literals:
            if self.function_string in literal:
                # FUNCTION
                function = literal[self.function_string]
                if function.name in domain and "terms" in domain[function.name]:
                    terms_domain = domain[function.name]["terms"]
                elif self.rule.is_tight is True:
                    terms_domain = []
            elif self.comparison_string in literal:
                function = literal[self.comparison_string]
                terms_domain = []
            else:
                # IF NEITHER FUNCTION NOR COMPARISON CTD.
                continue


            function_variables_domain_sizes = {}

            domain_size_inferer.get_function_domain_size(function, terms_domain, function_variables_domain_sizes)

            old_function_tuples = 1
            new_function_tuples = 1

            considered_head_variables = {}
            for function_variable in function_variables_domain_sizes.keys():

                old_function_tuples *= variable_domain_sizes[function_variable]
                new_function_tuples *= variable_domain_sizes[function_variable]

                for head_variable in head_variables:
                    if self.rule.variable_no_head_graph.is_reachable_variables(head_variable, function_variable) is True:
                        if head_variable not in considered_head_variables:
                            old_function_tuples *= variable_domain_sizes[head_variable]
                            considered_head_variables[head_variable] = True

            self.found_new_rules += new_function_tuples
            self.found_old_rules += old_function_tuples

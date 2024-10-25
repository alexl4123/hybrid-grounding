# pylint: disable=C0103

"""
Approx. gen. bdg rules.
"""

import clingo
from clingo.ast import Transformer

from heuristic_splitter.graph_data_structure import GraphDataStructure

from heuristic_splitter.rule import Rule


class ApproximateGeneratedBDGRulesTransformer(Transformer):
    """
    Approx. gen. bdg rules.
    May only be called with 1 rule!
    """

    def __init__(self, domain_transformer, variable_domains, rule, head_variables, graph_ds: GraphDataStructure, rule_dictionary):

        self.domain_transformer = domain_transformer

        self.bdg_rules = 0
        self.sat_rules = 0
        self.found_old_rules = 0
        self.found_new_rules = 0

        self.bdg_rules_old = 0 
        self.bdg_rules_new = 0 

        self.variable_domains = variable_domains
        self.rule = rule
        self.head_variables = head_variables
        self.graph_ds = graph_ds
        self.rule_dictionary = rule_dictionary

        self.function_variables = {}
        self.current_function_position = 0

        self.comparison_variables = {}

        self.node_signum = None


    def visit_Rule(self, node):
        """
        Visits an clingo-AST rule.
        """
        self.current_head = node.head

        variable_guesses = len(self.variable_domains.keys())
        # Once for variable guesses and once for saturation
        self.sat_rules += 2 *variable_guesses
        # For the :- not sat. and sat :- sat_r1, ... rules
        self.sat_rules += 2


        if self.rule.is_constraint is False:
            # The complexity defining rules for new-foundedness (the aritiy+1 rules):
            head_combiations = 1
            for head_variable in set(self.head_variables):
                head_combiations *= self.variable_domains[head_variable]

            for rule_variable in self.variable_domains.keys():
                if rule_variable not in self.head_variables:
                    # Then body variable - needs to be instantiated fully
                    self.found_new_rules += 2 * (head_combiations * self.variable_domains[rule_variable]) 

                    # Guessing the ufound-variables
                    self.found_old_rules += head_combiations

            if self.rule.is_tight is False:
                # The following is an approximation of the needed additional rules for level-mapping overhead.

                scc_domain_sizes = 0
                for scc_element in list(self.rule.scc):
                    scc_element_predicate = self.graph_ds.index_to_predicate_lookup[scc_element]

                    if scc_element_predicate in self.domain_transformer.domain_dictionary:
                        domain_sizes = self.domain_transformer.domain_dictionary[scc_element_predicate]["terms_size"]

                        terms_size = 1
                        for domain_term_size in domain_sizes:
                            terms_size *= domain_term_size

                    else:
                        # Need to estimate as no supporting rule in the cycle occurs:
                        # And need to compute the arity
                        # Such a rule has to exist as it is in the SCC
                        scc_tmp_rule_index = self.graph_ds.node_to_rule_lookup[scc_element][0]

                        print(scc_tmp_rule_index)

                        scc_tmp_rule = self.rule_dictionary[scc_tmp_rule_index]
                        scc_tmp_rule_ast = scc_tmp_rule.ast_rule
                        print(scc_tmp_rule_ast)

                        if "head" in scc_tmp_rule_ast.child_keys:
                            old = getattr(node, "head")

                            tmp_pred_arity = len(list(str(old).split(",")))
                                
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


            # Once for variable guesses and once for saturation
            self.found_new_rules += 2 *variable_guesses

            # For the :- not found.; found :- found_r1 (only 1 rule considered here) and found_r1 :- ...
            self.found_new_rules += 3 
            # For the :- ufr1, ... rules (only one head atom considered!)
            self.found_old_rules += 1


        # Step into functions/predicates:            
        if "head" in node.child_keys:
            self.in_head = True
            old = getattr(node, "head")
            self._dispatch(old)
            # self.visit_children(node.head)
            self.in_head = False

        if "body" in node.child_keys:
            self.in_body = True
            old = getattr(node, "body")
            self._dispatch(old)
            self.in_body = False

        self.bdg_rules_old = self.bdg_rules + self.sat_rules + self.found_old_rules
        self.bdg_rules_new = self.bdg_rules + self.sat_rules + self.found_new_rules

        return node

    def visit_Function(self, node):
        """
        Visits an clingo-AST function.
        """
        self.current_function = node
        
        self.visit_children(node)


        if self.in_head is True:

            head_rules = 1

            for head_variable in self.head_variables.keys():

                head_rules *= self.variable_domains[head_variable]

            self.bdg_rules += head_rules

        elif self.in_body is True:
            self._estimate_body_literal_bdg_rules(self.function_variables)
        else:
            print("[ERROR] - Neither head nor body")
            raise NotImplementedError()



        self._reset_temporary_function_variables()
        return node

    def visit_Variable(self, node):
        """
        Visits an clingo-AST variable.
        Takes care of most things about domain-inference.
        """

        self.visit_children(node)

        if self.current_function:
            self.function_variables[node.name] = self.current_function_position

            self.current_function_position += 1
        elif self.is_comparison:
            self.comparison_variables[node.name] = 0

        return node


    def visit_Literal(self, node):
        """
        Visits a clingo-AST literal (negated/non-negated).
        -> 0 means positive
        -> -1 means negative
        """

        if node.sign == 0:
            self.node_signum = +1
        else:
            # Do not consider literal if negative
            self.node_signum = -1

        self.visit_children(node)


        self._reset_temporary_literal_variables()

        return node

    def visit_SymbolicTerm(self, node):
        """
        Visits an clingo-AST symbolic term (constant).
        """
        if self.current_function:
            self.current_function_position += 1

        return node

    def visit_Comparison(self, node):
        """
        Visits a clinto-AST comparison.
        """

        self.is_comparison = True
        self.visit_children(node)

        self._estimate_body_literal_bdg_rules(self.comparison_variables)

        self.comparison_variables = {}
        self.is_comparison = False

        return node


    def _reset_temporary_literal_variables(self):
        self.node_signum = None


    def _reset_temporary_aggregate_variables(self):
        self.head_element_index = 0

    def _reset_temporary_function_variables(self):
        self.current_function = None
        self.current_function_position = 0

        self.function_variables = {}

    def _estimate_body_literal_bdg_rules(self, function_variables):

        # ------ SAT PART ------ :
        sat_rules = 1
        for function_variable in function_variables.keys():
            sat_rules *= self.variable_domains[function_variable]

        self.sat_rules += sat_rules

        if self.rule.is_constraint is False:
            # ------- NEW FOUNDEDNESS PART -----
            n_found_rules = 1
            for function_variable in function_variables.keys():
                n_found_rules *= self.variable_domains[function_variable]
            self.found_new_rules += n_found_rules

            # ------- OLD FOUNDEDNESS PART ------
            reachable = False
            for head_variable in self.head_variables.keys():
                for function_variable in function_variables.keys():

                    v_head_variable = self.rule.variable_graph.predicate_to_index_lookup[head_variable]
                    v_function_variable = self.rule.variable_graph.predicate_to_index_lookup[function_variable]

                    is_reachable = self.rule.variable_graph.is_reachable(v_head_variable, v_function_variable)

                    if is_reachable is True:
                        reachable = is_reachable
                        break
                
                if reachable is True:
                    break
            
            if reachable is False:
                # Variable Justifying independence:
                o_found_rules = 1
                for function_variable in function_variables.keys():
                    o_found_rules *= self.variable_domains[function_variable]
                self.found_old_rules += o_found_rules
            else:
                # Worst case 2*artiy exponential:
                # Head variables + variables in function differing from head variables (union of variables):
                to_ground_variables = list(set(list(self.head_variables.keys()) + list(function_variables.keys())))

                combinations = 1
                for to_ground_variable in to_ground_variables:
                    combinations *= self.variable_domains[to_ground_variable]

                self.found_old_rules += combinations
        



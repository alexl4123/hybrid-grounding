# pylint: disable=C0103
"""
Necessary for Tuples Approx.
"""

import math

import clingo
from clingo.ast import Transformer

from heuristic_splitter.graph_data_structure import GraphDataStructure

from heuristic_splitter.rule import Rule


class ApproximateGeneratedSotaRulesTransformer(Transformer):
    """
    Approx. gen. tuples.
    May only be called with 1 rule!
    """

    def __init__(self, domain_transformer):

        self.domain_transformer = domain_transformer
        self.rule_tuples = 1
        self.variable_domains = {}
        self.variable_domains_in_function = {}
        self.symbolic_term_positions_in_function = []

        self.current_head = None
        self.current_function = None
        self.current_head_function = None
        self.head_functions = []

        self.node_signum = None

        self.head_is_choice_rule = False

        self.current_rule_position = 0
        self.current_function_position = 0
        self.current_function = None

    def visit_Rule(self, node):
        """
        Visits an clingo-AST rule.
        """
        self.current_head = node.head

        if "body" in node.child_keys:
            self.in_body = True
            old = getattr(node, "body")
            self._dispatch(old)
            self.in_body = False

        self.current_rule_position += 1
        self._reset_temporary_rule_variables()
        return node

    def visit_Function(self, node):
        """
        Visits an clingo-AST function.
        """
        self.current_function = node

        if self.in_body:
            # Only consider body stuff
            # For the "b" and "c" in a :- b, not c.
            # For the "e" in {a:b;c:d} :- e.

            self.visit_children(node)

            if node.name in self.domain_transformer.domain_dictionary:
                tuples_maybe_function = self.domain_transformer.domain_dictionary[node.name]["tuples_size"]["maybe_true"]
                tuples_true_function = self.domain_transformer.domain_dictionary[node.name]["tuples_size"]["sure_true"]
            else:

                average_tuples = self.domain_transformer.domain_dictionary["_average_domain_tuples"]
                total_domain = len(self.domain_transformer.total_domain.keys())

                arity = len(str(self.current_function.name).split(","))

                combinations = 1
                for _ in range(arity):
                    combinations *= total_domain
                
                tuples_maybe_function = int(math.ceil(average_tuples * combinations))
                tuples_true_function = 0


            tuples_function = tuples_maybe_function + tuples_true_function


            variable_intersection_reduction_factor = 1

            for variable in self.variable_domains_in_function:

                if variable in self.variable_domains:

                    if self.variable_domains[variable] < self.variable_domains_in_function[variable]:

                        self.variable_domains[variable] = self.variable_domains_in_function[variable]
                    
                    variable_intersection_reduction_factor *= self.variable_domains[variable]

                else:
                    # Variable not in domain --> Add it:
                    self.variable_domains[variable] = self.variable_domains_in_function[variable]


            # ------------------------------------------------
            # General join:
            new_tuples = (tuples_function * self.rule_tuples)


            # --------------------------------------------------
            # Variable intersection join:
            new_tuples = new_tuples / variable_intersection_reduction_factor

            # -----------------------------------
            # Account for symbolic terms:
            # for example the "1" in p(X,1,Y)
            # -> reduces the tuples of p by the domain of the position of "1"

            symbolic_term_reduction_factor = 1
            for function_position in self.symbolic_term_positions_in_function:
                symbolic_term_reduction_factor *= self.domain_transformer.domain_dictionary[node.name]["terms_size"][function_position]


            new_tuples = new_tuples / symbolic_term_reduction_factor


            # -----------------------------------------
            # Multiplicative addition of new-tuples:
            self.rule_tuples = new_tuples

        self._reset_temporary_function_variables()
        return node

    def visit_Variable(self, node):
        """
        Visits an clingo-AST variable.
        Takes care of most things about domain-inference.
        """

        self.visit_children(node)

        if self.current_function is not None and self.current_function.name in self.domain_transformer.domain_dictionary:
            if node.name not in self.variable_domains_in_function:
                self.variable_domains_in_function[node.name] = self.domain_transformer.domain_dictionary[self.current_function.name]["terms_size"][self.current_function_position]
            elif self.variable_domains_in_function[node.name] > self.domain_transformer.domain_dictionary[self.current_function.name]["terms_size"][self.current_function_position]:
                self.variable_domains_in_function[node.name] = self.domain_transformer.domain_dictionary[self.current_function.name]["terms_size"][self.current_function_position]
        else:  
            total_domain = len(self.domain_transformer.total_domain.keys())
            self.variable_domains_in_function[node.name] = total_domain 

        self.current_function_position += 1

        return node

    def visit_SymbolicTerm(self, node):
        """
        Visits an clingo-AST symbolic term (constant).
        """
        if self.current_function:
            self.symbolic_term_positions_in_function.append(self.current_function_position) 

            self.current_function_position += 1



        return node



    def visit_Literal(self, node):
        """
        Visits a clingo-AST literal (negated/non-negated).
        -> 0 means positive
        -> -1 means negative
        """

        if node.sign == 0:
            self.node_signum = +1
            self.visit_children(node)
        else:
            # Do not consider literal if negative
            self.node_signum = -1


        self._reset_temporary_literal_variables()

        return node

    def _reset_temporary_literal_variables(self):
        self.node_signum = None

    def _reset_temporary_aggregate_variables(self):
        self.head_element_index = 0

    def _reset_temporary_rule_variables(self):
        self.current_head = None
        self.current_head_function = None
        self.head_is_choice_rule = False
        self.head_functions = []

    def _reset_temporary_function_variables(self):
        self.current_function = None
        self.current_function_position = 0

        self.symbolic_term_positions_in_function = []
        self.variable_domains_in_function = {}


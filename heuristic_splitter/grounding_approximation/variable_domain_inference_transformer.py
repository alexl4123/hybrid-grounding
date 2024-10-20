# pylint: disable=C0103
"""
Necessary for Tuples Approx.
"""

import clingo
from clingo.ast import Transformer

from heuristic_splitter.graph_data_structure import GraphDataStructure

from heuristic_splitter.rule import Rule


class VariableDomainInferenceTransformer(Transformer):
    """
    Infer Domain of variables of BDG rule (intersections between domains):
    May only be called with 1 rule!
    """

    def __init__(self, domain_transformer, rule):

        self.domain_transformer = domain_transformer
        self.variable_domains_helper = {}
        self.variable_domains = {}
        self.variable_domains_in_function = {}

        self.current_head = None
        self.current_function = None
        self.current_head_function = None

        self.node_signum = None

        self.head_is_choice_rule = False

        self.current_rule_position = 0
        self.current_function_position = 0

        self.head_variables = {}

        self.in_body = False
        self.in_head = False

    def visit_Rule(self, node):
        """
        Visits an clingo-AST rule.
        """
        self.current_head = node.head

        if "head" in node.child_keys:
            self.in_head = True
            old = getattr(node, "head")
            self._dispatch(old)
            self.in_head = False

        if "body" in node.child_keys:
            self.in_body = True
            old = getattr(node, "body")
            self._dispatch(old)
            self.in_body = False

        for variable in self.variable_domains_helper.keys():
            self.variable_domains[variable] = len(self.variable_domains_helper[variable])

        self.current_rule_position += 1
        self._reset_temporary_rule_variables()
        return node

    def visit_Function(self, node):
        """
        Visits an clingo-AST function.
        """
        self.current_function = node

        self.visit_children(node)

        if self.in_body:
            # Only consider body stuff
            # For the "b" and "c" in a :- b, not c.
            # For the "e" in {a:b;c:d} :- e.


            for variable in self.variable_domains_in_function.keys():

                if variable in self.variable_domains_helper:

                    # Domain Intersection:
                    self.variable_domains_helper[variable] = set(list(self.variable_domains_helper[variable])).intersection(set(list(self.variable_domains_in_function[variable])))

                else:
                    # Variable not in domain --> Add it:
                    self.variable_domains_helper[variable] = list(self.variable_domains_in_function[variable].keys())


        self._reset_temporary_function_variables()
        return node

    def visit_Variable(self, node):
        """
        Visits an clingo-AST variable.
        Takes care of most things about domain-inference.
        """

        self.visit_children(node)

        if self.in_body is True:
            self.variable_domains_in_function[node.name] = self.domain_transformer.domain_dictionary[self.current_function.name]["terms"][self.current_function_position]
        elif self.in_head is True:
            self.head_variables[node.name] = self.current_function_position

        self.current_function_position += 1

        return node

    def visit_SymbolicTerm(self, node):
        """
        Visits an clingo-AST symbolic term (constant).
        """
        if self.current_function:

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
        else:
            # Do not consider literal if negative
            self.node_signum = -1

        self.visit_children(node)

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

    def _reset_temporary_function_variables(self):
        self.current_function = None
        self.current_function_position = 0

        self.variable_domains_in_function = {}


# pylint: disable=C0103
"""
Necessary for Tuples Approx.
"""

import clingo
from clingo.ast import Transformer

from heuristic_splitter.graph_data_structure import GraphDataStructure

from heuristic_splitter.rule import Rule


class ApproximateGeneratedTuplesTransformer(Transformer):
    """
    Approx. gen. tuples.
    """

    def __init__(self, domain_transformer):

        self.domain_transformer = domain_transformer
        self.tuples = 1
        self.considered_variables = []

        self.current_head = None
        self.current_function = None
        self.current_head_function = None
        self.head_functions = []

        self.node_signum = None

        self.head_is_choice_rule = False

        self.current_rule_position = 0

        # TODO: Implement the estimation of number of generated rules.

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





        self._reset_temporary_function_variables()
        return node

    def visit_Variable(self, node):
        """
        Visits an clingo-AST variable.
        Takes care of most things about domain-inference.
        """

        self.visit_children(node)
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


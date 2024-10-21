# pylint: disable=C0103
"""
TODO
"""

import clingo
from clingo.ast import Transformer

from heuristic_splitter.graph_data_structure import GraphDataStructure

from heuristic_splitter.rule import Rule


class NaGGDomainConnectorTransformer(Transformer):
    """
     TODO
    """

    def __init__(self):
        self.current_head = None
        self.current_function = None
        self.current_head_function = None

        self.node_signum = None

        self.head_is_choice_rule = False

        self.current_rule_position = 0
        self.current_function_position = 0

        self.in_body = False
        self.in_head = False

        self.shown_predicates = {}


        self.nagg_safe_variables = {}

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

        self.current_rule_position += 1
        self._reset_temporary_rule_variables()
        return node

    def visit_Function(self, node):
        """
        Visits an clingo-AST function.
        """
        self.current_function = node

        self.visit_children(node)

        if str(node) not in self.shown_predicates:

            arity = len(list(str(node).split(",")))

            self.shown_predicates[str(node.name)] = {arity}


        self._reset_temporary_function_variables()
        return node

    def visit_Variable(self, node):
        """
        Visits an clingo-AST variable.
        Takes care of most things about domain-inference.
        """

        self.visit_children(node)

        if self.in_body is True and self.node_signum > 0 and self.current_function is not None:

            if self.current_rule_position not in self.nagg_safe_variables:
                self.nagg_safe_variables[self.current_rule_position] = {}

            if str(node) not in self.nagg_safe_variables[self.current_rule_position]:
                self.nagg_safe_variables[self.current_rule_position][str(node)] = []

            to_add_dict = {}
            to_add_dict["type"] = "function"
            to_add_dict["name"] = str(self.current_function.name)
            to_add_dict["position"] = str(self.current_function_position)
            to_add_dict["signum"] = str(0) # NaGG uses 0 as positive, but the heuristics +1

            self.nagg_safe_variables[self.current_rule_position][str(node)].append(to_add_dict)

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



# pylint: disable=C0103
"""
Necessary for graph creation.
"""

import clingo
from clingo.ast import Transformer

from heuristic_splitter.graph_data_structure import GraphDataStructure


class GraphCreatorTransformer(Transformer):
    """
    Necessary for domain inference.
    In conjunction with the Term-transformer used to infer the domain.
    """

    def __init__(self, graph_ds: GraphDataStructure):

        self.graph_ds = graph_ds

        self.current_head = None
        self.current_function = None
        self.current_head_function = None
        self.head_functions = []

        self.node_signum = None

        self.head_is_choice_rule = False

        self.current_rule_position = 0


    def visit_Rule(self, node):
        """
        Visits an clingo-AST rule.
        """
        self.current_head = node.head

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

        self.current_rule_position += 1
        self._reset_temporary_rule_variables()
        return node

    def visit_Function(self, node):
        """
        Visits an clingo-AST function.
        """
        self.current_function = node

        if self.in_head and self.head_is_choice_rule and self.head_aggregate_element_head:
            # For the "a" and "c" in {a:b;c:d} :- e.
            self.head_functions.append(node)
            self.current_head_function = node

            tmp_head_choice_name = f"{node.name}{self.current_rule_position}{self.head_element_index}"

            self.graph_ds.add_edge(node.name, tmp_head_choice_name, -1)
            self.graph_ds.add_edge(tmp_head_choice_name, node.name,  -1)

        elif self.in_head and self.head_is_choice_rule and self.head_aggregate_element_head:
            # For the "b" and "d" in {a:b;c:d} :- e.
            self.graph_ds.add_edge(self.current_head_function.name, node.name, self.node_signum)
        elif self.in_head and str(self.current_function) == str(self.current_head):
            # For the "a" in a :- b, not c.
            self.head_functions.append(node)
        elif self.in_head:
            print("HEAD TYPE NOT IMPLEMENTED:_")
            print(self.current_head)
            print(self.current_head_function)
            raise NotImplementedError
        elif self.in_body:
            # For the "b" and "c" in a :- b, not c.
            # For the "e" in {a:b;c:d} :- e.
            if len(self.head_functions) > 0:
                for head_function in self.head_functions:
                    self.graph_ds.add_edge(head_function.name, node.name, self.node_signum)
        else:
            print("HEAD TYPE NOT IMPLEMENTED:_")
            print(self.current_head)
            print(self.current_head_function)
            print(node)
            raise NotImplementedError

        self.visit_children(node)

        self._reset_temporary_function_variables()
        return node

    def visit_Aggregate(self, node):
        """
        Visits an clingo-AST aggregate.
        """



        if self.in_head:
            self.head_is_choice_rule = True

            self.head_element_index = 0
            for elem in node.elements:
                self.head_aggregate_element_head = True
                self.visit_children(elem.literal)
                self.head_aggregate_element_head = False

                self.head_aggregate_element_body = True
                for condition in elem.condition:
                    self.visit_Literal(condition)
                self.head_aggregate_element_body = False

                self.head_element_index += 1

            self._reset_temporary_aggregate_variables()

        return node

    def visit_Variable(self, node):
        """
        Visits an clingo-AST variable.
        Takes care of most things about domain-inference.
        """

        self.visit_children(node)

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
        self.head_functions = []

    def _reset_temporary_function_variables(self):
        self.current_function = None
        self.current_function_position = 0

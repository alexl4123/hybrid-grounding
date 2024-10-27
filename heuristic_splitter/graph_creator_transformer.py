# pylint: disable=C0103
"""
Necessary for graph creation.
"""

import clingo
from clingo.ast import Transformer

from heuristic_splitter.graph_data_structure import GraphDataStructure

from heuristic_splitter.rule import Rule


class GraphCreatorTransformer(Transformer):
    """
    Creates dependency graph.
    """

    def __init__(self, graph_ds: GraphDataStructure, rule_dictionary, rules_as_strings):

        self.graph_ds = graph_ds

        self.current_head = None
        self.current_function = None
        self.current_head_function = None
        self.head_functions = []

        self.node_signum = None

        self.head_is_choice_rule = False

        self.current_rule_position = 0

        self.rule_dictionary = rule_dictionary
        self.rules_as_strings = rules_as_strings

        self.in_head = False
        self.in_body = False


    def visit_Rule(self, node):
        """
        Visits an clingo-AST rule.
        """
        self.current_head = node.head

        self.rule_dictionary[self.current_rule_position] = Rule(node, self.rules_as_strings[self.current_rule_position])

        if "head" in node.child_keys:

            if str(node.head) == "#false":
                self.is_constraint = True
                constraint_vertex_name = f"_constraint{self.current_rule_position}"
                self.graph_ds.add_vertex(constraint_vertex_name)
                self.graph_ds.add_node_to_rule_lookup([self.current_rule_position], constraint_vertex_name)
            else:
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

            self.graph_ds.add_edge(node.name, tmp_head_choice_name, -1, is_choice_rule_head = True)
            self.graph_ds.add_edge(tmp_head_choice_name, node.name, -1, is_choice_rule_head = True)

            self.graph_ds.add_node_to_rule_lookup([self.current_rule_position], node.name)
            self.graph_ds.add_node_to_rule_lookup([], tmp_head_choice_name)

        elif self.in_head and self.head_is_choice_rule and self.head_aggregate_element_head:
            # For the "b" and "d" in {a:b;c:d} :- e.
            self.graph_ds.add_edge(self.current_head_function.name, node.name, self.node_signum)
            self.graph_ds.add_node_to_rule_lookup([], node.name)
        elif self.in_head and str(self.current_function) == str(self.current_head):
            # For the "a" in a :- b, not c.
            self.head_functions.append(node)

            self.graph_ds.add_vertex(node.name)

            self.graph_ds.add_node_to_rule_lookup([self.current_rule_position], node.name)

        elif self.in_head:
            print("HEAD TYPE NOT IMPLEMENTED:_")
            print(self.current_head)
            print(self.current_head_function)
            raise NotImplementedError
        elif self.in_body and len(self.head_functions) > 0:
            # For the "b" and "c" in a :- b, not c.
            # For the "e" in {a:b;c:d} :- e.
            for head_function in self.head_functions:
                self.graph_ds.add_edge(head_function.name, node.name, self.node_signum)
                self.graph_ds.add_node_to_rule_lookup([], node.name)
        elif self.in_body and self.is_constraint:
            self.graph_ds.add_edge(f"_constraint{self.current_rule_position}", node.name, self.node_signum)
            self.graph_ds.add_node_to_rule_lookup([], node.name)
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
        self.is_constraint = False

    def _reset_temporary_function_variables(self):
        self.current_function = None
        self.current_function_position = 0

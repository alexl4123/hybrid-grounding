# pylint: disable=C0103
"""
Necessary for domain inference.
"""

import clingo
from clingo.ast import Transformer

from heuristic_splitter.graph_data_structure import GraphDataStructure

from heuristic_splitter.rule import Rule


class DomainTransformer(Transformer):
    """
    Creates dependency graph.
    """

    def __init__(self):

        self.current_head = None
        self.current_function = None
        self.current_head_function = None
        self.head_functions = []
        self.current_rule = None

        self.node_signum = None

        self.head_is_choice_rule = False

        self.current_rule_position = 0

        # A dict. of all domain values
        self.total_domain = {}

        """
        Definition of domain-dictionary:
        ------------
        self.domain_dictionary[node.name] = {
            "tuples": {
                "sure_true": {...},
                "maybe_true": {
                    str(TUPLE): True
                },
            },
            "tuples_size": {
                "sure_true": INT VALUE,
                "maybe_true": INT VALUE
            }
            "terms": [POSITION IN LIST IS DOMAIN OF POSITION IN FUNCTION],
            "terms_size": [POSITION IN LIST IS DOMAIN-SIZE OF POSITION IN FUNCTION]
        }
        for term in term_tuple:
            -> Here the terms are added
            self.domain_dictionary[node.name]["terms"].append({term:True})
        """
        self.domain_dictionary = {}

    def visit_Rule(self, node):
        """
        Visits an clingo-AST rule.
        """
        self.current_rule = node
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

            self.add_node_to_domain(node)

        elif self.in_head and str(self.current_function) == str(self.current_head):
            # For the "a" in a :- b, not c.
            self.head_functions.append(node)


            self.add_node_to_domain(node)


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

        print(f"[ERROR] - FOUND VARIABLE IN GROUNDED PART: {node.name}, in Function: {self.current_function}, in Rule: {self.current_rule}")
        raise NotImplementedError()

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
        self.current_rule = None
        self.current_head = None
        self.current_head_function = None
        self.head_is_choice_rule = False
        self.head_functions = []

    def _reset_temporary_function_variables(self):
        self.current_function = None
        self.current_function_position = 0



    def add_node_to_domain(self, node):
        """
        May only be called for (grounded) nodes (expected AST-Functions) in heads of rules.
        """

        term_tuple = [str(argument) for argument in node.arguments]

        if node.name not in self.domain_dictionary:
            self.domain_dictionary[node.name] = {
                "tuples": {
                    "sure_true": {},
                    "maybe_true": {
                        str(term_tuple): True
                    },
                },
                "terms": []
            }

            for term in term_tuple:
                self.domain_dictionary[node.name]["terms"].append({term:True})

                if term not in self.total_domain:
                    self.total_domain[term] = True
        else:
            if str(term_tuple) not in self.domain_dictionary[node.name]["tuples"]["maybe_true"]:
                self.domain_dictionary[node.name]["tuples"]["maybe_true"][str(term_tuple)] = True

            for term_index in range(len(term_tuple)):

                term = term_tuple[term_index]

                if term not in self.domain_dictionary[node.name]["terms"][term_index]:
                    self.domain_dictionary[node.name]["terms"][term_index][term] = True
                if term not in self.total_domain:
                    self.total_domain[term] = True

    def update_domain_sizes(self):
        """
        Computes an update of the tuple_size and term_size keys of the domain object.
        -> This is done for efficiencies sake (not to recompute this)
        """

        for _tuple in self.domain_dictionary.keys():
            self.domain_dictionary[_tuple]["tuples_size"] = {}

            self.domain_dictionary[_tuple]["tuples_size"]["sure_true"] = len(self.domain_dictionary[_tuple]["tuples"]["sure_true"].keys())
            self.domain_dictionary[_tuple]["tuples_size"]["maybe_true"] = len(self.domain_dictionary[_tuple]["tuples"]["maybe_true"].keys())

            self.domain_dictionary[_tuple]["terms_size"] = []

            for _term_index in range(len(self.domain_dictionary[_tuple]["terms"])):

                self.domain_dictionary[_tuple]["terms_size"].append(len(self.domain_dictionary[_tuple]["terms"][_term_index].keys()))


# pylint: disable=C0103
"""
Necessary for Heuristic.
"""

import clingo
from clingo.ast import Transformer

from heuristic_splitter.variable_graph_structure import VariableGraphDataStructure
from heuristic_splitter.graph_data_structure import GraphDataStructure
from heuristic_splitter.heuristic import HeuristicInterface

from nagg.comparison_tools import ComparisonTools

class HeuristicTransformer(Transformer):
    """
    Necessary for domain inference.
    In conjunction with the Term-transformer used to infer the domain.
    """

    def __init__(self, graph_ds: GraphDataStructure, used_heuristic,
            bdg_rules, sota_rules, lpopt_rules,
            constraint_rules):

        self.graph_ds = graph_ds
        self.variable_graph = None

        self.current_head = None
        self.current_function = None
        self.current_head_function = None
        self.head_functions = []

        self.node_signum = None

        self.head_is_choice_rule = False
        self.has_aggregate = False

        self.current_rule_position = 0

        self.in_body = False
        self.in_head = False

        self.stratified_variables = []

        # Output -> How to ground the rule according to the heuristic used.
        self.bdg_rules = bdg_rules
        self.sota_rules = sota_rules
        self.lpopt_rules = lpopt_rules
        self.constraint_rules = constraint_rules

        # Used to determine if a rule is tight, or non-tight.
        self.head_atoms_scc_membership = {}
        self.body_atoms_scc_membership = {}

        self.heuristic = used_heuristic

        # Inside a function, to check on what position of the arguments we currently are.
        self.current_function_position = 0

        self.head_aggregate_element_head = False
        self.head_aggregate_element_body = False
        self.in_head_aggregate = False

        # Used for heuristic decision.
        self.maximum_rule_arity = 0

        # To check if the rule is a constraint (used for heuristic decision).
        self.is_constraint = False

        # Used in comparison (for variable graph)
        self.is_comparison = False
        self.current_comparison_variables = []

        # Dictionary storing all variables from functions, and comparisons.
        # In order to check if they are induced by either.
        self.all_positive_function_variables = {}
        self.all_comparison_variables = {}


    def visit_Rule(self, node):
        """
        Visits an clingo-AST rule.
        """
        self.current_head = node.head

        self.variable_graph = VariableGraphDataStructure()

        if "head" in node.child_keys:

            if str(node.head) == "#false":
                self.is_constraint = True
                self.constraint_rules.append(self.current_rule_position)

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

        self.heuristic.handle_rule(self.bdg_rules, self.sota_rules, self.lpopt_rules,
            self.variable_graph, self.stratified_variables, self.graph_ds,
            self.head_atoms_scc_membership, self.body_atoms_scc_membership,
            self.maximum_rule_arity, self.is_constraint,
            self.has_aggregate,
            node,
            self.current_rule_position,
            self.all_positive_function_variables,
            self.all_comparison_variables,)

        self.current_rule_position += 1
        self._reset_temporary_rule_variables()
        return node

    def visit_Function(self, node):
        """
        Visits an clingo-AST function.
        """
        self.current_function = node
        self.current_function_variables = []

        self.visit_children(node)

        for variable_0_index in range(len(self.current_function_variables)):
            for variable_1_index in range(variable_0_index + 1, len(self.current_function_variables)):

                variable_0 = self.current_function_variables[variable_0_index]
                variable_1 = self.current_function_variables[variable_1_index]

                self.variable_graph.add_edge(str(variable_0), str(variable_1))

        if self.graph_ds.predicate_is_stratified(node) is True:
            self.stratified_variables += self.current_function_variables

        if self.in_head and self.head_is_choice_rule and self.head_aggregate_element_head:
            # For the "a" and "c" in {a:b;c:d} :- e.

            if self.graph_ds.get_scc_index_of_atom(node.name) not in self.head_atoms_scc_membership:
                self.head_atoms_scc_membership[self.graph_ds.get_scc_index_of_atom(node.name)] = 1
            else:
                self.head_atoms_scc_membership[self.graph_ds.get_scc_index_of_atom(node.name)] += 1

        elif self.in_head and self.head_is_choice_rule and self.head_aggregate_element_head:
            # For the "b" and "d" in {a:b;c:d} :- e.
            if self.graph_ds.get_scc_index_of_atom(node.name) not in self.body_atoms_scc_membership:
                self.body_atoms_scc_membership[self.graph_ds.get_scc_index_of_atom(node.name)] = 1
            else:
                self.body_atoms_scc_membership[self.graph_ds.get_scc_index_of_atom(node.name)] += 1

        elif self.in_head and str(self.current_function) == str(self.current_head):
            # For the "a" in a :- b, not c.
            if self.graph_ds.get_scc_index_of_atom(node.name) not in self.head_atoms_scc_membership:
                self.head_atoms_scc_membership[self.graph_ds.get_scc_index_of_atom(node.name)] = 1
            else:
                self.head_atoms_scc_membership[self.graph_ds.get_scc_index_of_atom(node.name)] += 1



        elif self.in_head:
            print("HEAD TYPE NOT IMPLEMENTED:_")
            print(self.current_head)
            print(self.current_head_function)
            raise NotImplementedError

        elif self.in_body:
            # For the "b" and "c" in a :- b, not c.
            # For the "e" in {a:b;c:d} :- e.
            if self.graph_ds.get_scc_index_of_atom(node.name) not in self.body_atoms_scc_membership:
                self.body_atoms_scc_membership[self.graph_ds.get_scc_index_of_atom(node.name)] = 1
            else:
                self.body_atoms_scc_membership[self.graph_ds.get_scc_index_of_atom(node.name)] += 1

        else:
            print("HEAD TYPE NOT IMPLEMENTED:_")
            print(self.current_head)
            print(self.current_head_function)
            print(node)
            raise NotImplementedError

        if self.current_function_position > self.maximum_rule_arity:
            self.maximum_rule_arity = self.current_function_position

        self._reset_temporary_function_variables()
        return node

    def visit_Aggregate(self, node):
        """
        Visits an clingo-AST aggregate.
        """

        self.has_aggregate = True

        if self.in_head:
            self.in_head_aggregate = True
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

            self.in_head_aggregate = False
            self._reset_temporary_aggregate_variables()



        return node

    def visit_Variable(self, node):
        """
        Visits an clingo-AST variable.
        """

        if self.is_comparison is True:
            self.current_comparison_variables.append(str(node))

            if str(node) not in self.all_comparison_variables:
                self.all_comparison_variables[str(node)] = True

        elif self.in_head_aggregate is False and self.head_is_choice_rule is False:
            if self.current_function is not None:
                # Derived from predicate:
                self.current_function_variables.append(str(node))

            if self.node_signum > 0 and self.current_function is not None:
                if str(node) not in self.all_positive_function_variables:
                    self.all_positive_function_variables[str(node)] = True

        if self.current_function:
            self.current_function_position += 1
    


        self.visit_children(node)

        return node

    def visit_SymbolicTerm(self, node):
        """
        Visits an clingo-AST symbolic term (constant).
        """

        self.visit_children(node)

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
            self.node_signum = -1

        self.visit_children(node)

        self._reset_temporary_literal_variables()

        return node

    def visit_Comparison(self, node):
        """
        Visits a clinto-AST comparison.
        """

        self.is_comparison = True
        self.visit_children(node)

        for variable_0_index in range(len(self.current_comparison_variables)):
            for variable_1_index in range(variable_0_index + 1, len(self.current_comparison_variables)):

                variable_0 = self.current_comparison_variables[variable_0_index]
                variable_1 = self.current_comparison_variables[variable_1_index]

                self.variable_graph.add_edge(str(variable_0),str(variable_1))



        self.current_comparison_variables = []
        self.is_comparison = False

        return node





    def _reset_temporary_literal_variables(self):
        self.node_signum = None


    def _reset_temporary_rule_variables(self):
        self.current_head = None
        self.current_head_function = None
        
        self.variable_graph = None

        self.head_is_choice_rule = False
        self.has_aggregate = False

        self.head_functions = []

        self.stratified_variables = []

        self.maximum_rule_arity = 0

        self.is_constraint = False

        self.head_atoms_scc_membership = {}
        self.body_atoms_scc_membership = {}

    def _reset_temporary_function_variables(self):
        self.current_function_variables = None
        self.current_function = None
        self.current_function_position = 0

    def _reset_temporary_aggregate_variables(self):
        self.head_element_index = 0


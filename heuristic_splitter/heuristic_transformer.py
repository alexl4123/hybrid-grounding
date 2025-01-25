# pylint: disable=C0103
"""
Necessary for Heuristic.
"""

import clingo
from clingo.ast import Transformer

from heuristic_splitter.variable_graph_structure import VariableGraphDataStructure
from heuristic_splitter.graph_data_structure import GraphDataStructure
from heuristic_splitter.heuristic import HeuristicInterface

from heuristic_splitter.grounding_approximation.variable_domain_size_inferer import VariableDomainSizeInferer

from nagg.comparison_tools import ComparisonTools

class HeuristicTransformer(Transformer):
    """
    Necessary for domain inference.
    In conjunction with the Term-transformer used to infer the domain.
    """

    def __init__(self, graph_ds: GraphDataStructure, used_heuristic,
            bdg_rules, sota_rules, stratified_rules, lpopt_rules,
            constraint_rules, all_heads, debug_mode, rule_dictionary,
            program_ds):

        self.graph_ds = graph_ds
        self.all_heads = all_heads
        self.program_ds = program_ds

        self.variable_graph = None

        self.current_head = None
        self.current_function = None
        self.current_head_function = None
        self.head_functions = []

        self.node_signum = None

        self.head_is_choice_rule = False
        self.has_aggregate = False

        self.in_binary_op_arity_added = False
        
        self.body_is_stratified = True

        self.current_rule_position = 0

        self.in_body = False
        self.in_head = False

        self.in_disjunction = False
        self.in_unary_operation = False
        
        self.in_minimize_statement = False
        self.current_function_stack = []

        self.binary_operation_stack = []

        self.stratified_variables = []

        # Output -> How to ground the rule according to the heuristic used.
        self.bdg_rules = bdg_rules
        self.sota_rules = sota_rules
        self.stratified_rules = stratified_rules
        self.constraint_rules = constraint_rules
        self.lpopt_rules = lpopt_rules

        # Used to determine if a rule is tight, or non-tight.
        self.head_atoms_scc_membership = {}
        self.body_atoms_scc_membership = {}


        self.heuristic = used_heuristic

        # Inside a function, to check on what position of the arguments we currently are.
        self.current_function_position = 0

        self.head_aggregate_element_head = False
        self.head_aggregate_element_body = False
        self.in_head_aggregate = False
        self.debug_mode = debug_mode

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

        self.rule_dictionary = rule_dictionary
        self.function_string = "FUNCTION"
        self.comparison_string = "COMPARISON"

    def visit_Rule(self, node):
        """
        Visits an clingo-AST rule.
        """
        self.current_head = node.head

        self.variable_graph = VariableGraphDataStructure()

        if "head" in node.child_keys:

            if str(node.head) == "#false":
                self.is_constraint = True
                self.constraint_rules[self.current_rule_position] = True

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

        try:
            rule_object = self.rule_dictionary[self.current_rule_position]

            domain_size_inferer = VariableDomainSizeInferer()

            # Better than arity:
            maximum_variables_in_literal = 0

            for literal in rule_object.literals:
                if self.function_string in literal:
                    # FUNCTION
                    function = literal[self.function_string]
                    terms_domain = []
                elif self.comparison_string in literal:
                    function = literal[self.comparison_string]
                    terms_domain = []
                else:
                    # IF NEITHER FUNCTION NOR COMPARISON CTD.
                    continue

                function_variables_domain_sizes = {}
                domain_size_inferer.get_function_domain_size(function, terms_domain, function_variables_domain_sizes)

                number_variables_in_literal = len(list(function_variables_domain_sizes.keys()))

                if number_variables_in_literal > maximum_variables_in_literal:
                    maximum_variables_in_literal = number_variables_in_literal

            self.heuristic.handle_rule(
                self.bdg_rules, self.sota_rules, self.stratified_rules, self.lpopt_rules,
                self.variable_graph, self.stratified_variables, self.graph_ds,
                self.head_atoms_scc_membership, self.body_atoms_scc_membership,
                maximum_variables_in_literal, self.is_constraint,
                self.has_aggregate,
                self.current_rule_position,
                self.all_positive_function_variables,
                self.all_comparison_variables,
                self.body_is_stratified,
                self.in_minimize_statement,
                self.program_ds)
        except Exception as ex:
            print(f"In this rule: {str(node)}")
            raise ex

        self.current_rule_position += 1
        self._reset_temporary_rule_variables()
        return node

    def visit_Minimize(self, node):
        """
        Visit weak constraint:
        :~ p(X). [...]
        """
        if self.debug_mode is True:
            print(f"Minimize: {str(node)}")

        self.in_minimize_statement = True
        self.variable_graph = VariableGraphDataStructure()

        self.current_rule = node
        self.is_constraint = True

        self.in_body = True
        self.visit_children(node)
        self.in_body = False

        self.heuristic.handle_rule(
            self.bdg_rules, self.sota_rules, self.stratified_rules, self.lpopt_rules,
            self.variable_graph, self.stratified_variables, self.graph_ds,
            self.head_atoms_scc_membership, self.body_atoms_scc_membership,
            self.maximum_rule_arity, self.is_constraint,
            self.has_aggregate,
            self.current_rule_position,
            self.all_positive_function_variables,
            self.all_comparison_variables,
            self.body_is_stratified,
            self.in_minimize_statement,
            self.program_ds)

        self.current_rule_position += 1
        self._reset_temporary_rule_variables()
        self.in_minimize_statement = False
        return node


    def visit_Disjunction(self, node):

        self.in_disjunction = True
        self.visit_children(node)
        self.in_disjunction = False

        return node

    def visit_BodyAggregate(self, node):

        self.has_aggregate = True

        return node

    def visit_Function(self, node):
        """
        Visits an clingo-AST function.
        """
        self.current_function_stack.append(node)

        if len(self.current_function_stack) == 1:
            # If it is the top-level function:
            self.current_function = node
            self.current_function_variables = []

        self.visit_children(node)

        if len(self.current_function_stack) == 1:
            if len(self.current_function_variables) > 1:
                for variable_0_index in range(len(self.current_function_variables)):
                    for variable_1_index in range(variable_0_index + 1, len(self.current_function_variables)):

                        variable_0 = self.current_function_variables[variable_0_index]
                        variable_1 = self.current_function_variables[variable_1_index]

                        if self.in_head is False:
                            self.variable_graph.add_edge(str(variable_0), str(variable_1), in_head=False)
                        else:
                            self.variable_graph.add_edge(str(variable_0), str(variable_1), in_head=True)
            else:
                for variable in self.current_function_variables:
                    self.variable_graph.add_node(str(variable))



            if self.graph_ds.predicate_is_stratified(node) is True:
                self.stratified_variables += self.current_function_variables

            if self.in_body is True and self.graph_ds.predicate_is_stratified(node) is False:
                self.body_is_stratified = False

            if self.in_head and self.head_is_choice_rule and self.head_aggregate_element_head:
                # For the "a" and "c" in {a:b;c:d} :- e.

                if self.graph_ds.get_scc_index_of_atom(node.name) not in self.head_atoms_scc_membership:
                    self.head_atoms_scc_membership[self.graph_ds.get_scc_index_of_atom(node.name)] = 1
                else:
                    self.head_atoms_scc_membership[self.graph_ds.get_scc_index_of_atom(node.name)] += 1

            elif self.in_head and self.head_is_choice_rule and self.head_aggregate_element_body:
                # For the "b" and "d" in {a:b;c:d} :- e.
                if self.graph_ds.get_scc_index_of_atom(node.name) not in self.body_atoms_scc_membership:
                    self.body_atoms_scc_membership[self.graph_ds.get_scc_index_of_atom(node.name)] = 1
                else:
                    self.body_atoms_scc_membership[self.graph_ds.get_scc_index_of_atom(node.name)] += 1

            elif self.in_head and (str(self.current_function) == str(self.current_head) or self.in_disjunction is True):
                # For the "a" in a :- b, not c.
                # Or a|d :- b, not c. (the a,d)
                if self.graph_ds.get_scc_index_of_atom(node.name) not in self.head_atoms_scc_membership:
                    self.head_atoms_scc_membership[self.graph_ds.get_scc_index_of_atom(node.name)] = 1
                else:
                    self.head_atoms_scc_membership[self.graph_ds.get_scc_index_of_atom(node.name)] += 1

            elif self.in_head and self.in_unary_operation is True:

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
                print("BODY TYPE NOT IMPLEMENTED:_")
                print(self.current_head)
                print(self.current_head_function)
                print(node)
                raise NotImplementedError

            if self.current_function_position > self.maximum_rule_arity:
                self.maximum_rule_arity = self.current_function_position

            if node.name not in self.all_heads:
                self.all_heads[node.name] = self.current_function_position

            self._reset_temporary_function_variables()

        self.current_function_stack.pop()

        if len(self.current_function_stack) == 1:
            # If there is a function above the node-function:
            self.current_function_position += 1

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

        if str(node) != "_" and self.in_head_aggregate is False and self.head_is_choice_rule is False:
            if self.is_comparison is True and len(self.current_function_stack) == 0:
                self.current_comparison_variables.append(str(node))

                if str(node) not in self.all_comparison_variables:
                    self.all_comparison_variables[str(node)] = True

            else:
                if self.current_function is not None:
                    # Derived from predicate:
                    self.current_function_variables.append(str(node))

                try:    
                    if self.node_signum is not None and self.current_function is not None and self.node_signum > 0 and self.is_comparison is False and self.in_body is True:
                        if str(node) not in self.all_positive_function_variables:
                            self.all_positive_function_variables[str(node)] = True
                except Exception as ex:
                    print("-----")
                    for func in self.current_function_stack:
                        print(func)
                    print(self.current_function)
                    print(f"Is Minimize: {self.in_minimize_statement}")
                    print(f"Node: {node}")
                    raise ex

        if len(self.current_function_stack) == 1 and self.in_binary_op_arity_added is False:
            self.current_function_position += 1

            if len(self.binary_operation_stack) > 0:
                self.in_binary_op_arity_added = True


        self.visit_children(node)

        return node

    def visit_SymbolicTerm(self, node):
        """
        Visits an clingo-AST symbolic term (constant).
        """

        self.visit_children(node)

        if len(self.current_function_stack) == 1 and self.in_binary_op_arity_added is False:
            self.current_function_position += 1

            if len(self.binary_operation_stack) > 0:
                self.in_binary_op_arity_added = True



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

        if len(self.current_function_stack) == 0: # No function above:   
            if len(self.current_comparison_variables) > 1:
                for variable_0_index in range(len(self.current_comparison_variables)):
                    for variable_1_index in range(variable_0_index + 1, len(self.current_comparison_variables)):

                        variable_0 = self.current_comparison_variables[variable_0_index]
                        variable_1 = self.current_comparison_variables[variable_1_index]

                        self.variable_graph.add_edge(str(variable_0), str(variable_1), in_head=False)
            else:
                for variable in self.current_comparison_variables:
                    self.variable_graph.add_node(str(variable))

            self.current_comparison_variables = []

        self.is_comparison = False

        return node

    def _reset_temporary_literal_variables(self):
        self.node_signum = None


    def _reset_temporary_rule_variables(self):
        self.current_head = None
        self.current_head_function = None
        
        self.body_is_stratified = True
        
        self.variable_graph = None

        self.head_is_choice_rule = False
        self.has_aggregate = False

        self.head_functions = []

        self.stratified_variables = []

        self.maximum_rule_arity = 0

        self.is_constraint = False

        self.head_atoms_scc_membership = {}
        self.body_atoms_scc_membership = {}
        self.all_comparison_variables = {}

    def _reset_temporary_function_variables(self):
        self.current_function_variables = None
        self.current_function = None
        self.current_function_position = 0

    def _reset_temporary_aggregate_variables(self):
        self.head_element_index = 0

    def visit_BinaryOperation(self, node):


        self.binary_operation_stack.append(node)

        if len(self.binary_operation_stack) == 1:
            self.in_binary_op_arity_added = False

        self.visit_children(node)

        if len(self.binary_operation_stack) == 1:
            self.in_binary_op_arity_added = False

        self.binary_operation_stack.pop()
        return node
        
    def visit_UnaryOperation(self, node):

        self.in_unary_operation = True
        self.visit_children(node)
        self.in_unary_operation = False

        return node


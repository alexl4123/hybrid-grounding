# pylint: disable=C0103
"""
Necessary for graph creation.
"""

import clingo
from clingo.ast import Transformer

from heuristic_splitter.graph_data_structure import GraphDataStructure

from heuristic_splitter.rule import Rule
from heuristic_splitter.function import Function

class HeadFuncObject:
    def __init__(self, name):
        self.name = name

class GraphCreatorTransformer(Transformer):
    """
    Creates dependency graph.
    """

    def __init__(self, graph_ds: GraphDataStructure, rule_dictionary, rules_as_strings, debug_mode):

        self.graph_ds = graph_ds

        self.current_head = None
        self.current_function = None
        self.current_head_function = None
        self.current_rule = None
        self.head_functions = []

        self.node_signum = None

        self.head_is_choice_rule = False

        self.current_rule_position = 0

        self.rule_dictionary = rule_dictionary
        self.rules_as_strings = rules_as_strings

        self.in_head = False
        self.in_body = False

        self.in_disjunction = False
        self.tmp_head_disjunction_name = None 
        self.tmp_head_disjunction_name_neg = None

        self.debug_mode = debug_mode

        self.head_aggregate_element_head = False
        self.head_aggregate_element_body = False

        self.in_unary_operation = False
        self.is_constraint = False

        self.in_program_rules = False

        self.current_function_creation_stack = []

    def visit_Minimize(self, node):
        """
        Visit weak constraint:
        :~ p(X). [...]
        """
        if self.debug_mode is True:
            print(f"Minimize: {str(node)}")

        self.current_rule = node
        self.rule_dictionary[self.current_rule_position] = Rule(node, self.rules_as_strings[self.current_rule_position])

        self.is_constraint = True
        constraint_vertex_name = f"_constraint{self.current_rule_position}"
        self.graph_ds.add_vertex(constraint_vertex_name)
        self.graph_ds.add_node_to_rule_lookup([self.current_rule_position], constraint_vertex_name)

        self.in_body = True
        self.visit_children(node)
        self.in_body = False

        self.current_rule_position += 1
        self._reset_temporary_rule_variables()
        return node

    def visit_Rule(self, node):
        """
        Visits an clingo-AST rule.
        """
        self.current_head = node.head
        self.current_rule = node

        self.rule_dictionary[self.current_rule_position] = Rule(node, self.rules_as_strings[self.current_rule_position])

        if self.in_program_rules is True:
            self.rule_dictionary[self.current_rule_position].in_program_rules = True

        try:
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
        except Exception as ex:
            print(str(node))
            raise ex

        self.current_rule_position += 1
        self._reset_temporary_rule_variables()
        return node

    def visit_Function(self, node):
        """
        Visits an clingo-AST function.
        """

        if self.current_function is None:
            # Current-Function is the top-level function
            self.current_function = node

        self.current_function_creation_stack.append(Function())
        self.current_function_creation_stack[-1].name = node.name


        if self.in_head and self.head_is_choice_rule and self.head_aggregate_element_head:
            # For the "a" and "c" in {a:b;c:d} :- e.

            self.graph_ds.add_vertex(node.name)

            self.graph_ds.add_edge(node.name, self.tmp_head_choice_name, 1)

            self.graph_ds.add_node_to_rule_lookup([], node.name)

        elif self.in_head and self.head_is_choice_rule and self.head_aggregate_element_body:
            # For the "b" and "d" in {a:b;c:d} :- e.

            self.graph_ds.add_edge(self.tmp_head_choice_name, node.name, 1)
            self.graph_ds.add_node_to_rule_lookup([], node.name)

        elif self.in_head and str(node) == str(self.current_head):
            # For the "a" in a :- b, not c.
            self.head_functions.append(node)

            self.graph_ds.add_vertex(node.name)

            self.graph_ds.add_node_to_rule_lookup([self.current_rule_position], node.name)


        elif self.in_head and self.in_disjunction is True:
            # Or for the "a,d" in a|d :- b, not c.
            self.graph_ds.add_vertex(node.name)

            self.graph_ds.add_edge(node.name, self.tmp_head_disjunction_name, 1)
            self.graph_ds.add_node_to_rule_lookup([], node.name)

        elif self.in_head and str(node) != str(self.current_function):
            # Somewhere in a sub-function in the head:
            # Do nothing
            pass

        elif self.in_head and self.in_unary_operation:
            # In "-a :- b." (strong negation)
            # If all others fail, then we are in the strong negated head.
            self.head_functions.append(node)

            self.graph_ds.add_vertex(node.name)

            self.graph_ds.add_node_to_rule_lookup([self.current_rule_position], node.name)

        elif self.in_head:
            print("HEAD TYPE NOT IMPLEMENTED:")
            print(self.current_rule)
            print(f"Current Head: {self.current_head}")
            print(f"Current Head Function: {self.current_head_function}")
            print(f"Current head functions: {self.head_functions}")
            print(f"Node string: {str(node)}")
            print(self.in_head)
            print(self.head_is_choice_rule)
            print(self.head_aggregate_element_head)
            raise NotImplementedError
        elif self.in_body and len(self.head_functions) > 0 and str(node) == str(self.current_function):
            # For the "b" and "c" in a :- b, not c.
            # For the "e" in {a:b;c:d} :- e.
            # Is top-level-function:
            for head_function in self.head_functions:
                self.graph_ds.add_edge(head_function.name, node.name, self.node_signum)
                self.graph_ds.add_node_to_rule_lookup([], node.name)
        elif self.in_body and self.is_constraint and str(node) == str(self.current_function):
            self.graph_ds.add_edge(f"_constraint{self.current_rule_position}", node.name, self.node_signum)
            self.graph_ds.add_node_to_rule_lookup([], node.name)

        elif self.in_body and str(node) != str(self.current_function):
            # If not top-level function (e.g., :- p(X), q(p(X)).)
            pass
        else:
            print("BODY TYPE NOT IMPLEMENTED:")
            print(self.current_rule)
            print(f"Current Head: {self.current_head}")
            print(f"Current Head Function: {self.current_head_function}")
            print(f"Node string: {str(node)}")
            print(self.in_head)
            print(self.head_is_choice_rule)
            print(self.head_aggregate_element_head)
            raise NotImplementedError

        self.visit_children(node)

        if len(self.current_function_creation_stack) == 1:
            # Top level function:

            self.rule_dictionary[self.current_rule_position].functions.append(self.current_function_creation_stack[0])
            self.current_function_creation_stack.clear()
            self._reset_temporary_function_variables()
        else:
            prev_func = self.current_function_creation_stack.pop()
            self.current_function_creation_stack[-1].arguments.append({"FUNCTION":prev_func})

        return node

    def visit_Aggregate(self, node):
        """
        Visits an clingo-AST aggregate.
        """

        if self.in_head:
            self.head_is_choice_rule = True

            self.tmp_head_choice_name = f"#choice_{self.current_rule_position}"
            self.tmp_head_choice_name_neg = f"#choice_{self.current_rule_position}_neg"

            self.graph_ds.add_edge(self.tmp_head_choice_name, self.tmp_head_choice_name_neg, -1)
            self.graph_ds.add_edge(self.tmp_head_choice_name_neg, self.tmp_head_choice_name, -1)

            self.graph_ds.add_node_to_rule_lookup([self.current_rule_position], self.tmp_head_choice_name)
            self.graph_ds.add_node_to_rule_lookup([], self.tmp_head_choice_name_neg)

            self.head_functions = [HeadFuncObject(self.tmp_head_choice_name)]

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

    def visit_Disjunction(self, node):

        self.in_disjunction = True

        self.tmp_head_disjunction_name = f"#disjunction_{self.current_rule_position}"
        self.tmp_head_disjunction_name_neg = f"#disjunction_{self.current_rule_position}_neg"

        self.graph_ds.add_edge(self.tmp_head_disjunction_name, self.tmp_head_disjunction_name_neg, -1)
        self.graph_ds.add_edge(self.tmp_head_disjunction_name_neg, self.tmp_head_disjunction_name, -1)

        self.graph_ds.add_node_to_rule_lookup([self.current_rule_position], self.tmp_head_disjunction_name)
        self.graph_ds.add_node_to_rule_lookup([], self.tmp_head_disjunction_name_neg)

        self.rule_dictionary[self.current_rule_position].is_disjunctive = True

        self.head_functions = [HeadFuncObject(self.tmp_head_disjunction_name)]

        self.visit_children(node)
        self.in_disjunction = False

        return node

    def visit_Variable(self, node):
        """
        Visits an clingo-AST variable.
        Takes care of most things about domain-inference.
        """

        if len(self.current_function_creation_stack) > 0:
            self.current_function_creation_stack[-1].arguments.append({"VARIABLE":str(node)})
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

    def visit_SymbolicTerm(self, node):
        """
        Visits an clingo-AST symbolic term (constant).
        """

        if len(self.current_function_creation_stack) > 0:
            self.current_function_creation_stack[-1].arguments.append({"TERM":str(node)})

        self.visit_children(node)



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
        self.is_constraint = False

    def _reset_temporary_function_variables(self):
        self.current_function = None
        self.current_function_position = 0

    
    def visit_UnaryOperation(self, node):

        self.in_unary_operation = True
        self.visit_children(node)
        self.in_unary_operation = False

        return node

    
    def visit_Definition(self, node):
        if self.debug_mode is True:
            print(f"Definition: {str(node)}")
        self.visit_children(node)
        return node
    
    def visit_ShowSignature(self, node):
        if self.debug_mode is True:
            print(f"ShowSignature: {str(node)}")
        self.visit_children(node)
        return node

    def visit_Defined(self, node):
        if self.debug_mode is True:
            print(f"ShowSignature: {str(node)}")
        self.visit_children(node)
        return node

    def visit_ShowTerm(self, node):
        if self.debug_mode is True:
            print(f"ShowTerm: {str(node)}")
        self.visit_children(node)
        return node

    def visit_Script(self, node):
        if self.debug_mode is True:
            print(f"Script: {str(node)}")
        self.visit_children(node)
        return node

    def visit_Program(self, node):
        if self.debug_mode is True:
            print(f"Program: {str(node)}")

        if self.rules_as_strings[self.current_rule_position] == str(node):
            del self.rules_as_strings[self.current_rule_position]

        if node.name == "rules":
            self.in_program_rules = True

        self.visit_children(node)
        return node

    def visit_External(self, node):
        if self.debug_mode is True:
            print(f"External: {str(node)}")
        self.visit_children(node)
        return node

    def visit_Edge(self, node):
        if self.debug_mode is True:
            print(f"Edge: {str(node)}")
        self.visit_children(node)
        return node

    def visit_Heuristic(self, node):
        if self.debug_mode is True:
            print(f"Heuristic: {str(node)}")
        self.visit_children(node)
        return node

    def visit_ProjectAtom(self, node):
        if self.debug_mode is True:
            print(f"ProjectAtom: {str(node)}")
        self.visit_children(node)
        return node

    def visit_ProjectSignature(self, node):
        if self.debug_mode is True:
            print(f"ProjectSignature: {str(node)}")
        self.visit_children(node)
        return node

    def visit_TheoryDefinition(self, node):
        if self.debug_mode is True:
            print(f"TheoryDefinition: {str(node)}")
        self.visit_children(node)
        return node

    def visit_Comment(self, node):
        if self.debug_mode is True:
            print(f"Comment: {str(node)}")
        self.visit_children(node)
        return node

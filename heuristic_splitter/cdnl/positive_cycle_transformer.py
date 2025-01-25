
import clingo
from clingo.ast import Transformer

from heuristic_splitter.graph_data_structure import GraphDataStructure

from heuristic_splitter.program_structures.rule import Rule


class PositiveCycleTransformer(Transformer):
    """
    Creates dependency graph.
    """

    def __init__(self, scc_index, function_visit_index = 0):
        self.current_rule = None
        self.current_head = None
        self.in_head = False
        self.in_body = False

        self.scc_index = scc_index

        self.current_rule_position = 0
        self.function_visit_index = function_visit_index

        self.transformed_rules = []
        self.new_rules = []

        self.rewritten_to_original_dict = {}

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
            self.in_head = False

        body_string_list = []
        if "body" in node.child_keys:
            old = getattr(node, "body")
            for lit in old:
                body_string_list.append(str(lit))

        new_rule = f"{self.new_function} :- {','.join(body_string_list)}."
        self.transformed_rules.append(new_rule)

        self.current_rule_position += 1
        self._reset_temporary_rule_variables()
        return node

    def visit_Literal(self, node):
        """
        Visits a clingo-AST literal (negated/non-negated).
        -> 0 means positive -- convert_to --> +1
        -> -1 means negative -- convert_to --> -1
        """
        if node.sign == 0:
            self.node_signum = +1
        else:
            self.node_signum = -1

        self.visit_children(node)

        self._reset_temporary_literal_variables()

        return node

    def visit_Function(self, node):

        self.visit_children(node)
        new_name = f"{node.name}_{self.scc_index}_{self.function_visit_index}"

        node_argument_string = ",".join([str(argument) for argument in node.arguments])
        if len(node.arguments) > 0:
            node_argument_string = f"({node_argument_string})"

        self.new_function = f"{new_name}{node_argument_string}"

        new_tmp_rule = f"{str(node)} :- {self.new_function}."
        self.new_rules.append(new_tmp_rule)

        self.rewritten_to_original_dict[new_name] = node.name

        self.function_visit_index += 1

        return node

    def _reset_temporary_literal_variables(self):
        self.node_signum = None

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


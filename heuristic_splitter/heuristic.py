
from heuristic_splitter.variable_graph_structure import VariableGraphDataStructure
from heuristic_splitter.graph_data_structure import GraphDataStructure

from heuristic_splitter.treewidth_computation_strategy import TreewidthComputationStrategy

class HeuristicInterface:

    def __init__(self, treewidth_strategy: TreewidthComputationStrategy, rule_dictionary):
        self.treewidth_strategy = treewidth_strategy
        self.rule_dictionary = rule_dictionary

    def handle_rule(self, bdg_rules, sota_rules, lpopt_rules,
            variable_graph : VariableGraphDataStructure, stratified_variables,
            graph_ds : GraphDataStructure,
            head_atoms_scc_membership, body_atoms_scc_membership,
            maximum_rule_arity, is_constraint,
            ast_rule_node,
            rule_position):

        pass
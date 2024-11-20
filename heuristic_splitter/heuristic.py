
from heuristic_splitter.variable_graph_structure import VariableGraphDataStructure
from heuristic_splitter.graph_data_structure import GraphDataStructure

from heuristic_splitter.enums.treewidth_computation_strategy import TreewidthComputationStrategy
from heuristic_splitter.enums.sota_grounder import SotaGrounder

class HeuristicInterface:

    def __init__(self, treewidth_strategy: TreewidthComputationStrategy, rule_dictionary, sota_grounder: SotaGrounder, enable_lpopt):
        self.treewidth_strategy = treewidth_strategy
        self.rule_dictionary = rule_dictionary
        self.sota_grounder = sota_grounder
        self.enable_lpopt = enable_lpopt

    def handle_rule(
            self, bdg_rules, sota_rules, stratified_rules, lpopt_rules,
            variable_graph : VariableGraphDataStructure, stratified_variables,
            graph_ds : GraphDataStructure,
            head_atoms_scc_membership, body_atoms_scc_membership,
            maximum_rule_arity, is_constraint,
            has_aggregate,
            ast_rule_node,
            rule_position,
            all_positive_function_variables,
            all_comparison_variables,
            body_is_stratified,
            program_ds):

        pass
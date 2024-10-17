
from heuristic_splitter.heuristic import HeuristicInterface
from heuristic_splitter.variable_graph_structure import VariableGraphDataStructure
from heuristic_splitter.graph_data_structure import GraphDataStructure

from heuristic_splitter.treewidth_computation_strategy import TreewidthComputationStrategy



class Heuristic0(HeuristicInterface):

    def handle_rule(self, bdg_rules, sota_rules, lpopt_rules,
            variable_graph : VariableGraphDataStructure, stratified_variables,
            graph_ds : GraphDataStructure,
            head_atoms_scc_membership, body_atoms_scc_membership,
            maximum_rule_arity, is_constraint,
            has_aggregate,
            ast_rule_node,
            rule_position):

        full_variable_graph = variable_graph.clone()

        for stratified_variable in set(stratified_variables):
            variable_graph.remove_variable(str(stratified_variable))


        # The +1 comes from the number of variables (tw is max bag-size -1, so we need to add 1 again)
        if self.treewidth_strategy == TreewidthComputationStrategy.NETWORKX_HEUR:
            tw_effective = variable_graph.compute_networkx_bag_size()
            tw_full = full_variable_graph.compute_networkx_bag_size()
        elif self.treewidth_strategy == TreewidthComputationStrategy.TWALGOR_EXACT:
            tw_effective = variable_graph.compute_twalgor_bag_size()
            tw_full = full_variable_graph.compute_twalgor_bag_size()
        else:
            raise NotImplementedError()
        
        is_tight = len([True for head_key in head_atoms_scc_membership.keys() if head_key in body_atoms_scc_membership]) == 0

        if is_constraint is True and tw_effective > maximum_rule_arity:
            bdg_rules.append(rule_position)

        elif is_tight is True and tw_effective > maximum_rule_arity * 2:
            bdg_rules.append(rule_position)
        
        elif is_tight is False and tw_effective > maximum_rule_arity * 3:
            bdg_rules.append(rule_position)
        
        else:
            sota_rules.append(rule_position)

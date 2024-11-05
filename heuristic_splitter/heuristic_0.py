
from heuristic_splitter.heuristic import HeuristicInterface
from heuristic_splitter.variable_graph_structure import VariableGraphDataStructure
from heuristic_splitter.graph_data_structure import GraphDataStructure

from heuristic_splitter.treewidth_computation_strategy import TreewidthComputationStrategy



class Heuristic0(HeuristicInterface):

    def handle_rule(self, bdg_rules, sota_rules, stratified_rules,
            variable_graph : VariableGraphDataStructure, stratified_variables,
            graph_ds : GraphDataStructure,
            head_atoms_scc_membership, body_atoms_scc_membership,
            maximum_rule_arity, is_constraint,
            has_aggregate,
            rule_position,
            all_positive_function_variables,
            all_comparison_variables,
            body_is_stratified,
            in_minimize_statement):

        # If variables are induced by a comparison, they are not handled by BDG (inefficient domain inference) 
        all_comparison_variables_safe_by_predicate = set(all_comparison_variables.keys()).issubset(set(all_positive_function_variables.keys()))

        full_variable_graph = variable_graph.clone()
        variable_no_head_graph = variable_graph.clone()
        variable_no_head_graph.remove_head_edges()

        is_tight = len([True for head_key in head_atoms_scc_membership.keys() if head_key in body_atoms_scc_membership]) == 0

        if self.rule_dictionary[rule_position].in_program_rules is True:
            # If user specifies grounded by BDG, then ground by BDG
            bdg_rules[rule_position] = True
        elif body_is_stratified is True and has_aggregate is False:
            # If stratified then ground at first
            # TODO -> Fix aggregate dependencies.
            stratified_rules[rule_position] = True
        elif has_aggregate is True:
            # Aggregates are for now grounded via SOTA approaches.
            sota_rules[rule_position] = True

        elif body_is_stratified is True or in_minimize_statement is True:
            # Purely stratified rules are surely grounded by SOTA techniques
            # Also minimize statements
            sota_rules[rule_position] = True
        else:
            # A more complex decision is needed:

            # Stratified variables are not considered in the rewriting, as they are not grounded in SOTA grounders.
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
            

            if is_constraint is True and tw_effective > maximum_rule_arity and all_comparison_variables_safe_by_predicate is True:
                #bdg_rules.append(rule_position)
                bdg_rules[rule_position] = True

            elif is_tight is True and tw_effective > maximum_rule_arity * 2 and all_comparison_variables_safe_by_predicate is True:
                #bdg_rules.append(rule_position)
                bdg_rules[rule_position] = True
            
            elif is_tight is False and tw_effective > maximum_rule_arity * 3 and all_comparison_variables_safe_by_predicate is True:
                #bdg_rules.append(rule_position)
                bdg_rules[rule_position] = True

            else:
                #sota_rules.append(rule_position)
                sota_rules[rule_position] = True
        
        self.rule_dictionary[rule_position].add_variable_graph(full_variable_graph)
        self.rule_dictionary[rule_position].add_variable_no_head_graph(variable_no_head_graph)
        self.rule_dictionary[rule_position].add_is_tight(is_tight)
        self.rule_dictionary[rule_position].add_is_constraint(is_constraint)

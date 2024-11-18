
from heuristic_splitter.heuristic import HeuristicInterface
from heuristic_splitter.variable_graph_structure import VariableGraphDataStructure
from heuristic_splitter.graph_data_structure import GraphDataStructure

from heuristic_splitter.enums.sota_grounder import SotaGrounder
from heuristic_splitter.enums.treewidth_computation_strategy import TreewidthComputationStrategy



class Heuristic0(HeuristicInterface):

    def handle_rule(self, bdg_rules, sota_rules, stratified_rules, lpopt_rules,
            variable_graph : VariableGraphDataStructure, stratified_variables,
            graph_ds : GraphDataStructure,
            head_atoms_scc_membership, body_atoms_scc_membership,
            maximum_variables_in_literal, is_constraint,
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

        can_handle_rule = is_tight is True and has_aggregate is False and in_minimize_statement is False and all_comparison_variables_safe_by_predicate is True

        if self.rule_dictionary[rule_position].in_program_rules is True and can_handle_rule is True and body_is_stratified is False:
            # If user specifies grounded by BDG, then ground by BDG (if possible in theory)
            # If stratified -> Never use bdg
            bdg_rules[rule_position] = True
        elif self.rule_dictionary[rule_position].in_lpopt_rules is True and self.enable_lpopt is True:
            lpopt_rules[rule_position] = True
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
            

            if is_constraint is True and tw_effective > maximum_variables_in_literal and all_comparison_variables_safe_by_predicate is True:
                # Constraint:
                bdg_rules[rule_position] = True

            elif is_tight is True and tw_effective > maximum_variables_in_literal * 2 and all_comparison_variables_safe_by_predicate is True:
                # Tight normal:
                bdg_rules[rule_position] = True
            
            elif is_tight is False and tw_effective > maximum_variables_in_literal * 3 and all_comparison_variables_safe_by_predicate is True:
                # Non-tight normal:
                bdg_rules[rule_position] = True

            elif self.enable_lpopt is True and self.sota_grounder == SotaGrounder.GRINGO and (tw_full == maximum_variables_in_literal or tw_full < full_variable_graph.graph.number_of_nodes()):
                # Only use when expliticly enabled (enable lpopt/TW-Aware rewriting)
                # IDLV implemented Lpopt tools, so only potentially use it for Gringo.
                # As number of variables = full_variable_graph.number_of_nodes
                # Then using lpopt reduces number of variables to ground to tw_full (bag size)

                lpopt_rules[rule_position] = True

            else:
                #sota_rules.append(rule_position)
                sota_rules[rule_position] = True
        
        self.rule_dictionary[rule_position].add_variable_graph(full_variable_graph)
        self.rule_dictionary[rule_position].add_variable_no_head_graph(variable_no_head_graph)
        self.rule_dictionary[rule_position].add_is_tight(is_tight)
        self.rule_dictionary[rule_position].add_is_constraint(is_constraint)

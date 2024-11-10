


import networkx as nx

from heuristic_splitter.graph_data_structure import GraphDataStructure

class GroundingStrategyGenerator:

    def __init__(self, graph_ds: GraphDataStructure, bdg_rules, sota_rules, stratified_rules, constraint_rules, lpopt_rules, rule_dictionary):

        self.graph_ds = graph_ds
        self.bdg_rules = bdg_rules
        self.sota_rules = sota_rules
        self.stratified_rules = stratified_rules
        self.constraint_rules = constraint_rules
        self.lpopt_rules = lpopt_rules
        self.rule_dictionary = rule_dictionary

    
    def get_grounding_strategy_dependency_indices(self, current_scc_nodes, condensed_graph_inverted,scc_node_to_grounding_order_lookup):

        depends_on = []
        for node in current_scc_nodes:
            depends_on += condensed_graph_inverted.neighbors(node)

        grounding_strategy_dependencies = set()
        for node in depends_on:
            for grounding_strategy_index in scc_node_to_grounding_order_lookup[node]:
                grounding_strategy_dependencies.add(grounding_strategy_index)

        current_scc_nodes.clear()

        return grounding_strategy_dependencies

    def add_grounding_strategy_level(self, grounding_strategy, current_sota_grounded_rules,
        current_bdg_grounded_rules, current_lpopt_grounded_rules, grounding_strategy_dependencies):

        if len(current_sota_grounded_rules) > 0 or len(current_bdg_grounded_rules) > 0 or len(current_lpopt_grounded_rules) > 0:
            grounding_strategy.append({
                "sota":current_sota_grounded_rules.copy(),
                "bdg":current_bdg_grounded_rules.copy(),
                "lpopt":current_lpopt_grounded_rules.copy(),
                "dependencies": grounding_strategy_dependencies.copy()
            })
            
            current_sota_grounded_rules.clear()
            current_bdg_grounded_rules.clear()
            current_lpopt_grounded_rules.clear()

    def generate_grounding_strategy(self, grounding_strategy):
 
        positive_dependency_graph = self.graph_ds.get_positive_nx_object()
        
        sccs = list(nx.strongly_connected_components(positive_dependency_graph)) 
        condensed_graph = nx.condensation(positive_dependency_graph, sccs)
        condensed_graph_inverted = condensed_graph.reverse()

        scc_node_to_grounding_order_lookup = {}
        non_stratified_topological_order = self.handle_stratified_part(sccs, positive_dependency_graph, scc_node_to_grounding_order_lookup, condensed_graph, condensed_graph_inverted, grounding_strategy)

        self.handle_non_stratified_part(non_stratified_topological_order, sccs, positive_dependency_graph, scc_node_to_grounding_order_lookup, condensed_graph_inverted, grounding_strategy)

        self.post_process_grounding_strategy(grounding_strategy)

        return grounding_strategy



    def handle_stratified_part(self, sccs, positive_dependency_graph, scc_node_to_grounding_order_lookup, condensed_graph, condensed_graph_inverted, grounding_strategy):

        topological_order = list(nx.topological_sort(condensed_graph))
        
        current_sota_grounded_rules = []
        current_bdg_grounded_rules = []
        current_lpopt_grounded_rules = []

        current_scc_nodes = []

        # ---- STRATIFIED PROGRAM HANDLING ----
        non_stratified_topological_order = [] 

        potentially_non_stratified = []

        for scc_index in topological_order:
        
            scc = sccs[scc_index]
            subgraph = positive_dependency_graph.subgraph(scc)
        
            has_non_stratified_rule = False
            has_stratified_rule = False
        
            for node in subgraph.nodes:
                # All those rules that have "node" as a head.
                rules = self.graph_ds.node_to_rule_lookup[node]

                if len(rules) > 0:
                    for rule in rules:
                        cur_rule = self.rule_dictionary[rule]
                        cur_rule.add_scc(scc)
            
                        if rule in self.stratified_rules:
                            current_sota_grounded_rules.append(rule)
                            has_stratified_rule = True
                        else:
                            has_non_stratified_rule = True
                else:
                    # For facts and special rules.
                    if condensed_graph.in_degree(scc_index) == 0:
                        has_stratified_rule = True
                    else:
                        potentially_non_stratified.append(scc_index)
                        non_stratified_topological_order.append(scc_index)

        
            if has_non_stratified_rule is True:
                non_stratified_topological_order.append(scc_index)
        
            if has_stratified_rule is True:
                # Stratified rules are handled here:
                scc_node_to_grounding_order_lookup[scc_index] = [0]
                current_scc_nodes.append(scc_index)

        for potentially_non_stratified_scc_index in potentially_non_stratified:
            # This is only necessary for special rules that are introduced by e.g., choice or disjunctive rules.
            depends_on = condensed_graph_inverted.neighbors(potentially_non_stratified_scc_index)
            all_dependencies_stratified = True
            for dependency in depends_on:
                # If all dependencies are in the lookup-table, then it is surely stratified.
                if dependency not in scc_node_to_grounding_order_lookup:
                    all_dependencies_stratified = False
                    break
            if all_dependencies_stratified is True:
                # If stratified adjust data structures
                non_stratified_topological_order.remove(potentially_non_stratified_scc_index)
                scc_node_to_grounding_order_lookup[potentially_non_stratified_scc_index] = [0]
                current_scc_nodes.append(potentially_non_stratified_scc_index)
            # If not stratified do nothing.

        
        # Stratified part can only depend on stratified part
        grounding_strategy_dependencies = set()
        grounding_strategy_dependencies.add(0)

        self.add_grounding_strategy_level(grounding_strategy, current_sota_grounded_rules,
            current_bdg_grounded_rules, current_lpopt_grounded_rules, grounding_strategy_dependencies)
        return non_stratified_topological_order


    def handle_non_stratified_part(self, non_stratified_topological_order, sccs, positive_dependency_graph, scc_node_to_grounding_order_lookup, condensed_graph_inverted, grounding_strategy):
    
        current_sota_grounded_rules = []
        current_bdg_grounded_rules = []
        current_lpopt_grounded_rules = []
        current_scc_nodes = []

        next_sota_grounded_rules = []
        next_bdg_grounded_rules = []
        next_lpopt_grounded_rules = []
        next_scc_nodes = []

        # ---- NON-STRATIFIED PROGRAM HANDLING ----
        for scc_index in non_stratified_topological_order:
        
            scc = sccs[scc_index]
            subgraph = positive_dependency_graph.subgraph(scc)
        
            scc_node_to_grounding_order_lookup[scc_index] = [len(grounding_strategy)]
            current_scc_nodes.append(scc_index)
        
            exists_bdg_grounded_rule = False
            exists_potential_lpopt_rule = False

            exists_disjunctive_rule = False
            exists_non_tight_rule = False
        
            for node in subgraph.nodes:
                # All those rules that have "node" as a head.
                rules = self.graph_ds.node_to_rule_lookup[node]
        
                for rule in rules:
                    cur_rule = self.rule_dictionary[rule]
                    cur_rule.add_scc(scc)
        
                    if rule in self.bdg_rules:
                        exists_bdg_grounded_rule = True
                    
                    if rule in self.lpopt_rules:
                        exists_potential_lpopt_rule = True

                    if cur_rule.is_disjunctive is True:
                        exists_disjunctive_rule = True

                    if cur_rule.is_tight is not None and cur_rule.is_tight is False:
                        exists_non_tight_rule = True

            bdg_supports_asp_program_class = True
            if exists_disjunctive_rule is True and exists_non_tight_rule is True:
                # BDG is a reduction from Sigma_p^2 (non-ground normal) to Sigma_p^2 (ground disjunctive),
                # if there is a disjunctive head cycle, the complexity would be Sigma_p^3,
                # therefore 'bdg_supports_asp_program_class' is false if the complexity is Sigma_p^3 (so the wrong program class).
                bdg_supports_asp_program_class = False

            if (exists_bdg_grounded_rule is True and bdg_supports_asp_program_class is True) or exists_potential_lpopt_rule is True:
        
                grounding_strategy_dependencies = self.get_grounding_strategy_dependency_indices(current_scc_nodes, 
                    condensed_graph_inverted, scc_node_to_grounding_order_lookup)
                self.add_grounding_strategy_level(grounding_strategy, current_sota_grounded_rules,
                    current_bdg_grounded_rules, current_lpopt_grounded_rules, grounding_strategy_dependencies)
        
            is_tight = True
            for node in subgraph.nodes:
        
                rules = self.graph_ds.node_to_rule_lookup[node]

                for rule in rules:
                    if bdg_supports_asp_program_class is False:
                        # Handle special case
                        current_sota_grounded_rules.append(rule)
                        continue
        
                    if exists_bdg_grounded_rule is False:
                        # These rules include the "external support rules" for a cycle
                        if rule in self.sota_rules:
                            current_sota_grounded_rules.append(rule)
                        elif rule in self.stratified_rules:
                            pass
                        elif rule in self.lpopt_rules:
                            current_lpopt_grounded_rules.append(rule)
                        else:
                            print(f"[ERROR] - Cannot associate rules: {rule}")
                            print(str(self.rule_dictionary[rule]))
                            raise NotImplementedError()
                    else:
                        if cur_rule.is_tight is True:
                            # These rules include the "external support rules" for a cycle
                            if rule in self.sota_rules:
                                current_sota_grounded_rules.append(rule)
                            elif rule in self.bdg_rules:
                                current_bdg_grounded_rules.append(rule)
                            elif rule in self.stratified_rules:
                                # If stratified -> Already handled
                                pass
                            elif rule in self.lpopt_rules:
                                current_lpopt_grounded_rules.append(rule)
                            else:
                                print(f"[ERROR] - Cannot associate rules: {rule}")
                                raise NotImplementedError()
                        else:
                            is_tight = False
                            # The actual cyclic rules
                            if rule in self.sota_rules:
                                next_sota_grounded_rules.append(rule)
                            elif rule in self.bdg_rules:
                                next_bdg_grounded_rules.append(rule)
                            elif rule in self.stratified_rules:
                                # If stratified -> Already handled
                                pass
                            elif rule in self.lpopt_rules:
                                next_lpopt_grounded_rules.append(rule)
                            else:
                                print(f"[ERROR] - Cannot associate rules: {rule}")
                                raise NotImplementedError()
        
            #if exists_bdg_grounded_rule is True or is_tight is False:
            if (exists_bdg_grounded_rule is True and bdg_supports_asp_program_class is True) or exists_potential_lpopt_rule is True:
                # Handle BDG rule and lpopt rule (add layer)
                current_scc_nodes.append(scc_index)
                scc_node_to_grounding_order_lookup[scc_index].append(len(grounding_strategy))
        
                grounding_strategy_dependencies = self.get_grounding_strategy_dependency_indices(current_scc_nodes, 
                    condensed_graph_inverted, scc_node_to_grounding_order_lookup)
        
                self.add_grounding_strategy_level(grounding_strategy, current_sota_grounded_rules,
                    current_bdg_grounded_rules, current_lpopt_grounded_rules, grounding_strategy_dependencies)

            if is_tight is False and ((exists_bdg_grounded_rule is True and bdg_supports_asp_program_class is True) or exists_potential_lpopt_rule is True):
                next_scc_nodes.append(scc_index)
                scc_node_to_grounding_order_lookup[scc_index].append(len(grounding_strategy))
        
                grounding_strategy_dependencies = self.get_grounding_strategy_dependency_indices(current_scc_nodes, 
                    condensed_graph_inverted, scc_node_to_grounding_order_lookup)
        
                self.add_grounding_strategy_level(grounding_strategy, next_sota_grounded_rules,
                    next_bdg_grounded_rules, next_lpopt_grounded_rules, grounding_strategy_dependencies)
        
        grounding_strategy_dependencies = self.get_grounding_strategy_dependency_indices(current_scc_nodes, 
            condensed_graph_inverted, scc_node_to_grounding_order_lookup)
        self.add_grounding_strategy_level(grounding_strategy, current_sota_grounded_rules,
            current_bdg_grounded_rules, current_lpopt_grounded_rules, grounding_strategy_dependencies)
        
    def post_process_grounding_strategy(self, grounding_strategy):
        """
        May reduce the number of calls to the grounder gringo in the grounding strategy.
        - If only SOTA rules, then ground all in one go
        - If current and previous 
        """

        #print(grounding_strategy)
        #print("<<< BEFORE >>> AFTER:")

        changed = True

        while changed is True:
            changed = False

            for grounding_strategy_index in range(len(grounding_strategy)):

                sota_list = grounding_strategy[grounding_strategy_index]["sota"]
                bdg_list = grounding_strategy[grounding_strategy_index]["bdg"]
                lpopt_list = grounding_strategy[grounding_strategy_index]["lpopt"]
                dependencies_list = grounding_strategy[grounding_strategy_index]["dependencies"]


                if len(bdg_list) == 0 and len(sota_list) > 0 and len(lpopt_list) == 0:
                    # Only may change if BDG strategy is not used:
                    # And only changes for SOTA rules

                    dependency_list_has_bdg_rules = False
                    highest_not_self_dependency_list_index = -1
                    other_dependencies = []

                    for dependency_index in dependencies_list:

                        if dependency_index == grounding_strategy_index:
                            continue


                        tmp_bdg_list = grounding_strategy[dependency_index]["bdg"]
                        tmp_lpopt_list = grounding_strategy[dependency_index]["lpopt"]

                        if len(tmp_bdg_list) > 0 or len(tmp_lpopt_list) > 0:
                            dependency_list_has_bdg_rules = True
                            break

                        other_dependencies.append(dependency_index)
                        if dependency_index > highest_not_self_dependency_list_index:
                            highest_not_self_dependency_list_index = dependency_index

                    if dependency_list_has_bdg_rules is False and highest_not_self_dependency_list_index >= 0:
                        final_list = grounding_strategy[highest_not_self_dependency_list_index]["sota"] + sota_list
                        grounding_strategy[highest_not_self_dependency_list_index]["sota"] = final_list
                        grounding_strategy[highest_not_self_dependency_list_index]["dependencies"] = set(list(grounding_strategy[highest_not_self_dependency_list_index]["dependencies"]) + other_dependencies)
                        grounding_strategy[grounding_strategy_index]["sota"] = []
                        changed = True

        for grounding_strategy_reverse_index in range(len(grounding_strategy)-1,-1,-1):

            bdg_rules = grounding_strategy[grounding_strategy_reverse_index]["bdg"]
            sota_rules = grounding_strategy[grounding_strategy_reverse_index]["sota"]
            lpopt_rules = grounding_strategy[grounding_strategy_reverse_index]["lpopt"]

            if len(bdg_rules) == 0 and len(sota_rules) == 0 and len(lpopt_rules) == 0:
                del grounding_strategy[grounding_strategy_reverse_index]
            else:
                break
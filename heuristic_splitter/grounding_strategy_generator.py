


import networkx as nx

from heuristic_splitter.graph_data_structure import GraphDataStructure

class GroundingStrategyGenerator:

    def __init__(self, graph_ds: GraphDataStructure, bdg_rules, sota_rules, lpopt_rules, constraint_rules):

        self.graph_ds = graph_ds
        self.bdg_rules = bdg_rules
        self.sota_rules = sota_rules
        self.lpopt_rules = lpopt_rules
        self.constraint_rules = constraint_rules


    def add_grounding_strategy_level(self, grounding_strategy, current_sota_grounded_rules, current_bdg_grounded_rules, current_lpopt_grounded_rules):

        if len(current_sota_grounded_rules) > 0 or len(current_bdg_grounded_rules) > 0 or len(current_lpopt_grounded_rules) > 0:
            grounding_strategy.append({
                "sota":current_sota_grounded_rules.copy(),
                "bdg":current_bdg_grounded_rules.copy(),
                "lpopt": current_lpopt_grounded_rules.copy()
            })
            
            current_sota_grounded_rules.clear()
            current_lpopt_grounded_rules.clear()
            current_bdg_grounded_rules.clear()

    def generate_grounding_strategy(self):

        grounding_strategy = []

 
        G = self.graph_ds.get_positive_nx_object()
        
        sccs = list(nx.strongly_connected_components(G)) 
        condensed_graph = nx.condensation(G, sccs)
        topological_order = list(nx.topological_sort(condensed_graph))
        
        current_sota_grounded_rules = []
        current_bdg_grounded_rules = []
        current_lpopt_grounded_rules = []

        for scc_index in topological_order:
            scc = sccs[scc_index]
            subgraph = G.subgraph(scc)

            exists_bdg_grounded_rule = False

            for node in subgraph.nodes:
                # All those rules that have "node" as a head.
                rules = self.graph_ds.node_to_rule_lookup[node]

                for rule in rules:
                    if rule in self.bdg_rules:
                        exists_bdg_grounded_rule = True

            
            if exists_bdg_grounded_rule is True:
                self.add_grounding_strategy_level(grounding_strategy, current_sota_grounded_rules,
                    current_bdg_grounded_rules, current_lpopt_grounded_rules)
 
            for node in subgraph.nodes:

                rules = self.graph_ds.node_to_rule_lookup[node]

                for rule in rules:
                    if rule in self.sota_rules:
                        current_sota_grounded_rules.append(rule)
                    elif rule in self.bdg_rules:
                        current_bdg_grounded_rules.append(rule)
                    elif rule in self.lpopt_rules:
                        current_lpopt_grounded_rules.append(rule)
                    else:
                        print(f"[ERROR] - Cannot associate rules: {rule}")
                        raise NotImplementedError()

            if exists_bdg_grounded_rule is True:
                self.add_grounding_strategy_level(grounding_strategy, current_sota_grounded_rules,
                    current_bdg_grounded_rules, current_lpopt_grounded_rules)

        ## CONSTRAINT HANDLING: 

        exists_bdg_grounded_rule = False

        for rule in self.constraint_rules:
            if rule in self.bdg_rules:
                exists_bdg_grounded_rule = True

        if exists_bdg_grounded_rule is True:
            self.add_grounding_strategy_level(grounding_strategy, current_sota_grounded_rules,
                current_bdg_grounded_rules, current_lpopt_grounded_rules)

        for rule in self.constraint_rules: 
            if rule in self.sota_rules:
                current_sota_grounded_rules.append(rule)
            elif rule in self.bdg_rules:
                current_bdg_grounded_rules.append(rule)
            elif rule in self.lpopt_rules:
                current_lpopt_grounded_rules.append(rule)
            else:
                print(f"[ERROR] - Cannot associate rules: {rule}")
                raise NotImplementedError()

        self.add_grounding_strategy_level(grounding_strategy, current_sota_grounded_rules,
            current_bdg_grounded_rules, current_lpopt_grounded_rules)

        return grounding_strategy

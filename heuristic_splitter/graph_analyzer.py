import networkx as nx

from heuristic_splitter.graph_data_structure import GraphDataStructure

class GraphAnalyzer:

    def __init__(self, graph_ds: GraphDataStructure):

        self.graph_ds = graph_ds

    def start(self):
        self.compute_stratification_labels()

        self.compute_positive_dg_sccs()



    def compute_stratification_labels(self):
        
        G = self.graph_ds.get_full_nx_object()
        nx.set_node_attributes(G, False, "nstrat")
        
        sccs = list(nx.strongly_connected_components(G))
        
        condensed_graph = nx.condensation(G, sccs)
        nx.set_node_attributes(condensed_graph, False, "nstrat")
        
        topological_order = list(nx.topological_sort(condensed_graph))
        
        nstrat_nodes = []
        # Adding the "nstrat" label to the negative cycle-SCCs:
        for scc_index in topological_order:
            scc = sccs[scc_index]
            subgraph = G.subgraph(scc)
            negative_edge_count = sum(1 for u, v, d in subgraph.edges(data=True) if d['label'] == -1)
            if negative_edge_count >= 2:
                condensed_graph.nodes[scc_index]["nstrat"] = True
                nstrat_nodes.append(scc_index)
        
        # Propagate the "nstrat" label:
        for start_node in nstrat_nodes:
            reachable_nodes = nx.descendants(condensed_graph, start_node)
            for node in reachable_nodes:
                condensed_graph.nodes[node]["nstrat"] = True
        
        # Adding the "nstrat" label to the negative original Graph nodes:
        for scc_index in topological_order:
            scc = sccs[scc_index]
            subgraph = G.subgraph(scc)
            if condensed_graph.nodes[scc_index]["nstrat"] is True:
                for node in subgraph.nodes:
                    G.nodes[node]["nstrat"] = True
                    self.graph_ds.add_not_stratified_index(node)
        
        
        
                
            
    def compute_positive_dg_sccs(self):
        """
        Computes for every atom its SCC membership,
        and therefore is essential to determine if a rule is in a tight-part.
        """

        G = self.graph_ds.get_positive_nx_object()
        sccs = list(nx.strongly_connected_components(G))

        scc_index = 0
        for scc in sccs:

            for node in scc:
                atom_name = self.graph_ds.index_to_predicate_lookup[node]

                self.graph_ds.add_positive_dg_predicate_to_scc_index(atom_name, scc_index)
                
            scc_index += 1


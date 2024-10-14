import networkx as nx

from heuristic_splitter.graph_data_structure import GraphDataStructure

class GraphAnalyzer:

    def __init__(self, graph_ds: GraphDataStructure):

        self.graph_ds = graph_ds


    def start(self):

        G = self.graph_ds.get_nx_object()
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




        
                
            


import matplotlib.pyplot as plt
import networkx as nx

class GraphDataStructure:

    def __init__(self):

        self.current_node_index = 0

        self.predicate_to_index_lookup = {}
        self.index_to_predicate_lookup = {}

        self.not_stratified_index = {}

        self.graph = nx.DiGraph()

    def add_edge(self, head_literal, body_literal, signum):
        """
        - Head and body literals as strings
        - Signum as 1 (positive, e.g., "a"), or -1 (negative - e.g., "not a")
        """

        if body_literal not in self.predicate_to_index_lookup:
            self.graph.add_node(self.current_node_index)

            self.predicate_to_index_lookup[body_literal] = self.current_node_index
            self.index_to_predicate_lookup[self.current_node_index] = body_literal

            self.current_node_index += 1

        if head_literal not in self.predicate_to_index_lookup:
            self.graph.add_node(self.current_node_index)

            self.predicate_to_index_lookup[head_literal] = self.current_node_index
            self.index_to_predicate_lookup[self.current_node_index] = head_literal
            
            self.current_node_index += 1

        body_index = self.predicate_to_index_lookup[body_literal]
        head_index = self.predicate_to_index_lookup[head_literal]

        self.graph.add_edge(body_index, head_index, label=signum)

    def add_not_stratified_index(self, node_index):

        self.not_stratified_index[node_index] = True



    def plot_graph(self):
        # Define edge labels for visualization
        G = self.graph
        edge_labels = {(u, v): d['label'] for u, v, d in G.edges(data=True)}

        # Draw the graph
        pos = nx.spring_layout(G)  # layout for positions
        nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=1500, font_size=10, font_weight='bold', arrows=True)
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red')

        node_labels = {node: f"{node} (nstrat)" if G.nodes[node]["nstrat"] else f"{node}" for node in G.nodes()}

        nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=12, font_family="sans-serif")
        
        # Show the plot
        plt.show()

    def get_nx_object(self):
        return self.graph




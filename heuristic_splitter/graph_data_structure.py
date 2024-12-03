
#import matplotlib.pyplot as plt
import networkx as nx

class GraphDataStructure:

    def __init__(self):

        self.current_node_index = 0
        self.predicate_to_index_lookup = {}
        self.index_to_predicate_lookup = {}

        self.not_stratified_index = {}
        self.positive_predicate_scc_index = {}
        self.positive_sccs = []

        self.full_graph = nx.DiGraph()
        self.positive_graph = nx.DiGraph()

        self.node_to_rule_lookup = {}


    def add_vertex(self, predicate):

        if predicate not in self.predicate_to_index_lookup:
            self.predicate_to_index_lookup[predicate] = self.current_node_index
            self.index_to_predicate_lookup[self.current_node_index] = predicate

            self.full_graph.add_node(self.current_node_index)
            self.positive_graph.add_node(self.current_node_index)

            if self.current_node_index not in self.node_to_rule_lookup:
                self.node_to_rule_lookup[self.current_node_index] = []

            self.current_node_index += 1

    def add_edge(self, head_literal, body_literal, signum):
        """
        - Head and body literals as strings
        - Signum as 1 (positive, e.g., "a"), or -1 (negative - e.g., "not a")
        """

        if body_literal not in self.predicate_to_index_lookup:
            self.full_graph.add_node(self.current_node_index)

            self.positive_graph.add_node(self.current_node_index)

            self.predicate_to_index_lookup[body_literal] = self.current_node_index
            self.index_to_predicate_lookup[self.current_node_index] = body_literal

            self.current_node_index += 1

        if head_literal not in self.predicate_to_index_lookup:
            self.full_graph.add_node(self.current_node_index)

            self.positive_graph.add_node(self.current_node_index)

            self.predicate_to_index_lookup[head_literal] = self.current_node_index
            self.index_to_predicate_lookup[self.current_node_index] = head_literal
            
            self.current_node_index += 1

        body_index = self.predicate_to_index_lookup[body_literal]
        head_index = self.predicate_to_index_lookup[head_literal]

        self.full_graph.add_edge(body_index, head_index, label=signum)

        if signum > 0:
            self.positive_graph.add_edge(body_index, head_index)


    def add_not_stratified_index(self, node_index):
        self.not_stratified_index[node_index] = True

    def predicate_is_stratified(self, node):
        """
        - Return true if node is stratified
        - False otherwise
        """
        if node.name in self.predicate_to_index_lookup:
            node_index = self.predicate_to_index_lookup[node.name]
            if node_index in self.not_stratified_index:
                # not_stratified contains those that are NOT stratified
                return False
            else:
                return True

        else:
            print(f"[ERROR] -> Predicate name not found: {node.name}")
            raise Exception()

    def add_positive_dg_predicate_to_scc_index(self, atom_name, scc_index):

        if atom_name in self.positive_graph:
            print(f"[ERROR] - Atom name {atom_name} already in lookup table!")
            raise Exception()

        self.positive_predicate_scc_index[atom_name] = scc_index

    def get_scc_index_of_atom(self, atom_name):
        return self.positive_predicate_scc_index[atom_name]


    def plot_graph(self):
        # Define edge labels for visualization
        G = self.full_graph
        edge_labels = {(u, v): d['label'] for u, v, d in G.edges(data=True)}

        # Draw the graph
        pos = nx.spring_layout(G)  # layout for positions
        nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=1500, font_size=10, font_weight='bold', arrows=True)
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red')

        node_labels = {node: f"{node} (nstrat)" if G.nodes[node]["nstrat"] else f"{node}" for node in G.nodes()}

        nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=12, font_family="sans-serif")
        
        # Show the plot
        plt.show()

    def get_full_nx_object(self):
        return self.full_graph

    def get_positive_nx_object(self):
        return self.positive_graph



    def add_node_to_rule_lookup(self, rule_positions, predicate_name):
        vertex_index = self.predicate_to_index_lookup[predicate_name]

        if vertex_index not in self.node_to_rule_lookup:
            self.node_to_rule_lookup[vertex_index] = []

        self.node_to_rule_lookup[vertex_index] += rule_positions





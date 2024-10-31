
import os
import matplotlib.pyplot as plt
import networkx as nx

import subprocess

class VariableGraphDataStructure:


    def __init__(self):

        self.current_node_index = 0

        self.predicate_to_index_lookup = {}
        self.index_to_variable_lookup = {}

        self.graph = nx.Graph()

    def add_node(self, variable):
 
        if variable not in self.predicate_to_index_lookup:
            self.graph.add_node(self.current_node_index)

            self.predicate_to_index_lookup[variable] = self.current_node_index
            self.index_to_variable_lookup[self.current_node_index] = variable

            self.current_node_index += 1       


    def add_edge(self, variable_1, variable_2):
        """
        Adding an edge between two variables (if they occur in the same literal)
        """

        if variable_2 not in self.predicate_to_index_lookup:
            self.graph.add_node(self.current_node_index)

            self.predicate_to_index_lookup[variable_2] = self.current_node_index
            self.index_to_variable_lookup[self.current_node_index] = variable_2

            self.current_node_index += 1

        if variable_1 not in self.predicate_to_index_lookup:
            self.graph.add_node(self.current_node_index)

            self.predicate_to_index_lookup[variable_1] = self.current_node_index
            self.index_to_variable_lookup[self.current_node_index] = variable_1
            
            self.current_node_index += 1

        variable_1_index = self.predicate_to_index_lookup[variable_2]
        variable_2_index = self.predicate_to_index_lookup[variable_1]

        self.graph.add_edge(variable_1_index, variable_2_index)
    
    def remove_variable(self, variable):
        if variable in self.predicate_to_index_lookup:
            variable_index = self.predicate_to_index_lookup[variable]
            self.graph.remove_node(variable_index)
        else:
            print(f"[ERROR] - Could not find variable: {variable}")
            raise Exception(f"[ERROR] - Could not find variable: {variable}")

    def plot_graph(self):

        G = self.graph

        pos = nx.spring_layout(G)  # layout for positions
        nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=1500, font_size=10, font_weight='bold', arrows=True)
        
        # Show the plot
        plt.show()

    def get_nx_object(self):
        return self.graph

    def clone(self):

        clone = VariableGraphDataStructure()
        clone.graph = self.graph.copy()
        clone.current_node_index = self.current_node_index
        clone.predicate_to_index_lookup = self.predicate_to_index_lookup.copy()
        clone.index_to_variable_lookup = self.index_to_variable_lookup.copy()

        return clone



    def compute_networkx_bag_size(self):
        """
        We return the bag-size.
        """

        treewidth, _ = nx.algorithms.approximation.treewidth_min_fill_in(self.graph)

        return treewidth + 1

    def networkx_to_gr_format(self):

        output_string = ""

        output_string += f"p tw {self.graph.number_of_nodes()} {self.graph.number_of_edges()}\n"

        for v_start, v_end in self.graph.edges():
            output_string += f"{v_start + 1} {v_end + 1}\n"

        return output_string

    def parse_treewidth_from_gr_output_format(self, content):

        tw_line = content[0]
        # Parse other content lines as bags if needed

        bag_size = tw_line.split(" ")[3]

        return bag_size

    def compute_twalgor_bag_size(self):
        """
        With: https://github.com/twalgor/tw
        Local Java isntallation and compilation needed
        """

        if self.graph.number_of_edges() <= 0:
            return 0
        elif self.graph.number_of_edges() == 1 or self.graph.number_of_edges() == 2:
            return 1

        gr_input_format_string = self.networkx_to_gr_format()

        tmp_folder_path = os.path.join(*["tmp","twalgor"])
        tmp_input_file_path = os.path.join(tmp_folder_path, "input.txt")
        tmp_output_file_path = os.path.join(tmp_folder_path, "output.txt")
        tmp_temp_file_path = os.path.join(tmp_folder_path, "tmp.txt")

        os.makedirs(tmp_folder_path, exist_ok=True)

        with open(tmp_input_file_path, 'w') as file:
            file.write(gr_input_format_string)

        result = subprocess.run(['java','-cp', '/home/thinklex/Dropbox/2019_x_Studium/Masters_Thesis/04_automatic_splitting/newground/twalgor','io.github.twalgor.main.ExactTW',tmp_input_file_path, tmp_output_file_path, tmp_temp_file_path], capture_output=True, text=True)

        print("JAVA - OUTPUT - SHOULD BE EMPTY:")
        print(result.stdout)
        print(result.stderr)
        print("JAVA OUTPUT FINISHED")

        with open(tmp_output_file_path, 'r') as file:
            content = file.readlines()

            bag_size = self.parse_treewidth_from_gr_output_format(content)
        
        
        return int(bag_size)

    def is_reachable(self, v1, v2):
        return nx.has_path(self.graph, v1, v2)




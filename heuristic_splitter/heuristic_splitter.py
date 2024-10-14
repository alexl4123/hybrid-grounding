
from clingo.ast import ProgramBuilder, parse_string

from heuristic_splitter.graph_creator_transformer import GraphCreatorTransformer
from heuristic_splitter.graph_data_structure import GraphDataStructure
from heuristic_splitter.graph_analyzer import GraphAnalyzer

class HeuristicSplitter:

    def __init__(self, heuristic_strategy):

        self.heuristic_strategy = heuristic_strategy


    def start(self, contents):

        graph_ds = GraphDataStructure()

        graph_transformer = GraphCreatorTransformer(graph_ds)
        parse_string(contents, lambda stm: graph_transformer(stm))


        graph_analyzer = GraphAnalyzer(graph_ds)
        graph_analyzer.start()
        
        print(graph_ds.not_stratified_index) 
        # TODO -> Implement the heuristic from here
        #graph_ds.plot_graph()
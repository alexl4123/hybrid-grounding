
from clingo.ast import ProgramBuilder, parse_string

from heuristic_splitter.graph_creator_transformer import GraphCreatorTransformer
from heuristic_splitter.graph_data_structure import GraphDataStructure
from heuristic_splitter.graph_analyzer import GraphAnalyzer

from heuristic_splitter.heuristic_transformer import HeuristicTransformer

from heuristic_splitter.heuristic_strategy import HeuristicStrategy
from heuristic_splitter.treewidth_computation_strategy import TreewidthComputationStrategy

from heuristic_splitter.heuristic_0 import Heuristic0

class HeuristicSplitter:

    def __init__(self, heuristic_strategy: HeuristicStrategy, treewidth_strategy: TreewidthComputationStrategy):

        self.heuristic_strategy = heuristic_strategy
        self.treewidth_strategy = treewidth_strategy


    def start(self, contents):

        graph_ds = GraphDataStructure()

        graph_transformer = GraphCreatorTransformer(graph_ds)
        parse_string(contents, lambda stm: graph_transformer(stm))


        graph_analyzer = GraphAnalyzer(graph_ds)
        graph_analyzer.start()

        if self.heuristic_strategy == HeuristicStrategy.TREEWIDTH_PURE:
            heuristic = Heuristic0(self.treewidth_strategy)
        else:
            raise NotImplementedError()

        bdg_rules = []
        sota_rules = []
        lpopt_rules = []
        
        heuristic_transformer = HeuristicTransformer(graph_ds, heuristic, bdg_rules, sota_rules, lpopt_rules)
        parse_string(contents, lambda stm: heuristic_transformer(stm))

        if len(lpopt_rules) > 0:
            raise NotImplementedError()

        
        for sota_rule in sota_rules:
            print(str(sota_rule))

        if len(bdg_rules) > 0:
            print("#program rules.")

            for bdg_rule in bdg_rules:
                print(str(bdg_rule))

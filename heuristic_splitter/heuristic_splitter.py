
from clingo.ast import ProgramBuilder, parse_string

from heuristic_splitter.graph_creator_transformer import GraphCreatorTransformer
from heuristic_splitter.graph_data_structure import GraphDataStructure
from heuristic_splitter.graph_analyzer import GraphAnalyzer

from heuristic_splitter.heuristic_transformer import HeuristicTransformer

from heuristic_splitter.heuristic_strategy import HeuristicStrategy
from heuristic_splitter.treewidth_computation_strategy import TreewidthComputationStrategy
from heuristic_splitter.grounding_strategy import GroundingStrategy

from heuristic_splitter.heuristic_0 import Heuristic0

from heuristic_splitter.grounding_strategy_generator import GroundingStrategyGenerator
from heuristic_splitter.grounding_strategy_handler import GroundingStrategyHandler

class HeuristicSplitter:

    def __init__(self, heuristic_strategy: HeuristicStrategy, treewidth_strategy: TreewidthComputationStrategy, grounding_strategy:GroundingStrategy, debug_mode):

        self.heuristic_strategy = heuristic_strategy
        self.treewidth_strategy = treewidth_strategy
        self.grounding_strategy = grounding_strategy
        self.debug_mode = debug_mode


    def start(self, contents):

        graph_ds = GraphDataStructure()
        rule_dictionary = {}

        graph_transformer = GraphCreatorTransformer(graph_ds, rule_dictionary)
        parse_string(contents, lambda stm: graph_transformer(stm))

        graph_analyzer = GraphAnalyzer(graph_ds)
        graph_analyzer.start()

        if self.heuristic_strategy == HeuristicStrategy.TREEWIDTH_PURE:
            heuristic = Heuristic0(self.treewidth_strategy, rule_dictionary)
        else:
            raise NotImplementedError()

        bdg_rules = []
        sota_rules = []
        lpopt_rules = []
        constraint_rules = []
        
        heuristic_transformer = HeuristicTransformer(graph_ds, heuristic, bdg_rules, sota_rules, lpopt_rules, constraint_rules)
        parse_string(contents, lambda stm: heuristic_transformer(stm))

        if len(lpopt_rules) > 0:
            raise NotImplementedError()

        generator_grounding_strategy = GroundingStrategyGenerator(graph_ds, bdg_rules, sota_rules, lpopt_rules, constraint_rules, rule_dictionary)
        grounding_strategy = generator_grounding_strategy.generate_grounding_strategy()

        if self.debug_mode is True:
            print(">>>>> GROUNDING STRATEGY:")
            print(grounding_strategy)
            print("<<<<")

        if self.grounding_strategy == GroundingStrategy.FULL:

            grounding_handler = GroundingStrategyHandler(grounding_strategy, rule_dictionary, graph_ds, self.debug_mode)
            grounding_handler.ground()

        else:

            for sota_rule in sota_rules:
                print(str(rule_dictionary[sota_rule]))

            if len(bdg_rules) > 0:
                print("#program rules.")

                for bdg_rule in bdg_rules:
                    print(str(rule_dictionary[bdg_rule]))

            if len(lpopt_rules) > 0:
                print("#program lpopt.")

                for lpopt_rule in lpopt_rules:
                    print(str(rule_dictionary[lpopt_rule]))


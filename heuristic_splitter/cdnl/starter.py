
from typing import List, Sequence

from clingo.application import Application
from clingo.control import Control

from heuristic_splitter.cdnl.propagator import BDGPropagator
from heuristic_splitter.cdnl.cdnl_data_structure import CDNLDataStructure

class Starter(Application):

    def __init__(self, program_strings, cdnl_data_structure: CDNLDataStructure):

        self.program_strings = program_strings
        self.cdnl_data_structure = cdnl_data_structure

    def main(self, ctl: Control, files: Sequence[str]):
        '''
        Register the difference constraint propagator, and then ground and
        solve.
        '''

        propagator = BDGPropagator(self.cdnl_data_structure)
        ctl.register_propagator(propagator)
        ctl.configuration.solve.models = 0
        ctl.configuration.solve.mode = "clasp"
        content = self.program_strings
        ctl.add("base", [], content)
        ctl.solve()

            
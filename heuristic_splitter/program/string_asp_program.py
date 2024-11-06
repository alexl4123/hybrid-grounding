
from heuristic_splitter.program.asp_program import ASPProgram

class StringASPProgram(ASPProgram):

    def __init__(self, program):

        self.program = program

    def get_string(self, insert_flags = False):

        return self.program

    def add_string(self, to_add_prg):

        self.program = self.program + to_add_prg



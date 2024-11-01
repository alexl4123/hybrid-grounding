

class Rule:

    def __init__(self, ast_rule, str_rule):
        """
        Representation of a rule as an AST object, and a str object.
        -> Note that str(ast_rule) is not necessarily the same as str_rule,
        as the transformer introduces a ';' between body lits in the string-representation,
        which is not accepted by e.g., lpopt.
        """

        self.ast_rule = ast_rule
        self.str_rule = str_rule

        self.variable_graph = None
        self.is_tight = None
        self.is_disjunctive = False
        self.is_constraint = None

        self.in_program_rules = False

        self.functions = []

        self.scc = None

    def add_variable_graph(self, variable_graph):
        self.variable_graph = variable_graph

    def add_is_tight(self, is_tight):
        self.is_tight = is_tight

    def add_is_constraint(self, is_constraint):
        self.is_constraint = is_constraint

    def add_scc(self, scc):
        self.scc = scc

    def __str__(self):
        return self.str_rule

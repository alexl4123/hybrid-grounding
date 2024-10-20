

class Rule:

    def __init__(self, ast_rule):

        self.ast_rule = ast_rule

        self.full_treewidth = None
        self.effective_treewidth = None
        
        self.variable_graph = None
        self.is_tight = None
        self.is_constraint = None

        self.scc = None

    def set_full_treewidth(self, full_treewidth):
        self.full_treewidth = full_treewidth
    
    def set_effective_treewidth(self, effective_treewidth):
        self.effective_treewidth = effective_treewidth

    def add_variable_graph(self, variable_graph):
        self.variable_graph = variable_graph

    def add_is_tight(self, is_tight):
        self.is_tight = is_tight

    def add_is_constraint(self, is_constraint):
        self.is_constraint = is_constraint

    def add_scc(self, scc):
        self.scc = scc

    def __str__(self):
        return str(self.ast_rule)




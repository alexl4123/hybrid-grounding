

class Rule:

    def __init__(self, ast_rule):

        self.ast_rule = ast_rule

        self.full_treewidth = None
        self.effective_treewidth = None

    def set_full_treewidth(self, full_treewidth):
        self.full_treewidth = full_treewidth
    
    def set_effective_treewidth(self, effective_treewidth):
        self.effective_treewidth = effective_treewidth

    def __str__(self):
        return str(self.ast_rule)




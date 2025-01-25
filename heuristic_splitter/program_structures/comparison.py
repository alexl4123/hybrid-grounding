

class Comparison:

    def __init__(self):

        self.name = ""
        self.operator = ""
        self.negated_operator = ""
        self.arguments = []
        self.is_simple_comparison = True
        self.signum = 0

    def define_signum(self, signum):
        self.signum = signum

    def clone(self):

        clone = Function()
        clone.name = self.name
        clone.operator = self.operator
        clone.left_term = self.left_term
        clone.right_term = self.right_term

        return clone

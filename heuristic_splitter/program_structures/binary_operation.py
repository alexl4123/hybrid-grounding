

class BinaryOperation:

    def __init__(self):

        self.name = ""
        self.operation = ""
        self.arguments = []

    def define_signum(self, signum):
        self.signum = signum

    def clone(self):

        clone = Function()
        clone.name = self.name
        clone.operation = self.operation
        clone.left_term = self.left_term
        clone.right_term = self.right_term

        return clone





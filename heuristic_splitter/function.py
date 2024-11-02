

class Function:

    def __init__(self):

        self.name = ""
        self.arguments = []
        self.signum = 0
        self.in_head = False

    def define_signum(self, signum):
        self.signum = signum

    def clone(self):

        clone = Function()
        clone.name = self.name
        clone.arguments = self.arguments
        clone.signum = self.signum
        clone.in_head = self.in_head

        return clone

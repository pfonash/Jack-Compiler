__author__ = 'mono'

# Used to keep track of values that are accessed in differently scoped functions

class Current():

    def __init__(self):

        self.numClassVars = 0
        self.expressionName = ""
        self.letVariable = ""
        self.numExpressions = 0
        self.numLocals = 0
        self.subroutineName = ""
        self.subroutineType = ""
        return

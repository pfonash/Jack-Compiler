#Provides a symbol table abstraction.
# The symbol table associates the identifier names found in the program with identifier properties needed for compilation: type, kind, and running index.
# The symbol table for Jack programs has two nested scopes (class/subroutine).


ARG = "parameterList"
CLASS = "class"
CLASS_VAR = "classVarDec"
FIELD = "field"
STATIC = "static"
SUB_ROUT_DEC = "subroutineDec"
VAR = "varDec"
VARS = ["arg", FIELD, STATIC, "var"]

class SymbolTable():

    def __init__(self):
        '''

        Creates a new empty symbol table
        :return: void

        '''
        self.classScopeIndex = 0
        self.currentScopeIndex = 0
        self.methodScopeIndex = 1

        self.tables = [ [] , [] ]

        self.kindCounter = {

            "arg" : 0,
            "field" : 0,
            "static" : 0,
            "var" : 0

        }

        return

    def startClass(self, className):
        '''

        :param className: string
        :return: void

        Starts scope for the class
        '''

        newClass = []
        self.tables[0] = newClass
        self.currentScopeIndex = self.classScopeIndex

        return

    def startSubroutine(self):
        '''

        Starts a new subroutine scope (i.e., reset the subroutine's symbol table)
        :return: void

        '''
        newMethod = []
        self.tables[1] = newMethod

        self.currentScopeIndex = self.methodScopeIndex
        self.resetKindCounter()

        return

    def resetKindCounter(self):
        '''

        :return: void
        Sets all the values in kind counter to 0
        '''
        kinds = self.kindCounter.keys()
        for kind in kinds:
            self.kindCounter[kind] = 0

        return

    def define(self, name, type, kind):
        '''
        :param name: string
        :param type:  string
        :param kind: STATIC, FIELD, ARG, or VAR
        :return: void

        Defines a new identifier of a given name, type, and kind, and assigns it a running index.  STATIC and FIELD identifiers have class scope.
        ARG and VAR identifiers have a subroutine scope.

        '''


        if kind == STATIC or kind == FIELD:

            self.tables[self.classScopeIndex].append (
                {
                    "name" : name,
                    "type" : type,
                    "kind" : kind,
                    "number" : self.varCount(kind)
                })

        # Else, it's arg or var, so add it to the current method scope
        else:

            self.tables[self.methodScopeIndex].append (
                {
                    "name" : name,
                    "type" : type,
                    "kind" : kind,
                    "number" : self.varCount(kind)
                })

        self.kindCounter[kind] += 1

        return

    def varCount(self, kind):
        '''

        :param kind: STATIC, FIELD, ARG, or VAR
        :return: int

        Returns the number of variables of the given kind already defined in the current scope

        '''
        return self.kindCounter[kind]

    def kindOf(self, name):
        '''

        :param name: string
        :return: STATIC, FIELD, ARG, VAR, NONE

        Returns the kind of the named identifier in the current scope.  If the identifier is unknown in the current scope. returns NONE.

        '''
        # Check method scope first
        scope = self.tables[1]
        for identifier in scope:

            if identifier["name"] == name:
                return identifier["kind"]

        # If can't find in method, check the class scope
        scope = self.tables[0]
        for identifier in scope:

            if identifier["name"] == name:
                return identifier["kind"]

    def typeOf(self, name):
        '''

        :param name: string
        :return: string

        Returns the type of the named identifier in the current scope (int, string, class)

        '''

        # Check method scope first
        scope = self.tables[1]
        for identifier in scope:
            if identifier["name"] == name:
                return identifier["type"]

        # If can't find in method, check the class scope
        scope = self.tables[0]
        for identifier in scope:

            if identifier["name"] == name:
                return identifier["type"]

    def indexOf(self, name):
        '''

        :param name: string
        :return: int

        Returns the index assigned to the named identifier

        '''

        scope = self.tables[1]
        for identifier in scope:
            if identifier["name"] == name:
                return identifier["number"]

        # If can't find in method, check the class scope
        scope = self.tables[0]
        for identifier in scope:

            if identifier["name"] == name:
                return identifier["number"]


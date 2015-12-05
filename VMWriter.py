__author__ = 'mono'
# Generates VM code into a file

import xml.etree.cElementTree as ET

# Keyword constants
FALSE = "false"
NULL = "null"
THIS = "this"
TRUE = "true"

# Segment constants
CONST = "constant"
ARG = "argument"

# Operations constants
BINARY = "binary"
DIV = "/"
MULT = "*"
NOT = "~"
UNARY = "unary"

# Misc consntants
CALL = "call"
DOT = "."
FUNCTION = "function"
NEWLINE = "\n"
POP = "pop"
PUSH = "push"
SPACE = " "
VM_EXTENSION = ".vm"

class VMWriter():

    def __init__(self, outputFilePath):

        self.outputFilePath = outputFilePath + VM_EXTENSION

        # Converts operation symbol (from Jack) into operation word (for VM code)
        self.binaryOps = {

            "+" : "add",
            "-" : "sub",
            "&" : "and",
            "|" : "or",
            "<" : "lt",
            ">" : "gt",
            "=" : "eq",

        }

        self.unaryOps = {

            "~" : "not",
            "-" : "neg"

        }

        # Used to convert kinds (from the symbol table) to segments (for writing to VM code)
        self.kindToSegment = {

            "arg" : "argument",
            "field" : "this",
            "var" : "local",
            "this" : "pointer"

        }

        # Keeps track of the number of times conditional statements are written in a class
        self.statementCount = {

            # Start off at -1 because increment occurs before assignment (so first assignment is 0)
            "IF" : -1,
            "WHILE" : -1

        }

        self.className = outputFilePath.split("/")[1]
        self.vmCommands = []

    def resetStatementCount(self):
        '''

        :return: void

        Resets the number of if and while statements when starting to compile a new subR
        '''

        self.statementCount["IF"] = -1
        self.statementCount["WHILE"] = -1

    def needsTranslation(self, segment):

        if segment == "arg" or segment == "var" or segment == "field":
            return True
        return False

    def writePush(self, segment, index):
        '''

        :param segment: CONST, ARG, LOCAL, STATIC, THIS, THAT, POINTER, TEMP
        :param index: int
        :return: void
        Writes a VM push command

        '''

        # For var and arg, need to reword segment name
        if self.needsTranslation(segment):
            segment = self.kindToSegment[segment]

        command = PUSH + SPACE + segment + SPACE + str(index)
        self.vmCommands.append(command)
        return

    def writePop(self, segment, index):
        '''

        :param segment: CONST, ARG, LOCAL, STATIC, THIS, THAT, POINTER, TEMP
        :param index: int
        :return: void
        Writes a VM pop command

        '''

        # For var and arg, need to reword segment name
        if self.needsTranslation(segment):
            segment = self.kindToSegment[segment]

        command = POP + SPACE + segment + SPACE + str(index)
        self.vmCommands.append(command)
        return

    def writeKeywordConstant(self, constant):
        '''

        :param constant: true, false, null, this
        :return: void
        '''

        if constant == TRUE:
            self.writePush(CONST, 0)
            self.writeArithmetic(NOT, UNARY)

        elif constant == FALSE or constant == NULL:
            self.writePush(CONST, 0)

        # Otherwise, push this
        else:
            self.writePush("pointer", 0)

        return

    def writeArithmetic(self, command, opType):
        '''

        :param command: + (ADD), - (SUB), -(NEG), =(EQ), > (GT),  < (LT), & (AND), | (OR), ~ (NOT)
        :return: void
        Writes a vm arithmetic command

        '''

        if opType == "unary":

            vmCommand = self.unaryOps[command]
            self.vmCommands.append(vmCommand)

        # Otherwise, it's a binary op
        else:

            if command == MULT:
                self.writeCall("Math.multiply", "2")

            elif command == DIV:
                self.writeCall("Math.divide", "2")

            else:

                vmCommand = self.binaryOps[command]
                self.vmCommands.append(vmCommand )

        return

    def writeLabel(self, labelType, condition, count):
        '''

        :param label: string
        :return: void
        Writes a VM label command

        '''

        label = "label" + SPACE + labelType + "_" + condition + count
        self.vmCommands.append(label)

    def writeGoto(self, label):
        '''

        :param label: string
        :return: void
        Writes a VM goto command

        '''

        gotoCommand = "goto" + SPACE + label
        self.vmCommands.append(gotoCommand)

    def writeIf(self, label):
        '''

        :param label: string
        :return: void
        Writes a VM if-goto command

        '''

        ifGotoCommand = "if-goto" + SPACE + label
        self.vmCommands.append(ifGotoCommand)

    def writeCall(self, name, nArgs):
        '''

        :param name: string
        :param nArgs: int
        :return: void
        Writes a VM call command

        '''

        callCommand = CALL + SPACE +  name + SPACE +  str(nArgs)
        self.vmCommands.append(callCommand)

    def writeFunction(self, name, nLocals):
        '''

        :param name: string
        :param nLocals: int
        :return: void
        Writes a VM function command

        '''

        functionCommand = FUNCTION + SPACE + self.className + DOT + name + SPACE + str(nLocals)
        self.vmCommands.append(functionCommand)

    def writeReturn(self):
        '''

        :return: void
        Writes a VM return command

        '''

        returnCommand = "return"
        self.vmCommands.append(returnCommand)

    def writeCommandsToFile(self):

        # If extra pop command at the end, remove it
        if self.vmCommands[-1] == "pop temp 0":
            self.vmCommands.pop()

        with open(self.outputFilePath, "w") as vmFile:
            for command in self.vmCommands:
                vmFile.write(command)
                vmFile.write(NEWLINE)
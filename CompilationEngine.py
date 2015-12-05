# Effects the actual compilation output.
# Gets its input from a JackTokenizer and emits its parsed structure into an output file/stream.

from Current import Current
from collections import deque
from Identifier import Identifier
import SymbolTable
import VMWriter
import xml.etree.cElementTree as ET


# Constants
ADD = "+"
ARG = "argument"
CONSTRUCTOR = "constructor"
COMMA = ","
CONST = "constant"
DOT = "."
EQUAL_SIGN = "="
IDENTIFIER = "identifier"
IGNORE_RETURN = "pop temp 0"
KEYWORD = "keyword"
METHOD = "method"
NOT = "~"
POINTER = "pointer"
STRING = "stringConstant"
TEMP = "temp"
THAT = "that"
THIS = "this"
TRUE = "TRUE"


# Variables for writing labels
END = "END"
EXP = "EXP"
FALSE = "FALSE"
IF = "IF"
WHILE = "WHILE"

# Variables for symbols
BRACKET_EXPRESSION = "["
EXPRESSION_ENDER = ["]", ")"]
PAREN_EXPRESSION = "("
LEFT_PARENTHESIS = "("
RIGHT_PARENTHESIS = ")"
LEFT_BRACE = "{"
RIGHT_BRACE = "}"
RIGHT_BRACE_WITH_SPACE = " } "
SEMI_COLON = ";"
SPACE = " "

# Misc. variables
STATEMENTS = ["doStatement", "letStatement", "whileStatement", "returnStatement", "ifStatement"]
OPS = ["+", "-", "*", "/", "&", "|", "<", ">", "="]
UNARY_OPS = ["-", "~"]
BINARY = "binary"
UNARY = "unary"
XML_EXTENSION = ".xml"

class JackEngine():

    def __init__(self, tokens, outputFilePath, debugFlag):


        # Variables assigned from arguments
        self.tokenStream = deque(tokens)
        self.tokensForLookBack = deque(tokens)
        self.outputFilePath = outputFilePath

        # Check whether to print out each token as it's parsed
        if debugFlag == "0":
            self.debugMode = False
        else:
            self.debugMode = True

        # Variables relating to parsing tokens
        self.callingFunctionIsLet = False
        self.currentToken = ""
        self.symbolTable = SymbolTable.SymbolTable()
        self.identifier = Identifier(self.symbolTable)

        self.classVarDec = ["static", "field"]

        self.subroutineDec = ["constructor", "function", "method"]
        self.statements = ["let", "if", "else", "while", "do", "return"]
        self.callStatement = {
            "let" : self.compileLet,
            "if" : self.compileIf,
            "else" : self.compileWhile,
            "while" : self.compileWhile,
            "do" : self.compileDo,
            "return" : self.compileReturn
        }

        # Variables that hold the current xml element for a often used element
        self.doElement = None
        self.classVarDecElement = None
        self.elseElement = None
        self.expressionElement = None
        self.expressionElements = []
        self.ifElement = None
        self.letElement = None
        self.parameterListDecElement = None
        self.parentElement = None
        self.parentOfParentElement = None
        self.parentStatementsToIfOrWhile = None
        self.returnElement = None
        self.subroutineBodyElement = None
        self.subroutineDecElement = None
        self.statementsElement = None
        self.varDecElement = None
        self.whileElement = None

        # XML structure root
        self.root = ET.Element("class")

        # Used to keep track of values that are accessed in differently scoped functions
        self.current = Current()

        # Variables for turning xml structure into VM code
        self.VMWriter = VMWriter.VMWriter(outputFilePath)

    def advanceToken(self):
        if self.tokenStream:
            self.currentToken = self.tokenStream.popleft()
            if self.debugMode:
                self.debug("currentToken: ")
            return
        else:
            print "hit last token"

    def addCurrentTokenAsChildElement(self, parentElement):
        childTokenElement, childTokenValue = self.currentToken.items()[0]

        child = ET.SubElement(parentElement, childTokenElement)
        child.text = childTokenValue

        if childTokenElement == IDENTIFIER:
                self.compileIdentifier(child, parentElement)

        return

    def compileIdentifier(self, child, parent):

        # Determine if identifier is being declared or used
        self.identifier.identify(child, parent)
        beingDefined = child.get("beingDefined")
        identifierCategory = child.get("category")

       # print child.text + SPACE + beingDefined

        if beingDefined == "yes":
            self.addIdentifierToSymbolTable(child, identifierCategory)
            self.getIdentifierFromSymbolTable(child)

        else:
            self.compileIdentifierUse(child, parent, identifierCategory)

        return

    def compileIdentifierUse(self, child, parent, identifierCategory):

        if identifierCategory == SymbolTable.CLASS:
            return

        # If identifier is part of a do statement, it's a subroutine name
        elif parent.tag == "doStatement":
            self.identifier.setAttribute(child, "category", "subroutine")

        # If an identifier is part of a let statement, it can be a subroutine or a variable
        elif parent.tag == "letStatement":

            # If it's a variable, then it will be declared already, so try to find it
            kind = self.symbolTable.kindOf(child.text)

            # Check the class, too
            if kind == None:

                self.setClassAsCurrentScope()
                kind = self.symbolTable.kindOf(child.text)
                self.setMethodAsCurrentScope()

                if kind == None:
                    self.identifier.setAttribute(child, "category", "subroutine")

                else:
                    self.getIdentifierFromSymbolTable(child)

            else:
                self.getIdentifierFromSymbolTable(child)

        # Else, it's a subroutine
        else:
            self.getIdentifierFromSymbolTable(child)

        return

    def addIdentifierToSymbolTable(self, child, identifierCategory):

        # Then add identifier to symbol table
        if identifierCategory == SymbolTable.CLASS:
            self.symbolTable.startClass(child.text)

        elif identifierCategory == SymbolTable.SUB_ROUT_DEC:
            #print self.currentTokenValue()
            self.symbolTable.startSubroutine()

        elif identifierCategory in SymbolTable.VARS:
            self.symbolTable.define(child.text, child.get("type"), child.get("category"))

        return

    def getIdentifierFromSymbolTable(self, child):

        '''

        :param child: xml element (of identifier)
        :return: void

        Appends attributes the xml element representing the identifier by looking up the identifier in the symbol table
        '''

        attributes = self.identifier.getAttributes(child.text)
        self.identifier.setAttributes(child, attributes)

        return

    def isLastToken(self):
        if len(self.tokenStream) >= 1:
            return False
        return True

    def setClassAsCurrentScope(self):
        self.symbolTable.currentScopeIndex = self.symbolTable.classScopeIndex

    def setMethodAsCurrentScope(self):
        self.symbolTable.currentScopeIndex = self.symbolTable.methodScopeIndex

    def compile(self):

        self.compileClass()

        # Return parsed XML tree
        self.indentXML()
        #return self.root
        return

    def compileClass(self):
        '''
        Compiles a complete class
        '''

        self.advanceToken()

        if self.currentTokenValue() in self.classVarDec:

            # Current token is the first element of the new sub-element
            self.classVarDecElement = ET.SubElement(self.root, "classVarDec")
            self.addCurrentTokenAsChildElement(parentElement = self.classVarDecElement)

            self.compileClassVarDec()
            self.compileClass()

        elif self.currentTokenValue() in self.subroutineDec:

            # Current token is the first element of the new sub-element
            self.subroutineDecElement = ET.SubElement(self.root, "subroutineDec")
            self.addCurrentTokenAsChildElement(parentElement = self.subroutineDecElement)
            self.compileSubroutine()

            self.compileClass()

        # We're done
        elif self.currentTokenValue() == RIGHT_BRACE:

            self.addCurrentTokenAsChildElement(parentElement = self.root)
            return

        else:

            self.addCurrentTokenAsChildElement(parentElement = self.root)
            self.compileClass()

    def compileClassVarDec(self):
        '''
        Compiles a static declaration or a field declaration
        '''

        self.advanceToken()

        while self.currentTokenValue() is not SEMI_COLON:
            self.addCurrentTokenAsChildElement(parentElement = self.classVarDecElement)
            if self.currentTokenKey() == IDENTIFIER:
                self.current.numClassVars += 1

            self.advanceToken()

        return

    def compileSubroutine(self):
        '''
        Compiles a complete method, function, or constructor.  Starts on function owner
        '''

        self.current.subroutineType = self.currentTokenValue() # constructor, function or method

        # Append type
        self.advanceToken()
        self.addCurrentTokenAsChildElement(parentElement = self.subroutineDecElement)

        # Append name
        self.advanceToken()
        self.current.subroutineName = self.currentTokenValue()
        self.addCurrentTokenAsChildElement(parentElement = self.subroutineDecElement)

        # If it's a method call, this is argument 0
        if self.current.subroutineType == METHOD:
            self.symbolTable.kindCounter["arg"] += 1

        # Append param list symbol
        self.advanceToken()
        self.addCurrentTokenAsChildElement(parentElement = self.subroutineDecElement)

        # Compile the parameter list
        self.parameterListDecElement = ET.SubElement(self.subroutineDecElement, "parameterList")
        self.compileParameterList()

        # Append closing param list symbol
        self.addCurrentTokenAsChildElement(parentElement = self.subroutineDecElement)

        self.subroutineBodyElement = ET.SubElement(self.subroutineDecElement, "subroutineBody")
        self.compileSubroutineBody()

        # Reset if/while statement count
        self.VMWriter.resetStatementCount()
        return

    def compileParameterList(self):
        '''
        Compiles a (possibly empty) parameter list
        '''
        self.advanceToken()

        # If the parameter list is empty or we're done compiling it
        if self.currentTokenValue() == RIGHT_PARENTHESIS:
            return

        # Else
        self.addCurrentTokenAsChildElement(parentElement = self.parameterListDecElement)
        self.compileParameterList()

        return

    def compileSubroutineBody(self):
        '''
        Compiles either a varDec or statements
        '''

        self.advanceToken()

        # If beginning of body
        if self.currentTokenValue() == LEFT_BRACE:

            self.addCurrentTokenAsChildElement(parentElement = self.subroutineBodyElement)
            self.compileSubroutineBody()

        # If end of body
        elif self.currentTokenValue() == RIGHT_BRACE or self.currentTokenValue() == RIGHT_BRACE_WITH_SPACE:
            self.addCurrentTokenAsChildElement(parentElement = self.subroutineBodyElement)

            # Return to compile SR, which will return to compile class.
            return

        # If var dec
        elif self.currentTokenValue() == "var":

            self.varDecElement = ET.SubElement(self.subroutineBodyElement, "varDec")
            self.addCurrentTokenAsChildElement(parentElement = self.varDecElement)
            self.compileVarDec()
            self.compileSubroutineBody()

        # If statement
        elif self.currentTokenValue() in self.statements:

            # Because we're into the subroutine's statements, all vars have been declared, so write subroutine dec
            self.VMWriter.writeFunction(name = self.current.subroutineName, nLocals = self.current.numLocals)

            # If we are constructing an object, we need to allocate space for it
            if self.current.subroutineType == CONSTRUCTOR:

                self.VMWriter.writePush(CONST, self.current.numClassVars)
                self.VMWriter.writeCall("Memory.alloc", 1)

                # Take the value returned from alloc and put it in "this"
                self.VMWriter.writePop(POINTER, 0)

            if self.current.subroutineType == METHOD:

                # Set the value of this
                self.VMWriter.writePush(ARG, 0)
                self.VMWriter.writePop(POINTER, 0)

            # Reset the subroutine dec info
            self.current.numClassVars = 0
            self.current.numLocals = 0
            self.current.subroutineName = ""
            self.current.subroutineType = ""

            self.statementsElement = ET.SubElement(self.subroutineBodyElement, "statements")
            self.parentElement = self.subroutineBodyElement
            self.compileStatements()
            self.addCurrentTokenAsChildElement(parentElement = self.subroutineBodyElement)

            # Return to subroutine dec
            return

        else:
            return

    def compileVarDec(self):
        '''
        Compiles a var declaration
        '''

        # Advance past var keyword
        self.advanceToken()

        # Compile type
        self.addCurrentTokenAsChildElement(parentElement = self.varDecElement)
        self.advanceToken()

        # Compile name
        self.addCurrentTokenAsChildElement(parentElement = self.varDecElement)
        self.current.numLocals += 1
        self.advanceToken()

        while self.currentTokenValue() == COMMA:
            # Compile the comma
            self.addCurrentTokenAsChildElement(parentElement = self.varDecElement)
            self.advanceToken()

            # Compile the name
            self.addCurrentTokenAsChildElement(parentElement = self.varDecElement)

            # Increment num locals for this subroutine
            self.current.numLocals += 1
            self.advanceToken()

        # Append the closing semi-colon
        self.addCurrentTokenAsChildElement(parentElement = self.varDecElement)

        return

    def compileStatements(self, parentStatement = None):
        '''
        Compiles a sequence of statements, not including the enclosing {}
        '''

        # If no more statements
        if self.currentTokenValue() == RIGHT_BRACE or self.currentTokenValue() == RIGHT_BRACE_WITH_SPACE:
            return

        else:

            # Call statement
            self.callStatement[self.currentTokenValue()]()
            self.compileStatements()

    def resetDoElements(self):

        self.current.numExpressions = 0
        self.current.subroutineName = ""

    def isVar(self, tokenValue):
        '''

        :return: bool

        Returns whether the current token is a method.  Determined by checking if current token is a variable.
        In the context of a do statement (which calls this func), a variable beginning the do statement means the subR call is a method call
        '''

        if self.symbolTable.kindOf(tokenValue) == None:
            return False
        return True

    def compileDo(self):
        '''
        Compiles a do statement:  -- do subroutineCall --
        '''

        # Initially set to false, reset to false at end
        methodCall = False
        self.current.numExpressions = 0

        # Compile do keyword (do)
        self.doElement = ET.SubElement(self.statementsElement, "doStatement")
        self.addCurrentTokenAsChildElement(parentElement = self.doElement)
        self.advanceToken()

        # 3 cases: (1) do method() (2) do var.method() (3) do class.function()
        tokenIsVar = self.isVar(self.currentTokenValue())

        # Case: do var.method()
        if tokenIsVar:

            # Subroutine to call will be the varType, not it's name (because it's a method)
            varName = self.currentTokenValue()
            varAttributes = self.identifier.getAttributes(varName)
            self.current.subroutineName = varAttributes["type"]

            # Append dot and subR name to var name
            self.advanceToken()
            while self.currentTokenValue() is not LEFT_PARENTHESIS:
                self.addCurrentTokenAsChildElement(parentElement = self.doElement)
                self.current.subroutineName = self.current.subroutineName + self.currentTokenValue()
                self.advanceToken()

        else:

            tokenValue = self.currentTokenValue()
            self.advanceToken()

            # Case: do method()
            if self.currentTokenValue() == LEFT_PARENTHESIS:

                self.addCurrentTokenAsChildElement(parentElement = self.doElement)
                self.current.subroutineName = self.VMWriter.className + DOT + tokenValue
                methodCall = True

                # Don't advance token, so that compiling the EL starts on left paren

            # Case: do class.function()
            else:

                self.current.subroutineName = tokenValue
                while self.currentTokenValue() is not LEFT_PARENTHESIS:
                    self.addCurrentTokenAsChildElement(parentElement = self.doElement)
                    self.current.subroutineName = self.current.subroutineName + self.currentTokenValue()
                    self.advanceToken()

        # Compile the expression list: (expression,*)
        self.addCurrentTokenAsChildElement(parentElement = self.doElement)
        self.advanceToken()

        # Set do element as parent to the expression list
        self.parentElement = self.doElement

        if tokenIsVar:

            # Set the base
            self.VMWriter.writePush(varAttributes["kind"], varAttributes["index"])

            # Method calls operate on k + 1 args
            self.current.numExpressions += 1

        # Method calls operate on k + 1 args
        if methodCall:

            # Push value of this for function being called
            self.VMWriter.writePush(POINTER, 0)
            self.current.numExpressions += 1

        # Save number of expressions compiled for VM code
        self.current.numExpressions = self.current.numExpressions + self.compileExpressionList()

        # Append closing paren to do element
        self.addCurrentTokenAsChildElement(parentElement = self.doElement)
        #print "closing paren: " + self.currentTokenValue()
        self.advanceToken()

        # Compile the semi-colon
        self.addCurrentTokenAsChildElement(parentElement = self.doElement)

        # Write the call
        self.VMWriter.writeCall(self.current.subroutineName, self.current.numExpressions)

        # Pop the return value
        self.VMWriter.writePop(TEMP, 0)

        # Advance to start of next non-terminal
        self.advanceToken()
        self.current.numExpressions = 0
        return

    def compileLet(self):
        '''
        Compiles a let statement
        '''

        compilingArray = False

        # Compile let keyword
        self.letElement = ET.SubElement(self.statementsElement, "letStatement")
        self.addCurrentTokenAsChildElement(parentElement = self.letElement)
        self.advanceToken()

        # Compile varName for use later in function
        varName = self.currentTokenValue()
        kind = self.symbolTable.kindOf(varName)
        index = self.symbolTable.indexOf(varName)

        self.addCurrentTokenAsChildElement(parentElement = self.letElement)
        self.advanceToken()

        # Next token is either the beginning of an expression (index into an array) or an equal sign.
        # If expression, compile it and advance to the equal sign following it.
        if self.currentTokenValue() == BRACKET_EXPRESSION:

            compilingArray = True

            # Compile opening bracket
            self.addCurrentTokenAsChildElement(parentElement = self.letElement)
            self.advanceToken()

            # Compile expression
            self.parentElement = self.letElement
            self.compileExpression()

            # Push var onto the stack
            self.VMWriter.writePush(kind, index)

            # Add the result of the expression to the base of the variable
            self.VMWriter.writeArithmetic(ADD, BINARY)

            # Compile closing bracket
            self.addCurrentTokenAsChildElement(parentElement = self.letElement)
            self.advanceToken()

            # If nested brackets
            if self.currentTokenValue() == "]":
                self.advanceToken() # Compiled expression doesn't know about closing brace

        # Compile the equal sign and advance
        self.addCurrentTokenAsChildElement(parentElement = self.letElement)
        self.advanceToken()

        # Compile expression
        self.parentElement = self.letElement
        self.compileExpression() # Expression will be pushed to top of stack


        if compilingArray:

            # Pop the result of the expression into temp
            self.VMWriter.writePop(TEMP, 0)

            # Pop the address of the array into that
            self.VMWriter.writePop(POINTER, 1)

            # Push the expression result in temp onto the stack
            self.VMWriter.writePush(TEMP, 0)

            # Store the result in address that is pointing to
            self.VMWriter.writePop(THAT, 0)

        else:
            # Pop result of the expression into LHS of let statement
            self.VMWriter.writePop(kind, index)

        # Next token is either a semi-colon, right bracket or a right paren.
        # If right bracket or paren, we need an extra advance
        if self.currentTokenValue() in EXPRESSION_ENDER:

            self.addCurrentTokenAsChildElement(parentElement = self.letElement)
            self.advanceToken()

        # Compile semi-colon and advance out of the let statement
        self.addCurrentTokenAsChildElement(parentElement = self.letElement)
        self.advanceToken()
        return

    def compileWhile(self):
        '''
        Compiles a while statement
        '''

        # Append while element
        self.whileElement = ET.SubElement(self.statementsElement, "whileStatement")


        # Determine what number while statement this is (in the current subroutine)
        self.VMWriter.statementCount[WHILE] += 1
        parentWhileNumber = str(self.VMWriter.statementCount[WHILE])

        # Save value of parent statement element and value of while element (for the case where a while statement has while statements as statements)
        parentWhile = self.whileElement
        parentToWhile = self.statementsElement

        # Append while keyword
        self.addCurrentTokenAsChildElement(parentElement = self.whileElement)

        self.VMWriter.writeLabel(WHILE, EXP, parentWhileNumber)

        # Advance and append the left paren that marks the beginning of an expression
        self.advanceToken()
        self.addCurrentTokenAsChildElement(parentElement = self.whileElement)

        # Compile the expression, which will advance token(s)
        self.advanceToken()
        self.parentElement = self.whileElement
        self.compileExpression()

        # Not the result of the expression
        self.VMWriter.writeArithmetic(NOT, UNARY)

        # With the computed expression on the top of the stack, test if-goto
        self.VMWriter.writeIf(WHILE + "_" + END + parentWhileNumber)

        # Append the right paren that marks the end of the expression
        self.addCurrentTokenAsChildElement(parentElement = self.whileElement)

        # Advance to the left brace and append it
        self.advanceToken()
        self.addCurrentTokenAsChildElement(parentElement = self.whileElement)

        # Advance to the first keyword of the first statement
        self.advanceToken()
        self.statementsElement = ET.SubElement(self.whileElement, "statements")
        self.compileStatements()

        # After writing statements, go to the beginning of while statement (and then test the expression again)
        self.VMWriter.writeGoto(WHILE + "_" + EXP + parentWhileNumber)

        # Add closing brace
        self.addCurrentTokenAsChildElement(parentElement = parentWhile)
        self.advanceToken()

        # Label denoting end of while statement
        self.VMWriter.writeLabel(WHILE, END, parentWhileNumber)

        # Reset the statement element
        self.statementsElement = parentToWhile

        return

    def compileReturn(self):
        '''

        :return:
        Compile a return statement.  Two cases: return; | return expression;
        '''

        # Append return keyword
        self.returnElement = ET.SubElement(self.statementsElement, "returnStatement")
        self.addCurrentTokenAsChildElement(parentElement = self.returnElement)
        self.advanceToken()

        # Case: return;
        if self.currentTokenValue() == SEMI_COLON:

            self.addCurrentTokenAsChildElement(parentElement = self.returnElement)
            self.parentElement = self.returnElement
            self.advanceToken()

            self.VMWriter.writePush(CONST, 0)
            self.VMWriter.writeReturn()

            return

        # Case: return expression
        else:

            self.parentElement = self.returnElement
            self.compileExpression()

            # Append semi-colon and prepare for next statement (or end of statements)
            self.addCurrentTokenAsChildElement(parentElement = self.returnElement)
            self.advanceToken()

            self.VMWriter.writeReturn()

            return

    def compileIf(self):
        '''
        Compiles an if statement, possibly with a trailing else clause
        '''

        # Append if keyword
        self.ifElement = ET.SubElement(self.statementsElement, "ifStatement")

        # Determine what number if statement this is (in the current subroutine)
        self.VMWriter.statementCount[IF] += 1
        parentIfCount = str(self.VMWriter.statementCount[IF])

        # Save value of parent statement element and value of if element (for the case where a if statement has if statements as statements)
        parentIF = self.ifElement
        parentToIf = self.statementsElement

        self.addCurrentTokenAsChildElement(parentElement = self.ifElement)
        self.advanceToken()

        # Append paren as if symbol, then compile the expression
        self.addCurrentTokenAsChildElement(parentElement = self.ifElement)
        self.parentElement = self.ifElement
        self.advanceToken()
        self.compileExpression()

        # Not the result of the expression
        self.VMWriter.writeArithmetic(NOT, UNARY)

        # Determine which label to jump to
        self.VMWriter.writeIf(IF + "_" + FALSE + parentIfCount)
        self.VMWriter.writeGoto(IF + "_" + TRUE + parentIfCount)

        # Append closing paren
        self.addCurrentTokenAsChildElement(parentElement = self.ifElement)

        # Append opening brace as if symbol
        self.advanceToken()
        self.addCurrentTokenAsChildElement(parentElement = self.ifElement)

        # Write TRUE label
        self.VMWriter.writeLabel(IF, TRUE, parentIfCount)

        # Compile statements after if expression
        self.advanceToken()
        self.statementsElement = ET.SubElement(self.ifElement, "statements")
        self.compileStatements()

        self.VMWriter.writeGoto(IF + "_" + END + parentIfCount)
        # If expression was true, statements executed.  Now, jump to end of if statement
        #self.VMWriter.writeGoto(IF + "_" + FALSE + parentIfCount)

        self.statementsElement = parentToIf

        # Add closing brace to if
        self.addCurrentTokenAsChildElement(parentElement = parentIF)

        self.VMWriter.writeLabel(IF, FALSE, parentIfCount)

        # Check for a trailing else
        self.advanceToken()
        if self.currentTokenValue() == "else":

            self.addCurrentTokenAsChildElement(parentElement = parentIF)

            # Append the opening else brace to xml structure
            self.advanceToken()
            self.addCurrentTokenAsChildElement(parentElement = parentIF)

            # Compile statements in the else block
            self.advanceToken()
            self.compileStatements()

            # Append closing else brace
            self.addCurrentTokenAsChildElement(parentElement = parentIF)
            self.advanceToken()

        self.VMWriter.writeLabel(IF, END, parentIfCount)

        return

    def compileExpression(self):
        '''
        Compiles an expression.
        '''

        self.expressionElement = ET.SubElement(self.parentElement, "expression")
        self.parentElement = self.expressionElement

        # Compile the first term
        self.compileTerm()

        # Compile the op and second term
        while self.currentTokenValue() in OPS:
            operator = self.currentTokenValue()
            self.advanceToken()
            self.compileTerm()
            self.compileOp(operator)

        return

    def compileOp(self, operator):

        # XML tree
        child = ET.SubElement(self.parentElement, "symbol")
        child.text = operator

        self.VMWriter.writeArithmetic(operator, BINARY)

        return

    def compileTerm(self):
        '''
        Compiles a term.  This routine is faced with slight difficulty when trying to decide between alternate parsing roles
        If current token is an identifier, the routine must distinguish between a variable, an array entry, and a subroutine call.
        A single look ahead token, may may be one of "[", "(" or "." suffices to distinguish between the three possibilities
        Any other token is not part of this term and should not be advanced over.
        '''

        self.termElement = ET.SubElement(self.parentElement, "term")
        self.parentElement = self.termElement

        # If term is a unary op
        if self.currentTokenValue() in UNARY_OPS:

            # Add unary op to tree
            self.addCurrentTokenAsChildElement(self.parentElement)
            operator = self.currentTokenValue()

            # Compile the term the op applies to
            self.advanceToken()
            self.compileTerm()

            # Write vm code
            self.VMWriter.writeArithmetic(operator, UNARY)
            return

        # If term is an expression
        elif self.currentTokenValue() == LEFT_PARENTHESIS:

            # Opening paren goes to term
            self.addCurrentTokenAsChildElement(parentElement = self.termElement)

            # Save hierarchy of the expression
            savedExpressionElement = self.expressionElement
            savedTermElement = self.termElement

            self.advanceToken()
            self.compileExpression()

            # Append closing paren to term
            self.addCurrentTokenAsChildElement(parentElement = savedTermElement)
            self.parentElement = savedExpressionElement
            self.advanceToken()

            return

        else:

            # Append to XML structure
            self.addCurrentTokenAsChildElement(parentElement = self.parentElement)

            # Process look ahead token if identifier
            if self.currentTokenKey() == IDENTIFIER:

                # Lookup identifier in symbolTable
                name = self.currentTokenValue()
                kind = self.symbolTable.kindOf(name)
                index = self.symbolTable.indexOf(name)


                # Look ahead to determine if identifier is beginning of an expression
                self.advanceToken()

                # If subroutine call with a class
                if self.currentTokenValue() == DOT:

                    subroutineArgs = 0
                    subroutineName = name

                    # Check if subroutine call is from a var
                    tokenIsVar = self.isVar(name)
                    if tokenIsVar:

                        # Subroutine name is var's class type
                        varAttributes = self.identifier.getAttributes(name)
                        subroutineName = varAttributes["type"]

                        # Push var as arg 0
                        self.VMWriter.writePush(varAttributes["kind"], varAttributes["index"])
                        subroutineArgs =+ 1

                    # Add dot and advance
                    subroutineName = subroutineName + DOT
                    self.addCurrentTokenAsChildElement(parentElement = self.parentElement)
                    self.advanceToken()

                    # Add subroutine name and advance
                    subroutineName = subroutineName + self.currentTokenValue()
                    self.addCurrentTokenAsChildElement(parentElement = self.parentElement)
                    self.advanceToken()

                    # Add opening paren and advance
                    self.addCurrentTokenAsChildElement(self.termElement)
                    self.advanceToken()

                    savedTermElement = self.termElement
                    self.parentElement = self.termElement

                    # Compile expression list, returning number of expressions compiled (which equals num of args passed in)
                    subroutineArgs = subroutineArgs + self.compileExpressionList()
                    self.addCurrentTokenAsChildElement(parentElement = savedTermElement)

                    # Write subroutine call
                    self.VMWriter.writeCall(subroutineName, subroutineArgs)
                    self.advanceToken()
                    return

                # varName[expression]
                elif self.currentTokenValue() == BRACKET_EXPRESSION:

                    savedTermElement = self.termElement
                    self.addCurrentTokenAsChildElement(parentElement = self.termElement)
                    self.parentElement = self.termElement

                    # Advance to first term in expression and then compile the expression
                    self.advanceToken()
                    self.compileExpression()

                    # Push varNAme
                    self.VMWriter.writePush(kind, index)

                    # Add the result of the expression to the base of the variable
                    self.VMWriter.writeArithmetic(ADD, BINARY)

                    # Pop sum into "that" pointer
                    self.VMWriter.writePop(POINTER, 1)

                    # Push value of address that is pointing to
                    self.VMWriter.writePush("that", 0)

                    # Append closing bracket
                    self.addCurrentTokenAsChildElement(parentElement = savedTermElement)
                    self.advanceToken()
                    return

                # If a subroutine call
                elif self.currentTokenValue() == LEFT_PARENTHESIS:

                    # Parens symbol goes with the term
                    self.compileExpressionList()
                    return

                # Else, look ahead token is not part of greater identifier, so compile it as separate term or op
                else:

                    if self.currentTokenValue() == "]":
                        self.VMWriter.writePush(kind, index)
                        return

                    else:

                        # Push the token before the look ahead token
                        self.VMWriter.writePush(segment=kind, index=index)
                        self.parentElement = self.expressionElement
                        return

            # If current token is not an identifier or op, then it's a keyword, constant (string or int)
            else:

                if self.currentTokenKey() == KEYWORD:

                    keyword = self.currentTokenValue()
                    self.VMWriter.writeKeywordConstant(keyword)
                    self.advanceToken()

                elif self.currentTokenKey() == STRING:

                    # Create new string
                    string = self.currentTokenValue()
                    stringLen = len(string)
                    self.VMWriter.writePush(CONST, stringLen)
                    self.VMWriter.writeCall("String.new", 1)

                    # Append each character to string
                    for char in string:
                        self.VMWriter.writePush(CONST, ord(char))
                        self.VMWriter.writeCall("String.appendChar", 2)

                    self.advanceToken()

                # Otherwise, it's an int
                else:

                    self.VMWriter.writePush(CONST, self.currentTokenValue())
                    self.advanceToken()

            return

    def compileExpressionList(self):
        '''
        Compiles a (possibly empty) comma-separated list of expressions
        '''
        numExpressions = 0

        self.expressionListElement = ET.SubElement(self.parentElement, "expressionList")
        self.parentElement = self.expressionListElement


        # Return if expression list is empty
        if self.currentTokenValue() == RIGHT_PARENTHESIS:
            return numExpressions

        else:

            numExpressions += 1
            self.compileExpression()

            while self.currentTokenValue() == COMMA:

                numExpressions += 1

                self.addCurrentTokenAsChildElement(parentElement = self.expressionListElement)
                self.advanceToken()

                # Reset expression list as the parent element
                self.parentElement = self.expressionListElement
                self.compileExpression()


            return numExpressions

    def currentTokenKey(self):
        return self.currentToken.keys()[0]

    def currentTokenValue(self):
        return self.currentToken.values()[0]

    def debug(self, optionalString=""):
        print optionalString + self.currentTokenValue() + " " + self.outputFilePath

    def indent(self, elem, level=0):
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def indentXML(self):
        self.indent(self.root)
        return
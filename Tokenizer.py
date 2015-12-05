__author__ = 'mono'
# Removes all comments and white space from the input stream and breaks it into Jack language tokens.

from collections import deque
import Grammar

DOUBLE_QUOTE = "\""
NEWLINE = "\n"
SPACE = " "

class Tokenizer(object):

    def __init__(self, inputStream):
        '''
        :param jackFile: xxx.jack file to serve as input.
        :return: a new tokenizer object, ready to tokenize.
        '''
        self.currentChar = ""
        self.currentStackLine = ""
        self.currentToken = ""
        self.inputStream = inputStream
        self.grammar = Grammar.Grammar()
        self.tokenBeingBuilt = ""
        self.tokenFormatting = {

            "identifier": self.identifer,
            "integerConstant": self.intVal,
            "keyword": self.keyword,
            "stringConstant": self.stringVal,
            "symbol": self.symbol

        }

    def formatBuiltToken(self):

        # Determine the token type
        self.currentToken = self.tokenBeingBuilt
        tokenType = self.tokenType()

        # Format it according to type
        formattedToken = self.tokenFormatting[tokenType]()
        element, tokenValue = formattedToken.items()[0]

        return {element: tokenValue}

    def clearBuiltToken(self):

        self.tokenBeingBuilt  = ""
        return

    def nextChar(self):

        if self.currentStackLine:
            self.currentChar = self.currentStackLine.popleft()
            return True

        return False

    def addCharToToken(self):

        self.tokenBeingBuilt += self.currentChar
        return

    def tokenize(self, line):

        formattedTokens = [ ]
        line = line.strip("\n\r\t ")

        self.currentStackLine = deque(line)
        self.clearBuiltToken()

        # Iterate through each char in line, one by one
        while self.nextChar():

            # Case: char, c, is part of string constant |:: "cxxxx");
            if self.currentChar == DOUBLE_QUOTE:

                self.addCharToToken()
                self.nextChar()

                while self.currentChar != DOUBLE_QUOTE:
                    self.addCharToToken()
                    self.nextChar()

                # Append string constant to formatted tokens
                self.addCharToToken()
                formattedToken = self.formatBuiltToken()
                formattedTokens.append(formattedToken)
                self.clearBuiltToken()

            # Space separates tokens
            elif self.currentChar == SPACE and len(self.tokenBeingBuilt) > 1:

                formattedToken = self.formatBuiltToken()
                formattedTokens.append(formattedToken)
                self.clearBuiltToken()

            # Case: char is symbol +-&|
            elif self.currentChar in self.grammar.lexical.symbols:

                # If back to back symbols or 1 letter identifier
                if len(self.tokenBeingBuilt) >= 1 and self.tokenBeingBuilt != SPACE:

                    # First, append the 1 letter symbol/identifier, then append the current symbol
                    formattedToken = self.formatBuiltToken()
                    formattedTokens.append(formattedToken)
                    self.clearBuiltToken()

                self.tokenBeingBuilt = self.currentChar
                formattedToken = self.formatBuiltToken()
                formattedTokens.append(formattedToken)
                self.clearBuiltToken()

            else:
                self.addCharToToken()

        return formattedTokens


    def tokenType(self):

        '''
        Returns the type of the current token
        '''

        # Don't strip spaces out of strings
        if DOUBLE_QUOTE in self.currentToken:
            return "stringConstant"

        # Strip out leading or trailing spaces so current token can match values in grammar
        self.currentToken = self.currentToken.strip(" ")

        if self.currentToken in self.grammar.lexical.keywords:
            return "keyword"

        if self.currentToken in self.grammar.lexical.symbols:
            return "symbol"

        if self.currentToken.isdigit():
            return "integerConstant"

        if not self.currentToken[0].isdigit():
            return "identifier"

    def keyword(self):

        '''
        :return: dict["key:string"]The keyword which is the current token
        '''
        return {"keyword" : self.currentToken}

    def symbol(self):
        '''
        :return: dict["key:string"].  Returns the character which is the current symbol
        '''
        return {"symbol" : self.currentToken}

    def identifer(self):

        '''
        :return: dict["key:string"].  Returns the identifier which is the current token
        '''
        return {"identifier" : self.currentToken}

    def intVal(self):

        '''
        :return: dict["key:int"].  Returns the integer value of the current token
        '''
        return {"integerConstant": self.currentToken}

    def stringVal(self):

        '''
        :return dict["key:string"] Returns the string value of the current token (without the double quotes)
        '''
        return {"stringConstant" : self.currentToken[1:-1]}




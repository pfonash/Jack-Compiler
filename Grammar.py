__author__ = 'mono'

class Grammar(object):

    def __init__(self):
        self.lexical = Lexical()

class Lexical(object):

    def __init__(self):
        self.keywords = {"class": 0,
                   "constructor": 1,
                   "function": 2,
                   "method": 3,
                   "field": 4,
                   "static": 5,
                   "var": 6,
                   "int": 7,
                   "char": 8,
                   "boolean": 9,
                   "void": 10,
                   "true": 11,
                   "false": 12,
                   "null": 13,
                   "this": 14,
                   "let": 15,
                   "do": 16,
                   "if": 17,
                   "else:": 18,
                   "while": 19,
                   "return": 20,
                }
        self.symbols = "~{}()[].,;+-*/&|<>=_"
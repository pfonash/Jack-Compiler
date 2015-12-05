__author__ = 'mono'
import Analyzer
import CompilationEngine
import Tokernizer
import sys


def compile():
    '''
    :return:
    '''

    if len(sys.argv) != 2:
        print("compiler xxx.jack")
        exit()
    inFile = sys.argv[1]

    tokenizer = Tokernizer(inFile)

    while tokenizer.hasMoreTokens():
        tokenizer.advance()

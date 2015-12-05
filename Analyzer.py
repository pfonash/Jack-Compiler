__author__ = 'mono'
import CompilationEngine
import xml.etree.cElementTree as ET
import FileManager
import Tokenizer
import sys

NEWLINE = "\n"

# Operates on a given source, where source is either a file name of the form Xxx.jack or a directory name containing one or more such files.
# For each source Xxx.jack file, the analyzer goes through the following logic:

    # 1. Create a JackTokenizer from the Xxx.jack input file.
    # 2. Create an output file called Xxx.xml and prepare it for writing.
    # 3. Use the CompilationEngine to compile the input JackTokenizer into the output file.

def analyze():

    fileManager = FileManager.FileManager()

    if fileManager.receivedValidInput(sys.argv):
        sourceFiles = fileManager.getFilesInInput()

        for sourceFile in sourceFiles:
            linesInFile = fileManager.parseLinesFromFile(sourceFile)
            tokenizer = Tokenizer.Tokenizer(linesInFile)

            # Create or reset list to store all the tokens for each file.
            tokenStream = []

            for line in tokenizer.inputStream:
                tokens = tokenizer.tokenize(line)

                for token in tokens:
                    tokenStream.append(token)

            # Remove .jack extension
            sourceFile = sourceFile[:-5]

            jackCompilationEngine = CompilationEngine.JackEngine(tokenStream, sourceFile)
            jackCompilationEngine.compile()
            jackCompilationEngine.writeToXML()

analyze()

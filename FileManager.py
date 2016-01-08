__author__ = 'mono'

import os

COMMENT = "//"
DEST_FILE_EXTENSION = ".xml"
LONG_COMMENT_BEGINNER = "/**"
LONG_COMMENT_ENDER = "*/"
LONG_COMMENT_EXTENDER = "*"
SOURCE_FILE_EXTENSION = ".jack"


class FileManager(object):

    def __init__(self):
        self.path = ""
        self.filesInPath = ""
        self.sourceData = ""
        self.filesToCompile = []
        self.outputFilePath = ""

    def receivedValidInput(self, argv):

        if len(argv) != 3:
            self.showUsage()
            exit()

        self.path = argv[1]
        return True

    #def getFileName(self, path):
     #   return path.split("/")[2]

    def getFilesInInput(self):
        '''
        :return: list.  With a length of at least 1 to number of source files in directory.
        '''
        return [self.path + fileName for fileName in os.listdir(self.path) if fileName.endswith(SOURCE_FILE_EXTENSION)]

    def __getOutputPath(self):
        splitPath = self.path.split("/")
        inputName = splitPath[1]
        return splitPath[0] + "/" + inputName + "/" + inputName + DEST_FILE_EXTENSION

    def parseLinesFromFile(self, sourceFile):
        '''
        :return: list, with comments removed from Jack code
        '''
        with open(sourceFile) as f:

            # Get rid of comments
            lines = [line for line in f if COMMENT not in line.strip(" ")[0:2]]
            lines = [line for line in lines if LONG_COMMENT_BEGINNER not in line and LONG_COMMENT_ENDER not in line and len(line) != 2]
            lines = [self.clean(line) for line in lines]
            tokenLines = []
            for line in lines:
                if LONG_COMMENT_EXTENDER in line:
                    if LONG_COMMENT_EXTENDER == line[0]:
                        continue
                    else:
                        tokenLines.append(line)
                else:
                    tokenLines.append(line)

        # Return lines of tokens
        return tokenLines

    def prepareOutputFile(self):
        '''
        :return: Prepares the name for the output file path
        '''
        self.outputFilePath = self.__getOutputPath()

    def clean(self, line):

        if COMMENT in line:
            line = line.split("/")[0]

        return line.strip("  \t\n\r")

    def showUsage(self):
        print("Usage: python Analyzer.py xxx.jack | directoryWithJackFiles | debugFlag (0:false or 1:true)")

__author__ = 'mono'

ARG = "parameterList"
CLASS = "class"
CLASS_VAR = "classVarDec"
STATEMENTS = ["doStatement", "letStatement", "whileStatement", "returnStatement", "ifStatement"]
SUB_ROUT_DEC = "subroutineDec"
VAR = "varDec"

class Identifier():

    def __init__(self, symbolTable):

        self.symbolTable = symbolTable

    def identify(self, child, parent):

        # Set attributes required to call symbolTable's define function
        self.getAttributesFromParentXML(child, parent)

        return

    def getAttributesFromParentXML(self, child, parent):
        '''

        :param child: ET (child element in xml structure that represents an identifier)
        :param parent: ET (parent element to child, containing information about child)
        :return: void
        '''

        if parent.tag == CLASS_VAR or parent.tag == VAR:

            # Upper case identifier means that it's a class acting as a type for a variable
            if not child.text[0].islower():
                self.setAttribute(child, "category", CLASS)
                self.setAttribute(child, "type", child.text)
                self.setAttribute(child, "beingDefined", "no")
                return

            self.setAttribute(child, "category", parent[0].text)
            self.setAttribute(child, "type", parent[1].text)
            self.setAttribute(child, "beingDefined", "yes")

        elif parent.tag == ARG:

            # Find where in the parameter list this identifier is
            indexLocation = 0
            for c in parent:

                if c.text == child.text:
                    break

                else:
                    indexLocation += 1

            self.setAttribute(child, "category", "arg")
            self.setAttribute(child, "type", parent[indexLocation - 1].text)

            # Other objects may serve as argument types
            if not child.text[0].islower():
                self.setAttribute(child, "beingDefined", "no")
            else:
                self.setAttribute(child, "beingDefined", "yes")

        elif parent.tag == CLASS:
            self.setAttribute(child, "category", parent.tag)
            self.setAttribute(child, "beingDefined", "yes")

        elif parent.tag == SUB_ROUT_DEC:
            self.setAttribute(child, "category", parent.tag)
            self.setAttribute(child, "beingDefined", "yes")

        else:
            self.setAttribute(child, "beingDefined", "no")

        return

    def setAttribute(self, child, attribute, attributeValue):
        child.set(attribute, attributeValue)
        return

    def setAttributes(self, child, attributes):
        '''

        :param child: xml element
        :param attributes: dict
        :return: void

        Sets attributes of xml element (identifier) with attributes from symbol table
        '''
        for attribute in attributes.keys():
            self.setAttribute(child, attribute, attributes[attribute])

    def getAttributes(self, name):
        '''

        :param name: string (name of identifier)
        :return: dict

        Returns a dictionary with all the attributes of an identifier
        '''
        attributes = {}
        attributes["kind"] = str(self.symbolTable.kindOf(name))
        attributes["type"] = str(self.symbolTable.typeOf(name))
        attributes["index"] = str(self.symbolTable.indexOf(name))
        return attributes


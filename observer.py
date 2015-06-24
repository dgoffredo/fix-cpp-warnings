
# I define "observers" so I can use them to "traverse" the AST.
#
def traverse(c, observer):
    observer.observe(c)
    observer.pushFrom(c)
    for child in c.get_children():
        traverse(child, observer)
    observer.popTo(c)


# AST observer interface
#
class Observer(object):
    def __init__(self):
        pass

    def observe(self, cursor):
        pass

    def pushFrom(self, cursor):
        pass

    def popTo(self, cursor):
        pass


# Useful example: An Observer that's just a group of other Observers.
# You could use this to run a bunch of checks at the same time as you
# traverse the AST.
#
class ObserverGroup(Observer):
    def __init__(self, observers):
        super(ObserverGroup, self).__init__()
        self.observers = observers

    def observe(self, cursor):
        for observer in self.observers:
            observer.observe(cursor)

    def pushFrom(self, cursor):
        for observer in self.observers:
            observer.pushFrom(cursor)
    
    def popTo(self, cursor):
        for observer in self.observers:
            observer.popTo(cursor)

import sys
import fileprinter

def _repeatedString(s, n):
    return ''.join(s for _ in range(n))

def printCursor(c, printer=fileprinter.printf, indentLevel=0, tabWidth=4, tokenLineLimit=70):
    indent = _repeatedString(' ', indentLevel)
    tokensRep = ' '.join('"{}"'.format(token.spelling) \
                         for token in c.get_tokens())
    semantic_parent = c.semantic_parent
    definition = c.get_definition()
    printer('{}{} ({}) ({}) (hash {}) (refs {}) ({}) {}.{}({})-{}.{}({})',
                indent,
                c.kind,
                c.displayname,
                c.type.kind, 
                c.canonical.hash,
                definition.hash if definition else '',
                semantic_parent.displayname if semantic_parent else '',
                c.extent.start.line,
                c.extent.start.column,
                c.extent.start.offset,
                c.extent.end.line,
                c.extent.end.column,
                c.extent.end.offset)

    if len(tokensRep) > tokenLineLimit:
        tokensRep = tokensRep[0:tokenLineLimit - 3] + '...'
    printer('{}{}', indent, tokensRep)


# Print the AST as you go. 
#
class TreePrinter(Observer):
    def __init__(self, outFile=sys.stdout):
        super(TreePrinter, self).__init__()
        self.indentLevel = 0
        self.printf = fileprinter.FilePrinter(outFile)

    def observe(self, c):
        printCursor(c, printer=self.printf, indentLevel=self.indentLevel)

    def pushFrom(self, cursor):
        self.indentLevel += 1

    def popTo(self, cursor):
        self.indentLevel -= 1


#!/usr/bin/python

from clangwrapper import Index, CursorKind, Cursor, HashableCursor
from observer import traverse, Observer, ObserverGroup, TreePrinter

def getTransUnit(filepath, flags):
    index = Index.create()
    transUnit = index.parse(filepath, flags)
    return transUnit

class FunctionParameter:
    def __init__(self, name, location):
        self._id = FunctionParameter.makeId()
        self.location = location
        self.nMentions = 0

# CursorKind.PARM_DECL
# might be referred to in the topmost 
# CursorKind.COMPOUND_STMT
# by a
# CursorKind.DECL_REF_EXPR

class Function:
    Param = FunctionParameter
    def __init__(self, name):
        self.name = name
        self.hasBody = False
        self.parameters = dict()

    def addParam(self, name, location):
        assert name not in self.parameters
        self.parameters[name] = Function.Param(name, location)

    def mentionIfParam(self, name):
        if name in self.parameters:
            self.parameters[name].nMentions += 1

    def unmentionedParams(self):
        return [p for p in self.parameters.itervalues() if p.nMentions == 0]

def cursorIsFunction(c):
    return c.kind in [CursorKind.CXX_METHOD, 
                      CursorKind.FUNCTION_TEMPLATE,
                      CursorKind.FUNCTION_DECL]

from fileprinter import printf

import sys
inFilepath = sys.argv[1]
translationUnit = getTransUnit(inFilepath, ['-xc++', '-std=c++98'])

for diag in translationUnit.diagnostics:
    printf('**** {}', diag)
    for fix in diag.fixits:
        printf(' ****     possible fix --> {}', fix)

traverse(translationUnit.cursor, TreePrinter())

class FunctionNamer(Observer):
    def __init__(self):
        super(FunctionNamer, self).__init__()

    def observe(self, cursor):
        if not cursorIsFunction(cursor):
            return

        printf('I have found a function named "{}" or "{}", if you like.', 
               cursor.spelling, cursor.displayname)

printf('\n')
traverse(translationUnit.cursor, FunctionNamer())


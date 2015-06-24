#!/usr/bin/python

from clangwrapper import Index, CursorKind, Cursor, HashableCursor
from observer import traverse, Observer, ObserverGroup, TreePrinter, printCursor

def getTransUnit(filepath, flags):
    index = Index.create()
    transUnit = index.parse(filepath, flags)
    return transUnit

# CursorKind.PARM_DECL
# might be referred to in the topmost 
# CursorKind.COMPOUND_STMT
# by a
# CursorKind.DECL_REF_EXPR

class Function:
    def __init__(self, cursor):
        self.cursor = cursor
        self.hasBody = False
        self.parameterMentions = dict() # HashableCursor --> int

    def addParam(self, cursor):
        cursor = HashableCursor(cursor)
        assert cursor not in self.parameterMentions # Redundant?
        self.parameterMentions[cursor] = 0

    def mentionIfParam(self, cursor):
        definition = HashableCursor(cursor.get_definition())
        if definition in self.parameterMentions:
            self.parameterMentions[definition] += 1

    def unmentionedParams(self):
        return set(cursor \
                   for cursor, count in self.parameterMentions.iteritems() \
                   if count == 0)

def isFunction(cursor):
    return cursor.kind in [CursorKind.CXX_METHOD, 
                           CursorKind.FUNCTION_TEMPLATE,
                           CursorKind.FUNCTION_DECL]

def printErrors(transUnit):
    for diag in transUnit.diagnostics:
        printf('**** {}', diag)
        for fix in diag.fixits:
            printf(' ****     possible fix --> {}', fix)


from fileprinter import printf

import sys
inFilepath = sys.argv[1]
translationUnit = getTransUnit(inFilepath, ['-xc++', '-std=c++98'])

traverse(translationUnit.cursor, TreePrinter())

''' This was a toy Observer to get my feet wet with picking out functions.

class FunctionNamer(Observer):
    def __init__(self):
        super(FunctionNamer, self).__init__()

    def observe(self, cursor):
        if not isFunction(cursor):
            return

        printf('I have found a function named "{}" or "{}", if you like.', 
               cursor.spelling, cursor.displayname)

printf('\n')
traverse(translationUnit.cursor, FunctionNamer())
'''

# Don't let it fool you -- it's just a list with some convenience methods:
#     Stack.push(item)
#     Stack.top()
#     Stack.isEmpty()
#
class Stack(list):
    def __init__(self, *args):
        list.__init__(self, *args)
    
    def push(self, item):
        self.append(item)

    def top(self):
        return self[-1]

    def isEmpty(self):
        return len(self) == 0

class FindUnusedParameters(Observer):
    def __init__(self):
        super(FindUnusedParameters, self).__init__()
        self.unusedParameters = set() # of HashableCursor
        self._functionObservers = Stack() # of FunctionObserver

    def observe(self, cursor):
        funcs = self._functionObservers

        if isFunction(cursor):
            funcs.push(FunctionObserver(cursor))
        elif funcs.isEmpty():
            pass # Nothing to look at
        else:
            currentFunction = funcs.top()
            # printf('Going to tell {} to observe {}', currentFunction, cursor.displayname)
            currentFunction.observeChild(cursor)

    def pushFrom(self, cursor):
        pass # Nothing to do

    def popTo(self, cursor):
        funcs = self._functionObservers
        if funcs.isEmpty():
            return # Who cares; we have nothing to keep track of

        currentFunction = funcs.top()
        if cursor == currentFunction.cursor:
            # Get unused params from Function.
            unused = currentFunction.finish() 
            # Exclude nameless params.
            unused = set(c for c in unused if len(c.spelling)) 

            self.unusedParameters |= unused
            funcs.pop()

# TODO: Need a better name than 'FunctionObserver'. While it does observe
#       a function, it gives the impression that it should be derived from
#       observer.Observer, but it's not, since it's a //function// observer,
#       not an //AST// observer.
#
class FunctionObserver:
    def __init__(self, cursor):
        self.cursor = cursor
        self.function = Function(cursor)
        self._foundFirstBlock = False

    def __repr__(self):
        return self.function.cursor.displayname

    # Returns a (possibly empty) list of the function's unmentioned parameters
    #
    def finish(self):
        if self.function.hasBody:
            return self.function.unmentionedParams()
        else:
            return set()

    def _observeParam(self, paramCursor):
        # printf('{} is observing parameter {}', self, paramCursor.displayname)
        self.function.addParam(paramCursor)

    def _observeFirstBlock(self):
        # printf('{} is observing the first block', self)
        self._foundFirstBlock = True
        self.function.hasBody = True

    def _observeRef(self, refCursor):
        # printf('{} is observing a ref {}', self, refCursor.displayname)
        self.function.mentionIfParam(refCursor)

    def observeChild(self, childCursor):
        kind = childCursor.kind
        if not self._foundFirstBlock:
            if kind == CursorKind.PARM_DECL:
                self._observeParam(childCursor)
            elif kind == CursorKind.COMPOUND_STMT:
                self._observeFirstBlock()
        elif kind == CursorKind.DECL_REF_EXPR:
            self._observeRef(childCursor)

finder = FindUnusedParameters()
printf('')
traverse(translationUnit.cursor, finder)

def eponymousToken(cursor):
    matches = [token \
               for token in cursor.get_tokens() \
               if token.spelling == cursor.displayname]

    length = len(matches)
    assert length < 2
    return matches[0] if length > 0 else None

printf('\nUnused parameters:\n')
for cursor in finder.unusedParameters:
    printCursor(cursor)
    token = eponymousToken(cursor)
    printf('    whose eponymous token is at {} {}.{}({})-{}.{}({})', 
           token.location.file.name,
           token.extent.start.line,
           token.extent.start.column,
           token.extent.start.offset,
           token.extent.end.line,
           token.extent.end.column,
           token.extent.end.offset)
    printf('')

printErrors(translationUnit)


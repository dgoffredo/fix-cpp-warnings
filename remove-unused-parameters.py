#!/usr/bin/python

from clangwrapper import CursorKind, Cursor, Diagnostic, HashableCursor
from observer import traverse, Observer, ObserverGroup, printCursor

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
        definition = cursor.get_definition()
        if not definition:
            return # Can't see what this ref refers to.

        definition = HashableCursor(definition)

        if definition in self.parameterMentions:
            self.parameterMentions[definition] += 1

    def unmentionedParams(self):
        return set(cursor \
                   for cursor, count in self.parameterMentions.iteritems() \
                   if count == 0)

def isFunction(cursor):
    return cursor.kind in [CursorKind.CXX_METHOD, 
                           CursorKind.FUNCTION_TEMPLATE,
                           CursorKind.FUNCTION_DECL,
                           CursorKind.CONSTRUCTOR]

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
        # Just some sanity checking. If we are pushing from a function,
        # then it must be the case that we just put a new FunctionObserever
        # on the top of the stack, and its cursor should be this one.
        #
        if not isFunction(cursor):
            return

        currentFunc = self._functionObservers.top()
        assert currentFunc
        assert cursor == currentFunc.cursor

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
        self.hasBody = False

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

    def _observeBlock(self):
        # printf('{} is observing the first block', self)
        self.function.hasBody = True

    def _observeRef(self, refCursor):
        # printf('{} is observing a ref {}', self, refCursor.displayname)
        self.function.mentionIfParam(refCursor)

    def observeChild(self, childCursor):
        kind = childCursor.kind
        if kind == CursorKind.PARM_DECL:
            self._observeParam(childCursor)
        elif kind == CursorKind.COMPOUND_STMT:
            self._observeBlock()
        elif kind == CursorKind.DECL_REF_EXPR:
            self._observeRef(childCursor)

def eponymousToken(cursor):
    if not cursor.displayname:
        return None # Of course nothing will match

    matches = [token \
               for token in cursor.get_tokens() \
               if token.spelling == cursor.displayname]

    # "assert" might be too harsh.
    # assert len(matches) > 0
    if len(matches) == 0:
        printerr('ERROR The following cursor does not have an eponymous token:')
        printerr(cursor.location.file.name)
        printCursor(cursor, printerr)
        return None
                       # Take the last rather than the first, 
    return matches[-1] # in case the parameter shares its name with a type.


if __name__ == '__main__':
    from fileprinter import printf, printerr

    import fixer
    util = fixer.Fixer('Remove unused parameter variables from function definitions.')
    args, translationUnit = util.setup()
    inFilepath = util.filepath

    finder = FindUnusedParameters()
    traverse(translationUnit.cursor, finder)   

    from collections import defaultdict

    def rewritesByFile(unusedParameters):
        rewrites = defaultdict(list)

        for cursor in unusedParameters:
            token = eponymousToken(cursor)
            if not token:
                continue
            startOffset = token.extent.start.offset
            endOffset = token.extent.end.offset
            rewrite = (startOffset, endOffset - startOffset, '')
            rewrites[token.location.file.name].append(rewrite)

        return rewrites

    rewrites = rewritesByFile(finder.unusedParameters)

    from rewrite import rewrite
    for filename, rewrites in rewrites.iteritems():
        if filename != inFilepath:
            printf('Skipping file {}', filename)
            continue
        elif len(rewrites) == 0:
            continue
        with open(filename, 'r') as fin:
            printf('Rewriting file {}', filename)
            with open(filename + '.rewrite', 'w') as fout:
                rewrite(fin, fout, rewrites)


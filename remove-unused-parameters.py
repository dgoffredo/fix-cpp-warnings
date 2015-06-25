#!/usr/bin/python

from clangwrapper import Index, CursorKind, Cursor, Diagnostic, HashableCursor
from observer import traverse, Observer, ObserverGroup, TreePrinter, printCursor

def getTransUnit(filepath, flags):
    index = Index.create()
    transUnit = index.parse(filepath, flags)
    return transUnit

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
                           CursorKind.FUNCTION_DECL]

def printErrors(transUnit):
    didFindError = False
    for diag in transUnit.diagnostics:
        if diag.severity >= Diagnostic.Error:
            didFindError = True
        printf('**** {}', diag)
        for fix in diag.fixits:
            printf(' ****     possible fix --> {}', fix)

    return didFindError

import sys
from fileprinter import printf

inFilepath = sys.argv[1]

hackyHackyFlaggyFlaggy = [
'-DBB64BIT',
'-DBAS_NOBBENV', 
'-D_LINUX_SOURCE',
'-I/usr/lib/gcc/x86_64-redhat-linux6E/4.4.7/include',
'-I.',
'-I../../../../../src/bde/bdet',
'-I../bde/bbedc',
'-I../bde/bdet',
'-I../bde/bdetu',
'-I../bde/bdxt',
'-I../bdet',
'-I../contract',
'-I../core',
'-I/bb/bigstorq3/derv_xasset/thirdparty/dlib_dpkg_distribution_2015.25/refroot/amd64//opt/bb/include',
'-I/bb/bigstorq3/derv_xasset/thirdparty/dlib_dpkg_distribution_2015.25/refroot/amd64//opt/bb/lib64/mlfi//mlfilib',
'-I/bb/bigstorq3/derv_xasset/thirdparty/dlib_dpkg_distribution_2015.25/refroot/amd64/opt/bb/include',
'-I/bb/bigstorq3/derv_xasset/thirdparty/dlib_dpkg_distribution_2015.25/refroot/amd64/opt/bb/lib64/mlfi',
'-I/bb/bigstorq3/qfdlibci/qfd/qfd_external.git/libs/boost/dist/1.56.0/include',
'-I/bb/build/Linux-x86_64-64/release/robolibs/source/lib/dpkgroot/opt/bb/include',
'-I/bb/build/Linux-x86_64-64/release/robolibs/source/lib/dpkgroot/opt/bb/include/stlport',
'-I/bb/build/Linux-x86_64-64/release/robolibs/source/share/include/00depbuild',
'-I/bb/build/Linux-x86_64-64/release/robolibs/source/share/include/00deployed',
'-I/bb/build/Linux-x86_64-64/release/robolibs/source/share/include/00offlonly',
'-I/bb/build/share/stp/include/00offlonly',
'-I/bbshr/ird/hw2f/dlib/rel_candidate/qfd-v3.34.3/src',
'-I/bbshr/ird/hw2f/dlib/rel_candidate/qfd-v3.34.3/src/libs',
'-I/bbshr/ird/hw2f/dlib/rel_candidate/qfd-v3.34.3/src/libs/qfd_breg/qfd_breg_wrapper',
'-I/bbshr/ird/hw2f/dlib/rel_candidate/qfd-v3.34.3/src/libs/qfd_core/robo/quantcore',
'-I/bbshr/ird/hw2f/dlib/rel_candidate/qfd-v3.34.3/src/libs/qfd_equity/Equity',
'-I/bbshr/ird/hw2f/dlib/rel_candidate/qfd-v3.34.3/src/libs/qfd_equity/Equity/common',
'-I/bbshr/ird/hw2f/dlib/rel_candidate/qfd-v3.34.3/src/libs/qfd_equity/Equity/local_vol',
'-I/bbshr/ird/hw2f/dlib/rel_candidate/qfd-v3.34.3/src/libs/qfd_equity/Equity/qrdqnt',
'-I/bbshr/ird/hw2f/dlib/rel_candidate/qfd-v3.34.3/src/libs/qfd_equity/robo/quantcore',
'-I/bbshr/ird/hw2f/dlib/rel_candidate/qfd-v3.34.3/src/libs/qfd_equity_hybrid_transitional',
'-I/bbshr/ird/hw2f/dlib/rel_candidate/qfd-v3.34.3/src/libs/qfd_fx/robo/quantcore',
'-I/bbshr/ird/hw2f/dlib/rel_candidate/qfd-v3.34.3/src/libs/qfd_hybrid/cpp/gen2',
'-I/bbshr/ird/hw2f/dlib/rel_candidate/qfd-v3.34.3/src/libs/qfd_hybrid/cpp/lmm',
'-I/bbshr/ird/hw2f/dlib/rel_candidate/qfd-v3.34.3/src/libs/qfd_hybrid_converters',
'-I/bbshr/ird/hw2f/dlib/rel_candidate/qfd-v3.34.3/src/libs/qfd_infrastructure/robo/quantcore',
'-I/bbshr/ird/hw2f/dlib/rel_candidate/qfd-v3.34.3/src/libs/qfd_market/robo/quantcore',
'-I/bbshr/ird/hw2f/dlib/rel_candidate/qfd-v3.34.3/src/libs/qfd_mathutil',
'-I/bbshr/ird/hw2f/dlib/rel_candidate/qfd-v3.34.3/src/libs/qfd_mathutil/robo/quantcore',
'-I/bbshr/ird/hw2f/dlib/rel_candidate/qfd-v3.34.3/src/libs/qfd_mathutil/robo/quantquad',
'-I/bbshr/ird/hw2f/dlib/rel_candidate/qfd-v3.34.3/src/libs/qfd_poly_var',
'-I/bbshr/ird/hw2f/dlib/rel_candidate/qfd-v3.34.3/src/plugins',
'-I/home/dgoffred/mbig/git/dlib/blan/src/bde/bdet',
'-I/home/dgoffred/mbig/git/dlib/dlibbatchprice',
'-I/home/dgoffred/mbig/git/dlib/dlibbbcache',
'-I/home/dgoffred/mbig/git/dlib/dlibblpenv',
'-I/home/dgoffred/mbig/git/dlib/dlibblpenvstubs',
'-I/home/dgoffred/mbig/git/dlib/dlibclient',
'-I/home/dgoffred/mbig/git/dlib/dlibcoredbacc',
'-I/home/dgoffred/mbig/git/dlib/dlibcoretypes',
'-I/home/dgoffred/mbig/git/dlib/dlibdates',
'-I/home/dgoffred/mbig/git/dlib/dlibdbacc',
'-I/home/dgoffred/mbig/git/dlib/dlibdealapi',
'-I/home/dgoffred/mbig/git/dlib/dlibdealtypes',
'-I/home/dgoffred/mbig/git/dlib/dlibevent',
'-I/home/dgoffred/mbig/git/dlib/dlibexternal',
'-I/home/dgoffred/mbig/git/dlib/dlibhelper',
'-I/home/dgoffred/mbig/git/dlib/dlibiboxclient',
'-I/home/dgoffred/mbig/git/dlib/dlibiboxcore',
'-I/home/dgoffred/mbig/git/dlib/dliblisted',
'-I/home/dgoffred/mbig/git/dlib/dlibmktcmdty',
'-I/home/dgoffred/mbig/git/dlib/dlibmkteq',
'-I/home/dgoffred/mbig/git/dlib/dlibmkteqcore',
'-I/home/dgoffred/mbig/git/dlib/dlibmktfcd',
'-I/home/dgoffred/mbig/git/dlib/dlibmktfx',
'-I/home/dgoffred/mbig/git/dlib/dlibmktir',
'-I/home/dgoffred/mbig/git/dlib/dlibotccalclient',
'-I/home/dgoffred/mbig/git/dlib/dlibpdfgen',
'-I/home/dgoffred/mbig/git/dlib/dlibqfd',
'-I/home/dgoffred/mbig/git/dlib/dlibscn',
'-I/home/dgoffred/mbig/git/dlib/dlibui',
'-I/home/dgoffred/mbig/git/dlib/dlibuitypes',
'-I/home/dgoffred/mbig/git/dlib/iboxtypes',
'-I/home/dgoffred/mbig/git/dlib/m_dlibxl',
'-I/home/dgoffred/mbig/git/dlib/m_exdl',
'-I/home/dgoffred/mbig/git/dlib/m_exdlhandler',
'-I/home/dgoffred/mbig/git/dlib/m_ibox',
'-I/home/dgoffred/mbig/git/dlib/m_otccaln',
'-I/home/dgoffred/mbig/git/dlib/m_otcdsp',
'-I/home/dgoffred/mbig/git/dlib/thirdparty',
'-I/home/dgoffred/mbig/git/dlib/thirdparty/otcxsvcmsg']

translationUnit = getTransUnit(inFilepath, ['-xc++', '-std=c++98'] + hackyHackyFlaggyFlaggy)

didFindError = printErrors(translationUnit)
if didFindError:
    sys.exit('FATAL One or more errors found in compilation unit.')

# Comment out if it's too loud (it gets really loud)
#
# traverse(translationUnit.cursor, TreePrinter())

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

    # "assert" might be too harsh.
    # assert len(matches) > 0
    if len(matches) == 0:
        printf('ERROR The following cursor does not have an eponymous token:')
        printf(cursor.location.file.name)
        printCursor(cursor)
        return None
                       # Take the last rather than the first, 
    return matches[-1] # in case the parameter shares its name with a type.
    

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
    with open(filename, 'r') as fin:
        printf('Rewriting file {}', filename)
        with open(filename + '.rewrite', 'w') as fout:
            rewrite(fin, fout, rewrites)


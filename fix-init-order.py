#!/usr/bin/python

from clangwrapper import Index, CursorKind, Cursor, HashableCursor
from observer import traverse, Observer, ObserverGroup, TreePrinter

def getTransUnit(filepath, flags):
    index = Index.create()
    transUnit = index.parse(filepath, flags)
    return transUnit

from collections import defaultdict

def isRecordDef(kind):
    return kind in (CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION,
                    CursorKind.CLASS_DECL,
                    CursorKind.UNION_DECL,
                    CursorKind.CLASS_TEMPLATE,
                    CursorKind.STRUCT_DECL)

from pprint import pprint

class FieldFinder(Observer):
    def __init__(self):
        super(FieldFinder, self).__init__()
        self.classFields = defaultdict(list)
        self.classes = []
        self.fieldOrders = {} # Where each field is in its initializer list

    def observe(self, cursor):
        if isRecordDef(cursor.kind):
            self.classes.append(HashableCursor(cursor))
        elif cursor.kind == CursorKind.FIELD_DECL:
            fields = self.classFields[self.classes[-1]]
            self.fieldOrders[HashableCursor(cursor)] = len(fields)
            fields.append(cursor)

    def popTo(self, cursor):
        if isRecordDef(cursor.kind):
            assert self.classes[-1] == cursor
            self.classes.pop()

    def prettyPrint(self):
        pprint([(record.displayname, [ (f.displayname, self.fieldOrders[HashableCursor(f)]) for f in fields ]) \
                for record, fields in self.classFields.iteritems()])

class InitMember:
    def __init__(self, cursor):
        self.cursor = cursor
        self.filename = cursor.location.file.name
        self.beginOffset = cursor.extent.start.offset
        self.endOffset = None # later
        # Note: My endOffset is one-past-last. This is *different* from what
        #       cursor.extent.end.offset gives you. InitMember's end is
        #       exclusive, while the cursor's is inclusive.

        self.text = None # later

    def __repr__(self):
        if self.text is not None:
            return '"{}"'.format(self.text)
        else:
            return self.cursor.displayname

    def __eq__(self, other):
        return self.cursor == other.cursor
    def __ne__(self, other):
        return not self == other

class InitFinder(Observer):
    def __init__(self):
        super(InitFinder, self).__init__()
        self._currentConstructor = None
        self.constructorFields = defaultdict(list)
        self._depthWithinConstructor = None # None if at or above. >= 1 if below.
        self._prevChildOfConstructor = None # Last seen immediate child.
        self._prevMemberOfConstructor = None # Last seen child of kind MEMBER_REF.

    def _inConstructorChildren(self):
        return self._depthWithinConstructor == 1

    def _updatePreviousMemberOfConstructor(self):
        if self._prevMemberOfConstructor is None:
            return # Nothing to update

        prevChild, prevMember = self._prevChildOfConstructor, self._prevMemberOfConstructor
        assert prevChild != prevMember.cursor

        children = list(prevChild.get_children())
        if len(children) == 0:
            # Danger -- experimental
            if prevChild.extent.end.offset == 0: # Which would be nonsense.
                # Assume we had something like "field()," and so go up to the
                # comma. There may still be issues with whitespace. Beware!
                prevMember.endOffset = prevMember.cursor.extent.end.offset + 2
            else:
                prevMember.endOffset = prevChild.extent.end.offset + 1 
            # See note in class InitMember if you're wondering about the +1
        else:
            # Use the end of the last child of the previous item 
            # in the current constructor. Often the marked end of
            # prevChild is wrong, but children[-1] is right.
            #
            prevMember.endOffset = children[-1].extent.end.offset + 1
        
        self._prevMemberOfConstructor = None # Done with that guy

    def observe(self, cursor):
        if cursor.kind == CursorKind.CONSTRUCTOR:
            self._currentConstructor = HashableCursor(cursor)
        elif self._inConstructorChildren():
            if cursor.kind == CursorKind.MEMBER_REF:
                self._updatePreviousMemberOfConstructor()
                member = InitMember(cursor)
                self.constructorFields[self._currentConstructor].append(member)
                self._prevMemberOfConstructor = member
            # Different things that could "halt" a member initialization:
            #   COMPOUND_STMT would mean we're at the constructor body.
            #   TYPE_REF would mean we're calling a base class constructor
            #   (perhaps illegally, since base class constructors should 
            #    come before any members)
            #   NAMESPACE_REF would mean we're introducing a qualified base
            #    class constructor, so same situation as TYPE_REF.
            #
            elif cursor.kind in (CursorKind.COMPOUND_STMT, CursorKind.TYPE_REF, CursorKind.NAMESPACE_REF):
                self._updatePreviousMemberOfConstructor()
            elif cursor.kind == CursorKind.UNEXPOSED_EXPR \
             and cursor.extent.start == cursor.extent.end:
                printerr('!!! Warning: This node could be crap')

            self._prevChildOfConstructor = cursor

    def popTo(self, cursor):
        if cursor.kind == CursorKind.CONSTRUCTOR:
            if self._currentConstructor != cursor:
                raise ValueError('''Error: cursor={} _currentConstructor={} 
                                 should be equal'''.format(cursor.displayname, 
                                                           self._currentConstructor.displayname))
            self._depthWithinConstructor = None
            self._currentConstructor = None
            self._prevChildOfConstructor = None
            self._prevMemberOfConstructor = None
        elif self._depthWithinConstructor is not None:
            self._depthWithinConstructor -= 1

    def pushFrom(self, cursor):
        if cursor.kind == CursorKind.CONSTRUCTOR:
            self._depthWithinConstructor = 1
            if self._currentConstructor != cursor:
                raise ValueError('''Error: cursor={} _currentConstructor={} 
                                 should be equal'''.format(cursor.displayname, 
                                                           self._currentConstructor.displayname))
        elif self._depthWithinConstructor is not None:
            self._depthWithinConstructor += 1

    def prettyPrint(self):
        pprint([( constructor.displayname, [f for f in fields]) \
                 for constructor, fields in self.constructorFields.iteritems() ])

    # When the InitFinder is done, it contains a bunch of
    # (cursor, filename, begin, end) objects designating
    # where the member initializers are. This function opens
    # the apprioriate files and reads the text corresponding to
    # each member initializer, and writes it to the initializer's
    # .text attribute.
    #
    def fillInitFieldsText(self):
        files = {}
        def getFile(name):
            f = files.get(name)
            if f is None:
                f = open(name, 'r')
                files[name] = f
            return f

        for memberList in self.constructorFields.itervalues():
            for member in memberList:
                f = getFile(member.filename)
                f.seek(member.beginOffset)
                member.text = f.read(member.endOffset - member.beginOffset)

        # Clean up
        for file in files.itervalues():
            file.close()

class MisorderedInitMember:
    def __init__(self, wrong, right):
        self.wrong = wrong
        self.right = right

def misorderedInitMembers(fields, inits):
    orders = fields.fieldOrders
    def lookupOrder(member):
        return orders[HashableCursor(member.cursor.get_definition())]
    for constructor, fields in inits.constructorFields.iteritems():
        sortedCopy = list(sorted(fields, key=lookupOrder))
        assert len(sortedCopy) == len(fields)
        for asInConstructor, asInDefinition in zip(fields, sortedCopy):
            if asInDefinition != asInConstructor:
                if args.verbose:
                    printf('{} {} --> {}', 
                           constructor.displayname, 
                           asInConstructor.text,
                           asInDefinition.text)
                yield MisorderedInitMember(asInConstructor, asInDefinition)

def getRewrites(fields, inits):
    # A single rewrite has the form:
    #    (beginOffset, originalLength, replacementText)
    # but here I prepend filename so we can group by it next.
    #
    rewrites = [(x.wrong.filename,
                 x.wrong.beginOffset, 
                 len(x.wrong.text), 
                 x.right.text) for x in misorderedInitMembers(fields, inits)]
    
    rewritesByFile = defaultdict(list)
    for rw in rewrites:
        rewritesByFile[rw[0]].append(rw[1:])

    return rewritesByFile


import argparse
def parseArgs():
    parser = argparse.ArgumentParser(description='Rewrite misordered items in member initializer lists.')
    parser.add_argument('file', type=str,
                        help='The source file to analyze and rewrite.')
    parser.add_argument('flags', type=str, nargs='*',
                        help='A compiler flag to pass through the clang.')
    parser.add_argument('--flags-file', dest='flagsFile', action='store',
                        help='Path to a file containing clang compiler flags separated by newlines.')
    parser.add_argument('--log-file', '-l', dest='logFile', action='store',
                        help='Path to a file where verbose logging will be written.')
    parser.add_argument('--verbose', '-v', action='count',
                        help='Log to stdout verbosely.')
    return parser.parse_args()

def getFlagsFromFile(name):
    with open(name, 'r') as file:
        return [ line.strip() for line in file.readlines()]

def getFlagsFromArgs(args):
    if args.flagsFile:
        return getFlagsFromFile(args.flagsFile) + args.flags
    else:
        return args.flags

def doNothing(*args, **kwargs):
    pass

if __name__ == '__main__':
    args = parseArgs()

    import subprocess
    import sys
    import fileprinter

    if args.logFile and args.verbose:
        tee = subprocess.Popen(['tee', args.logFile], stdin=subprocess.PIPE)
        printf = fileprinter.FilePrinter(tee.stdin)
    elif args.logFile:
        printf = fileprinter.FilePrinter(open(args.logFile, 'w'))
    elif args.verbose:
        printf = fileprinter.printf # stdout
    else:
        printf = doNothing

    printerr = fileprinter.FilePrinter(sys.stderr)

    filepath = args.file
    flags = getFlagsFromArgs(args)
    transUnit = getTransUnit(filepath, ['-xc++', '-std=c++98'] + flags)
    c = transUnit.cursor

    printer = TreePrinter()
    fields = FieldFinder()
    inits = InitFinder()
    observers = ObserverGroup([fields, inits, printer])

    traverse(c, observers)
    inits.fillInitFieldsText()

    if args.verbose:
        printf('')
        printf('\nThe fields:')
        fields.prettyPrint()
        printf('\nThe constructors:')
        inits.prettyPrint()
        printf('')

    rewritesPerFile = getRewrites(fields, inits)
    printf('\nThe rewrites:')
    printf(rewritesPerFile)

    for diag in transUnit.diagnostics:
        printerr('**** {}', diag)
        for fix in diag.fixits:
            printerr(' ****     possible fix --> {}', fix)

    printf("Now let's try to do the rewrites")
    from rewrite import rewrite
    for filename, rewrites in rewritesPerFile.iteritems():
        if filename != filepath:
            printf('Skipping file {}', filename)
            continue
        with open(filename, 'r') as fin:
            with open(filename + '.rewrite', 'w') as fout:
                rewrite(fin, fout, rewrites)


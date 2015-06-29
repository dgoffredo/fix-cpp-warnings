#!/usr/bin/python

from clangwrapper import CursorKind, Cursor, HashableCursor
from observer import traverse, Observer, ObserverGroup
from collections import defaultdict
import fixer

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

def extentIsBetween(test, begin, end):
    return test.extent.start.offset >= begin.extent.start.offset \
           and test.extent.end.offset <= end.extent.end.offset

def isCppStyleComment(token):
    return token.kind.name == 'COMMENT' and token.spelling[:2] == '//'

class InitFinder(Observer):
    def __init__(self):
        super(InitFinder, self).__init__()
        self._currentConstructor = None
        self._currentConstructorTokens = None
        self.constructorFields = defaultdict(list)
        self._depthWithinConstructor = None # None if at or above. >= 1 if below.
        self._prevChildOfConstructor = None # Last seen immediate child.
        self._prevMemberOfConstructor = None # Last seen child of kind MEMBER_REF.

    def _inConstructorChildren(self):
        return self._depthWithinConstructor == 1

    def _updatePreviousMemberOfConstructor(self, currentCursor):
        if self._prevMemberOfConstructor is None:
            return # Nothing to update

        assert self._currentConstructor is not None

        prevChild, prevMember = self._prevChildOfConstructor, self._prevMemberOfConstructor
        assert prevChild != prevMember.cursor

        tokensBetween = [tok for tok in self._currentConstructorTokens \
                         if extentIsBetween(tok, prevMember.cursor, currentCursor)]
        assert len(tokensBetween) > 0

        separatorsBetween = [tok for tok in tokensBetween \
                             if tok.spelling in (',', '{')]
        assert len(separatorsBetween) > 0
        lastSeparator = separatorsBetween[-1]

        # We want to consume whitespace before lastSeparatorBegin,
        # but only if the previous token (if one exists) is not
        # a cppStyleComment.
        #
        tokIndex = tokensBetween.index(lastSeparator)
        if tokIndex != 0 and not isCppStyleComment(tokensBetween[tokIndex - 1]):
            tokJustBefore = tokensBetween[tokIndex - 1]
            # Eat whitespace
            printf('For member "{}" I\'m backing up to the token "{}"', 
                   prevMember.cursor.spelling,
                   tokJustBefore.spelling)
            prevMember.endOffset = tokJustBefore.extent.end.offset
        else:
            # Don't eat whitespace
            printf('For member "{}" I\'m sticking with token "{}"', 
                   prevMember.cursor.spelling,
                   lastSeparator.spelling)
            prevMember.endOffset = lastSeparator.extent.start.offset

        self._prevMemberOfConstructor = None # Done with that guy

    def observe(self, cursor):
        if cursor.kind == CursorKind.CONSTRUCTOR:
            self._currentConstructor = HashableCursor(cursor)
            self._currentConstructorTokens = list(cursor.get_tokens())
        elif self._inConstructorChildren():
            if cursor.kind == CursorKind.MEMBER_REF:
                self._updatePreviousMemberOfConstructor(cursor)
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
                self._updatePreviousMemberOfConstructor(cursor)
            elif cursor.kind == CursorKind.UNEXPOSED_EXPR \
             and cursor.extent.start == cursor.extent.end:
                printerr('Warning: This node could be crap')

            self._prevChildOfConstructor = cursor

    def popTo(self, cursor):
        if cursor.kind == CursorKind.CONSTRUCTOR:
            assert self._currentConstructor == cursor
            self._depthWithinConstructor = None
            self._currentConstructor = None
            self._currentConstructorTokens = None
            self._prevChildOfConstructor = None
            self._prevMemberOfConstructor = None
        elif self._depthWithinConstructor is not None:
            self._depthWithinConstructor -= 1

    def pushFrom(self, cursor):
        if cursor.kind == CursorKind.CONSTRUCTOR:
            assert self._currentConstructor == cursor
            self._depthWithinConstructor = 1
        elif self._depthWithinConstructor is not None:
            self._depthWithinConstructor += 1

    def prettyPrint(self):
        pprint([( constructor.displayname, [f for f in fields]) \
                 for constructor, fields in self.constructorFields.iteritems() ])

    # When the InitFinder is done, it contains a bunch of
    # (cursor, filename, begin, end) objects designating
    # where the member initializers are. This function opens
    # the appropriate files and reads the text corresponding to
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

def doNothing(*args, **kwargs):
    pass

if __name__ == '__main__':

    util = fixer.Fixer('Rewrite misordered items in member initializer lists.')
    args, transUnit = util.setup()
    filepath = util.filepath
    
    import fileprinter
    printf = fileprinter.printf if args.verbose else doNothing
    printerr = fileprinter.printerr
   
    fields = FieldFinder()
    inits = InitFinder()
    observers = ObserverGroup([fields, inits])

    traverse(transUnit.cursor, observers)
    inits.fillInitFieldsText()

    if args.verbose:
        printf('\n\nThe fields:')
        fields.prettyPrint()
        printf('\n\nThe constructors:')
        inits.prettyPrint()
        printf('')

    rewritesPerFile = getRewrites(fields, inits)
    printf('\nThe rewrites:')
    printf(rewritesPerFile)

    printf("Now let's try to do the rewrites")
    from rewrite import rewrite
    for filename, rewrites in rewritesPerFile.iteritems():
        if filename != filepath:
            printf('Skipping file {}', filename)
            continue
        elif len(rewrites) == 0:
            continue
        with open(filename, 'r') as fin:
            with open(filename + '.rewrite', 'w') as fout:
                rewrite(fin, fout, rewrites)


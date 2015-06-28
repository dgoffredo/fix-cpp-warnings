#!/usr/bin/python

from clangwrapper import HashableLocation, CursorKind
from observer import traverse, Observer, printCursor, repeatedString
import fixer

# Will find the parent of the //first// (uppermost) cursor for each location 
# passed into its constructor.
# The instance attribute 'cursors' is a dict from HashableLocation --> Cursor
#
class FindCursorParent(Observer):
    def __init__(self, locations):
        super(FindCursorParent, self).__init__()
        self.locations = set(locations)
        self.cursors = dict() # HashableLocation --> Cursor
        self.parentStack = []

    def observe(self, cursor):
        loc = HashableLocation(cursor.location)
        parents = self.parentStack
        if len(parents) == 0:
            return # Can't get a parent if there aren't any.

        # If looking for it and haven't found it
        if loc in self.locations and loc not in self.cursors:
            parent = self.parentStack[-1]
            self.cursors[loc] = parent

    def pushFrom(self, cursor):
        self.parentStack.append(cursor)
    
    def popTo(self, cursor):
        self.parentStack.pop()

def firstWith(sequence, predicate, default=None):
    return next((x for x in sequence if predicate(x)), default)

def getSwitchRewrite(switchCursor, printerr):
    if switchCursor.kind != CursorKind.SWITCH_STMT:
        printerr('This cursor is a {} instead of a switch.',
                 switchCursor.kind)
        return None

    # Find the only compound statement in the switch.
    body = None
    for child in switchCursor.get_children():
        if child.kind == CursorKind.COMPOUND_STMT:
            if body is not None:
                printerr("This switch has two or more bodies. Here's the second one:")
                printCursor(child, printer=printerr)
                return None
            else:
                body = child

    if body is None:
        printerr("This switch doesn't have a body. That's legal, but I can't work with it.")
        return None

    # Find the last child of the body.
    children = list(body.get_children())
    if len(children) == 0:
        printerr("The body of this switch doesn't have any children. What the hell.")
        return None

    lastChild = children[-1]
    offset = list(lastChild.get_tokens())[-1].extent.end.offset

    def isCase(cursor):
        return cursor.kind == CursorKind.CASE_STMT
        
    cursorToBeBelow = firstWith(reversed(children), isCase) or lastChild
    indentation = repeatedString(' ', cursorToBeBelow.location.column - 1)

    # A rewrite is (offset to beginning, length of old text, new text)
    # Note: I don't append a newline since I assume that the last token 
    #       of the last child was probably followed by a newline.
    tabWidth = 4
    return (offset, 0, '\n{0}default:\n{0}{1}break;{2}'.format(
                           indentation, 
                           repeatedString(' ', tabWidth),
                           '' if args.noTodo else ' /* TODO? */'))

if __name__ == '__main__':
    import fileprinter
    printf = fileprinter.printf
    printerr = fileprinter.printerr

    util = fixer.Fixer("Add no-op 'default:' to incomplete switches on enum types.")
    util.add_argument('--no-todo', dest='noTodo', action='count',
                      help="Don't add a TODO comment to each inserted 'default:'")
    args, transUnit = util.setup()
    filepath = util.filepath

    switchWarnLocations = set(HashableLocation(diag.location) \
                              for diag in transUnit.diagnostics \
                              if diag.option == '-Wswitch')

    finder = FindCursorParent(switchWarnLocations)
    traverse(transUnit.cursor, finder)

    rewrites = [getSwitchRewrite(cursor, printerr) for cursor in finder.cursors.itervalues()]

    if len(rewrites) > 0:
        fin = open(filepath, 'r')
        fout = open(filepath + '.rewrite', 'w')
        from rewrite import rewrite
        rewrite(fin, fout, rewrites)


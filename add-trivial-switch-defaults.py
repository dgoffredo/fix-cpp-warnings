#!/usr/bin/python

from clangwrapper import Index, HashableLocation, CursorKind
from observer import traverse, Observer, TreePrinter, printCursor, repeatedString

def getTransUnit(filepath, flags):
    index = Index.create()
    transUnit = index.parse(filepath, flags)
    return transUnit

from pprint import pprint

import argparse
def parseArgs():
    parser = argparse.ArgumentParser(description='Rewrite misordered items in member initializer lists.')
    parser.add_argument('--flags-file', dest='flagsFile', action='store',
                        help='Path to a file containing clang compiler flags separated by newlines.')
    parser.add_argument('file', type=str,
                        help='The source file to analyze and rewrite.')
    parser.add_argument('flags', type=str, nargs='*',
                        help='A compiler flag to pass through the clang.')
    return parser.parse_args()

def getFlagsFromFile(name):
    with open(name, 'r') as file:
        return [ line.strip() for line in file.readlines()]

def getFlagsFromArgs(args):
    if args.flagsFile:
        return getFlagsFromFile(args.flagsFile) + args.flags
    else:
        return args.flags

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
            printf('Found one:')
            printCursor(cursor)
            parent = self.parentStack[-1]
            printf("Here's the parent:")
            printCursor(parent)
            self.cursors[loc] = parent

    def pushFrom(self, cursor):
        self.parentStack.append(cursor)
    
    def popTo(self, cursor):
        self.parentStack.pop()


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

    last = children[-1]
    indentation = repeatedString(' ', last.location.column - 1)
    offset = last.extent.end.offset + 1

    # A rewrite is (offset to beginning, length of old text, new text)
    return (offset, 0, '\n{}default: break; /* TODO? */'.format(indentation)) 

if __name__ == '__main__':
    args = parseArgs()

    import subprocess
    import sys
    import fileprinter

    printf = fileprinter.printf # stdout
    printerr = fileprinter.FilePrinter(sys.stderr)

    filepath = args.file
    flags = getFlagsFromArgs(args)
    hardcodedFlags = ['-xc++', '-std=c++98', '-Wall']
    transUnit = getTransUnit(filepath, hardcodedFlags + flags)
    c = transUnit.cursor

    switchWarnLocations = set()
    hack = None

    for diag in transUnit.diagnostics:
        printerr('\n**** {} <{} ({}) [{}]>', 
                 diag, 
                 diag.category_name, 
                 diag.category_number,
                 diag.option)
        for fix in diag.fixits:
            printerr(' ****     possible fix --> {}', fix)

        if diag.option == '-Wswitch':
            switchWarnLocations.add(HashableLocation(diag.location))

    printer = TreePrinter()
    traverse(c, printer)
    printf('\n\n')

    from pprint import pprint
    pprint(switchWarnLocations)

    finder = FindCursorParent(switchWarnLocations)
    traverse(c, finder)

    rewrites = [getSwitchRewrite(cursor, printerr) for cursor in finder.cursors.itervalues()]
    pprint(rewrites)

    fin = open(filepath, 'r')
    fout = open(filepath + '.rewrite', 'w')
    from rewrite import rewrite
    rewrite(fin, fout, rewrites)


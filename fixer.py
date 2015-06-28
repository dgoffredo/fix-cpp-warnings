
import argparse
import fileprinter
import sys
from clangwrapper import Index, Diagnostic
from observer import traverse, TreePrinter
import re

# Shared utilties for the initialization of warning fixer scripts:
#    - Command line arguments (including reading compiler flags)
#    - Printing the syntax tree
#    - Detecting parsing errors
#
# Come to think of it, this doesn't really need to be an object.
# I just like how the caller doesn't have to import argparse.
#
class Fixer(object):
    def __init__(self, description):
        self._parser = argparse.ArgumentParser(description=description)
        _addDefaultArgs(self._parser)

    def add_argument(self, *args, **kwargs):
        self._parser.add_argument(*args, **kwargs)

    def setup(self):
        self.args = self._parser.parse_args()
        self.filepath = self.args.file
        self.flags = _getFlagsFromArgs(self.args)

        hardcodedFlags = ['-xc++', '-std=c++98', '-Wall']
        self.transUnit = _getTranslationUnit(self.filepath, hardcodedFlags + self.flags)

        if self.args.verbose:
            traverse(self.transUnit.cursor, TreePrinter())
            printf('\n')
        
        didFindError = _printErrors(self.transUnit, fileprinter.printerr)
        if didFindError and not self.args.ignoreErrors:
            sys.exit('FATAL One or more errors found in compilation unit.')

        return self.args, self.transUnit

def _getTranslationUnit(filepath, flags):
    index = Index.create()
    transUnit = index.parse(filepath, flags)
    return transUnit

def _addDefaultArgs(parser):
    parser.add_argument('file', type=str,
                        help='The source file to analyze and rewrite.')
    parser.add_argument('--flags-file', dest='flagsFile', action='store',
                        help='Path to a file containing clang compiler flags separated by newlines.')
    parser.add_argument('--verbose', '-v', action='count',
                        help='Log to stdout verbosely.')
    parser.add_argument('--ignore-errors', dest='ignoreErrors', action='count',
                        help="Don't quit after encountering a compiler error.")

def _getFlagsFromFile(name):
    with open(name, 'r') as file:
        uncommented = [ line.strip() for line in file.readlines() if not re.match(r'^\s*#', line)]
        unblank = [ line for line in uncommented if len(line) > 0 ]
        return unblank

def _getFlagsFromArgs(args):
    if args.flagsFile:
        return _getFlagsFromFile(args.flagsFile)
    else:
        return []

def _printErrors(transUnit, printerr):
    didFindError = False
    for diag in transUnit.diagnostics:
        if diag.severity >= Diagnostic.Error:
            didFindError = True
        printerr('**** {}', diag)
        for fix in diag.fixits:
            printerr(' ****     possible fix --> {}', fix)
    return didFindError


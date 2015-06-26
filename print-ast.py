#!/usr/bin/python

from clangwrapper import Index
from observer import traverse, TreePrinter

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

    printer = TreePrinter()
    traverse(c, printer)

    for diag in transUnit.diagnostics:
        printerr('\n**** {} <{} ({}) [{}]>', 
                 diag, 
                 diag.category_name, 
                 diag.category_number,
                 diag.option)
        for fix in diag.fixits:
            printerr(' ****     possible fix --> {}', fix)

#!/usr/bin/python

import fixer
from observer import traverse, TreePrinter

def printToken(token):
   s = '"{}"\t{}\t{}.{}({}) - {}.{}({})'.format(
           token.spelling,
           token.location.file.name if token.location.file else '',
           token.extent.start.line,
           token.extent.start.column,
           token.extent.start.offset,
           token.extent.end.line,
           token.extent.end.column,
           token.extent.end.offset)
   print(s)

if __name__ == '__main__':
    util = fixer.Fixer('Print the abstract syntax tree (AST) of a C++ file')
    args, translationUnit = util.setup()

    # for token in translationUnit.get_tokens(extent=translationUnit.cursor.extent):
    # for token in translationUnit.cursor.get_tokens():
    #     printToken(token)

    # If --verbose was passed, then we already printed the tree. If not,
    # then we print the tree here, and restrict it to the specified file.
    #
    if not args.verbose:
        traverse(translationUnit.cursor, TreePrinter(whitelist=set([util.filepath])))


#!/usr/bin/python

import fixer
from observer import traverse, TreePrinter

if __name__ == '__main__':
    util = fixer.Fixer('Print the abstract syntax tree (AST) of a C++ file')
    args, translationUnit = util.setup()

    # If --verbose was passed, then we already printed the tree. If not,
    # then we print the tree here.
    #
    if not args.verbose:
        traverse(translationUnit.cursor, TreePrinter())


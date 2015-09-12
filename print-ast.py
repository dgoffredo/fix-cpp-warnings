'''
    FixCppWarnings - Automated C++ rewriting for common compiler warnings
    Copyright (C) 2015  David Goffredo

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
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


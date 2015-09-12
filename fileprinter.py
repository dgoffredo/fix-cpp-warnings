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

# Is typing
#
#    file.write('{} blah {} {}\n'.format(foo, bar, baz))
#
# starting to get you down? Would writing
#
#    printer('{} blah {} {}', foo, bar, baz)
#
# make you feel better? Then all you need to do is
#
#    from fileprinter import FilePrinter
#    printer = FilePrinter(file)
#
# and the world is yours.
#
def FilePrinter(file):
    def printer(s, *args, **kwargs):
        if len(args) == 0 and len(kwargs) == 0:
            file.write('{}\n'.format(s))
        else:
            file.write(s.format(*args, **kwargs) + '\n')
    return printer

# For convenience, as a replacement for vanilla print()
#
import sys
printf = FilePrinter(sys.stdout)
printerr = FilePrinter(sys.stderr)


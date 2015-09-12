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

# Wrapper around a list() with some set operations.
# This is for when you need a set() of uncomparable, 
# unhashable items.
# Watch out for those algorithmic complexities.
#
class linearset(object):
    def __init__(self, iterable=None):
        self._items = []
        if not iterable:
            return

        for item in iterable:
            if item not in self:
                self.add(item)

    def add(self, item):
        if item not in self:
            self._items.append(item)

    def remove(self, item):
        self._items.remove(item)

    def __contains__(self, item):
        for member in self._items:
            if member == item:
                return True
        return False

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)

    # Comparisons would be n**2, so I omit them.
    #
    def __cmp__(self):
        raise Exception('Use a different data structure.')


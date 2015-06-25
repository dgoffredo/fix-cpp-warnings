
import clang
from clang.cindex import *

# This is where the matching version of libclang.so is
# on adslnydnlpap01 (and probably most other linux machines,
# according to Andrew Paprocki)
Config.set_library_path('/opt/bb/lib64') 

# clang.cindex.Cursor has a hash property (a wrapper around a clang hash)
# but it's not used to define a .__hash__ method, so I have to wrap
# up the whole Cursor just to be able to use it as a dict key.
#
class HashableCursor(object):
    def __init__(self, cursor):
        self.cursor = cursor

    def __getattr__(self, attr):
        return getattr(self.cursor, attr)

    def __repr__(self):
        return repr(self.cursor)

    def __str__(self):
        return str(self.cursor)

    def __hash__(self):
        return self.cursor.hash

    def __eq__(self, other):
        if type(other) is Cursor:
            return other == self.cursor
        else:
            return other.cursor == self.cursor

    def __ne__(self, other):
        return not self == other


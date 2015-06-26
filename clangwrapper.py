
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

# TODO Would plain delegation ("inheritance") work for here and HashableCursor,
#      or is the explicit forwarding of behavior necessary?
#
class HashableLocation(object):
    def __init__(self, location):
        self.location = location

    def __getattr__(self, attr):
        return getattr(self.location, attr)

    def __repr__(self):
        return repr(self.location)

    def __str__(self):
        return str(self.location)

    def __hash__(self):
        loc = self.location
        # Key is filename, offset.
        # Sometimes there is no file, so I account for that.
        key = (None if loc.file is None else loc.file.name, loc.offset)
        return hash(key)

    def __eq__(self, other):
        if type(other) is SourceLocation:
            return other == self.location
        else:
            return other.location == self.location

    def __ne__(self, other):
        return not self == other

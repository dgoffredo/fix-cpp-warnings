
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


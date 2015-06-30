
from observer import Observer, nameOrBlank, traverse
from fileprinter import printf
from fixer import Fixer
from linearset import linearset

# Collect the types as you go. 
#
class TypeGrabber(Observer):
    def __init__(self, whitelist=set()):
        super(TypeGrabber, self).__init__()
        self.whitelist = whitelist
        self.types = linearset()

    def _ignore(self, c):
        return len(self.whitelist) > 0 \
            and nameOrBlank(c.location.file) not in self.whitelist

    def observe(self, c):
        if self._ignore(c):
            return
        self.types.add(c.type)

# class Type:...
# def kind(self):
# def argument_types(self):
# def element_type(self):
# def element_count(self):
# def translation_unit(self):
# def from_result(res, fn, args):
# def get_canonical(self):
# def is_const_qualified(self):
# def is_volatile_qualified(self):
# def is_restrict_qualified(self):
# def is_function_variadic(self):
# def is_pod(self):
# def get_pointee(self):
# def get_declaration(self):
# def get_result(self):
# def get_array_element_type(self):
# def get_array_size(self):
# def get_class_type(self):
# def get_align(self):
# def get_size(self):
# def get_offset(self, fieldname):
# def get_ref_qualifier(self):
# def spelling(self):
# def __eq__(self, other):
# def __ne__(self, other):

def printType(cppType, columnWidth, printer=printf):
    printer('{{:<{0}}}{{:<{0}}}{{:<{0}}}'.format(columnWidth),
            '"' + cppType.spelling + '"',
            cppType.kind,
            cppType.get_ref_qualifier())

if __name__ == '__main__':
    util = Fixer('Print all of the types in a translation unit.')
    util.add_argument('--column-width', dest='columnWidth', default=45,
                      help='Width in characters of each output column')
    args, translationUnit = util.setup()

    grabber = TypeGrabber()
    traverse(translationUnit.cursor, grabber)

    if len(grabber.types):
        printf('{{:<{0}}}{{:<{0}}}{{:<{0}}}'.format(args.columnWidth),
               '---- Name ----', 
               '---- Kind ----',
               '---- Ref Qualifier ----')
    for cppType in grabber.types:
        printType(cppType, args.columnWidth)


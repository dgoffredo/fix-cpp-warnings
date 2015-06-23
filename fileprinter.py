
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


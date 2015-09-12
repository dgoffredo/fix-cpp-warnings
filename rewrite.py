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

def rewrite(fin, fout, rewrites, alreadySorted=False):
    if not alreadySorted:
        def selectOffset(tup):
            return tup[0]
        rewrites = sorted(rewrites, key=selectOffset)

    fin.seek(0) 
    FROM_CURRENT_POSITION = 1
    for offset, oldLen, replacement in rewrites:
        fout.write(fin.read(offset - fin.tell())) # catch up
        fout.write(replacement)
        fin.seek(oldLen, FROM_CURRENT_POSITION) # skip the old

    fout.write(fin.read()) # the rest of it


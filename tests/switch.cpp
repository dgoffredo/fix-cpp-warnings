/*
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
*/


enum Color {
    Red, Green, Blue, Yellow, Orange,
    Purple, Magenta, Violet, Brown,
    Black, White, Gray
};

void f(Color longVariableName)
{
    // Bugged version
    //
    switch (longVariableName)
    {
        case Gray:
        {
        }
    } (void) longVariableName;

    switch (longVariableName)
    {
        case Green:
        {
        } /*comment*/
    };

    switch (longVariableName)
    {
        case Blue:
            break;
        case Red:
            break   ;
    } /* stuff */

    switch (longVariableName)
    {
        case Blue:
            break;
        case Red:
            break; // About red
    }
}


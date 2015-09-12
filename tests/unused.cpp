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


int foo(int, char x, const double * const & s, float y) 
{
    (void) s;
    y = 0;
    return 0;
}

struct Foo {
    int method1(const char *s, double dee, float) const {
        dee += 2.0;
        return static_cast<int>(dee);
    }

    double method2(char, char);
};

double Foo::method2(char a, char b) 
{
    return static_cast<double>(a);
}

template <unsigned sz, typename T>
int nada(int ret, const T & unusedArg)
{
    char dummy[sz] = {};
    (void) dummy;
    return ret;
}

void nested(int i, double d) {
    nada<0>(i, d);
}

bool weirdOne(Foo f, char c, double d) try {
    f.method2(c, c);
    return true;
}
catch (...) {
}

void terribleSituation(int outer, double dupe)
{
    (void) outer;
    struct Structception {
        double method(int inner, double dupe) {
            return dupe;
        }
    } instance;
}

// int main() {
//     Foo f;
//     f.method1("haha", 23.6, 12);
//     f.method2('x', 'y');
// 
//     return 0;
// }

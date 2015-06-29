
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

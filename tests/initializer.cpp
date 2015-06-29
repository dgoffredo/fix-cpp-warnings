
struct Foo
{
    int member1;
    double member2;

    Foo(int, double, char);
};

Foo::Foo(int x, double y, char c)
    : member1(x), member2()
{
    y = 5.4;
}


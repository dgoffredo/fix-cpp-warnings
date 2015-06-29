
class C
{
    int a;
    int b;
    double c;

  public:
    C();
};

C::C()
  : c(3.4),
    a() // hah!

{}

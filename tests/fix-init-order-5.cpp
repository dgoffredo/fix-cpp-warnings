class C
{
    int a;
    int b;
    double c;
    int d;
    int e;
    int f;
    int g;
    int h;
    int i;

  public:
    C();
};

C::C()
  : c(3.4) // Killer comment!
   ,a()
   ,b()
   ,g()
   ,e()
   ,i()
   ,d()
   ,h()
   ,f() // Here's a comment
{
    // body
}

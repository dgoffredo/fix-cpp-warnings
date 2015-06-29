
double identity(double d)
{
    return d;
}

class C
{
    int a;
    int b;
    double c;

  public:
    C();
};

C::C()
    : b(/*content*/), 
      c(identity(4.5)), 
      a(  ) 
{}


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


# FixCppWarnings
Clang-based rewriters (in python) for the more easily fixed issues diagnosed by gcc's `-Wall`

# Tips

 - Run on a linux machine where clang is present. That's most dev linux machines. 
 - The tricky part of using these scripts is supplying the appropriate compiler flags; namely all of the `-I`s and `-D`s clang needs to understand your code.
 - Any diagnostic of severity 3 or greater (error) is enough to mess up these scripts.
 - The output of each script is a file with the same name as the input file, but with an additional suffix `.rewrite`.

# Scripts

## fix-init-order.py
#### Purpose
This is for `-Wreorder`, when the compiler warns `"memberX will be initialized before memberY when initialized here..."`. That's telling you that the order of a class's members in the class definition is different than it is in a particular initializer list. See http://stackoverflow.com/questions/1828037/whats-the-point-of-g-wreorder . This script will reorder the initializers _in the constructor_.
#### Comments
Make sure that you provide the proper `-I` and `-D` flags so that clang compiles your code without errors. If there are compiler errors, even if they occur far away from your intended rewrite, the AST produced by clang will be incomplete, and so `fix-init-order.py` can then miss instances of `-Wreorder`.

## remove-unused-parameters.py
#### Purpose
This is for `-Wunused-parameter`, when you give a name to a function parameter in the function's definition, but then don't use the variable in the function. This script will remove the _name_ (not the type) of the parameter in the function definition.
#### Comments
The whitepsace that previously surrounded any parameter name removed will remain; e.g. in
`int foo(int x, int y) { ... }` → `int foo(int , int y) { ... }` if the parameter `x` is removed. 
Note the space remaining after the first `int`. I haven't yet thought of a safe way to remove that.

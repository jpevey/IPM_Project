function [f, g] =  cyl_1d_twenty_var(variables)
%%% This function takes 20 beta values between 0 - 1, and runs a tsunami
%%% case. When this case is complete the keff (f) and the
%%% derivatives [g] are extracted

%%% Making sure the py_funct file is in the system path so that matlab can
%%% see it. Note: I also run this file with the python file in the same
%%% directory, not sure if both are necessary, but it works so...
pyversion
python_functions = fileparts(which('py_funct.py'))
if count(py.sys.path, python_functions) == 0
    insert(py.sys.path,int32(0), python_functions);
end

py.importlib.import_module('py_funct')

%%% Builing the array to pass to python 
python_array = [variables(1), variables(2), variables(3), variables(4), variables(5), ...
                variables(6), variables(7), variables(8), variables(9), variables(10), ...
                variables(11), variables(12), variables(13), variables(14), variables(15), ...
                variables(16), variables(17), variables(18), variables(19), variables(20)];

%%% This line I call the function evaluate_1d_cyl in the py_funct.py file 
%%% and passes it the list of beta variables.
output = py.py_funct.evaluate_1d_cyl(python_array);

%%% This turns the outuput returned by python into what matlab expects, a
%%% single value and a list of dk/dbeta values.
f = output{1};
g = [ output{2}{1} output{2}{2} output{2}{3} output{2}{4} output{2}{5}...
      output{2}{6} output{2}{7} output{2}{8} output{2}{9} output{2}{10}...
      output{2}{11} output{2}{12} output{2}{13} output{2}{14} output{2}{15}...
      output{2}{16} output{2}{17} output{2}{18} output{2}{19} output{2}{20}];



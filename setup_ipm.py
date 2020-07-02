### Sets up matlab files for IPM calculation
import os

constraint_string = """function [c, ceq, DC, DCeq] = cyl_1d_cyl_constraint(variables)
%%% This function calls a python function which:
% original constraint: c = sum(1 - variables) -  10;

ceq = 0;
c = -1 * sum(variables) - 9.21044037697652000E+01;
beta_values = 10 .^ variables
DC =  - 1 ./ beta_values;
DC = reshape(DC,[20,1]);
DCeq = zeros(20, 1);"""

ipm_file_string = """function [x,fval,exitflag,output,lambda,grad,hessian] = cyl_1d_interior_point_algo()
pyversion('/usr/bin/python3')
%%% To get more from the output, copy the entire 1st line (minus function)
x0 = ones(1, 20) * log10(0.5);
lb = ones(1, 20) * log(1e-4);
ub = ones(1, 20) * log(1 - 1e-4);
%OptimalityTolerance_Data = 0.00100
%StepTolerance_Data = 0.01

% Adding working directory to path
addpath %%%py_function_path%%%

%% This is an auto generated MATLAB file from Optimization Tool.

%% Start with the default options
options = optimoptions('fmincon');
%% Modify options setting
options = optimoptions(options,'Display', 'off');
%options = optimoptions(options,'OptimalityTolerance', OptimalityTolerance_Data);
%options = optimoptions(options,'FunctionTolerance', OptimalityTolerance_Data);
%options = optimoptions(options,'StepTolerance', StepTolerance_Data);
options = optimoptions(options,'SpecifyConstraintGradient', true);
options = optimoptions(options,'SpecifyObjectiveGradient', true);
[x,fval,exitflag,output,lambda,grad,hessian] = ...
fmincon(@cyl_1d_twenty_var,x0,[],[],[],[],lb,ub,@cyl_1d_cyl_constraint,options);
"""

ipm_function = """function [f, g] =  cyl_1d_twenty_var(variables)
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
"""

ipm_sh_string = """#!/bin/bash
#!/usr/bin/python3
#PBS -V
#PBS -q corei7
#PBS -l nodes=1:ppn=1
#PBS -l pmem=3500mb

#### cd working directory (where you submitted your job)
cd ${PBS_O_WORKDIR}

#### load module
module load matlab/R2019a

#### Executable Line
matlab -nodisplay -nodesktop -nojvm -nosplash -r 'run cyl_1d_interior_point_algo.m; exit'"""

def main():
    print("Setting up IPM matlab functions!")

    print("Creating matlab functions...")
    print("...   IPM main script")
    file_ = open("cyl_1d_interior_point_algo.m", 'w')
    ipm_file_string_ = ipm_file_string.replace("%%%py_function_path%%%", os.getcwd())
    file_.write(ipm_file_string_)
    file_.close()

    print("...   IPM function")
    file_ = open("cyl_1d_cyl_constraint.m", 'w')
    file_.write(constraint_string)
    file_.close()

    print("...   IPM constraint function")
    file_ = open("cyl_1d_twenty_var.m", 'w')
    file_.write(ipm_function)
    file_.close()

    print("...   Building IPM sh")
    file_ = open("run_matlab.sh", 'w')
    file_.write(ipm_sh_string)
    file_.close()

if __name__ == "__main__":
    main()
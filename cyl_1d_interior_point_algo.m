function [x,fval,exitflag,output,lambda,grad,hessian] = cyl_1d_interior_point_algo()
pyversion('/usr/bin/python3')
%%% To get more from the output, copy the entire 1st line (minus function)
x0 = ones(1, 20) * log10(0.5);
lb = ones(1, 20) * log10(1e-4);
ub = ones(1, 20) * log10(1 - 1e-4);
%OptimalityTolerance_Data = 0.00100
%StepTolerance_Data = 0.01

% Adding working directory to path
addpath /home/jpevey/Summer_2020/PY_Functions

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

function [c, ceq, DC, DCeq] = cyl_1d_cyl_constraint(variables)
%%% This function calls a python function which:
% original constraint: c = sum(1 - variables) -  10;

ceq = 0;
c = -1 * sum(variables) - 9.21044037697652000E+01;
beta_values = 10 .^ variables
DC =  - 1 ./ beta_values;
DC = reshape(DC,[20,1]);
DCeq = zeros(20, 1);

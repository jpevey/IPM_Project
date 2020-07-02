function [c, ceq, DC, DCeq] = cyl_1d_cyl_constraint(variables)
%%% This function calls a python function which:
% original constraint: c = sum(1 - variables) -  10;

ceq = 0;
c = -1 * sum(log10(variables)) - 4.00004343161981E+01;
DC =  - 1./ variables;
DCeq = zeros(20, 1);

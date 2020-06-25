function [c, ceq, DC, DCeq] = cyl_1d_cyl_constraint(variables)
%%% This function calls a python function which:
c = sum(1 - variables) -  10;
% sum(fuel) <= 10
% sum(1 - var) <= 10
% sum(1 - var) -  10 <= 0
ceq = 0;

DC = ones(20, 1) * -1;
DCeq = zeros(20, 1);

%%% Setting constraint to 0 for debugging
%c = 0;
%ceq = 0;

%DC = zeros(20, 1);
%DCeq = zeros(20, 1);
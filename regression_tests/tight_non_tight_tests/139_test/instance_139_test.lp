
%%%%%%%%%%%%%
% Instance:
e(1..4,1..4).
{c(1);c(2)}.
% Disunctive non-ground cycle:
a(X)|b(X) :- c(X), not d.
d :- b(X).
c(X) :- a(X).
c_ :- c(_).
{f(X,Y)} :- c_, e(X,Y), X < Y.



e(1..4,1..4).
{c}.
a|b :- c, not d.
d :- b.
c :- a.

{f(X,Y)} :- c, e(X,Y), X < Y.

#program rules.
:- f(X1,X2), f(X1,X3), f(X2,X3).

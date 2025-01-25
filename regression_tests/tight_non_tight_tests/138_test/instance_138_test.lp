
e(1..4,1..4).

{c}.
a|b :- c, not d.
d :- b.
c :- a.

{f(X,Y)} :- c, e(X,Y), X < Y.



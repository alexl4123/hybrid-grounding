
e(1,1).
e(1,2).
e(3,5).
e(2,5).


{f(X,Y)} :- e(X,Y).

#program rules.

a(X,Y) :- f(X,X1), f(Y,Y1), f(X1,Y1).

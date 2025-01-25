e(1,1).
e(1,2).
e(3,5).
e(2,5).


{f(X,Y)} :- e(X,Y).

#program rules.
a(X,Y) :- f(X,X1), f(Y,Y1), X1 = Y1.

b(X,Y) :- a(X,Y).

c(X,Y) :- b(X1,X), a(Y,Y1), f(X1,Y1).


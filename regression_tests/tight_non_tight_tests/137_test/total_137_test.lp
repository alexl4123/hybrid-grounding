
e(1,1).
e(1,2).
e(3,5).
e(2,5).
e(5,4).
e(10,6).
e(4,4).

{f(X,Y)} :- e(X,Y).
#program rules.

a(X1,X2) :- f(X1,X2), X1=X2.
b(X1,X2) :- f(X1,X2), X1!=X2.
c(X1,X2) :- f(X1,X2), X1<X2.
d(X1,X2) :- f(X1,X2), X1>X2.
% e & f already taken
g(X1,X2) :- f(X1,X2), X1<=X2.
h(X1,X2) :- f(X1,X2), X1>=X2.


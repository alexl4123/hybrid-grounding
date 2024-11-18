
a(X1,X2) :- f(X1,X2), X1=X2.
b(X1,X2) :- f(X1,X2), X1!=X2.
c(X1,X2) :- f(X1,X2), X1<X2.
d(X1,X2) :- f(X1,X2), X1>X2.
% e & f already taken
g(X1,X2) :- f(X1,X2), X1<=X2.
h(X1,X2) :- f(X1,X2), X1>=X2.


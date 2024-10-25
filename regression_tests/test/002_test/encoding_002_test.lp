q(X) :- p(X), p(Y), X = Y.

a(1) :- not a(2).
a(2) :- not a(1).


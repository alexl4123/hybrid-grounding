p(1).
p(2).
p(3).
q(2).

a(6).

b(Z) :- #count{X : p(X); X : q(X)} = Z.
%b(Z) :- #count{X : p(X); X : q(X); X,Y : p(X),q(Y)} = Z.

%:- a(Z), #count{X : p(X); X : q(X); X,Y : p(X),q(Y)} = Z.

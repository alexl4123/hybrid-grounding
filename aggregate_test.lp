
p(1).
p(2).
p(5).
p(8).
p(10).
p(12).
p(14).
p(20).
p(21).
p(22).
p(23).
q(15).

#program rules.
:- 14 <= #max{Y : q(Y); X1 : p(X1), p(X2), p(X3), p(X4), X1 < X2, X1 < X3, X1 < X4, X2 < X3, X2 < X4,  X3 < X4, X4 - X1 < 7}.

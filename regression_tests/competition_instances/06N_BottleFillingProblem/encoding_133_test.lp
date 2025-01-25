filled(X,Y) :- bottle(B,X,Y), not unfilled(X,Y).
unfilled(X,Y) :- bottle(B,X,Y), not filled(X,Y).

:- xvalue(Y,V), not #count{ X : filled(X,Y) } = V.
:- yvalue(X,V), not #count{ Y : filled(X,Y) } = V.

:- bottle(B,X1,Y1), bottle(B,X2,Y2), ysucc(Y1,Y2), filled(X1,Y1), unfilled(X2,Y2).
:- bottle(B,X1,Y), bottle(B,X2,Y), filled(X1,Y), unfilled(X2,Y), X1 != X2.

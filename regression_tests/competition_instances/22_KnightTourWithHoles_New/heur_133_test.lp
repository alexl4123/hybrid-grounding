size(6).
%forbidden(3,3).
%forbidden(2,2).
%forbidden(2,3).
%forbidden(3,5).
number(X)   :- size(X).
number(X-1) :- number(X), 1 < X.
cell(X,Y)   :- number(X), number(Y), not forbidden(X,Y).

hasx(X) :- cell(X,Y).
domx(X) :- hasx(X), hasx(XX), XX < X.
minx(X) :- hasx(X), not domx(X).

hasy(Y) :- cell(X,Y), hasx(X).
domy(Y) :- hasy(Y), hasy(YY), YY < Y.
miny(Y) :- hasy(Y), not domy(Y).

delta(1,2). delta(1,-2). delta(2,1). delta(2,-1).

conn(X,Y,X+DX,Y+DY) :- cell(X,Y), delta(DX,DY), cell(X+DX,Y+DY).

valid(X,Y,XX,YY) :- conn(X,Y,XX,YY).
valid(XX,YY,X,Y) :- conn(X,Y,XX,YY).

other(X,Y,XX,YY) :- valid(X,Y,XX,YY), move(A,B,XX,YY), X != A.
other(X,Y,XX,YY) :- valid(X,Y,XX,YY), move(X,B,XX,YY), Y != B.
other(X,Y,XX,YY) :- valid(X,Y,XX,YY), move(X,Y,A,BB), XX != A.
other(X,Y,XX,YY) :- valid(X,Y,XX,YY), move(X,Y,XX,B), YY != B.

move(X,Y,XX,YY) :- valid(X,Y,XX,YY), not other(X,Y,XX,YY).

from(X,Y) :- move(X,Y,XX,YY).
:- cell(X,Y), not from(X,Y).

reach(X,Y)   :- minx(X), miny(Y).
reach(XX,YY) :- move(X,Y,XX,YY), reach(X,Y).

:- cell(X,Y), not reach(X,Y).

% possible coordinates
value(0).
value(V) :- value(V1), V=V1+1, size(N), V1<=N.

step(-1).
step(1).
diff(X,0) :- step(X).
diff(0,Y) :- step(Y).
diff(X,Y) :- step(X), step(Y).

% a cell may live, except for the ones at the border
{ lives(X,Y) } <= 1 :- value(X), value(Y), X>0, Y>0, size(N), X<=N, Y<=N.

% cells with exactly 3 neighbours must live
%:- #sum { 1,DX,DY : lives(X+DX,Y+DY), diff(DX,DY) } = 3, not lives(X,Y), value(X), value(Y).
% Updated March 25th 2013
:- #count { DX,DY : lives(XDX,YDY), diff(DX,DY), XDX=X+DX, YDY=Y+DY } = 3, not lives(X,Y), value(X), value(Y).


% living cells must have 2-3 living neighbours
%:- lives(X,Y), not 2 <= #sum { 1,DX,DY : lives(X+DX,Y+DY), diff(DX,DY) } <= 3, value(X), value(Y).
% Updated March 25th 2013
:- lives(X,Y), not 2 <= #count { DX,DY : lives(XDX,YDY), diff(DX,DY), XDX=X+DX, YDY=Y+DY } <= 3, value(X), value(Y).


% connectedness
reached(XX,YY) :- XX = #min { X : lives(X,Y), value(X), value(Y) }, YY = #min { Y1 : lives(XX,Y1), value(Y1) }.
reached(XX,YY) :- reached(X,Y), value(X), value(Y), diff(DX,DY), XX=X+DX, YY=Y+DY, lives(XX,YY).
:- lives(X,Y), not reached(X,Y), value(X), value(Y).

% maximise living cells
%#maximise { 1 : lives(X,Y), value(X), value(Y) }.
:~ value(X),value(Y), not lives(X,Y). [1,X,Y]

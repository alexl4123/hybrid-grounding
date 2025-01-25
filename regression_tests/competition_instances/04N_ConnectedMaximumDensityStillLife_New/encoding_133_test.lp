% possible coordinates
value(0).
value(V+1) :- value(V), size(N), V <= N.

step(-1).
step(1).
diff(X,0) :- step(X).
diff(0,Y) :- step(Y).
diff(X,Y) :- step(X), step(Y).

cell(X,Y) :- value(X), value(Y), size(N), 0 < X, 0 < Y, X <= N, Y <= N.
near(X,Y,X+DX,Y+DY) :- value(X), value(Y), diff(DX,DY), cell(X+DX,Y+DY).

% a cell may live
{ lives(X,Y) } :- cell(X,Y).

active(X,Y,X,Y)   :- lives(X,Y).
active(X,Y,XX,YY) :- near(X,Y,XX,YY), lives(XX,YY).

upper(X,Y) :- cell(X,Y), 4 <= #count{ XX,YY : active(X,Y,XX,YY), near(X,Y,XX,YY) }.
lower(X,Y) :- value(X), value(Y), 3 <= #count{ XX,YY : active(X,Y,XX,YY) }.

% living cells must have at most 3 living neighbours
:- lives(X,Y), upper(X,Y).

% living cells must have at least 2 living neighbours
:- lives(X,Y), not lower(X,Y).

% cells with exactly 3 neighbours must live
:- lower(X,Y), not upper(X,Y), not lives(X,Y).

% connectedness
connect(X,Y,XX,YY) :- near(X,Y,XX,YY), lives(X,Y).
connect(X,Y,XX,YY) :- near(X,Y,XX,YY), cell(X,Y), not lives(XX,YY).

initial(1,1)   :- cell(1,1).
initial(X+1,Y) :- initial(X,Y), cell(X+1,Y), not lives(X,Y).
initial(1,Y+1) :- initial(X,Y), size(X), not size(Y), not lives(X,Y).

reached(X,Y)   :- initial(X,Y).
reached(XX,YY) :- reached(X,Y), connect(X,Y,XX,YY).
:- cell(X,Y), not reached(X,Y).

% maximise living cells
:~ cell(X,Y), not lives(X,Y). [1,X,Y]

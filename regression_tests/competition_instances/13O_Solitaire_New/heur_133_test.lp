time(1).
time(2).
time(3).
full(3,1).
full(4,1).
full(5,1).
full(3,2).
full(4,2).
full(5,2).
full(1,3).
full(2,3).
full(3,3).
full(4,3).
full(5,3).
full(6,3).
full(7,3).
full(1,4).
full(2,4).
full(3,4).
empty(4,4).
full(5,4).
full(6,4).
full(7,4).
full(1,5).
full(2,5).
full(3,5).
full(4,5).
full(5,5).
full(6,5).
full(7,5).
full(3,6).
full(4,6).
full(5,6).
full(3,7).
full(4,7).
full(5,7).


% Get locations
location(X,Y) :- full(X,Y).
location(X,Y) :- empty(X,Y).

% Map directions to coordinate changes
delta(up,    0,-1).
delta(down,  0, 1).
delta(left, -1, 0).
delta(right, 1, 0).

% Precalculate potential moves
poss(D,X,Y) :- delta(D,DX,DY), location(X,Y), location(XX,YY), location(XX+DX,YY+DY), XX = X+DX, YY = Y+DY.

% Cardinalities of filled grid cells
limit(N+1) :- time(1), #count{ X,Y : full(X,Y) } = N.

:- limit(N), time(T), K=N-T, not #count{ X,Y : filled(T,X,Y) } = K.

% At each time step choose a move
1 <= { move(T,D,X,Y) : poss(D,X,Y) } <= 1 :- time(T).

del(T,X,Y)         :- move(T,D,X,Y).
del(T,X+DX,Y+DY)   :- move(T,D,X,Y), delta(D,DX,DY).
add(T,X+DDX,Y+DDY) :- move(T,D,X,Y), delta(D,DX,DY), DDX = 2*DX, DDY = 2*DY.

:- del(T,X,Y), not filled(T,X,Y).
:- add(T,X,Y), filled(T,X,Y).

% Represent states by filled grid cells
filled(1,X,Y)   :- full(X,Y), time(1).
filled(T+1,X,Y) :- add(T,X,Y), time(T+1).
filled(T+1,X,Y) :- filled(T,X,Y), time(T+1), not del(T,X,Y).

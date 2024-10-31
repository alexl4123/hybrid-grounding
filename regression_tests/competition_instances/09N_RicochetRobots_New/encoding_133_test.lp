amo(west, -1).
amo(east,  1).
amo(north,-1).
amo(south, 1).

dl(west, -1).
dl(north,-1).
dl(east,  1).
dl(south, 1).

dir(west,  1).
dir(east,  1).
dir(north,-1).
dir(south,-1).

robot(R) :- pos(R,_,_).

pos2(R, 1,I,0) :- pos(R,I,_).
pos2(R,-1,J,0) :- pos(R,_,J).

barrier(I+1,J,west ) :- barrier(I,J,east ), dim(I), dim(J), dim(I+1).
barrier(I,J+1,north) :- barrier(I,J,south), dim(I), dim(J), dim(J+1).
barrier(I-1,J,east ) :- barrier(I,J,west ), dim(I), dim(J), dim(I-1).
barrier(I,J-1,south) :- barrier(I,J,north), dim(I), dim(J), dim(I-1).

conn(D,I,J) :- dir(D,-1), amo(D,DJ), not barrier(I,J,D), dim(I), dim(J), dim(J+DJ).
conn(D,J,I) :- dir(D, 1), amo(D,DI), not barrier(I,J,D), dim(I), dim(J), dim(I+DI).

step(1)   :- length(L), 0 < L.
step(X+1) :- step(X), length(L), X < L.

1 <= { move(R,D,O,T) : robot(R), dir(D,O) } <= 1 :- step(T).

axis(R,O,T) :- move(R,_,O,T).
go(R,D,T)   :- move(R,D,_,T).

sameLine(R,D,O,RR,T)  :- move(R,D,O,T), pos2(R,-O,L,T-1), pos2(RR,-O,L,T-1), R != RR.
blocked(R,D,O,I+DI,T) :- move(R,D,O,T), pos2(R,-O,L,T-1), not conn(D,L,I), dl(D,DI), dim(I), dim(I+DI).
blocked(R,D,O,L,T)    :- sameLine(R,D,O,RR,T), pos2(RR,O,L,T-1).

reachable(R,D,O,I,   T) :- move(R,D,O,T), pos2(R,O,I,T-1).
reachable(R,D,O,I+DI,T) :- reachable(R,D,O,I,T), not blocked(R,D,O,I+DI,T), dl(D,DI), dim(I+DI).

:- move(R,D,O,T), pos2(R,O,I,T-1), blocked(R,D,O,I+DI,T), dl(D,DI).
:- axis(R,O,T), axis(R,O,T-1).

pos2(R,O,I,T) :- reachable(R,D,O,I,T), not reachable(R,D,O,I+DI,T), dl(D,DI).
pos2(R,O,I,T) :- pos2(R,O,I,T-1), not axis(R,O,T), step(T).

:- robot(R), step(T), not #count{ I : pos2(R, 1,I,T), dim(I) } = 1.
:- robot(R), step(T), not #count{ I : pos2(R,-1,I,T), dim(I) } = 1.

:- target(R,I,_), not pos2(R, 1,I,L), length(L).
:- target(R,_,J), not pos2(R,-1,J,L), length(L).

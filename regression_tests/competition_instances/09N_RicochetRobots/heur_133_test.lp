barrier(1,2,south).
barrier(3,2,south).
barrier(2,3,north).
dim(1).
dim(2).
dim(3).
length(3).
pos(blue,1,3).
pos(green,3,1).
pos(red,1,1).
pos(yellow,3,3).
target(red,2,2).

%#const row =  1.
%#const col = -1.

dir3(west, -1, 0).
dir3(east,  1, 0).
dir3(north, 0,-1).
dir3(south, 0, 1).

dl(west, -1).
dl(north,-1).
dl(east,  1).
dl(south, 1).

dir2(west, 1).   %dir(west, row).
dir2(east, 1).   %dir(east, row).
dir2(north, -1). %dir(north,col).
dir2(south, -1). %dir(south,col).

dir1(D) :- dir2(D,_).

robot(R) :- pos(R,_,_).

pos2(R,1,I,0) :- pos(R,I,_).  %pos(R,row,I,0) :- pos(R,I,_).
pos2(R,-1,J,0) :- pos(R,_,J). %pos(R,col,J,0) :- pos(R,_,J).

barrier(I+1,J,west ) :- barrier(I,J,east ), dim(I), dim(J), dim(I+1).
barrier(I,J+1,north) :- barrier(I,J,south), dim(I), dim(J), dim(J+1).
barrier(I-1,J,east ) :- barrier(I,J,west ), dim(I), dim(J), dim(I-1).
barrier(I,J-1,south) :- barrier(I,J,north), dim(I), dim(J), dim(I-1).

conn(D,I,J) :- dir2(D,-1), dir3(D,_,DJ), not barrier(I,J,D), dim(I), dim(J), dim(J+DJ). %conn(D,I,J) :- dir2(D,col), dir3(D,_,DJ), not barrier(I,J,D), dim(I), dim(J), dim(J+DJ).
conn(D,J,I) :- dir2(D,1), dir3(D,DI,_), not barrier(I,J,D), dim(I), dim(J), dim(I+DI).  %conn(D,J,I) :- dir2(D,row), dir3(D,DI,_), not barrier(I,J,D), dim(I), dim(J), dim(I+DI).

%step(1..X) :- length(X).
step(1).
step(X+1) :- step(X), length(L), X < L. 

1 <= { selectRobot(R,T) : robot(R) } <= 1 :- step(T).
1 <= { selectDir(D,O,T) : dir2(D,O) } <= 1 :- step(T).

go(R,D,O,T) :- selectRobot(R,T), selectDir(D,O,T).
go_(R,O,T)   :- go(R,_,O,T).
go3(R,D,T) :- go(R,D,_,T).

sameLine(R,D,O,RR,T)  :- go(R,D,O,T), pos2(R,-O,L,T-1), pos2(RR,-O,L,T-1), R != RR.
blocked(R,D,O,I+DI,T) :- go(R,D,O,T), pos2(R,-O,L,T-1), not conn(D,L,I), dl(D,DI), dim(I), dim(I+DI).
blocked(R,D,O,L,T)    :- sameLine(R,D,O,RR,T), pos2(RR,O,L,T-1).

reachable(R,D,O,I,   T) :- go(R,D,O,T), pos2(R,O,I,T-1).
reachable(R,D,O,I+DI,T) :- reachable(R,D,O,I,T), not blocked(R,D,O,I+DI,T), dl(D,DI), dim(I+DI).

:- go(R,D,O,T), pos2(R,O,I,T-1), blocked(R,D,O,I+DI,T), dl(D,DI).
:- go(R,D,O,T), go(R,DD,O,T-1).

pos2(R,O,I,T) :- reachable(R,D,O,I,T), not reachable(R,D,O,I+DI,T), dl(D,DI).
pos2(R,O,I,T) :- pos2(R,O,I,T-1), not go_(R,O,T), step(T).

selectDir2(O,T) :- selectDir(D,O,T).

:- target(R,I,_), not pos2(R,1,I,X), length(X).  %:- target(R,I,_), not pos2(R,row,I,X), length(X).
:- target(R,_,J), not pos2(R,-1,J,X), length(X). %:- target(R,_,J), not pos2(R,col,J,X), length(X).

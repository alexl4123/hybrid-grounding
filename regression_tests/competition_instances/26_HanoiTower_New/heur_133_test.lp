

steps(10).
time(0).
time(1).
time(2).
time(3).
time(4).
time(5).
time(6).
time(7).
time(8).
time(9).
time(10).
disk(1).
disk(2).
disk(3).
disk(4).
on0(1,2).
on0(2,3).
on0(3,4).
ongoal(4,3).
ongoal(3,2).
ongoal(2,1).

% The meaning of the time predicate is self-evident. As for the disk
% predicate, there are k disks 1,2,...,k. Disks 1, 2, 3, 4 denote pegs.
% Disks 5, ... are "movable". The larger the number of the disk,
% the "smaller" it is.
%
% The program uses additional predicates:
% on(T,N,M), which is true iff at time T, disk M is on disk N
% move(t,N), which is true iff at time T, it is disk N that will be
% moved
% where(T,N), which is true iff at time T, the disk to be moved is moved
% on top of the disk N.
% goal, which is true iff the goal state is reached at time t
% steps(T), which is the number of time steps T, required to reach the goal (provided part of Input data)

peg(1). peg(2). peg(3). peg(4).
disc(D) :- disk(D), not peg(D).

at(D,P,T) :- disc(D), peg(P), time(T), not ta(D,P,T).
ta(D,P,T) :- disc(D), peg(P), time(T), at(D,PP,T), peg(PP), P != PP.

given(D,DD,0) :- on0(D,DD).
given(D,DD,T) :- ongoal(D,DD), steps(T).

:- given(D,P,T),  disc(D), peg(P),   not at(D,P,T).
:- given(D,P,T),  disc(D), peg(P),   disc(DD), DD < D, at(DD,P,T).
:- given(D,DD,T), disc(D), disc(DD), at(DD,P,T), not at(D,P,T).
:- given(D,DD,T), disc(D), disc(DD), disc(DDD), DD < DDD, DDD < D, at(DD,P,T), at(DDD,P,T).

move(D,T) :- at(D,P,T), not steps(T), not at(D,P,T+1).

:- move(D,T), move(D,T+1).

done(D-1,T) :- move(D,T), 5 < D.
done(D-1,T) :- done(D,T), 5 < D.

:- move(D,T), done(D,T).

moved(T) :- move(D,T).

:- moved(T), 0 < T, not moved(T-1).

blocked(P,D-1,T) :- at(D,P,T), not steps(T).
blocked(P,D-1,T) :- blocked(P,D,T), disc(D).

:- move(D,T), at(D,P,T),   blocked(P,D,T).
:- move(D,T), at(D,P,T+1), blocked(P,D-1,T).

top(P,P,T) :- peg(P), time(T), not steps(T), not blocked(P,4,T).
top(P,D,T) :- peg(P), time(T), not steps(T), blocked(P,DD,T), D = DD+1, not blocked(P,D,T).

put(T,DD,D) :- move(D,T), at(D,P,T+1), top(P,DD,T), DD < D.

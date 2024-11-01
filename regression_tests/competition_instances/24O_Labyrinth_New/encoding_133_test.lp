dir(e). dir(w). dir(n). dir(s).
inverse(e,w). inverse(w,e).
inverse(n,s). inverse(s,n).

row(X) :- field(X,Y).
col(Y) :- field(X,Y).

num_rows(X) :- row(X), not row(XX), XX = X+1.
num_cols(Y) :- col(Y), not col(YY), YY = Y+1.

number(X) :- col(X).
number(Y) :- row(Y).

goal(X,Y,0)   :- goal_on(X,Y).
reach(X,Y,0)  :- init_on(X,Y).
conn(X,Y,D,0) :- connect(X,Y,D).

step(S) :- max_steps(S),     0 < S.
step(T) :- step(S), T = S-1, 1 < S.

%%  Direct neighbors

dneighbor(n,X,Y,XX,Y) :- field(X,Y), field(XX,Y), XX = X+1.
dneighbor(s,X,Y,XX,Y) :- field(X,Y), field(XX,Y), XX = X-1.
dneighbor(e,X,Y,X,YY) :- field(X,Y), field(X,YY), YY = Y+1.
dneighbor(w,X,Y,X,YY) :- field(X,Y), field(X,YY), YY = Y-1.

%%  All neighboring fields

neighbor(D,X,Y,XX,YY) :- dneighbor(D,X,Y,XX,YY).
neighbor(n,X,Y, 1, Y) :- field(X,Y), num_rows(X).
neighbor(s,1,Y, X, Y) :- field(X,Y), num_rows(X).
neighbor(e,X,Y, X, 1) :- field(X,Y), num_cols(Y).
neighbor(w,X,1, X, Y) :- field(X,Y), num_cols(Y).

%%  Select a row or column to push

neg_goal(T) :- goal(X,Y,T), not reach(X,Y,T).

rrpush(T)   :- step(T), not ccpush(T).
ccpush(T)   :- step(T), neg_goal(S), S = T-1, not rrpush(T).

opush(N,T)  :- npush(M,T), number(N), M != N.
npush(N,T)  :- step(T), number(N), not opush(N,T).

:- step(T), num_rows(N), opush(N,T), S = T-1, not neg_goal(S).

rpush(X,T)  :- rrpush(T), npush(X,T).
cpush(Y,T)  :- ccpush(T), npush(Y,T).

:- rpush(X,T), not row(X).
:- cpush(Y,T), not col(Y).

dpush(0,T) :- step(T), not dpush(1,T).
dpush(1,T) :- step(T), neg_goal(S), S = T-1, not dpush(0,T).

push(X,e,T) :- rpush(X,T), dpush(0,T).
push(X,w,T) :- rpush(X,T), dpush(1,T).
push(Y,n,T) :- cpush(Y,T), dpush(0,T).
push(Y,s,T) :- cpush(Y,T), dpush(1,T).

%%  Determine new position of a (pushed) field

shift(XX,YY,X,Y,T) :- neighbor(e,XX,YY,X,Y), push(XX,e,T), step(T).
shift(XX,YY,X,Y,T) :- neighbor(w,XX,YY,X,Y), push(XX,w,T), step(T).
shift(XX,YY,X,Y,T) :- neighbor(n,XX,YY,X,Y), push(YY,n,T), step(T).
shift(XX,YY,X,Y,T) :- neighbor(s,XX,YY,X,Y), push(YY,s,T), step(T).
shift( X, Y,X,Y,T) :- field(X,Y), not rpush(X,T), not cpush(Y,T), step(T).

%%  Move connections around

conn(X,Y,D,T) :- conn(XX,YY,D,S), S = T-1, dir(D), shift(XX,YY,X,Y,T), step(T).

%%  Location of goal after pushing

goal(X,Y,T) :- goal(XX,YY,S), S = T-1, shift(XX,YY,X,Y,T), step(T).

%%  Locations reachable from new position

reach(X,Y,T) :- reach(XX,YY,S), S = T-1, shift(XX,YY,X,Y,T), step(T).
reach(X,Y,T) :- reach(XX,YY,T), dneighbor(D,XX,YY,X,Y), conn(XX,YY,D,T), conn(X,Y,E,T), inverse(D,E), step(T).

%%  Goal must be reached

:- neg_goal(S), max_steps(S).

%% Project output

% #hide.
% #show push(Z,D,T).

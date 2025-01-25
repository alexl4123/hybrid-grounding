% nodes and values
node(X) :- edge(X,Y).
node(Y) :- edge(X,Y).

%num_edges(N) :- N = #sum { 1,X,Y : edge(X,Y) }.
% Updated March 25th, 2013
num_edges(N) :- N = #count { X,Y : edge(X,Y) }.
num(0).
num(N) :- num(N1), N=N1+1, num_edges(E), N<=E.

% assignment to nodes
{ value(X,N) : num(N) } = 1 :- node(X).

% assignment to edges
{ edge_value(edge(X,Y),N) : num(N), N>0 } = 1 :- edge(X,Y).

% relates node values with edge values
:- not edge_value(edge(X,Y),M-N), edge(X,Y), value(X,M), value(Y,N), N < M.
:- not edge_value(edge(X,Y),N-M), edge(X,Y), value(X,M), value(Y,N), N > M.

% alldifferent values
:- value(X,N), value(Y,N), num(N), X<Y.
:- edge_value(X,N), edge_value(Y,N), num(N), X<Y.

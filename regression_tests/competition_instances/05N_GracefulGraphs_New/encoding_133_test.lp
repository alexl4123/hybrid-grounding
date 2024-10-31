% nodes and values
node(X) :- edge(X,Y).
node(Y) :- edge(X,Y).

symm(X,Y) :- edge(X,Y).
symm(Y,X) :- edge(X,Y).

pair(X,Y) :- node(X), node(Y), X < Y.
pair_(X)   :- pair(X,Y).
next(X,Y) :- pair_(X), Y = #min{ Z : pair(X,Z) }.

num_edges(N) :- N = #count{ X,Y : edge(X,Y) }.
num(0).
num(N+1) :- num(N), num_edges(E), N < E.

% assignment to nodes
1 <= { value(X,N) : num(N) } <= 1 :- node(X).

skip(Y,N) :- next(X,Y), value(X,N).
skip(Y,N) :- next(X,Y), skip(X,N).
:- value(Y,N), skip(Y,N).
% :- num(N), 2 <= #count{ X : value(X,N) }.

% assignment to edges
diff(X,N,1)   :- num(N), value(Y,N-1), symm(X,Y).
diff(X,N,D+1) :- num(N), diff(X,N-1,D).

edge_value(X,D) :- diff(X,N,D), value(X,N).

drop(Y,D) :- next(X,Y), edge_value(X,D).
drop(Y,D) :- next(X,Y), drop(X,D).
:- edge_value(Y,D), drop(Y,D).
% :- num(N), 2 <= #count{ X : edge_value(X,N) }.

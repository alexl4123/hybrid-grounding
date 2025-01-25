clique(X) :- node(X), not nonClique(X).
nonClique(X) :- node(X), not clique(X).

:- clique(X), clique(Y), X < Y, not edge(X,Y), not edge(Y,X).

:~ nonClique(X). [1,X]

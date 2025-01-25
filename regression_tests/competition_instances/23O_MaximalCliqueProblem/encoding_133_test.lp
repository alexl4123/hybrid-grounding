% Based on the 2009 ASP Competition encoding 
% submitted by the DLV team

% order edges in order to reduce checks
uedge(X,Y) :- edge(X,Y), X < Y.
uedge(Y,X) :- edge(X,Y), Y < X.

% guess the clique
clique(X) | nonClique(X) :- node(X).

% ensure property
:- clique(X), clique(Y), not uedge(X,Y), X < Y.

% maximize
:~ nonClique(X). [1,X]

edge(1,1). edge(2,2). edge(3,3). edge(4,4). edge(5,5). 
edge(1,2). edge(1,3). edge(1,4). edge(1,5).
edge(2,3). edge(2,4). edge(2,5). 
edge(3,4). edge(3,5). 
edge(4,5). 
edge(Y,X) :- edge(X,Y).
{f(X,Y)} :- edge(X,Y).

:- f(X1,X2), f(X1,X3), f(X2,X3), X1 < X2, X1 < X3, X2 < X3.


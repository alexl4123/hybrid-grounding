edge(1,1).
edge(2,2).
edge(3,3).
edge(4,4).
edge(5,5).
edge(6,6).
edge(7,7).
edge(8,8).
edge(9,9).
edge(1,2).
edge(1,3).
edge(1,4).
edge(1,5).
edge(1,6).
edge(1,7).
edge(1,8).
edge(1,9).
edge(2,3).
edge(2,4).
edge(2,5).
edge(2,6).
edge(2,7).
edge(2,8).
edge(2,9).
edge(3,4).
edge(3,5).
edge(3,6).
edge(3,7).
edge(3,8).
edge(3,9).
edge(4,5).
edge(4,6).
edge(4,7).
edge(4,8).
edge(4,9).
edge(5,6).
edge(5,7).
edge(5,8).
edge(5,9).
edge(6,7).
edge(6,8).
edge(6,9).
edge(7,8).
edge(7,9).
edge(8,9).

edge(Y,X):-edge(X,Y).
{f(X,Y)}:-edge(X,Y).
sat_0_0:-sat_0_0_X1(X1),sat_0_0_X2(X2),X1>=X2.
sat_0_0:-sat_0_0_X1(X1),sat_0_0_X3(X2),X1>=X2.
sat_0_0:-sat_0_0_X2(X1),sat_0_0_X3(X2),X1>=X2.
sat_0_0:-sat_0_0_X1(X1),sat_0_0_X2(X2),not f(X1,X2),X1<X2.
sat_0_0:-sat_0_0_X1(X1),sat_0_0_X3(X2),not f(X1,X2),X1<X2.
sat_0_0:-sat_0_0_X2(X1),sat_0_0_X3(X2),not f(X1,X2),X1<X2.
sat_0_0_X1(9):-sat_0.
sat_0_0_X1(7):-sat_0.
sat_0_0_X1(6):-sat_0.
sat_0_0_X1(4):-sat_0.
sat_0_0_X1(3):-sat_0.
sat_0_0_X1(5):-sat_0.
sat_0_0_X1(2):-sat_0.
sat_0_0_X1(1):-sat_0.
sat_0_0_X1(8):-sat_0.
sat_0_0_X1(9)|sat_0_0_X1(7)|sat_0_0_X1(6)|sat_0_0_X1(4)|sat_0_0_X1(3)|sat_0_0_X1(5)|sat_0_0_X1(2)|sat_0_0_X1(1)|sat_0_0_X1(8).
sat_0_0_X2(9):-sat_0.
sat_0_0_X2(7):-sat_0.
sat_0_0_X2(6):-sat_0.
sat_0_0_X2(4):-sat_0.
sat_0_0_X2(3):-sat_0.
sat_0_0_X2(5):-sat_0.
sat_0_0_X2(2):-sat_0.
sat_0_0_X2(1):-sat_0.
sat_0_0_X2(8):-sat_0.
sat_0_0_X2(9)|sat_0_0_X2(7)|sat_0_0_X2(6)|sat_0_0_X2(4)|sat_0_0_X2(3)|sat_0_0_X2(5)|sat_0_0_X2(2)|sat_0_0_X2(1)|sat_0_0_X2(8).
sat_0_0_X3(9):-sat_0.
sat_0_0_X3(7):-sat_0.
sat_0_0_X3(6):-sat_0.
sat_0_0_X3(4):-sat_0.
sat_0_0_X3(3):-sat_0.
sat_0_0_X3(5):-sat_0.
sat_0_0_X3(2):-sat_0.
sat_0_0_X3(1):-sat_0.
sat_0_0_X3(8):-sat_0.
sat_0_0_X3(9)|sat_0_0_X3(7)|sat_0_0_X3(6)|sat_0_0_X3(4)|sat_0_0_X3(3)|sat_0_0_X3(5)|sat_0_0_X3(2)|sat_0_0_X3(1)|sat_0_0_X3(8).
:- not sat_0.
sat_0:-sat_0_0.
#show edge/2.
#show f/2.
#show -edge/2.
#show -f/2.

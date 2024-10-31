controlled_by(1000,1054,964,504,921).
controlled_by(1000,638,988,735,686).
controlled_by(1001,1100,700,1176,770).
controlled_by(1001,1220,1353,279,790).

produced_by(p1000,1382,495,1415,1453).
produced_by(p1004,1009,89,1166,1055).
produced_by(p1010,1123,148,439,986).

strategic(X1) | strategic(X2) | strategic(X3) | strategic(X4) :- produced_by(X,X1,X2,X3,X4).
strategic(W) :- controlled_by(W,X1,X2,X3,X4), strategic(X1), strategic(X2), strategic(X3), strategic(X4).

strategic_pair(X,Y) :- strategic(X), strategic(Y).
non_strategic_pair(X,Y) :- company(X), company(Y), not strategic_pair(X,Y).

company(X1) :- produced_by(X,X1,X2,X3,X4).
company(X2) :- produced_by(X,X1,X2,X3,X4).
company(X3) :- produced_by(X,X1,X2,X3,X4).
company(X4) :- produced_by(X,X1,X2,X3,X4).
company(W) :- controlled_by(W,X1,X2,X3,X4).
company(X1) :- controlled_by(W,X1,X2,X3,X4).
company(X2) :- controlled_by(W,X1,X2,X3,X4).
company(X3) :- controlled_by(W,X1,X2,X3,X4).
company(X4) :- controlled_by(W,X1,X2,X3,X4).

:- not non_strategic_pair(1000,1001).

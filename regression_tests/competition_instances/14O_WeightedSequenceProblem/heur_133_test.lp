leafWeightCardinality(1,45,44).
leafWeightCardinality(2,21,3).
leafWeightCardinality(3,64,74).
leafWeightCardinality(4,29,91).
leafWeightCardinality(5,80,48).
leafWeightCardinality(6,91,8).
innerNode(1).
innerNode(2).
innerNode(3).
innerNode(4).
innerNode(5).
num(6).
max_total_weight(495).

color(red).
color(blue).
color(green).

leafCost(X,red,W)   :- leafWeightCardinality(X,W,C), 0 < W.
leafCost(X,blue,C)  :- leafWeightCardinality(X,W,C), 0 < C, C < W.
leafCost(X,green,D) :- leafWeightCardinality(X,W,C), D = W+C, 0 < D.

leafMin(X,W) :- leafWeightCardinality(X,W,C), W < C.
leafMin(X,C) :- leafWeightCardinality(X,W,C), C < W.

repeat(C,M/C)   :- max_total_weight(M), leafCost(X,L,C), L != green.
repeat(D-C,M/D) :- max_total_weight(M), leafCost(X,green,D), leafMin(X,C).
repeat(D,M/D)   :- max_total_weight(M), leafCost(X,green,D), leafWeightCardinality(X,C,C).

assign(C)  :- repeat(C,S).
maxim(C,R) :- assign(C), #max{ S : repeat(C,S) } = R.

assigned :- assign(C).
limit(R) :- assigned, #max{ S : maxim(C,S) } = R.

coloredPos(N-1) :- num(N), 1 < N.
coloredPos(P-1) :- coloredPos(P), 1 < P.

location(0) :- num(N), 0 < N.
location(P) :- coloredPos(P).

{ lt(X,P) } :- leafWeightCardinality(X,W,C), coloredPos(P).
:- lt(X,P-1), coloredPos(P), not lt(X,P).

leafPos(X,P-1) :- lt(X,P), not lt(X,P-1).
leafPos(X,N-1) :- leafWeightCardinality(X,W,C), num(N), not lt(X,N-1).

:- location(P), 2 <= #count{ X : leafPos(X,P) }.

{ posColor(P,green) } :- coloredPos(P).
posColor(P,blue)  :- coloredPos(P), leafPos(X,P), not posColor(P,green), leafWeightCardinality(X,W,C), C < W.
posColor(P,red)   :- coloredPos(P), leafPos(X,P), not posColor(P,green), leafWeightCardinality(X,W,C), W <= C.

iterate(0,1)     :- not posColor(1,green).
iterate(0,I+1)   :- not posColor(1,green), limit(I), iterate(1,I).
iterate(P-1,1)   :- coloredPos(P), not posColor(P,green), not limit(0).
iterate(P-1,I+1) :- coloredPos(P), not posColor(P,green), not limit(I), iterate(P,I).

cost(0,W,0)   :- leafPos(X,0), leafCost(X,red,W).
cost(P,C,0)   :- leafPos(X,P), coloredPos(P), leafMin(X,C), 0 < C.
cost(P,D-C,0) :- leafPos(X,P), coloredPos(P), leafMin(X,C), leafCost(X,green,D), posColor(P,green).
cost(P,C,0)   :- leafPos(X,P), coloredPos(P), leafWeightCardinality(X,C,C), 0 < C, not posColor(P,green).
cost(P,2*C,0) :- leafPos(X,P), coloredPos(P), leafWeightCardinality(X,C,C), 0 < C, posColor(P,green).
cost(P,C,I)   :- iterate(P,I), cost(P,C,I-1), not maxim(C,I-1).
cost(0,C,I)   :- iterate(0,I), cost(0,C,I-1), maxim(C,I-1).

scost(C,P,I) :- cost(P,C,I), P+I > 0.
:- max_total_weight(M), M < #sum{ C,P,I : scost(C,P,I) }. 

starting(X) :- leafPos(X,P), posColor(P,green), coloredPos(P+1), leafWeightCardinality(X-1,W,C).

started(X-1,P) :- starting(X), lt(X,P).
started(X-1,P) :- started(X,P), leafWeightCardinality(X-1,W,C).

:- started(X,P), leafPos(X,P), posColor(P,green).

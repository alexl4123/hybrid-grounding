%clingo 1 instance encoding


color(red).
color(blue).
color(green).



leafWeight(X,W)  :-leafWeightCardinality(X,W,C).

leafCard(X,C)  :-leafWeightCardinality(X,W,C).

leaf(X):-leafWeightCardinality(X,W,C).



%%
%% Sequence Definition
%%

coloredPos(1).
coloredPos(X+1):- coloredPos(X),  X < N-1, num(N).
%coloredPos(X):-  X=1..N-1, num(N).
location(0).
location(X+1) :- location(X), X < N-1, num(N).
%location(X):-X=0..N-1, num(N).

1 <= {leafPos(L,N) : location(N) } <= 1 :- leaf(L).
% No sharing locations
%:- leafPos(L1, N), leafPos(L2, N), location(N), L1 != L2.
1 <= { leafPos(L,N) : leaf(L) } <= 1 :- location(N).


%%
%% each node at colordPos has a unique color
%%
1 <= {posColor(P,C):color(C)} <= 1:-coloredPos(P).

% BEGIN Weight T  definition

%  if color of X is green
%    weight(X) = weight(right child of X) + cardinality(right child of X) 
%
nWeight(0,W):- leafWeightCardinality(L,W,C), leafPos(L,0).

nWeight(P,W):- W= W1+C, posColor(P,green),
			leafWeight(R,W1), leafCard(R,C),
            coloredPos(P), leafPos(R,P), leaf(R),  W<=M, max_total_weight(M).




%  if color of X is red
%     weight(X) = weight(right child of X) + weight(left child of X) 
nWeight(P,W):- W= W1+W2, posColor(P,red),
			leafWeight(R,W1),nWeight(P-1,W2),
			coloredPos(P), leafPos(R,P),
            leaf(R),  W<=M, max_total_weight(M).



%  if color(X) is blue
%     weight(X) = cardinality(right child of X) + weight(left child of X) 
nWeight(P,W):- W= W1+C,   posColor(P,blue),
			leafCard(R,C), nWeight(P-1,W1),
			coloredPos(P),leafPos(R,P),   
            leaf(R),  W<=M, max_total_weight(M).



%%
%% Weights related Tests
%%

%% 
%% definition of a total weight of a prime tree T'
tWeight(1,W):-nWeight(1,W), coloredPos(1),  W<=M, max_total_weight(M).
tWeight(N,W):-W=W1+W2, tWeight(N-1,W1), nWeight(N,W2),coloredPos(N),N>1,  W<=M, max_total_weight(M).



% END Weight T definition
% --------------------------------------------------------------
% --------------------------------------------------------------
% --------------------------------------------------------------
% exists Definition


exists:-tWeight(N-1,W), W<=M, max_total_weight(M),num(N).
:-not exists.



%#show posColor(N,C).
%#show leafWeightCardinality(X,W,C).
%#show max_total_weight(M).
%#show num(N).
%#show exists.

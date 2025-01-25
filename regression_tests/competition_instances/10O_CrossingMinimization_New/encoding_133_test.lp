pvalue(L,1)   :- width(L,T), 0 < T.
pvalue(L,X+1) :- pvalue(L,X), width(L,T), X < T.

{ gt(L,N,P) } :- in_layer(L,N), pvalue(L,P), not width(L,P).
:- pvalue(L,P), gt(L,N,P+1), not gt(L,N,P).

position(N,1) :- in_layer(L,N), width(L,T), 0 < T, not gt(L,N,1).
position(N,Q) :- gt(L,N,P), Q = P+1, not gt(L,N,Q).
:- pvalue(L,P), 2 <= #count{ N : in_layer(L,N), position(N,P) }.

edge_layer(L1,L2,N1,N2) :- edge(N1,N2), in_layer(L1,N1), in_layer(L2,N2), L1 < L2.
edge_layer(L1,L2,N1,N2) :- edge(N2,N1), in_layer(L1,N1), in_layer(L2,N2), L1 < L2.

edge_pair(N1,N2,N3,N4) :- edge_layer(L1,L2,N1,N2), edge_layer(L1,L2,N3,N4), N1 < N3, N2 != N4.
edge_paired(N2,N4)     :- edge_pair(N1,N2,N3,N4).

compare(N1,N3) :- edge_pair(N1,N2,N3,N4).
compare(N2,N4) :- edge_paired(N2,N4), N2 < N4.
compare(N4,N2) :- edge_paired(N2,N4), N4 < N2.

inorder(N1,N2) :- compare(N1,N2), gt(L,N2,P), not gt(L,N1,P).

crossing(N1,N2,N3,N4) :- edge_pair(N1,N2,N3,N4), not edge_pair(N1,N4,N3,N2), compare(N2,N4), inorder(N1,N3), not inorder(N2,N4).
crossing(N1,N2,N3,N4) :- edge_pair(N1,N2,N3,N4), not edge_pair(N1,N4,N3,N2), compare(N2,N4), inorder(N2,N4), not inorder(N1,N3).
crossing(N1,N4,N3,N2) :- edge_pair(N1,N4,N3,N2), not edge_pair(N1,N2,N3,N4), compare(N2,N4), inorder(N1,N3), inorder(N2,N4).
crossing(N1,N4,N3,N2) :- edge_pair(N1,N4,N3,N2), not edge_pair(N1,N2,N3,N4), compare(N2,N4), not inorder(N1,N3), not inorder(N2,N4).

:~ crossing(N1,N2,N3,N4). [1,N1,N2,N3,N4]

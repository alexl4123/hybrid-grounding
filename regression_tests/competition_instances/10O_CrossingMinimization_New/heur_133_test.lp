layers(3).
width(0,9).
in_layer(0,n1).
in_layer(0,n2).
in_layer(0,n3).
in_layer(0,n4).
in_layer(0,n5).
in_layer(0,n6).
in_layer(0,n7).
in_layer(0,n8).
in_layer(0,n9).
width(1,9).
in_layer(1,n10).
in_layer(1,n11).
in_layer(1,n12).
in_layer(1,n13).
in_layer(1,n14).
in_layer(1,n15).
in_layer(1,n16).
in_layer(1,n17).
in_layer(1,n18).
width(2,9).
in_layer(2,n19).
in_layer(2,n20).
edge(n2,n18).
edge(n8,n16).
edge(n14,n19).
edge(n7,n12).
edge(n6,n11).
edge(n1,n15).
edge(n2,n15).
edge(n7,n15).
edge(n6,n12).
edge(n3,n13).
edge(n2,n13).
edge(n5,n14).
edge(n1,n16).
edge(n4,n17).
edge(n4,n15).
edge(n2,n14).
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

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

%%guess
pvalue(L,0) :- width(L,_).
pvalue(L,X+1) :- pvalue(L,X), width(L,T), X < T.
position( Node, Pos ) | not_position( Node, Pos ) :- in_layer( Layer, Node ), width( Layer, T ), Pos = P + 1, 
                                                     pvalue(Layer,P), P < T.

%%check
%a node must be assigned at most at one position.
:- position( Node1, Pos1 ), position( Node1, Pos2 ), Pos1 < Pos2.

%two nodes of the same layer cannot be assigned at the same position.
:- in_layer( Layer1, Node1 ), in_layer( Layer1, Node2 ), position( Node1, Pos1 ), position( Node2, Pos1 ), Node1 != Node2.

%a node must be assigned at least at one position.  
node_assigned_at_position( Node ) :- position( Node, Pos ).
:- in_layer( Layer1, Node1 ), not node_assigned_at_position( Node1 ).


%%optimization
%Computing the edges from same layers.
edge_from_same_layers(Node1,Node2,Node3,Node4):- edge(Node1,Node2), edge(Node3,Node4), Node1 < Node3, Node2 != Node4, in_layer(Layer,Node1), in_layer(Layer,Node3).

%Computing all the crossings.
crossing(Node1,Node2,Node3,Node4) :- edge_from_same_layers(Node1,Node2,Node3,Node4), antecedent(Node1,Node3), antecedent(Node4,Node2). 
crossing(Node1,Node2,Node3,Node4) :- edge_from_same_layers(Node1,Node2,Node3,Node4), antecedent(Node3,Node1), antecedent(Node2,Node4).

% A node Node1 is an antecedent of a node Node2 if they are in the same layer and the Node1 position is antecedent of the Node2 position.
antecedent(Node1,Node2):- in_layer(Layer,Node1), in_layer(Layer,Node2), Node1 != Node2, position(Node1,Pos1), position(Node2,Pos2), Pos1 < Pos2.

% Assign a penalty to each violation of the crossing.
:~ crossing(Node1, Node2, Node3, Node4 ). [1,Node1,Node2,Node3,Node4]

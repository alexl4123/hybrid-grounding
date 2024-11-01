% Guess colours.
chosenColour(N,C) | notChosenColour(N,C) :- node(N), colour(C).

% At least one color per node.
:- node(X), not colored(X).
colored(X) :- chosenColour(X,Fv1).

% Only one color per node.
:- chosenColour(N,C1), chosenColour(N,C2), C1!=C2. 

% No two adjacent nodes have the same colour. 
Y, chosenColour(X,C), chosenColour(Y,C).

node(1).
node(2).
node(3).
node(4).
link(1,2).
link(1,3).
link(2,4).
link(4,3).
link(3,1).
colour(red0).
colour(green0).
colour(blue0).
%colour(yellow0).
%colour(cyan0).

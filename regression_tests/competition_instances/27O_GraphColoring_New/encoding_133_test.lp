colours(C1,C2) :- colour(C1), colour(C2), C1 < C2.
notnext(C1,C3) :- colours(C1,C2), colours(C2,C3).
next(C1,C2)    :- colours(C1,C2), not notnext(C1,C2).
later(C2)      :- next(C1,C2).
index(C1,1)    :- colour(C1), not later(C1).
index(C2,I+1)  :- next(C1,C2), index(C1,I).

chosenColour(N,C)    :- node(N), index(C,I), I <= N, not notChosenColour(N,C).
notChosenColour(N,C) :- chosenColour(N,CC), index(C,I), I <= N, C != CC.
notChosenColour(N,C) :- chosenColour(NN,C), link(NN,N), NN < N.

colored(N) :- chosenColour(N,C).
:- node(N), not colored(N).

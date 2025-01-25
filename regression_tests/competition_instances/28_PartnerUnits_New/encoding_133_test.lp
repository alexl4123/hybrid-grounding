
elem(z,Z) :- zone2sensor(Z,D).
elem(d,D) :- zone2sensor(Z,D).

numb(A,N) :- elem(A,N), not elem(A,N+1).

zone :- numb(z,N), numb(d,M), N > M.

rule(z) :- zone.
rule(d) :- not zone.

{ gt(A,X,U) } :- elem(A,X), comUnit(U), comUnit(U1), U1=U+1, rule(A), U < X.
{ gt(A,X,U) } :- elem(A,X), comUnit(U), comUnit(U1), U1=U+1, not rule(A).

:- gt(A,X,U), 1 < U, not gt(A,X,U-1).

unit2zone(1,Z)   :- elem(z,Z), comUnit(1), not gt(z,Z,1).
unit2zone(U+1,Z) :- gt(z,Z,U), not gt(z,Z,U+1).

:- comUnit(U), #count{ Z : unit2zone(U,Z) } > 2.

unit2sensor(1,D)   :- elem(d,D), comUnit(1), not gt(d,D,1).
unit2sensor(U+1,D) :- gt(d,D,U), not gt(d,D,U+1).

:- comUnit(U), #count{ D : unit2sensor(U,D) } > 2.

partner(d,D,U) :- unit2zone(U,Z), rule(d), zone2sensor(Z,D).
partner(z,Z,U) :- unit2sensor(U,D), rule(z), zone2sensor(Z,D).

partnerunits(U,P) :- partner(d,D,U), unit2sensor(P,D), U < P.
partnerunits(P,U) :- partner(d,D,U), unit2sensor(P,D), P < U.
partnerunits(U,P) :- partner(z,Z,U), unit2zone(P,Z), U < P.
partnerunits(P,U) :- partner(z,Z,U), unit2zone(P,Z), P < U.
partnerunits(U,P) :- partnerunits(P,U), P < U.

:- comUnit(U), maxPU(M), #count{ P : partnerunits(U,P) } > M.

% gtd(X+1,U) :- gt(A,X,U), comUnit(U+2), rule(A), elem(A,X+1).
% gtd(X+1,U) :- gtd(X,U), rule(A), elem(A,X+1).

% :- gt(A,X,U), 1 < U, rule(A), not gtd(X,U-1).

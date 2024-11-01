zone(Z) :- zone2sensor(Z,D).
doorSensor(D) :- zone2sensor(Z,D).

unit2zone(U,Z) | -unit2zone(U,Z) :- zone(Z), comUnit(U).
:- unit2zone(U,Z1), unit2zone(U,Z2), unit2zone(U,Z3), Z1!=Z2, Z2!=Z3,Z1!=Z3.
:- unit2zone(U1,Z), unit2zone(U2,Z), U1!=U2.
atLeastOneUnit(Z):- unit2zone(Fv1,Z).
:- zone(Z), not atLeastOneUnit(Z).


unit2sensor(U,D) | -unit2sensor(U,D) :- doorSensor(D), comUnit(U).

:- unit2sensor(U,D1), unit2sensor(U,D2), unit2sensor(U,D3), D1!=D2, 
   D2!=D3,D1!=D3.
:- unit2sensor(U1,D), unit2sensor(U2,D), U1!=U2.
atLeastOneSensor(D):- unit2sensor(Fv1,D).
:- doorSensor(D), not atLeastOneSensor(D).

partnerunits(U,P) :- unit2zone(U,Z), unit2sensor(P,D), zone2sensor(Z,D), 
     U!=P.
partnerunits(U,P) :- partnerunits(P,U).

:- partnerunits(U,P1), partnerunits(U,P2), partnerunits(U,P3), P1!=P2, 
    P2!=P3,P1!=P3.

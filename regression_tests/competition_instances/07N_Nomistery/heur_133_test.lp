fuelcost(17,l0,l1).
fuelcost(11,l0,l2).
fuelcost(1,l0,l3).
fuelcost(17,l1,l0).
fuelcost(4,l1,l2).
fuelcost(6,l1,l3).
at(t0,l1).
fuel(t0,18).
at(p0,l1).
at(p1,l0).
at(p2,l3).
at(p3,l1).
goal(p0,l3).
goal(p1,l2).
goal(p3,l0).
step(1).
step(2).
step(3).
step(4).
step(5).
step(6).
step(7).
step(8).
step(9).
step(10).
step(11).
step(12).
step(13).
step(14).
step(15).
%
% Nomystery for ASP 2013. 
%
% Domain specification freely adapted from the plasp PDDL-to-ASP output 
% (http://potassco.sourceforge.net/labs.html)
%
% Author (2013) GB Ianni
%
%
%
truck(T) :- fuel(T,_).
package(P) :- at(P,L), not truck(P).
location(L) :- fuelcost(_,L,_).
location(L) :- fuelcost(_,_,L).
locatable(O) :- at(O,L).
%
at(O,L,0) :- at(O,L).
fuel(T,F,0) :- fuel(T,F).
%

% 
% GENERATE  >>>>>
1 <= { unload( P,T,L,S ) : 
        package( P ) , 
 	truck( T ) , 
	location( L ); 
    load( P,T,L,S ) : 
	package( P ) , 
	truck( T ) , 
	location( L ); 
    drive( T,L1,L2,S ) : 
	fuelcost( Fueldelta,L1,L2 ) , 
	truck( T );
    noop(S)
  } <= 1 :- step(S), S > 0.
% <<<<<  GENERATE

% unload/4, effects
at( P,L,S ) :- unload( P,T,L,S ).
del( in( P,T ),S ) :- unload( P,T,L,S ).

% load/4, effects
del( at( P,L ),S ) :- load( P,T,L,S ).
in( P,T,S ) :- load( P,T,L,S ).

% drive/4, effects
del( at( T,L1 ), S ) :- drive( T,L1,L2,S ).
at( T,L2,S ) :- drive( T,L1,L2,S). 
del( fuel( T,Fuelpre ),S ) :- drive( T,L1,L2,S ), fuel(T, Fuelpre,S-1).
fuel( T,Fuelpost,S ) :- drive( T,L1,L2,S ), fuelcost(Fueldelta,L1,L2), fuel(T,Fuelpre,S-1), Fuelpost = Fuelpre - Fueldelta.
% <<<<<  EFFECTS APPLY
% 
% INERTIA  >>>>>
at( O,L,S ) :- at( O,L,S-1 ), not del( at( O,L ),S  ), step(S).
in( P,T,S ) :- in( P,T,S-1 ), not del( in( P,T ),S  ), step(S).
fuel( T,Level,S ) :- fuel( T,Level,S-1 ), not del( fuel( T,Level) ,S ), truck( T ), step(S).
% <<<<<  INERTIA
% 

% 
% 
% PRECONDITIONS CHECK  >>>>>

% unload/4, preconditions
 :- unload( P,T,L,S ), not preconditions_u( P,T,L,S ).
preconditions_u( P,T,L,S ) :- step(S), at( T,L,S-1 ), in( P,T,S-1 ), package( P ), truck( T ).

% load/4, preconditions
 :- load( P,T,L,S ), not preconditions_l( P,T,L,S ).
preconditions_l( P,T,L,S ) :- step(S), at( T,L,S-1 ), at( P,L,S-1 ).

% drive/5, preconditions
 :- drive( T,L1,L2,S ), not preconditions_d( T,L1,L2,S ).
preconditions_d( T,L1,L2,S ) :- step(S), at( T,L1,S-1 ), fuel( T, Fuelpre, S-1), fuelcost(Fueldelta,L1,L2), Fuelpre >= Fueldelta.
% <<<<<  PRECONDITIONS HOLD
% 

% GOAL CHECK

goalreached :- step(S),  N = #count{ P,L : at(P,L,S) , goal(P,L) }, N = #count{ P1,L1 : goal(P1,L1) }.
:- not goalreached.

% Gringo directives to show / hide particular literals
%#hide.
%#show unload/4.
%#show load/4.
%#show drive/4.
%#show at/2.
%#show at/3.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%% VALVES LOCATION OPTIMIZATION %%%%%%%
%%%%%%% FO: MAX MIN SATISFIED DEM.   %%%%%%%
%%%%%%%   TYPE: PIPE REACHABILITY    %%%%%%%
%%%%%%%   ANDREA PEANO 10/10/2012    %%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

		%just some tools
		%Symmetric pipe
symm_pipe(A,B):- pipe(A,B).
symm_pipe(B,A):- pipe(A,B).
		%We need a lexicographic order (there may be more than one worst isolation cases)
less_ico(pipe(A,B), pipe(C,D)):- pipe(A,B), pipe(C,D), A<C.
less_ico(pipe(A,B), pipe(C,D)):- pipe(A,B), pipe(C,D), A = C, B<D.

%Adjacency of pipes (common junction and unshared junctions)
%adj(pipe(X,Y), pipe(W,Z), COM, U1, U2) :- symm_pipe(COM,U1), symm_pipe(COM,U2), U1!=U2, not tank(COM),
%				pipe(X,Y), pipe(W,Z), 
%                                2 {COM=W, COM=Z, COM=X, COM=Y} 2,
%				1 {U1=W, U1=Z, U1=X, U1=Y} 1,
%				1 {U2=W, U2=Z, U2=X, U2=Y} 1.
%adj(pipe(X,Y), pipe(W,Z), COM, U1, U2) :- symm_pipe(COM,U1), symm_pipe(COM,U2), U1!=U2, not tank(COM),
%				pipe(X,Y), pipe(W,Z), 
%                                2 = #count {COM : COM=W; COM : COM=Z; COM : COM=X; COM : COM=Y},
%				1 = #count {U1 : U1=W; U1 : U1=Z; U1 : U1=X; U1 : U1=Y},
%				1 = #count {U2 : U2=W; U2 : U2=Z; U2 : U2=X; U2 : U2=Y}.
% 
% Fix Mar 24th. 2013. Removed cumbersome definition for adj predicate.
%
swap(pipe(A,B),pipe(A,B)):- pipe(A,B).
swap(pipe(A,B),pipe(B,A)):- pipe(A,B).
                %Adjacency of pipes (common junction and unshared junctions)
adj(pipe(A,B),pipe(C,D),COM,U1,U2):-
                swap(pipe(A,B),pipe(COM,U1)),
                swap(pipe(C,D),pipe(COM,U2)),
                U1!=U2, not tank(COM).



		%
		%There are some valves that are closed to isolate the broken pipe
1 <= { closed_valve(v(X,Y), broken(A,B)) : symm_pipe(X,Y) } <= Nv :- pipe(A,B), valves_number(Nv).

		%
		%If a valve is closed for some pipes, then it must be installed!!
valve(A,B) :- closed_valve(v(A,B), _).

		%
		%There should always be installed valves near the tanks
valve(A,B) :- symm_pipe(A,B), tank(A).

		%
		%Valves must be at most Nv
:- valves_number(Nv), not Nv = #count{ X,Y : valve(X,Y) , pipe(X,Y); Y,X : valve(Y,X) , pipe(X,Y)}.

		%
		%At most X valves per pipe must be allowed (either 1 or 2)
:- valves_per_pipe(1), pipe(A,B), valve(A,B), valve(B,A).

		%
		%some symmetry breaking on valves
:- junction(X), not tank(X), symm_pipe(X,A), symm_pipe(X,B),
		2 = #count{ X,Y : symm_pipe(X,Y) }, A>B, valve(X,A).

		%
		%A pipe adjacent to the tank is reached, when a generic pipe is broken iff there is no valve between them.
reached(pipe(A,B), broken(X,Y)):- tank(A), pipe(X,Y), pipe(A,B), not closed_valve(v(A,B), broken(X,Y)).
reached(pipe(A,B), broken(X,Y)):- tank(B), pipe(X,Y), pipe(A,B), not closed_valve(v(B,A), broken(X,Y)).

		%
		%Can we recursively reach any tank??
reached(pipe(A,B), broken(X,Y)) :- adj(pipe(A,B), pipe(C,D), COM, U1, U2), %COM is not a tank! 
				not closed_valve(v(COM,U1), broken(X,Y)),
				not closed_valve(v(COM,U2), broken(X,Y)),
				reached(pipe(C,D), broken(X,Y)).

		%
		%The broken pipe must be unreachable!
:- pipe(A,B), reached(pipe(A,B), broken(A,B)).

		%
		% Pair-wise comparisons between delivered demand pipe isolation cases
%lower(pipe(X,Y), pipe(W,Z)) :- pipe(X,Y), pipe(W,Z),
%		#sum [ 	reached(pipe(A,B), broken(X,Y))=Dn: dem(A,B,Dn),
%			reached(pipe(C,D), broken(W,Z))=-Dm: dem(C,D,Dm) ] 0.
%lower(pipe(X,Y), pipe(W,Z)) :- pipe(X,Y), pipe(W,Z),
%		S1 = #sum { Dn,A,B,X,Y : reached(pipe(A,B), broken(X,Y)), dem(A,B,Dn) },
%               S2 = #sum { Dm,C,D,W,Z : reached(pipe(C,D), broken(W,Z)), dem(C,D,Dm) }, S1 - S2 <= 0.
lower(pipe(X,Y), pipe(W,Z)) :- pipe(X,Y), pipe(W,Z),
		#sum { Dn,A,B : reached(pipe(A,B), broken(X,Y)), dem(A,B,Dn);
                       Dm,C,D : reached(pipe(C,D), broken(W,Z)), dem(C,D,NegDm), Dm = -NegDm } <= 0.

		%
		%Then the lower are...
lower_lexico(pipe(X,Y), pipe(W,Z)) :- pipe(X,Y), pipe(W,Z),
				lower(pipe(X,Y), pipe(W,Z)), not lower(pipe(W,Z), pipe(X,Y)).
lower_lexico(pipe(X,Y), pipe(X,Y)) :- pipe(X,Y),
				lower(pipe(X,Y), pipe(X,Y)).
lower_lexico(pipe(X,Y), pipe(W,Z)) :- pipe(X,Y), pipe(W,Z), % with the same delivered demand
				lower(pipe(X,Y), pipe(W,Z)), lower(pipe(W,Z),pipe(X,Y)),
				less_ico(pipe(X,Y), pipe(W,Z)).

		%
		%And the worst isolation case is the one for which all lower_lexico are true
%worst(pipe(X,Y)) :- pipe(X,Y), lower_lexico(pipe(X,Y),pipe(W,Z)) : pipe(W,Z).
worst(pipe(X,Y)) :- pipe(X,Y), C = #count { W,Z : pipe(W,Z) }, 
                               D = #count{ W,Z : lower_lexico(pipe(X,Y),pipe(W,Z)) , pipe(W,Z)}, C = D.


worst_deliv_dem(pipe(A,B), D) :- dem(A,B,D), pipe(X,Y),
		reached(pipe(A,B), broken(X,Y)), worst(pipe(X,Y)).

		%
		%Worst isolation case' delivered demand maximization

:~ dem(A,B,D),  not worst_deliv_dem(pipe(A,B),D). [D,A,B]
%#maximize [ worst_deliv_dem(pipe(A,B), D)=D : pipe(A,B) ].

%#hide.
%#show valve/2.
%#show worst_deliv_dem/2.

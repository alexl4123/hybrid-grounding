player(player_01).
stone(stone_01).
isgoal(pos_1_1).
isgoal(pos_1_2).
isnongoal(pos_2_1).
isnongoal(pos_2_2).
movedir(pos_1_1,pos_1_2,dir_down).
movedir(pos_1_1,pos_2_1,dir_right).
movedir(pos_2_1,pos_1_1,dir_left).
movedir(pos_2_1,pos_2_2,dir_down).
movedir(pos_1_2,pos_1_1,dir_up).
movedir(pos_1_2,pos_2_2,dir_right).
movedir(pos_2_2,pos_1_2,dir_left).
movedir(pos_2_2,pos_2_1,dir_up).
at(player_01,pos_2_2).
at(stone_01,pos_1_2).
clear(pos_1_1).
goal(stone_01).
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
step(16).
step(17).
step(18).
step(19).
step(20).
step(21).
step(22).
step(23).
step(24).
%
% Sokoban domain IPC 2008
%
% Adaptment from IPC 2008 domain description by GB Ianni, using the PDDL2ASP PLASP converter
% http://www.cs.uni-potsdam.de/wv/pdfformat/gekaknsc11a.pdf 
%
% 


% GENERATE  >>>>>
1 <= { pushtonongoal( P,S,Ppos,From,To,Dir,T ) : 
	movedir( Ppos,From,Dir ) ,
	movedir( From,To,Dir ) , 
	isnongoal( To ) , 
	player( P ) , 
	stone( S ) , Ppos != To , Ppos != From , From != To; 
    move( P,From,To,Dir,T ) : 
	movedir( From,To,Dir ) , 
	player( P ) , From != To;
    pushtogoal( P,S,Ppos,From,To,Dir,T ) : 
	movedir( Ppos,From,Dir ) , 
	movedir( From,To,Dir ) , 
	isgoal( To ) , player( P ) , stone( S ) , Ppos != To , Ppos != From , From != To;
    noop(T) } <= 1 :- step(T).

% <<<<<  GENERATE
% 

% 
%
% Initial state
at_(P,To,0) :- at(P,To).
clear_(P,0) :- clear(P).
atgoal(S,0) :- isgoal(L), stone(S), at(S,L).
 
% EFFECTS APPLY  >>>>>

% push-to-nongoal/7, effects
del( at( P,Ppos ),Ti ) :- pushtonongoal( P,S,Ppos,From,To,Dir,Ti ), 
                          movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
del( at( S,From ),Ti ) :- pushtonongoal( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
del( clear( To ),Ti ) :- pushtonongoal( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
at_( P,From,Ti ) :- pushtonongoal( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
at_( S,To,Ti ) :- pushtonongoal( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
clear_( Ppos,Ti ) :- pushtonongoal( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
del( atgoal( S ),Ti ) :- pushtonongoal( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.

% move/5, effects
del( at( P,From ),Ti ) :- move( P,From,To,Dir,Ti ), movedir( From,To,Dir ), player( P ), From != To.
del( clear( To ),Ti ) :- move( P,From,To,Dir,Ti ), movedir( From,To,Dir ), player( P ), From != To.
at_( P,To,Ti ) :- move( P,From,To,Dir,Ti ), movedir( From,To,Dir ), player( P ), From != To.
clear_( From,Ti ) :- move( P,From,To,Dir,Ti ), movedir( From,To,Dir ), player( P ), From != To.

% push-to-goal/7, effects
del( at( P,Ppos ),Ti ) :- pushtogoal( P,S,Ppos,From,To,Dir,Ti ), 
                          movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
del( at( S,From ),Ti ) :- pushtogoal( P,S,Ppos,From,To,Dir,Ti ), 
                          movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
del( clear( To ),Ti ) :- pushtogoal( P,S,Ppos,From,To,Dir,Ti ), 
                         movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
at_( P,From,Ti ) :- pushtogoal( P,S,Ppos,From,To,Dir,Ti ), 
                   movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
at_( S,To,Ti ) :- pushtogoal( P,S,Ppos,From,To,Dir,Ti ), 
                 movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
clear_( Ppos,Ti ) :- pushtogoal( P,S,Ppos,From,To,Dir,Ti ), 
                    movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
atgoal( S,Ti ) :- pushtogoal( P,S,Ppos,From,To,Dir,Ti ), 
                  stone( S ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
% <<<<<  EFFECTS APPLY
% 

% 
% 
% INERTIA  >>>>>
clear_( L,Ti ) :- clear_( L,Ti-1 ), not del( clear( L ),Ti  ), step(Ti).
atgoal( S,Ti ) :- atgoal( S,Ti-1 ), not del( atgoal( S ),Ti ), stone( S ), step(Ti).
at_( T,L,Ti ) :- at_( T,L,Ti-1 ), not del( at( T,L ) ,Ti  ), step(Ti).
% <<<<<  INERTIA
% 

% 
% 
% PRECONDITIONS HOLD  >>>>>

% push-to-nongoal/6, preconditions
 :- pushtonongoal( P,S,Ppos,From,To,Dir,Ti ), not preconditions_png( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To.
preconditions_png( P,S,Ppos,From,To,Dir,Ti ) :- at_( P,Ppos,Ti-1 ), at_( S,From,Ti-1 ), clear_( To,Ti-1 ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isnongoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, step(Ti).

% move/4, preconditions
 :- move( P,From,To,Dir,Ti ), not preconditions_m( P,From,To,Dir,Ti ), movedir( From,To,Dir ), player( P ), From != To.
preconditions_m( P,From,To,Dir,Ti ) :- at_( P,From,Ti-1 ), clear_( To,Ti-1 ), movedir( From,To,Dir ), movedir( From,To,Dir ), player( P ), From != To, step(Ti).

% push-to-goal/6, preconditions
 :- pushtogoal( P,S,Ppos,From,To,Dir,Ti ), not preconditions_pg( P,S,Ppos,From,To,Dir,Ti ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, step(Ti).
preconditions_pg( P,S,Ppos,From,To,Dir,Ti ) :- at_( P,Ppos,Ti-1 ), at_( S,From,Ti-1 ), clear_( To,Ti-1 ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), movedir( Ppos,From,Dir ), movedir( From,To,Dir ), isgoal( To ), player( P ), stone( S ), Ppos != To, Ppos != From, From != To, step(Ti).

% <<<<<  PRECONDITIONS HOLD
% 
%
% Goal Reached check 
%
goalreached :- step(T), N = #count{ X : atgoal(X,T) , goal(X) }, N = #count{ X1 : goal(X1) }.
:- not goalreached.

% Gringo directives to show / hide particular literals
%#hide.
%#show pushtonongoal/7.
%#show move/5.
%#show pushtogoal/7.

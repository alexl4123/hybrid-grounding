%
% IPC 2011 Visit-all domain
%
%
% ASP Competition 2013 version, by GB Ianni. Adaptment from a plasp PDDL2ASP conversion 
% (http://www.cs.uni-potsdam.de/wv/pdfformat/gekaknsc11a.pdf)
% 
% 
%
% initial status
%
visited(X) :- at(X).
atrobot(X,0) :- at(X).

% GENERATE  >>>>>
1 <= { move( Curpos,Nextpos,T ) : connected( Curpos,Nextpos ) , Curpos != Nextpos } <= 1 :- step(T).
% <<<<<  GENERATE
% 

% 
% 
% EFFECTS APPLY  >>>>>

% move/3, effects
atrobot( Nextpos,T ) :- move( Curpos,Nextpos,T ).
del( atrobot( Curpos ),T ) :- move( Curpos,Nextpos,T ).
visited( Nextpos ) :- move( Curpos,Nextpos,T ).
% <<<<<  EFFECTS APPLY
% 

% 
% 
% INERTIA  >>>>>
atrobot( X,T ) :- step(T), atrobot( X,T-1 ), not del( atrobot( X ) ,T  ).
%
% GB: it is not needed to let 'visited' subject to timestamping 
%
% <<<<<  INERTIA
% 

% 
% 
% PRECONDITIONS HOLD  >>>>>

% move/3, preconditions
 :- move( Curpos,Nextpos,T ), not atrobot(Curpos, T-1), step(T).
% <<<<<  PRECONDITIONS HOLD
% 

goalreached :- N = #count{ X : visited(X) , visit(X) }, N = #count{ X1 : visit(X1) }.
:- not goalreached.



% Gringo directives to show / hide particular literals
%#hide.
%#show move/3.

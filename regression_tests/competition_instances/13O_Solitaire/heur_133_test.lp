time(1).
time(2).
time(3).
full(3,1).
full(4,1).
full(5,1).
full(3,2).
full(4,2).
full(5,2).
full(1,3).
full(2,3).
full(3,3).
full(4,3).
full(5,3).
full(6,3).
full(7,3).
full(1,4).
full(2,4).
full(3,4).
empty(4,4).
full(5,4).
full(6,4).
full(7,4).
full(1,5).
full(2,5).
full(3,5).
full(4,5).
full(5,5).
full(6,5).
full(7,5).
full(3,6).
full(4,6).
full(5,6).
full(3,7).
full(4,7).
full(5,7).

% Solitare
%
% Martin Brain
% mjb@cs.bath.ac.uk
% 04/08/06
%
% Marcello Balduccini
% marcello.balduccini@gmail.com
% Jan 11, 2011
% Modified to comply with the requirements of ASPCOMP2011.
%

% Time steps and starting states are supplied by the instance.

% 2x2 squares in the corner aren't used
range(1).
range(X+1) :- range(X), X < 7.

location(1,X) :- range(X), 3 <= X, X <= 5.
location(2,X) :- range(X), 3 <= X, X <= 5.
location(Y,X) :- range(Y), 3 <= Y, Y <= 5, range(X).
location(6,X) :- range(X), 3 <= X, X <= 5.
location(7,X) :- range(X), 3 <= X, X <= 5.

% Moves can be made in one of four directions
direction(up).
direction(down).
direction(left).
direction(right).

% Each location is either full or empty
status(full).
status(empty).

% Can move a full location over a full location to an empty one.
possibleMove(T,up,X,Y) :-  state(T,full,X,Y), state(T,full,X,Y-1), state(T,empty,X,Y-2),
                      time(T), location(X,Y),     location(X,Y-1),      location(X,Y-2).

possibleMove(T,down,X,Y) :-  state(T,full,X,Y), state(T,full,X,Y+1), state(T,empty,X,Y+2),
                        time(T), location(X,Y),     location(X,Y+1),      location(X,Y+2).

possibleMove(T,left,X,Y) :-  state(T,full,X,Y), state(T,full,X-1,Y), state(T,empty,X-2,Y),
                        time(T), location(X,Y),     location(X-1,Y),      location(X-2,Y).

possibleMove(T,right,X,Y) :-  state(T,full,X,Y), state(T,full,X+1,Y), state(T,empty,X+2,Y),
                         time(T), location(X,Y),     location(X+1,Y),      location(X+2,Y).


%% At each time step choose a move
1 <= { move(T,D,X,Y) : direction(D) , location(X,Y) } <= 1 :- time(T), not checking_solution.

%% CHECKER [marcy 011111]
%% Exactly one move must be present at each step.
%% Only needed if the choice rule is not enabled.
% Mar 25th, 2013. DISABLED (meaningless)
%:- not 1 <= #count { T,D,X,Y : move(T,D,X,Y) , direction(D) , location(X,Y) } <= 1, time(T), checking_solution.

% A move must be possible
 :- move(T,D,X,Y), not possibleMove(T,D,X,Y), time(T), direction(D), location(X,Y).

% Now need to look at the effect of moves
% (section location parameter to cut grounding size)
state(T+1,empty,X,Y) :- move(T,up,X,Y), location(X,Y), time(T).
state(T+1,empty,X,Y-1) :- move(T,up,X,Y), location(X,Y), location(X,Y-1), time(T).
state(T+1,full,X,Y-2) :- move(T,up,X,Y), location(X,Y), location(X,Y-2), time(T).

state(T+1,empty,X,Y) :- move(T,down,X,Y), location(X,Y), time(T).
state(T+1,empty,X,Y+1) :- move(T,down,X,Y), location(X,Y), location(X,Y+1), time(T).
state(T+1,full,X,Y+2) :- move(T,down,X,Y), location(X,Y), location(X,Y+2), time(T).

state(T+1,empty,X,Y) :- move(T,left,X,Y), location(X,Y), time(T).
state(T+1,empty,X-1,Y) :- move(T,left,X,Y), location(X,Y), location(X-1,Y), time(T).
state(T+1,full,X-2,Y) :- move(T,left,X,Y), location(X,Y), location(X-2,Y), time(T).

state(T+1,empty,X,Y) :- move(T,right,X,Y), location(X,Y), time(T).
state(T+1,empty,X+1,Y) :- move(T,right,X,Y), location(X,Y), location(X+1,Y), time(T).
state(T+1,full,X+2,Y) :- move(T,right,X,Y), location(X,Y), location(X+2,Y), time(T).


changed(T+1,X,Y) :- move(T,up,X,Y), location(X,Y), time(T).
changed(T+1,X,Y-1) :- move(T,up,X,Y), location(X,Y), location(X,Y-1), time(T).
changed(T+1,X,Y-2) :- move(T,up,X,Y), location(X,Y), location(X,Y-2), time(T).

changed(T+1,X,Y) :- move(T,down,X,Y), location(X,Y), time(T).
changed(T+1,X,Y+1) :- move(T,down,X,Y), location(X,Y), location(X,Y+1), time(T).
changed(T+1,X,Y+2) :- move(T,down,X,Y), location(X,Y), location(X,Y+2), time(T).

changed(T+1,X,Y) :- move(T,left,X,Y), location(X,Y), time(T).
changed(T+1,X-1,Y) :- move(T,left,X,Y), location(X,Y), location(X-1,Y), time(T).
changed(T+1,X-2,Y) :- move(T,left,X,Y), location(X,Y), location(X-2,Y), time(T).

changed(T+1,X,Y) :- move(T,right,X,Y), location(X,Y), time(T).
changed(T+1,X+1,Y) :- move(T,right,X,Y), location(X,Y), location(X+1,Y), time(T).
changed(T+1,X+2,Y) :- move(T,right,X,Y), location(X,Y), location(X+2,Y), time(T).

state(T+1,S,X,Y) :- not changed(T+1,X,Y), state(T,S,X,Y), status(S), location(X,Y), time(T).

state(1,full,X,Y) :- full(X,Y).
state(1,empty,X,Y) :- empty(X,Y).

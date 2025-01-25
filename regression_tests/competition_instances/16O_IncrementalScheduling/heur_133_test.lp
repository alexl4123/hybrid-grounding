device(1).
instances(1,1).
device(2).
instances(2,1).
job(1).
job(2).
job(3).
job(4).
job(5).
precedes(1,3).
precedes(2,3).
precedes(3,4).
precedes(4,5).
importance(3,3).
importance(2,1).
importance(1,2).
importance(4,5).
importance(5,2).
job_device(1,1).
job_device(2,2).
job_device(3,1).
job_device(4,1).
job_device(5,2).
job_len(1,3).
job_len(2,4).
job_len(3,2).
job_len(4,5).
job_len(5,1).
deadline(2,4).
max_total_penalty(5).
curr_time(0).
max_value(11).
%
% ******GRINGO 3.x REQUIRED******
%
%

time(0).
time(T+1) :- time(T), T < MT, max_value(MT).
%time(0..MT) :- max_value(MT).

pen_value(T) :- time(T).
td_value(T) :- time(T).

instance_of(D,1) :- device(D).
instance_of(D,I+1) :- device(D), instance_of(D,I), instances(D,N), I < N.

% Pick a unique start time and instance for each job
1 <= { start(J,S) : time(S) } <= 1 :- job(J).
1 <= { on_instance(J,I) : instance_of(D,I) } <= 1 :- job(J), job_device(J,D).


%----------------------
% - overlap
%----------------------
:- on_instance(J1,I), on_instance(J2,I), J1 != J2,
   job_device(J1,D), job_device(J2,D),
   start(J1,S1), job_len(J1,L1),
   start(J2,S2),
   S1 <= S2, S2 < S1 + L1.


%----------------------
%     - order
%----------------------
:- precedes(J1,J2),
   start(J1,S1), job_len(J1,L1),
   start(J2,S2),
   S2 < S1 + L1.


%-------------------------------------
%     - completion -- total-tardiness
%-------------------------------------
td(J,S + L - D) :-
	job(J),
	start(J,S), job_len(J,L),
	deadline(J,D),
	S + L > D.

td(J,0) :-
	job(J),
	start(J,S), job_len(J,L),
	deadline(J,D),
	S + L <= D.

%-------------------------------------
%     - completion -- penalty
%-------------------------------------

penalty(J,TD * I) :-
	job(J),
	td(J,TD),
	importance(J,I).

:- penalty(J,P),
   max_value(MV),
   P > MV.

tot_penalty(TP) :-
	pen_value(TP),
	TP = #sum{ P,J :  penalty(J,P) }.

%
% If the value of the total penalty would be greater than the
% maximum allowed value of pen_value(_), the above rule
% does not define tot_penalty(_).
% In that case, the solution is not acceptable.
%
has_tot_penalty :-
	tot_penalty(TP).
-has_tot_penalty :-
	not has_tot_penalty.
:- -has_tot_penalty.

:- pen_value(TP), tot_penalty(TP), max_total_penalty(K),
   TP > K.


%----------------------
%     - instance assignment
%----------------------


:- on_instance(J1,I), on_instance(J2,I),
   job_device(J1,D), job_device(J2,D),
   instances(D,N), N > 1,
   J1 != J2,
   start(J1,S1), start(J2,S2),
   job_len(J1,L1),
   S1 <= S2, S2 < S1 + L1.

:- on_instance(J,I),
   device(D),
   job(J), job_device(J,D),
   offline_instance(D,I),
   must_schedule(J).


%----------------------
% - current schedule
%----------------------

already_started(J) :-
	curr_job_start(J,S),
	curr_time(CT),
	CT > S.

already_finished(J) :-
	curr_job_start(J,S),
	job_len(J,L),
	curr_time(CT),
	CT >= S + L.

must_schedule(J) :-
	job(J),
	not must_not_schedule(J).

must_not_schedule(J) :-
	already_started(J),
	not rescheduled(J).

rescheduled(J) :-
	already_started(J),
	not already_finished(J),
	job_device(J,D),
	curr_on_instance(J,I),
	offline_instance(D,I).

:- start(J,S),
   curr_time(CT),
   S < CT,
   device(D),
   job_device(J,D),
   time(S),
   must_schedule(J).

:- start(J,S),
   curr_job_start(J,CS),
   S != CS,
   job_device(J,D),
   must_not_schedule(J).

:- on_instance(J,I),
   curr_on_instance(J,CI),
   I != CI,
   must_not_schedule(J).

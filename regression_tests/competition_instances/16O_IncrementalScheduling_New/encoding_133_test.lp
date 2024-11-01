time(S)   :- curr_time(S), max_value(T), S <= T.
time(S+1) :- time(S), max_value(T), S < T.

instance_of(D,I)   :- device(D), instances(D,I), 0 < I.
instance_of(D,I-1) :- instance_of(D,I), 1 < I.

closure(J1,J2) :- job(J1), job(J2), precedes(J1,J2).
closure(J1,J2) :- job(J1), precedes(J1,J), closure(J,J2).
inconsistent   :- closure(J,J), job_len(J,L), 0 < L.

%----------------------
% - current schedule
%----------------------

already_started(J)   :- job(J), curr_job_start(J,S), curr_time(T), T > S.
already_finished(J)  :- job(J), curr_job_start(J,S), job_len(J,L), curr_time(T), T >= S+L.
rescheduled(J)       :- already_started(J), not already_finished(J), job_device(J,D), curr_on_instance(J,I), offline_instance(D,I).
must_not_schedule(J) :- already_started(J), not rescheduled(J).
must_schedule(J)     :- job(J), not must_not_schedule(J).

inconsistent :- precedes(J1,J2), must_schedule(J1), must_not_schedule(J2).
inconsistent :- precedes(J1,J2), must_not_schedule(J1), must_not_schedule(J2), curr_job_start(J1,S), job_len(J1,L), curr_job_start(J2,T), T < S+L.
inconsistent :- must_not_schedule(J1), must_not_schedule(J2), job_device(J1,D), curr_on_instance(J1,I), job_device(J2,D), curr_on_instance(J2,I), curr_job_start(J1,S), job_len(J1,L), curr_job_start(J2,T), S <= T, T < S+L, J1 != J2.

%----------------------
% - device instances
%----------------------

delay(D,I,S+L) :- must_not_schedule(J), job_device(J,D), curr_on_instance(J,I), curr_job_start(J,S), job_len(J,L), not already_finished(J).
delayed(D,I)   :- delay(D,I,S).

available(D,I,S) :- delay(D,I,S), time(S).
available(D,I,S) :- instance_of(D,I), curr_time(S), time(S), not delayed(D,I), not offline_instance(D,I).

avail(D,S) :- available(D,I,S).
later(D,T) :- avail(D,S), avail(D,T), S < T.
early(D,S) :- avail(D,S), not later(D,S).
sched(D)   :- early(D,S).

inconsistent :- must_schedule(J), job_device(J,D), not sched(D).

%----------------------
% - penalty factors
%----------------------

import(J) :- job(J), deadline(J,D), importance(J,I).

factor(J,I) :- job(J), deadline(J,D), importance(J,I), 0 < I.
factor(J,1) :- job(J), deadline(J,D), not import(J).

%----------------------
% - minimal start times
%----------------------

lower(J1,S)   :- must_not_schedule(J1), curr_job_start(J1,S).
lower(J1,S)   :- must_schedule(J1), job_device(J1,D), early(D,S).
lower(J2,S+L) :- must_not_schedule(J1), must_schedule(J2), precedes(J1,J2), lower(J1,S), job_len(J1,L), not already_finished(J1).
lower(J2,S+L) :- must_schedule(J1), must_schedule(J2), precedes(J1,J2), lower(J1,S), job_len(J1,L), time(S).
unlow(J,S)    :- lower(J,S), lower(J,T), S < T.
first(J,S)    :- lower(J,S), not unlow(J,S).

inconsistent :- must_schedule(J), first(J,S), not time(S).

%----------------------
% - static penalties
%----------------------

free(J,D-L) :- factor(J,I), deadline(J,D), job_len(J,L).

static(J,0)   :- free(J,F), first(J,S), S <= F.
static(J,I*D) :- free(J,F), first(J,S), factor(J,I), F < S, D = S-F.

stat(Q) :- #sum{ P,J : static(J,P) } = Q.

remain(P-Q) :- max_total_penalty(P), stat(Q), Q <= P.

pen(P)   :- remain(P).
pen(P-1) :- pen(P), 0 < P.

inconsistent :- max_total_penalty(P), stat(Q), P < Q.

%----------------------
% - maximal start times
%----------------------

budget(J,F+B) :- must_schedule(J), free(J,F), static(J,S), factor(J,I), remain(P), A = S+P, B = A/I.
budg(J)       :- budget(J,S), time(S+1).

decrease(J1) :- precedes(J1,J2), must_schedule(J1).

upper(J2,S)   :- budget(J2,S), budg(J2).
upper(J2,M)   :- must_schedule(J2), max_value(M), not decrease(J2), not budg(J2).
upper(J1,S-L) :- must_schedule(J1), precedes(J1,J2), upper(J2,S), job_len(J1,L), first(J2,F), F <= S.
unupp(J,T)    :- upper(J,S), upper(J,T), S < T.
final(J,S)    :- upper(J,S), not unupp(J,S).

inconsistent :- first(J,S), final(J,T), T < S.

%----------------------
% - start ranges
%----------------------

range(J,T)   :- final(J,T), not inconsistent.
range(J,T-1) :- range(J,T), first(J,S), S < T.

%----------------------
% - guess if not statically inconsistent
%----------------------

:- inconsistent.

{ gt(J,S) } :- range(J,S), not final(J,S).
:- gt(J,S+1), range(J,S), not gt(J,S).

start(J,S)   :- first(J,S), not gt(J,S).
start(J,S+1) :- gt(J,S), not gt(J,S+1).

on_instance(J,I) :- must_not_schedule(J), curr_on_instance(J,I).
1 <= { on_instance(J,I) : available(D,I,S), final(J,T), S <= T } <= 1 :- must_schedule(J), job_device(J,D), not inconsistent.
:- must_schedule(J), job_device(J,D), on_instance(J,I), available(D,I,S), T = S-1, range(J,T), not gt(J,T).

%----------------------
%     - order
%----------------------

exclude(J2,T) :- precedes(J1,J2), must_schedule(J1), gt(J1,S), job_len(J1,L), T = S+L, range(J2,T).
:- exclude(J2,T), not gt(J2,T).

%----------------------
% - overlap
%----------------------

pair(J1,J2) :- must_schedule(J1), must_schedule(J2), job_device(J1,D), job_device(J2,D), J1 < J2, not closure(J1,J2), not closure(J2,J1).

symm(J1,J2,J1,J2) :- pair(J1,J2).
symm(J1,J2,J2,J1) :- pair(J1,J2).

compare(J,JJ) :- symm(J,JJ,J1,J2), job_len(J1,L), first(J1,S1), final(J1,T1), first(J2,S2), final(J2,T2), S1 <= T2, S2 < T1+L.

unord(J1,J2) :- compare(J,JJ), symm(J,JJ,J1,J2), first(J1,S), job_len(J1,L), first(J2,F), T = S+L, F < T, not gt(J2,T-1).
unord(J1,J2) :- compare(J,JJ), symm(J,JJ,J1,J2), gt(J1,S), job_len(J1,L), first(J2,F), T = S+L, F <= T, range(J2,T), not gt(J2,T).

same(J1,J2) :- compare(J1,J2), on_instance(J1,I), on_instance(J2,I).

:- same(J1,J2), unord(J1,J2), unord(J2,J1).

%----------------------
% - reasonable start times
%----------------------

finish(D,I,T) :- available(D,I,T), not early(D,T).
finish(D,I,T) :- must_schedule(J), job_device(J,D), on_instance(J,I), job_len(J,L), start(J,S), T = S+L, time(T).
enable(J,S)   :- must_schedule(J), job_device(J,D), on_instance(J,I), finish(D,I,S), range(J,S), not first(J,S).
:- start(J,S), not first(J,S), not enable(J,S), not exclude(J,S-1).

%-------------------------------------
%     - completion -- penalty
%-------------------------------------

penal(J,T,1)     :- free(J,S), first(J,T), S < T, range(J,T+1).
penal(J,T,1)     :- free(J,T), S = T+1, range(J,S), not first(J,S).
penal(J,T+1,N+1) :- penal(J,T,N), range(J,T+2).

td(J,T,N) :- penal(J,T,N), gt(J,T).

penalty(J,0)   :- job(J), deadline(J,D), importance(J,0).
penalty(J,P)   :- static(J,P), free(J,S), first(J,T), not td(J,S,1), not td(J,T,1).
penalty(J,P+A) :- static(J,P), factor(J,I), td(J,T,N), not td(J,T+1,N+1), A = I*N.

:- remain(P), #sum{ I,J,N : td(J,T,N), factor(J,I) } > P.

has(P) :- pen(P), #sum{ I,J,N : td(J,T,N), factor(J,I) } >= P.

tot_penalty(P+Q) :- stat(Q), has(P), not has(P+1).

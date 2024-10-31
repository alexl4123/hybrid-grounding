swap(pipe(A,B),pipe(A,B)) :- pipe(A,B).
swap(pipe(A,B),pipe(B,A)) :- pipe(A,B).

symm_pipe(A,B) :- swap(P,pipe(A,B)).

less_ico(pipe(A,B),pipe(C,D)) :- pipe(A,B), pipe(C,D), A < C.
less_ico(pipe(A,B),pipe(A,D)) :- pipe(A,B), pipe(A,D), B < D.

drop(B,A) :- symm_pipe(A,B), tank(A), valves_per_pipe(1).
drop(A,C) :- symm_pipe(A,B), symm_pipe(A,C), B < C, not tank(A),
             #count{ D : symm_pipe(A,D) } < 3.

N <= { valve(A,B) : symm_pipe(A,B), not drop(A,B) } <= N :- valves_number(N).
:- symm_pipe(A,B), tank(A), not valve(A,B).
:- valves_per_pipe(1), valve(A,B), valve(B,A).

broken(P,P) :- swap(P,P).
broken(P,Q) :- extend(P,A), swap(Q,pipe(A,B)), not valve(A,B).
extend(P,A) :- broken(P,Q), swap(Q,pipe(A,B)), not valve(A,B), not tank(A).

reached(P,A) :- swap(P,P), tank(A).
reached(P,A) :- deliver(P,Q), swap(Q,pipe(A,B)), not extend(P,A).
deliver(P,Q) :- reached(P,A), swap(Q,pipe(A,B)), not broken(P,Q).

compare(P,Q,pipe(A,B),-N) :- less_ico(P,Q), dem(A,B,N),
                             deliver(P,pipe(A,B)), not deliver(Q,pipe(A,B)).
compare(P,Q,pipe(A,B), N) :- less_ico(P,Q), dem(A,B,N),
                             deliver(Q,pipe(A,B)), not deliver(P,pipe(A,B)).

lower(P) :- less_ico(P,Q), #sum{ N,R : compare(P,Q,R,N) } < X, X=0.
lower(Q) :- less_ico(P,Q), not lower(P).

worst_deliv_dem(A,B,N) :- deliver(P,pipe(A,B)), dem(A,B,N), not lower(P).

:~ dem(A,B,N), not worst_deliv_dem(A,B,N). [N,A,B]

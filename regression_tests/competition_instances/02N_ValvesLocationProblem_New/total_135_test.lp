valves_number(24).
valves_per_pipe(2).
tank(1).
tank(7).
tank(9).
junction(1). pipe(1,2). pipe(1,11). pipe(1,12). dem(1,12,56). dem(1,11,59). dem(1,2,39).
junction(2). pipe(2,3). pipe(2,14). dem(2,14,29). dem(2,3,23).
junction(3). pipe(3,4). dem(3,4,26).
junction(4). pipe(4,5). pipe(4,20). dem(4,20,29). dem(4,5,39).
junction(5). pipe(5,6). pipe(5,23). dem(5,23,43). dem(5,6,29).
junction(6). pipe(6,7). pipe(6,40). dem(6,40,28). dem(6,7,16).
junction(7). pipe(7,8). pipe(7,46). dem(7,46,26). dem(7,8,30).
junction(8). pipe(8,9). dem(8,9,33).
junction(9). pipe(9,10). pipe(9,41). dem(9,41,39). dem(9,10,53).
junction(10). pipe(10,11). dem(10,11,73).
junction(11). pipe(11,24). dem(11,24,48).
junction(12). pipe(12,13). pipe(12,15). dem(12,15,56). dem(12,13,53).
junction(13). pipe(13,14). pipe(13,16). dem(13,16,35). dem(13,14,39).
junction(14). pipe(14,17). dem(14,17,36).
junction(15). pipe(15,24). pipe(15,16). dem(15,24,41). dem(15,16,38).
junction(16). pipe(16,25). pipe(16,17). dem(16,25,38). dem(16,17,32).
junction(17). pipe(17,18). pipe(17,27). dem(17,27,50). dem(17,18,36).
junction(18). pipe(18,19). pipe(18,21). dem(18,21,26). dem(18,19,39).
junction(19). pipe(19,20). pipe(19,22). dem(19,22,38). dem(19,20,36).
junction(20). pipe(20,23). dem(20,23,33).
junction(21). pipe(21,22). pipe(21,28). dem(21,28,30). dem(21,22,25).
junction(22). pipe(22,23). pipe(22,29). dem(22,29,32). dem(22,23,35).
junction(23). pipe(23,30). dem(23,30,47).
junction(24). pipe(24,25). pipe(24,34). dem(24,34,38). dem(24,25,41).
junction(25). pipe(25,26). dem(25,26,49).
junction(26). pipe(26,27). pipe(26,35). dem(26,35,45). dem(26,27,53).
junction(27). pipe(27,28). dem(27,28,50).
junction(28). pipe(28,29). pipe(28,36). dem(28,36,37). dem(28,29,37).
junction(29). pipe(29,30). pipe(29,31). dem(29,31,47). dem(29,30,44).
junction(30). pipe(30,33). pipe(30,32). dem(30,33,40). dem(30,32,42).
junction(31). pipe(31,38). pipe(31,32). dem(31,38,46). dem(31,32,45).
junction(32). pipe(32,39). pipe(32,33). dem(32,39,27). dem(32,33,28).
junction(33). pipe(33,40). dem(33,40,35).
junction(34). pipe(34,35). pipe(34,41). dem(34,41,49). dem(34,35,45).
junction(35). pipe(35,36). pipe(35,42). dem(35,42,58). dem(35,36,39).
junction(36). pipe(36,37). pipe(36,43). dem(36,43,40). dem(36,37,43).
junction(37). pipe(37,38). pipe(37,44). dem(37,44,42). dem(37,38,42).
junction(38). pipe(38,39). dem(38,39,28).
junction(39). pipe(39,40). pipe(39,45). dem(39,45,35). dem(39,40,34).
junction(40). pipe(40,46). dem(40,46,38).
junction(41). pipe(41,42). dem(41,42,62).
junction(42). pipe(42,43). dem(42,43,59).
junction(43). pipe(43,44). dem(43,44,39).
junction(44). pipe(44,45). dem(44,45,39).
junction(45). pipe(45,46). dem(45,46,39).
junction(46).

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

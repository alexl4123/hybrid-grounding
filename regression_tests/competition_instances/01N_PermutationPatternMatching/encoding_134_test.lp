kval(1).
kval(N+1) :- kval(N), N < L, patternlength(L). 
1 <= { subt(K,I,E) : t(I,E) } <= 1 :- kval(K), patternlength(L).
:- subt(K1,I1,_), subt(K2,I2,_), K1<K2, I1 >= I2.

solution(K,E) :- subt(K,_,E).

% Check whether the subsequence is a matching
:- solution(K1,ET1), solution(K2,ET2), p(K1,EP1), p(K2,EP2), ET1 < ET2, EP1 >= EP2.

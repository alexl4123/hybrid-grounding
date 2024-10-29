t(1,16).
t(2,19).
t(3,5).
t(4,12).
t(5,11).
t(6,20).
t(7,9).
t(8,18).
t(9,8).
t(10,15).
t(11,7).
t(12,17).
t(13,1).
t(14,3).
t(15,2).
t(16,10).
t(17,4).
t(18,13).
t(19,6).
t(20,14).
p(1,4).
p(2,2).
p(3,1).
p(4,3).
p(5,5).
p(6,6).
patternlength(6).

#program rules.

% Example Input
% t(1,5).
% t(2,3).
% t(3,1).
% t(4,4).
% t(5,2).
% p(1,2).
% p(2,3).
% p(3,1).
% patternlength(3).

% Guess suitable subsequence

%1 <= { subt(K,I,E) : t(I,E) } <= 1 :- K=1..L, patternlength(L).

kval(1).
kval(N+1) :- kval(N), N < L, patternlength(L). 
1 <= { subt(K,I,E) : t(I,E) } <= 1 :- kval(K), patternlength(L).
:- subt(K1,I1,_), subt(K2,I2,_), K1<K2, I1 >= I2.

solution(K,E) :- subt(K,_,E).

% Check whether the subsequence is a matching
:- solution(K1,ET1), solution(K2,ET2), p(K1,EP1), p(K2,EP2), ET1 < ET2, EP1 >= EP2.



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

kval(K) :- p(K,P), patternlength(L), K <= L.
pair(K1,K2) :- kval(K1), kval(K2), p(K1,P1), p(K2,P2), P1 <= P2.

{ geq(K,I) } :- kval(K), t(I,E).
:- kval(K), t(I,E), geq(K,I+1), not geq(K,I).
:- kval(K), t(I,E), geq(K-1,I), not geq(K,I+1).
:- kval(K), not geq(K,K).

solution(K,E) :- kval(K), t(I,E), geq(K,I), not geq(K,I+1).
:- pair(K1,K2), solution(K1,E1), solution(K2,E2), E2 < E1.


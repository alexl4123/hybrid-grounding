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

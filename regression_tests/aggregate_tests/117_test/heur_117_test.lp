
manAssignsScore(1,1,1).
manAssignsScore(1,1,2).
manAssignsScore(1,1,3).
manAssignsScore(1,1,4).
manAssignsScore(1,1,5).
manAssignsScore(1,1,6).
manAssignsScore(1,1,7).
manAssignsScore(1,1,8).
manAssignsScore(1,1,9).
womanAssignsScore(1,1,1).
womanAssignsScore(1,1,2).
womanAssignsScore(1,1,3).
womanAssignsScore(1,1,4).
womanAssignsScore(1,1,5).
womanAssignsScore(1,1,6).
womanAssignsScore(1,1,7).
womanAssignsScore(1,1,8).
womanAssignsScore(1,1,9).


% guess matching
match(M,W) :- manAssignsScore(M,_,_), womanAssignsScore(W,_,_), not nonMatch(M,W).
nonMatch(M,W) :- manAssignsScore(M,_,_), womanAssignsScore(W,_,_), not match(M,W).
% no singles
jailed(M) :- match(M,_).
:- manAssignsScore(M,_,_), not jailed(M).
% strong stability condition
:- match(M,W1), manAssignsScore(M,W,Smw), W1 != W, manAssignsScore(M,W1,Smw1), Smw > Smw1, match(M1,W), womanAssignsScore(W,M,Swm), womanAssignsScore(W,M1,Swm1), Swm >= Swm1.

:- 2 <= #count{W : match(M1,W), match(M2,W), match(M3,W), M1 != M2, M1 != M3, M2 != M3}.
:- 2 <= #count{M : match(M,W1), match(M,W2), match(M,W3), W1 != W2, W1 != W3, W2 != W3}.


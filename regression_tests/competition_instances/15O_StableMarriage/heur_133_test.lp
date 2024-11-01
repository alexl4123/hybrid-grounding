%instance number:0
manAssignsScore(1,1,20).
manAssignsScore(1,2,15).
manAssignsScore(1,3,30).
manAssignsScore(1,4,35).
manAssignsScore(2,1,50).
manAssignsScore(2,2,35).
manAssignsScore(2,3,15).
manAssignsScore(2,4,17).
manAssignsScore(3,1,50).
manAssignsScore(3,2,35).
manAssignsScore(3,3,15).
manAssignsScore(3,4,17).
manAssignsScore(4,1,50).
manAssignsScore(4,2,35).
manAssignsScore(4,3,15).
manAssignsScore(4,4,17).

womanAssignsScore(1,1,4).
womanAssignsScore(1,2,6).
womanAssignsScore(1,3,8).
womanAssignsScore(1,4,9).
womanAssignsScore(2,1,25).
womanAssignsScore(2,2,15).
womanAssignsScore(2,3,21).
womanAssignsScore(2,4,19).
womanAssignsScore(3,1,4).
womanAssignsScore(3,2,6).
womanAssignsScore(3,3,5).
womanAssignsScore(3,4,40).
womanAssignsScore(4,1,14).
womanAssignsScore(4,2,15).
womanAssignsScore(4,3,8).
womanAssignsScore(4,4,13).


% guess matching
match(M,W) :- manAssignsScore(M,_,_), womanAssignsScore(W,_,_), not nonMatch(M,W).
nonMatch(M,W) :- manAssignsScore(M,_,_), womanAssignsScore(W,_,_), not match(M,W).

% no polygamy
:- match(M1,W), match(M,W), M <> M1.
:- match(M,W), match(M,W1), W <> W1.

% no singles
jailed(M) :- match(M,_).
:- manAssignsScore(M,_,_), not jailed(M).

% strong stability condition
:- match(M,W1), manAssignsScore(M,W,Smw), W1 <> W, manAssignsScore(M,W1,Smw1),   Smw >  Smw1,
   match(M1,W), womanAssignsScore(W,M,Swm),        womanAssignsScore(W,M1,Swm1), Swm >= Swm1.

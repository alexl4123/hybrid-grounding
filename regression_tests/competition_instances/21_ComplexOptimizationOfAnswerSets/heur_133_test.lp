rule(pos(atom(cl(1,pos,43))),pos(conjunction(0))).
rule(pos(atom(cl(1,pos,169))),pos(conjunction(0))).
rule(pos(atom(cl(1,pos,174))),pos(conjunction(0))).
rule(pos(atom(cl(2,pos,61))),pos(conjunction(0))).
rule(pos(atom(cl(2,pos,172))),pos(conjunction(0))).
rule(pos(atom(cl(2,neg,169))),pos(conjunction(0))).
rule(pos(atom(cl(3,pos,70))),pos(conjunction(0))).
rule(pos(atom(cl(3,pos,118))),pos(conjunction(0))).
rule(pos(atom(cl(3,neg,61))),pos(conjunction(0))).
rule(pos(atom(cl(4,pos,97))),pos(conjunction(0))).
set(1,neg(atom(x(174)))).
set(1,neg(atom(x(169)))).
set(1,neg(atom(x(43)))).
rule(pos(atom(r(1))),pos(conjunction(1))).
set(2,pos(atom(x(169)))).
set(2,neg(atom(x(172)))).
set(2,neg(atom(x(61)))).
rule(pos(atom(r(2))),pos(conjunction(2))).
set(3,pos(atom(x(61)))).
set(3,neg(atom(x(118)))).
set(3,neg(atom(x(70)))).
rule(pos(atom(r(3))),pos(conjunction(3))).
set(4,pos(atom(x(70)))).
set(4,neg(atom(x(172)))).
set(4,neg(atom(x(97)))).
rule(pos(atom(r(4))),pos(conjunction(4))).
set(5,pos(atom(x(97)))).
set(5,pos(atom(x(70)))).
set(5,pos(atom(x(61)))).
rule(pos(atom(r(5))),pos(conjunction(5))).
set(6,pos(atom(x(169)))).
set(6,neg(atom(x(43)))).
set(6,neg(atom(x(172)))).
rule(pos(atom(r(6))),pos(conjunction(6))).
set(7,pos(atom(x(169)))).
set(7,neg(atom(x(144)))).
set(7,neg(atom(x(68)))).
rule(pos(atom(r(7))),pos(conjunction(7))).
set(8,neg(atom(x(144)))).
set(8,neg(atom(x(135)))).
set(8,neg(atom(x(48)))).
rule(pos(atom(r(8))),pos(conjunction(8))).
set(9,pos(atom(x(135)))).
set(9,pos(atom(x(68)))).
set(9,neg(atom(x(48)))).
rule(pos(atom(r(9))),pos(conjunction(9))).
set(10,pos(atom(x(48)))).
set(10,pos(atom(x(172)))).
set(10,pos(atom(x(68)))).
rule(pos(atom(r(10))),pos(conjunction(10))).
wlist(1,0,pos(atom(r(1))),1).
wlist(1,1,pos(atom(r(2))),1).
wlist(1,2,pos(atom(r(3))),1).
wlist(1,3,pos(atom(r(4))),1).
wlist(1,4,pos(atom(r(5))),1).
wlist(1,5,pos(atom(r(6))),1).
wlist(1,6,pos(atom(r(7))),1).
wlist(1,7,pos(atom(r(8))),1).
wlist(1,8,pos(atom(r(9))),1).
wlist(1,9,pos(atom(r(10))),1).
minimize(1,1).
optimize(1,1,incl).
%:-not hold(atom(r(6))),not hold(atom(r(4))),not hold(atom(r(2))),not hold(atom(r(0))).


eleb(P) :- rule(_,pos(P)).

nhold(conjunction(S)) :- eleb(conjunction(S)), not hold(P), set(S,pos(P)).
nhold(conjunction(S)) :- eleb(conjunction(S)),     hold(P), set(S,neg(P)).
 hold(conjunction(S)) :- eleb(conjunction(S)), not nhold(conjunction(S)).

hold(atom(A))                     :- rule(pos(atom(A)),   pos(B)), hold(B).
                                  :- rule(pos(false),     pos(B)), hold(B).
{ hold(P) : wlist(S,_,pos(P),_) } :- rule(pos(sum(_,S,_)),pos(B)), hold(B).

elem(E) :- eleb(E).
elem(E) :- rule(pos(E),_).
elem(P) :- rule(pos(sum(_,S,_)),_), wlist(S,_,pos(P),_).
elem(P) :- minimize(J,S),           wlist(S,_,pos(P),W).

supp(atom(A),B) :- rule(pos(atom(A)),   pos(B)).
supp(atom(A),B) :- rule(pos(sum(_,S,_)),pos(B)), wlist(S,_,pos(atom(A)),_).

supp_(atom(A))   :- supp(atom(A),B).

set(S) :- set(S,E).
fact(atom(A))   :- rule(pos(atom(A)),pos(conjunction(S))), not set(S).

true_(atom(A))                 :- fact(atom(A)).
true_(atom(A)) | fail(atom(A)) :- supp_(atom(A)), not fact(atom(A)).
                fail(atom(A)) :- elem(atom(A)), not supp_(atom(A)).

fail(false).

sett(S,0,P)    :- set(S,P).
sett(S,N+1,P2) :- sett(S,N,P1), sett(S,N,P2), P1 < P2.

setn(S,N,P) :- sett(S,N,P), not sett(S,N+1,P).
setn_(S,N)  :- setn(S,N,_).

true(conjunction(S),N+1) :- elem(conjunction(S)), setn_(S,N), not setn_(S,N+1).
true(conjunction(S),N)   :- elem(conjunction(S)), true_(P), setn(S,N,pos(P)), true(conjunction(S),N+1).
true(conjunction(S),N)   :- elem(conjunction(S)), fail(P), setn(S,N,neg(P)), true(conjunction(S),N+1).

true_(conjunction(S)) :- true(conjunction(S),0).
fail(conjunction(S)) :- elem(conjunction(S)), set(S,pos(P)), fail(P).
fail(conjunction(S)) :- elem(conjunction(S)), set(S,neg(N)), true_(N).

suppt(S,0,P)    :- supp(S,P).
suppt(S,N+1,P2) :- suppt(S,N,P1), suppt(S,N,P2), P1 < P2.

suppn(S,N,P) :- suppt(S,N,P), not suppt(S,N+1,P).
suppn_(S,N)  :- suppn(S,N,_).

suppf(S,N+1) :- suppn_(S,N), not suppn_(S,N+1).
suppf(S,N)   :- fail(P), suppn(S,N,P), suppf(S,N+1).

bot :- true_(atom(A)), suppf(atom(A),0).
bot :- rule(pos(H),pos(B)), true_(B), fail(H).

true_(atom(A)) :- supp_(atom(A)), not fact(atom(A)), bot.
fail(atom(A)) :- supp_(atom(A)), not fact(atom(A)), bot.

target(P,N) :- minimize(_,S), wlist(S,N,pos(P),_).
target_(N) :- target(P,N).

equal(N+1) :- target_(N), not target_(N+1).
equal(N) :- target(P,N), true_(P),     hold(P), equal(N+1).
equal(N) :- target(P,N), fail(P), not hold(P), equal(N+1).

bot :- equal(0).
bot :- target(P,_), true_(P), not hold(P).

:- not bot.

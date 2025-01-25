% splitting a formula into its subformulas
subformula2(X,F) :- ac(X,F),statement(X).
subformula2(X,F) :- subformula2(X,and(F,_)).
subformula2(X,F) :- subformula2(X,and(_,F)).
subformula2(X,F) :- subformula2(X,or(_,F)).
subformula2(X,F) :- subformula2(X,or(F,_)).
subformula2(X,F) :- subformula2(X,neg(F)).
subformula2(X,F) :- subformula2(X,xor(F,_)).
subformula2(X,F) :- subformula2(X,xor(_,F)).
subformula2(X,F) :- subformula2(X,imp(F,_)).
subformula2(X,F) :- subformula2(X,imp(_,F)).
subformula2(X,F) :- subformula2(X,iff(F,_)).
subformula2(X,F) :- subformula2(X,iff(_,F)).
subformula(F) :- subformula2(_,F).

% decide whether a subformula is an atom or not
noatom(F) :- subformula(F), subformula(F1), subformula(F2), F=and(F1,F2).
noatom(F) :- subformula(F), subformula(F1), subformula(F2), F=or(F1,F2).
noatom(F) :- subformula(F), subformula(F1), F=neg(F1).
noatom(F) :- subformula(F), subformula(F1), subformula(F2), F=xor(F1,F2).
noatom(F) :- subformula(F), subformula(F1), subformula(F2), F=imp(F1,F2).
noatom(F) :- subformula(F), subformula(F1), subformula(F2), F=iff(F1,F2).

atom(X) :- subformula(X), not noatom(X).
atom(X) :- subformula(X), X=c(v).
atom(X) :- subformula(X), X=c(f).

% check whether an interpretation is a model or not at a specific iteration
ismodel(X,I) :- atom(X), in(X,I).
ismodel(X,I) :- atom(X), X=c(v), iteration(I).
ismodel(F,I) :- subformula(F), subformula(F1), F=neg(F1), nomodel(F1,I).
ismodel(F,I) :- subformula(F), F=and(F1,F2), ismodel(F1,I), ismodel(F2,I).
ismodel(F,I) :- subformula(F), subformula(F1), subformula(F2), F=or(F1,F2), ismodel(F1,I).
ismodel(F,I) :- subformula(F), subformula(F1), subformula(F2), F=or(F1,F2), ismodel(F2,I).
ismodel(F,I) :- subformula(F), F=xor(F1,F2), ismodel(F1,I), nomodel(F2,I).
ismodel(F,I) :- subformula(F), F=xor(F1,F2), ismodel(F2,I), nomodel(F1,I).
ismodel(F,I) :- subformula(F), subformula(F1), subformula(F2), F=imp(F1,F2), nomodel(F1,I).
ismodel(F,I) :- subformula(F), F=imp(F1,F2), ismodel(F1,I), ismodel(F2,I).
ismodel(F,I) :- subformula(F), F=iff(F1,F2), ismodel(F1,I), ismodel(F2,I).
ismodel(F,I) :- subformula(F), F=iff(F1,F2), nomodel(F1,I), nomodel(F2,I).

nomodel(X,I) :- atom(X), out(X,I).
nomodel(X,I) :- atom(X), X=c(f), iteration(I).
nomodel(F,I) :- subformula(F), subformula(F1), F=neg(F1), ismodel(F1,I).
nomodel(F,I) :- subformula(F), subformula(F1), subformula(F2), F=and(F1,F2), nomodel(F1,I).
nomodel(F,I) :- subformula(F), subformula(F1), subformula(F2), F=and(F1,F2), nomodel(F2,I).
nomodel(F,I) :- subformula(F), F=or(F1,F2), nomodel(F1,I), nomodel(F2,I).
nomodel(F,I) :- subformula(F), F=xor(F1,F2), ismodel(F1,I), ismodel(F2,I).
nomodel(F,I) :- subformula(F), F=xor(F1,F2), nomodel(F1,I), nomodel(F2,I).
nomodel(F,I) :- subformula(F), F=imp(F1,F2), ismodel(F1,I), nomodel(F2,I).
nomodel(F,I) :- subformula(F), F=iff(F1,F2), nomodel(F1,I), ismodel(F2,I).
nomodel(F,I) :- subformula(F), F=iff(F1,F2), nomodel(F2,I), ismodel(F1,I).

% get the number of statements and create an ordering
snum(I) :- I = #count{Y : statement(Y)}.
iteration(I) :- snum(J), I=J-1.
iteration(I) :- iteration(J), I=J-1, I>=0.

% create undecided set of variables at the starting point of the function
undec(X,I) :- snum(I), statement(X).

% iterate the function one step further, and guess an additional element for A or R
inA(X,I) :- inA(X,J), J=I+1, iteration(I).
inR(X,I) :- inR(X,J), J=I+1, iteration(I).
select(X,I) :- not deselect(X,I), statement(X), iteration(I), undec(X,J), J=I+1.
deselect(X,I) :- not select(X,I), statement(X), iteration(I), undec(X,J), J=I+1.
:- #count { J : select(J,I)} > 1, iteration(I).
undec(X,I) :- iteration(I), undec(X,J), J=I+1, deselect(X,I).
% check whether the selected element is in A or not.
in(X,I) | out(X,I) :- undec(X,J), J=I+1, iteration(I).
in(X,I) :- iteration(I), J=I+1, inA(X,J).
out(X,I) :- iteration(I), J=I+1, inR(X,J).

okA(I) :- select(X,I), ac(X,F), ismodel(F,I).
okA(I) :- #count{J : select(J,I)} = 0, iteration(I).
inA(X,I) :- okA(I), select(X,I).

in(X,I) :- okA(I), undec(X,J), J=I+1, iteration(I).
out(X,I) :- okA(I), undec(X,J), J=I+1, iteration(I).


% check whether the selected element is in R or not.
okR(I) :- select(X,I), ac(X,F), nomodel(F,I), not okA(I).
in(X,I) :- okR(I), undec(X,J), J=I+1, iteration(I).
out(X,I) :- okR(I), undec(X,J), J=I+1, iteration(I).
inR(X,I) :- okR(I), select(X,I).

ok(I) :- okA(I).
ok(I) :- okR(I).

:- not ok(I), iteration(I).

accept(X) :- inA(X,0).
reject(X) :- inR(X,0).

:~ statement(X), not accept(X). [1@2,X]
:~ statement(X), not reject(X). [1@1,X]
%#maximize [accept(X)@2].
%#maximize [reject(X)@1].

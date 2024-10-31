ysucc(0,1).
ysucc(1,2).
ysucc(2,3).
ysucc(3,4).
ysucc(4,5).
ysucc(5,6).
ysucc(6,7).
ysucc(7,8).
ysucc(8,9).
ysucc(9,10).
bottle(1,9,59).
bottle(2,140,47).
bottle(3,135,140).
bottle(4,108,31).
bottle(5,86,72).
bottle(5,86,71).
bottle(6,64,59).
bottle(6,64,60).
bottle(8,4,116).
bottle(8,5,116).
bottle(8,4,115).
bottle(9,146,29).
bottle(10,56,134).


row(B,Y) :- bottle(B,X,Y).

{ fill(B,Y) } :- row(B,Y).
:- ysucc(Y1,Y2), fill(B,Y1), row(B,Y2), not fill(B,Y2).

filled(X,Y) :- bottle(B,X,Y), fill(B,Y).
:- xvalue(Y,V), not #count{ X : filled(X,Y) } = V.
:- yvalue(X,V), not #count{ Y : filled(X,Y) } = V.

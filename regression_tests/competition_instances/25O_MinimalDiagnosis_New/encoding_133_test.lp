%%%%%%%%%%%%%%%%%
% Preprocessing %
%%%%%%%%%%%%%%%%%

sign(m). sign(p).

diff(V,V) :- edge(V,V), obs_elabel(V,V,m), not obs_elabel(V,V,p).
diff(U,V) :- edge(U,V), obs_elabel(U,V,m), not obs_elabel(U,V,p), obs_vlabel(U,S), obs_vlabel(V,S).
diff(U,V) :- edge(U,V), obs_elabel(U,V,p), not obs_elabel(U,V,m), obs_vlabel(U,S), obs_vlabel(V,T), S != T.

nontriv(V) :- vertex(V), not input(V), edge(U,V), not diff(U,V).
trivial(V) :- vertex(V), not input(V), not nontriv(V).

btedge(W,U,V) :- vertex(V), not input(V), not trivial(V), edge(W,V), edge(U,V), edge(Z,V), W < Z, Z < U.
ntedge(W,U,V) :- vertex(V), not input(V), not trivial(V), edge(W,V), edge(U,V), W < U, not btedge(W,U,V).
nfirst(U,V)   :- ntedge(W,U,V).
nlast(W,V)    :- ntedge(W,U,V).
first(U,V)    :- vertex(V), not input(V), not trivial(V), edge(U,V), not nfirst(U,V).
last(U,V)     :- vertex(V), not input(V), not trivial(V), edge(U,V), not nlast(U,V).


%%%%%%%%%%%%%
% Generator %
%%%%%%%%%%%%%

active(V)   :- vertex(V), not input(V), not inactive(V).
inactive(V) :- vertex(V), not input(V), not active(V).
inactive(V) :- vertex(V), not input(V), active(W), trivial(W), V != W.
singleton   :- active(V), trivial(V).

:- trivial(V), not singleton.

reach(U,V) :- edge(U,V), active(V), not trivial(V).
reach(V,U) :- edge(U,V), active(V), not trivial(V),                        not obs_vlabel(U,p), not obs_vlabel(U,m).
reach(U,W) :- edge(U,V), active(V), not trivial(V), reach(V,W), vertex(W).
reach(V,W) :- edge(U,V), active(V), not trivial(V), reach(U,W), vertex(W), not obs_vlabel(U,p), not obs_vlabel(U,m).

:- active(V), not trivial(V), active(W), not trivial(W), not reach(V,W).

aedge(V) :- vertex(V), not input(V), not trivial(V), not obs_vlabel(V,p), not obs_vlabel(V,m), active(W), edge(V,W).

:- active(V), not trivial(V), not obs_vlabel(V,p), not obs_vlabel(V,m), not aedge(V).


%%%%%%%%%%%%%%%%%%%%%%
% Inconsistency Test %
%%%%%%%%%%%%%%%%%%%%%%

vlabel(V,p)   | vlabel(V,m)   :- active(V),    not trivial(V),               not obs_vlabel(V,p),   not obs_vlabel(V,m).
vlabel(U,p)   | vlabel(U,m)   :- active(V),    not trivial(V), edge(U,V),    not obs_vlabel(U,p),   not obs_vlabel(U,m).
llabel(U,V,p) | llabel(U,V,m) :- active(V),    not trivial(V), edge(U,V),    not obs_elabel(U,V,p), not obs_elabel(U,V,m).

vlabel(V,S)   :- vertex(V), obs_vlabel(V,S),   not trivial(V), not input(V).
vlabel(U,S)   :- edge(U,V), obs_vlabel(U,S),   not trivial(V), not input(V).
llabel(U,V,S) :- edge(U,V), obs_elabel(U,V,S), not trivial(V), not input(V).

oppo(U,V)     :- llabel(U,V,m), vlabel(U,S),   not trivial(V), not input(V), not obs_elabel(U,V,p), vlabel(V,S).
oppo(U,V)     :- llabel(U,V,p), vlabel(U,S),   not trivial(V), not input(V), not obs_elabel(U,V,m), vlabel(V,T), S != T.

coppo(U,V)    :- oppo(U,V), first(U,V).
coppo(U,V)    :- oppo(U,V), coppo(W,V), ntedge(W,U,V).

bot           :- singleton.
bot           :- active(V), coppo(U,V), last(U,V).

vlabel(V,S)   :- bot, vertex(V), sign(S),      not trivial(V), not input(V), not obs_vlabel(V,p),   not obs_vlabel(V,m).
vlabel(U,S)   :- bot, edge(U,V), sign(S),      not trivial(V), not input(V), not obs_vlabel(U,p),   not obs_vlabel(U,m).
llabel(U,V,S) :- bot, edge(U,V), sign(S),      not trivial(V), not input(V), not obs_elabel(U,V,p), not obs_elabel(U,V,m).

:- not bot.


%%%%%%%%%%%%%%%%%%%
% Minimality Test %
%%%%%%%%%%%%%%%%%%%

mvlabel(W,V,p)   :-            active(W), not trivial(V), not trivial(W), active(V), reach(V,W), reach(W,V), W != V, not mvlabel(W,V,m).
mvlabel(W,V,m)   :-            active(W), not trivial(V), not trivial(W), active(V), reach(V,W), reach(W,V), W != V, not mvlabel(W,V,p).
mvlabel(W,U,p)   :- edge(U,V), active(W), not trivial(V), not trivial(W), active(V), reach(V,W), reach(W,V), W != V, not mvlabel(W,U,m).
mvlabel(W,U,m)   :- edge(U,V), active(W), not trivial(V), not trivial(W), active(V), reach(V,W), reach(W,V), W != V, not mvlabel(W,U,p).
mllabel(W,U,V,p) :- edge(U,V), active(W), not trivial(V), not trivial(W), active(V), reach(V,W), reach(W,V), W != V, not mllabel(W,U,V,m).
mllabel(W,U,V,m) :- edge(U,V), active(W), not trivial(V), not trivial(W), active(V), reach(V,W), reach(W,V), W != V, not mllabel(W,U,V,p).

mvlabel(W,V,S)   :- obs_vlabel(V,S),              vertex(W), not trivial(V), not trivial(W), not input(V), not input(W), W != V.
mvlabel(W,U,S)   :- obs_vlabel(U,S),   edge(U,V), vertex(W), not trivial(V), not trivial(W), not input(V), not input(W), W != V.
mllabel(W,U,V,S) :- obs_elabel(U,V,S), edge(U,V), vertex(W), not trivial(V), not trivial(W), not input(V), not input(W), W != V.

minfl(W,V,p) :- mvlabel(W,U,S), mllabel(W,U,V,S), W != V.
minfl(W,V,m) :- mvlabel(W,U,S), mllabel(W,U,V,T), W != V, S != T.

:- active(V), active(W), not trivial(V), not trivial(W), W != V, mvlabel(W,V,S), not minfl(W,V,S).


%%%%%%%%%%
% Output %
%%%%%%%%%%

% #hide.
% #show active(V).

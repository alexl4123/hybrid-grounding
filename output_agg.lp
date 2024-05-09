a(1).
a(2).
a(3).
c(4).
c(5).
r5_Y(5) | r5_Y(4).
r5_Y(5) :- sat.
r5_Y(4) :- sat.
sat_r5 :- r5_Y(5),body_count_ag0_0(5).
sat_r5 :- r5_Y(4),body_count_ag0_0(4).
sat_r5 :- r5_Y(5),not c(5).
sat_r5 :- r5_Y(4),not c(4).
domain_rule_5_variable_Y(5).
domain_rule_5_variable_Y(4).
{body_count_ag0_05(Y) : domain_rule_5_variable_Y(Y)} .
body_count_ag0_0(Y) :- body_count_ag0_05(Y).
r5_unfound(5) :- not c(5).
r5_unfound(4) :- not c(4).
b(X) :- a(X), 2 <= #count { Y: body_count_ag0_0(Y) }.
:- not sat.
sat :- sat_r5.
:- body_count_ag0_05(5), #sum{1,0 : r5_unfound(5)} >=1 .
:- body_count_ag0_05(4), #sum{1,0 : r5_unfound(4)} >=1 .
dom(1).
dom(2).
dom(3).
dom(4).
dom(5).
#show a/1.
#show c/1.
#show b/1.
#show body_count_ag0_0/1.

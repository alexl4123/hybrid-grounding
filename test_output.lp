a(1).
a(2).
a(3).
r3_X(2) | r3_X(3) | r3_X(1).
r3_X(2) :- sat.
r3_X(3) :- sat.
r3_X(1) :- sat.
sat_r3 :- r3_X(2),b(2).
sat_r3 :- r3_X(3),b(3).
sat_r3 :- r3_X(1),b(1).
sat_r3 :- r3_X(2),not a(2).
sat_r3 :- r3_X(3),not a(3).
sat_r3 :- r3_X(1),not a(1).
domain_rule_3_variable_X(2).
domain_rule_3_variable_X(3).
domain_rule_3_variable_X(1).
{b3(X) : domain_rule_3_variable_X(X)} .
b(X) :- b3(X).
r3_unfound(2) :- not a(2).
r3_unfound(3) :- not a(3).
r3_unfound(1) :- not a(1).
:- not sat.
sat :- sat_r3.
:- b3(2), #sum{1,0 : r3_unfound(2)} >=1 .
:- b3(3), #sum{1,0 : r3_unfound(3)} >=1 .
:- b3(1), #sum{1,0 : r3_unfound(1)} >=1 .
dom(1).
dom(2).
dom(3).
#show b/1.
#show a/1.

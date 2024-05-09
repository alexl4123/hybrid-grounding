a(1).
a(2).
a(3).
c(4).
c(5).
r5_X(3) | r5_X(1) | r5_X(2).
r5_X(3) :- sat.
r5_X(1) :- sat.
r5_X(2) :- sat.
r5_Y_0(4) | r5_Y_0(5).
r5_Y_0(4) :- sat.
r5_Y_0(5) :- sat.
r5_Y_1(4) | r5_Y_1(5).
r5_Y_1(4) :- sat.
r5_Y_1(5) :- sat.
sat_r5 :- r5_Y_0(1),r5_Y_1(1).
sat_r5 :- r5_Y_0(2),r5_Y_1(2).
sat_r5 :- r5_Y_0(3),r5_Y_1(3).
sat_r5 :- r5_Y_0(4),r5_Y_1(4).
sat_r5 :- r5_Y_0(5),r5_Y_1(5).
sat_r5 :- r5_X(3),b(3).
sat_r5 :- r5_X(1),b(1).
sat_r5 :- r5_X(2),b(2).
sat_r5 :- r5_X(3),not a(3).
sat_r5 :- r5_X(1),not a(1).
sat_r5 :- r5_X(2),not a(2).
sat_r5 :- r5_Y_1(4),not c(4).
sat_r5 :- r5_Y_1(5),not c(5).
sat_r5 :- r5_Y_0(4),not c(4).
sat_r5 :- r5_Y_0(5),not c(5).
domain_rule_5_variable_X(3).
domain_rule_5_variable_X(1).
domain_rule_5_variable_X(2).
{b5(X) : domain_rule_5_variable_X(X)} .
b(X) :- b5(X).
domain_rule_5_variable_Y_0(4).
domain_rule_5_variable_Y_0(5).
1<={r5f_Y_0(Y_0):domain_rule_5_variable_Y_0(Y_0)}<=1.
domain_rule_5_variable_Y_1(4).
domain_rule_5_variable_Y_1(5).
1<={r5f_Y_1(Y_1):domain_rule_5_variable_Y_1(Y_1)}<=1.
r5_unfound_ :-  r5f_Y_0(4),r5f_Y_1(4).
r5_unfound_ :-  r5f_Y_0(5),r5f_Y_1(5).
r5_unfound(3) :- not a(3).
r5_unfound(1) :- not a(1).
r5_unfound(2) :- not a(2).
r5_unfound_ :- r5f_Y_1(4), not c(4).
r5_unfound_ :- r5f_Y_1(5), not c(5).
r5_unfound_ :- r5f_Y_0(4), not c(4).
r5_unfound_ :- r5f_Y_0(5), not c(5).
:- not sat.
sat :- sat_r5.
:- b, #sum{1,0 : r5_unfound_} >=1 .
:- b5(3), #sum{1,0 : r5_unfound(3); 1,1 : r5_unfound_} >=1 .
:- b5(1), #sum{1,0 : r5_unfound(1); 1,1 : r5_unfound_} >=1 .
:- b5(2), #sum{1,0 : r5_unfound(2); 1,1 : r5_unfound_} >=1 .
dom(1).
dom(2).
dom(3).
dom(4).
dom(5).
#show a/1.
#show b/1.
#show c/1.

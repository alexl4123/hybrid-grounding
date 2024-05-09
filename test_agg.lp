% This is another very simple test file, for our valuable reviewers.

a(1).
a(2).
a(3).
c(4).
c(5).

#program rules.
b(X) :- a(X), #count{Y:c(Y)} >= 2.


# Closing unwind and impact decay

Status. Execution implementation under test before the development
study. Hypothesis commit `e3463b5` fixes the candidate, the
position size, the early exit policy, periods and advancement
gates. The formula and candidate extraction are implemented in
`formula.py`.

The candidate combines the remaining discount from the last
regular-session close with reduced price impact in the latest
three-minute window compared with the preceding three-minute
window. It requires activity to persist and the price to begin
recovering. The formula uses turnover in minutes with falling
closes as a proxy. The initiator of each trade is unobserved.

Synthetic tests verify the numerical definition, volume-scale
invariance, invalid and missing data, the first eligible minute,
exclusion of the auction boundary, regular-session rally
availability, early closes and replay with future bars removed.
Repository rules, Ruff and the import contracts pass. These
checks establish calculation behavior. Performance is untested.

The default engine fills during the regular session. The owner
explicitly authorized GPT to implement the scoped extended-hours
changes, recorded in OWNERS.md. The opt-in `extended_v1` path
uses opening-only capped execution, next-clock-minute entry
expiry, timed retrying sell limits, participation and capital
reservations. Both baseline and stress must fit each cap.
The development study uses those same fills and costs. The request is in
`docs/requests/2026-11-17-extended-hours-execution.md`.
The explicit reassignment supersedes the earlier lane restriction
for this change. Unresolved positions remain visible in the
run store and invalidate advancement; no regular-session auction
price settles an after-hours position.

The existing minute build contains extended-hours bars. The
data need no rebuild. Today's motivating example belongs to
the sealed period. Development remains 2003-09-10 through
2016-12-30 and the candidate's possible validation remains
2017-01-03 through 2023-11-08.

The follow-up numerical audit found that exact inclusive price
boundaries could be rejected by binary rounding. Regression
tests now cover the exact discount, one-cent uptick and initial
decline boundaries, with nearby ineligible values excluded.
The candidate metadata marks it as ready for the development study
once the clean commit is complete. The complete repository test
suite, focused extended-execution tests, Ruff and import contracts
pass. The run-store integration tests exercise both completed and
unresolved positions in study and portfolio mode using synthetic
bars. No empirical run has started yet.
Claude's new after-hours research at `2cc002a` supplies related
prior looks and retains the registered runner's regular-session
fill boundary. Historical performance for this candidate
remains unmeasured.

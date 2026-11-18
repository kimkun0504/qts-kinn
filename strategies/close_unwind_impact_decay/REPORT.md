# Closing unwind and impact decay

Status. Awaiting the platform execution contract before empirical
testing. Hypothesis commit `e3463b5` fixes the candidate, the
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

The existing engine clamps fills to the regular session and
treats its limit orders as passive. The proposed after-hours
policy needs session bounds and aggressive-limit cost and fill
semantics. The concrete request is in
`docs/requests/2026-11-17-extended-hours-execution.md`.
The original owner instructions assign platform modules to
Claude and prohibit GPT edits under `src/kinn/`. Platform
support from the lane owner or an explicit scoped reassignment
is needed to execute the registered test.

The existing minute build contains extended-hours bars. The
data need no rebuild. Today's motivating example belongs to
the sealed period. Development remains 2003-09-10 through
2016-12-30 and the candidate's possible validation remains
2017-01-03 through 2023-11-08.

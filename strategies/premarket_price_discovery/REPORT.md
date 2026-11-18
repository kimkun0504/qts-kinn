# Distributed premarket price discovery

Status: implementation under test. The hypothesis was committed
at `57c701d` before any empirical run. There is one signal and
one scheduled thirty-minute liquidation policy, using the tested
`extended_v1` profile and the unchanged gates in HYPOTHESIS.md.

The score combines log price progress, path efficiency and
turnover breadth. It uses completed premarket bars and prior
session liquidity only. It cannot infer news content or who is
trading. A good mathematical definition is not evidence of a
profitable market mechanism.

The signal's mathematical tests, concentration and choppiness
checks, missing-minute and liquidity rejections, full prefix
replay, early-close exclusion, isolated CLI loading and simulated
premarket entry and liquidation pass. Execution regression tests,
repository rules, Ruff and import contracts pass. No performance
result is available yet.

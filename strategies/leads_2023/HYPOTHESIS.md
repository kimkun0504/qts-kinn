# The 2023 check for the leads that could be paper-traded

Written 2026-11-17 23:03 ET, before any of it is looked at. Four results of 17 November failed their tests
on steadiness but stayed positive in most years. None passed, so none was entitled to the 2023
check (January to 13 October 2023), and for each of them 2023 has not been looked at. Before
any is proposed to the owner as a paper trade beside the earnings rule, each is read once on
2023, the most recent year on disk, with the rule it was tested with, unchanged:

1. **after_hours short:** $300M to $2B, down 15% or more half an hour after a results 8-K
   accepted after the close; sold short at the low of the next minute; bought back at the next
   open (and, shown, at the next close).
2. **after_hours long, resting order:** $2B or more, up 5% to 15%; a buy resting at the
   reading price for 15 minutes; held to the close 15 sessions after (the cell that met the
   search bar and missed 2018–2022 on the t).
3. **closing_bids:** $2B or more, a limit-on-close order 2% under the 15:49 price; sold at the
   next open.
4. **rebalance_flows, first days:** own the side (SPY or TLT) that won the month, for the
   first two sessions of the next.

**Reading, set now:** a lead whose 2023 mean after costs is **above zero** is "not
contradicted" and can be proposed for paper trading, with its 2023 figure; one **below zero**
is "contradicted" and is not proposed. With 10 to 150 trades a lead, this can only rule a lead
out, not in. Each read is one trial, charged to its own family: 4 trials.

**Results, 2026-11-17 23:04 ET.** In REPORT.md. Each lead read once on 2023 (to 13 October):

1. after_hours short, $300M–$2B down 15%+: **+6.66%** a trade to the next open (44 trades,
   median +6.13%, t 2.89; worst −29%), +8.80% to the next close. **Not contradicted.**
2. after_hours long, resting order, $2B+ up 5–15%, 15 sessions: **−0.85%** (139 trades).
   **Contradicted.**
3. closing_bids, $2B+ at 2%: **+0.56%** (39 fills, median −0.14%). Not contradicted, weakly.
4. rebalance_flows first days: **+1.17%** a month (10 months, 8 positive). Not contradicted.

The first run of the script owned the losing side in line 4 by a sign error (it printed
−1.29%, which is the same reading turned over: −1.29% − 2 × 0.06% cost = the winner's +1.17%);
fixed and rerun; recorded here because the wrong figure was seen first. 4 trials.

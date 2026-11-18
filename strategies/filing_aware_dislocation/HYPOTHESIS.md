# Filing-aware dislocation reversal

Registered before any run. Large short-lived declines can reflect
temporary demand for liquidity or persistent repricing after
company information. An 8-K that became usable this morning
identifies a stock with a recent formal disclosure. Excluding
those stocks may remove some information-related declines.
A filing may also be routine, and new information can arrive
without appearing in this date-level input.

This is one variant of the existing size-peer reversal, charged
to `intraday_rebound`. The family began this research with 48
trials and now carries 103 including nine pre-registry looks.
The earlier rebound itself used an untyped filing-count screen.
Its role here is related prior research. The size-peer variant's
development result motivates retaining its signal. Its 2017–2023
owner-requested result and failed recent block remain in the
record. That later window has been read for other definitions
and cannot become an independent untouched test again.

## Frozen definition

- Use listed domestic common stocks including later delistings
  while eligible. Require at least 20 matched prior sessions,
  prior split-adjusted price of at least $2 and median prior
  20-session dollar turnover of at least $10 million. Candidates
  have positive prior capitalisation below $10 billion.
- Divide all such candidates at $2 billion prior market cap.
  For each group, compute synchronous median 15-minute and
  one-minute close-to-close returns from observed regular bars.
  Each median needs at least 31 valid member returns. The
  candidate can be included in its own group's median as in
  the earlier strategy. Keep the entire pre-open cohort in
  the reference calculation even when a stock has a filing.
- Declare `inputs = {"form8k": {"sessions": 1}}`. Exclude a
  candidate if an available report has at least one typed 8-K
  item, a filing date strictly before this session, and matching
  symbol and permaticker. Non-item vendor codes alone do not
  establish an 8-K in this rule. The platform input defines
  which filings first became usable today. A report dated today
  remains hidden. This rule cannot screen out today's releases.
- From 09:50 through 14:45 ET, take the first completed bar
  whose exact 15-minute return is at least 12 percentage points
  below its size group's median. Require at least +1% over the
  immediately preceding observed clock-minute close, and at
  least one percentage point more than the group's simultaneous
  one-minute median. Require $40,000 of signal-bar turnover,
  approximated by close times volume. All necessary stock
  endpoints must be actual bars.
- Buy at market on the next clock minute only, with expiry at
  that minute's end. Hold 120 clock minutes after first fill,
  then sell at market with Kinn's normal closing-auction fallback.
  Use $20,000 equity and buying power, $2,000 target per order,
  at most ten positions or reservations, 5% bar participation
  and `ibkr_pro_tiered`. Positions open and close on the same day.

There is one candidate. Use the stored unfiltered development
study `20261116T212516Z_gpt_relative_dislocation_reversal_eb5399da`
for comparison. The new event set must be an exact subset, with
matching decision minute, entry, target shares, costs and
two-hour returns for common stock-dates. Check this before
interpreting the comparison. Report the removed events and
the full and 2013–2016 means at both costs. No baseline rerun
is registered and the comparison cannot change the signal.

## Run sequence and gates

1. Run `development --study` on 2003-09-10 through 2016-12-30.
   Judge `r_120` only. Require 150 events on 90 dates and at
   least 40 events in 2013–2016. Require mean gross at least
   +3% and positive mean net at 2× both overall and in
   2013–2016, with a strictly positive full-period lower 95%
   day-clustered gross bound. Apply the same gates to the
   next-minute-only subset if the study admits late prints.
   Park after any miss.
2. After a committed develop verdict, run the `development`
   portfolio once on the same dates. Require 150 trades on
   90 dates and 40 in 2013–2016, mean net at least +2.5%
   at 1× and above +1% at 2× both overall and in 2013–2016,
   full-period daily annualised Sharpe above 1 at 2× and
   worst stressed end-of-day drawdown below $10,000.
3. If qualified, run frozen `validation` once from 2017-01-03
   through 2023-11-08. Require at least +3% mean net across
   all completed trades at 1× and +1% at 2× overall and
   separately from 2022-01-03 through 2023-11-08. Require
   150 trades on 90 dates overall and 50 trades on 30 dates
   in the recent block, positive mean net at 1× in 2017–2021,
   full-period daily annualised Sharpe above 1 at 2× and
   worst stressed end-of-day drawdown below $10,000.

Count every run. Report sample size, annual results, daily P&L
t-statistics and worst drawdown at both costs. Report winner
and loser averages separately for portfolio trades. The study
estimates both cost legs from entry-bar conditions. The
pre-open company category and market cap carry the build's
known limitations. The filing label is incomplete for real-time
news and a passive-limit fill is not required. The sealed
holdout is excluded.

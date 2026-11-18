# Earnings model: one model of the drift after results, with the new measurements

Written 2026-11-17 22:35 ET, before anything is fitted. The model of 16 November (family 16) was fitted
on every stock and every day and found nothing worth trading. The only drift that has held up
here comes after results in small companies. This fits one model there only, on the daily
features and on tonight's new measurements (the first and last half hour of the report
sessions), to see whether it finds trades the fixed rule A50 misses. Settled now, once; no
second configuration.

## Events and target

Every session flagged as A50's event (the first session after a results 8-K), 2005 to 13
October 2023, in listed common stock of $50M to $2B, $250,000 a day, a close of $1 or
more. Target: A50's trade on that signal (bought at the next open, sold at the close 15
sessions after the signal), after A50's costs, clipped to −50% and +100% for fitting only.

## Features (all known at the signal session's close)

ret1, ret2, ret5, ret20, ret60, ret250, dvr, dvr2, gap, loc, vol20, rsi2, the distance from
the 250-day high, log market value, log price, log dollar volume, netcash_price, ni_pos,
rev_yoy, earn_price, issue; and from minute bars the first-half-hour and last-half-hour
returns of the signal session and the session before.

## Fit and selection

LightGBM regression, fixed: 300 trees, learning rate 0.03, 15 leaves, at least 200 events a
leaf, 80% of features and events a tree, seed 7. **Fitted once on 2010–2017.** Applied to
2005–2009, 2018–2022 and 2023. For 2010–2017 itself the figures come from fitting on four
folds of its years and predicting the fifth (shown, not judged).

Two cells: a signal is taken when its prediction is in the **top 10%**, or the **top 5%**, of
the 2010–2017 out-of-fold predictions (the cut-offs fixed from those, then applied
unchanged).

## What counts

In **both** 2005–2009 and 2018–2022: 2% a trade after costs, a weekly t of 2.5, four years of
five positive; **and** the trades that are not A50 signals must make 1% a trade or more in
both, or the model has only found A50 again. 2023 is shown. **2 cells**, family
`earnings_model`. The holdout stays sealed.

**Results, 2026-11-17 22:36 ET.** In REPORT.md. **Both cells fail.** 149,263 events (1,560 of them A50
signals). Out of fold in 2010–2017 the top 10% made 0.99% a trade and the top 5% 1.72%
(t 3.9 and 4.0). Fitted on those years and applied elsewhere: 2005–2009 −0.69% and −1.18% a
trade (2008 −5%); 2018–2022 +1.52% and +2.08% with a weekly t of 0.83 and 0.36 (2019 −2% to
−3.5%, 2020 +6% to +8%); 2023 −2.8% and −2.9%. The trades it adds beyond A50 (95% of them)
are worth nothing steady. The half-hour features are not among its ten most used. 2 trials.

A data error found on the way: the panel's open for ASEI on 2007-08-09 is $0.01 (close
$63.46), which makes a 15-session trade from the session before read +711,200%. The panel
has 18 opens under 20% of the previous close on a session that closed within 20% of it, 4 of
them in stocks of $50M and $250,000 a day; any study buying or selling at the open should
drop them.

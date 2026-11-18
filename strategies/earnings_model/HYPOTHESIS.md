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

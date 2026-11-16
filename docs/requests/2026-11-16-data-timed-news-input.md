# Add a point-in-time news input to Kinn

The owner supplied a Massive ticker-news archive. A read-only inventory of complete
monthly partitions through October 2023 found `published_utc`, article ID, headline,
publisher and ticker tags. Coverage is thin before 2021, then substantial through the
last full pre-seal month. These are coverage observations. No returns were measured.
The separate processed research parquet contains date-level 8-K information.

## Availability

`published_utc` is the publisher's timestamp. Massive documents hourly endpoint updates
and publisher-dependent delays. The inspected archive has no first-received timestamp.
It can support a publication-time research model with a stated delay. A credible claim
about execution minutes after release needs a historical delivery timestamp from the
intended feed. Sentiment insights begin after the cutoff.
[Massive news coverage and delivery timing](https://massive.com/knowledge-base/article/how-far-back-does-massives-news-and-sentiment-data-go)

## Requested interface

- Build a versioned, pre-seal news input alongside the existing derived data. Keep the
  vendor archives read-only. Enforce the same date boundary at import and query time.
  Store unique ID, publisher, headline, ticker tags and publisher UTC timestamp.
  Preserve first receipt time when available. Resolve the symbol to the company on the
  publication date using the existing symbol history. Record the news build in run
  manifests.
- Expose the available prefix of each symbol's news through the standard session view.
  A strategy should be able to ask for events through a specific completed bar. Later
  events must also disappear when a session is replayed up to that bar. Test no future
  release, exchange timezone conversion, early close, correction or duplicate handling,
  and stale ticker reuse. Record explicitly which availability model each run uses.
- Keep the existing date-only filing fields for older strategies. The news input
  requires the data, engine and manifest lanes. Tests should also cover a session
  without a news build.

## Proposed first test

Test underreaction to a prior-session primary-source headline explicitly raising
company guidance. Start with single-ticker releases and a fixed, deterministic
headline rule. Evaluate a next-session entry after a conservative publication lag
and compare to price reaction on the same kinds of stocks. This tests a signed
catalyst. The existing timed-news outline studies the first article after a quiet
spell and release-time reaction. Publication time with a lag remains a proxy.

The usual 2003–2016 development window has very sparse coverage for this feed.
For a separate news-only test, request a development window in the covered part
of 2021 and reserve 2022-01-03 through 2023-11-08 as the chronological check. If the
owner prefers to count this with `recent_search` under decision 0019, disclose its
2018–2022 search period and reserve only the authorised 2023 check. Freeze one date
split and trial-family assignment before any return is observed. Keep the holdout
sealed either way.

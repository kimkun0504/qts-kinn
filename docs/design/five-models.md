# Design: five models, many alphas, any holding period

**Status: built 2026-11-15 (claude), after the owner approved it with these choices: long and
short; $25,000; rebalance rhythm configurable; a published signal first; optimizer from the
start. The section "As built" at the end lists what differs from the proposal below.**

## Why

Kinn today is an intraday platform: a strategy emits buy signals, each becomes one fixed-size
order, and every position is closed by the end of the day. That is enough for the rebound work and
not enough for the project's aim: alpha, risk, transaction cost, portfolio construction and
execution as separate models, with several alphas plugged in, including long-term ones.

| Model | Today | Gap |
|---|---|---|
| Alpha | `strategies/<name>`: intraday signals | no forecasts for multi-day holding; one alpha per run |
| Risk | fixed-dollar sizing, buying-power cap, three simple loss rules | no volatility or exposure model |
| Transaction cost | `kinn.costs`, calibrated, shared | calibrated for small intraday orders only |
| Portfolio construction | none | nothing turns several forecasts into one book |
| Execution | intraday fill rules on minute bars | nothing carries a position overnight |

## The shape proposed

One loop per session, five models with one job each, and data contracts between them:

```
alphas ──forecasts──▶ portfolio construction ──targets──▶ execution ──fills──▶ book
                         ▲            ▲                       ▲
                    risk model    cost model            minute bars
```

1. **Alpha** says what it expects: a score per stock, with a horizon and the time it was known.
   It never sizes, never trades, never sees the book.
2. **Risk model** says how risky each stock and the book are: volatility, correlation, exposures.
3. **Cost model** says what a trade of a given size would cost.
4. **Portfolio construction** combines forecasts, risk and costs under constraints into target
   holdings. This is the only place where alphas meet.
5. **Execution** turns the change in targets into orders and simulates their fills.

The **book** (positions, cash, P&L) is the state carried from one session to the next.

## Contracts (the part that makes additions cheap)

Each model is a small Python `Protocol` in the platform; implementations are plain classes. No
plugin registry: a book's config names the classes it uses.

```python
@dataclass(frozen=True)
class Forecast:  # kinn.core.types
    day: date  # the session it is for
    permaticker: int
    score: float  # expected excess return over the horizon, or a rank
    horizon_days: int
    alpha: str  # which alpha produced it


class Alpha(Protocol):  # kinn.alpha
    name: str
    universe: Universe
    features: Sequence[Feature]  # each declares when it is available

    def forecasts(self, view: DailyView) -> list[Forecast]: ...


class RiskModel(Protocol):  # kinn.risk
    def estimate(self, view: DailyView) -> RiskEstimate: ...  # vol per stock, covariance or factors


class PortfolioConstructor(Protocol):  # kinn.portfolio
    def targets(
        self,
        forecasts: list[Forecast],
        book: Book,
        risk: RiskEstimate,
        costs: CostModel,
        limits: Limits,
    ) -> list[Target]: ...  # permaticker, shares


class ExecutionPolicy(Protocol):  # kinn.execution
    def orders(self, targets: list[Target], book: Book) -> list[Order]: ...  # when and how
```

- `DailyView` is the daily counterpart of today's `DayView`: only what was known before the open
  (the panel's `_prev` columns, point-in-time fundamentals, history up to yesterday). The same
  availability rule and the same replay check against lookahead apply.
- The existing intraday strategies keep working unchanged. An intraday strategy is, in these
  terms, an alpha with its own execution inside one session.

## The daily engine (`kinn.engine.daily`)

For each session, in order:

1. Apply corporate actions to the book (splits, cash dividends, delistings at their last price).
2. Build the `DailyView`; each alpha returns forecasts; the risk model returns its estimate.
3. Portfolio construction returns targets; execution returns orders.
4. **Fills are simulated on that session's minute bars with the existing fill rules** (open
   auction, close auction, or spread over the day with the participation cap). This reuses
   `kinn.engine.intraday` rather than assuming a daily price, so costs stay honest.
5. Mark the book at the official close; record positions, exposures, turnover and P&L.

Because the book carries over, sessions are no longer independent. Runs stay resumable by saving
the book at each month end and continuing from the last saved month.

## Starting implementations (simple first, one of each)

| Model | First version | Later, when earned |
|---|---|---|
| Alpha | one long-term alpha chosen by the owner | several, combined |
| Risk | per-stock volatility (60-day), sector and size exposures from the panel | a factor model |
| Costs | today's model plus auction and multi-day impact calibration; borrow cost for shorts | calibration from the quote sample |
| Portfolio | top-N by combined score, volatility-scaled, with position, sector and turnover limits | an optimizer (cvxpy) |
| Execution | market-on-close, and a spread-over-the-day policy | limit-order policies |

## What carries over unchanged

Data layer and holdout seal; cost model interface; `kinn run`, run folders and manifests; trial
counting by family; Deflated Sharpe and PBO; the Workbench (it gains positions and exposure
views); the canaries.

## What must be added to the data layer

- **Total-return accounting:** dividends and delisting proceeds from Sharadar ACTIONS.
- **Point-in-time fundamentals:** Sharadar SF1 keyed by the date each filing became available.
- **Borrow and short rules**, if the book is long-short.

## How alphas and books are told apart

- An alpha is a folder `strategies/<name>/` with `kind: forecast` in `strategy.yaml`, its own
  `HYPOTHESIS.md`, `REPORT.md` and trial family.
- A **book** is a config under `books/<name>.yaml`: which alphas with what weights, which risk
  model, constructor, execution policy, limits and account size.
- A run records the book and every alpha in it. Trials are charged to each alpha's family and to
  the book's family, so adding an alpha to a book cannot hide a search.

## Scaling

- **More alphas:** a new folder; no platform change.
- **More agents:** unchanged (worktrees, lanes, manifests as the source of truth).
- **More runs:** the Workbench reads the registry's DuckDB index instead of every manifest once
  there are thousands.
- **More data:** builds stay versioned and partitioned; the daily engine reads the daily panel
  (26 million rows), not minute bars, except to simulate fills.

## New canaries

1. A forecast built from tomorrow's return must be caught.
2. A random book must lose its turnover costs.
3. The same book config must give the same positions every day.
4. A fundamental must not be visible before its filing date.

## Build order (each step ends with a checkpoint)

| Step | Delivers |
|---|---|
| D1 | `Forecast`, `Book`, `Target` types; `DailyView`; total-return panel; corporate-action tests |
| D2 | Daily engine with market-on-close execution; resumable; canaries 2 and 3 |
| D3 | Risk model v1 and portfolio constructor v1 with limits; canary 1 |
| D4 | Point-in-time fundamentals (SF1); canary 4 |
| D5 | First long-term alpha: hypothesis, backtest, report; Workbench positions and exposure views |

## Decisions needed from the owner before D1

1. **Long-only or long-short?** Long-short needs borrow costs and a margin model.
2. **Account size and number of holdings** for the first book.
3. **Rebalance rhythm:** daily, weekly or monthly.
4. **Which long-term alpha first.** The old build's mid-cap machine-learning model was its
   strongest result; a simpler, published signal would be a cleaner first test of the engine.
5. **Optimizer now or later.** The proposal is later: start with a ranked, volatility-scaled book.

## As built (2026-11-15)

| Model | Code | First version |
|---|---|---|
| Alpha | `kinn.alpha`, `strategies/<name>/alpha.py` | `momentum_12_1` |
| Risk | `kinn.risk.model` | single-index model, 252 sessions |
| Transaction cost | `kinn.costs` (unchanged) | auction fees and slippage; borrow fee on shorts |
| Portfolio construction | `kinn.portfolio` | mean-variance optimizer (cvxpy), and the textbook ranked book |
| Execution | `kinn.execution` | opening or closing auction |
| Engine and runs | `kinn.engine.daily`, `kinn.book_run`, `kinn book <config>` | resumable by month |

Differences from the proposal, and why:

- **Alphas return an array of scores**, one per company, not a list of `Forecast` objects. It is
  the same contract and far faster.
- **The universe belongs to the book**, not to each alpha: alphas in one book must score the
  same companies. An alpha may still return NaN for names it has no view on.
- **Execution is in the auction only** (decision 0014). Orders this small are a negligible share
  of the auction, so slicing through the day on minute bars would add cost and no accuracy.
- **The risk model is single-index**, with sector limits in the optimizer, not a factor model.
- **A book is charged to one trial family.** Charging a multi-alpha book to each alpha's family
  as well is deferred until such a book exists.
- **Not modelled** (decision 0016): margin calls, interest on cash, hard-to-borrow names,
  dividends on shorts beyond the cash payment. The borrow fee is an assumed 1% a year.
- **Fundamentals** are available to alphas (`alpha.fundamentals = ("equityusd", ...)`,
  `view.fundamental(name)`), as reported and usable from the session after the filing. No alpha
  uses them yet.

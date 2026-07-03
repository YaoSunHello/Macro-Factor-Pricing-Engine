# Macro Factor Pricing Engine Documentation

## Purpose

Macro Factor Pricing Engine is a research and governance system for converting macro
regime evidence into explained, pending tactical allocation recommendations.

The project currently has two main layers:

1. A general macro regime layer that classifies environments by growth/inflation state
   and causal mechanism.
2. A rates-focused thin slice that turns Treasury policy signals into pending target
   weights for scoped government-bond buckets.

It is intentionally not a trading system. The code preserves approval gates, records
human-input governance, treats public-data timing as a first-class constraint, and keeps
live/paper execution out of scope until instrument approval and risk controls are built.

## Current Scope

Implemented scope:

- macro regime taxonomy and defined playbooks;
- deterministic Stage 1 regime classifier;
- human override/audit seam;
- rates-only analysis loop;
- read-only local API/dashboard;
- broker credential setup and read-only client metadata;
- strategic benchmark references;
- first-pass risk and turnover readouts.

Explicit non-scope:

- live order placement;
- paper trading execution;
- optimization;
- statistically fitted regime models;
- full backtesting and detection-lag charging;
- approval workflow for tradeable instruments.

## Architecture Overview

Package path:

```text
src/macro_factor_pricing_engine
```

| Module | Responsibility |
|---|---|
| `regimes.py` | Two-axis macro regime taxonomy, defined playbooks, transition matrix, `RegimeProbabilities` |
| `regime_classifier.py` | Deterministic Stage 1 classifier from raw public indicators |
| `regime_override.py` | Human override records plus audit metadata |
| `regime_input.py` | Manual regime probabilities used by the current rates loop |
| `data/regime_indicator_schema.py` | Nullable raw indicator snapshot schema and lag metadata |
| `data/sources.py` | Committed snapshot loader plus free public-source fetch helpers |
| `policy.py` | Strategy governance, review triggers, confirmation requirements |
| `benchmarks.py` | Strategic benchmark weights by investment horizon |
| `universe.py` | Asset-class universe and rates proxy securities with approval gate |
| `treasury_policy.py` | Structured Treasury policy records derived from `TreasuryPolicy.md` |
| `rates_scorer.py` | Rates cycle, valuation, fiscal-veto, overlay, and trigger scoring |
| `sizing.py` | First-pass rates target weights |
| `risk.py` | Duration, DV01, bucket exposure, and concentration readout |
| `inventory.py` | Paper inventory loading and append-only turnover ledger |
| `explain.py` | Plain-language recommendation explanation |
| `app.py` | CLI orchestration for the rates analysis loop |
| `api.py` | Read-only FastAPI seam for the dashboard |
| `api_keys.py` | Broker credential setup registry and readiness checks |
| `trading212.py` | Read-only Trading 212 client helpers |
| `ig.py` | Read-only IG client helpers |

## Regime Model

The regime model has two axes.

Macro state describes the structural growth/inflation quadrant:

| State | Growth | Inflation | Interpretation |
|---|---|---|---|
| `goldilocks` | stable positive | low | Growth is supported without inflation pressure |
| `reflation` | accelerating | rising | Nominal activity and cyclical demand improve |
| `stagflation` | decelerating | sticky high | Inflation pressure coexists with weak real activity |
| `disinflationary_slowdown` | decelerating | falling | Demand, inflation, and activity soften together |

Causal mechanism describes why the state exists:

| Mechanism | Interpretation |
|---|---|
| `cyclical_no_acute_mechanism` | Ordinary business-cycle dynamics |
| `peg_or_promise_break` | Currency, sovereign, peg, or policy-anchor break |
| `deliberate_policy_disruption` | Policy, real-rate, or fiscal shock dominates |
| `leverage_institutional_breakdown` | Funding, leverage, drawdown, or institutional stress dominates |

There are 16 possible state/mechanism combinations. Eight are currently defined in
`REGIME_DEFINITIONS`:

| Macro state | Mechanism |
|---|---|
| `goldilocks` | `cyclical_no_acute_mechanism` |
| `reflation` | `cyclical_no_acute_mechanism` |
| `stagflation` | `deliberate_policy_disruption` |
| `stagflation` | `leverage_institutional_breakdown` |
| `disinflationary_slowdown` | `cyclical_no_acute_mechanism` |
| `disinflationary_slowdown` | `peg_or_promise_break` |
| `disinflationary_slowdown` | `leverage_institutional_breakdown` |
| `disinflationary_slowdown` | `deliberate_policy_disruption` |

Undefined pairs are not errors by themselves. They mean no distinct strategy playbook is
approved yet, so downstream code must surface review instead of pretending the nearest
defined regime is correct.

## Regime Probabilities

`RegimeProbabilities` is the stable downstream interface. It validates that weights are
non-negative and sum to 1.0. It exposes:

- `dominant_regime()`;
- `is_transition(threshold=0.6)`.

The Stage 1 classifier wraps this object in `RegimeClassification` to add metadata that
the original frozen probability type does not store:

- channel scores;
- fired observable triggers;
- missing fields;
- computed state and mechanism;
- undefined-playbook flag;
- optional override audit.

This preserves compatibility with existing code while still exposing classifier
diagnostics.

## Stage 1 Classifier

Files:

```text
src/macro_factor_pricing_engine/data/regime_indicator_schema.py
src/macro_factor_pricing_engine/regime_classifier.py
tests/test_regime_classifier.py
```

`RegimeIndicatorSnapshot` contains one nullable raw field per input:

- growth: `ism_manufacturing_pmi`, `chicago_fed_nai`, `gdpnow_estimate`;
- inflation: `cpi_yoy`, `core_cpi_yoy`, `breakeven_5y5y`;
- policy/liquidity: `ust_2y_yield`, `ust_2y_yield_chg_1m`, `ust_10y_yield`,
  `ust_10y_yield_chg_1m`, `fed_funds_implied_path_chg_3m`, `nfci`;
- risk appetite: `ig_oas`, `ig_oas_chg_1m`, `hy_oas`, `hy_oas_chg_1m`, `vix`;
- fiscal/sovereign: `acm_term_premium_10y`, `dxy_chg_3m`, `dxy_trend_direction`;
- commodities: `broad_commodity_index_chg_3m`;
- equities: `sp500_drawdown_from_52w_high`.

Every raw field is `float | None`. `None` is not imputed. Missing fields are exposed
through `snapshot.missing_fields` and copied into `RegimeClassification.missing_fields`.

### Channel Scores

`compute_channel_scores()` returns scores in `[-1, 1]` for the five macro transmission
channels:

- `growth`;
- `inflation`;
- `policy_liquidity`;
- `risk_appetite`;
- `fiscal_sovereign`.

The numeric thresholds are sourced from `docs/market_history_patterns.md` where
available:

| Channel | Source |
|---|---|
| Growth | Part V Module A, ISM Manufacturing `< 47` concurrent recession threshold |
| Inflation | Part V Module B, low/moderate/high inflation regime bands |
| Risk appetite | Part V Module C HY OAS bands and Module G VIX bands |
| Fiscal/sovereign | Part V Module E DXY `>5%` over 6 months threshold |
| Policy/liquidity | Chicago Fed NFCI sign convention plus sign-only rates changes |

The classifier does not use z-scores or fitted model parameters. It is deterministic and
intentionally explainable.

### Observable Triggers

`derive_observable_triggers()` maps raw levels and channel scores onto trigger names
already present in `regimes.py`. It does not invent new trigger names.

Implemented trigger examples:

- `growth_momentum_negative`;
- `growth_momentum_positive`;
- `inflation_momentum_positive`;
- `inflation_momentum_negative`;
- `inflation_high_or_sticky`;
- `credit_spreads_widening_fast`;
- `credit_spreads_stable_or_tightening`;
- `volatility_or_financial_conditions_stress`;
- `equity_drawdown_breach`;
- `usd_trend_positive`;
- `commodity_trend_positive`;
- `nominal_yields_rising`;
- `nominal_yields_falling`;
- `policy_expectations_easing`;
- `yield_curve_not_signaling_policy_shock`.

### Open Threshold Stubs

The following are deliberately explicit stubs because no approved threshold exists in
`docs/market_history_patterns.md`:

- `currency_or_policy_anchor_break`;
- `cross_market_contagion`;
- `real_yields_rising`;
- `inflation_surprise_positive`;
- `financial_conditions_tightening`;
- `fiscal_or_term_premium_stress`;
- `front_end_yields_rising_fast`;
- ACM 10Y term-premium channel contribution.

Calling these stubs directly raises `NotImplementedError`. Tests enforce this behavior
so missing thresholds cannot silently become fabricated `False` signals.

### State And Mechanism Decision

`classify_regime()` computes channel scores first, then derives:

1. Macro state from growth/inflation channel scores.
2. Causal mechanism from ordered trigger rules.
3. Probability distribution across defined regime playbooks.

If the computed pair is defined, the classifier assigns primary weight to that pair and
spreads residual weight across other defined pairs. Missing inputs flatten confidence.

If the computed pair is undefined, the classifier returns a valid probability
distribution over defined pairs sharing the same macro state. It sets
`outside_defined_playbooks=True`.

## Human Overrides

File:

```text
src/macro_factor_pricing_engine/regime_override.py
```

`RegimeOverride` records:

- state;
- mechanism;
- confidence;
- reason;
- entered-by user;
- entered timestamp;
- optional expiry timestamp.

`apply_override()`:

- returns the computed classification unchanged when no override is supplied;
- raises `KeyError` if the override references an undefined regime pair;
- returns full weight on the override pair when valid;
- records an audit object containing the original computed probabilities and override;
- attaches `human_input_pending` policy trigger metadata, including
  `requires_confirmation=True`.

Overrides are research/governance events. They do not open the trade gate.

## Data Layer

Committed rates fixture:

```text
src/macro_factor_pricing_engine/data/snapshot_2026_06_18.json
```

The fixture is used by the current rates loop. It includes Treasury yields, breakevens,
ACM term premium, inflation readings, GDPNow, ISM, payrolls, unemployment change, MOVE,
auction-demand proxies, QT/supply flags, stock-bond correlation, and risk gauges.

`SnapshotSource.load_raw(as_of)` enforces no-lookahead by checking that no observation
date is after the requested `as_of` date.

`data/sources.py` also contains direct FRED CSV helpers for classifier raw fields. These
helpers return `(value | None, as_of_date)` and use only free public endpoints. Network
failures degrade to `None` instead of fabricating values.

## Rates Analysis Loop

Command:

```bash
PYTHONPATH=src python3 -m macro_factor_pricing_engine.app
```

The current loop still uses `regime_input.default_manual_regime_probabilities()` rather
than the Stage 1 classifier. This is intentional: the classifier is validated standalone
first, and wiring it into sizing is a follow-up.

Flow:

1. `SnapshotSource` loads the committed rates snapshot.
2. `regime_input.py` supplies manual probabilities.
3. `rates_scorer.py` computes cycle, valuation, fiscal-veto, overlay, trigger, and
   derived-metric outputs.
4. `sizing.py` turns scores and dominant mechanism into pending rates target weights.
5. `inventory.py` loads blank/persistent paper inventory and appends turnover rows.
6. `risk.py` computes duration, DV01, bucket exposure, and concentration flags.
7. `explain.py` writes the plain-language explanation.
8. `app.py` returns and prints a `Recommendation`.

The recommendation always has:

```text
mode = "analysis"
status = "PENDING"
```

## Rates Scoring

`rates_scorer.py` computes:

- cycle score from growth, inflation momentum, and real policy stance;
- valuation score from term premium, supply pressure, MOVE, real yields, positioning,
  and yield momentum;
- fiscal veto from CDS widening, auction tails, and fiscal event flags;
- cross-asset overlay from stock-bond correlation;
- composite signal;
- fired trigger list;
- derived metrics.

With the committed 2026-06-18 snapshot and manual regime probabilities, the current
default stance is:

```text
Cycle: -1
Valuation: -4
Fiscal veto: False
Overlay modifier: 0.5
Composite signal: long_end_underweight
```

## Sizing

`sizing.py` produces a `TargetPortfolio`. It starts from equal bucket weights and then
applies the current rates convention.

Under `deliberate_policy_disruption`, the bucket target is:

| Bucket | Target |
|---|---:|
| Short-duration government bonds | 25% |
| Intermediate-duration government bonds | 40% |
| Long-duration government bonds | 5% |
| Inflation-linked bonds | 30% |

Weights are split equally across in-scope securities inside each bucket. Curve trades
are notes only; they are not forced into the target vector.

## Universe And Approval Gate

`universe.py` defines asset-class membership and rates proxies. Current rates proxies:

| Bucket | Proxies |
|---|---|
| Short duration | `SHY`, `SHV` |
| Intermediate duration | `IEF`, `VGIT` |
| Long duration | `TLT`, `VGLT` |
| Inflation-linked bonds | `TIP`, `VTIP` |

Membership is not approval. Every scoped security currently has
`approved_for_allocation=False`, and `has_tradeable_instruments()` must remain `False`
until a future approval workflow changes that deliberately.

## Risk Readout

`risk.py` computes:

- weighted portfolio duration;
- DV01 per $1mm notional;
- bucket exposure;
- concentration cap;
- cap-breach list.

This is a first-pass readout, not a full risk model. Vol targeting, covariance modeling,
drawdown controls, turnover budgets, and optimization remain future work.

## Strategic Benchmarks

`benchmarks.py` defines neutral reference weights by horizon:

| Horizon | Intent |
|---|---|
| `10y` | Growth-heavy strategic blend |
| `5y` | Balanced medium-horizon blend |
| `1y` | Defensive one-year blend |
| `1q` | Capital preservation, all cash |

Benchmarks are validated at import time:

- every referenced bucket must exist in the universe;
- every horizon must sum to 1.0;
- omitted buckets resolve to 0.0.

Benchmarks are reference portfolios, not live holdings.

## Policy And Governance

`policy.py` defines the project-level governance contract.

Key policy points:

- optimize risk-adjusted return, not raw return;
- benchmark/liability reference remains pending;
- no unapproved ticker can receive a target allocation;
- no-lookahead data handling is mandatory;
- human input can create pending adjustments only;
- instrument-universe changes require confirmation;
- full risk model, vol target, concentration caps, turnover budget, and detection-lag
  budget remain future work.

Main triggers:

- `scheduled_monthly_review`;
- `regime_transition`;
- `policy_shock`;
- `liquidity_stress`;
- `human_input_pending`;
- `instrument_universe_change`.

`human_input_pending` and `instrument_universe_change` require confirmation.

## Broker And API Setup

`api_keys.py` records setup metadata for:

- Trading 212;
- Interactive Brokers;
- Robinhood;
- IG Group;
- Capital.com;
- Plus500.

`trading212.py` and `ig.py` provide read-only client helpers. No module places orders.

Credential templates live in `.env.example`. Real `.env` files are ignored by git.

## Local Dashboard

API module:

```text
src/macro_factor_pricing_engine/api.py
```

Run:

```bash
PYTHONPATH=src uvicorn macro_factor_pricing_engine.api:app --reload
```

Open:

```text
http://127.0.0.1:8000/
```

The API exposes:

```text
GET /api/state
```

The frontend is a static SPA in `frontend/`. It renders:

- 4 x 4 regime grid;
- active/undefined cells;
- transition banner;
- full regime distribution;
- dominant-regime explanation;
- score panel;
- pending target weights;
- asset-class list.

The dashboard is read-only and currently reflects the rates loop's manual regime input,
not the Stage 1 classifier.

## Runtime Files

The CLI writes runtime state under:

```text
.runtime/
```

The turnover ledger is:

```text
.runtime/turnover_ledger.jsonl
```

`.runtime/` is ignored by git.

## Testing

Run all tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

Focused commands:

```bash
PYTHONPATH=src python3 -m unittest tests.test_regime_classifier
PYTHONPATH=src python3 -m unittest tests.test_api_phase1
PYTHONPATH=src python3 -m unittest tests.test_policy_and_regimes
PYTHONPATH=src python3 -m unittest tests.test_benchmarks
PYTHONPATH=src python3 -m macro_factor_pricing_engine.app
```

Classifier tests are split into two tiers:

- synthetic fixtures assert specific labels;
- real-dated smoke fixtures assert only validity, non-negative weights, weight sum, and
  missing-data integrity.

Real data tests should not assert a specific regime unless a human-labeled golden
scenario is added.

## Known Open Decisions

Threshold decisions still needed:

- `currency_or_policy_anchor_break`;
- `cross_market_contagion`;
- `real_yields_rising`;
- `inflation_surprise_positive`;
- `financial_conditions_tightening`;
- `fiscal_or_term_premium_stress`;
- `front_end_yields_rising_fast`;
- ACM 10Y term-premium channel contribution;
- whether the classifier's current probability-spreading convention should become the
  production confidence model;
- whether the Stage 1 classifier should directly replace `regime_input.py` in the rates
  loop or run side-by-side for an evaluation period.

## Next Work

Recommended sequence:

1. Confirm the unresolved threshold stubs.
2. Add a dated classifier snapshot fixture from public data.
3. Wire Stage 1 classifier output into `app.py` behind an explicit switch.
4. Surface classifier diagnostics in `/api/state` and the dashboard.
5. Add validation/backtest scaffolding with detection-lag accounting.
6. Build instrument approval workflow.
7. Add full risk model and allocation optimizer.
8. Only then consider paper/live execution surfaces.

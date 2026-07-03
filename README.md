# Macro Driven Tactical Asset Allocation

Macro Factor Pricing Engine is a governance-first research system for macro-driven
tactical asset allocation. It combines a two-axis macro regime framework, a
deterministic Stage 1 regime classifier, a rates-focused analysis loop, and a
read-only local dashboard.

The project is not a trading bot. It runs in analysis mode, emits pending
recommendations, keeps every trade gate closed by default, and requires explicit human
confirmation before discretionary inputs or instrument approvals can affect allocation.

## What It Does

The core model classifies market conditions along two independent axes:

| Axis | Values |
|---|---|
| Macro state | `goldilocks`, `reflation`, `stagflation`, `disinflationary_slowdown` |
| Causal mechanism | `cyclical_no_acute_mechanism`, `peg_or_promise_break`, `deliberate_policy_disruption`, `leverage_institutional_breakdown` |

Crossing the two axes creates a 4 x 4 grid of 16 possible regime cells. Eight cells
currently have defined playbooks. Undefined cells remain explicit review cases instead
of being forced into a false match.

The mechanism axis matters because the same growth/inflation state can require
different positioning depending on why it is happening. For example,
`stagflation x deliberate_policy_disruption` treats long-duration government bonds as
a strong underweight, while `stagflation x leverage_institutional_breakdown` can restore
a flight-to-quality case for the same asset class.

## Current Implementation Status

Implemented:

- UK-retail research universe with asset classes and rates proxies;
- two-axis regime taxonomy and eight defined regime playbooks;
- soft `RegimeProbabilities` interface for downstream consumers;
- Stage 1 deterministic regime classifier from public macro/risk indicators;
- explicit missing-data handling for classifier inputs;
- explicit `NotImplementedError` stubs where no sourced threshold exists;
- human regime override records with policy-trigger audit metadata;
- strategic benchmark references for `10y`, `5y`, `1y`, and `1q` horizons;
- structured Treasury policy module;
- rates-only analysis loop that emits pending target weights;
- risk readout for duration, DV01, bucket exposure, and concentration flags;
- read-only FastAPI and static dashboard seam;
- tests covering regimes, policy, benchmarks, API, brokers, rates loop, and classifier.

Not yet implemented:

- automated wiring from the Stage 1 classifier into the rates loop;
- allocation optimizer or full risk model;
- validation/backtest engine;
- approved tradeable ticker workflow;
- live or paper order execution.

## Project Structure

```text
Macro-Factor-Pricing-Engine/
├── src/
│   └── macro_factor_pricing_engine/
│       ├── __init__.py
│       ├── api.py
│       ├── api_keys.py
│       ├── app.py
│       ├── benchmarks.py
│       ├── explain.py
│       ├── ig.py
│       ├── inventory.py
│       ├── policy.py
│       ├── rates_scorer.py
│       ├── regime_classifier.py
│       ├── regime_input.py
│       ├── regime_override.py
│       ├── regimes.py
│       ├── risk.py
│       ├── sizing.py
│       ├── trading212.py
│       ├── treasury_policy.py
│       ├── universe.py
│       ├── TreasuryPolicy.md
│       └── data/
│           ├── __init__.py
│           ├── regime_indicator_schema.py
│           ├── snapshot_2026_06_18.json
│           └── sources.py
├── docs/
│   ├── PROJECT_DOCUMENTATION.md
│   └── market_history_patterns.md
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── tests/
├── pyproject.toml
├── README.md
├── Notes
└── LICENSE
```

## Stage 1 Regime Classifier

`src/macro_factor_pricing_engine/regime_classifier.py` consumes a
`RegimeIndicatorSnapshot` from `data/regime_indicator_schema.py` and returns a
`RegimeClassification` wrapper containing:

- a validated `RegimeProbabilities` object;
- channel scores for growth, inflation, policy/liquidity, risk appetite, and
  fiscal/sovereign channels;
- observable triggers drawn from the exact trigger names in `regimes.py`;
- missing field names;
- the computed macro state and causal mechanism;
- `outside_defined_playbooks` when the computed pair has no defined playbook.

Thresholds are sourced from `docs/market_history_patterns.md` where available:

- Module A: ISM manufacturing recession threshold;
- Module B: inflation regime bands;
- Module C: HY OAS stress bands;
- Module E: DXY dollar-cycle threshold;
- Module G: VIX stress bands;
- Part IV: S&P 500 bear-market drawdown convention.

Open threshold decisions intentionally remain as explicit stubs:

- `currency_or_policy_anchor_break`;
- `cross_market_contagion`;
- `real_yields_rising`;
- `inflation_surprise_positive`;
- `financial_conditions_tightening`;
- `fiscal_or_term_premium_stress`;
- `front_end_yields_rising_fast`;
- ACM 10Y term-premium channel contribution.

## Rates Analysis Loop

The current executable slice is rates-only and still uses
`regime_input.default_manual_regime_probabilities()` rather than the new classifier.
This keeps the Stage 1 classifier independently testable until the next wiring step.

Run:

```bash
PYTHONPATH=src python3 -m macro_factor_pricing_engine.app
```

The loop:

1. loads the committed `2026-06-18` rates snapshot;
2. enforces no-lookahead through the data source boundary;
3. loads manual regime probabilities;
4. computes Treasury policy scores;
5. sizes pending rates target weights;
6. appends an analysis-only turnover ledger row;
7. computes a first-pass risk readout;
8. prints a plain-language pending recommendation.

## Local Dashboard

Run:

```bash
PYTHONPATH=src uvicorn macro_factor_pricing_engine.api:app --reload
```

Then open:

```text
http://127.0.0.1:8000/
```

The dashboard is read-only. It shows the regime grid, probability distribution,
transition flag, score panels, pending target weights, and defined/undefined regime
cells.

## Tests

Run the full suite:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

Focused commands:

```bash
PYTHONPATH=src python3 -m unittest tests.test_regime_classifier
PYTHONPATH=src python3 -m unittest tests.test_api_phase1
PYTHONPATH=src python3 -m macro_factor_pricing_engine.app
```

## Documentation

Full project documentation is in:

```text
docs/PROJECT_DOCUMENTATION.md
```

The historical pattern and threshold source library is in:

```text
docs/market_history_patterns.md
```

## Governance

Important invariants:

- recommendations are `PENDING`;
- no scoped security is approved for allocation;
- broker clients are read-only setup/readiness surfaces;
- `.env` files are ignored;
- discretionary overrides require `human_input_pending` policy metadata;
- missing classifier inputs remain missing and are exposed to callers;
- unsupported thresholds raise directly instead of silently returning fabricated
  signals.

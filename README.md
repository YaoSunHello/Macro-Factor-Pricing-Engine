# Macro-Factor-Pricing-Engine
Project Introduction
This project builds a top-down framework for two linked tasks: macro-driven asset allocation, and (eventually) policy-driven sub-asset-class portfolio construction.
Asset allocation is driven by a macro regime detection framework. The framework assumes that any market environment can be classified along two independent axes: a macro state (one of four structural growth/inflation quadrants — Goldilocks, Reflation, Stagflation, Disinflationary Slowdown) and a causal mechanism (one of four transmission mechanisms explaining why that state is occurring — e.g. ordinary cyclical dynamics, a currency/peg break, deliberate policy disruption, or leverage/institutional stress). Crossing these two axes gives a 4×4 grid of 16 possible regime cells; currently 8 of those cells have defined, research-backed playbooks, and the rest are left undefined until a distinct strategy case justifies building one out.
The mechanism axis matters because the same growth/inflation state can call for very different asset positioning depending on its cause — for example, stagflation driven by policy disruption is hostile to long-duration bonds, while stagflation driven by leverage/institutional stress can restore a flight-to-quality bid for the same bonds.
Extensive historical research — spanning major financial cycles, crises, and recoveries from 1900–2022 — informs which asset classes are expected to lead or lag under each defined regime pair. This produces theory-driven priors, not fitted or backtested estimates.
The model is intended to take in current cross-asset conditions (equities, credit, commodities, monetary and fiscal policy, currency, and rates) to infer the current regime as a soft probability distribution across the 16 cells, rather than a single hard label. Regime classification itself is not yet automated — a live classifier ("Stage 1") is the next planned module — but the interface it will eventually feed (RegimeProbabilities) already exists.
A heuristic monthly transition matrix, calibrated from historical regime persistence, encodes the assumption that a regime is most likely to persist unless a significant shock shifts probability mass toward another quadrant. This transition structure feeds into asset allocation tilts away from a strategic neutral benchmark, which is adjustable by investment horizon (10y, 5y, 1y, 1q).
Sub-asset-class portfolio construction is currently policy-driven rather than model-driven. Only one policy exists so far: a structured government bond (Treasury) strategy policy, encoding signal rules, fiscal credibility gates, and segment positioning logic, but not yet wired to live scoring or execution.
A separate ValuationOverlay — not part of the macro regime grid — is reserved for gating entry timing based on valuation and positioning, and is not yet implemented.
The system is research-stage and explicitly not tradeable: every instrument in the universe is unapproved for allocation, broker connections are credential-only plumbing with no live execution, and no signal can move portfolio weights without explicit human confirmation.

## Documentation

Full project documentation is available at [docs/PROJECT_DOCUMENTATION.md](docs/PROJECT_DOCUMENTATION.md).

## Current Implementation Status

The first implementation pass is complete. The repository now contains a small Python
package under `src/macro_factor_pricing_engine` with:

- a UK-retail UCITS/LSE-listed asset-class universe for research scope, with every
  instrument still unapproved for allocation;
- two-axis macro regime definitions: macro state plus causal mechanism;
- state-level macro profiles and a heuristic monthly transition matrix for the
  four structural macro quadrants;
- a policy module that records strategy governance, review triggers, risk controls, and
  human-input confirmation rules;
- a strategic overall-portfolio benchmark module with horizon-specific neutral SAA
  blends for `10y`, `5y`, `1y`, and `1q`;
- a structured Treasury strategy policy module derived from `TreasuryPolicy.md`;
- a rates-only end-to-end analysis loop that runs from committed snapshot data to a
  pending recommendation;
- a Phase 1 read-only local web dashboard backed by `GET /api/state`;
- a broker API setup registry that validates environment-variable readiness for
  Trading 212, Interactive Brokers, Robinhood, IG Group, Capital.com, and Plus500;
- a focused unit test suite for the universe, regime, and policy records.

The system is not tradeable yet. Asset classes are approved as categories, but no ticker
can receive a paper or live allocation until its `approved_for_allocation` flag is
explicitly reviewed and switched on.

Broker API setup is credential plumbing only. It does not create live broker clients,
open sessions, or submit orders.

## Project Structure

```text
Macro-Factor-Pricing-Engine/
├── src/
│   └── macro_factor_pricing_engine/
│       ├── __init__.py
│       ├── policy.py
│       ├── regimes.py
│       ├── benchmarks.py
│       ├── treasury_policy.py
│       ├── TreasuryPolicy.md
│       ├── universe.py
│       ├── api_keys.py
│       ├── api.py
│       ├── app.py
│       ├── rates_scorer.py
│       ├── sizing.py
│       ├── inventory.py
│       ├── risk.py
│       ├── explain.py
│       ├── regime_input.py
│       └── data/
│           ├── sources.py
│           └── snapshot_2026_06_18.json

├── tests/
│   ├── test_policy_and_regimes.py
│   ├── test_benchmarks.py
│   └── test_api_phase1.py
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── pyproject.toml
├── README.md
├── Notes
└── LICENSE
```

## Implemented Modules

### Universe Scaffold

`src/macro_factor_pricing_engine/universe.py` defines the approved asset-class map.
The empty/US ETF placeholder universe has been replaced with representative
UK-retail-accessible UCITS or LSE-listed instruments. Every security remains marked
`USER TO CONFIRM`, and every `approved_for_allocation` flag is `False`, so
`has_tradeable_instruments()` still returns `False`.

Current research-scope buckets:

- `us_equities`: `CSPX`, `VUSA`
- `global_developed_equities`: `SWDA`, `VEVE`
- `emerging_market_equities`: `EIMI`, `VFEM`
- `short_duration_government_bonds`: `IB01`, `IBTA`
- `intermediate_duration_government_bonds`: `IBTM`
- `long_duration_government_bonds`: `IDTL`, `DTLA`
- `inflation_linked_bonds`: `ITPS`
- `investment_grade_credit`: `LQDE`
- `high_yield_credit`: `IHYU`
- `gold`: `SGLN`, `SGLD`
- `broad_commodities`: `CMOD`, `ICOM`
- `usd_proxy`: `IB01`
- `cash`: `IGLS`

Some ISINs remain explicit `TODO confirm` entries rather than guessed identifiers.

Membership is used only for analysis scope. Allocation approval remains separate and
human-gated.

The module also records a platform capability matrix for `ibkr_uk`, `trading212`,
`hargreaves_lansdown`, `aj_bell`, and `investengine`. The key distinction is that only
`ibkr_uk` has `futures` and `fx_spot` enabled, `trading212` has `cfds` enabled, and all
listed platforms keep `us_domiciled_etfs` disabled for UK retail suitability.

### Macro Regime Layer

`src/macro_factor_pricing_engine/regimes.py` records the market-regime layer as two
separate ideas:

1. `MacroState`: the structural growth/inflation quadrant.
2. `CausalMechanism`: the shock or transmission mechanism explaining why the state is
   happening.

This separation matters because the same growth/inflation state can produce different
asset behavior depending on the mechanism. For example, sticky inflation with policy
disruption is hostile to long-duration bonds, while sticky inflation with leverage or
institutional stress can restore a flight-to-quality bid.

Macro states:

- `goldilocks`
- `reflation`
- `stagflation`
- `disinflationary_slowdown`

Causal mechanisms:

- `cyclical_no_acute_mechanism`
- `peg_or_promise_break`
- `deliberate_policy_disruption`
- `leverage_institutional_breakdown`

Former stand-alone labels for liquidity stress and tightening shocks have been moved
onto the mechanism axis. They are no longer structural macro states.

Transmission channels:

- growth;
- inflation;
- policy/liquidity;
- risk appetite;
- fiscal/sovereign.

Valuation and positioning are explicitly not macro channels. They are represented by a
separate placeholder `ValuationOverlay`, owned outside the macro-to-asset map and used
later to gate entry timing.

`MacroStateProfile` captures state-only structure before mechanism-specific playbooks
are applied:

| Macro state | Growth | Inflation | Typical interpretation |
|---|---|---|---|
| `goldilocks` | stable positive | low | productivity or supply expansion supports growth without inflation pressure |
| `reflation` | accelerating | rising | cyclical demand or fiscal impulse lifts nominal growth |
| `stagflation` | decelerating | sticky high | supply shock or policy distortion pressures margins and real activity |
| `disinflationary_slowdown` | decelerating | falling | demand exhaustion or deleveraging pulls inflation and growth lower |

Defined state x mechanism playbooks:

| Macro state | Causal mechanism | Why defined |
|---|---|---|
| `goldilocks` | `cyclical_no_acute_mechanism` | benign expansion playbook |
| `reflation` | `cyclical_no_acute_mechanism` | nominal growth acceleration playbook |
| `stagflation` | `deliberate_policy_disruption` | inflation/policy/fiscal pressure dominates |
| `stagflation` | `leverage_institutional_breakdown` | stress can restore duration flight-to-quality |
| `disinflationary_slowdown` | `cyclical_no_acute_mechanism` | normal slowdown with easing optionality |
| `disinflationary_slowdown` | `peg_or_promise_break` | anchor break or currency/sovereign stress causing risk-off demand collapse |
| `disinflationary_slowdown` | `leverage_institutional_breakdown` | deleveraging and policy-response playbook |
| `disinflationary_slowdown` | `deliberate_policy_disruption` | forced repricing from policy/real-rate shock |

The rest of the 4 x 4 grid is intentionally undefined because those pairs are not
distinct strategy playbooks yet. Each defined pair records the causal story, expected
leading asset classes, expected lagging asset classes, observable trigger names, and
mechanism-specific asset-map overrides. Leading/lagging lists are labelled as heuristic
theory-priors, not fitted estimates.

The state transition layer is deliberately simple and data-only:

- `TRANSITION_TIME_STEP = "monthly"`;
- `TRANSITION_MATRIX_IS_HEURISTIC = True`;
- every row in `TRANSITION_MATRIX` sums to 1.0;
- the diagonal stay term represents regime persistence;
- `disinflationary_slowdown` is the stickiest state at 0.80;
- `reflation -> stagflation` is higher than `stagflation -> reflation`, reflecting
  that overheating can tip into sticky inflation faster than sticky inflation usually
  resolves.

`transition_row_for(from_state, mechanism)` applies the first mechanism modifier:
`leverage_institutional_breakdown` increases the probability of moving into
`disinflationary_slowdown` and then renormalizes the row. Other mechanisms are identity
modifiers for now. No transition-intensity scorer, entropy/drift logic, hysteresis
logic, point-in-time transition model, or backtest timing engine exists yet.

The key test anchor is stagflation:

- `stagflation x deliberate_policy_disruption`: long-duration government bonds are
  `strong_underweight` because term-premium/fiscal risk dominates.
- `stagflation x leverage_institutional_breakdown`: long-duration government bonds are
  `overweight` because flight-to-quality can dominate once policy response is expected.

`RegimeProbabilities` supports soft regime assignment and flags transitions when no
single regime pair holds more than 0.6 of the probability mass.

### Policy Module

`src/macro_factor_pricing_engine/policy.py` records the strategy-level policy before the
allocation engine exists. The current policy states:

- objective: maximise risk-adjusted return using Sharpe and Calmar, not raw return;
- the benchmark or liability reference is pending/unconfirmed, so the objective is
  currently asset-only;
- no approved ticker can receive a target weight;
- human input can only create a pending adjustment and can never automatically move the
  portfolio;
- no-lookahead data handling is mandatory;
- risk model, vol target, concentration caps, turnover budget, and regime detection lag
  budget are pending Module 4.

Recorded strategy triggers:

- `scheduled_monthly_review`
- `regime_transition` based on probability-mass shift, not hard state flip
- `policy_shock`
- `liquidity_stress`
- `human_input_pending`
- `instrument_universe_change`

The human-input and instrument-universe-change triggers require explicit confirmation.

### Strategic Benchmarks

`src/macro_factor_pricing_engine/benchmarks.py` defines the neutral strategic asset
allocation reference the engine tilts away from. This benchmark is not the live
portfolio: the live portfolio can still initialize with every asset-class weight at
zero, while the benchmark has non-zero reference weights for performance and risk
measurement.

Benchmarks are defined by investment horizon:

| Horizon | Principle |
|---|---|
| `10y` | Growth-heavy blend with 80% growth / 20% defensive exposure |
| `5y` | Balanced medium-horizon blend with lower growth risk |
| `1y` | Defensive one-year blend with high short-duration/cash exposure |
| `1q` | Capital preservation benchmark, 100% cash |

Every benchmark bucket is validated against `universe.asset_classes()` at import time,
and every horizon must sum to 1.0 within `1e-9`. Omitted buckets are treated as 0.0 by
`benchmark_weight(horizon, asset_class)`. Starter weights are `USER TO CONFIRM` policy
defaults, not live allocations.

### Broker API Setup

`src/macro_factor_pricing_engine/api_keys.py` defines API credential setup metadata and
environment-variable readiness checks for:

| Broker | Required environment variables | Execution support in registry |
|---|---|---|
| Trading 212 | `TRADING212_API_KEY`, `TRADING212_API_SECRET` | Read-only account, positions, and instrument metadata client |
| Interactive Brokers | `IBKR_GATEWAY_BASE_URL` | Configurable via Client Portal Gateway, not wired to execution |
| Robinhood | `ROBINHOOD_API_KEY`, `ROBINHOOD_PRIVATE_KEY` | Disabled until the exact official API surface is approved |
| IG Group | `IG_API_KEY`, `IG_USERNAME`, `IG_PASSWORD` | Read-only session, accounts, and market lookup client |
| Capital.com | `CAPITAL_COM_API_KEY`, `CAPITAL_COM_IDENTIFIER`, `CAPITAL_COM_API_PASSWORD` | Configurable, not wired to execution |
| Plus500 | none | Unsupported unless Plus500 grants an official API integration |

Use `.env.example` as the local setup template. Real `.env` files are ignored by git.
For this workstation, Trading 212 credentials can also be loaded from the local file
outside the repository:

```bash
source ~/.config/macro-factor-pricing-engine/trading212.env
```

IG credentials can be loaded locally the same way:

```bash
source ~/.config/macro-factor-pricing-engine/ig.env
```

Example readiness check:

```bash
PYTHONPATH=src python3 - <<'PY'
from macro_factor_pricing_engine.api_keys import all_broker_api_statuses

for status in all_broker_api_statuses():
    missing = ", ".join(status.missing_required_env_vars) or "none"
    print(f"{status.setup.display_name}: configured={status.configured}, missing={missing}")
PY
```

Credential loading is explicit:

```python
from macro_factor_pricing_engine.api_keys import load_broker_api_credentials

credentials = load_broker_api_credentials("capital.com")
```

Trading 212 has a small read-only client:

```python
from macro_factor_pricing_engine.trading212 import Trading212Client

client = Trading212Client.from_environment()
summary = client.account_summary()
positions = client.positions()
```

The current recommendation loop still does not place orders or consume broker account
data automatically.

IG Group has a read-only client:

```python
from macro_factor_pricing_engine.ig import IgClient

client = IgClient.from_environment()
session = client.create_session()
accounts = client.accounts(session)
```

### Treasury Policy

`src/macro_factor_pricing_engine/TreasuryPolicy.md` is the human-readable sovereign
rates policy. `src/macro_factor_pricing_engine/treasury_policy.py` writes it into the
project as structured Python records:

- required inputs and source names;
- expected-short-rate, term-premium, fiscal-credibility, valuation/technical, and
  cross-asset blocks;
- signal rules;
- fiscal credibility gate;
- cross-asset sizing overlay;
- segment positioning rules;
- add/reduce long-end-duration checklists;
- governance cadence.

It is not a live scorer. It codifies the decision-support policy for later backtesting.

### Rates Analysis Loop

The current thin slice is rates-only and runs in `analysis` mode. It does not trade.

One command runs:

```bash
PYTHONPATH=src python3 -m macro_factor_pricing_engine.app
```

The loop:

1. loads the committed 2026-06-18 rates snapshot through `SnapshotSource`;
2. consumes manually supplied `RegimeProbabilities`;
3. scores the snapshot with Treasury Block A-D logic;
4. sizes pending target weights across in-scope rates securities;
5. diffs against a blank/persistent inventory;
6. appends turnover rows to `.runtime/turnover_ledger.jsonl`;
7. computes duration, DV01, bucket exposure, and concentration flags;
8. prints a plain-language pending recommendation.

`regime_input.py` is deliberately marked:

```text
STAGE 1 PLACEHOLDER - regime classification from data is the priority unbuilt module.
```

The future classifier must emit the same `RegimeProbabilities` interface. No validation,
backtest, or golden-scenario module exists in this pass.

### Local Web Dashboard

Phase 1 of the frontend is implemented as a read-only local dashboard. It does not
compute regimes, scores, or weights, and it does not persist discretionary signals.

`src/macro_factor_pricing_engine/api.py` exposes:

```text
GET /api/state
```

The endpoint serializes the existing `run_analysis()` output into JSON for the UI:

- full regime probability distribution, not only the dominant regime;
- dominant regime and transition metadata;
- 4 x 4 macro-state/causal-mechanism grid axes;
- defined regime pairs;
- rates scores and fired triggers;
- pending target weights;
- asset-class names from the universe.

`frontend/` is a static SPA using Chart.js and plain HTML/CSS/JS. It renders:

- two-axis regime grid with active/undefined cells;
- transition banner when no regime holds more than 60%;
- full regime distribution bar/chart, with a local canvas fallback if Chart.js is not
  available;
- dominant-regime explanation;
- scores panel, with overlay modifier labelled as computed but not yet applied;
- pending target weights with one-decimal percentage precision.

Run locally after installing project dependencies:

```bash
PYTHONPATH=src uvicorn macro_factor_pricing_engine.api:app --reload
```

Then open `http://127.0.0.1:8000/`.

## Test Command

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

Focused test commands:

```bash
# Frontend/API seam only
PYTHONPATH=src python3 -m unittest tests.test_api_phase1

# Full suite
PYTHONPATH=src python3 -m unittest discover tests

# CLI smoke test
PYTHONPATH=src python3 -m macro_factor_pricing_engine.app
```

Current test coverage checks that:

- approved asset classes exist with research-scope membership;
- no tradeable instruments are available yet;
- regimes have causal stories and observable triggers;
- only meaningful state x mechanism pairs are defined;
- all four state profiles are present and transition-matrix rows sum to 1.0;
- stagflation duration positioning flips by causal mechanism;
- invalid `RegimeProbabilities` sums are rejected;
- valuation overlay is not in the macro channel set;
- human-input and universe-change triggers require confirmation;
- policy blocks trading while tickers are empty;
- broker API setup aliases resolve and missing credentials are reported without exposing
  secret values;
- benchmark horizons are present, valid against the universe, and sum to 1.0;
- `/api/state` serializes valid Phase 1 dashboard JSON and the frontend remains
  read-only;
- the dashboard root page and static frontend assets are served by the FastAPI app;
- regime detection lag budget exists in policy;
- Treasury policy exists as structured data, not an autopilot scorer.
- rates loop runs end-to-end on the committed snapshot;
- recommendation remains pending;
- weights sum to 1;
- turnover ledger appends;
- smoke check reproduces the hand-derived stance: overweight front-belly, underweight
  long end, overweight 5y TIPS.

## Next Module

The next planned module is Stage 1 regime classification:

- map public data series to the two-axis regime model;
- emit `RegimeProbabilities` through the same interface currently filled manually;
- enforce point-in-time availability and detection-lag charging;
- keep the rates recommendation loop unchanged when the classifier is added.

## Changelog

- `2026-06-23`: Refactored regimes into two axes, `MacroState x CausalMechanism`;
  added fiscal/sovereign as a macro channel; kept valuation/positioning as a separate
  overlay; added `RegimeProbabilities`; added the Treasury policy as structured code;
  preserved empty ticker dictionaries and no-trade safety invariants.
- `2026-06-23`: Added the rates-only end-to-end analysis loop using a committed
  2026-06-18 snapshot, manual regime probabilities, Treasury scoring, target sizing,
  turnover ledger, first-pass risk readout, and pending recommendation output. Stage 1
  regime classification remains the priority unbuilt module.
- `2026-06-23`: Added broker API credential setup metadata and environment readiness
  checks for Trading 212, Interactive Brokers, Robinhood, IG Group, Capital.com, and
  Plus500 without enabling live execution.
- `2026-06-24`: Replaced empty/US-placeholder universe membership with a
  UK-retail-accessible UCITS/LSE-listed research universe and platform capability
  matrix while keeping all allocation approvals closed.
- `2026-06-24`: Added horizon-specific strategic benchmark blends for `10y`, `5y`,
  `1y`, and `1q`, validated against the asset-class universe.
- `2026-06-24`: Added Phase 1 read-only FastAPI JSON seam and static frontend regime
  dashboard; Phase 2 ingestion remains intentionally unstarted.
- `2026-06-24`: Collapsed macro states to four structural quadrants, re-homed mechanism
  playbooks, and added state profiles plus a heuristic monthly transition matrix.
- `2026-06-24`: Hardened the local dashboard frontend with exact target-weight
  percentages, a loading/error status, static-route tests, and an offline-safe chart
  fallback.

## Methodology
Based on Macro Economy Machenism, build a asset allocation framework on retail accessible assets to harvest macro return with minimized risk.

Indicators to watch will be public accessible information only. 

Add human input function, so if i give an input of one observation of the market, one article, or a feed on X, it can be translated by a free AI API, somehow integrate this information to the existing public accessible information, and ask relavent questions to access the data source, validate the information, and maybe help with integrate to the current strategy. 

Summarized by extensive market research on how different asset responds to events and come up with the allocation advise. and explain the reason behind the recommended the strategy.

Build paper portfolio with precise sizing and backtest on the history market. Give clear guidance on how and when to trade. 

Live monitor the daily PnL, turnover of the strategy. 

Include Portfolio Analysis Diagnosis Tool to access the healthiness of the recommended strategy. 


## Prompt

No active implementation prompt. The latest prompt has been implemented: the regime
taxonomy now uses four structural macro states, state-level profiles, and a heuristic
monthly transition matrix.

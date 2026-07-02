# Macro Driven Tactical Asset Allocation
## **Project Introduction**

This project builds a top-down framework for two linked tasks: macro-driven tactical asset allocation, and (stage 2) policy-driven sub-asset-class portfolio construction and optimization.

Asset allocation is driven by a macro regime detection framework. The framework assumes that any market environment can be classified along two independent axes: a macro state (one of four structural growth/inflation quadrants — Goldilocks, Reflation, Stagflation, Disinflationary Slowdown) and a causal mechanism (one of four transmission mechanisms explaining why that state is occurring — e.g. ordinary cyclical dynamics, a currency/peg break, deliberate policy disruption, or leverage/institutional stress). Crossing these two axes gives a 4×4 grid of 16 possible regime cells; currently 8 of those cells have defined, research-backed playbooks, and the rest are left undefined until a distinct strategy case justifies building one out.

The mechanism axis matters because the same growth/inflation state can call for very different asset positioning depending on its cause — for example, stagflation driven by policy disruption is hostile to long-duration bonds, while stagflation driven by leverage/institutional stress can restore a flight-to-quality bid for the same bonds.

Extensive historical research — spanning major financial cycles, crises, and recoveries from 1900–2022 — informs which asset classes are expected to lead or lag under each defined regime pair. This produces theory-driven priors.

The model is intended to take in current cross-asset conditions (equities, credit, commodities, monetary and fiscal policy, currency, and rates) to infer the current regime as a soft probability distribution across the 16 cells, rather than a single hard label. 

A heuristic quarterly transition matrix, calibrated from historical regime persistence, encodes the assumption that a regime is most likely to persist unless a significant shock shifts probability mass toward another quadrant. This transition structure feeds into asset allocation tilts away from a strategic neutral benchmark, which is adjustable by investment horizon (10y, 5y, 1y, 1q).



## Current Implementation Status

The first implementation pass is complete. The repository now contains a small Python
package under `src/macro_factor_pricing_engine` with:

- a UK-retail UCITS/LSE-listed asset-class universe for research scope;
- two-axis macro regime definitions: macro state plus causal mechanism;
- state-level macro profiles and a heuristic quarterly transition matrix for the
  four structural macro quadrants;
- a policy module that records strategy governance, review triggers, risk controls, and
  human-input confirmation rules;
- a strategic overall-portfolio benchmark module with horizon-specific neutral SAA
  blends for `10y`, `5y`, `1y`, and `1q`;
- a structured Treasury strategy policy module derived from `TreasuryPolicy.md`;


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

- `TRANSITION_TIME_STEP = "quarterly"`;
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


### Rates Analysis Loop

The current thin slice is rates-only and runs in `analysis` mode. It does not trade.

One command runs:

```bash
PYTHONPATH=src python3 -m macro_factor_pricing_engine.app
```


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

## Prompt
# Prompt: Build Stage 1 Regime Classification Module

## Context
`src/macro_factor_pricing_engine/regime_input.py` is currently a placeholder marked
`STAGE 1 PLACEHOLDER - regime classification from data is the priority unbuilt module`.
It must be replaced with a deterministic classifier that consumes a fixed public-data
snapshot and emits a `RegimeProbabilities` object matching the existing interface in
`regimes.py`. Do not change the `RegimeProbabilities`, `Regime`, `MacroState`, or
`CausalMechanism` definitions in `regimes.py` — this module is a new consumer/producer
that feeds that existing interface, not a replacement for it.

## Deliverables

### 1. `data/regime_indicator_schema.py`
Define a frozen dataclass `RegimeIndicatorSnapshot` with one field per raw input listed
below. Every field is `float | None` (None = missing, must degrade gracefully, never
silently impute). Include a `snapshot_date: date` field and an `as_of_lag_days: int`
field per source to support point-in-time integrity checks (no lookahead).

Raw inputs (all from free public sources):
- growth: `ism_manufacturing_pmi`, `chicago_fed_nai`, `gdpnow_estimate`
- inflation: `cpi_yoy`, `core_cpi_yoy`, `breakeven_5y5y`
- policy_liquidity: `ust_2y_yield`, `ust_2y_yield_chg_1m`, `ust_10y_yield`,
  `ust_10y_yield_chg_1m`, `fed_funds_implied_path_chg_3m`, `nfci`
- risk_appetite: `ig_oas`, `ig_oas_chg_1m`, `hy_oas`, `hy_oas_chg_1m`, `vix`
- fiscal_sovereign: `acm_term_premium_10y`, `dxy_chg_3m`, `dxy_trend_direction`
- commodities: `broad_commodity_index_chg_3m`
- equities: `sp500_drawdown_from_52w_high`

### 2. `data/sources.py` (extend existing file)
Add fetch functions for each raw input above, using free public APIs only
(FRED via `fredapi` or direct HTTP, NY Fed ACM model CSV, CME FedWatch scrape or API).
Each function returns `(value: float | None, as_of_date: date)`. Follow the existing
no-lookahead pattern already used elsewhere in `data/sources.py`. Do NOT add any
Bloomberg or paid-data dependency here — that stays in the discretionary/manual path.

### 3. `regime_classifier.py` (new file)
Implement:
- `compute_channel_scores(snapshot: RegimeIndicatorSnapshot) -> ChannelScores`
  Returns a score in [-1, 1] for each of the five `MACRO_TRANSMISSION_CHANNELS`
  (growth, inflation, policy_liquidity, risk_appetite, fiscal_sovereign), using
  simple, explainable transformations (e.g. z-score vs trailing 3y window, or
  directional sign of the _chg fields). Document the exact formula per channel
  in docstrings — no black-box scoring.
- `derive_observable_triggers(scores: ChannelScores) -> frozenset[str]`
  Maps channel scores to the exact `observable_trigger_names` strings already used
  in `REGIME_DEFINITIONS` in `regimes.py` (e.g. `growth_momentum_positive`,
  `credit_spreads_widening_fast`, `real_yields_rising`). Pull the exact trigger name
  strings from `regimes.py` — do not invent new ones.
- `classify_regime(snapshot: RegimeIndicatorSnapshot) -> RegimeProbabilities`
  Uses the fired triggers to assign soft weights across the 8 currently-defined
  `REGIME_DEFINITIONS`. Any reasonable, explainable weighting scheme is acceptable
  for v1 (e.g. count of matched triggers per regime, normalized) as long as it's
  documented as heuristic, matches `asset_priors_are_heuristic = True` in spirit,
  and produces a valid `RegimeProbabilities` (weights sum to 1.0).

### 4. `regime_override.py` (new file)
Implement a `RegimeOverride` frozen dataclass: `state: MacroState`,
`mechanism: CausalMechanism`, `confidence: float`, `reason: str`, `entered_by: str`,
`entered_at: datetime`, `expires_at: datetime | None`.
Implement `apply_override(computed: RegimeProbabilities, override: RegimeOverride | None) -> RegimeProbabilities`:
- If `override` is None, return `computed` unchanged.
- If present, return a `RegimeProbabilities` with full weight on the specified
  regime pair (must exist in `REGIME_DEFINITIONS`, raise `KeyError` if undefined).
- The override must route through the existing `human_input_pending` policy trigger
  in `policy.py` — check for and honor its `requires_confirmation` flag rather than
  applying silently.
- Log both `computed` and the override in the returned object or a paired audit
  record, so a human can later compare "what the data said" vs "what was overridden,"
  and why — this history matters for evaluating whether overrides add value over time.

### 5. Tests (`tests/test_regime_classifier.py`)
- Snapshot with clearly bullish-growth/low-inflation data classifies with highest
  weight on `goldilocks x cyclical_no_acute_mechanism`.
- Snapshot with widening HY OAS + negative growth classifies with weight on one of
  the `leverage_institutional_breakdown` pairs.
- Missing/None fields degrade gracefully (lower confidence / wider distribution),
  never crash and never silently impute a fabricated value.
- `RegimeOverride` correctly overrides computed output and requires confirmation.
- `RegimeOverride` referencing an undefined regime pair raises `KeyError`.
- Full snapshot-to-classification path round-trips through `RegimeProbabilities`
  validation (weights non-negative, sum to 1.0).

## Explicit non-goals for this pass
- Do not wire this into `sizing.py` or the rates loop yet — that's a follow-up step
  once classification is validated standalone.
- Do not add any HMM, ML classifier, or statistically fitted model — this is a
  deterministic, rule-based, explainable v1, consistent with the project's existing
  heuristic-and-labeled-as-such approach.
- Do not add Bloomberg-sourced fields to the automated `data/sources.py` path —
  Bloomberg-only inputs (e.g. sovereign CDS from a terminal) stay in the discretionary
  `RegimeOverride.reason` free-text field, not as a structured automated input.

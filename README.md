# Macro-Factor-Pricing-Engine
The model builds a probabilistic framework to understand asset price movements through macroeconomic drivers instead of a deterministic prediction.

## Documentation

Full project documentation is available at [docs/PROJECT_DOCUMENTATION.md](docs/PROJECT_DOCUMENTATION.md).

## Current Implementation Status

The first implementation pass is complete. The repository now contains a small Python
package under `src/macro_factor_pricing_engine` with:

- a UK-retail UCITS/LSE-listed asset-class universe for research scope, with every
  instrument still unapproved for allocation;
- two-axis macro regime definitions: macro state plus causal mechanism;
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

`src/macro_factor_pricing_engine/regimes.py` records the two-axis macro regime layer.
It separates macro state from causal mechanism because the same state can require
opposite asset calls depending on why it exists.

Macro states:

- `goldilocks`
- `reflation`
- `stagflation`
- `disinflationary_slowdown`
- `crisis_liquidity_stress`
- `policy_tightening_shock`

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

Defined state x mechanism pairs:

| Macro state | Causal mechanism | Why defined |
|---|---|---|
| `goldilocks` | `cyclical_no_acute_mechanism` | benign expansion playbook |
| `reflation` | `cyclical_no_acute_mechanism` | nominal growth acceleration playbook |
| `stagflation` | `deliberate_policy_disruption` | inflation/policy/fiscal pressure dominates |
| `stagflation` | `leverage_institutional_breakdown` | stress can restore duration flight-to-quality |
| `disinflationary_slowdown` | `cyclical_no_acute_mechanism` | normal slowdown with easing optionality |
| `crisis_liquidity_stress` | `peg_or_promise_break` | anchor break/contagion playbook |
| `crisis_liquidity_stress` | `leverage_institutional_breakdown` | deleveraging and policy-response playbook |
| `policy_tightening_shock` | `deliberate_policy_disruption` | forced repricing from policy/real-rate shock |

The rest of the 6 x 4 grid is intentionally undefined because those pairs are not
distinct strategy playbooks yet. Each defined pair records the causal story, expected
leading asset classes, expected lagging asset classes, observable trigger names, and
mechanism-specific asset-map overrides. Leading/lagging lists are labelled as heuristic
theory-priors, not fitted estimates.

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
| Trading 212 | `TRADING212_API_KEY` | Configurable, not wired to execution |
| Interactive Brokers | `IBKR_GATEWAY_BASE_URL` | Configurable via Client Portal Gateway, not wired to execution |
| Robinhood | `ROBINHOOD_API_KEY`, `ROBINHOOD_PRIVATE_KEY` | Disabled until the exact official API surface is approved |
| IG Group | `IG_API_KEY`, `IG_USERNAME`, `IG_PASSWORD` | Configurable, not wired to execution |
| Capital.com | `CAPITAL_COM_API_KEY`, `CAPITAL_COM_IDENTIFIER`, `CAPITAL_COM_API_PASSWORD` | Configurable, not wired to execution |
| Plus500 | none | Unsupported unless Plus500 grants an official API integration |

Use `.env.example` as the local setup template. Real `.env` files are ignored by git.

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

The returned values are for a future broker-client layer only. They are not consumed by
the current recommendation loop.

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
- 6 x 4 macro-state/causal-mechanism grid axes;
- defined regime pairs;
- rates scores and fired triggers;
- pending target weights;
- asset-class names from the universe.

`frontend/` is a static SPA using Chart.js and plain HTML/CSS/JS. It renders:

- two-axis regime grid with active/undefined cells;
- transition banner when no regime holds more than 60%;
- full regime distribution bar/chart;
- dominant-regime explanation;
- scores panel, with overlay modifier labelled as computed but not yet applied;
- pending target weights.

Run locally after installing project dependencies:

```bash
PYTHONPATH=src uvicorn macro_factor_pricing_engine.api:app --reload
```

Then open `http://127.0.0.1:8000/`.

## Test Command

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

Current test coverage checks that:

- approved asset classes exist with research-scope membership;
- no tradeable instruments are available yet;
- regimes have causal stories and observable triggers;
- only meaningful state x mechanism pairs are defined;
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

## Methodology
Based on Macro Economy Machenism, build a asset allocation framework on retail accessible assets to harvest macro return with minimized risk.

Indicators to watch will be public accessible information only. 

Add human input function, so if i give an input of one observation of the market, one article, or a feed on X, it can be translated by a free AI API, somehow integrate this information to the existing public accessible information, and ask relavent questions to access the data source, validate the information, and maybe help with integrate to the current strategy. 

Summarized by extensive market research on how different asset responds to events and come up with the allocation advise. and explain the reason behind the recommended the strategy.

Build paper portfolio with precise sizing and backtest on the history market. Give clear guidance on how and when to trade. 

Live monitor the daily PnL, turnover of the strategy. 

Include Portfolio Analysis Diagnosis Tool to access the healthiness of the recommended strategy. 


## Prompt
TASK
Rebuild src/macro_factor_pricing_engine/regimes.py around a 4-state taxonomy.
Update __init__.py exports and tests to match. Do NOT build the transition-
intensity scoring engine (entropy / drift / hysteresis / PIT) — that is a
SEPARATE later module that will CONSUME the matrix this file defines. Keep the
CLI and the full unittest suite green.

──────────────────────────────────────────────
CHANGE 1 — collapse MacroState 6 -> 4
──────────────────────────────────────────────
Keep ONLY the four structural quadrants:
  GOLDILOCKS, REFLATION, STAGFLATION, DISINFLATIONARY_SLOWDOWN
REMOVE CRISIS_LIQUIDITY_STRESS and POLICY_TIGHTENING_SHOCK — they are
mechanisms, not states, and belong on the CausalMechanism axis (unchanged:
PEG_OR_PROMISE_BREAK, DELIBERATE_POLICY_DISRUPTION,
LEVERAGE_INSTITUTIONAL_BREAKDOWN, CYCLICAL_NO_ACUTE_MECHANISM).

──────────────────────────────────────────────
CHANGE 2 — re-home the 3 orphaned REGIME_DEFINITIONS pairs
(keep each pair's mechanism, leading/lagging assets, triggers, causal_story;
 only the state field changes)  -- all flagged USER TO CONFIRM
──────────────────────────────────────────────
  CRISIS_LIQUIDITY_STRESS x PEG_OR_PROMISE_BREAK
    -> DISINFLATIONARY_SLOWDOWN x PEG_OR_PROMISE_BREAK
       (sovereign/currency break -> demand collapse; risk-off, core-deflationary)
  CRISIS_LIQUIDITY_STRESS x LEVERAGE_INSTITUTIONAL_BREAKDOWN
    -> DISINFLATIONARY_SLOWDOWN x LEVERAGE_INSTITUTIONAL_BREAKDOWN  (2008 archetype)
  POLICY_TIGHTENING_SHOCK x DELIBERATE_POLICY_DISRUPTION
    -> DISINFLATIONARY_SLOWDOWN x DELIBERATE_POLICY_DISRUPTION  (Volcker archetype)
Result: 8 defined pairs total (same count as before, just re-homed).

──────────────────────────────────────────────
CHANGE 3 — add STATE-level structural profiles (new)
──────────────────────────────────────────────
The existing Regime dataclass is per-(state x mechanism) PLAYBOOK. Add a
separate STATE-level structural descriptor:

  @dataclass(frozen=True) MacroStateProfile:
    state, growth_direction, inflation_direction,
    typical_root_causes: tuple[str,...], typical_drivers: tuple[str,...],
    key_indicators: tuple[str,...]

  MACRO_STATE_PROFILES: Mapping[MacroState, MacroStateProfile]  (all 4)

Content (verbatim intent from the desk review):
  GOLDILOCKS  growth=stable_positive, inflation=low
    root_causes: productivity boom, supply-side expansion
    drivers: tech adoption, global trade expansion
    key_indicators: positive output gap closing without unit-labor-cost spikes
  REFLATION   growth=accelerating, inflation=rising
    root_causes: cyclical demand-pull, fiscal expansion
    drivers: post-recession inventory rebuild, infrastructure spend
    key_indicators: credit-creation velocity, steepening yield curve
  STAGFLATION growth=decelerating, inflation=sticky_high
    root_causes: supply-side shock, structural policy distortion
    drivers: energy blockades, structural de-globalization
    key_indicators: collapsing profit margins alongside rising input/commodity prices
  DISINFLATIONARY_SLOWDOWN growth=decelerating, inflation=falling
    root_causes: cyclical demand exhaustion, post-bubble deleveraging
    drivers: end of credit cycle, monetary policy biting
    key_indicators: rising inventory-to-sales ratio, widening credit spreads

──────────────────────────────────────────────
CHANGE 4 — add the state-only TRANSITION MATRIX (new; data only, no scoring)
──────────────────────────────────────────────
Monthly time step. Heuristic prior (NOT estimated — only ~16 episodes exist).
Rows MUST sum to 1.0 (the diagonal "stay" term is mandatory — it is the
persistence/inertia term).

  TRANSITION_TIME_STEP = "monthly"
  TRANSITION_MATRIX_IS_HEURISTIC = True
  Tier key (documentation): adjacent~0.15, diagonal~0.05, reversal~0.03,
    stay = 1 - sum(off-diagonals). Tiers are a starting key; economic
    asymmetries override them (see Slowdown->Stagflation).

  TRANSITION_MATRIX: Mapping[MacroState, Mapping[MacroState, float]]
    (G=Goldilocks R=Reflation S=Stagflation D=Disinflationary_Slowdown)
    FROM G:  R 0.15, S 0.03, D 0.15, G(stay) 0.67
    FROM R:  G 0.10, S 0.15, D 0.05, R(stay) 0.70
    FROM S:  G 0.03, R 0.05, D 0.15, S(stay) 0.77
    FROM D:  G 0.15, R 0.03, S 0.02, D(stay) 0.80

  Encoded asymmetries (keep — this is the point of a matrix vs a scalar):
    - Slowdown stickiest (0.80); main escape D->G (recovery).
    - R->S (0.15) > S->R (0.05): overheating tips to stagflation easily;
      climbing back out of sticky inflation is hard.

──────────────────────────────────────────────
CHANGE 5 — mechanism modifier (few knobs, heuristic)
──────────────────────────────────────────────
The base matrix is state-only. The mechanism conditions transition odds.
Implement ONE concrete modifier now; others identity (TODO).
  MECHANISM_ROW_MODIFIERS: Mapping[CausalMechanism, Mapping[MacroState, float]]
    LEVERAGE_INSTITUTIONAL_BREAKDOWN: { DISINFLATIONARY_SLOWDOWN: 3.0 }
      # deleveraging accelerates the path into slowdown/crisis
    all other mechanisms: {} (identity)  # TODO confirm with more data
  Function: transition_row_for(from_state, mechanism) ->
    apply multipliers to the base row, then RENORMALISE to sum 1.0.

──────────────────────────────────────────────
HELPERS (stable signatures)
──────────────────────────────────────────────
  state_profile(state) -> MacroStateProfile
  transition_row(from_state) -> Mapping[MacroState, float]        # base
  transition_prob(from_state, to_state) -> float
  transition_row_for(from_state, mechanism) -> Mapping[MacroState, float]  # modified
  validate_transition_matrix() -> None   # rows sum 1.0 (tol 1e-9), no negatives,
                                         # keys are exactly the 4 MacroState; called at import

PRESERVE UNCHANGED (consumers depend on these):
  RegimeProbabilities (incl. dominant_regime AND is_transition(0.6) — keep both),
  Regime, AssetMapOverride, ValuationOverlay, MACRO_TRANSMISSION_CHANNELS,
  MACRO_TRANSMISSION_LOGIC, get_regime, regime_names, REGIME_DEFINITIONS,
  DEFINED_REGIME_PAIRS, UNDEFINED_REGIME_PAIR_RATIONALE.
  Every Regime keeps observable_trigger_names, causal_story,
  asset_priors_are_heuristic=True.

UPDATE:
  __init__.py — remove the two deleted states from any export list.
  tests/test_policy_and_regimes.py — update the expected DEFINED_REGIME_PAIRS
    set to the 8 re-homed pairs; keep the is_transition 0.55/0.65 test as-is.
  ADD tests: every TRANSITION_MATRIX row sums to 1.0; transition_row_for under
    LEVERAGE_INSTITUTIONAL_BREAKDOWN raises D's probability vs base then
    renormalises to 1.0; all 4 MACRO_STATE_PROFILES present.

ACCEPTANCE
  python -m unittest discover tests   passes
  validate_transition_matrix() passes at import
  MacroState has exactly 4 members; grep finds zero refs to the removed states
  CLI (app.py) still runs

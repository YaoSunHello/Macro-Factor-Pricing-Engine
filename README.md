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
Add a local web frontend + ingestion pipeline to the engine. Engine logic is
READ-ONLY: the frontend renders existing output and stores pending signals; it
does not compute regimes, scores, or weights. Build in two phases with a hard
stop between them. Do not modify regimes.py, sizing.py, rates_scorer.py,
policy.py, or universe.py. CLI (app.py) and existing tests must still pass.

──────────────────────────────────────────────
PHASE 1 — backend JSON seam + read-only regime dashboard
──────────────────────────────────────────────
1a. NEW: src/macro_factor_pricing_engine/api.py
    A thin FastAPI app. ONE endpoint for Phase 1:
      GET /api/state  -> serializes run_analysis() (from app.py) to JSON:
        - regime_distribution: list of {state, mechanism, name, weight,
          causal_story, leading_assets, lagging_assets} for EVERY regime in
          RegimeProbabilities.weights (full distribution, NOT just dominant)
        - dominant: {state, mechanism, name}
        - is_transition: bool   (RegimeProbabilities.is_transition(0.6))
        - max_mass: float       (the actual max weight, so UI can show "0.55")
        - defined_pairs: the (state, mechanism) pairs in DEFINED_REGIME_PAIRS
        - scores: {cycle, valuation, fiscal_veto, overlay_modifier,
          composite, fired_triggers}
        - target_weights: list of {ticker, bucket, weight}
        - asset_classes: universe.asset_classes()  (for the grid axes)
    Serialization helper goes in api.py only — do not add methods to the
    frozen dataclasses.

1b. NEW: frontend/ (static SPA; Chart.js, no heavy framework needed)
    Components:
      - TWO-AXIS REGIME GRID: rows = MacroState (6), cols = CausalMechanism (4).
        Shade each cell by its probability mass. The 8 cells in defined_pairs
        are active; the other 16 are greyed (undefined — not a strategy yet).
        Dominant cell highlighted.
      - TRANSITION BANNER: when is_transition is true, show a clear
        "TRANSITION — no regime holds >60% (max = {max_mass:.0%})" warning.
      - DISTRIBUTION BAR: every regime with its weight, sorted desc — this is
        the full distribution the rest of the engine discards.
      - DOMINANT CARD: state + mechanism + causal_story + leading/lagging assets.
      - SCORES PANEL: cycle/valuation/fiscal_veto/overlay_modifier/composite.
        Label overlay_modifier "computed, not yet applied" (it is inert today).
    Read-only. No inputs in Phase 1.

PHASE 1 ACCEPTANCE
  - GET /api/state returns valid JSON; regime_distribution sums to ~1.0.
  - Grid renders 6x4; exactly 8 active cells match DEFINED_REGIME_PAIRS.
  - Transition banner toggles correctly against a forced low-mass fixture.
  - Existing CLI + unittest suite still green.
  *** STOP. Do not start Phase 2 until Phase 1 is reviewed. ***

──────────────────────────────────────────────
PHASE 2 — ingestion + local LLM draft + confirmation commit
──────────────────────────────────────────────
2a. NEW endpoints in api.py:
      POST /api/ingest  -> accepts pdf | image | raw text
        - pdf: extract text (pdfplumber/pypdf)
        - image/photo: OCR (tesseract) to text
        - text: passed through
        Then call the local extractor; RETURN a DRAFT signal. Do NOT persist.
      POST /api/signal/confirm -> takes a (possibly user-edited) draft and
        writes it to a pending-signal store (jsonl, like turnover_ledger).
        Status = PENDING. This is the only path that persists a signal.

2b. NEW: src/macro_factor_pricing_engine/discretionary_signal.py
    Schema (the draft the extractor fills):
      as_of, target_type ("regime"|"asset_class"), target, score[-1,1],
      confidence[0,1], half_life_days, expires, corroboration[list],
      rationale, and per-calibration-field anchor strings.
    HARD RULES:
      - target validated: if asset_class -> must be in universe.asset_classes();
        if regime -> target must name a valid MacroState/CausalMechanism.
      - Layer 1 (as_of, direction/sign) and Layer 2 (taxonomy mapping) are
        extracted. Layer 3 (score, confidence, half_life) are PROPOSED with a
        required anchor string each; never committed without confirm.
      - effective contribution = score * confidence * decay(t); expired -> 0.
      - routes to regime-probability evidence OR a Block-D positioning input.
        MUST NOT import or write to sizing.py.

2c. LOCAL LLM (no data egress)
    - Use Ollama with a local instruct model (configurable model name).
    - Strict JSON output, validated against the schema; reject/repair invalid.
    - Prompt the model to SEPARATE reproducible extraction from proposed
      calibration, and to populate anchor strings (why this score, why this
      confidence). No network calls to hosted APIs.

2d. FRONTEND additions:
    - Upload widget (pdf/photo) + manual-text box.
    - Draft-review panel: shows extracted + proposed fields, ALL editable,
      with anchor strings visible. CONFIRM / REJECT buttons.
    - Pending-signals list with score/confidence/decay/expiry.

PHASE 2 ACCEPTANCE
  - Ingesting a sample text returns a schema-valid draft, nothing persisted.
  - Confirm writes exactly one PENDING row; reject writes nothing.
  - Invalid target (bucket not in universe) is rejected before draft returns.
  - No module imports sizing.py from the signal path.
  - No outbound network call in the ingest path (local model only).

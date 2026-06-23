# Macro-Factor-Pricing-Engine
The model builds a probabilistic framework to understand asset price movements through macroeconomic drivers instead of a deterministic prediction.

## Documentation

Full project documentation is available at [docs/PROJECT_DOCUMENTATION.md](docs/PROJECT_DOCUMENTATION.md).

## Current Implementation Status

The first implementation pass is complete. The repository now contains a small Python
package under `src/macro_factor_pricing_engine` with:

- an asset-class universe scaffold with ticker dictionaries intentionally left empty;
- two-axis macro regime definitions: macro state plus causal mechanism;
- a policy module that records strategy governance, review triggers, risk controls, and
  human-input confirmation rules;
- a structured Treasury strategy policy module derived from `TreasuryPolicy.md`;
- a rates-only end-to-end analysis loop that runs from committed snapshot data to a
  pending recommendation;
- a broker API setup registry that validates environment-variable readiness for
  Trading 212, Interactive Brokers, Robinhood, IG Group, Capital.com, and Plus500;
- a focused unit test suite for the universe, regime, and policy records.

The system is not tradeable yet. Asset classes are approved as categories, but no ticker
can receive a paper or live allocation until the ticker dictionary is explicitly filled
and approved.

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
│       ├── treasury_policy.py
│       ├── TreasuryPolicy.md
│       ├── universe.py
│       ├── api_keys.py
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
│   └── test_policy_and_regimes.py
├── pyproject.toml
├── README.md
├── Notes
└── LICENSE
```

## Implemented Modules

### Universe Scaffold

`src/macro_factor_pricing_engine/universe.py` defines the approved asset-class map.
The non-rates asset classes remain empty. The four rates buckets now have starter
membership proxies marked `USER TO CONFIRM`, but every `approved_for_allocation` flag is
`False`, so `has_tradeable_instruments()` still returns `False`.

- `short_duration_government_bonds`
- `intermediate_duration_government_bonds`
- `long_duration_government_bonds`
- `inflation_linked_bonds`

Membership is used only for analysis scope. Allocation approval remains separate and
human-gated.

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

## Test Command

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

Current test coverage checks that:

- approved asset classes exist but ticker dictionaries are blank;
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

## Methodology
Based on Macro Economy Machenism, build a asset allocation framework on retail accessible assets to harvest macro return with minimized risk.

Indicators to watch will be public accessible information only. 

Add human input function, so if i give an input of one observation of the market, one article, or a feed on X, it can be translated by a free AI API, somehow integrate this information to the existing public accessible information, and ask relavent questions to access the data source, validate the information, and maybe help with integrate to the current strategy. 

Summarized by extensive market research on how different asset responds to events and come up with the allocation advise. and explain the reason behind the recommended the strategy.

Build paper portfolio with precise sizing and backtest on the history market. Give clear guidance on how and when to trade. 

Live monitor the daily PnL, turnover of the strategy. 

Include Portfolio Analysis Diagnosis Tool to access the healthiness of the recommended strategy. 


## Prompt
# Macro-Factor-Pricing-Engine — Module: End-to-End Framework Loop (Asset Class #1: Rates)

## Context
Governance-first repo with: universe scaffold, two-axis regimes
(MacroState x CausalMechanism, soft RegimeProbabilities), policy.py, and
treasury_policy.py (Block A-D rules ported from TreasuryPolicy.md). Existing
invariants MUST hold.

This prompt builds the FULL recommendation loop for RATES ONLY, as a THIN
end-to-end slice — first-pass modules wired together so the system produces a
real, explained portfolio recommendation, not production-grade components.

Two hard design decisions for this pass:
- STAGE 1 (regime classification from data) is NOT built. The regime is SUPPLIED
  MANUALLY as a RegimeProbabilities input. Mark this everywhere as the priority
  module to fill next; the loop must consume regime probs through the SAME
  interface a future classifier would emit, so it drops in without refactor.
- NO validation / backtest / golden-scenario module. Do not build one; remove any
  validation-module stub if present. Keep ONLY consistency unit tests.

Runs in analysis/paper mode on a committed data SNAPSHOT. Nothing trades.

## Objective
From a BLANK portfolio and a fixed scope of input securities, the loop:
load snapshot data -> take manual regime input -> score (treasury_policy) ->
size target weights -> diff vs inventory -> log turnover -> compute risk readout
-> emit an explained PENDING recommendation. One command runs it and prints output.

## Components

### 1. universe.py — scope the securities
- Populate the four rates buckets (short/intermediate/long-duration govt, ILBs)
  with a STARTER list of liquid proxies, each marked "# USER TO CONFIRM", schema:
  { ticker, bucket, role, duration_proxy_years, approved_for_allocation: False }.
- Keep MEMBERSHIP vs approved_for_allocation distinct. has_tradeable_instruments()
  stays False. The engine may only build from securities in this scope.

### 2. data/ — pluggable source + committed snapshot
- DataSource interface with an `as_of` arg enforcing no-lookahead (no obs dated > as_of).
- SnapshotSource: reads a COMMITTED fixture of the 2026-06-18 tape (10y~4.46,
  2y~4.19, 5y BE~2.31, ACMTP10~0.73, core PCE 3.3, CPI 4.2, plus the other §3
  signals). FredSource: a stub behind the same interface, allowed-missing, for later.
- Returns clean aligned RAW series only; derived metrics belong to the scorer.

### 3. regime input (STAGE 1 STUB)
- A function/config that supplies current RegimeProbabilities MANUALLY
  (default fixture: stagflation x deliberate_policy_disruption, high mass).
- Big inline marker: "STAGE 1 PLACEHOLDER — regime classification from data is the
  priority unbuilt module; same RegimeProbabilities interface a classifier will emit."

### 4. scorer (wire treasury_policy.py to data)
- Compute derived metrics (real policy rate, 3m-ann vs y/y, TP percentile,
  breakeven-vs-realised, bid-to-cover z-score, momentum MAs).
- Run Block A-D -> Cycle score, Valuation score, Block C gate, overlay modifier
  -> composite signal + list of fired triggers, conditioned on the regime input.

### 5. sizing
- §6 matrix + an EXPLICIT, configurable sizing convention (e.g. score -> bucket
  weight, with concentration caps) -> target weights across the in-scope securities,
  from blank. Weights sum to 1.
- Steepener / curve trades are RELATIVE positions: surface as a flagged note,
  do NOT force into the weight vector.

### 6. inventory log
- Persistent portfolio snapshot (positions, weights, bucket, duration). Starts blank.

### 7. turnover / allocation log
- Append-only ledger: every recommended change (date, security, from->to weight,
  composite signal, fired trigger, regime, reason). Never overwrites.

### 8. risk readout (first-pass only)
- From the current/target snapshot: portfolio duration & DV01, per-bucket exposure,
  concentration vs caps, simple flag if a cap is breached. (Vol target / full risk
  model remain pending — do not build.)

### 9. explainability
- Every recommendation carries a plain-language "why": regime (+ probs), Cycle &
  Valuation scores, which block/trigger drove it, overlay effect, sizing rationale.

### 10. orchestrator (app.py)
- One entry point runs steps 2->9 end-to-end and PRINTS: regime used, scores,
  target portfolio, turnover vs blank, risk readout, and the explanation.
- Output is a PENDING adjustment (policy.py: human input creates pending only,
  never auto-moves). mode = "analysis"; live trading disabled.

## Governance (preserve)
- Pending-only recommendations; human-gated; no execution.
- has_tradeable_instruments() stays False; no approved_for_allocation = True.
- No-lookahead enforced at the data interface.

## Tests (consistency / smoke ONLY — not validation)
- Loop runs end-to-end on the snapshot and emits a recommendation.
- Gate stays False; recommendation is pending; weights sum to 1; turnover log appends.
- SMOKE check (label it as wiring, NOT validation, NOT edge): snapshot + the default
  stagflation x deliberate-policy regime reproduces the hand-derived stance
  (OW belly, UW long-end, OW 5y TIPS). State in the test docstring this only proves
  the loop reproduces a known hand calc, not that the policy is correct.

## Constraints
- Minimal clean diff; first-pass simplicity; no speculative abstraction; follow
  existing conventions. Update README + Notes (the manual-regime stub, dropped
  validation, the loop) + CHANGELOG.

## Out of scope (do not build)
Stage 1 classification, any validation/backtest/golden-scenario module, vol-target/
full risk model, other asset classes, live trading, real-feed wiring beyond the stub.

## Deliverable summary
End with: the securities in scope, a sample end-to-end run (regime -> scores ->
target portfolio -> risk -> explanation), and which tests pass.

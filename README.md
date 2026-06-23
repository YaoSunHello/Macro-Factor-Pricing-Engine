# Macro-Factor-Pricing-Engine
The model builds a probabilistic framework to understand asset price movements through macroeconomic drivers instead of a deterministic prediction.

## Current Implementation Status

The first implementation pass is complete. The repository now contains a small Python
package under `src/macro_factor_pricing_engine` with:

- an asset-class universe scaffold with ticker dictionaries intentionally left empty;
- two-axis macro regime definitions: macro state plus causal mechanism;
- a policy module that records strategy governance, review triggers, risk controls, and
  human-input confirmation rules;
- a structured Treasury strategy policy module derived from `TreasuryPolicy.md`;
- a focused unit test suite for the universe, regime, and policy records.

The system is not tradeable yet. Asset classes are approved as categories, but no ticker
can receive a paper or live allocation until the ticker dictionary is explicitly filled
and approved.

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
|       └── app.py

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
Each asset class is represented by an empty dictionary for now:

- `us_equities`
- `global_developed_equities`
- `emerging_market_equities`
- `short_duration_government_bonds`
- `intermediate_duration_government_bonds`
- `long_duration_government_bonds`
- `inflation_linked_bonds`
- `investment_grade_credit`
- `high_yield_credit`
- `gold`
- `broad_commodities`
- `usd_proxy`
- `cash`

The helper `has_tradeable_instruments()` returns `False` until at least one asset class
has an approved instrument.

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
- regime detection lag budget exists in policy;
- Treasury policy exists as structured data, not an autopilot scorer.

## Next Module

The next planned module is the indicator layer:

- map public data series to growth, inflation, policy/liquidity, and risk appetite;
- record source, cadence, release lag, and transform for every indicator;
- define auditable signal transforms and thresholds;
- enforce point-in-time availability before any signal can affect a regime score.

## Changelog

- `2026-06-23`: Refactored regimes into two axes, `MacroState x CausalMechanism`;
  added fiscal/sovereign as a macro channel; kept valuation/positioning as a separate
  overlay; added `RegimeProbabilities`; added the Treasury policy as structured code;
  preserved empty ticker dictionaries and no-trade safety invariants.

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

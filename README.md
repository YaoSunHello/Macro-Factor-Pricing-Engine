# Macro-Factor-Pricing-Engine
The model builds a probabilistic framework to understand asset price movements through macroeconomic drivers instead of a deterministic prediction.

## Current Implementation Status

The first implementation pass is complete. The repository now contains a small Python
package under `src/macro_factor_pricing_engine` with:

- an asset-class universe scaffold with ticker dictionaries intentionally left empty;
- macro transmission logic and observable regime definitions;
- a policy module that records strategy governance, review triggers, risk controls, and
  human-input confirmation rules;
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
│       └── universe.py
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

`src/macro_factor_pricing_engine/regimes.py` records the macro mechanism layer requested
in the prompt. It models the transmission channels:

- growth;
- inflation;
- policy/liquidity;
- risk appetite.

The current regime definitions are:

- `goldilocks`
- `reflation`
- `stagflation`
- `disinflationary_slowdown`
- `crisis_liquidity_stress`
- `policy_tightening_shock`

Each regime records the causal story, expected leading asset classes, expected lagging
asset classes, and observable trigger names. These are definitions only; the indicator
layer that scores live data has not been implemented yet.

### Policy Module

`src/macro_factor_pricing_engine/policy.py` records the strategy-level policy before the
allocation engine exists. The current policy states:

- objective: maximise risk-adjusted return using Sharpe and Calmar, not raw return;
- no approved ticker can receive a target weight;
- human input can only create a pending adjustment and can never automatically move the
  portfolio;
- no-lookahead data handling is mandatory;
- risk model, vol target, concentration caps, and turnover budget are pending Module 4.

Recorded strategy triggers:

- `scheduled_monthly_review`
- `regime_transition`
- `policy_shock`
- `liquidity_stress`
- `human_input_pending`
- `instrument_universe_change`

The human-input and instrument-universe-change triggers require explicit confirmation.

## Test Command

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

Current test coverage checks that:

- approved asset classes exist but ticker dictionaries are blank;
- no tradeable instruments are available yet;
- regimes have causal stories and observable triggers;
- human-input and universe-change triggers require confirmation;
- policy blocks trading while tickers are empty.

## Next Module

The next planned module is the indicator layer:

- map public data series to growth, inflation, policy/liquidity, and risk appetite;
- record source, cadence, release lag, and transform for every indicator;
- define auditable signal transforms and thresholds;
- enforce point-in-time availability before any signal can affect a regime score.

## Methodology
Based on Macro Economy Machenism, build a asset allocation framework on retail accessible assets to harvest macro return with minimized risk.

Indicators to watch will be public accessible information only. 

Add human input function, so if i give an input of one observation of the market, one article, or a feed on X, it can be translated by a free AI API, somehow integrate this information to the existing public accessible information, and ask relavent questions to access the data source, validate the information, and maybe help with integrate to the current strategy. 

Summarized by extensive market research on how different asset responds to events and come up with the allocation advise. and explain the reason behind the recommended the strategy.

Build paper portfolio with precise sizing and backtest on the history market. Give clear guidance on how and when to trade. 

Live monitor the daily PnL, turnover of the strategy. 

Include Portfolio Analysis Diagnosis Tool to access the healthiness of the recommended strategy. 


## Prompt
# Macro-Factor-Pricing-Engine — Module: Two-Axis Regime Refactor

## Context
This repo already has a governance-first scaffold: `universe.py` (approved
asset-class map, all ticker dicts empty, `has_tradeable_instruments()` returns
False), `regimes.py` (six macro-state definitions over four transmission
channels: growth, inflation, policy/liquidity, risk appetite), `policy.py`
(objective, pending-only human input, no-lookahead, strategy triggers), and a
unit-test suite. The system is intentionally NOT tradeable.

Preserve every existing safety invariant. This module is an architectural
refactor of the regime layer plus two channel additions. Do NOT build the live
data/indicator scoring layer, the allocation engine, or Module 4 risk model.

## Objective
Regime is currently single-axis (macro state). Add a second, orthogonal axis —
the causal MECHANISM — because state tells you what growth/inflation are doing
and mechanism tells you why, and the "why" is what disambiguates positioning
when the state is identical. Restructure regime records to (a) carry both axes,
(b) let mechanism modify the asset map, and (c) support probabilistic (soft)
assignment so transitions are a blended state, not a hard flip.

## Required changes

### regimes.py
1. `MacroState` enum: the existing six (goldilocks, reflation, stagflation,
   disinflationary_slowdown, crisis_liquidity_stress, policy_tightening_shock).
2. `CausalMechanism` enum: peg_or_promise_break, deliberate_policy_disruption,
   leverage_institutional_breakdown, and a benign `cyclical_no_acute_mechanism`
   for non-crisis states.
3. A `Regime` is the pair (state, mechanism) plus: causal_story,
   leading_assets, lagging_assets, observable_trigger_names, and an
   `asset_map_overrides` field where mechanism modifies the base state's map.
   Define ONLY the meaningful pairs — not the full 6×4 grid. Mechanism defaults
   to `cyclical_no_acute_mechanism` for benign states.
4. Make the override do real work with this concrete case used as a test anchor:
   - stagflation × deliberate_policy_disruption → long_duration_government_bonds
     moves to strong underweight (term-premium/fiscal risk dominates);
   - stagflation × leverage_institutional_breakdown → long_duration_government_bonds
     can rally (flight-to-quality once policy responds).
   Same state, opposite duration call — this is the reason the axis exists.
5. Add a `RegimeProbabilities` structure: a mapping of Regime → weight, weights
   sum to 1.0 (validate, with float tolerance). The eventual indicator layer
   emits this; the allocation layer will blend on it. Provide a helper to flag a
   transition when no single regime holds > 0.6 of the mass.
6. Add `fiscal_sovereign` to the transmission-channel set (it is a genuine
   channel, not reducible to policy or risk — see gilts 2022, US term premium).
7. Do NOT add valuation/positioning as a channel. It is a timing OVERLAY, not a
   macro channel. Create a separate `ValuationOverlay` placeholder concept,
   parallel to regimes, documented as "owned outside the macro→asset mapping;
   gates entry timing." Leave its scoring unimplemented.
8. Label leading/lagging asset lists as heuristic priors (a field or explicit
   docstring flag), since each regime has only ~2–4 historical instances — these
   are theory-priors, not fitted estimates.

### universe.py
- No tickers. `has_tradeable_instruments()` still returns False.
- Add an optional `scoring_module` reference per asset class (None for now) so a
  future rates module can attach to short_/intermediate_/long_duration_government
  _bonds and inflation_linked_bonds. Seam only; wire nothing.

### policy.py
- Preserve all invariants (pending-only human input, no-lookahead, False-by-default).
- Add `regime_detection_lag_budget` to the pending Module-4 controls: the signal
  layer will call turns late; the backtest must be charged for detection lag
  rather than assuming clean timing.
- Add a `benchmark_or_liability_reference` field marked pending/unconfirmed, and
  a note that the Sharpe/Calmar objective is currently asset-only.
- `regime_transition` trigger fires on a probability-mass shift past threshold
  (per RegimeProbabilities), not a hard state flip.

### tests
Extend the suite to assert:
- every defined (state, mechanism) pair is internally consistent and only
  meaningful pairs exist;
- the stagflation override flips long-duration positioning between the two
  mechanisms;
- RegimeProbabilities reject weights that don't sum to 1.0; transition helper
  triggers below the 0.6 threshold;
- valuation overlay is NOT in the channel set;
- `has_tradeable_instruments()` is still False;
- `regime_detection_lag_budget` exists in policy.

## Constraints
- Minimal, clean diff. No dead code, no speculative abstraction.
- Follow existing package/style conventions. Update README and Notes with the
  new two-axis model and a CHANGELOG entry.

## Out of scope (do not build)
Live data ingestion, indicator scoring functions, the allocation/optimization
engine, Module 4 risk model implementation, any ticker population.

## Deliverable summary
End with: the (state × mechanism) matrix you defined, which pairs you left
undefined and why, and confirmation all tests pass.

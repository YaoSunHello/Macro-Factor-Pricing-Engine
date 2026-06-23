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
ROLE
You are a quantitative macro strategist and Python engineer. Build a retail-accessible
asset allocation system that earns macro-driven return per unit of risk, using only
publicly/freely available data. Prioritise clean, modular code over abstraction; leave
no dead code. Build incrementally, one module at a time, and confirm the design of each
module with me before writing the next.

OBJECTIVE
Maximise risk-adjusted return (target: Sharpe and Calmar, not raw return) of a portfolio
of retail-tradeable instruments, by reading the macro environment and tilting allocations
accordingly. Every allocation call must come with the economic reasoning behind it.

HARD CONSTRAINTS
- Universe: only retail-accessible, liquid instruments (broad ETFs across equity regions,
  govt/IG/HY credit, duration buckets, gold/commodities, USD/FX proxies, cash). Propose
  the specific ticker set and justify it.
- Data: public/free only (e.g. FRED, Yahoo/Stooq, Treasury, ECB/BoE, public CFTC/COT,
  shadow-rate and financial-conditions series). List every source and its update cadence.
- AI calls: use a free AI API only, for the human-input module below.
- No lookahead: all backtests must be point-in-time; respect each series' real release lag.

BUILD IN THIS ORDER (confirm each before proceeding)

1. MACRO MECHANISM & REGIME LAYER
   Define the economic transmission logic (growth, inflation, policy/liquidity, risk
   appetite) and a small set of identifiable regimes. State, per regime, the causal story
   and which asset classes should lead/lag. Ground regimes in observable public indicators,
   not latent abstractions.

2. INDICATOR LAYER
   Map each public series to the macro variable it proxies. Define how raw series become
   signals (transforms, z-scores, thresholds, release-lag handling). Keep it minimal and
   auditable.

3. ASSET-RESPONSE RESEARCH
   Summarise how each asset class has historically responded to each regime/event type,
   citing the evidence. Produce a regime-to-asset-tilt mapping with expected sign and a
   confidence level. Flag where the historical record is thin or conflicting.

4. ALLOCATION ENGINE
   Translate live signals into target weights under an explicit risk model (vol targeting
   and/or risk-parity baseline + regime tilts). Specify constraints (per-asset caps, gross/
   net, turnover budget) and the rebalancing rule.

5. HUMAN-INPUT MODULE
   Accept a free-text observation, article, or X post. Then: (a) translate/normalise via the
   free AI API; (b) extract structured claims and tag which macro variable/regime each bears
   on; (c) assess source credibility and ask me targeted clarifying questions to validate it;
   (d) propose a tentative, confidence-weighted signal adjustment — and require my explicit
   confirmation before it can affect any weight. Never let unvalidated input move the portfolio.

6. PAPER PORTFOLIO & BACKTEST
   Implement precise position sizing and the trade rules: what triggers a trade, when to
   rebalance, and the no-trade band. Backtest with realistic transaction costs and slippage
   against a stated benchmark (e.g. 60/40). Report CAGR, vol, Sharpe, Calmar, max drawdown,
   turnover, hit rate, and regime-conditional performance. Give explicit "how and when to
   trade" guidance an end user could follow.

7. LIVE MONITORING
   Daily dashboard: PnL (cumulative and per-sleeve), current vs target weights, turnover,
   active risk, regime state, and any pending human-input adjustments awaiting confirmation.

8. PORTFOLIO DIAGNOSTIC TOOL
   Assess strategy health: factor/sector concentration, drawdown decomposition, signal decay,
   stress/scenario sensitivity, capacity, and robustness to parameter perturbation. Output a
   clear health verdict with the specific numbers behind it.

OUTPUT STANDARDS
- Every recommendation states its reasoning and the data points that drive it.
- Presentation-ready output suitable to show to a non-specialist.
- Surface assumptions and limitations explicitly; never present a fragile result as robust.

START
Before coding, confirm: (1) the instrument universe, (2) the data sources and their lags,
(3) the regime definitions. Then proceed module by module.

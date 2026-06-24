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
- a structured Treasury strategy policy module derived from `TreasuryPolicy.md`;
- a rates-only end-to-end analysis loop that runs from committed snapshot data to a
  pending recommendation;
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

TASK
Repopulate the asset-class universe in
  src/macro_factor_pricing_engine/universe.py
from empty/US-placeholder state to a UK-retail-tradable UCITS universe.
Do NOT change any other file. Do NOT flip any approval flag to True.

WHY (context — do not remove this design intent)
The current rates proxies (SHV, SHY, IEF, TLT, VGLT, TIP, VTIP, VGIT) are
US-domiciled ETFs. Under PRIIPs/KID rules a UK retail client cannot buy these
on any FCA platform (no Key Information Document → order blocked). They must be
replaced with the UCITS (Irish-domiciled, LSE-listed) equivalent. Equity,
credit, gold, commodity, usd_proxy and cash buckets are currently empty and
must be filled.

HARD CONSTRAINTS (these will be tested — see ACCEPTANCE)
1. Keep these exported symbols and their existing signatures unchanged:
   ASSET_CLASS_UNIVERSE, ASSET_CLASS_SCORING_MODULES, asset_classes(),
   scoring_module_for(), has_tradeable_instruments(), rates_securities().
   (sizing.py, app.py, __init__.py import from here — do not break them.)
2. has_tradeable_instruments() MUST still return False after your change.
   Membership ≠ approval: set approved_for_allocation=False on EVERY security.
3. ASSET_CLASS_SCORING_MODULES must stay keyed by the same set of asset classes
   as ASSET_CLASS_UNIVERSE (it is derived from it — keep that derivation).
4. rates_securities() must remain non-empty and cover the four rate buckets.
5. The four rate-bucket names must stay exactly:
   short_duration_government_bonds, intermediate_duration_government_bonds,
   long_duration_government_bonds, inflation_linked_bonds.

SCHEMA per security (extend the existing one, don't invent a parallel format)
  ticker, bucket, role, ccy, domicile, listing, isin, replaces,
  approved_for_allocation (always False),
  duration_proxy_years (rates buckets only)
- isin is the cross-platform identifier (tickers vary by currency/acc-dist line).
- replaces = the US proxy this UCITS line stands in for (None for new buckets).
- Add a module-level _sec(...) helper to build records and keep this DRY.

UNIVERSE TO POPULATE (representative tickers; one role line each)
us_equities:                 CSPX (S&P500 acc), VUSA (S&P500 dist)
global_developed_equities:   SWDA (MSCI World acc), VEVE (FTSE Dev dist)
emerging_market_equities:    EIMI (MSCI EM IMI acc), VFEM (FTSE EM dist)
short_duration_govt_bonds:   IB01 (0-1yr UST, dur≈0.4, replaces SHV),
                             IBTA (1-3yr UST, dur≈1.9, replaces SHY)
intermediate_duration_govt:  IBTM (7-10yr UST, dur≈7.5, replaces IEF)
long_duration_govt_bonds:    IDTL (20+yr UST acc, dur≈16.5, replaces TLT),
                             DTLA (20+yr UST dist, dur≈16.5, replaces VGLT)
inflation_linked_bonds:      ITPS (broad TIPS, dur≈6.5, replaces TIP)
investment_grade_credit:     LQDE (USD IG corp)
high_yield_credit:           IHYU (USD HY corp)
gold:                        SGLN (iShares Physical Gold), SGLD (Invesco)
broad_commodities:           CMOD (Invesco BCOM), ICOM (iShares div. cmdty swap)
usd_proxy:                   IB01 (USD cash-rate proxy, dur≈0.4)
cash:                        IGLS (GBP 0-5yr Gilts near-cash, dur≈2.3, ccy GBP)

LEAVE AS EXPLICIT TODO (do NOT guess these — add a code comment, no record)
- intermediate bucket: no clean single-line UCITS twin for VGIT's 3-10y blend.
- inflation_linked: short-TIPS / 5y-breakeven twin for VTIP unverified.
- Any ISIN you are not certain of: set isin=None with a "# TODO confirm" comment
  rather than inventing one.

ADD: platform-capability matrix (single source of truth, NOT per-security)
  PLATFORM_ACCESS: dict[platform -> dict[capability -> bool]]
  platforms in scope: ibkr_uk, trading212, hargreaves_lansdown, aj_bell,
    investengine
  capabilities: ucits_etfs, us_listed_stocks, us_domiciled_etfs(=False all),
    futures, fx_spot, options, cfds
  Key asymmetry to encode: only ibkr_uk has futures=True and fx_spot=True.
  trading212 has cfds=True; the rest are ucits-only.
  Add helpers: platforms() -> tuple[str,...],
               platform_supports(platform, capability) -> bool

ACCEPTANCE
- `python -m unittest tests.test_policy_and_regimes.UniverseTests` passes.
- No bucket in ASSET_CLASS_UNIVERSE is empty.
- has_tradeable_instruments() is False.
- Module imports with no errors; sizing.py and app.py still import cleanly.

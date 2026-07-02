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

# Prompt: Build Stage 1 Regime Classification Module

## Context
`src/macro_factor_pricing_engine/regime_input.py` is currently a placeholder marked
`STAGE 1 PLACEHOLDER - regime classification from data is the priority unbuilt module`.
It must be replaced with a deterministic classifier that consumes a fixed public-data
snapshot and emits a `RegimeProbabilities` object matching the existing interface in
`regimes.py`. Do not change the `RegimeProbabilities`, `Regime`, `MacroState`, or
`CausalMechanism` definitions in `regimes.py` — this module is a new consumer/producer
that feeds that existing interface, not a replacement for it.

**Threshold source of record: `docs/market_history_patterns.md`.** This repo already
contains a researched, human-curated threshold library (Part V, "Master Pattern
Library", Modules A–J) covering credit spreads, VIX bands, yield curve timing, dollar
cycles, and inflation regime bands. Every numeric threshold used in this module MUST
either (a) cite the specific Module/Pattern in `market_history_patterns.md` it came
from, in a code comment, or (b) if no threshold exists there for a given trigger, be
left as an explicit `NotImplementedError` stub with a `# USER TO CONFIRM: threshold
not found in docs/market_history_patterns.md` comment — never a plausible-sounding
number invented to fill the gap. This is a hard requirement, not a style preference.

**Known taxonomy mismatch — out of scope for this pass.** `market_history_patterns.md`
Module J defines its own single-axis 5-regime system (`REGIME_1` through `REGIME_5`,
including `DEFLATION/DEPRESSION` and `LATE_CYCLE_BOOM`), which does not map 1:1 onto
the `MacroState` enum in `regimes.py`. Do not attempt to reconcile these two taxonomies
in this pass, and do not add new `MacroState` or `CausalMechanism` values. Where a
Module J threshold is used below, it is being borrowed as a numeric input to the
existing two-axis system, not as evidence that the two taxonomies are equivalent.

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

  Returns a score in [-1, 1] for each of the five `MACRO_TRANSMISSION_CHANNELS`.
  Use the sourced bands below rather than an unsourced z-score formula — map each
  band to an evenly-spaced score (e.g. 5 bands → roughly -1.0, -0.5, 0.0, 0.5, 1.0)
  and document the exact mapping in the docstring:

  - **inflation**: use Module B (`INFLATION_REGIME_LOW/MODERATE/HIGH`) directly —
    CPI<2.5% and breakeven<2.5% → low/negative score; CPI 2.5–4.5% and rising →
    moderate; CPI>4.5% OR breakeven>3.5% → high/positive score.
  - **risk_appetite**: use Module C (HY OAS bands: <250 / 250–400 / 400–600 /
    600–1000 / >1000 bp) and Module G (VIX bands: <15 / 15–25 / 25–35 / >35 / >60).
    Combine the two sub-scores (e.g. average) since both live in this channel.
  - **fiscal_sovereign**: use Module E (DXY moving >5% over a rolling 6-month
    window = bull/bear dollar signal) for the `dxy_chg_3m`/`dxy_trend_direction`
    component. `acm_term_premium_10y` has no threshold in this doc —
    `NotImplementedError` stub with the required comment.
  - **growth**: Module A's concurrent-recession threshold (`ISM_Manufacturing < 47`)
    is the only sourced numeric anchor. Use it as the negative extreme of the score;
    otherwise derive the score from PMI/CFNAI/GDPNow trend direction (up vs down
    over the trailing readings), since the doc doesn't give graduated growth bands
    beyond that single recession-confirmation threshold. This score is computed
    once, here, and reused by Step 1's MacroState lookup below — do not recompute
    growth trend direction a second time elsewhere.
  - **policy_liquidity**: no graduated band exists in the doc for NFCI specifically;
    use the Chicago Fed's own published convention instead (NFCI > 0 = tighter than
    average, 0 = average, and note in a comment that this is sourced from the
    Chicago Fed NFCI methodology, not `market_history_patterns.md`, so the citation
    stays honest about which source it came from). `ust_2y/10y_yield_chg_1m` and
    `fed_funds_implied_path_chg_3m` have no doc-sourced fast/slow threshold —
    `NotImplementedError` stub for the magnitude cutoff; direction-of-change (sign)
    can still be used un-stubbed, since sign doesn't require a magnitude threshold.

- `derive_observable_triggers(scores: ChannelScores, snapshot: RegimeIndicatorSnapshot) -> frozenset[str]`
  Maps channel scores AND raw snapshot fields (some triggers need raw levels, not
  just the [-1,1] channel score — e.g. a specific OAS crossing) to the exact
  `observable_trigger_names` strings already used in `REGIME_DEFINITIONS` in
  `regimes.py`. Pull the exact trigger name strings from `regimes.py` — do not
  invent new ones. Source each trigger's firing condition as follows:

  - `credit_spreads_widening_fast`: fires if `hy_oas` crosses above 600bp
    (Module C: "600bps = strong recession confirmation"), OR `hy_oas_chg_1m`
    exceeds +150bp (no doc-sourced 1-month magnitude exists for "fast" —
    mark this disjunct with `# USER TO CONFIRM`, keep the 600bp level-crossing
    branch as the sourced primary rule).
  - `volatility_or_financial_conditions_stress`: fires if `vix > 35`
    (Module G: "VIX > 35: Crisis territory") OR nfci crosses above +0.5
    (cite the Chicago Fed NFCI documentation reviewed for this project, not
    `market_history_patterns.md` — keep the source distinction explicit).
  - `equity_drawdown_breach`: fires if `sp500_drawdown_from_52w_high` exceeds 20%,
    using the doc's own bear-market convention (used throughout Part IV's
    bull/bear market statistics table as the >20% decline definition).
  - `usd_trend_positive`: fires if `dxy_chg_3m` implies >5% over 6 months per
    Module E's dollar-cycle threshold (scale the 3-month figure accordingly and
    document the scaling assumption explicitly as a judgment call, since the doc's
    threshold is stated over 6 months, not 3).
  - `inflation_momentum_positive` / `inflation_high_or_sticky`: fires per Module B's
    CPI>4.5% OR breakeven>3.5% threshold.
  - `growth_momentum_negative`: fires if `ism_manufacturing_pmi < 47`
    (Module A signal 4) OR the trend-direction check from Step 1 is negative.
  - `currency_or_policy_anchor_break`, `cross_market_contagion`,
    `real_yields_rising`, `inflation_surprise_positive`,
    `financial_conditions_tightening`, `fiscal_or_term_premium_stress`,
    `front_end_yields_rising_fast`: **no explicit numeric threshold exists in
    `market_history_patterns.md` for these.** Implement each as a stub that
    raises `NotImplementedError` with a `# USER TO CONFIRM` comment rather than
    inventing a plausible-sounding cutoff. List these explicitly in the PR
    description as open items requiring a threshold decision from the repo owner.

- `classify_regime(snapshot: RegimeIndicatorSnapshot) -> RegimeProbabilities`

  **Step 1 — MacroState, derived FROM the channel scores (not recomputed
  separately).** Call `compute_channel_scores()` first. Do not implement a second,
  independent trend-direction calculation for this step — that would let the
  growth/inflation direction used for MacroState silently diverge from the
  growth/inflation channel scores used elsewhere, which is exactly the kind of
  duplicated, potentially-inconsistent logic this project avoids.

  Bin the `growth` and `inflation` channel scores into categorical direction:
  - `growth_score > +0.3` → accelerating; `-0.3` to `+0.3` → stable;
    `< -0.3` → decelerating.
  - `inflation_score > +0.3` → rising/sticky; `≤ +0.3` → falling.
  (These ±0.3 band edges are NOT sourced from `market_history_patterns.md` — they
  are a structural judgment call being made now, flag with `# USER TO CONFIRM:
  band edges are a judgment call, not sourced` in the code.)

  Map the resulting (growth direction, inflation direction) pair directly onto
  `MACRO_STATE_PROFILES` — this final mapping step is a lookup, not a score.

  **Step 2 — CausalMechanism (explicit rule set, not agent-invented).** Evaluate
  these three trigger groups, pulled directly from `REGIME_DEFINITIONS` in
  `regimes.py`. Do not substitute different trigger names or invent new ones.

  Rule set (evaluate in this order — first match wins, since some triggers overlap):

  1. `peg_or_promise_break` fires if `currency_or_policy_anchor_break` is true.
     This trigger is unique to this mechanism — check it first, before the
     overlapping triggers below, so a genuine currency/anchor crisis is never
     misattributed to leverage breakdown.
  2. `leverage_institutional_breakdown` fires if `volatility_or_financial_conditions_stress`
     is true OR `equity_drawdown_breach` is true. These two are unique to this
     mechanism and should drive the decision — do not use the shared triggers
     (`credit_spreads_widening_fast`, `usd_trend_positive`) as the deciding signal,
     since both mechanisms can produce those.
  3. `deliberate_policy_disruption` fires if at least two of
     {`front_end_yields_rising_fast`, `real_yields_rising`, `fiscal_or_term_premium_stress`,
     `inflation_surprise_positive`, `financial_conditions_tightening`} are true.
     Require two, not one, since any single one of these can occur in ordinary
     cyclical conditions.
  4. If none of the above fire, mechanism = `cyclical_no_acute_mechanism` (the
     default — it has no positive trigger of its own).

  Document this exact rule order and the overlap-tiebreak reasoning in a docstring.
  This is deliberately not a scored/weighted approach for the mechanism axis —
  it's a hard rule chain, because the mechanism axis represents a causal
  attribution, not a magnitude, and blending it into the same [-1,1] channel-score
  scheme as growth/inflation would blur causally distinct explanations together.

  **Step 3 — Undefined-pair fallback.** If Steps 1+2 produce a `(state, mechanism)`
  pair not present in `DEFINED_REGIME_PAIRS`, do not force a match onto a defined
  pair and do not raise. Instead return a `RegimeProbabilities` that spreads
  weight across the defined pairs sharing the same `state` (if any exist),
  and set a companion flag `outside_defined_playbooks: bool = True` on the
  return object (extend `RegimeProbabilities` or wrap it — coordinate with the
  `regimes.py` owner if a field addition is needed) so downstream consumers and
  the dashboard can surface "no playbook exists for this read, human review
  needed" rather than silently presenting false confidence. If no defined pair
  shares the same state either, spread weight uniformly across all 8 defined
  pairs and set the same flag — this is a low-information fallback, not a guess.

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

Two distinct test tiers. Do not blend them — a test asserting a specific regime
label must only ever run against a hand-specified synthetic fixture, never against
a real pulled snapshot.

**Tier A — synthetic fixture tests (assert specific regime labels).**
Use these exact fixture values, not agent-invented ones, so the test data is fixed
independently of whatever thresholds `compute_channel_scores()` ends up using. Values
are deliberately extreme so the expected classification holds under any reasonable
scoring formula:

- `GOLDILOCKS_FIXTURE`: ism_manufacturing_pmi=58.0, chicago_fed_nai=0.8,
  cpi_yoy=1.5 (below Module B's 2.5% low-inflation threshold), core_cpi_yoy=1.6,
  hy_oas=200 (bp, below Module C's 250bp euphoria/low band), vix=12.0
  (below Module G's 15 low-vol band), nfci=-0.9, all other fields at their
  historical-median placeholder. Assert classification places highest weight on
  `goldilocks x cyclical_no_acute_mechanism`, and assert that weight is materially
  higher than every other defined regime's weight (e.g. at least 2x the
  second-highest), not just nominally highest.
- `LEVERAGE_BREAKDOWN_FIXTURE`: ism_manufacturing_pmi=42.0 (below Module A's 47
  concurrent-recession threshold), chicago_fed_nai=-1.2, hy_oas=850 (bp, within
  Module C's 600–1000bp "deep recession" band), hy_oas_chg_1m=+250 (bp), vix=38.0
  (above Module G's 35 crisis threshold), nfci=+1.1. Assert classification places
  highest combined weight on the two `leverage_institutional_breakdown` regime
  pairs together (stagflation and disinflationary_slowdown variants) — don't
  force a single one, since the fixture doesn't disambiguate growth/inflation
  state cleanly by design.
- Missing/None fields degrade gracefully (test with a fixture that has ~40% of
  fields as `None`): confidence widens (distribution flattens toward uniform
  over defined regimes), the run never crashes, and no field is silently
  imputed — assert the returned object exposes which fields were missing.
- Every trigger left as a `NotImplementedError` stub actually raises when called
  directly, rather than silently returning `False` or a fabricated value — this
  confirms the "no invented thresholds" requirement is enforced in code, not just
  in the docstring.
- `RegimeOverride` correctly overrides computed output and requires confirmation
  per the `human_input_pending` policy trigger.
- `RegimeOverride` referencing an undefined regime pair raises `KeyError`.
- Full synthetic-fixture-to-classification path round-trips through
  `RegimeProbabilities` validation (weights non-negative, sum to 1.0).
- `UNDEFINED_PAIR_FIXTURE`: construct a fixture whose growth/inflation direction
  resolves to `stagflation` but whose mechanism triggers all evaluate false
  (no policy-disruption pair, no leverage/vol stress, no currency break) —
  this deliberately lands on `stagflation x cyclical_no_acute_mechanism`, which
  is NOT in `DEFINED_REGIME_PAIRS`. Assert this does not raise, returns a valid
  `RegimeProbabilities`, sets `outside_defined_playbooks=True`, and spreads
  weight only across the two defined stagflation pairs
  (`deliberate_policy_disruption`, `leverage_institutional_breakdown`) per the
  Step 3 fallback rule — not uniformly across all 8.

**Tier B — real-snapshot smoke test (never assert a specific regime label).**
Add one test that runs the classifier against a real, dated snapshot (e.g. the
2026-07-01 snapshot already compiled — see attached CSV) and asserts only:
- no exception is raised;
- returned weights are non-negative and sum to 1.0;
- no field silently defaulted to a fabricated value where the input was missing;
- the resulting `RegimeProbabilities.is_transition()` value and dominant regime
  are printed/logged, not asserted, since real data may legitimately be ambiguous
  or split across regimes and that is correct behavior, not a bug.
If a future maintainer wants Tier B to assert a specific outcome, that requires a
separate, explicit human-labeled golden scenario (e.g. from `macro_shocks_raw.csv`)
where the historical regime is independently known — not an assumption baked into
the test by whoever wrote the classifier.

## Explicit non-goals for this pass
- Do not wire this into `sizing.py` or the rates loop yet — that's a follow-up step
  once classification is validated standalone.
- Do not add any HMM, ML classifier, or statistically fitted model — this is a
  deterministic, rule-based, explainable v1, consistent with the project's existing
  heuristic-and-labeled-as-such approach.
- Do not add Bloomberg-sourced fields to the automated `data/sources.py` path —
  Bloomberg-only inputs (e.g. sovereign CDS from a terminal) stay in the discretionary
  `RegimeOverride.reason` free-text field, not as a structured automated input.
- Do not reconcile the Module J taxonomy in `market_history_patterns.md` with the
  `MacroState`/`CausalMechanism` enums, and do not add new enum values.
- Do not silently resolve any `NotImplementedError` stub with an invented threshold.
  The PR description must list every stub left in place (expected: at minimum
  `currency_or_policy_anchor_break`, `cross_market_contagion`, `real_yields_rising`,
  `inflation_surprise_positive`, `financial_conditions_tightening`,
  `fiscal_or_term_premium_stress`, `front_end_yields_rising_fast`, and
  `acm_term_premium_10y`'s channel contribution) as open decisions for the repo owner.

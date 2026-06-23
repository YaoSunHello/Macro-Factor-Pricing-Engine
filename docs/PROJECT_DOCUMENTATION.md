# Macro Factor Pricing Engine Documentation

## Purpose

Macro Factor Pricing Engine is a governance-first research system for turning macro
regime views into explained, pending portfolio recommendations. The project is currently
focused on one thin end-to-end slice: developed-market sovereign rates, calibrated around
US Treasury inputs.

The engine is not a trading system. It runs in analysis mode, produces pending
recommendations, and preserves human approval gates before any instrument could become
eligible for paper or live allocation.

## Current Scope

The implemented scope is rates only:

- short-duration government bonds;
- intermediate-duration government bonds;
- long-duration government bonds;
- inflation-linked bonds.

Starter securities are included as analysis-scope proxies:

| Bucket | Proxies | Status |
|---|---|---|
| Short duration | `SHY`, `SHV` | User to confirm, not approved |
| Intermediate duration | `IEF`, `VGIT` | User to confirm, not approved |
| Long duration | `TLT`, `VGLT` | User to confirm, not approved |
| Inflation-linked bonds | `TIP`, `VTIP` | User to confirm, not approved |

Membership is not approval. Every proxy has `approved_for_allocation: False`, and
`has_tradeable_instruments()` must remain `False` until a future approval workflow
explicitly changes that.

## Architecture

The package lives in `src/macro_factor_pricing_engine`.

| Module | Responsibility |
|---|---|
| `universe.py` | Asset-class and rates security scope, with approval gate preserved |
| `regimes.py` | Two-axis regime model: `MacroState x CausalMechanism` |
| `regime_input.py` | Manual `RegimeProbabilities` stub for Stage 1 |
| `treasury_policy.py` | Structured Treasury policy records from `TreasuryPolicy.md` |
| `data/sources.py` | Data source interface, committed snapshot source, FRED stub |
| `rates_scorer.py` | Treasury Block A-D scoring and derived metrics |
| `sizing.py` | First-pass target weight convention for rates buckets |
| `inventory.py` | Blank or persistent paper inventory plus append-only turnover ledger |
| `risk.py` | First-pass duration, DV01, bucket exposure, and concentration flags |
| `explain.py` | Plain-language explanation for the pending recommendation |
| `app.py` | CLI orchestrator for the full rates analysis loop |
| `policy.py` | Strategy governance rules and human approval constraints |

## Regime Model

Regimes have two axes:

1. Macro state: what growth, inflation, policy, liquidity, and risk appetite are doing.
2. Causal mechanism: why that state exists.

This distinction matters because the same macro state can imply different asset calls.
For example:

- `stagflation x deliberate_policy_disruption` makes long-duration government bonds a
  strong underweight because term-premium and fiscal risk dominate.
- `stagflation x leverage_institutional_breakdown` can make long-duration government
  bonds an overweight because flight-to-quality can dominate after policy response is
  expected.

The implemented regime probability interface is `RegimeProbabilities`. Stage 1 regime
classification is not built yet. For now, `regime_input.py` supplies manual probabilities
through the same interface the future classifier must emit.

## Rates Recommendation Loop

One command runs the current analysis loop:

```bash
PYTHONPATH=src python3 -m macro_factor_pricing_engine.app
```

The loop performs these steps:

1. Load the committed `2026-06-18` rates snapshot.
2. Enforce no-lookahead at the data source interface.
3. Load manually supplied regime probabilities.
4. Compute derived rates metrics in the scorer.
5. Run Treasury policy Block A-D scoring.
6. Size pending target weights across scoped rates securities.
7. Compare target weights with the current paper inventory.
8. Append recommended changes to `.runtime/turnover_ledger.jsonl`.
9. Compute first-pass duration, DV01, bucket exposure, and concentration flags.
10. Print a plain-language pending recommendation.

The recommendation status is always `PENDING`. Live trading is disabled.

## Data

The current committed fixture is:

```text
src/macro_factor_pricing_engine/data/snapshot_2026_06_18.json
```

It includes raw observations such as:

- 2y, 5y, 10y, and 30y Treasury yields;
- 5y and 10y breakevens;
- ACM 10y term premium;
- core PCE and CPI readings;
- GDPNow, ISM, payrolls, unemployment change;
- MOVE, auction-demand proxies, QT and issuance flags;
- stock-bond correlation and simple risk gauges.

The data source returns raw aligned observations only. Derived metrics, such as real
policy rate or breakeven gap to core PCE, belong in the scorer.

## Scoring

`rates_scorer.py` computes:

- Cycle score from growth, inflation momentum, and policy stance;
- valuation score from term premium, supply, MOVE, real yields, positioning, and momentum;
- fiscal veto state;
- cross-asset overlay modifier;
- fired trigger list;
- composite signal.

The current default snapshot and manual regime probabilities produce:

```text
Cycle: -1
Valuation: -4
Fiscal veto: False
Overlay modifier: 0.5
Composite signal: long_end_underweight
```

## Sizing

The current sizing convention is explicit and simple. Under the default
`stagflation x deliberate_policy_disruption` regime, the target bucket weights are:

| Bucket | Target |
|---|---:|
| Short-duration government bonds | 25% |
| Intermediate-duration government bonds | 40% |
| Long-duration government bonds | 5% |
| Inflation-linked bonds | 30% |

Weights are split equally across the scoped securities inside each bucket. Curve trades,
such as a 5s30s steepener, are surfaced as notes and are not forced into the weight
vector.

## Risk Readout

`risk.py` computes a first-pass readout only:

- weighted portfolio duration;
- DV01 per $1mm notional;
- per-bucket exposure;
- concentration cap;
- cap breach flags.

The full risk model, vol target, and optimization engine are not implemented yet.

## Governance And Safety Invariants

The following invariants are intentional:

- analysis mode only;
- pending recommendations only;
- no live trading;
- no approved allocation instruments;
- `has_tradeable_instruments()` remains `False`;
- human input can create only pending adjustments;
- no-lookahead is enforced at the data source boundary;
- Stage 1 regime classification is unbuilt and explicitly marked as the next priority.

## Runtime Files

The CLI app writes runtime artifacts under:

```text
.runtime/
```

The turnover ledger is append-only:

```text
.runtime/turnover_ledger.jsonl
```

The `.runtime/` directory is ignored by git.

## Tests

Run:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

The tests are consistency and smoke tests only. They do not validate investment
performance. The rates smoke test verifies that the committed snapshot and default
manual regime reproduce the known hand-calculated stance:

- overweight front-belly;
- underweight long end;
- overweight 5y TIPS.

## Next Work

The next priority is Stage 1 regime classification:

- map public macro data into `MacroState x CausalMechanism`;
- emit `RegimeProbabilities`;
- preserve the same interface consumed by the existing loop;
- charge detection lag in backtests later;
- avoid adding validation or optimization before the classifier is wired.

After Stage 1, the project can add a proper indicator layer, validation/backtest module,
allocation risk model, and approval workflow.

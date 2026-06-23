# Treasury Strategy Signal Policy (Pseudo-Policy)

**Version:** 0.2 (draft) · **Owner:** Investment Risk · **Asset class:** Developed-market sovereign rates (primary calibration: US Treasuries)
**Status:** Heuristic decision-support framework, not a binding mandate or investment advice. Every signal state is a *prior* that requires human judgment before sizing. Thresholds are starting calibrations to be refined against the backtest.

---

## 1. Purpose & scope

Codify the entry/exit logic for sovereign-rate positioning into rules-based, measurable signals so that (a) decisions are repeatable and auditable, (b) the logic can be backtested, and (c) headline-driven trading is replaced by regime + valuation + positioning discipline.

Scope: nominal and inflation-linked sovereign bonds, expressed in cash or futures, across the 2y–30y curve. Calibrated on USTs; the same block structure applies to gilts / bunds / JGBs by swapping the data sources in §3.

---

## 2. Conceptual foundation

Nominal yield = **expected path of short rates** + **term premium**. (Linker: real-rate path + breakeven.) Two engines that can move independently — the 2024 episode is the proof case (Fed cut 100bp, 10y *rose* 116bp; ~⅔ of the move was term premium, not the policy path). The framework therefore scores four blocks separately and only then combines them.

| Block | Drives | Anchors |
|---|---|---|
| A — Expected short-rate path | Cycle + monetary policy | Front-belly (2–5y) |
| B — Term premium | Supply / demand / uncertainty | Long end (10–30y) |
| C — Fiscal credibility | Sovereign risk premium | Long end (gate/veto) |
| D — Valuation, technicals, positioning | Timing | All segments |
| Overlay — Cross-asset | Hedge value & risk regime | Sizing modifier |

**Sign convention:** a positive signal score = **bullish duration** (own more duration / yields expected lower / valuation pays you to take risk). Negative = bearish duration.

---

## 3. Signal inputs & data sources

| Input | Source / ticker | Freq | Block |
|---|---|---|---|
| Policy rate (effective) | FRED `DFF` | Daily | A |
| Implied policy path | CME FedWatch (fed funds futures probabilities) | Daily | A |
| 2y / 5y / 10y / 30y yield | FRED `DGS2/DGS5/DGS10/DGS30` | Daily | A,B,D |
| Core PCE | FRED `PCEPILFE` (m/m, y/y) | Monthly | A |
| CPI / wages | FRED `CPIAUCSL`, `ECIWAG` | Monthly/Qtr | A |
| Inflation nowcast | Cleveland Fed Nowcast | Daily | A |
| Growth nowcast | Atlanta Fed GDPNow | ~Weekly | A |
| ISM mfg / services | ISM releases | Monthly | A |
| Payrolls / claims | BLS `PAYEMS`, `ICSA` | Monthly/Weekly | A |
| ACM 10y term premium | NY Fed `ACMTP10` | Daily | B |
| 10y real yield | FRED `DFII10` | Daily | B,D |
| Issuance / QRA / TBAC | Treasury QRA, TBAC minutes | Quarterly | B,C |
| Auction demand: bid-to-cover, tail, indirect bid | Treasury auction results | Per auction | B,C |
| QT pace | Fed H.4.1 | Weekly | B |
| Rate volatility | MOVE index | Daily | B,D |
| 5y / 10y breakeven | FRED `T5YIE`, `T10YIE` | Daily | D |
| 5y TIPS real yield | FRED `DFII5` | Daily | D |
| Sovereign 5y CDS | Market data | Daily | C |
| CFTC positioning | CFTC CoT (TY/FV/US) | Weekly | D |
| Stock-bond correlation | 60d rolling, SPX vs 10y total return | Daily | Overlay |
| Risk gauges | VIX, IG/HY OAS, DXY | Daily | Overlay |

---

## 4. Block-level signal rules

Each sub-signal scores −1 / 0 / +1 unless noted. Block score = sum.

### Block A — Expected short-rate path (cycle)

| Sub-signal | +1 (bullish duration) | −1 (bearish duration) |
|---|---|---|
| Growth | ISM composite < 48, or payrolls 3m-avg < 75k, or GDPNow < 1.0% | ISM > 52, or payrolls 3m-avg > 150k, or GDPNow > 2.5% |
| Inflation momentum | Core PCE 3m-annualised **below** y/y **and** falling | Core PCE 3m-ann **above** y/y **and** rising |
| Policy stance | Real policy rate (`DFF` − core PCE y/y) > +1.0% (clearly restrictive) | Real policy rate < 0% (not restrictive; hike risk live) |

Context flag (not scored): **CME FedWatch** implied path vs the 2y yield vs policy midpoint. 2y > policy → market pricing hikes (near-term duration caution). 2y < policy by > 50bp → cuts priced (cushion, but confirm with data). The 2y is the cleanest single proxy for the expected average policy rate over ~24 months.

**Transmission note — growth signals move the *whole* curve, not just the belly.** ISM and NFP are scored here as cycle inputs, but their duration expression runs the length of the curve: a contraction in manufacturing + rising unemployment lowers the expected-average-short-rate embedded in the 10y/30y, so the long end rallies (yields fall) in anticipation of slower growth — the textbook transmission. **Important exception:** this only holds when term premium (Block B) and fiscal risk (Block C) are quiescent. In a term-premium- or fiscal-dominant regime the long end can *fail to rally — or even sell off — on weak growth* (cf. 2024: cuts delivered, growth softening, yet 10y rose on term premium). So treat "weak growth → long-end rally" as the Block A prior, **subordinate to the Block B/C gate** in §6.

### Block B — Term premium

| Sub-signal | Rule |
|---|---|
| ACM TP level | > 1.8% → **+2**; 1.4–1.8% → +1; 0.5–1.4% → 0; < 0.5% → −1 |
| Supply / auctions | **−1** if bid-to-cover below trailing-6-auction average (weak demand → dealers absorb → secondary prices down) **or** persistent tails + falling indirect-bidder share; **+1** if bid-to-cover above trailing average + repeated stop-throughs; else 0. *(Read b/c as a z-score vs trailing same-tenor auctions, not an absolute level — ~2.3–2.6× for the 10y is normal but tenor-specific.)* |
| QT / issuance mix | Rising coupon-issuance share + active QT → −1; paused QT / bill-heavy → +1; else 0 |
| MOVE | < 90 → +1; > 120 and rising → −1; else 0 |

*Median ACM TP ≈ 1.4% over the 65y series — the reference point for "the long end is paying you."*

### Block C — Fiscal credibility (gate, not additive)

This block sets a **veto/cap on long-end length**, it does not add to the bullish score.

- **Fiscal-stress flag = TRUE** if ≥ 2 of: sovereign 5y CDS widening > 1 z-score; persistent auction tails (2+ consecutive); adverse fiscal/political event live (budget impasse, debt-ceiling, downgrade watch, election fiscal shock).
- Flag TRUE → **cap long-end at neutral-to-underweight regardless of B/D**, bias to steepener. (Gilt 2022 / OAT 2024 analogue: term premium can spike 50–100bp in weeks.)

### Block D — Valuation, technicals, positioning (timing)

| Sub-signal | +1 | −1 |
|---|---|---|
| 10y real yield (`DFII10`) | > 2.5% (rich real comp.) | < 1.0% (expensive) |
| Fair-value gap | Market yield > model (path + TP) by > 25bp → cheap | Market < model by > 25bp → rich |
| Momentum | 10y yield below 50d & 200d MA (falling) | 10y yield above both (rising) |
| Positioning | CFTC specs net short > 1 z-score (room to rally) | Net long > 1 z-score (crowded) |

### Overlay — Cross-asset (sizing modifier)

- Stock-bond 60d correlation **> +0.3** → duration hedge value impaired → **halve** any long-end add.
- Correlation **< −0.2** → hedge restored → long-end add may be **scaled up**.
- Acute risk-off (VIX spike + HY OAS widening fast) → front-belly flight-to-quality bid; do not fade.

---

## 5. Regime classification overlay

Map the prevailing environment to one of three causal regimes (and a pre-crisis signal type). Regime sets the *playbook*; the block scores set the *sizing*.

| Regime | Rates behaviour | Playbook |
|---|---|---|
| **Peg / promise breaking** (Asian '97, ERM, SNB) | Violent repricing, flight-to-quality into core duration | Own core front-belly; avoid the cracking sovereign; watch contagion |
| **Deliberate policy disruption** (2022 hikes, tariff/trade shock) | Bear-flattener then bear-steepener as term premium/inflation re-rate | Underweight long-end; front-belly carry; steepener; TIPS if breakevens cheap |
| **High leverage / institutional breakdown** (GFC, LTCM) | Sharp bull rally in core duration once Fed responds | Add duration into the response; long-end as recession hedge |

**Pre-crisis signal type:** Warning / Calm / Mixed / **Stealth buildup**. Stealth (low vol, tight spreads, rising leverage) is the most dangerous for positioning — flag for reduced gross.

---

## 6. Composite signal → positioning matrix

Compute `Cycle = ΣBlock A`, `Valuation = ΣBlock B + ΣBlock D`, apply Block C gate and the overlay modifier.

| Segment | Rule |
|---|---|
| **Front-belly (2–5y)** | Default **overweight** when curve offers positive carry/roll and Cycle ≥ 0. Move to neutral only if Cycle ≤ −2 with hike risk live (front-end reprices up). |
| **Long-end (10–30y)** | **Overweight** if Valuation ≥ +2 **and** no fiscal veto **and** Cycle ≥ −1. **Underweight** if Valuation ≤ 0 **or** fiscal veto TRUE. Neutral between. Cycle ≤ −2 (clear slowdown) can pull long-end to OW as recession hedge **only if** stock-bond corr < +0.3. |
| **Curve (5s30s)** | **Steepener** when fiscal veto TRUE or supply/term-premium risk rising or bull-steepening cycle. **Flattener** only in a deliberate-hiking-into-slowdown bear-flattener (rare). |
| **TIPS / breakeven** | **Overweight** (front-belly, 5y point) when breakeven < realised core PCE by a clear margin **and** inflation momentum not falling. Underweight when breakevens rich vs realised. |

---

## 7. Add / reduce long-end duration — trigger checklists

**ADD long-end duration when ≥ 3 of:**
- [ ] Core PCE prints sub-3% (annualised) two consecutive months
- [ ] ACM term premium > 1.4% (≥ median) — and a strong add if it overshoots > 1.8%
- [ ] Payrolls roll over (3m-avg < 75k) or unemployment rising > 0.3pp off lows
- [ ] Energy/supply shock fading and breakevens falling
- [ ] Market underpricing a Fed pivot vs deteriorating data (2y > policy while growth cracks)
- [ ] 10y real yield > 2.5%
- [ ] Stock-bond correlation back below +0.3 (hedge value restored)

**REDUCE long-end duration when ≥ 3 of:**
- [ ] Inflation re-accelerating (core PCE 3m-ann > y/y and rising)
- [ ] ACM term premium < 0.5% and rising (no cushion, momentum against)
- [ ] Persistent auction tails / falling indirect-bidder share
- [ ] Fiscal-stress flag TRUE (CDS widening, event risk)
- [ ] MOVE > 120 and rising
- [ ] Positive stock-bond correlation + risk-on momentum
- [ ] CFTC specs crowded net-long > 1 z-score

---

## 8. Execution & risk discipline

- **Don't trade the headline.** Trade the regime turn + valuation + positioning extreme. A priced-in event is not an entry.
- **Scale in/out in thirds**, not all-in. Let confirmation accrue.
- **Instrument choice:** cash where liquidity/carry favour it; futures (FV/TY/US) for capital efficiency — but **price implied repo into carry**; leverage is not edge.
- **Sizing:** size long-end to the stock-bond correlation regime (see overlay). Reduce gross in Stealth pre-crisis states.
- **Review/stop levels:** define a yield level at entry that invalidates the thesis (e.g. term premium overshooting, or core PCE re-accelerating) and act on it.

---

## 9. Worked example — current state (as of 17–22 Jun 2026)

| Input | Reading | Block contribution |
|---|---|---|
| Policy rate | 3.50–3.75% | — |
| Core PCE / CPI | 3.3% / 4.2%, re-accelerating | A: inflation −1 |
| Real policy rate | ~3.625 − 3.3 = **+0.3%** (not restrictive) | A: policy ~0/−1 |
| Growth (GDPNow / GDP Q1) | slowing, ~1.6% | A: growth +1 |
| 2y vs policy | 2y 4.19% ≈ policy; dots show hikes | Context: hike risk |
| ACM TP | ~0.73% (35th pct, below 1.4% median) | B: 0 |
| 10y real yield (`DFII10`) | ~2.2% | D: 0 |
| MOVE / supply | elevated; heavy issuance, QT | B: −1 |
| 5y breakeven vs core PCE | 2.31% vs 3.3% → **cheap** | TIPS: overweight |
| Stock-bond corr | frequently positive post-2022 | Overlay: halve long-end add |

**Regime:** Deliberate Policy Disruption (tariffs) + supply shock (energy). **Cycle ≈ −1, Valuation ≈ −1, no fiscal veto yet.**
**Resulting stance:** overweight 2–5y (carry + priced-in-cut cushion); underweight 10–30y duration (term-premium upside risk, thin cushion); 5s30s steepener bias; overweight 5y TIPS (breakeven cheap vs realised). Add-duration checklist currently < 3 → **wait**; primary trigger to watch is core PCE rolling sub-3% and/or term premium overshooting toward median.

---

## 10. Governance

- **Cadence:** weekly signal refresh; monthly full block review; re-calibrate thresholds quarterly against backtest output.
- **Backtest hook:** §4 scores and §6/§7 rules are designed to run as a daily positioning rule against the data series in §3 (DGS*, ACMTP10, PCEPILFE, MOVE, breakevens, auction data). Performance to be measured vs (a) buy-and-hold 10y, (b) constant-duration benchmark.
- **Limitations:** thresholds are heuristic priors, not optimised; term-premium models are model-dependent (ACM vs Kim-Wright differ); regime labels are judgmental; signals lag at turning points. Use as a structured prior, not an autopilot.
- **Change log:** v0.1 — initial codification. v0.2 — added CME FedWatch (implied path) to Block A and the growth→whole-curve transmission note with its term-premium/fiscal exception; made bid-to-cover an explicit, z-scored component of the Block B supply signal.

# Macro-Factor-Pricing-Engine
The model builds a probabilistic framework to understand asset price movements through macroeconomic drivers instead of a deterministic prediction.

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

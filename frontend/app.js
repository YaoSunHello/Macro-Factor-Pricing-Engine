const stateNames = {
  goldilocks: "Goldilocks",
  reflation: "Reflation",
  stagflation: "Stagflation",
  disinflationary_slowdown: "Disinflationary slowdown",
  crisis_liquidity_stress: "Crisis liquidity stress",
  policy_tightening_shock: "Policy tightening shock",
};

const mechanismNames = {
  peg_or_promise_break: "Peg / promise break",
  deliberate_policy_disruption: "Deliberate policy disruption",
  leverage_institutional_breakdown: "Leverage / institutional breakdown",
  cyclical_no_acute_mechanism: "Cyclical, no acute mechanism",
};

let distributionChart = null;

function pct(value) {
  return `${Math.round(value * 100)}%`;
}

function pairKey(state, mechanism) {
  return `${state}__${mechanism}`;
}

function byWeightDesc(a, b) {
  return b.weight - a.weight;
}

function renderTransition(data) {
  const banner = document.getElementById("transition-banner");
  if (!data.is_transition) {
    banner.hidden = true;
    banner.textContent = "";
    return;
  }
  banner.hidden = false;
  banner.textContent = `TRANSITION - no regime holds >60% (max = ${pct(data.max_mass)})`;
}

function renderGrid(data) {
  const grid = document.getElementById("regime-grid");
  const activePairs = new Set(data.defined_pairs.map((pair) => pairKey(pair.state, pair.mechanism)));
  const weights = new Map(data.regime_distribution.map((regime) => [regime.name, regime.weight]));
  const dominantKey = pairKey(data.dominant.state, data.dominant.mechanism);
  grid.innerHTML = "";

  grid.appendChild(cell("", "grid-cell grid-header"));
  data.causal_mechanisms.forEach((mechanism) => {
    grid.appendChild(cell(mechanismNames[mechanism] || mechanism, "grid-cell grid-header"));
  });

  data.macro_states.forEach((state) => {
    grid.appendChild(cell(stateNames[state] || state, "grid-cell row-header"));
    data.causal_mechanisms.forEach((mechanism) => {
      const key = pairKey(state, mechanism);
      const active = activePairs.has(key);
      const weight = weights.get(key) || 0;
      const node = document.createElement("div");
      node.className = `grid-cell regime-cell${active ? "" : " undefined"}${key === dominantKey ? " dominant" : ""}`;
      if (active) {
        const intensity = Math.max(0.04, weight);
        node.style.background = `rgba(15, 118, 110, ${0.08 + intensity * 0.75})`;
      }
      node.innerHTML = `<span class="cell-title">${active ? "Active" : "Undefined"}</span><span class="cell-weight">${pct(weight)}</span>`;
      grid.appendChild(node);
    });
  });

  document.getElementById("active-count").textContent = `${activePairs.size} active cells`;
}

function cell(text, className) {
  const node = document.createElement("div");
  node.className = className;
  node.textContent = text;
  return node;
}

function renderDistribution(data) {
  const regimes = [...data.regime_distribution].sort(byWeightDesc);
  const total = regimes.reduce((sum, regime) => sum + regime.weight, 0);
  document.getElementById("distribution-total").textContent = `total ${pct(total)}`;

  const list = document.getElementById("distribution-list");
  list.innerHTML = regimes.map((regime) => `
    <div class="bar-row">
      <div>
        <strong>${stateNames[regime.state] || regime.state}</strong>
        <div class="metric">${mechanismNames[regime.mechanism] || regime.mechanism}</div>
        <div class="bar-track"><div class="bar-fill" style="width: ${pct(regime.weight)}"></div></div>
      </div>
      <strong>${pct(regime.weight)}</strong>
    </div>
  `).join("");

  const canvas = document.getElementById("distribution-chart");
  if (!window.Chart || !canvas) return;
  if (distributionChart) distributionChart.destroy();
  distributionChart = new Chart(canvas, {
    type: "bar",
    data: {
      labels: regimes.map((regime) => `${stateNames[regime.state] || regime.state}`),
      datasets: [{
        data: regimes.map((regime) => regime.weight),
        backgroundColor: "#0f766e",
        borderRadius: 4,
      }],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: "#607077" }, grid: { display: false } },
        y: { min: 0, max: 1, ticks: { callback: (value) => `${value * 100}%` } },
      },
    },
  });
}

function renderDominant(data) {
  const dominant = data.regime_distribution.find((regime) => regime.name === data.dominant.name);
  if (!dominant) return;
  document.getElementById("dominant-name").textContent = pct(dominant.weight);
  document.getElementById("dominant-story").textContent = dominant.causal_story;
  renderList("leading-assets", dominant.leading_assets);
  renderList("lagging-assets", dominant.lagging_assets);
}

function renderList(id, values) {
  document.getElementById(id).innerHTML = values.map((value) => `<li>${value}</li>`).join("");
}

function renderScores(data) {
  const scores = [
    ["Cycle", data.scores.cycle],
    ["Valuation", data.scores.valuation],
    ["Fiscal veto", data.scores.fiscal_veto ? "true" : "false"],
    ["Overlay modifier", `${data.scores.overlay_modifier} computed, not yet applied`],
    ["Composite", data.scores.composite],
    ["Fired triggers", data.scores.fired_triggers.join(", ")],
  ];
  document.getElementById("scores").innerHTML = scores.map(([label, value]) => `
    <div class="score-row"><dt>${label}</dt><dd>${value}</dd></div>
  `).join("");
}

function renderTargets(data) {
  document.getElementById("target-weights").innerHTML = data.target_weights.map((weight) => `
    <div class="target-row">
      <div>
        <strong>${weight.ticker}</strong>
        <div class="metric">${weight.bucket}</div>
      </div>
      <strong>${pct(weight.weight)}</strong>
    </div>
  `).join("");
}

async function loadState() {
  const response = await fetch("/api/state");
  if (!response.ok) throw new Error(`State request failed: ${response.status}`);
  const data = await response.json();
  renderTransition(data);
  renderGrid(data);
  renderDistribution(data);
  renderDominant(data);
  renderScores(data);
  renderTargets(data);
}

document.getElementById("refresh").addEventListener("click", () => {
  loadState().catch((error) => {
    document.getElementById("transition-banner").hidden = false;
    document.getElementById("transition-banner").textContent = error.message;
  });
});

loadState().catch((error) => {
  document.getElementById("transition-banner").hidden = false;
  document.getElementById("transition-banner").textContent = error.message;
});

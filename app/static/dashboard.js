/* Dashboard logic: fetch data from the API, render charts and tables. */

const SCORERS = ["keyword", "similarity", "llm_judge"];

// Chart.js instances. We create them once and update their data on refresh —
// destroying/recreating them every refresh leaks memory and flickers the UI.
let tsChart, distChart;

// ---------- utilities ------------------------------------------------------
function fmt(n, digits = 2) {
  if (n === null || n === undefined) return "–";
  return Number(n).toFixed(digits);
}

async function jget(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url} → ${r.status}`);
  return r.json();
}


// ---------- header stat cards ---------------------------------------------
async function loadSummary() {
  const d = await jget("/api/summary");
  document.getElementById("stat-calls").textContent = d.total_calls;
  document.getElementById("stat-cost").textContent = "$" + fmt(d.total_cost_usd, 4);
  document.getElementById("stat-latency").textContent = fmt(d.avg_latency_ms, 0) + "ms";
  document.getElementById("stat-tokens").textContent = d.total_tokens;
  document.getElementById("subtitle").textContent =
    `${d.total_calls} calls · ${d.total_tokens} tokens · $${fmt(d.total_cost_usd, 4)}`;
}

// ---------- line chart: score over time -----------------------------------
async function loadTimeseries() {
  const scorer = document.getElementById("ts-scorer").value;
  const rows = await jget(`/api/scores/timeseries?scorer=${scorer}`);

  const labels = rows.map(r => r.day);
  const values = rows.map(r => r.avg_score);

  if (tsChart) {
    tsChart.data.labels = labels;
    tsChart.data.datasets[0].data = values;
    tsChart.update();
    return;
  }

  tsChart = new Chart(document.getElementById("chart-timeseries"), {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: `avg ${scorer}`,
        data: values,
        borderColor: "#38bdf8",
        backgroundColor: "rgba(56, 189, 248, 0.15)",
        tension: 0.3,
        fill: true,
        pointRadius: 4,
      }]
    },
    options: {
      scales: {
        y: { min: 0, max: 1, ticks: { color: "#94a3b8" }, grid: { color: "#334155" } },
        x: { ticks: { color: "#94a3b8" }, grid: { color: "#334155" } },
      },
      plugins: { legend: { labels: { color: "#e2e8f0" } } },
    },
  });
}


// ---------- histogram: score distribution ---------------------------------
async function loadDistribution() {
  const scorer = document.getElementById("dist-scorer").value;
  const rows = await jget(`/api/scores/distribution?scorer=${scorer}`);

  const labels = rows.map(r => r.label);
  const values = rows.map(r => r.count);

  if (distChart) {
    distChart.data.labels = labels;
    distChart.data.datasets[0].data = values;
    distChart.update();
    return;
  }

  distChart = new Chart(document.getElementById("chart-distribution"), {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "count",
        data: values,
        backgroundColor: "#38bdf8",
        borderRadius: 4,
      }]
    },
    options: {
      scales: {
        y: { beginAtZero: true, ticks: { color: "#94a3b8", precision: 0 }, grid: { color: "#334155" } },
        x: { ticks: { color: "#94a3b8" }, grid: { display: false } },
      },
      plugins: { legend: { display: false } },
    },
  });
}

// ---------- A/B table ------------------------------------------------------
async function loadAB() {
  const p1 = document.getElementById("p1").value.trim();
  const p2 = document.getElementById("p2").value.trim();
  const data = await jget(`/api/ab?p1=${encodeURIComponent(p1)}&p2=${encodeURIComponent(p2)}`);

  // Index variants by name for easy lookup
  const v = Object.fromEntries(data.variants.map(x => [x.variant, x]));

  // Rows: latency, tokens, cost, then one per scorer
  const rows = [
    ["n",   v[p1]?.n ?? 0,   v[p2]?.n ?? 0,  null],
    ["avg latency (ms)", v[p1]?.avg_latency_ms, v[p2]?.avg_latency_ms, "lower"],
    ["avg tokens",       v[p1]?.avg_tokens,     v[p2]?.avg_tokens,     "lower"],
    ["total cost (USD)", v[p1]?.total_cost_usd, v[p2]?.total_cost_usd, "lower"],
  ];

  // Score rows: for each scorer, avg_score per variant
  const scorers = [...new Set(data.scores.map(s => s.scorer))].sort();
  for (const sc of scorers) {
    const a = data.scores.find(s => s.scorer === sc && s.variant === p1);
    const b = data.scores.find(s => s.scorer === sc && s.variant === p2);
    rows.push([`score · ${sc}`, a?.avg_score, b?.avg_score, "higher"]);
  }

  const tbody = document.querySelector("#ab-table tbody");
  tbody.innerHTML = rows.map(([label, a, b, prefer]) => {
    const aNum = typeof a === "number" ? a : null;
    const bNum = typeof b === "number" ? b : null;
    const delta = (aNum !== null && bNum !== null) ? (bNum - aNum) : null;

    let aClass = "", bClass = "";
    if (prefer && aNum !== null && bNum !== null && aNum !== bNum) {
      const aWins = prefer === "higher" ? aNum > bNum : aNum < bNum;
      aClass = aWins ? "winner" : "loser";
      bClass = aWins ? "loser"  : "winner";
    }

    const fmtCell = (n, digits = 3) => (typeof n === "number" ? n.toFixed(digits) : (n ?? "–"));

    return `<tr>
      <td>${label}</td>
      <td class="num ${aClass}">${fmtCell(aNum)}</td>
      <td class="num ${bClass}">${fmtCell(bNum)}</td>
      <td class="num">${delta === null ? "–" : (delta >= 0 ? "+" : "") + delta.toFixed(3)}</td>
    </tr>`;
  }).join("");
}


// ---------- wiring ---------------------------------------------------------
function populateScorerSelects() {
  for (const id of ["ts-scorer", "dist-scorer"]) {
    const sel = document.getElementById(id);
    sel.innerHTML = SCORERS.map(s => `<option value="${s}">${s}</option>`).join("");
  }
  document.getElementById("ts-scorer").addEventListener("change", loadTimeseries);
  document.getElementById("dist-scorer").addEventListener("change", loadDistribution);
}

async function refresh() {
  try {
    await Promise.all([loadSummary(), loadTimeseries(), loadDistribution(), loadAB()]);
  } catch (e) {
    console.error(e);
    alert("Failed to load: " + e.message);
  }
}

window.addEventListener("DOMContentLoaded", () => {
  populateScorerSelects();
  refresh();
});
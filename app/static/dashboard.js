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

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

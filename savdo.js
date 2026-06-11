// ============================================================
//  RestoPulse — Savdo sahifasi (iiko ma'lumotlari)
// ============================================================

// Brend → iiko filiallari → Instagram akkaunt moslashuvi
const BRANDS = {
  benison: {
    name: "Benison", color: "#ff7a59", letter: "B",
    departments: ["Benison-MegaCenter", "Benison-Oila", "Smart City"],
    ig: "benison_uz",
  },
  eddo: {
    name: "Eddo", color: "#f9b234", letter: "E",
    departments: ["Eddo"],
    ig: "eddo_uz",
    note: "+ Dieto taomlari shu yerda",
  },
  mazzona: {
    name: "Mazzona", color: "#2bb3a3", letter: "M",
    departments: ["Mazzona"],
    ig: null, // Instagram hali ulanmagan
  },
};
const BRAND_ORDER = ["benison", "eddo", "mazzona"];

let SAVDO = [];     // savdo_data.json
let TAOMLAR = null; // savdo_taomlar.json
let IG = [];        // instagram_data.json (korrelyatsiya uchun)
let PERIOD = "7";
let CHARTS = {};

// ---- Format ----
function fmtMoney(n) {
  n = n || 0;
  if (n >= 1e9) return (n / 1e9).toFixed(1).replace(".", ",") + " mlrd";
  if (n >= 1e6) return (n / 1e6).toFixed(1).replace(".", ",") + " mln";
  return Math.round(n).toLocaleString("ru-RU").replace(/,/g, " ");
}
function fmt(n) { return Math.round(n || 0).toLocaleString("ru-RU").replace(/,/g, " "); }

// ---- Davr ----
function periodDays() {
  if (PERIOD === "all") return SAVDO;
  return SAVDO.slice(-parseInt(PERIOD, 10));
}

// ---- Brend bo'yicha kunlik yig'indi ----
function brandDay(day, brandKey) {
  const b = BRANDS[brandKey];
  let revenue = 0, checks = 0;
  b.departments.forEach(dep => {
    const d = (day.departments || {})[dep];
    if (d) { revenue += d.revenue || 0; checks += d.checks || 0; }
  });
  return { revenue, checks };
}

function brandTotals(brandKey, days) {
  let revenue = 0, checks = 0;
  days.forEach(day => {
    const v = brandDay(day, brandKey);
    revenue += v.revenue; checks += v.checks;
  });
  return { revenue, checks, avg: checks ? Math.round(revenue / checks) : 0 };
}

// ---- O'sish (davrning birinchi yarmiga nisbatan ikkinchi yarmi) ----
function halfGrowth(brandKey, days) {
  if (days.length < 4) return null;
  const mid = Math.floor(days.length / 2);
  const a = brandTotals(brandKey, days.slice(0, mid)).revenue / mid;
  const b = brandTotals(brandKey, days.slice(mid)).revenue / (days.length - mid);
  if (!a) return null;
  return Math.round((b - a) / a * 100);
}

// ============================================================
//  RENDER
// ============================================================
function renderSummary() {
  const days = periodDays();
  let revenue = 0, checks = 0;
  BRAND_ORDER.forEach(b => {
    const t = brandTotals(b, days);
    revenue += t.revenue; checks += t.checks;
  });
  const avg = checks ? Math.round(revenue / checks) : 0;

  document.getElementById("summary").innerHTML = `
    <div class="kpi glass">
      <div class="label">💵 Jami tushum</div>
      <div class="val">${fmtMoney(revenue)}</div>
      <div class="sub">so'm · ${days.length} kun · barcha filiallar</div>
    </div>
    <div class="kpi glass">
      <div class="label">🧾 Cheklar soni</div>
      <div class="val">${fmt(checks)}</div>
      <div class="sub">Mijozlar oqimi</div>
    </div>
    <div class="kpi glass">
      <div class="label">🛒 O'rtacha chek</div>
      <div class="val">${fmt(avg)}</div>
      <div class="sub">so'm</div>
    </div>
    <div class="kpi glass">
      <div class="label">📅 Kunlik o'rtacha</div>
      <div class="val">${fmtMoney(days.length ? revenue / days.length : 0)}</div>
      <div class="sub">so'm / kun</div>
    </div>`;
}

function renderBrands() {
  const days = periodDays();
  const el = document.getElementById("brands");
  el.innerHTML = BRAND_ORDER.map(key => {
    const b = BRANDS[key];
    const t = brandTotals(key, days);
    const g = halfGrowth(key, days);
    const chg = g === null ? "" :
      `<span class="chg ${g >= 0 ? "up" : "down"}">${g >= 0 ? "↑" : "↓"} ${Math.abs(g)}%</span>`;
    return `
      <div class="brand-card glass">
        <div class="brand-head">
          <div class="brand-avatar" style="background:${b.color}">${b.letter}</div>
          <div>
            <h3>${b.name}</h3>
            <div class="fil">${b.departments.join(" · ")}${b.note ? " · " + b.note : ""}</div>
          </div>
        </div>
        <div class="brand-row"><span class="rl">Tushum</span><span class="rv">${fmtMoney(t.revenue)} ${chg}</span></div>
        <div class="brand-row"><span class="rl">Cheklar</span><span class="rv">${fmt(t.checks)}</span></div>
        <div class="brand-row"><span class="rl">O'rtacha chek</span><span class="rv">${fmt(t.avg)}</span></div>
      </div>`;
  }).join("");
}

function destroyChart(id) { if (CHARTS[id]) { CHARTS[id].destroy(); delete CHARTS[id]; } }
function chartReady() { return typeof Chart !== "undefined"; }

function baseOpts() {
  return {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { labels: { color:"#3a2456", font:{size:13, weight:"600"}, usePointStyle:true, pointStyle:"circle" } } },
    scales: {
      x: { ticks:{color:"#6b5b8a", font:{size:11}}, grid:{color:"rgba(120,80,160,0.08)"} },
      y: { ticks:{color:"#6b5b8a", font:{size:11}}, grid:{color:"rgba(120,80,160,0.1)"} }
    }
  };
}

function renderRevenueChart() {
  if (!chartReady()) return;
  const days = periodDays();
  destroyChart("chartRevenue");
  const labels = days.map(d => {
    const dt = new Date(d.date); return dt.toLocaleDateString("ru-RU", {day:"2-digit", month:"2-digit"});
  });
  const datasets = BRAND_ORDER.map(key => {
    const b = BRANDS[key];
    return {
      label: b.name, borderColor: b.color, backgroundColor: b.color + "22",
      data: days.map(d => +(brandDay(d, key).revenue / 1e6).toFixed(1)),
      tension: 0.35, borderWidth: 3, pointRadius: 3, pointBackgroundColor: b.color,
    };
  });
  const opts = baseOpts();
  opts.scales.y.title = { display: true, text: "mln so'm", color: "#6b5b8a", font: {size: 11} };
  CHARTS["chartRevenue"] = new Chart(document.getElementById("chartRevenue"),
    { type: "line", data: { labels, datasets }, options: opts });
}

// ---- Marketing ↔ Savdo korrelyatsiya grafiklari ----
function igSnapForDate(date) {
  return IG.find(s => s.date === date) || null;
}
function postDatesFor(igAcc) {
  // Oxirgi IG snapshot'dagi postlarning chiqqan sanalari
  if (!IG.length) return new Set();
  const last = IG[IG.length - 1];
  const acc = last.accounts && last.accounts[igAcc];
  const set = new Set();
  if (acc && acc.posts) {
    acc.posts.forEach(p => {
      if (p.timestamp) set.add(p.timestamp.slice(0, 10));
    });
  }
  return set;
}

function renderCorrelation() {
  const el = document.getElementById("corrCharts");
  const days = periodDays();
  let html = "";
  const targets = BRAND_ORDER.filter(k => BRANDS[k].ig);

  targets.forEach(key => {
    html += `
      <div class="chart-card glass">
        <h3>${BRANDS[key].name}: qamrov va tushum</h3>
        <div class="csub">Ustunlar — kunlik tushum (mln). Chiziq — Instagram qamrovi (7 kun). ⭐ — post chiqqan kunlar</div>
        <div class="chart-box"><canvas id="corr-${key}"></canvas></div>
      </div>`;
  });
  el.innerHTML = html || `<div class="glass empty">Instagram bog'langan brendlar yo'q</div>`;

  if (!chartReady()) return;
  targets.forEach(key => {
    const b = BRANDS[key];
    destroyChart("corr-" + key);
    const labels = days.map(d => new Date(d.date).toLocaleDateString("ru-RU", {day:"2-digit", month:"2-digit"}));
    const revData = days.map(d => +(brandDay(d, key).revenue / 1e6).toFixed(1));
    const reachData = days.map(d => {
      const s = igSnapForDate(d.date);
      const acc = s && s.accounts && s.accounts[b.ig];
      return acc ? acc.reach_7d || null : null;
    });
    const posts = postDatesFor(b.ig);
    const postMarks = days.map((d, i) => posts.has(d.date) ? revData[i] * 1.06 : null);

    CHARTS["corr-" + key] = new Chart(document.getElementById("corr-" + key), {
      data: {
        labels,
        datasets: [
          { type: "bar", label: "Tushum (mln)", data: revData,
            backgroundColor: b.color + "99", borderRadius: 8, yAxisID: "y", order: 3 },
          { type: "line", label: "Qamrov (7 kun)", data: reachData,
            borderColor: "#962fbf", backgroundColor: "#962fbf22", tension: 0.35,
            borderWidth: 3, pointRadius: 3, pointBackgroundColor: "#962fbf",
            yAxisID: "y2", spanGaps: true, order: 1 },
          { type: "scatter", label: "Post chiqqan kun", data: postMarks,
            pointStyle: "star", pointRadius: 8, pointBorderWidth: 2,
            borderColor: "#d62976", backgroundColor: "#d62976",
            yAxisID: "y", order: 0 },
        ],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { labels: { color:"#3a2456", font:{size:12, weight:"600"}, usePointStyle:true } } },
        scales: {
          x: { ticks:{color:"#6b5b8a", font:{size:11}}, grid:{display:false} },
          y: { position:"left", ticks:{color:"#6b5b8a", font:{size:11}},
               grid:{color:"rgba(120,80,160,0.1)"},
               title:{display:true, text:"mln so'm", color:"#6b5b8a", font:{size:10}} },
          y2: { position:"right", ticks:{color:"#962fbf", font:{size:11}},
                grid:{display:false},
                title:{display:true, text:"qamrov", color:"#962fbf", font:{size:10}} },
        },
      },
    });
  });
}

function renderDishes() {
  const el = document.getElementById("dishes");
  if (!TAOMLAR || !TAOMLAR.departments) {
    el.innerHTML = `<div class="glass empty">Taomlar ma'lumoti hali yo'q</div>`;
    return;
  }
  // Filiallarni brendga yig'amiz
  const byBrand = {};
  BRAND_ORDER.forEach(key => {
    const b = BRANDS[key];
    const all = {};
    b.departments.forEach(dep => {
      (TAOMLAR.departments[dep] || []).forEach(x => {
        if (!all[x.dish]) all[x.dish] = { dish: x.dish, sum: 0, amount: 0 };
        all[x.dish].sum += x.sum; all[x.dish].amount += x.amount;
      });
    });
    byBrand[key] = Object.values(all).sort((a, b2) => b2.sum - a.sum).slice(0, 8);
  });

  el.innerHTML = BRAND_ORDER.map(key => {
    const b = BRANDS[key];
    const list = byBrand[key];
    if (!list.length) return "";
    return `
      <div class="dish-card glass">
        <h4><span class="ddot" style="background:${b.color}"></span>${b.name}</h4>
        ${list.map((x, i) => `
          <div class="dish-item">
            <div class="dish-rank">${i + 1}</div>
            <div class="dish-name">${escapeHtml(x.dish)}</div>
            <div class="dish-amt">${fmt(x.amount)} dona</div>
            <div class="dish-sum">${fmtMoney(x.sum)}</div>
          </div>`).join("")}
      </div>`;
  }).join("");
}

function escapeHtml(s) {
  return (s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function renderOpps() {
  const el = document.getElementById("opps");
  if (!TAOMLAR || !TAOMLAR.opportunities) {
    el.innerHTML = `<div class="glass empty" style="grid-column:1/-1">Bu tahlil keyingi savdo yig'ishdan keyin paydo bo'ladi (Actions → "iiko savdo yig'ish")</div>`;
    return;
  }
  const byBrand = {};
  BRAND_ORDER.forEach(key => {
    const b = BRANDS[key];
    const all = {};
    b.departments.forEach(dep => {
      (TAOMLAR.opportunities[dep] || []).forEach(x => {
        if (!all[x.dish] || x.price > all[x.dish].price) all[x.dish] = x;
      });
    });
    byBrand[key] = Object.values(all).sort((a, b2) => b2.price - a.price).slice(0, 6);
  });

  const html = BRAND_ORDER.map(key => {
    const b = BRANDS[key];
    const list = byBrand[key];
    if (!list.length) return "";
    return `
      <div class="dish-card glass">
        <h4><span class="ddot" style="background:${b.color}"></span>${b.name} — sinab ko'rilmagan xazinalar</h4>
        ${list.map((x, i) => `
          <div class="dish-item">
            <div class="dish-rank">💎</div>
            <div class="dish-name">${escapeHtml(x.dish)}</div>
            <div class="dish-amt">${fmt(x.amount)} dona/hafta</div>
            <div class="dish-sum">${fmt(x.price)} so'm</div>
          </div>`).join("")}
        <div style="font-size:11.5px;color:var(--muted);margin-top:10px;line-height:1.5;">Bu taomlar qimmat (daromadli), lekin kam buyurtirilyapti — reklama qilish uchun eng foydali nomzodlar. AI keyingi rejada shularni hisobga oladi.</div>
      </div>`;
  }).join("");
  el.innerHTML = html || `<div class="glass empty" style="grid-column:1/-1">Nomzodlar topilmadi</div>`;
}

function rerender() {
  renderSummary();
  renderBrands();
  renderRevenueChart();
  renderCorrelation();
  renderDishes();
  renderOpps();
}

// ============================================================
//  Yuklash
// ============================================================
async function loadData() {
  try {
    const r = await fetch("savdo_data.json?v=" + Date.now());
    if (r.ok) SAVDO = await r.json();
  } catch (e) {}
  try {
    const r = await fetch("savdo_taomlar.json?v=" + Date.now());
    if (r.ok) TAOMLAR = await r.json();
  } catch (e) {}
  try {
    const r = await fetch("instagram_data.json?v=" + Date.now());
    if (r.ok) IG = await r.json();
  } catch (e) {}

  if (SAVDO.length) {
    document.getElementById("lastUpdate").textContent = SAVDO[SAVDO.length - 1].date;
  }
}

(async function init() {
  await loadData();
  document.querySelectorAll(".per").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".per").forEach(x => x.classList.remove("active"));
      btn.classList.add("active");
      PERIOD = btn.dataset.period;
      rerender();
    });
  });
  if (!SAVDO.length) {
    document.getElementById("summary").innerHTML =
      `<div class="glass empty" style="grid-column:1/-1">Savdo ma'lumotlari hali yo'q — Actions'da "iiko savdo yig'ish"ni ishga tushiring.</div>`;
    return;
  }
  rerender();
})();

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
let TURLAR = null;  // savdo_turlar.json (buyurtma turlari)
let DISHDAY = null; // savdo_taom_kun.json (taom×kun atributsiya)
let FIL_GRAN = "kunlik"; // filiallar kesimi
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
    plugins: { legend: { labels: { color:"#1C1C1E", font:{size:13, weight:"600"}, usePointStyle:true, pointStyle:"circle" } } },
    scales: {
      x: { ticks:{color:"rgba(60,60,67,0.6)", font:{size:11}}, grid:{color:"rgba(60,60,67,0.06)"} },
      y: { ticks:{color:"rgba(60,60,67,0.6)", font:{size:11}}, grid:{color:"rgba(60,60,67,0.08)"} }
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
        plugins: { legend: { labels: { color:"#1C1C1E", font:{size:12, weight:"600"}, usePointStyle:true } } },
        scales: {
          x: { ticks:{color:"rgba(60,60,67,0.6)", font:{size:11}}, grid:{display:false} },
          y: { position:"left", ticks:{color:"rgba(60,60,67,0.6)", font:{size:11}},
               grid:{color:"rgba(60,60,67,0.08)"},
               title:{display:true, text:"mln so'm", color:"rgba(60,60,67,0.6)", font:{size:10}} },
          y2: { position:"right", ticks:{color:"#34C759", font:{size:11}},
                grid:{display:false},
                title:{display:true, text:"qamrov", color:"#34C759", font:{size:10}} },
        },
      },
    });
  });
}

// ---- 🎯 Marketing atributsiya (Daraja 1: post oldidan vs keyin savdo) ----

// SAVDO massividan sana -> brend kunlik tushum (tez qidirish uchun map)
function brandRevByDate(brandKey) {
  const map = {};
  SAVDO.forEach(day => { map[day.date] = brandDay(day, brandKey).revenue; });
  return map;
}

// Sana atrofidagi N kun o'rtacha kunlik tushum (from..to oraliq)
function avgRevWindow(revMap, centerDate, startOffset, endOffset) {
  const c = new Date(centerDate + "T00:00:00");
  let sum = 0, n = 0;
  for (let k = startOffset; k <= endOffset; k++) {
    const d = new Date(c); d.setDate(d.getDate() + k);
    const key = d.toISOString().slice(0, 10);
    if (revMap[key] != null && revMap[key] > 0) { sum += revMap[key]; n++; }
  }
  return n ? { avg: sum / n, days: n } : null;
}

// Brendning yirik postlari (reach bo'yicha, atributsiya uchun)
function topPostsFor(brandKey, limit) {
  const b = BRANDS[brandKey];
  if (!b.ig || !IG.length) return [];
  const last = IG[IG.length - 1];
  const acc = last.accounts && last.accounts[b.ig];
  if (!acc || !acc.posts) return [];
  return acc.posts
    .filter(p => p.timestamp && (p.reach || p.views || p.like_count))
    .map(p => ({
      date: p.timestamp.slice(0, 10),
      reach: p.reach || p.views || 0,
      likes: p.like_count || 0,
      caption: (p.caption || "").replace(/\s+/g, " ").trim(),
    }))
    .sort((a, b2) => b2.reach - a.reach)
    .slice(0, limit || 6);
}

// Har post uchun atributsiya: oldidan 7 kun vs keyin 7 kun
function postAttribution(brandKey, post, revMap) {
  const before = avgRevWindow(revMap, post.date, -7, -1);
  const after = avgRevWindow(revMap, post.date, 1, 7);
  if (!before || !after) return null;
  const pct = before.avg > 0 ? Math.round((after.avg - before.avg) / before.avg * 100) : null;
  return { before: before.avg, after: after.avg, pct, beforeDays: before.days, afterDays: after.days };
}

function renderAttribution() {
  const el = document.getElementById("attribution");
  if (!el) return;
  const targets = BRAND_ORDER.filter(k => BRANDS[k].ig);
  if (!targets.length || !SAVDO.length) {
    el.innerHTML = `<div class="glass empty">Atributsiya uchun Instagram va savdo ma'lumoti kerak</div>`;
    return;
  }

  let html = "";
  targets.forEach(key => {
    const b = BRANDS[key];
    const revMap = brandRevByDate(key);
    const posts = topPostsFor(key, 6);
    if (!posts.length) return;

    const cards = posts.map(p => {
      const a = postAttribution(key, p, revMap);
      const cap = p.caption ? (p.caption.length > 70 ? p.caption.slice(0, 70) + "…" : p.caption) : "(matnsiz post)";
      let badge, detail;
      if (!a) {
        badge = `<span class="att-badge att-na">ma'lumot yetarli emas</span>`;
        detail = `<div class="att-detail">Bu post atrofida 7 kunlik to'liq savdo ma'lumoti yo'q (yangi yoki eski post)</div>`;
      } else {
        const cls = a.pct > 0 ? "att-up" : (a.pct < 0 ? "att-down" : "att-flat");
        const arrow = a.pct > 0 ? "↑" : (a.pct < 0 ? "↓" : "→");
        badge = `<span class="att-badge ${cls}">${arrow} ${a.pct === null ? "—" : Math.abs(a.pct) + "%"}</span>`;
        detail = `<div class="att-detail">
          <span>Oldidan: <b>${fmtMoney(Math.round(a.before))}</b>/kun</span>
          <span>Keyin: <b>${fmtMoney(Math.round(a.after))}</b>/kun</span>
        </div>`;
      }
      return `
        <div class="att-post">
          <div class="att-top">
            <div class="att-meta">
              <div class="att-date">${new Date(p.date).toLocaleDateString("ru-RU", {day:"2-digit",month:"short"})}</div>
              <div class="att-reach">👁 ${fmt(p.reach)}${p.likes ? " · ❤️ " + fmt(p.likes) : ""}</div>
            </div>
            ${badge}
          </div>
          <div class="att-cap">${cap}</div>
          ${detail}
        </div>`;
    }).join("");

    html += `
      <div class="chart-card glass">
        <h3>${b.name}: yirik postlar ta'siri</h3>
        <div class="csub">Har post chiqishidan <b>oldingi 7 kun</b> o'rtacha kunlik savdo vs <b>keyingi 7 kun</b>. Bu sabab emas, bog'liqlikni ko'rsatadi.</div>
        <div class="att-list">${cards}</div>
      </div>`;
  });

  el.innerHTML = html || `<div class="glass empty">Yirik postlar topilmadi</div>`;
}

// ---- 🏢 Filiallar (har biri alohida, kunlik/haftalik/oylik) ----
// Barcha filiallar ro'yxati (BRANDS dan), har biri qaysi brendga tegishli
function allDepts() {
  const out = [];
  BRAND_ORDER.forEach(bk => {
    BRANDS[bk].departments.forEach(dep => out.push({ dep, brand: bk, color: BRANDS[bk].color }));
  });
  return out;
}

// Bitta filialning bitta kundagi ko'rsatkichi
function depDay(day, dep) {
  const d = (day.departments || {})[dep];
  return d ? { revenue: d.revenue || 0, checks: d.checks || 0 } : { revenue: 0, checks: 0 };
}

// Davrni kunlik/haftalik/oylik bo'laklarga guruhlash
function buckets(days, gran) {
  if (gran === "kunlik") {
    return days.slice(-10).map(d => ({ label: d.date.slice(5), days: [d] }));
  }
  const map = new Map();
  days.forEach(d => {
    let key;
    if (gran === "oylik") {
      key = d.date.slice(0, 7); // YYYY-MM
    } else {
      // haftalik: ISO haftaga yaqin — sanani 7 kunlik blokka
      const dt = new Date(d.date + "T00:00:00");
      const onejan = new Date(dt.getFullYear(), 0, 1);
      const week = Math.ceil((((dt - onejan) / 86400000) + onejan.getDay() + 1) / 7);
      key = dt.getFullYear() + "-H" + String(week).padStart(2, "0");
    }
    if (!map.has(key)) map.set(key, []);
    map.get(key).push(d);
  });
  const arr = [...map.entries()].map(([label, ds]) => ({ label, days: ds }));
  arr.sort((a, b) => a.label.localeCompare(b.label));
  // Faqat oxirgi 8 bo'lakni ko'rsatamiz
  return arr.slice(-8);
}

function depDostShare(dep, days) {
  if (!TURLAR || !Array.isArray(TURLAR)) return null;
  const set = new Set(days.map(d => d.date));
  let dost = 0, tot = 0;
  TURLAR.forEach(td => {
    if (!set.has(td.date)) return;
    const node = (td.departments || {})[dep];
    if (!node) return;
    Object.entries(node).forEach(([kind, v]) => {
      tot += v.revenue || 0;
      if (kind === "dostavka") dost += v.revenue || 0;
    });
  });
  return tot > 0 ? Math.round(dost / tot * 100) : null;
}

function depKindBucket(dep, days) {
  // Bir filial uchun davr ichidagi dostavka/zal/olib_ketish tushumi
  if (!TURLAR || !Array.isArray(TURLAR)) return null;
  const set = new Set(days.map(d => d.date));
  let dost = 0, zal = 0, olib = 0;
  TURLAR.forEach(td => {
    if (!set.has(td.date)) return;
    const node = (td.departments || {})[dep];
    if (!node) return;
    Object.entries(node).forEach(([kind, v]) => {
      const r = v.revenue || 0;
      if (kind === "dostavka") dost += r;
      else if (kind === "olib_ketish") olib += r;
      else zal += r;
    });
  });
  return { dost, zal, olib };
}

function renderFiliallar() {
  const el = document.getElementById("filiallar");
  if (!el) return;
  const days = periodDays();
  const bkts = buckets(days, FIL_GRAN);
  const granNom = { kunlik: "Kun", haftalik: "Hafta", oylik: "Oy" }[FIL_GRAN];
  const hasTur = !!(TURLAR && Array.isArray(TURLAR) && TURLAR.length);

  el.innerHTML = allDepts().map(({ dep, brand, color }) => {
    // Davr jami
    let revenue = 0, checks = 0;
    days.forEach(d => { const v = depDay(d, dep); revenue += v.revenue; checks += v.checks; });
    if (revenue <= 0 && checks <= 0) return ""; // bu filialda ma'lumot yo'q
    const avg = checks ? Math.round(revenue / checks) : 0;
    const dpct = depDostShare(dep, days);

    // Mini jadval — har bo'lak bo'yicha BARCHA ko'rsatkichlar
    const rows = bkts.map(bk => {
      let r = 0, c = 0;
      bk.days.forEach(d => { const v = depDay(d, dep); r += v.revenue; c += v.checks; });
      const a = c ? Math.round(r / c) : 0;
      let turCols = "";
      if (hasTur) {
        const kb = depKindBucket(dep, bk.days) || { dost: 0, zal: 0 };
        const tot = kb.dost + kb.zal + (kb.olib || 0);
        const sh = tot > 0 ? Math.round(kb.dost / tot * 100) : 0;
        turCols = `<td>${fmtMoney(kb.dost)}</td><td>${fmtMoney(kb.zal)}</td><td><span class="fil-dost">${sh}%</span></td>`;
      }
      return `<tr><td>${bk.label}</td><td><b>${fmtMoney(r)}</b></td><td>${fmt(c)}</td><td>${fmt(a)}</td>${turCols}</tr>`;
    }).join("");

    const turHead = hasTur ? `<th>🛵 Dost.</th><th>🍽 Zal</th><th>Ulush</th>` : "";

    return `
      <div class="brand-card glass fil-card">
        <div class="brand-head">
          <div class="brand-avatar" style="background:${color}">${dep[0]}</div>
          <div>
            <h3 style="font-size:16px;">${dep}</h3>
            <div class="fil">${BRANDS[brand].name}${dpct !== null ? ` · 🛵 dostavka ${dpct}%` : ""}</div>
          </div>
        </div>
        <div class="brand-row"><span class="rl">Tushum (${PERIOD === "all" ? "jami" : PERIOD + " kun"})</span><span class="rv">${fmtMoney(revenue)}</span></div>
        <div class="brand-row"><span class="rl">Cheklar</span><span class="rv">${fmt(checks)}</span></div>
        <div class="brand-row"><span class="rl">O'rtacha chek</span><span class="rv">${fmt(avg)}</span></div>
        <div class="fil-mini">
          <table>
            <thead><tr><th>${granNom}</th><th>Tushum</th><th>Chek</th><th>O'rt.</th>${turHead}</tr></thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      </div>`;
  }).join("");
}

// ---- 🛵 Dostavka vs Zal ----
function turlarDays() {
  if (!TURLAR || !Array.isArray(TURLAR)) return [];
  if (PERIOD === "all") return TURLAR;
  return TURLAR.slice(-parseInt(PERIOD, 10));
}

function renderDelivery() {
  const wrap = document.getElementById("deliveryWrap");
  if (!wrap) return;
  const days = turlarDays();
  if (!days.length) {
    wrap.innerHTML = `<div class="glass empty">Dostavka ma'lumoti hali yig'ilmagan. Actions'da <b>"iiko savdo yig'ish"</b>ni bir marta ishga tushiring — keyin shu yerda dostavka/zal taqsimoti chiqadi.</div>`;
    return;
  }

  const KINDS = [
    { k: "dostavka", nom: "Dostavka", emoji: "🛵", rang: "#34C759" },
    { k: "zal", nom: "Zal", emoji: "🍽", rang: "#5856D6" },
    { k: "olib_ketish", nom: "Olib ketish", emoji: "🥡", rang: "#FF9500" },
  ];

  // Umumiy yig'indi (kind -> revenue, checks) + brend bo'yicha
  const jami = {};
  const brandKind = {}; // brand -> kind -> revenue
  KINDS.forEach(x => jami[x.k] = { revenue: 0, checks: 0 });

  days.forEach(day => {
    Object.entries(day.departments || {}).forEach(([dep, kinds]) => {
      // dep -> qaysi brand?
      let brand = null;
      for (const bk of BRAND_ORDER) {
        if (BRANDS[bk].departments.includes(dep)) { brand = bk; break; }
      }
      Object.entries(kinds).forEach(([kind, v]) => {
        if (!jami[kind]) jami[kind] = { revenue: 0, checks: 0 };
        jami[kind].revenue += v.revenue || 0;
        jami[kind].checks += v.checks || 0;
        if (brand) {
          brandKind[brand] = brandKind[brand] || {};
          brandKind[brand][kind] = (brandKind[brand][kind] || 0) + (v.revenue || 0);
        }
      });
    });
  });

  const jamiRev = KINDS.reduce((s, x) => s + (jami[x.k] ? jami[x.k].revenue : 0), 0);
  if (jamiRev <= 0) {
    wrap.innerHTML = `<div class="glass empty">Tanlangan davrda buyurtma turi ma'lumoti yo'q.</div>`;
    return;
  }

  // KPI kartalari
  const kpis = KINDS.map(x => {
    const rev = jami[x.k] ? jami[x.k].revenue : 0;
    const chk = jami[x.k] ? jami[x.k].checks : 0;
    const pct = Math.round(rev / jamiRev * 100);
    const avg = chk ? Math.round(rev / chk) : 0;
    return `<div class="kpi glass">
      <div class="label">${x.emoji} ${x.nom}</div>
      <div class="val" style="color:${x.rang}">${fmtMoney(rev)}<span class="chg up" style="color:${x.rang};background:${x.rang}1f">${pct}%</span></div>
      <div class="sub">${fmt(chk)} chek · o'rtacha ${fmt(avg)} so'm</div>
    </div>`;
  }).join("");

  // Brend bo'yicha dostavka ulushi
  const brandRows = BRAND_ORDER.map(bk => {
    const kinds = brandKind[bk] || {};
    const tot = Object.values(kinds).reduce((s, v) => s + v, 0);
    if (tot <= 0) return "";
    const dost = kinds["dostavka"] || 0;
    const dpct = Math.round(dost / tot * 100);
    const b = BRANDS[bk];
    return `<div style="margin-bottom:13px;">
      <div style="display:flex;justify-content:space-between;font-size:13px;font-weight:500;margin-bottom:6px;">
        <span style="font-weight:600;color:${b.color}">${b.name}</span>
        <span style="color:var(--muted)">dostavka <b style="color:var(--ink);font-variant-numeric:tabular-nums">${dpct}%</b> · ${fmtMoney(dost)}</span>
      </div>
      <div style="height:9px;border-radius:5px;background:var(--fill);overflow:hidden;display:flex;">
        <div style="width:${dpct}%;background:#34C759;"></div>
      </div>
    </div>`;
  }).join("");

  wrap.innerHTML = `
    <div class="kpi-grid" style="margin-bottom:13px;">${kpis}</div>
    <div class="two-col">
      <div class="chart-card glass">
        <h3>Dostavka dinamikasi</h3>
        <div class="csub">Kunlik dostavka tushumi, mln so'm</div>
        <div class="chart-box" style="height:250px;"><canvas id="delivChart"></canvas></div>
      </div>
      <div class="glass" style="padding:22px 24px;">
        <h3 style="font-size:16.5px;font-weight:600;letter-spacing:-.35px;margin-bottom:4px;">Brendlar bo'yicha dostavka ulushi</h3>
        <div class="csub" style="color:var(--muted);font-size:13px;margin-bottom:16px;">Har brend tushumining qancha qismi yetkazib berishdan</div>
        ${brandRows || '<div class="empty">Ma\'lumot yo\'q</div>'}
      </div>
    </div>`;

  // Dinamika grafigi (dostavka kunlik)
  if (window.Chart) {
    const labels = days.map(d => d.date.slice(5));
    const dostByDay = days.map(day => {
      let s = 0;
      Object.values(day.departments || {}).forEach(kinds => {
        if (kinds.dostavka) s += kinds.dostavka.revenue || 0;
      });
      return Math.round(s / 1e6 * 10) / 10;
    });
    if (CHARTS.deliv) CHARTS.deliv.destroy();
    CHARTS.deliv = new Chart(document.getElementById("delivChart"), {
      type: "bar",
      data: { labels, datasets: [{ label: "Dostavka (mln)", data: dostByDay, backgroundColor: "#34C759", borderRadius: 6 }] },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: "rgba(60,60,67,0.6)", font: { size: 11 } }, grid: { display: false } },
          y: { ticks: { color: "rgba(60,60,67,0.6)", font: { size: 11 } }, grid: { color: "rgba(60,60,67,0.08)" } },
        },
      },
    });
  }
}

function renderDishes() {  const el = document.getElementById("dishes");
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
  renderAttribution();
  renderDelivery();
  renderFiliallar();
  renderDishes();
  renderOpps();
}

// ============================================================
//  Shifr ochish (Web Crypto API) — kalit sayt parolidan
// ============================================================
function getParol() {
  const pw = sessionStorage.getItem("rp_pw");
  if (!pw) return null;
  try { return decodeURIComponent(escape(atob(pw))); } catch (e) { return null; }
}

async function dekript(blob, parol) {
  const b64 = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));
  const km = await crypto.subtle.importKey("raw", new TextEncoder().encode(parol), "PBKDF2", false, ["deriveKey"]);
  const key = await crypto.subtle.deriveKey(
    { name: "PBKDF2", salt: b64(blob.salt), iterations: 150000, hash: "SHA-256" },
    km, { name: "AES-GCM", length: 256 }, false, ["decrypt"]);
  const pt = await crypto.subtle.decrypt({ name: "AES-GCM", iv: b64(blob.iv) }, key, b64(blob.ct));
  return JSON.parse(new TextDecoder().decode(pt));
}

async function fetchEncrypted(encUrl, plainUrl) {
  // 1) Shifrlangan faylni urinish
  try {
    const r = await fetch(encUrl + "?v=" + Date.now());
    if (r.ok) {
      const blob = await r.json();
      if (blob && blob.ct) {
        const parol = getParol();
        if (!parol) { location.replace("kirish.html"); return null; } // qayta kirish kerak
        return await dekript(blob, parol);
      }
    }
  } catch (e) {}
  // 2) O'tish davri: eski ochiq fayl
  try {
    const r = await fetch(plainUrl + "?v=" + Date.now());
    if (r.ok) return await r.json();
  } catch (e) {}
  return null;
}

// ============================================================
//  Yuklash
// ============================================================
async function loadData() {
  SAVDO = (await fetchEncrypted("savdo_data.enc.json", "savdo_data.json")) || [];
  TAOMLAR = await fetchEncrypted("savdo_taomlar.enc.json", "savdo_taomlar.json");
  TURLAR = await fetchEncrypted("savdo_turlar.enc.json", "savdo_turlar.json");
  DISHDAY = await fetchEncrypted("savdo_taom_kun.enc.json", "savdo_taom_kun.json");
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
  document.querySelectorAll(".fseg").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".fseg").forEach(x => x.classList.remove("active"));
      btn.classList.add("active");
      FIL_GRAN = btn.dataset.gran;
      renderFiliallar();
    });
  });
  if (!SAVDO.length) {
    document.getElementById("summary").innerHTML =
      `<div class="glass empty" style="grid-column:1/-1">Savdo ma'lumotlari hali yo'q — Actions'da "iiko savdo yig'ish"ni ishga tushiring.</div>`;
    return;
  }
  rerender();
})();

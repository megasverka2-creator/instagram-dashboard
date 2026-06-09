// ============================================================
//  Instagram Dashboard — ma'lumotni o'qish va ko'rsatish
// ============================================================

const META = {
  benison_uz: { name: "Benison", handle: "@benison_uz", color: "#ff7a59", letter: "B" },
  dieto_uz:   { name: "Dieto",   handle: "@dieto_uz",   color: "#8a5cf6", letter: "D" },
  eddo_uz:    { name: "Eddo",    handle: "@eddo_uz",    color: "#f9b234", letter: "E" },
};
const ORDER = ["benison_uz", "dieto_uz", "eddo_uz"];

let HISTORY = [];      // barcha kunlik snapshotlar
let PERIOD = "7";      // 7 | 30 | all
let PAGE = "overview";
let CHARTS = {};       // chart instanslari (qayta chizishda o'chirish uchun)

// ---- Ikonkalar (inline SVG) ----
const IC = {
  users: '<svg viewBox="0 0 24 24" fill="none"><path d="M16 19v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="9" cy="7" r="3.2" stroke="currentColor" stroke-width="2"/><path d="M22 19v-2a4 4 0 00-3-3.8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
  eye: '<svg viewBox="0 0 24 24" fill="none"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/></svg>',
  heart: '<svg viewBox="0 0 24 24" fill="none"><path d="M12 21s-7-4.5-9.5-9C1 9 2.5 5.5 6 5.5c2 0 3.2 1.2 4 2.3.8-1.1 2-2.3 4-2.3 3.5 0 5 3.5 3.5 6.5C19 16.5 12 21 12 21z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
  bookmark: '<svg viewBox="0 0 24 24" fill="none"><path d="M6 3h12a1 1 0 011 1v17l-7-4-7 4V4a1 1 0 011-1z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
  share: '<svg viewBox="0 0 24 24" fill="none"><path d="M4 12v7a1 1 0 001 1h14a1 1 0 001-1v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M12 16V3M12 3L8 7M12 3l4 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  fire: '<svg viewBox="0 0 24 24" fill="none"><path d="M12 2s4 4 4 8a4 4 0 11-8 0c0-1 .3-2 .8-2.6C8 8 7 9.5 7 12a5 5 0 1010 0c0-5-5-10-5-10z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
  grid: '<svg viewBox="0 0 24 24" fill="none"><rect x="3" y="3" width="7" height="7" rx="1.5" stroke="currentColor" stroke-width="2"/><rect x="14" y="3" width="7" height="7" rx="1.5" stroke="currentColor" stroke-width="2"/><rect x="3" y="14" width="7" height="7" rx="1.5" stroke="currentColor" stroke-width="2"/><rect x="14" y="14" width="7" height="7" rx="1.5" stroke="currentColor" stroke-width="2"/></svg>',
  chart: '<svg viewBox="0 0 24 24" fill="none"><path d="M3 3v18h18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M7 14l3-3 3 2 5-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  pin: '<svg viewBox="0 0 24 24" fill="none"><path d="M12 21s-7-5.5-7-11a7 7 0 1114 0c0 5.5-7 11-7 11z" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="10" r="2.5" stroke="currentColor" stroke-width="2"/></svg>',
  bolt: '<svg viewBox="0 0 24 24" fill="none"><path d="M13 2L4 14h7l-1 8 9-12h-7l1-8z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
};

// ---- Sonni chiroyli ko'rsatish ----
function fmt(n) {
  if (n === null || n === undefined) return "—";
  return Math.round(n).toLocaleString("ru-RU").replace(/,/g, " ");
}
function fmtType(t) {
  return { IMAGE: "Rasm", VIDEO: "Video", CAROUSEL_ALBUM: "Karusel", REELS: "Reels" }[t] || t || "Boshqa";
}

// ---- Davr bo'yicha snapshotlarni filtrlash ----
function periodSnaps() {
  if (PERIOD === "all") return HISTORY;
  const days = parseInt(PERIOD, 10);
  return HISTORY.slice(-days);
}

// ---- O'sish (birinchi va oxirgi snapshot orasidagi farq) ----
function growth(acc, field) {
  const snaps = periodSnaps().filter(s => s.accounts && s.accounts[acc]);
  if (snaps.length < 2) return null;
  const first = snaps[0].accounts[acc][field];
  const last = snaps[snaps.length - 1].accounts[acc][field];
  if (first == null || last == null) return null;
  return last - first;
}

function latest(acc) {
  const snaps = periodSnaps().filter(s => s.accounts && s.accounts[acc]);
  if (!snaps.length) return null;
  return snaps[snaps.length - 1].accounts[acc];
}

function chgBadge(delta) {
  if (delta === null || delta === 0) return "";
  const up = delta > 0;
  const sign = up ? "↑" : "↓";
  return `<span class="chg ${up ? "up" : "down"}">${sign} ${fmt(Math.abs(delta))}</span>`;
}

// ============================================================
//  RENDER: OVERVIEW (umumiy sahifa)
// ============================================================
function renderOverview() {
  const el = document.getElementById("page-overview");

  // Umumiy yig'indi
  let totalFollowers = 0, totalReach = 0, totalSaved = 0;
  ORDER.forEach(a => {
    const d = latest(a);
    if (d) { totalFollowers += d.followers||0; totalReach += d.reach_7d||0; totalSaved += d.total_saved||0; }
  });

  let html = `
    <div class="section-title">${IC.chart} Umumiy ko'rsatkichlar</div>
    <div class="kpi-grid">
      <div class="kpi glass">
        <div class="label">${IC.users} Jami followerlar</div>
        <div class="val">${fmt(totalFollowers)}</div>
        <div class="hint">Uchchala restoran birgalikda</div>
      </div>
      <div class="kpi glass">
        <div class="label">${IC.eye} Jami qamrov (7 kun)</div>
        <div class="val">${fmt(totalReach)}</div>
        <div class="hint">Postlaringizni ko'rgan odamlar soni</div>
      </div>
      <div class="kpi glass">
        <div class="label">${IC.bookmark} Jami saqlashlar</div>
        <div class="val">${fmt(totalSaved)}</div>
        <div class="hint">"Keyin boraman" signali — restoran uchun muhim</div>
      </div>
    </div>

    <div class="section-title">${IC.users} Akkauntlar holati</div>
    <div class="acc-grid">`;

  ORDER.forEach(a => {
    const m = META[a], d = latest(a);
    if (!d) {
      html += `<div class="acc-card glass"><div class="acc-head"><div class="acc-avatar" style="background:${m.color}">${m.letter}</div><div><h3>${m.name}</h3><div class="handle">${m.handle}</div></div></div><div class="empty">Ma'lumot yo'q</div></div>`;
      return;
    }
    const fg = growth(a, "followers");
    html += `
      <div class="acc-card glass">
        <div class="acc-head">
          <div class="acc-avatar" style="background:${m.color}">${m.letter}</div>
          <div><h3>${m.name}</h3><div class="handle">${m.handle}</div></div>
        </div>
        <div class="acc-row"><span class="rl">${IC.users} Followerlar</span><span class="rv">${fmt(d.followers)}${fg!==null&&fg!==0?`<small>${fg>0?"+":""}${fmt(fg)}</small>`:""}</span></div>
        <div class="acc-row"><span class="rl">${IC.bolt} Faollik darajasi</span><span class="rv">${d.engagement_rate||0}%</span></div>
        <div class="acc-row"><span class="rl">${IC.eye} Qamrov (7 kun)</span><span class="rv">${fmt(d.reach_7d)}</span></div>
        <div class="acc-row"><span class="rl">${IC.bookmark} Saqlashlar</span><span class="rv">${fmt(d.total_saved)}</span></div>
      </div>`;
  });
  html += `</div>`;

  // Grafiklar
  html += `
    <div class="section-title">${IC.chart} O'sish dinamikasi</div>
    <div class="chart-card glass">
      <h3>Followerlar o'zgarishi</h3>
      <div class="csub">Har restoran alohida chiziq — tanlangan davr bo'yicha</div>
      <div class="chart-box"><canvas id="chartFollowers"></canvas></div>
    </div>
    <div class="two-col">
      <div class="chart-card glass">
        <h3>Qamrov (reach)</h3>
        <div class="csub">7 kunlik qamrov dinamikasi</div>
        <div class="chart-box"><canvas id="chartReach"></canvas></div>
      </div>
      <div class="chart-card glass">
        <h3>Faollik darajasi</h3>
        <div class="csub">Engagement rate, % — bugungi holat</div>
        <div class="chart-box"><canvas id="chartER"></canvas></div>
      </div>
    </div>`;

  el.innerHTML = html;

  drawLineChart("chartFollowers", "followers");
  drawLineChart("chartReach", "reach_7d");
  drawERBar("chartER");
}

// ============================================================
//  RENDER: bitta restoran sahifasi
// ============================================================
function renderAccount(acc) {
  const el = document.getElementById("page-" + acc);
  const m = META[acc], d = latest(acc);

  if (!d) { el.innerHTML = `<div class="glass empty">Bu akkaunt uchun ma'lumot hali yo'q.</div>`; return; }

  const fg = growth(acc, "followers");
  const rg = growth(acc, "reach_7d");

  let html = `
    <div class="section-title" style="color:#fff">
      <span class="acc-avatar" style="width:34px;height:34px;border-radius:11px;font-size:16px;background:${m.color}">${m.letter}</span>
      ${m.name} — batafsil tahlil
    </div>

    <div class="kpi-grid">
      <div class="kpi glass">
        <div class="label">${IC.users} Followerlar</div>
        <div class="val">${fmt(d.followers)} ${chgBadge(fg)}</div>
        <div class="hint">Tanlangan davrdagi o'zgarish</div>
      </div>
      <div class="kpi glass">
        <div class="label">${IC.bolt} Faollik darajasi (ER)</div>
        <div class="val">${d.engagement_rate||0}%</div>
        <div class="hint">${erVerdict(d.engagement_rate)}</div>
      </div>
      <div class="kpi glass">
        <div class="label">${IC.eye} Qamrov (7 kun)</div>
        <div class="val">${fmt(d.reach_7d)} ${chgBadge(rg)}</div>
        <div class="hint">Postlarni ko'rgan odamlar</div>
      </div>
      <div class="kpi glass">
        <div class="label">${IC.pin} Profil ko'rishlari</div>
        <div class="val">${fmt(d.profile_views_7d)}</div>
        <div class="hint">Profilingizga kirgan odamlar (7 kun)</div>
      </div>
      <div class="kpi glass">
        <div class="label">${IC.bookmark} Saqlashlar</div>
        <div class="val">${fmt(d.total_saved)}</div>
        <div class="hint">Postlarni saqlab qo'yganlar — yuqori niyat</div>
      </div>
      <div class="kpi glass">
        <div class="label">${IC.share} Ulashishlar</div>
        <div class="val">${fmt(d.total_shares)}</div>
        <div class="hint">Postlarni do'stlariga yuborganlar</div>
      </div>
      <div class="kpi glass">
        <div class="label">${IC.eye} Qamrov/follower nisbati</div>
        <div class="val">${d.reach_rate||0}%</div>
        <div class="hint">Postlaringiz followerlardan tashqariga yetyaptimi</div>
      </div>
      <div class="kpi glass">
        <div class="label">${IC.heart} O'rtacha engagement</div>
        <div class="val">${fmt(d.avg_engagement)}</div>
        <div class="hint">Har post uchun layk+izoh+saqlash+ulashish</div>
      </div>
    </div>

    <div class="two-col">
      <div class="chart-card glass">
        <h3>Followerlar o'sishi</h3>
        <div class="csub">Tanlangan davr bo'yicha</div>
        <div class="chart-box"><canvas id="acc-foll-${acc}"></canvas></div>
      </div>
      <div class="chart-card glass">
        <h3>Kontent turi bo'yicha</h3>
        <div class="csub">Qaysi tur post ko'proq ishlaydi (o'rtacha engagement)</div>
        <div class="chart-box"><canvas id="acc-type-${acc}"></canvas></div>
      </div>
    </div>

    <div class="section-title" style="color:#fff">${IC.fire} Eng yaxshi postlar</div>
    <div class="posts-card glass">`;

  const posts = d.posts || [];
  if (!posts.length) {
    html += `<div class="empty">Postlar topilmadi</div>`;
  } else {
    posts.slice(0, 8).forEach((p, i) => {
      const date = p.timestamp ? new Date(p.timestamp).toLocaleDateString("ru-RU") : "";
      html += `
        <div class="post-item">
          <div class="post-rank">${i+1}</div>
          <div class="post-body">
            <div class="post-cap">${p.permalink ? `<a href="${p.permalink}" target="_blank" style="color:inherit;text-decoration:none">${escapeHtml(p.caption)}</a>` : escapeHtml(p.caption)}</div>
            <div class="post-meta">
              <span class="badge">${fmtType(p.type)}</span>
              <span>❤️ ${fmt(p.likes)}</span>
              <span>💬 ${fmt(p.comments)}</span>
              <span>🔖 ${fmt(p.saved)}</span>
              <span>👁 ${fmt(p.reach)}</span>
              ${date?`<span>${date}</span>`:""}
            </div>
          </div>
          <div class="post-eng"><b>${fmt(p.engagement)}</b><small>engagement</small></div>
        </div>`;
    });
  }
  html += `</div>`;

  el.innerHTML = html;
  drawLineChart("acc-foll-" + acc, "followers", [acc]);
  drawTypeBar("acc-type-" + acc, d.by_type);
}

function erVerdict(er) {
  if (!er) return "Ma'lumot to'planmoqda";
  if (er >= 6) return "A'lo — juda yuqori faollik";
  if (er >= 3) return "Yaxshi — sog'lom faollik";
  if (er >= 1) return "O'rtacha — yaxshilash mumkin";
  return "Past — kontentni qayta ko'rib chiqing";
}

function escapeHtml(s) {
  return (s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

// ============================================================
//  GRAFIKLAR (Chart.js)
// ============================================================
function destroyChart(id) { if (CHARTS[id]) { CHARTS[id].destroy(); delete CHARTS[id]; } }

function commonOpts() {
  return {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { labels: { color:"#3a2456", font:{size:13, weight:"600"}, usePointStyle:true, pointStyle:"circle" } } },
    scales: {
      x: { ticks:{color:"#6b5b8a", font:{size:11}}, grid:{color:"rgba(120,80,160,0.08)"} },
      y: { ticks:{color:"#6b5b8a", font:{size:11}}, grid:{color:"rgba(120,80,160,0.1)"} }
    }
  };
}

function drawLineChart(canvasId, field, only) {
  const cv = document.getElementById(canvasId);
  if (!cv) return;
  destroyChart(canvasId);
  const snaps = periodSnaps();
  const labels = snaps.map(s => {
    const d = new Date(s.date); return d.toLocaleDateString("ru-RU",{day:"2-digit",month:"2-digit"});
  });
  const accs = only || ORDER;
  const datasets = accs.map(a => {
    const m = META[a];
    return {
      label: m.name, borderColor: m.color, backgroundColor: m.color + "22",
      data: snaps.map(s => s.accounts && s.accounts[a] ? s.accounts[a][field] : null),
      tension: 0.35, borderWidth: 3, pointRadius: 3, pointBackgroundColor: m.color, fill: only ? true : false, spanGaps: true,
    };
  });
  CHARTS[canvasId] = new Chart(cv, { type:"line", data:{labels, datasets}, options: commonOpts() });
}

function drawERBar(canvasId) {
  const cv = document.getElementById(canvasId);
  if (!cv) return;
  destroyChart(canvasId);
  const labels = ORDER.map(a => META[a].name);
  const data = ORDER.map(a => { const d = latest(a); return d ? d.engagement_rate : 0; });
  const colors = ORDER.map(a => META[a].color);
  const opts = commonOpts(); opts.plugins.legend.display = false;
  CHARTS[canvasId] = new Chart(cv, {
    type:"bar",
    data:{ labels, datasets:[{ data, backgroundColor: colors, borderRadius:10, barThickness:48 }] },
    options: opts
  });
}

function drawTypeBar(canvasId, byType) {
  const cv = document.getElementById(canvasId);
  if (!cv) return;
  destroyChart(canvasId);
  byType = byType || {};
  const types = Object.keys(byType);
  if (!types.length) { return; }
  const labels = types.map(fmtType);
  const data = types.map(t => byType[t].avg_engagement || 0);
  const opts = commonOpts(); opts.plugins.legend.display = false;
  opts.indexAxis = "y";
  CHARTS[canvasId] = new Chart(cv, {
    type:"bar",
    data:{ labels, datasets:[{ data, backgroundColor:"#8a5cf6", borderRadius:8, barThickness:30 }] },
    options: opts
  });
}

// ============================================================
//  Boshqaruv: sahifa va davr almashinuvi
// ============================================================
function rerender() {
  if (PAGE === "overview") renderOverview();
  else renderAccount(PAGE);
}

function setupControls() {
  document.querySelectorAll(".tab").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      PAGE = btn.dataset.page;
      document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
      document.getElementById("page-" + PAGE).classList.add("active");
      rerender();
    });
  });
  document.querySelectorAll(".per").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".per").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      PERIOD = btn.dataset.period;
      rerender();
    });
  });
}

// ============================================================
//  Ma'lumotni yuklash
// ============================================================
async function loadData() {
  try {
    const res = await fetch("instagram_data.json?v=" + Date.now());
    if (!res.ok) throw new Error("yo'q");
    const data = await res.json();
    if (Array.isArray(data) && data.length) {
      HISTORY = data;
      document.getElementById("demoBanner").style.display = "none";
      const last = HISTORY[HISTORY.length - 1];
      document.getElementById("lastUpdate").textContent = last.date || "—";
      return;
    }
    throw new Error("bo'sh");
  } catch (e) {
    HISTORY = buildDemo();
    document.getElementById("demoBanner").style.display = "flex";
    document.getElementById("lastUpdate").textContent = HISTORY[HISTORY.length-1].date + " (namuna)";
  }
}

// ---- Namuna ma'lumot (haqiqiy fayl bo'lmasa) ----
function buildDemo() {
  const days = 30;
  const base = { benison_uz:{f:41200,r:13000,pv:1800,er:3.1,sv:240,sh:60}, dieto_uz:{f:360,r:230,pv:90,er:5.2,sv:18,sh:5}, eddo_uz:{f:38100,r:19000,pv:2400,er:2.4,sv:310,sh:80} };
  const hist = [];
  for (let i = days-1; i >= 0; i--) {
    const d = new Date(); d.setDate(d.getDate() - i);
    const snap = { date: d.toISOString().slice(0,10), accounts:{} };
    ORDER.forEach(a => {
      const b = base[a]; const k = (days-i);
      snap.accounts[a] = {
        username: a, followers: b.f + k*Math.round(b.f*0.0006) + Math.round(Math.random()*8),
        reach_7d: b.r + Math.round((Math.random()-0.3)*b.r*0.15),
        profile_views_7d: b.pv + Math.round((Math.random()-0.3)*b.pv*0.2),
        engagement_rate: +(b.er + (Math.random()-0.5)*0.4).toFixed(2),
        avg_engagement: Math.round(b.f*b.er/100/5),
        reach_rate: +(b.r/b.f*100).toFixed(1),
        avg_reach: Math.round(b.r/8),
        total_saved: b.sv + Math.round((Math.random()-0.3)*30),
        total_shares: b.sh + Math.round((Math.random()-0.3)*15),
        by_type: { IMAGE:{count:12,avg_engagement:Math.round(b.f*b.er/100/6)}, VIDEO:{count:8,avg_engagement:Math.round(b.f*b.er/100/4)}, CAROUSEL_ALBUM:{count:5,avg_engagement:Math.round(b.f*b.er/100/5)} },
        posts: demoPosts(a, b),
      };
    });
    hist.push(snap);
  }
  return hist;
}
function demoPosts(a, b) {
  const types = ["IMAGE","VIDEO","CAROUSEL_ALBUM"];
  const caps = ["Yangi taom — bugun mazza qiling!","Bizning mijozlar fikri ❤️","Maxsus aksiya — faqat shu hafta","Ortga nazar: oshxonamiz","Mehmonlarimiz lahzalar","Yangi menyu taqdimoti","Bayram chegirmalari","Eng sevimli taomingiz qaysi?"];
  return caps.map((c,i)=>{
    const reach = Math.round(b.r/8*(1+Math.random()));
    const eng = Math.round(b.f*b.er/100/5*(1+Math.random()*0.8));
    return { caption:c, type:types[i%3], permalink:"#", timestamp:new Date(Date.now()-i*86400000*3).toISOString(),
      likes:Math.round(eng*0.8), comments:Math.round(eng*0.05), saved:Math.round(eng*0.1), shares:Math.round(eng*0.05),
      reach, engagement:eng, post_er:+(eng/reach*100).toFixed(1) };
  }).sort((x,y)=>y.engagement-x.engagement);
}

// ---- Boshlash ----
(async function init(){
  await loadData();
  setupControls();
  rerender();
})();

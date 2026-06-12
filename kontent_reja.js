// ============================================================
//  Kontent Reja Generatori — tahlil + reja + caption'lar
// ============================================================

const ACCOUNTS = {
  benison_uz: { name:"Benison", color:"#ff7a59",
    defSpecialty:"milliy va zamonaviy taomlar",
    defDishes:"osh, shashlik, lag'mon, somsa" },
  dieto_uz: { name:"Dieto", color:"#8a5cf6",
    defSpecialty:"sog'lom va parhez taomlar",
    defDishes:"salatlar, smuzi, grill taomlar, parhez shirinliklar" },
  eddo_uz: { name:"Eddo", color:"#f9b234",
    defSpecialty:"pitsa va fastfud",
    defDishes:"pitsa, burger, lavash, kartoshka fri" },
};
const ORDER = ["benison_uz","dieto_uz","eddo_uz"];
const DAYS = ["Yakshanba","Dushanba","Seshanba","Chorshanba","Payshanba","Juma","Shanba"];
const DAYS_SHORT = ["Yak","Dush","Sesh","Chor","Pay","Jum","Shan"];

let HISTORY = [];
let ACC = "benison_uz";
let SETTINGS = loadSettings();
let CURRENT_PLAN = {};   // acc -> plan array (shablon rejimi)
let AI_PLAN = null;      // AI tuzgan reja (kontent_reja_ai.json)
let MODE = "template";   // "ai" | "template"

// ============================================================
//  CAPTION SHABLONLARI (o'zbekcha)
//  {taom} - taom nomi, {restoran} - restoran nomi
// ============================================================
const THEMES = [
  {
    id:"dish", label:"Taom tanishtiruvi", types:["IMAGE","CAROUSEL_ALBUM"],
    templates: [
      "Bugungi yulduzimiz — {taom}! 😍\n\nHar bir luqmasida mehr va sinalgan retsept. Hali tatib ko'rmaganlar — sizni kutamiz!\n\n📍 Manzil — profil bio'da",
      "{taom} sevuvchilar, bu post siz uchun! 🤤\n\nBizning oshpazlar uni alohida e'tibor bilan tayyorlaydi. Kelganingizda albatta buyurtma qiling.\n\n👇 Siz uni qanday yoqtirasiz? Izohda yozing!",
      "Sizningcha, eng mazali {taom} qayerda? 😉\n\nBiz javobni bilamiz — {restoran}da! Kelib, o'zingiz baholang.\n\n📲 Bron uchun: profil bio'dagi raqam",
      "Rasmga qarang va ayting: hozir {taom} yegingiz keldimi? 😋\n\nAgar 'ha' bo'lsa — biz sizni kutyapmiz!\n\n❤️ Layk bosing, do'stingizni belgilang",
    ]
  },
  {
    id:"reel", label:"Video / Reels", types:["VIDEO"],
    templates: [
      "{taom} qanday tayyorlanadi? 👨‍🍳 Sirlarni ochamiz!\n\nVideoni oxirigacha ko'ring — eng qizig'i oxirida 😉\n\n💬 Qaysi taomning tayyorlanishini ko'rmoqchisiz? Izohda yozing!",
      "Ovozni yoqing! 🔊 {taom}ning jizillashi... bu musiqa!\n\nKelib, jonli his qiling.\n\n📍 {restoran} — manzil bio'da",
      "POV: {restoran}ga birinchi marta keldingiz 🎬\n\nVideoda — sizni nima kutayotgani. Do'stingizni belgilang, birga keling!\n\n❤️ + 🔖 = rahmat!",
      "24 soat ichida eng ko'p buyurtma qilingan taom — {taom} 🏆\n\nNega ekanini videodan bilib oling!\n\n💬 Siz sinab ko'rdingizmi?",
    ]
  },
  {
    id:"question", label:"Savol-javob", types:["IMAGE","CAROUSEL_ALBUM","VIDEO"],
    templates: [
      "Tezkor savol! ⚡️\n\n{taom}ni qaysi vaqtda yeyish yoqadi — tushlikdami yoki kechki ovqatda?\n\n👇 Izohda yozing — eng faol 3 kishiga keyingi tashrifda kichik sovg'a! 🎁",
      "Bahslashamiz: {taom} achchiq bo'lishi kerakmi yoki yo'q? 🌶\n\n'Achchiq' tarafdorlari — ❤️\n'Achchiqsiz' tarafdorlari — 👍\n\nNatijani stories'da e'lon qilamiz!",
      "Agar umringizning oxirigacha faqat bitta taom yesangiz — {taom}ni tanlarmidingiz? 😄\n\nYo'q desangiz, qaysi taomni tanlaysiz? Izohda kutamiz! 👇",
      "Sizning fikringiz biz uchun muhim! 🙏\n\nMenyumizga qanday yangi taom qo'shishimizni xohlaysiz? Eng yaxshi takliflarni amalga oshiramiz!\n\n💬 Yozing!",
    ]
  },
  {
    id:"promo", label:"Aksiya / Taklif", types:["IMAGE","CAROUSEL_ALBUM"],
    templates: [
      "🔥 FAQAT SHU HAFTA!\n\n{taom}ga maxsus taklif. Do'stingiz bilan keling — ikkingizga ham yoqimli kutilmagan sovg'a! 🎁\n\n⏰ Shoshiling — taklif cheklangan!\n📍 Manzil bio'da",
      "Hafta o'rtasi charchog'iga eng yaxshi dori — {taom} 😌\n\nBugun kelganlar uchun maxsus kutib olish!\n\n📲 Stol bron qilish: bio'dagi raqam",
      "Do'stingizni belgilang — u sizni {taom}ga olib borishi kerak! 😄\n\nQoidasi shunday: kim belgilansa — o'sha to'laydi 😉\n\n📍 {restoran}",
      "Bayramni kutmasdan o'zingizni siylang! ✨\n\n{taom} + yaqin insoningiz + {restoran} = mukammal oqshom.\n\n🔖 Saqlab qo'ying — keyin kerak bo'ladi!",
    ]
  },
  {
    id:"behind", label:"Oshxona ortida", types:["VIDEO","CAROUSEL_ALBUM"],
    templates: [
      "Oshxonamiz ortida nima bo'lyapti? 👀\n\nHar kuni ertalab mahsulotlar yangi keladi, jamoamiz esa siz uchun mehr bilan tayyorlaydi.\n\nShaffoflik — bizning qoidamiz! 💪",
      "Bizning jamoa — bizning faxrimiz! ❤️\n\n{taom}ni shunchaki taom emas, san'at asari qilib taqdim etadiganlar — mana shular.\n\n👏 Ularni qo'llab-quvvatlang — izohda rahmat yozing!",
      "Sifat qayerdan boshlanadi? Mahsulotdan! 🥬\n\nBiz faqat yangi va sinalgan mahsulotlar bilan ishlaymiz. Farqini ta'mida sezasiz.\n\n📍 {restoran} — manzil bio'da",
      "Bir kunimiz qanday o'tadi? ⏰\n\nErtalab tayyorgarlik, kunduzi mehmonlar, kechqurun esa... eng gavjum payt! Videoda hammasini ko'ring 🎬",
    ]
  },
  {
    id:"review", label:"Mijoz fikri", types:["IMAGE","CAROUSEL_ALBUM"],
    templates: [
      "Mijozlarimiz fikri — biz uchun eng katta mukofot! ❤️\n\n'{restoran}da har safar o'zimni kutilgan mehmondek his qilaman' — doimiy mehmonimiz.\n\n💬 Siz ham tajribangizni izohda yozing!",
      "Bizga eng ko'p beriladigan savol: 'Nega aynan siz?' 🤔\n\nJavob oddiy: ta'm + muhit + samimiy xizmat.\n\nIshonmaysizmi? Kelib tekshiring! 😉",
      "5 yulduzli sharhlar — bizning motivatsiyamiz! ⭐️⭐️⭐️⭐️⭐️\n\nHar bir fikr biz uchun qadrli. Tashrifingizdan keyin baho qoldirishni unutmang!\n\n🙏 Rahmat, azizlar!",
      "Birinchi marta kelganlar ko'pincha shunday deydi: 'Nega oldinroq kelmadik?!' 😅\n\nSiz ham hali kelmagan bo'lsangiz — bugun ayni vaqti!\n\n📍 Manzil bio'da",
    ]
  },
];

// Har bir kontent turiga mos mavzular
function themesForType(type) {
  return THEMES.filter(t => t.types.includes(type));
}

// ============================================================
//  SOZLAMALAR (localStorage)
// ============================================================
function loadSettings() {
  try {
    const raw = localStorage.getItem("kr_settings");
    if (raw) return JSON.parse(raw);
  } catch(e) {}
  const s = { postsPerWeek: 4, accounts: {} };
  ORDER.forEach(a => {
    s.accounts[a] = { specialty: ACCOUNTS[a].defSpecialty, dishes: ACCOUNTS[a].defDishes };
  });
  return s;
}
function saveSettings() {
  try { localStorage.setItem("kr_settings", JSON.stringify(SETTINGS)); } catch(e) {}
}

// ============================================================
//  TAHLIL — haqiqiy ma'lumotdan
// ============================================================
function latest(acc) {
  for (let i = HISTORY.length - 1; i >= 0; i--) {
    if (HISTORY[i].accounts && HISTORY[i].accounts[acc]) return HISTORY[i].accounts[acc];
  }
  return null;
}

function analyze(acc) {
  const d = latest(acc);
  const result = {
    bestType: null, bestTypeLabel: "—", typeRank: [],
    bestDays: [4,5,2,6],          // standart: Pay, Jum, Sesh, Shan
    bestHour: 18, hourLabel: "18:00 atrofida",
    dataPoints: 0, hasData: false,
  };
  if (!d) return result;

  // Kontent turi reytingi
  const bt = d.by_type || {};
  const rank = Object.entries(bt)
    .map(([t,v]) => ({ type:t, avg:v.avg_engagement||0, count:v.count||0 }))
    .sort((a,b) => b.avg - a.avg);
  if (rank.length) {
    result.typeRank = rank;
    result.bestType = rank[0].type;
    result.bestTypeLabel = fmtType(rank[0].type);
  }

  // Postlar vaqtidan kun + soat tahlili (engagement og'irligi bilan)
  const posts = (d.posts || []).filter(p => p.timestamp);
  result.dataPoints = posts.length;
  if (posts.length >= 4) {
    const dayScore = {}, hourScore = {};
    posts.forEach(p => {
      const dt = new Date(p.timestamp);
      const day = dt.getDay(), hour = dt.getHours();
      dayScore[day] = (dayScore[day]||0) + (p.engagement||1);
      const bucket = hour < 11 ? 9 : hour < 15 ? 12 : hour < 18 ? 16 : 19;
      hourScore[bucket] = (hourScore[bucket]||0) + (p.engagement||1);
    });
    const days = Object.entries(dayScore).sort((a,b)=>b[1]-a[1]).map(e=>+e[0]);
    if (days.length >= 3) result.bestDays = days;
    const hours = Object.entries(hourScore).sort((a,b)=>b[1]-a[1]).map(e=>+e[0]);
    if (hours.length) {
      result.bestHour = hours[0];
      const names = {9:"ertalab (9:00–11:00)", 12:"tushlik payti (12:00–14:00)", 16:"kunduzi (16:00–17:00)", 19:"kechqurun (18:00–20:00)"};
      result.hourLabel = names[hours[0]] || hours[0]+":00";
    }
    result.hasData = true;
  }
  return result;
}

function fmtType(t) {
  return { IMAGE:"Rasm", VIDEO:"Video/Reels", CAROUSEL_ALBUM:"Karusel", REELS:"Reels" }[t] || t || "Aralash";
}

// ============================================================
//  REJA TUZISH
// ============================================================
function pickRandom(arr) { return arr[Math.floor(Math.random()*arr.length)]; }

function buildPlan(acc) {
  const an = analyze(acc);
  const n = SETTINGS.postsPerWeek || 4;
  const accSet = SETTINGS.accounts[acc] || {};
  const dishes = (accSet.dishes || ACCOUNTS[acc].defDishes).split(",").map(s=>s.trim()).filter(Boolean);
  const restName = ACCOUNTS[acc].name;

  // Kunlarni tanlash: eng yaxshi kunlardan, hafta bo'ylab taqsimlangan
  let days = [...new Set(an.bestDays)].slice(0, n);
  while (days.length < n) {
    const cand = [4,5,2,6,3,1,0].find(d => !days.includes(d));
    if (cand === undefined) break;
    days.push(cand);
  }
  days.sort((a,b) => (a===0?7:a) - (b===0?7:b)); // Dush...Yak tartibida

  // Kontent turlari: eng yaxshisiga ustunlik, lekin xilma-xil
  const typePool = [];
  if (an.typeRank.length >= 2) {
    typePool.push(an.typeRank[0].type, an.typeRank[0].type, an.typeRank[1].type);
    if (an.typeRank[2]) typePool.push(an.typeRank[2].type);
    else typePool.push(an.typeRank[1].type);
  } else {
    typePool.push("VIDEO","IMAGE","CAROUSEL_ALBUM","VIDEO");
  }

  // Soatlar: asosiy eng yaxshi vaqt + bir oz tafovut
  const hourOptions = {9:["9:30","10:00","10:30"],12:["12:00","12:30","13:00"],16:["16:00","16:30","17:00"],19:["18:00","18:30","19:00"]};
  const mainHours = hourOptions[an.bestHour] || hourOptions[19];

  const usedThemes = [];
  const plan = days.map((day, i) => {
    const type = typePool[i % typePool.length];
    // Mavzu: shu turga mos, hali ishlatilmaganidan
    let pool = themesForType(type).filter(t => !usedThemes.includes(t.id));
    if (!pool.length) pool = themesForType(type);
    const theme = pickRandom(pool);
    usedThemes.push(theme.id);

    const dish = dishes.length ? pickRandom(dishes) : "taomlarimiz";
    const caption = pickRandom(theme.templates)
      .replaceAll("{taom}", dish)
      .replaceAll("{restoran}", restName)
      + "\n\n" + hashtags(acc);

    return { day, time: pickRandom(mainHours), type, themeId: theme.id, themeLabel: theme.label, caption };
  });
  return plan;
}

function hashtags(acc) {
  const base = { benison_uz:"#benison", dieto_uz:"#dieto", eddo_uz:"#eddo" }[acc] || "";
  return `${base} #toshkent #restoran #tashkentfood #fooduz`;
}

// Bitta kunni almashtirish
function reshuffleDay(acc, idx) {
  const plan = CURRENT_PLAN[acc];
  if (!plan || !plan[idx]) return;
  const slot = plan[idx];
  const accSet = SETTINGS.accounts[acc] || {};
  const dishes = (accSet.dishes || ACCOUNTS[acc].defDishes).split(",").map(s=>s.trim()).filter(Boolean);

  let pool = themesForType(slot.type).filter(t => t.id !== slot.themeId);
  if (!pool.length) pool = themesForType(slot.type);
  const theme = pickRandom(pool);
  const dish = dishes.length ? pickRandom(dishes) : "taomlarimiz";

  slot.themeId = theme.id;
  slot.themeLabel = theme.label;
  slot.caption = pickRandom(theme.templates)
    .replaceAll("{taom}", dish)
    .replaceAll("{restoran}", ACCOUNTS[acc].name)
    + "\n\n" + hashtags(acc);
  renderPlan();
}

// ============================================================
//  RENDER
// ============================================================
function renderInsights() {
  const an = analyze(ACC);
  const el = document.getElementById("insights");
  const d = latest(ACC);
  const er = d ? (d.engagement_rate || 0) : 0;

  let typeDetail = "Ma'lumot to'planmoqda";
  if (an.typeRank.length) {
    typeDetail = an.typeRank.map(r => `${fmtType(r.type)}: ${r.avg}`).join(" · ");
  }

  el.innerHTML = `
    <div class="insight glass">
      <div class="lab">🏆 Eng yaxshi kontent turi</div>
      <div class="val">${an.bestTypeLabel}</div>
      <div class="sub">O'rtacha engagement: ${typeDetail}</div>
    </div>
    <div class="insight glass">
      <div class="lab">⏰ Eng yaxshi vaqt</div>
      <div class="val">${an.hourLabel}</div>
      <div class="sub">${an.hasData ? `${an.dataPoints} ta postingiz tahlilidan` : "Standart tavsiya — ma'lumot yig'ilgani sayin aniqlashadi"}</div>
    </div>
    <div class="insight glass">
      <div class="lab">📅 Eng faol kunlar</div>
      <div class="val">${an.bestDays.slice(0,3).map(d=>DAYS_SHORT[d]).join(" · ")}</div>
      <div class="sub">${an.hasData ? "Engagement bo'yicha eng kuchli kunlaringiz" : "Restoranlar uchun odatiy eng yaxshi kunlar"}</div>
    </div>
    <div class="insight glass">
      <div class="lab">⚡️ Faollik darajasi</div>
      <div class="val">${er}%</div>
      <div class="sub">${er >= 3 ? "Yaxshi! Reja shu sur'atni ushlab turishga yordam beradi" : "Reja muntazamligi buni oshirishga yordam beradi"}</div>
    </div>`;
}

function renderPlan() {
  if (MODE === "ai" && AI_PLAN) { renderAIPlan(); return; }
  const plan = CURRENT_PLAN[ACC] || [];
  const el = document.getElementById("plan");
  const color = ACCOUNTS[ACC].color;
  document.getElementById("planMeta").textContent = `— ${ACCOUNTS[ACC].name}, ${plan.length} ta post (shablon)`;

  if (!plan.length) { el.innerHTML = `<div class="glass empty">Reja tuzilmadi — "Yangi reja tuzish" ni bosing</div>`; return; }

  el.innerHTML = plan.map((s, i) => `
    <div class="day-card glass">
      <div class="day-head">
        <div class="day-num" style="background:${color}"><b>${DAYS_SHORT[s.day]}</b><small>${i+1}-post</small></div>
        <div>
          <h4>${DAYS[s.day]}</h4>
          <div class="tm">⏰ ${s.time}</div>
        </div>
      </div>
      <div class="badges">
        <span class="badge b-type">${fmtType(s.type)}</span>
        <span class="badge b-theme">${s.themeLabel}</span>
      </div>
      <div class="cap">${escapeHtml(s.caption)}</div>
      <div class="day-actions">
        <button class="btn btn-ghost btn-sm" onclick="copyCaption(${i}, this)">📋 Nusxa olish</button>
        <button class="btn btn-ghost btn-sm" onclick="reshuffleDay('${ACC}', ${i})">🔄 Almashtirish</button>
        <button class="btn btn-ghost btn-sm" onclick="rpChatOchish(this)">🎬 Chuqurlashtirish</button>
      </div>
    </div>`).join("");
}

// ---- AI rejasini ko'rsatish ----
function renderAIPlan() {
  const el = document.getElementById("plan");
  const accData = AI_PLAN.accounts ? AI_PLAN.accounts[ACC] : null;
  const color = ACCOUNTS[ACC].color;
  const plan = accData && Array.isArray(accData.plan) ? accData.plan : [];
  document.getElementById("planMeta").textContent = `— ${ACCOUNTS[ACC].name} · 🤖 AI tuzgan (${AI_PLAN.generated_at || ""})`;

  if (!plan.length) {
    el.innerHTML = `<div class="glass empty">Bu restoran uchun AI reja hali yo'q. "Shablon reja" tugmasini bosing yoki Actions'da "AI kontent reja"ni ishga tushiring.</div>`;
    return;
  }

  let html = "";
  if (accData.insight) {
    html += `<div class="glass" style="grid-column:1/-1; padding:16px 20px; font-size:14px; line-height:1.55;">
      <b>🤖 AI xulosasi:</b> ${escapeHtml(accData.insight)}
    </div>`;
  }
  if (accData.review) {
    html += `<div class="glass" style="grid-column:1/-1; padding:14px 20px; font-size:13.5px; line-height:1.55; background:rgba(31,157,87,0.12);">
      <b>📈 O'tgan hafta bahosi:</b> ${escapeHtml(accData.review)}
    </div>`;
  }

  const OYLAR = ["yanvar","fevral","mart","aprel","may","iyun","iyul","avgust","sentabr","oktabr","noyabr","dekabr"];
  const todayIso = new Date().toISOString().slice(0,10);
  function fmtSana(iso) {
    const d = new Date(iso + "T00:00:00");
    return d.getDate() + "-" + OYLAR[d.getMonth()];
  }

  html += plan.map((s, i) => {
    const dayIdx = DAYS.indexOf(s.day);
    const shortDay = dayIdx >= 0 ? DAYS_SHORT[dayIdx] : (s.day || "").slice(0,4);
    const bugun = s.sana === todayIso;
    const sanaTxt = s.sana
      ? `<div class="tm">📆 ${fmtSana(s.sana)}${bugun ? ' · <b style="color:#d62976">BUGUN</b>' : ''}</div>`
      : "";
    return `
    <div class="day-card glass" ${bugun ? 'style="outline:2px solid #d62976;"' : ''}>
      <div class="day-head">
        <div class="day-num" style="background:${color}"><b>${shortDay}</b><small>${i+1}-post</small></div>
        <div>
          <h4>${escapeHtml(s.day || "")}</h4>
          <div class="tm">⏰ ${escapeHtml(s.time || "")}</div>
          ${sanaTxt}
        </div>
      </div>
      <div class="badges">
        <span class="badge b-type">${fmtType(s.type)}</span>
        <span class="badge b-theme">${escapeHtml(s.theme || "")}</span>
      </div>
      ${s.why ? `<div style="font-size:12px;color:var(--muted);line-height:1.45;">💡 ${escapeHtml(s.why)}</div>` : ""}
      <div class="cap">${escapeHtml(s.caption || "")}</div>
      <div class="day-actions">
        <button class="btn btn-ghost btn-sm" onclick="copyCaption(${i}, this)">📋 Nusxa olish</button>
        <button class="btn btn-ghost btn-sm" onclick="rpChatOchish(this)">🎬 Chuqurlashtirish</button>
      </div>
    </div>`;
  }).join("");

  el.innerHTML = html;
}

function escapeHtml(s) {
  return (s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

function copyCaption(idx, btn) {
  let text = null;
  if (MODE === "ai" && AI_PLAN) {
    const accData = AI_PLAN.accounts ? AI_PLAN.accounts[ACC] : null;
    if (accData && accData.plan && accData.plan[idx]) text = accData.plan[idx].caption;
  } else {
    const plan = CURRENT_PLAN[ACC];
    if (plan && plan[idx]) text = plan[idx].caption;
  }
  if (!text) return;
  navigator.clipboard.writeText(text).then(() => {
    btn.classList.add("copied");
    btn.textContent = "✓ Nusxalandi";
    showToast("Caption nusxalandi — Instagram'ga qo'ying!");
    setTimeout(() => { btn.classList.remove("copied"); btn.innerHTML = "📋 Nusxa olish"; }, 1800);
  }).catch(() => showToast("Nusxalashda xato — matnni qo'lda belgilang"));
}

let toastTimer;
function showToast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove("show"), 2200);
}

function renderSettings() {
  const grid = document.getElementById("setGrid");
  grid.innerHTML = ORDER.map(a => {
    const s = SETTINGS.accounts[a];
    return `
      <div class="set-acc">
        <h4><span class="sdot" style="background:${ACCOUNTS[a].color}"></span>${ACCOUNTS[a].name}</h4>
        <div class="set-row">
          <label>Yo'nalishi (nimasi bilan mashhur)</label>
          <input id="sp-${a}" value="${escapeHtml(s.specialty)}">
        </div>
        <div class="set-row">
          <label>Mashhur taomlar (vergul bilan)</label>
          <input id="ds-${a}" value="${escapeHtml(s.dishes)}">
        </div>
      </div>`;
  }).join("");
  document.getElementById("setCount").value = String(SETTINGS.postsPerWeek || 4);
}

// ============================================================
//  BOSHQARUV
// ============================================================
function setupControls() {
  document.querySelectorAll(".tab").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      ACC = btn.dataset.acc;
      if (!CURRENT_PLAN[ACC]) CURRENT_PLAN[ACC] = buildPlan(ACC);
      renderInsights();
      renderPlan();
    });
  });

  document.getElementById("genBtn").addEventListener("click", () => {
    if (MODE === "ai") {
      // AI'dan shablon rejimga o'tish
      MODE = "template";
      CURRENT_PLAN[ACC] = buildPlan(ACC);
      updateGenBtn();
      renderPlan();
      showToast("Shablon reja tuzildi ✨");
    } else if (AI_PLAN) {
      // Shablondan AI'ga qaytish
      MODE = "ai";
      updateGenBtn();
      renderPlan();
      showToast("AI rejaga qaytdingiz 🤖");
    } else {
      CURRENT_PLAN[ACC] = buildPlan(ACC);
      renderPlan();
      showToast("Yangi reja tayyor! ✨");
    }
  });

  document.getElementById("saveBtn").addEventListener("click", () => {
    ORDER.forEach(a => {
      SETTINGS.accounts[a].specialty = document.getElementById("sp-"+a).value.trim() || ACCOUNTS[a].defSpecialty;
      SETTINGS.accounts[a].dishes = document.getElementById("ds-"+a).value.trim() || ACCOUNTS[a].defDishes;
    });
    SETTINGS.postsPerWeek = +document.getElementById("setCount").value;
    saveSettings();
    CURRENT_PLAN = {};
    CURRENT_PLAN[ACC] = buildPlan(ACC);
    renderPlan();
    showToast("Sozlamalar saqlandi ✓");
  });
}

function updateGenBtn() {
  const btn = document.getElementById("genBtn");
  if (MODE === "ai") btn.innerHTML = "✨ Shablon reja tuzish";
  else if (AI_PLAN) btn.innerHTML = "🤖 AI rejaga qaytish";
  else btn.innerHTML = "✨ Yangi reja tuzish";
}

// ============================================================
//  MA'LUMOT YUKLASH
// ============================================================
async function loadData() {
  // 1) Asosiy statistika
  try {
    const res = await fetch("instagram_data.json?v=" + Date.now());
    if (!res.ok) throw new Error();
    const data = await res.json();
    if (Array.isArray(data) && data.length) { HISTORY = data; }
    else throw new Error();
  } catch(e) {
    HISTORY = buildDemo();
    document.getElementById("demoBanner").style.display = "flex";
  }

  // 2) AI tuzgan reja (bo'lsa)
  try {
    const res = await fetch("kontent_reja_ai.json?v=" + Date.now());
    if (res.ok) {
      const ai = await res.json();
      if (ai && ai.accounts) { AI_PLAN = ai; MODE = "ai"; }
    }
  } catch(e) { /* AI reja yo'q — shablon rejimda davom */ }
}

function buildDemo() {
  // Minimal demo: by_type + timestampli postlar
  const mk = (type, daysAgo, hour, eng) => ({
    type, engagement: eng,
    timestamp: new Date(Date.now() - daysAgo*86400000).toISOString().slice(0,11) + String(hour).padStart(2,"0") + ":30:00+0000",
  });
  const accs = {};
  ORDER.forEach((a, i) => {
    accs[a] = {
      engagement_rate: [3.1, 5.2, 2.4][i],
      by_type: {
        VIDEO: { count: 8, avg_engagement: [420, 18, 510][i] },
        IMAGE: { count: 12, avg_engagement: [310, 12, 380][i] },
        CAROUSEL_ALBUM: { count: 5, avg_engagement: [350, 15, 430][i] },
      },
      posts: [
        mk("VIDEO", 2, 19, 520), mk("IMAGE", 4, 12, 300), mk("VIDEO", 6, 19, 480),
        mk("CAROUSEL_ALBUM", 9, 18, 410), mk("IMAGE", 11, 13, 280), mk("VIDEO", 13, 20, 450),
        mk("IMAGE", 16, 12, 260), mk("VIDEO", 19, 19, 500),
      ],
    };
  });
  return [{ date: new Date().toISOString().slice(0,10), accounts: accs }];
}

// ---- Boshlash ----
(async function init(){
  await loadData();
  renderSettings();
  setupControls();
  CURRENT_PLAN[ACC] = buildPlan(ACC);
  updateGenBtn();
  renderInsights();
  renderPlan();
})();

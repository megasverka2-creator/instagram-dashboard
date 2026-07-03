// ============================================================================
//  RestoPulse — AI Tahlilchi (Savdo + Marketing birga)
//  Butun ma'lumotni (savdo, filiallar, dostavka, taomlar, atributsiya, IG)
//  ixcham xulosaga jamlab, Claude'ga yuboradi va harakatga chorlovchi tahlil oladi.
//  API kalit FAQAT shu brauzerda (localStorage), to'g'ridan Anthropic API.
// ============================================================================
(function () {
  "use strict";

  const KEY_NAME = "rp_ai_kalit"; // rp_chat bilan bir xil kalit
  const MODEL = "claude-sonnet-4-6";
  const getKey = () => { try { return atob(localStorage.getItem(KEY_NAME) || ""); } catch (e) { return ""; } };
  const setKey = (k) => localStorage.setItem(KEY_NAME, btoa(k.trim()));

  const fmt = n => (n || 0).toLocaleString("ru-RU");
  const mln = n => (Math.round((n || 0) / 100000) / 10).toLocaleString("ru-RU") + " mln";

  // AI Jamoa sahifasi uchun "ishlamoqda" signali
  function markBusy(agentId) {
    try {
      const b = JSON.parse(localStorage.getItem("rp_agent_busy") || "{}");
      b[agentId] = Date.now();
      localStorage.setItem("rp_agent_busy", JSON.stringify(b));
    } catch (e) {}
  }

  // --- Ma'lumotni AI uchun ixcham matn xulosaga aylantirish ---
  function buildContext() {
    const lines = [];
    const days = (typeof periodDays === "function") ? periodDays() : (window.SAVDO || []);
    const periodLabel = (window.PERIOD === "all") ? "butun davr" : (window.PERIOD || "7") + " kun";
    lines.push(`=== TANLANGAN DAVR: ${periodLabel} (${days.length} kun) ===`);

    // 1. Umumiy + brendlar
    if (window.BRANDS && window.BRAND_ORDER) {
      lines.push("\n--- BRENDLAR (tanlangan davr) ---");
      let totRev = 0, totChk = 0;
      BRAND_ORDER.forEach(bk => {
        const b = BRANDS[bk];
        let rev = 0, chk = 0;
        days.forEach(d => {
          if (typeof brandDay === "function") {
            const v = brandDay(d, bk); rev += v.revenue; chk += v.checks;
          }
        });
        totRev += rev; totChk += chk;
        const avg = chk ? Math.round(rev / chk) : 0;
        lines.push(`${b.name}: tushum ${mln(rev)}, cheklar ${fmt(chk)}, o'rtacha chek ${fmt(avg)} so'm`);
      });
      lines.push(`JAMI: tushum ${mln(totRev)}, cheklar ${fmt(totChk)}`);
    }

    // 2. Filiallar (har biri)
    if (typeof allDepts === "function") {
      lines.push("\n--- FILIALLAR (tanlangan davr) ---");
      allDepts().forEach(({ dep }) => {
        let rev = 0, chk = 0;
        days.forEach(d => {
          if (typeof depDay === "function") { const v = depDay(d, dep); rev += v.revenue; chk += v.checks; }
        });
        if (rev <= 0) return;
        const avg = chk ? Math.round(rev / chk) : 0;
        let dostInfo = "";
        if (typeof depDostShare === "function") {
          const dp = depDostShare(dep, days);
          if (dp !== null) dostInfo = `, dostavka ulushi ${dp}%`;
        }
        lines.push(`${dep}: tushum ${mln(rev)}, cheklar ${fmt(chk)}, o'rtacha chek ${fmt(avg)}${dostInfo}`);
      });
    }

    // 3. Dostavka vs Zal (umumiy)
    if (window.TURLAR && Array.isArray(window.TURLAR)) {
      const set = new Set(days.map(d => d.date));
      let dost = 0, zal = 0, olib = 0;
      TURLAR.forEach(td => {
        if (!set.has(td.date)) return;
        Object.values(td.departments || {}).forEach(node => {
          Object.entries(node).forEach(([kind, v]) => {
            const r = v.revenue || 0;
            if (kind === "dostavka") dost += r;
            else if (kind === "olib_ketish") olib += r;
            else zal += r;
          });
        });
      });
      const tot = dost + zal + olib;
      if (tot > 0) {
        lines.push("\n--- BUYURTMA TURLARI ---");
        lines.push(`Dostavka: ${mln(dost)} (${Math.round(dost/tot*100)}%), Zal: ${mln(zal)} (${Math.round(zal/tot*100)}%), Olib ketish: ${mln(olib)} (${Math.round(olib/tot*100)}%)`);
      }
    }

    // 4. TOP taomlar (brend bo'yicha)
    if (window.TAOMLAR && TAOMLAR.departments) {
      lines.push("\n--- ENG KO'P SOTILGAN TAOMLAR (brend bo'yicha, top 6) ---");
      // brendlarga guruhlash
      const brandDishes = {};
      Object.entries(TAOMLAR.departments).forEach(([dep, items]) => {
        let bk = "mazzona";
        if (window.BRANDS) {
          for (const k of BRAND_ORDER) { if (BRANDS[k].departments.includes(dep)) { bk = k; break; } }
        }
        brandDishes[bk] = brandDishes[bk] || {};
        (items || []).forEach(it => {
          const key = it.dish;
          brandDishes[bk][key] = brandDishes[bk][key] || { sum: 0, amount: 0 };
          brandDishes[bk][key].sum += it.sum || 0;
          brandDishes[bk][key].amount += it.amount || 0;
        });
      });
      Object.entries(brandDishes).forEach(([bk, dishes]) => {
        const name = window.BRANDS ? BRANDS[bk].name : bk;
        const top = Object.entries(dishes).sort((a, b) => b[1].sum - a[1].sum).slice(0, 6);
        const txt = top.map(([d, v]) => `${d} (${mln(v.sum)}, ${fmt(v.amount)} dona)`).join("; ");
        if (txt) lines.push(`${name}: ${txt}`);
      });
    }

    // 5. Marketing faoliyati (yirik postlar — qamrov). Savdo bilan SUN'IY bog'lanmaydi.
    if (typeof allPostAttributions === "function" && window.BRAND_ORDER) {
      lines.push("\n--- MARKETING FAOLIYATI (o'sha davrdagi eng ko'p ko'rilgan postlar) ---");
      BRAND_ORDER.filter(k => window.BRANDS && BRANDS[k].ig).forEach(bk => {
        const atts = allPostAttributions(bk);
        if (!atts.length) return;
        const sorted = atts.slice().sort((a, b) => ((b.views || b.reach || 0) - (a.views || a.reach || 0))).slice(0, 4);
        const txt = sorted.map(a => {
          const v = a.views ? fmt(a.views) + " ko'rish" : fmt(a.reach) + " qamrov";
          const cap = (a.caption || "").slice(0, 40);
          return `"${cap}" (${v})`;
        }).join("; ");
        if (txt) lines.push(`${BRANDS[bk].name}: ${txt}`);
      });
    }

    return lines.join("\n");
  }

  // --- Kunlik kontekst (bitta kun + oldingi kunlar bilan solishtirish) ---
  function buildDailyContext(targetDate) {
    const lines = [];
    const all = (window.SAVDO || []).slice().sort((a, b) => a.date.localeCompare(b.date));
    if (!all.length) return "Ma'lumot yo'q";

    const idx = all.findIndex(d => d.date === targetDate);
    if (idx < 0) return "Bu kun uchun ma'lumot yo'q";
    const day = all[idx];

    // Oldingi 7 kun o'rtachasi (solishtirish uchun)
    const prev = all.slice(Math.max(0, idx - 7), idx);
    const dow = new Date(targetDate + "T00:00:00").toLocaleDateString("ru-RU", { weekday: "long" });
    lines.push(`=== KUNLIK TAHLIL: ${targetDate} (${dow}) ===`);

    function sumDay(d, depFilter) {
      let rev = 0, chk = 0;
      Object.entries(d.departments || {}).forEach(([dep, v]) => {
        if (depFilter && !depFilter(dep)) return;
        rev += v.revenue || 0; chk += v.checks || 0;
      });
      return { rev, chk };
    }

    // Umumiy
    const td = sumDay(day);
    const prevAvg = prev.length ? prev.reduce((s, d) => s + sumDay(d).rev, 0) / prev.length : 0;
    const diff = prevAvg > 0 ? Math.round((td.rev - prevAvg) / prevAvg * 100) : null;
    lines.push(`\n--- UMUMIY ---`);
    lines.push(`Bu kun tushum: ${mln(td.rev)}, cheklar: ${fmt(td.chk)}, o'rtacha chek: ${fmt(td.chk ? Math.round(td.rev / td.chk) : 0)} so'm`);
    lines.push(`Oldingi 7 kun o'rtacha: ${mln(prevAvg)}/kun`);
    if (diff !== null) lines.push(`Farq: ${diff > 0 ? "+" : ""}${diff}% (o'rtachaga nisbatan)`);

    // Filiallar
    if (typeof allDepts === "function") {
      lines.push(`\n--- FILIALLAR (bu kun) ---`);
      allDepts().forEach(({ dep }) => {
        const v = (day.departments || {})[dep];
        if (!v || !v.revenue) return;
        const prevDepAvg = prev.length ? prev.reduce((s, d) => s + ((d.departments || {})[dep] || {}).revenue || 0, 0) / prev.length : 0;
        const dd = prevDepAvg > 0 ? Math.round((v.revenue - prevDepAvg) / prevDepAvg * 100) : null;
        lines.push(`${dep}: ${mln(v.revenue)}, cheklar ${fmt(v.checks || 0)}${dd !== null ? ` (o'rtachaga nisbatan ${dd > 0 ? "+" : ""}${dd}%)` : ""}`);
      });
    }

    // Buyurtma turlari (bu kun)
    if (window.TURLAR && Array.isArray(window.TURLAR)) {
      const td2 = TURLAR.find(t => t.date === targetDate);
      if (td2) {
        let dost = 0, zal = 0, olib = 0;
        Object.values(td2.departments || {}).forEach(node => {
          Object.entries(node).forEach(([kind, v]) => {
            const r = v.revenue || 0;
            if (kind === "dostavka") dost += r; else if (kind === "olib_ketish") olib += r; else zal += r;
          });
        });
        const tot = dost + zal + olib;
        if (tot > 0) {
          lines.push(`\n--- BUYURTMA TURLARI (bu kun) ---`);
          lines.push(`Dostavka: ${mln(dost)} (${Math.round(dost/tot*100)}%), Zal: ${mln(zal)} (${Math.round(zal/tot*100)}%), Olib ketish: ${mln(olib)} (${Math.round(olib/tot*100)}%)`);
        }
      }
    }

    // O'sha kuni IG post bo'lganmi
    if (window.IG && window.BRANDS && window.BRAND_ORDER) {
      const postsToday = [];
      BRAND_ORDER.filter(k => BRANDS[k].ig).forEach(bk => {
        if (typeof topPostsFor === "function") {
          topPostsFor(bk, 50).forEach(p => {
            if (p.date === targetDate) postsToday.push(`${BRANDS[bk].name}: "${(p.caption||'').slice(0,40)}" (${p.views ? fmt(p.views)+" ko'rish" : fmt(p.reach)+" qamrov"})`);
          });
        }
      });
      if (postsToday.length) {
        lines.push(`\n--- BU KUNI INSTAGRAM POSTLARI ---`);
        postsToday.forEach(p => lines.push(p));
      }
    }

    return lines.join("\n");
  }

  function dailySystemPrompt() {
    return `Sen RestoPulse savdo tahlilchisisan. Restoran brendlari (Benison, Eddo/Dieto, Mazzona) uchun BITTA KUN savdosini tahlil qilasan.

Vazifang: o'sha kun qanday o'tganini, oldingi kunlarga nisbatan yaxshimi yomonmi, sababini va nima qilish kerakligini ayt.

QOIDALAR:
- O'zbek tilida, qisqa va aniq. Bu kunlik tezkor xulosa — uzun yozma.
- Eng muhim 3-4 narsaga e'tibor ber.
- Qaysi filial yaxshi/yomon ketdi, dostavka ulushi qanday — shularni bog'la. Post bo'lsa, faqat marketing faoliyati sifatida eslat; bitta postni savdo o'zgarishiga SABAB qilma.
- Hafta kunini hisobga ol (dam olish kuni savdo tabiiy yuqori/past bo'lishi mumkin).
- Amaliy bo'l: "Smart City past" emas, "Smart City bugun -15%, ertaga e'tibor bering".

JAVOB FORMATI (markdown, qisqa):
## 📅 Bugungi xulosa
(1-2 jumla: kun qanday o'tdi)

## 📈 Asosiy nuqtalar
- (3-4 ta qisqa nuqta: filiallar, dostavka, postlar)

## 💡 Tavsiya
(1-2 ta aniq harakat)`;
  }

  // --- System prompt ---
  function systemPrompt() {
    return `Sen RestoPulse tizimining savdo va marketing tahlilchisisan. Zarafshon va Uchquduq shaharlaridagi restoran brendlari (Benison, Eddo/Dieto, Mazzona) uchun ishlaysan.

Sening vazifang: berilgan savdo va marketing ma'lumotini tahlil qilib, restoran egasi va menejeriga ANIQ, HARAKATGA CHORLOVCHI xulosa berish.

QOIDALAR:
- O'zbek tilida, sodda va aniq yoz. Restoran egasi tushunadigan til.
- Raqamlarga tayanib gapir, lekin "shuncha foiz oshdi" bilan cheklanma — NEGA va NIMA QILISH kerakligini ayt.
- MUHIM — MARKETING va SAVDO ALOHIDA: bitta postni savdo o'zgarishiga SABAB qilib ko'rsatma. "Bu post savdoni X% tushirdi/oshirdi" deb HECH QACHON yozma — bu statistik jihatdan noto'g'ri (savdoga dam olish kuni, ob-havo, aksiya, mavsum, joylashuv va o'nlab omil ta'sir qiladi, bitta post emas). Marketingni (qamrov, faollik) va savdoni ayrim-ayrim tahlil qil. Agar bog'lanish haqida gapirsang — faqat uzoq muddatli, TAKRORLANUVCHI naqsh sifatida, ehtiyotkorlik bilan ("reels ko'p chiqqan haftalarda savdo o'rtacha yuqoriroq kuzatiladi"), va aniq foizni bitta postga bog'lama.
- Eng muhim 4-6 ta xulosaga e'tibor ber, hammasini sanama.
- Har xulosa amaliy bo'lsin: "Smart City -12% tushdi" emas, "Smart City -12% tushdi, sababini tekshiring va shu hafta aksiya o'ylang".
- Maqtov uchun maqtama. Muammoni ham, imkoniyatni ham ochiq ayt.

JAVOB FORMATI (markdown):
## 📊 Asosiy xulosa
(2-3 jumlada eng muhim narsa)

## ✅ Yaxshi ketayotgan
- (2-3 nuqta)

## ⚠️ E'tibor talab qiladi
- (2-3 nuqta, har biriga tavsiya bilan)

## 🎯 Bu hafta qilish kerak
- (3-4 aniq harakat)`;
  }

  // --- Tahlilni ishga tushirish ---
  async function runAnalysis() {
    const out = document.getElementById("analystOut");
    const btn = document.getElementById("analystBtn");
    if (!out) return;

    let key = getKey();
    if (!key) {
      const k = prompt("AI tahlil uchun Anthropic API kalitini kiriting (faqat shu brauzerda saqlanadi):");
      if (!k) return;
      setKey(k); key = k.trim();
    }

    const ctx = buildContext();
    markBusy("tahlil");
    out.innerHTML = `<div class="an-loading">🧠 AI butun savdo va marketing ma'lumotini tahlil qilmoqda…</div>`;
    if (btn) { btn.disabled = true; btn.textContent = "⏳ Tahlil qilinmoqda…"; }

    try {
      const res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-api-key": key,
          "anthropic-version": "2023-06-01",
          "anthropic-dangerous-direct-browser-access": "true",
        },
        body: JSON.stringify({
          model: MODEL,
          max_tokens: 1500,
          system: systemPrompt(),
          messages: [{ role: "user", content: "Mana joriy ma'lumot. To'liq tahlil qilib, xulosa va tavsiyalar ber:\n\n" + ctx }],
        }),
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error.message || "API xato");
      if (window.RP_Cost) RP_Cost.record("tahlil", data.usage);
      const text = (data.content || []).filter(c => c.type === "text").map(c => c.text).join("\n");
      out.innerHTML = `<div class="an-result">${mdToHtml(text)}</div>
        <div class="an-foot">AI tahlili · ${new Date().toLocaleString("ru-RU")} · ma'lumotga asoslangan, qaror sizniki</div>`;
    } catch (e) {
      out.innerHTML = `<div class="an-error">Xato: ${e.message}<br><small>API kalit noto'g'ri bo'lsa, <a href="#" onclick="localStorage.removeItem('${KEY_NAME}');location.reload();return false;">qaytadan kiriting</a>.</small></div>`;
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = "🔄 Qayta tahlil"; }
    }
  }

  // --- Oddiy markdown -> HTML ---
  function mdToHtml(md) {
    let h = md
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/^### (.*)$/gm, "<h4>$1</h4>")
      .replace(/^## (.*)$/gm, "<h3>$1</h3>")
      .replace(/^# (.*)$/gm, "<h3>$1</h3>")
      .replace(/\*\*(.+?)\*\*/g, "<b>$1</b>")
      .replace(/^- (.*)$/gm, "<li>$1</li>")
      .replace(/(<li>[\s\S]*?<\/li>)(?!\s*<li>)/g, "<ul>$1</ul>");
    h = h.split(/\n{2,}/).map(p => {
      if (/^\s*<(h3|h4|ul)/.test(p)) return p;
      return p.trim() ? `<p>${p.replace(/\n/g, "<br>")}</p>` : "";
    }).join("");
    return h;
  }

  // --- Kunlik tahlilni ishga tushirish ---
  async function runDailyAnalysis(targetDate) {
    const out = document.getElementById("dailyOut");
    const btn = document.getElementById("dailyBtn");
    if (!out) return;

    let key = getKey();
    if (!key) {
      const k = prompt("AI tahlil uchun Anthropic API kalitini kiriting (faqat shu brauzerda saqlanadi):");
      if (!k) return;
      setKey(k); key = k.trim();
    }

    const ctx = buildDailyContext(targetDate);
    markBusy("kunlik");
    out.innerHTML = `<div class="an-loading">🧠 ${targetDate} kuni tahlil qilinmoqda…</div>`;
    if (btn) { btn.disabled = true; btn.textContent = "⏳ Tahlil…"; }

    try {
      const res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-api-key": key,
          "anthropic-version": "2023-06-01",
          "anthropic-dangerous-direct-browser-access": "true",
        },
        body: JSON.stringify({
          model: MODEL,
          max_tokens: 1000,
          system: dailySystemPrompt(),
          messages: [{ role: "user", content: "Mana shu kunning ma'lumoti. Qisqa kunlik tahlil ber:\n\n" + ctx }],
        }),
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error.message || "API xato");
      if (window.RP_Cost) RP_Cost.record("kunlik", data.usage);
      const text = (data.content || []).filter(c => c.type === "text").map(c => c.text).join("\n");
      out.innerHTML = `<div class="an-result">${mdToHtml(text)}</div>
        <div class="an-foot">${targetDate} · AI kunlik tahlili</div>`;
    } catch (e) {
      out.innerHTML = `<div class="an-error">Xato: ${e.message}</div>`;
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = "✨ Kunni tahlil qil"; }
    }
  }

  // Mavjud kunlarni select uchun ro'yxat
  function availableDates() {
    return (window.SAVDO || []).map(d => d.date).sort().reverse();
  }

  // --- Tashqi interfeys ---
  window.RP_Analyst = { run: runAnalysis, runDaily: runDailyAnalysis, buildContext, buildDailyContext, availableDates };

  // Kun tanlash select'ini ma'lumot tayyor bo'lgach to'ldiramiz
  function fillDates() {
    const sel = document.getElementById("dailyDate");
    if (!sel) return;
    const dates = availableDates();
    if (!dates.length) { setTimeout(fillDates, 600); return; }
    sel.innerHTML = dates.slice(0, 60).map((d, i) => {
      const dow = new Date(d + "T00:00:00").toLocaleDateString("ru-RU", { weekday: "short" });
      const label = i === 0 ? `${d} (${dow}) — oxirgi` : `${d} (${dow})`;
      return `<option value="${d}">${label}</option>`;
    }).join("");
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => setTimeout(fillDates, 400));
  } else {
    setTimeout(fillDates, 400);
  }
})();

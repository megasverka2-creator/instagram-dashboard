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

    // 5. Marketing atributsiya (yirik postlar -> savdo)
    if (typeof allPostAttributions === "function" && window.BRAND_ORDER) {
      lines.push("\n--- MARKETING ATRIBUTSIYA (post -> savdo ta'siri) ---");
      BRAND_ORDER.filter(k => window.BRANDS && BRANDS[k].ig).forEach(bk => {
        const atts = allPostAttributions(bk);
        if (!atts.length) return;
        const sorted = atts.slice().sort((a, b) => (b.pct || 0) - (a.pct || 0)).slice(0, 4);
        const txt = sorted.map(a => {
          const v = a.views ? fmt(a.views) + " ko'rish" : fmt(a.reach) + " qamrov";
          const cap = (a.caption || "").slice(0, 40);
          return `"${cap}" (${v}, savdo ${a.pct > 0 ? "+" : ""}${a.pct}%)`;
        }).join("; ");
        if (txt) lines.push(`${BRANDS[bk].name}: ${txt}`);
      });
    }

    return lines.join("\n");
  }

  // --- System prompt ---
  function systemPrompt() {
    return `Sen RestoPulse tizimining savdo va marketing tahlilchisisan. Zarafshon va Uchquduq shaharlaridagi restoran brendlari (Benison, Eddo/Dieto, Mazzona) uchun ishlaysan.

Sening vazifang: berilgan savdo va marketing ma'lumotini tahlil qilib, restoran egasi va menejeriga ANIQ, HARAKATGA CHORLOVCHI xulosa berish.

QOIDALAR:
- O'zbek tilida, sodda va aniq yoz. Restoran egasi tushunadigan til.
- Raqamlarga tayanib gapir, lekin "shuncha foiz oshdi" bilan cheklanma — NEGA va NIMA QILISH kerakligini ayt.
- Atributsiyada ehtiyot bo'l: post savdoga "ta'sir qilgan" deb ayt, lekin "yagona sabab" dema (dam olish kuni, ob-havo ham ta'sir qiladi).
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

  // --- Tashqi interfeys ---
  window.RP_Analyst = { run: runAnalysis, buildContext };
})();

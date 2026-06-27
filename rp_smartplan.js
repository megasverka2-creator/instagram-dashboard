// ============================================================================
//  RestoPulse — 🧠 Aqlli reja (AI collaboratsiya)
//  Ikki agent ketma-ket ishlaydi:
//   1) Tahlilchi — savdo + marketingni o'qib, eng zo'r taom/format topadi
//   2) Reja AI  — o'sha xulosaga asoslanib yangi haftalik reja yozadi
//  Tahlilchi natijasi Reja AI'ga uzatiladi — bu rost agent collaboratsiyasi.
// ============================================================================
(function () {
  "use strict";
  const KEY_NAME = "rp_ai_kalit";
  const MODEL = "claude-sonnet-4-6";
  const getKey = () => { try { return atob(localStorage.getItem(KEY_NAME) || ""); } catch (e) { return ""; } };
  const setKey = (k) => localStorage.setItem(KEY_NAME, btoa(k.trim()));

  function markBusy(id) {
    try { const b = JSON.parse(localStorage.getItem("rp_agent_busy") || "{}"); b[id] = Date.now(); localStorage.setItem("rp_agent_busy", JSON.stringify(b)); } catch (e) {}
  }
  function recordCost(agentId, usage) { if (window.RP_Cost) RP_Cost.record(agentId, usage); }

  async function callClaude(key, system, userText, maxTokens) {
    const res = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "anthropic-dangerous-direct-browser-access": "true",
      },
      body: JSON.stringify({
        model: MODEL, max_tokens: maxTokens || 1500,
        system, messages: [{ role: "user", content: userText }],
      }),
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error.message || "API xato");
    const text = (data.content || []).filter(c => c.type === "text").map(c => c.text).join("\n");
    return { text, usage: data.usage };
  }

  // --- 1-bosqich: Tahlilchi xulosasi (savdo + marketing) ---
  // Reja sahifasida savdo.js yo'q — shuning uchun ma'lumotni mustaqil yuklaymiz
  async function analystBrief() {
    // rp_analyst.js dagi buildContext bor bo'lsa — o'shani ishlatamiz (eng to'liq)
    if (window.RP_Analyst && typeof RP_Analyst.buildContext === "function" && window.SAVDO && SAVDO.length) {
      try { const c = RP_Analyst.buildContext(); if (c && c.length > 50) return c; } catch (e) {}
    }
    // Mustaqil: shifrlangan savdo + IG'dan qisqa xulosa
    const lines = [];
    try {
      const dec = window.RP_Dekript;
      // TOP taomlar (shifrlangan)
      const taom = await loadEnc("savdo_taomlar.enc.json");
      if (taom && taom.departments) {
        lines.push("=== ENG KO'P SOTILGAN TAOMLAR (brend bo'yicha) ===");
        const brandMap = { "Benison-MegaCenter":"Benison","Benison-Oila":"Benison","Smart City":"Benison","Eddo":"Eddo","Mazzona":"Mazzona" };
        const byBrand = {};
        Object.entries(taom.departments).forEach(([dep, items]) => {
          const bk = brandMap[dep] || dep;
          byBrand[bk] = byBrand[bk] || {};
          (items||[]).forEach(it => {
            byBrand[bk][it.dish] = (byBrand[bk][it.dish]||0) + (it.sum||0);
          });
        });
        Object.entries(byBrand).forEach(([bk, dishes]) => {
          const top = Object.entries(dishes).sort((a,b)=>b[1]-a[1]).slice(0,6)
            .map(([d,s]) => `${d} (${(s/1e6).toFixed(1)} mln)`).join("; ");
          lines.push(`${bk}: ${top}`);
        });
      }
    } catch (e) {}
    // IG postlar (eng zo'r format)
    try {
      const ig = await fetchEncrypted("instagram_data.enc.json", "instagram_data.json");
      if (ig) {
        const last = ig[ig.length-1] || {};
        lines.push("\n=== INSTAGRAM ENG ZO'R POSTLAR ===");
        Object.entries(last.accounts || {}).forEach(([acc, data]) => {
          const posts = (data.posts || []).slice().sort((a,b)=>(b.views||b.reach||0)-(a.views||a.reach||0)).slice(0,3);
          if (posts.length) {
            const txt = posts.map(p => `"${(p.caption||'').slice(0,40)}" (${(p.views||p.reach||0).toLocaleString()} ko'rish)`).join("; ");
            lines.push(`@${acc}: ${txt}`);
          }
        });
      }
    } catch (e) {}
    return lines.length ? lines.join("\n") : null;
  }

  // Shifrlangan JSON yuklash (kontent_reja sahifasida dekript bor bo'lsa)
  async function loadEnc(fname) {
    try {
      if (window.fetchEncrypted) return await window.fetchEncrypted(fname, fname.replace(".enc",""));
    } catch (e) {}
    return null;
  }

  const analystSystem = `Sen RestoPulse savdo+marketing tahlilchisisan. Vazifang: berilgan ma'lumotdan KONTENT REJA uchun eng muhim xulosalarni ajratish.

Faqat shularni qisqa ber (kontent rejaga kerakli):
- Qaysi taom eng ko'p sotiladi / daromad keltiradi (brendlar bo'yicha)
- Qaysi post formati savdoga eng ko'p ta'sir qilgan (atributsiyadan)
- Qaysi kun/vaqt eng faol
- Qaysi taomni reklama qilish kerak (qimmat, lekin kam sotilyapti)

JAVOB: qisqa, faqat faktlar ro'yxati. Reja yozma — faqat tahlilchi xulosasi. O'zbek tilida.`;

  const plannerSystem = `Sen RestoPulse kontent rejachisisan. Zarafshon/Uchquduqdagi restoran brendlari (Benison, Eddo/Dieto, Mazzona) uchun Instagram haftalik reja tuzasan.

MUHIM: senga TAHLILCHI hamkasbing savdo xulosasini berdi. Rejani SHU XULOSAGA asoslab tuz — qaysi taom ko'p sotiladi, qaysi format ishlaydi, nimani reklama qilish kerak.

QOIDALAR:
- Har brend uchun 3-4 post g'oyasi (hafta bo'yi).
- Har g'oya tahlilchi xulosasiga bog'lanssin (masalan "shashlik eng ko'p daromad → shashlik posti").
- Reklama nomzodi taomlarni alohida ta'kidla.
- O'zbek tilida, restoran egasi tushunadigan til. Narx yozma, raqobatchi nomini yozma.

JAVOB FORMATI (markdown):
## 🧠 Tahlilchi nimani topdi
(1-2 jumla: asosiy xulosa)

## 📅 Bu hafta rejasi
### Benison
- **[Kun, format]**: g'oya — nega (tahlilchi xulosasiga bog'liq)
(3-4 ta)

### Eddo
(3-4 ta)

### Mazzona
(3-4 ta)

## 💡 Maxsus tavsiya
(reklama qilish kerak bo'lgan taom)`;

  async function runSmartPlan() {
    const out = document.getElementById("smartPlanOut");
    const btn = document.getElementById("smartPlanBtn");
    if (!out) return;

    let key = getKey();
    if (!key) {
      const k = prompt("AI uchun Anthropic API kalitini kiriting (faqat shu brauzerda saqlanadi):");
      if (!k) return;
      setKey(k); key = k.trim();
    }

    if (btn) { btn.disabled = true; btn.textContent = "⏳ Ishlamoqda…"; }

    try {
      // === 1-BOSQICH: Tahlilchi ===
      out.innerHTML = `<div class="sp-step"><div class="sp-spin"></div> <b>Tahlilchi</b> savdo va marketingni o'qiyapti…</div>`;
      markBusy("tahlil");
      const brief = await analystBrief();
      let insights;
      if (brief) {
        const r1 = await callClaude(key, analystSystem, "Mana joriy savdo va marketing ma'lumoti. Kontent reja uchun eng muhim xulosalarni ajrat:\n\n" + brief, 800);
        recordCost("tahlil", r1.usage);
        insights = r1.text;
      } else {
        insights = "(Savdo ma'lumoti bu sahifada yo'q — reja Instagram natijalariga asoslanadi.)";
      }

      // === 2-BOSQICH: Reja AI (tahlilchi xulosasini oladi) ===
      out.innerHTML = `<div class="sp-step sp-done">✅ <b>Tahlilchi</b> xulosa berdi</div>
        <div class="sp-step"><div class="sp-spin"></div> <b>Reja AI</b> shu xulosaga asoslab reja yozyapti…</div>`;
      markBusy("reja");
      const r2 = await callClaude(key, plannerSystem,
        "TAHLILCHI HAMKASBIM SHUNI TOPDI:\n\n" + insights + "\n\n---\n\nShu xulosaga asoslab, bu hafta uchun kontent reja tuz.", 2000);
      recordCost("reja", r2.usage);

      out.innerHTML = `
        <div class="sp-flow">
          <span class="sp-badge done">🧠 Tahlilchi</span>
          <span class="sp-arrow">→</span>
          <span class="sp-badge done">📅 Reja AI</span>
          <span class="sp-flow-note">ikki agent ketma-ket ishladi</span>
        </div>
        <div class="sp-result">${mdToHtml(r2.text)}</div>
        <div class="sp-foot">🧠 Tahlilchi → 📅 Reja · ${new Date().toLocaleString("ru-RU")} · ma'lumotga asoslangan</div>`;
    } catch (e) {
      out.innerHTML = `<div class="sp-error">Xato: ${e.message}<br><small>API kalit noto'g'ri bo'lsa <a href="#" onclick="localStorage.removeItem('${KEY_NAME}');location.reload();return false;">qaytadan kiriting</a>.</small></div>`;
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = "🧠 Aqlli reja tuz"; }
    }
  }

  function mdToHtml(md) {
    let h = md
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/^#### (.*)$/gm, "<h4>$1</h4>")
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

  window.RP_SmartPlan = { run: runSmartPlan };
})();

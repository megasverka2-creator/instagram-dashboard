// ============================================================
//  RestoPulse — Kontent studiyasi (AI chat)
//  Post g'oyasini chuqurlashtirish: ssenariy, kadrlar, captionlar
//  MUSTAQIL MODUL — kontent_reja.js ga bog'liq emas.
//  API kalit FAQAT shu brauzerda (localStorage) saqlanadi,
//  saytga/repoga hech qachon yozilmaydi.
// ============================================================
(function () {
  const KEY_NAME = "rp_ai_kalit";
  const MODEL = "claude-sonnet-4-6";
  let RESTO = null;          // restoran_info.json keshi
  let messages = [];         // joriy suhbat
  let systemPrompt = "";
  let busy = false;

  // ---------- Kalit ----------
  const getKey = () => { try { return atob(localStorage.getItem(KEY_NAME) || ""); } catch (e) { return ""; } };
  const setKey = (k) => localStorage.setItem(KEY_NAME, btoa(k.trim()));
  const delKey = () => localStorage.removeItem(KEY_NAME);

  // ---------- CSS ----------
  const css = document.createElement("style");
  css.textContent = `
  .rpc-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.35); z-index:120;
    opacity:0; pointer-events:none; transition:opacity .25s; backdrop-filter:blur(3px); -webkit-backdrop-filter:blur(3px); }
  .rpc-overlay.open { opacity:1; pointer-events:auto; }
  .rpc-sheet {
    position:fixed; left:50%; bottom:0; transform:translateX(-50%) translateY(105%);
    width:100%; max-width:600px; max-height:82vh; z-index:121;
    background:#FFFFFF; border:none;
    border-radius:24px 24px 0 0; box-shadow:0 -14px 50px rgba(0,0,0,0.16);
    display:flex; flex-direction:column;
    transition:transform .38s cubic-bezier(.3,1.1,.35,1);
    font-family:-apple-system,BlinkMacSystemFont,'SF Pro Display','SF Pro Text',Inter,sans-serif;
  }
  .rpc-sheet.open { transform:translateX(-50%) translateY(0); }
  .rpc-head { display:flex; align-items:center; gap:11px; padding:15px 18px 12px;
    border-bottom:1px solid rgba(60,60,67,0.12); flex-shrink:0; }
  .rpc-head .ava { width:38px; height:38px; border-radius:12px; flex-shrink:0;
    background:#FF9500; display:flex; align-items:center; justify-content:center; font-size:18px; }
  .rpc-head h3 { font-size:16.5px; font-weight:700; letter-spacing:-.35px; color:#1C1C1E; }
  .rpc-head .sub { font-size:11.5px; color:rgba(60,60,67,.6); margin-top:1px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:330px; }
  .rpc-head .sp { flex:1; }
  .rpc-ic { border:none; background:rgba(118,118,128,0.12); color:rgba(60,60,67,.6); width:32px; height:32px;
    border-radius:10px; cursor:pointer; font-size:15px; transition:background .2s; flex-shrink:0; }
  .rpc-ic:hover { background:rgba(118,118,128,0.2); color:#1C1C1E; }
  .rpc-body { flex:1; overflow-y:auto; padding:16px 18px; display:flex; flex-direction:column; gap:11px; -webkit-overflow-scrolling:touch; }
  .rpc-msg { max-width:88%; padding:11px 14px; border-radius:16px; font-size:13.5px; line-height:1.6; white-space:pre-wrap; word-break:break-word; }
  .rpc-msg.user { align-self:flex-end; background:#FF9500; color:#fff; border-bottom-right-radius:5px; }
  .rpc-msg.ai { align-self:flex-start; background:#fff; border:1px solid rgba(60,60,67,0.1); color:#1C1C1E; border-bottom-left-radius:5px; }
  .rpc-msg.ai b { font-weight:600; }
  .rpc-msg.err { align-self:center; background:rgba(210,59,94,0.09); color:#b02a4d; font-size:12.5px; text-align:center; }
  .rpc-typing { align-self:flex-start; display:flex; gap:4px; padding:13px 16px; }
  .rpc-typing i { width:7px; height:7px; border-radius:50%; background:#FF9500; opacity:.4; animation:rpcB 1.2s infinite; font-style:normal; }
  .rpc-typing i:nth-child(2){animation-delay:.18s} .rpc-typing i:nth-child(3){animation-delay:.36s}
  @keyframes rpcB { 0%,60%,100%{opacity:.35; transform:translateY(0)} 30%{opacity:1; transform:translateY(-4px)} }
  .rpc-chips { display:flex; gap:7px; flex-wrap:wrap; padding:0 18px 8px; flex-shrink:0; }
  .rpc-chip { border:1px solid rgba(60,60,67,0.16); background:#fff; color:#1C1C1E;
    font-family:inherit; font-size:12px; font-weight:500; padding:7px 12px; border-radius:999px; cursor:pointer; transition:all .2s; }
  .rpc-chip:hover { background:rgba(255,149,0,0.08); border-color:rgba(255,149,0,0.55); }
  .rpc-foot { display:flex; gap:9px; padding:11px 16px calc(13px + env(safe-area-inset-bottom)); border-top:1px solid rgba(60,60,67,0.12); flex-shrink:0; }
  .rpc-foot textarea { flex:1; border:1.5px solid rgba(60,60,67,0.14); background:#fff; border-radius:14px;
    padding:11px 14px; font-family:inherit; font-size:14px; color:#1C1C1E; outline:none; resize:none;
    height:44px; max-height:110px; line-height:1.45; transition:border .2s; }
  .rpc-foot textarea:focus { border-color:#FF9500; }
  .rpc-send { border:none; cursor:pointer; width:44px; height:44px; border-radius:14px; flex-shrink:0;
    background:#FF9500; color:#fff; font-size:17px;
    box-shadow:0 5px 16px rgba(255,149,0,0.3); transition:transform .15s, opacity .2s; }
  .rpc-send:hover { transform:translateY(-2px); }
  .rpc-send:disabled { opacity:.5; cursor:wait; transform:none; }
  .rpc-setup { padding:22px 20px; display:flex; flex-direction:column; gap:12px; overflow-y:auto; }
  .rpc-setup h4 { font-size:17px; font-weight:700; letter-spacing:-.35px; color:#1C1C1E; }
  .rpc-setup p { font-size:13px; line-height:1.6; color:rgba(60,60,67,.6); }
  .rpc-setup input { border:1.5px solid rgba(60,60,67,0.14); background:#fff; border-radius:13px;
    padding:12px 14px; font-family:inherit; font-size:13.5px; color:#1C1C1E; outline:none; }
  .rpc-setup input:focus { border-color:#FF9500; }
  .rpc-setup .save { border:none; cursor:pointer; padding:13px; border-radius:13px; font-family:inherit;
    font-size:14px; font-weight:600; color:#fff; background:#FF9500;
    box-shadow:0 5px 16px rgba(255,149,0,0.3); }
  .rpc-note { font-size:11.5px; color:rgba(60,60,67,.6); background:#FFF8E6;
    border:none; border-radius:12px; padding:10px 13px; line-height:1.55; }
  @media (max-width:640px){ .rpc-sheet{max-width:100%; border-radius:20px 20px 0 0; max-height:88vh;} .rpc-head .sub{max-width:200px;} }
  @media (prefers-reduced-motion:reduce){ .rpc-sheet{transition:none} .rpc-overlay{transition:none} }
  `;
  document.head.appendChild(css);

  // ---------- UI skelet ----------
  const overlay = document.createElement("div");
  overlay.className = "rpc-overlay";
  const sheet = document.createElement("div");
  sheet.className = "rpc-sheet";
  sheet.innerHTML = `
    <div class="rpc-head">
      <div class="ava">🎬</div>
      <div style="min-width:0;">
        <h3>Kontent studiyasi</h3>
        <div class="sub" id="rpcSub">Post g'oyasini birga chuqurlashtiramiz</div>
      </div>
      <div class="sp"></div>
      <button class="rpc-ic" id="rpcKeyBtn" title="API kalit sozlamasi">⚙️</button>
      <button class="rpc-ic" id="rpcClose" title="Yopish">✕</button>
    </div>
    <div class="rpc-body" id="rpcBody"></div>
    <div class="rpc-chips" id="rpcChips"></div>
    <div class="rpc-foot" id="rpcFoot">
      <textarea id="rpcInput" placeholder="Savolingizni yozing..." rows="1"></textarea>
      <button class="rpc-send" id="rpcSend">➤</button>
    </div>`;
  document.addEventListener("DOMContentLoaded", () => {
    document.body.appendChild(overlay);
    document.body.appendChild(sheet);
    wire();
  });
  if (document.readyState !== "loading") {
    document.body.appendChild(overlay);
    document.body.appendChild(sheet);
    wire();
  }

  const $ = (id) => document.getElementById(id);
  const esc = (t) => String(t).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");

  function wire() {
    if (wire.done) return; wire.done = true;
    overlay.addEventListener("click", close);
    $("rpcClose").addEventListener("click", close);
    $("rpcKeyBtn").addEventListener("click", () => showSetup(true));
    $("rpcSend").addEventListener("click", send);
    $("rpcInput").addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
    });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") close(); });
  }

  function open()  { overlay.classList.add("open"); sheet.classList.add("open"); }
  function close() { overlay.classList.remove("open"); sheet.classList.remove("open"); }

  // ---------- Kontekst yig'ish ----------
  async function loadResto() {
    if (RESTO) return RESTO;
    try {
      const r = await fetch("restoran_info.json?v=" + Date.now());
      if (r.ok) RESTO = await r.json();
    } catch (e) {}
    return RESTO;
  }

  function cardContext(btn) {
    const card = btn.closest(".day-card");
    const pick = (sel) => { const el = card && card.querySelector(sel); return el ? el.textContent.trim() : ""; };
    const badges = card ? [...card.querySelectorAll(".badge")].map(b => b.textContent.trim()).join(" · ") : "";
    return {
      kun: pick(".day-head h4"),
      vaqt: pick(".tm"),
      turi: badges,
      caption: pick(".cap"),
    };
  }

  function activeAcc() {
    const t = document.querySelector(".nav .tab.active");
    return t ? t.dataset.acc : "benison_uz";
  }

  async function buildSystem(ctx, acc) {
    const info = await loadResto();
    let restoTxt = "";
    if (info) {
      const u = info.umumiy || {};
      const a = (info.accounts || {})[acc] || {};
      restoTxt = `RESTORAN: ${a.nomi || acc} — ${a.tavsif || ""}
Mashhur taomlar: ${a.taomlar || "—"}
${a.muhim ? "MUHIM: " + a.muhim : ""}
Filiallar: ${(a.filiallar || []).join("; ")}
Ish vaqti: ${a.ish_vaqti || "—"}. Mijozlar: ${a.mijozlar || "—"}
CTA: ${u.cta || ""}
QAT'IY TAQIQLAR: ${(u.taqiqlar || []).join("; ")}. ${u.aksiya_chegarasi || ""}`;
    }
    return `Sen — O'zbekistondagi restoranlar tarmog'ining tajribali SMM-prodyuserisan. Marketolog seninle POST G'OYASINI amalga oshirishni maslahatlashadi.

${restoTxt}

MUHOKAMA QILINAYOTGAN POST:
Kun/vaqt: ${ctx.kun} ${ctx.vaqt}
Tur/mavzu: ${ctx.turi}
Caption (reja): ${ctx.caption}

QOIDALAR:
- Faqat o'zbek tilida, amaliy va aniq javob ber. Suv quyma.
- Video so'ralsa: kadrma-kadr ssenariy (vaqt belgilari bilan), qaysi telefon rakursi, yorug'lik, musiqa kayfiyati.
- Post so'ralsa: kompozitsiya, rekvizit, rang.
- Caption so'ralsa: 2-3 variant, har biri qisqa, emoji me'yorida, oxirida CTA.
- TAQIQLARGA qat'iy rioya qil: narx yozma, raqobatchi tilga olma, alkogol yo'q.
- Oddiy telefon bilan suratga olinadi deb hisobla — professional studiya talab qilma.
- Javob 250 so'zdan oshmasin (faqat to'liq ssenariy so'ralsa uzunroq mumkin).`;
  }

  // ---------- Ochish (global) ----------
  window.rpChatOchish = async function (btn) {
    const ctx = cardContext(btn);
    const acc = activeAcc();
    $("rpcSub").textContent = `${ctx.kun || "Post"} · ${ctx.turi || ""}`.slice(0, 70);
    messages = [];
    systemPrompt = await buildSystem(ctx, acc);
    if (!getKey()) { showSetup(false); open(); return; }
    showChat();
    aiMsg(`Salom! "${ctx.kun}" kungi post ustida ishlaymiz 🎬\nQuyidagi tez tugmalardan birini tanlang yoki o'z savolingizni yozing.`);
    open();
  };

  // ---------- Ko'rinishlar ----------
  function showChat() {
    $("rpcBody").innerHTML = "";
    $("rpcFoot").style.display = "flex";
    $("rpcChips").style.display = "flex";
    $("rpcChips").innerHTML = [
      "🎬 15 soniyalik video ssenariy",
      "📸 Qanday kadrlar olamiz?",
      "✍️ Caption 3 variant",
      "💡 G'oyani kuchaytir",
    ].map(c => `<button class="rpc-chip">${c}</button>`).join("");
    [...$("rpcChips").children].forEach(ch =>
      ch.addEventListener("click", () => { $("rpcInput").value = ch.textContent.replace(/^[^\s]+\s/, ""); send(); })
    );
  }

  function showSetup(fromGear) {
    $("rpcFoot").style.display = "none";
    $("rpcChips").style.display = "none";
    const has = !!getKey();
    $("rpcBody").innerHTML = `
      <div class="rpc-setup">
        <h4>🔑 AI kalitni ulash ${has ? "(almashtirish)" : ""}</h4>
        <p>Chat ishlashi uchun Anthropic API kaliti kerak. U <b>faqat shu brauzerda</b> saqlanadi — saytga ham, GitHub'ga ham yuborilmaydi.</p>
        <p>Kalit olish: <b>console.anthropic.com</b> → API Keys → Create Key. (GitHub Secrets'dagi ANTHROPIC_API_KEY bilan bir xil turdagi kalit.)</p>
        <input type="password" id="rpcKeyInput" placeholder="sk-ant-..." autocomplete="off">
        <button class="save" id="rpcKeySave">Saqlash va boshlash</button>
        ${has ? "<button class='save' id='rpcKeyDel' style='background:rgba(210,59,94,0.85)'>Kalitni bu brauzerdan o'chirish</button>" : ""}
        <div class="rpc-note">⚠️ Umumiy/begona kompyuterda kalit kiritmang. Har bir suhbat ozgina API xarajati qiladi (odatda bir necha yuz so'm atrofida).</div>
      </div>`;
    $("rpcKeySave").addEventListener("click", () => {
      const v = $("rpcKeyInput").value.trim();
      if (!v.startsWith("sk-ant-")) { $("rpcKeyInput").style.borderColor = "#d23b5e"; return; }
      setKey(v);
      showChat();
      aiMsg("Kalit saqlandi ✅ Endi post ustida ishlashimiz mumkin — tez tugmalardan birini tanlang.");
    });
    const del = $("rpcKeyDel");
    if (del) del.addEventListener("click", () => { delKey(); close(); });
    if (fromGear) open();
  }

  // ---------- Xabarlar ----------
  function userMsg(t) {
    const d = document.createElement("div");
    d.className = "rpc-msg user"; d.textContent = t;
    $("rpcBody").appendChild(d); scrollDown();
  }
  function aiMsg(t) {
    const d = document.createElement("div");
    d.className = "rpc-msg ai";
    d.innerHTML = esc(t).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
    $("rpcBody").appendChild(d); scrollDown();
  }
  function errMsg(t) {
    const d = document.createElement("div");
    d.className = "rpc-msg err"; d.textContent = t;
    $("rpcBody").appendChild(d); scrollDown();
  }
  function typing(on) {
    let t = $("rpcTyping");
    if (on) {
      if (t) return;
      t = document.createElement("div");
      t.className = "rpc-typing"; t.id = "rpcTyping";
      t.innerHTML = "<i></i><i></i><i></i>";
      $("rpcBody").appendChild(t); scrollDown();
    } else if (t) t.remove();
  }
  function scrollDown() { const b = $("rpcBody"); b.scrollTop = b.scrollHeight; }

  // ---------- Yuborish ----------
  async function send() {
    if (busy) return;
    const inp = $("rpcInput");
    const text = inp.value.trim();
    if (!text) return;
    inp.value = "";
    userMsg(text);
    messages.push({ role: "user", content: text });
    busy = true; $("rpcSend").disabled = true; typing(true);
    try {
      const res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-api-key": getKey(),
          "anthropic-version": "2023-06-01",
          "anthropic-dangerous-direct-browser-access": "true",
        },
        body: JSON.stringify({
          model: MODEL,
          max_tokens: 1400,
          system: systemPrompt,
          messages: messages.slice(-12),
        }),
      });
      const data = await res.json();
      typing(false);
      if (!res.ok) {
        const m = (data && data.error && data.error.message) || "";
        if (res.status === 401) errMsg("Kalit noto'g'ri yoki eskirgan — ⚙️ orqali yangisini kiriting.");
        else if (res.status === 429) errMsg("Limit to'ldi — bir-ikki daqiqadan keyin urinib ko'ring.");
        else errMsg("Xatolik: " + (m || res.status));
        messages.pop();
        return;
      }
      const reply = (data.content || []).filter(c => c.type === "text").map(c => c.text).join("\n").trim();
      messages.push({ role: "assistant", content: reply });
      aiMsg(reply || "…");
    } catch (e) {
      typing(false);
      errMsg("Tarmoq xatosi — internetni tekshirib, qayta urinib ko'ring.");
      messages.pop();
    } finally {
      busy = false; $("rpcSend").disabled = false;
    }
  }
})();

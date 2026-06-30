// ============================================================
//  RestoPulse — himoya (parol) + yagona navigatsiya
//  Bu fayl barcha sahifalarga ulanadi (kirish.html dan tashqari)
// ============================================================
(function () {
  // Parol hash'i (SHA-256). Parolni o'zgartirish: yangi parol hash'ini shu yerga qo'ying.
  const PAROL_HASH = "38f35912846eb95406aa8620795a68851541e0bd26e1969216ab22352b11f958";

  // --- 1. Himoya tekshiruvi ---
  if (sessionStorage.getItem("rp_auth") !== PAROL_HASH) {
    location.replace("kirish.html");
    return;
  }

  // --- 2. PWA service worker ---
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("sw.js").catch(() => {});
  }

  // --- 3. Pastki navigatsiya (ilova uslubida) ---
  function injectNav() {
    const here = location.pathname.split("/").pop() || "index.html";
    // iOS uslubidagi chiziqli SVG ikonkalar (currentColor — rangni CSS boshqaradi)
    const svg = (d) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">${d}</svg>`;
    const items = [
      { href: "index.html", icon: svg('<path d="M3 10.5L12 3l9 7.5"/><path d="M5 9.5V20a1 1 0 001 1h4v-6h4v6h4a1 1 0 001-1V9.5"/>'), label: "Bosh" },
      { href: "instagram_dashboard.html", icon: svg('<path d="M4 20V10"/><path d="M10 20V4"/><path d="M16 20v-7"/><path d="M22 20H2"/>'), label: "Statistika" },
      { href: "post_tahlil.html", icon: svg('<rect x="4" y="3" width="13" height="18" rx="2"/><path d="M8 8h5M8 12h3"/><circle cx="16.5" cy="15.5" r="3"/><path d="M19 18l2 2"/>'), label: "Tahlil" },
      { href: "kontent_reja.html", icon: svg('<rect x="3" y="5" width="18" height="16" rx="3"/><path d="M8 3v4M16 3v4M3 10h18"/><path d="M8 15h3"/>'), label: "Reja" },
      { href: "savdo.html", icon: svg('<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5v9M14.8 9.2c-.6-.9-1.7-1.4-2.8-1.4-1.6 0-2.8.9-2.8 2.1 0 2.9 5.6 1.5 5.6 4.3 0 1.2-1.2 2.1-2.8 2.1-1.2 0-2.3-.5-2.9-1.4"/>'), label: "Savdo" },
      { href: "jamoa.html", icon: svg('<rect x="5" y="8" width="14" height="11" rx="3"/><path d="M12 8V5M9 4.5h6"/><circle cx="9.5" cy="13" r="1.2"/><circle cx="14.5" cy="13" r="1.2"/><path d="M2 13h3M19 13h3"/>'), label: "Jamoa" },
    ];
    const exitIcon = svg('<path d="M14 8V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2h6a2 2 0 002-2v-2"/><path d="M9 12h11"/><path d="M17 9l3 3-3 3"/>');

    const css = document.createElement("style");
    css.textContent = `
      .rp-nav {
        position: fixed; bottom: 18px; left: 50%; transform: translateX(-50%);
        display: flex; gap: 3px; padding: 7px;
        max-width: calc(100vw - 20px); overflow-x: auto;
        scrollbar-width: none; -ms-overflow-style: none;
        background: rgba(26,17,34,0.72);
        backdrop-filter: blur(28px) saturate(1.5); -webkit-backdrop-filter: blur(28px) saturate(1.5);
        border: 1px solid rgba(255,255,255,0.14); border-radius: 24px;
        box-shadow: 0 16px 44px rgba(8,3,20,0.55), inset 0 1px 0 rgba(255,255,255,0.12); z-index: 90;
      }
      .rp-nav::-webkit-scrollbar { display: none; }
      .rp-nav a, .rp-nav button {
        display: flex; flex-direction: column; align-items: center; gap: 4px;
        min-width: 54px; padding: 8px 9px; border-radius: 16px;
        color: rgba(246,241,251,0.62); text-decoration: none; border: none;
        background: transparent; cursor: pointer; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', Inter, sans-serif;
        font-size: 10.5px; font-weight: 500; letter-spacing: .2px;
        transition: background .25s, color .25s;
        -webkit-tap-highlight-color: transparent; touch-action: manipulation;
      }
      .rp-nav .ni {
        width: 21px; height: 21px; display: block;
        transition: transform .45s cubic-bezier(.34,1.8,.4,1);
      }
      .rp-nav .ni svg { width: 100%; height: 100%; display: block; }
      .rp-nav a:hover, .rp-nav button:hover { background: rgba(255,255,255,0.08); color: rgba(246,241,251,0.95); }
      .rp-nav a:hover .ni, .rp-nav button:hover .ni { transform: translateY(-2px) scale(1.08); }
      .rp-nav a:active, .rp-nav button:active { transition: background .1s; }
      .rp-nav a:active .ni, .rp-nav button:active .ni {
        transform: scale(0.72); transition: transform .09s ease;
      }
      .rp-nav a.active {
        background: rgba(255,255,255,0.95); color: #1A1326; font-weight: 600;
        box-shadow: 0 4px 16px rgba(224,64,138,0.35);
      }
      .rp-nav a.active .ni { animation: rpPop .55s cubic-bezier(.34,1.9,.4,1) .05s both; }
      @keyframes rpPop {
        0% { transform: scale(0.6); }
        55% { transform: scale(1.22); }
        100% { transform: scale(1); }
      }
      @media (prefers-reduced-motion: reduce) {
        .rp-nav .ni { transition: none; }
        .rp-nav a.active .ni { animation: none; }
      }
      body { padding-bottom: 96px !important; }
      @media print { .rp-nav { display: none; } }
    `;
    document.head.appendChild(css);

    const nav = document.createElement("nav");
    nav.className = "rp-nav";
    nav.innerHTML = items.map(it =>
      `<a href="${it.href}" class="${here === it.href ? "active" : ""}"><span class="ni">${it.icon}</span>${it.label}</a>`
    ).join("") +
    `<button onclick="sessionStorage.removeItem('rp_auth');location.href='kirish.html'"><span class="ni">${exitIcon}</span>Chiqish</button>`;
    document.body.appendChild(nav);

    // iPhone'dagidek: bosilganda prujinali "siqilib-qaytish" effekti
    nav.querySelectorAll("a, button").forEach(el => {
      el.addEventListener("pointerdown", () => {
        const ic = el.querySelector(".ni");
        if (!ic) return;
        ic.style.transform = "scale(0.72)";
      });
      ["pointerup","pointerleave","pointercancel"].forEach(ev =>
        el.addEventListener(ev, () => {
          const ic = el.querySelector(".ni");
          if (ic) ic.style.transform = "";
        })
      );
    });
  }

  // --- 4. "Ma'lumot N kun eski" ogohlantirishi (jimgina to'xtab qolishni ushlaydi) ---
  //  instagram_data — kunlik yangilanadigan "yurak". 2+ kun eski bo'lsa qizil belgi chiqadi.
  const ESKI_LIMIT_KUN = 2;

  function rpParol() {
    const pw = sessionStorage.getItem("rp_pw");
    if (!pw) return null;
    try { return decodeURIComponent(escape(atob(pw))); } catch (e) { return null; }
  }

  async function rpDekript(blob, parol) {
    const b64 = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));
    const km = await crypto.subtle.importKey("raw", new TextEncoder().encode(parol), "PBKDF2", false, ["deriveKey"]);
    const key = await crypto.subtle.deriveKey(
      { name: "PBKDF2", salt: b64(blob.salt), iterations: 150000, hash: "SHA-256" },
      km, { name: "AES-GCM", length: 256 }, false, ["decrypt"]);
    const pt = await crypto.subtle.decrypt({ name: "AES-GCM", iv: b64(blob.iv) }, key, b64(blob.ct));
    return JSON.parse(new TextDecoder().decode(pt));
  }

  function rpEskiBelgi(matn) {
    const css = document.createElement("style");
    css.textContent = `
      .rp-eski {
        position: fixed; top: 12px; left: 50%; transform: translateX(-50%);
        display: flex; align-items: center; gap: 8px; max-width: 92vw;
        padding: 9px 16px; background: rgba(214,76,40,0.96); color: #fff;
        border-radius: 14px; z-index: 200;
        font: 600 13px -apple-system, BlinkMacSystemFont, 'SF Pro Text', Inter, sans-serif;
        box-shadow: 0 8px 28px rgba(180,50,20,0.45);
        animation: rpEskiIn .4s cubic-bezier(.34,1.6,.4,1);
      }
      .rp-eski svg { width: 18px; height: 18px; flex-shrink: 0; }
      @keyframes rpEskiIn { from { opacity:0; transform: translate(-50%,-10px); } to { opacity:1; transform: translate(-50%,0); } }
      @media print { .rp-eski { display: none; } }
    `;
    document.head.appendChild(css);
    const el = document.createElement("div");
    el.className = "rp-eski";
    el.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/></svg><span>${matn}</span>`;
    document.body.appendChild(el);
  }

  async function rpTozalik() {
    try {
      let data = null;
      const r = await fetch("instagram_data.enc.json?v=" + Date.now());
      if (r.ok) {
        const blob = await r.json();
        const parol = rpParol();
        if (blob && blob.ct && parol) data = await rpDekript(blob, parol);
      }
      if (!data) {   // ko'chish davri — eski ochiq fayl
        const r2 = await fetch("instagram_data.json?v=" + Date.now());
        if (r2.ok) data = await r2.json();
      }
      if (!Array.isArray(data) || !data.length) return;
      const oxirgi = data[data.length - 1].date;   // "YYYY-MM-DD"
      if (!oxirgi) return;
      const kun = Math.floor((Date.now() - new Date(oxirgi + "T00:00:00")) / 86400000);
      if (kun < ESKI_LIMIT_KUN) return;             // yangi — belgi yo'q
      rpEskiBelgi(`Ma'lumot ${kun} kun yangilanmagan (oxirgi: ${oxirgi})`);
    } catch (e) { /* xato bo'lsa jim — noto'g'ri ogohlantirish bermaymiz */ }
  }

  function rpBoshla() { injectNav(); rpTozalik(); }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", rpBoshla);
  } else {
    rpBoshla();
  }
})();

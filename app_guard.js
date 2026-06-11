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
    const items = [
      { href: "index.html", icon: "🏠", label: "Bosh" },
      { href: "instagram_dashboard.html", icon: "📊", label: "Statistika" },
      { href: "kontent_reja.html", icon: "📅", label: "Reja" },
      { href: "savdo.html", icon: "💰", label: "Savdo" },
    ];
    const css = document.createElement("style");
    css.textContent = `
      .rp-nav {
        position: fixed; bottom: 16px; left: 50%; transform: translateX(-50%);
        display: flex; gap: 4px; padding: 7px;
        background: rgba(42,26,62,0.82); backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border: 1px solid rgba(255,255,255,0.18); border-radius: 22px;
        box-shadow: 0 8px 30px rgba(20,5,40,0.45); z-index: 90;
      }
      .rp-nav a, .rp-nav button {
        display: flex; flex-direction: column; align-items: center; gap: 2px;
        min-width: 64px; padding: 7px 10px; border-radius: 15px;
        color: rgba(255,255,255,0.85); text-decoration: none; border: none;
        background: transparent; cursor: pointer; font-family: inherit;
        font-size: 10.5px; font-weight: 600; transition: background .2s;
      }
      .rp-nav a .ni, .rp-nav button .ni { font-size: 17px; }
      .rp-nav a:hover, .rp-nav button:hover { background: rgba(255,255,255,0.12); }
      .rp-nav a.active { background: rgba(255,255,255,0.92); color: #2a1a3e; }
      body { padding-bottom: 92px !important; }
      @media print { .rp-nav { display: none; } }
    `;
    document.head.appendChild(css);

    const nav = document.createElement("nav");
    nav.className = "rp-nav";
    nav.innerHTML = items.map(it =>
      `<a href="${it.href}" class="${here === it.href ? "active" : ""}"><span class="ni">${it.icon}</span>${it.label}</a>`
    ).join("") +
    `<button onclick="sessionStorage.removeItem('rp_auth');location.href='kirish.html'"><span class="ni">🚪</span>Chiqish</button>`;
    document.body.appendChild(nav);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", injectNav);
  } else {
    injectNav();
  }
})();

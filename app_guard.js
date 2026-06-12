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
        position: fixed; bottom: 18px; left: 50%; transform: translateX(-50%);
        display: flex; gap: 3px; padding: 7px;
        background: rgba(26,17,34,0.72);
        backdrop-filter: blur(28px) saturate(1.5); -webkit-backdrop-filter: blur(28px) saturate(1.5);
        border: 1px solid rgba(255,255,255,0.14); border-radius: 24px;
        box-shadow: 0 16px 44px rgba(8,3,20,0.55), inset 0 1px 0 rgba(255,255,255,0.12); z-index: 90;
      }
      .rp-nav a, .rp-nav button {
        display: flex; flex-direction: column; align-items: center; gap: 3px;
        min-width: 62px; padding: 8px 10px; border-radius: 16px;
        color: rgba(246,241,251,0.66); text-decoration: none; border: none;
        background: transparent; cursor: pointer; font-family: inherit;
        font-size: 10.5px; font-weight: 500; letter-spacing: .2px; transition: background .2s, color .2s;
      }
      .rp-nav a .ni, .rp-nav button .ni { font-size: 18px; }
      .rp-nav a:hover, .rp-nav button:hover { background: rgba(255,255,255,0.08); color: rgba(246,241,251,0.95); }
      .rp-nav a.active { background: rgba(255,255,255,0.95); color: #1A1326; font-weight: 600;
        box-shadow: 0 4px 16px rgba(224,64,138,0.35); }
      body { padding-bottom: 96px !important; }
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

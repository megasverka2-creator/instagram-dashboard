// ============================================================
// RestoPulse — umumiy shifr ochish (Web Crypto API)
// Kalit sayt parolidan olinadi (sessionStorage "rp_pw").
// Bu savdo.js dagi ishlaydigan kod bilan AYNAN bir xil —
// shu modulni har sahifaga ulab, shifrlangan JSON ochiladi.
// ============================================================
function getParol() {
  const pw = sessionStorage.getItem("rp_pw");
  if (!pw) return null;
  try { return decodeURIComponent(escape(atob(pw))); } catch (e) { return null; }
}
const _b64 = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));

// Kalitni paroldan olish (PBKDF2 — sekin amal, shuning uchun fayl bo'yicha BIR marta)
async function _kalit(parol, salt) {
  const km = await crypto.subtle.importKey("raw", new TextEncoder().encode(parol), "PBKDF2", false, ["deriveKey"]);
  return crypto.subtle.deriveKey(
    { name: "PBKDF2", salt, iterations: 150000, hash: "SHA-256" },
    km, { name: "AES-GCM", length: 256 }, false, ["decrypt"]);
}

async function dekript(blob, parol) {
  const key = await _kalit(parol, _b64(blob.salt));

  // v2 — har bir kun alohida shifrlangan (git uchun tejamkor format).
  // Kalit bitta, shuning uchun sekin PBKDF2 faqat bir marta ishlaydi.
  if (blob.v === 2 && Array.isArray(blob.kunlar)) {
    const kunlar = [];
    for (const ch of blob.kunlar) {
      const pt = await crypto.subtle.decrypt({ name: "AES-GCM", iv: _b64(ch.iv) }, key, _b64(ch.ct));
      kunlar.push(JSON.parse(new TextDecoder().decode(pt)));
    }
    return kunlar;
  }

  // v1 — butun fayl bitta blob (savdo va boshqa fayllar hali shu formatda)
  const pt = await crypto.subtle.decrypt({ name: "AES-GCM", iv: _b64(blob.iv) }, key, _b64(blob.ct));
  return JSON.parse(new TextDecoder().decode(pt));
}
// Faqat shifrlangan fayl ochiladi. Ochiq JSON'ga tushish (fallback)
// xavfsizlik sababli olib tashlangan — plainUrl argumenti eski
// chaqiruvlar buzilmasligi uchun saqlab qolingan, lekin ishlatilmaydi.
async function fetchEncrypted(encUrl, plainUrl) {
  try {
    const r = await fetch(encUrl + "?v=" + Date.now());
    if (r.ok) {
      const blob = await r.json();
      if (blob && (blob.ct || blob.kunlar)) {
        const parol = getParol();
        if (!parol) { location.replace("kirish.html"); return null; }
        return await dekript(blob, parol);
      }
    }
  } catch (e) {}
  return null;
}

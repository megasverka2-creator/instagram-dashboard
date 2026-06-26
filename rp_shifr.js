// ============================================================
//  RestoPulse — umumiy shifr ochish (Web Crypto API)
//  Kalit sayt parolidan olinadi (sessionStorage "rp_pw").
//  Bu savdo.js dagi ishlaydigan kod bilan AYNAN bir xil —
//  shu modulni har sahifaga ulab, shifrlangan JSON ochiladi.
// ============================================================
function getParol() {
  const pw = sessionStorage.getItem("rp_pw");
  if (!pw) return null;
  try { return decodeURIComponent(escape(atob(pw))); } catch (e) { return null; }
}

async function dekript(blob, parol) {
  const b64 = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));
  const km = await crypto.subtle.importKey("raw", new TextEncoder().encode(parol), "PBKDF2", false, ["deriveKey"]);
  const key = await crypto.subtle.deriveKey(
    { name: "PBKDF2", salt: b64(blob.salt), iterations: 150000, hash: "SHA-256" },
    km, { name: "AES-GCM", length: 256 }, false, ["decrypt"]);
  const pt = await crypto.subtle.decrypt({ name: "AES-GCM", iv: b64(blob.iv) }, key, b64(blob.ct));
  return JSON.parse(new TextDecoder().decode(pt));
}

// Shifrlangan faylni urinadi; topilmasa/ochiq bo'lsa — eski ochiq faylga tushadi (o'tish davri)
async function fetchEncrypted(encUrl, plainUrl) {
  try {
    const r = await fetch(encUrl + "?v=" + Date.now());
    if (r.ok) {
      const blob = await r.json();
      if (blob && blob.ct) {
        const parol = getParol();
        if (!parol) { location.replace("kirish.html"); return null; }
        return await dekript(blob, parol);
      }
    }
  } catch (e) {}
  try {
    const r = await fetch(plainUrl + "?v=" + Date.now());
    if (r.ok) return await r.json();
  } catch (e) {}
  return null;
}

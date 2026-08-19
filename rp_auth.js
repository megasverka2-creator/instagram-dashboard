// ============================================================
//  RestoPulse — kirish paroli tekshiruvi (umumiy modul)
//  kirish.html va app_guard.js shu fayldan foydalanadi.
// ============================================================
//
// NEGA BU FAYL BOR:
// Avval parol hash'i oddiy SHA-256 bilan olinardi. SHA-256 juda tez
// amal — oddiy kompyuter sekundiga milliardlab variantni sinab ko'radi.
// Hash esa saytda ochiq turadi, ya'ni parolni offline topib olish
// mumkin edi. Parol topilsa — barcha shifrlangan ma'lumot ochiladi.
//
// PBKDF2 sxemasida bitta variantni sinash 150 000 marta qimmatroq
// bo'ladi. Bu ma'lumot fayllarining o'z himoyasi bilan bir xil daraja,
// ya'ni "arzon yo'l" yopiladi.
//
// PASTDAGI IKKI QATORNI parol_almashtirish.py YANGILAYDI — qo'lda tegmang.
const RP_PAROL_SXEMA = "sha256";
const RP_PAROL_HASH  = "38f35912846eb95406aa8620795a68851541e0bd26e1969216ab22352b11f958";

// Salt ochiq bo'lishi normal — u faqat oldindan tayyorlangan
// jadvallardan (rainbow table) himoya qiladi.
const RP_PAROL_SALT = "restopulse-kirish-v2";
const RP_PAROL_ITER = 150000;

function _rpHex(buf) {
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, "0")).join("");
}

// Paroldan hash oladi — amaldagi sxemaga qarab.
async function rpParolHash(parol) {
  const enc = new TextEncoder();
  if (RP_PAROL_SXEMA === "pbkdf2") {
    const km = await crypto.subtle.importKey("raw", enc.encode(parol), "PBKDF2", false, ["deriveBits"]);
    const bits = await crypto.subtle.deriveBits(
      { name: "PBKDF2", salt: enc.encode(RP_PAROL_SALT), iterations: RP_PAROL_ITER, hash: "SHA-256" },
      km, 256);
    return _rpHex(bits);
  }
  return _rpHex(await crypto.subtle.digest("SHA-256", enc.encode(parol)));
}

// Kiritilgan parol to'g'rimi?
async function rpParolTogri(parol) {
  return (await rpParolHash(parol)) === RP_PAROL_HASH;
}

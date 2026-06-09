# GitHub'ga joylash — qadam-baqadam yo'riqnoma

Bu yo'riqnoma dashboard'ni internetga qo'yadi (havola) va skriptni har kuni
avtomatik ishga tushiradi. Hammasi bepul.

═══════════════════════════════════════════════════════════════
QISMLAR
═══════════════════════════════════════════════════════════════
1. Repozitoriya yaratish
2. Fayllarni yuklash
3. Token'ni xavfsiz saqlash (Secret)
4. Dashboard'ni internetga qo'yish (Pages)
5. Avtomatik yig'ishni yoqish (Actions)
6. Tekshirish

───────────────────────────────────────────────────────────────
0. AVVAL: skriptga ID'larni yozing
───────────────────────────────────────────────────────────────
`instagram_collector.py` ni oching va ACCOUNTS qismiga o'z
Instagram ID'laringizni yozing (token YO'Q — u Secret'dan keladi):

    ACCOUNTS = {
        "benison_uz": "17841455964894264",
        "dieto_uz":   "17841479699303953",
        "eddo_uz":    "17841461424798889",
    }

(ID'lar maxfiy emas, shuning uchun ular kodda qolishi mumkin.)

───────────────────────────────────────────────────────────────
1. REPOZITORIYA YARATISH
───────────────────────────────────────────────────────────────
1. github.com ga kiring
2. O'ng yuqorida "+" → "New repository"
3. Repository name: masalan `instagram-dashboard`
4. "Public" tanlang (Pages bepul ishlashi uchun)
5. "Create repository" bosing

───────────────────────────────────────────────────────────────
2. FAYLLARNI YUKLASH
───────────────────────────────────────────────────────────────
Bu papkadagi HAMMA narsani yuklang (.github papkasi bilan birga):
- instagram_dashboard.html
- instagram_collector.py
- .gitignore
- .github/workflows/collect.yml   ← bu eng muhimi, struktura saqlansin

Eng oson usul (saytdan):
1. Repozitoriya sahifasida "Add file" → "Upload files"
2. Fayllarni sudrab tashlang
   DIQQAT: .github/workflows/collect.yml ni yuklash uchun papka
   strukturasi saqlanishi kerak. Agar sayt orqali murakkab bo'lsa,
   pastdagi "Terminal orqali" usulini ishlating.
3. "Commit changes"

Terminal orqali (ishonchliroq):
    cd ~/Downloads/"mening dashportim"
    git init
    git add .
    git commit -m "Birinchi yuklash"
    git branch -M main
    git remote add origin https://github.com/FOYDALANUVCHI/instagram-dashboard.git
    git push -u origin main
(FOYDALANUVCHI — sizning GitHub useringiz)

───────────────────────────────────────────────────────────────
3. TOKEN'NI XAVFSIZ SAQLASH (Secret)
───────────────────────────────────────────────────────────────
Token kodga yozilmaydi — GitHub Secret'da yashirin saqlanadi:
1. Repozitoriya → "Settings" (yuqori menyu)
2. Chap menyu → "Secrets and variables" → "Actions"
3. "New repository secret"
4. Name: IG_ACCESS_TOKEN
5. Secret: 60 kunlik uzoq muddatli tokeningizni qo'ying
6. "Add secret"

───────────────────────────────────────────────────────────────
4. DASHBOARD'NI INTERNETGA QO'YISH (Pages)
───────────────────────────────────────────────────────────────
1. Repozitoriya → "Settings" → chap menyu "Pages"
2. "Source" → "Deploy from a branch"
3. Branch: "main", papka: "/ (root)" → "Save"
4. 1-2 daqiqa kuting. Havola paydo bo'ladi:
   https://FOYDALANUVCHI.github.io/instagram-dashboard/instagram_dashboard.html
5. Shu havolani rahbarlarga yuborasiz!

───────────────────────────────────────────────────────────────
5. AVTOMATIK YIG'ISHNI YOQISH (Actions)
───────────────────────────────────────────────────────────────
1. Repozitoriya → "Actions" (yuqori menyu)
2. Agar so'rasa — workflow'larni yoqing ("I understand... enable")
3. Chapda "Instagram ma'lumot yig'ish" workflow'ini ko'rasiz
4. Uni bosing → "Run workflow" → "Run workflow" (qo'lda sinab ko'rish)
5. Bir-ikki daqiqada ishlaydi. Yashil ✓ — muvaffaqiyat.

Bundan keyin u HAR KUNI o'zi ishlaydi (UTC 04:00 / Toshkent ~09:00).

───────────────────────────────────────────────────────────────
6. TEKSHIRISH
───────────────────────────────────────────────────────────────
- Actions yashil ✓ bo'lsa → ma'lumot yig'ildi
- instagram_data.json fayli yangilanadi (repozitoriyada ko'rinadi)
- Dashboard havolasini oching → haqiqiy raqamlar ko'rinadi
- Har kuni grafik boyib boradi

═══════════════════════════════════════════════════════════════
MUHIM ESLATMALAR
═══════════════════════════════════════════════════════════════
• Token ~60 kun amal qiladi. Tugashidan oldin yangilab,
  GitHub Secret (IG_ACCESS_TOKEN) ni yangilash kerak.
• Repozitoriya "Public" — lekin token Secret'da yashirin, ko'rinmaydi.
• Dashboard havolasi borlar ko'ra oladi. Maxfiy kerak bo'lsa,
  keyinroq parol/himoya qo'shish mumkin (alohida sozlanadi).

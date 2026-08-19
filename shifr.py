#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RestoPulse shifrlash moduli
============================
Savdo ma'lumotlarini AES-256-GCM bilan shifrlaydi.
Kalit sayt parolidan PBKDF2 orqali olinadi — parolni bilgan brauzer
(Web Crypto API) faylni ochadi, begona odam ocholmaydi.
"""

import json
import os
import base64
import hashlib

ITERATIONS = 150000


def _key(parol: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", parol.encode("utf-8"), salt, ITERATIONS, 32)


def encrypt_json(obj, parol: str) -> dict:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    salt, iv = os.urandom(16), os.urandom(12)
    key = _key(parol, salt)
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    ct = AESGCM(key).encrypt(iv, data, None)
    return {
        "v": 1,
        "salt": base64.b64encode(salt).decode(),
        "iv": base64.b64encode(iv).decode(),
        "ct": base64.b64encode(ct).decode(),
    }


def decrypt_json(blob: dict, parol: str):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    salt = base64.b64decode(blob["salt"])
    iv = base64.b64decode(blob["iv"])
    ct = base64.b64decode(blob["ct"])
    data = AESGCM(_key(parol, salt)).decrypt(iv, ct, None)
    return json.loads(data.decode("utf-8"))


def load_encrypted(path: str, parol: str):
    """Shifrlangan faylni o'qish. Topilmasa/ochilmasa None."""
    if not os.path.exists(path) or not parol:
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            blob = json.load(f)
        if blob.get("v") == 2:
            return decrypt_days(blob, parol)
        return decrypt_json(blob, parol)
    except Exception:
        return None


def save_encrypted(path: str, obj, parol: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(encrypt_json(obj, parol), f)


# =============================================================
#  v2 — "kunlar" formati (git uchun tejamkor)
# =============================================================
# Muammo: butun faylni har kuni qayta shifrlasak, tasodifiy salt/iv
# tufayli BITTA ham bayt bir xil qolmaydi va git har kuni faylning
# to'liq nusxasini saqlaydi (kuniga ~1.25 MB, yiliga ~0.5 GB).
#
# Yechim: kalit (salt) bitta bo'lib qoladi, lekin har bir kun ALOHIDA
# shifrlanadi. O'zgarmagan kunlarning shifrlangan baytlari aynan
# o'sha-o'sha qoladi — git faqat yangi kunni saqlaydi (~22 KB).
#
# Xavfsizlik: bitta fayl uchun bitta salt — bu oddiy amaliyot. Har bir
# kunning iv'si alohida tasodifiy, shuning uchun AES-GCM talabi buziladi
# emas. Ochiq qoladigan yagona narsa — kunlar sanasi (u allaqachon
# commit xabarlarida ko'rinadi).

def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode()


def _load_raw(path: str):
    """Faylni shifrini ochmasdan o'qish."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def decrypt_days(blob: dict, parol: str, kalit: str = "date"):
    """v2 formatdagi bloblarni ochib, kunlar ro'yxatini qaytaradi."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    aes = AESGCM(_key(parol, base64.b64decode(blob["salt"])))
    kunlar = []
    for ch in blob.get("kunlar", []):
        pt = aes.decrypt(base64.b64decode(ch["iv"]), base64.b64decode(ch["ct"]), None)
        kunlar.append(json.loads(pt.decode("utf-8")))
    return kunlar


def save_days_encrypted(path: str, kunlar, parol: str, kalit: str = "date"):
    """Kunlar ro'yxatini v2 formatda saqlaydi.

    O'zgarmagan kunlar uchun ESKI shifrlangan bo'lak qayta ishlatiladi —
    aynan shu narsa faylni git uchun barqaror qiladi.
    """
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    eski = _load_raw(path)
    salt = None
    mavjud = {}   # {sana: (ochiq_kun, eski_bolak)}

    if eski and eski.get("v") == 2 and eski.get("salt"):
        try:
            salt = base64.b64decode(eski["salt"])
            aes_eski = AESGCM(_key(parol, salt))
            for ch in eski.get("kunlar", []):
                try:
                    pt = aes_eski.decrypt(base64.b64decode(ch["iv"]),
                                          base64.b64decode(ch["ct"]), None)
                    mavjud[ch.get(kalit)] = (json.loads(pt.decode("utf-8")), ch)
                except Exception:
                    continue   # ochilmadi — bu kun qaytadan shifrlanadi
        except Exception:
            salt = None        # parol o'zgargan bo'lsa — hammasi qaytadan

    if salt is None:
        salt = os.urandom(16)
    aes = AESGCM(_key(parol, salt))

    bolaklar, yangi = [], 0
    for kun in kunlar:
        sana = kun.get(kalit)
        oldingi = mavjud.get(sana)
        if oldingi and oldingi[0] == kun:
            bolaklar.append(oldingi[1])       # o'zgarmagan — eski baytlar
            continue
        iv = os.urandom(12)
        data = json.dumps(kun, ensure_ascii=False, sort_keys=True).encode("utf-8")
        bolaklar.append({kalit: sana, "iv": _b64(iv),
                         "ct": _b64(aes.encrypt(iv, data, None))})
        yangi += 1

    with open(path, "w", encoding="utf-8") as f:
        json.dump({"v": 2, "salt": _b64(salt), "kunlar": bolaklar}, f)
    return yangi

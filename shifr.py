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
            return decrypt_json(json.load(f), parol)
    except Exception:
        return None


def save_encrypted(path: str, obj, parol: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(encrypt_json(obj, parol), f)

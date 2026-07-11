# -*- coding: utf-8 -*-
"""
Stop-list ma'lumoti (saytga) — yig'uvchi.
Postgres'dagi stop_kunlik va stop_sabablar jadvallaridan oxirgi 14 kunni oladi,
SAVDO_PAROL bilan shifrlab stop_tahlil.enc.json'ga yozadi.
Bu faylni marketolog bot va rp_analyst.js kontekst sifatida o'qiydi.

Jadval tuzilishiga bog'lanmaydi: ustunlarni o'zi aniqlaydi (information_schema),
shuning uchun stop-bot jadvalga ustun qo'shsa ham ishlayveradi.
"""

import datetime
import decimal
import json
import os
import sys

import psycopg2

from shifr import encrypt_json

DB_URL = os.environ["STOP_DATABASE_URL"]
PAROL = os.environ["SAVDO_PAROL"]
DAVR_KUN = 14          # necha kunlik tarix
MAX_QATOR = 3000       # fayl kattalashib ketmasligi uchun
CHIQISH = "stop_tahlil.enc.json"
JADVALLAR = ("stop_kunlik", "stop_sabablar")  # faqat shu ikkitasi (xavfsiz ro'yxat)

SANA_TIPLAR = (
    "date",
    "timestamp without time zone",
    "timestamp with time zone",
)


def _norm(v):
    """Postgres qiymatlarini JSON'ga mos holga keltirish."""
    if isinstance(v, (datetime.date, datetime.datetime, datetime.time)):
        return v.isoformat()
    if isinstance(v, decimal.Decimal):
        return float(v)
    return v


def jadval_oqish(cur, jadval: str):
    """Jadval ustunlarini aniqlab, oxirgi DAVR_KUN kunini o'qiydi."""
    cur.execute(
        """SELECT column_name, data_type FROM information_schema.columns
           WHERE table_name = %s ORDER BY ordinal_position""",
        (jadval,),
    )
    ustunlar = cur.fetchall()
    if not ustunlar:
        return None  # jadval yo'q

    nomlar = [u[0] for u in ustunlar]
    sana_ustuni = next((n for n, t in ustunlar if t in SANA_TIPLAR), None)

    if sana_ustuni:
        cur.execute(
            f'SELECT * FROM {jadval} WHERE "{sana_ustuni}"::date >= '
            f"CURRENT_DATE - %s ORDER BY \"{sana_ustuni}\" DESC LIMIT %s",
            (DAVR_KUN, MAX_QATOR),
        )
    else:
        cur.execute(f"SELECT * FROM {jadval} LIMIT %s", (MAX_QATOR,))

    qatorlar = [dict(zip(nomlar, (_norm(v) for v in r))) for r in cur.fetchall()]
    return {"sana_ustuni": sana_ustuni, "qatorlar": qatorlar}


def main():
    natija = {
        "yaratilgan": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "davr_kun": DAVR_KUN,
        "izoh": "Stop-bot Postgres bazasidan olingan tarix. Raqamlar taxminiy bo'lishi mumkin.",
    }

    with psycopg2.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            for jadval in JADVALLAR:
                data = jadval_oqish(cur, jadval)
                if data is None:
                    print(f"! Ogohlantirish: '{jadval}' jadvali topilmadi")
                    natija[jadval] = {"xato": "jadval topilmadi", "qatorlar": []}
                else:
                    natija[jadval] = data
                    print(
                        f"✓ {jadval}: {len(data['qatorlar'])} qator "
                        f"(sana ustuni: {data['sana_ustuni']})"
                    )

    if not natija.get("stop_kunlik", {}).get("qatorlar"):
        # Bo'sh baza — fayl baribir yoziladi (bot 404 emas, "hali ma'lumot yo'q" ko'radi),
        # lekin logda aniq ko'rinadi.
        print("! Diqqat: stop_kunlik bo'sh — bot 22:00 xulosasi hali yozmagan bo'lishi mumkin")

    with open(CHIQISH, "w", encoding="utf-8") as f:
        json.dump(encrypt_json(natija, PAROL), f, ensure_ascii=False)

    print(f"✓ {CHIQISH} yozildi")


if __name__ == "__main__":
    sys.exit(main())

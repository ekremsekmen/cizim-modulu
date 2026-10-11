"""Formdaki isteğe bağlı kat aralıkları (mm); toplamı seyirle aynı olmalı."""

import math

from cizim import izli
import re


def araliklar(ham, durak, seyir):
    if ham is None or (isinstance(ham, str) and not ham.strip()):
        return seyir * 1000.0 / (durak - 1), []
    if isinstance(ham, str):
        parcalar = re.split(r"[;\n]", ham.strip())
    elif isinstance(ham, (list, tuple)):
        parcalar = ham
    else:
        return None, ["Kat yükseklikleri: mm cinsinden, noktalı virgülle ayrılmış bir liste olmalı."]
    if len(parcalar) != durak - 1:
        return None, [
            f"Kat yükseklikleri: {durak:g} durak için {durak - 1:g} aralık girilmeli "
            f"( {len(parcalar)} girildi )."
        ]
    sonuc, hata = [], []
    for i, p in enumerate(parcalar):
        if isinstance(p, str):
            p = p.strip()
            if re.fullmatch(r"[+-]?[1-9]\d{0,2}[.,]\d{3}", p):
                hata.append(
                    f"{i + 1}. kat yüksekliği: belirsiz sayı yazımı {p!r}; "
                    "binlik ayracı kullanmayın ( örnek: 3400 )."
                )
                continue
            try:
                p = float(p.replace(",", "."))
            except ValueError:
                p = None
        if (
            not isinstance(p, (int, float))
            or isinstance(p, bool)
            or not math.isfinite(p)
            or p <= 0
            or p > 1e12
        ):
            hata.append(f"{i + 1}. kat yüksekliği: sıfırdan büyük, sonlu bir sayı olmalı.")
        else:
            sonuc.append(float(p))
    if hata:
        return None, hata
    toplam = izli.fsum(sonuc)
    if abs(toplam - seyir * 1000.0) > 0.5:
        return None, [
            f"Kat yükseklikleri toplamı {toplam:g} mm, seyir mesafesi "
            f"{seyir * 1000.0:g} mm — iki değer aynı olmalı."
        ]
    return sonuc, []

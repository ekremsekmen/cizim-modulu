# -*- coding: utf-8 -*-
"""
REFERANS TARAMASI ÜRETİCİ  —  TEST 1 ve TEST 10'un dondurulmuş sonuçları

    python3 dogrulama/tarama_uret.py        → iki dosyayı YENİDEN ÜRETİR

Yeniden üretmek DAVRANIŞI DEĞİŞTİRME İZNİDİR.  Refactor sırasında ASLA
çalıştırılmaz;  yalnız kasıtlı bir hesap değişikliğinden sonra, TEST 1 /
TEST 10'un gösterdiği farklar tek tek incelenip onaylandığında çalıştırılır.
( Altın çıktının kuralıyla aynı — bkz. altin_uret.py. )
"""

import gzip
import json
import os
import sys

#  Giriş noktası:  programın kökleri ( depo kökü, hesap/ ) — yollar.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import yollar

yollar.kur()

from dogrulama import test_avan_tarama
from dogrulama import test_mukavemet_tarama


def yaz(kayit, dosya):
    ham = json.dumps(kayit, ensure_ascii=False, sort_keys=True, indent=1)
    #  mtime=0:  aynı içerik aynı baytları üretsin ( yeniden üretim diff'i temiz )
    with open(dosya, "wb") as ham_dosya:
        with gzip.GzipFile(fileobj=ham_dosya, mode="wb", mtime=0) as f:
            f.write(ham.encode("utf-8"))
    adet = sum(len(v) for v in kayit.values())
    print(f"  {os.path.basename(dosya):28} {adet:4} senaryo  ·  {os.path.getsize(dosya) / 1024:5.0f} KB")


if __name__ == "__main__":
    yaz(test_avan_tarama.uret(), test_avan_tarama.DOSYA)
    yaz(test_mukavemet_tarama.uret(), test_mukavemet_tarama.DOSYA)

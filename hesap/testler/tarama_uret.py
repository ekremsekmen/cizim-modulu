# -*- coding: utf-8 -*-
"""
REFERANS TARAMASI ÜRETİCİ  —  TEST 1 ve TEST 10'un dondurulmuş sonuçları

    python3 testler/tarama_uret.py        → iki dosyayı YENİDEN ÜRETİR

Yeniden üretmek DAVRANIŞI DEĞİŞTİRME İZNİDİR.  Refactor sırasında ASLA
çalıştırılmaz;  yalnız kasıtlı bir hesap değişikliğinden sonra, TEST 1 /
TEST 10'un gösterdiği farklar tek tek incelenip onaylandığında çalıştırılır.
( Altın çıktının kuralıyla aynı — bkz. altin_uret.py. )
"""
import gzip
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from testler import test_avan_tarama as T1                        # noqa: E402
from testler import test_mukavemet_tarama as T10                  # noqa: E402


def yaz(kayit, dosya):
    ham = json.dumps(kayit, ensure_ascii=False, sort_keys=True, indent=1)
    #  mtime=0:  aynı içerik aynı baytları üretsin ( yeniden üretim diff'i temiz )
    with open(dosya, "wb") as ham_dosya:
        with gzip.GzipFile(fileobj=ham_dosya, mode="wb", mtime=0) as f:
            f.write(ham.encode("utf-8"))
    adet = sum(len(v) for v in kayit.values())
    print(f"  {os.path.basename(dosya):28} {adet:4} senaryo  ·  "
          f"{os.path.getsize(dosya) / 1024:5.0f} KB")


if __name__ == "__main__":
    yaz(T1.uret(), T1.DOSYA)
    yaz(T10.uret(), T10.DOSYA)

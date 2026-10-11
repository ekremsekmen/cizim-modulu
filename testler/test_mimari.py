"""MİMARİ — modüllerin adları ve birbirine erişimi ( araclar/mimari.py ).

Kurallar ( kod kalitesi 2. adım ):
  · Programın modülleri KENDİ adıyla import edilir:  from cizim import
    kuyu_dibi → kuyu_dibi.yerlesim( … ).  Takma ad yalnız gerçek bir ad
    çakışmasında ve açıklayıcı tam adla ( İSTİSNALAR ).
  · Her modülün adı programda tektir ( iki "girdi", iki "sabitler" … yok ).
  · Bir modül başka bir modülün import ettiği modüle onun içinden uzanmaz.
"""

import ast
import os
import unittest

from araclar import mimari

#  ( dosya , modül , takma ad ) — gerekçeli istisnalar
ISTISNALAR = {
    #  uygulama_sabitleri'nin kendi sabitler() fonksiyonu var
    ("hesap/motor/uygulama/uygulama_sabitleri.py", "cizim.sabitler", "cizim_sabitleri"),
}
#  Programın paketleri ( testler ve doğrulama paketi hariç )
PAKETLER = ("cizim", "tasarim", "araclar", "hesap/motor", "hesap/uclar", "hesap/ciktilar")


class Mimari(unittest.TestCase):
    def test_modul_takma_adi_yok(self):
        bulunan = set()
        for f in mimari.dosyalar():
            with open(os.path.join(mimari.KOK, f), encoding="utf-8") as d:
                t = ast.parse(d.read())
            for n in ast.walk(t):
                if isinstance(n, ast.ImportFrom) and n.module and not n.level:
                    for a in n.names:
                        tam = f"{n.module}.{a.name}"
                        if a.asname and mimari.modul_dosyasi(tam):
                            bulunan.add((f, tam, a.asname))
                elif isinstance(n, ast.Import):
                    for a in n.names:
                        if a.asname and mimari.modul_dosyasi(a.name):
                            bulunan.add((f, a.name, a.asname))
        self.assertEqual(bulunan, ISTISNALAR)

    def test_modul_adlari_tek(self):
        adlar = {}
        for p in PAKETLER:
            for kok, _alt, dosyalar in os.walk(os.path.join(mimari.KOK, p)):
                for d in dosyalar:
                    if d.endswith(".py") and d != "__init__.py":
                        adlar.setdefault(d[:-3], []).append(os.path.relpath(os.path.join(kok, d), mimari.KOK))
        for d in os.listdir(mimari.KOK):
            if d.endswith(".py"):
                adlar.setdefault(d[:-3], []).append(d)
        self.assertEqual({a: y for a, y in adlar.items() if len(y) > 1}, {})

    def test_baska_modulun_icinden_uzanilmaz(self):
        self.assertEqual(mimari.ihlaller(), [])


if __name__ == "__main__":
    unittest.main()

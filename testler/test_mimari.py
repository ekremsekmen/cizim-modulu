"""MİMARİ — modüllerin adları ve birbirine erişimi ( araclar/mimari.py ).

Kurallar ( kod kalitesi 2. adım ):
  · Programın modülleri KENDİ adıyla import edilir:  from cizim import
    kuyu_dibi → kuyu_dibi.yerlesim( … ).  Takma ad yalnız gerçek bir ad
    çakışmasında ve açıklayıcı tam adla ( İSTİSNALAR ).
  · Her modülün adı programda tektir ( iki "girdi", iki "sabitler" … yok ).
  · Bir modül başka bir modülün import ettiği modüle onun içinden uzanmaz.
  · Bir modül başka bir modülün özel ( alt çizgili ) adını kullanmaz:
    kullanılan ad arayüzdür ( kod kalitesi 3. adım ).
  · Adlar Türkçedir, Türkçe harfsiz yazılır ( aski, boslugun ).
  · Hiçbir fonksiyon 120 satırı ( UZUN_FONKSIYON ) aşmaz ( kod kalitesi 3. adım ):
    uzun iş yardımcılara ya da yöntem nesnesine bölünür.
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
#  Bir fonksiyonun en çok satırı ( yorumlar ve belge metni dahil )
UZUN_FONKSIYON = 120


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

    def test_modul_adi_golgelenmez(self):
        self.assertEqual(mimari.golgeler(), [])

    def test_baska_modulun_ozeli_kullanilmaz(self):
        self.assertEqual(mimari.ozel_erisimler(), [])

    def test_adlarda_turkce_harf_yok(self):
        self.assertEqual(mimari.ascii_disi_adlar(), [])

    def test_uzun_fonksiyon_yok(self):
        self.assertEqual(mimari.uzun_fonksiyonlar(UZUN_FONKSIYON), [])


class Katmanlar(unittest.TestCase):
    """temel → tasarim ( şema ) → cizim → motor ( hesap ) → ciktilar → uclar:
    bir katman yalnız altındakileri import eder;  modüller arasında döngü
    yok;  import fonksiyon içine saklanmaz ( döngüyü gizlemenin yolu oydu )."""

    @classmethod
    def setUpClass(cls):
        cls.graf, cls.fonksiyon_ici = mimari.bagimliliklar()

    def test_dongu_yok(self):
        self.assertEqual(mimari.donguler(self.graf), [])

    def test_katman_kurali(self):
        self.assertEqual(mimari.katman_ihlalleri(self.graf), [])

    def test_fonksiyon_ici_import_yok(self):
        #  Tek istisna:  ezdxf'in çizim eklentisi yalnız önizlemede gerekir ve
        #  ağırdır ( pafta.onizleme ) — program açılırken yüklenmez.
        self.assertEqual(
            sorted({(f, i.split(" import ")[0]) for f, _s, i in self.fonksiyon_ici}),
            [("cizim/pafta.py", "from ezdxf.addons.drawing"), ("cizim/pafta.py", "from ezdxf.entities")],
        )

    def test_kurallarin_kendisi(self):
        #  Kural yanlış bir şeyi geçirmesin:  üst katmana bağlanan, döngü kuran
        #  örnek graflar yakalanır.
        self.assertEqual(
            mimari.katman_ihlalleri({"cizim.a": {"motor.b"}, "motor.b": set()}), [("cizim.a", "motor.b")]
        )
        self.assertEqual(
            mimari.donguler({"cizim.a": {"cizim.b"}, "cizim.b": {"cizim.a"}}), [["cizim.a", "cizim.b"]]
        )
        self.assertEqual(
            mimari.katman_ihlalleri({"motor.ortak.ofis": {"motor.x"}, "motor.x": {"tasarim.alanlar"}}),
            [("motor.ortak.ofis", "tasarim.alanlar")],
        )


if __name__ == "__main__":
    unittest.main()

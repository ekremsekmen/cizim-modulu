"""OFİSİN GERÇEK PROJELERİ ( 5. adım ) — programın hükmü ve sebebi.

~/Desktop/örnekliftler'deki altı LiftDesigner projesi ( veri ve kaynak
satırları:  gercek_projeler.py ) programın kendi yolundan geçer:  formun
isteği → hesap → köprü → çizim ( api_cizimler ) ve hesap ( bölüm 11 ).

Kilitlenen ( kullanıcı kararı:  denetimler projeye uysun diye değiştirilmez,
program projeden farklı hükmediyorsa sebebi yazılır ):
  · çizim kuruluyor mu, kurulmuyorsa hangi maddeyle
  · bölüm 11 ( sığınma ve açıklıklar — yerleşimden ölçülür )
  · halat inişleri:  programın kendi geometrisinden çıkan ile projenin
    çiziminde okunan
Hesabın öbür bölümleri karşılaştırılmaz:  halat çapı ve adedi, motor gücü,
sarılma açısı LiftDesigner'ın veri bloğunda yok, varsayılanla hesaplanır.
"""
import json
import os
import sys
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _yol in (os.path.join(KOK, "hesap"), os.path.join(KOK, "testler")):
    if _yol not in sys.path:
        sys.path.append(_yol)

from api import cizim as UC                                # noqa: E402
from api import uygulama as UYG                            # noqa: E402
from cizim import geometri as CGE                          # noqa: E402
from cizim import girdi as CG                              # noqa: E402
from cizim import kopru as CK                              # noqa: E402
from cizim import kuyu_dibi as CKD                         # noqa: E402
from cizim import makine_dairesi as CMD                    # noqa: E402
from cizim import sabitler as CS                           # noqa: E402
from engine.uygulama import girdi as E_UGR                 # noqa: E402
from engine.uygulama import hesap as E_UYG                 # noqa: E402

import gercek_projeler as GP                               # noqa: E402

CIZILENLER = ("4815-6", "1022", "1275", "800 KG")


def _calistir(ad):
    """Projeyi formdan girilmiş gibi çalıştırır:  ( çizim ucu , çizim girdisi ,
    bölüm 11'in metni )."""
    a = dict(GP.PROJELER[ad])
    pg = {k: a.pop(k) for k in list(a) if k in UYG.PROJE_GENELI_ALANLAR}
    veri = {"asansorler": [a], "proje_geneli": pg, "sabitler": {}, "asansor": 0}
    cizim = json.loads(UC.api_cizimler(veri).body)
    ham, _i, proje = UC._istek(veri)
    g, _hata = CK.cizim_girdisi(E_UGR.tamamla(ham), None, proje, 1)
    s = E_UYG.hesapla(dict(ham))
    b11 = next(b for b in s["bolumler"] if b["kimlik"] == "siginma_alanlari")
    return cizim, g, b11["sonuc"]["metin"]


class GercekProjeler(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.S = {ad: _calistir(ad) for ad in GP.PROJELER}

    def test_cizilenler_uygun(self):
        """4815-6, 1022, 1275, 800 KG:  çizilir, bölüm 11 uygun."""
        for ad in CIZILENLER:
            cizim, _g, b11 = self.S[ad]
            with self.subTest(ad):
                self.assertTrue(cizim["aktif"], cizim.get("hata"))
                self.assertEqual(b11, "UYGUNDUR.")

    def test_12495_18_korkuluk(self):
        """12495-18 ( makine dairesiz, ağırlık arkada, 2:1 kabin üstü ) — ret:
        arkadaki 1,10 m korkuluğun küpeştesi makine kirişine 230 ( en az 300,
        m.5.2.5.7.2 c ).  LiftDesigner korkuluğu denetlemiyor;  kendi kesitinde
        kiriş 3.650'de, kabin tepesi 2.000 — onun ölçüleriyle de küpeşte kirişe
        275 kalır.  Son kat 4.270 olunca çizilir."""
        cizim, _g, b11 = self.S["12495-18"]
        self.assertFalse(cizim["aktif"])
        self.assertEqual(cizim["hata"],
                         ["Korkuluk – kuyu tavanı:  230 mm < 300 mm  ( TS EN 81-20 m.5.2.5.7.2 c )."])
        self.assertEqual(b11, "UYGUN DEĞİLDİR — Korkuluk / kuyu tavanının en alt kısmı "
                              "( makine şasesi )  ( 230 < 300 mm )")
        for son_kat, hata in ((4260, ["Korkuluk – kuyu tavanı:  290 mm < 300 mm  "
                                      "( TS EN 81-20 m.5.2.5.7.2 c )."]), (4270, None)):
            a = dict(GP.PROJELER["12495-18"], son_kat_yuksekligi=son_kat)
            pg = {k: a.pop(k) for k in list(a) if k in UYG.PROJE_GENELI_ALANLAR}
            d = json.loads(UC.api_cizimler({"asansorler": [a], "proje_geneli": pg,
                                            "sabitler": {}, "asansor": 0}).body)
            with self.subTest(son_kat=son_kat):
                self.assertEqual(d.get("hata"), hata)

    def test_1250_kg_son_kat_dusuk(self):
        """1250 KG ( makine dairesiz, 2:1 kabin altı, son kat 3.400 ) — ret:  kuyu
        tepesi yetmiyor.  LiftDesigner'ın kendi kesitinde de şasenin altı 2.550'de,
        üst paten en üst konumda ~2.615'e çıkıyor ( şaseyi 65 aşar )."""
        cizim, _g, b11 = self.S["1250 KG"]
        self.assertFalse(cizim["aktif"])
        self.assertEqual(cizim["hata"], [
            "Karşı ağırlık en üst konumunda makine şasesine çarpıyor:  tepesi 2765 mm, "
            "şasenin altı 2665 mm ( son kattan ).",
            "Sığınma yüksekliği:  915 mm < 1000 mm  ( TS EN 81-20 m.5.2.5.7.1 · Çizelge 3 ).",
            "Üst paten – kuyu tavanı:  50 mm < 100 mm  ( TS EN 81-20 m.5.2.5.7.2 b ).",
            "Korkuluk – kuyu tavanı:  -370 mm < 100 mm  ( TS EN 81-20 m.5.2.5.7.2 c ).",
            "Karşı ağırlık üst pateni – rayın üst ucu:  5 mm < 100 mm  ( TS EN 81-20 m.5.2.5.6.2 )."])
        self.assertTrue(b11.startswith("UYGUN DEĞİLDİR — Sığınma alanı / üstündeki en alt kısım "
                                       "( kuyu tavanı )  ( 915 < 1.000 mm )"))
        for parca in ("( 50 < 100 mm )", "( -370 < 100 mm )", "( 5 < 100 mm )",
                      "makine şasesine çarpıyor"):
            self.assertIn(parca, b11)

    def test_halat_inisleri_projeyle(self):
        """Programın geometrisinden çıkan halat inişleri, projenin kuyu planında
        okunan ( gercek_projeler.py ) ile:  2:1'de kabin kasnağının dış teğeti ya
        da tahrik kasnağının kabin inişi;  makine daireli 1:1'de döşeme delikleri."""
        def inisler(ad):
            g = self.S[ad][1]
            return [tuple(round(c) for c in p)
                    for p in CGE.halat_konumlari(g, CS.sabitler(g.get("_cizim_sabitleri")))]
        #  4815-6:  kabin halatı sol duvardan 415
        self.assertEqual(inisler("4815-6")[0][0], 415)
        #  12495-18 ve 1275:  tahrik kasnağının kabin inişi y 1.356 · 2.230
        self.assertEqual(inisler("12495-18")[0][1], 1356)
        self.assertEqual(inisler("1275")[0][1], 2230)
        #  1022 ve 800 KG:  ağırlığın deliği y 1.820 ( ikisinde de ) aynı;  kabininki
        #  10 önde ( 880 / 890 · 840 / 850 ) — LiftDesigner'ın kapı bölgesi 10 derin:
        #  kabinin iç önü onda 280, bizde 270, kabin halatı ray ekseninde
        for ad, kabin in (("1022", 880), ("800 KG", 840)):
            g = self.S[ad][1]
            d = {t: ((k[1] + k[3]) / 2.0) for t, k in CMD.yerlesim(g)["delikler"]
                 if t in ("KABİN", "AĞIRLIK")}
            with self.subTest(ad):
                self.assertEqual(d["AĞIRLIK"], 1820)
                self.assertEqual(d["KABİN"], kabin)
                self.assertEqual(g["kabin"]["on_pay"], 270)

    def test_1022_gergi_raya_sigar(self):
        """1022:  kabin rayları duvara 35 – 45 mm.  Gerçek gergiler kabin rayına
        bağlanır, duvara paralel ince bir dilimdedir ( ASPAR / Akşöz OSG kılavuzu:
        25 kg ağırlık 82 kalınlıkta );  ağırlık eskiden 160 × 160 sayıldığı için
        duvarı aşıyordu.  LiftDesigner regülatör halatını sol rayın yanında, ray
        ekseninin ~280 / 580 arkasında indiriyor;  program ( karşı ağırlığın
        karşısı ) sağ rayı seçer, 280'de kasnak en alttaki ray konsoluna değdiği
        için 360'a alır."""
        _c, g, _b = self.S["1022"]
        kd = g["kuyu_dibi"]
        self.assertEqual((kd["regulator_yan"], kd["regulator_kaciklik"]), ("Sağ", 360))
        Y = CKD.yerlesim(g)
        self.assertEqual(Y["hata"], [])
        k = Y["gergi_donanim"]["agirlik"]
        self.assertEqual(k[2] - k[0], 82)
        self.assertGreaterEqual(min(k[0], k[1], g["kuyu"]["genislik"] - k[2],
                                    g["kuyu"]["derinlik"] - k[3]), CG.ASGARI_ACIKLIK)


if __name__ == "__main__":
    unittest.main()

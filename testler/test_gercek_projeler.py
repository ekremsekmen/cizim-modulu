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
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from uclar import cizim_uclari
from cizim import geometri
from cizim import girdi
from cizim import kopru
from cizim import kuyu_dibi
from cizim import makine_dairesi
from cizim import sabitler
from motor.uygulama import uygulama_girdisi
from motor.uygulama import uygulama_hesabi

from testler import gercek_projeler
from uclar import uygulama_istegi

CIZILENLER = ("4815-6", "1022", "1275", "800 KG")


def _calistir(ad):
    """Projeyi formdan girilmiş gibi çalıştırır:  ( çizim ucu , çizim girdisi ,
    bölüm 11'in metni )."""
    a = dict(gercek_projeler.PROJELER[ad])
    pg = {k: a.pop(k) for k in list(a) if k in uygulama_istegi.PROJE_GENELI_ALANLAR}
    veri = {"asansorler": [a], "proje_geneli": pg, "sabitler": {}, "asansor": 0}
    cizim = json.loads(cizim_uclari.api_cizimler(veri).body)
    ham, _i, proje = cizim_uclari._istek(veri)
    g, _hata = kopru.cizim_girdisi(uygulama_girdisi.tamamla(ham), None, proje, 1)
    s = uygulama_hesabi.hesapla(dict(ham))
    b11 = next(b for b in s["bolumler"] if b["kimlik"] == "siginma_alanlari")
    return cizim, g, b11["sonuc"]["metin"]


class GercekProjeler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.S = {ad: _calistir(ad) for ad in gercek_projeler.PROJELER}

    def test_cizilenler_uygun(self):
        """4815-6, 1022, 1275, 800 KG:  çizilir, bölüm 11 uygun."""
        for ad in CIZILENLER:
            cizim, _g, b11 = self.S[ad]
            with self.subTest(ad):
                self.assertTrue(cizim["aktif"], cizim.get("hata"))
                self.assertEqual(b11, "UYGUNDUR.")

    def test_12495_18_kabin_ustu_siginma(self):
        """12495-18 ( makine dairesiz, ağırlık arkada, 2:1 kabin üstü çapraz ) — ret:
        1.100 × 1.100'lük tavanı kasnaklar arasındaki çapraz halat ( tavanın 80
        üstünde;  LiftDesigner'ın kesitinde de kasnaklar 2.080 – 2.320, tavan 2.000 )
        köşegen boyunca ikiye böler:  kenarları ~1.100 olan dik üçgene sığan en
        büyük dikdörtgen ~550 × 550, çömelme alanı 500 × 700 sığmaz ( ray
        ekseninden geçen şasenin üst kirişi de ayrıca böler ).  LiftDesigner
        kabin üstü planını çizmiyor.  10 Eki'ye dek halat engel sayılmıyordu,
        tek ret arkadaki 1,10 m korkuluğun makine kirişine 230 ( en az 300,
        m.5.2.5.7.2 c ) olmasıydı;  son kat 4.270 olunca çiziliyordu — artık son
        kat yetse de çizilmez."""
        cizim, _g, b11 = self.S["12495-18"]
        self.assertFalse(cizim["aktif"])
        self.assertEqual(len(cizim["hata"]), 1)
        self.assertIn("Kabin tavanında çömelme tipi sığınma alanına", cizim["hata"][0])
        self.assertIn("kasnaklar ve aralarındaki halat", cizim["hata"][0])
        self.assertTrue(b11.startswith("HESAP EKSİK — kuyunun çizimi kurulamadı:  Kabin tavanında"))
        for son_kat in (4260, 4270, 6000):
            a = dict(gercek_projeler.PROJELER["12495-18"], son_kat_yuksekligi=son_kat)
            pg = {k: a.pop(k) for k in list(a) if k in uygulama_istegi.PROJE_GENELI_ALANLAR}
            d = json.loads(
                cizim_uclari.api_cizimler(
                    {"asansorler": [a], "proje_geneli": pg, "sabitler": {}, "asansor": 0}
                ).body
            )
            with self.subTest(son_kat=son_kat):
                self.assertEqual(d.get("hata"), cizim["hata"])

    def test_1250_kg_son_kat_dusuk(self):
        """1250 KG ( makine dairesiz, 2:1 kabin altı, son kat 3.400 ) — ret:  kuyu
        tepesi yetmiyor.  LiftDesigner'ın kendi kesitinde de şasenin altı 2.550'de,
        üst kiriş en üst konumda ~2.615'e çıkıyor ( şaseyi 65 aşar );  üst paten
        onun da 100 üstünde ( 8 Eki:  patenler kirişlerin dışında — üst paten
        açıklığı 50'den −50'ye düştü, rayın ucu da yetmiyor ).  16 Eki:  hidrolik
        tamponun stroku boş — kuraldan 0,0674·v² = 68 mm ( eskiden 90 ):  kabinin
        en üst konumu 22 mm alçaldı, bütün açıklıklar 22 mm arttı, ret aynı."""
        cizim, _g, b11 = self.S["1250 KG"]
        self.assertFalse(cizim["aktif"])
        self.assertEqual(
            cizim["hata"],
            [
                "Karşı ağırlık en üst konumunda tavana çarpıyor:  karşı ağırlığın üst pateni tepesi "
                "2753 mm, üstündeki en alt tavan kısmı ( makine şasesi ) 2665 mm ( son kattan )  "
                "( ayrıca karşı ağırlık kasnağı ).",
                "Sığınma yüksekliği:  937 mm < 1000 mm  ( TS EN 81-20 m.5.2.5.7.1 · Çizelge 3 ).",
                "Üst paten – kuyu tavanı:  -28 mm < 100 mm  ( TS EN 81-20 m.5.2.5.7.2 b ).",
                "Üst paten – rayın üst ucu:  57 mm < 100 mm  ( TS EN 81-20 m.5.2.5.6.2 ).",
                "Korkuluk – kuyu tavanı:  -348 mm < 100 mm  ( TS EN 81-20 m.5.2.5.7.2 c ).",
                "Karşı ağırlık üst pateni – rayın üst ucu:  -3 mm < 100 mm  ( TS EN 81-20 m.5.2.5.6.2 ).",
            ],
        )
        self.assertTrue(
            b11.startswith(
                "UYGUN DEĞİLDİR — Sığınma alanı / üstündeki en alt kısım ( kuyu tavanı )  ( 937 < 1.000 mm )"
            )
        )
        for parca in (
            "( -28 < 100 mm )",
            "( -348 < 100 mm )",
            "( 57 < 100 mm )",
            "( -3 < 100 mm )",
            "tavana çarpıyor",
        ):
            self.assertIn(parca, b11)

    def test_halat_inisleri_projeyle(self):
        """Programın geometrisinden çıkan halat inişleri, projenin kuyu planında
        okunan ( gercek_projeler.py ) ile:  2:1'de kabin kasnağının dış teğeti ya
        da tahrik kasnağının kabin inişi;  makine daireli 1:1'de döşeme delikleri."""

        def inisler(ad):
            g = self.S[ad][1]
            return [
                tuple(round(c) for c in p)
                for p in geometri.halat_konumlari(g, sabitler.sabitler(g.get("_cizim_sabitleri")))
            ]

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
            d = {
                t: ((k[1] + k[3]) / 2.0)
                for t, k in makine_dairesi.yerlesim(g)["delikler"]
                if t in ("KABİN", "AĞIRLIK")
            }
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
        karşısı ) sağ rayı seçer, varsayılan 280'de.  ( 15 Eki'ye kadar 360'a
        alıyordu:  konsol plakası boşluktan geniş — 55 > 45 — çizilip rayın içine
        taşıyor, gergi o sahte parçaya "değiyordu".  Plaka artık boşluk kadar. )"""
        _c, g, _b = self.S["1022"]
        kd = g["kuyu_dibi"]
        self.assertEqual((kd["regulator_yan"], kd["regulator_kaciklik"]), ("Sağ", 280))
        Y = kuyu_dibi.yerlesim(g)
        self.assertEqual(Y["hata"], [])
        k = Y["gergi_donanim"]["agirlik"]
        self.assertEqual(k[2] - k[0], 82)
        self.assertGreaterEqual(
            min(k[0], k[1], g["kuyu"]["genislik"] - k[2], g["kuyu"]["derinlik"] - k[3]), girdi.ASGARI_ACIKLIK
        )


if __name__ == "__main__":
    unittest.main()

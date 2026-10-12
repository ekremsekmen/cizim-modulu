"""ÜSLUP — ekran ve AutoCAD AYNI görünür, yazılar ISO boylarında, DXF temiz
( cizim/uslup.py — 12 Eki ).

Ölçülenler ( kullanıcı:  "çizimlerimiz aşırı kaliteli olmalı" ):  33 katmanın
22'sinde ekran ile DXF'in kalınlığı farklıydı;  ölçü ucu ekranda dik çizgi,
AutoCAD'de eğik tikti;  13 ayrı yazı boyu vardı ( 1,45 … 4,34 mm );  yazının
eni harf × 0,6 sayılıyordu ( gerçeğinden −%6 … +%20 );  DXF'in ölçüleri elle
yazılmış metindi ve stillerinin DIMLFAC'ı 100'dü;  ezdxf'in kurulumu ve şablon
30'a yakın yazı stili getiriyordu ( AutoCAD 20'sini simplex.shx'e düşürüyordu ).
"""

import unittest
import xml.etree.ElementTree as ET

from araclar import harf_tablosu
from cizim import cizimler
from cizim import dxf
from cizim import eleman
from cizim import geometri
from cizim import harf_eni
from cizim import svg
from cizim import uslup
from testler.test_olcu_kaynagi import DUZENLER
from uclar import cizim_uclari

NS = "{http://www.w3.org/2000/svg}"


def _duzenlerin_cizimleri():
    """( düzen , çizim , ölçek , elemanlar ) — çizilen her düzenin her çizimi."""
    for ad_d, v in DUZENLER.items():
        ham, i, proje = cizim_uclari._istek(v())
        for ad, (_d, ciz, _b) in cizimler.CIZIMLER.items():
            kur, bilgi = cizim_uclari._kurucu(ham, ad, proje, i + 1)
            if kur({}) is None:
                continue
            yield ad_d, ad, cizimler.OLCEKLER.get(ad, 20), ciz(bilgi["g"])


class TekTablo(unittest.TestCase):
    """Ekran ( svg ) ve AutoCAD ( dxf ) aynı tablodan okur."""

    def test_her_katman_tabloda_ve_kalemler_iso_dizisinde(self):
        self.assertEqual(set(uslup.KATMAN), set(eleman.KATMANLAR))
        for ad, k in uslup.KATMAN.items():
            with self.subTest(ad):
                self.assertIn(k.kalinlik, uslup.KALEMLER)
                self.assertTrue(k.desen is None or k.desen in uslup.DESENLER)
        self.assertIn(uslup.INCE, uslup.KALEMLER)
        self.assertIn(uslup.TIK_KALEM, uslup.KALEMLER)

    def test_dxf_katmanlari_ve_ekran_kalemleri_tablodan(self):
        d = dxf.belge([eleman.cizgi("KUYU-DUVAR", 0, 0, 100, 0)])
        for ad, k in uslup.KATMAN.items():
            with self.subTest(ad):
                katman = d.layers.get(ad)
                self.assertEqual(katman.dxf.color, k.aci)
                self.assertEqual(katman.dxf.lineweight, round(k.kalinlik * 100))
                self.assertEqual(
                    katman.dxf.linetype, uslup.DESENLER[k.desen].dxf if k.desen else "Continuous"
                )
                self.assertEqual(svg.kalem(ad), (k.ekran, round(k.kalinlik * 20, 3)))

    def test_cizgi_deseni_ekranda_ve_dxfte_ayni(self):
        d = dxf.belge([eleman.cizgi("KUYU-DUVAR", 0, 0, 100, 0)])
        for ad, des in uslup.DESENLER.items():
            with self.subTest(ad):
                #  DXF:  AutoCAD'in ISO tanımı ( çizgi, boşluk, nokta )
                self.assertEqual(
                    d.linetypes.get(des.dxf).simplified_line_pattern(), tuple(map(abs, des.tanim))
                )
                #  ekran:  W100 tanımı × kâğıt çarpanı ( 1/20 birimi );  nokta NOKTA boyunda
                beklenen = [(abs(v) * des.olcek or uslup.NOKTA) * 20 for v in des.tanim]
                self.assertEqual([float(x) for x in svg.kesik(ad).split()], beklenen)
        #  Varlığın desen ölçeği:  tek başına DXF'te × ölçek, paftanın bloğunda kâğıtta
        for olcek in (20, 50):
            e = [eleman.cizgi("GIZLI", 0, 0, 1000, 0), eleman.cizgi("RAY", 0, 0, 10, 0, tip="eksen")]
            cizgi, eksen = dxf.belge(e, olcek=olcek).modelspace().query("LINE")
            self.assertEqual(cizgi.dxf.ltscale, uslup.DESENLER["GIZLI"].olcek * olcek)
            self.assertEqual(eksen.dxf.linetype, uslup.DESENLER["EKSEN"].dxf)

    def test_tarama_araligi_ekranda_ve_dxfte_ayni(self):
        for olcek in (20, 50):
            k = olcek / 20.0
            e = [
                eleman.dikdortgen("KUYU-DUVAR", 0, 0, 500, 500, tip="tarama"),
                eleman.dikdortgen("BINA", 0, 0, 500, 500, tip="tarama_tugla"),
            ]
            taramalar = dxf.belge(e, olcek=olcek).modelspace().query("HATCH")
            for h, tur in zip(taramalar, ("tarama", "tarama_tugla")):
                t = uslup.TARAMALAR[tur]
                self.assertEqual(h.dxf.pattern_name, t.dxf)
                #  kâğıtta sıra aralığı:  desenin temel aralığı × ölçeği / çizimin ölçeği
                self.assertAlmostEqual(t.temel * h.dxf.pattern_scale / olcek, t.aralik)
            r = ET.fromstring(svg.yaz(e, geometri.sinir(e), olcek=olcek))
            desen = {p.attrib["id"]: p for p in r.iter(NS + "pattern")}
            a, t = uslup.TARAMALAR["tarama"].aralik, uslup.TARAMALAR["tarama_tugla"].aralik
            self.assertAlmostEqual(float(desen["tarama"].attrib["width"]) * k / olcek, a)
            self.assertAlmostEqual(float(desen["tugla"].attrib["height"]) / 2 * k / olcek, t)


class Yazilar(unittest.TestCase):
    def test_harf_enleri_yazi_tipinin_kendisi(self):
        #  Tablo üretildiği yazı tipiyle aynı ( elle değiştirilmez );  Arial'le
        #  aynı enler:  "W" 0,944, rakam 0,556, "İ" 0,278 em
        self.assertEqual(harf_tablosu.enler(), harf_eni.EN)
        self.assertAlmostEqual(eleman.yazi_eni("W", 1.0), 1933 / 2048)
        self.assertAlmostEqual(eleman.yazi_eni("2100", 1.0), 4 * 1139 / 2048)
        self.assertAlmostEqual(eleman.yazi_eni("İ", 1.0), 569 / 2048)

    def test_butun_yazilar_iso_boyunda_ve_birbirine_binmez(self):
        boylar = {round(uslup.kagitta(h, 20), 2) for h in uslup.YAZI_SINIFLARI}
        self.assertEqual(boylar, {2.51, 3.51, 5.01})
        for ad_d, ad, olcek, e in _duzenlerin_cizimleri():
            with self.subTest(duzen=ad_d, cizim=ad):
                kutular = []
                for el in e:
                    if el["tip"] == "yazi":
                        h = el["yukseklik"]
                    elif el["tip"] == "olcu":
                        h = el["yazi"]["h"]
                    else:
                        continue
                    self.assertIn(round(uslup.kagitta(h, olcek), 2), boylar, el["metin"])
                    kutular.append((el["metin"], geometri.yazi_kutusu(el)))
                #  Gerçek enle:  hiçbir yazı bir başkasına binmez ( 0,5 mm pay )
                for i, (m, a) in enumerate(kutular):
                    for n, b in kutular[i + 1 :]:
                        binme = min(a[2], b[2]) - max(a[0], b[0]), min(a[3], b[3]) - max(a[1], b[1])
                        self.assertFalse(min(binme) > 0.5 * olcek, (m, n))

    def test_ekranda_gomulu_yazi_tipi_kerningsiz(self):
        s = svg.yaz([eleman.yazi(0, 0, "AV")], (0, 0, 100, 100))
        self.assertIn("font-family=\"CizimYazi, Arial, 'Liberation Sans', sans-serif\"", s)
        self.assertIn("font-kerning:none", s)


class Olculer(unittest.TestCase):
    def test_olculen_deger_autocadin(self):
        o = lambda metin, u: dxf.olcu_metni({"metin": metin, "uzunluk": u})
        self.assertEqual(o("KUYU GENİŞLİĞİ 2100", 2100.0), "KUYU GENİŞLİĞİ <>")
        self.assertEqual(o("1022,5", 1022.5), "<>")
        self.assertEqual(o("KAPI 900 x 2100", 900.0), "KAPI <> x 2100")
        #  Kırık kesit:  yazı ölçülen değil — olduğu gibi
        self.assertEqual(o("3 × 3000", 9190.0), "3 × 3000")
        self.assertEqual(o("ASKI KAÇIKLIĞI 69,5", 69.49999999), "ASKI KAÇIKLIĞI <>")

    def test_olcu_stili_ve_ezdxf_cizimi(self):
        for olcek in (20, 50):
            h = uslup.NORMAL * olcek / 20.0
            e = [
                eleman.olcu(
                    "yatay", (0, 0), (2100, 0), 500, "KUYU GENİŞLİĞİ 2100", yazi={"x": 1050, "y": 540, "h": h}
                ),
                eleman.olcu(
                    "dusey",
                    (0, 0),
                    (0, 1022.5),
                    -300,
                    "1022,5",
                    yazi={"x": -340, "y": 511, "aci": 90, "h": h},
                ),
            ]
            d = dxf.belge(e, olcek=olcek)
            stil = d.dimstyles.get(f"ASANSOR-{olcek}")
            for alan, deger in (
                ("dimscale", olcek),
                ("dimlfac", 1.0),
                ("dimdsep", ord(",")),
                ("dimblk", dxf.UC_BLOGU),
                ("dimtxsty", dxf.YAZI_TIPI),
                ("dimse1", 1),
                ("dimtfill", 1),
            ):
                self.assertEqual(stil.dxf.get(alan), deger, alan)
            for o in d.modelspace().query("DIMENSION"):
                self.assertEqual(o.dxf.dimstyle, stil.dxf.name)
                self.assertEqual(set(o.override().dimstyle_attribs) - {"dimtmove"}, set())
                yazi = [t.text for t in o.get_geometry_block() if t.dxftype() == "MTEXT"]
                self.assertIn(yazi, (["KUYU GENİŞLİĞİ 2100"], ["1022,5"]))

    def test_ucu_ekranda_ve_dxfte_ayni(self):
        #  DXF'in uç bloğu × DIMASZ:  eğik çizgi ±TIK, kısa uzatma çizgisi ±SAPLAMA ( kâğıtta mm )
        d = dxf.belge([eleman.olcu("yatay", (0, 0), (2100, 0), 500, "2100", yazi={"x": 1050, "y": 540})])
        asz = d.dimstyles.get("ASANSOR-20").dxf.dimasz
        tik, sap = d.blocks.get(dxf.UC_BLOGU).query("LINE")
        self.assertAlmostEqual(tik.dxf.end.x * asz, uslup.TIK)
        self.assertAlmostEqual(tik.dxf.end.y * asz, uslup.TIK)
        self.assertAlmostEqual(sap.dxf.end.y * asz, uslup.SAPLAMA)
        self.assertEqual(tik.dxf.lineweight, round(uslup.TIK_KALEM * 100))
        el = eleman.olcu("yatay", (0, 0), (2100, 0), 500, "2100", yazi={"x": 1050, "y": 540})
        r = ET.fromstring(svg.yaz([el], (0, 0, 2100, 600), olcek=20))
        cizgiler = [{k: float(v) for k, v in c.attrib.items() if k[0] in "xy"} for c in r.iter(NS + "line")]
        #  sol uç ( x = 0 ):  dik ±SAPLAMA ve eğik ±TIK — 1/20'de kâğıt mm × 20
        self.assertIn({"x1": 0, "y1": 500 - 30, "x2": 0, "y2": 500 + 30}, cizgiler)
        self.assertIn({"x1": -20, "y1": 500 - 20, "x2": 20, "y2": 500 + 20}, cizgiler)


class TemizDxf(unittest.TestCase):
    def test_tek_cizimin_dxfi_yalniz_kendi_stillerini_tasir(self):
        from ezdxf.audit import Auditor

        e = [
            eleman.olcu("yatay", (0, 0), (2100, 0), 500, "2100", yazi={"x": 1050, "y": 540}),
            eleman.yazi(0, 0, "KABİN"),
        ]
        d = dxf.belge(e, "PLAN", 20)
        self.assertEqual({s.dxf.name for s in d.styles}, {"Standard", dxf.YAZI_TIPI})
        self.assertEqual({s.dxf.name for s in d.dimstyles}, {"Standard", "ASANSOR-20"})
        self.assertEqual(
            {t.dxf.name for t in d.linetypes} - {"ByBlock", "ByLayer", "Continuous"},
            {des.dxf for des in uslup.DESENLER.values()},
        )
        a = Auditor(d)
        a.run()
        self.assertEqual(list(a.errors), [])


if __name__ == "__main__":
    unittest.main()

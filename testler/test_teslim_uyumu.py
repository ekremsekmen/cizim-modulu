"""TESLİM DOSYALARININ UYUMU  —  girdi ↔ çizim ( DXF ) ↔ hesap.

Denetçi programın içine bakmaz:  "Projeyi paketle"nin ZIP'ini açar, DXF'teki
ölçüleri ve yazıları okur, formun girdisiyle ve hesabın sonucuyla karşılaştırır.
Öteki testler çizimi programın eleman listesinden denetler;  burada bakılan
kullanıcıya giden dosyadır ( 16 Eki gerçek senaryo taraması:  49 düzen, 35
paket — bu dört düzen onun kalıcı parçası ).

Denetlenen:  VERİLER tablosu · kuyu planının ana ölçüleri · düşey kesitlerin
kuyu dibi, üst boşluk, kotları ve kapı yüksekliği · kuyu dibindeki bina
kuvvetleri · çizilen rayın boyu ( hesabın ray ağırlığına giren boy ) · plandan
kabin – karşı ağırlık açıklığı ( m.5.2.5.5.1 h ).
"""

import collections
import io
import json
import re
import unittest
import zipfile

import ezdxf
from ezdxf import bbox, disassemble

from testler import altin_cizim
from uclar import uygulama_istegi, uygulama_uclari

DUZENLER = ("1000 Sağ MRL", "1275 Sağ MD 1:1", "1275 Arka 2:1 MRL", "örnek makine daireli")


def _sayi(x):
    return None if x in (None, "") else float(str(x).replace(",", "."))


def _tr(m):
    return float(m.replace(".", "").replace(",", "."))


def _olculer(b):
    return {round(e.get_measurement(), 1) for e in b.query("DIMENSION")}


def _yazilar(b):
    return [e.text.replace("\\P", " ") for e in b.query("MTEXT")]


def _kirik_cevir(k):
    """Kesit kırıktır ( aradaki katlar çizilmez ):  çizimdeki y → gerçek kot."""
    kotlar = sorted(
        (_tr(m.group(2)) * (-1000 if m.group(1) == "-" else 1000), e.dxf.insert.y)
        for e in k.query("MTEXT")
        if (m := re.fullmatch(r"([+-]|±)(\d+,\d\d)", e.text))
    )
    kiriklar = [
        (y0, (k1 - k0) - (y1 - y0))
        for (k0, y0), (k1, y1) in zip(kotlar, kotlar[1:])
        if (k1 - k0) - (y1 - y0) > 50
    ]
    return lambda y: y + sum(e for y0, e in kiriklar if y > y0)


def _ray_boylari(k):
    cevir, gr = _kirik_cevir(k), collections.defaultdict(list)
    for e in disassemble.recursive_decompose(k):
        if e.dxf.layer == "RAY":
            kk = bbox.extents([e])
            gr[round(kk.extmin.x / 40)].append(kk)
    return [
        (cevir(max(x.extmax.y for x in ks)) - cevir(min(x.extmin.y for x in ks))) / 1000 for ks in gr.values()
    ]


class TeslimUyumu(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        alanlar = uygulama_istegi.alanlar()["gruplar"]
        cls.varsayilan = {f["anahtar"]: f["varsayilan"] for gr in alanlar for f in gr["alanlar"]}
        cls.S = {}
        for ad in DUZENLER:
            v = altin_cizim.duzenler()[ad]
            z = zipfile.ZipFile(io.BytesIO(uygulama_uclari.indir_uygulama_dwg(v).body))
            dxf = next(n for n in z.namelist() if n.endswith(".dxf"))
            doc = ezdxf.read(io.StringIO(z.read(dxf).decode("utf-8")))
            hesap = json.loads(uygulama_uclari.api_uygulama_coklu(v).body)["asansorler"][0]
            a = {**cls.varsayilan, **{k: x for k, x in v["asansorler"][0].items() if x not in (None, "")}}
            cls.S[ad] = (a, doc, hesap)

    def _blok(self, doc, ad):
        return next((b for b in doc.blocks if b.name.startswith(ad)), None)

    def test_veriler_tablosu(self):
        for ad, (a, doc, h) in self.S.items():
            ver = _yazilar(self._blok(doc, "CIZIM_VERILER"))
            cift = dict(zip(ver[1::2], ver[2::2]))
            g = h["girdi"]
            beklenen = {
                "Beyan yükü": f"{_sayi(a['beyan_yuku']):.0f} kg  ·  {h['ozet']['kabin_kisi']} kişi",
                "Beyan hızı": f"{_sayi(a['beyan_hizi']):.2f} m/s".replace(".", ","),
                "Durak  ·  seyir": f"{int(_sayi(a['durak_adedi']))} durak  ·  "
                f"{_sayi(a['seyir_mesafesi']) * 1000:.0f} mm",
                "Kuyu": f"SW × SD  {_sayi(a['kuyu_genisligi']):.0f} × {_sayi(a['kuyu_derinligi']):.0f}",
                "Kuyu dibi  ·  üst boşluk": f"{_sayi(a['kuyu_dibi']):.0f}  ·  OH{_sayi(a['son_kat_yuksekligi']):.0f}",
                "Halat": f"{g['halat_adedi']} × ø{g['halat_capi']:g}".replace(".", ","),
            }
            for k, b in beklenen.items():
                with self.subTest(ad, alan=k):
                    self.assertEqual(cift.get(k), b)
            with self.subTest(ad, alan="Kabin"):
                self.assertTrue(
                    cift["Kabin"].startswith(
                        f"CW × CD  {_sayi(a['kabin_genisligi']):.0f} × {_sayi(a['kabin_derinligi']):.0f}"
                    ),
                    cift["Kabin"],
                )

    def test_kuyu_plani_ana_olculer(self):
        for ad, (a, doc, h) in self.S.items():
            po = _olculer(self._blok(doc, "CIZIM_KUYU_PLANI"))
            g = h["girdi"]
            for alan in (
                "kuyu_genisligi",
                "kuyu_derinligi",
                "kabin_genisligi",
                "kabin_derinligi",
                "kapi_genisligi",
            ):
                with self.subTest(ad, alan=alan):
                    self.assertIn(round(_sayi(a[alan]), 1), po)
            #  DBG / DBGW hesaba girmez:  VERİLER'in yazdığı plandaki ölçüdür;  ray
            #  profilleri hesabınkiyle aynı
            ver = _yazilar(self._blok(doc, "CIZIM_VERILER"))
            cift = dict(zip(ver[1::2], ver[2::2]))
            for satir, profil, ara in (
                ("Kabin rayı", "kabin_ray_profili", "DBG"),
                ("Ağırlık rayı", "agirlik_ray_profili", "DBGW"),
            ):
                m = re.fullmatch(rf"(.+?)  ·  {ara}(\d+)", cift[satir])
                with self.subTest(ad, alan=ara):
                    self.assertIsNotNone(m, cift[satir])
                    self.assertEqual(m.group(1).replace(" × ", " x "), g[profil])
                    self.assertIn(float(m.group(2)), po)

    def test_dusey_kesitler(self):
        for ad, (a, doc, _h) in self.S.items():
            seyir, kd = _sayi(a["seyir_mesafesi"]), _sayi(a["kuyu_dibi"])
            hepsi = set()
            for kesit in ("CIZIM_KUYU_KESITI_YAN", "CIZIM_KUYU_KESITI_ON"):
                k = self._blok(doc, kesit)
                ko, ky = _olculer(k), " ".join(_yazilar(k))
                hepsi |= ko
                with self.subTest(ad, kesit=kesit):
                    self.assertIn(round(kd, 1), ko)
                    self.assertIn(round(_sayi(a["son_kat_yuksekligi"]), 1), ko)
                    self.assertIn(f"+{seyir:.2f}".replace(".", ","), ky)
                    self.assertIn(f"-{kd / 1000:.2f}".replace(".", ","), ky)
            hepsi |= _olculer(self._blok(doc, "CIZIM_KAPI_KESITI"))
            with self.subTest(ad, alan="kapı yüksekliği"):
                self.assertIn(round(_sayi(a["kapi_yuksekligi"]), 1), hepsi)

    def test_kuyu_dibi_kuvvetleri_hesapla_ayni(self):
        for ad, (_a, doc, h) in self.S.items():
            cizim = collections.defaultdict(set)
            for t in _yazilar(self._blok(doc, "CIZIM_KUYU_DIBI")):
                if m := re.fullmatch(r"(FKR|FAR|Fkt|Fat) = ([\d,]+) kN", t):
                    cizim[m.group(1)].add(_tr(m.group(2)))
            for k in ("FKR", "FAR", "Fkt", "Fat"):
                with self.subTest(ad, kuvvet=k):
                    self.assertEqual(cizim[k], {round(h["ozet"][k] / 1000, 2)})

    def test_cizilen_ray_hesabin_ray_boyu(self):
        for ad, (_a, doc, h) in self.S.items():
            boylar = []
            for kesit in ("CIZIM_KUYU_KESITI_YAN", "CIZIM_KUYU_KESITI_ON"):
                boylar += _ray_boylari(self._blok(doc, kesit))
            with self.subTest(ad):
                self.assertTrue(
                    any(abs(b - h["ozet"]["ray_boyu"]) < 0.011 for b in boylar), (boylar, h["ozet"])
                )

    def test_kabin_karsi_agirlik_acikligi(self):
        for ad, (_a, doc, _h) in self.S.items():
            es = list(disassemble.recursive_decompose(self._blok(doc, "CIZIM_KUYU_PLANI")))

            def kutu(katman, es=es):
                return bbox.extents([e for e in es if e.dxf.layer == katman and e.dxftype() != "MTEXT"])

            k, g = kutu("KABIN"), kutu("AGIRLIK")
            dx = max(g.extmin.x - k.extmax.x, k.extmin.x - g.extmax.x, 0)
            dy = max(g.extmin.y - k.extmax.y, k.extmin.y - g.extmax.y, 0)
            with self.subTest(ad):
                self.assertGreaterEqual(max(dx, dy), 50 - 0.5)


if __name__ == "__main__":
    unittest.main()

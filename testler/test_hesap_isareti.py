"""HESABIN UYGUN BULMADIĞI BÖLÜMLER ÇİZİMDE ( cizim/hesap_isareti.py — 1 Kas ).

· ekran:  çizim yanıtı uygun olmayan bölümlerin parçalarını ekrandaki
  adlarıyla taşır ( hesap_parcalari ) ve o adlar SVG'de vardır
· pafta:  her çizimin künyesinin altında not;  hesap uygunsa not yok;  not
  çerçeveyi genişletmez ( sarılır )
"""

import copy
import json
import re
import unittest

from cizim import eleman, geometri, hesap_isareti, pafta, parca_adlari, uslup
from motor.uygulama import uygulama_hesabi
from testler import test_grup, test_yerlesim_saglamligi
from uclar import uygulama_istegi


def _hesap(v):
    a, o = uygulama_istegi.asansor_girdileri(copy.deepcopy(v))
    return uygulama_hesabi.hesapla_coklu(a, o)["asansorler"][0]


def _bolum(kimlik, metin, uygun=False):
    return {"kimlik": kimlik, "ad": kimlik.upper(), "sonuc": {"metin": metin, "uygun": uygun}}


class BolumParcalari(unittest.TestCase):
    def test_parcalar_ekrandaki_adlarla_ve_bolumler_hesapta_var(self):
        bolumler = {
            b["kimlik"]
            for b in _hesap(test_yerlesim_saglamligi.standart_istek(800, False, "Sağ"))["bolumler"]
        }
        #  Ayırma kirişi yalnız tek kuyuda ( iki asansör )
        bolumler |= {b["kimlik"] for b in _hesap(test_grup.ikili())["bolumler"]}
        for kimlik, adlar in hesap_isareti.BOLUM_PARCALARI.items():
            self.assertIn(kimlik, bolumler)
            for a in adlar + hesap_isareti.DOLGU:
                self.assertIn(a, parca_adlari.ADLAR, f"{kimlik}:  {a} ekranda adsız")
        self.assertLessEqual(set(hesap_isareti.KISA_AD), bolumler | {"siginma_alanlari"})

    def test_dolgu_hukmunde_karsi_agirlik_isaretlenir(self):
        s = {
            "aktif": True,
            "bolumler": [
                _bolum("agirlik_raylari", "UYGUN DEĞİLDİR — karşı ağırlık dolgusu çerçeveye sığmıyor"),
                _bolum("kabin_raylari", "UYGUN DEĞİLDİR — sehim ( δ )"),
            ],
        }
        a, k = hesap_isareti.uygun_olmayanlar(s)
        self.assertIn("Karşı ağırlık dolgusu", a["parcalar"])
        self.assertIn("Karşı ağırlık", a["parcalar"])
        self.assertEqual(k["parcalar"], ["Kabin rayı", "Kabin rayı konsolu"])

    def test_eksik_hukum_ayri_uygunlar_ve_bilgi_yok(self):
        s = {
            "aktif": True,
            "bolumler": [
                _bolum("tahrik_yetenegi", "HESAP EKSİK — sarılma açısı α girilmedi"),
                _bolum("tamponlar", "UYGUN DEĞİLDİR — tampon tipi bu hıza uygun değil."),
                _bolum("motor_gucu", "UYGUNDUR.", uygun=True),
                _bolum("kuyu_tabani", "FKR = …", uygun=None),
            ],
        }
        liste = hesap_isareti.uygun_olmayanlar(s)
        self.assertEqual(
            [(b["kimlik"], b["eksik"]) for b in liste], [("tahrik_yetenegi", True), ("tamponlar", False)]
        )
        self.assertEqual(
            hesap_isareti.not_satirlari(liste),
            [
                "HESAP:  1 bölüm UYGUN DEĞİLDİR  ·  1 bölümün hesabı EKSİK  —  bkz. hesap raporu",
                "Tamponlar  ·  Tahrik yeteneği ( eksik )",
            ],
        )

    def test_hesap_yoksa_ya_da_durduysa_isaret_yok(self):
        self.assertEqual(hesap_isareti.uygun_olmayanlar(None), [])
        self.assertEqual(hesap_isareti.uygun_olmayanlar({"aktif": False, "hata": ["…"]}), [])
        self.assertEqual(hesap_isareti.not_satirlari([]), [])


class Ekran(unittest.TestCase):
    def test_yanit_uygun_olmayan_bolumlerin_parcalarini_tasir_svgde_var(self):
        """Standart 800 kg ( test varsayılanları:  6,5 mm halat, 4,9 kW ) hesabın
        uygun bulmadığı bölümler;  yanıttaki her ad SVG'de bir parçanın adı."""
        v = test_yerlesim_saglamligi.standart_istek(800, True, "Sağ")
        d = test_yerlesim_saglamligi.cizim_yaniti(copy.deepcopy(v))
        kalan = {b["kimlik"] for b in _hesap(v)["bolumler"] if (b.get("sonuc") or {}).get("uygun") is False}
        self.assertTrue(kalan)
        self.assertEqual(set(d["hesap_parcalari"]), kalan)
        svg = "".join(c["svg"] for c in d["cizimler"])
        adlar = set(re.findall(r'data-ad="([^"]+)"', svg))
        for kimlik, parcalar in d["hesap_parcalari"].items():
            self.assertTrue(parcalar, kimlik)
            self.assertTrue(set(parcalar) & adlar, f"{kimlik}:  {parcalar} çizimde yok")
        self.assertIn("HESAP:", svg)


class Pafta(unittest.TestCase):
    def _g(self, liste):
        g, _A, hata = test_yerlesim_saglamligi.duzen_girdisi(
            test_yerlesim_saglamligi.standart_istek(800, True, "Sağ")
        )
        self.assertFalse(hata)
        g["proje"]["hesap_uygun_degil"] = liste
        return g

    def test_her_cizimde_not_hesap_uygunsa_yok(self):
        uygun_degil = [
            {"kimlik": "tamponlar", "ad": "Tamponlar", "metin": "", "eksik": False, "parcalar": []},
        ]
        temiz = pafta.cizim_listesi(self._g([]))
        notlu = pafta.cizim_listesi(self._g(uygun_degil))
        self.assertEqual([c[0] for c in temiz], [c[0] for c in notlu])
        for (ad, _b, _o, e0), (_ad, _b2, _o2, e1) in zip(temiz, notlu):
            self.assertFalse([x for x in e0 if x.get("katman") == "UYARI"], ad)
            yazilar = [x["metin"] for x in e1 if x.get("katman") == "UYARI" and x["tip"] == "yazi"]
            self.assertIn("Tamponlar", yazilar, ad)
            #  Çizimin kendisi ( çerçeve dışı ) aynı
            govde = lambda e: [
                json.dumps(x, sort_keys=True) for x in e if x.get("katman") not in ("CERCEVE", "UYARI")
            ]
            self.assertEqual(govde(e0), govde(e1), ad)

    def test_uzun_not_cerceveyi_genisletmez_sarilir(self):
        e = [eleman.dikdortgen("KABIN", 0, 0, 2000, 1500)]
        uzun = hesap_isareti.not_satirlari(
            [
                {"kimlik": k, "ad": a, "metin": "", "eksik": False, "parcalar": []}
                for k, a in list(hesap_isareti.KISA_AD.items())[:8]
            ]
        )
        cerceve = lambda x: next(y for y in x if y.get("katman") == "CERCEVE" and y["tip"] == "dikdortgen")
        a = cerceve(geometri.cerceveli(e, "KUYU PLANI", 20))
        b = geometri.cerceveli(e, "KUYU PLANI", 20, uyari=uzun)
        self.assertAlmostEqual(cerceve(b)["g"], a["g"])
        satirlar = [x["metin"] for x in b if x.get("katman") == "UYARI" and x["tip"] == "yazi"]
        self.assertGreater(len(satirlar), len(uzun))
        for s in satirlar:
            self.assertLessEqual(eleman.yazi_eni(s, uslup.HARF), cerceve(b)["g"] - 240)


if __name__ == "__main__":
    unittest.main()

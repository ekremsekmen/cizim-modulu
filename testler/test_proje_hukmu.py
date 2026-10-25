"""PROJENİN GENEL HÜKMÜ ( uygulama_hesabi.proje_hukmu ) — açılış listesindeki durum.

24 Eki:  "Son projeler" listesi ekranda SEÇİLİ asansörün hükmünü yazıyordu
( ikinci asansör hesaplanamazken birinciye geçilince "Uygun" ), "hesap eksik"
ve proje geneli "uygun değil" ( topraklama ) de "Uygun" sayılıyordu — ön yüz
hükmü kendisi kuruyordu.  Hüküm artık motordan, asansörlerinkiyle aynı kuralla
( mukavemet.genel_hukum );  uç yanıta ekler, ekran yalnız basar.

Burada tek tek durumlar ve senaryoların hepsinde tutarlılık:  "uygun" ancak
sunucu bütün projeye uygun dediyse ( ozet.tumu_uygun ), "durdu" ancak
hesaplanamayan asansör varsa, tek asansörlü projede asansörün kendi hükmü.
"""

import json
import os
import re
import unittest

from cizim import istek_onbellegi
from dogrulama import altin_uret
from motor.uygulama import uygulama_hesabi
from uclar import uygulama_istegi
from uclar import uygulama_uclari

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#  Asansörün kısa hükmü → projenin durumu ( tek asansörde ikisi aynı olmalı )
KISA = {"UYGUN": "uygun", "UYGUN DEĞİL": "uygun_degil", "HESAP EKSİK": "eksik"}


def _ornek():
    """Örnek projenin asansörü — tek kaynağı ön yüzün ornek.ts'i ( gerçek BAR 2515 )."""
    metin = open(os.path.join(KOK, "on-yuz", "src", "lib", "ornek.ts"), encoding="utf-8").read()
    d = dict(re.findall(r'^\s+(\w+):\s*"([^"]*)",', metin.split("export const ORNEK_ASANSOR", 1)[1], re.M))
    assert len(d) > 20, d
    return d


ORNEK = _ornek()


def _hesap(asansorler, proje_geneli=None, sabitler=None):
    """Ön yüzün isteğiyle ( yazılan alanlar + ofis standardı ) çoklu hesap."""
    a, ortak = uygulama_istegi.asansor_girdileri(
        {"asansorler": asansorler, "proje_geneli": proje_geneli or {}, "sabitler": sabitler or {}}
    )
    with istek_onbellegi.etkin():
        return uygulama_hesabi.hesapla_coklu(a, ortak)


def _senaryolar():
    """Altın senaryolar ve örneğin hükmün her yoluna giden türevleri."""
    for g in altin_uret.uygulama_senaryolar():
        yield f"altın {g.get('bina_tipi') or ''}", altin_uret.uygulama_motoru(g)
    temel = {"temel_a": "2", "temel_b": "2"}
    yield "örnek", _hesap([ORNEK])
    yield "temel uzunluğu yalnız", _hesap([ORNEK], {"temel_a": "20"})
    yield "temel 20 × 15", _hesap([ORNEK], {"temel_a": "20", "temel_b": "15"})
    yield "topraklama uygun değil", _hesap([ORNEK], temel, {"beta": "5000"})
    yield "ikinci asansör dar kuyu", _hesap([ORNEK, {**ORNEK, "kuyu_genisligi": "1000"}])
    yield "birinci asansör dar kuyu", _hesap([{**ORNEK, "kuyu_genisligi": "1000"}, ORNEK])
    yield "iki asansör, biri uygun değil", _hesap([ORNEK, {**ORNEK, "kuyu_dibi": "1400"}], temel)
    for k, v in (("kuyu_dibi", "1200"), ("son_kat_yuksekligi", "3700"), ("kabin_derinligi", "2400")):
        yield f"{k} {v}", _hesap([{**ORNEK, k: v}])


class ProjeHukmu(unittest.TestCase):
    def test_ornek_uygun(self):
        s = _hesap([ORNEK])
        self.assertTrue(s["ozet"]["tumu_uygun"])
        self.assertEqual(uygulama_hesabi.proje_hukmu(s), {"durum": "uygun", "uygun_degil": 0})

    def test_hesaplanamayan_asansor_durdu(self):
        """Hangi asansör hesaplanamazsa hesaplanamasın proje durur ( seçili asansör yok )."""
        for liste in (
            [ORNEK, {**ORNEK, "kuyu_genisligi": "1000"}],
            [{**ORNEK, "kuyu_genisligi": "1000"}, ORNEK],
        ):
            s = _hesap(liste)
            self.assertTrue(s["aktif"])
            self.assertEqual(uygulama_hesabi.proje_hukmu(s), {"durum": "durdu", "uygun_degil": 0})

    def test_hesap_eksik_uygun_degil(self):
        """Yalnız temel uzunluğu:  topraklama yapılamaz — "uygun" değil, hesap eksik."""
        s = _hesap([ORNEK], {"temel_a": "20"})
        self.assertFalse(s["ozet"]["tumu_uygun"])
        self.assertEqual(uygulama_hesabi.proje_hukmu(s), {"durum": "eksik", "uygun_degil": 0})

    def test_proje_geneli_bolum_sayilir(self):
        """Topraklama ( proje geneli ) uygun değil:  asansörlerin bölümleri uygun olsa da."""
        s = _hesap([ORNEK], {"temel_a": "2", "temel_b": "2"}, {"beta": "5000"})
        self.assertFalse(s["ozet"]["proje_geneli_uygun"])
        self.assertEqual(uygulama_hesabi.proje_hukmu(s), {"durum": "uygun_degil", "uygun_degil": 1})

    def test_butun_senaryolarda_tutarli(self):
        goruldu = set()
        for ad, s in _senaryolar():
            with self.subTest(ad):
                h = uygulama_hesabi.proje_hukmu(s)
                goruldu.add(h["durum"])
                asansorler = s.get("asansorler") or []
                durdu = not s.get("aktif") or not all(a.get("aktif") for a in asansorler)
                self.assertEqual(h["durum"] == "durdu", durdu)
                if durdu:
                    continue
                self.assertEqual(h["durum"] == "uygun", bool(s["ozet"]["tumu_uygun"]))
                if h["durum"] == "eksik":
                    self.assertEqual(h["uygun_degil"], 0)
                    self.assertTrue(any(a["ozet"]["eksik_hesap"] for a in asansorler))
                if h["durum"] == "uygun_degil" and not h["uygun_degil"]:
                    #  bölümü kalmayan "uygun değil":  engelleyici uyarı
                    self.assertFalse(any(a["ozet"]["eksik_hesap"] for a in asansorler))
                if len(asansorler) == 1:
                    self.assertEqual(h["durum"], KISA[asansorler[0]["ozet"]["genel_sonuc_kisa"]])
        #  Senaryolar hükmün her yolundan geçer
        self.assertEqual(goruldu, {"uygun", "uygun_degil", "eksik", "durdu"})

    def test_uc_yanita_ekler(self):
        """Ekran hükmü uçtan okur ( on-yuz/src/lib/durum.ts uygulamaHukmu )."""
        yanit = uygulama_uclari.api_uygulama_coklu(
            {"asansorler": [ORNEK], "proje_geneli": {"temel_a": "20"}, "sabitler": {}}
        )
        self.assertEqual(json.loads(yanit.body)["ozet"]["proje_hukmu"], {"durum": "eksik", "uygun_degil": 0})


if __name__ == "__main__":
    unittest.main()

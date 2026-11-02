"""PROJENİN GENEL HÜKMÜ ( uygulama_hesabi · avan_hesabi · trafik .proje_hukmu ) —
açılış listesindeki durum.

24 Eki:  "Son projeler" listesi ekranda SEÇİLİ asansörün hükmünü yazıyordu
( ikinci asansör hesaplanamazken birinciye geçilince "Uygun" ), "hesap eksik"
ve proje geneli "uygun değil" ( topraklama ) de "Uygun" sayılıyordu — ön yüz
hükmü kendisi kuruyordu.  Hüküm artık motordan, asansörlerinkiyle aynı kuralla
( mukavemet.genel_hukum );  uç yanıta ekler, ekran yalnız basar.

Burada tek tek durumlar ve senaryoların hepsinde tutarlılık:  "uygun" ancak
sunucu bütün projeye uygun dediyse ( ozet.tumu_uygun ), "durdu" ancak
hesaplanamayan asansör varsa, tek asansörlü projede asansörün kendi hükmü.

25 Eki ( dış inceleme ):  avanın hükmü de ön yüzde kuruluyordu — temel ölçüleri
boş ( topraklama yapılamamış ) avan "Uygun" görünüyordu.  Avan ve trafik
hükmü de motordan;  avanın zorunlu hesapları paftanın bastıkları ( topraklama
hep, makine dairesi varsa aydınlatması ).
"""

import json
import os
import re
import unittest

from cizim import istek_onbellegi
from dogrulama import altin_uret
from motor.avan import avan_hesabi
from motor.avan import trafik
from motor.uygulama import uygulama_hesabi
from uclar import avan_uclari
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
    #  Örnek kotla girilir ( 2 Kas'tan beri yalnız kotla ):  kuyu dibi ve son kat kotlarla
    #  değişir — ölçüyle anahtarı ( kuyu_dibi … ) kotla girişte okunmaz, senaryo örneğin aynısı olurdu
    yield "iki asansör, biri uygun değil", _hesap([ORNEK, {**ORNEK, "kuyu_dibi_kotu": "-1,40"}], temel)
    for k, v in (("kuyu_dibi_kotu", "-1,20"), ("kuyu_tavani_kotu", "+45,70"), ("kabin_derinligi", "2400")):
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
        self.assertEqual(json.loads(yanit.body)["proje_hukmu"], {"durum": "eksik", "uygun_degil": 0})


# ------------------------------------------------------------------ avan projesi
#  Trafik:  konut, 10 kat — iki asansör verir ( avan_koprusu )
TRAFIK = {
    "bina_tipi": "Konut",
    "bina_yuksekligi": "30",
    "yapi_yuksekligi": "31",
    "N": "10",
    "h": "3",
    "hizli1": "20",
    "hizli2": "2",
    "ek_nufus": [],
    "taahhutname": "",
    "asansorler": [{"P": "8", "kapi_genisligi": "800", "kapi_tipi": "Teleskopik Otomatik"}],
}
KART = {"Hk": "34", "kuyu_genisligi": "1800", "kabin_boyu": "1400", "kabin_genisligi": "1100"}
MRL = {"mk_yok": True}
TEMEL = {"temel_a": "20", "temel_b": "15"}


def _yanit(uc, girdiler):
    return json.loads(uc({"girdiler": girdiler}).body)


def _avan(ortak, kartlar=None, sabitler=None):
    """Ön yüzün avan isteği ( AvanCalisma avanGirdi ):  kartlar trafiğin asansörlerine."""
    kopru = _yanit(avan_uclari.api_trafik, TRAFIK)["avan_koprusu"]
    kartlar = kartlar if kartlar is not None else [KART] * len(kopru["asansorler"])
    asansorler = [
        {
            **k,
            "aktif": True,
            "kapasite": str(x["P"]),
            "V": str(x["V"]),
            "makine_tipi": "Dişlisiz",
            "eta": "0.85",
        }
        for k, x in zip(kartlar, kopru["asansorler"])
    ]
    asansorler += [{"aktif": False}] * (4 - len(asansorler))
    return _yanit(
        avan_uclari.api_avan,
        {"ortak": ortak, "asansorler": asansorler, "sabitler": sabitler or {}, "trafik": kopru},
    )


def _avan_senaryolari():
    yield "temel boş", _avan(MRL)
    yield "temel 20 × 15", _avan({**MRL, **TEMEL})
    yield "topraklama uygun değil", _avan({**MRL, "temel_a": "2", "temel_b": "2"}, sabitler={"beta": "5000"})
    yield "makine dairesi ölçüsüz", _avan({"mk_yok": False, **TEMEL})
    yield (
        "makine dairesi ölçülü",
        _avan({"mk_yok": False, "mk_uzunluk": "4000", "mk_genislik": "3000", **TEMEL}),
    )
    yield "ikinci kart boş", _avan({**MRL, **TEMEL}, [KART, {}])


class AvanHukmu(unittest.TestCase):
    def test_topraklama_yapilamadiysa_eksik(self):
        """25 Eki:  temel ölçüleri boş avan listede "Uygun" görünüyordu."""
        y = _avan(MRL)
        self.assertFalse(y["topraklama"]["aktif"])
        self.assertEqual(y["proje_hukmu"]["durum"], "eksik")

    def test_makine_dairesi_varsa_aydinlatmasi_zorunlu(self):
        self.assertEqual(_avan({"mk_yok": False, **TEMEL})["proje_hukmu"]["durum"], "eksik")
        #  MRL'de uygulanmaz:  eksik sayılmaz
        self.assertNotEqual(_avan({**MRL, **TEMEL})["proje_hukmu"]["durum"], "eksik")

    def test_karti_bos_asansor_durdu(self):
        self.assertEqual(
            _avan({**MRL, **TEMEL}, [KART, {}])["proje_hukmu"], {"durum": "durdu", "uygun_degil": 0}
        )

    def test_topraklama_uygun_degil_sayilir(self):
        h = _avan({**MRL, "temel_a": "2", "temel_b": "2"}, sabitler={"beta": "5000"})["proje_hukmu"]
        self.assertEqual(h["durum"], "uygun_degil")
        self.assertGreaterEqual(h["uygun_degil"], 1)

    def test_butun_senaryolarda_tutarli(self):
        goruldu = set()
        for ad, y in _avan_senaryolari():
            with self.subTest(ad):
                h = y["proje_hukmu"]
                goruldu.add(h["durum"])
                self.assertEqual(h, avan_hesabi.proje_hukmu(y))
                if h["durum"] in ("uygun", "uygun_degil") and not h["uygun_degil"]:
                    mk = y.get("makine_dairesi") or {}
                    #  Zorunlu hesapların hepsi yapılmış
                    self.assertTrue(y["topraklama"]["aktif"])
                    self.assertTrue(mk.get("aktif") or mk.get("mk_yok"))
                if h["durum"] == "uygun":
                    self.assertFalse(y.get("engelleyici"))
                    bolumler = [b for a in y["asansorler"] for b in a.get("bolumler") or []]
                    self.assertFalse(any((b.get("sonuc") or {}).get("uygun") is False for b in bolumler))
        self.assertEqual(goruldu, {"uygun", "uygun_degil", "eksik", "durdu"})

    def test_trafik_hukmu(self):
        self.assertEqual(
            _yanit(avan_uclari.api_trafik, {})["proje_hukmu"], {"durum": "durdu", "uygun_degil": 0}
        )
        y = _yanit(avan_uclari.api_trafik, TRAFIK)
        self.assertEqual(y["proje_hukmu"], trafik.proje_hukmu(y))
        self.assertEqual(y["proje_hukmu"]["durum"], "uygun")
        #  Karar ölçütü sağlanmıyorsa uygun değil
        kalan = dict(y, ozet={**y["ozet"], "karar_olcutleri": [{"ad": "Bekleme", "uygun": False}]})
        self.assertEqual(trafik.proje_hukmu(kalan)["durum"], "uygun_degil")


if __name__ == "__main__":
    unittest.main()

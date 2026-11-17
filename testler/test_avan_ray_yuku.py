"""AVAN HESABINDA RAYA BİNEN YÜK VE AVAN PAFTASININ KUVVETLERİ ( 17 Kas 2026 ).

Kullanıcı:  "avanda da çizimle hesapların tutarlılığı kesinlikle doğru mu" — değildi:
  · avan hesap belgesi kuyu tabanı kuvvetlerini MMO/697'den yazıyor, makine dairesizde
    raylara binen makine ve kabin halat bağlantısı yükünü saymıyordu ( ağırlık rayı 3,6 kN;
    uygulama hesabı aynı rayda 22 – 28 kN );
  · avan paftası aynı kuvvetleri seçicinin hazır asansörünün uygulama hesabından yazıyordu —
    belge ile pafta farklı sayı söylüyordu.
Düzeltme:  avan hesabı TS EN 81-20 m.5.2.1.8.4 ' ün raya bağlı yükünü ( k3 · MY ) katar
( motor/avan/avan_hesabi._kuvvetler );  avan paftası kuvvetleri avanın hesabından yazar
( uclar/avan_cizimi.avan_kuvvetleri ), ray konsolu yükleri ( Fx / Fy ) avanda yazılmaz."""

import json
import math
import re
import unittest

from motor.avan import avan_hesabi
from motor.uygulama import uygulama_sabitleri
from uclar import avan_cizim_uclari, avan_cizimi, avan_secici, avan_uclari

KISI = {800: "10", 630: "8", 1000: "13"}


def govde(yuk, mk_yok, **degisen):
    """Hazır asansörün kendi kuyusu ve kabiniyle avan kartı ( avan hesabı da tam )."""
    T = avan_secici.paketler()[(yuk, mk_yok)]
    a = T["asansor"]
    kart = {
        "kapasite": KISI[yuk],
        "V": str(a["beyan_hizi"]).replace(".", ","),
        "eta": "0,85",
        "kabin_boyu": a["kabin_derinligi"],
        "kabin_genisligi": a["kabin_genisligi"],
        **{k: a[k] for k in ("kuyu_genisligi", "kuyu_derinligi", "durak_kotlari", "kuyu_dibi_kotu")},
        "kuyu_tavani_kotu": a["kuyu_tavani_kotu"],
    }
    if not mk_yok:
        kart["md_zemini_kotu"] = a["md_zemini_kotu"]
    kart.update(degisen)
    ortak = {"mk_yok": mk_yok}
    if not mk_yok:
        ortak.update({k: v for k, v in T["proje_geneli"].items() if k != "mk_yok"})
    return {"girdiler": {"ortak": ortak, "asansorler": [kart], "sabitler": {}}, "asansor": 0}


def avan(g):
    girdi, hata = avan_uclari.avan_girdisi(g)
    assert not hata, hata
    s = avan_hesabi.hesapla(girdi)
    return s, s["ozet"]["asansorler"][0]


def tavan10(x):
    return math.ceil(round(x, 6) / 10.0) * 10


def pafta_kuvvetleri(g):
    r = json.loads(avan_cizim_uclari.api_avan_cizimler(g).body)
    assert r["durum"] == "uygun", r
    yazilar = {
        re.sub(r"<[^>]+>", "", x).strip()
        for c in r["cizim"]["cizimler"]
        for x in re.findall(r"<text[^>]*>(.*?)</text>", c["svg"], flags=re.S)
    }
    return r, yazilar


class RayaBinenYuk(unittest.TestCase):
    def test_k3_uygulamayla_ayni(self):
        """k3 ofis sabitidir:  avan uygulamanınkini kullanır ( içe aktaramaz — döngü )."""
        self.assertEqual(avan_hesabi.K3_YARDIMCI, uygulama_sabitleri.VARSAYILAN["k3_yardimci"])

    def test_makine_dairesiz_elle_hesap(self):
        """1000 kg makine dairesiz 2:1:  PR ve PK formülü elle yeniden kurulur."""
        s, oz = avan(govde(1000, True))
        gn, k3, i = 9.81, 2, oz["i_palanga"]
        self.assertEqual(i, 2)
        Gh = oz["mz"] if oz["mz"] is not None else None
        #  Gh:  zincir kabulü ( zincir = halat ağırlığı ) — mz · Hk;  zincir yokken özette mz yok,
        #  ofisin değeri sabitlerden
        S = avan_hesabi.sabitler()
        mz = S["zincir_birim_kutle"] if Gh is None else Gh
        P, Q, Ga, Hk = oz["P"], oz["Q"], oz["Ga"], oz["Hk"]
        MY_k = gn * (P + Q + mz * Hk) / i
        MY_a = gn * (S["Fmk"] + S["Fsh"] + Ga / i)
        self.assertAlmostEqual(oz["MY_k"], MY_k, places=6)
        self.assertAlmostEqual(oz["MY_a"], MY_a, places=6)
        n, k1, Mg = 2, oz["k1"], oz["Mg"]
        self.assertEqual(oz["PR"], tavan10(k1 * gn * (P + Q) / n + Mg * gn + k3 * MY_k))
        #  Karşı ağırlıkta güvenlik tertibatı yok:  k1 = 0
        self.assertEqual(oz["PK"], tavan10(Mg * gn + k3 * MY_a))
        #  Uygulama hesabının bulduğu büyüklükte ( eskiden 3,6 kN )
        self.assertGreater(oz["PK"], 20_000)
        #  Belgede satırları kaynağıyla
        b = next(x for x in s["asansorler"][0]["bolumler"] if x.get("kimlik") == "avan_kuvvetler")
        formuller = [a.get("formul") or "" for a in b["adimlar"]]
        self.assertTrue(any(f.startswith("MYk") for f in formuller), formuller)
        self.assertTrue(any(f.startswith("MYa") for f in formuller), formuller)
        self.assertTrue(any(f.startswith("PR") and "k3 · MYk" in f for f in formuller), formuller)
        self.assertTrue(any(f.startswith("PK") and "k3 · MYa" in f for f in formuller), formuller)

    def test_makine_dairesiz_bire_bir(self):
        """1:1 askı:  kabin halat bağlantısı kabinin üstündedir ( raya binmez );  makine raylarda."""
        _s, oz = avan(govde(1000, True, i_palanga="1"))
        S = avan_hesabi.sabitler()
        self.assertEqual(oz["MY_k"], 0.0)
        self.assertAlmostEqual(oz["MY_a"], 9.81 * (S["Fmk"] + S["Fsh"]), places=6)

    def test_makine_daireli_degismez(self):
        """Makine dairesinde makine binaya oturur:  terim yok, MMO/697'nin formülü aynen."""
        s, oz = avan(govde(800, False))
        self.assertEqual((oz["MY_k"], oz["MY_a"]), (0.0, 0.0))
        gn, P, Q, n = 9.81, oz["P"], oz["Q"], 2
        self.assertEqual(oz["PR"], tavan10(oz["k1"] * gn * (P + Q) / n + oz["Mg"] * gn))
        self.assertEqual(oz["PK"], tavan10(oz["Mg"] * gn))
        b = next(x for x in s["asansorler"][0]["bolumler"] if x.get("kimlik") == "avan_kuvvetler")
        self.assertFalse(any((a.get("formul") or "").startswith("MY") for a in b["adimlar"]))

    def test_makine_dairesiz_kurali(self):
        """Kutu gönderilmişse o;  gönderilmemişse ( eski dosya ) ölçü yoksa makine dairesiz."""
        mrl = avan_hesabi.makine_dairesiz_mi
        self.assertTrue(mrl({"mk_yok": True}))
        self.assertFalse(mrl({"mk_yok": "false", "mk_uzunluk": 4100, "mk_genislik": 2600}))
        self.assertTrue(mrl({}))
        self.assertFalse(mrl({"mk_uzunluk": 4100, "mk_genislik": 2600}))


class AvanPaftasininKuvvetleri(unittest.TestCase):
    """Avan paftası kuyu tabanı kuvvetlerini hesap belgesindeki sayıyla yazar."""

    def setUp(self):
        avan_secici._ONBELLEK.clear()

    def test_belge_ile_pafta_ayni(self):
        for yuk, mk_yok in ((630, True), (1000, True), (800, False)):
            with self.subTest(yuk=yuk, mk_yok=mk_yok):
                g = govde(yuk, mk_yok)
                _s, oz = avan(g)
                r, yazilar = pafta_kuvvetleri(g)
                self.assertEqual(
                    r["avan"]["kuvvetler"],
                    {"FKR": oz["PR"], "FAR": oz["PK"], "Fkt": oz["P1"], "Fat": oz["P2"]},
                )
                for ad, k in avan_cizimi.AVAN_KUVVETLERI.items():
                    metin = f"{ad} = {oz[k] / 1000:.2f} kN".replace(".", ",")
                    self.assertIn(metin, yazilar)
                #  Ray konsolu yükleri ( ray profiline bağlı ) avanda yok
                self.assertFalse([y for y in yazilar if "Fx =" in y or "RAY KONSOLUNA" in y])

    def test_avan_hesabi_yoksa_yalniz_adlar(self):
        self.assertIsNone(avan_cizimi.avan_kuvvetleri(None))
        self.assertIsNone(avan_cizimi.avan_kuvvetleri({"PR": 1, "PK": 1, "P1": 1}))
        self.assertEqual(
            avan_cizimi.avan_kuvvetleri({"PR": 1, "PK": 2, "P1": 3, "P2": 4}),
            {"FKR": 1, "FAR": 2, "Fkt": 3, "Fat": 4},
        )


if __name__ == "__main__":
    unittest.main()

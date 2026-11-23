"""VARSAYILAN YERLEŞİMİN KURTARILMASI ( 23 Kas ) — kabinin yana kaçıklığı ve kat
kapısının kaçıklığı BOŞKEN varsayılan yerleşim ( kabin kuyunun, kapı kabinin ortasında )
planda çakışıyorsa köprü onları kurtarır ( cizim/kopru — yerleşim kurtarması ).

Gerekçe ( 23 Kas taraması, cikti/araclar/kurulamayan_23kas ):  ofisin gerçek projeleri
yalnız temel ölçülerle girilince "kurulamaz" deniyordu — LD 4815-6:  kuyu kabinden 750
geniş, ağırlık solda, kapı ağırlığa doğru açılıyor;  ağırlık kabin rayının ara kirişine,
kabin kapısının kanat cebi ara kirişe çarpıyordu.  Taslaklarda 2 kanatlı merkezi kapı
hiçbir kuyu genişliğinde kurulmuyordu.  "Düzeltme öner" aynı düzenleri iki üç adımda
kuruyordu.

Değişmezler:  kurulabilen düzen değişmez;  girilen değer olduğu gibi kullanılır;
çözülemeyen düzende varsayılanlar ve eski ileti kalır;  hesap ve çizim aynı yerleşimi
okur ( değer çizimden — hesabın girdisinde, ekranın soluk kutusunda );  tek kuyuda
kurtarma yoktur."""

import copy
import json
import unittest

from cizim import kopru
from motor.uygulama import uygulama_girdisi
from testler import gercek_projeler
from testler import test_grup
from testler.test_taslaklar import TASLAKLAR, istek
from testler.test_yerlesim_saglamligi import duzen_girdisi, standart_istek
from uclar import cizim_uclari, uygulama_istegi, uygulama_uclari

KACIKLIKLAR = ("kabin_yana_kaciklik", "kapi_kaciklik")
#  Formun temel kutuları:  ürün, kuyu, ağırlığın yanı, askı, katlar ( yerleşimin
#  kaçıklıkları, RK, raylar … boş — kullanıcı ilk girişte bunları yazmaz )
TEMEL = (
    "beyan_yuku",
    "beyan_hizi",
    "kabin_genisligi",
    "kabin_derinligi",
    "kapi_genisligi",
    "kat_kapisi_tipi",
    "kuyu_genisligi",
    "kuyu_derinligi",
    "agirlik_yeri",
    "aski_orani",
    "aski_duzeni",
    "durak_adedi",
    "seyir_mesafesi",
    "son_kat_yuksekligi",
    "kuyu_dibi",
    "kabin_ic_yuksekligi",
)
T = {t["kimlik"]: t for t in TASLAKLAR}


def _cizim(v):
    return json.loads(cizim_uclari.api_cizimler(copy.deepcopy(v)).body)


def _hesap_girdisi(v, i=0):
    return json.loads(uygulama_uclari.api_uygulama_coklu(copy.deepcopy(v)).body)["asansorler"][i]["girdi"]


def _temel(v):
    a = v["asansorler"][0]
    return dict(v, asansorler=[{k: a[k] for k in a if k in TEMEL}])


def _ld(ad):
    a = dict(gercek_projeler.PROJELER[ad])
    pg = {k: a.pop(k) for k in list(a) if k in uygulama_istegi.PROJE_GENELI_ALANLAR}
    return {"asansorler": [a], "proje_geneli": pg, "sabitler": {}, "asansor": 0}


def _merkezi(kimlik, **ek):
    v = istek(T[kimlik])
    v["asansorler"][0].update(kat_kapisi_tipi="Otomatik Merkezi", **ek)
    return v


def _referans_gibi():
    """Ofisin referans projesinin kuyusu ( 800 kg, 1.350 × 1.400, kuyu 2.100 × 1.850 —
    kabinden 750 geniş ), ağırlık solda, kapı ağırlığa doğru ( Teleskopik Sol )."""
    v = standart_istek(800, True, "Sol", kat_kapisi_tipi="Teleskopik Sol")
    v["asansorler"][0]["kuyu_genisligi"] = 2100
    return v


class Kurtarma(unittest.TestCase):
    def test_gercek_proje_temel_olculerle_kurulur(self):
        for ad, v in (("LD 4815-6", _temel(_ld("4815-6"))), ("referans proje gibi", _referans_gibi())):
            with self.subTest(ad):
                c = _cizim(v)
                self.assertTrue(c.get("aktif"), c.get("hata"))
                gi = _hesap_girdisi(v)
                #  Ağırlık solda:  kabin sağa ( + ) kaçar;  değer çizimden gelir
                self.assertGreater(gi["kabin_yana_kaciklik"], 0)
                self.assertIn("kabin_yana_kaciklik", gi["_cizimden"])

    def test_taslakta_merkezi_kapi_kurulur(self):
        for k in ("630", "800", "630-md", "800-md"):
            with self.subTest(k):
                v = _merkezi(k)
                c = _cizim(v)
                self.assertTrue(c.get("aktif"), c.get("hata"))
                gi = _hesap_girdisi(v)
                #  Ağırlık sağda:  kapı sola ( − ), kabinin önünde kalır
                self.assertLess(gi["kapi_kaciklik"], 0)
                kb, kp = float(T[k]["asansor"]["kabin_genisligi"]), float(T[k]["asansor"]["kapi_genisligi"])
                self.assertLessEqual(abs(gi["kapi_kaciklik"]), (kb - kp) / 2.0)

    def test_kurulabilen_duzen_degismez(self):
        for t in TASLAKLAR:
            with self.subTest(t["kimlik"]):
                gi = _hesap_girdisi(istek(t))
                for k in KACIKLIKLAR:
                    self.assertNotIn(k, gi.get("_cizimden") or {})
                    girilen = t["asansor"].get(k)
                    self.assertEqual(gi.get(k), None if girilen is None else float(girilen))

    def test_girilen_deger_kullanilir(self):
        v = _temel(_ld("4815-6"))
        v["asansorler"][0]["kabin_yana_kaciklik"] = "0"
        c = _cizim(v)
        self.assertFalse(c.get("aktif"))
        self.assertIn("ara kirişi arasında", c["hata"][0])

    def test_cozulemeyen_duzen_eski_iletisiyle_kalir(self):
        #  1.100'lük 2 kanatlı merkezi kapının iki cebi 2.000'lik kuyuya sığmaz ( 1.100 + 2 × 580 ):
        #  kurtarma denemez ( iki yanda da taşıyor ), çizim ve hesap aynı iletiyle durur
        c = _cizim(_merkezi("1250"))
        self.assertFalse(c.get("aktif"))
        self.assertIn("kanat cebi kuyuya sığmıyor", c["hata"][0])
        ham, _i, _p = cizim_uclari._istek(_merkezi("1250"))
        A = uygulama_girdisi.tamamla(ham)
        for k in KACIKLIKLAR:
            girilen = T["1250"]["asansor"].get(k)
            self.assertEqual(A.get(k), None if girilen is None else float(girilen))
            self.assertNotIn(k, A.get("_cizimden") or {})

    def test_hesap_ve_cizim_ayni_yerlesimi_okur(self):
        v = _temel(_ld("4815-6"))
        g, A, hata = duzen_girdisi(v)
        self.assertEqual(hata, [])
        gi = _hesap_girdisi(v)
        for k in KACIKLIKLAR:
            self.assertEqual(A[k], gi[k], k)
        self.assertAlmostEqual(g["kabin"]["kaciklik_y"], gi["kabin_yana_kaciklik"])
        kx = g["kuyu"]["genislik"] / 2.0 + gi["kabin_yana_kaciklik"]
        self.assertAlmostEqual(g["kapi"]["sol_pay"], kx + gi["kapi_kaciklik"] - g["kapi"]["genislik"] / 2.0)

    def test_rk_yanal_yetmeyince_kurtarilir(self):
        #  Derin kabinde merkezi kapı ( 1000 kg, 1.100 × 2.100 ) ve ağırlığa doğru açılan kapı
        #  ( 1275 taslağı RK'sız — BAR 2515 gibi ):  kabin kapısının cebi ara kirişe çarpar,
        #  yana kaydırmak yetmez;  RK boşsa raylar arkaya alınır ( 650 → kabin ortasının en çok
        #  200 arkası ), askı kaçıklığı yeni RK'yla
        ornek = {"1000 merkezi": _merkezi("1000"), "1000-md merkezi": _merkezi("1000-md")}
        v = istek(T["1275"])
        for k in ("ray_kapi_arasi", "kabin_yana_kaciklik"):
            v["asansorler"][0].pop(k)
        ornek["1275 RK'sız"] = v
        for ad, v in ornek.items():
            with self.subTest(ad):
                c = _cizim(v)
                self.assertTrue(c.get("aktif"), c.get("hata"))
                gi = _hesap_girdisi(v)
                self.assertIn("ray_kapi_arasi", gi["_cizimden"])
                self.assertGreater(gi["ray_kapi_arasi"], 650)
                kabin_ortasi = 30 + 90 + (float(v["asansorler"][0]["kabin_derinligi"]) + 20) / 2.0
                self.assertLessEqual(gi["ray_kapi_arasi"], kabin_ortasi + kopru.RK_KABIN_ORTASI_PAYI)
                xs = kopru._aski_x(gi)
                self.assertAlmostEqual(gi["aski_kaciklik_x"], 0.0 if xs is None else xs)

    def test_rk_yanal_yetince_ve_kurulabilende_650(self):
        for ad, v in (
            ("referans proje gibi", _referans_gibi()),
            ("630 merkezi", _merkezi("630")),
            ("taslak 630", istek(T["630"])),
        ):
            with self.subTest(ad):
                self.assertTrue(_cizim(v).get("aktif"))
                gi = _hesap_girdisi(v)
                self.assertEqual(gi["ray_kapi_arasi"], 650)
                self.assertNotIn("ray_kapi_arasi", gi.get("_cizimden") or {})

    def test_girilen_rk_kullanilir(self):
        v = _merkezi("1000", ray_kapi_arasi="650")
        c = _cizim(v)
        self.assertFalse(c.get("aktif"))
        self.assertIn("ara kirişine çarpıyor", c["hata"][0])

    def test_tek_kuyuda_kurtarma_yok(self):
        B = dict(uygulama_girdisi.varsayilanlar(), kuyu_duzeni="Tek kuyu")
        self.assertEqual(kopru._yerlesim_kurtarmasi(B, KACIKLIKLAR + (kopru.RK,)), ({}, None))
        v = test_grup.ikili(630, "Sağ", 630, "Sağ")
        for i in range(2):
            gi = _hesap_girdisi(dict(v, asansor=i), i)
            for k in KACIKLIKLAR + (kopru.RK,):
                self.assertNotIn(k, gi.get("_cizimden") or {})


if __name__ == "__main__":
    unittest.main()

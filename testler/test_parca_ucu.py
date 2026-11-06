"""PARÇAYA TIKLAMA — parçayı belirleyen girdiler ( hesap/uclar/parca_uclari.py ).

Ekranda bir parçaya tıklanınca onu belirleyen girdiler listelenir:  ölçü
kutusunun yöntemiyle çizim bir kez izli kurulur, parçanın koordinatları
kaynaklarını taşır.  Tıklanan ekrandaki ÖRNEKTİR ( data-parca "ad-n" ):  uç
aynı sırayı görmelidir — yoksa başka parçanın girdisi söylenir."""

import json
import re
import unittest

from cizim import cizimler
from cizim import geometri
from cizim import pafta
from cizim import parca_adlari
from cizim import sorunlu
from tasarim.alanlar import DURAK_KOTLARI
from testler import test_yerlesim_saglamligi
from testler.test_olcu_kaynagi import DUZENLER, _g, _veri
from testler.yavas import yavas
from motor.uygulama import uygulama_hesabi
from uclar import cizim_uclari
from uclar import parca_uclari
from uclar import uygulama_istegi


def _parca(v, cizim, parca):
    return json.loads(parca_uclari.api_parca(dict(v, cizim=cizim, parca=parca)).body)


def _ornekler(e):
    return [(ad, len(liste)) for ad, liste in geometri.parca_ornekleri(e)]


def _ilk(v, cizim, ad, son=False):
    """Çizimdeki ilk ( son ) ``ad`` örneğinin ekrandaki kimliği ( "ad-n" ) — ekranın
    çizim girdisiyle ( sorunlu girdide de kurulur ) ve onun gibi sorunlu çizim kipinde."""
    asansorler, ortak = uygulama_istegi.asansor_girdileri(v)
    s = uygulama_hesabi.hesapla_coklu(asansorler, ortak)
    g, hata = cizim_uclari.asansor_girdisi(asansorler, ortak, s if s.get("aktif") else None, "P", 0)
    with sorunlu.kip(bool(hata)):
        e = cizim_uclari._elemanlar(g, cizim)[0]
    bulunan = [f"{a}-{n}" for n, (a, _l) in enumerate(geometri.parca_ornekleri(e)) if a == ad]
    if not bulunan:
        raise AssertionError(f"{cizim} çiziminde {ad} yok")
    return bulunan[-1 if son else 0]


def _ayni_sira(test, v):
    """Ekranın parça örnekleri ( hesabın sonucuyla, çerçeveli — SVG bunlardan ) ucun
    çözdüğünün ÖNÜNDE aynı sırayla;  fazlası yalnız hesabın ölçeksiz şeması."""
    g, _h = _g(v)
    ham, i, proje = cizim_uclari._istek(v)
    for ad in pafta.sira(g):
        ekran = _ornekler(cizim_uclari._elemanlar(g, ad)[0])
        r = parca_uclari._cozumle(ham, i, proje, ad)
        test.assertIsNotNone(r, ad)
        uc = [(a, len(k)) for a, k in r["ornekler"]]
        test.assertEqual([a for a, _n in ekran[: len(uc)]], [a for a, _n in uc], ad)
        test.assertTrue({a for a, _n in ekran[len(uc) :]} <= {"kuvvet_semasi"}, (ad, ekran[len(uc) :]))


class EkranlaAyni(unittest.TestCase):
    def test_ornek_projelerde_ekranin_sirasi(self):
        for md in (False, True):
            with self.subTest(md=md):
                _ayni_sira(self, _veri(md))

    @yavas("1 dk")
    def test_butun_duzenlerde_ekranin_sirasi(self):
        for ad, kur in DUZENLER.items():
            with self.subTest(duzen=ad):
                _ayni_sira(self, kur())

    def test_ekranin_adiyla(self):
        #  Yanıtın adı SVG'nin data-ad'ı:  kutunun başlığı tıklanan parçanınki
        v = _veri()
        y = json.loads(cizim_uclari.cizimler_yaniti(v).body)
        c = next(c for c in y["cizimler"] if c["ad"] == "kuyu_plani")
        for pid, dad in dict.fromkeys(re.findall(r'data-parca="([^"]+)" data-ad="([^"]+)"', c["svg"])):
            r = _parca(v, "kuyu_plani", pid)
            self.assertTrue(r["aktif"], (pid, r))
            self.assertEqual(r["ad"], dad.replace("&amp;", "&"), pid)


class Girdiler(unittest.TestCase):
    def test_kabin_olculeri_kabinin_boyutu(self):
        v = _veri()
        r = _parca(v, "kuyu_plani", _ilk(v, "kuyu_plani", "kabin_dis"))
        self.assertTrue(r["aktif"], r)
        self.assertEqual(r["ad"], parca_adlari.ad("kabin_dis"))
        g = {x["anahtar"]: x for x in r["girdiler"]}
        for k in ("kabin_genisligi", "kabin_derinligi"):
            self.assertEqual((g[k]["etki"], g[k]["degistirilir"], g[k]["yer"]), ("boyut", True, "asansor"), k)
        #  Sıra:  değiştirilebilenler önce, onların içinde parçanın ölçüsünü verenler önce
        sira = [(not x["degistirilir"], x["etki"] != "boyut") for x in r["girdiler"]]
        self.assertEqual(sira, sorted(sira))

    def test_ofis_standardi_yalniz_gosterilir(self):
        v = _veri()
        r = _parca(v, "kuyu_kesiti_yan", _ilk(v, "kuyu_kesiti_yan", "kapi_kasasi"))
        ofis = [x for x in r["girdiler"] if x["yer"] == "ofis"]
        self.assertTrue(ofis, r["girdiler"])
        self.assertTrue(all(not x["degistirilir"] and x["etiket"] for x in ofis), ofis)

    def test_kotla_giriste_duragin_kotu(self):
        #  En üst durağın kapısı:  yeri durakların kotundan ( en alttaki kesitin sıfırıdır )
        v = test_yerlesim_saglamligi.kotla(_veri(True), kayma=-3500)
        r = _parca(v, "kuyu_kesiti_yan", _ilk(v, "kuyu_kesiti_yan", "kat_kapisi", son=True))
        kot = [x for x in r["girdiler"] if x["anahtar"] == DURAK_KOTLARI]
        self.assertTrue(kot, r["girdiler"])
        self.assertTrue(all(not x["degistirilir"] and isinstance(x["durak"], int) for x in kot), kot)

    def test_secim_kategorisi_istenince(self):
        #  Ray profili türevle bulunmaz:  liste söylemez, yanıtın notu söyler;  istenince
        #  ( "Seçimleri de bul" ) her seçim denenir ve bulunur — düzenlenebilir, seçenekleriyle
        v = _veri()
        pid = _ilk(v, "kuyu_plani", "kabin_ray")
        r = _parca(v, "kuyu_plani", pid)
        self.assertNotIn("kabin_ray_profili", [x["anahtar"] for x in r["girdiler"]])
        self.assertEqual(r["not"], parca_uclari.NOT)
        y = json.loads(parca_uclari.api_parca(dict(v, cizim="kuyu_plani", parca=pid, secimler=True)).body)
        g = {x["anahtar"]: x for x in y["girdiler"]}
        self.assertTrue(g["kabin_ray_profili"]["degistirilir"])
        self.assertIn(g["kabin_ray_profili"]["deger"], g["kabin_ray_profili"]["secenekler"])
        self.assertEqual(y["not"], parca_uclari.NOT_SECIMLI)
        #  Türevle bulunanlar yine listede
        self.assertTrue({x["anahtar"] for x in r["girdiler"]} <= set(g))

    def test_sorunlu_cizimde_de(self):
        #  Ekran sorunlu çizimi de kurar;  kırmızı parçanın girdisi asıl aranandır
        #  ( kuyu 1600:  test_sorunlu_cizim.VAKALAR — bütün çizimler gelir )
        v = _veri(kuyu_genisligi=1600)
        self.assertTrue(_g(v)[1])
        r = _parca(v, "kuyu_plani", _ilk(v, "kuyu_plani", "kabin_dis"))
        self.assertTrue(r["aktif"], r)
        self.assertIn("kuyu_genisligi", [x["anahtar"] for x in r["girdiler"]])


class Reddeder(unittest.TestCase):
    def test_bozuk_istekler_kendi_iletisiyle(self):
        v = _veri()
        for cizim, parca, ileti in (
            ([], "kabin_dis-0", "Bilinmeyen çizim."),
            ("yok_boyle", "kabin_dis-0", "Bilinmeyen çizim."),
            ("kuyu_plani", None, "Parça belirtilmedi."),
            ("kuyu_plani", ["kabin_dis-0"], "Parça belirtilmedi."),
            ("kuyu_plani", "kabin_dis", "Parça belirtilmedi."),
            ("kuyu_plani", "kabin_dis-999", "Bu, hesabın ölçeksiz şeması — bir girdinin ölçüsü değil."),
        ):
            with self.subTest(cizim=cizim, parca=parca):
                self.assertEqual(_parca(v, cizim, parca), {"aktif": False, "hata": [ileti]})

    def test_cizim_degistiyse_baska_parcanin_girdisi_soylenmez(self):
        v = _veri()
        pid = _ilk(v, "kuyu_plani", "kabin_dis")
        n = pid.rpartition("-")[2]
        self.assertEqual(
            _parca(v, "kuyu_plani", f"kat_kapisi-{n}"),
            {"aktif": False, "hata": ["Çizim değişmiş — yeniden tıklayın."]},
        )

    def test_tek_kuyunun_ortak_cizimi(self):
        ad = next(iter(cizim_uclari._BIRLESIK))
        r = _parca(_veri(), ad, "kabin_dis-0")
        self.assertFalse(r["aktif"])
        self.assertIn("asansörün kendi çiziminden", r["hata"][0])

    def test_cizilmeyen_cizim(self):
        #  Projenin paftasında olmayan çizim ( makine dairesinde kuyu üstü planı ) kurulmaz
        v = _veri(True)
        g, _h = _g(v)
        ad = next(a for a in cizimler.CIZIMLER if not pafta.cizilir(g, a))
        self.assertEqual(
            _parca(v, ad, "kabin_dis-0"), {"aktif": False, "hata": ["Çizim bu girdilerle kurulamıyor."]}
        )


if __name__ == "__main__":
    unittest.main()

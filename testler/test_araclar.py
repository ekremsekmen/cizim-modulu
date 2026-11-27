"""GELİŞTİRME ARAÇLARI ( araclar/ ) — taramanın hüküm karşılaştırması bir
değişikliği kaçırırsa tarama boşuna "geçti" der."""

import os
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from unittest import mock

from araclar import avan_tarama
from araclar import care_tarama
from araclar import fiziksel
from araclar import karne
from araclar import kesisme
from araclar import tarama
from cizim import cizimler
from cizim import eleman
from cizim import girdi
from cizim import kuyu_kesiti
from cizim import pafta
from uclar import avan_secici
from uclar import care_uclari

KAYIT = {"ana": {"A": {"durum": "çizildi", "sebep": ""}, "B": {"durum": "ret", "sebep": "X sığmıyor"}}}


class Karsilastirma(unittest.TestCase):
    def test_ayni_hukum_fark_yok(self):
        sonuc = [
            {"ad": "A", "durum": "çizildi", "sorun": []},
            {"ad": "B", "durum": "ret", "hata": ["X sığmıyor", "Y de"]},
        ]
        self.assertEqual(tarama.karsilastir("ana", sonuc, KAYIT), [])

    def test_tek_kuyuda_zincirler_asansor_asansor(self):
        """Tek kuyunun ortak çiziminde iki asansörün aynı kottaki sıraları ayrı zincirdir
        ( ölçünün "asansor" işareti );  işaretsiz çizimde geometri.zincirler ile aynı."""

        def olcu(a, b, n=None):
            el = {"tip": "olcu", "yon": "yatay", "kot": 100.0, "a": (a, 0), "b": (b, 0), "uzunluk": b - a}
            return el if n is None else dict(el, asansor=n)

        kapanir = lambda e: all(abs(z["toplam"] - (z["son"] - z["bas"])) < 0.5 for z in tarama._zincirler(e))
        #  İki asansörün sıraları arasında ayırma kirişi kadar boşluk:  ikisi de kapanır
        self.assertTrue(
            kapanir([olcu(0, 1000, 0), olcu(1000, 2000, 0), olcu(2140, 3000, 1), olcu(3000, 4100, 1)])
        )
        #  Aynı asansörün zincirinde eksik aralık yakalanır
        self.assertFalse(kapanir([olcu(0, 1000, 0), olcu(1500, 2000, 0), olcu(2140, 4100, 1)]))
        #  İşaretsiz ( tek asansörlü ) çizimde eskisi gibi tek zincir
        self.assertFalse(kapanir([olcu(0, 1000), olcu(2140, 3000)]))

    def test_tek_kuyu_grubu_tam_boy_perdeli_duzeni_tarar(self):
        """Tek kuyu grubu ağırlığı ortada kalan ( tam boy perdeli — m.5.2.5.5.2.2 ) düzenleri
        de tarar ve kayıtta çizilmiş görünürler:  11 Kas'a kadar ret sebebiydi."""
        import json

        adlar = {ad for ad, _v in tarama.duzenler("tek_kuyu")}
        with open(tarama.HUKUMLER, encoding="utf-8") as f:
            kayit = json.load(f)["tek_kuyu"]
        for ad in ("taslak 1000 + 1250", "taslak 1275 + 1250"):
            self.assertIn(ad, adlar)
            self.assertEqual(kayit[ad]["durum"], "çizildi", ad)
        self.assertGreaterEqual(sum(v["durum"] == "çizildi" for v in kayit.values()), 30)

    def test_hukum_ve_sebep_degisimi(self):
        sonuc = [
            {"ad": "A", "durum": "ret", "hata": ["Z yok"]},
            {"ad": "B", "durum": "ret", "hata": ["W yok"]},
        ]
        f = tarama.karsilastir("ana", sonuc, KAYIT)
        self.assertEqual(
            f, ["A:  çizildi → ret  ( Z yok )", "B:  ret → ret  ( W yok )  ·  önceki sebep:  X sığmıyor"]
        )

    def test_sorun_cokme_ve_eksik_duzen(self):
        sonuc = [
            {"ad": "A", "durum": "çizildi", "sorun": ["kuyu_plani: NaN kabin"]},
            {"ad": "C", "durum": "çöktü", "ayrinti": "KeyError"},
        ]
        f = tarama.karsilastir("ana", sonuc, KAYIT)
        self.assertIn("düzen artık taranmıyor:  B", f)
        self.assertIn("yeni düzen ( kayıtta yok ):  C  →  çöktü", f)
        self.assertIn("SORUN  A:  kuyu_plani: NaN kabin", f)
        self.assertIn("ÇÖKTÜ  C:  KeyError", f)

    def test_kayit_butun_gruplari_kapsar(self):
        import json

        with open(tarama.HUKUMLER, encoding="utf-8") as f:
            kayit = json.load(f)
        self.assertEqual(sorted(kayit), sorted(tarama.GRUPLAR))
        self.assertEqual(
            {g: len(v) for g, v in kayit.items()},
            {g: sum(1 for _ in tarama.duzenler(g)) for g in tarama.GRUPLAR},
        )

    def test_karne_kotulesmesi_de_iyilesmesi_de_durdurur(self):
        #  Cırcır ( araclar/karne ):  sayı artarsa kötüleşme, azalırsa kayıt
        #  yenilenmeli — ikisi de taramayı başarısız yapar
        kayit = {"ana": {"A": {"kuyu_plani": {"maske_kenar_siliyor": 2}}}}
        sonuc = [
            {"ad": "A", "durum": "çizildi", "sorun": [], "karne": {"kuyu_plani": {"maske_kenar_siliyor": 3}}},
            {"ad": "B", "durum": "çizildi", "sorun": [], "karne": {}},
        ]
        f = tarama.karne_farklari("ana", sonuc, kayit)
        self.assertEqual(len(f), 1)
        self.assertTrue(f[0].startswith("KARNE KÖTÜLEŞTİ  A · kuyu_plani"), f)
        sonuc[0]["karne"] = {"kuyu_plani": {"maske_kenar_siliyor": 1}}
        f = tarama.karne_farklari("ana", sonuc, kayit)
        self.assertTrue(f and f[0].startswith("KARNE İYİLEŞTİ  A · kuyu_plani"), f)
        sonuc[0]["karne"] = {"kuyu_plani": {"maske_kenar_siliyor": 2}}
        self.assertEqual(tarama.karne_farklari("ana", sonuc, kayit), [])

    def test_karne_kaydi_taranan_duzenlerden(self):
        kayit = karne.oku(karne.TARAMA_KAYDI)
        self.assertEqual(sorted(kayit), sorted(tarama.GRUPLAR))
        for g, duzenler in kayit.items():
            with self.subTest(grup=g):
                self.assertLessEqual(set(duzenler), {ad for ad, _ in tarama.duzenler(g)})
                for cizimler_ in duzenler.values():
                    for sayilar in cizimler_.values():
                        self.assertLessEqual(set(sayilar), set(karne.KURALLAR) | set(karne.TARAMA_KURALLARI))


def _beton(x, y, g, d):
    return eleman.dikdortgen("TARAMA", x, y, g, d, tip="tarama")


def _ornek():
    return {k: (dict(v) if isinstance(v, dict) else v) for k, v in girdi.ORNEK.items()}


class Kesisme(unittest.TestCase):
    """araclar/kesisme.py:  biçimi olan parçada çizilen biçimdir, dikdörtgen yalnız
    mantık zarfı ( svg._bicim zarfı çizmez ) — 21 Eki:  ağırlık konsolunun
    görünmeyen zarfı perde yazısına "binen" sayılıyordu ( 4815-6 DBGW 1315,
    63444-2 kuyu 2455 )."""

    def _yazi(self):
        return eleman.yazi(138.25, 651.25, "AĞIRLIK PERDESİ", 70.0, aci=90)

    def test_bicimli_parcada_zarf_kenari_sayilmaz(self):
        plaka = eleman.dikdortgen("KONSOL", 0, 282, 160, 100, ad="plaka")
        plaka["bicim"] = [{"noktalar": [(0, 292), (40, 292), (40, 1788), (0, 1788)]}]
        self.assertEqual(kesisme.kesismeler([plaka, self._yazi()]), [])
        #  Biçimsiz aynı dikdörtgen çizilir:  kenarı yazıdan geçer
        dz = eleman.dikdortgen("KONSOL", 0, 282, 160, 100, ad="plaka")
        self.assertEqual([x[2:] for x in kesisme.kesismeler([dz, self._yazi()])], [("KONSOL", "plaka")] * 2)

    def test_duvar_ici_kenar_payiyla(self):
        """Duvara 1 mm giren yazı kutusu ( kâğıtta 0,05 mm ) duvarın içinde sayılmaz
        — kenar denetimiyle aynı pay ( 2·k );  gerçekten içindeki sayılır."""
        duvar = eleman.dikdortgen("TARAMA", -150, 0, 150, 1850, tip="tarama")
        yazi = eleman.yazi(328, 1698, "HALAT BAĞLANTISI", 70.0)
        kb = kesisme.yazi_kutusu(yazi)
        self.assertLess(kb[1], 0.0)  # kutu duvara giriyor ( −1 )
        self.assertEqual(kesisme.kesismeler([duvar, yazi]), [])
        yazi["x"] -= 100
        self.assertIn("TARAMA-İÇİ", [x[2] for x in kesisme.kesismeler([duvar, yazi])])

    def test_bicimin_kenari_sayilir(self):
        kol = eleman.dikdortgen("KONSOL", 160, 2000, 100, 30, ad="kol")
        kol["bicim"] = [{"noktalar": [(0, 600), (283, 600), (283, 640), (0, 640)]}]
        f = kesisme.kesismeler([kol, self._yazi()])
        self.assertTrue(f and all(x[2:] == ("KONSOL", "kol") for x in f), f)


class Fiziksel(unittest.TestCase):
    """araclar/fiziksel.py:  her kural bir hatalı, bir doğru düzenle ( 17 Eki —
    PR #26'nın üç hatası bu kurallarla bulundu )."""

    def test_r1_beton_parcaya_giriyor(self):
        duvar = _beton(1000, 0, 200, 2000)
        icinde = eleman.dikdortgen("KONSOL", 980, 500, 150, 150, ad="makine_sasesi")
        yaninda = eleman.dikdortgen("KONSOL", 840, 500, 150, 150, ad="makine_sasesi")
        f = fiziksel.sorunlar({}, "makine_dairesi", [duvar, icinde])
        self.assertEqual(len(f), 1)
        self.assertIn("R1 beton parçaya giriyor  makine_sasesi", f[0])
        self.assertEqual(fiziksel.sorunlar({}, "makine_dairesi", [duvar, yaninda]), [])

    def test_r1_bicime_bakar(self):
        """Biçimi olan parçada zarfa değil biçime bakılır:  zarfı duvara
        değen ama biçimi değmeyen parça sorun değildir."""
        duvar = _beton(1000, 0, 200, 2000)
        el = eleman.dikdortgen("KONSOL", 900, 500, 150, 150, ad="konsol")
        el["bicim"] = [{"noktalar": [(900, 500), (990, 500), (990, 650), (900, 650)]}]
        self.assertEqual(fiziksel.sorunlar({}, "makine_dairesi", [duvar, el]), [])

    def test_r2_kuyu_boslugunda_beton(self):
        g = _ornek()
        tavan = kuyu_kesiti.yerlesim(g)["M"]["tavan"]
        D = g["kuyu"]["derinlik"]
        e = [_beton(-150, -1500, D + 300, 150), _beton(D, -1500, 150, tavan + 1650)]
        self.assertEqual(fiziksel.sorunlar(g, "kuyu_kesiti_yan", e), [])
        #  Kuyunun içine inen duvar ( oda duvarı hatası, PR #26 )
        e.append(_beton(D - 300, tavan - 1200, 200, 1200))
        f = fiziksel.sorunlar(g, "kuyu_kesiti_yan", e)
        self.assertTrue(any("R2 kuyu boşluğunda beton" in m for m in f), f)

    def test_r3_duvarin_alti_bosta_lento_haric(self):
        g = _ornek()
        taban = _beton(-150, -1500, 2500, 150)
        havada = _beton(-150, 3000, 150, 2000)
        f = fiziksel.sorunlar(g, "kuyu_kesiti_yan", [taban, havada])
        self.assertTrue(any("R3 duvarın altı boşta" in m for m in f), f)
        #  Altında kapı varsa lentodur
        kapi = eleman.dikdortgen("KAPI", -150, 0, 150, 2300)
        self.assertEqual(fiziksel.sorunlar(g, "kuyu_kesiti_yan", [taban, havada, kapi]), [])

    def test_r3_dar_doseme_duvar_sayilmaz(self):
        """Kuyunun arkasından 195 mm taşan, 250 kalın oda döşemesi:  dar da olsa
        döşemedir ( 21 Eki bulanık tarama — 63444-2, kuyu derinliği 2455 ).  Aynı
        ölçüde adsız düşey beton ise duvardır, altı boştaysa sorun."""
        g = _ornek()
        taban = _beton(-150, -1500, 2500, 150)
        doseme = _beton(2705, 6000, 195, 250)
        ad = eleman.ad(eleman.dikdortgen("KUYU-DUVAR", 2705, 6000, 195, 250), "oda_dosemesi")
        self.assertEqual(fiziksel.sorunlar(g, "kuyu_kesiti_yan", [taban, doseme, ad]), [])
        f = fiziksel.sorunlar(g, "kuyu_kesiti_yan", [taban, doseme])
        self.assertTrue(any("R3 duvarın altı boşta" in m for m in f), f)

    def test_r4_kuyu_planinda_binis(self):
        kabin = eleman.dikdortgen("KABIN", 500, 300, 1000, 1200, ad="kabin")
        agirlik = eleman.dikdortgen("AGIRLIK", 1450, 400, 150, 800, ad="agirlik")
        f = fiziksel.sorunlar({}, "kuyu_plani", [kabin, agirlik])
        self.assertEqual(len(f), 1)
        self.assertIn("R4 kabin / agirlik biniyor", f[0])
        agirlik["x"] = 1550
        self.assertEqual(fiziksel.sorunlar({}, "kuyu_plani", [kabin, agirlik]), [])

    def test_ornek_projeler_temiz(self):
        """Programın örnek projeleri ( makine dairesiz ve daireli ) bütün
        çizimlerinde fiziksel olarak tutarlıdır."""
        for md in (False, True):
            with self.subTest(makine_dairesi=md):
                g = _ornek()
                if md:
                    g["makine"] = dict(g["makine"], yeri="Makine dairesi")
                for c in pafta.SIRA_MD if md else pafta.SIRA_MRL:
                    e = cizimler.CIZIMLER[c][1](g)
                    self.assertEqual(fiziksel.sorunlar(g, c, e), [], c)


if __name__ == "__main__":
    unittest.main()


class DogrulukOlcumu(unittest.TestCase):
    """SEÇİCİ DOĞRULUK PLANI ( 27 Kas, Adım 1 ):  avan taramasının dar ekseni ve güvenceleri,
    çare taraması.  Ölçüm yanlışsa düzeltmelerin etkisi yanlış ölçülür."""

    def test_dar_eksen_senaryolari(self):
        liste = avan_tarama.dar_senaryolari()
        kimlikler = [k for k, _a, _m in liste]
        self.assertEqual(len(kimlikler), len(set(kimlikler)))
        #  10 hazır asansör × 8 kuyu + 5 makine daireli × 2 odalı + kullanıcının 4 vakası
        self.assertEqual(len(liste), 94)
        m = dict(next(m for k, _a, m in liste if k == "vaka|800|k900|s4050"))
        self.assertEqual((m["kuyu_genisligi"], m["kuyu_derinligi"], m["kapi_genisligi"]), (1800, 2700, 900))
        self.assertEqual(m["kuyu_tavani_kotu"], "+28,75")
        self.assertTrue(m["durak_kotlari"].startswith("-2,60; +0,70; +3,70"))
        self.assertTrue(m["durak_kotlari"].endswith("+24,70"))
        #  Temel eksen değişmedi ( kaydı ve CI işleri aynı )
        self.assertEqual(len(avan_tarama.senaryolar()), 581)

    def test_bir_adim_geri(self):
        """G2'nin geri adımı mimarınkine doğru;  arada bir adım yoksa ölçülmez."""
        self.assertEqual(avan_tarama._geri({"eski": "1800", "yeni": 1980.0}), 1970)
        self.assertEqual(avan_tarama._geri({"eski": "+28,75", "yeni": "+29,00"}), "+28,99")
        #  Kuyu dibi aşağı iner:  geri adım yukarı
        self.assertEqual(avan_tarama._geri({"eski": "-4,70", "yeni": "-4,95"}), "-4,94")
        self.assertIsNone(avan_tarama._geri({"eski": "1800", "yeni": 1805.0}))
        self.assertIsNone(avan_tarama._geri({"eski": "+28,75", "yeni": "+28,76"}))

    def test_guvenceler(self):
        """Sahte seçiciyle:  bir adım eksiği uygunsa G2;  büyütmede gereken G3, sığmaz G4."""
        m = {"kuyu_genisligi": 1800, "kuyu_derinligi": 2700}
        gereken = {
            "durum": "gereken",
            "gereken": [{"anahtar": "kuyu_genisligi", "eski": "1800", "yeni": 1980.0}],
        }
        uygun = {"durum": "uygun", "istek": {"asansorler": [{"agirlik_yeri": "Arka"}]}}
        with mock.patch.object(avan_secici, "sec", return_value=uygun) as sec:
            g = avan_tarama.guvenceler(m, gereken)
        self.assertEqual([x[0] for x in g], ["G2"])
        self.assertEqual(sec.call_args[0][0]["kuyu_genisligi"], 1970)
        with mock.patch.object(avan_secici, "sec", return_value={"durum": "gereken", "gereken": []}):
            self.assertEqual([x[0] for x in avan_tarama.guvenceler(m, uygun)], ["G3", "G3"])
        with mock.patch.object(avan_secici, "sec", return_value={"durum": "sigmaz", "nedenler": ["x"]}):
            self.assertEqual([x[0] for x in avan_tarama.guvenceler(m, uygun)], ["G4", "G4"])
        with mock.patch.object(avan_secici, "sec", return_value={"durum": "gereken", "gereken": []}):
            self.assertEqual(avan_tarama.guvenceler(m, gereken), [])

    def test_care_taramasi_onerinin_guvencesi(self):
        """Çare taraması önerinin sözünü bağımsız denetler:  sorun kalırsa, yeni sorun çıkarsa,
        hesap durursa ihlal;  söylenen ortaya çıkan sorun ihlal değil."""
        once = ({"A": "A:  x", "B": "B:  y"}, True, set(), frozenset(), True)
        oneri = {"anahtar": "k", "yeni": 1, "yontem": "türev", "gider": ["A:  x"], "ortaya_cikan": ["C"]}
        care = {
            "careler": [{"metin": "A:  x", "oneriler": [oneri]}, {"metin": "B:  y", "oneriler": []}],
            "tamamlandi": True,
            "sinama": 3,
        }
        for sonra, beklenen in (
            (({"B": "B:  y", "C": "C:  z"}, True), []),
            (({"A": "A:  x", "B": "B:  y"}, True), ["gidereceği sorun kaldı"]),
            (({"B": "B:  y", "D": "D:  w"}, True), ["yeni sorun"]),
            (({"B": "B:  y"}, False), ["hesap durdu"]),
        ):
            with (
                self.subTest(sonra),
                mock.patch.object(
                    care_uclari,
                    "girdi_durumu",
                    side_effect=[once, sonra + (set(), frozenset(), True)],
                ),
                mock.patch.object(care_uclari, "coz", return_value=care),
                mock.patch.object(care_uclari, "girdi_yaz", return_value={}),
            ):
                r = care_tarama.dene(("x", {}))
            self.assertEqual([i.split(":  ", 1)[1].split(" [")[0] for i in r["ihlal"]], beklenen)
            self.assertEqual(r["caresiz"], ["B"])

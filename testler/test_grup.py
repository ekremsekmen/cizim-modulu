"""TEK KUYUDA İKİ ASANSÖR ( cizim/grup.py — 1 Kas;  plan cikti/devir/ORTAK_KUYU_PLANI.md § 8 ).

· girdi:  proje düzeyinde "Kuyu düzeni" ( Ayrı · Tek kuyu ), "Soldaki asansör" ve
  "Ayırma kirişi" ( NPU ) — tek kuyunun alanları yalnız iki asansörlü tek kuyuda
  okunur;  kuyunun ortak girdileri ( KUYU_ORTAK ) iki asansörde aynıdır ( kapı 1.
  asansörünkini öbürüne yazar );  köprü asansörün kuyudaki yerini ( 1 solda, 2 sağda )
  ve aradaki kirişi koyar, hesap motoru numarayı girdiden alır
· denetim:  ayırma kirişi seçilmeli;  korkuluk komşunun hareketli parçasına 0,50 m'den
  yakınsa perde kuyu boyunca uzanmalı ( m.5.2.5.5.2.2 )
· plan:  12744-3 düzeni ( ağırlıklar arkada, dış duvarlar 250 ) tek düzlemde — duvarlar
  bir kez, ortada ayırma kirişi, en dışta 250 · SW · kiriş · SW · 250 ve ayraçta toplam,
  yan ölçüler dış yanlarda, kesit işareti yok, adlar en üstte;  her asansörün parçası
  kirişin kendi yarısında, yeni yazı çakışması yok, alt sıralar aynı hizada
· asansörün kendi çizimleri:  açık yanda duvar yerine kiriş ( planlar, kesitler ), iki
  kuyu dibinin arasında perde ( m.5.2.5.5.2.1 )
· ekran, pafta ve paket:  kuyunun planı önde ( ekranda tıklanmaz ), sorunları ekranda
  söylenir ve paketi durdurur
"""

import copy
import itertools
import json
import unittest

from cizim import cizimler
from cizim import geometri
from cizim import grup
from cizim import kopru
from cizim import kuyu_kesiti
from cizim import makine
from cizim import pafta
from motor.uygulama import uygulama_girdisi
from motor.uygulama import uygulama_hesabi
from tasarim import alanlar
from testler.test_yerlesim_saglamligi import KABIN, standart_istek
from uclar import cizim_uclari
from uclar import uygulama_istegi
from uclar import uygulama_uclari


def ikili(Q1=1000, yer1="Arka", Q2=800, yer2="Arka", kiris=140, soldaki=1, duzen="Tek kuyu", **ek):
    """İki asansörlü, makine dairesiz, tek kuyulu istek:  standart asansörler
    ( arkadaki ağırlıkta askı kabin üstü, makine bina yapısında — test_yerlesim_
    saglamligi.gecerli_duzen gibi ).  Kuyunun girdileri ( derinlik, duvarlar 250,
    son kat 5.000 ) tek kuyuda 1. asansörde — kapı öbürüne yazar.  kiris:  ayırma kirişinin
    NPU'su ( None:  seçilmemiş ).  ek:  birinci asansöre eklenecek girdiler."""
    a = []
    for Q, yer in ((Q1, yer1), (Q2, yer2)):
        x = standart_istek(Q, True, yer)["asansorler"][0]
        if yer == "Arka":
            x.update(aski_duzeni="Kabin üstü", makine_raya_biniyor="Bina yapısına")
        a.append(x)
    D = max(KABIN[Q][1] + (700 if y == "Arka" else 450) for Q, y in ((Q1, yer1), (Q2, yer2)))
    #  Ayrı kuyuda her asansör kendi değerini taşır;  tek kuyuda 2.'ninki kapıda ezilir
    for x in a if duzen != "Tek kuyu" else a[:1]:
        x.update(kuyu_derinligi=D, kuyu_duvar_kalinligi=250, son_kat_yuksekligi=5000)
    a[0].update(ek)
    pg = {"mk_yok": True, "kuyu_duzeni": duzen, "soldaki_asansor": soldaki}
    if kiris:
        pg["ayirma_kirisi"] = kiris
    return {"asansorler": a, "proje_geneli": pg, "sabitler": {}, "asansor": 0}


def girdiler(v):
    """Programın yolu ( kapı → hesap → köprü → çizimlerin doğrulamaları ):  [ ( g, hata ) ]."""
    asansorler, ortak = uygulama_istegi.asansor_girdileri(copy.deepcopy(v))
    s = uygulama_hesabi.hesapla_coklu(asansorler, ortak)
    return cizim_uclari.girdiler(v, asansorler, ortak, s if s.get("aktif") else None, "DENEME")


def gecerli(v):
    c = girdiler(v)
    hata = [h for _g, h in c]
    assert not any(hata), hata
    return [g for g, _h in c]


def kuyudakiler(v):
    """Tek kuyudaki asansörlerin çizim girdileri, soldan sağa."""
    return grup.gruptakiler(gecerli(v))


def yanit(v, i=0):
    return json.loads(cizim_uclari.api_cizimler(dict(copy.deepcopy(v), asansor=i)).body)


def olculer(e, ad):
    return [x for x in e if x["tip"] == "olcu" and x.get("ad") == "olcu_" + ad]


def _yazi_kutulari(e):
    out = []
    for x in e:
        if x["tip"] == "olcu":
            k = geometri.yazi_kutusu(x)
        elif x["tip"] == "yazi":
            k = geometri.sinir([x])
        else:
            continue
        if k:
            out.append(k)
    return out


def yarisindan_tasan(gler):
    """Her asansörün kuyunun planındaki parçası ( kendi koordinatında ) aradaki
    kirişin ortasını geçmemeli:  geçen elemanlar.  Üst ve alt sıralar birlikte
    yerleşir, sayılmaz."""
    alt = min(geometri.olcu_alti(g) for g in gler)
    tasan = []
    for n, g in enumerate(gler):
        komsu, komsu_g = ("Sağ", gler[1]) if n == 0 else ("Sol", gler[0])
        k = g["kuyu"]
        orta = k["genislik"] + k["duvar_sag"] / 2 if komsu == "Sağ" else -k["duvar_sol"] / 2
        ust, alt_ = k["derinlik"] + k["duvar_arka"], -k["duvar_on"]
        for x in grup._asansorun_plani(g, komsu, komsu_g, alt):
            if x["tip"] == "olcu" and x["yon"] == "yatay" and not alt_ <= x["kot"] <= ust:
                continue
            b = geometri.sinir([x])
            if (b[2] > orta + 1) if komsu == "Sağ" else (b[0] < orta - 1):
                tasan.append((n + 1, x["tip"], x.get("ad"), x.get("metin"), [round(v) for v in b]))
    return tasan


def cakisan_yazilar(e, pay=2.0):
    k = _yazi_kutulari(e)
    return sum(
        1
        for a, b in itertools.combinations(k, 2)
        if a[0] < b[2] - pay and b[0] < a[2] - pay and a[1] < b[3] - pay and b[1] < a[3] - pay
    )


class Girdi(unittest.TestCase):
    def test_alanlar(self):
        a = alanlar.ALAN["kuyu_duzeni"]
        self.assertEqual(
            (a.secenekler, a.varsayilan, a.proje_geneli, a.gelismis),
            (("Ayrı", "Tek kuyu"), "Ayrı", True, False),
        )
        self.assertEqual(a.grup, "Kuyu ve katlar")
        for k in ("soldaki_asansor", "ayirma_kirisi"):
            self.assertEqual((alanlar.ALAN[k].kuyu, alanlar.ALAN[k].proje_geneli), ("tek", True), k)
        self.assertEqual(alanlar.ALAN["ayirma_kirisi"].secenekler, alanlar.AYIRMA_KIRISLERI)
        self.assertTrue(set(alanlar.AYIRMA_KIRISLERI) <= set(makine.NPU))
        for k in alanlar.KUYU_ORTAK:
            self.assertEqual((alanlar.ALAN[k].kuyu, alanlar.ALAN[k].proje_geneli), ("ortak", False), k)
        #  Asansörün kendi bölmesi ortak değil;  1. adımın alanları kalktı
        self.assertNotIn("kuyu_genisligi", alanlar.KUYU_ORTAK)
        self.assertFalse({"grup_sirasi", "grup_arasi"} & set(alanlar.ALAN))

    def test_form_sozlesmesi(self):
        kd = uygulama_istegi.alanlar()["kuyu_duzeni"]
        self.assertEqual(
            kd,
            {
                "alan": "kuyu_duzeni",
                "tek": "Tek kuyu",
                "ortak": sorted(alanlar.KUYU_ORTAK),
                "gizli": ["ayirma_kirisi", "soldaki_asansor"],
            },
        )

    def test_kapi_kuyunun_ortaklarini_esitler(self):
        v = ikili()
        v["asansorler"][1].update(kuyu_derinligi=1234, kuyu_duvar_on=99, kuyu_genisligi=1900)
        a, o = uygulama_istegi.asansor_girdileri(v)
        for k in alanlar.KUYU_ORTAK:
            self.assertEqual(a[1].get(k), a[0].get(k), k)
        #  Asansöre ait olan kalır;  tek kuyunun seçimleri projede
        self.assertEqual(a[1]["kuyu_genisligi"], 1900)
        self.assertEqual((o["kuyu_duzeni"], o["soldaki_asansor"], o["ayirma_kirisi"]), ("Tek kuyu", 1, 140))

    def test_kapi_iki_asansor_ve_tek_kuyu_disinda_okumaz(self):
        v = ikili()
        v["asansorler"][1]["kuyu_derinligi"] = 1234
        for a in (v["asansorler"][:1], v["asansorler"] + [copy.deepcopy(v["asansorler"][0])]):
            _a, o = uygulama_istegi.asansor_girdileri(dict(v, asansorler=a))
            self.assertEqual(
                (o.get("kuyu_duzeni"), o.get("soldaki_asansor"), o.get("ayirma_kirisi")), (None,) * 3
            )
        a, o = uygulama_istegi.asansor_girdileri(ikili(duzen="Ayrı"))
        self.assertEqual(
            (o["kuyu_duzeni"], o.get("soldaki_asansor"), o.get("ayirma_kirisi")), ("Ayrı", None, None)
        )
        #  Ayrı kuyuda kuyunun değerleri asansör başına kalır
        w = ikili(duzen="Ayrı")
        w["asansorler"][1]["kuyu_derinligi"] = 1234
        a, _o = uygulama_istegi.asansor_girdileri(w)
        self.assertEqual(a[1]["kuyu_derinligi"], 1234)

    def test_kopru_kuyudaki_yer_ve_kiris(self):
        for soldaki, yerler in ((1, (1, 2)), (2, (2, 1))):
            gler = gecerli(ikili(soldaki=soldaki))
            self.assertEqual(tuple(g["proje"]["grup_sirasi"] for g in gler), yerler)
            for g in gler:
                yan = "Sağ" if g["proje"]["grup_sirasi"] == 1 else "Sol"
                self.assertEqual((g["kuyu"]["acik_yan"], g["proje"]["ayirma_kirisi"]), (yan, 140))
                self.assertEqual(g["kuyu"]["duvar_sag" if yan == "Sağ" else "duvar_sol"], 140.0)
        for g in gecerli(ikili(duzen="Ayrı")):
            self.assertEqual((g["proje"]["grup_sirasi"], g["proje"]["ayirma_kirisi"]), (None, None))
            self.assertNotIn("acik_yan", g["kuyu"])

    def test_hesap_motoru_numarayi_girdiden_alir(self):
        #  Hesap çizimden ölçerken köprüyü sırasız çağırır ( sira = 1 ):  numara girdide
        a, o = uygulama_istegi.asansor_girdileri(ikili())
        A = uygulama_girdisi.tamamla({**uygulama_girdisi.varsayilanlar(), **o, **a[1], **o, "_asansor_no": 2})
        g, hata = kopru.cizim_girdisi(A)
        self.assertEqual((hata, g["proje"]["grup_sirasi"], g["kuyu"]["acik_yan"]), ([], 2, "Sol"))


class Denetim(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gler = kuyudakiler(ikili())

    def test_kiris_secilmeli(self):
        self.assertEqual(grup.duzen_hatalari(self.gler), [])
        self.assertEqual(grup.duzen_hatalari(kuyudakiler(ikili(kiris=None))), [grup.KIRIS_YOK])

    def test_kuyu_boyunca_perde_gerekirse_soylenir(self):
        #  m.5.2.5.5.2.2:  korkuluğun iç kenarı komşunun kabinine 0,50 m'den yakın
        self.assertGreaterEqual(grup.korkuluk_mesafesi(self.gler)[0], 500)
        dar = copy.deepcopy(self.gler)
        dar[1]["kabin"]["kaciklik_y"] -= 650
        self.assertLess(grup.korkuluk_mesafesi(dar)[0], 500)
        self.assertIn("perde kuyu boyunca uzanmalı ( m.5.2.5.5.2.2 )", " ".join(grup.duzen_hatalari(dar)))

    def test_projenin_sorunlari(self):
        self.assertEqual(grup.sorunlar([None, self.gler[1]]), [])
        self.assertEqual(grup.sorunlar(gecerli(ikili(kiris=None))), [grup.KIRIS_YOK])
        self.assertEqual(grup.sorunlar(gecerli(ikili(duzen="Ayrı"))), [])


class Plan(unittest.TestCase):
    """LiftDesigner 12744-3 düzeni tek düzlemde:  iki asansör, ağırlıklar arkada,
    dış duvarlar 250, arada NPU 140."""

    @classmethod
    def setUpClass(cls):
        cls.gler = kuyudakiler(ikili())
        cls.e = grup.plan(cls.gler)
        k1, k2 = cls.gler[0]["kuyu"], cls.gler[1]["kuyu"]
        cls.G1, cls.G2, cls.D = k1["genislik"], k2["genislik"], k1["derinlik"]
        cls.X1 = cls.G1 + 140
        cls.sol, cls.sag = -250, cls.X1 + cls.G2 + 250

    def test_duvarlar_bir_kez_tek_kuyu_ortada_kiris(self):
        duvar = [(x["x"], x["y"], x["g"], x["d"]) for x in self.e if x["katman"] == "KUYU-DUVAR"]
        self.assertEqual(
            sorted(duvar), sorted((x["x"], x["y"], x["g"], x["d"]) for x in self.e if x["tip"] == "tarama")
        )
        #  Ön duvar üç parça ( iki kapı boşluğu, kapıların arası dolu ), arka, sol, sağ
        self.assertEqual(len(duvar), 6)
        self.assertIn((self.sol, self.D, self.sag - self.sol, 250), duvar)
        self.assertEqual([d for d in duvar if self.G1 - 1 < d[0] < self.X1 + 1 and d[1] == 0], [])
        ic = [(x["x"], x["y"], x["g"], x["d"]) for x in self.e if x["katman"] == "KUYU-IC"]
        self.assertEqual(ic, [(0, 0, self.X1 + self.G2, self.D)])
        (kiris,) = [x for x in self.e if x.get("ad") == "ayirma_kirisi"]
        self.assertEqual(
            (kiris["katman"], kiris["x"], kiris["y"], kiris["g"], kiris["d"]),
            ("KONSOL", self.G1, 0, 140, self.D),
        )
        self.assertTrue(any(x["tip"] == "yazi" and x["metin"] == "AYIRMA KİRİŞİ  NPU 140" for x in self.e))

    def test_dista_duvarlar_bolmeler_kiris_ayracta_toplam(self):
        zincir = [
            olculer(self.e, a)[0]
            for a in (
                "grup_duvar_sol",
                "grup_kuyu_1",
                "grup_ayirma_kirisi_1",
                "grup_kuyu_2",
                "grup_duvar_sag",
            )
        ]
        self.assertEqual(
            [o["metin"] for o in zincir], ["250", f"SW{self.G1:g}", "140", f"SW{self.G2:g}", "250"]
        )
        self.assertEqual(len({o["kot"] for o in zincir}), 1)
        (toplam,) = olculer(self.e, "grup_genisligi")
        self.assertEqual(toplam["metin"], f"({self.sag - self.sol:g})")
        self.assertEqual(toplam["kot"], zincir[0]["kot"] + geometri.SIRA_ARASI)
        for a in ("duvar_sol", "kuyu_genisligi", "duvar_sag"):
            self.assertEqual(olculer(self.e, a), [])
        self.assertEqual(
            max(x["kot"] for x in self.e if x["tip"] == "olcu" and x["yon"] == "yatay"), toplam["kot"]
        )

    def test_yan_olculer_dis_yanlarda_kesit_isareti_yok(self):
        dusey = [x["kot"] for x in self.e if x["tip"] == "olcu" and x["yon"] == "dusey"]
        self.assertEqual([k for k in dusey if self.sol <= k <= self.sag], [])
        sd = sorted(x["kot"] for x in self.e if x["tip"] == "olcu" and x["metin"] == f"SD{self.D:g}")
        self.assertEqual(len(sd), 2)
        self.assertTrue(sd[0] < self.sol and sd[1] > self.sag)
        self.assertEqual([x for x in self.e if x["katman"] == "KESIT"], [])

    def test_ortaya_bakan_konsollar_kirise_dayanir(self):
        plaka = [geometri.sinir([x]) for x in self.e if x.get("ad") == "plaka"]
        self.assertTrue(any(abs(b[2] - self.G1) < 0.5 for b in plaka))
        self.assertTrue(any(abs(b[0] - self.X1) < 0.5 for b in plaka))

    def test_adlar_en_ustte_soldaki_asansor_solda(self):
        def adlar(e):
            return [
                (x["metin"], x["x"])
                for x in e
                if x["tip"] == "yazi" and x["metin"] in ("ASANSÖR 1", "ASANSÖR 2")
            ]

        a = [x for x in self.e if x["tip"] == "yazi" and x["metin"].startswith("ASANSÖR ")]
        self.assertEqual(adlar(self.e), [("ASANSÖR 1", self.G1 / 2), ("ASANSÖR 2", self.X1 + self.G2 / 2)])
        for x in a:
            self.assertGreater(geometri.sinir([x])[1], geometri.sinir([y for y in self.e if y not in a])[3])
        #  Soldaki 2 numara ( 12744-3 gibi ):  kuyunun solunda ASANSÖR 2
        ters = kuyudakiler(ikili(soldaki=2))
        self.assertEqual([g["proje"]["asansor"] for g in ters], ["ASANSÖR 2", "ASANSÖR 1"])
        self.assertEqual(
            [m for m, _x in sorted(adlar(grup.plan(ters)), key=lambda t: t[1])], ["ASANSÖR 2", "ASANSÖR 1"]
        )

    def test_baslik_kesitlerin_harfiyle_not_asansor_asansor(self):
        self.assertTrue(grup.baslik(self.gler).startswith("KUYU GRUBU PLANI  C-C"))
        gler = copy.deepcopy(self.gler)
        gler[0]["proje"]["hesap_uygun_degil"] = []
        gler[1]["proje"]["hesap_uygun_degil"] = [
            {"kimlik": "tamponlar", "ad": "Tamponlar", "metin": "", "eksik": False, "parcalar": []}
        ]
        self.assertEqual(
            grup.uyari(gler),
            ["ASANSÖR 2  —  HESAP:  1 bölüm UYGUN DEĞİLDİR  —  bkz. hesap raporu", "Tamponlar"],
        )
        gler[1]["proje"]["hesap_uygun_degil"] = []
        self.assertEqual(grup.uyari(gler), [])

    def test_kirissiz_plan_cizilmez(self):
        with self.assertRaises(ValueError):
            grup.plan(kuyudakiler(ikili(kiris=None)))


class Yerlesim(unittest.TestCase):
    """Her asansörün parçası kirişin kendi yarısında ( eksenler kirişin ortasında
    biter, yazılar ve etiketler komşunun yerine kaçmaz;  kiriş yazılara duvar
    sayılır );  kuyunun planı yeni yazı çakışması getirmez.  Tarama 1 Kas:  4 kabin
    çifti × 9 ağırlık yeri × MRL / MD × NPU 100 / 140 — kurulan 80 düzende taşan 0,
    yeni çakışma 0."""

    DUZENLER = (
        dict(),
        dict(Q1=630, yer1="Sağ", Q2=800, yer2="Sol", kat_kapisi_tipi="Manuel Sol"),
        dict(Q1=800, yer1="Sol", Q2=1275, yer2="Sağ", kiris=100),
        dict(Q1=1000, yer1="Sağ", Q2=630, yer2="Sol"),
    )

    @classmethod
    def setUpClass(cls):
        cls.gruplar = [kuyudakiler(ikili(**d)) for d in cls.DUZENLER]

    def test_her_asansorun_parcasi_kendi_yarisinda(self):
        for gler in self.gruplar:
            self.assertEqual(yarisindan_tasan(gler), [])

    def test_yeni_yazi_cakismasi_yok(self):
        for gler in self.gruplar:
            tek = sum(cakisan_yazilar(cizimler.CIZIMLER["kuyu_plani"][1](g)) for g in gler)
            self.assertLessEqual(cakisan_yazilar(grup.plan(gler)), tek)

    def test_alt_siralar_ayni_hizada(self):
        #  Menteşeli kapının yayı birincinin sıralarını aşağı iter;  ikincininkiler de iner
        gler = self.gruplar[1]
        e = grup.plan(gler)
        G1 = gler[0]["kuyu"]["genislik"]
        alt = {n: set() for n in (0, 1)}
        for x in e:
            if x["tip"] == "olcu" and x["yon"] == "yatay" and x["kot"] < -gler[0]["kuyu"]["duvar_on"]:
                alt[0 if x["b"][0] <= G1 else 1].add(x["kot"])
        self.assertEqual(len(alt[0]), 2)
        self.assertEqual(alt[0], alt[1])
        self.assertLess(min(alt[0]), geometri.olcu_alti(gler[1]) - 120)

    def test_ayri_kuyuda_cizimler_kuyu_duzeninden_etkilenmez(self):
        #  "Ayrı" seçili iki asansörlü projede asansörün çizimleri seçimsizkiyle aynı
        v = ikili(duzen="Ayrı")
        w = copy.deepcopy(v)
        for k in ("kuyu_duzeni", "soldaki_asansor", "ayirma_kirisi"):
            w["proje_geneli"].pop(k)
        g, h = gecerli(v)[0], gecerli(w)[0]
        for ad in pafta.sira(g):
            ciz = cizimler.CIZIMLER[ad][1]
            self.assertEqual(json.dumps(ciz(g), sort_keys=True), json.dumps(ciz(h), sort_keys=True), ad)


class AsansorunCizimleri(unittest.TestCase):
    """Tek kuyuda asansörün KENDİ çizimleri — açık yanda duvar yok, ayırma kirişi
    ( planlar, B-B'de kesiti, A-A'da görünüşü — ortaya bakan rayların konsol
    kotlarında );  iki kuyu dibinin arasında perde ( m.5.2.5.5.2.1 ).  Soldaki
    asansörün sağı, sağdakinin solu açık."""

    @classmethod
    def setUpClass(cls):
        cls.gler = kuyudakiler(ikili())
        cls.npu = makine.npu(140)

    def _ciz(self, n, ad):
        return cizimler.CIZIMLER[ad][1](self.gler[n])

    def _kiris_yeri(self, n):
        k = self.gler[n]["kuyu"]
        return k["genislik"] if n == 0 else -k["duvar_sol"]

    def test_planlarda_acik_yanda_duvar_yok_kiris_var(self):
        for n in (0, 1):
            k, x = self.gler[n]["kuyu"], self._kiris_yeri(n)
            e = self._ciz(n, "kuyu_plani")
            yan = [el for el in e if el["katman"] == "KUYU-DUVAR" and abs(el["x"] - x) < 0.5 and el["y"] == 0]
            self.assertEqual(yan, [])  # ön ve arka duvar kirişin ötesine uzanır, yan duvar yok
            (kiris,) = [el for el in e if el.get("ad") == "ayirma_kirisi"]
            self.assertEqual((kiris["x"], kiris["y"], kiris["g"], kiris["d"]), (x, 0, 140, k["derinlik"]))
            self.assertTrue(any(el.get("ad") == "ayirma_kirisi_adi" for el in e))
            for ad in ("kabin_ustu", "kuyu_dibi", "kuyu_ustu"):
                self.assertEqual(sum(el.get("ad") == "ayirma_kirisi" for el in self._ciz(n, ad)), 1, (n, ad))

    def test_kuyu_dibi_planinda_perde_aranin_ortasinda(self):
        for n in (0, 1):
            k = self.gler[n]["kuyu"]
            (p,) = [el for el in self._ciz(n, "kuyu_dibi") if el.get("ad") == "grup_perdesi"]
            xm = self._kiris_yeri(n) + 70
            self.assertEqual((p["x1"], p["y1"], p["x2"], p["y2"]), (xm, 0, xm, k["derinlik"]))

    def test_on_kesitte_kiris_kesitleri_ve_perde(self):
        for n in (0, 1):
            g = self.gler[n]
            Y = kuyu_kesiti.yerlesim(g)
            kotlar = kuyu_kesiti.ayirma_kirisi_kotlari(g, Y["M"])
            self.assertTrue(kotlar)
            e = self._ciz(n, "kuyu_kesiti_on")
            G, dg = g["kuyu"]["genislik"], g["kuyu"]["duvar_sag"]
            u0 = -dg if n == 0 else G  # B-B arkadan bakar:  plandaki sağ solda
            kirisler = [el for el in e if el.get("ad") == "ayirma_kirisi"]
            self.assertEqual(sorted(round(el["y"] + el["d"], 3) for el in kirisler), kotlar)
            for el in kirisler:
                self.assertEqual((el["x"], el["g"], el["d"]), (u0, 140, self.npu["b"]))
                self.assertTrue(el["bicim"][0]["dolu"])
            #  O yanda tam boy duvar yok;  kuyu dibi döşemesi aranın altından geçer
            duvar = [el for el in e if el["katman"] == "KUYU-DUVAR"]
            self.assertEqual([el for el in duvar if abs(el["x"] - u0) < 0.5 and el["d"] > 5000], [])
            taban = Y["taban"]
            self.assertTrue(
                any(abs(el["y"] + el["d"] - taban) < 0.5 and el["g"] >= G + 140 - 0.5 for el in duvar)
            )
            (p,) = [el for el in e if el.get("ad") == "grup_perdesi"]
            self.assertEqual((p["y1"], p["y2"]), (taban + 300, Y["kotlar"][0] + 2500))
            self.assertEqual(p["x1"], u0 + 70)

    def test_yan_kesitte_kirisler_yalniz_bakilan_yanda(self):
        #  A-A kabin ekseninden sağa bakar ( ağırlıklar arkada ):  soldakinin açık yanı
        #  görünür, sağdakininki bakanın arkasında
        self.assertTrue(any(el.get("ad") == "ayirma_kirisi" for el in self._ciz(0, "kuyu_kesiti_yan")))
        self.assertTrue(any(el.get("ad") == "grup_perdesi" for el in self._ciz(0, "kuyu_kesiti_yan")))
        sagdaki = self._ciz(1, "kuyu_kesiti_yan")
        self.assertFalse(any(el.get("ad") in ("ayirma_kirisi", "grup_perdesi") for el in sagdaki))

    def test_kiris_kotlari_ortaya_bakan_raylarin_konsollari(self):
        g = self.gler[0]
        M = kuyu_kesiti.yerlesim(g)["M"]
        kx = g["kuyu"]["genislik"] / 2 + g["kabin"]["kaciklik_y"]
        sag = [r for r in M["raylar"] if r["tur"] == "kabin" and (r["kutu"][0] + r["kutu"][2]) / 2 > kx]
        self.assertEqual(len(sag), 1)
        self.assertEqual(
            kuyu_kesiti.ayirma_kirisi_kotlari(g, M), sorted(round(z, 3) for z in sag[0]["konsollar"])
        )
        ayri = gecerli(ikili(duzen="Ayrı"))[0]
        self.assertEqual(kuyu_kesiti.ayirma_kirisi_kotlari(ayri, kuyu_kesiti.yerlesim(ayri)["M"]), [])


class EkranVePaket(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v = ikili()

    def test_ekranda_kuyunun_plani_once_tiklanmaz(self):
        for i in (0, 1):
            d = yanit(self.v, i)
            self.assertTrue(d["aktif"], d.get("hata"))
            c = d["cizimler"][0]
            self.assertEqual((c["ad"], c["olcek"]), (grup.AD, 20))
            self.assertIn("KUYU GRUBU PLANI  C-C", c["baslik"])
            self.assertNotIn("data-olcu", c["svg"])
            self.assertNotIn(grup.AD, [x["ad"] for x in d["cizimler"][1:]])
        self.assertNotIn(grup.AD, [x["ad"] for x in yanit(ikili(duzen="Ayrı"))["cizimler"]])

    def test_kuyunun_sorunu_ekranda_ve_paketi_durdurur(self):
        v = ikili(kiris=None)
        for i in (0, 1):
            d = yanit(v, i)
            self.assertFalse(d["aktif"])
            self.assertIn(grup.KIRIS_YOK, d["hata"])
            self.assertNotIn(grup.AD, [x["ad"] for x in d["cizimler"]])
        p = json.loads(uygulama_uclari.indir_uygulama_dwg(v).body)
        self.assertIn(grup.KIRIS_YOK, p["hata"])

    def test_obur_asansorun_sorunu_kuyunun_planini_durdurur(self):
        #  630 kg, ağırlık arkada, makine dairesiz:  kabin üstüne çömelme sığınması sığmaz
        d = yanit(ikili(Q1=630, Q2=800), 1)
        self.assertFalse(d["aktif"])
        self.assertIn("Tek kuyunun planı çizilemedi:  ASANSÖR 1 çiziminde sorun var.", d["hata"])
        self.assertNotIn(grup.AD, [x["ad"] for x in d["cizimler"]])

    def test_paftada_kuyunun_plani_once_kunyeler_esit(self):
        gler = gecerli(self.v)
        b, k = pafta.bloklar(gler), pafta.kunyeler(gler)
        self.assertEqual(len(b), len(k))
        self.assertEqual(b[0][0], grup.AD)
        self.assertEqual(k[0], {"proje": "DENEME", "asansor": "ASANSÖR 1  ·  ASANSÖR 2"})
        self.assertEqual(b[1][0], "kuyu_kesiti_yan_1")
        gler[0]["proje"]["ayirma_kirisi"] = gler[1]["proje"]["ayirma_kirisi"] = None
        with self.assertRaises(ValueError):
            pafta.bloklar(gler)


if __name__ == "__main__":
    unittest.main()

"""KUYU GRUBU ( cizim/grup.py — 1 Kas;  plan cikti/devir/ORTAK_KUYU_PLANI.md, 1. adım ).

· girdi:  "Kuyu grubundaki sırası" köprüde g["proje"]["grup_sirasi"];  kapı tam sayı,
  en çok 2 ister;  boşsa asansör ayrı kuyudadır
· denetim:  sıralar ( tek asansör, aynı sıra ) ve kuyuların uyumu ( derinlik, ön ve
  arka duvar, ortak duvar, durak kotları ) iletileriyle
· plan:  12744-3 düzeni ( ağırlıklar arkada, dış duvarlar 250, ara 100 ):  duvarlar bir
  kez, en dışta 250 · SW · 100 · SW · 250 ve ayraçta toplam, yan ölçüler dış yanlarda,
  kesit işareti yok, adlar en üstte;  her asansörün parçası ortak duvarın kendi
  yarısında, grup yeni yazı çakışması getirmez, alt sıralar aynı hizada
· ekran, pafta ve paket:  grubun planı önde ( ekranda tıklanmaz ), sorunları ekranda
  söylenir ve paketi durdurur;  gruptaki asansörün kendi çizimleri değişmez
"""

import copy
import itertools
import json
import unittest

from cizim import cizimler
from cizim import geometri
from cizim import grup
from cizim import pafta
from motor.uygulama import uygulama_hesabi
from tasarim import alanlar
from testler.test_yerlesim_saglamligi import KABIN, duzen_girdisi, standart_istek
from uclar import cizim_uclari
from uclar import uygulama_istegi
from uclar import uygulama_uclari


def ikili(Q1=1000, yer1="Arka", Q2=800, yer2="Arka", ara=100, **ek):
    """İki asansörlü, makine dairesiz grup isteği:  standart asansörler ( dış duvarlar
    250, aradaki duvar `ara`, kuyular aynı derinlikte;  arkadaki ağırlıkta askı kabin
    üstü, makine bina yapısında, son kat 5.000 — test_yerlesim_saglamligi.gecerli_duzen gibi ).
    ek:  birinci asansöre eklenecek girdiler."""
    a = []
    for Q, yer in ((Q1, yer1), (Q2, yer2)):
        x = standart_istek(Q, True, yer)["asansorler"][0]
        if yer == "Arka":
            x.update(aski_duzeni="Kabin üstü", makine_raya_biniyor="Bina yapısına", son_kat_yuksekligi=5000)
        x.update(kuyu_duvar_kalinligi=250)
        a.append(x)
    D = max(KABIN[Q][1] + (700 if y == "Arka" else 450) for Q, y in ((Q1, yer1), (Q2, yer2)))
    a[0].update(kuyu_derinligi=D, kuyu_duvar_sag=ara, grup_sirasi=1, **ek)
    a[1].update(kuyu_derinligi=D, kuyu_duvar_sol=ara, grup_sirasi=2)
    return {"asansorler": a, "proje_geneli": {"mk_yok": True}, "sabitler": {}, "asansor": 0}


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


def cakisan_yazilar(e, pay=2.0):
    k = _yazi_kutulari(e)
    return sum(
        1
        for a, b in itertools.combinations(k, 2)
        if a[0] < b[2] - pay and b[0] < a[2] - pay and a[1] < b[3] - pay and b[1] < a[3] - pay
    )


class Girdi(unittest.TestCase):
    def test_alan_kuyu_ve_katlarda_tam_sayi_en_cok_iki(self):
        a = alanlar.ALAN["grup_sirasi"]
        self.assertEqual(
            (a.grup, a.sozlesme, a.tam_sayi, alanlar.AZAMI["grup_sirasi"]),
            ("Kuyu ve katlar", alanlar.CIZ, True, 2),
        )
        self.assertFalse(a.proje_geneli)

    def test_kopru_okur_bossa_ayri_kuyu(self):
        v = standart_istek(800, True, "Sağ", grup_sirasi="2")
        g, _A, hata = duzen_girdisi(v)
        self.assertEqual((hata, g["proje"]["grup_sirasi"]), ([], 2))
        self.assertIsInstance(g["proje"]["grup_sirasi"], int)
        g, _A, _h = duzen_girdisi(standart_istek(800, True, "Sağ"))
        self.assertIsNone(g["proje"]["grup_sirasi"])

    def test_kapi_tam_sayi_ve_en_cok_iki_ister(self):
        for deger, ileti in (("3", "en çok 2"), ("1,5", "tam sayı")):
            with self.assertRaises(uygulama_istegi.GecersizGirdi) as h:
                uygulama_istegi.asansor_girdileri(standart_istek(800, True, "Sağ", grup_sirasi=deger))
            self.assertIn(ileti, " ".join(h.exception.hatalar))


class Denetim(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gler = gecerli(ikili())

    def test_uyeler_soldan_saga(self):
        self.assertEqual(grup.uyeler([None, 2, 1]), [2, 1])
        self.assertEqual(grup.uyeler([None, None]), [])

    def test_sira_hatalari(self):
        ad = ["A", "B", "C"]
        self.assertEqual(grup.sira_hatalari([None, None, None], ad), [])
        self.assertEqual(grup.sira_hatalari([1, None, 2], ad), [])
        self.assertIn("tek asansör var ( B )", grup.sira_hatalari([None, 2, None], ad)[0])
        self.assertIn("sırası aynı ( 1 ):  A · C", grup.sira_hatalari([1, 2, 1], ad)[0])
        self.assertIn("en çok 2", " ".join(grup.sira_hatalari([1, 2, 3], ad)))

    def test_uyumlu_grupta_sorun_yok(self):
        self.assertEqual(grup.duzen_hatalari(self.gler), [])

    def _hata(self, degistir):
        gler = copy.deepcopy(self.gler)
        degistir(gler)
        return " ".join(grup.duzen_hatalari(gler))

    def test_kuyularin_uyumu(self):
        def kuyu(n, k, d):
            return lambda gler: gler[n]["kuyu"].__setitem__(k, d)

        for degistir, ileti in (
            (kuyu(1, "derinlik", 9000), "aynı derinlikte olmalı:  ASANSÖR 1"),
            (kuyu(0, "duvar_on", 200), "ön duvarı ( kapıların duvarı ) aynı kalınlıkta"),
            (kuyu(1, "duvar_arka", 200), "arka duvarı aynı kalınlıkta"),
            (kuyu(0, "duvar_sag", 250), "ASANSÖR 1 sağ duvarı 250 · ASANSÖR 2 sol duvarı 100"),
        ):
            self.assertIn(ileti, self._hata(degistir))

    def test_duraklar_ayni_kotlarda(self):
        def az(gler):
            gler[1]["dusey"]["durak_adedi"] -= 1

        def yuksek(gler):
            gler[1]["dusey"]["kat_yuksekligi"] = gler[1]["dusey"]["kat_yuksekligi"] + 200

        self.assertIn("durakları aynı olmalı:  ASANSÖR 1 8 durak · ASANSÖR 2 7 durak", self._hata(az))
        self.assertIn("aynı kotlarda olmalı:  2. durak", self._hata(yuksek))

    def test_projenin_sorunlari_kurulamayan_asansorde_uyumu_atlar(self):
        ad = ["ASANSÖR 1", "ASANSÖR 2"]
        self.assertEqual(grup.sorunlar([1, 2], ad, [self.gler[0], None]), [])
        self.assertIn("tek asansör", grup.sorunlar([1, None], ad, self.gler)[0])


class Plan(unittest.TestCase):
    """LiftDesigner 12744-3 düzeni:  iki asansör, ağırlıklar arkada, ara duvar 100."""

    @classmethod
    def setUpClass(cls):
        cls.gler = gecerli(ikili())
        cls.e = grup.plan(cls.gler)
        k1, k2 = cls.gler[0]["kuyu"], cls.gler[1]["kuyu"]
        cls.G1, cls.G2, cls.D = k1["genislik"], k2["genislik"], k1["derinlik"]
        cls.X1 = cls.G1 + 100
        cls.sol, cls.sag = -250, cls.X1 + cls.G2 + 250

    def _dik(self, katman, tip="dikdortgen"):
        return [(x["x"], x["y"], x["g"], x["d"]) for x in self.e if x["katman"] == katman and x["tip"] == tip]

    def test_duvarlar_bir_kez_kuyularin_ici_bos(self):
        duvar = self._dik("KUYU-DUVAR")
        self.assertEqual(sorted(duvar), sorted(self._dik("TARAMA", "tarama")))
        #  Ön duvar üç parça ( iki kapı boşluğu ), arka boydan boya, sol, ara, sağ
        self.assertEqual(len(duvar), 7)
        self.assertIn((self.sol, self.D, self.sag - self.sol, 250), duvar)
        self.assertEqual([d for d in duvar if d[0] == self.G1], [(self.G1, 0, 100, self.D)])
        self.assertEqual(
            sorted(self._dik("KUYU-IC")), [(0, 0, self.G1, self.D), (self.X1, 0, self.G2, self.D)]
        )
        for x, y, g_, d_ in duvar:
            for x0, G in ((0, self.G1), (self.X1, self.G2)):
                self.assertFalse(x < x0 + G and x0 < x + g_ and y < self.D and 0 < y + d_, (x, y, g_, d_))

    def test_dista_duvarlar_ve_kuyular_zinciri_ayracta_toplam(self):
        zincir = [
            olculer(self.e, a)[0]
            for a in ("grup_duvar_sol", "grup_kuyu_1", "grup_ara_duvar_1", "grup_kuyu_2", "grup_duvar_sag")
        ]
        self.assertEqual(
            [o["metin"] for o in zincir], ["250", f"SW{self.G1:g}", "100", f"SW{self.G2:g}", "250"]
        )
        self.assertEqual(len({o["kot"] for o in zincir}), 1)
        (toplam,) = olculer(self.e, "grup_genisligi")
        self.assertEqual(toplam["metin"], f"({self.sag - self.sol:g})")
        self.assertEqual(toplam["kot"], zincir[0]["kot"] + geometri.SIRA_ARASI)
        #  Asansörlerin kendi en dış sırası grubun zincirine geçti
        for a in ("duvar_sol", "kuyu_genisligi", "duvar_sag"):
            self.assertEqual(olculer(self.e, a), [])
        ust = max(x["kot"] for x in self.e if x["tip"] == "olcu" and x["yon"] == "yatay")
        self.assertEqual(ust, toplam["kot"])

    def test_yan_olculer_dis_yanlarda_kesit_isareti_yok(self):
        dusey = [x["kot"] for x in self.e if x["tip"] == "olcu" and x["yon"] == "dusey"]
        ara = [k for k in dusey if self.sol <= k <= self.sag]
        self.assertEqual(ara, [])
        sd = sorted(x["kot"] for x in self.e if x["tip"] == "olcu" and x["metin"] == f"SD{self.D:g}")
        self.assertEqual(len(sd), 2)
        self.assertTrue(sd[0] < self.sol and sd[1] > self.sag)
        self.assertEqual([x for x in self.e if x["katman"] == "KESIT"], [])

    def test_adlar_en_ustte_kuyularin_ortasinda(self):
        adlar = [x for x in self.e if x["tip"] == "yazi" and x["metin"] in ("ASANSÖR 1", "ASANSÖR 2")]
        self.assertEqual(
            [(x["metin"], x["x"]) for x in adlar],
            [("ASANSÖR 1", self.G1 / 2), ("ASANSÖR 2", self.X1 + self.G2 / 2)],
        )
        geri = [x for x in self.e if not any(x is a for a in adlar)]
        for a in adlar:
            self.assertGreater(geometri.sinir([a])[1], geometri.sinir(geri)[3])

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


class Yerlesim(unittest.TestCase):
    """Her asansörün parçası ortak duvarın kendi yarısında ( eksenler duvarın ortasında
    biter, yazılar ve etiketler komşu kuyuya kaçmaz );  grup yeni yazı çakışması
    getirmez.  Tarama 1 Kas:  4 kabin çifti × 9 ağırlık yeri × MRL / MD × ara 100 / 250
    — kurulan 96 düzende taşan 0, yeni çakışma 0."""

    DUZENLER = (
        dict(),
        dict(Q1=630, yer1="Sağ", Q2=800, yer2="Sol", ara=250, kat_kapisi_tipi="Manuel Sol"),
        dict(Q1=800, yer1="Sol", Q2=1275, yer2="Sağ"),
    )

    @classmethod
    def setUpClass(cls):
        cls.gruplar = [gecerli(ikili(**d)) for d in cls.DUZENLER]

    def test_her_asansorun_parcasi_kendi_yarisinda(self):
        for gler in self.gruplar:
            alt = min(geometri.olcu_alti(g) for g in gler)
            for n, g in enumerate(gler):
                komsu, komsu_g = ("Sağ", gler[1]) if n == 0 else ("Sol", gler[0])
                k = g["kuyu"]
                orta = k["genislik"] + k["duvar_sag"] / 2 if komsu == "Sağ" else -k["duvar_sol"] / 2
                ust, alt_ = k["derinlik"] + k["duvar_arka"], -k["duvar_on"]
                for x in grup._asansorun_plani(g, komsu, komsu_g, alt):
                    if x["tip"] == "olcu" and x["yon"] == "yatay" and not alt_ <= x["kot"] <= ust:
                        continue  # üst ve alt sıralar grupça yerleşir
                    b = geometri.sinir([x])
                    with self.subTest(n=n, tip=x["tip"], ad=x.get("ad"), metin=x.get("metin")):
                        self.assertTrue(b[2] <= orta + 1 if komsu == "Sağ" else b[0] >= orta - 1, b)

    def test_grup_yeni_yazi_cakismasi_getirmez(self):
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

    def test_gruptaki_asansorun_kendi_cizimleri_degismez(self):
        g = self.gruplar[0][0]
        tek = copy.deepcopy(g)
        tek["proje"]["grup_sirasi"] = None
        for ad in pafta.sira(g):
            ciz = cizimler.CIZIMLER[ad][1]
            self.assertEqual(json.dumps(ciz(g), sort_keys=True), json.dumps(ciz(tek), sort_keys=True), ad)


class EkranVePaket(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v = ikili()

    def test_ekranda_grubun_plani_once_tiklanmaz(self):
        for i in (0, 1):
            d = yanit(self.v, i)
            self.assertTrue(d["aktif"], d.get("hata"))
            c = d["cizimler"][0]
            self.assertEqual((c["ad"], c["olcek"]), (grup.AD, 20))
            self.assertIn("KUYU GRUBU PLANI  C-C", c["baslik"])
            self.assertNotIn("data-olcu", c["svg"])
            self.assertNotIn(grup.AD, [x["ad"] for x in d["cizimler"][1:]])
        w = copy.deepcopy(self.v)
        for a in w["asansorler"]:
            a.pop("grup_sirasi")
        self.assertNotIn(grup.AD, [x["ad"] for x in yanit(w)["cizimler"]])

    def test_grubun_sorunu_ekranda_ve_paketi_durdurur(self):
        v = copy.deepcopy(self.v)
        v["asansorler"][1]["kuyu_derinligi"] += 100
        d = yanit(v)
        self.assertFalse(d["aktif"])
        self.assertIn("Gruptaki kuyuların aynı derinlikte olmalı", " ".join(d["hata"]))
        self.assertNotIn(grup.AD, [x["ad"] for x in d["cizimler"]])
        p = json.loads(uygulama_uclari.indir_uygulama_dwg(v).body)
        self.assertIn("Gruptaki kuyuların aynı derinlikte olmalı", p["hata"])

    def test_obur_asansorun_sorunu_grubun_planini_durdurur(self):
        #  630 kg, ağırlık arkada, makine dairesiz:  kabin üstüne çömelme sığınması sığmaz
        v = ikili(Q1=630, Q2=800)
        d = yanit(v, 1)
        self.assertFalse(d["aktif"])
        self.assertIn("Kuyu grubunun planı çizilemedi:  ASANSÖR 1 çiziminde sorun var.", d["hata"])
        self.assertNotIn(grup.AD, [x["ad"] for x in d["cizimler"]])

    def test_paftada_grubun_plani_once_kunyeler_esit(self):
        gler = gecerli(self.v)
        b, k = pafta.bloklar(gler), pafta.kunyeler(gler)
        self.assertEqual(len(b), len(k))
        self.assertEqual(b[0][0], grup.AD)
        self.assertEqual(k[0], {"proje": "DENEME", "asansor": "ASANSÖR 1  ·  ASANSÖR 2"})
        self.assertEqual(b[1][0], "kuyu_kesiti_yan_1")
        gler[0]["kuyu"]["duvar_sag"] = 250
        with self.assertRaises(ValueError):
            pafta.bloklar(gler)


if __name__ == "__main__":
    unittest.main()

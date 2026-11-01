"""KUYU GRUBU ( cizim/grup.py — 1 Kas;  plan cikti/devir/ORTAK_KUYU_PLANI.md, 1. ve 2. adım ).

· girdi:  "Kuyu grubundaki sırası" köprüde g["proje"]["grup_sirasi"];  kapı tam sayı,
  en çok 2 ister;  boşsa asansör ayrı kuyudadır.  Grubun arası ( Açık varsayılan ·
  Duvar ) ve açık aradaki ayırma kirişi ( NPU ) proje geneli
· denetim:  sıralar ( tek asansör, aynı sıra ) ve kuyuların uyumu ( derinlik, ön ve
  arka duvar, durak kotları;  duvarlı arada ortak duvar, açık arada kiriş seçimi,
  kuyu dibi, kuyu üstü, tavan döşemesi ) iletileriyle
· duvarlı ara — 12744-3 düzeni ( ağırlıklar arkada, dış duvarlar 250, ara 100 ):
  duvarlar bir kez, en dışta 250 · SW · 100 · SW · 250 ve ayraçta toplam, yan ölçüler
  dış yanlarda, kesit işareti yok, adlar en üstte;  her asansörün parçası ortak duvarın
  kendi yarısında, grup yeni yazı çakışması getirmez, alt sıralar aynı hizada
· açık ara:  ara kirişin yüksekliği ( köprü asansörün o yanını ona çevirir ), ortada
  duvar yok, tek kuyu, ayırma kirişi ön duvardan arka duvara, zincirde kirişin ölçüsü
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
from cizim import kuyu_kesiti
from cizim import makine
from cizim import pafta
from motor.uygulama import uygulama_hesabi
from tasarim import alanlar
from testler.test_yerlesim_saglamligi import KABIN, duzen_girdisi, standart_istek
from uclar import cizim_uclari
from uclar import uygulama_istegi
from uclar import uygulama_uclari


def ikili(Q1=1000, yer1="Arka", Q2=800, yer2="Arka", ara=100, arasi="Duvar", kiris=None, **ek):
    """İki asansörlü, makine dairesiz grup isteği:  standart asansörler ( dış duvarlar
    250, aradaki duvar `ara`, kuyular aynı derinlikte;  arkadaki ağırlıkta askı kabin
    üstü, makine bina yapısında, son kat 5.000 — test_yerlesim_saglamligi.gecerli_duzen gibi ).
    arasi:  grubun arası ( "Duvar" · "Açık" ), kiris:  ayırma kirişinin NPU'su ( açıkta ).
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
    pg = {"mk_yok": True, "grup_arasi": arasi, **({"ayirma_kirisi": kiris} if kiris else {})}
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
    """Her asansörün grubun planındaki parçası ( kendi koordinatında ) ortak duvarın
    ya da açık aradaki kirişin ortasını geçmemeli:  geçen elemanlar.  Üst ve alt
    sıralar grupça yerleşir, sayılmaz."""
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
            self.assertEqual(yarisindan_tasan(gler), [])

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


class AcikAra(unittest.TestCase):
    """2. adım:  açık ara — tek kuyu, ortaya bakan raylar ayırma kirişine ( NPU 140 )
    bağlı, ara kirişin yüksekliği ( kullanıcı kararları 1 Kas )."""

    @classmethod
    def setUpClass(cls):
        cls.v = ikili(arasi="Açık", kiris=140)
        cls.gler = gecerli(cls.v)
        cls.e = grup.plan(cls.gler)
        k1, k2 = cls.gler[0]["kuyu"], cls.gler[1]["kuyu"]
        cls.G1, cls.G2, cls.D = k1["genislik"], k2["genislik"], k1["derinlik"]
        cls.X1 = cls.G1 + 140

    def test_alanlar_proje_geneli_varsayilan_acik_kirissiz(self):
        a, k = alanlar.ALAN["grup_arasi"], alanlar.ALAN["ayirma_kirisi"]
        self.assertEqual((a.varsayilan, a.secenekler, a.proje_geneli), ("Açık", ("Açık", "Duvar"), True))
        self.assertEqual((k.varsayilan, k.proje_geneli), (None, True))
        self.assertEqual(k.secenekler, alanlar.AYIRMA_KIRISLERI)
        self.assertTrue(set(k.secenekler) <= set(makine.NPU))

    def test_kopru_komsu_yani_kirisin_yuksekligi(self):
        k1, k2 = self.gler[0]["kuyu"], self.gler[1]["kuyu"]
        self.assertEqual((k1["duvar_sag"], k1["acik_yan"]), (140.0, "Sağ"))
        self.assertEqual((k2["duvar_sol"], k2["acik_yan"]), (140.0, "Sol"))
        #  Dış yanlar değişmez;  duvarlı arada duvar kutusu ( 100 ) okunur
        self.assertEqual((k1["duvar_sol"], k2["duvar_sag"]), (250.0, 250.0))
        duvarli = gecerli(ikili())[0]["kuyu"]
        self.assertEqual((duvarli["duvar_sag"], duvarli.get("acik_yan")), (100.0, None))

    def test_denetim_kiris_dip_ust_tavan(self):
        self.assertEqual(grup.duzen_hatalari(self.gler), [])
        kirissiz = gecerli(ikili(arasi="Açık"))
        self.assertIn("Açık arada ayırma kirişi seçilmeli", " ".join(grup.duzen_hatalari(kirissiz)))
        for (b, a), ne in (
            (("kuyu_dibi", "derinlik"), "kuyu dibi"),
            (("dusey", "son_kat"), "kuyu üstü"),
            (("kuyu", "tavan_dosemesi"), "tavan döşemesi"),
        ):
            gler = copy.deepcopy(self.gler)
            gler[1][b][a] += 100
            self.assertIn(f"Açık arada {ne} aynı olmalı", " ".join(grup.duzen_hatalari(gler)))
        #  Açık arada ortak duvar kutuları okunmaz:  farklı girilse de sorun yok
        v = copy.deepcopy(self.v)
        v["asansorler"][0]["kuyu_duvar_sag"] = 250
        self.assertEqual(grup.duzen_hatalari(gecerli(v)), [])

    def test_plan_ortada_duvar_yok_tek_kuyu_kiris(self):
        duvar = [x for x in self.e if x["katman"] == "KUYU-DUVAR"]
        #  Ön duvar üç parça ( iki kapı boşluğu ), arka, sol, sağ — ortada yok
        self.assertEqual(len(duvar), 6)
        self.assertEqual([x for x in duvar if self.G1 - 1 < x["x"] < self.X1 + 1], [])
        ic = [(x["x"], x["y"], x["g"], x["d"]) for x in self.e if x["katman"] == "KUYU-IC"]
        self.assertEqual(ic, [(0, 0, self.X1 + self.G2, self.D)])
        (kiris,) = [x for x in self.e if x.get("ad") == "ayirma_kirisi"]
        self.assertEqual(
            (kiris["katman"], kiris["x"], kiris["y"], kiris["g"], kiris["d"]),
            ("KONSOL", self.G1, 0, 140, self.D),
        )
        self.assertTrue(any(x["tip"] == "yazi" and x["metin"] == "AYIRMA KİRİŞİ  NPU 140" for x in self.e))
        (ara,) = olculer(self.e, "grup_ayirma_kirisi_1")
        self.assertEqual(ara["metin"], "140")
        (toplam,) = olculer(self.e, "grup_genisligi")
        self.assertEqual(toplam["metin"], f"({250 + self.X1 + self.G2 + 250:g})")

    def test_ortaya_bakan_konsollar_kirise_dayanir(self):
        plaka = [geometri.sinir([x]) for x in self.e if x.get("ad") == "plaka"]
        self.assertTrue(any(abs(b[2] - self.G1) < 0.5 for b in plaka))
        self.assertTrue(any(abs(b[0] - self.X1) < 0.5 for b in plaka))

    def test_her_asansorun_parcasi_kendi_yarisinda(self):
        self.assertEqual(yarisindan_tasan(self.gler), [])
        tek = sum(cakisan_yazilar(cizimler.CIZIMLER["kuyu_plani"][1](g)) for g in self.gler)
        self.assertLessEqual(cakisan_yazilar(self.e), tek)

    def test_kirissiz_plan_yok_ekranda_sorun(self):
        with self.assertRaises(ValueError):
            grup.plan(gecerli(ikili(arasi="Açık")))
        d = yanit(ikili(arasi="Açık"))
        self.assertFalse(d["aktif"])
        self.assertIn("Açık arada ayırma kirişi seçilmeli", " ".join(d["hata"]))
        self.assertNotIn(grup.AD, [x["ad"] for x in d["cizimler"]])
        d = yanit(self.v)
        self.assertTrue(d["aktif"], d.get("hata"))
        self.assertEqual(d["cizimler"][0]["ad"], grup.AD)

    def test_kuyu_boyunca_perde_gerekirse_soylenir(self):
        #  m.5.2.5.5.2.2:  korkuluğun iç kenarı komşunun kabinine 0,50 m'den yakın
        m = grup.korkuluk_mesafesi(self.gler)
        self.assertGreaterEqual(m[0], 500)
        dar = copy.deepcopy(self.gler)
        dar[1]["kabin"]["kaciklik_y"] -= 650
        m = grup.korkuluk_mesafesi(dar)
        self.assertLess(m[0], 500)
        self.assertIn("perde kuyu boyunca uzanmalı ( m.5.2.5.5.2.2 )", " ".join(grup.duzen_hatalari(dar)))


class AcikAraCizimleri(unittest.TestCase):
    """2. adım:  açık arada asansörün KENDİ çizimleri — o yanda duvar yok, ayırma kirişi
    ( planlar, B-B'de kesiti, A-A'da görünüşü — ortaya bakan rayların konsol kotlarında );
    iki kuyu dibinin arasında perde ( m.5.2.5.5.2.1 ).  Birinci asansör sağı, ikinci
    asansör solu açık."""

    @classmethod
    def setUpClass(cls):
        cls.gler = gecerli(ikili(arasi="Açık", kiris=140))
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
        #  A-A kabin ekseninden sağa bakar ( ağırlıklar arkada ):  birincinin açık yanı
        #  görünür, ikincininki bakanın arkasında
        self.assertTrue(any(el.get("ad") == "ayirma_kirisi" for el in self._ciz(0, "kuyu_kesiti_yan")))
        self.assertTrue(any(el.get("ad") == "grup_perdesi" for el in self._ciz(0, "kuyu_kesiti_yan")))
        self.assertFalse(
            any(el.get("ad") in ("ayirma_kirisi", "grup_perdesi") for el in self._ciz(1, "kuyu_kesiti_yan"))
        )

    def test_kiris_kotlari_ortaya_bakan_raylarin_konsollari(self):
        g = self.gler[0]
        M = kuyu_kesiti.yerlesim(g)["M"]
        kx = g["kuyu"]["genislik"] / 2 + g["kabin"]["kaciklik_y"]
        sag = [r for r in M["raylar"] if r["tur"] == "kabin" and (r["kutu"][0] + r["kutu"][2]) / 2 > kx]
        self.assertEqual(len(sag), 1)
        self.assertEqual(
            kuyu_kesiti.ayirma_kirisi_kotlari(g, M), sorted(round(z, 3) for z in sag[0]["konsollar"])
        )
        #  Duvarlı arada kiriş yok
        duvarli = gecerli(ikili())[0]
        self.assertEqual(kuyu_kesiti.ayirma_kirisi_kotlari(duvarli, kuyu_kesiti.yerlesim(duvarli)["M"]), [])


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

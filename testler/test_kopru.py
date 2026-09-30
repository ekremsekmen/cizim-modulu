"""HESAP → ÇİZİM KÖPRÜSÜ ( cizim/kopru.py ) ve birleşik programın çizim uçları.

Hesap programının kopyası hesap/ klasöründedir;  motoru ve uçları buradan
çağrılır ( sys.path'in SONUNA eklenir:  iki programın da testler/ klasörü var,
çizim modülününki önce bulunmalı )."""
import copy
import io
import json
import os
import sys
import unittest
import zipfile

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _yol in (os.path.join(KOK, "hesap"), os.path.join(KOK, "ornekler")):
    if _yol not in sys.path:
        sys.path.append(_yol)

import ezdxf                                              # noqa: E402

from api import cizim as UC_CIZIM                         # noqa: E402
from api import uygulama as UC_UYG                        # noqa: E402
from cizim import girdi as CG                             # noqa: E402
from cizim import kopru as CK                             # noqa: E402
from cizim import sabitler as CS                          # noqa: E402
from engine.uygulama import girdi as E_UGR                # noqa: E402
from engine.uygulama import hesap as E_UYG                # noqa: E402
from hesap_girdi import ASANSOR, ASANSOR_MD, ORTAK, ORTAK_MD, SABITLER    # noqa: E402


def _veri(md=False, **ek):
    return {"asansorler": [dict(ASANSOR_MD if md else ASANSOR, siginma_tipi_dip="Yatarak", **ek)],
            "proje_geneli": dict(ORTAK_MD if md else ORTAK), "sabitler": dict(SABITLER)}


def _kur(veri, proje="ÖRNEK PROJE"):
    """Programın yolu:  formun isteği → hesap → köprü.  ( [ ( g, hata ) ], sonuç, girdiler )"""
    asansorler, ortak = UC_UYG._asansor_girdileri(veri)
    s = E_UYG.hesapla_coklu(asansorler, ortak)
    return UC_CIZIM.girdiler(veri, asansorler, ortak, s if s.get("aktif") else None, proje), s, asansorler


def _tam(veri):
    """Köprünün gördüğü tamamlanmış girdi ( tek asansör )."""
    asansorler, ortak = UC_UYG._asansor_girdileri(veri)
    return E_UGR.tamamla({**E_UGR.varsayilanlar(), **ortak, **asansorler[0]})


class OrnekProjeler(unittest.TestCase):
    """Örnek projelerin çizim girdisi köprüden önce ELLE kuruluyordu
    ( ornekler/uret.py );  köprü aynı girdiyi vermeli — çizimler değişmesin."""

    def _elle(self, md):
        g = copy.deepcopy(CG.ORNEK)
        g["proje"] = {"ad": "ÖRNEK PROJE", "asansor": "ASANSÖR 1", "olcek": 20}
        g["dusey"].update({
            "kabin_paten_arasi": 3300, "agirlik_paten_arasi": 2920, "beyan_hizi": 1.6,
            "durak_adedi": 11, "kat_yuksekligi": 2900, "son_kat": 5000,
            "kabin_tampon_baba": 306, "kabin_tampon_boyu": 618, "kabin_carpma_arasi": 96,
            "kabin_tampon_ezilme": 203, "agirlik_tampon_baba": 300, "agirlik_tampon_boyu": 618,
            "agirlik_carpma_arasi": 150, "agirlik_tampon_ezilme": 203,
            "kabin_konsol_arasi": 1500, "agirlik_konsol_arasi": 1500})
        g["kuyu_dibi"].update({"siginma_tipi": "Yatarak", "regulator_kasnak_capi": 240,
                               "regulator_halat_capi": 6})
        g["kabin_ustu"]["siginma_tipi"] = "Çömelme"
        if md:
            g["makine"].update(tip="Dişli", yeri="Makine dairesi", yan_yatak=140)
        else:
            del g["makine_dairesi"]
        return g

    def test_kopru_elle_kurulan_girdiyi_verir(self):
        for md in (False, True):
            (g, hata), = _kur(_veri(md))[0]
            self.assertEqual(hata, [])
            beklenen = self._elle(md)
            for g_ in (g, beklenen):
                g_["kuyu_dibi"].pop("kuvvetler", None)
                g_["makine"].pop("saptirma_kasnak_capi", None)
            #  Hesabın Sabitler sekmesindeki kabin ölçüleri:  örnek referans
            #  projenin kabiniyle ( elle kurulan girdi de onu taşır )
            self.assertEqual(g.pop("_cizim_sabitleri"), beklenen.pop("_cizim_sabitleri"))
            self.assertEqual(json.loads(json.dumps(g)), json.loads(json.dumps(beklenen)))

    def test_kuvvetler_hesabin_sonucundan(self):
        (g, _h), = _kur(_veri())[0]
        s = _kur(_veri())[1]
        k = g["kuyu_dibi"]["kuvvetler"]
        oz = s["asansorler"][0]["ozet"]
        for ad in ("FKR", "FAR", "Fkt", "Fat"):
            self.assertEqual(k[ad], oz[ad])
        self.assertEqual(set(k), {"FKR", "FAR", "Fkt", "Fat", "Fx_kabin", "Fy_kabin",
                                  "Fx_agirlik", "Fy_agirlik"})

    def test_askinin_x_kacikligi_cizimden(self):
        #  Referans proje:  kasnaklar ağırlık ekseninin 200 önünde, ağırlık ekseni
        #  ray ekseninin 50 önünde → askı ray ekseninin 250 önünde.  Türetme
        #  hesap motorunun tamamla'sında:  hesap ve çizim aynı sayıyı görür.
        self.assertEqual(_tam(_veri())["aski_kaciklik_x"], -250.0)
        s = _kur(_veri())[1]
        self.assertEqual(s["asansorler"][0]["girdi"]["aski_kaciklik_x"], -250.0)
        #  Girilmişse girilen kullanılır;  anahtar hiç yoksa da çizimden
        self.assertEqual(_tam(_veri(aski_kaciklik_x=-100))["aski_kaciklik_x"], -100)
        v = _veri(); del v["asansorler"][0]["aski_kaciklik_x"]
        self.assertEqual(_tam(v)["aski_kaciklik_x"], -250.0)
        #  1:1 askıda halatlar kabin şasesinin üst kirişinin ortasında biter:  kiriş
        #  ray ekseni üstünde, 0.  Arkadaki ağırlıkla 2:1 ( kabin üstü, çapraz ):
        #  askı kabin merkezinde — xs kabinin ( pano dahil ) derinlik ortası ile
        #  ray ekseni arası.
        self.assertEqual(_tam(_veri(aski_orani=1))["aski_kaciklik_x"], 0.0)
        a = _tam(_veri(agirlik_yeri="Arka", aski_duzeni="Kabin üstü"))
        g, _h = CK.cizim_girdisi(a)
        S = CS.sabitler(g.get("_cizim_sabitleri"))
        kb = g["kabin"]
        self.assertAlmostEqual(a["aski_kaciklik_x"], kb["on_pay"] + (kb["derinlik"] + S["kabin_pano_arka"]) / 2.0
                               - g["kabin_ray"]["kapi_arasi"])


class CizimdenTuretilen(unittest.TestCase):
    def test_kasnaklar_ve_kaide_bosken_cizimden(self):
        v = _veri(saptirma_kasnak_capi=None, saptirma_kasnak_min_capi=None, kabin_tampon_baba=None)
        a = _tam(v)
        #  ( 240 + 240 + 400 ) / 3;  en küçüğü 240;  1.500 − 618 − 96 − 480
        self.assertEqual(a["saptirma_kasnak_capi"], 293.3)
        self.assertEqual(a["saptirma_kasnak_min_capi"], 240)
        self.assertEqual(a["kabin_tampon_baba"], 306)
        (g, hata), = _kur(v)[0]
        self.assertEqual(hata, [])

    def test_d2_ds_formdan_okunmaz(self):
        #  Saptırma kasnaklarının çapları formda sorulmaz ( tasarım şeması:
        #  kaynağı çizim ):  eski bir proje dosyasında yazılı olsa da okunmaz,
        #  değer çizilen kasnaklardan gelir ve çizim durmaz.
        v = _veri(saptirma_kasnak_capi=294, saptirma_kasnak_min_capi=200)
        self.assertEqual((_tam(v)["saptirma_kasnak_capi"], _tam(v)["saptirma_kasnak_min_capi"]),
                         (293.3, 240))
        (g, hata), = _kur(v)[0]
        self.assertEqual(hata, [])

    def test_motora_dogrudan_verilen_d2(self):
        #  Formu atlayan çağrıda ( motor doğrudan ) D2 çizimin en küçük kasnağından
        #  da küçükse Ds türetilmez:  hesap Ds'yi "D2'den büyük" diye reddetmesin.
        A = _tam(_veri())
        A.update(saptirma_kasnak_capi=200, saptirma_kasnak_min_capi=None)
        self.assertNotIn("saptirma_kasnak_min_capi", CK.cizimden(A))

    def test_bos_alan_iletisi_formun_adiyla(self):
        #  Boş bırakılan alan "( None )" ya da çizim modülünün iç adıyla
        #  ( agirlik.yeri ) değil, formdaki adıyla söylenir.
        for k, beklenen in (("kabin_genisligi", "Kabin genişliği:  girilmemiş."),
                            ("agirlik_yeri", "Karşı ağırlık yeri:  seçilmemiş"),
                            ("halat_adedi", "Askı halatı adedi:  girilmemiş."),
                            ("yan_yatak", "F  ( yan yatak")):
            (g, hata), = _kur(_veri(**{k: None}))[0]
            self.assertTrue(any(h.startswith(beklenen) for h in hata), (k, hata))
            self.assertFalse(any("None" in h for h in hata), (k, hata))

    def test_varsayilan_formda_turetilenler_bos_acilir(self):
        v = UC_UYG.uygulama_alanlari()
        alan = {f["anahtar"]: f for gr in v["gruplar"] for f in gr["alanlar"]}
        self.assertEqual(sorted(v["cizimden"]), sorted(CK.CIZIMDEN))
        #  Kasnak çapları ve kaide formda sorulmaz;  askı kaçıklığı ve sarılma
        #  açısı sorulur ( boşsa çizimden )
        self.assertEqual(sorted(set(CK.CIZIMDEN) - set(alan)),
                         ["kabin_tampon_baba", "saptirma_kasnak_capi", "saptirma_kasnak_min_capi"])
        for a in set(CK.CIZIMDEN) & set(alan):
            self.assertIsNone(alan[a]["varsayilan"], a)
            self.assertIn("boşsa çizimden", alan[a]["etiket"])
            self.assertEqual(alan[a]["etiket"].count("boşsa"), 1, alan[a]["etiket"])
        #  Çizim alanlarının hepsi formda, makine dairesininkiler proje geneli
        for a in CK.ALAN:
            self.assertIn(a, alan)
        for a in CK.PROJE_GENELI:
            self.assertIn(a, v["proje_geneli"])
        self.assertTrue(set(CK.YALNIZ_DAIRELI) <= set(v["yerlesime_gore_gizli"]["mrl"]))
        self.assertTrue(set(CK.YALNIZ_MRL) <= set(v["yerlesime_gore_gizli"]["daireli"]))


class Tutarlilik(unittest.TestCase):
    """Aynı fiziksel büyüklük hesapta ve çizimde ayrı modelleniyorsa ikisi eşit
    olmalı;  uyuşmazsa çizim durur ve doğru değeri söyler."""

    def _hata(self, **ek):
        (g, hata), = _kur(_veri(**ek))[0]
        return hata

    def test_sarilma_acisi(self):
        hata = self._hata(sarilma_acisi=170)
        self.assertTrue(any("α = 180.0°" in h and "170°" in h and "boş bırakın" in h
                            for h in hata), hata)
        #  Boşsa çizimden:  halat geometrisi ( iki iniş düşey → 180° );  tahrik
        #  kontrolleri hesaplanır, çizim kurulur.
        v = _veri(sarilma_acisi=None)
        self.assertEqual(_tam(v)["sarilma_acisi"], 180.0)
        ((g, hata),), s, _a = _kur(v)
        self.assertEqual(hata, [])
        self.assertFalse(any("α" in x for x in s["asansorler"][0]["ozet"].get("eksik_hesap") or []))

    def test_egik_iniste_alfa_turetilmez(self):
        #  Makine dairesizde ağırlık tarafındaki iniş kasnağın düzleminde eğikse
        #  ( HALAT SAPMASI ) açı ağırlığın konumuyla değişir:  çizim tek bir sayı
        #  söylemez ( eskiden "180° girin" diyordu ), girilen açıya itiraz etmez.
        from cizim import kuyu_ustu as CKU
        ek = dict(aski_duzeni="Kabin üstü", kabin_kasnak_arasi=None)
        (g, hata), = _kur(_veri(**ek))[0]
        self.assertGreater(abs(CKU.yerlesim(g)["sapma"][0]), 0.5)
        self.assertIsNone(CK.sarim_acisi(g))
        self.assertIsNone(_tam(_veri(sarilma_acisi=None, **ek))["sarilma_acisi"])
        self.assertFalse(any("α =" in h for h in self._hata(sarilma_acisi=176, **ek)))

    def test_cift_sarim_cizilmez_alfa_turetilmez(self):
        #  Çizim tek sarım çizer:  çift sarımda α çizimden bulunamaz ( sayı
        #  uydurulmaz ) ve çizim bunu söyler — eskiden "hesaba 180° girin"
        #  diyordu, hesap da çift sarımda 180°'yi reddediyordu.
        cs = "Yarım Daire Kanal (Çift Sarım)"
        v = _veri(kanal_sekli=cs, sarilma_acisi=None)
        self.assertIsNone(_tam(v)["sarilma_acisi"])
        for alfa in (None, 330):
            hata = self._hata(kanal_sekli=cs, sarilma_acisi=alfa)
            self.assertTrue(any("Çift sarımlı kanal" in h for h in hata), hata)
            self.assertFalse(any("girin" in h and "180" in h for h in hata), hata)

    def test_saptirma_kasnaklari(self):
        #  Formdan gelmez;  motora doğrudan verilmişse çizimle karşılaştırılır.
        self.assertEqual(self._hata(saptirma_kasnak_capi=240, saptirma_kasnak_min_capi=200), [])
        (g, _h), = _kur(_veri())[0]
        A = _tam(_veri())
        self.assertTrue(any("ortalaması 293.3" in h
                            for h in CK.tutarlilik(g, dict(A, saptirma_kasnak_capi=240))))
        self.assertTrue(any("en küçük kasnak 240" in h
                            for h in CK.tutarlilik(g, dict(A, saptirma_kasnak_min_capi=200))))

    def test_makine_kirisi(self):
        #  Kirişin açıklığı girdi değildir ( çizimden:  raylara oturan kirişte DBGW ):
        #  formdan gelmez, eski projede yazılı olsa da okunmaz.
        self.assertEqual(self._hata(yan_yatak_boyu=900), [])
        #  Karar 3:  bina yapısına ( duvardan duvara ) oturan kiriş henüz çizilmiyor
        hata = self._hata(makine_raya_biniyor="Bina yapısına")
        self.assertTrue(any("bina yapısına" in h and "karar 3" in h for h in hata), hata)

    def test_kuyu_dibi_zinciri(self):
        #  Kaide formdan gelmez ( zincirden );  motora doğrudan verilmişse zincir denetlenir.
        self.assertEqual(self._hata(kabin_tampon_baba=400), [])
        _g, hata = CK.cizim_girdisi(dict(_tam(_veri()), kabin_tampon_baba=400))
        self.assertTrue(any("zinciri kapanmıyor" in h and "306" in h for h in hata), hata)

    def test_cizilemeyen_kaciklik_soylenir(self):
        #  yc · ys formda sorulmaz ( çizim kabini iki rayın, askıyı kabinin
        #  ortasına koyar );  eski dosyada yazılı olsa da okunmaz.  Motora
        #  doğrudan verilmişse çizim söyler.
        self.assertEqual(self._hata(kabin_kaciklik=40, aski_kaciklik_y=40), [])
        A = _tam(_veri())
        self.assertTrue(any("( yc )" in h for h in CK.cizim_girdisi(dict(A, kabin_kaciklik=40))[1]))
        self.assertTrue(any("( ys )" in h for h in CK.cizim_girdisi(dict(A, aski_kaciklik_y=40))[1]))

    def test_regulator_halat_cizgisinin_obur_yaninda(self):
        #  Halat çizgisi ray ekseninin arkasındaysa regülatör öne geçer
        A = _tam(_veri(aski_kaciklik_x=120, regulator_kaciklik=None))
        g, hata = CK.cizim_girdisi(A)
        self.assertEqual(hata, [])
        self.assertEqual(g["kuyu_dibi"]["regulator_kaciklik"], -280.0)
        A = _tam(_veri(regulator_kaciklik=None))
        self.assertEqual(CK.cizim_girdisi(A)[0]["kuyu_dibi"]["regulator_kaciklik"], 280.0)


class Bolum11CizimdenOlculur(unittest.TestCase):
    """Hesabın bölüm 11'i ( sığınma alanları ve açıklıklar ) açıklıkları kuyunun
    çiziminden okur:  paftadaki tablo ile kesitteki ölçü aynı sayıdır."""

    def test_hesabin_acikliklari_cizimin_olculeri(self):
        from cizim import dusey as CDU
        for md in (False, True):
            ((g, hata),), s, _a = _kur(_veri(md))
            self.assertEqual(hata, [])
            ara = s["asansorler"][0]["ara"]
            Y = CDU.yerlesim(g)
            for ad, anahtar in (("siginma", "kabin_ustu_tavan"), ("paten", "paten_tavan"),
                                ("ray", "ust_paten_ray"), ("agirlik_ray", "agirlik_paten_ray")):
                self.assertAlmostEqual(ara[f"siginma.{anahtar}"], Y["ust_aciklik"][ad][0], places=6)
            for ad, anahtar in (("siginma", "dip_siginma"), ("en_alt", "kuyu_tabani_kabin"),
                                ("etek", "etek"), ("sase", "ray_kabin_alt")):
                self.assertAlmostEqual(ara[f"siginma.{anahtar}"], Y["dip_aciklik"][ad][0], places=6)

    def test_sabitler_sekmesindeki_kabin_olcusu_ikisine_birden_girer(self):
        #  Şase altı 480 → 500:  kaide çizimden 20 kısalır, kuyu dibi açıklıkları
        #  hesapta ve çizimde aynı kadar değişir
        v = _veri(kabin_tampon_baba=None)
        v["sabitler"]["sase_alt_derinlik"] = 500
        ((g, hata),), s, _a = _kur(v)
        self.assertEqual(hata, [])
        self.assertEqual(g["_cizim_sabitleri"]["sase_alt_derinlik"], 500.0)
        self.assertEqual(s["asansorler"][0]["girdi"]["kabin_tampon_baba"], 286)
        ((g0, _h),), s0, _a = _kur(_veri())
        a0, a1 = s0["asansorler"][0]["ara"], s["asansorler"][0]["ara"]
        self.assertAlmostEqual(a1["siginma.ray_kabin_alt"], a0["siginma.ray_kabin_alt"] - 20, places=6)

    def test_turetilen_deger_girdiyi_izler(self):
        #  Varsayılanlar türetilen değeri TAŞIMAZ:  kuyu dibi değişince kaide de değişir
        from engine.uygulama import mukavemet as MK
        for k in CK.CIZIMDEN:
            self.assertIsNone(E_UGR.varsayilanlar()[k], k)
        a = MK.hesapla({"kuyu_dibi": 1700})["girdi"]["kabin_tampon_baba"]
        b = MK.hesapla({"kuyu_dibi": 1800})["girdi"]["kabin_tampon_baba"]
        self.assertEqual(b - a, 100)

    def test_cizilemeyen_duzende_hesap_eksik_der(self):
        #  Makine dairesiz 1:1 ve arkadaki ağırlıkla KABİN ALTI 2:1 çizilmez
        #  ( gerçek projelerde yok;  arkadakinde kasnaklar kabin üstünde,
        #  çapraz ):  bölüm 11 HESAP EKSİK der, sebebini yazar
        for ek, metin in (({"aski_orani": 1}, "1:1 askı çizilmez"),
                          ({"agirlik_yeri": "Arka", "aski_duzeni": "Kabin altı"},
                           "kabin üstünde çizilir")):
            ((g, hata),), s, _a = _kur(_veri(**ek))
            b = next(b for b in s["asansorler"][0]["bolumler"] if b["kimlik"] == "siginma_alanlari")
            self.assertTrue(b["eksik_hesap"].startswith("HESAP EKSİK — kuyunun çizimi kurulamadı"), ek)
            self.assertIn(metin, b["eksik_hesap"])


class YeniDuzenler(unittest.TestCase):
    """Kabin üstü 2:1, makine dairesinde 1:1 ( ağırlık yanda ve arkada ).  Örnek
    projenin kendi asansörü, askı düzeni değişerek;  α, D2, Ds boş — çizimden
    gelir ve hesaba o girer."""

    def _kur(self, md, **ek):
        v = _veri(md, **ek)
        for k in ("saptirma_kasnak_capi", "saptirma_kasnak_min_capi", "kabin_kasnak_arasi",
                  "regulator_kaciklik", "sarilma_acisi"):
            v["asansorler"][0][k] = None
        ((g, hata),), s, _a = _kur(v)
        if g is not None:
            #  hesabın α'sı çizimdeki sarım açısıdır
            self.assertAlmostEqual(_tam(v)["sarilma_acisi"], CK.sarim_acisi(g), delta=0.05)
        return g, hata, s

    def _bolum11(self, s):
        return next(b for b in s["asansorler"][0]["bolumler"] if b["kimlik"] == "siginma_alanlari")

    def test_kabin_ustu_2_1(self):
        g, hata, s = self._kur(False, aski_duzeni="Kabin üstü")
        self.assertEqual(hata, [])
        from cizim import dusey as CDU, donanim as CDN
        Y = CDU.yerlesim(g)
        #  Kasnaklar şasenin üst kirişinin üstünde:  alt uçları 30 mm yukarıda
        kt = CDN.kabin_kotlari(g["dusey"], Y["S"], 0.0, g["aski"])
        self.assertAlmostEqual(kt["kasnak_merkez"] - g["aski"]["kasnak_capi"] / 2.0, kt["sase_ust"] + 30.0)
        self.assertIn("kasnak", Y["ust_aciklik"])
        self.assertEqual(Y["kasnaklar"], [])          # kuyu dibinde kabin kasnağı yok
        b = self._bolum11(s)
        self.assertIn("siginma.kasnak_tavan", s["asansorler"][0]["ara"])
        self.assertIsNone(b.get("eksik_hesap"))

    def test_makine_dairesinde_1_1_agirlik_yanda(self):
        g, hata, s = self._kur(True, aski_orani=1)
        self.assertEqual(hata, [])
        from cizim import makine_dairesi as CMD
        Y = CMD.yerlesim(g)
        #  Kabin halatı kabin ekseninde, ağırlık halatı ağırlık ekseninde;  aralık
        #  tahrik kasnağından büyük:  saptırma kasnağı çizilir, D2 · Ds ondan gelir
        (hx, hy), = Y["M"]["halatlar"]
        self.assertAlmostEqual(hx, g["kuyu"]["genislik"] / 2.0 + g["kabin"]["kaciklik_y"])
        self.assertAlmostEqual(hy, g["kabin_ray"]["kapi_arasi"])
        self.assertTrue(Y["saptirma"])
        gi = s["asansorler"][0]["girdi"]
        self.assertEqual(gi["saptirma_kasnak_capi"], Y["saptirma"]["D"])
        self.assertEqual(gi["aski_kaciklik_x"], 0.0)
        self.assertIsNone(Y["M"]["kabin_baglanti"])       # tepede bağlantı yok
        self.assertEqual([a for a, _ in Y["delikler"]], ["KABİN", "AĞIRLIK", "REGÜLATÖR", "REGÜLATÖR"])
        self.assertIn("siginma.baglanti_tavan", s["asansorler"][0]["ara"])

    def test_makine_dairesinde_1_1_agirlik_arkada(self):
        #  Ofisin 12744-3'ü gibi:  kuyu arkadaki ağırlığa göre derin, kabin ortada,
        #  kaide makineyle saptırmayı taşıyacak boyda
        g, hata, s = self._kur(True, aski_orani=1, agirlik_yeri="Arka", kuyu_derinligi=2250,
                               kabin_yana_kaciklik=0)
        self.assertEqual(hata, [])
        from cizim import makine_dairesi as CMD, kuyu_kesiti as CKK
        Y = CMD.yerlesim(g)
        d = Y["duzlem"]
        self.assertEqual((d.yon, d.eksen), ("y", "x"))     # halat düzlemi derinlik boyunca
        kasnak = next(p for p in Y["M"]["makine"] if p["parca"] == "kasnak")
        self.assertEqual(kasnak["eksen"], "x")
        ks = Y["M"]["kasnak"]
        self.assertAlmostEqual(ks[3] - ks[1], g["makine"]["tahrik_kasnak_capi"])
        #  A-A kesiti halat düzleminin içinden geçer:  halatlar orada çizilir
        e = CKK.yan_kesit(g)
        self.assertTrue([el for el in e if el.get("ad") == "aski_halati"])
        self.assertTrue([el for el in e if el.get("ad") == "sarim_acisi"])
        self.assertIsNone(self._bolum11(s).get("eksik_hesap"))

    def test_tahrik_kasnagi_kuyu_arasindan_kucukse_saptirma_gerekmez(self):
        #  Yan ağırlıkta aralık kasnaktan küçükse saptırma kasnağıyla çözülmez
        g, hata, s = self._kur(True, aski_orani=1, tahrik_kasnak_capi=1400)
        self.assertTrue(any("saptırma" in h for h in hata), hata)


class Uclar(unittest.TestCase):
    def test_onizleme_bütün_cizimleri_verir(self):
        for md in (False, True):
            v = _veri(md)
            v["asansor"] = 0
            d = json.loads(UC_CIZIM.api_cizimler(v).body)
            self.assertTrue(d["aktif"], d.get("hata"))
            self.assertTrue(d["hesap"])
            ad = [c["ad"] for c in d["cizimler"]]
            self.assertEqual(ad[-1], "delik_plani" if md else "kuyu_ustu")
            for c in d["cizimler"]:
                self.assertTrue(c["svg"].startswith("<svg"), c["ad"])

    def test_onizleme_hata_listesi(self):
        v = _veri(kuyu_derinligi=1200)
        d = json.loads(UC_CIZIM.api_cizimler(v).body)
        self.assertFalse(d["aktif"])
        self.assertTrue(d["hata"])
        #  Aynı hata birçok çizimde tekrarlanır;  bir kez söylenir
        self.assertEqual(len(d["hata"]), len(set(d["hata"])))

    def _paket(self, veri):
        yanit = UC_UYG.indir_uygulama_dwg(veri)
        self.assertEqual(yanit.media_type, "application/zip", getattr(yanit, "body", b"")[:300])
        z = zipfile.ZipFile(io.BytesIO(yanit.body))
        ad = next(n for n in z.namelist() if n.endswith(".dxf"))
        return ezdxf.read(io.StringIO(z.read(ad).decode("utf-8", "ignore")))

    def test_paket_cizimleri_hesap_sayfalarinin_sagina_ekler(self):
        d = self._paket(_veri())
        bloklar = {b.name for b in d.blocks if b.name.startswith("CIZIM_")}
        self.assertEqual(bloklar, {"CIZIM_" + a.upper() for a in
                                   ("kuyu_kesiti_yan", "kuyu_kesiti_on", "kuyu_plani", "kabin_ustu",
                                    "kuyu_dibi", "kuyu_ustu")})

    def test_cok_asansorlu_pakette_her_asansorun_cizimleri(self):
        v = _veri()
        ikinci = dict(v["asansorler"][0], asansor_adi="ASANSÖR 2")
        v["asansorler"].append(ikinci)
        d = self._paket(v)
        bloklar = {b.name for b in d.blocks if b.name.startswith("CIZIM_")}
        self.assertIn("CIZIM_KUYU_PLANI_1", bloklar)
        self.assertIn("CIZIM_KUYU_PLANI_2", bloklar)
        #  Şeritte asansörün adı:  hangi kuyunun çizimi olduğu okunur
        yazilar = {t.dxf.text for b in d.blocks if b.name.startswith("CIZIM_KUYU_PLANI_")
                   for t in b.query("TEXT MTEXT") if t.dxftype() == "TEXT"}
        self.assertTrue({"ASANSÖR 1", "ASANSÖR 2"} <= yazilar, yazilar)

    def test_cizimi_kurulamayan_paket_inmez(self):
        yanit = UC_UYG.indir_uygulama_dwg(_veri(kuyu_derinligi=1200))
        self.assertEqual(yanit.media_type, "application/json")
        d = json.loads(yanit.body)
        self.assertIn("ÇİZİMLER KURULAMADI", d["hata"])
        self.assertIn("1. asansör", d["hata"])


if __name__ == "__main__":
    unittest.main()

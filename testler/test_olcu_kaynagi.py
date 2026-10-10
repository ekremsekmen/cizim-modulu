"""ÖLÇÜYE TIKLAMA — ölçünün kaynağı ve ölçüden değiştirme ( cizim/olcu_kaynagi.py,
hesap/api/cizim.py ).

Ekranda bir ölçüye tıklanınca hangi girdiden geldiği söylenir;  yeni değer o
girdiye yazılır ve çizim yeniden kurularak doğrulanır.  Kaynak ölçülür ( her
girdi 1 mm oynatılır ), elle etiketlenmez — testler de ölçerek denetler."""

import json
import os
import re
import threading
import time
import unittest
from unittest import mock

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from api import cizim as UC
from testler.yavas import yavas
from api import uygulama as UC_UYG
from cizim import cizimler as CZ
from cizim import geometri as CGE
from cizim import kopru as CK
from cizim import kuyu_dibi as CKD
from cizim import olcu_kaynagi as CO
from cizim import pafta as CPF
from cizim import sabitler as CS
from engine.uygulama import hesap as E_UYG
from hesap_girdi import ASANSOR, ASANSOR_MD, ORTAK, ORTAK_MD, SABITLER

from testler import gercek_projeler as GP


def _veri(md=False, **ek):
    return {
        "asansorler": [dict(ASANSOR_MD if md else ASANSOR, siginma_tipi_dip="Yatarak", **ek)],
        "proje_geneli": dict(ORTAK_MD if md else ORTAK),
        "sabitler": dict(SABITLER),
        "asansor": 0,
    }


def _yeni_duzen(md, **ek):
    """Örneğin asansörü, askı düzeni değişerek;  türetilenler boş ( çizimden )."""
    v = _veri(md, **ek)
    for k in (
        "saptirma_kasnak_capi",
        "saptirma_kasnak_min_capi",
        "kabin_kasnak_arasi",
        "regulator_kaciklik",
        "sarilma_acisi",
    ):
        v["asansorler"][0][k] = None
    return v


#  Birleşik programın çizdiği düzenler ( test_kopru.YeniDuzenler ile aynı )
DUZENLER = {
    "örnek makine dairesiz": lambda: _veri(),
    "örnek makine daireli": lambda: _veri(True),
    #  xs −200:  çizimden gelen −250'de kasnaklar ve aralarındaki halat şasenin
    #  üst kirişinin önünden ayrı bant olarak geçer, tavanda çömelme alanına yer
    #  kalmaz ( test_kopru.test_kabin_ustu_kasnaklari_kirisin_onunde )
    "kabin üstü 2:1": lambda: _yeni_duzen(False, aski_duzeni="Kabin üstü", aski_kaciklik_x=-200),
    "makine dairesinde 1:1": lambda: _yeni_duzen(True, aski_orani=1),
    "makine dairesinde 1:1, ağırlık arkada": lambda: _yeni_duzen(
        True, aski_orani=1, agirlik_yeri="Arka", kuyu_derinligi=2250, kabin_yana_kaciklik=0
    ),
    #  Arkadaki ağırlıkla 2:1 ( kabin üstü, çapraz — arka_aski ):  örnek kuyu
    #  arkadaki ağırlığa göre derin;  makine dairesizde makine duvardan duvara
    #  kirişte ( bina yapısına ), kabin üstündeki makineye göre son kat yüksek.
    #  Kabin 1.800 derin:  örneğin 1.400'lük kabininin tavanını şasenin üst
    #  kirişi ( ray ekseninde ) ve çapraz halat dört parçaya böler, en büyüğü
    #  604 × 607 — çömelme alanı ( 500 × 700 ) sığmaz ( 10 Eki'den beri ikisi
    #  de engel );  1.800'de kirişin arkasında 746 kalır.
    "arkada 2:1 makine dairesiz": lambda: _yeni_duzen(
        False,
        agirlik_yeri="Arka",
        aski_duzeni="Kabin üstü",
        makine_raya_biniyor="Bina yapısına",
        agirlik_ray_duvar=None,
        kabin_derinligi=1800,
        kuyu_derinligi=2500,
        son_kat_yuksekligi=5500,
    ),
    "arkada 2:1 makine daireli": lambda: _yeni_duzen(
        True,
        agirlik_yeri="Arka",
        aski_duzeni="Kabin üstü",
        agirlik_ray_duvar=None,
        kabin_derinligi=1800,
        kuyu_derinligi=2500,
    ),
    "formun varsayılanı": lambda: {"asansorler": [{}], "proje_geneli": {}, "sabitler": {}, "asansor": 0},
}


def _g(v):
    asansorler, ortak = UC_UYG._asansor_girdileri(v)
    s = E_UYG.hesapla_coklu(asansorler, ortak)
    ((g, hata),) = UC.girdiler(v, asansorler, ortak, s if s.get("aktif") else None, "P")
    return g, hata


def _olcu(r, soz, n=0):
    return [i for i, o in enumerate(r["taban"]) if o["metin"].startswith(soz)][n]


def _degistir(v, ad, i, r, anahtar, hedef):
    return json.loads(
        UC.api_olcu_degistir(
            dict(v, cizim=ad, olcu=i, metin=r["taban"][i]["metin"], anahtar=anahtar, hedef=hedef)
        ).body
    )


def _uygula(v, y):
    """Dönen değişiklikleri isteğe yazar ( formun kutularına yazılmış gibi )."""
    v = json.loads(json.dumps(v))
    pg = UC._sozlesme()[1]
    for d in y["degisiklikler"]:
        (v["proje_geneli"] if d["anahtar"] in pg else v["asansorler"][0])[d["anahtar"]] = d["deger"]
    return v


class Eksiksiz(unittest.TestCase):
    """Her düzenin her çiziminin her ölçüsü ya bir girdiye ( form, ofis
    standardı, ürün ölçüsü ) bağlıdır ya da dayandığı kuralı söyler — tıklanan
    hiçbir ölçü "bilinmiyor" demez."""

    @yavas("7 dk")
    def test_her_olcunun_kaynagi_ya_da_kurali_var(self):
        for ad_d, v in DUZENLER.items():
            v = v()
            g, hata = _g(v)
            self.assertIsNotNone(g, (ad_d, hata))
            for ad in CPF.sira(g):
                r = UC._cozumleme(v, ad)
                self.assertIsNotNone(r, (ad_d, ad))
                eksik = [
                    o["metin"] for i, o in enumerate(r["taban"]) if not r["kaynak"][i] and not o.get("kural")
                ]
                self.assertEqual(eksik, [], (ad_d, ad))


class Kaynak(unittest.TestCase):
    def setUp(self):
        self.v = _veri()
        self.r = UC._cozumleme(self.v, "kuyu_plani")

    def _kaynaklar(self, soz, n=0, r=None):
        r = r or self.r
        return UC._kaynaklar(r, _olcu(r, soz, n))

    def test_olcunun_kendisi_olan_girdi_once(self):
        for soz, anahtar in (
            ("KUYU GENİŞLİĞİ", "kuyu_genisligi"),
            ("KUYU DERİNLİĞİ", "kuyu_derinligi"),
            ("DUVAR", "kuyu_duvar_sol"),
            ("KABİN İÇİ", "kabin_genisligi"),
            ("DBG ", "kabin_ray_arasi"),
            ("KAPI 900", "kapi_genisligi"),
        ):
            k = self._kaynaklar(soz)
            self.assertEqual(k[0]["anahtar"], anahtar, (soz, k[:2]))
            self.assertTrue(k[0]["dogrudan"] and k[0]["degistirilir"], soz)

    def test_duvarin_kendi_kutusu_once(self):
        #  2 Eki:  planın dört "DUVAR" ölçüsü kendi duvarının kutusundan gelir;
        #  ortak "kuyu duvarı kalınlığı" ikinci ( değiştirseydi dört duvar birden
        #  değişirdi ).  Ön ve arka duvar da ölçülür.
        for n, anahtar in enumerate(("kuyu_duvar_sol", "kuyu_duvar_sag", "kuyu_duvar_on", "kuyu_duvar_arka")):
            k = self._kaynaklar("DUVAR", n)
            self.assertEqual([x["anahtar"] for x in k[:2]], [anahtar, "kuyu_duvar_kalinligi"])
            self.assertTrue(k[0]["dogrudan"] and k[0]["degistirilir"])

    def test_kuralla_dolan_alan_kuralin_girdisinden_once(self):
        #  DBGW boşsa Gy + 60:  ölçü "ağırlık genişliğinden geliyor" görünmemeli —
        #  değiştirmek Gy'yi ( karşı ağırlığın enini ) değiştirirdi.
        k = self._kaynaklar("DBGW")
        self.assertEqual([x["anahtar"] for x in k[:2]], ["agirlik_ray_arasi", "agirlik_genisligi"])
        self.assertTrue(k[0]["dogrudan"])
        self.assertFalse(k[1]["dogrudan"])

    def test_zincir_olcusunun_bircok_kaynagi(self):
        #  Kabinin dış yüzü – sağ kuyu duvarı ( KABİN DIŞI zincirinde ):  kuyu
        #  genişliği, kabin genişliği, kaçıklık, ürün ölçüsü ( pano — tek katalog:
        #  ofis standardı ).  8 Eki'ye dek şase dikmesi de giriyordu ( "430" — dikme
        #  artık rayın ucunda;  iç sıradaki duvar – kabin ölçüleri kalktı )
        i = next(i for i, o in enumerate(self.r["taban"]) if o["metin"] == "200")
        k = UC._kaynaklar(self.r, i)
        ad = {x["anahtar"]: x for x in k}
        self.assertEqual(ad["kuyu_genisligi"]["egim"], 0.5)
        self.assertEqual(ad["kabin_genisligi"]["egim"], -0.5)
        self.assertEqual(abs(ad["kabin_yana_kaciklik"]["egim"]), 1.0)
        self.assertEqual(ad["kabin_pano_yan"]["yer"], "ofis")
        self.assertFalse(ad["kabin_pano_yan"]["degistirilir"])
        self.assertTrue(all(not x["dogrudan"] for x in k))

    def test_secim_kutusu_kaynagi(self):
        k = self._kaynaklar("RAY 62")
        self.assertEqual([(x["anahtar"], x["tur"]) for x in k], [("kabin_ray_profili", "secim")])
        self.assertFalse(k[0]["degistirilir"])  # seçenekleri sayı değil

    def test_urun_olcusu_adiyla(self):
        #  Ürün ölçüleri ofis standardındadır ( Sabitler sekmesi — karar 12 ).
        #  Eşiğin derinliği kapı tipine de bağlı ( 3 kanatlı teleskopikte 135 —
        #  girdi.esik_derinligi, 2 Eki ):  kapı tipi seçim olarak önce gelir.
        k = self._kaynaklar("KABİN EŞİĞİ")
        ofis = [x for x in k if x["yer"] == "ofis"]
        self.assertTrue(ofis[0]["etiket"].startswith(CS.ETIKET["kabin_esik_derinlik"]))
        self.assertFalse(ofis[0]["degistirilir"])
        self.assertEqual(k[0]["anahtar"], "kat_kapisi_tipi")

    def test_kuyu_dibi_dogrudan_kaide_zincirden(self):
        #  Kabin tamponu kaidesinin formda kutusu yok ( tasarım şeması:  kaynağı
        #  çizim ):  kuyu dibi zincirinden gelir.  Kuyu dibi tek başına değişir,
        #  kaide onu izler — eskiden girilmiş kaide yüzünden ikisi bağlıydı.
        r = UC._cozumleme(self.v, "kuyu_kesiti_yan")
        k = UC._kaynaklar(r, _olcu(r, "KUYU DİBİ"))
        self.assertEqual(k[0]["anahtar"], "kuyu_dibi")
        self.assertFalse(k[0]["bagli"])
        self.assertTrue(k[0]["dogrudan"])

    def test_ofis_standardi(self):
        #  Kuyu tavanı payı ( Sabitler sekmesi ) ön kesitte raylarla kabin rayının
        #  tavana kalan ölçülerini belirler;  ofis standardı değiştirilmez, gösterilir.
        r = UC._cozumleme(self.v, "kuyu_kesiti_on")
        ofis = [x for i in range(len(r["taban"])) for x in UC._kaynaklar(r, i) if x["yer"] == "ofis"]
        self.assertIn("tavan_payi", {x["anahtar"] for x in ofis})
        self.assertTrue(all(not x["degistirilir"] for x in ofis))

    def test_standardin_ve_yerlesimin_kurali(self):
        r = UC._cozumleme(self.v, "kabin_ustu")
        kural = [o["kural"] for o in r["taban"] if o.get("kural")]
        self.assertTrue(any("Çizelge 3" in k for k in kural), kural)
        self.assertTrue(any("kapıya en yakın" in k for k in kural), kural)
        r = UC._cozumleme(self.v, "kuyu_ustu")
        self.assertTrue(any("m.5.2.6.3.2.1 a" in (o.get("kural") or "") for o in r["taban"]))

    def test_uc_ve_ekran_ayni_olcuyu_gorur(self):
        #  Çözümleme çerçevesiz listeyi okur;  ekran çerçeveli listeden SVG'yi.
        #  Ölçüler ve sıraları birebir aynı olmalı ( tıklanan sıra = çözülen ).
        for md in (False, True):
            g, _h = _g(_veri(md))
            for ad in CPF.sira(g):
                a = [(o["a"], o["b"], o["kot"], o["metin"]) for o in CO.olculer(CZ.CIZIMLER[ad][1](g))]
                b = [(o["a"], o["b"], o["kot"], o["metin"]) for o in CO.olculer(UC._elemanlar(g, ad)[0])]
                self.assertEqual(a, b, ad)

    def test_hesabin_sonucu_olculeri_degistirmez(self):
        #  Ekran çizimleri hesabın sonucuyla ( yük kutuları ), çözümleme onsuz kurar.
        v = _veri()
        asansorler, ortak = UC_UYG._asansor_girdileri(v)
        s = E_UYG.hesapla_coklu(asansorler, ortak)
        ((g1, _h),) = UC.girdiler(v, asansorler, ortak, s, "P")
        ((g0, _h),) = UC.girdiler(v, asansorler, ortak, None, "P")
        for ad in CPF.sira(g1):
            self.assertEqual(
                [(o["a"], o["b"], o["metin"]) for o in CO.olculer(UC._elemanlar(g1, ad)[0])],
                [(o["a"], o["b"], o["metin"]) for o in CO.olculer(UC._elemanlar(g0, ad)[0])],
                ad,
            )


class CokAsansor(unittest.TestCase):
    def test_cizimin_hesap_durumu_secilen_asansorundur(self):
        v = _veri()
        saglam = dict(v["asansorler"][0])
        hatali = dict(saglam, motor_gucu=-1)
        for asansorler, beklenen in (
            ([saglam, hatali], [True, False]),
            ([hatali, saglam], [False, True]),
            ([hatali], [False]),
        ):
            for i, hesap_var in enumerate(beklenen):
                with self.subTest(adet=len(asansorler), asansor=i, hesap=hesap_var):
                    c = json.loads(UC.api_cizimler(dict(v, asansorler=asansorler, asansor=i)).body)
                    self.assertTrue(c["aktif"], c.get("hata"))
                    self.assertTrue(c["cizimler"])
                    self.assertEqual(c["hesap"], hesap_var)

    def test_aktif_asansorun_girdisi(self):
        #  Çizimler aktif asansörün;  çözümleme de onun girdisini okur.
        v = _veri()
        v["asansorler"].append(dict(v["asansorler"][0], kuyu_genisligi=2300, kabin_yana_kaciklik=230))
        for i, kg in ((0, 2100), (1, 2300)):
            r = UC._cozumleme(dict(v, asansor=i), "kuyu_plani")
            self.assertEqual(r["taban"][_olcu(r, "KUYU GENİŞLİĞİ")]["uzunluk"], kg)

    def test_proje_geneli_alan(self):
        #  Makine dairesinin ölçüleri binanındır:  kaynak "proje" diye söylenir.
        v = _veri(True)
        r = UC._cozumleme(v, "makine_dairesi")
        k = UC._kaynaklar(r, _olcu(r, "MAKİNE DAİRESİ"))
        self.assertEqual((k[0]["anahtar"], k[0]["yer"]), ("mk_genislik", "proje"))


class Degistirme(unittest.TestCase):
    """Yeni değer girdiye yazılır ve çizim yeniden kurulduğunda ölçü hedeftedir."""

    def _dene(self, v, ad, soz, anahtar, hedef, n=0, beklenen=None):
        r = UC._cozumleme(v, ad)
        i = _olcu(r, soz, n)
        y = _degistir(v, ad, i, r, anahtar, hedef)
        self.assertTrue(y["aktif"], y)
        self.assertTrue(y["dogrulandi"], y)
        if beklenen:
            self.assertEqual({d["anahtar"]: d["deger"] for d in y["degisiklikler"]}, beklenen)
        #  Bağımsız doğrulama:  değişiklik isteğe yazılıp çizim programın kendi
        #  yolundan ( girdiler ) yeniden kurulur, aynı sıradaki ölçü okunur.
        g, hata = _g(_uygula(v, y))
        self.assertIsNotNone(g, hata)
        o = CO.olculer(UC._elemanlar(g, ad)[0])
        if not beklenen or anahtar not in ("tahrik_kasnak_capi",):
            yakin = [x["uzunluk"] for x in o if abs(x["uzunluk"] - hedef) < 0.05]
            self.assertTrue(yakin, (soz, hedef))
        return y

    def test_dogrudan(self):
        v = _veri()
        self._dene(
            v, "kuyu_plani", "KUYU GENİŞLİĞİ", "kuyu_genisligi", 2200, beklenen={"kuyu_genisligi": 2200}
        )
        #  Makine kirişleri ağırlık raylarına oturuyor:  kirişin açıklığı ( L ) DBGW'dir
        #  ama girdi değil — çizimden gelir, yalnız DBGW değişir.
        self._dene(v, "kuyu_plani", "DBGW", "agirlik_ray_arasi", 900, beklenen={"agirlik_ray_arasi": 900})

    def test_olcu_sayisi_ana_formla_ayni_okunur(self):
        from api.ortak import _belirsiz_hata

        v = _veri()
        r = UC._cozumleme(v, "kuyu_plani")
        i = _olcu(r, "KUYU GENİŞLİĞİ")
        for ham, beklenen in (
            ("2200", 2200),
            ("2200,5", 2200.5),
            ("2.200,5", 2200.5),
            ("2,200.5", 2200.5),
            ("2 200,5", 2200.5),
            (2200.5, 2200.5),
            ("0,075", 0.075),
        ):
            with self.subTest(ham=ham):
                form, _ortak = UC_UYG._asansor_girdileri(
                    dict(v, asansorler=[dict(v["asansorler"][0], kuyu_genisligi=ham)])
                )
                self.assertIsNone(_belirsiz_hata())
                self.assertEqual(form[0]["kuyu_genisligi"], beklenen)
                y = _degistir(v, "kuyu_plani", i, r, "kuyu_genisligi", ham)
                self.assertTrue(y["aktif"], y)
                self.assertEqual(y["degisiklikler"][0]["deger"], beklenen)

    def test_belirsiz_olcu_yazimi_reddedilir(self):
        v = _veri()
        r = UC._cozumleme(v, "kuyu_plani")
        i = _olcu(r, "KUYU GENİŞLİĞİ")
        for ham in ("2.200", "2,200", " 2.200 ", "\u00a02.200\u00a0"):
            with self.subTest(ham=ham):
                y = _degistir(v, "kuyu_plani", i, r, "kuyu_genisligi", ham)
                self.assertFalse(y["aktif"], y)
                self.assertIn("Belirsiz sayı", y["hata"][0])
                self.assertNotIn("degisiklikler", y)

    def test_gecersiz_olcu_sayisi_reddedilir(self):
        v = _veri()
        r = UC._cozumleme(v, "kuyu_plani")
        i = _olcu(r, "KUYU GENİŞLİĞİ")
        for ham in (None, "", "  ", True, "nan", "inf", "2200 mm", "0x898", "1e309", [], {}):
            with self.subTest(ham=ham):
                y = _degistir(v, "kuyu_plani", i, r, "kuyu_genisligi", ham)
                self.assertFalse(y["aktif"], y)
                self.assertTrue(y["hata"])
                self.assertNotIn("degisiklikler", y)

    def test_zincir_parcasi_iki_ayri_girdiyle(self):
        v = _veri()
        r = UC._cozumleme(v, "kuyu_plani")
        i = next(i for i, o in enumerate(r["taban"]) if o["metin"] == "343")
        y = _degistir(v, "kuyu_plani", i, r, "kabin_yana_kaciklik", 300)
        self.assertTrue(y["dogrulandi"])
        self.assertEqual(y["degisiklikler"][0]["deger"], 87)  # 130 − 43
        y = _degistir(v, "kuyu_plani", i, r, "kuyu_genisligi", 300)
        self.assertTrue(y["dogrulandi"])
        self.assertEqual(y["degisiklikler"][0]["deger"], 2014)  # 2.100 − 2 × 43

    def test_bagli_alan_birlikte_degisir(self):
        #  Makine kirişleri karşı ağırlık raylarına oturuyor:  kirişin mesnet
        #  aralığı raylar arasıdır ( L = DBGW ).  Eskiden yan yatak boyu da
        #  birlikte değişirdi;  artık girdi değildir ( çizimden ) — DBGW 850 → 900
        #  yalnız DBGW'yi değiştirir, hesabın L'si çizimden 900 olur.
        self._dene(
            _veri(), "kuyu_plani", "DBGW", "agirlik_ray_arasi", 900, beklenen={"agirlik_ray_arasi": 900}
        )

    def test_kuyu_dibi_degisince_kaide_izler(self):
        self._dene(_veri(), "kuyu_kesiti_yan", "KUYU DİBİ", "kuyu_dibi", 1600, beklenen={"kuyu_dibi": 1600})

    def test_baska_birimdeki_girdi(self):
        #  Kat yüksekliği = seyir / ( durak − 1 ):  seyir metre
        self._dene(
            _veri(), "kuyu_kesiti_yan", "2900", "seyir_mesafesi", 3000, beklenen={"seyir_mesafesi": 30}
        )

    def test_uzak_zincir_halkasi(self):
        #  22 konsolun sonuncuları:  konsol arası değişince konsol sayısı da değişir
        self._dene(
            _veri(),
            "kuyu_kesiti_yan",
            "1500",
            "agirlik_konsol_arasi",
            1400,
            n=20,
            beklenen={"agirlik_konsol_arasi": 1400},
        )

    def test_olcu_cizimde_bolunse_de(self):
        #  "ø 240":  kasnak çapı değişince zincir bölünür ( halat sapması ), ölçü
        #  ayrı görünmez — ölçü girdinin kendisi olduğu için yeni değer hedeftir.
        y = self._dene(
            _veri(), "kuyu_ustu", "ø", "tahrik_kasnak_capi", 320, beklenen={"tahrik_kasnak_capi": 320}
        )
        self.assertTrue(y["dogrulandi"])

    def test_dogrusal_olmayan_ve_kaynak_disi_istekler(self):
        v = _veri()
        r = UC._cozumleme(v, "kuyu_plani")
        i = _olcu(r, "KABİN EŞİĞİ")
        y = _degistir(v, "kuyu_plani", i, r, "kabin_esik_derinlik", 100)
        self.assertFalse(y["aktif"])  # ürün ölçüsü değiştirilmez
        i = _olcu(r, "KUYU GENİŞLİĞİ")
        self.assertFalse(_degistir(v, "kuyu_plani", i, r, "kuyu_genisligi", "abc")["aktif"])
        self.assertFalse(_degistir(v, "kuyu_plani", i, r, "kabin_genisligi", 2000)["aktif"])

    def test_cizimi_bozacak_deger_once_soylenir(self):
        #  Varsayılan asansörde kuyu 2.400 → 2.500:  kabin – duvar 0,30 m'yi
        #  aşar, korkuluk gerekir, korkuluk tavana sığmaz.  Uç değişikliği
        #  verir ama sebebini de ( ekran uygulamadan önce sorar ).
        v = DUZENLER["formun varsayılanı"]()
        r = UC._cozumleme(v, "kuyu_plani")
        i = _olcu(r, "KUYU GENİŞLİĞİ")
        y = _degistir(v, "kuyu_plani", i, r, "kuyu_genisligi", r["taban"][i]["uzunluk"] + 100)
        self.assertTrue(y["aktif"])
        self.assertTrue(any("Korkuluk" in u for u in y["uyarilar"]), y["uyarilar"])
        y = _degistir(v, "kuyu_plani", i, r, "kuyu_genisligi", r["taban"][i]["uzunluk"] - 50)
        self.assertEqual(y["uyarilar"], [])

    def test_uzunluk_secimi_olcuden_secilir(self):
        #  KAPI 900:  kapı genişliği bir seçim kutusu ( 700 · 800 · 900 … );
        #  ölçüden seçenek seçilir.  Askı oranı gibi kategoriler seçilmez.
        v = DUZENLER["formun varsayılanı"]()
        r = UC._cozumleme(v, "kuyu_plani")
        i = _olcu(r, "KAPI")
        k = UC._kaynaklar(r, i)[0]
        self.assertEqual(
            (k["anahtar"], k["tur"], k["degistirilir"], k["dogrudan"]),
            ("kapi_genisligi", "secim", True, True),
        )
        y = _degistir(v, "kuyu_plani", i, r, "kapi_genisligi", 1000)
        self.assertTrue(y["dogrulandi"], y)
        self.assertEqual((y["degisiklikler"][0]["deger"], y["olcu"]), (1000, 1000))
        for ad in ("kabin_ustu", "kuyu_dibi"):
            r = UC._cozumleme(v, ad)
            self.assertFalse(
                any(
                    x["anahtar"] == "aski_orani" and x["degistirilir"]
                    for i in range(len(r["taban"]))
                    for x in UC._kaynaklar(r, i)
                )
            )

    def test_cizim_degistiyse_yanlis_olcu_degismez(self):
        v = _veri()
        r = UC._cozumleme(v, "kuyu_plani")
        i = _olcu(r, "KUYU GENİŞLİĞİ")
        y = json.loads(
            UC.api_olcu_degistir(
                dict(v, cizim="kuyu_plani", olcu=i, metin="BAŞKA 1", anahtar="kuyu_genisligi", hedef=2200)
            ).body
        )
        self.assertFalse(y["aktif"])
        self.assertIn("değişmiş", y["hata"][0])
        y = json.loads(UC.api_olcu(dict(v, cizim="kuyu_plani", olcu=9999)).body)
        self.assertFalse(y["aktif"])
        y = json.loads(UC.api_olcu(dict(v, cizim="yok", olcu=0)).body)
        self.assertFalse(y["aktif"])

    def test_uc_kaynaklari_verir(self):
        v = _veri()
        r = UC._cozumleme(v, "kuyu_plani")
        i = _olcu(r, "KUYU GENİŞLİĞİ")
        y = json.loads(UC.api_olcu(dict(v, cizim="kuyu_plani", olcu=i, metin=r["taban"][i]["metin"])).body)
        self.assertTrue(y["aktif"])
        self.assertEqual(y["deger"], 2100)
        self.assertEqual(y["kaynaklar"][0]["anahtar"], "kuyu_genisligi")
        self.assertEqual(y["kaynaklar"][0]["etiket"], UC._sozlesme()[0]["kuyu_genisligi"]["etiket"])


def _gercek(ad):
    """Ofisin gerçek projesi formdan girilmiş gibi ( gercek_projeler.py )."""
    a = dict(GP.PROJELER[ad])
    pg = {k: a.pop(k) for k in list(a) if k in UC_UYG.PROJE_GENELI_ALANLAR}
    return {"asansorler": [a], "proje_geneli": pg, "sabitler": {}, "asansor": 0}


class RegulatorunYeri(unittest.TestCase):
    """Regülatörün yeri boşsa program onu kuralla arar ( kopru._regulator_yeri:
    varsayılan xs'in işaretine göre ±280, gergi çarpıyorsa başka yer ).  1022'de
    280'de gergi konsola değer, 360 seçilir.  Çözümleme her girdiyi 1 mm oynatıp
    çizimi yeniden kurar:  arama her kuruluşta baştan yapılıyor ( bir çizimin
    çözümlemesi 6 – 8 sn, ön istekle tıklama 12 sn ) ve askı kaçıklığı 0 → 1
    olunca regülatör rayın öbür yanına atlıyordu — kuyu dibinin ölçü zinciri
    değişiyor, 880'lik ölçü "askı kaçıklığına bağlı, eğimi −180" görünüyor,
    değiştirmek xs'e 0,05 mm yazıyordu.  Çözümlemede regülatör tabandaki yerinde
    tutulur;  seçim kutularında düzen yeniden kurulur."""

    @classmethod
    def setUpClass(cls):
        cls.v = _gercek("1022")
        UC._ONBELLEK.clear()
        cls.r = UC._cozumleme(cls.v, "kuyu_dibi")

    def test_ray_ekseni_olcusu_ray_kapi_arasindan(self):
        i = _olcu(self.r, "880")
        kaynak = {k["kimlik"][1] for k in self.r["kaynak"][i]}
        self.assertNotIn("aski_kaciklik_x", kaynak)
        self.assertIn("ray_kapi_arasi", kaynak)
        y = _degistir(self.v, "kuyu_dibi", i, self.r, "ray_kapi_arasi", "890")
        self.assertEqual([(d["anahtar"], d["deger"]) for d in y["degisiklikler"]], [("ray_kapi_arasi", 740)])
        self.assertTrue(y["dogrulandi"])

    def test_sayi_oynatmada_arama_yapilmaz(self):
        kd = _g(self.v)[0]["kuyu_dibi"]
        self.assertEqual((kd["regulator_yan"], kd["regulator_kaciklik"]), ("Sağ", 360))
        with mock.patch.object(CK, "_regulator_yeri") as m:
            self.r["kur"]({("girdi", "aski_kaciklik_x"): 1.0})
            self.r["kur"]({("girdi", "kuyu_derinligi"): 2251.0})
        self.assertFalse(m.called)
        #  Seçimde düzen kuralla yeniden kurulur
        with mock.patch.object(CK, "_regulator_yeri") as m:
            self.r["kur"]({("girdi", "agirlik_yeri"): "Sağ"}, denetle=True)
        self.assertTrue(m.called)

    def test_kabin_kuyu_ortasini_gecince(self):
        #  Üst zincir 1.000 · 5 · 995 ( kuyu ortası, kabin ekseni ).  995 → 1.005
        #  için kabin 5 → −5;  ölçü yolda "5 + 1.000" diye bölünür, izlenemez —
        #  kiriş yöntemi başka aralığı izleyip −15 veriyordu.  Doğrusal tahmin
        #  döner:  yeni çizimde iki ardışık parçanın toplamı hedeftir.
        i = _olcu(self.r, "995")
        y = _degistir(self.v, "kuyu_dibi", i, self.r, "kabin_yana_kaciklik", "1005")
        self.assertEqual(
            [(d["anahtar"], d["deger"]) for d in y["degisiklikler"]], [("kabin_yana_kaciklik", -5)]
        )
        self.assertFalse(y["dogrulandi"])
        self.assertTrue(y["bolundu"])


class Degistirilemeyen(unittest.TestCase):
    """Hedef doğrulanamıyor ve ölçü iki parçaya da bölünmüyorsa değer kutuya
    yazılmaz, sebebi söylenir — eskiden kabin genişliği 1.360 → 1.359,9995
    ( ölçü bir eşikte sıçrıyor ) ya da 58.430 yazılıyordu."""

    def test_sicrayan_olcu(self):
        #  4815-6 kabin üstü:  sığınma alanı şasenin üst kirişinin arkasındadır
        #  ( 4 Eki ) ve 25 mm'lik adımla konur — ray – kapı arası oynayınca
        #  kirişle birlikte kayar, arka kenara ölçü doğrusal değişmez.  ( Eskiden
        #  1022'de kabin genişliğiyle sıçrayan "125" ölçülüyordu;  alan kirişin
        #  arkasına geçince o ölçü kalmadı. )
        v = _gercek("4815-6")
        r = UC._cozumleme(v, "kabin_ustu")
        i = _olcu(r, "920")
        k = next(x for x in r["kaynak"][i] if x["kimlik"] == ("girdi", "ray_kapi_arasi"))
        self.assertFalse(k["dogrusal"])
        y = _degistir(v, "kabin_ustu", i, r, "ray_kapi_arasi", "940")
        self.assertFalse(y["aktif"])
        self.assertIn("düzgün değişmiyor", y["hata"][0])

    def test_adimla_kayan_olcu(self):
        #  Kuyu dibindeki sığınma alanı 25 mm'lik adımla konur:  1 mm'de
        #  doğrusal görünen ölçü 20 mm'de başka yere atlar ( eskiden kabin
        #  genişliği 58.430 çıkıyordu )
        v = DUZENLER["formun varsayılanı"]()
        r = UC._cozumleme(v, "kuyu_dibi")
        i = _olcu(r, "860")
        y = _degistir(v, "kuyu_dibi", i, r, "kabin_genisligi", "870")
        self.assertFalse(y["aktif"])

    def test_kiris_dogrularsa_o_kullanilir(self):
        #  1250 KG kabin üstü:  sığınma alanının yeri 295 → 305 için kabin
        #  1.240 → 1.300 doğrulanır ( doğrusal tahmin 1.250'de alan 25 mm'lik
        #  adımla kayar, ölçü 280 olur ).  10 Eki'ye dek örnek 1275'in 670'iydi:
        #  çapraz halat engel olunca alan başka yere taşındı.
        v = _gercek("1250 KG")
        r = UC._cozumleme(v, "kabin_ustu")
        i = _olcu(r, "295")
        y = _degistir(v, "kabin_ustu", i, r, "kabin_genisligi", "305")
        self.assertEqual(
            [(d["anahtar"], d["deger"]) for d in y["degisiklikler"]], [("kabin_genisligi", 1300)]
        )
        self.assertTrue(y["dogrulandi"])

    def test_negatif_olcu(self):
        v = _veri()
        r = UC._cozumleme(v, "kuyu_plani")
        i = _olcu(r, "KUYU GENİŞLİĞİ")
        y = _degistir(v, "kuyu_plani", i, r, "kuyu_genisligi", "-10")
        self.assertFalse(y["aktif"])
        self.assertIn("sıfırdan küçük", y["hata"][0])


class Hiz(unittest.TestCase):
    def test_ayni_cozumleme_bir_kez_yapilir(self):
        #  Ekran fare çizimin üstüne gelince çözümlemeyi önceden ister;  o
        #  bitmeden tıklanınca ikinci istek bekler, yeniden hesaplamaz.
        v = DUZENLER["örnek makine dairesiz"]()
        UC._ONBELLEK.clear()
        asil, sayac, sonuc = UC._cozumle, [], []

        def say(*a, **k):
            sayac.append(1)
            time.sleep(0.2)
            return asil(*a, **k)

        with mock.patch.object(UC, "_cozumle", side_effect=say):
            ipler = [
                threading.Thread(target=lambda: sonuc.append(UC._cozumleme(v, "kuyu_plani")))
                for _ in range(3)
            ]
            for t in ipler:
                t.start()
            for t in ipler:
                t.join()
        self.assertEqual(len(sayac), 1)
        self.assertEqual(len(sonuc), 3)
        self.assertTrue(all(r is sonuc[0] for r in sonuc))

    def test_yalniz_olcu_kipinde_olculer_ayni(self):
        #  Çözümlemede kuyu dibinin yük kutuları ve perde yazısı yerleşmez;
        #  ölçüler tam çizimdekiyle aynıdır.
        for v in (DUZENLER["örnek makine dairesiz"](), _gercek("1022")):
            g = _g(v)[0]
            tam_cizim = CKD.ciz(g)
            self.assertTrue(any(e.get("ad") == "yuk_kutusu" for e in tam_cizim))
            tam = CO.olculer(tam_cizim)
            with CGE.yalniz_olculer():
                kisa = CKD.ciz(g)
            self.assertEqual(CO.olculer(kisa), tam)
            self.assertFalse(any(e.get("ad") == "yuk_kutusu" for e in kisa))
            self.assertFalse(CGE.olcu_kipi())


class Parcalar(unittest.TestCase):
    def test_eslestirme(self):
        o = lambda a, b, m="#": {
            "yon": "yatay",
            "a": (a, 0),
            "b": (b, 0),
            "kot": 0,
            "metin": m,
            "uzunluk": b - a,
        }
        t = [o(0, 100, "1"), o(100, 300, "2"), o(300, 400, "3")]
        #  Dizi aynı:  sırayla ( uzak kayma da olsa )
        self.assertEqual(CO.eslestir(t, [o(0, 101), o(101, 330), o(330, 450)], 25), [0, 1, 2])
        #  Dizi değişti:  en yakın aynı sözlü
        self.assertEqual(CO.eslestir(t, [o(0, 101), o(101, 101), o(101, 301), o(301, 401)], 25), [0, 2, 3])
        #  Kesikli değişimde dizi değiştiyse eşleşme yok
        self.assertEqual(CO.eslestir(t, [o(0, 1)]), [None, None, None])
        #  Sonuna ölçü eklenince sırasıyla ( izleme )
        uzak = [o(0, 100), o(100, 900), o(900, 2000), o(2000, 2500)]
        self.assertEqual(CO.eslestir(t, uzak, 25, sira_yedek=True)[2], 2)

    def test_coz_dogrusal_olmayanda_kiris(self):
        #  Ölçü = girdi²:  eğim 2 ( x = 1'de ), hedef 9 → girdi 3
        def kur(d, serbest=False):
            x = d.get("x", 1.0)
            return [{"yon": "yatay", "a": (0, 0), "b": (x * x, 0), "kot": 0, "metin": "#", "uzunluk": x * x}]

        taban = kur({})
        s = CO.coz(kur, taban, 0, "x", 1.0, 2.0, 9.0)
        self.assertTrue(s["dogrulandi"])
        self.assertAlmostEqual(s["deger"], 3.0, places=3)

    def test_svg_tiklanir(self):
        g, _h = _g(_veri())
        for ad in CPF.sira(g):
            e = UC._elemanlar(g, ad)[0]
            n = len(CO.olculer(e))
            svg = UC._svg(g, ad, onek="c1-")["svg"]
            sira = [int(x) for x in re.findall(r'data-olcu="(\d+)"', svg)]
            self.assertEqual(sira, list(range(n)), ad)
            self.assertNotIn('id="tarama"', svg)
            self.assertIn('id="c1-tarama"', svg)
            #  Paftanın ve önizlemenin SVG'si eskisi gibi ( tıklanmaz )
            self.assertNotIn('class="olcu"', UC._svg(g, ad)["svg"])

    def test_sabitlere_yalniz_sabitler_ile_erisilir(self):
        #  Okunan ürün ölçüleri kaydı ( çözümleme yalnız onları oynatır ) ancak
        #  sabitlere CS.sabitler() ile erişilirse eksiksizdir.
        kok = os.path.join(KOK, "cizim")
        for ad in os.listdir(kok):
            if ad.endswith(".py") and ad != "sabitler.py":
                with open(os.path.join(kok, ad), encoding="utf-8") as f:
                    metin = f.read()
                self.assertNotRegex(metin, r"\bSABIT\s*\[|\bSABIT\.get|import SABIT", ad)
        with CS.okunanlar() as okunan:
            CS.sabitler()["esik_derinlik"]
        self.assertEqual(okunan, {"esik_derinlik"})
        self.assertIs(type(CS.sabitler()), dict)  # kayıt dışında sade sözlük

    def test_etiketler_ve_kurallar_tam(self):
        self.assertEqual(set(CS.ETIKET), set(CS.SABIT))
        #  Sayısal kutuların etkin değerleri ölçü çözümlemesinde bulunmalı;
        #  isteğe bağlı kat listesi metindir ve bu sayısal haritaya girmez.
        self.assertEqual(
            sorted(k for k in CK.ALAN if CK.ALAN[k][3] == "sayi" and CK.ALAN[k][5] is None),
            sorted(CK.KURALLI),
        )
        self.assertIn("kural", CGE._olcu("yatay", (0, 0), (1, 0), 0, kural="x"))


if __name__ == "__main__":
    unittest.main()

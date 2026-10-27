"""KOTLA GİRİŞ ( cikti/devir/KOT_PLANI.md ) — şema, kapı, türetme.

Mimari pafta konum ( kot ) verir;  seyir, KY, son kat ve tabliye iki konumun
farkıdır.  Kat girişinin iki kipi var ( tasarim/alanlar KAT GİRİŞİ ):  durak
kotları doluysa katlar KOTLA girilir ve ölçüden türeyen altı kutu okunmaz;
boşsa ÖLÇÜYLE girilir ve kot kutuları okunmaz — bir sayının iki kaynağı olmaz.

  -  Kot yazımı ( cizim/katlar.kot_oku ):  metre, işaretli, mm'ye kadar;  nokta
     da virgül de ondalık, binlik ayracı yok;  paftadan kopyalanan "−" ve "±0,00".
  -  Durak kotları alttan üste, kesin artan;  mm ile yazılmış liste birimini
     söyleyen iletiyle durur.
  -  Kapı öbür kipin alanını okumaz;  bozuk kot alanın adıyla reddedilir.
  -  TÜRETME tek yerde ( katlar.kot_tablosu, hesabın tamamla'sı ):  beklenen
     değerler kaynağın kendisinden — LD paftasının veri bloğu, mimarın plan
     kotları — programın çıktısından değil.
  -  "NE ÇİZİLİYORSA O HESAPLANIR":  kotla girilen proje ile aynı ölçülerin elle
     girildiği ikizi hesapta ve bütün paftalarda bit bit aynıdır;  bütün kotlar
     birlikte kayınca da.  Hatalı tabloda hesap da çizim de aynı iletiyle durur."""

import copy
import json
import os
import re
import unittest

from araclar import karne
from cizim import cizimler, dusey, geometri, giris, izli, katlar, kopru, veri_tablosu
from motor.uygulama import mukavemet
from tasarim import alanlar, gorunum
from testler import test_yerlesim_saglamligi
from uclar import care_uclari, cizim_uclari, uygulama_istegi, uygulama_uclari

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#  Kottan türeyen ( kotla girişte okunmayan ) alanlar — KOT_PLANI § 1.1
TURETILEN = {
    "durak_adedi",
    "seyir_mesafesi",
    "kat_yukseklikleri",
    "kuyu_dibi",
    "son_kat_yuksekligi",
    "tabliye_yuksekligi",
}
KOT_KUTULARI = {"kuyu_dibi_kotu", "kuyu_tavani_kotu", "md_zemini_kotu"}


def _istek(**a):
    v = test_yerlesim_saglamligi.standart_istek(1000, True, "Sağ")
    v["asansorler"][0].update(a)
    return v


class KotYazimi(unittest.TestCase):
    def test_okunan_yazimlar_mm_tam_sayi(self):
        for ham, mm in (
            ("−8,80", -8800),  # paftadan kopyalanan eksi ( U+2212 )
            ("-8.80", -8800),  # mimari CAD:  nokta ondalık
            ("–3,50", -3500),  # en tire ( kelime işlemci )
            ("+62,20", 62200),
            ("±0,00", 0),
            ("0", 0),
            ("8,805", 8805),  # virgülle üç ondalık:  mm
            ("8,8050", 8805),  # ön yüzün sona eklediği sıfır ( kutuyaYaz )
            ("0.805", 805),  # "0." ile başlayan nokta binlik olamaz
            (" − 8 , 80 ", -8800),
            (-8.8, -8800),  # API sayısı
            (57, 57000),
        ):
            with self.subTest(ham=ham):
                self.assertEqual(katlar.kot_oku(ham), (mm, None))
                self.assertIs(type(katlar.kot_oku(ham)[0]), int)

    def test_reddedilen_yazimlar_sebebiyle(self):
        for ham, sebep in (
            ("1.200", "belirsiz"),  # bin iki yüz de okunur
            ("+60.800", "belirsiz"),
            ("8,8051", "mm'den ince"),
            (8.8051, "mm'den ince"),
            ("1.234,56", "okunamadı"),  # binlik ayracı yok
            ("8,80m", "okunamadı"),
            ("abc", "okunamadı"),
            ("inf", "okunamadı"),
            ("±1,00", "yalnız sıfırda"),
            ("5000,001", "arasında olmalı"),
            (-6000, "arasında olmalı"),
            (1e12, "arasında olmalı"),
            (True, "kot olmalı"),
            ([], "kot olmalı"),
            (float("nan"), "kot olmalı"),
        ):
            with self.subTest(ham=ham):
                mm, ileti = katlar.kot_oku(ham)
                self.assertIsNone(mm)
                self.assertIn(sebep, ileti)

    def test_on_yuzle_ayni_liste(self):
        """Ön yüzün okuyucusu ( on-yuz/src/lib/kotlar.ts kotOku — vitest ) aynı listeyle
        sınanır:  ön yüzün okumadığını sunucu da reddeder ( ön yüz sunucudan sıkı
        olamaz ), okuduğunu aynı mm ile okur."""
        yol = os.path.join(KOK, "on-yuz", "src", "lib", "kot-yazimlari.json")
        with open(yol, encoding="utf-8") as f:
            liste = json.load(f)["yazimlar"]
        self.assertGreater(len(liste), 10)
        for ham, mm in liste:
            with self.subTest(ham=ham):
                self.assertEqual(katlar.kot_oku(ham)[0], mm)

    def test_sinir_metre_alanlarinin_tavani(self):
        self.assertEqual(katlar.kot_oku("-5000"), (-5_000_000, None))
        self.assertEqual(katlar.kot_oku("+5000"), (5_000_000, None))
        self.assertEqual(katlar.KOT_AZAMI_MM, alanlar.BIRIM_AZAMI["m"] * 1000)


class DurakKotlari(unittest.TestCase):
    def test_alttan_uste_noktali_virgul_ya_da_satir(self):
        for ham in ("−7,00; −3,50; ±0,00; +3,20", "-7;-3,5;0;3,2;", "-7\n-3,5\n0\n3,2", [-7, -3.5, 0, 3.2]):
            with self.subTest(ham=ham):
                self.assertEqual(katlar.kotlari_oku(ham), ([-7000, -3500, 0, 3200], []))

    def test_sira_ve_sayi_hatalari(self):
        for ham, sebep in (
            ("+3,20; ±0,00", "ters sırada"),
            ("0; 3; 3", "aynı kotta"),
            ("0; 3; 2; 5", "artan sırayla"),
            ("0", "en az iki durak"),
            ("0; 3,2; x", "3. kot okunamadı"),
            ("; ".join(str(i * 3) for i in range(101)), "en çok 100 durak"),
            ("1;" * 3000, "çok uzun"),
            (True, "noktalı virgülle"),
        ):
            with self.subTest(ham=str(ham)[:30]):
                kotlar, iletiler = katlar.kotlari_oku(ham)
                self.assertIsNone(kotlar)
                self.assertTrue(any(sebep in i for i in iletiler), iletiler)

    def test_mm_ile_yazilan_liste_birimini_soyler(self):
        """Kotun tavanı ya da 11 m kuralı da reddederdi, ama sebebi söylemeden."""
        for ham in ("0; 3200; 6400", "-7000; -3500; 0; 3200", [0, 3200, 6400]):
            with self.subTest(ham=ham):
                kotlar, iletiler = katlar.kotlari_oku(ham)
                self.assertIsNone(kotlar)
                self.assertIn("metreyle yazılır", iletiler[0])
        #  Ondalıksız ama metre:  4 m katlar, 100 m'nin altında 15 m'lik boşluk
        for ham in ("0; 4; 8; 12", "0; 4; 19"):
            with self.subTest(ham=ham):
                self.assertEqual(katlar.kotlari_oku(ham)[1], [])

    def test_kip(self):
        self.assertFalse(katlar.kot_kipi({}))
        self.assertFalse(katlar.kot_kipi({alanlar.DURAK_KOTLARI: "  "}))
        self.assertFalse(katlar.kot_kipi({alanlar.DURAK_KOTLARI: []}))
        self.assertTrue(katlar.kot_kipi({alanlar.DURAK_KOTLARI: "0; 3"}))
        #  Okunamayan değer de kotla giriştir:  kapı onun hatasını söyler
        self.assertTrue(katlar.kot_kipi({alanlar.DURAK_KOTLARI: 0}))


class Sema(unittest.TestCase):
    def test_kiplerin_alanlari(self):
        self.assertEqual(gorunum.kip_disi(True), TURETILEN)
        self.assertEqual(gorunum.kip_disi(False), KOT_KUTULARI)
        for k in KOT_KUTULARI:
            a = alanlar.ALAN[k]
            self.assertEqual((a.birim, a.tur, a.isaretli, a.opsiyonel), ("m", "sayi", True, True), k)
        #  Kipi belirleyen alan iki kipte de okunur;  tavan döşemesi de
        self.assertIsNone(alanlar.ALAN[alanlar.DURAK_KOTLARI].kip)
        self.assertIsNone(alanlar.ALAN["tavan_dosemesi"].kip)
        self.assertEqual(alanlar.ALAN["md_zemini_kotu"].yerlesim, "daireli")

    def test_kot_alanlari_hesabin_girdi_listesine_girmez(self):
        """Sözleşmesi CIZ:  mukavemetin girdisi türeyen sayılardır — kot hesabın
        çıktısına ( girdi listesi ) boş değerle girmesin ( altın )."""
        for k in KOT_KUTULARI | {alanlar.DURAK_KOTLARI, "tavan_dosemesi"}:
            self.assertEqual(alanlar.ALAN[k].sozlesme, alanlar.CIZ, k)

    def test_form_kipi_soyler(self):
        k = gorunum.form()["kot_kipi"]
        self.assertEqual(k["alan"], alanlar.DURAK_KOTLARI)
        self.assertEqual(set(k["gizli"]["kotla"]), TURETILEN)
        self.assertEqual(set(k["gizli"]["olcuyle"]), KOT_KUTULARI)
        self.assertEqual(uygulama_istegi.alanlar()["kot_kipi"], k)

    def test_kotlar_bina_olcusu(self):
        """Düzeltme öner:  kotlar ve tavan döşemesi binanındır — en sonda, işaretli."""
        self.assertLessEqual(KOT_KUTULARI | {"tavan_dosemesi"}, care_uclari.BINA)


class Kapi(unittest.TestCase):
    def _oku(self, v):
        return uygulama_istegi.asansor_girdileri(v)[0][0]

    def test_olcuyle_giriste_kot_okunmaz(self):
        a = self._oku(_istek(seyir_mesafesi="21", kuyu_dibi_kotu="abc", kuyu_tavani_kotu="+25,20"))
        self.assertEqual(a["seyir_mesafesi"], 21)
        self.assertIsNone(a["kuyu_dibi_kotu"])  # bozuk değer projeyi durdurmaz
        self.assertIsNone(a["kuyu_tavani_kotu"])

    def test_kotla_giriste_turetilen_okunmaz_kot_okunur(self):
        v = test_yerlesim_saglamligi.kotla(test_yerlesim_saglamligi.standart_istek(1000, False, "Sağ"))
        v["asansorler"][0].update(seyir_mesafesi="abc", kuyu_dibi="1600", durak_adedi="8")
        a = self._oku(v)
        for k in ("seyir_mesafesi", "kuyu_dibi", "durak_adedi"):
            self.assertIsNone(a[k], k)
        self.assertEqual(
            (a["kuyu_dibi_kotu"], a["kuyu_tavani_kotu"], a["md_zemini_kotu"]), (-1.6, 25.2, 24.15)
        )
        self.assertEqual(a[alanlar.DURAK_KOTLARI], v["asansorler"][0][alanlar.DURAK_KOTLARI])

    def test_bozuk_kot_alanin_adiyla_reddedilir(self):
        for alan, deger, sebep in (
            (alanlar.DURAK_KOTLARI, "0; 3; 2", "artan sırayla"),
            (alanlar.DURAK_KOTLARI, "0; 3200; 6400", "metreyle yazılır"),
            ("kuyu_dibi_kotu", "8,80m", "okunamadı"),
            ("kuyu_tavani_kotu", "1.200", "belirsiz"),
        ):
            with self.subTest(alan=alan, deger=deger):
                v = test_yerlesim_saglamligi.kotla(test_yerlesim_saglamligi.standart_istek(1000, True, "Sağ"))
                v["asansorler"][0][alan] = deger
                with self.assertRaises(uygulama_istegi.GecersizGirdi) as k:
                    uygulama_istegi.asansor_girdileri(v)
                (h,) = k.exception.hatalar
                self.assertTrue(h.startswith(alanlar.ALAN[alan].etiket), h)
                self.assertIn(sebep, h)

    def test_kip_asansor_basina(self):
        """Çok asansörlüde biri kotla, öbürü ölçüyle girilebilir ( 1. aşama:  asansör başına )."""
        v = test_yerlesim_saglamligi.kotla(test_yerlesim_saglamligi.standart_istek(1000, True, "Sağ"))
        v["asansorler"].append(
            dict(test_yerlesim_saglamligi.standart_istek(1000, True, "Sağ")["asansorler"][0])
        )
        v["asansorler"][1].update(seyir_mesafesi="30", kuyu_dibi_kotu="abc")
        v["asansorler"][0]["seyir_mesafesi"] = "abc"
        a, _o = uygulama_istegi.asansor_girdileri(v)
        self.assertEqual((a[0]["kuyu_dibi_kotu"], a[1]["kuyu_dibi_kotu"]), (-1.6, None))
        self.assertEqual((a[0]["seyir_mesafesi"], a[1]["seyir_mesafesi"]), (None, 30))

    def test_eski_istekte_yeni_alan_yok(self):
        """Kot alanı yazılmamış istek bugünkü gibi okunur:  yeni anahtar doğmaz
        ( hesap ve çizim bit bit aynı — altın testleri )."""
        a = self._oku(test_yerlesim_saglamligi.standart_istek(1000, True, "Sağ"))
        self.assertEqual(set(a) & (KOT_KUTULARI | {alanlar.DURAK_KOTLARI, "tavan_dosemesi"}), set())


#  63444-2 A BLOK — mimarın plan kotları ( KOTLAR.md § 3 ):  2. bodrum planında
#  kuyunun tabanı −8,80;  duraklar −7,00 ( 2. bodrum ) … +57,60 ( 18. kat ), iki
#  bodrum 3,50, kalanı 3,20;  çatı arası planında makine dairesinin zemini
#  +60,80, kuyunun üstü +62,30 ( döşemenin ÜSTÜ;  paftadaki tabliye betonu 100 —
#  kuyu tavanı, yani döşemenin altı, +62,20 ).
DURAKLAR_63444 = "−7,00; −3,50; ±0,00; " + "; ".join(
    f"+{3.2 * i:.2f}".replace(".", ",") for i in range(1, 19)
)
KOT_63444 = {
    alanlar.DURAK_KOTLARI: DURAKLAR_63444,
    "kuyu_dibi_kotu": "−8,80",
    "kuyu_tavani_kotu": "+62,20",
    "md_zemini_kotu": "+60,80",
}
#  Aynı kuyunun ölçüleri — mimarın kotlarından elle:  seyir 57,60 + 7,00 ·
#  KY 8,80 − 7,00 · son kat 62,20 − 57,60 · tabliye 62,30 − 60,80
OLCU_63444 = {
    "durak_adedi": 21,
    "seyir_mesafesi": 64.6,
    "kat_yukseklikleri": [3500, 3500] + [3200] * 18,
    "kuyu_dibi": 1800,
    "son_kat_yuksekligi": 4600,
    "tabliye_yuksekligi": 1500,
}

#  LiftDesigner paftaları ( KOTLAR.md § 2.1 — kesitlerin LD bloklarından ):
#  ( pafta , en alt durak , en üst durak , kuyu dibi kotu , LD'nin veri bloğunda
#  kuyu dibi , seyir ) — mm.  Beklenen iki sütun LD'nin kendi hesabıdır.
LD_PAFTALARI = (
    ("1022", 0, 9000, -1700, 1700, 9000),
    ("12495-18", 200, 3700, -1500, 1700, 3500),
    ("1250 KG MRL", 0, 12000, -1450, 1450, 12000),
    ("1275", -2500, 24500, -4200, 1700, 27000),
    ("4815-6", 180, 18330, -1520, 1700, 18150),
    ("800 KG", 200, 27700, -1500, 1700, 27500),
    ("K106", 0, 15000, -1700, 1700, 15000),
    ("K111", 0, 9000, -1480, 1480, 9000),
    ("K379", 0, 24000, -1750, 1750, 24000),
    ("K407", -3500, 6000, -5000, 1500, 9500),
    ("K431", -2750, 9250, -4200, 1450, 12000),
)


class Turetme(unittest.TestCase):
    def test_63444_2_mimari_kotlarindan(self):
        t, kot, hata = katlar.kot_tablosu(KOT_63444, 100, True)
        self.assertEqual(hata, [])
        self.assertEqual(t, OLCU_63444)
        self.assertEqual(kot["ofset"], -7000)
        self.assertEqual(kot["kaynak"]["seyir_mesafesi"], "+57,60 − ( -7,00 )")

    def test_ld_paftalarinin_kendi_hesabi(self):
        for pafta, alt, ust, dip, ky, seyir in LD_PAFTALARI:
            with self.subTest(pafta=pafta):
                A = {
                    alanlar.DURAK_KOTLARI: [alt / 1000, ust / 1000],
                    "kuyu_dibi_kotu": dip / 1000,
                    "kuyu_tavani_kotu": (ust + 4000) / 1000,
                }
                t, _kot, hata = katlar.kot_tablosu(A, 150, False)
                self.assertEqual(hata, [])
                self.assertEqual((t["kuyu_dibi"], t["seyir_mesafesi"] * 1000), (ky, seyir))
                self.assertNotIn("tabliye_yuksekligi", t)  # makine dairesiz

    def test_turler_kapinin_okudugu_gibi(self):
        """Tam değerli düz sayı int ( kapı "4600"ü 4600 okur ):  ikiz aynı türü alır."""
        t, _k, _h = katlar.kot_tablosu(KOT_63444, 100, True)
        self.assertIs(type(t["seyir_mesafesi"]), float)  # 64,6
        for k in ("durak_adedi", "kuyu_dibi", "son_kat_yuksekligi", "tabliye_yuksekligi"):
            self.assertIs(type(t[k]), int, k)
        t, _k, _h = katlar.kot_tablosu({**KOT_63444, alanlar.DURAK_KOTLARI: "0; 3; 21"}, 100, True)
        self.assertEqual((t["seyir_mesafesi"], type(t["seyir_mesafesi"])), (21, int))

    def test_hatali_tablo_turetmez(self):
        for degisiklik, sebep in (
            ({"kuyu_dibi_kotu": "−6,50"}, "en alt durağın altında"),
            ({"kuyu_dibi_kotu": "−7,00"}, "en alt durağın altında"),
            ({"kuyu_tavani_kotu": "+57,00"}, "en üst durağın üstünde"),
            ({"md_zemini_kotu": "+62,40"}, "tabliyenin üstünden yukarıda"),
            ({"kuyu_tavani_kotu": None}, "kotla girişte girilmeli"),
            ({"kuyu_dibi_kotu": "x"}, "okunamadı"),
            ({alanlar.DURAK_KOTLARI: "0; 3; 2"}, "artan sırayla"),
        ):
            with self.subTest(degisiklik=degisiklik):
                t, kot, hata = katlar.kot_tablosu({**KOT_63444, **degisiklik}, 100, True)
                self.assertEqual((t, kot), ({}, {}))
                self.assertTrue(any(sebep in h for h in hata), hata)
        #  Makine dairesizde zeminin kotu sorulmaz
        A = {k: v for k, v in KOT_63444.items() if k != "md_zemini_kotu"}
        self.assertEqual(katlar.kot_tablosu(A, 100, False)[2], [])

    def test_bos_zemin_kotu_tabliyenin_varsayilani(self):
        """Makine dairesinin zemini KURAL:  boşsa tabliye 1.200 ( ölçüyle girişteki
        varsayılan ) — zemin +62,30 − 1,20 = +61,10;  ekran kuralın kotunu soluk
        gösterir ( türetilende md_zemini_kotu ).  Ölçü kaynağı kutunun kendisi."""
        A = {**KOT_63444, "md_zemini_kotu": ""}
        t, _k, hata = katlar.kot_tablosu(A, 100, True)
        self.assertEqual(hata, [])
        self.assertEqual((t["tabliye_yuksekligi"], t["md_zemini_kotu"]), (1200, 61.1))
        with izli.izleme():
            A = {**A, "kuyu_tavani_kotu": izli.girdi(62.2, ("girdi", "kuyu_tavani_kotu"))}
            t, _k, _h = katlar.kot_tablosu(A, izli.girdi(100.0, ("girdi", "tavan_dosemesi")), True)
            self.assertEqual(izli.turev(t["tabliye_yuksekligi"]), {("girdi", "md_zemini_kotu"): -1000.0})

    def test_olcuyle_giris_turetmez(self):
        self.assertEqual(katlar.kot_tablosu({"seyir_mesafesi": 21}, 150, True), ({}, {}, []))

    def test_izli_turev_kotlara_tasinir(self):
        """Ölçü kaynağı ve çare türevle çalışır:  KY'nin kaynağı kuyu dibi kotu ( mm /
        m );  makine dairesinin zemini döşemenin kalınlığına bağlı kalmaz."""
        with izli.izleme():
            A = {
                alanlar.DURAK_KOTLARI: DURAKLAR_63444,
                **{
                    k: izli.girdi(v, ("girdi", k))
                    for k, v in (
                        ("kuyu_dibi_kotu", -8.8),
                        ("kuyu_tavani_kotu", 62.2),
                        ("md_zemini_kotu", 60.8),
                    )
                },
            }
            d = izli.girdi(100.0, ("girdi", "tavan_dosemesi"))
            t, _k, hata = katlar.kot_tablosu(A, d, True)
            self.assertEqual(hata, [])
            #  KY iki kotun farkı:  kuyu dibi kotu ( mm / m ) ve en alt durağın kotu
            #  ( ( "kot" , 0 ) — ölçü kaynağında yalnız gösterilir )
            self.assertEqual(
                izli.turev(t["kuyu_dibi"]), {("girdi", "kuyu_dibi_kotu"): -1000.0, ("kot", 0): 1.0}
            )
            self.assertEqual(
                izli.turev(t["son_kat_yuksekligi"]),
                {("girdi", "kuyu_tavani_kotu"): 1000.0, ("kot", 20): -1.0},
            )
            self.assertEqual(izli.turev(t["kat_yukseklikleri"][0]), {("kot", 0): -1.0, ("kot", 1): 1.0})
            #  Değer gürültüsüz:  −7.000 − ( −8.800 ) tam 1.800
            self.assertEqual(float(t["kuyu_dibi"]), 1800.0)
            #  Zemin = tavan + döşeme − tabliye ( çizimin kurduğu ):  yalnız kendi kotuna bağlı
            tavan = izli.oturt(A["kuyu_tavani_kotu"] * 1000.0)
            zemin = tavan + d - t["tabliye_yuksekligi"]
            self.assertEqual(float(zemin), 60800.0)
            self.assertEqual(izli.turev(zemin), {("girdi", "md_zemini_kotu"): 1000.0})


_YAZI = re.compile(r">([^<>]*)</text>")
_KOT_YAZISI = re.compile(r">([±+-])(\d+),(\d\d)</text>")


def _ic_kotlar(svg, ofset):
    """Kot yazıları iç koordinatta ( en alt durak ±0,00 ):  kot yalnız yazıya
    eklenir ( KOT_PLANI § 1.2 madde 3 ) — geri çıkarılınca pafta ölçüyle
    girişinkiyle aynı olmalı."""

    def ic(m):
        mm = (-1 if m[1] == "-" else 1) * (int(m[2]) * 1000 + int(m[3]) * 10) - ofset
        return ">" + dusey.kot_yazisi(mm) + "</text>"

    return _KOT_YAZISI.sub(ic, svg)


def _girisle(bolumler):
    """Raporun kaynak sütununda kottan türeyen satır "GİRİŞ" sayılır:  ikizde
    aynı satırı kullanıcı yazmıştır ( kaynağın kendisi ayrıca denetlenir —
    RaporunKaynagi )."""
    for b in bolumler:
        for x in b.get("adimlar") or []:
            if str(x.get("kaynak") or "").startswith(mukavemet.KOT + "  ·"):
                x["kaynak"] = "GİRİŞ"
    return bolumler


def _yuz(v, ofset=0):
    """Karşılaştırılan yüz ( uçlardan — ekranın ve paftanın gördüğü ):  hesabın
    bölümleri ( kaynak sütunu _girisle ), özeti, uyarıları;  paftaların SVG'si,
    kot yazıları iç koordinatta ( ofset:  en alt durağın kotu, mm );  veri
    tablosunun yazıları ayrı — kotla girişin notu orada."""
    h = json.loads(uygulama_uclari.api_uygulama_coklu(copy.deepcopy(v)).body)
    c = json.loads(cizim_uclari.api_cizimler(copy.deepcopy(v)).body)
    assert h.get("aktif") and c.get("aktif"), (h.get("hata"), c.get("hata"))
    a = h["asansorler"][0]
    a["bolumler"] = _girisle(a["bolumler"])
    svg = {x["ad"]: _ic_kotlar(x["svg"], ofset) for x in c["cizimler"]}
    return {k: a[k] for k in ("bolumler", "ozet", "uyarilar")}, svg, _YAZI.findall(svg.pop("veriler"))


def _md_63444(v):
    """63444-2'nin makine dairesi:  iç yükseklik 3.700 ( projenin dosyası — tabliye
    1.500'ün üstünde çalışma alanı m.5.2.6.3.2.1 ), tabliye betonu 100."""
    v["proje_geneli"]["md_yukseklik"] = 3700
    v["asansorler"][0]["tavan_dosemesi"] = 100
    return v


def _kotla(v, kotlar, **ek):
    """İsteği verilen kotlarla kotla girişe çevirir ( ölçü kutuları istekten çıkar )."""
    a = v["asansorler"][0]
    for k in TURETILEN:
        a.pop(k, None)
    a.update(kotlar, **ek)
    return v


class NeCiziliyorsaOHesaplanir(unittest.TestCase):
    """Kotla giriş ↔ ölçüyle giriş:  türetme tek yerde, hesap ve çizim aynı sayıyı okur."""

    def _ikiz(self, kot, olcu, ofset=0):
        """Hesap ve paftalar aynı ( kot yazıları ofset kadar kayık );  veri tablosunda
        kotla girişin notu fazladan ( "2." ve notun kendisi ), gerisi aynı."""
        hk, sk, vk = _yuz(kot, ofset)
        ho, so, vo = _yuz(olcu)
        self.assertEqual(hk, ho)
        self.assertEqual(sk, so)
        self.assertNotIn(veri_tablosu.KOT_NOTU, vo)
        i = vk.index(veri_tablosu.KOT_NOTU)
        self.assertEqual(vk[: i - 1] + vk[i + 1 :], vo)

    def test_ikiz_ayni(self):
        for ad, mrl, Q, ek in (
            ("makine dairesiz", True, 1000, {}),
            ("makine daireli", False, 1000, {}),
            ("karışık katlar", False, 630, {"kat_yukseklikleri": "3400; 3000; 3000; 3000; 3000; 3000; 2600"}),
        ):
            with self.subTest(ad):
                v = test_yerlesim_saglamligi.standart_istek(Q, mrl, "Sağ")
                v["asansorler"][0].update(ek)
                self._ikiz(test_yerlesim_saglamligi.kotla(copy.deepcopy(v)), v)

    def test_63444_2_ikizi(self):
        """Mimarın kotları ile LD'nin ölçüleri ( döşemenin 100'üyle ):  21 durak, iki
        bodrum, makine dairesi — hesabın gördüğü sayılar ve paftalar aynı."""
        v = _md_63444(test_yerlesim_saglamligi.standart_istek(1000, False, "Sağ"))
        v["asansorler"][0]["kuyu_duvar_kalinligi"] = 250
        olcu = copy.deepcopy(v)
        olcu["asansorler"][0].update(
            {k: ("; ".join(map(str, x)) if isinstance(x, list) else x) for k, x in OLCU_63444.items()}
        )
        kot = _kotla(copy.deepcopy(v), KOT_63444)
        self._ikiz(kot, olcu, -7000)
        g = json.loads(uygulama_uclari.api_uygulama_coklu(kot).body)["asansorler"][0]["girdi"]
        self.assertEqual(
            {k: g[k] for k in OLCU_63444 if k != "kat_yukseklikleri"},
            {k: x for k, x in OLCU_63444.items() if k != "kat_yukseklikleri"},
        )
        #  Kuyu boyu ( HESAP ):  kuyu tavanı − kuyu dibi = 62,20 + 8,80
        self.assertEqual(g["kuyu_boyu"], 71000)

    def test_butun_kotlar_kayinca_hesap_ve_cizim_degismez(self):
        """±0,00'ın yeri ( mimarın datumu ) geometriye girmez:  iç koordinat 0 = en alt durak."""
        v = _md_63444(test_yerlesim_saglamligi.standart_istek(1000, False, "Sağ"))

        def kaydir(m):
            return {
                alanlar.DURAK_KOTLARI: "; ".join(
                    katlar.kot_metni(k + m) for k in katlar.kotlari_oku(DURAKLAR_63444)[0]
                ),
                "kuyu_dibi_kotu": katlar.kot_metni(-8800 + m),
                "kuyu_tavani_kotu": katlar.kot_metni(62200 + m),
                "md_zemini_kotu": katlar.kot_metni(60800 + m),
            }

        yuz = _yuz(_kotla(copy.deepcopy(v), kaydir(0)), -7000)
        for m in (7000, -3250):
            with self.subTest(kayma=m):
                self.assertEqual(_yuz(_kotla(copy.deepcopy(v), kaydir(m)), -7000 + m), yuz)
        #  Mutlak kot ( deniz seviyesinden:  +850 m ):  yazılar uzar ( "+843,00" ),
        #  yazı yerleştirici onlara yer açar — hesap ve yazıların içeriği aynı, yerleri
        #  serbest ( geometri yukarıdaki kaymalarda birebir )
        h, s, veri = _yuz(_kotla(copy.deepcopy(v), kaydir(850_000)), -7000 + 850_000)
        self.assertEqual((h, veri), (yuz[0], yuz[2]))
        for ad in s:
            self.assertEqual(sorted(_YAZI.findall(s[ad])), sorted(_YAZI.findall(yuz[1][ad])), ad)

    def test_hatali_tabloda_hesap_ve_cizim_ayni_iletiyle_durur(self):
        for degisiklik, sebep in (
            ({"kuyu_dibi_kotu": "+0,50"}, "en alt durağın altında"),
            ({"kuyu_tavani_kotu": ""}, "kotla girişte girilmeli"),
            ({"md_zemini_kotu": "+70,00"}, "tabliyenin üstünden yukarıda"),
        ):
            with self.subTest(degisiklik=degisiklik):
                v = test_yerlesim_saglamligi.kotla(
                    test_yerlesim_saglamligi.standart_istek(1000, False, "Sağ")
                )
                v["asansorler"][0].update(degisiklik)
                h = json.loads(uygulama_uclari.api_uygulama_coklu(copy.deepcopy(v)).body)
                c = json.loads(cizim_uclari.api_cizimler(copy.deepcopy(v)).body)
                self.assertFalse(h["aktif"])
                self.assertFalse(c["aktif"])
                (ileti,) = c["hata"]
                self.assertIn(sebep, ileti)
                self.assertIn(ileti, h["hata"])

    def test_paftadaki_kotlar_mimarinin(self):
        """Kesitlerde duraklar, kuyu dibi, makine dairesinin zemini ve tabliyenin
        üstü mimari paftadaki sayılarla yazılır ( 63444-2 ):  tabliyenin üstü
        +62,30 — mimarın çatı arası planındaki kot, kuyu tavanı +62,20 + 100'den.
        Giriş görünüşü ve kapı kesiti en alt durağın kapısıdır."""
        v = _md_63444(test_yerlesim_saglamligi.standart_istek(1000, False, "Sağ"))
        c = json.loads(cizim_uclari.api_cizimler(_kotla(v, KOT_63444)).body)
        self.assertTrue(c["aktif"], c.get("hata"))
        kot = {x["ad"]: [m[0][1:-7] for m in _KOT_YAZISI.finditer(x["svg"])] for x in c["cizimler"]}
        duraklar = [katlar.kot_metni(k) for k in katlar.kotlari_oku(DURAKLAR_63444)[0]]
        self.assertEqual(duraklar[:3] + duraklar[-1:], ["-7,00", "-3,50", "±0,00", "+57,60"])
        for ad in ("kuyu_kesiti_yan", "kuyu_kesiti_on"):
            self.assertEqual(kot[ad], duraklar + ["-8,80", "+60,80", "+62,30"], ad)
        self.assertEqual((kot["giris"], kot["kapi_kesiti"]), (["-7,00"], ["-7,00"]))

    def test_turetilmeden_gelen_kot_koprude_durur(self):
        """Bir yol hesabın tamamla'sını atlarsa çizim eski sayılarla sessizce kurulmaz."""
        with self.assertRaises(RuntimeError):
            kopru.cizim_girdisi({alanlar.DURAK_KOTLARI: "0; 3"})


def _kotlu_63444():
    v = _md_63444(test_yerlesim_saglamligi.standart_istek(1000, False, "Sağ"))
    v["asansorler"][0]["kuyu_duvar_kalinligi"] = 250
    return _kotla(v, KOT_63444)


class GirisKotu(unittest.TestCase):
    """Giriş görünüşünde kot işareti yerinde kalır ( kot geometriye girmez ),
    yazısının maskesi kenar silmez, ayırıcı yazıyı kaydırmaz.  Kenara binen
    yazıyı ayırıcı tek başına kaydırıyordu:  yazı işaretinden kopuyor ya da kendi
    üçgeninin üstüne düşüyordu ( 27 Eki kotlu tarama:  "-10,50" 78, mutlak
    "+850,00" 143 düzende kasaya;  ölçüyle girişte 4 kanatlı kapıda "±0,00"
    kanadın kenarına ).  kesit_parcalari.kot_isareti:  yazı ucun 60 sağında,
    döşemeden 80 yukarıda.  Kanattan geniş yazı ( 450'nin 4 kanatlısında
    "-10,50" ) kapının içinde temiz yer bulamaz:  eşiğin altına iner
    ( test_kanattan_genis_yazi_esigin_altinda )."""

    def test_isaret_yerinde_yazi_temiz(self):
        for Q, ek, kaymalar in (
            (450, {}, (-10500, 850000)),
            (1600, {"kat_kapisi_tipi": "Otomatik Merkezi 4 Kanat"}, (-10500,)),
            (2500, {}, (-10500, 850000)),
        ):
            u = None
            for kayma in (None, *kaymalar):
                v = test_yerlesim_saglamligi.standart_istek(Q, True, "Sağ", **ek)
                if kayma is not None:
                    test_yerlesim_saglamligi.kotla(v, 0, kayma)
                g, _A, _h = test_yerlesim_saglamligi.duzen_girdisi(v)
                yerlesen = next(x for x in giris.ciz(g) if x.get("ad") == "kot")
                e = cizimler.CIZIMLER["giris"][1](g)
                kot = next(x for x in e if x.get("ad") == "kot")
                if u is None:  # ölçüyle giriş:  yazı işaretin yanında
                    u = kot["x"] - 60.0
                    self.assertEqual(kot["y"], 80.0, Q)
                cizgiler = [_uclar(x) for x in e if x["tip"] == "cizgi"]
                with self.subTest(Q=Q, kot=kot["metin"]):
                    self.assertIn({(round(u, 3), 0.0), (round(u + 40.0, 3), 55.0)}, cizgiler, "işaret kaydı")
                    self.assertEqual((kot["x"], kot["y"]), (yerlesen["x"], yerlesen["y"]), "ayırıcı kaydırdı")
                    self.assertEqual(karne.karne(e, 20)["maske_kenar_siliyor"], [])

    def test_kanattan_genis_yazi_esigin_altinda(self):
        """27 Eki kotlu tarama:  kanattan geniş yazının kapının içinde maskesi
        temiz yeri yoktur ( 450'nin 4 kanatlısında kanat 200, "-10,50"ın maskesi
        216 ) — kanadın ve kasanın kenarını siliyordu.  Eşiğin altına iner
        ( giris._esigin_altina ):  işaret yerinde, yazı işaretin hizasından en
        çok 200 öte, maskesi kenar ve ölçü çizgisi silmez;  ölçüyle girişte
        "±0,00" işaretin yanında kalır."""
        for Q, tip, kayma in (
            (450, "Otomatik Merkezi 4 Kanat", -10500),
            (450, "Teleskopik 3 Kanat Sol", 850000),
            (1600, "Otomatik Merkezi 4 Kanat", 850000),
        ):
            u = None
            for k in (None, kayma):
                v = test_yerlesim_saglamligi.standart_istek(Q, True, "Sağ", kat_kapisi_tipi=tip)
                if k is not None:
                    test_yerlesim_saglamligi.kotla(v, 0, k)
                g, _A, _h = test_yerlesim_saglamligi.duzen_girdisi(v)
                e = cizimler.CIZIMLER["giris"][1](g)
                kot = next(x for x in e if x.get("ad") == "kot")
                b = karne.karne(e, 20)
                with self.subTest(Q=Q, tip=tip, kot=kot["metin"]):
                    if u is None:
                        u = kot["x"] - 60.0
                        self.assertEqual(kot["y"], 80.0, "ölçüyle girişte yazı işaretin yanında")
                    else:
                        alt = giris.yerlesim(g)["esik"][1]
                        self.assertLess(geometri.maske_kutusu(kot)[3], alt, "eşiğin altında")
                        self.assertLessEqual(abs(kot["x"] - (u + 60.0)), 200.0, "işaretinden kopmaz")
                    cizgiler = [_uclar(x) for x in e if x["tip"] == "cizgi"]
                    self.assertIn({(round(u, 3), 0.0), (round(u + 40.0, 3), 55.0)}, cizgiler, "işaret kaydı")
                    self.assertEqual((b["maske_kenar_siliyor"], b["maske_olcu_siliyor"]), ([], []))


def _uclar(x):
    return {(round(x["x1"], 3), round(x["y1"], 3)), (round(x["x2"], 3), round(x["y2"], 3))}


class OlcuKaynagi(unittest.TestCase):
    """Ölçüye tıklanınca kaynak kotlardır:  kot kutusu değiştirilir, durağın kotu
    yalnız gösterilir ( kot tablosunda değişir );  türeyen kutu kaynak değildir."""

    @classmethod
    def setUpClass(cls):
        cls.v = _kotlu_63444()
        cls.r = cizim_uclari._cozumleme(copy.deepcopy(cls.v), "kuyu_kesiti_yan")

    def _kaynak(self, soz):
        i = next(j for j, o in enumerate(self.r["taban"]) if o["metin"].startswith(soz))
        return i, [
            (k["anahtar"], k.get("durak"), round(k["egim"], 6), k["degistirilir"])
            for k in cizim_uclari._kaynaklar(self.r, i)
        ]

    def test_kaynaklar_kotlar(self):
        D = alanlar.DURAK_KOTLARI
        for soz, beklenen in (
            ("KUYU DİBİ", [("kuyu_dibi_kotu", None, -1000.0, True), (D, 0, 1.0, False)]),
            ("3500", [(D, 0, -1.0, False), (D, 1, 1.0, False)]),
            ("SEYİR", [(D, 0, -1.0, False), (D, 20, 1.0, False)]),
            ("OH", [("kuyu_tavani_kotu", None, 1000.0, True), (D, 20, -1.0, False)]),
        ):
            with self.subTest(soz):
                self.assertEqual(sorted(self._kaynak(soz)[1], key=str), sorted(beklenen, key=str))

    def test_tureyen_kutu_kaynak_degil(self):
        kaynaklar = {
            k["anahtar"] for i in range(len(self.r["taban"])) for k in cizim_uclari._kaynaklar(self.r, i)
        }
        self.assertEqual(kaynaklar & gorunum.kip_disi(True), set())

    def test_olcuden_degistirme_kota_yazar(self):
        """KOTLAR.md § 6.7:  KUYU DİBİ 1.800 → 1.950 kuyu dibi kotunu −8,80'den −8,95'e indirir."""
        i, _k = self._kaynak("KUYU DİBİ")
        y = json.loads(
            cizim_uclari.api_olcu_degistir(
                dict(
                    copy.deepcopy(self.v),
                    cizim="kuyu_kesiti_yan",
                    olcu=i,
                    metin=self.r["taban"][i]["metin"],
                    anahtar="kuyu_dibi_kotu",
                    hedef=1950,
                )
            ).body
        )
        self.assertTrue(y["aktif"], y)
        self.assertEqual(
            [(d["anahtar"], d["deger"]) for d in y["degisiklikler"]], [("kuyu_dibi_kotu", -8.95)]
        )


class RaporunKaynagi(unittest.TestCase):
    """Hesap raporu kottan türeyen değerin kaynağını formülüyle yazar ( KOTLAR.md
    § 6.5:  "H = +57,60 − ( −7,00 ) = 64,60 m" );  ölçüyle girişte "GİRİŞ"."""

    def _satirlar(self, v):
        h = json.loads(uygulama_uclari.api_uygulama_coklu(copy.deepcopy(v)).body)
        return {
            x["aciklama"]: (x["deger"], x["kaynak"])
            for b in h["asansorler"][0]["bolumler"]
            for x in b.get("adimlar") or []
            if x.get("aciklama") in ("Seyir mesafesi", "En üst durak ( son kat ) yüksekliği")
        }

    def test_kotla_giriste_kot_ve_formul(self):
        self.assertEqual(
            self._satirlar(_kotlu_63444()),
            {
                "Seyir mesafesi": (64.6, "KOT  ·  +57,60 − ( -7,00 )"),
                "En üst durak ( son kat ) yüksekliği": (4600, "KOT  ·  +62,20 − ( +57,60 )"),
            },
        )

    def test_olcuyle_giriste_giris(self):
        self.assertEqual(
            {
                k: x[1]
                for k, x in self._satirlar(test_yerlesim_saglamligi.standart_istek(1000, True, "Sağ")).items()
            },
            {"Seyir mesafesi": "GİRİŞ", "En üst durak ( son kat ) yüksekliği": "GİRİŞ"},
        )


class DuzeltmeOner(unittest.TestCase):
    def test_sig_kuyuya_kuyu_dibi_kotu_onerilir(self):
        """Kuyu dibi yetmeyince bina ölçüsü olarak kuyu dibi KOTU önerilir ( en sonda,
        işaretli, mimarın diliyle );  türeyen kuyu dibi kutusu önerilmez."""
        v = test_yerlesim_saglamligi.kotla(test_yerlesim_saglamligi.standart_istek(1000, True, "Sağ"))
        v["asansorler"][0]["kuyu_dibi_kotu"] = "-1,05"  # KY 1.050
        r = care_uclari.coz(copy.deepcopy(v), 0)
        oneriler = [o for c in r["careler"] for o in c["oneriler"]]
        kot = [o for o in oneriler if o["anahtar"] == "kuyu_dibi_kotu"]
        self.assertTrue(kot, r)
        for o in kot:
            self.assertTrue(o["bina"])
            self.assertLess(o["yeni"], o["eski"])
            self.assertTrue(o["aciklama"].endswith("cm daha derin"), o["aciklama"])
        self.assertEqual({o["anahtar"] for o in oneriler} & gorunum.kip_disi(True), set())


if __name__ == "__main__":
    unittest.main()

"""TRAFİĞİN KAT DÜZENİ KOT TABLOSUNDAN ( cikti/devir/KOT_TABLOSU_PLANI.md, 16 Kas ).

Kullanıcı:  "kot tablosu en başta olsa, trafik hesabı ortalama kat yüksekliğini buradan
hesaplasa … çizimlerle hesaplar birebir uyumlu olur".  Binanın kot tablosu doluyken trafik
ucu N / bodrum / h'yi ondan türetir ( katlar.kat_duzeni, avan_uclari._kat_duzeni );  motor
değişmez.  Burada:  kural, sınır durumları, uç ve DEĞİŞMEZ — rastgele kot tablolarında
trafiğin toplam seyahati avanın kotlardan türettiği seyirle, durak sayıları birbiriyle
aynıdır ve avan "kat düzeni tutmuyor" demez.  Son halka ÇİZİM ( planın 4. adımı ):  her
asansörün düşey kesitlerinde yazan durak kotları tablonunkilerdir — ekranda ve pakette."""

import io
import json
import random
import re
import unittest
import zipfile

import ezdxf

from cizim import katlar
from testler.test_avan_cizim_ucu import T630
from testler.test_avan_cizim_ucu import kart as cizim_karti
from uclar import avan_cizim_uclari, avan_uclari

BINA = {"bina_tipi": "Konut", "bina_yuksekligi": "30", "yapi_yuksekligi": "31", "hizli1": "20", "hizli2": "2"}
ASANSOR = {"P": "8", "kapi_genisligi": "800", "kapi_tipi": "Teleskopik Otomatik"}
KART = {"kuyu_genisligi": "2050", "kabin_boyu": "1400", "kabin_genisligi": "1100", "eta": "0,85"}


def trafik(**ek):
    g = {**BINA, "asansorler": [dict(ASANSOR)], **ek}
    return json.loads(avan_uclari.api_trafik({"girdiler": g}).body)


def avan(kart, kopru):
    a = kopru["asansorler"][0]
    kart = {**KART, "kapasite": str(a["P"]), "V": str(a["V"]), **kart}
    g = {"ortak": {"mk_yok": True}, "asansorler": [kart], "sabitler": {}, "trafik": kopru}
    return json.loads(avan_uclari.api_avan({"girdiler": g}).body)


def metin(kotlar):
    return "; ".join(katlar.kot_metni(k) for k in kotlar)


def sayilar(o):
    """Yanıtın sayıları tek türde ( 3 ile 3.0 aynı sayıdır ):  karşılaştırma için."""
    if isinstance(o, dict):
        return {k: sayilar(v) for k, v in o.items()}
    if isinstance(o, list):
        return [sayilar(v) for v in o]
    return float(o) if isinstance(o, (int, float)) and not isinstance(o, bool) else o


class Kural(unittest.TestCase):
    def test_bodrumlu_esitsiz_katlar(self):
        d, ileti = katlar.kat_duzeni("-3,20; ±0,00; +4,50; +7,60; +10,70; +13,80")
        self.assertEqual(ileti, [])
        self.assertEqual((d["N"], d["bodrum"], d["durak"], d["giris"]), (4, 1, 6, 2))
        self.assertAlmostEqual(d["seyir"], 17.0, places=12)
        self.assertAlmostEqual(d["h"], 17.0 / 5, places=12)
        #  Trafiğin toplam seyahati ( N + bodrum ) · h = kotların seyri
        self.assertAlmostEqual((d["N"] + d["bodrum"]) * d["h"], d["seyir"], places=12)

    def test_giris_kati_cizimin_kuraliyla(self):
        """Giriş:  verilmişse o;  yoksa kotu ±0,00'a en yakın durak ( katlar.durak_adlari —
        çizimin kat adları da onu kullanır )."""
        kot = "-2,50; +0,50; +3,50; +6,50"
        self.assertEqual(katlar.kat_duzeni(kot)[0]["giris"], 2)
        d = katlar.kat_duzeni(kot, "1")[0]
        self.assertEqual((d["giris"], d["N"], d["bodrum"]), (1, 3, 0))
        _adlar, g, _hata = katlar.durak_adlari(None, None, [-2500, 500, 3500, 6500])
        self.assertEqual(g + 1, 2)

    def test_sinir_durumlari(self):
        for kot, giris, beklenen in (
            ("±0,00", None, "en az iki durak gerekir"),
            ("±0,00; +3,00; +2,00", None, "artan sırayla"),
            ("-3,00; ±0,00", None, "Giriş katı en üst durak"),
            ("±0,00; +3,00", "2", "Giriş katı en üst durak"),
            ("±0,00; +3,00", "5", "giriş katı 5. durak olamaz"),
            ("±0,00; +3,00", "iki", "durağın sırası yazılır"),
        ):
            with self.subTest(kot=kot, giris=giris):
                d, ileti = katlar.kat_duzeni(kot, giris)
                self.assertIsNone(d)
                self.assertEqual(len(ileti), 1)
                self.assertIn(beklenen, ileti[0])


class Uc(unittest.TestCase):
    def test_tablo_bosken_elle_girilen(self):
        r = trafik(N="10", h="3")
        self.assertNotIn("kat_duzeni", r)
        self.assertEqual((r["ozet"]["N"], r["ozet"]["h"], r["ozet"]["toplam_seyahat"]), (10, 3, 30))

    def test_esit_katli_tablo_elle_girisle_ayni_sonucu_verir(self):
        """Motor aynı üç sayıyı alır:  10 kat × 3 m'nin kot tablosu ile elle N = 10, h = 3
        girişi AYNI trafik hesabını verir — yanıtın tamamı;  fark yalnız girdinin yankısı
        ( "girdiler":  tabloyu ve türetilenleri de taşır ) ve kat_duzeni bilgisi."""
        elle = trafik(N="10", h="3", bodrum="0")
        kot = trafik(durak_kotlari=metin([i * 3000 for i in range(11)]))
        self.assertIsNone(elle.get("hata"))
        duzen = {"N": 10, "bodrum": 0, "h": 3.0, "durak": 11, "seyir": 30.0, "giris": 1, "alt": 1, "ust": 11}
        kd = kot.pop("kat_duzeni")
        self.assertEqual(kd.pop("asansorler"), [{"sira": 1, **duzen}])
        self.assertEqual(kd, duzen)
        #  Köprünün asansörleri hizmet aralığını da taşır ( "kat" ) — elle girişte yoktur
        for a in kot["avan_koprusu"]["asansorler"]:
            self.assertEqual((a.pop("kat")["alt"], a["toplam_seyahat"]), (1, 30.0))
        ge, gk = elle.pop("girdiler"), kot.pop("girdiler")
        self.assertEqual(gk.pop("kat_duzeni")["N"], 10)
        self.assertEqual(gk.pop("durak_kotlari"), metin([i * 3000 for i in range(11)]))
        self.assertEqual(sayilar(gk), sayilar(ge))
        self.assertEqual(sayilar(kot), sayilar(elle))

    def test_tablo_elle_yazilanin_yerine_gecer(self):
        """Tablo doluyken elle yazılmış N / bodrum / h okunmaz — okunamayan eski bir yazım da
        hesabı durdurmaz."""
        r = trafik(durak_kotlari="-3,20; ±0,00; +4,50; +7,60; +10,70; +13,80", N="99", h="abc", bodrum="7")
        self.assertIsNone(r.get("hata"))
        o = r["ozet"]
        self.assertEqual((o["N"], o["bodrum"], o["durak"]), (4, 1, 6))
        self.assertAlmostEqual(o["toplam_seyahat"], 17.0, places=9)
        self.assertEqual(r["avan_koprusu"]["N"], 4)
        self.assertEqual(r["avan_koprusu"]["bodrum"], 1)

    def test_butun_asansorler_tablonun_tamamini_kullanir(self):
        """Kullanıcı kararı ( 16 Kas ):  tablo doluyken trafik sütununun kendi durak sayısı,
        kat yüksekliği ve bodrumu okunmaz — iki asansör de aynı seyahati yapar.  Tablo
        boşken sütunun kendi değeri bugünkü gibi geçerlidir."""
        iki = [dict(ASANSOR), dict(ASANSOR, durak="4", h="5", bodrum="2")]
        kot = "-3,20; ±0,00; +4,50; +7,60; +10,70; +13,80"
        r = json.loads(
            avan_uclari.api_trafik({"girdiler": {**BINA, "asansorler": iki, "durak_kotlari": kot}}).body
        )
        self.assertIsNone(r.get("hata"), r.get("hata"))
        seyahat = [a["toplam_seyahat"] for a in r["avan_koprusu"]["asansorler"]]
        self.assertEqual(len(seyahat), 2)
        for s in seyahat:
            self.assertAlmostEqual(s, 17.0, places=9)
        elle = json.loads(
            avan_uclari.api_trafik({"girdiler": {**BINA, "N": "5", "h": "3", "asansorler": iki}}).body
        )
        self.assertIsNone(elle.get("hata"), elle.get("hata"))
        e = [a["toplam_seyahat"] for a in elle["avan_koprusu"]["asansorler"]]
        self.assertNotEqual(e[0], e[1])

    def test_okunamayan_tablo_hesabi_durdurur(self):
        r = trafik(durak_kotlari="±0,00; +3,00; +2,00", N="10", h="3")
        self.assertIn("Durak kotları", r["hata"])
        self.assertIn("artan sırayla", r["hata"])
        r = trafik(durak_kotlari="-3,00; ±0,00", N="10", h="3")
        self.assertIn("Giriş katı en üst durak", r["hata"])

    def test_bodrum_siniri_motorun_iletisiyle(self):
        """11 bodrum durağı:  motorun kendi sınırı ( tablolar.BODRUM_AZAMI ) söyler."""
        kotlar = [i * 3000 for i in range(-11, 4)]
        r = trafik(durak_kotlari=metin(kotlar))
        self.assertIn("bodrum durak adedi", r["hata"])


class Degismez(unittest.TestCase):
    """RASTGELE KOT TABLOLARI:  trafik, avan hesabı ve kotlar aynı binayı hesaplar."""

    def tablolar(self, adet, tohum=20261116):
        r = random.Random(tohum)
        for _ in range(adet):
            n = r.randint(2, 24)
            giris = r.randint(0, min(n - 2, 6))  # sıra ( 0'dan ):  en üst olamaz, bodrum ≤ 6
            esit = r.random() < 0.3
            h0 = r.randrange(2600, 4501, 10)
            araliklar = [h0 if esit else r.randrange(2600, 5001, 10) for _ in range(n - 1)]
            #  Giriş katının kotu ±0,00 olmak zorunda değil ( −0,90 … +1,50 )
            giris_kotu = r.choice((0, 0, r.randrange(-900, 1501, 10)))
            kotlar = [0]
            for a in araliklar:
                kotlar.append(kotlar[-1] + a)
            kotlar = [k - kotlar[giris] + giris_kotu for k in kotlar]
            yield kotlar, giris

    def test_trafigin_seyahati_kotlarin_seyri(self):
        """300 tablo:  ( N + bodrum ) · h = en üst − en alt;  N + bodrum + 1 = durak."""
        for kotlar, giris in self.tablolar(300):
            with self.subTest(kotlar=metin(kotlar), giris=giris + 1):
                r = trafik(durak_kotlari=metin(kotlar), giris_duragi=str(giris + 1))
                self.assertIsNone(r.get("hata"), r.get("hata"))
                o = r["ozet"]
                seyir = (kotlar[-1] - kotlar[0]) / 1000.0
                self.assertEqual((o["N"], o["bodrum"]), (len(kotlar) - 1 - giris, giris))
                self.assertEqual(o["durak"], len(kotlar))
                self.assertAlmostEqual(o["toplam_seyahat"], seyir, places=9)
                self.assertAlmostEqual((o["N"] + o["bodrum"]) * o["h"], seyir, places=9)

    def test_avan_ayni_binayi_hesaplar(self):
        """60 tablo, trafik → avan:  avanın kotlardan türettiği seyir ve durak trafiğinkiyle
        aynı, kuyu yüksekliği kotlardan ve avan "kat düzeni tutmuyor" demiyor."""
        for kotlar, giris in self.tablolar(60, tohum=7):
            with self.subTest(kotlar=metin(kotlar), giris=giris + 1):
                kot = {"durak_kotlari": metin(kotlar), "giris_duragi": str(giris + 1)}
                t = trafik(**kot)
                self.assertIsNone(t.get("hata"), t.get("hata"))
                dip, tavan = kotlar[0] - 1800, kotlar[-1] + 4600
                kart = {
                    **kot,
                    "kuyu_dibi_kotu": katlar.kot_metni(dip),
                    "kuyu_tavani_kotu": katlar.kot_metni(tavan),
                }
                a = avan(kart, t["avan_koprusu"])
                self.assertIsNone(a.get("hata"), a.get("hata"))
                k = a["kotlar"][0]
                self.assertFalse(k.get("hata"), k.get("hata"))
                self.assertEqual(k["durak"], t["ozet"]["durak"])
                self.assertAlmostEqual(k["seyir"], t["ozet"]["toplam_seyahat"], places=9)
                self.assertAlmostEqual(a["ozet"]["asansorler"][0]["Hk"], (tavan - dip) / 1000.0, places=9)
                self.assertEqual([u for u in a["uyarilar"] if "kat düzeni" in u or "trafik hesabı" in u], [])


_KOT = re.compile(r"^[+\-−±]\d+,\d\d$")


class CizimAyniTablo(unittest.TestCase):
    """TABLO → TRAFİK → AVAN → ÇİZİM:  aynı kotlar.  Hazır 630 kg asansörünün kuyusu ( kuyu dibi
    1,60 · son kat 4,20 ) tablonun altına ve üstüne eklenir;  katlar eşitsiz, giriş katı en
    alt durak olmayabilir."""

    TABLOLAR = (
        ([0, 3200, 6100, 9400, 12300, 15000], None),
        ([-3100, 0, 3200, 6100, 9400, 12300], None),  # bodrumlu:  giriş ±0,00 ( kuraldan 2. durak )
        ([500, 3400, 6500, 9300, 12600, 15500, 18400], "1"),  # giriş katı +0,50 ( girildi )
    )

    def kartlar(self, kotlar, giris, adet=1):
        kot = {"durak_kotlari": metin(kotlar)}
        if giris:
            kot["giris_duragi"] = giris
        kuyu = {
            "kuyu_dibi_kotu": katlar.kot_metni(kotlar[0] - 1600),
            "kuyu_tavani_kotu": katlar.kot_metni(kotlar[-1] + 4200),
        }
        return kot, [cizim_karti(T630, **kot, **kuyu, eta="0,85") for _ in range(adet)]

    def kesit_kotlari(self, kartlar, i):
        """i. asansörün iki düşey kesitinde yazan kotlar:  { çizim : { kot yazısı } }."""
        g = {"girdiler": {"ortak": {"mk_yok": True}, "asansorler": kartlar, "sabitler": {}}, "asansor": i}
        r = json.loads(avan_cizim_uclari.api_avan_cizimler(g).body)
        self.assertEqual(r["durum"], "uygun", r)
        out = {}
        for c in r["cizim"]["cizimler"]:
            if c["ad"] in ("kuyu_kesiti_yan", "kuyu_kesiti_on"):
                yazilar = (
                    re.sub(r"<[^>]+>", "", t).strip()
                    for t in re.findall(r"<text[^>]*>(.*?)</text>", c["svg"], flags=re.S)
                )
                out[c["ad"]] = {y for y in yazilar if _KOT.match(y)}
        self.assertEqual(set(out), {"kuyu_kesiti_yan", "kuyu_kesiti_on"})
        return out

    def test_kesitlerin_durak_kotlari_tablonun(self):
        """Üç tablo:  trafiğin seyahati = avanın seyri = tablonun en üst − en alt kotu ve iki düşey
        kesitte yazan kotlar tam olarak tablonun kotları ( + kuyu dibi )."""
        for kotlar, giris in self.TABLOLAR:
            with self.subTest(kotlar=metin(kotlar), giris=giris):
                kot, kartlar = self.kartlar(kotlar, giris)
                seyir = (kotlar[-1] - kotlar[0]) / 1000.0
                t = trafik(**kot)
                self.assertIsNone(t.get("hata"), t.get("hata"))
                self.assertAlmostEqual(t["ozet"]["toplam_seyahat"], seyir, places=9)
                a = avan(kartlar[0], t["avan_koprusu"])
                self.assertIsNone(a.get("hata"), a.get("hata"))
                self.assertAlmostEqual(a["kotlar"][0]["seyir"], seyir, places=9)
                self.assertEqual(a["kotlar"][0]["durak"], t["ozet"]["durak"])
                beklenen = {katlar.kot_metni(k) for k in kotlar} | {katlar.kot_metni(kotlar[0] - 1600)}
                for ad, yazilan in self.kesit_kotlari(kartlar, 0).items():
                    self.assertEqual(yazilan, beklenen, ad)

    def test_butun_asansorlerin_kesitleri_ayni_tablo(self):
        """İki asansör ( kartlarında aynı tablo ):  ekranda her birinin kesitleri ve PAKETTEKİ
        ( "Projeyi indir" ) düşey kesitleri tablonun kotlarını yazar."""
        kotlar, giris = self.TABLOLAR[1]
        _kot, kartlar = self.kartlar(kotlar, giris, adet=2)
        beklenen = {katlar.kot_metni(k) for k in kotlar}
        for i in (0, 1):
            for ad, yazilan in self.kesit_kotlari(kartlar, i).items():
                self.assertTrue(beklenen <= yazilan, (i, ad, beklenen - yazilan))
        yanit = avan_uclari.indir_proje_dwg(
            {
                "kapak": {"project_title": "Kot tablosu"},
                "girdiler": {
                    "avan": {
                        "ortak": {"mk_yok": True, "temel_a": "20", "temel_b": "15"},
                        "asansorler": [
                            {"kabin_boyu": "1400", "kabin_genisligi": "1100", **k} for k in kartlar
                        ],
                        "sabitler": {},
                    }
                },
            }
        )
        self.assertEqual(yanit.media_type, "application/zip", getattr(yanit, "body", b"")[:400])
        self.assertNotIn("CIZIM", (yanit.headers.get("X-Avan-Not") or "").split(","))
        z = zipfile.ZipFile(io.BytesIO(yanit.body))
        d = ezdxf.read(
            io.StringIO(z.read(next(n for n in z.namelist() if n.endswith(".dxf"))).decode("utf-8", "ignore"))
        )
        for i in (1, 2):
            for kesit in ("YAN", "ON"):
                blok = d.blocks.get(f"CIZIM_KUYU_KESITI_{kesit}_{i}")
                self.assertIsNotNone(blok, [b.name for b in d.blocks if b.name.startswith("CIZIM_KUYU")])
                yazilan = {t.plain_text().strip() for t in blok.query("MTEXT TEXT")}
                self.assertTrue(beklenen <= yazilan, (i, kesit, beklenen - yazilan))


def dilim(kotlar, giris, alt, ust):
    """Asansörün kartına giden kotlar — tablonun [ alt … ust ] aralığı ( sıralar 1'den;
    giriş aralığın içindeki sırasına kayar ).  Ön yüzün dilimi ( lib/kotlar ) bunun eşidir."""
    return {"durak_kotlari": metin(kotlar[alt - 1 : ust]), "giris_duragi": str(giris - alt + 1)}


class HizmetAraligi(unittest.TestCase):
    """HER ASANSÖR TABLONUN BİR ARALIĞINA HİZMET EDER ( 17 Kas — kullanıcı:  "biri −1'e iniyor
    biri inmiyor senaryosunu da yapabilmemiz lazım" ).  Aralık trafik sütunundadır ( alt_durak ·
    ust_durak — tablodaki sıra );  asansörün bodrumu, durak sayısı, kat yüksekliği ve seyahati
    aralığından, kartına da tablonun o dilimi gider."""

    KOT = "-3,20; ±0,00; +4,50; +7,60; +10,70; +13,80"

    def iki(self, **ikinci):
        g = {**BINA, "asansorler": [dict(ASANSOR), dict(ASANSOR, **ikinci)], "durak_kotlari": self.KOT}
        return json.loads(avan_uclari.api_trafik({"girdiler": g}).body)

    def test_kural(self):
        d, ileti = katlar.kat_duzeni(self.KOT, None, 2, None)
        self.assertEqual(ileti, [])
        self.assertEqual(
            (d["N"], d["bodrum"], d["durak"], d["giris"], d["alt"], d["ust"]), (4, 0, 5, 2, 2, 6)
        )
        self.assertAlmostEqual(d["seyir"], 13.8, places=12)
        self.assertAlmostEqual((d["N"] + d["bodrum"]) * d["h"], d["seyir"], places=12)
        d, _ = katlar.kat_duzeni(self.KOT, None, None, 4)
        self.assertEqual((d["N"], d["bodrum"], d["durak"]), (2, 1, 4))
        self.assertAlmostEqual(d["seyir"], 10.8, places=12)
        for alt, ust, beklenen in (
            (3, None, "asansör ana girişe hizmet etmelidir"),
            (None, 2, "Giriş katı en üst durak"),
            (0, None, "en alt durak 0. durak olamaz"),
            (None, 7, "en üst durak 7. durak olamaz"),
        ):
            with self.subTest(alt=alt, ust=ust):
                d, ileti = katlar.kat_duzeni(self.KOT, None, alt, ust)
                self.assertIsNone(d)
                self.assertIn(beklenen, ileti[0])

    def test_biri_bodruma_inmez(self):
        r = self.iki(alt_durak="2")
        self.assertIsNone(r.get("hata"), r.get("hata"))
        #  Ortak düzen aralıkların zarfı ( tablonun tamamı );  asansörler kendi aralığıyla
        self.assertEqual((r["ozet"]["N"], r["ozet"]["bodrum"]), (4, 1))
        a, b = r["avan_koprusu"]["asansorler"]
        self.assertEqual((a["N"], a["bodrum"], a["kat"]["alt"], a["kat"]["durak"]), (4, 1, 1, 6))
        self.assertEqual((b["N"], b["bodrum"], b["kat"]["alt"], b["kat"]["durak"]), (4, 0, 2, 5))
        self.assertAlmostEqual(a["toplam_seyahat"], 17.0, places=9)
        self.assertAlmostEqual(b["toplam_seyahat"], 13.8, places=9)
        #  Kapak her asansörün durağını bodrum dahil yazar ( 18 Kas:  "5" yazıyordu — sütunun
        #  "durak"ı ana giriş ve üstü;  seyahat doğruydu )
        self.assertEqual(r["kapak_bilgileri"]["stops"], "6 / 5")
        self.assertEqual(r["kapak_bilgileri"]["travel"], "17,00 / 13,80 m")

    def test_alcak_blok(self):
        """Üst sınır:  ikinci asansör 4. durağa kadar ( 2 kat + ana giriş + bodrum )."""
        r = self.iki(ust_durak="4")
        self.assertIsNone(r.get("hata"), r.get("hata"))
        b = r["avan_koprusu"]["asansorler"][1]
        self.assertEqual((b["N"], b["bodrum"], b["kat"]["ust"]), (2, 1, 4))
        self.assertAlmostEqual(b["toplam_seyahat"], 10.8, places=9)

    def test_tek_tipte_ortak_duzen_araliktan(self):
        """Tek sütun:  ortak N / bodrum / h o asansörün aralığından ( tek yol sütunun kendi
        durak sayısını N + 1 ister );  gereken adet kadar asansörün hepsi aynı aralıkta."""
        g = {**BINA, "asansorler": [dict(ASANSOR, alt_durak="2")], "durak_kotlari": self.KOT}
        r = json.loads(avan_uclari.api_trafik({"girdiler": g}).body)
        self.assertIsNone(r.get("hata"), r.get("hata"))
        self.assertEqual((r["ozet"]["N"], r["ozet"]["bodrum"], r["ozet"]["durak"]), (4, 0, 5))
        for a in r["avan_koprusu"]["asansorler"]:
            self.assertEqual((a["kat"]["alt"], a["kat"]["ust"]), (2, 6))
            self.assertAlmostEqual(a["toplam_seyahat"], 13.8, places=9)

    def test_aralik_tablosuz_okunmaz_bozuksa_soylenir(self):
        g = {**BINA, "N": "5", "h": "3", "asansorler": [dict(ASANSOR, alt_durak="2", ust_durak="4")]}
        r = json.loads(avan_uclari.api_trafik({"girdiler": g}).body)
        self.assertIsNone(r.get("hata"), r.get("hata"))
        self.assertEqual(r["ozet"]["N"], 5)
        self.assertIn("asansör ana girişe hizmet etmelidir", self.iki(alt_durak="3")["hata"])
        self.assertIn("durağın sırası yazılır", self.iki(alt_durak="iki")["hata"])

    def araliklar(self, adet, tohum):
        """( kotlar , giriş sırası 1'den , [ ( alt , ust ) ] ) — iki asansör;  en az biri en üste çıkar."""
        r = random.Random(tohum)
        for kotlar, g0 in Degismez().tablolar(adet, tohum=tohum):
            n, g = len(kotlar), g0 + 1
            tam = (1, n)
            kisa = (r.randint(1, g), r.randint(g + 1, n))
            yield kotlar, g, r.choice(([tam, kisa], [kisa, tam], [tam, tam]))

    def test_her_asansorun_seyahati_araliginin_seyri(self):
        """150 tablo × iki asansör:  her asansörün trafikteki seyahati ve durak sayısı kendi
        aralığınınki;  ortak kat sayısı en yükseğe çıkanınki."""
        for kotlar, g, ar in self.araliklar(150, 20261117):
            with self.subTest(kotlar=metin(kotlar), giris=g, araliklar=ar):
                asl = [dict(ASANSOR, alt_durak=str(a), ust_durak=str(u)) for a, u in ar]
                gi = {**BINA, "asansorler": asl, "durak_kotlari": metin(kotlar), "giris_duragi": str(g)}
                r = json.loads(avan_uclari.api_trafik({"girdiler": gi}).body)
                self.assertIsNone(r.get("hata"), r.get("hata"))
                self.assertEqual(r["ozet"]["N"], max(u for _a, u in ar) - g)
                kopru = r["avan_koprusu"]["asansorler"]
                if r["tip"] == "coklu":
                    self.assertEqual(len(kopru), 2)
                for t in kopru:
                    a, u = t["kat"]["alt"], t["kat"]["ust"]
                    self.assertIn((a, u), ar)
                    self.assertAlmostEqual(
                        t["toplam_seyahat"], (kotlar[u - 1] - kotlar[a - 1]) / 1000.0, places=9
                    )
                    self.assertEqual(t["kat"]["durak"], u - a + 1)
                    if r["tip"] == "coklu":
                        self.assertEqual((t["N"], t["bodrum"]), (u - g, g - a))

    def test_avan_her_asansoru_kendi_dilimiyle(self):
        """40 tablo, trafik → avan:  kartlara tablonun dilimi gider;  avanın durak sayısı ve seyri
        her asansörde trafiğinkiyle aynı, "kat düzeni tutmuyor" uyarısı yok."""
        for kotlar, g, ar in self.araliklar(40, 11):
            with self.subTest(kotlar=metin(kotlar), giris=g, araliklar=ar):
                asl = [dict(ASANSOR, alt_durak=str(a), ust_durak=str(u)) for a, u in ar]
                gi = {**BINA, "asansorler": asl, "durak_kotlari": metin(kotlar), "giris_duragi": str(g)}
                t = json.loads(avan_uclari.api_trafik({"girdiler": gi}).body)
                self.assertIsNone(t.get("hata"), t.get("hata"))
                kopru = t["avan_koprusu"]
                kartlar = []
                for k in kopru["asansorler"]:
                    a, u = k["kat"]["alt"], k["kat"]["ust"]
                    kartlar.append(
                        {
                            **KART,
                            "kapasite": str(k["P"]),
                            "V": str(k["V"]),
                            **dilim(kotlar, g, a, u),
                            "kuyu_dibi_kotu": katlar.kot_metni(kotlar[a - 1] - 1800),
                            "kuyu_tavani_kotu": katlar.kot_metni(kotlar[u - 1] + 4600),
                        }
                    )
                gv = {"ortak": {"mk_yok": True}, "asansorler": kartlar, "sabitler": {}, "trafik": kopru}
                av = json.loads(avan_uclari.api_avan({"girdiler": gv}).body)
                self.assertIsNone(av.get("hata"), av.get("hata"))
                for i, k in enumerate(kopru["asansorler"]):
                    kot = av["kotlar"][i]
                    self.assertFalse(kot.get("hata"), kot.get("hata"))
                    self.assertEqual(kot["durak"], k["kat"]["durak"])
                    self.assertAlmostEqual(kot["seyir"], k["toplam_seyahat"], places=9)
                self.assertEqual([u for u in av["uyarilar"] if "kat düzeni" in u], [])

    def test_bodruma_inmeyen_asansorun_kesiti(self):
        """Çizim:  bodruma inen asansörün kesitinde bodrum kotu var, inmeyeninkinde yok —
        her biri kendi diliminin kotlarını ve kendi kuyu dibini yazar."""
        kotlar = [-3100, 0, 3200, 6100, 9400, 12300]
        ciz = CizimAyniTablo()
        kartlar = []
        for alt in (1, 2):
            d = dilim(kotlar, 2, alt, 6)
            kuyu = {
                "kuyu_dibi_kotu": katlar.kot_metni(kotlar[alt - 1] - 1600),
                "kuyu_tavani_kotu": katlar.kot_metni(kotlar[-1] + 4200),
            }
            kartlar.append(cizim_karti(T630, **d, **kuyu, eta="0,85"))
        for i, alt in enumerate((1, 2)):
            beklenen = {katlar.kot_metni(k) for k in kotlar[alt - 1 :]} | {
                katlar.kot_metni(kotlar[alt - 1] - 1600)
            }
            for ad, yazilan in ciz.kesit_kotlari(kartlar, i).items():
                self.assertEqual(yazilan, beklenen, (i, ad))


if __name__ == "__main__":
    unittest.main()

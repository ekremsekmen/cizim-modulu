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
        duzen = {"N": 10, "bodrum": 0, "h": 3.0, "durak": 11, "seyir": 30.0, "giris": 1}
        self.assertEqual(kot.pop("kat_duzeni"), duzen)
        ge, gk = elle.pop("girdiler"), kot.pop("girdiler")
        self.assertEqual(gk.pop("kat_duzeni"), duzen)
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


if __name__ == "__main__":
    unittest.main()

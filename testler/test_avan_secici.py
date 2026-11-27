"""AVAN SEÇİCİSİ ( uclar/avan_secici — 12 Kas, kullanıcı:  "avan projesine de çizim;  elde
yalnız mimari var, buraya en doğru asansör" ).  Sözleşmesi:

  · "uygun" dönen istek uygulamanın kendi uçlarından TEMİZ çıkar ( çizim sorunsuz;  hesabın
    düşen bölümü varsa yalnız seçicinin "acik_bolumler"de söylediği ÜRÜN bölümleri — avanı
    bağlayan bölümler hep uygun ) — seçicinin kendi sınamasına güvenilmez, ayrı yoldan sorulur.
  · Mimarın verdikleri ( kuyu, kotlar, yük, hız ) istekte AYNEN durur;  kabin kartınkidir ( standarda
    uyuyorsa — 24 Kas ), kartta yoksa paketinki.
  · Sığmayan kuyuda asansör dönmez:  ya mimardan istenecek ölçü ( o ölçüyle temiz ) ya da sebep.
"""

import asyncio
import contextlib
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

from cizim import katlar, kopru
from uclar import avan_cizim_uclari, avan_secici, avan_uclari, care_uclari, cizim_uclari, uygulama_uclari
from yollar import KOK

PAKETLER = avan_secici.paketler()
KABIN = ("beyan_yuku", "kabin_genisligi", "kabin_derinligi", "kapi_genisligi")


def mimari(t, **degisen):
    """Taslağın kendi kuyusu ve kotları, mimarın vereceği biçimde."""
    a, pg = t["asansor"], t["proje_geneli"]
    m = {k: a[k] for k in ("beyan_yuku", "beyan_hizi", *avan_secici.MIMARI) if k in a}
    m["mk_yok"] = pg.get("mk_yok") == "true"
    m.update({k: pg[k] for k in avan_secici.MIMARI_GENEL if k in pg})
    m.update(degisen)
    return m


def kot(metin, ek_mm):
    mm, hata = katlar.kot_oku(metin)
    assert hata is None, hata
    return katlar.kot_metni(mm + ek_mm)


@contextlib.contextmanager
def yavas_saat(adim=30.0):
    """Yavaş, yüklü bilgisayar:  seçicinin her sınaması saati adim sn ilerletir."""
    saat = [0.0]
    asil = care_uclari.girdi_durumu

    def yavas(v, i):
        saat[0] += adim
        return asil(v, i)

    sahte = mock.Mock(time=lambda: saat[0], monotonic=lambda: saat[0])
    with mock.patch.object(care_uclari, "girdi_durumu", yavas), mock.patch.object(avan_secici, "time", sahte):
        yield saat


class AvanSecici(unittest.TestCase):
    def temiz(self, r):
        """Uygulamanın uçlarından:  çizim sorunsuz;  hesabın düşen bölümleri seçicinin
        söyledikleri ( acik_bolumler ), onlar da avanı bağlamayan ürün bölümleri."""
        v = r["istek"]
        h = json.loads(uygulama_uclari.api_uygulama_coklu(copy.deepcopy(v)).body)
        self.assertTrue(h["aktif"], h.get("hata"))
        dusen = sorted(
            b["kimlik"]
            for b in h["asansorler"][0]["bolumler"]
            if (b.get("sonuc") or {}).get("uygun") is False
        )
        self.assertEqual(dusen, r["acik_bolumler"])
        self.assertFalse(set(dusen) & avan_secici.AVAN_BOLUMLERI)
        if not dusen:
            self.assertEqual(h["proje_hukmu"]["durum"], "uygun", h["proje_hukmu"])
        c = json.loads(cizim_uclari.api_cizimler(copy.deepcopy(v)).body)
        self.assertTrue(c["aktif"], c.get("hata"))
        self.assertFalse(c.get("hata"))

    def mimari_aynen(self, m, v):
        a = {**v["proje_geneli"], **v["asansorler"][0]}
        for k in ("beyan_yuku", "beyan_hizi", *avan_secici.MIMARI, *avan_secici.MIMARI_GENEL):
            if k in m:
                self.assertEqual(a[k], avan_secici._metin(m[k]), k)

    def test_paketin_kendi_kuyusu(self):
        """Her yük, makine dairesiz ve daireli:  taslağın kuyusunda taslağın kendisi."""
        #  Açılışın taslakları ( yalnız avanın hazır asansörleri:  testler/test_avan_paketleri )
        taslaklar = [t for t in PAKETLER.values() if "acik_bolumler" not in t]
        self.assertEqual(len(taslaklar), 10)
        for t in taslaklar:
            with self.subTest(t["kimlik"]):
                m = mimari(t)
                r = avan_secici.sec(m)
                self.assertEqual(r["durum"], "uygun", r)
                self.assertEqual(r["paket"], t["kimlik"])
                self.assertEqual(r["acik_bolumler"], [])
                #  "uygun"da denenen yerleşim söylenmez ( yalnız "gereken" / "sigmaz" )
                self.assertNotIn("denenen", r)
                self.assertNotIn("yerlesim", r)
                self.mimari_aynen(m, r["istek"])
                a = r["istek"]["asansorler"][0]
                self.assertEqual({k: a[k] for k in KABIN}, {k: t["asansor"][k] for k in KABIN})
                #  Kendi kuyusunda ağırlık paketin yerinde ( yanda ):  arka sığmaz
                self.assertEqual(a["agirlik_yeri"], t["asansor"]["agirlik_yeri"])
                #  Kendi kuyusunda ürün araması yok:  tek sınamada bulunur — makine daireli 1:1'de
                #  önce arka denenir ( 13 Kas ), o da bir sınama
                once_arka = avan_secici._once_arka(t, m)
                self.assertEqual(once_arka, t["kimlik"] in ("630-md", "800-md", "1000-md"))
                self.assertEqual(r["sinama"], 2 if once_arka else 1)

    def test_genis_kuyu(self):
        """12 Kas ölçümü:  paket 100 mm geniş kuyuda bile düşüyordu ( makine dairesizde halat
        sapması, korkuluk ).  Kabin ağırlığın yanına kayar, kabin büyümez."""
        for anahtar in ((630, True), (1000, True), (1275, True), (800, False), (1250, False)):
            t = PAKETLER[anahtar]
            with self.subTest(t["kimlik"]):
                gen = int(t["asansor"]["kuyu_genisligi"]) + 300
                ek = {"mk_genislik": int(t["proje_geneli"]["mk_genislik"]) + 300} if not anahtar[1] else {}
                #  Geniş kuyuda kabinin öbür yanı açılır ( > 0,30 m ):  korkuluk, kuyu üstü + 0,40
                m = mimari(
                    t, kuyu_genisligi=gen, kuyu_tavani_kotu=kot(t["asansor"]["kuyu_tavani_kotu"], 400), **ek
                )
                if not anahtar[1]:
                    m["md_zemini_kotu"] = kot(t["asansor"]["md_zemini_kotu"], 400)
                r = avan_secici.sec(m)
                self.assertEqual(r["durum"], "uygun", r)
                self.mimari_aynen(m, r["istek"])
                a = r["istek"]["asansorler"][0]
                self.assertEqual({k: a[k] for k in KABIN}, {k: t["asansor"][k] for k in KABIN})
                self.temiz(r)

    def test_kuyu_ustu_yetmiyorsa_mimardan_istenir(self):
        """Geniş kuyuda korkuluk gerekir, kuyu üstü yetmez:  asansör "uygun" dönmez;
        mimardan istenecek kuyu tavanı kotu döner ve o kotla temizdir.  Kuyu üstü taslağınkinden
        500 kısa ( 24 Kas:  korkuluğun dışındaki parçaya 0,10 m açıklık — taslağın kuyu üstü
        geniş kuyuda da artık yetiyor;  eskiden +19,38 istenirdi.  25 Kas:  küpeşte tavana asılı
        parçalardan da içeri alınınca 200 kısası da kurulur — 400 kısası kurulur, 500 kısası değil ).

        İSTENEN KOT EN KÜÇÜĞÜNE İNER ( 24 Kas ):  çare bulucunun türevi sorunu o an bağlayan parçaya
        göre fazla istiyordu ( +19,37 — +19,18 yetiyordu );  seçici kotu da ikili aramayla en küçük
        yeterli değere indirir.  400 kısası kurulduğu için istenen kot taslağınkinin en az 400
        altındadır."""
        t = PAKETLER[(630, True)]
        genis = int(t["asansor"]["kuyu_genisligi"]) + 300
        taslagin, _h = katlar.kot_oku(t["asansor"]["kuyu_tavani_kotu"])
        #  Önkoşul:  taslağın 400 kısası bu kuyuda yetiyor
        self.assertEqual(
            avan_secici.sec(
                mimari(t, kuyu_genisligi=genis, kuyu_tavani_kotu=kot(t["asansor"]["kuyu_tavani_kotu"], -400))
            )["durum"],
            "uygun",
        )
        for kisa in (500,):
            m = mimari(t, kuyu_genisligi=genis, kuyu_tavani_kotu=kot(t["asansor"]["kuyu_tavani_kotu"], -kisa))
            r = avan_secici.sec(m)
            self.assertEqual(r["durum"], "gereken", r)
            self.assertEqual([g["anahtar"] for g in r["gereken"]], ["kuyu_tavani_kotu"])
            (g,) = r["gereken"]
            self.assertEqual(g["eski"], m["kuyu_tavani_kotu"])
            eski, _h = katlar.kot_oku(g["eski"])
            yeni, hata = katlar.kot_oku(g["yeni"])
            self.assertIsNone(hata)
            self.assertGreater(yeni, eski)
            self.assertLessEqual(yeni, taslagin - 400, (kisa, g))
            self.assertTrue(g["sebep"])
            #  İstenen kotla seçici "uygun" der
            r2 = avan_secici.sec({**m, "kuyu_tavani_kotu": g["yeni"]})
            self.assertEqual(r2["durum"], "uygun", r2)
            self.temiz(r2)

    def test_kuyu_dibi_yetmiyorsa_en_kucugu_istenir(self):
        """Kuyu dibi kotu da küçültülür ( 24 Kas ):  taslağın kuyusunda kuyu dibi 800 sığ ( sığınma
        yüksekliği yetmez ) — çare bulucunun türevi kuyu dibini fazla derin istiyordu.  Küçültme
        aşağı doğrudur ( mimarınkinden önerilene ):  istenen kot mimarınkinden derin, çare
        bulucununkinden ( küçültmesiz seçim ) sığ, taslağınkinden derin değil;  onunla seçici "uygun" der."""
        t = PAKETLER[(630, True)]
        m = mimari(t, kuyu_dibi_kotu=kot(t["asansor"]["kuyu_dibi_kotu"], 800))

        def istenen(r):
            self.assertEqual(r["durum"], "gereken", r)
            self.assertEqual([g["anahtar"] for g in r["gereken"]], ["kuyu_dibi_kotu"])
            return katlar.kot_oku(r["gereken"][0]["yeni"])[0]

        with mock.patch.object(avan_secici, "_kucult", lambda v, d, gereken, *_a, **_k: (v, d, gereken)):
            ham = istenen(avan_secici.sec(m))
        r = avan_secici.sec(m)
        yeni = istenen(r)
        self.assertEqual(r["gereken"][0]["eski"], m["kuyu_dibi_kotu"])
        self.assertLess(yeni, katlar.kot_oku(m["kuyu_dibi_kotu"])[0])
        self.assertGreater(yeni, ham)
        self.assertGreaterEqual(yeni, katlar.kot_oku(t["asansor"]["kuyu_dibi_kotu"])[0])
        r2 = avan_secici.sec({**m, "kuyu_dibi_kotu": r["gereken"][0]["yeni"]})
        self.assertEqual(r2["durum"], "uygun", r2)
        self.temiz(r2)

    def test_hiz_degisince_urun_degisir(self):
        """1,6 m/s, 10 durak:  enerji biriktirmeli tampon olmaz ( m.5.8.1.5 ), motor büyür."""
        t = PAKETLER[(630, True)]
        n, h = 10, 2900
        son = (n - 1) * h
        m = mimari(
            t,
            beyan_hizi=1.6,
            durak_kotlari="; ".join(katlar.kot_metni(j * h) for j in range(n)),
            kuyu_dibi_kotu=katlar.kot_metni(-1800),
            kuyu_tavani_kotu=katlar.kot_metni(son + 4600),
        )
        r = avan_secici.sec(m)
        self.assertEqual(r["durum"], "uygun", r)
        self.assertIn("Hidrolik", r["secimler"]["tampon_tipi"])
        self.assertGreater(float(r["secimler"]["motor_gucu"]), float(t["asansor"]["motor_gucu"]))
        self.assertEqual(r["acik_bolumler"], [])
        self.temiz(r)

    def test_urun_bolumu_avani_engellemez(self):
        """Kullanıcı ( 12 Kas ):  "tahrikle alakalı bir işimiz yok ki, avan projesi bu".
        1250 kg 1,6 m/s'de tahrik yeteneği hiçbir seçimle geçmiyor ( acil frenleme );  asansör
        yine çizilir, geçmeyen bölüm söylenir.  Avanı bağlayan bölüm ise hep engeldir."""
        t = PAKETLER[(1250, True)]
        n, h = 10, 2900
        son = (n - 1) * h
        m = mimari(
            t,
            beyan_hizi=1.6,
            durak_kotlari="; ".join(katlar.kot_metni(j * h) for j in range(n)),
            kuyu_dibi_kotu=katlar.kot_metni(-1800),
            kuyu_tavani_kotu=katlar.kot_metni(son + 4600),
        )
        r = avan_secici.sec(m)
        self.assertEqual(r["durum"], "uygun", r)
        self.assertEqual(r["acik_bolumler"], ["tahrik_yetenegi"])
        self.temiz(r)

    def test_beyan_aynen_durur(self):
        """Avanın beyanı ( askı oranı, makine tipi ) verilmişse istekte aynen durur;  paketin
        ürünü ona göre aranır.  Beyanla kurulamayan, paketin askısıyla kurulabilen kuyuda
        asansör DÖNMEZ:  kartta değişecek değerler döner ( en az değişiklik, doğrulanmış )."""
        t = PAKETLER[(1275, False)]
        r = avan_secici.sec(mimari(t, aski_orani=1, makine_tipi="Dişlisiz"))
        self.assertEqual(r["durum"], "uygun", r)
        a = r["istek"]["asansorler"][0]
        self.assertEqual((a["aski_orani"], a["makine_tipi"]), ("1", "Dişlisiz"))
        self.temiz(r)
        #  Makine daireli 630 ( paket 1:1 dişli ):  2:1 dişlisiz beyanı da kurulur — ikinci
        #  yerleşim adayı askı kasnaklarını kabin üstüne alır ( 14 Kas;  13 Kas'ta kurulamıyordu )
        t = PAKETLER[(630, False)]
        r = avan_secici.sec(mimari(t, aski_orani=2, makine_tipi="Dişlisiz"))
        self.assertEqual(r["durum"], "uygun", r)
        a = r["istek"]["asansorler"][0]
        self.assertEqual(
            (a["aski_orani"], a["makine_tipi"], a["aski_duzeni"]), ("2", "Dişlisiz", "Kabin üstü")
        )
        self.temiz(r)
        #  Makine dairesizde 1:1 çizilmez ( programın kuralı ):  asansör DÖNMEZ, karta 2:1
        t = PAKETLER[(630, True)]
        m = mimari(t, aski_orani=1)
        r = avan_secici.sec(m)
        self.assertEqual(r["durum"], "beyan", r)
        self.assertNotIn("istek", r)
        self.assertEqual(
            [(b["anahtar"], b["eski"], b["yeni"]) for b in r["beyan"]], [("aski_orani", "1", "2")]
        )
        r = avan_secici.sec({**m, **{b["anahtar"]: b["yeni"] for b in r["beyan"]}})
        self.assertEqual(r["durum"], "uygun", r)
        self.temiz(r)

    def test_agirlik_sigmazsa_arkaya(self):
        """Kullanıcı ( 14 Kas ):  "önce yan, sığmazsa arka".  Paketin kuyusunda ağırlık yanda
        kalır ( test_paketin_kendi_kuyusu );  dar ve derin kuyuda yan yerleşim mimarın
        ölçüleriyle kurulamaz — ağırlık arkaya alınır, programın arka kurallarıyla ( 2:1 askı
        kabin üstünde, makine dairesizde makine bina yapısına oturur ).  Sonuç yine doğrulanmış."""
        t = PAKETLER[(630, True)]
        self.assertEqual(t["asansor"]["agirlik_yeri"], "Sağ")
        m = mimari(t, kuyu_genisligi=1650, kuyu_derinligi=2300)
        #  YAVAŞ BİLGİSAYARDA AYNI SONUÇ ( 16 Kas — bütçe sınama sayısıdır, saat değil ):  bu arama
        #  28 sınama, hızlı makinede ~22 sn.  Eski saat sınırında ( 24 sn ) yüklü CI makinesi 6.
        #  sınamada kesiyor, "sığmaz" diyordu ( PR #141 ).  Burada her sınama saati 30 sn ilerletir
        with yavas_saat():
            r = avan_secici.sec(m)
        self.assertEqual(r["durum"], "uygun", r)
        a = r["istek"]["asansorler"][0]
        self.assertEqual(
            (a["agirlik_yeri"], a["aski_duzeni"], a["makine_raya_biniyor"]),
            ("Arka", "Kabin üstü", "Bina yapısına"),
        )
        self.mimari_aynen(m, r["istek"])
        self.assertEqual({k: a[k] for k in KABIN}, {k: t["asansor"][k] for k in KABIN})
        self.temiz(r)
        #  Makine daireli 1:1:  askı kasnağı da makine kirişi de yok — yalnız ağırlığın yeri
        t = PAKETLER[(630, False)]
        r = avan_secici.sec(mimari(t, kuyu_genisligi=1700, kuyu_derinligi=2400))
        self.assertEqual(r["durum"], "uygun", r)
        a = r["istek"]["asansorler"][0]
        self.assertEqual(a["agirlik_yeri"], "Arka")
        self.assertNotIn("aski_duzeni", a)
        self.temiz(r)

    def test_agirlik_yerinin_sirasi(self):
        """Kullanıcı ( 13 Kas ):  "makine dairesiz 2:1 askılı asansörde ilk denenecek yanda ağırlık,
        makine daireli 1:1 askıda ilk denenecek arkada ağırlık".  İkisinin de sığdığı kuyuda
        ( paketinkinden 550 mm derin ) ilk denenen seçilir;  ikisi de doğrulanmıştır."""
        for anahtar, beklenen in (
            ((630, False), "Arka"),
            ((800, False), "Arka"),
            ((1000, False), "Arka"),
            ((630, True), "Sağ"),
            ((800, True), "Sağ"),
        ):
            t = PAKETLER[anahtar]
            with self.subTest(t["kimlik"]):
                m = mimari(t, kuyu_derinligi=int(t["asansor"]["kuyu_derinligi"]) + 550)
                r = avan_secici.sec(m)
                self.assertEqual(r["durum"], "uygun", r)
                self.assertEqual(r["istek"]["asansorler"][0]["agirlik_yeri"], beklenen)
                self.temiz(r)
        #  Makine daireli 2:1 ( 1250 / 1275 paketleri ) ve makine dairesiz 1:1:  önce yan
        self.assertFalse(avan_secici._once_arka(PAKETLER[(1250, False)], mimari(PAKETLER[(1250, False)])))
        t = PAKETLER[(630, True)]
        self.assertFalse(avan_secici._once_arka(t, mimari(t, aski_orani=1)))
        #  Makine daireli pakete avanın 2:1 beyanı:  önce yan
        t = PAKETLER[(630, False)]
        self.assertFalse(avan_secici._once_arka(t, mimari(t, aski_orani=2)))

    def test_kapi_beyani(self):
        """Trafik hesabının kapısı ( genişlik, tip ) beyandır:  istekte aynen durur;  çare
        kapının ailesini değiştirmez."""
        t = PAKETLER[(630, True)]
        self.assertEqual(
            (t["asansor"]["kapi_genisligi"], t["asansor"]["kat_kapisi_tipi"]), ("800", "Teleskopik Sol")
        )
        r = avan_secici.sec(mimari(t, kapi_genisligi=900, kat_kapisi_tipi="Otomatik Merkezi"))
        self.assertEqual(r["durum"], "uygun", r)
        a = r["istek"]["asansorler"][0]
        self.assertEqual((a["kapi_genisligi"], a["kat_kapisi_tipi"]), ("900", "Otomatik Merkezi"))
        self.temiz(r)
        self.assertEqual(
            [
                avan_secici.kapi_ailesi(x)
                for x in ("Teleskopik 3 Kanat Sağ", "Otomatik Merkezi 4 Kanat", "Manuel Sol")
            ],
            ["Teleskopik", "Otomatik Merkezi", "Manuel"],
        )

    def test_sigmayan_kuyu(self):
        """Kabinden dar kuyu:  asansör dönmez."""
        t = PAKETLER[(630, True)]
        r = avan_secici.sec(mimari(t, kuyu_genisligi=1200))
        self.assertIn(r["durum"], ("gereken", "sigmaz"), r)
        self.assertNotIn("istek", r if r["durum"] == "sigmaz" else {})
        if r["durum"] == "gereken":
            self.assertIn("kuyu_genisligi", [g["anahtar"] for g in r["gereken"]])
        else:
            self.assertTrue(r["nedenler"])

    def test_kullanilmayan_yerlesimin_sebebi(self):
        """27 Kas ( kullanıcı:  "merdivenin sığmama senaryosunu program açıkça söylüyor mu" ):
        800 kg makine dairesiz, 1350 × 1400 kabin, 900 kapı, kuyu 1800 × 2700, son kat 4300.
        Önce yan denenir ( 13 Kas ):  1980 genişlik ister.  Ağırlık arkada mimarın kuyusunda
        kuyu dibi merdivenine yer yok ( Ek F.5 b — kapının yanında 300 mm, merdiven 330 ).  Ekran
        eskiden yalnız 1980'i ve "kabin ve karşı ağırlığı sığmıyor"u söylüyordu;  arkadaki
        düzenin neden olmadığı görünmüyordu.  Şimdi sonuç yerleşimini ve denenenin sebebini taşır."""
        t = PAKETLER[(800, True)]
        kotlar = "; ".join(["-2,60"] + [kot("+0,70", 3000 * i) for i in range(9)])
        m = mimari(
            t,
            kuyu_genisligi=1800,
            kuyu_derinligi=2700,
            durak_kotlari=kotlar,
            kuyu_dibi_kotu="-4,70",
            kuyu_tavani_kotu="+29,00",
            kisi=10,
            kabin_genisligi=1350,
            kabin_derinligi=1400,
            kapi_genisligi=900,
        )
        r = avan_secici.sec(m)
        self.assertEqual(r["durum"], "gereken", r)
        #  27 Kas ( seçici doğruluk planı Adım 2 + 4 ):  çare bulucu merdivene kuyu genişliği önerir
        #  ( bina ölçüsü taraması ), iki yerleşim de küçültülüp karşılaştırılır — arka 1830, yan 1960
        #  seçenek ( küçültme sınırın altını da dener;  önce 1980 ).
        #  Arkanın mimarın 1800'ündeki sebebi ( merdiven ) yine söylenir.
        self.assertEqual(r["yerlesim"], "ağırlık arkada")
        self.assertEqual([(g["anahtar"], g["yeni"]) for g in r["gereken"]], [("kuyu_genisligi", 1830.0)])
        self.assertEqual(
            [(x["yerlesim"], [(g["anahtar"], g["yeni"]) for g in x["gereken"]]) for x in r["secenek"]],
            [("ağırlık yanda", [("kuyu_genisligi", 1960.0)])],
        )
        self.assertEqual([x["yerlesim"] for x in r["denenen"]], ["ağırlık yanda"])
        self.assertNotIn("_mimarda", r)
        #  Seçilen arka da mimarın 1800'ünde kurulmuyordu:  sebebi merdiven
        t2 = avan_secici.paketler()[(800, True)]
        v = avan_secici._istek(t2, m, avan_secici._arka_adayi(t2, m))
        nedenler = list(care_uclari.girdi_durumu(v, 0)[0].values())
        self.assertTrue(
            any(n.startswith("Kuyu dibi merdiveni") and "Ek F.5 b" in n for n in nedenler), nedenler
        )
        nedenler = r["denenen"][0]["nedenler"]
        #  Uç bölüm kimliğini ekrandaki adına çevirir ( "nedenler"deki gibi )
        with mock.patch.object(avan_cizim_uclari, "secim", return_value=copy.deepcopy(r)):
            y = avan_cizim_uclari.avan_cizimler_sonucu({})
        self.assertEqual(y["denenen"][0]["nedenler"][0], nedenler[0])
        self.assertFalse(
            any(n.startswith("bölüm:") for x in y["denenen"] for n in x["nedenler"]), y["denenen"]
        )

    def test_denenen_her_birlesimde(self):
        """Yerleşimlerin bütün sonuç birleşimleri ( _yerlesimler;  sahte yerlesim — hızlı ):  sonuç
        ilkinin "uygun"u → ikincisinin "uygun"u → ilkinin "gereken"i → ikincisinin "gereken"i → ilkinin
        "sığmaz"ı.  "uygun"da yerlesim / denenen yok;  öbürlerinde kullanılmayan yerleşim, mimarın
        ölçülerindeki sorunlarıyla."""

        def sahte(sonuclar):
            def yerlesim(adaylar, kucult=True):
                d = sonuclar[adaylar]
                if d == "uygun":
                    return "uygun", {"istek": adaylar}
                if d == "gereken":
                    g = {"anahtar": "kuyu_genisligi", "eski": "1800", "yeni": artis[adaylar] + 1800.0}
                    return "gereken", {"gereken": [g], "_mimarda": [f"{adaylar} sorunu"]}
                return "sigmaz", {"nedenler": [f"{adaylar} sorunu"]}

            return yerlesim

        #  İkisi de ölçü isterse eşit istekte sıradaki ilk ( K2 — c )
        artis = {"yan": 100.0, "arka": 100.0}
        sina = mock.Mock(kalan=0)
        sira = [("yanda", "yan"), ("arkada", "arka")]
        beklenen = {
            ("uygun", "uygun"): ("uygun", "yan", None),
            ("uygun", "gereken"): ("uygun", "yan", None),
            ("uygun", "sigmaz"): ("uygun", "yan", None),
            ("gereken", "uygun"): ("uygun", "arka", None),
            ("gereken", "gereken"): ("gereken", "yan", "arka"),
            ("gereken", "sigmaz"): ("gereken", "yan", "arka"),
            ("sigmaz", "uygun"): ("uygun", "arka", None),
            ("sigmaz", "gereken"): ("gereken", "arka", "yan"),
            ("sigmaz", "sigmaz"): ("sigmaz", "yan", "arka"),
        }
        ad = dict((x, a) for a, x in sira)
        for (yan, arka), (durum, kaynak, oteki) in beklenen.items():
            with self.subTest(yan=yan, arka=arka):
                d, al = avan_secici._yerlesimler(sira, sahte({"yan": yan, "arka": arka}), sina)
                self.assertEqual(d, durum)
                self.assertNotIn("_mimarda", al)
                if durum == "uygun":
                    self.assertEqual(al["istek"], kaynak)
                    self.assertNotIn("denenen", al)
                    self.assertNotIn("yerlesim", al)
                else:
                    self.assertEqual(al["yerlesim"], ad[kaynak])
                    self.assertEqual(
                        al["denenen"], [{"yerlesim": ad[oteki], "nedenler": [f"{oteki} sorunu"]}]
                    )
                    #  Öbürü de ölçü istiyorsa isteği seçenektir
                    oteki_durum = {"yan": yan, "arka": arka}[oteki]
                    self.assertEqual(
                        [x["yerlesim"] for x in al["secenek"]],
                        [ad[oteki]] if oteki_durum == "gereken" else [],
                    )
        #  K2 ( b ):  ikincinin isteği küçükse o seçilir, ilki seçenek olur
        artis = {"yan": 180.0, "arka": 30.0}
        d, al = avan_secici._yerlesimler(sira, sahte({"yan": "gereken", "arka": "gereken"}), sina)
        self.assertEqual(
            (d, al["yerlesim"], [x["yerlesim"] for x in al["secenek"]]), ("gereken", "arkada", ["yanda"])
        )
        #  K2 ( a ):  az ölçü isteyen önce — iki ölçünün toplamı küçük olsa da
        self.assertEqual(avan_secici._bedel([{"anahtar": "a", "eski": "1800", "yeni": 1980.0}]), (1, 180.0))
        self.assertLess(
            avan_secici._bedel([{"anahtar": "a", "eski": "1800", "yeni": 1980.0}]),
            avan_secici._bedel(
                [
                    {"anahtar": "a", "eski": "1800", "yeni": 1830.0},
                    {"anahtar": "kuyu_tavani_kotu", "eski": "+28,75", "yeni": "+28,88"},
                ]
            ),
        )
        #  Tek yerleşim ( paketin ağırlığı zaten arkada ):  denenen boş
        d, al = avan_secici._yerlesimler(sira[:1], sahte({"yan": "sigmaz"}), sina)
        self.assertEqual((d, al["yerlesim"], al["denenen"]), ("sigmaz", "yanda", []))

    def test_yeniden_secimde_denenen_ilkinki(self):
        """İstenen ölçüyle yeniden seçim ( _tek_seferde ) yine ölçü isterse:  denenen ilk seçimdekidir
        ( mimarın ölçüleriyle — _nedenler ), sonucun yerleşimi denenenden ve seçenekten çıkar.
        Seçenek doğrulanmış sonuçtan pahalıysa doğrulanmaz."""
        ilk = {
            "durum": "gereken",
            "sinama": 1,
            "gereken": [{"anahtar": "kuyu_genisligi", "eski": "1800", "yeni": 1900.0}],
            "yerlesim": "ağırlık yanda",
            "denenen": [{"yerlesim": "ağırlık arkada", "nedenler": ["arka mimarda"]}],
            "secenek": [
                {
                    "yerlesim": "ağırlık arkada",
                    "gereken": [{"anahtar": "kuyu_derinligi", "eski": "2700", "yeni": 3500.0}],
                }
            ],
            "_nedenler": {"ağırlık yanda": ["yan mimarda"], "ağırlık arkada": ["arka mimarda"]},
        }
        for yerlesim, denenen, secenek in (
            ("ağırlık yanda", [("ağırlık arkada", ["arka mimarda"])], ["ağırlık arkada"]),
            ("ağırlık arkada", [("ağırlık yanda", ["yan mimarda"])], []),
        ):
            with self.subTest(yerlesim):
                ikinci = {
                    "durum": "gereken",
                    "sinama": 1,
                    "gereken": [{"anahtar": "kuyu_genisligi", "eski": "1900", "yeni": 1950.0}],
                    "yerlesim": yerlesim,
                    "denenen": [{"yerlesim": "başka", "nedenler": ["büyütülmüş ölçüde"]}],
                    "secenek": [{"yerlesim": "başka", "gereken": []}],
                }
                with mock.patch.object(avan_secici, "_sec", return_value=copy.deepcopy(ikinci)) as sec:
                    r = avan_secici._tek_seferde({}, copy.deepcopy(ilk), time.monotonic())
                self.assertEqual(r["yerlesim"], yerlesim)
                self.assertEqual([(x["yerlesim"], x["nedenler"]) for x in r["denenen"]], denenen)
                self.assertEqual([x["yerlesim"] for x in r["secenek"]], secenek)
                self.assertEqual(r["gereken"][0]["eski"], "1800")
                self.assertNotIn("_nedenler", r)
                #  Seçenek ( +800 ) sonuçtan ( +150 ) pahalı:  doğrulanmadı ( AZAMI_YENIDEN tur )
                self.assertEqual(sec.call_count, avan_secici.AZAMI_YENIDEN)

    def test_secenek_dogrulaninca_ucuzsa_secilir(self):
        """630 kg 1600 × 1600 ( 27 Kas ):  arka ilk aramada tek ölçü ( derinlik +345 ) görünüp yanın iki
        ölçüsüne ( +210 ) yeğ tutuluyordu;  doğrulanınca genişlik de istedi ( +355 ).  Seçenek
        doğrulanır, doğrulanmış istekleri küçük olan sonuç olur ( sahte seçim — hızlı )."""
        ilk = {
            "durum": "gereken",
            "sinama": 1,
            "istek": "arka istek",
            "yerlesim": "ağırlık arkada",
            "gereken": [{"anahtar": "kuyu_derinligi", "eski": "1600", "yeni": 1945.0}],
            "secenek": [
                {
                    "yerlesim": "ağırlık yanda",
                    "gereken": [
                        {"anahtar": "kuyu_genisligi", "eski": "1600", "yeni": 1720.0},
                        {"anahtar": "kuyu_derinligi", "eski": "1600", "yeni": 1690.0},
                    ],
                }
            ],
            "_nedenler": {"ağırlık arkada": ["arka mimarda"], "ağırlık yanda": ["yan mimarda"]},
        }

        def sec(m2, taban=None):
            self.assertEqual(taban, {"kuyu_genisligi": 1600, "kuyu_derinligi": 1600})
            if m2["kuyu_derinligi"] == 1945 and m2["kuyu_genisligi"] == 1600:
                return {
                    "durum": "gereken",
                    "sinama": 1,
                    "yerlesim": "ağırlık arkada",
                    "istek": "arka istek",
                    "gereken": [{"anahtar": "kuyu_genisligi", "eski": "1600", "yeni": 1610.0}],
                }
            return {"durum": "uygun", "sinama": 1, "istek": f"istek {m2['kuyu_genisligi']}"}

        with mock.patch.object(avan_secici, "_sec", side_effect=sec):
            r = avan_secici._tek_seferde(
                {"kuyu_genisligi": 1600, "kuyu_derinligi": 1600}, copy.deepcopy(ilk), time.monotonic()
            )
        self.assertEqual(r["yerlesim"], "ağırlık yanda")
        self.assertEqual(
            [(g["anahtar"], g["yeni"]) for g in r["gereken"]],
            [("kuyu_genisligi", 1720.0), ("kuyu_derinligi", 1690.0)],
        )
        self.assertEqual(r["istek"], "istek 1720")
        self.assertEqual(
            [(x["yerlesim"], [(g["anahtar"], g["yeni"]) for g in x["gereken"]]) for x in r["secenek"]],
            [("ağırlık arkada", [("kuyu_derinligi", 1945.0), ("kuyu_genisligi", 1610.0)])],
        )
        self.assertEqual(
            [(x["yerlesim"], x["nedenler"]) for x in r["denenen"]], [("ağırlık arkada", ["arka mimarda"])]
        )

    def test_beyanla_olcu_isteniyorsa_kart_once(self):
        """K7 ( 27 Kas — kullanıcı:  "kartta 1:1 önce" ):  630 kg makine daireli pakette kartta 2:1;  2:1
        ancak kuyu genişleyince kuruluyor ( bina taraması 2430 buluyor ), paketin 1:1'i mimarın kuyusuna
        olduğu gibi sığıyor.  Sonuç "beyan" ( kartta 1:1 ), 2:1'in istediği seçenek ( kosul:  kartın
        askısı kalırsa ) — mimarın binası değişmeden çözüm önce."""
        t = PAKETLER[(630, False)]
        r = avan_secici.sec(mimari(t, aski_orani=2))
        self.assertEqual(r["durum"], "beyan", r)
        self.assertEqual([(b["anahtar"], b["yeni"]) for b in r["beyan"]], [("aski_orani", "1")])
        self.assertEqual(len(r["secenek"]), 1)
        x = r["secenek"][0]
        self.assertEqual(x["kosul"], [["aski_orani", "2"]])
        self.assertEqual([g["anahtar"] for g in x["gereken"]], ["kuyu_genisligi"])
        self.assertGreater(x["gereken"][0]["yeni"], int(t["asansor"]["kuyu_genisligi"]))
        #  Kartın 1:1'i mimarın kuyusunda olduğu gibi uygun
        self.assertEqual(avan_secici.sec(mimari(t, aski_orani=1))["durum"], "uygun")
        #  Kapı trafik hesabınındır:  ölçü isteniyorsa kapıyı daraltmak önerilmez ( ilk CI'da 16 kapı
        #  senaryosu "kuyu +" yerine "kapıyı 800'e düşürün" diyordu )
        r = avan_secici.sec(
            mimari(PAKETLER[(1000, True)], kat_kapisi_tipi="Otomatik Merkezi", kapi_genisligi=1000)
        )
        self.assertEqual(r["durum"], "gereken", r)
        self.assertEqual([g["anahtar"] for g in r["gereken"]], ["kuyu_genisligi"])

    def test_istenen_olcu_en_kucuk(self):
        """13 Kas denetimi:  630 kg 1600 × 1600 kuyuda genişlik 2110 isteniyordu;  asansör 1800'e
        sığıyor.  İstenen ölçü paketin kuyusundan büyük olamaz ve o ölçüyle seçici "uygun" der.
        ( Kanıtlı en küçük değildir:  eşik aralığı gibi başka yerleşim ayarları birkaç cm daha
        kazandırabilir — o kuyu girilirse seçici yine "uygun" der. )"""
        t = PAKETLER[(630, True)]
        m = mimari(t, kuyu_genisligi=1600, kuyu_derinligi=1600)
        r = avan_secici.sec(m)
        self.assertEqual(r["durum"], "gereken", r)
        yeni = {g["anahtar"]: g for g in r["gereken"]}
        self.assertEqual(sorted(yeni), ["kuyu_derinligi", "kuyu_genisligi"])
        for k, g in yeni.items():
            self.assertEqual(g["eski"], "1600")
            self.assertGreater(g["yeni"], 1600)
            self.assertLessEqual(g["yeni"], int(t["asansor"][k]))
            self.assertTrue(g["sebep"])
        #  Çare bulucunun topladığı 2110'un çok altında:  kabin 1100 + ağırlık yanda
        self.assertLessEqual(yeni["kuyu_genisligi"]["yeni"], 1800)
        self.temiz(r)
        m2 = {**m, **{k: int(g["yeni"]) for k, g in yeni.items()}}
        r2 = avan_secici.sec(m2)
        self.assertEqual(r2["durum"], "uygun", r2)
        self.temiz(r2)

    def test_dar_kuyuda_once_yerlesim(self):
        """Paketinkinden dar kuyu kaçıklıklarla ( kabin, kapı ) sığıyorsa mimardan ölçü istenmez."""
        t = PAKETLER[(630, True)]
        m = mimari(t, kuyu_genisligi=1800, kuyu_derinligi=1690)
        r = avan_secici.sec(m)
        self.assertEqual(r["durum"], "uygun", r)
        self.mimari_aynen(m, r["istek"])
        self.temiz(r)

    def test_paketin_tamponu_hiza_yetmezse(self):
        """1275 kg paketinin tampon stroku ( 180 mm ) 1,0 m/s içindir;  2 m/s'de "sığmaz"
        deniyordu.  Tampon programın kuralına bırakılır ( hıza göre ) — asansör kurulur."""
        t = PAKETLER[(1275, True)]
        self.assertEqual(t["asansor"]["kabin_tampon_ezilme"], "180")
        r = avan_secici.sec(mimari(t, beyan_hizi=2))
        self.assertIn(r["durum"], ("uygun", "gereken"), r)
        self.assertEqual(r["istek"]["asansorler"][0]["kabin_tampon_ezilme"], "")
        self.temiz(r)

    def test_kucuk_makine_dairesi(self):
        """Mimarın makine dairesi hazır asansörünkinden küçük ( 13 Kas ):  yetiyorsa asansör
        aynen kurulur;  yetmiyorsa "sığmaz" denmez — odanın ölçüsü mimardan istenir, o ölçüyle
        seçici "uygun" der.  İstenen oda hazır asansörünkinden büyük olamaz."""
        t = PAKETLER[(630, False)]
        pg = t["proje_geneli"]
        #  Biraz küçük oda yetiyor
        m = mimari(t, mk_uzunluk=3000, mk_genislik=2500)
        r = avan_secici.sec(m)
        self.assertEqual(r["durum"], "uygun", r)
        self.mimari_aynen(m, r["istek"])
        self.temiz(r)
        #  Kuyudan küçük oda yetmiyor
        m = mimari(t, mk_uzunluk=1000, mk_genislik=1000)
        r = avan_secici.sec(m)
        self.assertEqual(r["durum"], "gereken", r)
        yeni = {g["anahtar"]: g for g in r["gereken"]}
        self.assertEqual(sorted(yeni), ["mk_genislik", "mk_uzunluk"])
        for k, g in yeni.items():
            self.assertEqual(g["eski"], "1000")
            self.assertGreater(g["yeni"], 1000)
            self.assertLessEqual(g["yeni"], int(pg[k]))
            self.assertTrue(g["sebep"])
        self.temiz(r)
        r2 = avan_secici.sec({**m, **{k: int(g["yeni"]) for k, g in yeni.items()}})
        self.assertEqual(r2["durum"], "uygun", r2)
        self.temiz(r2)

    def test_verilmeyen_makine_dairesi_kuyuyla_buyur(self):
        """Tarama ( 14 Kas ):  630 ve 1000 kg makine dairelide paketinkinden 600 mm geniş kuyu
        "sığmaz" çıkıyordu — mimarın vermediği makine dairesi hazır asansörünkinde kalıyor,
        duvarı geniş kuyunun boşluğuna basıyordu.  Oda kuyuyla birlikte büyür."""
        for yuk in (630, 1000):
            t = PAKETLER[(yuk, False)]
            with self.subTest(t["kimlik"]):
                m = mimari(t, kuyu_genisligi=int(t["asansor"]["kuyu_genisligi"]) + 600)
                del m["mk_genislik"], m["mk_uzunluk"]
                r = avan_secici.sec(m)
                self.assertEqual(r["durum"], "uygun", r)
                pg = r["istek"]["proje_geneli"]
                self.assertEqual(int(pg["mk_genislik"]), int(t["proje_geneli"]["mk_genislik"]) + 600)
                self.assertEqual(pg["mk_uzunluk"], t["proje_geneli"]["mk_uzunluk"])
                self.temiz(r)
        #  Mimarın verdiği oda aynen kullanılır ( büyütülmez )
        t = PAKETLER[(630, False)]
        m = mimari(t, mk_genislik=3400, kuyu_genisligi=int(t["asansor"]["kuyu_genisligi"]) + 600)
        r = avan_secici.sec(m)
        self.assertEqual(r["durum"], "uygun", r)
        self.assertEqual(r["istek"]["proje_geneli"]["mk_genislik"], "3400")

    def test_istenen_olcu_tek_seferde_yeter(self):
        """Tarama ( 14 Kas ):  1250 kg makine dairelide trafiğin 900 mm kapısıyla "kuyu genişliği
        2020" isteniyor, 2020 girilince bu kez 2030 isteniyordu.  Mimara söylenen ölçüyle seçici
        "uygun" der."""
        t = PAKETLER[(1250, False)]
        m = mimari(t, kat_kapisi_tipi="Teleskopik Sol", kapi_genisligi=900)
        r = avan_secici.sec(m)
        self.assertEqual(r["durum"], "gereken", r)
        self.assertEqual([g["anahtar"] for g in r["gereken"]], ["kuyu_genisligi"])
        (g,) = r["gereken"]
        self.assertEqual(g["eski"], m["kuyu_genisligi"])
        self.temiz(r)
        r2 = avan_secici.sec({**m, "kuyu_genisligi": int(g["yeni"])})
        self.assertEqual(r2["durum"], "uygun", r2)
        self.temiz(r2)

    def test_elle_ayarlanan_olcu(self):
        """Kullanıcı ( 14 Kas ):  "ölçüye tıklayınca değiştirebilmem lazım — ray – kapı, karşı
        ağırlık – duvar".  Elle ayar ( m["ayar"] ) istekte AYNEN durur, sonuç yine doğrulanır;
        mimarinin, trafiğin ve kartın ölçüleri ayarla değişmez."""
        t = PAKETLER[(630, True)]
        m = mimari(t)
        r = avan_secici.sec({**m, "ayar": {"ray_kapi_arasi": 700}})
        self.assertEqual(r["durum"], "uygun", r)
        self.assertEqual(r["istek"]["asansorler"][0]["ray_kapi_arasi"], "700")
        self.mimari_aynen(m, r["istek"])
        self.temiz(r)
        #  Seçicinin kendi seçtiği kaçıklık da ayarlanır:  uyarlama onu değiştirmez
        r = avan_secici.sec({**m, "ayar": {"kabin_yana_kaciklik": "40"}})
        self.assertIn(r["durum"], ("uygun", "gereken"), r)
        self.assertEqual(r["istek"]["asansorler"][0]["kabin_yana_kaciklik"], "40")
        self.temiz(r)
        #  MAKİNE DAİRESİ KAPISI ( 17 Kas — avanda da sürüklenir, dört duvar arasında ):  proje geneli
        #  girdidir, isteğin proje_geneli'sine yazılır;  kalan proje geneli girdiler ayarlanamaz
        md = mimari(PAKETLER[(630, False)])
        kapisiz = avan_secici.sec(md)
        r = avan_secici.sec({**md, "ayar": {"md_kapi_konum": 900, "md_pano_duvar": "Sol"}})
        self.assertEqual(r["durum"], "uygun", r)
        self.assertEqual(r["istek"]["proje_geneli"]["md_kapi_konum"], "900")
        self.assertNotIn("md_kapi_konum", r["istek"]["asansorler"][0])
        self.assertNotEqual(r["istek"]["proje_geneli"].get("md_pano_duvar"), "Sol")
        self.assertNotIn("kapi_reddi", r)
        self.temiz(r)
        #  Başka duvara:  630-md odasında ( 2600 × 3800 ) yan duvarın arka ucu uygun
        r = avan_secici.sec({**md, "ayar": {"md_kapi_duvar": "Sağ", "md_kapi_konum": 2400}})
        self.assertEqual(r["durum"], "uygun", r)
        pg = r["istek"]["proje_geneli"]
        self.assertEqual((pg["md_kapi_duvar"], pg["md_kapi_konum"]), ("Sağ", "2400"))
        self.temiz(r)
        #  Kapı seçimi ETKİLEMEZ:  asansör kapısız seçilenle aynı ( yalnız kapının girdileri farklı )
        ayni = lambda x: {k: v for k, v in x.items() if not k.startswith("md_kapi_")}
        self.assertEqual(ayni(pg), ayni(kapisiz["istek"]["proje_geneli"]))
        self.assertEqual(r["istek"]["asansorler"], kapisiz["istek"]["asansorler"])
        #  UYGUN OLMAYAN YER:  çizim kaybolmaz — istek eski kapısıyla, sebep kapi_reddi'nde.
        #  Eskiden kapı aramaya giriyordu:  6 – 12 sn sonra ilgisiz gerekçeyle "sığmaz"
        for ayar, sebep in (
            ({"md_kapi_duvar": "Sağ", "md_kapi_konum": 900}, "tabliyenin kenarına denk geliyor"),
            ({"md_kapi_konum": 2400}, "duvarın dışına taşıyor"),
        ):
            with self.subTest(ayar=ayar):
                r = avan_secici.sec({**md, "ayar": ayar})
                self.assertEqual(r["durum"], "uygun", r)
                self.assertEqual(r["istek"], kapisiz["istek"])
                self.assertTrue(any(sebep in x for x in r["kapi_reddi"]), r["kapi_reddi"])
                self.assertLess(r["sure"], 5)
        #  İzinsiz ve tanınmayan alanlar atılır
        ayar = {"kuyu_genisligi": 9999, "kabin_genisligi": 900, "beyan_hizi": 2, "aski_orani": 1, "yok": 1}
        self.assertEqual(avan_secici.ayarlar({"ayar": ayar}), {})
        r = avan_secici.sec({**m, "ayar": ayar})
        self.assertEqual(r["durum"], "uygun", r)
        self.mimari_aynen(m, r["istek"])
        a = r["istek"]["asansorler"][0]
        self.assertEqual({k: a[k] for k in KABIN}, {k: t["asansor"][k] for k in KABIN})

    def test_eksik_ve_paketsiz(self):
        t = PAKETLER[(630, True)]
        m = mimari(t)
        del m["kuyu_derinligi"]
        self.assertEqual(
            avan_secici.sec(m), {"durum": "eksik", "eksik": ["kuyu_derinligi"], "sinama": 0, "sure": 0.0}
        )
        #  Makine dairesi varsa zemini de mimariden
        m = mimari(PAKETLER[(630, False)])
        del m["md_zemini_kotu"]
        self.assertEqual(avan_secici.sec(m)["eksik"], ["md_zemini_kotu"])
        #  Hazır asansörü olmayan yük ( 1125 kg — 15 kişi;  Tablo-7'de basılı değil )
        self.assertEqual(avan_secici.sec(mimari(t, beyan_yuku=1125))["durum"], "paket_yok")

    def test_kartin_kabini(self):
        """24 Kas ( kullanıcı:  "Evet, kullanılsın" ):  kartın kabini standarda uyuyorsa çizim onunla
        kurulur, seçici değiştirmez.  Paketinkinden 100 mm dar, alanı koruyan derin kabin 100 mm dar
        kuyuya sığar:  kabinin ağırlık yanındaki kenarı paketteki yerinde kalır ( kaçıklık 0 — kuyu
        ile kabin aynı kadar daraldı;  eskiden kabin yalnız kuyunun farkıyla kayardı ).  Boş kutu
        paketinkini alır."""
        t = PAKETLER[(800, True)]
        m = mimari(
            t, kuyu_genisligi=2200, kuyu_derinligi=2000, kabin_genisligi=1250, kabin_derinligi=1550, kisi=10
        )
        r = avan_secici.sec(m)
        self.assertEqual(r["durum"], "uygun", r)
        self.mimari_aynen(m, r["istek"])
        a = r["istek"]["asansorler"][0]
        self.assertEqual((a["kabin_genisligi"], a["kabin_derinligi"]), ("1250", "1550"))
        self.assertEqual(a["kabin_yana_kaciklik"], "0")
        self.temiz(r)
        #  Kartta yalnız genişlik:  derinlik paketinki
        self.assertEqual(
            avan_secici.kabin(t, {"kabin_genisligi": "1300", "kabin_derinligi": ""}),
            {"kabin_genisligi": 1300, "kabin_derinligi": 1400},
        )
        #  Paketin kabini ya da boş kart:  denetlenmez, paketinki ( 24 Kas'tan önceki gibi )
        for kabin in ({"kabin_genisligi": "1350", "kabin_derinligi": "1400"}, {"kabin_genisligi": 0}, {}):
            with self.subTest(kabin):
                self.assertEqual(
                    avan_secici.kabin_nedenleri(t, {"beyan_yuku": "800", "kisi": 10, **kabin}), []
                )
                self.assertEqual(
                    avan_secici.kabin(t, kabin), {"kabin_genisligi": 1350, "kabin_derinligi": 1400}
                )

    def test_kartin_dar_kabini_dar_kuyuda(self):
        """Kullanıcının kuyusu ( 24 Kas ):  800 kg, makine dairesiz, 1800 × 2700, son kat 4050.  Paketin
        1350 × 1400 kabiniyle genişlik isteniyordu;  kartın 1300 × 1400 kabiniyle de istenir, ama
        paketin kuyusunun kabin farkı kadar darı ( 2250 ) başlangıçtır ve istenen ölçü onun altındadır.
        İstenen ölçüyle çizim kartın kabiniyle temiz."""
        t = PAKETLER[(800, True)]
        m = mimari(
            t,
            kuyu_genisligi=1800,
            kuyu_derinligi=2700,
            kuyu_tavani_kotu="+19,05",
            kabin_genisligi=1300,
            kabin_derinligi=1400,
            kisi=10,
        )
        r = avan_secici.sec(m)
        self.assertEqual(r["durum"], "gereken", r)
        self.assertEqual([g["anahtar"] for g in r["gereken"]], ["kuyu_genisligi"], r["gereken"])
        self.assertGreater(r["gereken"][0]["yeni"], 1800)
        self.assertLess(r["gereken"][0]["yeni"], 2250)
        a = r["istek"]["asansorler"][0]
        self.assertEqual((a["kabin_genisligi"], a["kabin_derinligi"]), ("1300", "1400"))
        self.temiz(r)

    def test_standarda_uymayan_kabin_aranmaz(self):
        """Kartın kabini standarda uymuyorsa seçici aramaz ( sınama 0 ):  "beyan" — kartta paketin
        kabini, sebebi TS EN 81-20'nin çizelgesiyle.  Büyük kabin Çizelge 6'yı aşar ( 800 kg en çok
        2,00 m² ):  uygulamanın hesabı da reddeder.  Küçük kabin trafiğin kişisini taşımaz ( Çizelge 8:
        10 kişi en az 1,73 m² ):  pafta kartın kişisini yazar.  Kişi verilmezse yalnız üst sınır
        ( Çizelge 8 uygulamada ret ölçütü değildir — kabine yazılacak kişiyi verir )."""
        t = PAKETLER[(800, True)]
        r = avan_secici.sec(mimari(t, kabin_genisligi=1500, kisi=10))
        self.assertEqual(
            (r["durum"], r["beyan_turu"], r["sinama"], r["paket"]), ("beyan", "kabin", 0, "800"), r
        )
        self.assertEqual(
            [(b["anahtar"], b["eski"], b["yeni"]) for b in r["beyan"]], [("kabin_genisligi", "1500", "1350")]
        )
        (neden,) = r["nedenler"]
        for parca in ("2,10 m²", "800 kg", "2,00 m²", "Çizelge 6"):
            self.assertIn(parca, neden)
        r = avan_secici.sec(mimari(t, kabin_genisligi=1200, kabin_derinligi=1400, kisi=10))
        self.assertEqual((r["durum"], r["beyan_turu"], r["sinama"]), ("beyan", "kabin", 0), r)
        self.assertEqual([b["anahtar"] for b in r["beyan"]], ["kabin_genisligi"])
        (neden,) = r["nedenler"]
        for parca in ("1,68 m²", "10 kişi", "1,73 m²", "Çizelge 8"):
            self.assertIn(parca, neden)
        self.assertEqual(
            avan_secici.kabin_nedenleri(
                t, {"beyan_yuku": 800, "kabin_genisligi": 1200, "kabin_derinligi": 1400}
            ),
            [],
        )
        #  Aramayan sonuç sunucunun paketinde de aranmaz
        self.assertFalse(avan_secici.aranacak_mi(mimari(t, kabin_genisligi=1500, kisi=10)))


class MakineDairesiYuksekligi(unittest.TestCase):
    """16 Kas ( kullanıcının A BLOK 800 KG projesi:  kesitte bakım kulesi 2,40 m, paftada 3500
    yazıyordu ):  avanda makine dairesinin iç yüksekliği de mimarın ( bina ölçüsü ).  Boşsa
    uygulamanın varsayılanı;  verilirse istekte aynen;  yetmiyorsa mimardan istenir.  Oda
    zemini tabliyenin üstünde ( kot farkı yok — kullanıcının projesi gibi )."""

    def setUp(self):
        self.t = PAKETLER[(630, False)]
        a = {**self.t["proje_geneli"], **self.t["asansor"]}
        doseme = kopru.tavan_dosemesi({k: float(v) for k, v in a.items() if k == "kuyu_duvar_kalinligi"})
        self.zemin = kot(self.t["asansor"]["kuyu_tavani_kotu"], doseme)

    def m(self, **ek):
        return mimari(self.t, md_zemini_kotu=self.zemin, **ek)

    def test_bossa_varsayilan_verilirse_aynen(self):
        r = avan_secici.sec(self.m())
        self.assertEqual(r["durum"], "uygun", r)
        self.assertNotIn("md_yukseklik", r["istek"]["proje_geneli"])
        r = avan_secici.sec(self.m(md_yukseklik=2400))
        self.assertEqual(r["durum"], "uygun", r)
        self.assertEqual(r["istek"]["proje_geneli"]["md_yukseklik"], "2400")
        AvanSecici.temiz(self, r)

    def test_alcak_oda_mimardan_istenir(self):
        """2000 mm oda:  "sığmaz" değil, yükseklik mimardan istenir;  küçük oda kuralı
        ( plan ölçüleri ) yüksekliğe bakmaz."""
        self.assertEqual(avan_secici._kucuk_oda(self.t, self.m(md_yukseklik=2000)), {})
        r = avan_secici.sec(self.m(md_yukseklik=2000))
        self.assertEqual(r["durum"], "gereken", r)
        g = {x["anahtar"]: x for x in r["gereken"]}
        self.assertEqual(set(g), {"md_yukseklik"})
        self.assertGreaterEqual(float(g["md_yukseklik"]["yeni"]), 2100)
        self.assertIn("temiz yüksekliği", g["md_yukseklik"]["sebep"])


class KorumaliSecici(unittest.TestCase):
    """16 Kas ( kullanıcı:  "süre sınırı koymasak daha doğru olmaz mı" — uygulamanın "düzeltme
    öner"i gibi ):  sunucuda ( avan_secici.korumali ) seçici güvenlik süresi, iptal ve önbellekle
    çalışır.  Süre ya da iptal aramayı keserse yanıt "tamamlanmadi" — "sığmaz" DEĞİL."""

    def setUp(self):
        avan_secici._ONBELLEK.clear()
        self.m = mimari(PAKETLER[(630, True)])

    def test_guvenlik_suresi_sigmaz_demez(self):
        with mock.patch.object(avan_secici, "GUVENLIK_SURESI", -1.0), avan_secici.korumali():
            r = avan_secici.sec(self.m)
        self.assertEqual((r["durum"], r["neden"]), ("tamamlanmadi", "sure"), r)
        self.assertIn("güvenlik süresinde bitmedi", r["hata"])
        #  Yarıda kalan saklanmaz:  sonraki istek aramayı yapar
        with avan_secici.korumali():
            self.assertEqual(avan_secici.sec(self.m)["durum"], "uygun")

    def test_birakilan_istek_durur(self):
        """İptal sorgusu True dönünce arama durur — çare bulucunun içinde de ( _CareButcesi )."""
        sayi = [0]
        asil = care_uclari.girdi_durumu

        def say(v, i):
            sayi[0] += 1
            return asil(v, i)

        m = mimari(PAKETLER[(630, True)], kuyu_genisligi=1650, kuyu_derinligi=2300)  #  28 sınamalık
        with mock.patch.object(care_uclari, "girdi_durumu", say), avan_secici.korumali(lambda: sayi[0] >= 3):
            r = avan_secici.sec(m)
        self.assertEqual((r["durum"], r["neden"]), ("tamamlanmadi", "iptal"), r)
        #  En çok bir sınama geç:  çare bulucunun ilk ölçümü bütçeye bakmaz ( care_uclari.coz ).
        #  Eskiden çare bulucu iptali hiç görmüyordu:  27 sınama sürüyordu
        self.assertLessEqual(sayi[0], 4)

    def test_onbellek(self):
        """Bütçe deterministik:  aynı girdinin sonucu saklanır, ikinci istek sınamasız döner;
        dönen kopyadır ( değiştirmek saklananı bozmaz ).  Bağlam dışında ( testler, tarama )
        önbellek kullanılmaz."""
        with avan_secici.korumali():
            r1 = avan_secici.sec(self.m)
        self.assertEqual(r1["durum"], "uygun")
        r1["istek"]["asansorler"][0]["kuyu_genisligi"] = "bozuldu"
        with (
            mock.patch.object(care_uclari, "girdi_durumu", side_effect=AssertionError("sınama yapıldı")),
            avan_secici.korumali(),
        ):
            r2 = avan_secici.sec(self.m)
        self.assertEqual(r2["istek"]["asansorler"][0]["kuyu_genisligi"], self.m["kuyu_genisligi"])
        with mock.patch.object(care_uclari, "girdi_durumu", side_effect=AssertionError("sınama yapıldı")):
            with self.assertRaises(AssertionError):
                avan_secici.sec(self.m)

    def test_kapi_aramayi_yinelemez(self):
        """18 Kas ( yayın öncesi denetim ):  makine dairesi kapısı seçimi etkilemez ( _sec_ham ) —
        sunucuda kapısız seçim önbellekten gelir, kapı ona taşınır:  TEK sınama.  Eskiden önbellek
        yalnız kapılı anahtara bakıyordu, kapı her sürüklenişte arama baştan yapılıyordu ( 800 kg
        makine daireli örnek:  kapısız önbellekten 0,26 sn, her kapı yeri 9,7 sn ).  Sonuç korumasız
        seçiminkiyle aynıdır:  kapı taşınır ya da gerekçesiyle reddedilir."""
        md = mimari(PAKETLER[(630, False)])
        with avan_secici.korumali():
            self.assertEqual(avan_secici.sec(md)["durum"], "uygun")
        sayi = [0]
        asil = care_uclari.girdi_durumu

        def say(v, i):
            sayi[0] += 1
            return asil(v, i)

        hicbiri = mock.patch.object(care_uclari, "girdi_durumu", side_effect=AssertionError("sınama yapıldı"))
        #  Uygun yer ve tabliyenin kenarı ( kapi_reddi — test_elle_ayarlanan_olcu )
        for ayar in ({"md_kapi_konum": 900}, {"md_kapi_duvar": "Sağ", "md_kapi_konum": 900}):
            with self.subTest(ayar=ayar):
                m = {**md, "ayar": ayar}
                #  Paketin "henüz aranmadı" sorusu:  kapısız seçim hazırsa kapılı asansör aranmaz
                self.assertFalse(avan_secici.aranacak_mi(m))
                sayi[0] = 0
                with mock.patch.object(care_uclari, "girdi_durumu", say), avan_secici.korumali():
                    r = avan_secici.sec(m)
                self.assertEqual(sayi[0], 1)
                ham = avan_secici.sec(m)
                alanlar_ = ("durum", "istek", "kapi_reddi", "sinama")
                self.assertEqual({k: r.get(k) for k in alanlar_}, {k: ham.get(k) for k in alanlar_})
                #  Kapılı sonuç da saklanır:  aynı yer sınamasız
                with hicbiri, avan_secici.korumali():
                    self.assertEqual(avan_secici.sec(m)["istek"], r["istek"])
        #  Kapısız seçim yoksa paket arar;  yarıda kalan arama kapılı da saklanmaz
        avan_secici._ONBELLEK.clear()
        m = {**md, "ayar": {"md_kapi_konum": 950}}
        self.assertTrue(avan_secici.aranacak_mi(m))
        with mock.patch.object(avan_secici, "GUVENLIK_SURESI", -1.0), avan_secici.korumali():
            self.assertEqual(avan_secici.sec(m)["durum"], "tamamlanmadi")
        self.assertEqual(len(avan_secici._ONBELLEK), 0)

    def test_uc_baglanti_kapaninca_durur(self):
        """/api/avan/cizimler:  ekran isteği bırakınca ( bağlantı kapandı ) arama durur — eskiden
        sunucu bırakılan aramayı sonuna kadar sürdürüyordu ( 28 sınamalık kuyu ~20 sn )."""
        from testler.test_avan_cizim_ucu import govde, kart

        t = PAKETLER[(630, True)]["asansor"]
        g = govde(kart(t, kuyu_genisligi="1650", kuyu_derinligi="2300"))

        class Kapandi:
            headers = {}

            async def is_disconnected(self):
                return True

        t0 = time.monotonic()
        r = json.loads(asyncio.run(avan_cizim_uclari.api_avan_cizimler_ucu(Kapandi(), g)).body)
        self.assertEqual((r["durum"], r.get("neden")), ("tamamlanmadi", "iptal"), r)
        self.assertLess(time.monotonic() - t0, 5)


class DiskOnbellegi(unittest.TestCase):
    """17 Kas ( yayın öncesi denetim ):  sunucunun dört işçisi seçicinin sonucunu diskten paylaşır
    ( avan_secici._Onbellek ).  "Projeyi indir" Çizimler adımında bulunan asansörü başka işçide
    bulamayınca baştan arıyordu — kullanıcının 2 asansörlü projesinde 48 sn."""

    def setUp(self):
        self.kok = tempfile.mkdtemp(prefix="secici-disk-")
        self.ortam = mock.patch.dict(os.environ, {"AVAN_SECICI_ONBELLEK": self.kok})
        self.ortam.start()
        self.addCleanup(self.ortam.stop)
        self.addCleanup(shutil.rmtree, self.kok, True)
        self.m = mimari(PAKETLER[(630, True)])

    def onbellek(self):
        """Yeni bir işçinin önbelleği:  belleği boş, disk aynı."""
        return avan_secici._Onbellek()

    def sec(self, onbellek):
        with mock.patch.object(avan_secici, "_ONBELLEK", onbellek), avan_secici.korumali():
            return avan_secici.sec(copy.deepcopy(self.m))

    def test_baska_surec_diskten_okur(self):
        """Başka bir süreç ( işçi ) arar ve yazar;  bu süreç sınama yapmadan aynı sonucu alır."""
        betik = (
            "import sys, json\n"
            "sys.path[:0] = ['hesap', '.']\n"
            "from uclar import avan_secici\n"
            "m = json.loads(sys.argv[1])\n"
            "with avan_secici.korumali():\n"
            "    print(json.dumps(avan_secici.sec(m)['durum']))\n"
        )
        cikti = subprocess.run(
            [sys.executable, "-c", betik, json.dumps(self.m)],
            check=False,
            cwd=KOK,
            capture_output=True,
            text=True,
            timeout=600,
            env={**os.environ, "AVAN_SECICI_ONBELLEK": self.kok},
        )
        self.assertEqual(cikti.stdout.strip(), '"uygun"', cikti.stderr[-2000:])
        with mock.patch.object(care_uclari, "girdi_durumu", side_effect=AssertionError("sınama yapıldı")):
            r = self.sec(self.onbellek())
        self.assertEqual(r["durum"], "uygun")
        #  Diskten okunan, aramanın kendisiyle birebir ( önbelleksiz yeni arama )
        with mock.patch.dict(os.environ, {"AVAN_SECICI_ONBELLEK": "kapali"}):
            yeni = self.sec(self.onbellek())
        r.pop("sure"), yeni.pop("sure")
        self.assertEqual(r, yeni)

    def test_klasor_silinince_yeniden_kurulur(self):
        o = self.onbellek()
        self.sec(o)
        shutil.rmtree(self.kok)
        o.clear()  # hata vermez
        self.sec(o)
        self.assertTrue([x for x in os.listdir(o._disk()) if x.endswith(".json")])

    def test_program_degisince_eskisi_silinir(self):
        o = self.onbellek()
        with mock.patch.object(avan_secici, "_kod_imzasi", return_value="eski"):
            self.sec(o)
        self.assertTrue(os.listdir(os.path.join(self.kok, "eski")))
        with mock.patch.object(avan_secici, "_kod_imzasi", return_value="yeni"):
            yeni = self.onbellek()
            with mock.patch.object(care_uclari, "girdi_durumu", wraps=care_uclari.girdi_durumu) as s:
                self.assertEqual(self.sec(yeni)["durum"], "uygun")
            self.assertGreater(s.call_count, 0)  # eski programın sonucu kullanılmadı
        self.assertEqual(os.listdir(self.kok), ["yeni"])

    def test_bozuk_ve_yarim_dosya_yok_sayilir(self):
        o = self.onbellek()
        self.sec(o)
        k = o._disk()
        (ad,) = [x for x in os.listdir(k) if x.endswith(".json")]
        with open(os.path.join(k, ad), "w", encoding="utf-8") as f:
            f.write('{"anahtar": "yarım')
        with mock.patch.object(care_uclari, "girdi_durumu", wraps=care_uclari.girdi_durumu) as s:
            self.assertEqual(self.sec(self.onbellek())["durum"], "uygun")
        self.assertGreater(s.call_count, 0)
        #  Geçici dosya kalmaz ( atomik yazım )
        self.assertEqual([x for x in os.listdir(k) if x.endswith(".tmp")], [])

    def test_yarida_kalan_yazilmaz(self):
        o = self.onbellek()
        with mock.patch.object(avan_secici, "GUVENLIK_SURESI", -1.0):
            self.assertEqual(self.sec(o)["durum"], "tamamlanmadi")
        self.assertEqual([x for x in os.listdir(o._disk()) if x.endswith(".json")], [])

    def test_kapali_ve_guvensiz_klasor(self):
        with mock.patch.dict(os.environ, {"AVAN_SECICI_ONBELLEK": "kapali"}):
            o = self.onbellek()
            self.assertEqual(self.sec(o)["durum"], "uygun")
            self.assertIs(o._disk(), False)
        #  Herkesin yazabildiği klasör:  içine başkası sonuç koyabilir — kullanılmaz
        acik = tempfile.mkdtemp(prefix="secici-acik-")
        self.addCleanup(shutil.rmtree, acik, True)
        os.chmod(acik, 0o777)
        with (
            mock.patch.dict(os.environ, {"AVAN_SECICI_ONBELLEK": acik}),
            self.assertLogs(avan_secici.log, "WARNING"),
        ):
            self.assertIs(avan_secici._disk_klasoru(), False)

    def test_sinir(self):
        o = self.onbellek()
        with mock.patch.object(avan_secici, "DISK_ONBELLEK_AZAMI", 2):
            for i in range(4):
                o.koy(f"anahtar {i}", {"durum": "uygun", "i": i})
                time.sleep(0.01)
        dosyalar = [x for x in os.listdir(o._disk()) if x.endswith(".json")]
        self.assertEqual(len(dosyalar), 2)
        yeni = self.onbellek()
        self.assertEqual(yeni.al("anahtar 3"), {"durum": "uygun", "i": 3})
        self.assertIsNone(yeni.al("anahtar 0"))
        #  JSON'a birebir dönmeyen sonuç diske yazılmaz ( okunan farklı olurdu )
        o.koy("demet", {"durum": "uygun", "x": (1, 2)})
        self.assertIsNone(self.onbellek().al("demet"))


class KodImzasi(unittest.TestCase):
    """17 Kas denetimi:  disk önbelleğinin "program değişti mi" imzası taslak verisini ( kod
    klasörlerinin dışında — on-yuz/src/lib/taslaklar.json ), yazı tiplerini ve kütüphane
    sürümlerini kapsamıyordu;  ilk kullanımda hesaplanıyordu.  Yalnız taslak değişen bir
    güncellemeden sonra eski hazır asansörle bulunmuş sonuç kullanılırdı."""

    def agac(self):
        """Küçük bir program ağacı:  kod, yazı tipi ( imza klasörlerinde ), temel.py."""
        kok = tempfile.mkdtemp(prefix="imza-")
        self.addCleanup(shutil.rmtree, kok, True)
        for yol, icerik in (
            ("temel.py", b"x = 1"),
            ("cizim/kod.py", b"y = 2"),
            ("cizim/yazi/Yazi.ttf", b"yazi tipi 1"),
            ("cizim/yazi/OKU.txt", b"lisans"),
        ):
            os.makedirs(os.path.dirname(os.path.join(kok, yol)) or kok, exist_ok=True)
            with open(os.path.join(kok, yol), "wb") as f:
                f.write(icerik)
        return kok

    def test_taslak_verisi_imzada(self):
        """Taslakların dosyası kod klasörlerinin dışında:  bu sürecin yüklediği veri imzaya girer."""
        taslaklar = copy.deepcopy(avan_secici._TASLAKLAR)
        taslaklar[0]["asansor"]["kuyu_genisligi"] = "9999"
        self.assertNotEqual(
            avan_secici._imza_hesapla(),
            avan_secici._imza_hesapla(veri=[taslaklar, avan_secici._AVAN_PAKETLERI]),
        )
        self.assertNotIn(
            os.path.relpath(os.path.join(KOK, "on-yuz"), KOK).split(os.sep)[0], avan_secici._IMZA_KLASORLERI
        )

    def test_yazi_tipi_ve_kutuphane_imzada(self):
        kok = self.agac()
        ilk = avan_secici._imza_hesapla(kok=kok, veri=[])
        self.assertEqual(ilk, avan_secici._imza_hesapla(kok=kok, veri=[]))
        #  İmzanın türü olmayan dosya ( lisans metni ) imzayı değiştirmez
        with open(os.path.join(kok, "cizim", "yazi", "OKU.txt"), "wb") as f:
            f.write(b"lisans 2")
        self.assertEqual(ilk, avan_secici._imza_hesapla(kok=kok, veri=[]))
        with open(os.path.join(kok, "cizim", "yazi", "Yazi.ttf"), "wb") as f:
            f.write(b"yazi tipi 2")
        ikinci = avan_secici._imza_hesapla(kok=kok, veri=[])
        self.assertNotEqual(ilk, ikinci)
        with mock.patch("importlib.metadata.version", return_value="999.0"):
            self.assertNotEqual(ikinci, avan_secici._imza_hesapla(kok=kok, veri=[]))

    def test_programin_yazi_tipi_kapsanir(self):
        """Çizimin yazı ölçüsünün yazı tipi ( cizim/pdf — uslup.YAZI_DOSYASI ) imza klasörlerinde ve
        türlerinde:  taşınırsa ya da türü değişirse bu test kırılır."""
        from cizim import uslup

        yol = os.path.relpath(uslup.YAZI_DOSYASI, KOK)
        self.assertIn(yol.split(os.sep)[0], avan_secici._IMZA_KLASORLERI, yol)
        self.assertTrue(yol.endswith(avan_secici._IMZA_TURLERI), yol)

    def test_imza_acilista_hesaplanir(self):
        """İmza modül yüklenirken hesaplanır:  sonradan dosya okumaz ( güncelleme dosyaları yerinde
        değiştirirken eski işçi eski koduyla bulduğu sonucu yeni imzayla yazamasın )."""
        with mock.patch("builtins.open", side_effect=AssertionError("dosya okundu")):
            self.assertEqual(avan_secici._kod_imzasi(), avan_secici._KOD_IMZASI)


class PaketinAramasi(unittest.TestCase):
    """17 Kas:  "Projeyi indir" bırakılınca ( bağlantı kapandı ) paketin asansör araması durur."""

    def test_aranacaklar_arama_yapmaz(self):
        """Paketin "henüz aranmadı" sorusu ( /api/avan/aranacaklar ):  arama yapmadan, önbellekte
        sonucu olmayan asansörleri söyler;  mimarisi eksik olan aranmaz ( anında "eksik" )."""
        from testler.test_avan_cizim_ucu import govde, kart

        avan_secici._ONBELLEK.clear()
        t = PAKETLER[(630, True)]["asansor"]
        eksik = kart(t)
        del eksik["kuyu_dibi_kotu"]
        g = govde(kart(t))
        g["girdiler"]["asansorler"] = [kart(t), eksik]
        with mock.patch.object(care_uclari, "girdi_durumu", side_effect=AssertionError("arama yapıldı")):
            self.assertEqual(avan_cizim_uclari.api_avan_aranacaklar(g), {"aranacaklar": [0]})
        with avan_secici.korumali():
            from uclar import avan_cizimi

            okunan, _h = avan_uclari.avan_girdisi(g)
            self.assertEqual(avan_cizimi.secim(okunan, 0)["durum"], "uygun")
        with mock.patch.object(care_uclari, "girdi_durumu", side_effect=AssertionError("arama yapıldı")):
            self.assertEqual(avan_cizim_uclari.api_avan_aranacaklar(g), {"aranacaklar": []})

    def test_birakilan_paket_durur(self):
        from testler.test_avan_cizim_ucu import govde, kart

        avan_secici._ONBELLEK.clear()
        t = PAKETLER[(630, True)]["asansor"]
        #  ~28 sınamalık kuyu;  avan hesabı eksiksiz ( eksik avanla paket seçici koşmadan reddedilir )
        g = govde(
            kart(
                t,
                kuyu_genisligi="1650",
                kuyu_derinligi="2300",
                kabin_boyu="1400",
                kabin_genisligi="1100",
                eta="0,85",
            )
        )
        g["girdiler"]["ortak"].update(temel_a="20", temel_b="15")
        veri = {"girdiler": {"avan": g["girdiler"]}, "kapak": {"project_title": "Bırakılan"}}

        class Kapandi:
            headers = {}

            async def is_disconnected(self):
                return True

        t0 = time.monotonic()
        r = asyncio.run(avan_uclari.indir_proje_dwg_ucu(Kapandi(), veri))
        self.assertLess(time.monotonic() - t0, 15)
        self.assertIn("bırakıldı", json.loads(r.body)["hata"])
        self.assertEqual(len(avan_secici._ONBELLEK), 0)


if __name__ == "__main__":
    unittest.main()

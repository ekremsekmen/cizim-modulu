"""AVAN SEÇİCİSİ ( uclar/avan_secici — 12 Kas, kullanıcı:  "avan projesine de çizim;  elde
yalnız mimari var, buraya en doğru asansör" ).  Sözleşmesi:

  · "uygun" dönen istek uygulamanın kendi uçlarından TEMİZ çıkar ( çizim sorunsuz;  hesabın
    düşen bölümü varsa yalnız seçicinin "acik_bolumler"de söylediği ÜRÜN bölümleri — avanı
    bağlayan bölümler hep uygun ) — seçicinin kendi sınamasına güvenilmez, ayrı yoldan sorulur.
  · Mimarın verdikleri ( kuyu, kotlar, yük, hız ) istekte AYNEN durur;  kabin paketinkidir.
  · Sığmayan kuyuda asansör dönmez:  ya mimardan istenecek ölçü ( o ölçüyle temiz ) ya da sebep.
"""

import copy
import json
import unittest

from cizim import katlar
from uclar import avan_secici, cizim_uclari, uygulama_uclari

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
        """Geniş kuyuda korkuluk gerekir, taslağın kuyu üstü yetmez:  asansör "uygun" dönmez;
        mimardan istenecek kuyu tavanı kotu döner ve o kotla temizdir."""
        t = PAKETLER[(630, True)]
        m = mimari(t, kuyu_genisligi=int(t["asansor"]["kuyu_genisligi"]) + 300)
        r = avan_secici.sec(m)
        self.assertEqual(r["durum"], "gereken", r)
        self.assertEqual([g["anahtar"] for g in r["gereken"]], ["kuyu_tavani_kotu"])
        (g,) = r["gereken"]
        self.assertEqual(g["eski"], m["kuyu_tavani_kotu"])
        eski, _h = katlar.kot_oku(g["eski"])
        yeni, hata = katlar.kot_oku(g["yeni"])
        self.assertIsNone(hata)
        self.assertGreater(yeni, eski)
        self.assertTrue(g["sebep"])
        #  İstenen kotla seçici "uygun" der
        r2 = avan_secici.sec({**m, "kuyu_tavani_kotu": g["yeni"]})
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


if __name__ == "__main__":
    unittest.main()

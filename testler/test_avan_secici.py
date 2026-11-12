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
        self.assertEqual(len(PAKETLER), 10)
        for t in PAKETLER.values():
            with self.subTest(t["kimlik"]):
                m = mimari(t)
                r = avan_secici.sec(m)
                self.assertEqual(r["durum"], "uygun", r)
                self.assertEqual(r["paket"], t["kimlik"])
                self.assertEqual(r["acik_bolumler"], [])
                self.mimari_aynen(m, r["istek"])
                a = r["istek"]["asansorler"][0]
                self.assertEqual({k: a[k] for k in KABIN}, {k: t["asansor"][k] for k in KABIN})
                #  Kendi kuyusunda ürün araması yok:  tek sınamada bulunur
                self.assertEqual(r["sinama"], 1)

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
        #  Makine daireli 630:  2:1 kurulamıyor;  makine tipi beyanı ( dişlisiz ) kalabilir
        t = PAKETLER[(630, False)]
        m = mimari(t, aski_orani=2, makine_tipi="Dişlisiz")
        r = avan_secici.sec(m)
        self.assertEqual(r["durum"], "beyan", r)
        self.assertNotIn("istek", r)
        self.assertEqual(
            [(b["anahtar"], b["eski"], b["yeni"]) for b in r["beyan"]], [("aski_orani", "2", "1")]
        )
        r = avan_secici.sec({**m, **{b["anahtar"]: b["yeni"] for b in r["beyan"]}})
        self.assertEqual(r["durum"], "uygun", r)
        self.assertEqual(r["istek"]["asansorler"][0]["makine_tipi"], "Dişlisiz")
        self.temiz(r)

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
        #  Taslağı olmayan yük ( 450 kg — 6 kişi )
        self.assertEqual(avan_secici.sec(mimari(t, beyan_yuku=450))["durum"], "paket_yok")


if __name__ == "__main__":
    unittest.main()

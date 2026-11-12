"""AVAN ÇİZİMLERİNİN UCU ( /api/avan/cizimler — uclar/avan_cizim_uclari;  12 Kas ).
Gövde avan hesabınınki ( /api/avan );  asansörün mimarisi kartta.  Yanıt seçicinin
sonucu;  "uygun"da uygulamanın çizim yanıtı.  Çizim bulunamadıysa çizim YOKTUR."""

import json
import unittest

from uclar import avan_cizim_uclari, avan_secici

T630 = avan_secici.paketler()[(630, True)]["asansor"]
T800MD = avan_secici.paketler()[(800, False)]


def govde(kart, ortak=None, asansor=0):
    return {
        "girdiler": {"ortak": {"mk_yok": True, **(ortak or {})}, "asansorler": [kart], "sabitler": {}},
        "asansor": asansor,
    }


def kart(t, **degisen):
    """Avan kartı:  kapasite kişi ( Tablo-7 ), ölçüler ekranda yazıldığı gibi metin."""
    kisi = {"630": "8", "800": "10"}[t["beyan_yuku"]]
    k = {"kapasite": kisi, "V": "1", **{a: t[a] for a in avan_cizim_uclari.KART if a in t}}
    k.update(degisen)
    return k


def yanit(g):
    return json.loads(avan_cizim_uclari.api_avan_cizimler(g).body)


class AvanCizimUcu(unittest.TestCase):
    def test_uygun_kuyuda_cizimler(self):
        r = yanit(govde(kart(T630)))
        self.assertEqual(r["durum"], "uygun", r)
        self.assertEqual(r["paket"], "630")
        self.assertTrue(r["cizim"]["aktif"], r["cizim"].get("hata"))
        self.assertGreaterEqual(len(r["cizim"]["cizimler"]), 5)
        self.assertTrue(all("<svg" in c["svg"] for c in r["cizim"]["cizimler"]))
        #  Ürün bölümlerinin turuncu işareti avana gitmez
        self.assertNotIn("hesap_parcalari", r["cizim"])
        #  Mimarın verdikleri isteğe aynen geçti;  kabin Tablo-7 yükünün paketi
        a = r["istek"]["asansorler"][0]
        self.assertEqual((a["beyan_yuku"], a["kuyu_genisligi"], a["kuyu_derinligi"]), ("630", "2050", "1850"))
        self.assertEqual(a["kuyu_tavani_kotu"], T630["kuyu_tavani_kotu"])

    def test_makine_daireli(self):
        a, pg = T800MD["asansor"], T800MD["proje_geneli"]
        ortak = {"mk_yok": False, "mk_uzunluk": pg["mk_uzunluk"], "mk_genislik": pg["mk_genislik"]}
        r = yanit(govde(kart(a), ortak))
        self.assertEqual(r["durum"], "uygun", r)
        self.assertEqual(r["paket"], "800-md")
        self.assertEqual(r["istek"]["proje_geneli"]["mk_yok"], "false")
        self.assertTrue(r["cizim"]["aktif"])

    def test_gereken_cizim_dondurmez(self):
        """Geniş kuyuda kuyu üstü yetmez:  çizim de istek de dönmez, mimardan istenen döner."""
        r = yanit(govde(kart(T630, kuyu_genisligi="2350")))
        self.assertEqual(r["durum"], "gereken", r)
        self.assertEqual([g["anahtar"] for g in r["gereken"]], ["kuyu_tavani_kotu"])
        self.assertNotIn("cizim", r)
        self.assertNotIn("istek", r)

    def test_eksik_mimari(self):
        k = kart(T630)
        del k["kuyu_derinligi"], k["kuyu_dibi_kotu"]
        r = yanit(govde(k))
        self.assertEqual((r["durum"], r["eksik"]), ("eksik", ["kuyu_derinligi", "kuyu_dibi_kotu"]))

    def test_okunamayan_ve_olmayan_asansor(self):
        #  Belirsiz yazım ( "1.850" ) avan hesabındaki gibi durdurur
        r = yanit(govde(kart(T630, kuyu_derinligi="1.850")))
        self.assertEqual(r["durum"], "hata", r)
        self.assertIn("Kuyu derinliği", r["hata"])
        #  Kapasitesi yazılmamış kart ve olmayan sıra
        self.assertEqual(yanit(govde(kart(T630, kapasite="")))["durum"], "hata")
        self.assertEqual(yanit(govde(kart(T630), asansor=3))["durum"], "hata")

    def test_paketi_olmayan_kapasite(self):
        self.assertEqual(yanit(govde(kart(T630, kapasite="6")))["durum"], "paket_yok")


if __name__ == "__main__":
    unittest.main()

"""AVAN ÇİZİMLERİNİN UCU ( /api/avan/cizimler — uclar/avan_cizim_uclari;  12 Kas ).
Gövde avan hesabınınki ( /api/avan );  asansörün mimarisi kartta.  Yanıt seçicinin
sonucu;  "uygun"da uygulamanın çizim yanıtı.  Çizim bulunamadıysa çizim YOKTUR."""

import json
import re
import unittest

from cizim import avan_kipi, katlar, pafta
from motor.uygulama import uygulama_hesabi
from uclar import avan_cizim_uclari, avan_secici, cizim_uclari, uygulama_istegi

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


def yazilar(c):
    """Çizim yanıtının bütün SVG'lerindeki yazılar."""
    return {
        re.sub(r"<[^>]+>", "", t).strip()
        for x in c["cizimler"]
        for t in re.findall(r"<text[^>]*>(.*?)</text>", x["svg"], flags=re.S)
    }


class AvanCizimUcu(unittest.TestCase):
    def test_uygun_kuyuda_cizimler(self):
        r = yanit(govde(kart(T630)))
        self.assertEqual(r["durum"], "uygun", r)
        self.assertEqual(r["paket"], "630")
        self.assertTrue(r["cizim"]["aktif"], r["cizim"].get("hata"))
        self.assertGreaterEqual(len(r["cizim"]["cizimler"]), 5)
        self.assertTrue(all("<svg" in c["svg"] for c in r["cizim"]["cizimler"]))
        #  Ürün bölümlerinin turuncu işareti avana gitmez
        self.assertEqual(r["cizim"]["hesap_parcalari"], {})
        #  Mimarın verdikleri isteğe aynen geçti;  kabin Tablo-7 yükünün paketi
        a = r["istek"]["asansorler"][0]
        self.assertEqual((a["beyan_yuku"], a["kuyu_genisligi"], a["kuyu_derinligi"]), ("630", "2050", "1850"))
        self.assertEqual(a["kuyu_tavani_kotu"], T630["kuyu_tavani_kotu"])

    def test_urun_yazilari_avanda_yok(self):
        """Kullanıcı kararı ( 12 Kas ):  paftanın bilgi tablosunda seçicinin iç seçimleri
        ( motor, halat, ray profili ) yazmaz;  tahrikin çizimi ( kasnak düzenlemesi ) yok.
        Aynı istek uygulamadan sorulunca hepsi yerindedir ( avan kipi sızmaz )."""
        r = yanit(govde(kart(T630)))
        avan = yazilar(r["cizim"])
        uygulama = yazilar(json.loads(cizim_uclari.api_cizimler(r["istek"]).body))
        urun = re.compile(
            r"kW|konsol arası|kasnak ø|halat ø|\d × ø|KASNAK DÜZENLEMESİ|70 × 65 × 9|50 × 50 × 5"
        )
        self.assertEqual(sorted(t for t in avan if urun.search(t)), [])
        self.assertGreaterEqual(len({t for t in uygulama if urun.search(t)}), 5)
        self.assertIn(avan_kipi.NOT, avan)
        self.assertNotIn(avan_kipi.NOT, uygulama)
        #  Kalan satırlar aynı:  avan yalnız eksiltir ( + notu ve onun sıra numarası )
        self.assertEqual({t for t in avan - uygulama if "Dişlisiz" not in t}, {avan_kipi.NOT, "3."})
        self.assertFalse(avan_kipi.acik())

    def test_acik_urun_bolumu_isaretlenmez(self):
        """1250 kg ( Q elle ) 1,6 m/s:  tahrik yeteneği geçmiyor ( acik_bolumler );  avanın
        çiziminde hesap notu da turuncu işaret de yok."""
        t = avan_secici.paketler()[(1250, True)]["asansor"]
        n, h = 10, 2900
        k = {a: t[a] for a in avan_cizim_uclari.KART if a in t}
        k.update(
            Q_elle="1250",
            kapasite="16",
            V="1,6",
            durak_kotlari="; ".join(katlar.kot_metni(j * h) for j in range(n)),
            kuyu_dibi_kotu=katlar.kot_metni(-1800),
            kuyu_tavani_kotu=katlar.kot_metni((n - 1) * h + 4600),
        )
        r = yanit(govde(k))
        self.assertEqual((r["durum"], r["acik_bolumler"]), ("uygun", ["tahrik_yetenegi"]), r)
        self.assertEqual(r["cizim"]["hesap_parcalari"], {})
        self.assertEqual([t for t in yazilar(r["cizim"]) if "HESAP" in t or "UYGUN DEĞİL" in t], [])
        #  Uygulamada aynı istek notunu taşır
        u = json.loads(cizim_uclari.api_cizimler(r["istek"]).body)
        self.assertTrue([t for t in yazilar(u) if t.startswith("HESAP:")])

    def test_pafta_avan_kipinde(self):
        """Paftanın girdisi avan kipinde kurulunca:  kasnak düzenlemesi sırada yok, antette
        ray boş, hesap notu yok;  kip kapanınca aynı istek uygulamanın paftasıdır."""
        v = yanit(govde(kart(T630)))["istek"]

        def girdi():
            A, o = uygulama_istegi.asansor_girdileri(json.loads(json.dumps(v)))
            s = uygulama_hesabi.hesapla_coklu(A, o)
            ((g, hata),) = cizim_uclari.girdiler(v, A, o, s, "AVAN")
            self.assertEqual(hata, [])
            return g

        with avan_kipi.etkin():
            g = girdi()
        self.assertTrue(g["proje"]["avan"])
        self.assertNotIn("kasnak_duzeni", pafta.sira(g))
        self.assertEqual(pafta.antet_degerleri(g, [20])["ray"], "")
        self.assertEqual([ad for ad, *_ in pafta.cizim_listesi(g)], list(pafta.sira(g)))
        u = girdi()
        self.assertFalse(u["proje"]["avan"])
        self.assertIn("kasnak_duzeni", pafta.sira(u))
        self.assertTrue(pafta.antet_degerleri(u, [20])["ray"])

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

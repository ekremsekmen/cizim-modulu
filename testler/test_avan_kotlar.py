"""AVANDA KUYU YÜKSEKLİĞİ VE SEYİR KOTLARDAN ( 13 Kas — kullanıcı:  "Hk kotlardan
hesaplanmalı;  uygulama projesindeki kot tablosunun aynısı avanda da olmalı, kuyu
yüksekliği ve seyir buradan hesaplanmalı" ).  Sözleşme:

  · Kartta kot varsa Hk = kuyu tavanı kotu − kuyu dibi kotu;  elle yazılmış Hk OKUNMAZ.
    Hesap, aynı sayı elle yazılmış gibi çıkar ( yalnız kaynağı "KOTLARDAN" ).
  · Kartta hiç kot yoksa ( eski projeler ) elle Hk geçerlidir — sonuç değişmez.
  · Kullanılamayan kot ( okunamayan yazım, tavan dipten alçak … ) asansörü DURDURUR.
  · Avan çizimi aynı kotları okur:  hesap sayfası ile pafta aynı kuyuyu gösterir.
"""

import json
import unittest

from motor.avan import avan_hesabi
from uclar import avan_cizim_uclari, avan_secici, avan_uclari

T630 = avan_secici.paketler()[(630, True)]["asansor"]
KOTLAR = {k: T630[k] for k in ("durak_kotlari", "kuyu_dibi_kotu", "kuyu_tavani_kotu")}
HESAP = {"kapasite": "8", "V": "1", "kuyu_genisligi": "2050", "kabin_boyu": "1400"}
HESAP.update(kabin_genisligi="1100", eta="0,85")


def avan(kart, trafik=None):
    g = {"ortak": {"mk_yok": True}, "asansorler": [{**HESAP, **kart}], "sabitler": {}}
    if trafik:
        g["trafik"] = trafik
    return json.loads(avan_uclari.api_avan({"girdiler": g}).body)


def bolumler(r):
    return json.dumps(r["asansorler"][0]["bolumler"], ensure_ascii=False, sort_keys=True)


class KotTuretme(unittest.TestCase):
    def test_turetilenler(self):
        t, hata = avan_hesabi.kot_turetilenleri(
            {
                "durak_kotlari": "-3,00; ±0,00; +3,20; +6,40",
                "kuyu_dibi_kotu": "-4,60",
                "kuyu_tavani_kotu": "+10,25",
            }
        )
        self.assertEqual(hata, [])
        self.assertEqual((t["Hk"], t["seyir"], t["durak"]), (14.85, 9.4, 4))
        self.assertEqual((t["kuyu_dibi"], t["ust_bosluk"]), (1.6, 3.85))
        self.assertEqual(t["kaynak"], "KOTLARDAN  ·  +10,25 − ( -4,60 )")

    def test_kot_yoksa_none(self):
        self.assertEqual(avan_hesabi.kot_turetilenleri({"Hk": 20.8}), (None, []))
        self.assertEqual(avan_hesabi.kot_turetilenleri({"durak_kotlari": "  "}), (None, []))

    def test_yarim_kotlar(self):
        """Yalnız duraklar:  seyir var, kuyu yüksekliği yok ( elle Hk'ya DÖNÜLMEZ )."""
        t, hata = avan_hesabi.kot_turetilenleri({"durak_kotlari": "0; 3", "Hk": 20})
        self.assertEqual((hata, t["Hk"], t["seyir"], t["kuyu_dibi"]), ([], None, 3.0, None))

    def test_kullanilamayan_kotlar(self):
        for kart, parca in (
            ({"kuyu_dibi_kotu": "-1.600", "kuyu_tavani_kotu": "+19"}, "belirsiz yazım"),
            ({"kuyu_dibi_kotu": "abc", "kuyu_tavani_kotu": "+19"}, "Kuyu dibi kotu:  okunamadı"),
            ({"kuyu_dibi_kotu": "+5", "kuyu_tavani_kotu": "+3"}, "kuyu dibi kotundan"),
            ({**KOTLAR, "kuyu_dibi_kotu": "+1"}, "en alt durağın kotundan"),
            ({**KOTLAR, "kuyu_tavani_kotu": "+15"}, "en üst durağın kotundan"),
            ({**KOTLAR, "durak_kotlari": "0; x; 6"}, "Durak kotları"),
        ):
            with self.subTest(parca):
                t, hata = avan_hesabi.kot_turetilenleri(kart)
                self.assertIsNone(t)
                self.assertIn(parca, " | ".join(hata))


class AvanHesabiKotlardan(unittest.TestCase):
    def test_hk_kotlardan(self):
        """Kotlarla hesap = aynı sayı elle yazılmış hesap;  yalnız kaynak yazısı farklı."""
        k = avan(KOTLAR)
        self.assertIsNone(k.get("hata"))
        self.assertEqual(k["ozet"]["asansorler"][0]["Hk"], 20.8)
        b = k["kotlar"][0]
        self.assertEqual((b["Hk"], b["seyir"], b["durak"]), (20.8, 15.0, 6))
        e = avan({"Hk": "20,8"})
        kaynak = "KOTLARDAN  ·  +19,20 − ( -1,60 )"
        self.assertIn(kaynak, bolumler(k))
        self.assertEqual(bolumler(k).replace(f'"{kaynak}"', '"GİRİŞ"'), bolumler(e))
        self.assertEqual(k["proje_hukmu"], e["proje_hukmu"])

    def test_elle_hk_kot_varken_okunmaz(self):
        self.assertEqual(bolumler(avan({**KOTLAR, "Hk": "99"})), bolumler(avan(KOTLAR)))

    def test_eski_proje_elle_hk(self):
        """Kotsuz kart:  elle Hk ile hesap eskisi gibi;  kot bilgisi boş."""
        r = avan({"Hk": "20,8"})
        self.assertTrue(r["asansorler"][0]["aktif"])
        self.assertEqual(r["ozet"]["asansorler"][0]["Hk"], 20.8)
        self.assertEqual(
            {k: v for k, v in r["kotlar"][0].items() if k not in ("doseme", "doseme_kural", "adlar")},
            {"hata": []},
        )

    def test_kuyu_dibi_ya_da_tavani_eksik(self):
        r = avan({"durak_kotlari": KOTLAR["durak_kotlari"], "Hk": "20,8"})
        a = r["asansorler"][0]
        self.assertFalse(a["aktif"])
        self.assertIn("eksik : Kuyu dibi kotu, Kuyu tavanı kotu  ( kuyu yüksekliği kotlardan", a["uyari"])
        self.assertEqual(r["proje_hukmu"]["durum"], "durdu")

    def test_kullanilamayan_kot_durdurur(self):
        r = avan({**KOTLAR, "kuyu_tavani_kotu": "+15,00"})
        a = r["asansorler"][0]
        self.assertFalse(a["aktif"])
        self.assertIn("kotlar kullanılamıyor", a["uyari"])
        self.assertIn("en üst durağın kotundan", a["uyari"])
        self.assertEqual(r["proje_hukmu"]["durum"], "durdu")
        self.assertTrue(r["kotlar"][0]["hata"])

    def test_ekranin_kot_bilgisi(self):
        """Kot tablosunun sunucudan beklediği:  türetilenler, kuraldan kat adları, döşeme."""
        kart = {**KOTLAR, "durak_kotlari": "-3,00; ±0,00; +3,00", "kuyu_dibi_kotu": "-4,60"}
        b = avan(kart)["kotlar"][0]
        self.assertEqual((b["Hk"], b["seyir"], b["durak"], b["doseme"]), (23.8, 6.0, 3, 150))
        self.assertEqual(b["adlar"], {"adlar": ["-1", "0", "1"], "giris": 2, "ad_hatasi": []})

    def test_trafikle_durak_sayisi(self):
        """Trafiğin kat düzeni ( N kat + ana giriş + bodrum ) ile kartın durak sayısı
        tutmuyorsa uyarı ( engel değil );  tutuyorsa yok.  Pay kotların kendi seyrinden."""
        t = {"tip": "tek", "N": 5, "bodrum": 0, "h": 3, "adet": 1}
        t["asansorler"] = [{"P": 8, "V": 1, "toplam_seyahat": 15}]
        self.assertEqual(avan(KOTLAR, t)["uyarilar"], [])
        u = avan(KOTLAR, {**t, "N": 7})["uyarilar"]
        self.assertEqual(len(u), 1, u)
        self.assertIn("kartın kotlarında 6 durak var, trafik hesabının kat düzeni 8 durak veriyor", u[0])


class CizimAyniKotlar(unittest.TestCase):
    def test_hesap_ve_cizim_ayni_kuyu(self):
        """Avan hesabının Hk'sı = çizimin kuyusu ( kuyu dibi + seyir + son kat ), kat adları
        ve giriş katı çizime geçer."""
        kart = {**KOTLAR, "kuyu_derinligi": T630["kuyu_derinligi"], "durak_adlari": "B; Z; 1; 2; 3; 4"}
        kart["giris_duragi"] = "2"
        g = {"girdiler": {"ortak": {"mk_yok": True}, "asansorler": [{**HESAP, **kart}], "sabitler": {}}}
        hk = json.loads(avan_uclari.api_avan(g).body)["ozet"]["asansorler"][0]["Hk"]
        r = json.loads(avan_cizim_uclari.api_avan_cizimler({**g, "asansor": 0}).body)
        self.assertEqual(r["durum"], "uygun", r)
        a = r["istek"]["asansorler"][0]
        self.assertEqual({k: a[k] for k in KOTLAR}, KOTLAR)
        self.assertEqual((a["durak_adlari"], a["giris_duragi"]), ("B; Z; 1; 2; 3; 4", "2"))
        self.assertEqual(hk, 20.8)
        yazilar = " ".join(c["svg"] for c in r["cizim"]["cizimler"])
        self.assertIn("Z  ·  +3,00", yazilar)

    def test_tavan_dosemesi_kalinligi(self):
        """Tavan döşemesinin kalınlığı kartta girilir ( boşsa uygulamanın kuralı );  çizimin
        isteğine geçer, kot tablosunun "döşemenin üstü" satırı onu kullanır."""
        kart = {**KOTLAR, "kuyu_derinligi": T630["kuyu_derinligi"]}

        def sor(k):
            g = {"girdiler": {"ortak": {"mk_yok": True}, "asansorler": [{**HESAP, **k}], "sabitler": {}}}
            kot = json.loads(avan_uclari.api_avan(g).body)["kotlar"][0]
            return kot, json.loads(avan_cizim_uclari.api_avan_cizimler({**g, "asansor": 0}).body)

        kot, r = sor(kart)
        self.assertEqual((kot["doseme"], kot["doseme_kural"]), (150, 150))
        self.assertNotIn("tavan_dosemesi", r["istek"]["asansorler"][0])
        kot, r = sor({**kart, "tavan_dosemesi": "200"})
        self.assertEqual((kot["doseme"], kot["doseme_kural"]), (200, 150))
        self.assertEqual(r["durum"], "uygun", r)
        self.assertEqual(r["istek"]["asansorler"][0]["tavan_dosemesi"], "200")
        #  Hesap değişmez:  kuyu yüksekliği döşemenin ALTINA kadardır
        self.assertEqual(kot["Hk"], 20.8)


if __name__ == "__main__":
    unittest.main()

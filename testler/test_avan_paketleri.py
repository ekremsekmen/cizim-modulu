"""YALNIZ AVANIN HAZIR ASANSÖRLERİ ( hesap/uclar/avan_paketleri.json — 14 Kas;  450 · 1600 ·
2000 · 2500 kg, makine dairesiz ve daireli ).  Açılışın taslağı değiller ( testler/test_taslaklar
onlara bakar );  seçici ( uclar/avan_secici ) avan çizimine bunlardan başlar.

  · Çizim temiz;  hesap çalışır;  avanı bağlayan bölümler ( sığınma alanları, kabin alanı,
    tamponlar ) uygun.
  · Düşen bölümler dosyada yazanlardır ( "acik_bolumler" — yalnız ürün bölümleri ):  450 kg'da
    hiç yok;  1600 kg ve üstünde tahrik / halat açık kalır ( kullanıcı, 14 Kas:  "çıksın" ).
  · Seçici her birini kendi kuyusunda "uygun" bulur.
"""

import copy
import json
import os
import unittest

from uclar import avan_secici, cizim_uclari, uygulama_uclari

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(KOK, "hesap", "uclar", "avan_paketleri.json"), encoding="utf-8") as f:
    PAKETLER = json.load(f)
YUKLER = ["450", "1600", "2000", "2500"]


def istek(t):
    return {
        "asansorler": [dict(t["asansor"])],
        "proje_geneli": dict(t["proje_geneli"]),
        "sabitler": {},
        "asansor": 0,
    }


class AvanPaketleri(unittest.TestCase):
    def test_liste(self):
        self.assertEqual([t["kimlik"] for t in PAKETLER], YUKLER + [f"{q}-md" for q in YUKLER])
        for t in PAKETLER:
            with self.subTest(t["kimlik"]):
                a = t["asansor"]
                md = t["kimlik"].endswith("-md")
                self.assertEqual(a["beyan_yuku"], t["kimlik"].removesuffix("-md"))
                self.assertEqual(t["proje_geneli"].get("mk_yok"), "false" if md else "true")
                self.assertTrue(all(isinstance(v, str) for v in (*a.values(), *t["proje_geneli"].values())))
                #  Açılışın taslaklarıyla aynı yükte paket olmaz ( seçici yükle arar )
                self.assertEqual(avan_secici.paketler()[(int(a["beyan_yuku"]), not md)], t)
        self.assertEqual(len(avan_secici.paketler()), 18)

    def test_cizim_temiz_avan_bolumleri_uygun(self):
        for t in PAKETLER:
            with self.subTest(t["kimlik"]):
                h = json.loads(uygulama_uclari.api_uygulama_coklu(istek(t)).body)
                self.assertTrue(h["aktif"], h.get("hata"))
                dusen = sorted(
                    b["kimlik"]
                    for b in h["asansorler"][0]["bolumler"]
                    if (b.get("sonuc") or {}).get("uygun") is False
                )
                self.assertEqual(dusen, t["acik_bolumler"])
                self.assertFalse(set(dusen) & avan_secici.AVAN_BOLUMLERI)
                if t["asansor"]["beyan_yuku"] == "450":
                    self.assertEqual(dusen, [])
                c = json.loads(cizim_uclari.api_cizimler(copy.deepcopy(istek(t))).body)
                self.assertTrue(c["aktif"], c.get("hata"))
                self.assertFalse(c.get("hata"))

    def test_secici_kendi_kuyusunda_uygun(self):
        for t in PAKETLER:
            with self.subTest(t["kimlik"]):
                a = t["asansor"]
                m = {k: a[k] for k in ("beyan_yuku", "beyan_hizi", *avan_secici.MIMARI) if k in a}
                m["mk_yok"] = t["proje_geneli"]["mk_yok"] == "true"
                r = avan_secici.sec(m)
                self.assertEqual(r["durum"], "uygun", r)
                self.assertFalse(set(r["acik_bolumler"]) & avan_secici.AVAN_BOLUMLERI)
                #  Seçici ürünü de arar:  açık kalan, dosyada yazandan fazla olamaz
                self.assertLessEqual(set(r["acik_bolumler"]), set(t["acik_bolumler"]))


if __name__ == "__main__":
    unittest.main()

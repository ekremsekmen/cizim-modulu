"""TASLAK PROJELER ( on-yuz/src/lib/taslaklar.json — açılışın sağında;  3 Kas, kullanıcı:
"her şeyi uygun tertemiz projeler taslak halinde olsun";  her yük makine dairesiz ve daireli ).  Ön yüzün göndereceği
metinlerle:  hesabın hiçbir bölümü uygun değil ya da eksik değil ( 9. bölüm hükümsüz
bilgidir ), uyarı yok, çizim temiz,
paftanın bütün çizimlerinde kalite kapısı 0 ( test_kalite.kapi_bulgulari ).  Taslak
değişirse bu test birlikte koşar;  açılıştaki "Uygun" rozetinin güvencesi budur.
Kaynaklar ve seçim kuralı:  on-yuz/src/lib/taslak.ts."""

import copy
import json
import os
import unittest

from cizim import pafta
from motor.uygulama import uygulama_hesabi
from testler.test_kalite import kapi_bulgulari
from uclar import cizim_uclari, uygulama_istegi, uygulama_uclari

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(KOK, "on-yuz", "src", "lib", "taslaklar.json"), encoding="utf-8") as f:
    TASLAKLAR = json.load(f)


def istek(t):
    return {
        "asansorler": [dict(t["asansor"])],
        "proje_geneli": dict(t["proje_geneli"]),
        "sabitler": {},
        "asansor": 0,
    }


class Taslaklar(unittest.TestCase):
    def test_liste(self):
        yukler = ["630", "800", "1000", "1250", "1275"]
        self.assertEqual([t["kimlik"] for t in TASLAKLAR], yukler + [f"{q}-md" for q in yukler])
        for t in TASLAKLAR:
            with self.subTest(t["kimlik"]):
                a = t["asansor"]
                self.assertEqual(a["beyan_yuku"], t["kimlik"].removesuffix("-md"))
                self.assertTrue(all(isinstance(v, str) for v in (*a.values(), *t["proje_geneli"].values())))
                #  Her yük makine dairesiz ve makine daireli ( 3 Kas )
                md = t["kimlik"].endswith("-md")
                self.assertEqual(t["duzen"], "Makine daireli" if md else "Makine dairesiz")
                self.assertEqual(t["proje_geneli"].get("mk_yok"), "false" if md else "true")
                #  Özetteki askı ve makine taslağın kendisi ( 3 Kas:  makine dairelide 1:1 dişli
                #  yaygın — 1250 ve 1275 2:1, taslak_secici )
                aski = f"{a.get('aski_orani', '2')}:1 {a.get('makine_tipi', 'Dişlisiz').lower()}"
                self.assertTrue(t["ozet"].endswith(aski), (t["ozet"], aski))
                self.assertEqual(float(a["beyan_hizi"]), 1.0)
                self.assertEqual(len(a["durak_kotlari"].split(";")), 6)
                #  Kişi sayısı ( TS EN 81-20 m.5.4.2.3:  Q / 75, aşağı )
                self.assertIn(f"{int(a['beyan_yuku']) // 75} kişi", t["ad"])

    def test_hesap_her_bolumu_uygun(self):
        for t in TASLAKLAR:
            with self.subTest(t["kimlik"]):
                h = json.loads(uygulama_uclari.api_uygulama_coklu(istek(t)).body)
                self.assertTrue(h["aktif"], h.get("hata"))
                a = h["asansorler"][0]
                #  Uygun değil yok, sonucu olmayan ( HESAP EKSİK ) yok;  hükümsüz bilgi bölümü
                #  ( 9 — kuyu tabanının yükleri:  sayı verir, hüküm vermez ) kalır
                kotu = [
                    b["baslik"]
                    for b in a["bolumler"]
                    if b.get("sonuc") is None or b["sonuc"].get("uygun") is False
                ]
                self.assertEqual(kotu, [])
                self.assertEqual(a["uyarilar"], [])
                self.assertEqual(
                    [
                        b["baslik"]
                        for b in h.get("proje_geneli") or []
                        if b.get("sonuc") and b["sonuc"].get("uygun") is False
                    ],
                    [],
                )

    def test_cizim_temiz(self):
        for t in TASLAKLAR:
            with self.subTest(t["kimlik"]):
                c = json.loads(cizim_uclari.api_cizimler(istek(t)).body)
                self.assertTrue(c["aktif"], c.get("hata"))
                self.assertFalse(c.get("hata"))
                v = istek(t)
                asansorler, ortak = uygulama_istegi.asansor_girdileri(copy.deepcopy(v))
                s = uygulama_hesabi.hesapla_coklu(asansorler, ortak)
                ((g, hata),) = cizim_uclari.girdiler(v, asansorler, ortak, s, "TASLAK")
                self.assertEqual(hata, [])
                for ad, _b, olcek, e in pafta.cizim_listesi(g):
                    bulgu = {k: x for k, x in kapi_bulgulari(e, olcek).items() if x}
                    self.assertEqual(bulgu, {}, ad)


if __name__ == "__main__":
    unittest.main()

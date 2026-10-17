"""İSTEK İÇİ ÖNBELLEK ( cizim/istek_onbellegi.py ) — yerleşim bir istekte bir
kez kurulur;  çıktı önbelleksizle birebir aynıdır ( 17 Eki — web hızı:  çizim
isteği 644 → 274 ms )."""

import json
import os
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from cizim import istek_onbellegi
from cizim import izli
from testler import test_yerlesim_saglamligi
from uclar import cizim_uclari


class _Sayac:
    def __init__(self):
        self.n = 0

        @istek_onbellegi.sakla
        def kur(g, ek=None):
            self.n += 1
            return {"liste": [dict(g)], "ek": ek}

        self.kur = kur


class Kurallar(unittest.TestCase):
    def test_etkin_istek_yoksa_her_seferinde_kurar(self):
        s = _Sayac()
        s.kur({"a": 1})
        s.kur({"a": 1})
        self.assertEqual(s.n, 2)

    def test_istekte_bir_kez_kurar_ek_girdi_ayri(self):
        s = _Sayac()
        with istek_onbellegi.etkin():
            s.kur({"a": 1})
            s.kur({"a": 1})
            s.kur({"a": 1}, ek=2)
        self.assertEqual(s.n, 2)

    def test_her_cagirana_kendi_kopyasi(self):
        """Yazı yerleştirici yerleşimin listesini değiştirir:  sonraki çağıran
        bunu görmemeli ( kabin üstü `taban` )."""
        s = _Sayac()
        with istek_onbellegi.etkin():
            ilk = s.kur({"a": 1})
            ilk["liste"][0]["a"] = 99
            ilk["liste"].append("bozuk")
            ikinci = s.kur({"a": 1})
        self.assertEqual(ikinci, {"liste": [{"a": 1}], "ek": None})
        self.assertEqual(s.n, 1)

    def test_anahtar_icerik_kimlik_degil(self):
        """Köprü regülatörün yerini ararken aynı g'yi yerinde değiştirip
        yeniden kurar:  değişen g yeniden kurulur."""
        s = _Sayac()
        g = {"kuyu_dibi": {"regulator_kaciklik": 100}}
        with istek_onbellegi.etkin():
            s.kur(g)
            g["kuyu_dibi"]["regulator_kaciklik"] = 200
            r = s.kur(g)
        self.assertEqual(s.n, 2)
        self.assertEqual(r["liste"][0]["kuyu_dibi"]["regulator_kaciklik"], 200)

    def test_istekler_arasi_paylasilmaz(self):
        s = _Sayac()
        with istek_onbellegi.etkin():
            s.kur({"a": 1})
        with istek_onbellegi.etkin():
            s.kur({"a": 1})
        self.assertEqual(s.n, 2)

    def test_iz_surerken_devre_disi(self):
        """İzli sayı float'tır, JSON'da düz sayıya döner:  iz sürerken önbellek
        kapalı olmalı ( ölçüye tıklamanın türevi )."""
        s = _Sayac()
        with istek_onbellegi.etkin():
            s.kur({"a": 1.0})
            with izli.izleme():
                r = s.kur({"a": izli.girdi(1.0, "a")})
        self.assertEqual(s.n, 2)
        self.assertEqual(izli.turev(r["liste"][0]["a"]), {"a": 1.0})

    def test_json_olmayan_girdi_onbellege_girmez(self):
        s = _Sayac()
        with istek_onbellegi.etkin():
            s.kur({"a": object()})
            s.kur({"a": object()})
        self.assertEqual(s.n, 2)


class CizimYaniti(unittest.TestCase):
    def test_onbellekli_ve_onbelleksiz_ayni(self):
        """Çizim isteğinin yanıtı önbellekle birebir aynı:  makine dairesiz,
        makine daireli ve elle kaydırılmış makine dairesi."""
        oda = test_yerlesim_saglamligi.standart_istek(630, False, "Sağ", tabliye_yuksekligi=600)
        oda["proje_geneli"].update(md_kapi_duvar="Ön", md_pano_duvar="Sol", md_yukseklik=3700)
        for ad, v in (
            ("dairesiz", test_yerlesim_saglamligi.standart_istek(1000, True, "Sağ")),
            ("daireli", test_yerlesim_saglamligi.standart_istek(1275, False, "Sol")),
            ("oda", oda),
        ):
            with self.subTest(ad):
                onbellekli = cizim_uclari.api_cizimler(v).body
                onbelleksiz = cizim_uclari.cizimler_yaniti(v).body
                self.assertTrue(json.loads(onbellekli)["aktif"], json.loads(onbellekli).get("hata"))
                self.assertEqual(onbellekli, onbelleksiz)


if __name__ == "__main__":
    unittest.main()

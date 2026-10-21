"""İSTEK İÇİ ÖNBELLEK ( cizim/istek_onbellegi.py ) — yerleşim bir istekte bir
kez kurulur;  çıktı önbelleksizle birebir aynıdır ( 17 Eki — web hızı:  çizim
isteği 644 → 274 ms )."""

import json
import os
import unittest
from unittest import mock

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from cizim import istek_onbellegi
from cizim import izli
from cizim import sabitler
from testler import test_yerlesim_saglamligi
from uclar import care_uclari
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

    def test_iz_surerken_duz_ile_karismaz(self):
        """İzli sayı float'tır, JSON'da düz sayıya döner:  iz sürerken anahtar
        türevi yazar — düz girdinin sonucu izliye verilmez ( ölçüye tıklamanın
        türevi )."""
        s = _Sayac()
        with istek_onbellegi.etkin():
            s.kur({"a": 1.0})
            with izli.izleme():
                r = s.kur({"a": izli.girdi(1.0, "a")})
        self.assertEqual(s.n, 2)
        self.assertEqual(izli.turev(r["liste"][0]["a"]), {"a": 1.0})

    def test_iz_surerken_ayni_izli_girdi_bir_kez_kurulur(self):
        """Çare bulucu:  makine dairesinin yerleşimi izli sayılarla dört kez
        kuruluyordu.  Aynı izli girdi ( değer + türev ) bir kez;  türevi ayrı
        aynı değer ayrı;  iz sürerken düz girdi de iz sürülmeyenden ayrı."""
        s = _Sayac()
        with istek_onbellegi.etkin():
            s.kur({"a": 2.0})
            with izli.izleme():
                ilk = s.kur({"a": izli.girdi(2.0, "a")})
                ikinci = s.kur({"a": izli.girdi(2.0, "a")})
                baska = s.kur({"a": izli.girdi(2.0, "b")})
                s.kur({"a": 2.0})
        self.assertEqual(s.n, 4)
        self.assertEqual(izli.turev(ikinci["liste"][0]["a"]), {"a": 1.0})
        self.assertEqual(izli.turev(baska["liste"][0]["a"]), {"b": 1.0})
        self.assertIsNot(ilk["liste"][0], ikinci["liste"][0])

    def test_json_olmayan_girdi_onbellege_girmez(self):
        s = _Sayac()
        with istek_onbellegi.etkin():
            s.kur({"a": object()})
            s.kur({"a": object()})
        self.assertEqual(s.n, 2)


class _Yerlesim:
    """Yerleşimlerin imzası:  ( g , cizim_sabitleri ) — sabitler g'den ya da ayrı."""

    def __init__(self):
        self.n = 0

        @istek_onbellegi.sakla
        def yerlesim(g, cizim_sabitleri=None):
            self.n += 1
            S = sabitler.sabitler(g.get("_cizim_sabitleri") if cizim_sabitleri is None else cizim_sabitleri)
            return {"bina_duvari": S["bina_duvari"], "a": g["a"]}

        self.yerlesim = yerlesim


class Sabitler(unittest.TestCase):
    """Anahtar sabitlerin ETKİN değerleridir ( 21 Eki ):  aynı yerleşim sabitleri
    ayrı argümanla ya da g'nin içinden, ezmeleri dolu ya da boş alıyordu ve her
    biri baştan kuruluyordu."""

    def test_ayni_etkin_sabitler_bir_kez_kurulur(self):
        y, bos = _Yerlesim(), {"a": 1, "_cizim_sabitleri": {}}
        dolu = dict(bos, _cizim_sabitleri=dict(sabitler.SABIT))
        with istek_onbellegi.etkin():
            r = [
                y.yerlesim(bos),
                y.yerlesim(dolu),
                y.yerlesim(bos, sabitler.sabitler({})),
                y.yerlesim(dolu, cizim_sabitleri=sabitler.sabitler(None)),
            ]
        self.assertEqual(y.n, 1)
        self.assertEqual(len({json.dumps(x, sort_keys=True) for x in r}), 1)

    def test_farkli_sabitler_ayri_kurulur(self):
        y, g = _Yerlesim(), {"a": 1, "_cizim_sabitleri": {}}
        with istek_onbellegi.etkin():
            y.yerlesim(g)
            r = y.yerlesim(dict(g, _cizim_sabitleri={"bina_duvari": 200}))
            #  Ayrı argüman g'ninkinden farklı:  ikisi de anahtarda kalır
            s = y.yerlesim(g, sabitler.sabitler({"bina_duvari": 300}))
        self.assertEqual(y.n, 3)
        self.assertEqual((r["bina_duvari"], s["bina_duvari"]), (200, 300))

    def test_duz_arama_ayri_kurulur(self):
        """Makine dairesinin yer araması düz arama kipinde başka sonuç verir."""
        y, g = _Yerlesim(), {"a": 1, "_cizim_sabitleri": {}}
        with istek_onbellegi.etkin(), izli.izleme():
            y.yerlesim(g)
            with izli.duz_arama():
                y.yerlesim(g)
        self.assertEqual(y.n, 2)

    def test_okunan_sabitler_kaydedilirken_atlanir(self):
        """Ölçü kaynağı hangi sabitlerin okunduğunu kaydeder:  önbellekten dönen
        sonuç sabitleri okumadan gelirdi."""
        y, g = _Yerlesim(), {"a": 1, "_cizim_sabitleri": {}}
        with istek_onbellegi.etkin():
            y.yerlesim(g)
            with sabitler.okunanlar() as okunan:
                y.yerlesim(g)
        self.assertEqual(y.n, 2)
        self.assertIn("bina_duvari", okunan)


class Denetim(unittest.TestCase):
    def test_atlanan_bagimlilik_yakalanir(self):
        """Denetim kipi:  isabet baştan kurulanla karşılaştırılır — anahtarın
        görmediği bir şeye bağlı sonuç yakalanır."""
        dis = {"x": 1}

        @istek_onbellegi.sakla
        def kur(g):
            return {"x": dis["x"]}

        with mock.patch.object(istek_onbellegi, "DENETIM", True), istek_onbellegi.etkin():
            kur({"a": 1})
            kur({"a": 1})  # aynı:  geçer
            dis["x"] = 2
            with self.assertRaises(istek_onbellegi.Tutarsiz):
                kur({"a": 1})

    def test_cizim_ve_care_isabetleri_tutarli(self):
        """Gerçek istekler denetim kipinde:  çizim yanıtı ve çare bulucunun
        sınamaları — her isabet baştan kurulanla aynı."""
        from testler import test_care

        with mock.patch.object(istek_onbellegi, "DENETIM", True):
            for v in (
                test_yerlesim_saglamligi.standart_istek(1000, True, "Sağ"),
                test_yerlesim_saglamligi.standart_istek(1275, False, "Sol"),
            ):
                self.assertTrue(json.loads(cizim_uclari.api_cizimler(v).body)["aktif"])
            for vaka in (("md", "son_kat_yuksekligi", "3200"), ("ornek", "kuyu_dibi", "1300")):
                veri, _onceki = test_care._vaka(*vaka)
                care_uclari._durum(veri, 0)


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

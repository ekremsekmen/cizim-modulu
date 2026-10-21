"""Yayın öncesi SON BUG DENETİMİ ( 21 Eki ) — bulanık tarama, uç değer taraması ve
kalın duvar taraması ( cikti/araclar/son_denetim/ ) bulguları.

Başka dosyalarda kilitlenenler:  sayısal seçimin tavanı ve yanlış türdeki seçim
değeri ( test_web_korumalari ), kesişme denetiminin biçimli parçası ve dar
döşeme ( test_araclar ), klemens kutusu ( test_arka_aski ), yerleşime bağlı
seçenek ( ön yüz:  lib/proje.test.ts ).
"""

import copy
import json
import unittest

import hesap_girdi
from araclar import tarama
from cizim import cizimler
from testler import test_yerlesim_saglamligi
from uclar import cizim_uclari


def _girdi(v):
    g, _A, hata = test_yerlesim_saglamligi.duzen_girdisi(copy.deepcopy(v))
    return g, hata


class KalinDuvar(unittest.TestCase):
    """Girdi taraması düzenleri 150 mm duvarla koşar.  400 mm'de kuyu üstünde
    makinenin yanındaki HALAT BAĞLANTISI yazısı makinenin, şasenin ve duvarın
    üstünde kalıyordu:  son adımın ( geometri.etiketleri_ayir ) uzak araması
    yalnız hiçbir parçanın içinde olmayan yeri kabul ediyordu, kuyunun iç kutusu
    da parça sayıldığı için tek kaçış kuyunun dışıydı — duvar ~370 mm'yi geçince
    orası da duvara değdi.  Şimdi yazı kuyunun içinde, oklu."""

    def test_kuyu_ustu_yazilari_kalin_duvarda_temiz(self):
        for Q, yer in ((1000, "Sağ"), (630, "Sol")):
            for kalinlik in (400, 600):
                with self.subTest(Q=Q, yer=yer, kalinlik=kalinlik):
                    v = test_yerlesim_saglamligi.standart_istek(Q, True, yer, kuyu_duvar_kalinligi=kalinlik)
                    g, _A, hata = test_yerlesim_saglamligi.duzen_girdisi(copy.deepcopy(v))
                    self.assertEqual(hata, [])
                    self.assertEqual([s for s in tarama.denetle(g) if s.startswith("kuyu_ustu")], [])


class DarOda(unittest.TestCase):
    """Makine dairesi kuyudan dar ( 2.600 < 2.700 ):  zincirin kimliksiz ortası
    dış sıradaki oda ölçüsüyle aynı aralıktı, tekrar ayıklayıcı onu silip zinciri
    koparıyordu ( yalnız 50 | 50 kalıyordu ).  Şimdi iç sıra 50 | MRW | 50,
    dış sıra SW."""

    def test_zincir_kapanir_oda_ve_kuyu_olculu(self):
        v = test_yerlesim_saglamligi.standart_istek(
            1600,
            False,
            "Arka",
            aski_duzeni="Kabin üstü",
            kat_kapisi_tipi="Otomatik Merkezi 4 Kanat",
            son_kat_yuksekligi=5000,
            kuyu_dibi=1700,
            siginma_tipi_dip="Yatarak",
            kabin_ray_arasi=1550,
            agirlik_ray_duvar=200,
        )
        v["asansorler"][0].update(kuyu_genisligi=2700, kuyu_derinligi=3100)
        v["proje_geneli"].update(mk_uzunluk=4400, mk_genislik=2600)
        g, hata = _girdi(v)
        self.assertEqual(hata, [])
        self.assertEqual([s for s in tarama.denetle(g) if s.startswith("makine_dairesi")], [])
        e = cizimler.CIZIMLER["makine_dairesi"][1](g)
        metin = {el["metin"] for el in e if el["tip"] == "olcu"}
        self.assertTrue({"MRW2600", "SW2700"} <= metin, metin)


class KabinUstuArkaAgirlik(unittest.TestCase):
    """Arkadaki ağırlık, dar kuyu ( 2.150 ):  sığınma alanı ile tavanın arka
    kenarı arasındaki "70"in yazısı zincirin ucundan taşıp ağırlığın patenine
    biniyordu — sığınma ölçülerinin yer seçimi ağırlığı engel saymıyordu."""

    def test_yazi_agirliga_binmez(self):
        v = test_yerlesim_saglamligi.standart_istek(
            800,
            True,
            "Arka",
            aski_duzeni="Kabin üstü",
            kat_kapisi_tipi="Manuel Sol",
            kapi_montaji="Duvar boşluğuna",
            beyan_hizi=1.6,
            son_kat_yuksekligi=5000,
            kuyu_dibi=1300,
            makine_raya_biniyor="Bina yapısına",
            kabin_ray_arasi=1600,
        )
        v["asansorler"][0].update(kuyu_genisligi=2150, kuyu_derinligi=2100)
        g, hata = _girdi(v)
        self.assertEqual(hata, [])
        self.assertEqual([s for s in tarama.denetle(g) if s.startswith("kabin_ustu")], [])


class OdaKapisi(unittest.TestCase):
    """Odanın arka duvarı kuyunun üstündeyse kapı tabliyenin üstünden başlar:
    1.500'lük tabliyede 2.425'lik kapı 3.700'lük odanın tavanını aşıyor, yan
    kesitte çatının betonuna giriyordu ( 63444-2 ).  Kapı tavana sığmalı."""

    def _veri(self, kapi):
        pg = dict(hesap_girdi.ORTAK_MD, md_kapi_yukseklik=kapi, md_y=-1450, mk_uzunluk=3350)
        return {
            "asansorler": [dict(hesap_girdi.ASANSOR_MD)],
            "proje_geneli": pg,
            "sabitler": dict(hesap_girdi.SABITLER),
        }

    def test_tavana_sigmayan_kapi_reddedilir(self):
        yanit = json.loads(cizim_uclari.api_cizimler(self._veri(2500)).body)
        self.assertFalse(yanit["aktif"])
        self.assertIn("Makine dairesi kapısı ( 2500 mm ) tavana sığmıyor", yanit["hata"][0])
        self.assertIn("tavana 2300 mm var", yanit["hata"][0])

    def test_sigan_kapi_betona_girmez(self):
        v = self._veri(2300)
        self.assertTrue(json.loads(cizim_uclari.api_cizimler(v).body)["aktif"])
        g, _hata = _girdi(v)
        self.assertEqual([s for s in tarama.denetle(g) if " R1 " in s or " R2 " in s or " R3 " in s], [])


if __name__ == "__main__":
    unittest.main()

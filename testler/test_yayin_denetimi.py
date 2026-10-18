"""Yayın öncesi dış denetimin ( 16 Eki ) çizim bulguları.

1.  Karşı ağırlık derinliği çerçevenin iki kalınlığından küçükken plan ve
    kesit eksi enli dolgu ve kasnak çiziyor, paket yine iniyordu.
3.  175 – 190 mm'lik merdivende MERDİVEN yazısı ağırlık rayının ayağını
    örtüyor, oradaki yük kutusu yer bulamıyor, bütün çizim duruyordu.

( 2. bulgu ekrandadır:  bağlantı kopunca çizim "güncel değil" der — on-yuz/src/uygulama/useSunucu.ts. )
"""

import copy
import json
import unittest

from cizim import geometri, girdi, kuyu_dibi, sabitler
from temel import ortusur
from testler.test_yerlesim_saglamligi import duzen_girdisi, standart_istek
from uclar import cizim_uclari, uygulama_uclari


def _derinlik(d):
    g = copy.deepcopy(girdi.ORNEK)
    g["agirlik"]["derinlik"] = d
    return g


def _cerceve_hatasi(hata):
    return [h for h in hata if "çerçeve profilinin iki kalınlığından" in h]


class AgirlikCercevesininIci(unittest.TestCase):
    """İç ölçü = dış − 2 × çerçeve ( 40 );  sıfır ya da eksi iç ölçü hata."""

    def test_ic_olcu_eksi_ya_da_sifir_hata(self):
        for d in (60, 80):
            hata = _cerceve_hatasi(girdi.dogrula(_derinlik(d)))
            self.assertTrue(hata and "( 2 × 40 = 80 )" in hata[0], (d, hata))

    def test_ic_olcu_artiysa_hata_yok(self):
        self.assertEqual(_cerceve_hatasi(girdi.dogrula(_derinlik(81))), [])

    def test_kalin_cerceve_sabitlerden(self):
        v = standart_istek(800)
        v["sabitler"][sabitler.ofis_adi("agirlik_cerceve")] = 80
        g, A, hata = duzen_girdisi(v)
        hata = hata if g is None else cizim_uclari._cizim_hatalari(g, A)
        self.assertTrue(_cerceve_hatasi(hata), hata)

    def test_paket_inmez_sebebi_soylenir(self):
        r = uygulama_uclari.indir_uygulama_dwg(
            standart_istek(800, agirlik_derinligi=60, agirlik_malzemesi="Pik Döküm")
        )
        self.assertEqual(r.media_type, "application/json")
        self.assertTrue(_cerceve_hatasi(json.loads(r.body)["hata"]))


class MerdivenYazisi(unittest.TestCase):
    def test_dar_merdivende_kuyu_dibi_cizilir_yazi_parcaya_binmez(self):
        for me in (150, 175, 190):
            v = standart_istek(800)
            v["sabitler"][sabitler.ofis_adi("merdiven_eni")] = me
            g, A, hata = duzen_girdisi(v)
            self.assertIsNotNone(g, hata)
            e = kuyu_dibi.ciz(g)
            yazi = geometri.sinir([x for x in e if x.get("metin") == "MERDİVEN"])
            binen = [
                x.get("ad") or x["katman"]
                for x in e
                if x["tip"] not in ("yazi", "olcu", "tarama")
                and x["katman"] not in kuyu_dibi._YUK_DISI + ("YUK",)
                and x.get("ad") != "merdiven"
                and ortusur(yazi, geometri.sinir([x]))
            ]
            self.assertEqual(binen, [], me)

    def test_yazinin_altindaki_noktanin_kutusu_yer_bulur(self):
        """Nokta bir yazının içindeyse her ok o yazıyı keser:  o yazı ok için
        engel sayılmaz ( kutu yine ona binemez )."""
        yazi = (450.0, 450.0, 550.0, 550.0)
        e = kuyu_dibi._yuk_yerlesimi([], [((500.0, 500.0), "FAR = 1,00 kN")], 2000.0, 2000.0, [], [yazi])
        kutu = geometri.sinir([x for x in e if x.get("ad") == "yuk_kutusu"])
        self.assertFalse(ortusur(kutu, yazi))


if __name__ == "__main__":
    unittest.main()

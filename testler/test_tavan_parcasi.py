"""KUYU ÜSTÜ AÇIKLIĞININ ENGELİ İLETİDE ADIYLA ( 25 Kas — kullanıcı:  "Evet, düzelt" ).

Kuyu üstündeki açıklıklar ( korkuluk, revizyon kutusu, üst paten, kabin üstü kasnağı, kabindeki
halat bağlantısı ) kabinin üstündeki EN ALÇAK TAVAN PARÇASINA ölçülür:  kuyu tavanı ya da onun
altındaki makine şasesi, halat bağlantıları, regülatör ( donanim.tavan_engeli ).  Eskiden ileti
hep "– kuyu tavanı" diyordu:  800 kg makine dairesiz, ağırlık arkada, 1850 × 2700, son kat 4050'de
"Korkuluk – kuyu tavanı:  80 mm < 300 mm" yazıyordu, oysa 80 mm makine şasesineydi ( tavana 465 mm ).

Parçanın adı iki noktadan SONRA yazılır:  çare bulucu sorunu iki noktaya kadarki metinden tanır
( care_uclari.kimlik ) — düzeltme engeli değiştirince ( makine şasesi → kuyu tavanı ) sorun aynı
sorun kalmalı, yoksa çare bulucu onu "giden + yeni sorun" sayar ve önerileri değişir.
"""

import unittest

from cizim import donanim, dusey
from uclar import avan_secici, care_uclari

#  Kullanıcının kuyusu ( 24 Kas ):  800 kg, makine dairesiz, 6 durak, kuyu dibi 1,60, son kat 4050
KUYU = {
    "beyan_yuku": 800,
    "beyan_hizi": 1,
    "kuyu_derinligi": 2700,
    "durak_kotlari": "±0,00; +3,00; +6,00; +9,00; +12,00; +15,00",
    "kuyu_dibi_kotu": "-1,60",
    "kuyu_tavani_kotu": "+19,05",
    "mk_yok": True,
    "aski_orani": 2,
}


def _arkada(genislik):
    """Paketin kabini ( 1350 × 1400 ), karşı ağırlık arkada ( seçicinin arka adayı ) — çizim sorunları."""
    t = avan_secici.paketler()[(800, True)]
    m = {**KUYU, "kuyu_genisligi": genislik}
    v = avan_secici._istek(t, m, avan_secici._arka_adayi(t, m))
    cizim, _aktif, _hesap, _bolum, _olctu = care_uclari.girdi_durumu(v, 0)
    return cizim


class TavanParcasi(unittest.TestCase):
    def test_korkulugun_engeli_makine_sasesi(self):
        cizim = _arkada(1850)
        self.assertEqual(
            list(cizim.values()),
            ["Korkuluk – tavan parçası:  makine şasesi, 80 mm < 300 mm  ( TS EN 81-20 m.5.2.5.7.2 c )."],
        )
        #  Çare bulucunun kimliği parçadan bağımsız
        self.assertEqual(list(cizim), ["Korkuluk – tavan parçası"])

    def test_kimlik_parcadan_bagimsiz(self):
        """Aynı açıklık başka parçayla ( gerçek 1250 KG projesinde kuyu tavanı ) aynı sorundur."""
        tavan = "Korkuluk – tavan parçası:  kuyu tavanı, 237 mm < 300 mm  ( TS EN 81-20 m.5.2.5.7.2 c )."
        sase = "Korkuluk – tavan parçası:  makine şasesi, 80 mm < 300 mm  ( TS EN 81-20 m.5.2.5.7.2 c )."
        self.assertEqual(care_uclari.kimlik(tavan), care_uclari.kimlik(sase))

    def test_etiket_parca_adi_soylemez(self):
        """Engeli ölçülen beş açıklığın etiketi bir parçayı adlandırmaz ( adı iletinin içinde );
        engelin her olası adının okunur karşılığı var ( donanim._tavan_alti_parcalari + kuyu tavanı )."""
        for ad in dusey.TAVAN_PARCALI:
            with self.subTest(ad):
                self.assertTrue(dusey.AD[ad].endswith(" – tavan parçası"), dusey.AD[ad])
        self.assertNotIn("kuyu tavanı", " ".join(dusey.AD.values()))
        self.assertEqual(
            set(donanim.TAVAN_PARCASI),
            {"sase", "kabin_baglanti", "agirlik_baglanti", "regulator", "kuyu tavanı"},
        )

    def test_kuyu_dibinde_ve_rayda_parca_yazmaz(self):
        """Öbür yanı adıyla belli açıklıklar ( rayın üst ucu ) ve kuyu dibi eskisi gibi."""
        engel = {"ray": (100.0, "ray"), "korkuluk": (100.0, "sase")}
        self.assertEqual(dusey._tavan_parcasi("ust", "ray", engel), "")
        self.assertEqual(dusey._tavan_parcasi("dip", "korkuluk", engel), "")
        self.assertEqual(dusey._tavan_parcasi("ust", "korkuluk", engel), "makine şasesi, ")


if __name__ == "__main__":
    unittest.main()

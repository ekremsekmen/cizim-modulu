"""SORUNLU ÇİZİM ( cizim/sorunlu.py ) — kural sağlanmasa da ekranda çizim gelir.

19 Eki:  bir kural bozulunca ekran hiçbir çizim göstermiyordu, mühendis sorunu
çizimde göremiyordu.  Artık ekranın çizim ucu ( cizim_uclari.cizimler_yaniti )
sorun varken de çizer;  hesap, paket ve sorun listesi değişmez.

Değişmezler:
  1.  Sorun listesi, sıkı yoldakinin ( girdiler — paket de onu kullanır )
      birebir aynısıdır;  "aktif" bugünkü anlamında kalır ( çizim uygun değil —
      ön yüzün denetimi ve testler reddi oradan okur ), çizimler ek alandır.
  2.  Sorun varken çizimler gelir;  kurulamayan yalnız geometrisi hiç
      kurulamayan çizimdir ( BILINEN — sebebiyle ).
  3.  Paket uygunsuz çizimi yine reddeder.
  4.  Kip kapalıyken yerleşim bugünkü gibi durur;  aynı istekte iki kip
      karışmaz ( istek içi önbellek ).
"""

import json
import unittest

from cizim import dusey
from cizim import istek_onbellegi
from cizim import kopru
from cizim import pafta
from cizim import sorunlu
from motor.uygulama import uygulama_girdisi
from motor.uygulama import uygulama_hesabi
from uclar import cizim_uclari
from uclar import uygulama_istegi
from uclar import uygulama_uclari
from hesap_girdi import ASANSOR, ASANSOR_MD, ORTAK, ORTAK_MD, SABITLER

KESITLER = ("A-A KUYU DÜŞEY KESİTİ", "B-B KUYU DÜŞEY KESİTİ", "KASNAK DÜZENLEMESİ")

#  ( makine dairesi mi , değişen alan , değer ) → kurulamayan çizimler.  Her
#  vaka bir sorun sınıfı:  ray duvara, kabin kuyudan büyük, kanat cebi, durak
#  arası, sığınma, ağırlık tavana, korkuluk – tavan, ağırlık çerçevesi …
VAKALAR = {
    (False, "kuyu_genisligi", 1600): (),
    (False, "kabin_derinligi", 2300): (),
    (False, "kapi_genisligi", 1200): (),
    (False, "durak_adedi", 30): (),
    (False, "kuyu_dibi", 1200): (),
    (False, "son_kat_yuksekligi", 3200): (),
    (False, "son_kat_yuksekligi", 4400): (),
    (False, "agirlik_derinligi", 70): (),
    (False, "kabin_yana_kaciklik", 0): (),
    (True, "son_kat_yuksekligi", 3200): (),
    (True, "ray_kapi_arasi", 500): (),
    #  BILINEN:  arkadaki ağırlıkla 2:1 kabin altı askı çizilemeyen düzendir
    #  ( kuyu_ustu.duzen_hatalari ) — donanımın geometrisi hiç kurulmaz
    (False, "agirlik_yeri", "Arka"): KESITLER + ("KUYU ÜSTÜ PLANI",),
    #  BILINEN:  makine dairesinde kaide odaya yerleşemeyince donanım makine
    #  çerçevesini kurmaz ( donanim:  "çerçeve hiç kurulmaz" ) — kesitler yok,
    #  kuyu planı ve makine dairesi planı var
    (True, "kuyu_genisligi", 1600): KESITLER,
}


def _veri(md, **ek):
    return {
        "asansorler": [dict(ASANSOR_MD if md else ASANSOR, siginma_tipi_dip="Yatarak", **ek)],
        "proje_geneli": dict(ORTAK_MD if md else ORTAK),
        "sabitler": dict(SABITLER),
    }


def _ekran(veri):
    with istek_onbellegi.etkin():
        return json.loads(cizim_uclari.cizimler_yaniti(veri).body)


def _siki(veri):
    """Sıkı yolun ( paket ) sonucu:  ( g , sorunlar ) — g sorun varsa None."""
    asansorler, ortak = uygulama_istegi.asansor_girdileri(veri)
    s = uygulama_hesabi.hesapla_coklu(asansorler, ortak)
    return cizim_uclari.girdiler(veri, asansorler, ortak, s if s.get("aktif") else None, "")[0]


def _g(veri):
    """Köprünün kurduğu çizim girdisi ( sorunlar denetlenmeden )."""
    asansorler, ortak = uygulama_istegi.asansor_girdileri(veri)
    pg = {k: ortak[k] for k in ortak if k != "_ofis"}
    A = uygulama_girdisi.tamamla({**uygulama_girdisi.varsayilanlar(), **ortak, **asansorler[0], **pg})
    return kopru.cizim_girdisi(A, None, "", 1)[0]


class SorunluCizim(unittest.TestCase):
    def test_sorun_varken_cizim_gelir_sorunlar_ayni(self):
        for (md, alan, deger), bilinen in VAKALAR.items():
            with self.subTest(md=md, alan=alan, deger=deger):
                veri = _veri(md, **{alan: deger})
                r = _ekran(veri)
                g_siki, siki = _siki(veri)
                self.assertFalse(r["aktif"])
                self.assertIsNone(g_siki)
                self.assertTrue(siki)
                self.assertEqual(r["hata"], siki)
                self.assertEqual(set(r["kurulamayan"]), set(bilinen))
                self.assertEqual(len(r["cizimler"]) + len(r["kurulamayan"]), len(pafta.sira(_g(veri))))

    def test_sorunsuz_girdide_yanit_bugunku_gibi(self):
        for md in (False, True):
            r = _ekran(_veri(md))
            self.assertTrue(r["aktif"])
            self.assertEqual(set(r), {"aktif", "hesap", "cizimler"})

    def test_paket_uygunsuz_cizimi_reddeder(self):
        veri = _veri(False, son_kat_yuksekligi=4400)
        self.assertTrue(_ekran(veri)["cizimler"])
        d = json.loads(uygulama_uclari.indir_uygulama_dwg(veri).body)
        self.assertIn("ÇİZİMLER KURULAMADI", d["hata"])

    def test_kip_kapaliyken_yerlesim_durur_onbellek_karismaz(self):
        g = _g(_veri(False, durak_adedi=30))
        for sira in ((False, True), (True, False)):
            with self.subTest(sira=sira), istek_onbellegi.etkin():
                for acik in sira:
                    with sorunlu.kip(acik):
                        Y = dusey.yerlesim(g)
                    self.assertTrue(Y["hata"])
                    if acik:
                        self.assertIn("S", Y)
                    else:
                        self.assertEqual(set(Y), {"hata"})

    def test_kip_yalniz_blokta_acik(self):
        self.assertFalse(sorunlu.acik())
        with sorunlu.kip():
            self.assertTrue(sorunlu.acik())
            with sorunlu.kip(False):
                self.assertTrue(sorunlu.acik())  # iç blok dıştakini kapatmaz
        with sorunlu.kip(False):
            self.assertFalse(sorunlu.acik())
        self.assertFalse(sorunlu.acik())


if __name__ == "__main__":
    unittest.main()

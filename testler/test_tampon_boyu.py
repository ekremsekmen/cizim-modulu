"""BOŞ TAMPON BOYU ( 28 Eki ) — tipten ve hızdan ( mukavemet_tablolari.tampon_kural_boyu ).

Eskiden her tipte 100 mm varsayılandı:  1,6 m/s hidrolikte 173 mm'lik strok
100 mm'lik tampona sığmıyor, sahada çalışan asansör ( KONTEST K408 ) "ezilme >
boy" diye reddediliyordu;  1,0 m/s yaylıda da ( 135 mm ).  Yaylı tampon 1 m/s
üstünde ise ileti "boyunu girin" diyordu — asıl engel m.5.8.1.5.

Değişmezler ( bütün tipler × bütün beyan hızları, kabin ve ağırlık boyu boş ):
  1.  Boy kurulabiliyorsa tampon yüzünden ret yok:  ne çizim ne hesap "ezilme
      > boy" der.
  2.  Kurulamıyorsa çizim ve hesap AYNI tek iletiyi söyler;  kaidenin
      "girilmemiş"i ( boydan türer ) ayrıca söylenmez.
  3.  Yaylı tampon 1 m/s üstünde:  ileti tipi söyler, boy istemez.
  4.  Hidrolik boy, gereken stroku karşılayan EN KÜÇÜK YH modelinden;  girilen
      boy olduğu gibi kalır.
"""

import unittest

from motor.uygulama import mukavemet_tablolari, uygulama_girdisi, uygulama_hesabi
from tasarim import alanlar
from uclar import care_uclari, uygulama_istegi
from testler.test_care import ORNEK

HIDROLIK, POLIURETAN, YAYLI = (
    mukavemet_tablolari.TAMPON_TIPLERI_ADLARI[2],
    mukavemet_tablolari.TAMPON_TIPLERI_ADLARI[1],
    mukavemet_tablolari.TAMPON_TIPLERI_ADLARI[0],
)
HIZLAR = alanlar.ALAN["beyan_hizi"].secenekler
TAMPON_ALANLARI = ("kabin_tampon_boyu", "kabin_tampon_ezilme", "agirlik_tampon_boyu", "agirlik_tampon_ezilme")


def _veri(tip, v, **ek):
    a = {k: x for k, x in ORNEK.items() if k not in TAMPON_ALANLARI}
    a.update(tampon_tipi=tip, beyan_hizi=str(v).replace(".", ","), **ek)
    return {"asansorler": [a], "proje_geneli": {}, "sabitler": {}, "asansor": 0}


def _tamamla(tip, v, **ek):
    return uygulama_girdisi.tamamla(
        {**uygulama_girdisi.varsayilanlar(), "tampon_tipi": tip, "beyan_hizi": v, **ek}
    )


def _iletiler(tip, v, **ek):
    """( çizimin iletileri , hesabın iletileri ) — tam metinler."""
    veri = _veri(tip, v, **ek)
    cizim, _aktif, _k, _ud = care_uclari._durum(veri, 0)
    s = uygulama_hesabi.hesapla_coklu(*uygulama_istegi.asansor_girdileri(veri))
    return list(cizim.values()), [str(h) for h in s["asansorler"][0].get("hata") or []]


def _tampon_reddi(metinler):
    return [m for m in metinler if "ezilme" in m and ("boyundan" in m or "boyunu" in m) or "stroku boş" in m]


class Katalog(unittest.TestCase):
    def test_en_kucuk_yeten_model(self):
        for v in HIZLAR:
            s = mukavemet_tablolari.tampon_gereken_stroku(HIDROLIK, v)
            t = mukavemet_tablolari.hidrolik_tampon(v)
            yetenler = [x for x in mukavemet_tablolari.HIDROLIK_TAMPONLAR if x[1] >= s]
            with self.subTest(v=v):
                self.assertEqual(t, yetenler[0] if yetenler else None)

    def test_boy_fiziksel(self):
        """Tek kademeli hidrolik tampon:  piston stroku kadar dışarıda, silindir en
        az o kadar — boy ≥ 2 × strok;  katalog strokla sıralı."""
        for model, strok, boy in mukavemet_tablolari.HIDROLIK_TAMPONLAR:
            with self.subTest(model=model):
                self.assertGreaterEqual(boy, 2 * strok)
        self.assertEqual(
            list(mukavemet_tablolari.HIDROLIK_TAMPONLAR),
            sorted(mukavemet_tablolari.HIDROLIK_TAMPONLAR, key=lambda x: x[1]),
        )

    def test_ornekler(self):
        self.assertEqual(mukavemet_tablolari.tampon_kural_boyu(HIDROLIK, 1.6)[0], 540)  # YH52/175
        self.assertEqual(mukavemet_tablolari.tampon_kural_boyu(HIDROLIK, 1.0)[0], 315)  # YH51/80
        self.assertEqual(mukavemet_tablolari.tampon_kural_boyu(HIDROLIK, 2.5)[0], 1125)  # YH55/435
        self.assertIsNone(
            mukavemet_tablolari.tampon_kural_boyu(HIDROLIK, 3)[0]
        )  # 607 mm strok:  katalog yetmez
        self.assertEqual(mukavemet_tablolari.tampon_kural_boyu(POLIURETAN, 2)[0], 100)
        self.assertEqual(mukavemet_tablolari.tampon_kural_boyu(YAYLI, 0.8)[0], 100)  # 86 mm strok
        self.assertIsNone(mukavemet_tablolari.tampon_kural_boyu(YAYLI, 1.0)[0])  # 135 mm strok
        self.assertEqual(
            mukavemet_tablolari.tampon_kural_boyu(YAYLI, 1.6)[0], 100
        )  # tip uygun değil:  boy çare değil


class Tamamla(unittest.TestCase):
    def test_hidrolik_boy_katalogdan_isaretli(self):
        g = _tamamla(HIDROLIK, 1.6)
        self.assertEqual(g["kabin_tampon_boyu"], 540)
        self.assertIn("YH52/175", g["_kural"]["kabin_tampon_boyu"])
        self.assertEqual(g["kabin_tampon_ezilme"], 173)

    def test_girilen_boy_kalir(self):
        g = _tamamla(HIDROLIK, 1.6, kabin_tampon_boyu=630)
        self.assertEqual(g["kabin_tampon_boyu"], 630)
        self.assertNotIn("kabin_tampon_boyu", g.get("_kural") or {})

    def test_varsayilan_projede_boy_bos(self):
        """Açılış değerleri boyu taşımaz:  tipten ve hızdan her istekte yeniden."""
        self.assertIsNone(uygulama_girdisi.varsayilanlar()["kabin_tampon_boyu"])


class Sinif(unittest.TestCase):
    """Bütün tipler × bütün beyan hızları, kabin ve ağırlık tamponu boş."""

    def test_degismezler(self):
        for tip in mukavemet_tablolari.TAMPON_TIPLERI_ADLARI:
            for v in HIZLAR:
                with self.subTest(tip=tip, v=v):
                    cizim, hesap = _iletiler(tip, v)
                    boy, _yazi = mukavemet_tablolari.tampon_kural_boyu(tip, v)
                    biriktirmeli_asim = (
                        mukavemet_tablolari.tampon(tip)[1]
                        and v > mukavemet_tablolari.TAMPON_BIRIKTIRMELI_AZAMI_HIZ
                    )
                    if biriktirmeli_asim and tip == YAYLI:
                        #  3.  yaylıda tip uygun değil:  ileti tipi söyler, boy istemez
                        for m in cizim + hesap:
                            self.assertNotIn("boyunu", m)
                        self.assertTrue(any(m.startswith("Tampon tipi:") for m in hesap), hesap)
                        self.assertTrue(any(m.startswith("Tampon tipi:") for m in cizim), cizim)
                    elif boy is not None:
                        #  1.  boy kuruldu:  tampon yüzünden ret yok
                        self.assertEqual(_tampon_reddi(cizim), [])
                        self.assertEqual(_tampon_reddi(hesap), [])
                    else:
                        #  2.  kurulamadı:  çizim ve hesap aynı tek ileti
                        ileti = mukavemet_tablolari.bos_tampon_boyu_iletisi(tip, v)
                        self.assertEqual(cizim, [ileti])
                        self.assertEqual(hesap, [ileti])

    def test_agirlik_boyu_girilmis(self):
        """Ağırlık tamponunun boyu girilmiş ve strok ona sığmıyor:  ileti o sayıyı söyler."""
        _cizim, hesap = _iletiler(HIDROLIK, 1.6, agirlik_tampon_boyu="100")
        self.assertTrue(any(m.startswith("Ağırlık tamponunun stroku boş") for m in hesap), hesap)


if __name__ == "__main__":
    unittest.main()

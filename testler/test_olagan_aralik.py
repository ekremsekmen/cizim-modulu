# -*- coding: utf-8 -*-
"""OLAĞAN ARALIK ( 28 Kas — cikti/devir/GIRDI_SINIRLARI_PLANI.md, tablo GIRDI_ARALIK_TABLOSU.md ).

Kullanıcı:  "devasa değerler girilebiliyor … duvar kalınlığını 300 cm yapmıştım, pratikte olamaz".
Kesin tavan ( alanlar.AZAMI — çökme koruması ) reddeder;  olağan aralık ( alanlar.OLAGAN ) yalnız
SORAR:  ekran kutunun yanında "olağan dışı", teslim listeler.  Güvenceler:

  S-G1 / S-G2  şemanın öz denetimi ( alanlar._denetle — içe aktarılırken );
  S-G3         bilinen gerçek girdilerin hiçbiri uyarı almaz ( yanlış uyarı gürültüdür, okunmaz );
  S-G4         olağan dışı değer reddedilmez — kapı geçirir, kesin tavan bugünkü gibi reddeder.

Ön yüz ile sunucunun aynı hükmü:  test_on_yuz_denetimi.test_olagan_disi_sunucuyla_ayni_ve_reddedilmez.
"""

import unittest

import hesap_girdi
from araclar import tarama
from tasarim import alanlar
from testler import gercek_projeler
from testler import test_yerlesim_saglamligi
from uclar import avan_secici
from uclar import uygulama_istegi


def _sayi(x):
    """Formun yazımı ( "1250", "1,5", 2.5 ) → float ya da None ( seçim, metin, boş )."""
    if isinstance(x, bool) or x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    try:
        return float(str(x).strip().replace(",", "."))
    except ValueError:
        return None


def _kaynaklar():
    """( kaynak adı , { anahtar:  değer } ) — bilinen gerçek girdiler."""
    for ad, p in gercek_projeler.PROJELER.items():
        yield f"gerçek proje {ad}", p
    yield "örnek proje", gercek_projeler.ornek_proje()
    for t in avan_secici.paketler().values():
        yield f"paket {t['kimlik']}", {**t["proje_geneli"], **t["asansor"]}
    for ad in ("ASANSOR", "ASANSOR_MD", "ORTAK", "ORTAK_MD"):
        yield f"hesap_girdi {ad}", getattr(hesap_girdi, ad, {})
    for grup in tarama.GRUPLAR:
        for ad, v in tarama.duzenler(grup):
            for i, a in enumerate(v["asansorler"]):
                yield f"tarama {grup} {ad} [{i}]", {**v.get("proje_geneli", {}), **a}


class OlaganAralik(unittest.TestCase):
    def test_bilinen_girdiler_uyari_almaz(self):
        """S-G3:  gerçek projeler, örnek, paketler, hesabın test girdisi, çizim taramasının düzenleri."""
        uyarilar, n = [], 0
        for kaynak, d in _kaynaklar():
            for k, v in d.items():
                x = _sayi(v)
                if k in alanlar.OLAGAN and x is not None:
                    n += 1
                    ileti = alanlar.olagan_disi(k, x)
                    if ileti:
                        uyarilar.append(f"{kaynak}:  {ileti}")
        self.assertGreater(n, 1000, "test neredeyse hiç değer denemedi")
        self.assertEqual(uyarilar, [], "\n".join(uyarilar[:20]))

    def test_kullanicinin_ornegi(self):
        """300 cm duvar uyarı alır;  olağan duvar almaz;  ileti aralığı söyler."""
        ileti = alanlar.olagan_disi("kuyu_duvar_kalinligi", 3000)
        self.assertEqual(ileti, "Kuyu duvarı kalınlığı 3.000 mm — olağan 30 – 750 mm")
        self.assertIsNone(alanlar.olagan_disi("kuyu_duvar_kalinligi", 200))
        #  Bir sıfır fazla / eksik ( × 10 ) her aralıklı alanda yakalanır
        for k in alanlar.OLAGAN:
            if k in alanlar.OLAGAN_ADET:
                continue
            d = alanlar.OLAGAN_GOZLEM.get(k, alanlar.ALAN[k].varsayilan)
            with self.subTest(alan=k):
                self.assertIsNone(alanlar.olagan_disi(k, d))
                if d * 10 <= alanlar.AZAMI[k]:
                    self.assertIsNotNone(alanlar.olagan_disi(k, d * 10))
                self.assertIsNotNone(alanlar.olagan_disi(k, d / 10))

    def test_standardin_alt_siniri(self):
        """TS EN 81-20:  kapı ve kabin 2,0 m ( m.5.3.2.1, m.5.4.1 ), makine dairesi 2,1 m
        ( m.5.2.6.3.2.1 ), makine dairesi kapısı 2,0 × 0,6 m ( m.5.2.3.2 a ) — altı olağan dışı."""
        for k, alt in alanlar.OLAGAN_STANDART_ALT.items():
            with self.subTest(alan=k):
                self.assertEqual(alanlar.OLAGAN[k][0], alt)
                self.assertIsNotNone(alanlar.olagan_disi(k, alt - 1))
                self.assertIsNone(alanlar.olagan_disi(k, alt))

    def test_olagan_disi_reddedilmez(self):
        """S-G4:  kapı olağan dışı değeri geçirir;  kesin tavanı aşan bugünkü gibi reddedilir."""
        v = test_yerlesim_saglamligi.standart_istek(1000, True, "Sağ")
        v["asansorler"][0]["kuyu_duvar_kalinligi"] = "3000"
        asansorler, _ortak = uygulama_istegi.asansor_girdileri(v)
        self.assertEqual(asansorler[0]["kuyu_duvar_kalinligi"], 3000)
        v["asansorler"][0]["kuyu_duvar_kalinligi"] = "30000"
        with self.assertRaises(uygulama_istegi.GecersizGirdi):
            uygulama_istegi.asansor_girdileri(v)

    def test_kurallar_ekrana_gider(self):
        """Form şemasının kuralları olağan aralığı taşır ( ön yüz kutuda sorar );  aralıksız alanda None."""
        k = uygulama_istegi.alanlar()["kurallar"]
        self.assertEqual(
            (k["kuyu_duvar_kalinligi"]["olagan_alt"], k["kuyu_duvar_kalinligi"]["olagan_ust"]), (30.0, 750)
        )
        self.assertIsNone(k["seyir_mesafesi"]["olagan_alt"])
        self.assertEqual(
            {a for a, x in k.items() if x["olagan_alt"] is not None}, set(alanlar.OLAGAN) & set(k)
        )


if __name__ == "__main__":
    unittest.main()

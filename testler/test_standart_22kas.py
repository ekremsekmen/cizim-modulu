"""TS EN 81-20 METNİYLE BAĞIMSIZ DENETİM — 22 KAS bulguları.

Programın kabul sınırı standardın metninden hesaplanan eşikle karşılaştırıldı
( kara kutu, HTTP uçları );  çoğu kural birebir tuttu, üçü düzeltildi:

1.  m.5.8.2.1.2.2:  lineer olmayan ( poliüretan ) tamponda "tam ezilme" kurulu
    boyun %90'ıdır — ezilmeyi daha azıyla sınırlayabilecek bağlantı elemanları
    DİKKATE ALINMADAN.  Daha küçük girilen ezilme sığınma açıklıklarında
    kullanılıyordu ( kabinde yalnız uyarı, ağırlıkta hiçbir şey ):  100 mm'lik
    tampona 20 girilince kuyu dibi 71, kuyu üstü 70 mm daha az isteniyordu.
2.  m.5.2.2.4 a:  kuyu dibi 2,50 m'yi aşarsa erişim kapısı gerekir.  Çizim
    merdiveni kaldırıyordu ama kapı hiçbir yerde söylenmiyordu.
3.  Üç ondalıklı yazım ( "1,850" m/s ) "belirsiz" diye reddediliyordu;  alanın
    tavanı binlik okumayı imkânsız kılıyorsa ondalıktır.
"""

import json
import unittest

from testler import test_yerlesim_saglamligi as yerlesim
from uclar import cizim_uclari, uygulama_istegi, uygulama_uclari

PU = "Poliüretan  ( lineer olmayan )"
HIDROLIK = "Hidrolik  ( enerji yutmalı )"


def _istek(**asansor):
    v = yerlesim.standart_istek(1000, True, "Sağ")
    v["asansorler"][0].update({k: str(x) for k, x in asansor.items()})
    return v


def _hesap(v):
    return json.loads(uygulama_uclari.api_uygulama_coklu(v).body)


class LineerOlmayanTamponunTamEzilmesi(unittest.TestCase):
    def test_yuzde_doksanin_alti_iki_tarafta_da_hesabi_durdurur(self):
        for taraf, olcen in (("kabin_tampon_ezilme", "Kuyu dibi"), ("agirlik_tampon_ezilme", "Kuyu üstü")):
            for ez in (20, 70, 89):
                with self.subTest(taraf=taraf, ezilme=ez):
                    r = _hesap(_istek(tampon_tipi=PU, kabin_tampon_boyu=100, **{taraf: ez}))
                    self.assertFalse(r["aktif"], r.get("hata"))
                    ileti = " ".join(r["hata"])
                    self.assertIn("m.5.8.2.1.2.2", ileti)
                    self.assertIn(olcen, ileti)
                    self.assertIn("en az 90", ileti)

    def test_yuzde_doksan_ve_ustu_bos_ve_boy_kadari_gecer(self):
        for ez in (90, 95, 100, None):
            with self.subTest(ezilme=ez):
                d = {"tampon_tipi": PU, "kabin_tampon_boyu": 100}
                if ez is not None:
                    d["kabin_tampon_ezilme"] = ez
                    d["agirlik_tampon_ezilme"] = ez
                r = _hesap(_istek(**d))
                self.assertTrue(r["aktif"], r.get("hata"))

    def test_eski_ters_uyari_yok(self):
        """Uyarı "bağlantı elemanları sınırlıyorsa değer doğrudur" diyordu — standardın tersi."""
        r = _hesap(_istek(tampon_tipi=PU, kabin_tampon_boyu=100, kabin_tampon_ezilme=90))
        metin = json.dumps(r, ensure_ascii=False)
        self.assertNotIn("gerçekten sınırlıyorsa", metin)

    def test_lineer_ve_hidrolikte_kural_aranmaz(self):
        """Strokları bağıntıyla denetlenir ( m.5.8.2.1.1.1 · 5.8.2.2.1 ) — %90 yalnız lineer olmayanın tanımı."""
        r = _hesap(
            _istek(
                tampon_tipi=HIDROLIK, kabin_tampon_boyu=400, kabin_tampon_ezilme=80, agirlik_tampon_ezilme=80
            )
        )
        self.assertTrue(r["aktif"], r.get("hata"))


class DerinKuyuDibineErisimKapisi(unittest.TestCase):
    def _kur(self, kuyu_dibi):
        v = _istek(kuyu_dibi=kuyu_dibi)
        yerlesim.kotla(v)
        return v

    def test_iki_buçuk_metreyi_asinca_uyari_ve_not(self):
        v = self._kur(2800)
        r = _hesap(v)
        self.assertTrue(r["aktif"], r.get("hata"))
        uyarilar = r["asansorler"][0]["uyarilar"]
        self.assertTrue(any("ERİŞİM KAPISI" in u and "m.5.2.2.4" in u for u in uyarilar), uyarilar)
        c = json.loads(cizim_uclari.api_cizimler(v).body)
        self.assertTrue(c["aktif"], c.get("hata"))
        cizim = {x["ad"]: x["svg"] for x in c["cizimler"]}
        self.assertIn("erişim kapısı", cizim["veriler"])
        self.assertNotIn("MERDİVEN", cizim["kuyu_dibi"])

    def test_iki_buçuk_metre_ve_alti_merdiven_notsuz(self):
        for ky in (1600, 2500):
            with self.subTest(kuyu_dibi=ky):
                v = self._kur(ky)
                r = _hesap(v)
                self.assertTrue(r["aktif"], r.get("hata"))
                self.assertFalse([u for u in r["asansorler"][0]["uyarilar"] if "ERİŞİM KAPISI" in u])
                c = json.loads(cizim_uclari.api_cizimler(v).body)
                cizim = {x["ad"]: x["svg"] for x in c["cizimler"]}
                self.assertNotIn("erişim kapısı", cizim["veriler"])
                self.assertIn("MERDİVEN", cizim["kuyu_dibi"])


class UcOndalikliYazim(unittest.TestCase):
    def _oku(self, anahtar, ham):
        v = _istek(**{anahtar: ham})
        asansorler, _ortak = uygulama_istegi.asansor_girdileri(v)
        return asansorler[0][anahtar]

    def test_tavan_binlik_okumayi_dislarsa_ondalik(self):
        #  m/s ( tavan 50 ):  1850 olamaz;  kg/m ( tavan 100 ):  1200 olamaz
        for anahtar, ham, bek in (
            ("reg_devreye_hizi", "1,850", 1.85),
            ("reg_devreye_hizi", "2.156", 2.156),
            ("reg_devreye_hizi", "1,85", 1.85),
            ("halat_birim_kutle", "1,200", 1.2),
        ):
            with self.subTest(anahtar=anahtar, ham=ham):
                self.assertAlmostEqual(self._oku(anahtar, ham), bek, places=9)

    def test_tavanin_altindaki_binlik_okuma_belirsiz_kalir(self):
        #  mm ( tavan 20.000 ):  1.200 hem 1200 hem 1,2 olabilir
        for ham in ("1.200", "1,450"):
            with self.subTest(ham=ham), self.assertRaises(uygulama_istegi.GecersizGirdi) as k:
                self._oku("kabin_genisligi", ham)
            self.assertIn("Belirsiz", " ".join(k.exception.hatalar))

    def test_tavani_asan_ondalik_yine_reddedilir(self):
        """Okunuş çözülür, kural yine uygulanır:  regülatör hızı 1,850 sınır içinde, 51,500 değil."""
        with self.assertRaises(uygulama_istegi.GecersizGirdi):
            self._oku("reg_devreye_hizi", "51,500")


if __name__ == "__main__":
    unittest.main()

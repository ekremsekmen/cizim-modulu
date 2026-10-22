"""GİRDİ KAPISI ( uclar/uygulama_istegi.asansor_girdileri ) — uygulamanın
bütün uçları isteği yalnız buradan okur.  21 Eki:  girdi üç yerde ayrı ayrı
denetleniyordu ( istek, hesabın doğrulaması, çizim köprüsü ) ve hesap
denetimi bitirmeden çizimi kurup değer türetiyordu:  kapı genişliği 10¹²
belleği bitirdi, True / liste / sözlük çökertti;  2,5 halat çiziliyor,
"xyz" kapı montajı hesaplanıyordu.

  -  Tür, okunuş, seçenek, tam sayı, alt sınır ve tavan kapıda:  geçersiz
     girdide hesap da çizim de BAŞLAMAZ, iki uç aynı iletiyi verir.
  -  Kural tablosu ön yüzünkü ( mukavemet_girdi.form_kurallari ):  ön yüz
     ile kapı aynı değerde aynı kararı verir.
  -  Alanlar arası ve mühendislik kuralları motorda kalır."""

import json
import unittest
from unittest import mock

from cizim import kopru
from motor.uygulama import mukavemet_girdi, uygulama_hesabi
from tasarim import alanlar
from testler import test_on_yuz_denetimi, test_yerlesim_saglamligi
from uclar import care_uclari, cizim_uclari, uygulama_istegi, uygulama_uclari

#  Her türün bozuk değerleri ( API'den gelebilir — form göndermez )
BOZUK = {
    "sayi": ("abc", "1.200", True, [], {}, "inf", 1e12),
    "secim": (True, False, [], {}, "yok böyle", 1e12, -1),
    "onay": ([], {}),
    "metin": (True, [], {"a": 1}),
}


def _istek(anahtar, deger, mrl=True):
    v = test_yerlesim_saglamligi.standart_istek(1000, mrl, "Sağ")
    pg = anahtar in uygulama_istegi.PROJE_GENELI_ALANLAR
    (v["proje_geneli"] if pg else v["asansorler"][0])[anahtar] = deger
    return v


def _formdaki(tur):
    gizli_mrl = uygulama_istegi.uygulanmayan({"mk_yok": True})
    return [
        (a.anahtar, a.anahtar not in gizli_mrl)
        for a in alanlar.ALANLAR
        if a.formda and a.tur == tur and not (a.tur == "secim" and a.anahtar == "makine_raya_biniyor")
    ]


class GecersizGirdiIsBaslatmaz(unittest.TestCase):
    def test_her_alanin_bozuk_degeri_kapida_durur(self):
        """Her kutuya kendi türünün bozuk değerleri:  kapı reddeder, ileti
        alanın adını taşır;  hesap ve çizim hiç çağrılmaz."""
        yasak = AssertionError("geçersiz girdide iş başladı")
        with (
            mock.patch.object(uygulama_hesabi, "hesapla_coklu", side_effect=yasak),
            mock.patch.object(kopru, "cizim_girdisi", side_effect=yasak),
        ):
            for tur, degerler in BOZUK.items():
                for anahtar, mrl in _formdaki(tur):
                    for d in degerler:
                        with self.subTest(anahtar=anahtar, deger=d):
                            v = _istek(anahtar, d, mrl)
                            with self.assertRaises(uygulama_istegi.GecersizGirdi) as k:
                                uygulama_istegi.asansor_girdileri(v)
                            et = alanlar.ALAN[anahtar].etiket
                            self.assertTrue(any(et in h for h in k.exception.hatalar), k.exception.hatalar)
                            hesap = json.loads(uygulama_uclari.api_uygulama_coklu(v).body)
                            cizim = json.loads(cizim_uclari.api_cizimler(v).body)
                            self.assertEqual(hesap, {"aktif": False, "hata": k.exception.hatalar})
                            self.assertEqual(cizim, {"aktif": False, "hata": k.exception.hatalar})

    def test_care_ve_olcu_ucu_de_kapidan(self):
        v = _istek("aski_orani", 3)
        hata = uygulama_istegi.GecersizGirdi
        with self.assertRaises(hata):
            uygulama_istegi.asansor_girdileri(v)
        c = json.loads(care_uclari.api_care(v).body)
        self.assertEqual(c, {"aktif": False, "hata": [mukavemet_girdi.secim_iletisi("aski_orani", 3)]})
        o = json.loads(cizim_uclari.api_olcu(dict(v, cizim="kuyu_plani", olcu=0)).body)
        self.assertFalse(o["aktif"])
        self.assertIn("geçersiz seçim", o["hata"][0])


class KuralTablosu(unittest.TestCase):
    def test_on_yuz_ve_kapi_ayni_karari_verir(self):
        """Ön yüzün okuduğu her değerde ( sınırın iki yanı, kesirli, eksi )
        ön yüz ile kapının kararı aynı:  ikisi aynı tabloyu uygular."""
        kurallar = mukavemet_girdi.form_kurallari()
        durumlar = []
        for a, k in kurallar.items():
            degerler = {-150, -1, 0, 0.5, 1, 2.5, 7, 1e12}
            for s in (k["en_az"], k["en_cok"]):
                if s is not None:
                    degerler |= {s - 1, s - 0.01, s, s + 0.01, s + 1}
            durumlar += [(a, k, x) for x in sorted(degerler)]
        on_yuz = test_on_yuz_denetimi.on_yuz(
            [[a, k, f"{x:.6f}".rstrip("0").rstrip(".").replace(".", ",")] for a, k, x in durumlar]
        )
        farkli = [
            f"{a} = {x:g}:  ön yüz {o!r}, kapı {mukavemet_girdi.alan_hatasi(a, x)!r}"
            for (a, _k, x), o in zip(durumlar, on_yuz)
            if bool(o) != bool(mukavemet_girdi.alan_hatasi(a, x))
        ]
        self.assertEqual(farkli, [], "\n".join(farkli[:20]))

    def test_her_sayi_alaninin_kurali_var(self):
        sayi = {a.anahtar for a in alanlar.ALANLAR if a.formda and a.tur == "sayi"}
        self.assertEqual(sayi - set(mukavemet_girdi.form_kurallari()), set())

    def test_ileti_motorunkiyle_ayni(self):
        """Motor doğrudan çağrılınca ( altınlar, hesap testleri ) aynı cümle."""
        for anahtar, d in (
            ("kabin_genisligi", 0),
            ("halat_adedi", 6.5),
            ("kabin_tampon_adedi", 0),
            ("reg_kanal_acisi", 360),
            ("halat_kopma_kN", 31500),
            ("kabin_paten_arasi", 30000),
        ):
            with self.subTest(anahtar=anahtar):
                ileti = mukavemet_girdi.alan_hatasi(anahtar, d)
                g = mukavemet_girdi.tamamla({**mukavemet_girdi.varsayilanlar(), anahtar: d})
                self.assertIn(ileti, mukavemet_girdi.dogrula(g))


class Okuma(unittest.TestCase):
    def test_secim_listedeki_degere_eslenir(self):
        v = test_yerlesim_saglamligi.standart_istek(1000, True, "Sağ")
        v["asansorler"][0].update(aski_orani="2", beyan_hizi="1,6", yan_yatak="30", kapi_genisligi=1000.0)
        a = uygulama_istegi.asansor_girdileri(v)[0][0]
        self.assertEqual(
            (a["aski_orani"], a["beyan_hizi"], a["yan_yatak"], a["kapi_genisligi"]), (2, 1.6, 30, 1000)
        )
        self.assertIs(type(a["kapi_genisligi"]), int)

    def test_eski_onay_kutusu_makine_yuku_yoluna_cevrilir(self):
        for eski, yeni in ((True, "Kılavuz raylara"), ("EVET", "Kılavuz raylara"), (False, "Bina yapısına")):
            with self.subTest(eski=eski):
                a = uygulama_istegi.asansor_girdileri(_istek("makine_raya_biniyor", eski))[0][0]
                self.assertEqual(a["makine_raya_biniyor"], yeni)
        with self.assertRaises(uygulama_istegi.GecersizGirdi):
            uygulama_istegi.asansor_girdileri(_istek("makine_raya_biniyor", []))

    def test_gizli_alan_okunmaz_denetlenmez(self):
        """Makine dairesizde makine dairesi alanı gizlidir:  içindeki bozuk
        değer projeyi durdurmaz ( kullanıcı göremez, düzeltemez )."""
        a, o = uygulama_istegi.asansor_girdileri(_istek("md_duvar", "abc"))
        self.assertIsNone(o["md_duvar"])

    def test_regulator_kacikligi_eksi_olabilir(self):
        """Öne eksi ( "arkaya +" ) — kuralı da −280 verebilir."""
        a = uygulama_istegi.asansor_girdileri(_istek("regulator_kaciklik", -280))[0][0]
        self.assertEqual(a["regulator_kaciklik"], -280)

    def test_cok_asansorlude_ileti_asansorun_adiyla(self):
        v = test_yerlesim_saglamligi.standart_istek(1000, True, "Sağ")
        v["asansorler"].append(dict(v["asansorler"][0], halat_adedi=2.5))
        v["asansorler"].append(dict(v["asansorler"][0], asansor_adi="Yük", aski_orani=3))
        with self.assertRaises(uygulama_istegi.GecersizGirdi) as k:
            uygulama_istegi.asansor_girdileri(v)
        self.assertEqual(
            k.exception.hatalar,
            [
                "2 nolu asansör:  Askı halatı adedi: adet tam sayı olmalıdır ( 2.5 girildi ).",
                "Yük:  " + mukavemet_girdi.secim_iletisi("aski_orani", 3),
            ],
        )

    def test_okunamayan_yazim_bugunku_toplu_iletiyle(self):
        with self.assertRaises(uygulama_istegi.GecersizGirdi) as k:
            uygulama_istegi.asansor_girdileri(_istek("kabin_genisligi", "12abc"))
        self.assertEqual(len(k.exception.hatalar), 1)
        self.assertIn("Girdi kabul edilmedi", k.exception.hatalar[0])

    def test_sabitler_araligi_kapida(self):
        v = test_yerlesim_saglamligi.standart_istek(1000, True, "Sağ")
        v["sabitler"] = {"beta": 0.5}
        with self.assertRaises(uygulama_istegi.GecersizGirdi) as k:
            uygulama_istegi.asansor_girdileri(v)
        self.assertTrue(k.exception.hatalar[0].startswith("Ofis standardı · "), k.exception.hatalar)


if __name__ == "__main__":
    unittest.main()

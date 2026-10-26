"""KOTLA GİRİŞ — 1. adım:  şema ve kapı ( cikti/devir/KOT_PLANI.md ).

Mimari pafta konum ( kot ) verir;  seyir, KY, son kat ve tabliye iki konumun
farkıdır.  Kat girişinin iki kipi var ( tasarim/alanlar KAT GİRİŞİ ):  durak
kotları doluysa katlar KOTLA girilir ve ölçüden türeyen altı kutu okunmaz;
boşsa ÖLÇÜYLE girilir ve kot kutuları okunmaz — bir sayının iki kaynağı olmaz.

  -  Kot yazımı ( cizim/katlar.kot_oku ):  metre, işaretli, mm'ye kadar;  nokta
     da virgül de ondalık, binlik ayracı yok;  paftadan kopyalanan "−" ve "±0,00".
  -  Durak kotları alttan üste, kesin artan;  mm ile yazılmış liste birimini
     söyleyen iletiyle durur.
  -  Kapı öbür kipin alanını okumaz;  bozuk kot alanın adıyla reddedilir.

Türetme ( kot → seyir, KY … ) 2. adımdadır."""

import unittest

from cizim import katlar
from tasarim import alanlar, gorunum
from testler import test_yerlesim_saglamligi
from uclar import care_uclari, uygulama_istegi

#  Kottan türeyen ( kotla girişte okunmayan ) alanlar — KOT_PLANI § 1.1
TURETILEN = {
    "durak_adedi",
    "seyir_mesafesi",
    "kat_yukseklikleri",
    "kuyu_dibi",
    "son_kat_yuksekligi",
    "tabliye_yuksekligi",
}
KOT_KUTULARI = {"kuyu_dibi_kotu", "kuyu_tavani_kotu", "md_zemini_kotu"}


def _istek(**a):
    v = test_yerlesim_saglamligi.standart_istek(1000, True, "Sağ")
    v["asansorler"][0].update(a)
    return v


class KotYazimi(unittest.TestCase):
    def test_okunan_yazimlar_mm_tam_sayi(self):
        for ham, mm in (
            ("−8,80", -8800),  # paftadan kopyalanan eksi ( U+2212 )
            ("-8.80", -8800),  # mimari CAD:  nokta ondalık
            ("–3,50", -3500),  # en tire ( kelime işlemci )
            ("+62,20", 62200),
            ("±0,00", 0),
            ("0", 0),
            ("8,805", 8805),  # virgülle üç ondalık:  mm
            ("8,8050", 8805),  # ön yüzün sona eklediği sıfır ( kutuyaYaz )
            ("0.805", 805),  # "0." ile başlayan nokta binlik olamaz
            (" − 8 , 80 ", -8800),
            (-8.8, -8800),  # API sayısı
            (57, 57000),
        ):
            with self.subTest(ham=ham):
                self.assertEqual(katlar.kot_oku(ham), (mm, None))
                self.assertIs(type(katlar.kot_oku(ham)[0]), int)

    def test_reddedilen_yazimlar_sebebiyle(self):
        for ham, sebep in (
            ("1.200", "belirsiz"),  # bin iki yüz de okunur
            ("+60.800", "belirsiz"),
            ("8,8051", "mm'den ince"),
            (8.8051, "mm'den ince"),
            ("1.234,56", "okunamadı"),  # binlik ayracı yok
            ("8,80m", "okunamadı"),
            ("abc", "okunamadı"),
            ("inf", "okunamadı"),
            ("±1,00", "yalnız sıfırda"),
            ("5000,001", "arasında olmalı"),
            (-6000, "arasında olmalı"),
            (1e12, "arasında olmalı"),
            (True, "kot olmalı"),
            ([], "kot olmalı"),
            (float("nan"), "kot olmalı"),
        ):
            with self.subTest(ham=ham):
                mm, ileti = katlar.kot_oku(ham)
                self.assertIsNone(mm)
                self.assertIn(sebep, ileti)

    def test_sinir_metre_alanlarinin_tavani(self):
        self.assertEqual(katlar.kot_oku("-5000"), (-5_000_000, None))
        self.assertEqual(katlar.kot_oku("+5000"), (5_000_000, None))
        self.assertEqual(katlar.KOT_AZAMI_MM, alanlar.BIRIM_AZAMI["m"] * 1000)


class DurakKotlari(unittest.TestCase):
    def test_alttan_uste_noktali_virgul_ya_da_satir(self):
        for ham in ("−7,00; −3,50; ±0,00; +3,20", "-7;-3,5;0;3,2;", "-7\n-3,5\n0\n3,2", [-7, -3.5, 0, 3.2]):
            with self.subTest(ham=ham):
                self.assertEqual(katlar.kotlari_oku(ham), ([-7000, -3500, 0, 3200], []))

    def test_sira_ve_sayi_hatalari(self):
        for ham, sebep in (
            ("+3,20; ±0,00", "ters sırada"),
            ("0; 3; 3", "aynı kotta"),
            ("0; 3; 2; 5", "artan sırayla"),
            ("0", "en az iki durak"),
            ("0; 3,2; x", "3. kot okunamadı"),
            ("; ".join(str(i * 3) for i in range(101)), "en çok 100 durak"),
            ("1;" * 3000, "çok uzun"),
            (True, "noktalı virgülle"),
        ):
            with self.subTest(ham=str(ham)[:30]):
                kotlar, iletiler = katlar.kotlari_oku(ham)
                self.assertIsNone(kotlar)
                self.assertTrue(any(sebep in i for i in iletiler), iletiler)

    def test_mm_ile_yazilan_liste_birimini_soyler(self):
        """Kotun tavanı ya da 11 m kuralı da reddederdi, ama sebebi söylemeden."""
        for ham in ("0; 3200; 6400", "-7000; -3500; 0; 3200", [0, 3200, 6400]):
            with self.subTest(ham=ham):
                kotlar, iletiler = katlar.kotlari_oku(ham)
                self.assertIsNone(kotlar)
                self.assertIn("metreyle yazılır", iletiler[0])
        #  Ondalıksız ama metre:  4 m katlar, 100 m'nin altında 15 m'lik boşluk
        for ham in ("0; 4; 8; 12", "0; 4; 19"):
            with self.subTest(ham=ham):
                self.assertEqual(katlar.kotlari_oku(ham)[1], [])

    def test_kip(self):
        self.assertFalse(katlar.kot_kipi({}))
        self.assertFalse(katlar.kot_kipi({alanlar.DURAK_KOTLARI: "  "}))
        self.assertFalse(katlar.kot_kipi({alanlar.DURAK_KOTLARI: []}))
        self.assertTrue(katlar.kot_kipi({alanlar.DURAK_KOTLARI: "0; 3"}))
        #  Okunamayan değer de kotla giriştir:  kapı onun hatasını söyler
        self.assertTrue(katlar.kot_kipi({alanlar.DURAK_KOTLARI: 0}))


class Sema(unittest.TestCase):
    def test_kiplerin_alanlari(self):
        self.assertEqual(gorunum.kip_disi(True), TURETILEN)
        self.assertEqual(gorunum.kip_disi(False), KOT_KUTULARI)
        for k in KOT_KUTULARI:
            a = alanlar.ALAN[k]
            self.assertEqual((a.birim, a.tur, a.isaretli, a.opsiyonel), ("m", "sayi", True, True), k)
        #  Kipi belirleyen alan iki kipte de okunur;  tavan döşemesi de
        self.assertIsNone(alanlar.ALAN[alanlar.DURAK_KOTLARI].kip)
        self.assertIsNone(alanlar.ALAN["tavan_dosemesi"].kip)
        self.assertEqual(alanlar.ALAN["md_zemini_kotu"].yerlesim, "daireli")

    def test_kot_alanlari_hesabin_girdi_listesine_girmez(self):
        """Sözleşmesi CIZ:  mukavemetin girdisi türeyen sayılardır — kot hesabın
        çıktısına ( girdi listesi ) boş değerle girmesin ( altın )."""
        for k in KOT_KUTULARI | {alanlar.DURAK_KOTLARI, "tavan_dosemesi"}:
            self.assertEqual(alanlar.ALAN[k].sozlesme, alanlar.CIZ, k)

    def test_form_kipi_soyler(self):
        k = gorunum.form()["kot_kipi"]
        self.assertEqual(k["alan"], alanlar.DURAK_KOTLARI)
        self.assertEqual(set(k["gizli"]["kotla"]), TURETILEN)
        self.assertEqual(set(k["gizli"]["olcuyle"]), KOT_KUTULARI)
        self.assertEqual(uygulama_istegi.alanlar()["kot_kipi"], k)

    def test_kotlar_bina_olcusu(self):
        """Düzeltme öner:  kotlar ve tavan döşemesi binanındır — en sonda, işaretli."""
        self.assertLessEqual(KOT_KUTULARI | {"tavan_dosemesi"}, care_uclari.BINA)


class Kapi(unittest.TestCase):
    def _oku(self, v):
        return uygulama_istegi.asansor_girdileri(v)[0][0]

    def test_olcuyle_giriste_kot_okunmaz(self):
        a = self._oku(_istek(seyir_mesafesi="21", kuyu_dibi_kotu="abc", kuyu_tavani_kotu="+25,20"))
        self.assertEqual(a["seyir_mesafesi"], 21)
        self.assertIsNone(a["kuyu_dibi_kotu"])  # bozuk değer projeyi durdurmaz
        self.assertIsNone(a["kuyu_tavani_kotu"])

    def test_kotla_giriste_turetilen_okunmaz_kot_okunur(self):
        v = test_yerlesim_saglamligi.kotla(test_yerlesim_saglamligi.standart_istek(1000, False, "Sağ"))
        v["asansorler"][0].update(seyir_mesafesi="abc", kuyu_dibi="1600", durak_adedi="8")
        a = self._oku(v)
        for k in ("seyir_mesafesi", "kuyu_dibi", "durak_adedi"):
            self.assertIsNone(a[k], k)
        self.assertEqual(
            (a["kuyu_dibi_kotu"], a["kuyu_tavani_kotu"], a["md_zemini_kotu"]), (-1.6, 25.2, 24.15)
        )
        self.assertEqual(a[alanlar.DURAK_KOTLARI], v["asansorler"][0][alanlar.DURAK_KOTLARI])

    def test_bozuk_kot_alanin_adiyla_reddedilir(self):
        for alan, deger, sebep in (
            (alanlar.DURAK_KOTLARI, "0; 3; 2", "artan sırayla"),
            (alanlar.DURAK_KOTLARI, "0; 3200; 6400", "metreyle yazılır"),
            ("kuyu_dibi_kotu", "8,80m", "okunamadı"),
            ("kuyu_tavani_kotu", "1.200", "belirsiz"),
        ):
            with self.subTest(alan=alan, deger=deger):
                v = test_yerlesim_saglamligi.kotla(test_yerlesim_saglamligi.standart_istek(1000, True, "Sağ"))
                v["asansorler"][0][alan] = deger
                with self.assertRaises(uygulama_istegi.GecersizGirdi) as k:
                    uygulama_istegi.asansor_girdileri(v)
                (h,) = k.exception.hatalar
                self.assertTrue(h.startswith(alanlar.ALAN[alan].etiket), h)
                self.assertIn(sebep, h)

    def test_kip_asansor_basina(self):
        """Çok asansörlüde biri kotla, öbürü ölçüyle girilebilir ( 1. aşama:  asansör başına )."""
        v = test_yerlesim_saglamligi.kotla(test_yerlesim_saglamligi.standart_istek(1000, True, "Sağ"))
        v["asansorler"].append(
            dict(test_yerlesim_saglamligi.standart_istek(1000, True, "Sağ")["asansorler"][0])
        )
        v["asansorler"][1].update(seyir_mesafesi="30", kuyu_dibi_kotu="abc")
        v["asansorler"][0]["seyir_mesafesi"] = "abc"
        a, _o = uygulama_istegi.asansor_girdileri(v)
        self.assertEqual((a[0]["kuyu_dibi_kotu"], a[1]["kuyu_dibi_kotu"]), (-1.6, None))
        self.assertEqual((a[0]["seyir_mesafesi"], a[1]["seyir_mesafesi"]), (None, 30))

    def test_eski_istekte_yeni_alan_yok(self):
        """Kot alanı yazılmamış istek bugünkü gibi okunur:  yeni anahtar doğmaz
        ( hesap ve çizim bit bit aynı — altın testleri )."""
        a = self._oku(test_yerlesim_saglamligi.standart_istek(1000, True, "Sağ"))
        self.assertEqual(set(a) & (KOT_KUTULARI | {alanlar.DURAK_KOTLARI, "tavan_dosemesi"}), set())


if __name__ == "__main__":
    unittest.main()

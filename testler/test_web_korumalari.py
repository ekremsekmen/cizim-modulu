"""WEB KORUMALARI ( 17 Eki ) — web'e açılan programda tek bir istek bir işçiyi
kilitlememeli, programın iç yapısı kullanıcıya gitmemeli:

  -  istek boyutu sınırı ( main.IstekBoyutu, 1 MB ):  5 MB'lık asansör adı çizim
     işçisini 3,9 sn tutuyordu
  -  durak sınırı ( kopru.DURAK_AZAMI, 100 ):  1.000 durak dakikalarca
  -  fiziksel tavan ( alanlar.BIRIM_AZAMI ):  10¹² mm'lik kuyu genişliği yazı
     yerleştiricinin ızgarasında milyarlarca hücre kurup belleği bitirdi
     ( geliştirme bilgisayarı çöktü )
  -  beklenmeyen hata ( uc_ortak.hata_iletisi ):  web sunucusunda Python
     metni yerine genel ileti;  girdi reddi her zaman kendi metniyle"""

import asyncio
import json
import time
import unittest
from unittest import mock

import main
from cizim import kopru
from tasarim import alanlar
from testler import test_yerlesim_saglamligi
from uclar import cizim_uclari
from uclar import uygulama_uclari
from uclar import uygulama_istegi
from uclar.uc_ortak import GENEL_HATA, hata_iletisi


def _calistir(govde_parcalari, basliklar=(), azami=100):
    """IstekBoyutu'nu küçük bir sınırla çalıştırır:  ( durum, gövde, içteki uygulamanın aldığı gövde )."""
    alinan = []

    async def ic(kapsam, al, gonder):
        govde = b""
        while True:
            m = await al()
            govde += m.get("body", b"")
            if not m.get("more_body"):
                break
        alinan.append(govde)
        await gonder({"type": "http.response.start", "status": 200, "headers": []})
        await gonder({"type": "http.response.body", "body": b"tamam"})

    mesajlar = [
        {"type": "http.request", "body": p, "more_body": i < len(govde_parcalari) - 1}
        for i, p in enumerate(govde_parcalari)
    ]
    giden = []

    async def al():
        return mesajlar.pop(0)

    async def gonder(m):
        giden.append(m)

    kapsam = {"type": "http", "method": "POST", "headers": list(basliklar)}
    asyncio.run(main.IstekBoyutu(ic, azami=azami)(kapsam, al, gonder))
    durum = giden[0]["status"]
    return durum, b"".join(m.get("body", b"") for m in giden[1:]), alinan


class IstekBoyutu(unittest.TestCase):
    def test_kucuk_istek_aynen_gecer(self):
        durum, govde, alinan = _calistir([b'{"a":', b"1}"])
        self.assertEqual(durum, 200)
        self.assertEqual(alinan, [b'{"a":1}'])

    def test_basligi_buyuk_istek_okunmadan_reddedilir(self):
        durum, govde, alinan = _calistir([b"{}"], basliklar=[(b"content-length", b"5000")])
        self.assertEqual(durum, 413)
        self.assertEqual(alinan, [])
        self.assertIn("İstek çok büyük", json.loads(govde)["hata"][0])

    def test_parca_parca_gelen_buyuk_govde_reddedilir(self):
        """Başlıksız ( parça parça ) gövde de sayılır."""
        durum, govde, alinan = _calistir([b"x" * 60, b"x" * 60])
        self.assertEqual(durum, 413)
        self.assertEqual(alinan, [])

    def test_sinir_bir_megabayt(self):
        self.assertEqual(main.ISTEK_AZAMI, 1024 * 1024)


class DurakSiniri(unittest.TestCase):
    def test_yuz_durak_cizilir_yuz_bir_reddedilir(self):
        for durak, gecer in ((100, True), (101, False)):
            with self.subTest(durak=durak):
                v = test_yerlesim_saglamligi.standart_istek(
                    1000, True, "Sağ", durak_adedi=durak, seyir_mesafesi=round((durak - 1) * 3.3, 1)
                )
                g, _A, hata = test_yerlesim_saglamligi.duzen_girdisi(v)
                if gecer:
                    self.assertIsNotNone(g, hata)
                else:
                    self.assertIsNone(g)
                    self.assertIn(
                        f"Durak adedi:  en çok {kopru.DURAK_AZAMI} adet olabilir ( 101 girildi ).", hata
                    )


class FizikselTavan(unittest.TestCase):
    def test_her_sayi_alaninin_tavani_var(self):
        sayi = [a.anahtar for a in alanlar.ALANLAR if a.tur == "sayi"]
        self.assertEqual([k for k in sayi if alanlar.AZAMI.get(k) is None], [])

    def test_tavan_gecer_ustu_hesapta_ve_cizimde_reddedilir(self):
        ust = alanlar.AZAMI["kuyu_genisligi"]
        self.assertEqual(ust, 20_000)
        ileti = "en çok 20.000 mm olabilir"
        for deger in (ust + 1, 1e12):
            v = test_yerlesim_saglamligi.standart_istek(1000, True, "Sağ")
            v["asansorler"][0]["kuyu_genisligi"] = deger
            for ad, uc in (
                ("hesap", uygulama_uclari.api_uygulama_coklu),
                ("cizim", cizim_uclari.api_cizimler),
            ):
                with self.subTest(deger=deger, uc=ad):
                    t = time.perf_counter()
                    yanit = json.loads(uc(v).body)
                    self.assertLess(time.perf_counter() - t, 2.0)
                    self.assertFalse(yanit["aktif"])
                    self.assertEqual(len([h for h in yanit["hata"] if ileti in h]), 1, yanit["hata"])
        #  Tavanın kendisi kapıdan geçer ( çizilmesi başka kurallara kalır )
        v = test_yerlesim_saglamligi.standart_istek(1000, True, "Sağ")
        v["asansorler"][0]["kuyu_genisligi"] = ust
        self.assertFalse(
            any(ileti in h for h in json.loads(cizim_uclari.api_cizimler(v).body).get("hata") or [])
        )

    def test_sayisal_secim_listenin_ustunu_cizime_gecirmez(self):
        """21 Eki bulanık tarama:  kat kapısı genişliği SEÇİM alanı olduğu için
        tavansızdı — 10¹² mm'de hesap "geçersiz seçim" derken çizim köprüsü
        planı kurup belleği bitiriyordu ( 2,5 GB, işlem öldürüldü ).  Sayıyla
        okunan her seçim alanında hesap reddeder, iki uç da saniyeler içinde
        yanıt verir ( beyan yükü çizimde yalnız veri tablosundadır — çizim
        kurulur, hesap durur );  listenin en büyüğü kapıdan geçer."""
        self.assertEqual(alanlar.SECIM_AZAMI["kapi_genisligi"], 1400)
        for alan in ("kapi_genisligi", "halat_capi", "reg_halat_capi", "beyan_hizi", "beyan_yuku"):
            v = test_yerlesim_saglamligi.standart_istek(1000, True, "Sağ")
            v["asansorler"][0][alan] = 1e12
            for ad, uc in (
                ("hesap", uygulama_uclari.api_uygulama_coklu),
                ("cizim", cizim_uclari.api_cizimler),
            ):
                with self.subTest(alan=alan, uc=ad):
                    t = time.perf_counter()
                    yanit = json.loads(uc(v).body)
                    self.assertLess(time.perf_counter() - t, 2.0)
                    self.assertFalse(yanit["aktif"] if ad == "hesap" else yanit.get("hesap"))
        v = test_yerlesim_saglamligi.standart_istek(1000, True, "Sağ")
        v["asansorler"][0]["kapi_genisligi"] = 1e12
        hata = json.loads(cizim_uclari.api_cizimler(v).body)["hata"]
        self.assertIn("Kat kapısı genişliği:  en çok 1.400 mm olabilir", hata[0])
        self.assertIsNone(alanlar.secim_asimi("kapi_genisligi", 1400))

    def test_verim_biri_asamaz(self):
        self.assertEqual(alanlar.AZAMI["makine_verimi"], 1)

    def test_elektrik_alaninin_tavani_tek_iletiyle(self):
        """Kesit ve motor gücünün avan aralığı da var:  tavanı aşan değer tavan
        iletisiyle durur ( iki denetim birbirini atlayınca 1.001 mm² geçiyordu ),
        aralığın dışı ama tavanın altı avan iletisiyle."""
        for alan, deger, parca in (
            ("kolon_kesit", 1001, "en çok 1.000 mm²"),
            ("makine_kesit", 1e9, "en çok 1.000 mm²"),
            ("motor_gucu", 600, "geçerli aralık"),
            ("motor_gucu", 1e9, "en çok 5.000 kW"),
        ):
            with self.subTest(alan=alan, deger=deger):
                v = test_yerlesim_saglamligi.standart_istek(1000, False, "Sağ")
                v["asansorler"][0][alan] = deger
                hata = json.loads(uygulama_uclari.api_uygulama_coklu(v).body).get("hata") or []
                self.assertEqual(len(hata), 1, hata)
                self.assertIn(parca, hata[0])

    def test_konsollar_ust_uste_binemez(self):
        """0,001 mm'lik konsol aralığı 21 milyon konsol diziyordu:  konsolun
        kendi boyundan ( kabin 300, ağırlık 100 ) küçük aralık hesapta da
        çizimde de reddedilir;  boyun kendisi geçer."""
        for alan, boy in (("kabin_konsol_arasi", 300), ("agirlik_konsol_arasi", 100)):
            for deger, gecer in ((0.001, False), (boy - 1, False), (boy, True)):
                v = test_yerlesim_saglamligi.standart_istek(1000, True, "Sağ")
                v["asansorler"][0][alan] = deger
                for ad, uc in (
                    ("hesap", uygulama_uclari.api_uygulama_coklu),
                    ("cizim", cizim_uclari.api_cizimler),
                ):
                    with self.subTest(alan=alan, deger=deger, uc=ad):
                        hata = json.loads(uc(v).body).get("hata") or []
                        ret = [h for h in hata if "konsollar üst üste biner" in h]
                        self.assertEqual(len(ret), 0 if gecer else 1, hata)


class BeklenmeyenHata(unittest.TestCase):
    def test_girdi_reddi_her_zaman_kendi_metniyle(self):
        with mock.patch.dict("os.environ", {"AVAN_SUNUCU": "1"}):
            self.assertEqual(
                hata_iletisi("HESAP HATASI", ValueError("Kabin sığmıyor")), "HESAP HATASI: Kabin sığmıyor"
            )

    def test_kendi_bilgisayarinda_metin_gorunur(self):
        with mock.patch.dict("os.environ", {"AVAN_SUNUCU": ""}):
            self.assertEqual(hata_iletisi("ÇİZİM HATASI", KeyError("x")), "ÇİZİM HATASI: 'x'")

    def test_web_sunucusunda_genel_ileti(self):
        """Uç programın kendi hatasında Python metnini değil genel iletiyi
        döndürür;  önek kalır ( arayüz testleri ona bakar )."""
        with (
            mock.patch.object(uygulama_istegi, "asansor_girdileri", side_effect=KeyError("ic_alan")),
            mock.patch.dict("os.environ", {"AVAN_SUNUCU": "1"}),
            self.assertLogs(cizim_uclari.log, level="ERROR"),
        ):
            yanit = json.loads(cizim_uclari.api_cizimler({"asansorler": [{}]}).body)
        self.assertEqual(yanit, {"aktif": False, "hata": [f"ÇİZİM HATASI: {GENEL_HATA}"]})
        self.assertNotIn("ic_alan", yanit["hata"][0])


class BozukGovde(unittest.TestCase):
    """Bozuk gövde programın hatası sayılmaz:  kendi iletisiyle reddedilir
    ( eskiden liste çizim adı "unhashable type", sayı kapak "not iterable"
    ile uçta beklenmeyen hata kaydı düşüyordu ).  Uç taraması, 20 Eki."""

    def test_cizim_adi_metin_degilse_bilinmeyen_cizim(self):
        for uc in (cizim_uclari.api_olcu, cizim_uclari.api_olcu_degistir):
            for ad in ([], {}, ["kuyu_plani"]):
                with self.subTest(uc=uc.__name__, ad=ad):
                    yanit = json.loads(uc({"cizim": ad, "asansorler": [{}]}).body)
                    self.assertEqual(yanit, {"aktif": False, "hata": ["Bilinmeyen çizim."]})

    def test_secim_alaninda_yanlis_tur_kendi_iletisiyle_reddedilir(self):
        """Seçim alanına mantıksal / liste / sözlük ( yalnız API — form göndermez ):
        21 Eki uç tarama — True seçenek 1 sayılıyordu ( True == 1:  askı oranı
        sessizce 1:1 hesaplanıyor, beyan hızında tampon hesabı TypeError ),
        liste / sözlük makine tipinde sözlük anahtarı olunca hesap da çizim de
        çöküyordu ( uçta beklenmeyen hata kaydı ).  Şimdi hesap "geçersiz seçim"
        der, uçlarda ERROR kaydı yok;  veri tablosu sayı gelen kapı tipinde
        çökmez."""
        for alan, deger in (
            ("aski_orani", True),
            ("beyan_hizi", True),
            ("beyan_yuku", False),
            ("makine_tipi", []),
            ("makine_tipi", {}),
            ("tampon_tipi", {}),
            ("kat_kapisi_tipi", -1),
        ):
            v = test_yerlesim_saglamligi.standart_istek(1000, True, "Sağ")
            v["asansorler"][0][alan] = deger
            with self.subTest(alan=alan, deger=deger):
                with self.assertNoLogs("uclar", level="ERROR"):
                    hesap = json.loads(uygulama_uclari.api_uygulama_coklu(v).body)
                    cizim = json.loads(cizim_uclari.api_cizimler(v).body)
                self.assertFalse(hesap["aktif"])
                self.assertTrue(any("geçersiz seçim" in h for h in hesap["hata"]), hesap["hata"])
                self.assertFalse(cizim.get("kurulamayan"), cizim.get("kurulamayan"))

    def test_sozluk_olmayan_kapak_bos_kapak(self):
        from ciktilar import kapak_cikti

        for kapak in (-5, True, [None], "x"):
            with self.subTest(kapak=kapak):
                self.assertTrue(kapak_cikti.pdf_baytlari(kapak).startswith(b"%PDF"))

    def test_asansor_adindaki_etiket_yazildigi_gibi_basilir(self):
        """Asansör adındaki "<b>" paftanın biçim etiketi sayılmaz:  eskiden
        ayrıştırıcı kırılıyor, PDF hiç üretilemiyordu ( 422 )."""
        from ciktilar import pdf_cikti

        for ad in ("Yolcu <b>A", "A</i> & <br/>"):
            with self.subTest(ad=ad):
                v = test_yerlesim_saglamligi.standart_istek(1000, True, "Sağ")
                v["asansorler"].append(dict(v["asansorler"][0], asansor_adi="İkinci"))
                v["asansorler"][0]["asansor_adi"] = ad
                yanit = uygulama_uclari.indir_uygulama_pdf(v)
                self.assertEqual(yanit.headers.get("content-type"), "application/pdf")
                self.assertIn(ad, pdf_cikti._p(f"ASANSÖR {pdf_cikti._duz(ad)}").getPlainText())


if __name__ == "__main__":
    unittest.main()

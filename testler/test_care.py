"""ÇARE BULUCU ( uclar/care_uclari.py ) — sorunun sayılı, doğrulanmış çaresi.

Değişmezler:
  1.  Gösterilen her çare BAĞIMSIZ olarak yeniden sınanır:  uygulanınca
      sorunu giderir, yeni sorun doğurmaz, hesabı kötüleştirmez ( hesap
      durmaz, "uygun değil" bölüm artmaz ).  Çözücü tahminle öneri vermez.
      "Yeni" sayılmayan tek şey:  bugün de var olan ama denetim ilk hatada
      durduğu için gizli kalan sorun ( cizim_uclari.genis_sorunlar ) — o
      öneride ortaya_cikan olarak söylenir.
  2.  Sorunun açığı ( sorun.Sorun.fark ) sorun varken ≤ 0 — türevin yönü
      buna dayanır.
  3.  Kullanıcının örnekleri ( 19 Eki ölçümü, örnek proje ):  kuyu 2300 →
      kuyu genişliğinin sınırı 2230 ( son değişiklik — türevin göremediği
      korkuluk sıçraması ) ve son kat 4515 ( türev );  kuyu dibi 1300 →
      kuyu dibi 1415 dört sorunu birden giderir;  kuyu dibi 1000 ( girdi
      çizime çevrilemiyor ) → kuyu dibi 1415.
"""

import json
import unittest
from unittest import mock

from testler import test_grup
from testler import test_yerlesim_saglamligi
from uclar import care_uclari
from uclar import cizim_uclari
from uclar import uygulama_istegi
from hesap_girdi import ASANSOR, ASANSOR_MD, ORTAK, ORTAK_MD, SABITLER

#  Örnek proje ( on-yuz/src/lib/ornek.ts — gerçekte var olan asansör )
ORNEK = dict(
    beyan_yuku="1275",
    beyan_hizi="1.6",
    agirlik_yeri="Sol",
    kuyu_genisligi="2200",
    kuyu_derinligi="2700",
    durak_adedi="15",
    seyir_mesafesi="42",
    son_kat_yuksekligi="4250",
    kuyu_dibi="1750",
    kabin_genisligi="1260",
    kabin_derinligi="2100",
    kapi_genisligi="1100",
    kabin_yana_kaciklik="30",
    kabin_ic_yuksekligi="2100",
    kabin_agirligi="",
    ray_kapi_arasi="1370",
    kabin_konsol_arasi="1800",
    agirlik_konsol_arasi="1800",
    kabin_ray_arasi="1550",
    agirlik_derinligi="100",
    agirlik_malzemesi="Pik Döküm",
    agirlik_ray_arasi="1100",
    halat_capi="8",
    kabin_kasnak_capi="320",
    kanal_isleme="Sertleştirilmiş",
    denge_zinciri="Var",
    motor_gucu="12,5",
    tahrik_kasnak_capi="320",
    tampon_tipi="Hidrolik  ( enerji yutmalı )",
    kabin_tampon_boyu="630",
    kabin_tampon_ezilme="180",
    agirlik_tampon_ezilme="180",
)

#  ( taban , değişen alan , değer ) — her biri bir sorun sınıfı
VAKALAR = (
    ("ornek", "kuyu_genisligi", "2300"),
    ("ornek", "kuyu_dibi", "1300"),
    ("ornek", "kuyu_genisligi", "2100"),
    ("ornek", "kuyu_dibi", "1000"),
    ("mrl", "kabin_yana_kaciklik", "0"),
    ("mrl", "kapi_genisligi", "1200"),
    ("mrl", "durak_adedi", "30"),
    ("md", "son_kat_yuksekligi", "3200"),
    ("ornek", "agirlik_yeri", "Arka"),
    #  Makine dairesizde 1:1 çizilmez — çaresi askı oranı ( 1 Kas )
    ("mrl", "aski_orani", "1"),
)


def _taban(ad):
    if ad == "ornek":
        return {"asansorler": [dict(ORNEK)], "proje_geneli": {}, "sabitler": {}}
    md = ad == "md"
    return {
        "asansorler": [dict(ASANSOR_MD if md else ASANSOR, siginma_tipi_dip="Yatarak")],
        "proje_geneli": dict(ORTAK_MD if md else ORTAK),
        "sabitler": dict(SABITLER),
    }


def _vaka(ad, alan, deger):
    taban = _taban(ad)
    veri = json.loads(json.dumps(taban))
    veri["asansorler"][0][alan] = deger
    return veri, {"asansor": taban["asansorler"][0], "proje_geneli": taban["proje_geneli"]}


def _oneriler(r, parca):
    """Metni `parca`yı içeren sorunun önerileri:  { anahtar:  ( yeni , yöntem , kaç sorun ) }."""
    c = next(c for c in r["careler"] if parca in c["metin"])
    return {o["anahtar"]: (o["yeni"], o["yontem"], len(o["gider"])) for o in c["oneriler"]}


class Care(unittest.TestCase):
    _sonuc = {}

    @classmethod
    def coz(cls, ad, alan, deger):
        if (ad, alan, deger) not in cls._sonuc:
            veri, onceki = _vaka(ad, alan, deger)
            cls._sonuc[(ad, alan, deger)] = (veri, care_uclari.coz(veri, 0, onceki))
        return cls._sonuc[(ad, alan, deger)]

    def test_her_care_bagimsiz_sinanir(self):
        for vaka in VAKALAR:
            veri, r = self.coz(*vaka)
            once = care_uclari._durum(veri, 0)
            ortulu = {care_uclari.kimlik(h) for h in cizim_uclari.genis_sorunlar(veri, 0)} - set(once[0])
            self.assertTrue(r["careler"], vaka)
            #  Vakaların hepsi bütçenin içinde biter ( kesilmiş arama değil )
            self.assertTrue(r["tamamlandi"], (vaka, r["neden"]))
            self.assertLessEqual(r["sinama"], care_uclari.AZAMI_SINAMA, vaka)
            for c in r["careler"]:
                for o in c["oneriler"]:
                    with self.subTest(vaka=vaka, sorun=c["metin"][:50], care=(o["anahtar"], o["yeni"])):
                        sonra = care_uclari._durum(care_uclari._yaz(veri, 0, o["anahtar"], o["yeni"]), 0)
                        s = care_uclari._sonucu(once, sonra, ortulu)
                        self.assertIn(care_uclari.kimlik(c["metin"]), s["gider"])
                        self.assertEqual(s["yeni"], [])
                        self.assertEqual(sorted(s["ortaya"]), sorted(o["ortaya_cikan"]))
                        self.assertFalse(s["kotu"])
                        self.assertNotIn(o["anahtar"], care_uclari.DISI)

    def test_sorun_varken_acik_eksi(self):
        for vaka in VAKALAR:
            veri, _r = self.coz(*vaka)
            asansorler, ortak = uygulama_istegi.asansor_girdileri(veri)
            _g, hata = cizim_uclari.asansor_girdisi(asansorler, ortak, None, "", 0)
            for h in hata:
                f = getattr(h, "fark", None)
                if f is not None:
                    self.assertLessEqual(float(f), 1e-6, (vaka, str(h)))

    def test_korkuluk_sicramasi_ve_son_kat(self):
        _veri, r = self.coz("ornek", "kuyu_genisligi", "2300")
        o = _oneriler(r, "Korkuluk – kuyu tavanı")
        self.assertEqual(o["kuyu_genisligi"][:2], (2230.0, "son değişiklik"))
        self.assertEqual(o["son_kat_yuksekligi"][:2], (4515.0, "türev"))

    def test_kuyu_dibi_dort_sorunu_birden_giderir(self):
        _veri, r = self.coz("ornek", "kuyu_dibi", "1300")
        self.assertEqual(len(r["careler"]), 4)
        for c in r["careler"]:
            o = {x["anahtar"]: x for x in c["oneriler"]}
            self.assertEqual((o["kuyu_dibi"]["yeni"], len(o["kuyu_dibi"]["gider"])), (1415.0, 4), c["metin"])
            #  Bina ölçüsü:  işaretli ve bina olmayan çarelerden sonra
            self.assertTrue(o["kuyu_dibi"]["bina"])

    def test_cizime_cevrilemeyen_girdinin_caresi(self):
        _veri, r = self.coz("ornek", "kuyu_dibi", "1000")
        o = _oneriler(r, "Kabin tamponu baba yüksekliği")
        self.assertEqual(o["kuyu_dibi"][:2], (1415.0, "son değişiklik"))

    def test_secim_duzeltmesi(self):
        """Arkadaki ağırlıkla kabin altı askı çizilemez:  seçim düzeltmesi
        askı düzenini kabin üstüne alır ( türevin göremediği seçim )."""
        _veri, r = self.coz("ornek", "agirlik_yeri", "Arka")
        o = _oneriler(r, "Arkadaki karşı ağırlıkla")
        self.assertEqual(o["aski_duzeni"][:2], ("Kabin üstü", "seçim"))

    def test_mrl_de_bir_bir_askinin_caresi_aski_orani(self):
        """30 Eki taraması:  ileti "askı oranını 2 seçin" diyordu, öneri gelmiyordu
        ( 27 çaresiz sorun )."""
        _veri, r = self.coz("mrl", "aski_orani", "1")
        o = _oneriler(r, "1:1 askı çizilmez")
        self.assertEqual((str(o["aski_orani"][0]), o["aski_orani"][1]), ("2", "seçim"))

    def test_cizimsiz_hesapta_eksik_kalan_duzeltmeyle_bozulmus_sayilmaz(self):
        """30 Eki taraması:  "askı kabin altı → kabin üstü" ağırlık raylarını uygun
        değil gösteriyordu.  Askı rayı bozmaz:  çizim kurulamayınca dolgu ölçülemiyor,
        bölüm denetlenmeden "UYGUNDUR" yazıyordu ( 1 Kas ).  Artık bölüm o hâlde
        EKSİK;  öneri kalır ve hesapta "ortaya çıkan" bölüm yoktur."""
        v = test_yerlesim_saglamligi.standart_istek(1275, True, "Arka", aski_duzeni="Kabin altı")
        v["asansorler"][0]["kuyu_derinligi"] = test_yerlesim_saglamligi.KABIN[1275][1] + 700
        once = care_uclari._durum(v, 0)
        self.assertIn("agirlik_raylari", once[3])
        self.assertFalse(once[4])  # hesap çizimin bütün ölçülerini alamadı
        r = care_uclari.coz(v, 0)
        o = _oneriler(r, "Arkadaki karşı ağırlıkla")
        self.assertEqual(o["aski_duzeni"][:2], ("Kabin üstü", "seçim"))
        c = next(c for c in r["careler"] if "Arkadaki karşı ağırlıkla" in c["metin"])
        self.assertEqual(
            next(x for x in c["oneriler"] if x["anahtar"] == "aski_duzeni")["hesapta_ortaya_cikan"], []
        )

    def test_hesapta_ortaya_cikan_dogru_ve_sonda(self):
        """Her önerinin "hesapta ortaya çıkan"ı uygulanınca gerçekten yeni uygun
        olmayan bölümlerdir;  onları çıkaran öneriler temizlerden sonra gelir."""
        for vaka in VAKALAR:
            veri, r = self.coz(*vaka)
            once = care_uclari._durum(veri, 0)
            for c in r["careler"]:
                sira = [bool(o["hesapta_ortaya_cikan"]) for o in c["oneriler"]]
                self.assertEqual(sira, sorted(sira), (vaka, c["metin"][:50]))
                for o in c["oneriler"]:
                    sonra = care_uclari._durum(care_uclari._yaz(veri, 0, o["anahtar"], o["yeni"]), 0)
                    #  Yalnız bugün uygun görünen bölümler ( hesap bugün durmuşsa yok )
                    beklenen = sorted(sonra[3] - once[3]) if once[1] and sonra[1] else []
                    self.assertEqual(beklenen, o["hesapta_ortaya_cikan"], (vaka, o["anahtar"]))

    def test_tek_kuyuda_ikinci_asansorde_kuyunun_ortak_girdisi_onerilir(self):
        """Kuyunun ortak girdisi 1. asansörden okunur ( kapı ):  aday yalnız seçili asansöre
        yazılınca 2. asansörde hiç etki etmiyor, "düzeltme bulunamadı" deniyordu ( 9 Kas ).
        Öneri uygulanınca ( ön yüz ikisine birden yazar ) sorun gider."""
        v = test_grup.ikili(1000, "Sağ", 800, "Sol", son_kat_yuksekligi=3900)
        v.setdefault("sabitler", {})
        v["asansor"] = 1
        r = care_uclari.coz(json.loads(json.dumps(v)), 1)
        oneriler = [o for c in r["careler"] for o in c["oneriler"] if o["anahtar"] == "son_kat_yuksekligi"]
        self.assertTrue(oneriler, r["careler"])
        y = json.loads(json.dumps(v))
        y["asansorler"][0]["son_kat_yuksekligi"] = oneriler[0]["yeni"]
        once = {h for h in json.loads(cizim_uclari.api_cizimler(json.loads(json.dumps(v))).body)["hata"]}
        sonra = set(json.loads(cizim_uclari.api_cizimler(y).body).get("hata") or [])
        self.assertTrue(set(oneriler[0]["gider"]) <= once - sonra, (oneriler[0], once, sonra))

    def test_bina_olcusu_en_sonda(self):
        for vaka in VAKALAR:
            _veri, r = self.coz(*vaka)
            for c in r["careler"]:
                turev = [o["bina"] for o in c["oneriler"] if o["yontem"] == "türev"]
                self.assertEqual(turev, sorted(turev), (vaka, c["metin"][:50]))

    def test_yavas_bilgisayarda_ayni_careler(self):
        """BÜTÇE SINAMA SAYISIDIR, SAAT DEĞİL:  her sınama saati 1 sn
        ilerletince ( yavaş, yüklü bilgisayar ) çareler aynı kalır.  6 sn'lik
        duvar saatiyle bu vaka türev aşamasında kesiliyor, "Yatarak" sığınma
        çaresi düşüyordu ( ölçüldü 20 Eki )."""
        vaka = ("ornek", "kuyu_dibi", "1300")
        veri, r = self.coz(*vaka)
        asil, saat = care_uclari._durum, [0.0]

        def yavas(v, i):
            saat[0] += 1.0
            return asil(v, i)

        sahte = mock.Mock(time=lambda: saat[0], monotonic=lambda: saat[0])
        with mock.patch.object(care_uclari, "_durum", yavas), mock.patch.object(care_uclari, "time", sahte):
            y = care_uclari.coz(veri, 0, _vaka(*vaka)[1])
        self.assertEqual(y["careler"], r["careler"])
        self.assertEqual((y["sinama"], y["tamamlandi"]), (r["sinama"], True))

    def test_butce_biterse_yanit_soyler(self):
        """Bütçeye ya da güvenlik süresine takılan arama "tamamlandı" demez;
        bulduğu çareler yine sınanmıştır."""
        veri, onceki = _vaka("ornek", "kuyu_genisligi", "2300")
        r = care_uclari.coz(veri, 0, onceki, care_uclari._Butce(sinama=3))
        self.assertEqual((r["tamamlandi"], r["neden"], r["sinama"]), (False, "sinama", 3))
        r = care_uclari.coz(veri, 0, onceki, care_uclari._Butce(sure=-1.0))
        self.assertEqual((r["tamamlandi"], r["neden"], r["sinama"]), (False, "sure", 0))

    def test_kimlik_sayilardan_ve_sonundan_bagimsiz(self):
        self.assertEqual(
            care_uclari.kimlik(
                "Karşı ağırlık en üst konumunda tavana çarpıyor:  karşı ağırlığın üst pateni 3599.6"
            ),
            care_uclari.kimlik(
                "Karşı ağırlık en üst konumunda tavana çarpıyor:  karşı ağırlık çerçevesi 3610"
            ),
        )
        self.assertEqual(
            care_uclari.kimlik("1. – 2. durak arası 1000 mm:  kat kapısı"),
            care_uclari.kimlik("3. – 4. durak arası 900 mm:  kat kapısı"),
        )
        #  Durak adlarıyla ( KAT_ADLARI_PLANI ):  sayı adları da atılır
        self.assertEqual(
            care_uclari.kimlik("-1 ile 0 katları arası 1000 mm:  kat kapısı"),
            care_uclari.kimlik("2 ile 3 katları arası 900 mm:  kat kapısı"),
        )


if __name__ == "__main__":
    unittest.main()

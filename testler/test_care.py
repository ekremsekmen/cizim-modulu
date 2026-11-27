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
  3.  Kullanıcının örnekleri ( 19 Eki ölçümü, örnek proje ):  kuyu 2400 →
      kuyu genişliğinin sınırı 2350 ( son değişiklik — türevin göremediği
      korkuluk sıçraması:  sağdaki korkuluk 1,10 m olur, regülatör küpeştenin
      9 mm yanında — m.5.4.7.4 d;  24 Kas'a dek kuyu 2300'de soldaki şase
      düşey ölçülüp reddediliyordu, sınır 2230 ve son kat 4515 );  kuyu dibi 1300 →
      kuyu dibi 1415 dört sorunu birden giderir;  kuyu dibi 1000 ( girdi
      çizime çevrilemiyor ) → kuyu dibi 1415.
"""

import json
import unittest
from unittest import mock

from cizim import katlar
from cizim import sorun
from testler import test_grup
from testler import test_yerlesim_saglamligi
from uclar import avan_secici
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
    #  Korkuluk sıçraması ( test_korkuluk_sicramasi )
    ("ornek_alcak", "kuyu_genisligi", "2400"),
    ("ornek", "kuyu_dibi", "1300"),
    ("ornek", "kuyu_genisligi", "2100"),
    ("ornek", "kuyu_dibi", "1000"),
    ("mrl", "kabin_yana_kaciklik", "0"),
    #  Kanat cebi kuyuya sığmaz ( 1.200'ü 23 Kas'tan beri yerleşim kurtarması kurar:
    #  kapı kaçıklığı boş — cizim/kopru )
    ("mrl", "kapi_genisligi", "1300"),
    ("mrl", "durak_adedi", "30"),
    ("md", "son_kat_yuksekligi", "3200"),
    ("ornek", "agirlik_yeri", "Arka"),
    #  Makine dairesizde 1:1 çizilmez — çaresi askı oranı ( 1 Kas )
    ("mrl", "aski_orani", "1"),
)


def _taban(ad):
    if ad == "ornek":
        return {"asansorler": [dict(ORNEK)], "proje_geneli": {}, "sabitler": {}}
    if ad == "ornek_alcak":
        #  Son kat 4.100:  iki korkuluk 0,70 m'yken kuyu üstü yeter ( en az 4.017 ), 1,10 m'ye 4.130 gerekir
        return {"asansorler": [dict(ORNEK, son_kat_yuksekligi="4100")], "proje_geneli": {}, "sabitler": {}}
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
            once = care_uclari.girdi_durumu(veri, 0)
            ortulu = {care_uclari.kimlik(h) for h in cizim_uclari.genis_sorunlar(veri, 0)} - set(once[0])
            self.assertTrue(r["careler"], vaka)
            #  Vakaların hepsi bütçenin içinde biter ( kesilmiş arama değil )
            self.assertTrue(r["tamamlandi"], (vaka, r["neden"]))
            self.assertLessEqual(r["sinama"], care_uclari.AZAMI_SINAMA, vaka)
            for c in r["careler"]:
                for o in c["oneriler"]:
                    with self.subTest(vaka=vaka, sorun=c["metin"][:50], care=(o["anahtar"], o["yeni"])):
                        sonra = care_uclari.girdi_durumu(
                            care_uclari.girdi_yaz(veri, 0, o["anahtar"], o["yeni"]), 0
                        )
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

    def test_korkuluk_sicramasi(self):
        #  Kuyu 2.230'dan sonra soldaki boşluk 500'ü aşar, korkuluk 0,70 → 1,10 m ( m.5.4.7.4 b ):
        #  kuyu tavanına 0,30 m için son kat 4.130 gerekir.  Kuyu genişliğinde türev yok ( sıçrama ),
        #  sınırı son değişiklikten;  kuyu tavanınınki türevden.  ( 24 Kas'a dek bu vaka son kat
        #  4.250'de kuyu 2.400'dü:  regülatör sağ küpeştenin 9 mm yanındaydı — küpeşte tavana asılı
        #  parçalardan da içeri alınınca o düzen kurulur )
        _veri, r = self.coz("ornek_alcak", "kuyu_genisligi", "2400")
        o = _oneriler(r, "Korkuluk – tavan parçası")
        self.assertEqual(o["kuyu_genisligi"][:2], (2230.0, "son değişiklik"))
        self.assertEqual(o["son_kat_yuksekligi"][:2], (4130.0, "türev"))

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
        once = care_uclari.girdi_durumu(v, 0)
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
            once = care_uclari.girdi_durumu(veri, 0)
            for c in r["careler"]:
                sira = [bool(o["hesapta_ortaya_cikan"]) for o in c["oneriler"]]
                self.assertEqual(sira, sorted(sira), (vaka, c["metin"][:50]))
                for o in c["oneriler"]:
                    sonra = care_uclari.girdi_durumu(
                        care_uclari.girdi_yaz(veri, 0, o["anahtar"], o["yeni"]), 0
                    )
                    #  Yalnız bugün uygun görünen bölümler ( hesap bugün durmuşsa yok )
                    beklenen = sorted(sonra[3] - once[3]) if once[1] and sonra[1] else []
                    self.assertEqual(beklenen, o["hesapta_ortaya_cikan"], (vaka, o["anahtar"]))

    def test_tek_kuyuda_ikinci_asansorde_kuyunun_ortak_girdisi_onerilir(self):
        """Kuyunun ortak girdisi 1. asansörden okunur ( kapı ):  aday yalnız seçili asansöre
        yazılınca 2. asansörde hiç etki etmiyor, "düzeltme bulunamadı" deniyordu ( 9 Kas ).
        Öneri uygulanınca ( ön yüz ikisine birden yazar ) sorun gider.  ( 24 Kas:  küpeşte tavana
        asılı parçalardan da içeri alınınca 3.900 kurulur — sorun 3.800'de )"""
        v = test_grup.ikili(1000, "Sağ", 800, "Sol", son_kat_yuksekligi=3800)
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

    def test_alcak_makine_dairesinin_caresi_yukseklik(self):
        """16 Kas:  makine dairesinin yükseklik sorunları ne kadar eksik olduğunu söyler ( fark ) —
        çare bulucu odanın yüksekliğini önerir.  Eskiden düz metindi:  çare çıkmıyor, avan
        seçicisi "sığmıyor" diyordu."""
        taban = _taban("md")
        veri = json.loads(json.dumps(taban))
        veri["proje_geneli"]["md_yukseklik"] = "2000"
        #  Tabliye oda zemininde ( kot farkı yok ):  yoksa oda 2100'e çıkınca tabliyenin üstündeki
        #  yükseklik sorunu ortaya çıkar ( önceden "temiz yükseklik" sorununun arkasında ) — tek
        #  değişiklikli çare olmaz, öneri doğru olarak reddedilir
        veri["asansorler"][0]["tabliye_yuksekligi"] = "0"
        r = care_uclari.coz(
            veri, 0, {"asansor": taban["asansorler"][0], "proje_geneli": taban["proje_geneli"]}
        )
        o = _oneriler(r, "Makine dairesinin temiz yüksekliği 2000 mm < 2100 mm")
        self.assertIn("md_yukseklik", o)
        self.assertGreaterEqual(float(o["md_yukseklik"][0]), 2100)

    def test_yavas_bilgisayarda_ayni_careler(self):
        """BÜTÇE SINAMA SAYISIDIR, SAAT DEĞİL:  her sınama saati 1 sn
        ilerletince ( yavaş, yüklü bilgisayar ) çareler aynı kalır.  6 sn'lik
        duvar saatiyle bu vaka türev aşamasında kesiliyor, "Yatarak" sığınma
        çaresi düşüyordu ( ölçüldü 20 Eki )."""
        vaka = ("ornek", "kuyu_dibi", "1300")
        veri, r = self.coz(*vaka)
        asil, saat = care_uclari.girdi_durumu, [0.0]

        def yavas(v, i):
            saat[0] += 1.0
            return asil(v, i)

        sahte = mock.Mock(time=lambda: saat[0], monotonic=lambda: saat[0])
        with (
            mock.patch.object(care_uclari, "girdi_durumu", yavas),
            mock.patch.object(care_uclari, "time", sahte),
        ):
            y = care_uclari.coz(veri, 0, _vaka(*vaka)[1])
        self.assertEqual(y["careler"], r["careler"])
        self.assertEqual((y["sinama"], y["tamamlandi"]), (r["sinama"], True))

    def test_butce_biterse_yanit_soyler(self):
        """Bütçeye ya da güvenlik süresine takılan arama "tamamlandı" demez;
        bulduğu çareler yine sınanmıştır."""
        veri, onceki = _vaka("ornek_alcak", "kuyu_genisligi", "2400")
        r = care_uclari.coz(veri, 0, onceki, care_uclari.Butce(sinama=3))
        self.assertEqual((r["tamamlandi"], r["neden"], r["sinama"]), (False, "sinama", 3))
        r = care_uclari.coz(veri, 0, onceki, care_uclari.Butce(sure=-1.0))
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


def _sahte_durum(anahtar, gider):
    """girdi_durumu'nun sahtesi:  "M" sorunu, anahtar ölçüsü gider( değer ) olunca gider."""
    once = ({"M": "M:  merdiven"}, True, set(), frozenset(), True)
    temiz = ({}, True, set(), frozenset(), True)

    def durum(v, _i):
        x = v["asansorler"][0].get(anahtar, (v.get("proje_geneli") or {}).get(anahtar))
        return temiz if x is not None and gider(float(x)) else once

    return once, durum


class BinaTaramasi(unittest.TestCase):
    """AÇIĞI BİLİNMEYEN SORUNUN BİNA ÖLÇÜSÜ TARAMASI ( 27 Kas — seçici doğruluk planı Adım 2 ):
    türev ve seçimden sonra çaresiz kalan sorunda sorunun çizimine göre bina ölçüleri büyüyen
    adımlarla denenir, ikiye bölünür ( 10 mm / 1 cm );  her aday tam sınanır."""

    ALAN = {a["anahtar"]: a for gr in uygulama_istegi.alanlar()["gruplar"] for a in gr["alanlar"]}
    VERI = {"proje_geneli": {}, "asansorler": [{}]}

    def tara(self, s, degerler, durum, once, gizli=frozenset(), butce=None):
        with mock.patch.object(care_uclari, "girdi_durumu", side_effect=durum) as m:
            r = care_uclari._taramayla(
                self.VERI,
                0,
                once,
                [s],
                degerler,
                set(gizli),
                self.ALAN,
                butce or care_uclari.Butce(sure=float("inf")),
                set(),
                set(),
            )
        return r, m.call_count

    def test_buyur_ve_ikiye_boler(self):
        """1800'de yok, 1837'den sonra gider:  1850 geçer, ikiye bölme 1840'ı bulur ( 1820, 1830 geçmez )."""
        once, durum = _sahte_durum("kuyu_genisligi", lambda x: x >= 1837)
        r, n = self.tara(
            sorun.Sorun("M:  merdiven", ("merdiven",), "kuyu_dibi"), {"kuyu_genisligi": 1800.0}, durum, once
        )
        self.assertEqual(
            [(c["anahtar"], c["yeni"], c["yontem"]) for c in r], [("kuyu_genisligi", 1840.0, "tarama")]
        )
        self.assertEqual(r[0]["gider"], ["M"])
        self.assertLessEqual(n, care_uclari.TARAMA_SORUN_SINAMA)

    def test_kuyu_dibi_kotu_asagi(self):
        """Kot metredir ve kuyu dibi AŞAĞI iner:  −4,70 → −4,83 ( 1 cm çözünürlük )."""
        once, durum = _sahte_durum("kuyu_dibi_kotu", lambda x: x <= -4.83 + 1e-9)
        s = sorun.Sorun("M:  kaide", ("kabin_kaidesi",), "kuyu_kesiti_yan")
        r, _n = self.tara(s, {"kuyu_dibi_kotu": -4.7}, durum, once)
        self.assertEqual([(c["anahtar"], c["yeni"]) for c in r], [("kuyu_dibi_kotu", -4.83)])

    def test_cozulmezse_oneri_yok_ve_pay_asilmaz(self):
        once, durum = _sahte_durum("kuyu_genisligi", lambda x: False)
        r, n = self.tara(
            sorun.Sorun("M:  merdiven", ("merdiven",), "kuyu_dibi"),
            {"kuyu_genisligi": 1800.0, "kuyu_derinligi": 2700.0},
            durum,
            once,
        )
        self.assertEqual(r, [])
        self.assertLessEqual(n, care_uclari.TARAMA_SORUN_SINAMA)

    def test_taranmayanlar(self):
        """Açığı olan sorun ( türevin işi ), çizimi listede olmayan ( ürün / girdi sorunu ) ve formda
        görünmeyen ölçü taranmaz;  görünmeyenin yerine sıradaki ölçü."""
        once, durum = _sahte_durum("kuyu_derinligi", lambda x: x >= 2750)
        degerler = {"kuyu_genisligi": 1800.0, "kuyu_derinligi": 2700.0}
        farkli = sorun.Sorun("M:  merdiven", ("merdiven",), "kuyu_dibi", fark=-30.0)
        self.assertEqual(self.tara(farkli, degerler, durum, once)[0], [])
        urun = sorun.Sorun("M:  kasnak", ("tahrik_kasnagi",), "kasnak_duzeni")
        self.assertEqual(self.tara(urun, degerler, durum, once)[0], [])
        r, _n = self.tara(
            sorun.Sorun("M:  merdiven", ("merdiven",), "kuyu_dibi"),
            degerler,
            durum,
            once,
            gizli={"kuyu_genisligi"},
        )
        self.assertEqual([(c["anahtar"], c["yeni"]) for c in r], [("kuyu_derinligi", 2750.0)])

    def test_butce_biterse_durur(self):
        once, durum = _sahte_durum("kuyu_genisligi", lambda x: x >= 1837)
        r, n = self.tara(
            sorun.Sorun("M:  merdiven", ("merdiven",), "kuyu_dibi"),
            {"kuyu_genisligi": 1800.0},
            durum,
            once,
            butce=care_uclari.Butce(sinama=0),
        )
        self.assertEqual((r, n), ([], 0))

    def test_arka_mrl_kirisinin_caresi_secim(self):
        """Arkadaki ağırlıkla makine dairesizde makine duvardan duvara kirişe oturur:  ileti
        "yük bina yapısına" diyordu, öneri yoktu ( 27 Kas çare taraması:  6 çaresiz ) — seçim."""
        v = test_yerlesim_saglamligi.standart_istek(800, True, "Arka", aski_duzeni="Kabin üstü")
        v["asansorler"][0]["kuyu_derinligi"] = test_yerlesim_saglamligi.KABIN[800][1] + 700
        v["asansorler"][0]["son_kat_yuksekligi"] = 5000
        r = care_uclari.coz(v, 0, None, care_uclari.Butce(sure=float("inf")))
        self.assertEqual(
            [[(o["anahtar"], o["yeni"], o["yontem"]) for o in c["oneriler"]] for c in r["careler"]],
            [[("makine_raya_biniyor", "Bina yapısına", "seçim")]],
        )

    def test_merdivenin_caresi_kuyu_genisligi(self):
        """Kullanıcının kuyusu ( 27 Kas ):  800 kg MRL, kabin 1350 × 1400, kapı 900, 1800 × 2700, ağırlık
        arkada — kuyu dibi merdiveni kapının yanına sığmıyordu ( Ek F.5 b ), çare bulucu öneri
        bulamıyordu.  Tarama:  kuyu genişliği 1850 ( merdiven 350 — 27 Kas K1;  330'la 1830 );  bağımsız
        sınama:  sorun gider, yeni sorun yok."""
        t = avan_secici.paketler()[(800, True)]
        m = dict(
            beyan_yuku=800,
            beyan_hizi=1,
            kuyu_genisligi=1800,
            kuyu_derinligi=2700,
            kuyu_dibi_kotu="-4,70",
            durak_kotlari="; ".join(["-2,60"] + [katlar.kot_metni(700 + 3000 * i) for i in range(9)]),
            kuyu_tavani_kotu="+29,00",
            mk_yok=True,
            aski_orani=2,
            kisi=10,
            kabin_genisligi=1350,
            kabin_derinligi=1400,
            kapi_genisligi=900,
        )
        veri = avan_secici._istek(t, m, avan_secici._arka_adayi(t, m))
        once = care_uclari.girdi_durumu(veri, 0)
        self.assertEqual(len(once[0]), 1)
        self.assertTrue(next(iter(once[0])).startswith("Kuyu dibi merdiveni"))
        r = care_uclari.coz(veri, 0, None, care_uclari.Butce(sure=float("inf")))
        oneriler = r["careler"][0]["oneriler"]
        self.assertEqual(
            [(o["anahtar"], o["yeni"], o["yontem"], o["bina"]) for o in oneriler],
            [("kuyu_genisligi", 1850.0, "tarama", True)],
        )
        sonra = care_uclari.girdi_durumu(care_uclari.girdi_yaz(veri, 0, "kuyu_genisligi", 1850.0), 0)
        self.assertEqual(sonra[0], {})
        #  10 mm eksiği ( 1840 ) gidermiyor
        self.assertTrue(
            care_uclari.girdi_durumu(care_uclari.girdi_yaz(veri, 0, "kuyu_genisligi", 1840.0), 0)[0]
        )


if __name__ == "__main__":
    unittest.main()

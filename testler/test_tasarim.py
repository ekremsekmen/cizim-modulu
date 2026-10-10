"""TASARIM ŞEMASI ( tasarim/ ) — her girdinin tek tanımı.

Formun, hesap motorunun, elektrik hesaplarının ve çizimin alanları tek
şemadan türetilir;  bu testler türetmenin eksiksiz ve tek yönlü olduğunu
sınar:  bir alan iki kez tanımlanamaz, motorun listesi şemadan ayrışamaz,
formdan kalkan alan istekte gelse de okunmaz."""

import os
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from uclar import uygulama_uclari as UC_UYG
from cizim import kopru as CK
from motor.uygulama import uygulama_girdisi as UG
from motor.uygulama import mukavemet_girdi as MG
from tasarim import alanlar as TS
from tasarim import gorunum as TG
from tasarim import sozluk as TZ

#  Tasarım sırası:  düzen → kuyu → kabin ve kapı → parçalar → elektrik
GRUP_SIRASI = (
    "Asansör ve düzen",
    "Kuyu ve katlar",
    "Kabin ve kapı",
    "Raylar ve patenler",
    "Karşı ağırlık",
    "Askı ve halatlar",
    "Makine",
    "Makine dairesi",
    "Tamponlar",
    "Hız regülatörü",
    "Elektrik ve topraklama",
)
#  Formda kutusu olmayanlar:  çizimden gelen ya da çizimin tek çizebildiği
#  değerler ( kararlar 1 · 7 ) ve hesabın kendi türettikleri.
FORMDA_YOK = {
    "saptirma_kasnak_capi",
    "saptirma_kasnak_min_capi",
    "kabin_tampon_baba",
    "kabin_kaciklik",
    "aski_kaciklik_y",
    "kabin_ray_sayisi",
    "agirlik_ray_sayisi",
    "karsi_agirlik",
    "kuyu_boyu",
    "kablo_tipi_2",
    #  3. adım:  yerleşimin ölçü listesi ( cizim/olculer.py )
    "kabin_merkezi_x",
    "esik_x",
    "kabin_ray_boyu",
    "agirlik_ray_boyu",
    "aski_halat_boyu",
    "reg_halat_boyu",
    "kasnak_tek_yon",
    "kasnak_ters_yon",
    "kasnak_kabin_adedi",
    "kasnak_agirlik_adedi",
    "saptirma_agirlik_capi",
    "makine_yuku_x",
    #  4. adım:  kirişin açıklığı çizimden ( kaide halatlara ortalı, makineyi sarar );
    #  karşı ağırlık dolgusuna kalan yükseklik ( karar 11 )
    "yan_yatak_boyu",
    "agirlik_dolgu_yuksekligi",
}


def _form():
    v = UC_UYG.uygulama_alanlari()
    return v, {f["anahtar"]: f for gr in v["gruplar"] for f in gr["alanlar"]}


class TekTanim(unittest.TestCase):
    def test_her_alan_bir_kez(self):
        k = [a.anahtar for a in TS.ALANLAR]
        self.assertEqual(len(k), len(set(k)))

    def test_motorlarin_listeleri_semadan(self):
        #  Üç sözleşme birlikte şemanın tamamıdır;  birbirleriyle kesişmez.
        muk, elk = {a[0] for a in MG.ALANLAR}, {a[0] for a in UG.EK_ALANLAR}
        ciz = {a[0] for a in CK.ALANLAR}
        self.assertEqual(muk | elk | ciz, set(TS.ALAN))
        self.assertFalse(muk & elk or muk & ciz or elk & ciz)
        for a in MG.ALANLAR:
            s = TS.ALAN[a[0]]
            self.assertEqual(a, (s.anahtar, s.etiket, s.birim, s.tur, s.secenekler, s.varsayilan))
        self.assertEqual(set(MG.POZITIF_ALANLAR), set(TG.anahtarlar(TS.MUK, pozitif=True)))
        self.assertEqual(MG.ACIKLAMA["sarilma_acisi"], TG.bilgi(TS.ALAN["sarilma_acisi"]))
        self.assertEqual(CK.CIZIMDEN, TG.cizimden())

    def test_kaynaklar(self):
        for a in TS.ALANLAR:
            self.assertIn(a.kaynak, TS.KAYNAKLAR, a.anahtar)
            #  Formda kutusu olmayan bir alan kullanıcının girdisi olamaz
            if not a.formda:
                self.assertIn(a.kaynak, (TS.CIZIM, TS.HESAP), a.anahtar)


class Form(unittest.TestCase):
    def test_gruplar_tasarim_sirasiyla(self):
        v, _alan = _form()
        self.assertEqual(tuple(g["ad"] for g in v["gruplar"]), GRUP_SIRASI)

    def test_cizimden_ve_hesaptan_gelenler_formda_yok(self):
        _v, alan = _form()
        self.assertEqual(set(TS.ALAN) - set(alan), FORMDA_YOK)
        self.assertEqual(set(TG.formda_olmayan()), FORMDA_YOK)

    def test_formdan_kalkan_alan_istekte_olsa_da_okunmaz(self):
        eski = {k: 4 for k in ("kabin_ray_sayisi", "agirlik_ray_sayisi")}
        eski.update(
            kabin_kaciklik=40,
            aski_kaciklik_y=40,
            saptirma_kasnak_capi=500,
            saptirma_kasnak_min_capi=200,
            kabin_tampon_baba=10,
        )
        a, _o = UC_UYG._asansor_girdileri({"asansorler": [eski], "proje_geneli": {}, "sabitler": {}})
        self.assertFalse(set(eski) & set(a[0]), a[0])

    def test_makine_dairesizde_bir_bir_secilmez(self):
        #  Karar 5:  makine dairesizde 1:1 askı formda seçilemez ( çizim 2:1 çizer ).
        _v, alan = _form()
        k = alan["aski_orani"]["secenek_kosulu"]
        self.assertEqual(set(k), {"1"})
        self.assertEqual(k["1"]["yerlesim"], "daireli")
        self.assertTrue(k["1"]["sebep"])

    def test_yerlesime_gore_gizlenenler(self):
        v, _alan = _form()
        g = v["yerlesime_gore_gizli"]
        self.assertTrue(
            {"mk_uzunluk", "md_duvar", "tabliye_yuksekligi", "makine_saptirma_capi"} <= set(g["mrl"])
        )
        self.assertTrue({"makine_raya_biniyor", "acil_pano_yani"} <= set(g["daireli"]))
        self.assertEqual(set(g["mrl"]), UG.uygulanmayan_alanlar(True))

    def test_proje_geneli(self):
        v, _alan = _form()
        self.assertEqual(
            set(v["proje_geneli"]),
            {"mk_yok", "mk_uzunluk", "mk_genislik", "temel_a", "temel_b"} | set(CK.PROJE_GENELI),
        )

    def test_hesap_bolumu_eslemesi_gercek_gruplari_gosterir(self):
        v, _alan = _form()
        ad = {g["ad"] for g in v["gruplar"]}
        for k, gruplar in v["bolum_grubu"].items():
            self.assertTrue(set(gruplar) <= ad, (k, gruplar))


class Sozluk(unittest.TestCase):
    def test_her_alan_sozlukte(self):
        s = TZ.satirlar()
        self.assertTrue(set(TS.ALAN) <= {r["anahtar"] for r in s})
        self.assertEqual([r["grup"] for r in s], sorted((r["grup"] for r in s), key=GRUP_SIRASI.index))

    def test_cozulen_sorunlar_sozlukten_silindi(self):
        #  2. adımda çözülenler:  ray sayısı, yc · ys, D2 · Ds · kaide formdan kalktı
        for k in (
            "kabin_ray_sayisi",
            "agirlik_ray_sayisi",
            "kabin_kaciklik",
            "aski_kaciklik_y",
            "saptirma_kasnak_capi",
            "kabin_tampon_baba",
            "aski_orani",
            #  3. adım:  Nps · Npr çizilen kasnaklardan
            "kasnak_tek_yon",
            "kasnak_ters_yon",
            #  4. adım:  kirişin açıklığı çizimden;  arkadaki ağırlıkla 2:1
            #  çiziliyor ( kabin üstünde çapraz kasnaklar — karar 4 );
            #  dolgunun çerçeveye sığması denetleniyor ( karar 11 )
            "yan_yatak_boyu",
            "agirlik_yeri",
            "agirlik_malzemesi",
        ):
            self.assertNotIn(k, TZ.SORUNLAR)
        #  3. adım:  hesabın geometri tahminleri çizimden geliyor;  yalnız
        #  çizimde olmayan revizyon kutusu kaldı ( karar 10:  çizilmez ).
        self.assertEqual([r[0] for r in TZ.ICSEL], ["Revizyon kutusu"])


if __name__ == "__main__":
    unittest.main()

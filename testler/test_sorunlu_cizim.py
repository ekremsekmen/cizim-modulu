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
  5.  Her sorun parçalıdır ( cizim/sorun.py ) ve parçası gösterilen çizimde
      gerçekten vardır — yoksa ekranın kırmızı işareti boşa düşer.  Sorunun
      söylediği çizim gelmişse parça o çizimdedir.
"""

import html
import json
import pickle
import re
import unittest
from unittest import mock

from cizim import cizimler
from cizim import dusey
from cizim import istek_onbellegi
from cizim import kuyu_kesiti
from cizim import kopru
from cizim import pafta
from cizim import sorun
from cizim import sorunlu
from motor.uygulama import uygulama_girdisi
from motor.uygulama import uygulama_hesabi
from uclar import cizim_uclari
from uclar import uygulama_istegi
from uclar import uygulama_uclari
from hesap_girdi import ASANSOR, ASANSOR_MD, ORTAK, ORTAK_MD, SABITLER
from testler import gercek_projeler

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
    #  Kuyu dibi ( regülatör gergisi ), kabin üstü ( kasnak – ara kiriş ),
    #  makine dairesi ( kaide ), kat aralığı ( ara acil kapı )
    (False, "kuyu_genisligi", 2000): (),
    (False, "kuyu_derinligi", 1800): (),
    (False, "kabin_genisligi", 900): (),
    (False, "durak_adedi", 2): (),
    (True, "kuyu_genisligi", 2800): KESITLER,
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

    def test_sorunun_parcasi_cizimde(self):
        for (md, alan, deger), _bilinen in VAKALAR.items():
            with self.subTest(md=md, alan=alan, deger=deger):
                r = _ekran(_veri(md, **{alan: deger}))
                self.assertEqual([m["metin"] for m in r["sorunlar"]], r["hata"])
                svg = {
                    c["ad"]: {html.unescape(x) for x in re.findall(r'data-ad="([^"]+)"', c["svg"])}
                    for c in r["cizimler"]
                }
                hepsi = set().union(*svg.values())
                for m in r["sorunlar"]:
                    self.assertTrue(m["parcalar"], m["metin"])
                    self.assertTrue(set(m["parcalar"]) & hepsi, (m["metin"], m["parcalar"]))
                    if m["cizim"] in svg:
                        self.assertTrue(set(m["parcalar"]) & svg[m["cizim"]], (m["metin"], m["cizim"]))
                    #  Türkçe harf:  capitalize / lower "Kabi̇n bağlantisi" yazıyordu
                    self.assertNotIn("\u0307", m["metin"])

    def test_sorun_duz_metin_gibi(self):
        s = sorun.Sorun("Kabin taşıyor.", ("kabin_dis", "", "kabin", "kabin_dis"), "kuyu_plani")
        self.assertEqual((s, hash(s)), ("Kabin taşıyor.", hash("Kabin taşıyor.")))
        self.assertEqual(s.parcalar, ("kabin_dis", "kabin"))
        self.assertEqual(json.dumps([s]), json.dumps(["Kabin taşıyor."]))
        t = pickle.loads(pickle.dumps(s, protocol=pickle.HIGHEST_PROTOCOL))
        self.assertEqual((type(t), t.parcalar, t.cizim), (sorun.Sorun, s.parcalar, "kuyu_plani"))
        self.assertIs(type(s + "x"), str)
        b = sorun.birlestir(
            ["a", sorun.Sorun("b", ("x",)), sorun.Sorun("a", ("y",), "k"), sorun.Sorun("b", ("z",))]
        )
        self.assertEqual(b, ["a", "b"])
        self.assertEqual(
            [(sorun.parcalari(x), getattr(x, "cizim", None)) for x in b], [(("y",), "k"), (("x", "z"), None)]
        )
        self.assertEqual(
            sorun.yapili(s),
            {"metin": "Kabin taşıyor.", "parcalar": ["Kabin ( dış )", "Kabin"], "cizim": "kuyu_plani"},
        )

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

    def test_siginma_yerlesemezse_butun_cizimler_gelir(self):
        """Ofisin gerçek projesi 12495-18 ( makine dairesiz, 1.100 × 1.100,
        arkada ağırlıkla kabin üstü 2:1 ):  kabin tavanında çömelme alanına yer
        yok.  Eskiden boş sığınma kutusu kuyu üstü açıklığında çöküyor, pafta
        başlığı bu denetimi her çizimde çağırdığından ekranın 7 çiziminin
        hepsi kayboluyordu ( 20 Eki ).  Kuyu dibinde de yer yoksa aynı."""
        a = dict(gercek_projeler.PROJELER["12495-18"])
        pg = {k: a.pop(k) for k in list(a) if k in uygulama_istegi.PROJE_GENELI_ALANLAR}
        for ek, sorunlar in (
            ({}, ("Kabin tavanında",)),
            ({"siginma_tipi_dip": "Yatarak"}, ("Kabin tavanında", "Kuyu dibinde")),
        ):
            with self.subTest(**ek):
                veri = {"asansorler": [dict(a, **ek)], "proje_geneli": pg, "sabitler": {}}
                r = _ekran(veri)
                self.assertFalse(r["aktif"])
                self.assertEqual(r["kurulamayan"], [])
                self.assertEqual(len(r["cizimler"]), len(pafta.sira(_g(veri))))
                for bas in sorunlar:
                    self.assertTrue(any(h.startswith(bas) for h in r["hata"]), (bas, r["hata"]))
                #  Paketin hükmü değişmez:  uygunsuz çizim inmez
                g_siki, siki = _siki(veri)
                self.assertIsNone(g_siki)
                self.assertEqual(r["hata"], siki)

    def test_kesit_kurulamazsa_plan_yine_kurulur(self):
        """Sorunlu kipte kesitin yerleşimi kurulamasa da planın başlığı harfsiz
        yazılır:  bilinen sınır ( CizimKurulamaz ) sessizce, programın hatası
        kayıtta ERROR ile.  Kip kapalıyken hata bugünkü gibi yükselir."""
        g = _g(_veri(False))
        baslik = "KUYU PLANI  ( kabin hizasından yatay kesit )"
        with mock.patch.object(kuyu_kesiti, "dogrula", side_effect=sorun.CizimKurulamaz(["kesit"])):
            with sorunlu.kip(), self.assertNoLogs(cizimler.log, level="ERROR"):
                self.assertEqual(cizimler.plan_basligi(g, "kuyu_plani", baslik), baslik)
        with mock.patch.object(kuyu_kesiti, "dogrula", side_effect=TypeError("kesit")):
            with sorunlu.kip(), self.assertLogs(cizimler.log, level="ERROR") as k:
                self.assertEqual(cizimler.plan_basligi(g, "kuyu_plani", baslik), baslik)
            self.assertIsNotNone(k.records[0].exc_info)  # izi ( traceback ) var
            with self.assertRaises(TypeError):
                cizimler.plan_basligi(g, "kuyu_plani", baslik)
        self.assertIn("C-C", cizimler.plan_basligi(g, "kuyu_plani", baslik))

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

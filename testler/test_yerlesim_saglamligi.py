"""YERLEŞİMİN SAĞLAMLIĞI — standart asansörler formun varsayılan çizim
ayarlarıyla çizilir;  çizim yalnız gerçek bir engel varsa reddeder.

Program denetiminde ( 29 Eyl 2026 ) varsayılan çizim ayarlarıyla standart 72
düzenin yalnız 22'si çiziliyordu:  sığınma alanı kabin kasnağının köşesine
giriyordu, merdiven yalnız yan duvara konuyordu, kasnaklar arası halatı ray
ara kirişinin dibine koyuyordu, regülatör gergisi küçük kuyuda raya iniyordu.
Kalan retler gerçektir:  kabin üstü askı daha yüksek son kat ister, 900 ×
1.000 kabinin tavanına 1:1 bağlantıyla çömelme alanı sığmaz."""

import json
import os
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from uclar import cizim_uclari as UC
from cizim import kabin_ustu as CKU
from cizim import kopru as CK
from cizim import kuyu_dibi as CKD
from cizim import kuyu_ustu as CKT
from motor.uygulama import uygulama_girdisi as E_UGR

#  ISO 4190 / TS EN 81-20 Çizelge 6'ya uygun kabinler, kuyu kabinden 950 geniş,
#  450 derin ( formun varsayılanı gibi ), kapı yüke göre.
KABIN = {
    320: (900, 1000, 800),
    450: (1000, 1250, 800),
    630: (1100, 1400, 800),
    800: (1350, 1400, 900),
    1000: (1100, 2100, 900),
    1275: (2000, 1400, 1100),
    1600: (1400, 2400, 1100),
    2000: (1500, 2700, 1300),
    2500: (1800, 2700, 1400),
}


def _veri(Q, mrl=True, yer="Sağ", **ek):
    kg, kd, dw = KABIN[Q]
    #  KAPI KARŞI AĞIRLIĞIN TERSİNE AÇILIR ( 2 Eki ):  bu kuyularda yandaki
    #  ağırlığın ön rayı ön duvara yakındır;  ağırlığa doğru açılan kapının
    #  kabin kapısı cebi ( kabinle yürür ) rayın konsoluna ve ara kirişe çarpar
    #  ( 26 düzenin 23'ünde ).  1.300 ve 1.400'lük kapılar 3 ya da 4 kanatlıdır:
    #  2 kanatlının cebi ( kapının yarısı + 30 ) iki yanda da sığmaz ( Fermator
    #  T3 · C4 );  ağırlık arkadaysa 4 kanatlı merkezi.
    kanat = " 3 Kanat" if dw >= 1300 else ""
    ek.setdefault(
        "kat_kapisi_tipi",
        {"Sol": f"Teleskopik{kanat} Sağ", "Sağ": f"Teleskopik{kanat} Sol"}.get(
            yer, "Otomatik Merkezi 4 Kanat" if dw >= 1300 else "Teleskopik Sol"
        ),
    )
    a = dict(
        beyan_yuku=Q,
        kabin_genisligi=kg,
        kabin_derinligi=kd,
        kapi_genisligi=dw,
        kuyu_genisligi=kg + 950,
        kuyu_derinligi=kd + 450,
        agirlik_yeri=yer,
        **ek,
    )
    pg = {"mk_yok": mrl}
    if not mrl:
        pg.update(mk_uzunluk=max(3800, kd + 2000), mk_genislik=max(2600, kg + 1200))
    return {"asansorler": [a], "proje_geneli": pg, "sabitler": {}, "asansor": 0}


def gecerli_duzen(Q, yer="Sağ", mrl=True, **ek):
    """Programın çizdiği bir standart düzen:  ( g, hata ).  Arkadaki ağırlıkta
    kuyu kabinden 700 derin ve askı kabin üstü ( 450'de ağırlık kabinin
    arkasına sığmaz — m.5.2.5.5.1 h;  bkz. test_arkadaki_agirlik… ), makine
    dairesizde makine bina yapısında, son kat 5.000."""
    if yer == "Arka":
        ek = dict(
            {"aski_duzeni": "Kabin üstü"},
            **({"makine_raya_biniyor": "Bina yapısına", "son_kat_yuksekligi": 5000} if mrl else {}),
            **ek,
        )
    v = _veri(Q, mrl, yer, **ek)
    if yer == "Arka":
        v["asansorler"][0]["kuyu_derinligi"] = KABIN[Q][1] + 700
    g, _A, hata = _g(v)
    return g, hata


def _cizim(v):
    return json.loads(UC.api_cizimler(v).body)


def _g(v):
    ham, _i, proje = UC._istek(v)
    A = E_UGR.tamamla(ham)
    g, hata = CK.cizim_girdisi(A, None, proje, 1)
    return g, A, hata


def _ortusur(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


class StandartAsansorler(unittest.TestCase):
    def test_varsayilan_ayarlarla_cizilir(self):
        for Q in KABIN:
            for yer in ("Sağ", "Sol"):
                for ad, mrl, ek in (
                    ("makine dairesiz 2:1", True, {}),
                    ("makine daireli 2:1", False, {}),
                    ("makine daireli 1:1", False, {"aski_orani": 1}),
                ):
                    if Q == 320 and ek:
                        continue  # 900 × 1.000 tavanına 1:1 bağlantıyla çömelme sığmaz
                    d = _cizim(_veri(Q, mrl, yer, **ek))
                    if Q == 320:
                        #  900 × 1.000 tavanını şasenin üst kirişi ( ray ekseninde
                        #  300 — ÇİZİM KABULÜ ) ikiye böler:  kirişin önünde ve
                        #  arkasında çömelme alanına yer kalmaz ( 4 Eki;  eskiden
                        #  alan kirişin altına giriyordu ).
                        self.assertFalse(d.get("aktif"), (Q, yer, ad))
                        self.assertTrue(any("şasenin üst kirişi" in h for h in d["hata"]), d["hata"])
                        continue
                    self.assertTrue(d.get("aktif"), (Q, yer, ad, d.get("hata")))

    def test_arkadaki_agirlikla_iki_bir(self):
        #  Kabin üstünde çapraz kasnaklar ( arka_aski ).  Kuyu kabinden 450 derin
        #  olunca ağırlık kabinin arkasına sığmaz ( kapı bölgesi + pano sonrası
        #  147 mm;  ağırlık 160 + 50 açıklık — m.5.2.5.5.1 h ):  gerçek ret.  700
        #  derinde 800 kg'dan küçükler çizilmez:  kasnaklar arasındaki çapraz halat
        #  ( tavanın 80 üstünde ) ve şasenin üst kirişi 900 × 1.000, 1.000 × 1.250,
        #  1.100 × 1.400 tavanlarını çömelme alanının sığmadığı parçalara böler
        #  ( 10 Eki'ye dek yalnız 320 kg;  halat ve kabin üstü askıda kiriş engel
        #  sayılmıyordu — hareketli.kabin_parcalari ).  Makine dairesizde makine
        #  duvardan duvara kirişte ( bina yapısına ), kabinin üstünde:  son kat 5.000.
        for Q in KABIN:
            kd = KABIN[Q][1]
            for mrl, ek in (
                (True, {"makine_raya_biniyor": "Bina yapısına", "son_kat_yuksekligi": 5000}),
                (False, {}),
            ):
                for derin, cizilir in ((450, False), (700, Q not in (320, 450, 630))):
                    v = _veri(Q, mrl, "Arka", aski_duzeni="Kabin üstü", **ek)
                    v["asansorler"][0]["kuyu_derinligi"] = kd + derin
                    d = _cizim(v)
                    self.assertEqual(bool(d.get("aktif")), cizilir, (Q, mrl, derin, d.get("hata")))
                    if derin == 450:
                        self.assertTrue(any("m.5.2.5.5.1 h" in h for h in d["hata"]), d["hata"])
                    elif not cizilir:
                        self.assertTrue(any("aralarındaki halat" in h for h in d["hata"]), d["hata"])

    def test_kabin_ustu_askiya_yuksek_son_kat_gerekir(self):
        #  Kabin tepede:  tavandaki kasnak, kabinin öbür halatının kuyu tavanındaki
        #  bağlantısının altına gelir ( 645 sarkar );  aralarında en az 0,50 m
        #  ( m.5.2.5.7.2 a ).  Ofisin kabiniyle ( kabin 2.000;  8 Eki'den kasnaklar
        #  gerçek üst kirişin üstünde — 2.340, eskiden 2.270 ) varsayılan 4.200 yeter,
        #  4.030'da çizilir, 4.029'da kasnak – tavan 499 < 500 kalır ( eskiden 4.000
        #  yetiyordu ).  Referans projenin kabiniyle ( şase 3.300 ) 4.600 gerekiyordu.
        for Q in (450, 1000, 2500):
            self.assertTrue(_cizim(_veri(Q, aski_duzeni="Kabin üstü")).get("aktif"), Q)
            self.assertTrue(
                _cizim(_veri(Q, aski_duzeni="Kabin üstü", son_kat_yuksekligi=4030)).get("aktif"), Q
            )
            d = _cizim(_veri(Q, aski_duzeni="Kabin üstü", son_kat_yuksekligi=4029))
            self.assertTrue(
                any("m.5.2.5.7.1" in h or "m.5.2.5.7.2 a" in h for h in d.get("hata") or []),
                (Q, d.get("hata")),
            )


class SiginmaAlani(unittest.TestCase):
    def test_kabin_kasnaklarinin_ve_halatin_altina_dusmez(self):
        #  1.350 × 1.400 kabin:  alan kapıya en yakın yerde sağ kasnağın köşesine
        #  giriyor, yükseklik 945 kalıyordu ( 1.000 gerekir ).
        g, _A, _h = _g(_veri(800))
        KD = CKD.yerlesim(g)
        alcak = CKD.kabin_alti_askisi(g, KD["S"], KD["taban"])
        self.assertEqual(len(alcak), 3)  # iki kasnak + aradaki halat
        self.assertFalse(any(_ortusur(KD["siginma"], k) for k in alcak), KD["siginma"])
        self.assertTrue(_cizim(_veri(800)).get("aktif"))

    def test_dar_bosluk_izgarada_kacmaz(self):
        #  1.000 × 1.250 kabin:  halat şeridinin arkasında 507 mm'lik bant;  25 mm
        #  ızgara ya şeride 1 mm değiyor ya kabinden taşıyordu.
        g, _A, _h = _g(_veri(450))
        KD = CKD.yerlesim(g)
        alcak = CKD.kabin_alti_askisi(g, KD["S"], KD["taban"])
        self.assertFalse(any(_ortusur(KD["siginma"], k) for k in alcak), KD["siginma"])

    def test_kucuk_kabinde_kuyu_tabaninin_baska_yerinde(self):
        #  900 × 1.000:  ortadaki tamponun iki yanı 500'e yetmez;  m.5.2.5.8.1
        #  yalnız kuyu tabanında engelsiz bir alan ister — alan kabinin izinin
        #  dışına taşar, karşı ağırlığın şeridine girmez.
        g, _A, _h = _g(_veri(320))
        KD = CKD.yerlesim(g)
        self.assertEqual([h for h in KD["hata"] if "sığınma" in h], [])
        sg = KD["siginma"]
        self.assertTrue(
            sg[0] < KD["kabin"][0]
            or sg[2] > KD["kabin"][2]
            or sg[1] < KD["kabin"][1]
            or sg[3] > KD["kabin"][3],
            sg,
        )
        self.assertLess(sg[2], min(k[0] for k in KD["agirlik_raylari"]))  # ağırlık sağda


class Merdiven(unittest.TestCase):
    def test_genis_kuyuda_kapinin_yaninda(self):
        #  2.000 genişlikte kabin, kuyu 2.950:  yan duvarlar kapıdan 800'den uzak
        g, _A, _h = _g(_veri(1275))
        KD = CKD.yerlesim(g)
        self.assertEqual(KD["merdiven"][1], 0.0)
        self.assertTrue(_cizim(_veri(1275)).get("aktif"))


class KasnaklarArasi(unittest.TestCase):
    def test_bossa_halat_agirliga_duseyince_iner(self):
        #  Varsayılan asansör:  eski kural ( kabin + 30 ) halatı ağırlığa 25 mm eğik
        #  indiriyordu — sarım açısı çizimden bulunamıyordu.
        v = {"asansorler": [{}], "proje_geneli": {}, "sabitler": {}, "asansor": 0}
        g, A, _h = _g(v)
        self.assertEqual(CKT.yerlesim(g)["sapma"][0], 0.0)
        self.assertEqual(A["sarilma_acisi"], 180.0)
        self.assertNotEqual(g["aski"]["kasnak_arasi"], 1450 + 30)

    def test_kasnak_buyuyunce_ara_kirise_carpmaz(self):
        #  Kabin kasnağı 240 → 260:  eski kuralda halat ara kirişin 20 mm payına
        #  giriyordu ( çizim reddediliyordu ).
        v = {"asansorler": [{"kabin_kasnak_capi": 260}], "proje_geneli": {}, "sabitler": {}, "asansor": 0}
        self.assertTrue(_cizim(v).get("aktif"), _cizim(v).get("hata"))

    def test_carpiyorsa_eski_kural(self):
        #  Kuyu 100 geniş:  ağırlık duvarla birlikte uzaklaşır, düşey inen halat ara
        #  kirişe girerdi — halat kabine yakın kalır ( eğik iner, α girilir ).
        v = {"asansorler": [{"kuyu_genisligi": 2500}], "proje_geneli": {}, "sabitler": {}, "asansor": 0}
        g, A, _h = _g(v)
        self.assertEqual(g["aski"]["kasnak_arasi"], 1450 + 30)
        self.assertFalse(any(h.startswith("Halat (") for h in CKU.yerlesim(g)["hata"]))

    def test_girilen_kasnak_arasi_degismez(self):
        v = {"asansorler": [{"kabin_kasnak_arasi": 1400}], "proje_geneli": {}, "sabitler": {}, "asansor": 0}
        self.assertEqual(_g(v)[0]["aski"]["kasnak_arasi"], 1400)


class Regulator(unittest.TestCase):
    def test_bossa_carpmayan_yer(self):
        #  900 × 1.000 kabin, 1.450 derin kuyu:  varsayılan yerde gergi kolu döner,
        #  ağırlık kabin rayına iner — program çarpmayan en yakın yeri seçer.
        g, _A, _h = _g(_veri(320))
        self.assertNotEqual(abs(g["kuyu_dibi"]["regulator_kaciklik"]), 0)
        self.assertEqual([h for h in CKD.yerlesim(g)["hata"] if "egülatör" in h], [])
        self.assertEqual([h for h in CKT.yerlesim(g)["hata"] if "egülatör" in h], [])

    def test_girilen_yer_degismez(self):
        g, _A, _h = _g(_veri(320, regulator_kaciklik=280))
        self.assertEqual(g["kuyu_dibi"]["regulator_kaciklik"], 280)
        self.assertTrue(any("gergisinin ağırlığı" in h for h in CKD.yerlesim(g)["hata"]))


if __name__ == "__main__":
    unittest.main()

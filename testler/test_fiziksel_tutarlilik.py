"""Plan ve kesitte aynı parçaların konumu ve fiziksel bağlantıları."""

import math
import unittest

from temel import ortusur

from cizim import girdi, geometri, kuyu_dibi
from cizim import kuyu_kesiti, kabin_ustu, kesit_parcalari
from testler.test_cizim import _ornek, _sag_ayna
from cizim import parca_kotlari


class FizikselTutarlilik(unittest.TestCase):
    def test_sase_plan_yan_kesit_ayni_derinlik(self):
        for factory in (_ornek, _sag_ayna):
            g = factory()
            if g["agirlik"]["yeri"] == "Sağ":
                g["kuyu_dibi"]["regulator_yan"] = "Sol"
            g["_cizim_sabitleri"] = {"sase_dikme_derinlik": 360}
            plan = [e for e in geometri.plan(g) if e.get("ad") == "sase_dikme"]
            yan = [e for e in kuyu_kesiti.yan_kesit(g) if e.get("ad") == "sase"]
            self.assertEqual(len(plan), 2)
            self.assertEqual(min(e["x"] for e in yan), plan[0]["y"])
            self.assertEqual(max(e["x"] + e["g"] for e in yan), plan[0]["y"] + plan[0]["d"])
            self.assertEqual(plan[0]["d"], 360)

    def test_gergi_plakasi_rayda_kol_kasnagi_ve_agirligi_tasir(self):
        """Kollu gergi ( R4K ):  plaka rayın tabanının arka yüzünde ve ray
        ekseni plakanın üstünde;  kontak plakanın arkasında;  kol plakadan
        ( mafsal ) kasnağa ve ağırlığa — hep raydan uzağa doğru."""
        for yan, kaciklik in (("Sol", 280), ("Sol", -280), ("Sağ", -440)):
            g = _ornek(kuyu_dibi={"regulator_kaciklik": kaciklik, "regulator_yan": yan})
            Y = kuyu_dibi.yerlesim(g)
            with self.subTest(yan=yan, kaciklik=kaciklik):
                self.assertEqual(Y["hata"], [])
                gp = Y["gergi_donanim"]
                kol, ag, pl, kt = gp["kol"], gp["agirlik"], gp["plaka"], gp["kontak"]
                ry = g["kabin_ray"]["kapi_arasi"]
                gy = (Y["gergi"][1] + Y["gergi"][3]) / 2
                ray = Y["kabin_raylari"][-1 if yan == "Sağ" else 0]
                self.assertTrue(pl[1] <= ry <= pl[3])
                if yan == "Sağ":
                    self.assertEqual((pl[0], kt[0]), (ray[2], pl[2]))
                else:
                    self.assertEqual((pl[2], kt[2]), (ray[0], pl[0]))
                self.assertTrue(ortusur(kol, pl) or kol[1] <= pl[3] and pl[1] <= kol[3])
                for y in (gy, (ag[1] + ag[3]) / 2):
                    self.assertTrue(kol[1] <= y <= kol[3])
                self.assertGreater(abs((ag[1] + ag[3]) / 2 - ry), abs(gy - ry))

    def test_gergi_agirligi_sigmayinca_kol_donmez(self):
        #  300:  arkada ağırlık duvara 3 mm.  Eskiden kol öne dönüp rayla çakışıyordu;
        #  kollu gergide dönmek plakanın raydan kopması olur — yer reddedilir
        hata = kuyu_dibi.dogrula(_ornek(kuyu_dibi={"regulator_kaciklik": 300}))
        self.assertTrue(any("gergisinin ağırlığı duvara 3 mm" in h for h in hata), hata)

    def test_gergi_plakasi_raya_oturmali(self):
        """Ray ekseni plakanın oluğunun boyunca:  Ø240 kasnakta kasnak – ray
        ekseni 267 – 442 ( mafsal kasnaktan kol boyunca 220, kol 15° — PFB s. 70 ),
        Ø200'de 211,5 – 386,5 ( mafsal 162,5 )."""
        from cizim import parcalar

        lo, hi = parcalar.gergi_ray_araligi(240)
        self.assertAlmostEqual(lo, 220 * math.cos(math.radians(15)) + 54.5)
        self.assertAlmostEqual(hi, 220 * math.cos(math.radians(15)) + 229.5)
        self.assertEqual((round(lo), round(hi)), (267, 442))
        lo, hi = parcalar.gergi_ray_araligi(200)
        self.assertAlmostEqual(hi - lo, 175.0)
        self.assertAlmostEqual(lo, 162.5 * math.cos(math.radians(15)) + 54.5)
        for kac, cap in ((260, 240), (460, 300), (-700, 300), (200, 200)):
            hata = kuyu_dibi.dogrula(
                _ornek(kuyu_dibi={"regulator_kaciklik": kac, "regulator_kasnak_capi": cap})
            )
            with self.subTest(kaciklik=kac, cap=cap):
                self.assertTrue(any("kabin rayına oturmuyor" in h for h in hata), hata)
        for kac, cap in ((280, 240), (280, 200), (-440, 300)):
            with self.subTest(kaciklik=kac, cap=cap):
                self.assertEqual(
                    kuyu_dibi.dogrula(
                        _ornek(kuyu_dibi={"regulator_kaciklik": kac, "regulator_kasnak_capi": cap})
                    ),
                    [],
                )

    def test_gergi_plan_kesit_ayni_kutular_ve_siginma_bos(self):
        for factory in (_ornek, _sag_ayna):
            g = factory()
            if g["agirlik"]["yeri"] == "Sağ":
                g["kuyu_dibi"]["regulator_yan"] = "Sol"
            Y = kuyu_kesiti.yerlesim(g)
            self.assertEqual(Y["hata"], [])
            gp = Y["KD"]["gergi_donanim"]
            e = kuyu_dibi.ciz(g)
            for ad, kutu in gp.items():
                el = next(el for el in e if el.get("ad") == "gergi_" + ad)
                self.assertEqual(kesit_parcalari.kutu_(el), kutu)
                self.assertEqual(Y["M"]["gergi"][ad][:2], (kutu[1], kutu[3]))
                self.assertFalse(ortusur(kutu, Y["KD"]["siginma"]))
            for kutu in gp.values():
                self.assertTrue(0 <= kutu[0] <= kutu[2] <= g["kuyu"]["genislik"])
                self.assertTrue(0 <= kutu[1] <= kutu[3] <= g["kuyu"]["derinlik"])

    def test_gergi_donanimi_merdiven_ve_siginmaya_engel(self):
        """Gergi kolu ve ağırlığı kuyu dibinde yer tutar:  merdiven ve sığınma
        onlara basmaz.  Gergi sağ rayda, kaçıklık −900 iken engel sayılmasa
        merdiven sağ yanda kolun ve ağırlığın üstüne düşüyordu ( kollu gergide
        plaka raydan kopar:  artık reddedilir — en uzağı −440 )."""
        for kac in (-440, -280, 280):
            for tip in ("Yatarak", "Çömelme", "Dik duruş"):
                g = _ornek(kuyu_dibi={"regulator_yan": "Sağ", "regulator_kaciklik": kac, "siginma_tipi": tip})
                Y = kuyu_dibi.yerlesim(g)
                with self.subTest(kaciklik=kac, siginma=tip):
                    self.assertEqual(Y["hata"], [])
                    for kutu in Y["gergi_donanim"].values():
                        for alan in (Y["merdiven"], Y["siginma"]):
                            self.assertFalse(alan and ortusur(kutu, alan), (kutu, alan))

    def test_gergi_agirligi_duvara_degmez(self):
        """Gergi ağırlığı duvarlara en az çizimin çakışma payı ( 20 ) kadar uzak:
        örnekte arka duvara 3 mm kalıyordu.  Kabul edilen her düzende pay var;
        300 reddedilir ( arkada 3 mm;  kol dönmez )."""
        from cizim import sabitler

        S = sabitler.sabitler()
        #  referans proje regülatör hesabı:  ağırlığın merkezi kasnak merkezinden A = 300
        self.assertEqual((S["gergi_agirlik_yakin"] + S["gergi_agirlik_uzak"]) / 2.0, 300)
        self.assertEqual(girdi.ORNEK["kuyu_dibi"]["regulator_kaciklik"], 280)  # referans proje
        self.assertEqual(kuyu_dibi.dogrula(_ornek()), [])
        self.assertTrue(kuyu_dibi.dogrula(_ornek(kuyu_dibi={"regulator_kaciklik": 300})))
        #  Kaçıklık −780:  eskiden kol arkaya dönüp kabul ediliyordu;  kollu
        #  gergide plaka raydan kopar — reddedilir
        self.assertTrue(
            any(
                "kabin rayına oturmuyor" in h
                for h in kuyu_dibi.dogrula(_ornek(kuyu_dibi={"regulator_kaciklik": -780}))
            )
        )
        #  Ağırlığın duvara dik eni katalogdan ( ASPAR 25 kg:  82 ), kasnak düzlemine
        #  ortalı — eskiden boyuyla aynı 160 sayılıyordu
        self.assertEqual(S["gergi_agirlik_eni"], 82)
        k = kuyu_dibi.yerlesim(_ornek())["gergi_donanim"]["agirlik"]
        self.assertEqual(k[2] - k[0], 82)
        #  Kabin 54 mm sağa kayınca ray ve gergi de kayar:  ağırlık yan duvara 19 mm —
        #  yön değiştirmek kurtarmaz, reddedilir ( 160'lık ağırlıkta 15 mm yetiyordu )
        self.assertTrue(
            any("duvara 19 mm" in h for h in kuyu_dibi.dogrula(_ornek(kabin={"kaciklik_y": 184})))
        )
        kabul = 0
        for kac in range(-900, 901, 20):
            g = _ornek(kuyu_dibi={"regulator_kaciklik": kac})
            Y = kuyu_dibi.yerlesim(g)
            if Y["hata"]:
                continue
            kabul += 1
            k = Y["gergi_donanim"]["agirlik"]
            with self.subTest(kaciklik=kac):
                self.assertGreaterEqual(
                    min(k[0], k[1], g["kuyu"]["genislik"] - k[2], g["kuyu"]["derinlik"] - k[3]),
                    girdi.ASGARI_ACIKLIK,
                )
        #  Ø300 kasnakta oluğun aralığı −442 … −267 ve 267 … 442;  örnekte arkada
        #  280'den ötesi duvara değer:  −440 … −280 ve 280
        self.assertEqual(kabul, 10)

    def test_regulator_gercek_olculerle(self):
        """Hız regülatörü PFB kılavuzunun R5 / R6 resimlerinden ( parcalar.
        regulator_geometrisi ):  plan ile kesit aynı kutular;  kasnak tavandan 462,
        gövde eksenin 168 altından 167 üstüne ( R6 );  taban 150 × 238, uzun ucu
        ( mekanizma ve kontak ) kuyunun içine;  makine dairesinde ayaklar döşemede."""
        from cizim import parcalar
        from testler.test_olcu_kaynagi import _g, _gercek

        g6, g5 = parcalar.regulator_geometrisi(300), parcalar.regulator_geometrisi(200)
        self.assertEqual((g6["eksen"], g6["tepe"], g6["zarf"]), (168.0, 167.0, (-75.0, 75.0, -86.0, 152.0)))
        self.assertEqual((g5["eksen"], g5["tepe"], g5["zarf"]), (120.0, 141.0, (-75.0, 75.0, -83.0, 121.0)))
        self.assertAlmostEqual(2 * g6["deneme"], 220.0)
        self.assertAlmostEqual(2 * g5["deneme"], 143.0)
        g = _ornek()
        M = kuyu_kesiti.yerlesim(g)["M"]
        KU, rg, rk = M["KU"], M["regulator"], M["regulator_kasnak"]
        self.assertEqual((rg[:4], rk[:4]), (KU["reg_govde"], KU["reg_kasnak"]))
        self.assertEqual(M["tavan"] - rk[4], 462)
        self.assertEqual((rk[4] - rg[4], rg[5] - rk[4]), (168.0, 167.0))
        gv, rx = KU["reg_govde"], (rk[0] + rk[2]) / 2.0
        self.assertEqual((gv[2] - gv[0], gv[3] - gv[1]), (238.0, 150.0))
        ic = gv[0] if rx > g["kuyu"]["genislik"] / 2.0 else gv[2]
        self.assertEqual(abs(ic - rx), 152.0)
        Mm = kuyu_kesiti.yerlesim(_g(_gercek("1022"))[0])["M"]
        self.assertEqual(Mm["regulator"][4], Mm["tabliye_ustu"])
        self.assertEqual(Mm["regulator_kasnak"][4] - Mm["tabliye_ustu"], 168.0)

    def test_kasnak_tasiyicisi_kasnagi_saseye_baglar(self):
        """Kabin altı kasnaklar şaseye bağlıdır:  planda yol kasnağın
        merkezinden şase dikmesine ( ray eksenine ) gider;  iki kesitte de
        aynı yol kasnak merkezinin kotunda çizilir."""
        g = _ornek()
        plan = geometri.plan(g)
        yol = [e for e in plan if e.get("ad") == "kasnak_tasiyici_sematik"]
        kasnaklar = [e for e in plan if e.get("ad") == "kabin_kasnak"]
        dikmeler = [e for e in plan if e.get("ad") == "sase_dikme"]
        self.assertEqual((len(kasnaklar), len(dikmeler)), (2, 2))
        uclar = [(e["x1"], e["y1"]) for e in yol] + [(e["x2"], e["y2"]) for e in yol]

        def icinde(p, el):
            return (
                el["x"] - 1e-6 <= p[0] <= el["x"] + el["g"] + 1e-6
                and el["y"] - 1e-6 <= p[1] <= el["y"] + el["d"] + 1e-6
            )

        for k in kasnaklar:
            self.assertIn((k["x"] + k["g"] / 2.0, k["y"] + k["d"] / 2.0), uclar)
        for d in dikmeler:
            self.assertTrue(any(icinde(p, d) for p in uclar), d)

        Y = kuyu_kesiti.yerlesim(g)
        #  A-A'da kabin en alt, B-B'de en üst durakta
        for ciz, z in ((kuyu_kesiti.yan_kesit, Y["kotlar"][0]), (kuyu_kesiti.on_kesit, Y["kotlar"][-1])):
            yol = [x for x in ciz(g) if x.get("ad") == "kasnak_tasiyici_sematik"]
            zk = parca_kotlari.kabin_kotlari(g["dusey"], Y["S"], z)["kasnak_merkez"]
            with self.subTest(kesit=ciz.__name__):
                self.assertTrue(yol)
                self.assertEqual({x[k] for x in yol for k in ("y1", "y2")}, {zk})

    def test_kabin_halat_baglantisi_raya_baglanir(self):
        """Kuyu tepesinde kabin halat bağlantısının plakası kabin rayının başına
        bağlıdır:  kuyu üstü planında ve B-B'de yol plakanın ortasından ray
        eksenine gider ( eskiden plaka ile ray arasında 105,5 mm boşluk vardı,
        plaka havada duruyordu ).  Makine dairesinde bağlantı döşemededir, yol yok."""
        from cizim import kuyu_ustu

        g = _ornek()
        Y = kuyu_ustu.yerlesim(g)
        kb = Y["kabin_baglanti"]
        rx, ry = Y["halat_konsolu"][-1]["p1"][:2]
        #  Bağlantıya en yakın kabin rayı ( öbür yandaki ray kuyunun karşı ucundadır )
        r = min(
            (e for e in geometri.plan(g) if e.get("ad") == "kabin_ray"),
            key=lambda e: abs(e["x"] + e["g"] / 2 - (kb[0] + kb[2]) / 2),
        )
        self.assertTrue(r["x"] <= rx <= r["x"] + r["g"] and r["y"] <= ry <= r["y"] + r["d"], (rx, ry, r))
        self.assertEqual(Y["halat_konsolu"][0]["p0"][:2], ((kb[0] + kb[2]) / 2, (kb[1] + kb[3]) / 2))
        plan = kuyu_ustu.ciz(g)
        self.assertEqual(
            len([e for e in plan if e.get("ad") == "halat_konsolu_sematik"]), len(Y["halat_konsolu"])
        )
        M = kuyu_kesiti.yerlesim(g)["M"]
        zb = (M["kabin_baglanti"][4] + M["kabin_baglanti"][5]) / 2
        yol = [e for e in kuyu_kesiti.on_kesit(g) if e.get("ad") == "halat_konsolu_sematik"]
        self.assertTrue(yol)
        self.assertEqual({e[k] for e in yol for k in ("y1", "y2")}, {zb})
        md = _ornek(makine={"yeri": "Makine dairesi"})
        self.assertFalse(
            [
                e
                for e in kuyu_kesiti.on_kesit(md) + kuyu_ustu.ciz(md)
                if e.get("ad") == "halat_konsolu_sematik"
            ]
        )

    def test_kesitte_ondeki_parca_arkadakini_orter(self):
        """Kesitte bakana yakın parça uzaktakinden SONRA çizilir.  A-A kabin
        ekseninden ağırlığa bakar:  ağırlık tarafındaki kabin rayı ( x 343–405 )
        ve ara kiriş ( x 293–343 ) karşı ağırlığın ( x 50–210 ) önündedir;
        eskiden ağırlık en son çiziliyor, ray ağırlık boyunca kayboluyordu.
        B-B arkadan bakar:  arka ağırlık rayı ağırlığın önünde, ön ray arkasında."""
        g = _ornek()

        def binen(e, ad, ag):
            u0, u1, z0, z1 = ag["x"], ag["x"] + ag["g"], ag["y"], ag["y"] + ag["d"]
            return [
                i
                for i, x in enumerate(e)
                if x.get("ad") == ad
                and x["tip"] == "dikdortgen"
                and x["x"] < u1
                and u0 < x["x"] + x["g"]
                and x["y"] < z1
                and z0 < x["y"] + x["d"]
            ]

        e = kuyu_kesiti.yan_kesit(g)
        i_ag = max(i for i, x in enumerate(e) if x.get("ad") == "agirlik")
        ag = e[i_ag]
        for ad in ("kabin_rayi", "agirlik_konsolu"):
            with self.subTest(kesit="A-A", parca=ad):
                i = binen(e, ad, ag)
                self.assertTrue(i)
                self.assertTrue(all(j > i_ag for j in i), (ad, i, i_ag))
        e = kuyu_kesiti.on_kesit(g)
        i_ag = max(i for i, x in enumerate(e) if x.get("ad") == "agirlik")
        i = binen(e, "agirlik_rayi", e[i_ag])
        self.assertTrue(any(j < i_ag for j in i) and any(j > i_ag for j in i), (i, i_ag))

    def test_raylar_tavana_degmez_ve_tavan_payi_beton_degil(self):
        """Tavanın en alt kısmı ( kuyu tavanı payı ) bir kabuldür:  kesikle
        çizilir, taralı katman değildir.  Hiçbir ray ona değmez — en az
        kabin_rayi_tepe ( referans proje 50 ) altında biter;  eskiden uzak kabin rayı
        ( makine dairelide bütün raylar ) payın alt yüzüne tam değiyordu."""
        for g in (_ornek(), _ornek(makine={"yeri": "Makine dairesi"})):
            Y = kuyu_kesiti.yerlesim(g)
            M, S = Y["M"], Y["S"]
            with self.subTest(makine=g["makine"]["yeri"]):
                self.assertTrue(
                    all(r["ust"] <= M["tavan_alti"] - S["kabin_rayi_tepe"] + 1e-9 for r in M["raylar"])
                )
                for ciz in (kuyu_kesiti.yan_kesit, kuyu_kesiti.on_kesit):
                    e = ciz(g)
                    pay = [x for x in e if x.get("ad") == "tavan_kirisi"]
                    self.assertTrue(pay and all(x["tip"] == "cizgi" and x["katman"] == "GIZLI" for x in pay))
                    z = M["tavan_alti"]
                    self.assertFalse(
                        [
                            x
                            for x in e
                            if x["tip"] == "tarama"
                            and x["y"] < z + 1
                            and z - 1 < x["y"] + x["d"]
                            and x["y"] + x["d"] <= M["tavan"] + 1e-6
                            and x["y"] >= z - 1e-6
                        ]
                    )

    def test_agirlik_patenleri_cercevenin_disinda(self):
        """Karşı ağırlığın patenleri çerçevenin üstünde ve altındadır
        ( LiftDesigner 1022 — 8 Eki ):  merkezleri arası hesabın paten arası,
        çerçeve ondan bir paten boyu kısa.  Eskiden patenler çerçevenin uçlarına
        ortalıydı, daha önce 1.500 aralıkla çerçevenin ortasındaydılar.
        Kasnağına ve kirişlerine yetmeyen çerçeve reddedilir."""
        from cizim import sabitler

        for x in (2920, 2000):
            g = _ornek(dusey={"agirlik_paten_arasi": x})
            paten_boyu = sabitler.sabitler(g.get("_cizim_sabitleri"))["paten_yukseklik"]
            e = kuyu_kesiti.on_kesit(g)
            ag = next(el for el in e if el.get("ad") == "agirlik")
            pat = [el for el in e if el.get("ad") == "agirlik_paten"]
            with self.subTest(paten_arasi=x):
                self.assertEqual(ag["d"], x - paten_boyu)
                merkezler = sorted({round(el["y"] + el["d"] / 2.0, 6) for el in pat})
                self.assertEqual(
                    merkezler,
                    [
                        round(ag["y"] - paten_boyu / 2.0, 6),
                        round(ag["y"] + ag["d"] + paten_boyu / 2.0, 6),
                    ],
                )
        #  örnek:  ø400 kasnak, kasnak merkezi üst kirişten 110 — çerçeve > 310, paten 140
        self.assertTrue(
            any(
                "agirlik_paten_arasi" in h
                for h in kuyu_kesiti.dogrula(_ornek(dusey={"agirlik_paten_arasi": 450}))
            )
        )
        self.assertEqual(kuyu_kesiti.dogrula(_ornek(dusey={"agirlik_paten_arasi": 460})), [])

    def test_korkuluk_kapi_operatorunden_gecmez(self):
        """Kapı operatörü tavanın önünde;  yan korkuluk onun arka yüzünden
        başlar.  Eskiden sol korkuluk tavanın bütün derinliğince çiziliyor,
        operatörün içinden 140 mm geçiyordu ( ön dikmesi operatörün içinde )."""
        say = 0
        for g in (
            _ornek(),
            _ornek(kapi={"tip": "Teleskopik Sağ"}),
            _ornek(kapi={"tip": "Otomatik Merkezi"}),
            _sag_ayna(),
        ):
            if g["agirlik"]["yeri"] == "Sağ":
                g["kuyu_dibi"]["regulator_yan"] = "Sol"
            Y = kabin_ustu.yerlesim(g)
            self.assertEqual(Y["hata"], [])
            op = Y["operator"]
            for (xa, ya, xb, yb), _ in kabin_ustu.korkuluklar(Y):
                say += 1
                with self.subTest(
                    kapi=g["kapi"]["tip"], agirlik=g["agirlik"]["yeri"], korkuluk=(xa, ya, xb, yb)
                ):
                    if xa == xb:  # yan kenar ( y boyunca )
                        kesiyor = op[0] < xa < op[2] and min(ya, yb) < op[3] and op[1] < max(ya, yb)
                    else:  # ön / arka kenar
                        kesiyor = op[1] < ya < op[3] and min(xa, xb) < op[2] and op[0] < max(xa, xb)
                    self.assertFalse(kesiyor)
        self.assertGreater(say, 2)
        Y = kabin_ustu.yerlesim(_ornek())
        sol = next(k for k, _ in kabin_ustu.korkuluklar(Y) if k[0] == k[2] == Y["ic"][0])
        self.assertEqual(sol[1], Y["operator"][3])

    def _delikte(self, parcalar, x, y, r):
        """( x, y )'deki r yarıçaplı halat bir halat deliğinin içinde mi."""
        return any(
            q["k"][0] <= x - r and x + r <= q["k"][2] and q["k"][1] <= y - r and y + r <= q["k"][3]
            for q in parcalar
            if q["tur"] == "kutu" and q["parca"] == "halat_deligi"
        )

    def test_kuyu_ustu_sasesinde_halat_delikleri(self):
        """Makine dairesizde karşı ağırlık halatları ( tahrik kasnağından ve
        ağırlık bağlantısından ) motor plakasının içinden iner:  plakada delik
        vardır.  Eskiden deliksiz plakanın içinden geçiyorlardı."""
        g = _ornek()
        M = kuyu_kesiti.yerlesim(g)["M"]
        KU = M["KU"]
        r = g["aski"]["halat_capi"] / 2.0
        mp = next(q["k"] for q in M["sase_parcalari"] if q["tur"] == "kutu" and q["parca"] == "motor_plakasi")
        icinde = 0
        for x, y in (KU["halatlar"][0], KU["ag_dusus"], KU["ag_teget2"]):
            if mp[0] < x < mp[2] and mp[1] < y < mp[3]:
                icinde += 1
                with self.subTest(halat=(x, y)):
                    self.assertTrue(self._delikte(M["sase_parcalari"], x, y, r))
        self.assertEqual(icinde, 2)  # ağırlık tarafı ve bağlantısı
        #  Kuyu üstü planında da iki delik
        from cizim import kuyu_ustu

        self.assertEqual(len([e for e in kuyu_ustu.ciz(g) if e.get("parca") == "halat_deligi"]), 2)

    def test_makine_dairesinde_makine_plakada_halatlar_delikte(self):
        """Makine kaidenin yan yataklarının arasındaki plakaya oturur ( hesap:
        yük iki yan yatağa );  plakayı kesen her halat bir delikten geçer —
        saptırmada eğik halat plakayı kestiği yerde;  saptırma kasnağının
        askıları plakanın altına kadar çıkar.  Eskiden plaka yoktu, makine iki
        yan yatağın arasında havada duruyordu."""
        from cizim import makine

        #  Son düzen:  ø400 dişli kasnağı plakanın altına sarkar ( merkez kaide
        #  üstünün 195 üstünde ) — plakada kasnağın yuvası açılır
        duzenler = [(tip, sap, {}) for tip in ("Dişli", "Dişlisiz") for sap in (False, True)] + [
            #  Kasnaklar arası 1000 kabinden dar ( 1350 ):  kabin altında halat kabinin
            #  İÇİNDEN geçerdi ( kabin_ustu._halatlar reddeder — 15 Eki );  ø400 bu
            #  kuyuda yalnız kabin üstü askıyla kurulur.  Sığınma bu testin konusu değil.
            (
                "Dişli",
                True,
                {
                    "aski": {"kasnak_arasi": 1000, "duzen": "Kabin üstü"},
                    "kabin_ustu": {"siginma_tipi": "Dik duruş"},
                    "D1": 400,
                    "D2": 320,
                },
            )
        ]
        for tip, sap, ek in duzenler:
            mk = {"yeri": "Makine dairesi", "tip": tip}
            if sap:
                mk.update(tahrik_kasnak_capi=ek.get("D1", 200), saptirma_kasnak_capi=ek.get("D2", 294))
            g = _ornek(makine=mk, **{b: ek[b] for b in ("aski", "kabin_ustu") if b in ek})
            Y = kuyu_kesiti.yerlesim(g)
            self.assertEqual(Y["hata"], [])
            M = Y["M"]
            zs = M["sase"][5]
            parcalar = M["sase_parcalari"]
            plaka = next(q["k"] for q in parcalar if q["tur"] == "kutu" and q["parca"] == "makine_plakasi")
            with self.subTest(tip=tip, saptirma=sap):
                self.assertEqual(plaka[5], zs)
                #  Kaideye oturan her parça plakanın üstünde
                oturan = [q for q in M["makine"] if abs(makine.sinirlar(q)[4] - zs) < 1.0]
                self.assertTrue(oturan)
                for q in oturan:
                    b = makine.sinirlar(q)
                    self.assertTrue(
                        plaka[0] <= b[0] and b[2] <= plaka[2] and plaka[1] <= b[1] and b[3] <= plaka[3],
                        (q.get("parca"), b, plaka),
                    )
                r = g["aski"]["halat_capi"] / 2.0
                KU = M["KU"]
                y0 = KU["halatlar"][0][1]
                noktalar = [(KU["yakin"], y0)]
                if sap:
                    ((P1, P2),) = [((a[0], a[2]), (b[0], b[2])) for a, b in M["agirlik_yolu"]]
                    noktalar += [
                        (P1[0] + (z - P1[1]) * (P2[0] - P1[0]) / (P2[1] - P1[1]), y0)
                        for z in (zs, zs - makine.MOTOR_PLAKASI_KALINLIK)
                    ]
                    levha = [
                        q["k"] for q in parcalar if q["tur"] == "kutu" and q["parca"] == "saptirma_levhasi"
                    ]
                    self.assertTrue(levha and all(k[5] == zs - makine.MOTOR_PLAKASI_KALINLIK for k in levha))
                else:
                    noktalar.append((M["agirlik_dusus"][0], y0))
                for x, y in noktalar:
                    self.assertTrue(plaka[0] < x < plaka[2] and plaka[1] < y < plaka[3])
                    self.assertTrue(self._delikte(parcalar, x, y, r), (x, y))
                ks = M["kasnak"]
                if ks[4] - g["makine"]["tahrik_kasnak_capi"] / 2.0 < zs:
                    #  Plakanın altına sarkan kasnak kendi yuvasından geçer
                    self.assertTrue(
                        any(
                            q["k"][0] <= ks[0]
                            and ks[2] <= q["k"][2]
                            and q["k"][1] <= ks[1]
                            and ks[3] <= q["k"][3]
                            for q in parcalar
                            if q["tur"] == "kutu" and q["parca"] == "halat_deligi"
                        )
                    )

    def test_korkuluk_yuksekligi_ve_kotu_iki_kesitte(self):
        g = _ornek()
        Y = kuyu_kesiti.yerlesim(g)
        h = max(h for _, h in kabin_ustu.korkuluklar(Y["KU"]))
        for ciz, z in ((kuyu_kesiti.yan_kesit, 0), (kuyu_kesiti.on_kesit, Y["kotlar"][-1])):
            es = [e for e in ciz(g) if e.get("ad") == "korkuluk"]
            self.assertTrue(es)
            zs = [e[k] for e in es for k in ("y1", "y2")]
            tavan = z + g["dusey"]["kabin_ic_yukseklik"] + Y["S"]["kabin_tavan_kalinlik"]
            self.assertEqual(min(zs), tavan)
            self.assertEqual(max(zs), tavan + h)

    def test_kirik_kesit_korkulugu_kesmez(self):
        g = _ornek()
        tam = [e for e in kuyu_kesiti.yan_kesit(g) if e.get("ad") == "korkuluk"]
        kirik = [e for e in kuyu_kesiti.yan_kesit(g, azami=10000) if e.get("ad") == "korkuluk"]

        def parcalar(es):
            return sorted(tuple(sorted(((e["x1"], e["y1"]), (e["x2"], e["y2"])))) for e in es)

        self.assertEqual(parcalar(kirik), parcalar(tam))


if __name__ == "__main__":
    unittest.main()

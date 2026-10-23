"""ELEKTRİK PROJESİ — hesabın elektrik değerleri tek hat şemasına ve kuyu
tesisatına aynen geçer;  paftada kapağın yanında, alt satırın solunda durur
( cizim/elektrik.py, ciktilar/dxf_cikti — 23 Eki, kullanıcı:  "kuyuya hesapta
çıkan adette aydınlatma, kabine hesaptaki adet, motor gücü … DXF'te sol alta" ).
"""

import io
import json
import math
import unittest
import zipfile

import ezdxf
from ezdxf import bbox
from pypdf import PdfReader

from cizim import eleman
from cizim import elektrik
from cizim import geometri
from cizim import pafta
from cizim import uslup
from ciktilar import dxf_cikti
from ciktilar import pafta_pdf
from ciktilar import pdf_cikti
from dogrulama.altin_uret import avan_senaryolar, uygulama_senaryolar
from motor.avan import avan_hesabi
from motor.avan import tablolar
from motor.uygulama import uygulama_hesabi

K = elektrik.K
SAYFA = (0.0, 0.0, elektrik.EN * K, elektrik.BOY * K)


def _avan_asansorleri():
    """Altın avan senaryolarının hesaplanan asansörleri:  ( sonuç , asansör )."""
    for g in avan_senaryolar():
        s = avan_hesabi.hesapla(json.loads(json.dumps(g)))
        for a in s.get("asansorler") or []:
            if a.get("aktif"):
                yield s, a


def _uygulama_asansorleri():
    for g in uygulama_senaryolar():
        s = uygulama_hesabi.hesapla_coklu(g.get("asansorler"), g.get("ortak"))
        for a in s.get("asansorler") or []:
            if a.get("aktif"):
                yield s, a


def _ornek(**degisen):
    v = {
        "tablo": "TAS1",
        "motor_kW": 4.9,
        "motor_sigorta_A": 16,
        "kuyu": {"adet": 6, "W": 40, "sigorta_A": 10},
        "kabin": {"adet": 4, "W": 5, "sigorta_A": 10},
        "kabin_ustu": {"adet": 1, "W": 5},
        "priz": {"adet": 3, "W": 300, "sigorta_A": 16},
        "kolon": {"S": 6, "SPE": 6, "kablo": "NHXMH FE180"},
        "makine_besleme": {"S": 6, "SPE": 6},
        "kacak_akim_A": 0.3,
        "makine_dairesi": False,
    }
    for k, d in degisen.items():
        v[k] = dict(v[k], **d) if isinstance(v.get(k), dict) and isinstance(d, dict) else d
    return v


#  Makine dairesi aydınlatması bu tablodan ( avan_hesabi._elektrik_projesi )
MD_DEVRESI = {"adet": 6, "W": 40, "sigorta_A": 10}


def _yazilar(e):
    return [el["metin"] for el in e if el["tip"] == "yazi"]


def _ornek_sayisi(e, ad):
    """Kuyunun içindeki parça örnekleri ( sembol listesindeki ve kuyunun üstündeki
    odadaki sayılmaz )."""
    return sum(
        1
        for a, liste in geometri.parca_ornekleri(e)
        if a == ad
        and geometri.sinir(liste)[0] > elektrik._KX0 * K
        and geometri.sinir(liste)[3] < elektrik._UST_Y0 * K
    )


def _cetvel(a):
    return next(b for b in a["bolumler"] if b.get("kimlik") == "kurulu_guc")


class HesabinDegerleri(unittest.TestCase):
    """Elektrik projesinin değerleri hesabın kendisinden:  kurulu güç cetveli,
    armatür adetleri, motor, kablo ( avan_hesabi._elektrik_projesi )."""

    def _ayni(self, s, a, v):
        o = a["ozet"]
        self.assertEqual(v["kuyu"]["adet"], o["n_kuyu"])
        self.assertEqual(v["kabin"]["adet"], o["n_kabin"])
        self.assertEqual(v["motor_kW"], o["Nsc"])
        self.assertEqual(v["motor_sigorta_A"], o["sigorta_A"])
        self.assertEqual(v["kolon"], {"S": o["S1"], "SPE": o["SPE1"], "kablo": o["kablo_tipi"]})
        self.assertEqual(v["makine_besleme"], {"S": o["S2"], "SPE": o["SPE2"]})
        self.assertEqual(v["motor_akimi_A"], o["I_motor"])
        #  Kurulu güç cetvelinin satırları şemanın devreleri:  sigortaları ve
        #  armatürlerin / prizin gücü aynı;  makine dairesi aydınlatması yalnız
        #  onu besleyen tablonun cetvelinde ( adedi hesaplanmışsa )
        c = _cetvel(a)["cetvel"]
        md = v.get("makine_dairesi_ayd") or {}
        devreler = [
            (v["kuyu"], v["kuyu"]["adet"] * v["kuyu"]["W"]),
            (v["kabin"], (v["kabin"]["adet"] + v["kabin_ustu"]["adet"]) * v["kabin"]["W"]),
        ]
        if md.get("adet"):
            devreler.append((md, md["adet"] * md["W"]))
        devreler.append((v["priz"], v["priz"]["adet"] * v["priz"]["W"]))
        self.assertEqual([r["sigorta"] for r in c[1:]], [str(d["sigorta_A"]) for d, _g in devreler])
        for r, (_d, guc) in zip(c[1:], devreler):
            self.assertAlmostEqual(r["guc"], guc)
        self.assertAlmostEqual(o["P_kurulu"], sum(r["guc"] for r in c))
        if v["motor_sigorta_A"]:
            self.assertEqual(c[0]["sigorta"], f"4 x {v['motor_sigorta_A']}")

    def test_avan(self):
        n = 0
        for s, a in _avan_asansorleri():
            with self.subTest(no=a["no"], baslik=a["baslik"]):
                v = a["elektrik"]
                self.assertEqual(v["tablo"], f"TAS{a['no']}")
                self.assertIn(f"TAS{a['no']}", _cetvel(a)["kaynak"])
                self.assertEqual(v["kacak_akim_A"], s["sabitler"]["IDn"])
                self._ayni(s, a, v)
                n += 1
        self.assertGreater(n, 50)

    def test_makine_dairesi_var_mi(self):
        #  Hesabı yapılan makine dairesinin sonucunda "mk_yok" yazmaz:  23 Eki ilk
        #  yazımda oda görülmüyordu ( ana tabloda aydınlatma devresi çıkmıyordu )
        g = next(iter(avan_senaryolar()))
        for ortak, oda in (
            ({"mk_uzunluk": 3000, "mk_genislik": 2500}, True),
            ({"mk_yok": False}, True),
            ({"mk_yok": True, "mk_uzunluk": 3000, "mk_genislik": 2500}, False),
            ({}, False),
        ):
            with self.subTest(ortak=ortak):
                v = dict(g, ortak=dict(ortak))
                s = avan_hesabi.hesapla(json.loads(json.dumps(v)))
                self.assertEqual(s["asansorler"][0]["elektrik"]["makine_dairesi"], oda)
        from hesap_girdi import ASANSOR, ASANSOR_MD, ORTAK, ORTAK_MD
        from uclar import uygulama_istegi

        for asansor, ortak, oda in ((ASANSOR, ORTAK, False), (ASANSOR_MD, ORTAK_MD, True)):
            with self.subTest(oda=oda):
                veri = {
                    "asansorler": [dict(asansor, siginma_tipi_dip="Yatarak")],
                    "proje_geneli": dict(ortak),
                }
                s = uygulama_hesabi.hesapla_coklu(*uygulama_istegi.asansor_girdileri(veri))
                self.assertEqual(s["asansorler"][0]["elektrik"]["makine_dairesi"], oda)

    def test_makine_dairesi_aydinlatmasi_tek_tabloda(self):
        #  Oda tektir:  aydınlatması ilk asansörün tablosundan beslenir ( devresi,
        #  cetvel satırı, kolon hattının yükü ) — öbür tablolar onu yalnız anar
        #  ( 23 Eki, kullanıcı:  "makine daireli ise makine dairesi aydınlatmasını
        #  da koymamız gerekiyor" )
        sayac = {"avan": 0, "uygulama": 0}
        for g in avan_senaryolar():
            s = avan_hesabi.hesapla(json.loads(json.dumps(g)))
            mk = s.get("makine_dairesi") or {}
            vs = [a["elektrik"] for a in s.get("asansorler") or [] if a.get("elektrik")]
            if not vs or not vs[0]["makine_dairesi"]:
                self.assertFalse(any("makine_dairesi_ayd" in v for v in vs))
                continue
            with self.subTest(senaryo=sayac["avan"]):
                ilk, digerleri = vs[0], vs[1:]
                self.assertEqual(ilk["makine_dairesi_ayd"]["adet"], mk.get("n"))
                self.assertEqual(ilk["makine_dairesi_ayd"]["sigorta_A"], avan_hesabi.SIGORTA_AYDINLATMA)
                for v in digerleri:
                    self.assertEqual(v["makine_dairesi_ayd"], {"besleyen": ilk["tablo"]})
                sayac["avan"] += 1
        for _s, a in _uygulama_asansorleri():
            v = a["elektrik"]
            if not v["makine_dairesi"]:
                continue
            with self.subTest(no=a["no"], tanim=a["tanim"]):
                md = v["makine_dairesi_ayd"]
                satir = [r for r in _cetvel(a)["cetvel"] if r["sorti"].startswith("MAKİNE DAİRESİ")]
                if a["no"] == 1:
                    self.assertTrue(md.get("adet"))
                    self.assertEqual([r["guc"] for r in satir], [md["adet"] * md["W"]])
                else:
                    self.assertEqual(md, {"besleyen": "TAS1"})
                    self.assertEqual(satir, [])
                sayac["uygulama"] += 1
        self.assertGreater(sayac["avan"], 20)
        self.assertGreater(sayac["uygulama"], 3)

    def test_makine_dairesi_elektrigi_hesaplanan_ilk_tabloda(self):
        #  Devre hep 1. asansörün tablosuna veriliyordu:  onun hesabı düşünce TAS1
        #  çizilmiyor, öbürleri "Aydınlatma devresi:  TAS1" diyordu — devre ve yükü
        #  pakette hiçbir tabloda yoktu ( 23 Eki bağımsız denetim )
        def md_satiri(a):
            return [r for r in _cetvel(a)["cetvel"] if r["sorti"].startswith("MAKİNE DAİRESİ")]

        g = next(iter(avan_senaryolar()))
        a = g["asansorler"][0]
        s = avan_hesabi.hesapla(
            json.loads(json.dumps(dict(g, asansorler=[dict(a, Nsc=0.01), dict(a), dict(a)])))
        )
        bir, iki, uc = s["asansorler"]
        self.assertFalse(bir["aktif"])
        md = iki["elektrik"]["makine_dairesi_ayd"]
        self.assertEqual(
            (md["adet"], md["sigorta_A"]), (s["makine_dairesi"]["n"], avan_hesabi.SIGORTA_AYDINLATMA)
        )
        self.assertEqual([r["guc"] for r in md_satiri(iki)], [md["adet"] * md["W"]])
        self.assertEqual(uc["elektrik"]["makine_dairesi_ayd"], {"besleyen": "TAS2"})
        self.assertEqual(md_satiri(uc), [])

        oda = {"temel_a": 26.55, "temel_b": 16.4, "mk_yok": False, "mk_uzunluk": 4000, "mk_genislik": 3000}
        s = uygulama_hesabi.hesapla_coklu([{"halat_adedi": 1}, {}, {}], oda)
        bir, iki, uc = s["asansorler"]
        self.assertFalse(bir["aktif"])
        self.assertEqual(iki["elektrik"]["tablo"], "TAS2")
        self.assertTrue(iki["elektrik"]["makine_dairesi_ayd"]["adet"])
        self.assertEqual(len(md_satiri(iki)), 1)
        self.assertEqual(uc["elektrik"]["makine_dairesi_ayd"], {"besleyen": "TAS2"})
        self.assertEqual(md_satiri(uc), [])

    def test_uygulama_her_asansor_kendi_tablosu(self):
        #  Avan motoru her asansörü tek başına hesaplar:  çok asansörlü uygulama
        #  projesinde dört cetvel de TAS1'di ( 23 Eki )
        cok = 0
        for _s, a in _uygulama_asansorleri():
            with self.subTest(no=a["no"], tanim=a["tanim"]):
                self.assertEqual(a["elektrik"]["tablo"], f"TAS{a['no']}")
                self.assertEqual(_cetvel(a)["kaynak"], f"tablo adı :  TAS{a['no']}")
                self.assertEqual(a["elektrik"]["kuyu"]["adet"], a["ozet"]["n_kuyu"])
                self.assertEqual(a["elektrik"]["kabin"]["adet"], a["ozet"]["n_kabin"])
                cok += a["no"] > 1
        self.assertGreater(cok, 3)


class Sema(unittest.TestCase):
    """Şema hesabın sayılarını gösterir:  kuyuya hesabın adedi kadar armatür,
    kabinde hesaptaki adet, motor gücü, sigortalar, kablo."""

    def test_kuyuya_hesabin_adedi_kadar_armatur(self):
        for n in (1, 2, 3, 6, 12, 22):
            with self.subTest(n=n):
                e = elektrik.ciz(_ornek(kuyu={"adet": n}))
                self.assertEqual(_ornek_sayisi(e, "etanj_armatur"), n)
                self.assertEqual(_yazilar(e).count("Etanj 1x40 W"), n)
                self.assertFalse(any("toplam" in y for y in _yazilar(e)))

    def test_cok_armaturde_kirik_ve_toplam(self):
        #  Kuyu çok yüksekse armatürlerin hepsi sayfaya sığmaz:  aradakiler kırıkla
        #  gösterilir, adedi yazar
        for n in (23, 40, 90):
            with self.subTest(n=n):
                e = elektrik.ciz(_ornek(kuyu={"adet": n}))
                self.assertLess(_ornek_sayisi(e, "etanj_armatur"), n)
                self.assertIn(f"( toplam {n} adet )", _yazilar(e))

    def test_degerler_semada(self):
        v = _ornek(
            motor_kW=11.3,
            motor_sigorta_A=32,
            motor_akimi_A=24.6789,
            kabin={"adet": 7, "W": 5.5},
            kuyu={"adet": 9, "W": 36},
        )
        y = _yazilar(elektrik.ciz(v, "ASANSÖR 2"))
        for metin in (
            "TAS1",
            "11,3 kW  ·  I = 24,68 A",
            "4x32A",
            "7x5,5W Led Spot",
            "1x5W Led Spot",
            "Etanj 1x36 W",
            "4x6/6 NHXMH FE180",
            "IΔn 300 mA",
            "10 A",
            "16 A",
            #  kuraldan:  güç K.A.R ≥ 32 → 40, kesici ≥ 32 → 32, aydınlatma K.A.R 25 / 30 mA,
            #  pako ≥ 40;  kablolar 3x1,5 ( 10 A ) ve 3x2,5 ( 16 A ) mm², kolonun ailesinden
            "4x40A",
            "2x25A",
            "30 mA",
            "3x1,5 mm² NHXMH",
            "3x2,5 mm² NHXMH",
            "TAS1  ·  ASANSÖR 2",
            "Kabin + kabin üstü aydınlatması  ( 7x5,5 W + 1x5 W )",
            "Kuyu aydınlatması  ( 9x36 W )",
            "Priz  ( 3x300 W )",
        ):
            self.assertIn(metin, y)

    def test_hesabin_vermedigi_deger_yazilmaz(self):
        #  Motor sigortası tablonun dışındaysa ( hesap "uygulama projesinde" yazar )
        #  şema sayı uydurmaz
        y = _yazilar(elektrik.ciz(_ornek(motor_sigorta_A=None, kolon={"SPE": None})))
        self.assertFalse(any(m.startswith("4x") and m.endswith("A") and "/" not in m for m in y), y)
        self.assertIn("4x6 NHXMH FE180", y)

    def test_iki_kacak_akim_rolesi(self):
        #  Güç devresininki hesabın IΔn'ı ( topraklama direncine göre ), aydınlatma ve
        #  prizinki 30 mA ( Asansör Periyodik Kontrol EK-5 1.33.11 · 12 · 14 )
        e = elektrik.ciz(_ornek(kacak_akim_A=0.3))
        tek_hat = [x for a, x in geometri.parca_ornekleri(e) if a == "kacak_akim_rolesi"]
        sol = [
            x for x in tek_hat if geometri.sinir(x)[2] < elektrik._KX0 * K and geometri.sinir(x)[1] > 200 * K
        ]
        self.assertEqual(len(sol), 2)
        y = _yazilar(e)
        self.assertIn("IΔn 300 mA", y)
        self.assertGreaterEqual(y.count("30 mA"), 2)  # tek hat şeması ve ana tablo

    def test_makine_dairesi(self):
        #  Aydınlatması bu tablodan:  tek hat şemasında kendi sigortası ve kablosu,
        #  ana tabloda amperiyle ( 23 Eki öncesi ana tabloda amperi yazmıyordu, tek
        #  hat şemasında hiç yoktu ), odada armatürü ( hesabın adedi ) ve anahtarı
        e = elektrik.ciz(_ornek(makine_dairesi=True, makine_dairesi_ayd=MD_DEVRESI))
        y = _yazilar(e)
        self.assertIn("MAKİNE DAİRESİ", y)
        self.assertIn("Makine dairesi aydınlatması  ( 6x40 W )", y)  # tek hat şeması
        self.assertIn("Makine dairesi aydınlatması", y)  # ana tablo
        self.assertIn("Etanj 1x40 W  ( 6 adet )", y)
        self.assertIn("Anahtar", y)
        self.assertEqual(y.count("10 A"), 6)  # kabin, kuyu, makine dairesi:  şemada ve ana tabloda
        self.assertEqual(y.count("3x1,5 mm² NHXMH"), 3)
        anahtarlar = [x for a, x in geometri.parca_ornekleri(e) if a == "anahtar"]
        self.assertEqual(len(anahtarlar), 2)  # odada ve sembol listesinde
        #  Kuyunun armatürleri hesabın adedi kadar ( odanınki sayılmaz )
        self.assertEqual(_ornek_sayisi(e, "etanj_armatur"), 6)
        #  Aydınlatması başka bir asansörün tablosundan:  yalnız onu anar
        y = _yazilar(elektrik.ciz(_ornek(makine_dairesi=True, makine_dairesi_ayd={"besleyen": "TAS1"})))
        self.assertIn("MAKİNE DAİRESİ", y)
        self.assertIn("Aydınlatma devresi:  TAS1", y)
        self.assertFalse(any(m.startswith("Makine dairesi aydınlatması") for m in y), y)
        self.assertEqual(y.count("10 A"), 4)
        y = _yazilar(elektrik.ciz(_ornek()))
        self.assertIn("KUYU ÜSTÜ", y)
        self.assertFalse(any(m.startswith("Makine dairesi aydınlatması") for m in y), y)
        self.assertNotIn("Anahtar", y)


def _dondur(el, u0, u1, v0, v1):
    """Yazıya göre kutu ( u yazı boyunca, v yazının ortasından yukarı ) → çizimin
    kutusu;  90° yazı yukarı okunur."""
    x, y = el["x"], el["y"]
    if abs(el.get("aci", 0)) > 1:
        return (x - v1, y + u0, x - v0, y + u1)
    return (x + u0, y + v0, x + u1, y + v1)


def _harfler(el):
    """Harflerin kutusu:  taban yazının ortasının 0,35 h altında, büyük harf
    üstte, alt uzantılı harfler ( Ç, Ş, g ) altta ( cizim/pdf._metin )."""
    h = el["yukseklik"]
    w = eleman.yazi_eni(el["metin"], h)
    a = {"sol": 0.0, "sag": -w}.get(el.get("hiza"), -w / 2.0)
    return _dondur(el, a, a + w, -0.56 * h, 0.366 * h)


def _maske(el):
    """Yazının maskesi:  PDF'teki ( harflerin kutusu + maske payı ) — üç çıktının
    en genişi;  çizgi buraya girerse kâğıtta kesik çıkar."""
    pay = uslup.maske_payi(el["yukseklik"])
    x0, y0, x1, y1 = _harfler(el)
    return (x0 - pay, y0 - pay, x1 + pay, y1 + pay)


def _ortusur(a, b, pay):
    return a[0] < b[2] - pay and b[0] < a[2] - pay and a[1] < b[3] - pay and b[1] < a[3] - pay


def _kenarlar(el):
    """Çizgi elemanlarının doğru parçaları ( dikdörtgenin dört kenarı, biçimin
    kenarları )."""
    if el["tip"] in ("cizgi", "eksen"):
        return [((el["x1"], el["y1"]), (el["x2"], el["y2"]))]
    if el["tip"] == "daire":
        n = 16
        p = [
            (
                el["x"] + el["r"] * math.cos(2 * math.pi * i / n),
                el["y"] + el["r"] * math.sin(2 * math.pi * i / n),
            )
            for i in range(n + 1)
        ]
        return list(zip(p, p[1:]))
    if el["tip"] == "dikdortgen":
        if "bicim" in el:
            out = []
            for b in el["bicim"]:
                p = list(b["noktalar"]) + ([b["noktalar"][0]] if b.get("kapali", True) else [])
                out += list(zip(p, p[1:]))
            return out
        x, y, g, d = el["x"], el["y"], el["g"], el["d"]
        p = [(x, y), (x + g, y), (x + g, y + d), (x, y + d), (x, y)]
        return list(zip(p, p[1:]))
    return []


def _kesiyor(kutu, a, b):
    """Doğru parçası kutunun içinden geçiyor mu ( Liang–Barsky )."""
    x0, y0, x1, y1 = kutu
    t0, t1 = 0.0, 1.0
    dx, dy = b[0] - a[0], b[1] - a[1]
    for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
        if abs(p) < 1e-12:
            if q < 0:
                return False
            continue
        t = q / p
        if p < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 > t1:
            return False
    return True


def _sorunlar(e):
    """Yazı yazıya ya da çizgiye biniyor mu, sayfadan taşan var mı:  [ ileti ].
    Bir yazının maskesi öbür yazının harflerine binmez ( sonra basılan önce
    basılanı örterdi ), hiçbir çizgi maskeye girmez."""
    out = []
    yazilar = [el for el in e if el["tip"] == "yazi"]
    harf = [_harfler(el) for el in yazilar]
    maske = [_maske(el) for el in yazilar]
    for i, el in enumerate(yazilar):
        if not _ortusur(harf[i], SAYFA, -1) or not (
            SAYFA[0] <= harf[i][0]
            and harf[i][2] <= SAYFA[2]
            and SAYFA[1] <= harf[i][1]
            and harf[i][3] <= SAYFA[3]
        ):
            out.append(f"sayfadan taşıyor:  {el['metin']!r}")
        for j in range(len(yazilar)):
            if i != j and _ortusur(maske[i], harf[j], 0.1 * K):
                out.append(f"yazı yazıya biniyor:  {el['metin']!r} · {yazilar[j]['metin']!r}")
    for el in e:
        for a, b in _kenarlar(el):
            for i, k in enumerate(maske):
                if _kesiyor(k, a, b):
                    out.append(
                        f"çizgi yazının maskesine giriyor:  {yazilar[i]['metin']!r} ( {el['katman']} )"
                    )
    x0, y0, x1, y1 = geometri.sinir(e)
    if x0 < -1 or y0 < -1 or x1 > SAYFA[2] + 1 or y1 > SAYFA[3] + 1:
        out.append(f"sayfadan taşıyor:  {(x0, y0, x1, y1)}")
    return out


class Kurallar(unittest.TestCase):
    """Şalterlerin ve kaçak akım rölelerinin anma akımı birlikte çalıştığı
    sigortadan küçük olmaz, sonra standart kademe;  son devrenin kesiti
    sigortayı taşır ( EK-5 1.31.13 ) ve yönetmeliğin en küçüğünden az olmaz."""

    def test_anma_akimlari(self):
        for grup in (None, 6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 630):
            with self.subTest(grup=grup):
                a = elektrik.anma_akimlari(_ornek(motor_sigorta_A=grup))
                self.assertEqual(a["ayd_kar"], 25)
                if grup is None:
                    self.assertIsNone(a["guc_kar"])
                    self.assertIsNone(a["kesici"])
                    self.assertIsNone(a["pako"])  # tablonun girişi motoru da taşır
                    continue
                #  en küçük uyan kademe:  kaçak akım rölesinin kademesi bitince ( 125 A
                #  üstü ) röleli kesici — şalter kademesi
                kar = [k for k in elektrik.KAR_KADEMELERI if k >= grup]
                self.assertEqual(
                    a["guc_kar"], kar[0] if kar else min(k for k in elektrik.SALTER_KADEMELERI if k >= grup)
                )
                self.assertEqual(a["kesici"], min(k for k in elektrik.SALTER_KADEMELERI if k >= grup))
                self.assertGreaterEqual(a["guc_kar"], grup)
                self.assertGreaterEqual(a["kesici"], grup)
                self.assertGreaterEqual(a["pako"], max(a["guc_kar"], a["ayd_kar"]))
        #  Referans paftanın sırası:  4x25A sigorta → kesici 25 ( ≥ 25 ), K.A.R 25
        a = elektrik.anma_akimlari(_ornek(motor_sigorta_A=25))
        self.assertEqual((a["kesici"], a["guc_kar"]), (25, 25))

    def test_devre_kesiti(self):
        for amper, en_az, kesit in (
            (10, 1.5, 1.5),
            (16, 2.5, 2.5),
            (16, 1.5, 2.5),
            (20, 1.5, 2.5),
            (25, 1.5, 4.0),
            (50, 1.5, 6.0),
            (63, 1.5, None),
            (6, 1.0, 1.0),
        ):
            with self.subTest(amper=amper, en_az=en_az):
                self.assertEqual(elektrik.devre_kesiti(amper, en_az), kesit)
        self.assertEqual(elektrik.devre_kablosu(_ornek(), 10, 1.5), "3x1,5 mm² NHXMH")
        self.assertEqual(elektrik.devre_kablosu(_ornek(kolon={"kablo": ""}), 16, 2.5), "3x2,5 mm²")

    def test_grup_sigortasi_makine_besleme_kablosunu_korur(self):
        #  Hesap motor akımını kabloyla karşılaştırıyordu ( I2 ≤ Iz2 ), seçtiği
        #  sigortayı değil:  4 mm² kabloya 4 x 40 A "uygundu" ( 23 Eki bağımsız
        #  denetim ).  Sınır son devrelerin kablosuyla aynı tablo ( EK-5 1.31.13 ),
        #  6 mm² üstünde Iz;  kesitle birlikte artar
        for kesit, sinir in ((1.5, 10), (2.5, 20), (3, 20), (4, 32), (6, 50), (8, 50), (10, 57), (16, 76)):
            with self.subTest(kesit=kesit):
                self.assertEqual(tablolar.sigorta_siniri(kesit)[0], sinir)
        self.assertIsNone(tablolar.sigorta_siniri(0.5)[0])
        sinirlar = [tablolar.sigorta_siniri(k)[0] for k in tablolar.STANDART_KESITLER]
        self.assertEqual(sinirlar, sorted(sinirlar))

        g = next(iter(avan_senaryolar()))
        a = g["asansorler"][0]
        sayi = {True: 0, False: 0}
        for S2 in (2.5, 4, 6, 10):
            for Nsc in (5.5, 9.2, 11, 13, 15, 18.5, 22):
                with self.subTest(S2=S2, Nsc=Nsc):
                    v = dict(g, asansorler=[dict(a, S2=S2, Nsc=Nsc)])
                    x = avan_hesabi.hesapla(json.loads(json.dumps(v)))["asansorler"][0]
                    sig, I2 = x["elektrik"]["motor_sigorta_A"], x["ozet"]["I2"]
                    korunmuyor = sig > tablolar.sigorta_siniri(S2)[0]
                    uyari = [u for u in x["engelleyici"] if "SİGORTAYLA KORUNMUYOR" in u]
                    self.assertEqual(len(uyari), int(korunmuyor), uyari)
                    b6 = next(b for b in x["bolumler"] if b.get("kimlik") == "gerilim_dusumu")
                    self.assertIn(
                        "In ≤  Inmax2:  " + ("UYGUN DEĞİL" if korunmuyor else "UYGUN"),
                        "\n".join(b6["sonuc"]["alt"]),
                    )
                    if korunmuyor:
                        self.assertFalse(b6["sonuc"]["uygun"])
                        #  Önerilen kesit akımı da taşır, sigortayla da korunur;  bir küçüğü değil
                        en_az = tablolar.gerekli_kesit(I2, sig)
                        self.assertIn(f"en az {en_az:g} mm²".replace(".", ","), uyari[0])
                        once = tablolar.STANDART_KESITLER[tablolar.STANDART_KESITLER.index(en_az) - 1]
                        self.assertTrue(
                            tablolar.kablo_iz_sinir(once)[0] < I2 or tablolar.sigorta_siniri(once)[0] < sig
                        )
                    sayi[korunmuyor] += 1
        self.assertGreater(sayi[True], 5)
        self.assertGreater(sayi[False], 5)
        #  Uygulama projesi aynı motoru kullanır:  hükme ve engelleyiciye girer
        from hesap_girdi import ASANSOR, ORTAK
        from uclar import uygulama_istegi

        veri = {"asansorler": [dict(ASANSOR, motor_gucu=15, makine_kesit=4)], "proje_geneli": dict(ORTAK)}
        x = uygulama_hesabi.hesapla_coklu(*uygulama_istegi.asansor_girdileri(veri))["asansorler"][0]
        self.assertTrue(any("SİGORTAYLA KORUNMUYOR" in u for u in x["ozet"]["engelleyici"]))


class Kalite(unittest.TestCase):
    """Yazılar birbirine ve çizgilere binmez, sayfadan taşmaz — hesabın gerçek
    değerleriyle ( altın senaryoların bütün asansörleri ) ve uç değerlerle."""

    def test_hesabin_butun_asansorlerinde(self):
        gorulen = set()
        for _s, a in list(_avan_asansorleri()) + list(_uygulama_asansorleri()):
            v = a["elektrik"]
            imza = json.dumps(v, sort_keys=True, default=str)
            if imza in gorulen:
                continue
            gorulen.add(imza)
            with self.subTest(v=imza[:160]):
                self.assertEqual(_sorunlar(elektrik.ciz(v, "1 NOLU ASANSÖR  ·  İnsan")), [])
        self.assertGreater(len(gorulen), 20)

    def test_uc_degerler(self):
        for degisen in (
            {"kuyu": {"adet": 1}},
            {"kuyu": {"adet": 2}},
            {"kuyu": {"adet": 22}},
            {"kuyu": {"adet": 23}},
            {"kuyu": {"adet": 150, "W": 1000}},
            {"kabin": {"adet": 48, "W": 12.5}, "kabin_ustu": {"adet": 20, "W": 12.5}},
            {"kabin_ustu": {"adet": 0}},
            {"priz": {"adet": 0}},
            {"priz": {"adet": 1}},
            {"priz": {"adet": 2}},
            {"priz": {"adet": 50, "W": 10000}},
            {"motor_kW": 160, "motor_sigorta_A": 630},
            {"motor_sigorta_A": None},
            {
                "kolon": {"S": 240, "SPE": 120, "kablo": "NHXMH FE180"},
                "makine_besleme": {"S": 240, "SPE": 120},
            },
            {"kolon": {"S": 6, "SPE": None, "kablo": ""}},
            {"kacak_akim_A": 0.03},
            {"kacak_akim_A": None},
            {"makine_dairesi": True},
            {"makine_dairesi": True, "makine_dairesi_ayd": MD_DEVRESI},
            {"makine_dairesi": True, "makine_dairesi_ayd": dict(MD_DEVRESI, adet=None)},
            {"makine_dairesi": True, "makine_dairesi_ayd": dict(MD_DEVRESI, adet=240, W=1000)},
            {"makine_dairesi": True, "makine_dairesi_ayd": MD_DEVRESI, "kuyu": {"adet": 150}},
            {"makine_dairesi": True, "makine_dairesi_ayd": {"besleyen": "TAS1"}},
        ):
            with self.subTest(degisen=degisen):
                self.assertEqual(_sorunlar(elektrik.ciz(_ornek(**degisen), "ASANSÖR 4")), [])


class Pafta(unittest.TestCase):
    """Paftada kapağın yanında, alt satırın solunda;  hesap sayfaları yanından
    akar, çerçeve gerektiği kadar uzar ( dxf_cikti._yerlesim )."""

    def test_izgara(self):
        a4_g, a4_y = dxf_cikti.A4_G, dxf_cikti.A4_Y
        sol = dxf_cikti.SERBEST[0] + dxf_cikti.SOL_PAY
        for elektrik_adedi in range(5):
            for adet in range(0, 70, 3):
                with self.subTest(adet=adet, elektrik=elektrik_adedi):
                    ayrilan = elektrik.HUCRE * elektrik_adedi
                    yerler, tasti = dxf_cikti._yerlesim(adet, ayrilan)
                    self.assertFalse(tasti)
                    ey = dxf_cikti.elektrik_yerleri(adet, elektrik_adedi)
                    sag = dxf_cikti.BANT[2] + dxf_cikti._uzatma(adet, ayrilan)
                    kutular = [(x, y, x + a4_g, y + a4_y) for x, y in yerler]
                    kutular += [(x, y, x + elektrik.EN, y + elektrik.BOY) for x, y in ey]
                    for i, k in enumerate(kutular):
                        self.assertTrue(sol - 0.5 <= k[0] and k[2] <= sag + 0.5, k)
                        self.assertTrue(
                            dxf_cikti.BANT[1] - 0.5 <= k[1] and k[3] <= dxf_cikti.BANT[3] + 0.5, k
                        )
                        for j in range(i + 1, len(kutular)):
                            self.assertFalse(_ortusur(k, kutular[j], 0.5), (k, kutular[j]))
                    if ey:
                        #  Alt satırın başında, kapağın yanında;  ilk sayfa sol üstte
                        alt = min(y for _x, y in yerler + ey)
                        self.assertEqual(ey[0], (sol, alt))
                        if yerler:
                            self.assertEqual(yerler[0][0], sol)
                            self.assertGreater(yerler[0][1], alt)
                    else:
                        self.assertEqual(yerler, dxf_cikti._yerlesim(adet)[0])

    def test_avan_paftasi(self):
        g = next(iter(avan_senaryolar()))
        s = avan_hesabi.hesapla(json.loads(json.dumps(g)))
        e = elektrik.pafta_sayfalari(
            [(a["elektrik"], a["baslik"]) for a in s["asansorler"] if a.get("aktif")]
        )
        self.assertEqual([x[0] for x in e], ["elektrik"])
        paftalar = [("Avan", pdf_cikti.avan_pdf(s))]
        dxf = dxf_cikti.proje_dxf(paftalar, elektrikler=e)
        d = ezdxf.read(io.StringIO(dxf.decode("utf-8")))
        msp = d.modelspace()
        ins = [x for x in msp.query("INSERT") if x.dxf.name == pafta.blok_adi("elektrik")]
        self.assertEqual(len(ins), 1)
        n = len(dxf_cikti.sayfalari_topla(paftalar))
        ((x, y),) = dxf_cikti.elektrik_yerleri(n, 1)
        self.assertAlmostEqual(ins[0].dxf.insert.x, x)
        self.assertAlmostEqual(ins[0].dxf.insert.y, y)
        self.assertAlmostEqual(ins[0].dxf.xscale, 1 / elektrik.OLCEK)
        #  Hesap sayfaları elektrik projesine binmez
        for k in dxf_cikti.a4_cerceveleri(msp):
            self.assertFalse(_ortusur(k, (x, y, x + elektrik.EN, y + elektrik.BOY), 0.5), k)
        #  Paftanın PDF'i aynı yerde çizer ( blok adından )
        self.assertTrue(pafta_pdf.serit(dxf, paftalar, elektrikler=e).startswith(b"%PDF"))
        #  Şablonun katmanları geçerli malzeme / çizim stili kaydını gösterir:  avan
        #  paftası AutoCAD'in AUDIT'inde 16 hata veriyordu ( 23 Eki — uygulama
        #  paftası pafta.birlestir'de onarılıyordu )
        db = d.entitydb
        for k in d.layers:
            self.assertEqual(db[k.dxf.material_handle].dxftype(), "MATERIAL", k.dxf.name)
            self.assertEqual(db[k.dxf.plotstyle_handle].dxftype(), "ACDBPLACEHOLDER", k.dxf.name)

    def test_cok_asansorde_yan_yana(self):
        v = _ornek()
        e = elektrik.pafta_sayfalari(
            [(dict(v, tablo=f"TAS{i}"), f"ASANSÖR {i}") for i in (1, 2, 3)] + [(None, "")]
        )
        self.assertEqual([x[0] for x in e], ["elektrik_1", "elektrik_2", "elektrik_3"])
        ey = dxf_cikti.elektrik_yerleri(40, 3)
        self.assertEqual([round(b[0] - a[0], 6) for a, b in zip(ey, ey[1:])], [elektrik.EN, elektrik.EN])
        self.assertEqual(len({y for _x, y in ey}), 1)


class Paket(unittest.TestCase):
    """Projeyi paketle:  uygulama paketinde elektrik projesi ve çizimler birbirine
    binmez;  ayrı sayfalı PDF'te kendi sayfasında."""

    def test_uygulama_paketi(self):
        from hesap_girdi import ASANSOR, ORTAK, SABITLER
        from uclar import uygulama_uclari

        veri = {
            "asansorler": [dict(ASANSOR, siginma_tipi_dip="Yatarak")],
            "proje_geneli": dict(ORTAK),
            "sabitler": dict(SABITLER),
            "asansor": 0,
        }
        z = zipfile.ZipFile(io.BytesIO(uygulama_uclari.indir_uygulama_dwg(veri).body))
        ad = next(n for n in z.namelist() if n.endswith(".dxf"))
        d = ezdxf.read(io.StringIO(z.read(ad).decode("utf-8")))
        msp = d.modelspace()
        ekler = {x.dxf.name: x for x in msp.query("INSERT") if x.dxf.name.startswith("CIZIM_")}
        self.assertIn("CIZIM_ELEKTRIK", ekler)
        kutu = {ad_: bbox.extents([x]) for ad_, x in ekler.items()}
        el = kutu.pop("CIZIM_ELEKTRIK")
        for ad_, k in kutu.items():
            #  Çizimler hesap sayfalarının ve elektrik projesinin sağında
            self.assertGreaterEqual(k.extmin.x, el.extmax.x - 0.5, ad_)
        self.assertIn("Elektrik projesi", z.read("OKUBENI.txt").decode())
        cizimler = next(n for n in z.namelist() if n.endswith("çizimler.pdf"))
        sayfalar = PdfReader(io.BytesIO(z.read(cizimler))).pages
        son = sayfalar[-1].mediabox
        pay = 2 * 5.0
        self.assertAlmostEqual(float(son.width) * 25.4 / 72, elektrik.EN + pay, places=1)
        self.assertAlmostEqual(float(son.height) * 25.4 / 72, elektrik.BOY + pay, places=1)
        self.assertIn("TOPRAKLAMA TESİSATI", sayfalar[-1].extract_text())


if __name__ == "__main__":
    unittest.main()

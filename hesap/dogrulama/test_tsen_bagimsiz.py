"""Bağımsız EN 81-50 sayısal denetimi, 2026-09-09.

Çalıştırma: .venv/bin/python -m unittest dogrulama.test_tsen_bagimsiz -v
Kaynak: https://liftescalatorlibrary.org/paper_indexing/papers/00000063.pdf
Bu yayın standardın kendisi değildir; 2014 baskısını açıklayan örneklerdir.
Tam TS baskısı doğrulaması yerine geçmez. Üretim kodunu değiştirmez.
Beklenen değerler altın çıktıdan alınmaz. Kalan testler açık bulgudur.
"""

import math
import re
import unittest

from engine.uygulama import mukavemet as M
from engine.uygulama import mukavemet_girdi as MG
from engine.uygulama import mukavemet_tablolari as T
from engine.uygulama import sabitler as U
from dogrulama.ortak import P_std


class BagimsizDenetim(unittest.TestCase):
    def test_yayin_halat_guvenligi(self):
        # Yayın §5: aynı halat/kasnak girdileri; diğer proje alanları varsayılan.
        s = M.hesapla(
            {
                "beyan_yuku": 1000,
                "kabin_agirligi": 1250,
                "tahrik_kasnak_capi": 320,
                "saptirma_kasnak_capi": 320,
                "halat_capi": 8,
                "halat_adedi": 5,
                "halat_kopma_kN": 43,
                "kasnak_tek_yon": 2,
                "kanal_sekli": "V Kanal",
                #  Yayında halat arası = kasnak çapı = 320 mm:  halatlar kasnaktan
                #  DİKEY iner, sarılma açısı 180°'dir.  ( Eskiden bu açı Ra'dan
                #  türetiliyordu;  α artık zorunlu girdi. )
                "kanal_isleme": "Sertleştirilmiş",
                "sarilma_acisi": 180,
                "_ofis": {"kanal_gama_v": 50, "q_denge": 0.45},
            }
        )
        self.assertTrue(s["aktif"], s.get("hata"))
        self.assertAlmostEqual(s["ara"]["aski.Nequiv"], 7)
        # Yayında Sf tam sayıya yuvarlanarak 16 verilmiş.
        self.assertAlmostEqual(s["ozet"]["Sf"], 16, delta=0.5)
        self.assertAlmostEqual(s["ozet"]["S_gercek"], 19, delta=0.1)
        # Yayın §4.2: sürtünme katsayısı ve kritik oran; 1.87 yuvarlatılmıştır.
        self.assertAlmostEqual(s["ara"]["tahrik.mu_fren"], 1 / 12)
        self.assertAlmostEqual(s["ara"]["tahrik.fren_alt.sinir"], 1.87, delta=0.02)

    def test_yayin_ray_egilmesi_cekirdegi(self):
        # Yayının T127-1/B kesiti katalogda yok: yalnız sayısal çekirdek testi.
        # Bu kontrol, uygulamanın bu rayı seçebildiği anlamına gelmez.
        fx = 3 * 9.81 * 1000 * 175 / (2 * 2800)
        fy = 3 * 9.81 * 1000 * 200 / 2800
        self.assertAlmostEqual(M._moment(fx, 4000) / 23610, 29, delta=0.5)
        self.assertAlmostEqual(M._moment(fy, 4000) / 30650, 51, delta=0.5)

    def test_yayin_flans_cekirdegi(self):
        p = {"c": 10, "h1_b_f": 89 - 19 - 11, "h1_f": 89 - 11}
        self.assertAlmostEqual(M._flans(7951, p, 140, True), 147, delta=0.5)
        # Yayındaki 96, yazılı girdiler ve formülle tutarsızdır (95.08966).
        # Kaynak baskı hatasını motor hatası saymamak için aritmetik kullanılır.
        self.assertAlmostEqual(M._flans(7951, p, 140, False), 6 * 7951 * 59 / (100 * (140 + 156)), places=8)

    def test_yayin_omega_cekirdegi(self):
        # Yayın §3.1. Program narinliği yukarı tam sayıya yuvarlar.
        lam, omega = M._burkulma_omega(4000, 23.61, 370)
        self.assertEqual(lam, 170)
        self.assertAlmostEqual(omega, 4.85, delta=0.04)

    def test_burkulmada_en_kucuk_atalet_yaricapi(self):
        s = M.hesapla()
        g, h = s["girdi"], s["ara"]
        p = g["kabin_ray_profili"]
        imin = min(T.ray(p, "ix"), T.ray(p, "iy"))
        lam = math.ceil(g["kabin_konsol_arasi"] / imin)
        # Bu test yarıçap seçimini ayırır; yukarı yuvarlama aynen korunur.
        omega = 0.00016887 * lam**2
        expected = h["kabin_ray.sigma_k"] / h["kabin_ray.omega"] * omega
        self.assertAlmostEqual(h["kabin_ray.sigma_k"], expected, places=6)

    def test_narinlik_250_sinirinin_asimi_burkulmayi_dusurmeli(self):
        # ix=20.9; iy=14.0. Gerçek narinlik 3600/14 = 257.143 > 250.
        # m.5.10.3'ün ω tablosu 20 ≤ λ ≤ 250 arasında tanımlıdır: dışında ω
        # yoktur, dolayısıyla σk hesaplanamaz ve BURKULMA kontrolü düşer.
        # Hesabın tamamı durmaz — eğilme, birleşik gerilme, flanş ve sehim
        # bağıntıları ω'ya bağlı değildir ve geçerliliğini korur.
        g = {"kabin_ray_profili": "70 x 65 x 9", "kabin_konsol_arasi": 3600}
        s = M.hesapla(g)
        self.assertTrue(s["aktif"], s.get("hata"))
        self.assertTrue(any("narin" in u for u in s["uyarilar"]), s["uyarilar"])
        b7 = next(x for x in s["bolumler"] if x["kimlik"] == "kabin_raylari")
        self.assertFalse(b7["sonuc"]["uygun"], "Tablo dışı narinlikte bölüm uygun çıkmamalı")
        # ω gerçekten üretilmemiş olmalı; σk None kalmalı.
        lam, omega = M._burkulma_omega(3600, min(T.ray("70 x 65 x 9", "ix"), T.ray("70 x 65 x 9", "iy")), 370)
        self.assertEqual(lam, 258)
        self.assertIsNone(omega)

    def test_kabin_y_kacikligi_guvenlik_yukune_girmeli(self):
        # Girdinin ilan edilen anlamı kabin merkezinin y kaçıklığıdır.
        # Kabin ve merkezlenmiş kapı birlikte +200 mm ötelenmiştir.
        s = M.hesapla({"kabin_kaciklik": 200})
        self.assertTrue(s["aktif"], s.get("hata"))
        g = s["girdi"]
        #  P, m.5.7.2.3.2'nin tanımıyla:  boş kabin + gezici kablo payı +
        #  denge zinciri.  Eklenen kütleler kabin merkezinde kabul edilir,
        #  yani onların da y kolu 200 mm'dir.
        expected = (
            2
            * 9.81
            * (g["beyan_yuku"] * (200 + g["kabin_genisligi"] / 8) + P_std(s) * 200)
            / g["kabin_paten_arasi"]
        )
        self.assertAlmostEqual(s["ara"]["kabin_ray.c21.d2.Fy"], expected, places=6)

    #  ------------------------------------------------------------------
    #  ACİL FRENLEME  —  EN 81-50 Ek D'nin ÇÖZÜMLÜ ÖRNEĞİ  ( 2:1, dengeleme
    #  yok, makine üstte ).  Ek D, m.5.11.2.2'nin genel formülünün bu
    #  düzenek için sadeleşmiş hâlidir ve ± işaretlerini AÇIK yazar:
    #
    #    a) yüklü kabin en alt durakta   ( kabin AŞAĞI yavaşlıyor )
    #         T1 = (P+Q)/2·(gn+a) + MSRcar·(gn+2a) + mPcar·2·a/2 − FRcar/2
    #         T2 = Mcwt/2·(gn−a)                   − mPcwt·1·a/2 + FRcwt/2
    #    b) boş kabin en üst durakta     ( kabin YUKARI yavaşlıyor )
    #         T1 = Mcwt/2·(gn+a) + MSRcwt·(gn+2a)  + mPcwt·1·a/2 − FRcwt/2
    #         T2 = (P+MTrav)/2·(gn−a)              − mPcar·2·a/2 + FRcar/2
    #
    #  KASNAK SAYILARI EK D'NİN KENDİSİNDEDİR:  kabin tarafında "·2·",
    #  ağırlık tarafında "·1·" yazar.  Ofis sabitleri bu iki sayıyı
    #  varsayılan olarak taşır ( kasnak_adet_kabin · kasnak_adet_agirlik ).
    #
    #  SÜRTÜNME KUYUDAKİ KUVVETTİR  ( m.5.11.2.2:  "FRcar is the frictional
    #  force in the well" ).  Ek D sayı vermez;  yüzde ofis sabitidir ve o
    #  taraftaki GÖVDENİN ağırlık kuvvetine uygulanır, formüle "/2" ile girer:
    #      a)  FRcar = %k·(P+Q)·(gn+a)          FRcwt = %k·Mcwt·(gn−a)
    #      b)  FRcar = %k·(P+MTrav)·(gn−a)      FRcwt = %k·Mcwt·(gn+a)
    #  ( Eskiden motor yüzdeyi ZATEN /2'li halat kuvvetinden alıp bir kez daha
    #    /2 yapıyordu ve bu test o yanlışı "standart" diye sabitliyordu. )
    #
    #  NOT 1 gereği b'de etiketler yer değiştirir;  oran max/min alındığı
    #  için bu karşılaştırmayı etkilemez.
    #  ------------------------------------------------------------------
    def _ekD(self, durum, ofis=None):
        s = M.hesapla({"_ofis": ofis} if ofis else None)
        g = s["girdi"]
        o = {"ofis": U.sabitler(g.get("_ofis"))}
        M._motor(g, o)
        t = M._terimler(g, o, durum)
        self.assertEqual(t["r"], 2, "Ek D örneği 2:1 askı içindir")
        for sifir in ("MComp", "iPDT", "mPTD", "mDPcar", "mDPcwt", "MCRcar", "MCRcwt"):
            self.assertEqual(t[sifir], 0.0, f"{sifir} Ek D örneğinde yoktur")
        gn, a = t["gn"], t["a"]
        k_car = o["ofis"]["kuyu_surtunme_kabin"] / 100
        k_cwt = o["ofis"]["kuyu_surtunme_agirlik"] / 100
        #  Ek D'nin kasnak atalet terimleri  ( r = 2 olduğu için "/2" )
        kas_car = t["mPcar"] * t["iPcar"] * a / 2
        kas_cwt = t["mPcwt"] * t["iPcwt"] * a / 2
        if durum == "fren_alt":
            FRcar = k_car * (t["P"] + t["Q"]) * (gn + a)
            FRcwt = k_cwt * t["Mcwt"] * (gn - a)
            T1 = (t["P"] + t["Q"]) / 2 * (gn + a) + t["MSRcar"] * (gn + 2 * a) + kas_car - FRcar / 2
            T2 = t["Mcwt"] / 2 * (gn - a) - kas_cwt + FRcwt / 2
        else:
            FRcar = k_car * (t["P"] + t["MTrav"]) * (gn - a)
            FRcwt = k_cwt * t["Mcwt"] * (gn + a)
            T1 = t["Mcwt"] / 2 * (gn + a) + t["MSRcwt"] * (gn + 2 * a) + kas_cwt - FRcwt / 2
            T2 = (t["P"] + t["MTrav"]) / 2 * (gn - a) + t["MSRcar"] * (gn - 2 * a) - kas_car + FRcar / 2
        hucre = "tahrik.fren_alt.oran" if durum == "fren_alt" else "tahrik.fren_ust.oran"
        return s["ara"][hucre], max(T1, T2) / min(T1, T2)

    def test_fren_alt_ek_D_ile_ayni(self):
        motor, ek_d = self._ekD("fren_alt")
        self.assertAlmostEqual(motor, ek_d, places=6)

    def test_fren_ust_ek_D_ile_ayni(self):
        motor, ek_d = self._ekD("fren_ust")
        self.assertAlmostEqual(motor, ek_d, places=6)

    def test_kuyu_surtunmesi_ofis_sabitiyle_degisir(self):
        """Sürtünme 0 da, farklı bir yüzde de Ek D bağıntısıyla aynı sonucu verir."""
        for ofis in (
            {"kuyu_surtunme_kabin": 0, "kuyu_surtunme_agirlik": 0},
            {"kuyu_surtunme_kabin": 3, "kuyu_surtunme_agirlik": 2.5},
        ):
            for durum in ("fren_alt", "fren_ust"):
                motor, ek_d = self._ekD(durum, ofis)
                self.assertAlmostEqual(motor, ek_d, places=6, msg=f"{ofis} · {durum}")

    def test_surtunme_frenlemede_lehe_calisir(self):
        """Sürtünme kaldırılınca frenleme oranı BÜYÜR — kabul lehe çalışan terimdir."""
        for durum in ("fren_alt", "fren_ust"):
            varsayilan, _ = self._ekD(durum)
            sifir, _ = self._ekD(durum, {"kuyu_surtunme_kabin": 0, "kuyu_surtunme_agirlik": 0})
            self.assertGreater(sifir, varsayilan, durum)

    def test_frenlemede_kabin_tarafi_agirlasir(self):
        """Yüklü kabin aşağı yavaşlarken kabin tarafı halat DAHA ÇOK gerilir."""
        s = M.hesapla()
        g = s["girdi"]
        o = {"ofis": U.sabitler(g.get("_ofis"))}
        M._motor(g, o)
        t = M._terimler(g, o, "fren_alt")
        durgun = M._T1(dict(t, a=0.0), 0.0, +1)
        frenli = M._T1(t, 0.0, +1)
        self.assertGreater(frenli, durgun, "Aşağı yavaşlayan yüklü kabinde T1 artmalıdır")
        durgun2 = M._T2(dict(t, a=0.0), 0.0, +1)
        frenli2 = M._T2(t, 0.0, +1)
        self.assertLess(frenli2, durgun2, "Yukarı yavaşlayan karşı ağırlıkta T2 azalmalıdır")

    #  ------------------------------------------------------------------
    #  TAMPONLAR            TS EN 81-20 m.5.8.1 / m.5.8.2
    #  ------------------------------------------------------------------
    def _tampon(self, tip, v, strok=None):
        g = {"tampon_tipi": tip, "beyan_hizi": v}
        if strok is not None:
            g["kabin_tampon_ezilme"] = strok
            g["agirlik_tampon_ezilme"] = strok
            #  Tampon kendi boyundan fazla ezilemez;  bu modül STROK
            #  şartını denetliyor, tamponun boyunu değil — boy her zaman
            #  denenen stroku taşıyacak kadar büyük tutulur.
            g["kabin_tampon_boyu"] = max(strok, 100)
        s = M.hesapla(g)
        self.assertTrue(s["aktif"], s.get("hata"))
        return next(b for b in s["bolumler"] if b["kimlik"] == "tamponlar")

    def test_biriktirmeli_tampon_1_m_s_ustunde_kullanilamaz(self):
        """m.5.8.1.5:  enerji biriktirmeli tampon yalnız v ≤ 1 m/s."""
        for tip in (T.TAMPON_TIPLERI[0][0], T.TAMPON_TIPLERI[1][0]):
            self.assertTrue(self._tampon(tip, 1.0, 900)["sonuc"]["uygun"], tip)
            self.assertFalse(self._tampon(tip, 1.2, 900)["sonuc"]["uygun"], tip)
        #  m.5.8.1.6:  enerji yutmalıda hız sınırı yoktur.
        yut = T.TAMPON_TIPLERI[2][0]
        self.assertTrue(self._tampon(yut, 2.5, 900)["sonuc"]["uygun"])

    def test_lineer_tampon_stroku(self):
        """m.5.8.2.1.1.1:  strok ≥ 0,135·v² , en az 65 mm."""
        lin = T.TAMPON_TIPLERI[0][0]
        #  v = 1 m/s  →  135 mm.  134 düşer, 135 geçer.
        self.assertFalse(self._tampon(lin, 1.0, 134)["sonuc"]["uygun"])
        self.assertTrue(self._tampon(lin, 1.0, 135)["sonuc"]["uygun"])
        #  Düşük hızda 65 mm ALT SINIRI devreye girer:  0,135·0,63² = 53,6 mm
        #  ama madde 65 mm'nin altına inilemeyeceğini söyler.
        self.assertFalse(self._tampon(lin, 0.63, 64)["sonuc"]["uygun"])
        self.assertTrue(self._tampon(lin, 0.63, 65)["sonuc"]["uygun"])

    def test_enerji_yutmali_tampon_stroku(self):
        """m.5.8.2.2.1:  strok ≥ 0,0674·v².  Alt sınır YOKTUR."""
        yut = T.TAMPON_TIPLERI[2][0]
        #  v = 2,5 m/s  →  0,0674 · 6,25 = 0,42125 m = 421,25 mm
        self.assertFalse(self._tampon(yut, 2.5, 421)["sonuc"]["uygun"])
        self.assertTrue(self._tampon(yut, 2.5, 422)["sonuc"]["uygun"])
        #  65 mm alt sınırı burada uygulanmaz:  0,0674·0,63² = 26,8 mm
        self.assertTrue(self._tampon(yut, 0.63, 27)["sonuc"]["uygun"])

    def test_lineer_olmayan_tamponda_strok_bagintisi_yok(self):
        """m.5.8.2.1.2:  yavaşlama ölçütleri tip deneyine bırakılmıştır."""
        pol = T.TAMPON_TIPLERI[1][0]
        b = self._tampon(pol, 1.0, 1)  # 1 mm bile olsa bağıntı yok
        self.assertTrue(b["sonuc"]["uygun"])
        self.assertIn("tip inceleme", b["sonuc"]["metin"].lower())

    def test_kuyu_tabani_kuvveti_tampon_adedine_bolunur(self):
        """m.5.2.1.8.5:  kuvvet tampon sayısına eşit dağılır."""
        s = M.hesapla({"kabin_tampon_adedi": 2, "agirlik_tampon_adedi": 4})
        h = s["ara"]
        g, gn = s["girdi"], 9.81
        #  m.5.2.1.8.5:  F = 4·gn·( P + Q ) — oradaki P boş kabin DEĞİL,
        #  "empty car and components supported by the car, i.e. part of the
        #  travelling cable, compensating ropes/chains (if any)".
        Fkt = 4 * gn * (P_std(s) + g["beyan_yuku"])
        self.assertAlmostEqual(h["kuyu.Fkt"], Fkt, places=6)
        b9 = next(b for b in s["bolumler"] if b["kimlik"] == "kuyu_tabani")
        tekil = [a["deger"] for a in b9["adimlar"] if "Fkt1" in str(a.get("formul") or "")]
        self.assertEqual(len(tekil), 1)
        self.assertAlmostEqual(tekil[0], Fkt / 2, places=6)

    #  ------------------------------------------------------------------
    #  KASNAK ATALETİ       TS EN 81-50 m.5.11.2.2 a)  ( koşul III )
    #  ------------------------------------------------------------------
    def test_kasnak_atalet_referans_ornegiyle_ayni(self):
        """referans projenin yayımlanmış paftası:  Dp=294 · 7 × 6,5 mm → J = 0,29."""
        mP, J, A = M._kasnak_atalet(
            {"saptirma_kasnak_capi": 294, "halat_adedi": 7, "halat_capi": 6.5}, U.sabitler(None)
        )
        self.assertAlmostEqual(J, 0.29, delta=0.005)
        self.assertAlmostEqual(A * 1000, 92.4, delta=0.5)  # paftada 0,09 m
        self.assertAlmostEqual(mP, J / 0.147**2, delta=0.05)

    def test_kasnak_atalet_terimi_orani_buyutur(self):
        """Terim T1'i büyütüp T2'yi küçültür → T1/T2 oranı ARTAR."""
        s = M.hesapla()
        g = s["girdi"]
        o = {"ofis": U.sabitler(g.get("_ofis"))}
        M._motor(g, o)
        t = M._terimler(g, o, "fren_alt")
        self.assertGreater(t["mPcar"], 0, "2:1 askıda terim sıfır olmamalı")
        self.assertEqual(t["iPcar"], 2)
        self.assertEqual(t["iPcwt"], 1)
        terimli = M._T1(t, 0.0, +1)
        terimsiz = M._T1(dict(t, mPcar=0.0), 0.0, +1)
        self.assertGreater(terimli, terimsiz)
        #  Büyüklüğü:  mP · iP · a / r
        self.assertAlmostEqual(terimli - terimsiz, t["mPcar"] * t["iPcar"] * t["a"] / t["r"], places=6)

    def test_kasnak_atalet_1_1_askida_sifir(self):
        """m.5.11.2.2 koşul III:  terim yalnız askı oranı > 1 içindir."""
        s = M.hesapla({"aski_orani": 1})
        g = s["girdi"]
        o = {"ofis": U.sabitler(g.get("_ofis"))}
        M._motor(g, o)
        t = M._terimler(g, o, "fren_alt")
        self.assertEqual(t["r"], 1)
        self.assertEqual(t["mPcar"], 0.0)
        self.assertEqual(t["iPcar"], 0)

    def test_kasnak_atalet_ofis_sabitine_baglidir(self):
        """Yoğunluk ofis kabulüdür;  değişince terim de değişmeli."""
        _, J1, _ = M._kasnak_atalet(
            {"saptirma_kasnak_capi": 240, "halat_adedi": 7, "halat_capi": 6.5}, U.sabitler(None)
        )
        _, J2, _ = M._kasnak_atalet(
            {"saptirma_kasnak_capi": 240, "halat_adedi": 7, "halat_capi": 6.5},
            U.sabitler({"kasnak_yogunluk": 3700}),
        )
        self.assertAlmostEqual(J2, J1 / 2, places=6)

    def test_negatif_halat_kuvveti_uygun_sayilmamali(self):
        """Halat gevşerse tahrik bağıntısı geçersizdir.

        T1/T2 oranı max(a/b, b/a) olduğu için kuvvetlerden biri negatife
        düşünce oran da NEGATİF çıkar ve "oran ≤ e^(f·α)" karşılaştırması
        sessizce geçer.  Sürtünme bağıntısı GERGİN halat varsayar;  T ≤ 0
        fiziksel olarak halatın gevşemesi demektir ve o noktada hiçbir
        tahrik hükmü verilemez.
        """
        s = M.hesapla({"acil_frenleme_a": 9.81})  # a = 1 gn
        self.assertTrue(s["aktif"], s.get("hata"))
        h = s["ara"]
        self.assertLess(h["tahrik.fren_alt.T2"], 0, "bu girdide T2 negatife düşmeli")
        self.assertLess(h["tahrik.fren_alt.oran"], 0, "oran da negatif çıkmalı")
        b6 = next(x for x in s["bolumler"] if x["kimlik"] == "tahrik_yetenegi")
        self.assertFalse(b6["sonuc"]["uygun"], "negatif halat kuvvetiyle bölüm uygun sayılamaz")
        #  Sebep paftada YAZILI olmalı — sessiz düşme olmaz.
        self.assertTrue(
            any("GEVŞ" in str(a.get("aciklama") or "") for a in b6["adimlar"]),
            "gevşek halat sebebi adımlarda görünmüyor",
        )


class UcDuzeltmeDenetimi(unittest.TestCase):
    """2026-09-10'da bulunan üç hatanın standart tarafından doğrulanması.

    Beklenen değerler altın çıktıdan ya da motordan ALINMAZ;  her
    test standardın kendi cümlesinden ya da fizikten türetilir.
    """

    #  ── 1)  MOTOR GÜCÜ İKİ HAREKET YÖNÜNDEN ────────────────────────
    def _motor_gucu(self, q):
        s = M.hesapla({"_ofis": {"q_denge": q}})
        self.assertTrue(s["aktif"], s.get("hata"))
        return s["ozet"]["N_hesap"]

    def test_motor_gucu_q_ekseninde_simetriktir(self):
        """q ve ( 1−q ) aynayı verir:  dengesizliğin BÜYÜKLÜĞÜ aynıdır.

        Dolu kabin yukarı  → ( 1−q )·Q ,  boş kabin aşağı → q·Q.
        q = 0,40'ta birincisi 0,60·Q, q = 0,60'ta ikincisi 0,60·Q'dur;
        motorun görmesi gereken güç ikisinde de aynı olmalıdır.
        """
        for q in (0.30, 0.35, 0.40, 0.45):
            self.assertAlmostEqual(self._motor_gucu(q), self._motor_gucu(1 - q), places=9, msg=f"q = {q}")

    def test_motor_gucu_en_kucuk_q_yarimda(self):
        """Denge q = 0,50'de tamdır;  iki yana da sapınca güç ARTMALIDIR."""
        yarim = self._motor_gucu(0.50)
        for q in (0.30, 0.40, 0.45, 0.55, 0.60, 0.70):
            self.assertGreater(self._motor_gucu(q), yarim, f"q = {q}")

    def test_bos_kabin_yonu_q_buyukken_belirleyicidir(self):
        """q > 0,50'de dengesizlik q·Q'dur;  Gmax bunu içermelidir."""
        Q = 800.0
        for q in (0.60, 0.70):
            s = M.hesapla({"beyan_yuku": Q, "_ofis": {"q_denge": q}})
            self.assertTrue(s["aktif"], s.get("hata"))
            #  Gmax = Gden + Gs + MSR − MCR + MTrav;  Gden = q·Q olmalı
            Gmax = s["ara"]["motor.Gmax"]
            self.assertGreaterEqual(Gmax, q * Q, f"q = {q}")
            self.assertLess(Gmax, q * Q + 200, f"q = {q}  ( artık terimler )")

    #  ── 2)  KABİN AÇIKLIKLARI EN ÜST KONUMDA  ( Çizelge 2 ) ────────
    def _ust_acikliklar(self, **ek):
        #  130 mm stroku karşılayacak gerçek bir tampon boyu kullanılır.
        s = M.hesapla({"agirlik_tampon_boyu": 200, **ek})
        self.assertTrue(s["aktif"], s.get("hata"))
        h = s["ara"]
        return [
            h["siginma.ust_paten_ray"],
            h["siginma.kabin_ustu_tavan"],
            h["siginma.revizyon_tavan"],
            h["siginma.paten_tavan"],
        ]

    def test_agirlik_tampon_acikligi_ust_bosluktan_dusulur(self):
        """Çizelge 2:  kabinin en üst konumu = ağırlık TAM EZİLMİŞ tampon üzerinde.

        Karşı ağırlığın tampona inişi artarsa kabin o kadar daha yükselir;
        kabin üstü açıklıkları AYNI kadar AZALMALIDIR.
        """
        taban = self._ust_acikliklar()
        artan = self._ust_acikliklar(agirlik_carpma_arasi=150 + 60)
        for a, b in zip(taban, artan):
            self.assertAlmostEqual(b, a - 60, places=6)

    def test_tampon_ezilmesi_ust_bosluktan_dusulur(self):
        taban = self._ust_acikliklar()
        artan = self._ust_acikliklar(agirlik_tampon_ezilme=90 + 40)
        for a, b in zip(taban, artan):
            self.assertAlmostEqual(b, a - 40, places=6)

    def test_hiz_payi_ust_bosluktan_dusulur(self):
        """Çizelge 2 dipnot a:  0,035·v²  ( 1,15·v'de durma yolunun yarısı )."""
        v1, v2 = 1.0, 1.6
        taban = self._ust_acikliklar(beyan_hizi=v1)
        hizli = self._ust_acikliklar(beyan_hizi=v2)
        fark = 0.035 * (v2**2 - v1**2) * 1000
        for a, b in zip(taban, hizli):
            self.assertAlmostEqual(b, a - fark, places=6)

    def test_kuyu_dibi_acikliklari_yukselmeden_etkilenmez(self):
        """Kuyu dibi ölçüleri KABİN tampon üzerindeyken alınır — ağırlık tamponu girmez."""
        s1 = M.hesapla()
        s2 = M.hesapla(
            {"agirlik_carpma_arasi": 260, "agirlik_tampon_ezilme": 140, "agirlik_tampon_boyu": 200}
        )
        #  Regülatör gergisi satırı yalnız gergi kabinin izdüşümündeyse çıkar
        #  ( birleşik program:  açıklıklar çizimden );  varsayılanda değil.
        for hucre in (
            "siginma.kuyu_tabani_kabin",
            "siginma.etek",
            "siginma.ray_kabin_alt",
            "siginma.dip_siginma",
        ):
            self.assertAlmostEqual(s1["ara"][hucre], s2["ara"][hucre], places=9, msg=hucre)

    def test_paten_tavan_siniri_standardin_yazdigi_gibi(self):
        """m.5.2.5.7.2 b):  0,10 m.  Hız payı sınıra değil ÖLÇÜYE girer."""
        for v in (0.63, 1.0, 1.6, 2.5):
            s = M.hesapla({"beyan_hizi": v})
            self.assertTrue(s["aktif"], s.get("hata"))
            self.assertEqual(s["ara"]["siginma.paten_tavan_asgari"], 100, f"v = {v}")

    #  ── 3)  BURKULMA ZAYIF EKSENDE ─────────────────────────────────
    def test_kaide_burkulmasi_en_kucuk_atalet_yaricapindan(self):
        """Çubuk en küçük atalet yarıçapına sahip eksende burkulur."""
        for olcu in T.NPU_OLCULERI:
            ix, iy = T.npu(olcu, "ix"), T.npu(olcu, "iy")
            if ix is None or iy is None:
                continue
            s = M.hesapla({"dikine_kiris": olcu})
            self.assertTrue(s["aktif"], f"{olcu}: {s.get('hata')}")
            self.assertAlmostEqual(s["ara"]["makine.imin"], min(ix, iy) * 10, places=9, msg=f"NPU {olcu}")

    def test_zayif_eksende_narinlik_buyur(self):
        """iy < ix olan profilde λ, güçlü eksenden bulunandan BÜYÜK olmalı."""
        s = M.hesapla({"dikine_kiris": 120})
        L1 = s["girdi"]["sase_yuksekligi"]
        self.assertGreater(s["ara"]["makine.lam_ham"], L1 / (T.npu(120, "ix") * 10))
        self.assertAlmostEqual(s["ara"]["makine.lam_ham"], L1 / (T.npu(120, "iy") * 10), places=9)

    def test_mesnet_beyani_gucli_eksene_dondurur(self):
        """Şase zayıf ekseni bağlıyorsa burkulma o eksende olamaz — ix geçerli."""
        s = M.hesapla({"dikine_kiris": 120, "_ofis": {"kaide_zayif_eksen_mesnetli": 1}})
        self.assertTrue(s["aktif"], s.get("hata"))
        self.assertAlmostEqual(s["ara"]["makine.imin"], T.npu(120, "ix") * 10, places=9)

    def test_zayif_eksen_kucuk_profilde_karari_cevirir(self):
        """NPU 40x20 ve 50x25:  güçlü eksende 'uygun', zayıf eksende değil."""
        for olcu in ("40x20", "50x25"):
            zayif = M.hesapla({"dikine_kiris": olcu})
            gucli = M.hesapla({"dikine_kiris": olcu, "_ofis": {"kaide_zayif_eksen_mesnetli": 1}})
            b_z = next(x for x in zayif["bolumler"] if x.get("kimlik") == "makine_konstruksiyonu")
            b_g = next(x for x in gucli["bolumler"] if x.get("kimlik") == "makine_konstruksiyonu")
            self.assertTrue(b_g["sonuc"]["uygun"], f"NPU {olcu} güçlü eksen")
            self.assertFalse(b_z["sonuc"]["uygun"], f"NPU {olcu} zayıf eksen")


class PveMRLDenetimi(unittest.TestCase):
    """2026-09-10 · ikinci tur:  P'nin tanımı, regülatör kataloğu, MRL.

    Beklenen değerler altın çıktıdan ya da motordan ALINMAZ;  her
    test standardın kendi cümlesinden türetilir.
    """

    #  ── P'NİN TANIMI  ( m.5.2.1.8.5 · m.5.2.1.8.6 · m.5.7.2.3.2 ) ──────
    def test_kuyu_tabani_P_gezici_kablo_ve_zinciri_icerir(self):
        for zincir in ("Yok", "Var"):
            s = M.hesapla({"denge_zinciri": zincir})
            self.assertTrue(s["aktif"], s.get("hata"))
            Q = s["girdi"]["beyan_yuku"]
            self.assertAlmostEqual(
                s["ara"]["kuyu.Fkt"], 4 * 9.81 * (P_std(s) + Q), places=6, msg=f"zincir {zincir}"
            )

    def test_agirlik_tamponu_da_ayni_P_ile(self):
        """m.5.2.1.8.6:  F = 4·gn·( P + q·Q ) — sembol listesi aynı P'yi tanımlar."""
        q = U.VARSAYILAN["q_denge"]
        s = M.hesapla()
        Q = s["girdi"]["beyan_yuku"]
        self.assertAlmostEqual(s["ara"]["kuyu.Fat"], 4 * 9.81 * (P_std(s) + q * Q), places=6)

    def test_denge_zinciri_ray_kuvvetini_buyutur(self):
        """Zincir P'ye girdiğine göre ray ve kuyu tabanı kuvveti ARTMALI."""
        yok = M.hesapla({"denge_zinciri": "Yok"})
        var = M.hesapla({"denge_zinciri": "Var"})
        self.assertGreater(P_std(var), P_std(yok))
        for hucre in ("kabin_ray.Fk", "kuyu.Fkt", "kuyu.FKR"):
            self.assertGreater(var["ara"][hucre], yok["ara"][hucre], msg=hucre)

    def test_motor_bolumu_P_std_KULLANMAZ(self):
        """Bölüm 1'in F1'i kabin tarafındaki GERÇEK yüktür — zincir oraya
        Gmax ile ayrı girer, P'ye ikinci kez eklenmez."""
        s = M.hesapla({"denge_zinciri": "Var"})
        g = s["girdi"]
        b1 = next(x for x in s["bolumler"] if x["kimlik"] == "motor_gucu")
        P = next(a["deger"] for a in b1["adimlar"] if a.get("sembol") == "P")
        self.assertAlmostEqual(P, g["kabin_agirligi"], places=9)
        self.assertGreater(P_std(s), P)  # ray tarafı gerçekten farklı

    #  ── REGÜLATÖR HALATI KATALOG VERİSİ ────────────────────────────────
    def test_regulator_katalog_kopma_yuku_tabloyu_ezer(self):
        tablo = M.hesapla({"reg_halat_capi": 6})
        katalog = M.hesapla({"reg_halat_capi": 6, "reg_halat_kopma_kN": 28})
        self.assertAlmostEqual(tablo["ara"]["regulator.Tmin"], T.halat_kopma(6), places=6)
        self.assertAlmostEqual(katalog["ara"]["regulator.Tmin"], 28_000.0, places=6)
        self.assertGreater(katalog["ara"]["regulator.Tmin"], tablo["ara"]["regulator.Tmin"])

    def test_regulator_katalog_birim_kutlesi_tabloyu_ezer(self):
        tablo = M.hesapla({"reg_halat_capi": 6})
        katalog = M.hesapla({"reg_halat_capi": 6, "reg_halat_birim_kutle": 0.30})
        self.assertGreater(katalog["ara"]["regulator.gh"], tablo["ara"]["regulator.gh"])

    #  ── MAKİNE YÜKÜNÜN YOLU  ( m.5.7.2.3.7 · m.5.2.1.8.4 ) ─────────────
    def test_makine_raya_binince_Maux_turetilir(self):
        """m.5.7.2.3.7:  Maux "per guide rail" — KABİN VE KARŞI AĞIRLIK
        raylarının toplam sayısına eşit bölünür ( makine şasesi dört raya
        oturur;  kullanıcı kararı ).

        Seçim YALNIZ makine dairesiz tesiste uygulanır;  makine dairesi varsa
        makine kendi kaidesindedir ve yük iki kez sayılmamalıdır.
        """
        s = M.hesapla({"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY})
        self.assertTrue(s["aktif"], s.get("hata"))
        g = s["girdi"]
        Gm, Tst = g["makine_agirligi"], s["ozet"]["Tst_hesap"]
        n = g["kabin_ray_sayisi"] + g["agirlik_ray_sayisi"]
        self.assertEqual(n, 4)
        self.assertAlmostEqual(s["ara"]["kabin_ray.MY"], (Gm + Tst) * 9.81 / n, places=6)
        self.assertAlmostEqual(s["ara"]["agirlik_ray.MY"], (Gm + Tst) * 9.81 / n, places=6)

    def test_Maux_ray_sayisina_bolunur(self):
        """Kabin rayları 2'den 4'e çıkınca toplam 4'ten 6 raya bölünür."""
        iki = M.hesapla({"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY, "kabin_ray_sayisi": 2})
        dort = M.hesapla(
            {"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY, "kabin_ray_sayisi": 4}
        )
        self.assertAlmostEqual(dort["ara"]["kabin_ray.MY"] * 6, iki["ara"]["kabin_ray.MY"] * 4, places=6)
        self.assertAlmostEqual(dort["ara"]["agirlik_ray.MY"], dort["ara"]["kabin_ray.MY"], places=9)

    def test_makine_yuku_karsi_agirlik_raylarina_da_biner(self):
        """Karşı ağırlık rayları makinenin payını σv · σc'de ve kuyu tabanında
        ( FAR ) görür;  dört rayın payları toplamı makinenin tamamıdır."""
        bina = M.hesapla({"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU[0]})
        raya = M.hesapla({"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY})
        self.assertAlmostEqual(bina["ara"]["agirlik_ray.MY"], M.SABIT["MY_agirlik"], places=9)
        self.assertGreater(raya["ara"]["agirlik_ray.sv"], bina["ara"]["agirlik_ray.sv"])
        self.assertGreater(raya["ara"]["kuyu.FAR"], bina["ara"]["kuyu.FAR"])
        g = raya["girdi"]
        toplam = (
            raya["ara"]["kabin_ray.MY"] * g["kabin_ray_sayisi"]
            + raya["ara"]["agirlik_ray.MY"] * g["agirlik_ray_sayisi"]
        )
        self.assertAlmostEqual(toplam, (g["makine_agirligi"] + raya["ozet"]["Tst_hesap"]) * 9.81, places=6)
        kb = next(b for b in raya["bolumler"] if b["kimlik"] == "agirlik_raylari")
        my = next(a for a in kb["adimlar"] if a.get("sembol") == "MY")
        self.assertIn("karşı ağırlık", my["kaynak"])

    def test_bir_raya_dusen_yuk_sorulmaz(self):
        """Bir raya düşen makine yükü formda YOKTUR:  "bina yapısına"da hesaba
        girmez, "kılavuz raylara"da ( Gm + Tst ) raylara eşit dağıtılır."""
        self.assertNotIn("raya_binen_yuk", MG.ALAN)
        self.assertEqual(MG.RAYA_BINEN_ALANLARI, ("makine_raya_biniyor",))

    def test_makine_raya_binmezse_ofis_kabulu_kalir(self):
        s = M.hesapla({"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU[0]})
        self.assertAlmostEqual(s["ara"]["kabin_ray.MY"], M.SABIT["MY_kabin"], places=9)

    def test_form_disi_ray_yuku_esit_dagilimi_ezmez(self):
        """Form dışından gelen bir 'bir raya düşen yük' değeri eşit dağılımı
        değiştirmez — hesap yalnız Gm + Tst ile ray sayısını kullanır."""
        esit = M.hesapla({"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY})
        disari = M.hesapla(
            {"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY, "raya_binen_yuk": 1000}
        )
        self.assertAlmostEqual(disari["ara"]["kabin_ray.MY"], esit["ara"]["kabin_ray.MY"], places=9)

    def test_makine_raya_binince_kuyu_tabani_da_buyur(self):
        """m.5.2.1.8.4 kalemi adıyla anar:  'load on traction sheave due to
        rebound when machine on rails'."""
        yok = M.hesapla({"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU[0]})
        var = M.hesapla({"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY})
        self.assertGreater(var["ara"]["kuyu.FKR"], yok["ara"]["kuyu.FKR"])
        self.assertGreater(var["ara"]["kabin_ray.sigma_k"], yok["ara"]["kabin_ray.sigma_k"])

    def test_MRL_de_bolum_2_makine_kirisini_denetler(self):
        """MRL'de tabliye ve kolon yoktur;  makine kuyu üstündeki NPU kirişlere
        oturur.  Bölüm 2 yalnız kiriş eğilmesini denetler ( σe ≤ σem ),
        burkulma satırı basılmaz ve karar verilir ( None değil )."""
        for mrl in (False, True):
            s = M.hesapla({"mk_yok": mrl})
            b = next(x for x in s["bolumler"] if x["kimlik"] == "makine_konstruksiyonu")
            self.assertIn(b["sonuc"]["uygun"], (True, False), msg=f"mk_yok={mrl}")
            self.assertTrue(b["baslik"].startswith("2 "))
            burkulma = any("σb" in str(a.get("formul")) for a in b["adimlar"])
            self.assertEqual(burkulma, not mrl, msg=f"mk_yok={mrl}")
        mrl = M.hesapla({"mk_yok": True})
        self.assertFalse(any(k in mrl["ara"] for k in ("makine.sigma_b", "makine.lam", "makine.A")))
        #  Eğilme iki yerleşimde aynı statik:  σe = FA·X / Wx ,  Wx NPU 140'tan
        a = mrl["ara"]
        self.assertEqual(mrl["girdi"]["yan_yatak"], 140)
        self.assertAlmostEqual(a["makine.Wx"], T.npu(140, "Wx") * 1000)
        self.assertAlmostEqual(a["makine.sigma_e"], a["makine.FA"] * a["makine.X"] / a["makine.Wx"], places=9)
        daireli = M.hesapla({"mk_yok": False})
        self.assertAlmostEqual(a["makine.sigma_e"], daireli["ara"]["makine.sigma_e"], places=9)
        #  Kabin rayı k1'i yine bulur
        self.assertEqual(mrl["ara"]["kabin_ray.c21.d1.Fx"], daireli["ara"]["kabin_ray.c21.d1.Fx"])

    def test_MRL_de_yalniz_makine_dairesi_alanlari_dogrulanmaz(self):
        """Tabliye ve kaide kolonu ( şase yüksekliği · dikine kiriş ) MRL'de yoktur:
        gizlidir ve bozuk değerleri projeyi durdurmaz.  Makine kirişi ( yan yatak )
        MRL'de de sorulur ve denetlenir."""
        bozuk = {"sase_yuksekligi": 0, "dikine_kiris": "x", "tabliye_yuksekligi": "x"}
        self.assertFalse(M.hesapla(dict(bozuk, mk_yok=False))["aktif"])
        s = M.hesapla(dict(bozuk, mk_yok=True))
        self.assertTrue(s["aktif"], s.get("hata"))
        self.assertEqual(
            set(MG.MAKINE_DAIRESI_ALANLARI), {"tabliye_yuksekligi", "sase_yuksekligi", "dikine_kiris"}
        )
        for mrl in (False, True):
            self.assertFalse(M.hesapla({"yan_yatak_boyu": 100, "mk_yok": mrl})["aktif"], msg=f"mk_yok={mrl}")

    def test_tabliye_ray_boyuna_girmez(self):
        #  Tabliye beton yüksekliği oda zemininden ölçülür ( LiftDesigner 1022 · 1275 ·
        #  800 KG:  1.200 );  son kat kuyu tavanına:  ray kuyu tavanının 200 altında
        #  biter, makine daireli de MRL de ( 5 Eki'ye kadar "+ tabliye − 200" )
        g = {"seyir_mesafesi": 20, "son_kat_yuksekligi": 4000, "kuyu_dibi": 1500}
        for t in (500, 1200):
            for mrl in (False, True):
                d = M.hesapla(dict(g, mk_yok=mrl, tabliye_yuksekligi=t))
                self.assertAlmostEqual(d["ozet"]["ray_boyu"], (20000 + 4000 - 200 + 1200) / 1000)
        self.assertEqual(MG.ALAN["tabliye_yuksekligi"][5], 1200)
        self.assertNotIn("tabliye_yuksekligi", MG.GELISMIS_ALANLAR)

    def test_paten_tipi_ray_basina(self):
        """Kabinin paten tipi karşı ağırlığa geçmez;  girilen ℓ kabinindir."""
        kabin_mak = M.hesapla({"paten_tipi": "Makaralı"})
        ikisi_mak = M.hesapla({"paten_tipi": "Makaralı", "agirlik_paten_tipi": "Makaralı"})
        varsayilan = M.hesapla({})
        p = {"c": T.ray(MG.ALAN["agirlik_ray_profili"][5], "c")}
        #  karşı ağırlık kaymalı kaldıkça σF varsayılanla aynı
        self.assertEqual(kabin_mak["ara"]["agirlik_ray.sf"], varsayilan["ara"]["agirlik_ray.sf"])
        #  makaralıda σF = 1,85·Fx/c²
        self.assertAlmostEqual(
            ikisi_mak["ara"]["agirlik_ray.sf"],
            1.85 * ikisi_mak["ara"]["agirlik_ray.Fx"] / p["c"] ** 2,
            places=9,
        )
        l140 = M.hesapla({"paten_balata_boyu": 140})
        self.assertEqual(l140["ara"]["agirlik_ray.sf"], varsayilan["ara"]["agirlik_ray.sf"])
        self.assertNotEqual(l140["ara"]["kabin_ray.c23.sf"], varsayilan["ara"]["kabin_ray.c23.sf"])

    def test_makine_dairesi_varken_secim_yok_sayilir(self):
        """Makine dairesi varsa makine kendi kaidesindedir ( bölüm 2 );  aynı
        yükü bir de raya bindirmek onu İKİ KEZ saymaktır."""
        md = M.hesapla({"mk_yok": False, "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY})
        self.assertAlmostEqual(md["ara"]["kabin_ray.MY"], M.SABIT["MY_kabin"], places=9)
        mrl = M.hesapla({"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY})
        self.assertGreater(mrl["ara"]["kabin_ray.MY"], md["ara"]["kabin_ray.MY"])

    def test_gizli_secim_uyari_uretmez(self):
        """Karar 3:  varsayılan "Kılavuz raylara" ve alan makine daireli formda
        gizli ( kullanıcı seçemez ) — eskiden basılan "seçim YOK SAYILDI"
        uyarısı her makine daireli projede anlamsız çıkardı."""
        from engine.uygulama import mukavemet_girdi as MG

        u = MG.uyarilar(
            MG.tamamla(
                {
                    "mk_yok": False,
                    "mk_uzunluk": 4000,
                    "mk_genislik": 3000,
                    "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY,
                }
            )
        )
        self.assertFalse(any("YOK SAYILDI" in x for x in u), f"→ {u}")

    def test_bina_yapisina_giden_yuk_bildirilir(self):
        """m.5.2.1.8.1 · Ek E:  yapı makinenin yükünü taşıyacak;  hesabı
        inşaat projesindedir ama SAYIYI pafta vermelidir."""
        from engine.uygulama import mukavemet_girdi as MG

        _bina = T.MAKINE_YUK_YOLU[0]
        bina = MG.uyarilar(MG.tamamla({"mk_yok": True, "makine_raya_biniyor": _bina}))
        ray = MG.uyarilar(MG.tamamla({"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY}))
        self.assertTrue(any("BİNA YAPISINA" in u for u in bina), f"→ {bina}")
        self.assertFalse(any("BİNA YAPISINA" in u for u in ray))
        #  Varsayılan raylara ( karar 3 )
        self.assertEqual(MG.varsayilanlar()["makine_raya_biniyor"], T.MAKINE_YUK_YOLU_RAY)
        #  Sayı da verilmeli — inşaat mühendisine gidecek değer
        s = M.hesapla({"mk_yok": True, "makine_raya_biniyor": _bina})
        Gm, Tst = s["girdi"]["makine_agirligi"], s["ozet"]["Tst_hesap"]
        b = next(x for x in s["bolumler"] if x["kimlik"] == "kabin_raylari")
        satir = next(a for a in b["adimlar"] if a.get("aciklama") == "Bina yapısına aktarılan makine yükü")
        self.assertAlmostEqual(satir["deger"], (Gm + Tst) * 9.81, places=6)

    def test_raya_binerken_bina_satiri_yazilmaz(self):
        s = M.hesapla({"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY})
        b = next(x for x in s["bolumler"] if x["kimlik"] == "kabin_raylari")
        self.assertFalse(
            any(a.get("aciklama") == "Bina yapısına aktarılan makine yükü" for a in b["adimlar"])
        )

    def test_eski_onay_bicimi_okunmaya_devam_eder(self):
        """Eski .uygulama dosyaları True / 'EVET' taşır."""
        from engine.uygulama import mukavemet_girdi as MG

        for eski, beklenen in ((True, True), ("EVET", True), (False, False), ("HAYIR", False)):
            g = MG.tamamla({"mk_yok": True, "makine_raya_biniyor": eski})
            self.assertEqual(T.makine_raya_mi(g["makine_raya_biniyor"]), beklenen, msg=f"{eski!r}")
            self.assertIn(g["makine_raya_biniyor"], T.MAKINE_YUK_YOLU)


class KuyuTabaniK3Denetimi(unittest.TestCase):
    """m.5.2.1.8.4 · m.5.7.4.3  —  raya bağlı donanım kuyu tabanına k3 ile iner.

    Madde kalemleri sayarken  "any load due to components fixed or linked to
    the guide(s) AND/OR any additional reaction (N) occurring during emergency
    stopping ( e.g. load on traction sheave due to REBOUND when machine on
    rails )"  der.  Geri tepmenin katsayısı m.5.7.4.3'ün k3'üdür.
    """

    def _bilesenler(self, s, kimlik):
        b = next(x for x in s["bolumler"] if x["kimlik"] == kimlik)
        ilk = {}
        for a in b["adimlar"]:
            if isinstance(a, dict):
                ilk.setdefault(str(a.get("sembol") or a.get("formul") or ""), a)
        return ilk

    def test_FKR_k3_ile_kurulur(self):
        """FKR, MY'yi çarpansız değil k3 ile toplamalı."""
        for ek in (
            {"mk_yok": False},
            {"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU[0]},
            {"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY},
        ):
            with self.subTest(**ek):
                s = M.hesapla(dict(ek))
                a = self._bilesenler(s, "kuyu_tabani")
                k3, MY, Fgt = a["k3"]["deger"], a["MY"]["deger"], a["Fgt"]["deger"]
                LR, Gr = a["LR"]["deger"], T.ray(s["girdi"]["kabin_ray_profili"], "Gr")
                bek = M.SABIT["gn"] * Gr * LR / 1000.0 + k3 * MY + Fgt
                self.assertAlmostEqual(s["ara"]["kuyu.FKR"], bek, places=6)
                #  çarpansız hâl artık YANLIŞ olmalı  ( k3 > 1 olduğu sürece )
                self.assertNotAlmostEqual(s["ara"]["kuyu.FKR"], bek - (k3 - 1) * MY, places=3)

    def test_bolum_7_ile_bolum_9_ayni_k3_ve_MY(self):
        """Aynı donanım rayın gövdesinde ve tabanında aynı sayıyı görmeli."""
        s = M.hesapla({"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY})
        ray = self._bilesenler(s, "kabin_raylari")
        taban = self._bilesenler(s, "kuyu_tabani")
        self.assertAlmostEqual(ray["MY"]["deger"], taban["MY"]["deger"], places=9)
        self.assertAlmostEqual(ray["k3"]["deger"], taban["k3"]["deger"], places=12)

    def test_k3_ofis_sabitini_izler(self):
        """k3 ofis sabitidir;  değişince hem ray hem taban takip etmeli."""
        bir = M.hesapla(
            {"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY, "_ofis": {"k3_yardimci": 1.2}}
        )
        iki = M.hesapla(
            {"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY, "_ofis": {"k3_yardimci": 2.0}}
        )
        MY = bir["ara"]["kabin_ray.MY"]
        self.assertAlmostEqual(iki["ara"]["kuyu.FKR"] - bir["ara"]["kuyu.FKR"], (2.0 - 1.2) * MY, places=6)
        self.assertGreater(iki["ara"]["kabin_ray.sigma_k"], bir["ara"]["kabin_ray.sigma_k"])

    def test_FAR_da_k3_tasir(self):
        """Karşı ağırlık rayının tabanı da aynı maddeye tabidir."""
        s = M.hesapla({})
        a = self._bilesenler(s, "kuyu_tabani")
        k3 = a["k3"]["deger"]
        Gr = T.ray(s["girdi"]["agirlik_ray_profili"], "Gr")
        LR = a["LR"]["deger"]
        taban_ray = M.SABIT["gn"] * Gr * LR / 1000.0
        self.assertAlmostEqual(s["ara"]["kuyu.FAR"], taban_ray + k3 * M.SABIT["MY_agirlik"], places=6)

    def test_pafta_islemi_kendi_sonucunu_verir(self):
        """FKR satırının gösterilen işlemi, basılan sonuca eşit olmalı.

        Eskiden işlem metni ofis sabitini ( 150 N ) yazıyor, sonuç türetilen
        MY ile hesaplanıyordu:  toplamı tutmayan bir pafta satırı.
        """
        s = M.hesapla({"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY})
        a = self._bilesenler(s, "kuyu_tabani")["FKR = gn × Gr × LR / 1000 + k3 × MY + Fgt"]
        sayi = a["islem"].replace(".", "").replace(",", ".").replace("×", "*")
        self.assertAlmostEqual(eval(sayi), a["deger"], delta=1.0)


class PaftaIslemDenetimi(unittest.TestCase):
    """Paftadaki 'işlem' satırı kendi sonucunu vermeli.

    Bu oturumda AYNI KUSUR ÜÇ KEZ çıktı:  FKR'nin işlemi ofis sabitini
    yazıyordu, Sapd'ınki üst sınırı uygulanmış değeri, ray Fy'lerininki
    x ekseninin bağıntısını ve n·h paydasını.  Hepsinde SAYI doğruydu,
    pafta yanlış anlatıyordu — denetçi için görünmez bir hata.

    Aşağısı sayıya dökülebilen her işlem satırını ayrıştırıp değerle
    karşılaştırır.  Ayrıştırılamayanlar ( 'l = 1.700 mm , Iy = …' gibi
    açıklama taşıyanlar ) atlanır;  ölçüt, AYRIŞTIRILABİLENLERİN hepsinin
    tutmasıdır.
    """

    #  Türkçe sayı biçimi:  binlik ayıracı nokta, ondalık virgül.
    _SAYI = re.compile(r"^[-+0-9.,()×xX*/ ]+$")

    @classmethod
    def _cevir(cls, islem):
        t = islem.strip().lstrip("=").strip()
        if not t or not cls._SAYI.match(t):
            return None
        t = t.replace(".", "").replace(",", ".").replace("×", "*").replace("x", "*")
        try:
            return eval(t, {"__builtins__": {}}, {})
        except Exception:  # noqa: BLE001 — sayı olmayan işlem satırı:  karşılaştırılmaz
            return None

    def _satirlar(self, s):
        for b in s["bolumler"]:
            for a in b["adimlar"]:
                if (
                    isinstance(a, dict)
                    and a.get("tip") == "hesap"
                    and isinstance(a.get("deger"), (int, float))
                    and isinstance(a.get("islem"), str)
                ):
                    yield b["kimlik"], a

    def test_islem_kendi_sonucunu_verir(self):
        denenen = 0
        for ek in (
            {},
            {"kabin_kaciklik": 200},
            {"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY},
            {"agirlik_guvenlik_tertibati": "Kaymalı"},
        ):
            s = M.hesapla(dict(ek))
            self.assertTrue(s["aktif"], s.get("hata"))
            for kimlik, a in self._satirlar(s):
                hesaplanan = self._cevir(a["islem"])
                if hesaplanan is None:
                    continue
                denenen += 1
                self.assertAlmostEqual(
                    hesaplanan,
                    a["deger"],
                    delta=max(1.0, abs(a["deger"]) * 2e-3),
                    msg=f"{kimlik} · {a.get('formul')} · işlem={a['islem']!r}",
                )
        #  Tarama gerçekten iş görmüş olmalı — kalkan boş kalmasın.
        self.assertGreater(denenen, 40, f"yalnız {denenen} satır sınanabildi")

    def test_tahrik_oran_satiri_kendi_bolmesini_yazar(self):
        """T1/T2 satırı, üstündeki iki sayıdan üretilebilmeli.

        T1 ve T2 TARAFA göre etiketlenir ( T1 = kabin tarafı ).  Oran ise
        büyük/küçüktür ve "boş kabin en üstte frenleme"de büyük olan karşı
        ağırlık tarafıdır:  pafta T1 = 3.238 · T2 = 6.049 yazarken oran
        1,8678 çıkıyordu ve okuyan 0,54 buluyordu.
        """
        s = M.hesapla({})
        b = next(x for x in s["bolumler"] if x["kimlik"] == "tahrik_yetenegi")
        oranlar = [
            a
            for a in b["adimlar"]
            if isinstance(a, dict) and str(a.get("formul") or "").startswith("T1 / T2")
        ]
        self.assertEqual(len(oranlar), 4, "dört yük durumu bekleniyor")
        for a in oranlar:
            pay, _, payda = str(a["islem"]).partition("/")
            p = float(pay.strip().replace(".", "").replace(",", "."))
            q = float(payda.strip().replace(".", "").replace(",", "."))
            self.assertAlmostEqual(p / q, a["deger"], places=3, msg=f"{a['formul']} · {a['islem']}")
            #  Bloke DIŞINDA oran her zaman ≥ 1 olmalı ( büyük / küçük )
            if "büyük" in a["formul"]:
                self.assertGreaterEqual(a["deger"], 1.0)

    def test_ray_Fy_paydasi_paftada_dogru_yazar(self):
        """C.2.1.1 b) · C.2.2.1 b) · C.2.3.1 b):  Fy'nin paydası ( n/2 )·h."""
        s = M.hesapla({"kabin_kaciklik": 200})
        b = next(x for x in s["bolumler"] if x["kimlik"] == "kabin_raylari")
        fy = [
            a
            for a in b["adimlar"]
            if isinstance(a, dict)
            and (str(a.get("formul") or "") == "Fy" or str(a.get("formul") or "").startswith("Fy ="))
        ]
        self.assertGreaterEqual(len(fy), 5, "Fy satırları bulunamadı")
        for a in fy:
            #  Bölünmez boşluk ( U+00A0 ) okuyan için boşluktur.
            metin = (str(a.get("formul") or "") + " " + str(a.get("islem") or "")).replace("\u00a0", " ")
            self.assertIn("n / 2", metin, msg=f"Fy satırı ( n/2 )·h demiyor: {metin!r}")
            #  x ekseninin bağıntısı Fy satırına basılmamalı
            self.assertNotIn("Q·xQ", metin)
            self.assertNotIn("xp−xs", metin)


class CiftSarimBlokeDenetimi(unittest.TestCase):
    """EN 81-50 m.5.11.2.1'in İKİ eşitsizliği ters yönlüdür.

        yükleme · acil frenleme :  T1 / T2  ≤  e^(f·α)
        bloke                    :  T1 / T2  ≥  e^(f·α)

    Çift sarımda halat kasnağın üzerinden iki kez geçer ve toplam sarılma
    açısı yarım turu AŞAR.  180° ve altı bir açı tek sarıma aittir ( büyük
    ihtimalle tek geçişin açısı girilmiştir ).  Bu açı GİRDİDE REDDEDİLİR.

    Aşağıdaki sayılar motorun kararından DEĞİL, standardın bağıntısından
    türetilir:  e^(f·α) doğrudan hesaplanır ve reddin NİÇİN gerekli olduğu
    gösterilir — tek sarım açısı blokede hükmü gerçekten döndürüyor.
    """

    CIFT = "Yarım Daire Kanal (Çift Sarım)"

    def _bloke(self, ek=None):
        """( T1/T2 , e^(f·α) , α derece ) — motorun yazdığı ham sayılar."""
        s = M.hesapla(dict(ek or {}))
        self.assertTrue(s["aktif"], s.get("hata"))
        h = s["ara"]
        return h["tahrik.bloke.oran"], h["tahrik.bloke.sinir"], h["tahrik.alfa_derece"], s

    def test_blokede_buyuk_aci_kontrolu_ZORLASTIRIR(self):
        """m.5.11.2.1:  bloke  T1/T2 ≥ e^(f·α).  α ↑  →  sağ taraf ↑."""
        _o1, s_kucuk, a_kucuk, _ = self._bloke({"kanal_sekli": self.CIFT, "sarilma_acisi": 200})
        _o2, s_buyuk, a_buyuk, _ = self._bloke({"kanal_sekli": self.CIFT, "sarilma_acisi": 340})
        self.assertLess(a_kucuk, a_buyuk)
        #  Aynı kanalda f aynıdır;  sınır yalnız α ile büyür — üstel bağıntı.
        self.assertLess(s_kucuk, s_buyuk)
        self.assertAlmostEqual(math.log(s_buyuk) / math.log(s_kucuk), a_buyuk / a_kucuk, places=9)

    def test_cift_sarimda_tek_sarim_acisi_karari_DONDUREBILIYOR(self):
        """Ret kuramsal değil:  çift sarımda 180° kullanılsa hüküm dönüyor.

        Çift sarımda gerçek açı 180°'yi aşar.  Aşağısı, 180°'yi aşmayan
        açıyı reddetmenin GEREKLİ olduğunu gösterir:  aynı tesiste 180° ile
        bloke hükmü "uygun" çıkarken gerçek açıyla düşüyor.
        """
        CIFT = self.CIFT
        donen = 0
        #  Hafif kabin, kalın halat, 2:1:  boş kabin blokede T1/T2 = 4,23.
        #  180°'de sınır 2,19 ( geçer ), 350°'de 4,60 ( kalır ).
        for ek in (
            {"beyan_yuku": 400, "kabin_agirligi": 600, "halat_adedi": 6, "halat_capi": 13.0, "aski_orani": 2},
            {"beyan_yuku": 400, "kabin_agirligi": 600, "halat_adedi": 6, "halat_capi": 16.0, "aski_orani": 2},
        ):
            tek = M.hesapla(dict(ek, kanal_sekli="Yarım Daire Kanal", sarilma_acisi=180))
            cift = M.hesapla(dict(ek, kanal_sekli=CIFT, sarilma_acisi=350))
            if not (tek["aktif"] and cift["aktif"]):
                continue
            ot, st = tek["ara"]["tahrik.bloke.oran"], tek["ara"]["tahrik.bloke.sinir"]
            oc, sc = cift["ara"]["tahrik.bloke.oran"], cift["ara"]["tahrik.bloke.sinir"]
            if None in (ot, st, oc, sc):
                continue
            #  m.5.11.2.1:  hüküm  e^(f·α) ≤ T1/T2
            if (st <= ot) and not (sc <= oc):
                donen += 1
        self.assertGreater(
            donen,
            0,
            "180° ile geçip gerçek çift sarım açısıyla kalan senaryo "
            "bulunamadı — reddin gerekliliği gösterilemiyor",
        )

    def test_cift_sarimda_180_ve_alti_GIRDIDE_reddedilir(self):
        for aci in (90, 180):
            s = M.hesapla({"kanal_sekli": self.CIFT, "sarilma_acisi": aci})
            self.assertFalse(s["aktif"], f"çift sarım · {aci}° kabul edildi")
            self.assertTrue(any("çift sarımlı kanalda 180°'yi aşmalıdır" in h for h in s["hata"]), s["hata"])
        self.assertTrue(M.hesapla({"kanal_sekli": self.CIFT, "sarilma_acisi": 181})["aktif"])

    def test_motor_dogrudan_cagrilsa_imkansiz_aciya_UYGUN_basmaz(self):
        """İKİNCİ KALKAN:  doğrulama atlatılsa bile hiçbir yük durumu geçmez."""
        asil = MG.dogrula
        MG.dogrula = lambda g: []
        try:
            for ek in ({"kanal_sekli": self.CIFT, "sarilma_acisi": 180}, {"sarilma_acisi": 300}):
                s = M.hesapla(dict(ek))
                b = next(x for x in s["bolumler"] if x["kimlik"] == "tahrik_yetenegi")
                durum = [
                    a["deger"]
                    for a in b["adimlar"]
                    if isinstance(a, dict) and a.get("deger") in ("UYGUN", "UYGUN DEĞİL", "HESAP EKSİK")
                ]
                self.assertEqual(durum, ["UYGUN DEĞİL"] * 5, ek)
                self.assertFalse(b["sonuc"]["uygun"])
        finally:
            MG.dogrula = asil

    def test_tek_sarim_davranisi_degismedi(self):
        s = M.hesapla({"kanal_sekli": "Yarım Daire Kanal", "sarilma_acisi": 180})
        b = next(x for x in s["bolumler"] if x["kimlik"] == "tahrik_yetenegi")
        self.assertIsNone(b.get("eksik_hesap"))
        oran, sinir = s["ara"]["tahrik.bloke.oran"], s["ara"]["tahrik.bloke.sinir"]
        satir = [
            a
            for a in b["adimlar"]
            if isinstance(a, dict) and a.get("deger") in ("UYGUN", "UYGUN DEĞİL", "HESAP EKSİK")
        ]
        #  Hüküm m.5.11.2.1'in kendisinden yeniden türetilir.
        self.assertEqual(satir[-1]["deger"], "UYGUN" if sinir <= oran else "UYGUN DEĞİL")


class KanalIslemeDenetimi(unittest.TestCase):
    """TS EN 81-50 m.5.11.2.3.1.2:  sertleştirilmemiş V kanalın alt kesilmesi
    olmalıdır ( "an undercut is necessary" ).  Düz V + sertleştirilmemiş
    eskiden yalnız not alıyor, sayısal kontroller geçerse "UYGUNDUR" oluyordu.
    """

    def test_duz_V_sertlestirilmemis_GIRDIDE_reddedilir(self):
        s = M.hesapla({"kanal_sekli": "V Kanal", "kanal_isleme": "Sertleştirilmemiş", "sarilma_acisi": 180})
        self.assertFalse(s["aktif"])
        self.assertTrue(any("m.5.11.2.3.1.2" in h for h in s["hata"]), s["hata"])

    def test_standarda_uyan_birlesimler_kabul_edilir(self):
        for kanal, isl in (
            ("V Kanal", "Sertleştirilmiş"),
            ("Altı Kesik V Kanal", "Sertleştirilmemiş"),
            ("Altı Kesik V Kanal", "Sertleştirilmiş"),
            ("Yarım Daire Kanal", "Sertleştirilmemiş"),
            ("Altı Kesik Yarım Daire Kanal", "Sertleştirilmemiş"),
        ):
            s = M.hesapla({"kanal_sekli": kanal, "kanal_isleme": isl, "sarilma_acisi": 180})
            self.assertTrue(s["aktif"], (kanal, isl, s.get("hata")))

    def test_secim_sessizce_degistirilmez(self):
        """Ret, girdiyi 'sertleştirilmiş'e çevirerek geçilmemeli."""
        s = M.hesapla({"kanal_sekli": "V Kanal", "kanal_isleme": "Sertleştirilmemiş", "sarilma_acisi": 180})
        self.assertEqual(s["girdi"]["kanal_isleme"], "Sertleştirilmemiş")

    def test_motor_dogrudan_cagrilsa_standart_disi_kanala_UYGUN_basmaz(self):
        asil = MG.dogrula
        MG.dogrula = lambda g: []
        try:
            s = M.hesapla(
                {
                    "kanal_sekli": "V Kanal",
                    "kanal_isleme": "Sertleştirilmemiş",
                    "sarilma_acisi": 180,
                    "_ofis": {"q_denge": 0.40},
                    "beyan_yuku": 320,
                    "kabin_agirligi": 800,
                    "acil_frenleme_a": 0.5,
                    "halat_adedi": 5,
                }
            )
            b = next(x for x in s["bolumler"] if x["kimlik"] == "tahrik_yetenegi")
            durum = [
                a["deger"]
                for a in b["adimlar"]
                if isinstance(a, dict) and a.get("deger") in ("UYGUN", "UYGUN DEĞİL")
            ]
            #  α satırı aralıktadır ( UYGUN );  dört yük durumu geçemez.
            self.assertEqual(durum[1:], ["UYGUN DEĞİL"] * 4, durum)
            self.assertIn("m.5.11.2.3.1.2", b["sonuc"]["metin"])
        finally:
            MG.dogrula = asil


class SarilmaAcisiDenetimi(unittest.TestCase):
    """α bir KABULDÜR ve yönü m.5.11.2.1'in iki eşitsizliğinde terstir.

    Kitabın geometrik modeli  α = 180° − arctan( ( Ra − 2·R1 ) / B )  halatın
    tahrik kasnağından karşı ağırlığa EĞİK indiğini varsayar.  Arada saptırma
    kasnağı varsa halat kasnaktan DİKEY iner ve gerçek α 180°'ye yakındır —
    iki dış referans programı da 180° kullanır.

    Aşağısı motorun kararına bakmaz;  bağıntıyı doğrudan kurup YÖNÜ denetler.
    """

    @staticmethod
    def _ara(ek=None):
        s = M.hesapla(dict(ek or {}))
        assert s["aktif"], s.get("hata")
        return s["ara"]

    def test_aci_buyuyunce_sinir_buyur(self):
        """e^(f·α) α ile artar — iki eşitsizlikte ZIT etki yapar."""
        kucuk = self._ara({"sarilma_acisi": 140})
        buyuk = self._ara({"sarilma_acisi": 180})
        self.assertLess(kucuk["tahrik.alfa_derece"], buyuk["tahrik.alfa_derece"])
        #  f aynı kaldığına göre sınır yalnız α ile büyümeli
        self.assertAlmostEqual(kucuk["tahrik.f_bloke"], buyuk["tahrik.f_bloke"], places=9)
        for hucre in (
            "tahrik.yukleme.sinir",
            "tahrik.fren_alt.sinir",
            "tahrik.fren_ust.sinir",
            "tahrik.bloke.sinir",
        ):
            self.assertLess(kucuk[hucre], buyuk[hucre], hucre)

    def test_kucuk_aci_yuklemede_EMNIYETLI_blokede_EMNIYETSIZ(self):
        """m.5.11.2.1:  yükleme  T1/T2 ≤ e^(fα) ·  bloke  T1/T2 ≥ e^(fα)."""
        kucuk = self._ara({"sarilma_acisi": 140})
        buyuk = self._ara({"sarilma_acisi": 180})
        #  Yüklemede sınır DARALIR  →  geçmek zorlaşır  ( emniyetli taraf )
        self.assertLessEqual(kucuk["tahrik.yukleme.sinir"], buyuk["tahrik.yukleme.sinir"])
        #  Blokede de sınır küçülür, ama orada ölçüt  sınır ≤ oran  olduğu
        #  için küçük sınır geçmeyi KOLAYLAŞTIRIR  ( emniyetsiz taraf ).
        self.assertLessEqual(kucuk["tahrik.bloke.sinir"], buyuk["tahrik.bloke.sinir"])
        #  Aynı oranla iki hüküm:  küçük açı blokede daha kolay geçiyor.
        oran = kucuk["tahrik.bloke.oran"]
        self.assertTrue(kucuk["tahrik.bloke.sinir"] <= oran or buyuk["tahrik.bloke.sinir"] > oran)

    def test_beyan_edilen_aci_modeli_EZER(self):
        self.assertAlmostEqual(self._ara({"sarilma_acisi": 155})["tahrik.alfa_derece"], 155.0)
        #  radyan değeri de takip etmeli — bütün e^(f·α) satırları ona bakar
        self.assertAlmostEqual(
            self._ara({"sarilma_acisi": 155})["tahrik.alfa"], math.radians(155.0), places=9
        )

    def test_tek_sarimda_180_ustu_reddedilir(self):
        """Tek sarımda halat kasnağı en çok yarım tur sarar — girdide ret."""
        for aci in (181, 300):
            s = M.hesapla({"sarilma_acisi": aci})
            self.assertFalse(s["aktif"], f"tek sarım · {aci}° kabul edildi")
            self.assertTrue(any("tek sarımlı kanalda 180°'yi aşamaz" in h for h in s["hata"]), s["hata"])
        self.assertTrue(M.hesapla({"sarilma_acisi": 180})["aktif"])

    def test_cift_sarimda_360_ye_kadar_kabul(self):
        s = M.hesapla({"kanal_sekli": "Yarım Daire Kanal (Çift Sarım)", "sarilma_acisi": 330})
        b = next(x for x in s["bolumler"] if x["kimlik"] == "tahrik_yetenegi")
        k = [
            a
            for a in b["adimlar"]
            if isinstance(a, dict) and a.get("deger") in ("UYGUN", "UYGUN DEĞİL", "HESAP EKSİK")
        ]
        self.assertEqual(k[0]["deger"], "UYGUN")
        #  Açı bilindiği için bloke artık karara bağlanabilir
        self.assertIsNone(b.get("eksik_hesap"))

    def test_referans_acisiyla_sinir_yayindaki_gibi(self):
        """α = 180° · V kanal sertleştirilmiş · γ = 38°  →  f = 0,2/sin19°."""
        h = self._ara(
            {
                "sarilma_acisi": 180,
                "kanal_sekli": "V Kanal",
                "kanal_isleme": "Sertleştirilmiş",
                "_ofis": {"kanal_gama_v": 38},
            }
        )
        f_bloke = 0.2 / math.sin(math.radians(38) / 2)
        self.assertAlmostEqual(h["tahrik.f_bloke"], f_bloke, places=6)
        #  referans proje aynı girdilerde 6,89 basıyor
        self.assertAlmostEqual(h["tahrik.bloke.sinir"], math.exp(f_bloke * math.pi), places=6)
        self.assertAlmostEqual(h["tahrik.bloke.sinir"], 6.89, delta=0.01)


class GenelHukumDenetimi(unittest.TestCase):
    """Hüküm sırası:  "uygun değil"  >  "hesap eksik"  >  "uygundur".

    Kesin olumsuzluk, eksiklikten daha güçlü bilgidir.  Sıra ters kurulursa
    bölümleri çakılan bir proje ekranda yalnız "HESAP EKSİK" der.
    """

    @staticmethod
    def _b(uygun, eksik=False):
        b = {"sonuc": {"uygun": uygun}}
        if eksik:
            b["eksik_hesap"] = "x"
        return b

    def test_kalan_bolum_eksigi_orter(self):
        self.assertEqual(M.genel_hukum([self._b(True), self._b(False)], False, ["e"])[0], "UYGUN DEĞİLDİR.")

    def test_yalniz_eksik_varsa_hesap_eksik(self):
        #  Eksik bölümün KENDİ sonucu da "uygun değil"dir;  "kaldı" sayılmamalı.
        self.assertEqual(
            M.genel_hukum([self._b(True), self._b(False, eksik=True)], False, ["e"])[0], "HESAP EKSİK"
        )

    def test_temiz_proje_uygundur(self):
        self.assertEqual(M.genel_hukum([self._b(True)], True, [])[0], "UYGUNDUR.")

    def test_engelleyici_uyari_uygun_birakmaz(self):
        self.assertEqual(M.genel_hukum([self._b(True)], False, [])[0], "UYGUN DEĞİLDİR.")

    def test_kisa_hukum_uzuna_uyar(self):
        for bol, tu, eks in (
            ([self._b(False)], False, []),
            ([self._b(False, eksik=True)], False, ["e"]),
            ([self._b(True)], True, []),
        ):
            uzun, kisa = M.genel_hukum(bol, tu, eks)
            self.assertTrue(uzun.startswith(kisa.split()[0]), (uzun, kisa))

    def test_gercek_projede_kalan_bolum_soyleniyor(self):
        #  Eksik:  α ( çift sarım — çizim tek sarım çizer, α çizimden bulunamaz;
        #  varsayılan asansörün α'sı çizimden gelir ).
        s = M.hesapla({"kanal_sekli": "Yarım Daire Kanal (Çift Sarım)"})
        o = s["ozet"]
        kalan = [
            b
            for b in s["bolumler"]
            if (b.get("sonuc") or {}).get("uygun") is False and not b.get("eksik_hesap")
        ]
        self.assertTrue(kalan, "senaryoda kalan bölüm yok")
        self.assertTrue(o["eksik_hesap"], "senaryoda eksik hesap yok")
        self.assertEqual(o["genel_sonuc"], "UYGUN DEĞİLDİR.")


class AgirlikMerkeziVeRm450Denetimi(unittest.TestCase):
    """Boş kabinin ağırlık merkezi ( xp · yp ) girdisi ve Rm = 450 ray çeliği."""

    def test_bos_birakilinca_turetme_aynen(self):
        a = M.hesapla({})["ara"]
        b = M.hesapla({"kabin_agirlik_merkezi_x": None, "kabin_agirlik_merkezi_y": ""})["ara"]
        for k in ("kabin_ray.xp", "kabin_ray.c21.d1.Fx", "kabin_ray.c22.d2.Fy", "kabin_ray.c23.Fx"):
            self.assertEqual(a[k], b[k], k)

    def test_girilen_xp_yp_P_nin_tamamina_uygulanir(self):
        """Ek C.2.1.1:  Fx = k1·gn·( Q·xQ + P·xp ) / ( n·h ) ,
        Fy = k1·gn·( Q·yQ + P·yp ) / ( ( n/2 )·h ) — P standardın P'si."""
        s = M.hesapla(
            {"kabin_agirlik_merkezi_x": 120, "kabin_agirlik_merkezi_y": -80, "guvenlik_tertibati": "Kaymalı"}
        )
        self.assertTrue(s["aktif"], s.get("hata"))
        a, g = s["ara"], s["girdi"]
        self.assertEqual(a["kabin_ray.xp"], 120)
        kb = next(b for b in s["bolumler"] if b["kimlik"] == "kabin_raylari")
        #  Standardın P'si ( boş kabin + gezici kablo + zincir ) bölüm 9'da basılır.
        kt = next(b for b in s["bolumler"] if b["kimlik"] == "kuyu_tabani")
        P = next(x["deger"] for x in kt["adimlar"] if "P'nin standarttaki tanımı" in str(x.get("kaynak")))
        n, h, Q = g["kabin_ray_sayisi"], g["kabin_paten_arasi"], g["beyan_yuku"]
        xQ = a["kabin_ray.xQ1"]
        Fx = 2 * 9.81 * (Q * xQ + P * 120) / (n * h)
        self.assertAlmostEqual(abs(a["kabin_ray.c21.d1.Fx"]), abs(Fx), places=6)
        yc = g["kabin_kaciklik"]
        Fy_d1 = 2 * 9.81 * (Q * yc + P * -80) / ((n / 2) * h)
        self.assertAlmostEqual(abs(a["kabin_ray.c21.d1.Fy"]), abs(Fy_d1), places=6)
        satir = {x.get("sembol"): x for x in kb["adimlar"]}
        self.assertIn("GİRİŞ", satir["xp"]["kaynak"])
        self.assertIn("GİRİŞ", satir["yp"]["kaynak"])
        self.assertFalse(any("Kabin kapısı ağırlığı" in str(x.get("aciklama")) for x in kb["adimlar"]))

    def test_isaretli_ve_opsiyonel(self):
        self.assertIn("kabin_agirlik_merkezi_x", MG.ISARETLI_ALANLAR)
        self.assertIn("kabin_agirlik_merkezi_y", MG.OPSIYONEL_ALANLAR)
        self.assertIn("kabin_agirlik_merkezi_x", MG.GELISMIS_ALANLAR)
        self.assertTrue(M.hesapla({"kabin_agirlik_merkezi_x": -300})["aktif"])

    def test_rm_450_iso_7465_araliginda_ara_deger(self):
        """ISO 7465 m.5:  370 ≤ Rm ≤ 520.  EN 81-50 m.5.10.3:
        ω = ω370 + ( ω520 − ω370 ) · ( Rm − 370 ) / 150 ;  σperm = Rm / St."""
        self.assertIn(450, T.RAY_CELIKLERI)
        self.assertAlmostEqual(T.sigma_perm_normal(450), 200.0)
        self.assertAlmostEqual(T.sigma_perm_guvenlik(450), 250.0)
        for lam in (40, 90, 128.45, 200):
            w370, w520 = T.omega_en8150(lam, 370), T.omega_en8150(lam, 520)
            self.assertAlmostEqual(T.omega_en8150(lam, 450), w370 + (w520 - w370) * 80 / 150, places=12)
        # referans proje örneği:  λ = 128,45 · W370 2,79 · W520 4,18 · wRm 3,53
        self.assertAlmostEqual(T.omega_en8150(128.45, 450), 3.53, delta=0.005)
        self.assertTrue(M.hesapla({"ray_celigi_rm": 450})["aktif"])


class NequivEkEDenetimi(unittest.TestCase):
    """TS EN 81-50 Ek E'nin iki çözümlü örneği — Nps BOŞ bırakılarak.

    Nps boşsa askı oranından gelir ( 1:1 → 1, 2:1 → 2 ).  Beklenen sayılar
    standardın metnindeki örneklerdir;  altın çıktıdan alınmaz.
    """

    def _nequiv(self, **g):
        s = M.hesapla(dict({"halat_capi": 10, "sarilma_acisi": 180}, **g))
        self.assertTrue(s["aktif"], s.get("hata"))
        return s["ara"]

    def test_sekil_e1_2e1_v_kanal(self):
        # Şekil E.1 — 2:1 · V kanal γ = 40° · Dt 600 · Dp 500
        #   Nequiv(t) = 10 · Kp = (600/500)⁴ = 2,07 · Nequiv(p) = 2,07·(2+0) = 4,14
        #   Nequiv = 14,14   ( "No reversed bend because of moving pulley" )
        a = self._nequiv(
            aski_orani=2,
            tahrik_kasnak_capi=600,
            saptirma_kasnak_capi=500,
            kanal_sekli="V Kanal",
            kanal_isleme="Sertleştirilmiş",
            _ofis={"kanal_gama_v": 40},
        )
        self.assertAlmostEqual(a["aski.Nequiv_t"], 10)
        self.assertAlmostEqual(a["aski.Nequiv_p"], 4.14, delta=0.01)
        self.assertAlmostEqual(a["aski.Nequiv"], 14.14, delta=0.01)

    def test_sekil_e2_1e1_alti_kesik_u(self):
        # Şekil E.2 — 1:1 · alt kesikli U kanal β = 90° · Dt 600 · Dp 400
        #   Nequiv(t) = 5 · Kp = (600/400)⁴ = 5,06 · Nequiv(p) = 5,06·(1+0) = 5,06
        #   Nequiv = 10,06
        a = self._nequiv(
            aski_orani=1,
            tahrik_kasnak_capi=600,
            saptirma_kasnak_capi=400,
            kanal_sekli="Altı Kesik Yarım Daire Kanal",
            _ofis={"kanal_beta": 90},
        )
        self.assertAlmostEqual(a["aski.Nequiv_t"], 5)
        self.assertAlmostEqual(a["aski.Nequiv_p"], 5.06, delta=0.01)
        self.assertAlmostEqual(a["aski.Nequiv"], 10.06, delta=0.01)


class ProjeVerimiDenetimi(unittest.TestCase):
    """Projeye girilen toplam sistem verimi η ( imalatçı ) — boşsa ofis değeri.

    Beklenen güç MMO 208/7 - 2.4 bağıntısından elle kurulur:
    N = Gmax · v / ( η · 102 ).
    """

    OFIS = {"verim_dislisiz": 0.80}

    def _motor(self, s):
        return next(b for b in s["bolumler"] if b["kimlik"] == "motor_gucu")

    def _eta_satiri(self, s):
        return next(x for x in self._motor(s)["adimlar"] if x.get("sembol") == "η")

    def test_bos_birakilinca_ofis_degeri_aynen(self):
        a = M.hesapla({"_ofis": self.OFIS})
        for bos in (None, ""):
            b = M.hesapla({"_ofis": self.OFIS, "makine_verimi": bos})
            self.assertEqual(a["ara"], b["ara"])
            self.assertEqual(b["ara"]["motor.eta"], 0.80)
            self.assertIn("KABUL", self._eta_satiri(b)["kaynak"])

    def test_girilen_verim_gucu_belirler(self):
        s = M.hesapla({"_ofis": self.OFIS, "makine_verimi": 0.83})
        self.assertTrue(s["aktif"], s.get("hata"))
        a, g = s["ara"], s["girdi"]
        self.assertEqual(a["motor.eta"], 0.83)
        N = a["motor.Gmax"] * g["beyan_hizi"] / (0.83 * 102)
        self.assertAlmostEqual(s["ozet"]["N_hesap"], N, places=9)
        self.assertEqual(self._motor(s)["sonuc"]["uygun"], g["motor_gucu"] >= N)
        self.assertEqual(self._eta_satiri(s)["kaynak"], "KATALOG")

    def test_dislili_makinede_de_girilen_kullanilir(self):
        s = M.hesapla({"makine_tipi": "Dişli", "makine_verimi": 0.62})
        self.assertEqual(s["ara"]["motor.eta"], 0.62)

    def test_aralik_disi_reddedilir(self):
        for e in (0, 0.05, 1.2, -0.8):
            s = M.hesapla({"makine_verimi": e})
            self.assertFalse(s["aktif"], e)
        for e in (0.1, 1.0):
            self.assertTrue(M.hesapla({"makine_verimi": e})["aktif"], e)

    def test_elektrik_koprusu_ayni_verimi_alir(self):
        from engine.uygulama import girdi as UG

        g = MG.tamamla(dict(MG.varsayilanlar(), _ofis=self.OFIS, makine_verimi=0.83))
        self.assertEqual(UG.kopru(g)["asansorler"][0]["eta"], 0.83)
        g = MG.tamamla(dict(MG.varsayilanlar(), _ofis=self.OFIS))
        self.assertEqual(UG.kopru(g)["asansorler"][0]["eta"], 0.80)

    def test_opsiyonel_ve_gelismis(self):
        self.assertIn("makine_verimi", MG.OPSIYONEL_ALANLAR)
        self.assertIn("makine_verimi", MG.GELISMIS_ALANLAR)
        self.assertIsNone(MG.ALAN["makine_verimi"][5])


class RegulatorSartDenetimi(unittest.TestCase):
    """TS EN 81-20 m.5.6.2.2.1.1 — imalatçı değerleri boşken paftaya ŞART yazılır.

    d):  regülatörün ürettiği kuvvet ≥ max( 2 × devreye sokma kuvveti ; 300 N ).
         Kuvvet bilinmiyorsa 300 N denetlenir ve ikinci koşul tersinden
         yazılır:  devreye sokma kuvveti ≤ Fçekme / 2.
    a):  1,15·v ≤ v_dev < üst sınır;  v > 1 m/s'de üst sınıra, düşük hızda
         alt sınıra olabildiğince yakın seçilmesi önerilir.
    """

    def _bolum(self, s):
        return next(b for b in s["bolumler"] if b["kimlik"] == "regulator_halati")

    def _satir(self, b, bas):
        return next(x for x in b["adimlar"] if str(x.get("aciklama", "")).startswith(bas))

    def test_kuvvet_bossa_300_N_ve_sart(self):
        s = M.hesapla({})
        a, b = s["ara"], self._bolum(s)
        Fc = a["regulator.Freg2"] - a["regulator.Freg"]
        self.assertGreaterEqual(Fc, 300)
        self.assertTrue(b["sonuc"]["uygun"])
        self.assertIsNone(b.get("eksik_hesap"))
        self.assertEqual(a["regulator.F_sinir"], 300)
        self.assertAlmostEqual(a["regulator.Fgt_azami"], Fc / 2, places=9)
        sart = self._satir(b, "Şart:  Fgt")
        self.assertIn(f"{Fc / 2:.2f}".replace(".", ","), sart["aciklama"])
        self.assertIn("Fgt ≤ Fçekme / 2", b["sonuc"]["baslik"])

    def test_kuvvet_bossa_da_300_N_altinda_kalir(self):
        s = M.hesapla({"reg_gergi_agirligi": 5, "_ofis": {"reg_mu": 0.05}})
        self.assertLess(s["ara"]["regulator.F_cekme"], 300)
        self.assertFalse(self._bolum(s)["sonuc"]["uygun"])

    def test_kuvvet_girilince_iki_kati_aranir_sart_yazilmaz(self):
        for F, sinir in ((100, 300), (400, 800), (900, 1800)):
            s = M.hesapla({"guvenlik_devreye_kuvvet": F})
            a, b = s["ara"], self._bolum(s)
            self.assertEqual(a["regulator.F_sinir"], sinir)
            self.assertIsNone(a["regulator.Fgt_azami"])
            self.assertEqual(b["sonuc"]["uygun"], a["regulator.F_cekme"] >= sinir)
            self.assertFalse(any(str(x.get("aciklama", "")).startswith("Şart:  Fgt") for x in b["adimlar"]))
        self.assertFalse(self._bolum(M.hesapla({"guvenlik_devreye_kuvvet": 9000}))["sonuc"]["uygun"])

    def test_hiz_bossa_aralik_uc_haneyle_ve_oneri(self):
        for v, alt, ust, yon in ((1.6, "1,840", "2,156", "üst"), (1.0, "1,150", "1,500", "alt")):
            b = self._bolum(M.hesapla({"beyan_hizi": v}))
            sart = self._satir(b, "Şart:  ")
            self.assertEqual(sart["aciklama"], f"Şart:  {alt} m/s  ≤  v_dev  <  {ust} m/s")
            self.assertIn(f"{yon} sınıra olabildiğince yakın", sart["deger"])
            self.assertTrue(b["sonuc"]["uygun"])

    def test_hiz_girilince_denetlenir(self):
        #  1,6 m/s kaymalı:  1,25·1,6 + 0,25/1,6 = 2,15625
        for v_dev, uygun in ((2.0, True), (2.155, True), (2.158, False), (1.83, False)):
            b = self._bolum(M.hesapla({"beyan_hizi": 1.6, "reg_devreye_hizi": v_dev}))
            self.assertEqual(b["sonuc"]["uygun"], uygun, v_dev)
        b = self._bolum(M.hesapla({"beyan_hizi": 1.6, "reg_devreye_hizi": 2.158}))
        self.assertTrue(any("< 2,156 m/s" in str(x.get("aciklama")) for x in b["adimlar"]))

    def test_regulator_grubu_tamamen_gelismis(self):
        grup = dict(MG.GRUPLAR)["Hız regülatörü"]
        self.assertTrue(set(grup) <= MG.GELISMIS_ALANLAR)
        for a in ("guvenlik_devreye_kuvvet", "reg_devreye_hizi"):
            self.assertIn(a, MG.OPSIYONEL_ALANLAR)
            self.assertIsNone(MG.ALAN[a][5])


if __name__ == "__main__":
    unittest.main(verbosity=2)

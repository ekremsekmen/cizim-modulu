# -*- coding: utf-8 -*-
"""
TEST 2  —  KENAR DURUMLAR VE TABLO SINIRLARI

Motorun kendi kurallarını sınar:
tablo sınırları, yuvarlama kuralları, kapsam dışı girdiler, hata mesajları.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.avan import hesap as AV
from engine.avan import tablolar as T
from engine.avan import trafik as TR   # noqa: E402
from engine.ortak.steps import yuvarla, tavana_yuvarla, yukari_yuvarla, tr as TRS  # noqa: E402
from testler.ortak import Rapor                              # noqa: E402

TEMEL = dict(bina_tipi="Konut", bina_yuksekligi=39.98, yapi_yuksekligi=43, N=11,
             hizli1=44, hizli2=3, h=3, P=10, kapi_genisligi=900,
             kapi_tipi="Merkezden Açılan Oto.")
ORT = dict(U=380, kappa=56, eps_max=3, temel_a=26.55, temel_b=16.4, beta=150,
           serit_L=58.5, cubuk_sayisi=4, mk_uzunluk=0, mk_genislik=0)
AS = dict(tanim="A", kapasite=10, V=1.6, eta=0.85, Hk=32.85, kuyu_genisligi=1800,
          kabin_boyu=1450, kabin_genisligi=1300, gr=17.91, Fmk=350, Fsh=100,
          Nsc=11, S1=6, L1=32.85, S2=6, L2=3, kablo_tipi="NHXMH FE180")


def g(**kw):
    d = dict(TEMEL)
    d.update(kw)
    return d


def _yakin_o(a, b, tol=1e-6):
    if a is None or b is None:
        return False
    return abs(float(a) - float(b)) <= tol * max(abs(float(a)), abs(float(b)), 1.0)


def calistir():
    print("\n\033[1mTEST 2 — KENAR DURUMLAR VE TABLO SINIRLARI\033[0m")
    r = Rapor("Kenar durumlar")

    # ---------------------------------------------------- yuvarlama kuralları
    # yuvarla() yarımı YUKARI yuvarlar; Python'un round() bankacı yuvarlaması yapar.
    for x, b, bek in ((865, -1, 870), (875, -1, 880), (2.5, 0, 3), (3.5, 0, 4),
                      (-2.5, 0, -3), (0.125, 2, 0.13)):
        r.esit(f"yuvarla({x},{b})", yuvarla(x, b), bek)
    #  KAYAN NOKTA GÜRÜLTÜSÜ.  1,005 ikili sistemde 1,00499999… diye saklanır;
    #  floor( x·100 + 0,5 ) bu yüzden 1,01 yerine 1,00 veriyordu.  Yarımın
    #  GERÇEKTEN altında kalan değer ise yukarı gitmemeli.
    for x, b, bek in ((1.005, 2, 1.01), (-1.005, 2, -1.01), (4.015, 2, 4.02),
                      (2.675, 2, 2.68), (1.0049999, 2, 1.0), (0.1 + 0.2, 1, 0.3),
                      (219.99999999999997, 6, 220.0), (1234.5, -1, 1230)):
        r.kontrol(f"yuvarla({x!r},{b}) = {bek}  ( gürültü )",
                  yuvarla(x, b) == bek, f"→ {yuvarla(x, b)!r}")
    for x, k, bek in ((63921.0, 10, 63930), (63930.0, 10, 63930), (0.1, 10, 10)):
        r.esit(f"tavana_yuvarla({x},{k})", tavana_yuvarla(x, k), bek)
    for x, bek in ((3.0001, 4), (3.0, 3), (2.9999, 3)):
        r.esit(f"yukari_yuvarla({x})", yukari_yuvarla(x, 0), bek)

    # ---------------------------------------------------- Türkçe sayı biçimi
    r.esit("tr(1234.5)", TRS(1234.5), "1.234,50")
    r.esit("tr(0.075, 4)", TRS(0.075, 4), "0,0750")
    r.esit("tr(None)", TRS(None), "—")
    #  PAFTADAKİ SAYI DA YARIMI YUKARI YUVARLANIR.  Python'un biçimlendirmesi
    #  sayının ikili değerini bankacı kuralıyla yuvarlıyordu:  2,5 → "2",
    #  0,125 → "0,12", 9,325 ( ikilide 9,32499… ) → "9,32".  Ekranla aynı
    #  kural TEST 5'te tarayıcıda denetlenir.
    for x, n, bek in ((2.5, 0, "3"), (3.5, 0, "4"), (0.5, 0, "1"), (0.125, 2, "0,13"),
                      (9.325, 2, "9,33"), (347.835, 2, "347,84"), (4978.575, 2, "4.978,58"),
                      (1.15, 1, "1,2"), (-1.005, 2, "-1,01"), (1.0049999, 2, "1,00"),
                      (999999.995, 2, "1.000.000,00"), (float("inf"), 2, "inf")):
        r.esit(f"tr({x}, {n})", TRS(x, n), bek)

    # ---------------------------------------------------- Tablo-3 / Tablo-5
    # Kapalı formüller MMO/697 tablolarıyla örtüşmeli, sınır dışında None dönmeli.
    r.esit("H(N=1,P=10)", T.tablo3_H(1, 10), 1.0)
    r.esit("S(N=1,P=10)", T.tablo5_S(1, 10), 1.0)
    r.kontrol("H(N=31) kapsam dışı", T.tablo3_H(31, 10) is None)
    r.kontrol("H(P=35) kapsam dışı", T.tablo3_H(10, 35) is None)
    r.kontrol("H(P=5) kapsam dışı", T.tablo3_H(10, 5) is None)
    r.kontrol("S artan P ile artmalı", T.tablo5_S(10, 20) > T.tablo5_S(10, 10))
    r.kontrol("H ≤ N olmalı", all(T.tablo3_H(n, 10) <= n for n in range(1, 31)))
    r.kontrol("S ≤ N olmalı", all(T.tablo5_S(n, 10) <= n + 1e-9 for n in range(1, 31)))

    # ---------------------------------------------------- Tablo-2 hız kademeleri
    for durak, bek in ((2, 1), (9, 1), (10, 1.6), (14, 1.6), (15, 2), (19, 2), (20, 2.5), (40, 2.5)):
        r.esit(f"Tablo-2 Konut {durak} durak", T.tablo2_min_hiz("Konut", durak), bek)
    for durak, bek in ((5, 1), (6, 1.6), (10, 1.6), (11, 2), (15, 2), (16, 2.5), (19, 2.5), (20, 3.5)):
        r.esit(f"Tablo-2 Büro {durak} durak", T.tablo2_min_hiz("Büro ve İş Merkezi", durak), bek)
    for durak, bek in ((6, 1), (7, 1.6), (10, 1.6), (11, 2), (15, 2), (16, 2.5), (20, 3.5)):
        r.esit(f"Tablo-2 Otel {durak} durak", T.tablo2_min_hiz("Otel", durak), bek)
    r.kontrol("Tablo-2 tanımsız grup → None", T.tablo2_min_hiz(None, 10) is None)

    # ---------------------------------------------------- Tablo-6 tg
    for V, bek in ((0.63, 10), (1, 7), (1.6, 6), (1.75, 5.8875), (2, 5.7),
                   (2.5, 5.5), (3, 5.25), (3.5, 5), (5, 4.5), (6, 4.3)):
        r.esit(f"Tablo-6 tg(V={V})", T.tablo6_tg(V), bek)
    r.esit("1,75 m/s ara değer notu", T.tg_kaynagi(1.75), "MMO/697 Tablo-6 (ara değer — enterpolasyon)")
    r.esit("1,60 m/s tablo değeri", T.tg_kaynagi(1.6), "MMO/697 Tablo-6")

    # ---------------------------------------------------- Tablo-4 / Tablo-8
    r.esit("Tablo-4 900 Merkezden", T.tablo4_ta_tk(900, "Merkezden Açılan Oto."), (2.3, 2.9))
    r.esit("Tablo-4 eşanlamlı ad", T.tablo4_ta_tk(900, "Merkezden Açılan Otomatik"), (2.3, 2.9))
    r.esit("Tablo-4 1300 kabin içi → yok", T.tablo4_ta_tk(1300, "Kabin İçi Oto. Kat K.Ç."), (None, None))
    r.esit("Tablo-4 1200 kabin içi → yok", T.tablo4_ta_tk(1200, "Kabin İçi Oto. Kat K.Ç."), (None, None))
    #  1000 ve 1200 mm MMO Tablo-4'te basılı değildir; komşu satırların TAM ORTASI olmalı
    for kt in ("Teleskopik Otomatik", "Merkezden Açılan Oto."):
        for ara, alt, ust in ((1000, 900, 1100), (1200, 1100, 1300)):
            bek = tuple((T.TABLO_4[alt][kt][j] + T.TABLO_4[ust][kt][j]) / 2 for j in (0, 1))
            r.esit(f"Tablo-4 {ara} {kt[:9]} = ({alt}+{ust})/2", T.tablo4_ta_tk(ara, kt), bek)
    r.esit("Tablo-4 1000 kabin içi = (5+6)/2", T.tablo4_ta_tk(1000, "Kabin İçi Oto. Kat K.Ç."), (5.5, 5.5))
    r.esit("1000 mm ara değer notu", T.tablo4_kaynagi(1000), "MMO/697 Tablo-4 (ara değer — enterpolasyon)")
    r.esit("900 mm tablo değeri", T.tablo4_kaynagi(900), "MMO/697 Tablo-4")
    #  700 mm ISO tablosunun dışında — 800→900 eğiminden dış değerleme
    r.esit("Tablo-8 tp(700) dış değer", T.tablo8_tp(700), 1.3)
    r.esit("Tablo-8 tp(700) = 800 + (800−900)", T.tablo8_tp(700),
           T.TABLO_8[800] + (T.TABLO_8[800] - T.TABLO_8[900]))
    r.kontrol("700 mm kaynağı kapsam dışı diyor", "kapsam dışı" in T.tablo8_kaynagi(700))
    r.esit("800 mm tablo kaynağı", T.tablo8_kaynagi(800), "ISO 8100-32:2020, Tablo 6")
    r.esit("Tablo-8 tp(1200)", T.tablo8_tp(1200), 0.9)
    r.kontrol("tp kapı genişledikçe azalır (monoton)",
              all(T.tablo8_tp(a) >= T.tablo8_tp(b)
                  for a, b in zip(T.KAPI_GENISLIKLERI, T.KAPI_GENISLIKLERI[1:])))
    r.kontrol("ta/tk kapı genişledikçe artar (monoton)",
              all(T.TABLO_4[a]["Teleskopik Otomatik"][j] <= T.TABLO_4[b]["Teleskopik Otomatik"][j]
                  for j in (0, 1)
                  for a, b in zip(T.KAPI_GENISLIKLERI, T.KAPI_GENISLIKLERI[1:])))
    r.kontrol("her genişlik iki tabloda da var (boşluk kalmadı)",
              all(T.tablo8_tp(w) is not None
                  and T.tablo4_ta_tk(w, "Teleskopik Otomatik")[0] is not None
                  for w in T.KAPI_GENISLIKLERI))

    # ---------------------------------------------------- Tablo-7 / Tablo-11
    r.esit("Tablo-7 15 kişi (istisna)", T.tablo7_yuk(15), 1125)
    r.esit("Tablo-7 10 kişi", T.tablo7_yuk(10), 800)
    r.esit("Tablo-11 alt sınır", T.tablo11_Gk(300), 500)
    r.esit("Tablo-11 üst sınır", T.tablo11_Gk(5000), 1900)
    r.esit("Tablo-11 tam nokta 800", T.tablo11_Gk(800), 800)
    r.esit("Tablo-11 ara değer 900", T.tablo11_Gk(900), 880)
    r.kontrol("Tablo-11 monoton artan",
              all(T.tablo11_Gk(q) <= T.tablo11_Gk(q + 50) for q in range(450, 2450, 50)))

    # ---------------------------------------------------- aydınlatma verimi
    # k bir ALT satıra yuvarlanarak okunur (emniyetli taraf)
    r.esit("η(k=0,50) alt sınıra kenetlenir", T.ayd_verim(0.50, 2), 0.23)
    r.esit("η(k=0,79) → 0,60 satırı", T.ayd_verim(0.79, 2), 0.23)
    r.esit("η(k=0,80) → 0,80 satırı", T.ayd_verim(0.80, 2), 0.29)
    r.esit("η(k=9,9) üst satır", T.ayd_verim(9.9, 2), 0.57)
    r.esit("η sütun 5", T.ayd_verim(1.5, 5), 0.36)

    # ---------------------------------------------------- trafik: hata yolları
    r.kontrol("boş girdi çökmez",
              "HESAP HATASI" in (TR.hesapla_tek({"bina_tipi": "Konut"}).get("hata") or ""))
    r.kontrol("geçersiz bina tipi",
              "Bina tipi" in (TR.hesapla_tek({"bina_tipi": "Yok Böyle"}).get("hata") or ""))
    r.kontrol("N=31 → bölgeli hesap uyarısı",
              "30" in (TR.hesapla_tek(g(N=31)).get("hata") or ""))
    #  Boşluklar kapandı: yedi genişliğin tamamı hesaplanabilmeli
    for w in T.KAPI_GENISLIKLERI:
        r.kontrol(f"kapı {w} mm hesaplanabiliyor",
                  TR.hesapla_tek(g(kapi_genisligi=w)).get("hata") is None)
    r.kontrol("1000 mm ara değer uyarısı veriyor",
              any("enterpolasyon" in u for u in TR.hesapla_tek(g(kapi_genisligi=1000))["uyarilar"]))
    r.kontrol("700 mm dış değerleme uyarısı veriyor",
              any("dış değerleme" in u for u in TR.hesapla_tek(g(kapi_genisligi=700))["uyarilar"]))
    r.kontrol("700 mm erişilebilirlik uyarısı veriyor",
              any("TS EN 81-70" in u for u in TR.hesapla_tek(g(kapi_genisligi=700))["uyarilar"]))
    r.kontrol("elle ta/tk girilince ara değer uyarısı susar",
              not any("enterpolasyon" in u for u in
                      TR.hesapla_tek(g(kapi_genisligi=1000, manuel_ta=2.4,
                                       manuel_tk=3.0))["uyarilar"]))
    #  Kabin içi kapı tipi 1200/1300 mm'de tabloda yok → net hata, elle girişle geçer
    for w in (1200, 1300):
        s_ = TR.hesapla_tek(g(kapi_genisligi=w, kapi_tipi="Kabin İçi Oto. Kat K.Ç."))
        r.kontrol(f"kabin içi {w} mm → açıklayıcı hata",
                  "Kabin İçi" in (s_.get("hata") or ""))
        r.kontrol(f"kabin içi {w} mm + elle ta/tk geçer",
                  TR.hesapla_tek(g(kapi_genisligi=w, kapi_tipi="Kabin İçi Oto. Kat K.Ç.",
                                   manuel_ta=6.0, manuel_tk=6.0)).get("hata") is None)
    # ---------------------------------------------------- bodrum durağı
    #  MMO/697 s.14/s.16 : H ve S ana giriş ÜSTÜNDEKİ kat adedi N ile tanımlıdır.
    #  Bodrum durağı H, S ve TR'yi değiştirmez; yalnız Tablo-2 durak adedine ve
    #  toplam seyahat mesafesine girer.
    t0 = TR.hesapla_tek(g(N=13, h=3, manuel_V=1.6))
    t2 = TR.hesapla_tek(g(N=13, h=3, bodrum=2, manuel_V=1.6))
    r.esit("bodrum H'yi değiştirmez", t2["ozet"]["H"], t0["ozet"]["H"])
    r.esit("bodrum S'yi değiştirmez", t2["ozet"]["S"], t0["ozet"]["S"])
    r.esit("bodrum TR'yi değiştirmez (hız sabitken)", t2["ozet"]["TR"], t0["ozet"]["TR"])
    r.esit("durak = N + 1 + Nb", t2["ozet"]["durak"], 16)
    r.esit("bodrumsuz durak = N + 1", t0["ozet"]["durak"], 14)
    r.esit("toplam seyahat = (N+Nb)·h", t2["ozet"]["toplam_seyahat"], 45)
    r.esit("bodrumsuz seyahat = N·h", t0["ozet"]["toplam_seyahat"], 39)
    #  Konut: durak ≤14 → 1,6 m/s ; 15-19 → 2,0 m/s.  Bodrum eşiği aşırır.
    r.esit("bodrum Tablo-2 asgari hızını yükseltir",
           TR.hesapla_tek(g(N=13, h=3, bodrum=2))["ozet"]["V"], 2)
    r.esit("bodrumsuz Tablo-2 asgari hızı",
           TR.hesapla_tek(g(N=13, h=3))["ozet"]["V"], 1.6)
    r.esit("bodrum boş = 0", TR.hesapla_tek(g(bodrum=""))["ozet"]["bodrum"], 0)
    r.esit("bodrum None = 0", TR.hesapla_tek(g(bodrum=None))["ozet"]["bodrum"], 0)
    for kotu in (-1, 2.5, 11, "abc"):
        r.kontrol(f"bodrum {kotu!r} reddedilir",
                  "bodrum" in (TR.hesapla_tek(g(bodrum=kotu)).get("hata") or ""))
    #  Bodrum notu bir YÖNTEM açıklamasıdır: ekranda ( ! ) balonuna girer,
    #  paftaya ise basılır — bu yüzden "aciklamalar" listesinde durur.
    r.kontrol("bodrum açıklaması üretiliyor",
              any("H (Tablo-3)" in n for b in t2["bolumler"] for n in b["aciklamalar"]))
    r.kontrol("bodrum açıklaması uyarı listesine karışmıyor",
              not any("H (Tablo-3)" in n for b in t2["bolumler"] for n in b["notlar"]))
    r.kontrol("bodrumsuzda bodrum açıklaması yok",
              not any("H (Tablo-3)" in n for b in t0["bolumler"]
                      for n in list(b["notlar"]) + list(b["aciklamalar"])))
    #  Nüfus türetimi SONUÇTUR — görünür kalmalı, balona girmemeli
    r.kontrol("nüfus türetimi görünür notlarda",
              any("b = " in n or "→ b" in n for b in t2["bolumler"] for n in b["notlar"]))
    r.kontrol("Tablo-1 kuralı açıklamalarda",
              any("Tablo-1:" in n for b in t2["bolumler"] for n in b["aciklamalar"]))
    #  Her bölümde iki liste de bulunmalı (arayüz ve PDF ikisini de okur)
    r.kontrol("her bölümde iki not listesi var",
              all(isinstance(b.get("notlar"), list) and isinstance(b.get("aciklamalar"), list)
                  for s_ in (t0, t2) for b in s_["bolumler"]))

    # ---------------------------------------------------- erişilebilirlik
    r.kontrol("6 kişi erişilebilirlik uyarısı",
              any("81-70" in u for u in TR.hesapla_tek(g(P=6))["uyarilar"]))
    r.kontrol("10 kişi 900 mm uyarı vermez",
              not any("81-70" in u for u in TR.hesapla_tek(g(P=10, kapi_genisligi=900))["uyarilar"]))
    r.kontrol("6 kişi öneri sıralamasında en iyi seçilmez",
              all(not o.get("onerilen") for o in TR.hesapla_tek(g())["oneriler"]
                  if o["kapasite"] == 6))
    r.kontrol("öneri satırları erişilebilirlik bayrağı taşır",
              all("erisilebilir" in o for o in TR.hesapla_tek(g())["oneriler"]))
    r.kontrol("erisilebilir_mi 8 kişi 800 mm", T.erisilebilir_mi(8, 800))
    r.kontrol("erisilebilir_mi 8 kişi 700 mm değil", not T.erisilebilir_mi(8, 700))
    r.kontrol("erisilebilir_mi 6 kişi değil", not T.erisilebilir_mi(6, 900))

    # ---------------------------------------------------- Kamu binaları
    kamu = TR.hesapla_tek(g(bina_tipi="Kamu Binaları"))
    r.kontrol("kamu %k varsayımı paftada", any("Tablo-9" in u for u in kamu["uyarilar"]))
    r.kontrol("kamu hız varsayımı paftada", any("Tablo-2" in u for u in kamu["uyarilar"]))
    r.esit("kamu %k = İş Merkezi", kamu["ozet"]["k"],
           T.TABLO_9["İş Merkezi"][kamu["ozet"]["standart"]])
    r.kontrol("kamuda manuel k kabul edilir",
              TR.hesapla_tek(g(bina_tipi="Kamu Binaları", manuel_k=0.13))["ozet"]["k"] == 0.13)

    # ==================================================================
    #  v2.8 — KİTAP DENETİMİ:  motor tabloları MMO/697 ile BİREBİR mi?
    #
    #  Bu, doğrulama zincirinin eskiden EKSİK olan halkasıdır.  Diğer testler
    #  "motor ≡ referans ≡ testlerdeki beklenen değer" der;  üçü de aynı
    #  aktarımdan geldiği için bir tablo kitaptan YANLIŞ aktarılmışsa üçü de
    #  aynı yanlışı taşır ve hiçbir test görmez.
    #  Aşağıdaki değerler kitabın ( MMO/697, 2. Baskı, Ocak 2020 ) basılı
    #  tablolarından İKİNCİ KEZ, bağımsız olarak yazılmıştır — ikisinden
    #  birinde yazım hatası olursa test söyler.
    # ==================================================================
    for _ad, _bek in (("KONUT — İlk yatak odası", 2), ("KONUT — Diğer oda", 1),
                      ("OTEL — Yatak", 1), ("İŞ MERKEZİ — Çalışma alanı", 1 / 12),
                      ("HASTANE — Yatak", 3), ("RESMİ BİNA — Çalışma alanı", 1 / 12),
                      ("OTOPARK — Ticari araç", 1.5), ("OTOPARK — Özel araç", 1)):
        r.esit(f"kitap T1 · {_ad}", T.TABLO_1[_ad]["katsayi"], _bek)

    for _grup, _ara in (("Konut", ((2, 9, 1), (10, 14, 1.6), (15, 19, 2.0), (20, 30, 2.5))),
                        ("Büro ve İş Merkezi", ((2, 5, 1), (6, 10, 1.6), (11, 15, 2.0), (16, 19, 2.5))),
                        ("Otel", ((2, 6, 1), (7, 10, 1.6), (11, 15, 2.0), (16, 19, 2.5)))):
        for _alt, _ust, _bek in _ara:
            for _d in (_alt, _ust):
                r.esit(f"kitap T2 · {_grup} {_d} durak", T.tablo2_min_hiz(_grup, _d), _bek)

    _T4 = {700: {"Teleskopik Otomatik": (2.5, 3.0), "Merkezden Açılan Oto.": (2.0, 2.5),
                 "Kabin İçi Oto. Kat K.Ç.": (5.0, 5.0)},
           800: {"Teleskopik Otomatik": (2.5, 3.0), "Merkezden Açılan Oto.": (2.0, 2.5),
                 "Kabin İçi Oto. Kat K.Ç.": (5.0, 5.0)},
           900: {"Teleskopik Otomatik": (2.5, 3.8), "Merkezden Açılan Oto.": (2.3, 2.9),
                 "Kabin İçi Oto. Kat K.Ç.": (5.0, 5.0)},
           1100: {"Teleskopik Otomatik": (3.0, 4.0), "Merkezden Açılan Oto.": (2.5, 3.5),
                  "Kabin İçi Oto. Kat K.Ç.": (6.0, 6.0)},
           1300: {"Teleskopik Otomatik": (3.7, 5.0), "Merkezden Açılan Oto.": (2.7, 3.7)}}
    for _kg, _satir in _T4.items():
        for _tip, (_ta, _tk) in _satir.items():
            _p = T.tablo4_ta_tk(_kg, _tip)
            r.esit(f"kitap T4 · {_kg} {_tip} ta", _p[0], _ta)
            r.esit(f"kitap T4 · {_kg} {_tip} tk", _p[1], _tk)

    for _V, _bek in ((0.63, 10.0), (1.0, 7.0), (1.6, 6.0), (2.0, 5.7),
                     (2.5, 5.5), (3.5, 5.0), (5.0, 4.5), (6.0, 4.3)):
        r.esit(f"kitap T6 · V={_V}", T.tablo6_tg(_V), _bek)

    for _P, _bek in ((6, 450), (8, 630), (10, 800), (13, 1000), (16, 1275),
                     (20, 1600), (25, 2000), (30, 2500)):
        r.esit(f"kitap T7 · {_P} kişi", T.tablo7_yuk(_P), _bek)

    for _tip, (_s, _y) in (("Konut", (0.075, 0.10)), ("Otel", (0.12, 0.15)),
                           ("İş Merkezi", (0.15, 0.17)), ("Hastane", (0.10, 0.20)),
                           ("Otopark", (0.10, 0.20))):
        r.esit(f"kitap T9 · {_tip} standart", T.TABLO_9[_tip]["Standart"], _s)
        r.esit(f"kitap T9 · {_tip} yükseltilmiş", T.TABLO_9[_tip]["Yükseltilmiş"], _y)

    for _ad, (_sa, _st, _yu) in (
            ("Konut", (120, 100, 80)), ("Karma Binalar (İşyeri ve Konut)", (60, 50, 30)),
            ("İş Merkezi (Tek Firmalı)", (60, 50, 40)), ("İş Merkezi (Çok Firmalı)", (50, 40, 30)),
            ("Otel (3* ve altı)", (60, 50, 40)), ("Otel (4* ve üzeri)", (50, 40, 30)),
            ("Kamu Binaları", (None, 40, 30)), ("Hastane", (None, 40, 30)),
            ("Poliklinik Binaları ve Yaşlı Bakım Ev.", (60, 50, 40)),
            ("Katlı Otopark", (60, 50, 40))):
        r.esit(f"kitap T10 · {_ad} şartlı", T.TABLO_10[_ad]["sartli"], _sa)
        r.esit(f"kitap T10 · {_ad} standart", T.TABLO_10[_ad]["standart"], _st)
        r.esit(f"kitap T10 · {_ad} yükseltilmiş", T.TABLO_10[_ad]["yukseltilmis"], _yu)

    for _Q, _bek in ((100, 0.37), (180, 0.58), (225, 0.70), (300, 0.90), (375, 1.10),
                     (400, 1.17), (450, 1.30), (525, 1.45), (600, 1.60), (630, 1.66),
                     (675, 1.75), (750, 1.90), (800, 2.00), (825, 2.05), (900, 2.20),
                     (975, 2.35), (1000, 2.40), (1050, 2.50), (1125, 2.65), (1200, 2.80),
                     (1250, 2.90), (1275, 2.95), (1350, 3.10), (1425, 3.25), (1500, 3.40),
                     (1600, 3.56), (2000, 4.20), (2500, 5.00)):
        r.esit(f"kitap T11 · {_Q} kg", T.kabin_azami_alan(_Q), _bek)

    #  Kitabın KENDİ örnek hesabı ( s.53 ):  H, S ve TR değerleri
    r.esit("kitap örneği · H(9 kat, 15 kişi)", round(T.tablo3_H(9, 15), 1), 8.8)
    r.esit("kitap örneği · S(9 kat, 15 kişi)", round(T.tablo5_S(9, 15), 2), 7.46)
    r.esit("kitap örneği · H(9 kat, 6 kişi)", round(T.tablo3_H(9, 6), 2), 8.16)
    r.esit("kitap örneği · S(9 kat, 6 kişi)", round(T.tablo5_S(9, 6), 2), 4.56)
    #  TR = 2·H·tv + (S+1)·ts + 2·p·tp
    _tv = 3 / 1.6
    #  450 kg asansörü — kitabın verdiği sonuçla BİREBİR ( tp = 2,2 doğrulanır )
    r.esit("kitap örneği · TR2 = 103,567 s",
           round(2 * 8.16 * _tv + (4.56 + 1) * (2.3 + 2.9 + 6 - _tv) + 2 * 4.8 * 2.2, 3), 103.567)
    #  1125 kg asansörü — KİTAPTA ARİTMETİK HATA VAR.  Kitap TR1 = 149,9955 s
    #  yazar; kendi verdiği H = 8,8 · S = 7,46 · ts = 10,425 · p = 12 · tp = 2,2
    #  ile doğru sonuç 173,9955 s'dir ( fark tam 24,0 s = 2·12·1,0 ).  Kitabın
    #  R1 = 24 değeri de hatalı TR1'den türer ( doğrusu 20,7 ) ve aynı sayfada
    #  Reş "337,9" yazılmıştır ( doğrusu 37,9 ).  Program DOĞRU aritmetiği
    #  uygular;  bu kontrol o farkı kalıcı olarak kayda geçirir.
    _tr1 = round(2 * 8.8 * _tv + (7.46 + 1) * (2.5 + 3.8 + 6 - _tv) + 2 * 12 * 2.2, 4)
    r.esit("kitap örneği · TR1 doğru aritmetikle", _tr1, 173.9955)
    r.esit("kitabın bastığı TR1 ile fark tam 24,0 s", round(_tr1 - 149.9955, 4), 24.0)

    # ---------------------------------------------------- Tablo-7 15 kişi
    r.esit("15 kişi tabloda açık", T.TABLO_7[15], 1125)
    r.esit("15 kişi kaynağı ayrı", T.tablo7_kaynagi(15), "MMO örneği s.53-54 (Tablo-7 dışı)")
    r.esit("16 kişi normal kaynak", T.tablo7_kaynagi(16), "MMO/697 Tablo-7")
    #  v2.8 — Tablo-7'de OLMAYAN bir kapasiteye kaynak olarak "Tablo-7" yazmak,
    #  olmayan bir tablo satırına atıf yapmaktır ( 7 kişi → 525 kg ).
    #  v2.8 — KAYNAK ADI TEK ANLAMLI OLMALIDIR.  Paftada ISO 8100-32:2020'nin
    #  "Tablo 6"sı ( tp ) ile MMO/697'nin "Tablo-6"sı ( tg ) yan yana basılıyor;
    #  çıplak "Tablo-6" hangisi olduğunu söylemiyordu.
    r.kontrol("MMO tabloları tam adıyla yazılıyor",
              all(x.startswith("MMO/697 Tablo") for x in
                  (T.tablo4_kaynagi(900), T.tg_kaynagi(1.6), T.tablo7_kaynagi(16))))
    r.kontrol("ISO tablosu ISO adıyla yazılıyor",
              T.tablo8_kaynagi(900).startswith("ISO 8100-32:2020"))
    r.kontrol("tp kaynağı MMO tablosuna atfedilmiyor",
              "MMO" not in T.tablo8_kaynagi(900))

    r.kontrol("tablo dışı kapasite Tablo-7 diye gösterilmez",
              T.tablo7_kaynagi(7) != "Tablo-7" and "DIŞI" in T.tablo7_kaynagi(7))
    r.kontrol("tablo dışı büyük kapasite de gösterilmez",
              T.tablo7_kaynagi(34) != "Tablo-7")
    r.esit("kapasite girilmemişse kaynak boş", T.tablo7_kaynagi(None), "—")
    r.kontrol("15 kişi hesaplanabiliyor", TR.hesapla_tek(g(P=15)).get("hata") is None)

    r.kontrol("nüfus yok → uyarı",
              "Nüfus" in (TR.hesapla_tek(g(hizli1=None, hizli2=None)).get("hata") or ""))
    r.kontrol("Tablo-9 varken manuel k reddedilir",
              "manuel k girilemez" in (TR.hesapla_tek(g(manuel_k=0.2)).get("hata") or ""))
    r.kontrol("geçersiz manuel hız reddedilir",
              "hız" in (TR.hesapla_tek(g(manuel_V=1.3)).get("hata") or "").lower())
    r.kontrol("karma bina k'sız hesaplanmaz",
              TR.hesapla_tek(g(bina_tipi="Karma Binalar (İşyeri ve Konut)")).get("hata") is not None)

    # ---------------------------------------------------- trafik: doğru davranış
    s = TR.hesapla_tek(g())
    r.esit("hesap standardı yüksek yapıda", s["ozet"]["standart"], "Yükseltilmiş")
    r.esit("adet = MAX(taşıma, bekleme)", s["ozet"]["adet"],
           int(max(1, s["ozet"]["tasima_adedi"], s["ozet"]["bekleme_adedi"])))
    r.kontrol("Ieer = TR / adet",
              abs(s["ozet"]["Ieer"] - s["ozet"]["TR"] / s["ozet"]["adet"]) < 1e-9)
    r.esit("standart eşiği tam 21,50 m", TR.hesapla_tek(
        g(bina_yuksekligi=21.50, yapi_yuksekligi=30.50))["ozet"]["standart"], "Standart")
    r.esit("21,51 m → Yükseltilmiş", TR.hesapla_tek(
        g(bina_yuksekligi=21.51, yapi_yuksekligi=30.50))["ozet"]["standart"], "Yükseltilmiş")
    r.esit("b<200 → n=0,30", TR.hesapla_tek(g(hizli1=10, hizli2=3))["ozet"]["n_artis"], 0.3)
    r.esit("b≥200 → n=0,25", TR.hesapla_tek(g(hizli1=40, hizli2=4))["ozet"]["n_artis"], 0.25)
    r.esit("elle adet uygulanır", TR.hesapla_tek(g(manuel_adet=5))["ozet"]["adet"], 5)
    r.kontrol("elle adet yetersizse Kabul Edilmez",
              TR.hesapla_tek(g(manuel_adet=1))["ozet"]["sonuc"].startswith("Kabul Edilmez"))
    r.kontrol("öneri tablosu 6 kişiliği önermez",
              all(not x.get("onerilen") for x in s["oneriler"] if x["kapasite"] == 6))
    r.kontrol("öneri tablosunda tam bir öneri var",
              sum(1 for x in s["oneriler"] if x.get("onerilen")) == 1)

    #  v2.8 — ÖNERİ TABLOSUNDA ŞARTLI KABUL GERÇEKTEN HESAPLANIYOR.
    #  Burada eskiden "Şartlı kabul" ve "Kriteri aşıyor" dalları vardı ama
    #  ÇALIŞAMIYORLARDI:  adet zaten MAX[taşıma; TR/Izul] seçildiği için
    #  Ieer ≤ Izul her zaman doğru.  Şartlı kabulün gerçek karşılığı
    #  "taahhütnameyle DAHA AZ asansör yeterdi" sorusudur.
    #  Yükseltilmiş Konut:  Izul = 80 sn,  şartlı kabul sınırı = 120 sn
    _so = TR.hesapla_tek(g(hizli1=90))
    _oz, _on = _so["ozet"], _so["oneriler"]
    r.kontrol("şartlı sınır standarttan gevşek", _oz["esik_sartli"] > _oz["Izul"])
    r.kontrol("her seçenek uygulanan sınırı sağlıyor",
              all(x["Ieer"] <= _oz["Izul"] + 1e-9 for x in _on))
    r.kontrol("'Kriteri aşıyor' satırı hiç oluşmuyor",
              not any("aşıyor" in x["sinif"] for x in _on))
    _sart = [x for x in _on if x.get("adet_sartli")]
    r.kontrol("en az bir seçenekte şartlı kabul avantajı var", bool(_sart))
    r.kontrol("şartlı adet uygulanan adetten KÜÇÜK",
              all(x["adet_sartli"] < x["adet"] for x in _sart))
    r.kontrol("şartlı adet sınıf metnine yazılıyor",
              all("şartlı kabulle" in x["sinif"] for x in _sart))
    r.kontrol("şartlı adet şartlı sınırı sağlıyor",
              all(x["TR"] / x["adet_sartli"] <= _oz["esik_sartli"] + 1e-9 for x in _sart))
    #  Taahhütname yalnız BEKLEME süresini gevşetir — taşıma kapasitesi ölçütü durur
    r.kontrol("şartlı adet taşıma kapasitesini de sağlıyor",
              all(x["adet_sartli"] * x["R"] >= _oz["B"] * _oz["k"] - 1e-9 for x in _sart))
    #  Şartlı sınırı OLMAYAN bina tipinde ( Hastane ) alan hiç dolmamalı
    _hs = TR.hesapla_tek(g(bina_tipi="Hastane", hizli1=60, hizli2=None, manuel_k=None))
    r.kontrol("şartlı sınırı olmayan tipte adet_sartli boş",
              all(x.get("adet_sartli") is None for x in (_hs.get("oneriler") or [])))

    #  TAAHHÜTNAME SEÇİMİ  —  öneri tablosunun "şartlı kabulle 1 adet"
    #  dediği adet artık SEÇİLEBİLİYOR.  Kullanıcının projesi:  Konut, 6 kat,
    #  h = 3,06,  12 daire × 3+1,  10 kişilik 800 mm kapı, Tablo-2 hızı 1 m/s.
    #  Yok  →  2 adet ( Standart 100 sn );  Var  →  1 adet ( şartlı 120 sn ).
    _kp = dict(bina_tipi="Konut", bina_yuksekligi=21.33, yapi_yuksekligi=24.33, N=6,
               h=3.06, hizli1=12, hizli2=3, P=10, kapi_genisligi=800,
               kapi_tipi="Merkezden Açılan Oto.")
    _ty = TR.hesapla_tek(dict(_kp))
    _tv = TR.hesapla_tek(dict(_kp, taahhutname="Var"))
    _ov = _tv["ozet"]
    r.esit("taahhütname Yok → Standart adedi", _ty["ozet"]["adet"], _ty["ozet"]["adet_hesap"])
    _yk = TR.hesapla_tek(dict(_kp, taahhutname="Yok"))
    r.esit("taahhütname 'Yok' yazmak boş bırakmakla aynı",
           {k: x for k, x in _yk.items() if k != "girdiler"},
           {k: x for k, x in _ty.items() if k != "girdiler"})
    r.kontrol("taahhütname Var → daha az asansör", _ov["adet"] < _ov["adet_hesap"])
    r.esit("taahhütname Var → şartlı sınırda gereken adet",
           _ov["adet"], max(1, int(-(-_ov["TR"] // _ov["esik_sartli"]))))
    r.kontrol("taahhütname Var → sonuç Şartlı Kabul", _ov["sonuc"].startswith("Şartlı Kabul"))
    r.kontrol("taahhütname Var → Ieer şartlı sınır içinde", _ov["Ieer"] <= _ov["esik_sartli"])
    r.kontrol("taahhütname Var → Standart için gereken adet yine yazılıyor",
              f"{_ov['adet_hesap']} adet gerekir" in _ov["sonuc_cumlesi"])
    r.kontrol("taahhütname Var → karar kutusunda bekleme uygun",
              all(x["uygun"] for x in _ov["karar_olcutleri"]))
    r.kontrol("taahhütname Var → avan köprüsü şartlı adedi taşıyor",
              TR.trafik_ozeti(_tv)["adet"] == _ov["adet"])
    r.kontrol("taahhütname Var → taşıma kapasitesi yine sağlanıyor",
              _ov["adet"] * _ov["R"] >= _ov["B"] * _ov["k"])
    r.kontrol("taahhütname Yok → çıktıda taahhütname işareti yok",
              "taahhutname" not in _ty["ozet"])
    #  Gereksiz taahhütname:  Standart sınır aynı adetle zaten sağlanıyorsa
    #  adet değişmez, sonuç Standart kalır, bilgi notu düşülür.
    _tg = TR.hesapla_tek(dict(_kp, N=2, taahhutname="Var"))
    r.kontrol("gereksiz taahhütname → Standart sonuç",
              _tg["ozet"]["sonuc"].startswith("Standart"))
    r.kontrol("gereksiz taahhütname → bilgi notu",
              any("gerekmiyor" in u for u in _tg["uyarilar"]))
    #  Şartlı sınırı olmayan bina tipinde Var seçimi kullanılamaz → hesap durur
    #  ( Tablo-2'de Hastane yok → hız elle verilir, yoksa hesap 'kabin hızı
    #    belirlenemedi' der )
    _th = TR.hesapla_tek(g(bina_tipi="Hastane", hizli1=60, hizli2=None, manuel_k=None,
                           manuel_V=1.6, taahhutname="Var"))
    r.kontrol("Hastane senaryosu taahhütname olmadan geçerli",
              TR.hesapla_tek(g(bina_tipi="Hastane", hizli1=60, hizli2=None, manuel_k=None,
                               manuel_V=1.6)).get("hata") is None)
    r.kontrol("şartlı sınırı olmayan tipte taahhütname → HESAP HATASI",
              "şartlı kabul sınırı yoktur" in (_th.get("hata") or ""))
    r.kontrol("okunamayan taahhütname → HESAP HATASI",
              "okunamadı" in (TR.hesapla_tek(dict(_kp, taahhutname="belki")).get("hata") or ""))
    #  Adedi kullanıcı belirliyorsa ( 2+ kolon ) taahhütname adede dokunmaz
    _t2 = TR.hesapla(dict(_kp, taahhutname="Var", asansorler=[
        {"P": 10, "kapi_genisligi": 800, "kapi_tipi": "Merkezden Açılan Oto."}] * 2))
    r.esit("2 kolonda taahhütname adede dokunmaz", _t2["ozet"]["adet"], 2)

    # ---------------------------------------------------- çoklu asansör
    c = dict(bina_tipi="Konut", bina_yuksekligi=39.98, yapi_yuksekligi=43, N=11,
             hizli1=44, hizli2=3, h=3,
             asansorler=[dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik"),
                         dict(P=16, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik")])
    s = TR.hesapla_coklu(c)
    r.kontrol("Reş = ΣR", abs(s["ozet"]["Res"] - sum(a["R"] for a in s["asansorler"])) < 1e-9)
    r.kontrol("1/TReş = Σ(1/TR)",
              abs(1 / s["ozet"]["TRes"] - sum(1 / a["TR"] for a in s["asansorler"])) < 1e-9)
    r.kontrol("TReş her TR'den küçük",
              all(s["ozet"]["TRes"] < a["TR"] for a in s["asansorler"]))
    r.kontrol("boş liste → uyarı",
              "en az bir" in (TR.hesapla_coklu(dict(c, asansorler=[])).get("hata") or ""))
    r.kontrol("geçersiz durak reddedilir",
              TR.hesapla_coklu(dict(c, asansorler=[
                  dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik", durak=99)
              ])).get("hata") is not None)
    r.kontrol("N grup maksimumu değilse uyarı",
              TR.hesapla_coklu(dict(c, asansorler=[
                  dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik", durak=5),
                  dict(P=16, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik", durak=6)
              ])).get("hata") is not None)
    #  v2.8 — KAPASİTE DENETİMİ İKİ YOLDA DA VAR.  Tek yol ( _dogrula_tek )
    #  P'yi Tablo-7'ye karşı aratıyordu, çoklu yol aratmıyordu:  P = 7 sessizce
    #  geçiyor, Q = 525 kg türetiliyor ve pafta kaynak olarak "Tablo-7" yazıyordu.
    r.kontrol("çoklu: Tablo-7 dışı kapasite reddedilir",
              "Tablo-7'de yoktur" in (TR.hesapla_coklu(dict(c, asansorler=[
                  dict(P=7, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik"),
                  dict(P=9, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik")
              ])).get("hata") or ""))
    r.kontrol("tek: Tablo-7 dışı kapasite reddedilir",
              TR.hesapla_tek(g(P=7)).get("hata") is not None)
    r.kontrol("çoklu: geçerli kapasiteler hâlâ geçiyor",
              TR.hesapla_coklu(dict(c, asansorler=[
                  dict(P=8, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik"),
                  dict(P=16, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik")
              ])).get("hata") is None)

    #  v2.8 — DURAK ALANI TEK YOLDA DA OKUNUYOR.  hesapla() asansör bazındaki
    #  alanları tek hesaba aktarırken `durak`ı atlıyordu:  çoklu yol aynı girdiyi
    #  reddederken tek yol alanı hiç görmüyor, kullanıcının yazdığı sayı hiçbir
    #  şeyi değiştirmiyordu ( N = 11 iken durak = 5 sessizce yok sayılıyordu ).
    def _dg(d):
        return TR.hesapla(dict(g(), asansorler=[
            dict(P=10, kapi_genisligi=900, kapi_tipi="Merkezden Açılan Oto.", durak=d)]))

    r.kontrol("tek: N ile çelişen durak reddedilir",
              "durak adedi" in (_dg(5).get("hata") or ""))
    r.kontrol("tek: aralık dışı durak reddedilir",
              "durak sayısı geçersiz" in (_dg(99).get("hata") or ""))
    r.kontrol("tek: N + 1 durak sorunsuz geçer", _dg(12).get("hata") is None)
    r.kontrol("tek: boş durak sorunsuz geçer", _dg(None).get("hata") is None)
    r.esit("tek: durak girilse de N değişmez", _dg(12)["ozet"]["N"], 11)

    #  v2.8 — FİZİKSEL OLARAK İMKÂNSIZ TÜREYEN DEĞERLER.
    #  Süreleri tek tek denetlemek yetmiyordu:  ta=tk=tg=tp=0,1 s ( izin verilen
    #  tam alt sınır ) her biri geçerliyken ts = −1,57 s üretiyor, TR 129→28 sn
    #  düşüyor ve 2 yerine 1 asansör yetiyor deniyordu.
    _sf = TR.hesapla_tek(g(manuel_ta=0.1, manuel_tk=0.1, manuel_tg=0.1, manuel_tp=0.1))
    r.kontrol("ts negatif çıkarsa hesap durur", "ts" in (_sf.get("hata") or ""),
              f"→ {_sf.get('hata')}")
    r.kontrol("makul elle süreler hâlâ geçiyor",
              TR.hesapla_tek(g(manuel_ta=2.5, manuel_tk=3.0)).get("hata") is None)
    #  Asansöre özel kat yüksekliği de ortak h ile aynı sınırlara tabidir
    #  ( h = −3 m ile −33 m seyahat mesafesi ve "kriter karşılanıyor" çıkıyordu ).
    for _h, _gecerli in ((-3, False), (0, False), (15, False), (2.8, True)):
        _c = TR.hesapla_coklu(dict(c, asansorler=[
            dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik", h=_h),
            dict(P=16, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik")]))
        r.kontrol(f"asansöre özel h={_h} {'kabul' if _gecerli else 'red'}",
                  (_c.get("hata") is None) == _gecerli, f"→ {_c.get('hata')}")

    #  v2.8 — BÖLGELİ HİZMET UYARISI.  Grup kontrolü bütün asansörlerin aynı
    #  talebe hizmet ettiğini varsayar; farklı katlara çıkıyorlarsa bu varsayım
    #  kırılır ve program bunu SÖYLEMİYORDU.
    _bz = TR.hesapla_coklu(dict(c, N=11, asansorler=[
        dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik", durak=12),
        dict(P=16, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik", durak=3)]))
    r.kontrol("farklı bölgede uyarı çıkıyor",
              any("FARKLI KATLARA" in u for u in _bz.get("uyarilar") or []))
    _ay = TR.hesapla_coklu(dict(c, asansorler=[
        dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik"),
        dict(P=16, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik")]))
    r.kontrol("aynı bölgede uyarı ÇIKMIYOR",
              not any("FARKLI KATLARA" in u for u in _ay.get("uyarilar") or []))

    #  v2.9 — ⑤/⑥ NEGATİF OLAMAZ.  Alt sınır yoktu:  ⑥ = −1 girilince bir
    #  dairedeki kişi 2 + (−1) = 1 oluyor, nüfus 500'den 100'e düşüyor ve
    #  gereken asansör 4'ten 2'ye iniyordu — hiçbir hata verilmeden.
    r.kontrol("tek: ⑥ negatif reddedilir",
              "negatif" in (TR.hesapla_tek(g(hizli1=100, hizli2=-1)).get("hata") or ""))
    r.kontrol("tek: ⑤ negatif reddedilir",
              "negatif" in (TR.hesapla_tek(g(hizli1=-5)).get("hata") or ""))
    r.kontrol("tek: ⑥ = 0 hâlâ geçerli",
              TR.hesapla_tek(g(hizli1=100, hizli2=0)).get("hata") is None)
    r.kontrol("çoklu: ⑤ negatif reddedilir",
              "negatif" in (TR.hesapla_coklu(dict(c, hizli1=-5)).get("hata") or ""))
    r.kontrol("olağandışı üst sınır korundu",
              "olağandışı" in (TR.hesapla_tek(g(hizli2=99)).get("hata") or ""))

    #  v2.9 — ÖNERİ TABLOSU GEÇERSİZ HESAPTA ÜRETİLMEZ.  Tablo kullanıcının
    #  kendi ta/tk/tg/tp değerlerini taban alır;  bunlar reddedilmişse ( ts < 0 )
    #  tablonun tamamı geçersiz tabana dayanır.  Ana hesap dururken tablo
    #  "uygun / önerilen" satırlar basmaya devam ediyordu.
    _bozuk = TR.hesapla_tek(g(manuel_ta=0.1, manuel_tk=0.1, manuel_tg=0.1))
    r.kontrol("hatalı hesapta öneri tablosu boş",
              bool(_bozuk.get("hata")) and not (_bozuk.get("oneriler") or []))
    r.kontrol("geçerli hesapta öneri tablosu dolu",
              len(TR.hesapla_tek(g()).get("oneriler") or []) > 0)

    #  v2.9 — ORTAK MANUEL HIZ ÇOKLUDA DA UYGULANIR.  Eskiden yalnız o asansörün
    #  Tablo-2 minimumu YOKSA devreye giriyordu:  arayüzde 2,50 m/s seçiliyken
    #  iki asansör de 1,60 m/s üzerinden hesaplanıyordu ( tekte çalışıyordu ).
    _mv = TR.hesapla_coklu(dict(c, manuel_V=2.5))
    r.kontrol("çoklu: ortak manuel V uygulanıyor",
              all(a["V"] == 2.5 for a in _mv.get("asansorler") or []),
              f"→ {[a['V'] for a in _mv.get('asansorler') or []]}")
    r.kontrol("çoklu: geçersiz ortak V reddedilir",
              "Manuel hız geçersiz" in (TR.hesapla_coklu(dict(c, manuel_V=9)).get("hata") or ""))
    _kv = TR.hesapla_coklu(dict(c, manuel_V=2.5, asansorler=[
        dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik", V=1.6),
        dict(P=16, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik")]))
    r.esit("asansörün kendi V'si ortak hızı ezer", _kv["asansorler"][0]["V"], 1.6)
    r.esit("kendi V'si olmayan ortak hızı alır", _kv["asansorler"][1]["V"], 2.5)

    tek1 = TR.hesapla_tek(g(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik"))
    cok1 = TR.hesapla_coklu(dict(c, asansorler=[dict(P=10, kapi_genisligi=900,
                                                     kapi_tipi="Teleskopik Otomatik")]))
    r.kontrol("tek ve çoklu aynı asansörde aynı TR'yi verir",
              abs(tek1["ozet"]["TR"] - cok1["asansorler"][0]["TR"]) < 1e-9)

    # ---------------------------------------------------- avan
    a = AV.hesapla({"ortak": ORT, "asansorler": [AS]})["asansorler"][0]["ozet"]
    r.kontrol("P = Gk + Gf", abs(a["P"] - (a["Gk"] + a["Gf"])) < 1e-9)
    r.kontrol("Ga = P + q·Q", abs(a["Ga"] - (a["P"] + 0.5 * a["Q"])) < 1e-9)
    r.kontrol("P1 10 N'a yuvarlanmış", a["P1"] % 10 == 0)
    r.kontrol("kurulu güç = kalemler toplamı",
              abs(a["P_kurulu"] - (a["g_motor"] + a["g_kuyu"] + a["g_kabin"] + a["g_priz"])) < 1e-9)
    r.kontrol("ε = ε1 + ε2", abs(a["eps"] - (a["eps1"] + a["eps2"])) < 1e-9)
    r.kontrol("kuyu armatürü = MAX(n1, n2)", a["n_kuyu"] == max(a["n1_kuyu"], a["n2_kuyu"]))

    #  v2.8 — MOTOR:  AĞIR ÇALIŞMA YÖNÜ.  Karşı ağırlık q·Q dengeler; dolu kabin
    #  yukarı ( 1−q )·Q, boş kabin aşağı q·Q dengesiz yük üretir.  Program yalnız
    #  ( 1−q ) yönünü hesaplıyordu:  q = 0,55'te 5,5 kW seçiyor, gereken 7,5 kW.
    #  q = 0,50'de iki yön eşittir — kitabın Q/2 formülüyle birebir aynı sonuç.
    def _mot(q_):
        return AV.hesapla_asansor(dict(kapasite=10, Q_elle=800, V=1, eta=0.85,
                                       i_palanga=2, q_denge=q_, Hk=20,
                                       kuyu_genisligi=1800, kabin_boyu=1400,
                                       kabin_genisligi=1100, makine_tipi="Dişlisiz"),
                                  {"mk_yok": True}, AV.sabitler(None), 1)["ozet"]
    #  2:1 askı:  η′ = 0,85 − 0,10 = 0,75  ( MMO/697 §2.4 )
    r.esit("q=0,50'de kitapla aynı ( Q/2 )", round(_mot(0.50)["N_hes"], 6),
           round(0.5 * 800 * 1 / (102 * 0.75), 6))
    for _q in (0.55, 0.60, 0.65):
        _o = _mot(_q)
        r.kontrol(f"q={_q}: ağır yön hesaplanıyor",
                  abs(_o["N_hes"] - _q * 800 / (102 * 0.75)) < 1e-9,
                  f"→ N={_o['N_hes']}")
    for _q in (0.40, 0.45, 0.50):
        _o = _mot(_q)
        r.kontrol(f"q={_q}: hafif yön değişmedi",
                  abs(_o["N_hes"] - (1 - _q) * 800 / (102 * 0.75)) < 1e-9)

    #  v2.8 — KABİN ALANI  ( MMO/697 Tablo-11 = TS EN 81-20, YOLCU asansörü ).
    #  DİKKAT:  kitapta Tablo-11'in hemen ardından Tablo-12 ( hidrolik YÜK
    #  asansörü ) gelir ve değerleri çok daha büyüktür ( 450 kg → 1,84 m² ).
    #  Yolcu asansöründe geçerli olan Tablo-11'dir:  450 kg → 1,30 m².
    r.esit("Tablo-11 450 kg", T.kabin_azami_alan(450), 1.30)
    r.esit("Tablo-11 630 kg", T.kabin_azami_alan(630), 1.66)
    r.esit("Tablo-11 1275 kg", T.kabin_azami_alan(1275), 2.95)
    r.esit("Tablo-11 2500 kg", T.kabin_azami_alan(2500), 5.00)
    r.esit("2500 kg üstü +0,16 m²/100 kg", round(T.kabin_azami_alan(3000), 4), 5.80)
    r.kontrol("Tablo-12 ( yük asansörü ) değeri KULLANILMIYOR",
              abs(T.kabin_azami_alan(450) - 1.84) > 0.4)

    def _kabin(P, en, boy):
        return [x for x in (AV.hesapla_asansor(
            dict(kapasite=P, V=1.6, eta=0.85, Hk=20, kuyu_genisligi=max(en, boy) + 400,
                 kabin_boyu=en, kabin_genisligi=boy, makine_tipi="Dişlisiz"),
            {"mk_yok": True}, AV.sabitler(None), 1).get("uyarilar") or [])
            if "KABİN ALANI" in x]
    #  TS EN 81-70 standart kabinleri yanlış alarm üretmemeli
    for _ad, _P, _a, _b in (("Tip 1", 6, 1000, 1250), ("Tip 2", 8, 1100, 1400),
                            ("Tip 3", 16, 2000, 1400)):
        r.kontrol(f"{_ad} kabini temiz geçiyor", not _kabin(_P, _a, _b))
    r.kontrol("aşırı kabin alanı uyarı üretiyor", bool(_kabin(6, 2000, 2000)))

    #  v2.8 — YANLIŞ KAYNAK GÖSTERİMİ.  MMO/697 trafik, kuvvet, motor gücü ve
    #  kabin boyutlarını kapsar;  AYDINLATMA / TOPRAKLAMA / GERİLİM DÜŞÜMÜ
    #  bölümleri kitapta YOKTUR.  Kitabın Tablo-4'ü kapı süreleri, Tablo-11'i
    #  ise beyan yükü ↔ kabin alanı tablosudur — boş kabin kütlesi vermez.
    #  Paftada bunlara "MMO/697 Tablo-4 / Tablo-11" demek yanlış atıftır.
    _oz = AV.hesapla_asansor(AS, ORT, AV.sabitler(None), 1)
    _gk = next(x for x in _oz["bolumler"][1]["adimlar"] if x.get("sembol") == "Gk")
    _ol = next(x for x in _oz["bolumler"][3]["adimlar"] if x.get("sembol") == "ØL")
    _eta = next(x for x in _oz["bolumler"][0]["adimlar"] if x.get("sembol") == "η")
    for _ad, _adim in (("Gk", _gk), ("ØL", _ol), ("η", _eta)):
        _k = str(_adim["kaynak"])
        r.kontrol(f"{_ad} kaynağı MMO tablosuna atfedilmiyor",
                  not any(x in _k for x in ("Tablo-4", "Tablo-11", "s.21")), f"→ {_k!r}")
    #  Kaynak metni hem OFİS tablosu olduğunu söylemeli hem de standart
    #  sayısı OLMADIĞINI açıkça yazmalı:  TS EN 81-20 / 81-50 boş kabin
    #  kütlesini hep GİRDİ olarak tanımlar, çizelge vermez.
    #  Kaynak sütununda "ofis" sözü GEÇMEZ ( kullanıcı kararı ):  ofisin
    #  kabulleri KABUL, katalogdan girilenler KATALOG diye yazılır.
    r.kontrol("Gk kaynağı kabul olduğunu ve standart sayısı olmadığını söylüyor",
              T.GK_KAYNAGI.startswith("KABUL")
              and "değildir" in T.GK_KAYNAGI
              and "fis" not in T.GK_KAYNAGI,
              f"→ {T.GK_KAYNAGI!r}")
    #  TABLO TEK KAYNAKTAN OKUNUR.  Avan ile uygulama aynı asansöre aynı
    #  kabin kütlesini vermelidir;  iki kopya tutulsaydı biri güncellenip
    #  öteki unutulurdu.
    from engine.ortak import ofis as _OF
    r.esit("Gk tablosu ortak dosyadan okunuyor",
           [tuple(x) for x in T.TABLO_11], [tuple(x) for x in _OF.GK_TABLOSU])
    for _q, _bek in ((450, 500), (630, 650), (800, 800), (1000, 950),
                     (1125, 1020), (1275, 1100), (1600, 1350), (2000, 1600),
                     (2500, 1900)):
        r.esit(f"Gk( {_q} kg )", T.tablo11_Gk(_q), _bek)
    r.esit("Gk ara değer  ( 700 kg )", T.tablo11_Gk(700), 710)
    r.esit("Gk tablo altında uç değere sabitlenir", T.tablo11_Gk(225), 500)
    r.esit("Gk tablo üstünde uç değere sabitlenir", T.tablo11_Gk(5000), 1900)

    #  v2.8 — ARMATÜR IŞIK AKISI TABLO-4'TEN GELİR VE KAYNAĞI PAFTADA YAZAR.
    #  Kuyu / makine dairesi varsayılanı eskiden kaynağı belirsiz 2600 lm idi
    #  ( Tablo-4: 40 W flüoresan = 2100 lm ) ve pafta ØL satırına yalnız
    #  "SABİTLER B" yazdığı için tablodan sapıldığı GÖRÜNMÜYORDU.  2600 daha az
    #  armatür verir, yani emniyetsiz taraftır.
    _t4 = {(t, w): lm for t, w, lm in T.ARMATUR_ISIK_AKISI}
    r.esit("kuyu ØL varsayılanı Tablo-4'ten",
           AV.SABIT_B_VARSAYILAN["kuyu_armatur_lm"], int(_t4[("Flüoresan", "40 W")]))
    r.esit("kabin ØL varsayılanı Tablo-4'ten",
           AV.SABIT_B_VARSAYILAN["kabin_armatur_lm"], int(_t4[("LED spot", "5 W")]))

    def _ol_kaynagi(sabit, bolum):
        S_ = AV.sabitler(sabit)
        if bolum == "mk":
            #  ORT makine dairesiz ( MRL ) — bu kontrol için ölçü verilir
            b = AV.hesapla_makine_dairesi(
                dict(ORT, mk_uzunluk=3000, mk_genislik=2500), S_)["bolum"]
        else:
            b = AV.hesapla_asansor(AS, ORT, S_, 1)["bolumler"][bolum]
        return next(x for x in b["adimlar"] if x.get("sembol") == "ØL")["kaynak"]

    #  MAKİNE DAİRESİNDE ÇALIŞMA DÜZLEMİ DÖŞEMEDİR  ( TS EN 81-20 m.5.2.1.4.2 )
    #  200 lüks döşeme seviyesinde istenir;  armatür tavandadır ve net yükseklik
    #  en az 2,10 m'dir ( m.5.2.6.3.2.1 ).  Kabinin 1,0 m'lik düzlemi ( m.5.4.10.1:
    #  döşemeden 1 m yukarıda 100 lüks ) buraya da uygulanıyordu:  k iki kat,
    #  η büyük, armatür %20-30 az.
    _Sd = AV.sabitler(None)
    _mk = AV.hesapla_makine_dairesi(dict(ORT, mk_yok=False, mk_uzunluk=4000,
                                         mk_genislik=3000), _Sd)
    r.esit("makine dairesi: h = döşemeden armatüre 2,10 m",
           next(x for x in _mk["bolum"]["adimlar"] if x.get("sembol") == "h")["deger"], 2.10)
    r.esit("makine dairesi: k = a·b / ( 2,10 · ( a + b ) )", _mk["k"], 4 * 3 / (2.10 * 7))
    r.esit("makine dairesi 4 × 3 m → 5 armatür  ( h = 1 m ile 4 çıkıyordu )", _mk["n"], 5)
    r.esit("kabin: h = 1,0 m  ( döşemeden 1 m yukarıda ölçülür )",
           next(x for x in AV.hesapla_asansor(AS, ORT, _Sd, 1)["bolumler"][2]["adimlar"]
                if x.get("sembol") == "h")["deger"], 1.0)

    #  KAYNAK "MMO/697 Tablo-4" DEĞİLDİR:  kitapta aydınlatma bölümü yoktur ve
    #  Tablo-4 kapı süreleri tablosudur.  Varsayılan ofis armatür tablosundan gelir.
    for bolum, ad in ((2, "kabin"), (3, "kuyu"), ("mk", "mk.dairesi")):
        _k = _ol_kaynagi(None, bolum)
        r.kontrol(f"{ad}: varsayılan ØL kaynağı armatür tablosu diyor",
                  _k.startswith("KABUL") and "armatür tablosu" in _k
                  and "Tablo-4" not in _k, f"→ {_k!r}")
    for bolum, ad in ((3, "kuyu"), ("mk", "mk.dairesi")):
        r.kontrol(f"{ad}: elle girilen ØL kaynağı KATALOG diyor",
                  "KATALOG" in _ol_kaynagi({"kuyu_armatur_lm": 2600}, bolum))
    r.kontrol("elle girilen armatür GÜCÜ de kaynağı değiştirir",
              "KATALOG" in _ol_kaynagi({"kuyu_armatur_W": 58}, 3))
    r.kontrol("sabitler() kabul edilen ezmeyi kaydediyor",
              "kuyu_armatur_lm" in AV.sabitler({"kuyu_armatur_lm": 2600})["_ozel"])
    r.kontrol("reddedilen ezme _ozel'e girmiyor",
              "kuyu_armatur_lm" not in AV.sabitler({"kuyu_armatur_lm": 0})["_ozel"])
    for V, k1 in ((0.5, 5), (0.63, 5), (0.7, 3), (1.0, 3), (1.01, 2), (2.5, 2)):
        r.esit(f"k1 (V={V})", AV.hesapla({"ortak": ORT, "asansorler": [dict(AS, V=V)]}
                                         )["asansorler"][0]["ozet"]["k1"], k1)
    r.esit("palanga i=1 → η aynen  ( 1:1 askıda düşüş yok )",
           AV.hesapla({"ortak": ORT, "asansorler": [AS], "sabitler": {"i_palanga": 1}}
                      )["asansorler"][0]["ozet"]["eta_p"], 0.85)
    r.esit("palanga i=2 → η′ = η − 0,10  ( MMO/697 §2.4 )",
           AV.hesapla({"ortak": ORT, "asansorler": [AS]})["asansorler"][0]["ozet"]["eta_p"], 0.75)
    r.kontrol("Dmax=0 → geometrik kontrol kapalı",
              AV.hesapla({"ortak": ORT, "asansorler": [AS], "sabitler": {"kuyu_Dmax": 0}}
                         )["asansorler"][0]["ozet"]["n2_kuyu"] == 0)
    r.kontrol("tanımsız asansör pasif",
              AV.hesapla({"ortak": ORT, "asansorler": [dict(AS, kapasite=None)]}
                         )["asansorler"][0]["aktif"] is False)
    r.kontrol("Q elle ile Tablo-7 dışı kapasite çalışır",
              AV.hesapla({"ortak": ORT, "asansorler": [dict(AS, kapasite=None, Q_elle=1125)]}
                         )["asansorler"][0]["ozet"]["Q"] == 1125)
    r.kontrol("Gk elle Tablo-11'i geçersiz kılar",
              AV.hesapla({"ortak": ORT, "asansorler": [dict(AS, Gk_elle=740)]}
                         )["asansorler"][0]["ozet"]["Gk"] == 740)
    #  SINIR DIŞI DEĞERLE HESAP YAPILMAZ.  L1 = 600 m ya da Nsç = 600 kW
    #  önce hesaba giriyordu ( uyarı "varsayılan kullanıldı" diyerek yalan
    #  söylüyordu ), sonra varsayılanla değiştirildi.  İkisi de kullanıcının
    #  yazmadığı bir sayıyla pafta üretiyordu:  artık asansör DURUR ve hangi
    #  alanın neden reddedildiği söylenir.
    for _ad6, _ek6, _parca in (("L1 = 600 m", {"L1": 600}, "L1 — kolon hattı uzunluğu"),
                               ("Nsç = 600 kW", {"Nsc": 600}, "Nsç — seçilen motor gücü")):
        _a6 = AV.hesapla({"ortak": ORT, "asansorler": [dict(AS, **_ek6)]})["asansorler"][0]
        r.kontrol(f"{_ad6}: aralık dışı değerle hesap yapılmıyor", _a6["aktif"] is False)
        r.kontrol(f"{_ad6}: sebep alanı ve aralığı söylüyor",
                  _parca in (_a6.get("uyari") or "")
                  and "geçerli aralık" in (_a6.get("uyari") or ""),
                  f"→ {_a6.get('uyari')!r}")
    r.esit("L1 geçerliyse kullanılıyor",
           AV.hesapla({"ortak": ORT, "asansorler": [dict(AS, L1=45)]}
                      )["asansorler"][0]["ozet"]["L1"], 45)
    #  Birden çok hatalı alan TEK SEFERDE söylenir
    _a6 = AV.hesapla({"ortak": ORT, "asansorler": [dict(AS, L1=600, Nsc=600, S1=0.5)]}
                     )["asansorler"][0]
    r.kontrol("üç hatalı alan tek uyarıda sayılıyor",
              all(x in (_a6.get("uyari") or "") for x in ("L1 —", "Nsç —", "S1 —")),
              f"→ {_a6.get('uyari')!r}")

    r.kontrol("motor yetersizse UYGUN DEĞİL",
              AV.hesapla({"ortak": ORT, "asansorler": [dict(AS, Nsc=5)]}
                         )["asansorler"][0]["ozet"]["motor_uygun"] is False)
    kesit = AV.hesapla({"ortak": ORT, "asansorler": [dict(AS, S1=1.5, L1=200)]}
                       )["asansorler"][0]["ozet"]
    r.kontrol("kesit yetersizse ε ve I uyarır", not kesit["eps_uygun"] and not kesit["akim_uygun"])
    #  TABLO DIŞI KESİT  ( v2.2 )
    #  Iz kesitle birlikte arttığı için, tabloda bulunmayan bir kesitte
    #  ondan küçük en büyük tablo satırı GÜVENLİ ALT SINIRDIR.  Eskiden
    #  Iz = None dönüyordu ve pafta 150 mm² gibi standart bir kesitte bile
    #  "UYGUN DEĞİLDİR — kesiti büyütün" diyordu ( büyütmek işe yaramıyordu ).
    def _kesit(s1):
        return AV.hesapla({"ortak": ORT, "asansorler": [dict(AS, S1=s1)]})["asansorler"][0]

    r.esit("tablo dışı kesit ( 3 mm² ) → bir küçük satırın değeri",
           _kesit(3)["ozet"]["Iz"], T.KABLO_IZ[2.5])
    r.esit("tablonun üstündeki kesit ( 150 mm² ) → en büyük tablo değeri",
           _kesit(150)["ozet"]["Iz"], T.KABLO_IZ[120])
    r.kontrol("150 mm² kesitte akım kontrolü UYGUN çıkıyor",
              _kesit(150)["ozet"]["akim_uygun"] is True)
    r.kontrol("tablo dışı kesit uyarı üretiyor",
              any("akım tablosunda BULUNMUYOR" in x
                  for x in (_kesit(150).get("uyarilar") or [])))
    r.kontrol("paftada Iz alt sınır olarak yazılıyor",
              any(a.get("sembol") == "Iz" and str(a.get("metin", "")).startswith("≥")
                  for a in _kesit(150)["bolumler"][5]["adimlar"]))
    r.esit("tablodaki kesitte Iz kesin değer", _kesit(6)["ozet"]["Iz"], T.KABLO_IZ[6])
    r.kontrol("tablodaki kesitte '≥' işareti yok",
              not any(a.get("sembol") == "Iz" and str(a.get("metin", "")).startswith("≥")
                      for a in _kesit(6)["bolumler"][5]["adimlar"]))
    r.kontrol("tablonun altındaki kesit ( 1 mm² ) → kontrol edilemedi",
              _kesit(1)["ozet"]["Iz"] is None
              and "KONTROL EDİLEMEDİ" in _kesit(1)["bolumler"][5]["sonuc"]["alt"][1])

    #  η FİZİKSEL OLMALI.  η'nın KENDİ aralığı ( 0,05 - 1,00 ) dışı hesabı
    #  durdurur.  Palangalı sistemde kitabın düşüşünden ( η′ = η − 0,10,
    #  MMO/697 §2.4 ) sonra da verim sıfırın üstünde kalmalıdır:  η = 0,08 ·
    #  2:1 → η′ = −0,02 paftaya negatif verim basar, N eksi çıkar.  Aralık
    #  içindeki bu değer de hesabı durdurur, sessizce kullanılmaz.
    def _verim(eta, i=2, **kw):
        return AV.hesapla({"ortak": ORT,
                           "asansorler": [dict(AS, eta=eta, i_palanga=i, **kw)]}
                          )["asansorler"][0]

    for _eta in (0.04, 0, -0.10, 1.5):
        _h = _verim(_eta)
        r.kontrol(f"η = {_eta} → hesap duruyor", _h["aktif"] is False,
                  f"→ {_h.get('uyari')}")
    for _eta in (0.05, 0.08, 0.10):
        _h = _verim(_eta)
        r.kontrol(f"η = {_eta} + 2:1 askı → η′ ≤ 0, hesap duruyor",
                  _h["aktif"] is False and "MMO/697 §2.4" in (_h.get("uyari") or ""),
                  f"→ {_h.get('uyari')}")
        _h1 = _verim(_eta, i=1)
        r.kontrol(f"η = {_eta} + 1:1 askı → hesaplanıyor ( düşüş yok )",
                  _h1["aktif"] is True and _h1["ozet"]["eta_p"] == _eta,
                  f"→ {_h1.get('uyari')}")
    for _eta, _bek in ((0.20, 0.10), (0.85, 0.75), (1.0, 0.90)):
        _h = _verim(_eta)
        r.kontrol(f"η = {_eta} + 2:1 askı → η′ = {_bek}",
                  _h["aktif"] is True and _h["ozet"]["eta_p"] == _bek,
                  f"→ {_h.get('uyari') or _h['ozet']['eta_p']}")
    r.kontrol("Nsç elle girilmişken de aralık dışı η durduruyor",
              _verim(0.04, Nsc=11)["aktif"] is False)
    r.kontrol("Nsç elle girilmişken de η′ ≤ 0 durduruyor",
              _verim(0.08, Nsc=11)["aktif"] is False)

    # topraklama
    t = AV.hesapla({"ortak": ORT, "asansorler": [AS]})["topraklama"]
    r.kontrol("Re paralel bağıntısı",
              abs(t["Re"] - t["Ry"] * t["Rc"] / (t["Ry"] + t["Rc"])) < 1e-9)
    r.kontrol("Re < Ry ve Re < Rç", t["Re"] < t["Ry"] and t["Re"] < t["Rc"])
    t0 = AV.hesapla({"ortak": dict(ORT, cubuk_sayisi=0), "asansorler": [AS]})["topraklama"]
    r.kontrol("çubuk yoksa Re = Ry", abs(t0["Re"] - t0["Ry"]) < 1e-9 and t0["Rc"] is None)
    r.kontrol("temel ölçüsü eksikse pasif",
              AV.hesapla({"ortak": dict(ORT, temel_a=0), "asansorler": [AS]}
                         )["topraklama"]["aktif"] is False)
    r.esit("Re max = UL / IΔn", t["Re_max"], 50 / 0.3)

    # makine dairesi
    r.kontrol("MRL sistemde makine dairesi hesabı yok",
              AV.hesapla({"ortak": ORT, "asansorler": [AS]})["makine_dairesi"]["aktif"] is False)
    mk = AV.hesapla({"ortak": dict(ORT, mk_uzunluk=4200, mk_genislik=3100),
                     "asansorler": [AS]})["makine_dairesi"]
    r.kontrol("makine daireli sistemde hesap yapılır", mk["aktif"] and mk["n"] >= 1)

    # 4 asansör + tesis toplamı
    dort = AV.hesapla({"ortak": ORT, "asansorler": [AS] * 4})
    r.esit("4 asansör aktif", len([x for x in dort["asansorler"] if x["aktif"]]), 4)
    r.kontrol("tesis kurulu gücü = Σ asansör",
              abs(dort["ozet"]["tesis_kurulu_guc"]
                  - sum(x["ozet"]["P_kurulu"] for x in dort["asansorler"] if x["aktif"])) < 1e-9)

    # ---------------------------------------------------- belirlenimcilik
    a1 = TR.hesapla_tek(g())["ozet"]
    a2 = TR.hesapla_tek(g())["ozet"]
    r.kontrol("aynı girdi → aynı sonuç (trafik)", a1 == a2)
    b1 = AV.hesapla({"ortak": ORT, "asansorler": [AS]})["asansorler"][0]["ozet"]
    b2 = AV.hesapla({"ortak": ORT, "asansorler": [AS]})["asansorler"][0]["ozet"]
    r.kontrol("aynı girdi → aynı sonuç (avan)", b1 == b2)

    # ============================================================
    #  ÇOKLU : asansör bazında bodrum ve imalatçı süreleri
    # ============================================================
    def gc(**kw):
        temel = dict(bina_tipi="Konut", bina_yuksekligi=39.98, yapi_yuksekligi=43,
                     N=11, hizli1=44, hizli2=3, h=3)
        asan = kw.pop("asansorler", None) or [
            dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik"),
            dict(P=16, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik")]
        temel.update(kw)
        temel["asansorler"] = asan
        return temel

    c0 = TR.hesapla_coklu(gc())
    r.kontrol("çoklu temel senaryo hatasız", c0.get("hata") is None)
    r.esit("çoklu ortak durak = N+1", c0["ozet"]["durak"], 12)
    c1 = TR.hesapla_coklu(gc(bodrum=3))
    r.esit("çoklu ortak bodrum durak adedine girer", c1["asansorler"][0]["durak_toplam"], 15)
    r.esit("çoklu bodrum H'yi değiştirmez", c1["asansorler"][0]["H"], c0["asansorler"][0]["H"])
    r.esit("çoklu bodrum S'yi değiştirmez", c1["asansorler"][0]["S"], c0["asansorler"][0]["S"])
    c2 = TR.hesapla_coklu(gc(bodrum=1, asansorler=[
        dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik"),
        dict(P=16, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik", bodrum=4)]))
    r.esit("A1 ortak bodrumu alır", c2["asansorler"][0]["bodrum"], 1)
    r.esit("A2 kendi bodrumunu alır", c2["asansorler"][1]["bodrum"], 4)
    r.esit("A1 durak toplam", c2["asansorler"][0]["durak_toplam"], 13)
    r.esit("A2 durak toplam", c2["asansorler"][1]["durak_toplam"], 16)
    r.kontrol("çoklu geçersiz bodrum reddedilir",
              "bodrum" in (TR.hesapla_coklu(gc(asansorler=[
                  dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik",
                       bodrum=99)])).get("hata") or ""))
    c3 = TR.hesapla_coklu(gc(asansorler=[
        dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik",
             manuel_ta=2.9, manuel_tk=3.4, manuel_tg=6.2, manuel_tp=1.15)]))
    a3 = c3["asansorler"][0]
    r.esit("çoklu manuel ta", a3["ta"], 2.9)
    r.esit("çoklu manuel tk", a3["tk"], 3.4)
    r.esit("çoklu manuel tg", a3["tg"], 6.2)
    r.esit("çoklu manuel tp", a3["tp"], 1.15)
    r.esit("çoklu manuel sayısı", a3["elle_sure"], 4)
    r.esit("çoklu manuel kaynağı", a3["kaynak_ta"], "İmalatçı verisi")
    r.kontrol("çoklu manuel süre uyarısı",
              any("imalatçı verisiyle" in u for u in c3["uyarilar"]))
    r.kontrol("çoklu kabin içi 1300 → elle süreyle geçer",
              TR.hesapla_coklu(gc(asansorler=[
                  dict(P=10, kapi_genisligi=1300, kapi_tipi="Kabin İçi Oto. Kat K.Ç.",
                       manuel_ta=6.0, manuel_tk=6.0)])).get("hata") is None)
    r.kontrol("çoklu 6 kişi erişilebilirlik uyarısı",
              any("81-70" in u for u in TR.hesapla_coklu(gc(asansorler=[
                  dict(P=6, kapi_genisligi=800, kapi_tipi="Teleskopik Otomatik")]))["uyarilar"]))
    kamuc = TR.hesapla_coklu(gc(bina_tipi="Kamu Binaları"))
    r.kontrol("çoklu kamu varsayımları paftada",
              sum(1 for u in kamuc["uyarilar"] if "Kamu" in u) >= 2)

    # ============================================================
    #  AVAN : asansör bazında palanga ve denge faktörü
    # ============================================================
    ORTAK_Y = {"U": 380, "kappa": 56, "eps_max": 3, "temel_a": 26.55, "temel_b": 16.4,
               "beta": 150, "serit_L": 58.5, "cubuk_sayisi": 4,
               "mk_uzunluk": 0, "mk_genislik": 0}
    TEMEL_AS = dict(tanim="İnsan", kapasite=13, V=1.6, eta=0.85, Hk=32.85,
                    kuyu_genisligi=1800, kabin_boyu=1450, kabin_genisligi=1300,
                    gr=17.91, Fmk=350, Fsh=100, Nsc=11, S1=6, L1=32.85, S2=6, L2=3,
                    kablo_tipi="NHXMH")

    def av(*asan, **kw):
        return AV.hesapla({"ortak": ORTAK_Y, "asansorler": list(asan), **kw})

    v0 = av(dict(TEMEL_AS))
    v1 = av(dict(TEMEL_AS, i_palanga=1))
    o0, o1 = v0["asansorler"][0]["ozet"], v1["asansorler"][0]["ozet"]
    r.esit("palanga 2 → η′ = η − 0,10  ( MMO/697 §2.4 )", o0["eta_p"], 0.75)
    r.esit("palanga 1 → η aynen", o1["eta_p"], 0.85)
    r.esit("askı oranı motor gücüne yalnız verimden giriyor",
           o0["N_hes"], o1["N_hes"] * 0.85 / 0.75, tol=1e-9)
    v2 = av(dict(TEMEL_AS, q_denge=0.45))
    o2 = v2["asansorler"][0]["ozet"]
    r.esit("asansör bazında q kullanılır", o2["Ga"], o2["P"] + 0.45 * o2["Q"])
    r.esit("varsayılan q kullanılır", o0["Ga"], o0["P"] + 0.50 * o0["Q"])
    v3 = av(dict(TEMEL_AS), dict(TEMEL_AS, eta=0.50, i_palanga=1, q_denge=0.40))
    x, y = v3["asansorler"][0]["ozet"], v3["asansorler"][1]["ozet"]
    r.esit("karışık projede A1 η′  ( 2:1 )", x["eta_p"], 0.75)
    r.esit("karışık projede A2 η  ( 1:1 )", y["eta_p"], 0.50)
    r.esit("karışık projede A2 Ga", y["Ga"], y["P"] + 0.40 * y["Q"])
    #  Geçersiz askı oranı ve q varsayılanla DEĞİŞTİRİLMEZ, asansör durur;
    #  yan yana duran geçerli asansör hesaplanmaya devam eder.
    v4 = av(dict(TEMEL_AS, i_palanga=9, q_denge=5), dict(TEMEL_AS))
    a4 = v4["asansorler"][0]
    r.kontrol("geçersiz palanga ve q ile hesap yapılmıyor", a4["aktif"] is False)
    r.kontrol("ikisi de tek uyarıda söyleniyor",
              "i — askı oranı" in a4.get("uyari", "")
              and "q — denge faktörü" in a4.get("uyari", ""), f"→ {a4.get('uyari')!r}")
    r.kontrol("bir asansörün hatası ötekini durdurmuyor",
              v4["asansorler"][1]["aktif"] is True)
    r.esit("i kaynağı — asansör bazı", v1["asansorler"][0]["ozet"]["i_kaynak"],
           "GİRİŞ — asansör bazında")
    r.esit("i kaynağı — ofis kabulü", o0["i_kaynak"], "KABUL")
    r.esit("q kaynağı — asansör bazı", o2["q_kaynak"], "GİRİŞ — asansör bazında")
    v5 = AV.hesapla({"ortak": ORTAK_Y, "sabitler": {"q_denge": 0.42},
                     "asansorler": [dict(TEMEL_AS), dict(TEMEL_AS, q_denge=0.55)]})
    aa, bb = v5["asansorler"][0]["ozet"], v5["asansorler"][1]["ozet"]
    r.esit("ofis standardı boş kolona uygulanır", aa["Ga"], aa["P"] + 0.42 * aa["Q"])
    r.esit("asansör bazı ofis standardını ezer", bb["Ga"], bb["P"] + 0.55 * bb["Q"])

    # ============================================================
    #  TRAFİK  →  AVAN  tutarlılık köprüsü
    # ============================================================
    t = TR.hesapla_tek(g(N=13, h=3, P=13, manuel_V=1.6))
    kopru = TR.trafik_ozeti(t)
    n_as = len(kopru["asansorler"])
    r.kontrol("köprü asansör listesi doluyor", n_as >= 1)
    r.esit("köprü kapasitesi", kopru["asansorler"][0]["P"], 13)
    r.esit("köprü seyahati", kopru["asansorler"][0]["toplam_seyahat"], 39)

    def kopru_uyari(**kw):
        return av(*[dict(TEMEL_AS, **kw) for _ in range(n_as)], trafik=kopru)["uyarilar"]

    r.kontrol("tutarlı girdide köprü uyarısı yok",
              not any("NOLU ASANSÖR:" in u for u in kopru_uyari(Hk=44.5)))
    r.kontrol("kapasite tutarsızlığı yakalanır",
              any("kapasite" in u for u in kopru_uyari(kapasite=10, Hk=44.5)))
    r.kontrol("hız tutarsızlığı yakalanır",
              any("kabin hızı" in u for u in kopru_uyari(V=2.5, Hk=44.5)))
    r.kontrol("Hk < seyahat yakalanır",
              any("küçük ya da ona eşit" in u for u in kopru_uyari(Hk=30)))
    r.kontrol("dar pay uyarısı",
              any("kuyu dibi + üst boşluk payı yalnız" in u for u in kopru_uyari(Hk=41)))
    r.kontrol("aşırı pay uyarısı",
              any("olağandışı büyük" in u for u in kopru_uyari(Hk=60)))
    r.kontrol("adet uyuşmazlığı yakalanır",
              any("adet asansör veriyor" in u for u in
                  av(dict(TEMEL_AS, Hk=44.5),
                     trafik={"asansorler": [{"P": 13, "V": 1.6}, {"P": 13, "V": 1.6}]})["uyarilar"]))
    r.kontrol("köprü yoksa uyarı da yok",
              not any("NOLU ASANSÖR:" in u for u in av(dict(TEMEL_AS))["uyarilar"]))
    for bozuk in (None, "metin", 5, [], {"asansorler": "x"}):
        r.kontrol(f"bozuk köprü {bozuk!r} çökmez",
                  isinstance(av(dict(TEMEL_AS), trafik=bozuk).get("uyarilar"), list))

    # ============================================================
    #  MAKİNE TİPİ × ASKI ORANI  ve  TOPLAM SİSTEM VERİMİ
    # ============================================================
    #  MMO/697 s.21: dişlisiz 0,85 · dişli 0,50   —   §2.4: palangalı η − 0,10
    r.esit("MMO makine verimi — dişlisiz", T.makine_verimi("Dişlisiz"), 0.85)
    r.esit("MMO makine verimi — dişli", T.makine_verimi("Dişli"), 0.50)
    r.kontrol("tanınmayan makine tipi None", T.makine_verimi("Hidrolik") is None)
    r.esit("askı metni 1", T.aski_orani_metni(1), "1:1")
    r.esit("askı metni 2", T.aski_orani_metni(2), "2:1")

    def eta_p(**kw):
        return av(dict(TEMEL_AS, **kw))["asansorler"][0]["ozet"]["eta_p"]

    #  η MAKİNE VERİMİDİR ( kitabın η'sı ):  palangalı sistemde 0,10 düşer.
    for tip, i, bek in (("Dişli", 1, 0.50), ("Dişli", 2, 0.40),
                        ("Dişlisiz", 1, 0.85), ("Dişlisiz", 2, 0.75)):
        r.esit(f"{tip} {T.aski_orani_metni(i)} → η′",
               eta_p(makine_tipi=tip, eta=T.makine_verimi(tip), i_palanga=i), bek)
    #  Askı oranı motor gücüne YALNIZ verim üzerinden girer
    n11 = av(dict(TEMEL_AS, makine_tipi="Dişlisiz", eta=0.85,
                  i_palanga=1))["asansorler"][0]["ozet"]["N_hes"]
    n21 = av(dict(TEMEL_AS, makine_tipi="Dişlisiz", eta=0.85,
                  i_palanga=2))["asansorler"][0]["ozet"]["N_hes"]
    r.esit("askı oranı motor gücüne yalnız verimden giriyor", n21, n11 * 0.85 / 0.75,
           tol=1e-12)

    #  KİTABIN ÇÖZÜMLÜ ÖRNEĞİ BİREBİR  ( MMO/697 §4.4, s.56 ):
    #    1125 kg · 1,6 m/s · 2:1 · η 0,5 → η = 0,5 − 0,1 = 0,4 → N1 = 22 kW
    #     450 kg · 1,6 m/s · 1:1 · η 0,5                       → N2 = 7,05 kW
    _k1 = av(dict(TEMEL_AS, Q_elle=1125, V=1.6, eta=0.5, i_palanga=2,
                  makine_tipi="Dişli"))["asansorler"][0]["ozet"]
    _k2 = av(dict(TEMEL_AS, Q_elle=450, V=1.6, eta=0.5, i_palanga=1,
                  makine_tipi="Dişli"))["asansorler"][0]["ozet"]
    r.esit("kitap örneği N1:  η = 0,5 − 0,1 = 0,4", _k1["eta_p"], 0.4)
    r.esit("kitap örneği N1 = (1/0,4)·(1125·1,6)/(2·102)", _k1["N_hes"],
           (1 / 0.4) * (1125 * 1.6) / (2 * 102))
    r.kontrol("kitap örneği N1 ≈ 22 kW", abs(_k1["N_hes"] - 22) < 0.1, f"→ {_k1['N_hes']}")
    r.esit("kitap örneği N2 = (1/0,5)·(450·1,6)/(2·102)  ( 7,05 kW )", _k2["N_hes"],
           (1 / 0.5) * (450 * 1.6) / (2 * 102))

    #  Girilen η kitabın η'sıdır:  palangalı sistemde yalnız 0,10 düşer
    r.esit("η = 0,82 · 2:1 → η′ = 0,72",
           eta_p(makine_tipi="Dişlisiz", eta=0.82, i_palanga=2), 0.72)
    r.esit("η = 0,60 · 1:1 → aynen 0,60",
           eta_p(makine_tipi="Dişli", eta=0.60, i_palanga=1), 0.60)
    for _eski in ("Hayır", "Evet"):
        r.kontrol(f"kaldırılan 'toplam_verim' anahtarı ( {_eski} ) hesabı ETKİLEMİYOR",
                  eta_p(makine_tipi="Dişlisiz", eta=0.82, i_palanga=2,
                        toplam_verim=_eski) == 0.72,
                  "→ eski projelerden gelen anahtar hâlâ okunuyor")
    #  Düşüşü YALNIZ uygulama köprüsünün bayrağı kapatır ( η orada toplamdır )
    r.esit("köprü bayrağı ( η toplam ) → düşüş yok",
           eta_p(makine_tipi="Dişlisiz", eta=0.82, i_palanga=2,
                 **{T.ETA_TOPLAM_ANAHTARI: True}), 0.82)
    #  Pafta satırları ve notlar
    v_t = av(dict(TEMEL_AS, makine_tipi="Dişlisiz", eta=0.82,
                  i_palanga=2))["asansorler"][0]["bolumler"][0]
    v_1 = av(dict(TEMEL_AS, makine_tipi="Dişlisiz", eta=0.82,
                  i_palanga=1))["asansorler"][0]["bolumler"][0]

    def _eta_satiri(b):
        return [a for a in b["adimlar"] if str(a.get("formul") or "").startswith("η′")]
    r.kontrol("2:1 → paftada η′ = η − 0,10 satırı, kaynağı MMO/697 §2.4",
              len(_eta_satiri(v_t)) == 1 and "MMO/697 §2.4" in _eta_satiri(v_t)[0]["kaynak"])
    r.kontrol("1:1 → η′ satırı yok", not _eta_satiri(v_1))
    r.kontrol("makine verimi notu paftada",
              any("η makine verimidir" in n for n in v_t["notlar"]))
    r.kontrol("paftada kitaptan sapma notu KALMADI",
              not any("uygulanmaz" in n for n in v_t["notlar"] + v_t["aciklamalar"]),
              f"→ {v_t['notlar']}")
    r.kontrol("askı oranı açıklaması ( ! ) balonunda",
              any("MMO/697 §2.4" in n for n in v_t["aciklamalar"]))
    v_s = av(dict(TEMEL_AS, makine_tipi="Dişli", eta=0.70,
                  i_palanga=1))["asansorler"][0]["bolumler"][0]
    r.kontrol("MMO değerinden sapma bildiriliyor",
              any("farklı girilmiştir" in n for n in v_s["notlar"]))
    v_n = av(dict(TEMEL_AS, makine_tipi="Dişli", eta=0.50,
                  i_palanga=1))["asansorler"][0]["bolumler"][0]
    r.kontrol("MMO değeri kullanılınca sapma notu yok",
              not any("farklı girilmiştir" in n for n in v_n["notlar"]))
    #  Askı oranı özette metin olarak da bulunmalı
    r.esit("özette askı metni",
           av(dict(TEMEL_AS, i_palanga=2))["asansorler"][0]["ozet"]["aski"], "2:1")

    # ============================================================
    #  MAKİNE DAİRESİ YOK ( MRL ) İŞARET KUTUSU
    # ============================================================
    def mk(**kw):
        return AV.hesapla({"ortak": dict(ORTAK_Y, **kw),
                           "asansorler": [dict(TEMEL_AS)]})["makine_dairesi"]

    r.kontrol("MRL işaretli → hesap yapılmaz", mk(mk_yok=True)["aktif"] is False)
    r.kontrol("MRL işaretli → açık ifade", "işaretlendi" in mk(mk_yok=True)["uyari"])
    r.kontrol("MRL işaretli, ölçü olsa da hesaplanmaz",
              mk(mk_yok=True, mk_uzunluk=4200, mk_genislik=3100)["aktif"] is False)
    r.kontrol("MRL değil + ölçü var → hesaplanır",
              mk(mk_yok=False, mk_uzunluk=4200, mk_genislik=3100)["aktif"] is True)
    r.kontrol("MRL değil + ölçü yok → açık uyarı",
              "ÖLÇÜLERİ GİRİLMEDİ" in (mk(mk_yok=False).get("uyari") or ""))
    #  Kutu hiç gönderilmemişse ESKİ davranış korunur ( eski proje dosyaları )
    r.kontrol("kutu yokken ölçüsüz → MRL kabul edilir", mk()["aktif"] is False)
    r.kontrol("kutu yokken ölçü varsa → hesaplanır",
              mk(mk_uzunluk=4200, mk_genislik=3100)["aktif"] is True)
    for ham in ("Evet", "evet", True, "1"):
        r.kontrol(f"MRL {ham!r} doğru okundu", mk(mk_yok=ham)["aktif"] is False)
    for ham in ("Hayır", "hayir", False, ""):
        r.kontrol(f"MRL {ham!r} → ölçü aranıyor",
                  "ÖLÇÜLERİ GİRİLMEDİ" in (mk(mk_yok=ham).get("uyari") or "")
                  or mk(mk_yok=ham)["aktif"] is False)

    # ==================================================================
    #  v1.6 — MANUEL k  ( tek ve çoklu yolda AYNI davranış )
    # ==================================================================
    _gk = {"bina_tipi": "Konut", "bina_yuksekligi": 39.98, "yapi_yuksekligi": 43,
           "N": 11, "h": 3, "hizli1": 44, "hizli2": 3,
           "asansorler": [{"P": 10, "kapi_genisligi": 900,
                           "kapi_tipi": "Teleskopik Otomatik"},
                          {"P": 16, "kapi_genisligi": 1100,
                           "kapi_tipi": "Teleskopik Otomatik"}]}
    r.kontrol("çoklu: manuel k yokken hesap yapılıyor",
              not TR.hesapla_coklu(dict(_gk)).get("hata"))
    r.kontrol("çoklu: Tablo-9 varken manuel k reddediliyor",
              "manuel k girilemez" in (TR.hesapla_coklu(
                  dict(_gk, manuel_k=0.08)).get("hata") or ""))
    _gt = {"bina_tipi": "Konut", "bina_yuksekligi": 39.98, "yapi_yuksekligi": 43,
           "N": 11, "h": 3, "hizli1": 44, "hizli2": 3, "P": 10,
           "kapi_genisligi": 900, "kapi_tipi": "Teleskopik Otomatik"}
    r.kontrol("tek: Tablo-9 varken manuel k reddediliyor",
              "manuel k girilemez" in (TR.hesapla_tek(
                  dict(_gt, manuel_k=0.08)).get("hata") or ""))
    #  Kamu binasında manuel k GEÇERLİDİR ( Tablo-9'da kamu yok )
    _gkamu = dict(_gk, bina_tipi="Kamu Binaları", hizli1=5280, hizli2="")
    _rk = TR.hesapla_coklu(dict(_gkamu, manuel_k=0.08))
    r.kontrol("çoklu: kamu binasında manuel k kabul ediliyor",
              not _rk.get("hata") and abs(_rk["ozet"]["k"] - 0.08) < 1e-9)

    # ==================================================================
    #  v1.6 — OFİS VARSAYILANLARI, OTOMATİK MOTOR GÜCÜ, L1 TÜRETMESİ
    # ==================================================================
    O_ORT = {"temel_a": 26.55, "temel_b": 16.4, "serit_L": 58.5, "mk_yok": True}
    O_AS = {"tanim": "A", "kapasite": 10, "V": 1.6, "eta": 0.85, "Hk": 38.5,
            "kuyu_genisligi": 1800, "kabin_boyu": 1450, "kabin_genisligi": 1300,
            "i_palanga": 2, "makine_tipi": "Dişlisiz"}

    def av(as_ek=None, sabit=None, ortak_ek=None):
        o = dict(O_ORT); o.update(ortak_ek or {})
        a = dict(O_AS);  a.update(as_ek or {})
        return AV.hesapla({"ortak": o, "asansorler": [a], "sabitler": sabit or {}})

    #  Boş bırakılan malzeme alanları ofis varsayılanından gelir
    t = av()
    r.kontrol("boş alanlarla hesap yapılıyor", t["asansorler"][0]["aktif"] is True)
    oz = t["asansorler"][0]["ozet"]
    r.esit("kablo tipi ofis varsayılanından", oz["kablo_tipi"], "NHXMH FE180")
    r.esit("S1 ofis varsayılanından", oz["S1"], 6)
    r.esit("L1 = Hk + ofis payı", round(oz["L1"], 4), round(38.5 + 3.5, 4))

    #  Ofis varsayılanı değiştirilince hesap da değişir
    t2 = av(sabit={"S1": 10, "L1_pay": 5})
    r.esit("ofis S1 değişince kullanılan da değişti", t2["asansorler"][0]["ozet"]["S1"], 10)
    r.esit("ofis L1 payı değişince L1 değişti",
           round(t2["asansorler"][0]["ozet"]["L1"], 4), round(38.5 + 5, 4))

    #  Asansör bazında ezme, ofis varsayılanını yener
    r.esit("asansör bazında S1 ofis değerini eziyor",
           av(as_ek={"S1": 16}, sabit={"S1": 10})["asansorler"][0]["ozet"]["S1"], 16)
    r.esit("asansör bazında L1 ofis türetmesini eziyor",
           av(as_ek={"L1": 51.5})["asansorler"][0]["ozet"]["L1"], 51.5)
    r.esit("asansör bazında kablo tipi eziliyor",
           av(as_ek={"kablo_tipi": "N2XH"})["asansorler"][0]["ozet"]["kablo_tipi"], "N2XH")

    #  Geçersiz ofis değeriyle HESAP YAPILMAZ.  Eskiden varsayılana dönülüp
    #  hesap sürüyordu;  sabitler() değeri yine sözlüğe yazmaz, ama hesapla()
    #  artık durur ve alanı adıyla söyler.
    r.kontrol("geçersiz ofis değeri sabitler()'de reddediliyor",
              "gr" in AV.sabitler({"gr": -5})["_reddedilen"])
    r.esit("reddedilen değer sözlüğe yazılmıyor", AV.sabitler({"gr": -5})["gr"], 17.91)
    t3 = av(sabit={"gr": -5})
    r.kontrol("geçersiz ofis değeriyle hesap yapılmıyor",
              set(t3) == {"hata"}, f"→ {sorted(t3)}")
    r.kontrol("hata alanı adıyla ve aralığıyla söylüyor",
              "gr — ray birim kütlesi = -5" in t3.get("hata", "")
              and "geçerli aralık 1 - 200" in t3.get("hata", ""),
              f"→ {t3.get('hata')!r}")
    #  Ortak paneldeki β da aynı kurala bağlı:  aralık dışı β eskiden HİÇBİR
    #  uyarı olmadan 150 Ω·m'ye dönüyordu ( topraklama red listesi almıyordu ).
    for _ad3, _ok3 in (("β = 0,5", {"beta": 0.5}), ("U = 50", {"U": 50}),
                       ("Is = -1", {"cubuk_sayisi": -1}), ("şerit L = -5", {"serit_L": -5})):
        _h3 = av(ortak_ek=_ok3).get("hata") or ""
        r.kontrol(f"ortak panel {_ad3} hesabı durduruyor", bool(_h3), "→ hesap yapıldı")
    #  Her sayısal ofis alanının kullanıcıya gösterilecek bir adı var
    r.kontrol("her ofis aralığının etiketi var",
              not (set(AV.SABIT_B_ARALIK) | set(AV.OFIS_ARALIK)) - set(AV.OFIS_ETIKET),
              f"→ etiketsiz: {sorted((set(AV.SABIT_B_ARALIK) | set(AV.OFIS_ARALIK)) - set(AV.OFIS_ETIKET))}")
    r.kontrol("her sayısal ofis varsayılanının aralığı var",
              not [k for k, v in {**AV.SABIT_B_VARSAYILAN, **AV.OFIS_VARSAYILAN}.items()
                   if not isinstance(v, str)
                   and k not in AV.SABIT_B_ARALIK and k not in AV.OFIS_ARALIK])

    #  Ortak alanlar ( U / κ / εmax / β / çubuk adedi ) da ofis varsayılanından
    r.kontrol("ortak alanlar boşken hesap yapılıyor",
              av(ortak_ek={"U": "", "kappa": "", "eps_max": "",
                           "beta": "", "cubuk_sayisi": ""})["topraklama"]["aktif"] is True)
    r.esit("β boşken ofis varsayılanı kullanıldı",
           round(av(ortak_ek={"beta": ""})["ozet"]["Re"], 4),
           round(av(ortak_ek={"beta": 150})["ozet"]["Re"], 4))

    #  β ve çubuk adedi ofis standardına taşındı ( v1.7 ) — avan panelinde
    #  artık alan yok, motor değeri ofis varsayılanından almalı ve ofis
    #  değeri değişince hesap da değişmeli.
    _tb = lambda ek=None, sab=None: av(ortak_ek=ek, sabit=sab)["ozet"]["Re"]
    r.kontrol("β alanı hiç gönderilmese de topraklama hesaplanıyor",
              av(ortak_ek={"beta": "", "cubuk_sayisi": ""})["topraklama"]["aktif"] is True)
    r.esit("β boşken ofis varsayılanı ( 150 ) kullanılıyor",
           round(_tb({"beta": ""}), 4), round(_tb({"beta": 150}), 4))
    r.esit("çubuk adedi boşken ofis varsayılanı ( 4 ) kullanılıyor",
           round(_tb({"cubuk_sayisi": ""}), 4), round(_tb({"cubuk_sayisi": 4}), 4))
    r.kontrol("ofis β'sı değişince topraklama direnci değişiyor",
              abs(_tb({"beta": ""}, {"beta": 90}) - _tb({"beta": ""})) > 1e-6)
    r.kontrol("ofis çubuk adedi değişince direnç değişiyor",
              abs(_tb({"cubuk_sayisi": ""}, {"cubuk_sayisi": 8})
                  - _tb({"cubuk_sayisi": ""})) > 1e-6)

    #  Nsç — standart kademeden otomatik seçim
    r.esit("motor kademesi: 13,33 kW → 15", T.motor_sec(13.33), 15.0)
    r.esit("motor kademesi: tam eşit değer kendisi", T.motor_sec(11.0), 11.0)
    r.esit("motor kademesi: küçük güç → en alt kademe", T.motor_sec(0.4), 2.2)
    r.kontrol("motor kademesi: hesap yoksa None", T.motor_sec(None) is None)
    r.kontrol("motor kademesi: liste üstü → None", T.motor_sec(9999) is None)
    o16 = av(as_ek={"kapasite": 16})["asansorler"][0]["ozet"]
    r.esit("16 kişilik asansöre 15 kW seçildi", o16["Nsc"], 15.0)
    r.kontrol("otomatik seçim motor kontrolünü geçiyor", o16["motor_uygun"] is True)
    r.kontrol("otomatik seçim hesaplanan güçten büyük", o16["Nsc"] >= o16["N_hes"])
    #  Elle girilen küçük değer korunur ama UYGUN DEĞİL der
    o16e = av(as_ek={"kapasite": 16, "Nsc": 11})["asansorler"][0]["ozet"]
    r.esit("elle girilen Nsç korunuyor", o16e["Nsc"], 11)
    r.kontrol("elle girilen küçük Nsç uygun değil", o16e["motor_uygun"] is False)
    #  v2.8 — SEÇİM ile KONTROL AYNI TOLERANSI KULLANIR.  N = ( 1−q )·Q·V/( 102·η′ )
    #  kayan noktada kademenin bir kıl payı üstüne düşebilir; motor_sec toleranslı
    #  seçtiği hâlde kontrol katı olunca program KENDİ seçtiği motoru reddediyor,
    #  pafta "Nsç = 15,00  ≥  N = 15,00  →  UYGUN DEĞİL" basıyordu.
    #  MEKANİZMAYI sınar, şanslı bir senaryoyu değil:  kademenin kıl payı
    #  üstündeki bir N için seçim ile kontrol AYNI eşiği kullanmalıdır.
    r.esit("tolerans tek yerde", T.MOTOR_TOLERANS, 1e-9)
    for _kademe in (5.5, 15.0, 37.0):
        _N = _kademe + T.MOTOR_TOLERANS / 2          # kıl payı üstü
        _sec = T.motor_sec(_N)
        r.esit(f"{_kademe} kW: kıl payı üstteki N kademeyi bulur", _sec, _kademe)
        r.kontrol(f"{_kademe} kW: seçim ile kontrol aynı eşiği kullanır",
                  _sec >= _N - T.MOTOR_TOLERANS)
        r.kontrol(f"{_kademe} kW: gerçekten küçük kademe reddedilir",
                  not (_kademe >= _kademe * 1.5 - T.MOTOR_TOLERANS))
    #  DEĞİŞMEZ:  otomatik seçilen motor HİÇBİR girdide kendi kendini reddetmez
    _red = []
    for _P in T.GECERLI_KAPASITELER:
        for _V in (0.63, 1.6, 2.5):
            for _q in (0.40, 0.50, 0.60):
                _o = AV.hesapla_asansor(
                    dict(kapasite=_P, V=_V, eta=0.85, i_palanga=2, q_denge=_q, Hk=25,
                         kuyu_genisligi=2400, kabin_boyu=1100, kabin_genisligi=1000,
                         makine_tipi="Dişlisiz"), {"mk_yok": True}, AV.sabitler(None), 1)
                if _o.get("aktif") and _o["ozet"]["motor_uygun"] is not True:
                    _red.append((_P, _V, _q, _o["ozet"]["N_hes"], _o["ozet"]["Nsc"]))
    r.kontrol("otomatik seçim hiçbir girdide kendini reddetmiyor", not _red,
              f"→ {_red[:3]}")

    #  Boş bırakılan alanlar ofis varsayılanına çözülür
    _S_of = AV.sabitler({})
    for anahtar, beklenen in (("gr", 17.91), ("Fmk", 350), ("Fsh", 100),
                              ("S1", 6), ("S2", 6), ("L2", 3),
                              ("kablo_tipi", "NHXMH FE180")):
        r.esit(f"çözülmüş girdi {anahtar}", AV._ofis_degeri(dict(O_AS), _S_of, anahtar)[0],
               beklenen)
    _oz_of = AV.hesapla({"ortak": dict(O_ORT), "asansorler": [dict(O_AS)],
                         "sabitler": {}})["asansorler"][0]["ozet"]
    #  2:1 · η 0,85 → η′ 0,75 ( MMO/697 §2.4 ) → N = 8,37 kW → 11 kW kademesi
    for anahtar, beklenen in (("L1", 42.0), ("Nsc", 11.0)):
        r.esit(f"kullanılan değer {anahtar}", _oz_of[anahtar], beklenen)
    #  κ ofis varsayılanı TS HD 60364-5-52 EK-G'ye çekildi ( ρ1 = 1,25·ρ20
    #  → 0,0225 Ω·mm²/m ).  Sayıyı BURAYA ikinci kez yazmak yerine tek
    #  kaynaktan okunur;  değişirse test sessizce eskimez.
    for anahtar, beklenen in (("U", 380),
                              ("kappa", AV.sabitler(None)["kappa"]),
                              ("eps_max", 3),
                              ("beta", 150), ("cubuk_sayisi", 4)):
        r.esit(f"çözülmüş ortak {anahtar}", AV._ortak_degeri({}, _S_of, anahtar), beklenen)
    r.kontrol("çözme işlemi özgün girdiyi bozmuyor", "gr" not in O_AS)

    # ==================================================================
    #  v1.7 — GEÇERSİZ GİRDİ YOLLARI
    #  Bu altı bulgu bir dış denetimde ortaya çıktı: hesap "normal" girdilerde
    #  doğruydu, ama geçersiz girdi yollarında program
    #  yanlışlıkla "uygun" sonucu verebiliyordu.  Her biri için kalıcı test.
    # ==================================================================
    _gt = {"bina_tipi": "Konut", "bina_yuksekligi": 39.98, "yapi_yuksekligi": 43,
           "N": 11, "h": 3, "hizli1": 44, "hizli2": 3, "P": 10,
           "kapi_genisligi": 900, "kapi_tipi": "Merkezden Açılan Oto."}
    _gc = {"bina_tipi": "Konut", "bina_yuksekligi": 39.98, "yapi_yuksekligi": 43,
           "N": 11, "h": 3, "hizli1": 44, "hizli2": 3,
           "asansorler": [{"P": 10, "kapi_genisligi": 900,
                           "kapi_tipi": "Teleskopik Otomatik"},
                          {"P": 16, "kapi_genisligi": 1100,
                           "kapi_tipi": "Teleskopik Otomatik"}]}

    #  1) MANUEL SÜRELER  —  0 / negatif / saçma büyük değer reddedilmeli.
    #     Dördü de 0 iken TR = 24,5 sn çıkıyor, ts = −1,88 sn gibi imkânsız bir
    #     ara değer oluşuyor ve 44 daireli bina 1 asansörle "yeterli" görünüyordu.
    r.kontrol("tek: dört manuel süre de 0 → reddediliyor",
              bool(TR.hesapla_tek(dict(_gt, manuel_ta=0, manuel_tk=0,
                                       manuel_tg=0, manuel_tp=0)).get("hata")))
    for _alan in ("manuel_ta", "manuel_tk", "manuel_tg", "manuel_tp"):
        for _d in (0, -5):
            r.kontrol(f"tek: {_alan} = {_d} reddediliyor",
                      bool(TR.hesapla_tek(dict(_gt, **{_alan: _d})).get("hata")))
    r.kontrol("tek: manuel ta = 999 s reddediliyor",
              bool(TR.hesapla_tek(dict(_gt, manuel_ta=999)).get("hata")))
    r.kontrol("tek: makul manuel süre KABUL ediliyor",
              not TR.hesapla_tek(dict(_gt, manuel_ta=2.9)).get("hata"))
    _v = dict(_gc)
    _v["asansorler"] = [dict(_gc["asansorler"][0], manuel_tg=-5), _gc["asansorler"][1]]
    r.kontrol("çoklu: asansör bazında negatif süre reddediliyor",
              "ASANSÖR-1" in (TR.hesapla_coklu(_v).get("hata") or ""))
    _v["asansorler"] = [dict(_gc["asansorler"][0], manuel_ta=2.9), _gc["asansorler"][1]]
    r.kontrol("çoklu: makul manuel süre KABUL ediliyor",
              not TR.hesapla_coklu(_v).get("hata"))

    #  2) ÇOKLU HESAP  —  bina girdileri tek asansör hesabıyla AYNI denetimden
    #     geçmeli.  ( h = −3 m ile "Yükseltilmiş kriteri karşılanıyor" çıkıyordu. )
    for _ad, _ek in (("h = -3", {"h": -3}), ("h = 0", {"h": 0}), ("h = 99", {"h": 99}),
                     ("bina yüksekliği boş", {"bina_yuksekligi": ""}),
                     ("yapı yüksekliği boş", {"yapi_yuksekligi": ""})):
        _rc = TR.hesapla_coklu(dict(_gc, **_ek))
        _rt = TR.hesapla_tek(dict(_gt, **_ek))
        r.kontrol(f"çoklu: {_ad} reddediliyor", bool(_rc.get("hata")))
        r.kontrol(f"tek: {_ad} reddediliyor", bool(_rt.get("hata")))
    r.kontrol("çoklu: normal girdi hâlâ hesaplanıyor",
              not TR.hesapla_coklu(dict(_gc)).get("hata"))

    #  3) BELİRSİZ SAYI  —  "1.200" bin iki yüz mü, bir virgül iki mi?
    #     Sessizce 1,2 okunuyordu: 1.200 daireli binada asansör adedi 41 → 2.
    from api import ortak as _M
    for _ham in ("1.200", "1,200", "2.500", "12.345", "1,000", "100,000", "-1.500"):
        r.kontrol(f"belirsiz sayı reddediliyor: {_ham!r}", _M._sayi(_ham) is None)
        r.kontrol(f"belirsiz olarak işaretleniyor: {_ham!r}", _M.belirsiz_sayi_mi(_ham))
    #  Sıfırla başlayan ondalıklar BELİRSİZ DEĞİLDİR: binlik ayracı sıfırdan
    #  sonra gelmez.  "0,075" ( manuel k = %7,5 ) geçerli kalmalıdır.
    for _ham, _bek in (("1200", 1200), ("39,98", 39.98), ("39.98", 39.98),
                       ("1.234,56", 1234.56), ("1,234.56", 1234.56),
                       ("1.2", 1.2), ("0.5", 0.5), ("1.20", 1.2),
                       ("0,075", 0.075), ("0.075", 0.075), ("0,750", 0.75)):
        r.kontrol(f"geçerli sayı okunuyor: {_ham!r} = {_bek}",
                  abs((_M._sayi(_ham) or 0) - _bek) < 1e-9)
        r.kontrol(f"belirsiz sayılmıyor: {_ham!r}", not _M.belirsiz_sayi_mi(_ham))

    #  4) AVAN — elle girilen fiziksel büyüklüklerin sınırı
    _oa = {"temel_a": 26.55, "temel_b": 16.4, "serit_L": 58.5, "mk_yok": True}
    _aa = {"tanim": "A", "kapasite": 10, "V": 1.6, "eta": 0.85, "Hk": 38.5,
           "kuyu_genisligi": 1800, "kabin_boyu": 1450, "kabin_genisligi": 1300,
           "i_palanga": 2, "makine_tipi": "Dişlisiz"}

    def _av(ek=None, sab=None):
        a = dict(_aa); a.update(ek or {})
        return AV.hesapla({"ortak": _oa, "asansorler": [a], "sabitler": sab or {}})

    r.kontrol("avan: normal girdi hesaplanıyor", _av()["asansorler"][0]["aktif"] is True)
    for _ad, _ek in (("Q elle = 0", {"Q_elle": 0}), ("Q elle = -500", {"Q_elle": -500}),
                     ("Gk elle = 0", {"Gk_elle": 0}), ("Gk elle = -800", {"Gk_elle": -800}),
                     ("η = 10", {"eta": 10}), ("η = 0", {"eta": 0})):
        r.kontrol(f"avan: {_ad} reddediliyor",
                  _av(_ek)["asansorler"][0]["aktif"] is False)

    #  5) Tablo-11 dışı anma yükü  —  Gk sessizce uç değere sabitlenmemeli
    r.kontrol("avan: Q = 5000 kg ( Tablo-11 dışı ) Gk elle olmadan reddediliyor",
              _av({"Q_elle": 5000})["asansorler"][0]["aktif"] is False)
    r.kontrol("avan: Tablo-11 dışı uyarısı tabloyu adıyla anıyor",
              "Tablo-11" in (_av({"Q_elle": 5000})["asansorler"][0].get("uyari") or ""))
    _t11 = _av({"Q_elle": 5000, "Gk_elle": 2400})["asansorler"][0]
    r.kontrol("avan: Gk elle verilince Tablo-11 dışı yük hesaplanıyor",
              _t11["aktif"] is True and _t11["ozet"]["Gk"] == 2400)
    r.kontrol("avan: Q = 300 kg ( tablo altı ) da reddediliyor",
              _av({"Q_elle": 300})["asansorler"][0]["aktif"] is False)

    #  6) Denge faktörü q  —  q = 1 iken N = 0 kW çıkıp 2,2 kW motor
    #     "uygun" görünüyordu.
    for _q in (0, 1, 1.5, -0.2):
        _rq = _av({"q_denge": _q})["asansorler"][0]
        r.kontrol(f"avan: q = {_q} ile hesap yapılmıyor", _rq["aktif"] is False)
        r.kontrol(f"avan: q = {_q} için sebep denge faktörünü söylüyor",
                  "q — denge faktörü" in (_rq.get("uyari") or ""),
                  f"→ {_rq.get('uyari')!r}")
    r.kontrol("avan: q = 0,45 kabul ediliyor",
              abs(_av({"q_denge": 0.45})["asansorler"][0]["ozet"]["q_denge"] - 0.45) < 1e-9)
    r.kontrol("avan: q = 0,60 kabul ediliyor ama uygulama bandı uyarısı çıkıyor",
              any("bandındadır" in x for x in (_av({"q_denge": 0.60}).get("uyarilar") or [])))

    #  Aralık dışı ofis alanları SESSİZ düşmemeli — ve hesaba da girmemeli
    for _ad, _ek in (("gr = -17", {"gr": -17}), ("Fmk = -350", {"Fmk": -350}),
                     ("Nsç = -11", {"Nsc": -11}), ("L1 = -40", {"L1": -40}),
                     ("S1 = 0", {"S1": 0}), ("S2 = 500", {"S2": 500}),
                     ("L2 = 0", {"L2": 0}), ("Fsh = -1", {"Fsh": -1}),
                     ("i = 9", {"i_palanga": 9})):
        _ru = _av(_ek)
        r.kontrol(f"avan: {_ad} hesabı durduruyor",
                  _ru["asansorler"][0]["aktif"] is False, "→ hesap yapıldı")
        r.kontrol(f"avan: {_ad} sebebi uyarılarda görünüyor",
                  any("girilen değer kullanılamıyor" in x
                      for x in (_ru.get("uyarilar") or [])), f"→ {_ru.get('uyarilar')}")
    #  Boş bırakılan alan hesabı durdurmaz — ofis varsayılanı kullanılır
    _bos = _av({"gr": "", "S1": None, "Nsc": "", "L1": None})["asansorler"][0]
    r.kontrol("avan: boş bırakılan ofis alanları varsayılanla hesaplanıyor",
              _bos["aktif"] is True and _bos["ozet"]["S1"] == 6)
    r.kontrol("avan: geçerli girdide gereksiz uyarı yok", not (_av().get("uyarilar") or []))

    # ==================================================================
    #  v1.8 — ŞERİT BOYU ( L ) TEMEL ÖLÇÜLERİNDEN TÜRETİLİR
    #  Ofiste temel için yalnız UZUNLUK ve GENİŞLİK giriliyor; band boyu
    #  bunlardan çıkarılır.  Girilirse girilen değer kullanılır.
    # ==================================================================
    _S = AV.sabitler({})
    r.esit("karelaj gözü ofis varsayılanı 20 m", _S["goz_araligi"], 20)

    #  Formülün kendisi:  L = 2·( a + b ) + na·b + nb·a
    _L, _ring, _na, _nb = AV.serit_boyu_tahmin(31.05, 18.9, 20)
    r.esit("ring = 2·( a + b )", round(_ring, 4), round(2 * (31.05 + 18.9), 4))
    r.esit("31,05 m kenar için 1 enine bağ", _na, 1)
    r.esit("18,90 m kenar için bağ gerekmiyor", _nb, 0)
    r.esit("L = ring + 1 · b", round(_L, 4), round(2 * (31.05 + 18.9) + 18.9, 4))
    r.esit("20 × 20 m'den küçük temelde bağ yok",
           AV.serit_boyu_tahmin(15, 10, 20)[0], 50)
    r.kontrol("ölçü yoksa türetme yok", AV.serit_boyu_tahmin(0, 18.9, 20)[0] is None)
    #  Tam 20 m kenar bağ gerektirmez ( kayan nokta payı ile )
    r.esit("tam 20 m kenarda bağ yok", AV.serit_boyu_tahmin(20, 20, 20)[0], 80)
    r.esit("20,01 m kenarda bağ çıkıyor", AV.serit_boyu_tahmin(20.01, 20, 20)[2], 1)

    _TO = {"temel_a": 31.05, "temel_b": 18.9}
    _t = AV.hesapla_topraklama(dict(_TO), _S)
    r.kontrol("L boşken hesap çalışıyor", _t["aktif"] is True)
    r.esit("L türetildi", round(_t["L"], 2), 118.80)
    r.esit("L kaynağı türetilen", _t["L_kaynak"], "türetilen")

    #  L TÜRETİLDİYSE PAFTAYA HESABIYLA BASILIR  ( kullanıcı kararı ):
    #  eskiden "GİRİŞ" diye basılıyordu ve sayının nereden geldiği
    #  görünmüyordu.  Formül, sayılar ve kaynak ( karelaj gözü ) yazılır.
    _p1 = _t["bolumler"][0]
    _Ls = [x for x in _p1["adimlar"] if (x.get("formul") or "").startswith("L ")]
    r.kontrol("paftada L hesabıyla basılıyor",
              len(_Ls) == 1 and "2 · ( a + b )" in _Ls[0]["formul"]
              and "31,05" in _Ls[0]["islem"] and "karelaj" in _Ls[0]["kaynak"],
              f"→ {_Ls}")
    r.esit("paftadaki L hesabın değeri", round(_Ls[0]["deger"], 2) if _Ls else None, 118.80)
    r.kontrol("türetilen L için 'GİRİŞ' satırı YOK",
              not any(x.get("sembol") == "L" and x.get("kaynak") == "GİRİŞ"
                      for x in _p1["adimlar"]))

    #  Elle girilen boy türetileni EZER — plan çizilince gerçek boy yazılır
    _te = AV.hesapla_topraklama(dict(_TO, serit_L=140), _S)
    r.esit("elle girilen L kullanılıyor", _te["L"], 140)
    r.esit("elle girilince kaynak GİRİŞ", _te["L_kaynak"], "GİRİŞ")
    r.kontrol("elle girilince türetme notu yok", not _te["bolumler"][0].get("notlar"))
    #  Elle girilen boy sıradan bir girdi satırıdır ( hesabı yoktur )
    r.kontrol("elle girilen L paftada GİRİŞ satırı",
              any(x.get("sembol") == "L" and x.get("kaynak") == "GİRİŞ"
                  for x in _te["bolumler"][0]["adimlar"]))

    #  Ofis paftasının kendi sayısı ( 31,05 × 18,90 · L = 140 · β = 150 · Is = 4 )
    r.esit("ofis paftası Ry", round(_te["Ry"], 2), 3.82)
    r.esit("ofis paftası Rç", round(_te["Rc"], 2), 25.00)
    r.esit("ofis paftası Re", round(_te["Re"], 3), 3.310)
    r.esit("ofis paftası Re max", round(_te["Re_max"], 2), 166.67)
    r.kontrol("ofis paftası sonucu: uygun", _te["uygun"] is True)

    #  Göz aralığı ofis sabitidir — değişince türetilen boy da değişir
    _t10 = AV.hesapla_topraklama(dict(_TO), AV.sabitler({"goz_araligi": 10}))
    r.kontrol("göz 10 m olunca L uzuyor", _t10["L"] > _t["L"],
              f"→ {_t10['L']:.2f} > {_t['L']:.2f}")
    r.kontrol("geçersiz göz aralığı reddediliyor",
              any("goz_araligi" in x
                  for x in AV.sabitler({"goz_araligi": 0})["_reddedilen"]))

    #  Ölçü yoksa hesap kapanır ve hata metni ölçüleri işaret eder
    _ty = AV.hesapla_topraklama({"temel_b": 18.9}, _S)
    r.kontrol("uzunluk yoksa topraklama kapalı", _ty["aktif"] is False)
    r.kontrol("hata metni temel ölçülerini işaret ediyor",
              "uzunluk" in _ty["uyari"] and "genişlik" in _ty["uyari"])

    _v = {"ortak": dict(_TO, mk_yok=True), "asansorler": [dict(O_AS)], "sabitler": {}}
    r.esit("elle girilen L korunuyor",
           AV.hesapla({"ortak": dict(_TO, serit_L=58.5, mk_yok=True),
                       "asansorler": [dict(O_AS)], "sabitler": {}})["ozet"]["serit_L"], 58.5)
    r.esit("özette şerit boyu ve kaynağı var",
           (round(AV.hesapla(_v)["ozet"]["serit_L"], 2),
            AV.hesapla(_v)["ozet"]["serit_L_kaynak"]), (118.80, "türetilen"))
    # ==================================================================
    #  v1.9 — DIŞ DENETİM BULGULARI
    #  ( S2 akım kontrolü · motor sigortası · kabin/kuyu uyumu )
    # ==================================================================
    import math as _m

    #  --- Motor koruma cihazı standart kademeden seçilir
    r.kontrol("sigorta kademeleri artan ve tekrarsız",
              list(T.SIGORTA_KADEMELERI) == sorted(set(T.SIGORTA_KADEMELERI)))
    for _kW, _bek in ((11, 25), (15, 32), (37, 80), (110, 250)):
        _In = _kW * 1000 / (_m.sqrt(3) * 380 * 0.90)
        r.esit(f"{_kW} kW motor → sigorta kademesi", T.sigorta_sec(_In, 1.25), _bek)
    r.kontrol("geçersiz akımda kademe yok", T.sigorta_sec(0) is None
              and T.sigorta_sec(None) is None and T.sigorta_sec(-5) is None)
    r.kontrol("liste dışına taşan akımda kademe yok", T.sigorta_sec(9000) is None)
    r.esit("geçersiz katsayı varsayılana döner",
           T.sigorta_sec(18.58, 0), T.sigorta_sec(18.58, 1.25))

    #  ŞEBEKEDEN ÇEKİLEN AKIM motorun ELEKTRİK verimine de bölünür:
    #  Pşeb = P2 / ηm.  Program bir süre ηm'yi atlıyordu ve akımı %18 DÜŞÜK
    #  gösteriyordu — kablo ve sigorta olduğundan küçük seçiliyordu.  Eski
    #  avan paftasındaki "4 x 25" ηm'siz hesaplanmış değerdir.
    _S0 = AV.sabitler({})
    _s = _av()["asansorler"][0]["ozet"]
    r.esit("motor akımı ηm'ye de bölünüyor", round(_s["I_motor"], 1),
           round(_s["Nsc"] * 1000 / (_m.sqrt(3) * 380 * 0.90
                                     * _S0["motor_elektrik_verimi"]), 1))
    r.kontrol("ηm atlanmış eski akımdan BÜYÜK",
              _s["I_motor"] > _s["Nsc"] * 1000 / (_m.sqrt(3) * 380 * 0.90),
              f"→ {_s['I_motor']}")
    #  Örneğin motoru 11 kW ( 2:1 · η′ 0,75 ):  In = 21,85 A · 1,25 = 27,3 A → 32 A
    r.esit("ofis örneğinde sigorta", _s["motor_sigorta"], "4 x 32")
    _cet = [b for b in _av()["asansorler"][0]["bolumler"] if b.get("cetvel")][0]["cetvel"]
    r.esit("cetveldeki sigorta hesaplanan değer", _cet[0]["sigorta"], "4 x 32")
    r.kontrol("sigorta artık sabit değil — güç büyüyünce değişiyor",
              _av({"Nsc": 110})["asansorler"][0]["ozet"]["motor_sigorta"] == "4 x 315")
    #  Katsayı ofis standardındadır
    r.esit("katsayı büyüyünce sigorta da büyüyor",
           _av(sab={"sigorta_katsayisi": 2.5})["asansorler"][0]["ozet"]["motor_sigorta"],
           "4 x 63")
    #  ηm ofis sabitidir — değiştirilince akım da değişir
    r.kontrol("ηm ofis sabitinden geliyor",
              _av(sab={"motor_elektrik_verimi": 1.0})["asansorler"][0]["ozet"]["I_motor"]
              < _s["I_motor"])
    r.kontrol("geçersiz katsayı reddediliyor",
              any("sigorta_katsayisi" in x
                  for x in AV.sabitler({"sigorta_katsayisi": 0})["_reddedilen"]))

    #  ------------------------------------------------------------------
    #  B5  KURULU GÜÇ ETİKET GÜCÜDÜR;  KOLON HATTI ŞEBEKEDEN ÇEKİLENİ TAŞIR
    #  ------------------------------------------------------------------
    #  Kurulu güç tanım gereği anma ( etiket ) güçlerinin toplamıdır ( Elektrik
    #  İç Tesisleri Proje Hazırlama Yönetmeliği m.5-19 );  motorun anma gücü
    #  mil gücüdür ( TS EN 60034-1 m.5.5.3 ).  Kolon hattı ise motorun
    #  şebekeden çektiğini taşır ( Pşeb = Nsç / ηm ):  I ve ε1 onunla kurulur.
    #  Önce hat ηm'siz hesaplanıyordu ( kesit emniyetsiz ), sonra akım doğru
    #  çıksın diye Pşeb cetvele yazıldı ( kurulu güç %18 büyük ) — ikisi ayrıldı.
    _etam = _S0["motor_elektrik_verimi"]
    r.esit("B5  cetveldeki motor gücü = etiket gücü  ( Nsç )",
           round(_cet[0]["guc"], 3), round(_s["Nsc"] * 1000, 3))
    r.esit("B5  kurulu güç = etiket güçlerinin toplamı",
           round(_s["P_kurulu"], 3),
           round(_s["Nsc"] * 1000 + _s["g_kuyu"] + _s["g_kabin"] + _s["g_priz"], 3))
    r.esit("B5  kolon hattı gücü P1 = Nsç / ηm + aydınlatma + priz",
           round(_s["P_hat"], 3),
           round(_s["Nsc"] * 1000 / _etam + _s["g_kuyu"] + _s["g_kabin"] + _s["g_priz"], 3))
    r.esit("B5  kolon hattı akımı I = P1 / (√3·U·cosφ)",
           round(_s["I"], 3),
           round(_s["P_hat"] / (_m.sqrt(3) * 380 * 0.90), 3))
    r.kontrol("B5  I, ηm'siz eski değerden BÜYÜK",
              _s["I"] > (_s["Nsc"] * 1000 + _s["g_kuyu"] + _s["g_kabin"]
                         + _s["g_priz"]) / (_m.sqrt(3) * 380 * 0.90),
              f"→ {_s['I']}")
    r.kontrol("B5  ε1 de Pşeb ile hesaplanıyor  ( ε1 ∝ P1 )",
              _yakin_o(_s["eps1"],
                       100 * _s["P_hat"] * _s["L1"]
                       / (AV.sabitler(None)["kappa"] * _s["S1"] * 380 ** 2))
              if all(_s.get(k) is not None for k in ("eps1", "L1", "S1")) else True,
              f"→ {_s.get('eps1')!r}")
    #  Denetimin bildirdiği karar çeviren birleşimler
    for _kw, _s1, _iz in ((22, 6, 41), (30, 10, 57), (55, 25, 96)):
        _o5 = _av({"Nsc": _kw, "S1": _s1, "S2": _s1})["asansorler"][0]["ozet"]
        r.kontrol(f"B5  {_kw} kW · S1 = {_s1} mm² → UYGUN DEĞİL  "
                  f"( I = {_o5['I']:.1f} A > Iz = {_iz} A )",
                  _o5["akim_uygun"] is False and _o5["Iz"] == _iz,
                  f"→ I={_o5['I']!r} Iz={_o5['Iz']!r} uygun={_o5['akim_uygun']!r}")
        r.kontrol(f"B5  {_kw} kW ηm'siz olsaydı 'uygun' görünürdü",
                  _o5["P_kurulu"] / (_m.sqrt(3) * 380 * 0.90) < _iz)
    #  B6  Iz TABLOSU BAŞLIĞINDAKİ TABLONUN KENDİSİDİR
    #  IEC 60364-5-52 Tablo B.52.4 · bakır · PVC · 3 yüklü iletken · Yöntem C.
    #  25 mm² ve üstü eskiden 101 · 125 · 151 · 192 · 232 · 269 A yazıyordu —
    #  tablonun değerlerinden %4-5 fazla.  Aradaki akımlarda kolon hattı
    #  "uygundur" görünüyordu.
    r.esit("B6  Iz tablosu = IEC 60364-5-52 B.52.4 · Cu · PVC · 3 yüklü · Yöntem C",
           T.KABLO_IZ, {1.5: 17.5, 2.5: 24, 4: 32, 6: 41, 10: 57, 16: 76, 25: 96,
                        35: 119, 50: 144, 70: 184, 95: 223, 120: 259})
    for _kw, _s1, _iz, _eski in ((48, 25, 96, 101), (60, 35, 119, 125)):
        _o6 = _av({"Nsc": _kw, "S1": _s1, "S2": _s1})["asansorler"][0]["ozet"]
        r.kontrol(f"B6  {_kw} kW · S1 = {_s1} mm² → UYGUN DEĞİL  "
                  f"( Iz = {_iz} A < I ≤ eski tablonun {_eski} A'i )",
                  _o6["akim_uygun"] is False and _o6["Iz"] == _iz
                  and _iz < _o6["I"] <= _eski,
                  f"→ I={_o6['I']!r} Iz={_o6['Iz']!r} uygun={_o6['akim_uygun']!r}")
    #  ε2 de mil gücüyle değil, ŞEBEKEDEN ÇEKİLEN güçle hesaplanır.
    #  ε ∝ P olduğu için oran doğrudan 1/ηm'dir.
    _e2 = _s["eps2"]
    r.kontrol("B5  ε2 Pşeb ile hesaplanıyor  ( mil gücünün 1/ηm katı )",
              _e2 is not None and _yakin_o(
                  _e2, 100 * (_s["Nsc"] * 1000 / _etam) * _s["L2"]
                  / (AV.sabitler(None)["kappa"] * _s["S2"] * 380 ** 2), 1e-6),
              f"→ ε2 = {_e2!r}")

    #  ------------------------------------------------------------------
    #  B18  Nsç = 0 girilince paftada TEK bir motor gücü kalır
    #  ------------------------------------------------------------------
    #  Nsç = 0 ile hesap YAPILMAZ ( eskiden varsayılana dönüyordu ).  Hesap
    #  yapıldığında da bölüm 1 ile kurulu güç cetveli AYNI değeri yazmalı —
    #  yoksa paftada iki farklı motor gücü görünürdü.  İki yol denenir:
    #  elle girilen Nsç ve boş bırakılıp standart kademeden seçilen Nsç.
    _s0 = _av({"Nsc": 0})["asansorler"][0]
    r.kontrol("B18  Nsç = 0 ile hesap yapılmıyor", _s0["aktif"] is False)
    r.kontrol("B18  Nsç = 0 sebebi motor gücünü söylüyor",
              "Nsç — seçilen motor gücü" in (_s0.get("uyari") or ""),
              f"→ {_s0.get('uyari')!r}")
    for _ad18, _nsc18 in (("elle 15 kW", 15), ("otomatik kademe", "")):
        _s18 = _av({"Nsc": _nsc18})["asansorler"][0]
        _b1 = [b for b in _s18["bolumler"] if b["baslik"].startswith("1 ")][0]
        _nsc_b1 = [a["deger"] for a in _b1["adimlar"] if a.get("sembol") == "Nsç"]
        _cet0 = [b for b in _s18["bolumler"] if b.get("cetvel")][0]["cetvel"]
        r.esit(f"B18  [{_ad18}] bölüm 1'in Nsç'si özetle aynı",
               _nsc_b1, [_s18["ozet"]["Nsc"]])
        r.esit(f"B18  [{_ad18}] cetveldeki güç aynı Nsç'den geliyor",
               round(_cet0[0]["guc"], 3), round(_s18["ozet"]["Nsc"] * 1000, 3))
        r.kontrol(f"B18  [{_ad18}] paftada sıfır motor gücü yazmıyor",
                  _s18["ozet"]["Nsc"] > 0 and _cet0[0]["guc"] > 0)

    #  --- S2 ( makine besleme ) akım kontrolü
    #  37 kW motor + 1,5 mm² : I2 = 62 A, kablo 17,5 A taşır.  ε2 küçük
    #  kaldığı için paftada yakalanmıyordu.
    _ince = _av({"kapasite": 25, "V": 2.5, "S2": 1.5, "S1": 50, "L1": 5, "L2": 1})
    _oz = _ince["asansorler"][0]["ozet"]
    r.kontrol("ince S2'de gerilim düşümü hâlâ 'uygun' — tek başına yetmiyor",
              _oz["eps_uygun"] is True)
    r.kontrol("S2 akım kontrolü yapılıyor", _oz["akim2_uygun"] is False)
    r.kontrol("S2 yetersizliği uyarı üretiyor",
              any("MAKİNE BESLEME KESİTİ" in x for x in (_ince.get("uyarilar") or [])),
              f"→ {_ince.get('uyarilar')}")
    r.kontrol("yeterli S2'de uyarı yok",
              not any("MAKİNE BESLEME" in x
                      for x in (_av({"kapasite": 25, "V": 2.5, "S2": 25,
                                     "S1": 50}).get("uyarilar") or [])))
    #  S2 YETERSİZSE BÖLÜM DE UYGUN DEĞİLDİR.
    #  Bir süre yalnız ⚠ uyarı veriliyordu;  hatalı bir sonuç bırakılamaz.
    _b6i = [b for b in _ince["asansorler"][0]["bolumler"]
            if (b.get("sonuc") or {}).get("baslik", "").startswith("KONTROL      ε")][0]
    r.kontrol("S2 yetersizken pafta BÖLÜMÜ de uygun değil",
              _b6i["sonuc"]["uygun"] is False, f"→ {_b6i['sonuc']}")
    r.kontrol("bölümün alt satırında I2 ≤ Iz2 var",
              any("I2" in x for x in _b6i["sonuc"]["alt"]), f"→ {_b6i['sonuc']['alt']}")
    r.kontrol("S2 yetersizliği ENGELLEYİCİ listede",
              any("MAKİNE BESLEME" in x for x in (_ince.get("engelleyici") or [])),
              f"→ {_ince.get('engelleyici')}")

    #  --- Kabin kuyuya sığmalı
    _sig = _av({"kuyu_genisligi": 1500, "kabin_genisligi": 2100})
    r.kontrol("kabin > kuyu uyarı üretiyor",
              any("KABİN KUYUYA SIĞMIYOR" in x for x in (_sig.get("uyarilar") or [])),
              f"→ {_sig.get('uyarilar')}")
    r.kontrol("kabin = kuyu de reddediliyor",
              any("SIĞMIYOR" in x for x in
                  (_av({"kuyu_genisligi": 1800, "kabin_genisligi": 1800}
                       ).get("uyarilar") or [])))
    r.kontrol("normal ölçülerde uyarı yok",
              not any("SIĞMIYOR" in x for x in (_av().get("uyarilar") or [])))

    # ============================================================
    #  v2.2 — SONUÇ CÜMLESİ DOĞRU GEREKÇEYİ SÖYLEMELİ
    #
    #  Paftanın en görünür satırı sonuç cümlesidir.  Eskiden her olumsuz
    #  sonuçta "Bekleme süresi kriteri sağlanmıyor" yazıyordu; oysa elle
    #  seçilen adette çoğu zaman sağlanmayan TAŞIMA kapasitesidir ve bekleme
    #  süresi pekâlâ sağlanıyor olabilir.  Ölçüt listesi ( ✔ / ✘ ) ile
    #  cümlenin çelişmesi, denetime giren bir paftada kabul edilemez.
    # ============================================================
    _GY = dict(bina_tipi="Konut", bina_yuksekligi=45, yapi_yuksekligi=50, N=15, h=3,
               hizli1=60, hizli2=3, P=8, kapi_genisligi=900,
               kapi_tipi="Merkezden Açılan Oto.")

    def _trf(**kw):
        return TR.hesapla_tek(dict(_GY, **kw))["ozet"]

    _iki = _trf(manuel_adet=2)          # taşıma ✘ , bekleme ✔
    _olc = {x["ad"]: x["uygun"] for x in _iki["karar_olcutleri"]}
    r.kontrol("kurgu doğru: taşıma ✘ / bekleme ✔",
              _olc.get("Taşıma") is False and _olc.get("Bekleme") is True)
    r.kontrol("cümle TAŞIMA kapasitesini işaret ediyor",
              "aşıma kapasitesi" in _iki["sonuc_cumlesi"])
    r.kontrol("cümle bekleme süresini SUÇLAMIYOR",
              "Bekleme süresi kriteri sağlanmıyor" not in _iki["sonuc_cumlesi"])
    _bir = _trf(manuel_adet=1)          # ikisi de ✘
    r.kontrol("iki ölçüt de sağlanmıyorsa ikisi de yazılıyor",
              "aşıma kapasitesi" in _bir["sonuc_cumlesi"]
              and "bekleme süresi" in _bir["sonuc_cumlesi"])
    r.kontrol("olumsuz cümle gerekli adedi söylüyor",
              f"{_bir['adet_hesap']} adet" in _bir["sonuc_cumlesi"])

    #  Hiçbir senaryoda cümle ile ölçüt listesi çelişmemeli
    _celiski = 0
    for _P in (6, 8, 10, 13, 16):
        for _n in (1, 2, 3, 4):
            _o = _trf(P=_P, manuel_adet=_n)
            _bk = next((x for x in _o["karar_olcutleri"] if x["ad"] == "Bekleme"), None)
            if _bk and _bk["uygun"] and \
                    "Bekleme süresi kriteri sağlanmıyor" in str(_o["sonuc_cumlesi"]):
                _celiski += 1
    r.esit("cümle ↔ ölçüt çelişkisi ( 20 senaryo )", _celiski, 0)

    # ---- ŞARTLI KABUL:  UYGULANAN sınır esas alınmalı
    #  Yüksek yapıda geçerli sınır "Yükseltilmiş"tir;  "Standart" sütunundan
    #  adet vermek gereken asansör sayısını OLDUĞUNDAN AZ gösteriyordu.
    _SY = dict(bina_tipi="Konut", bina_yuksekligi=29, yapi_yuksekligi=32, N=10, h=2.9,
               hizli1=20, hizli2=3, P=6, kapi_genisligi=900,
               kapi_tipi="Merkezden Açılan Oto.", manuel_adet=1)
    _sk = TR.hesapla_tek(_SY)["ozet"]
    r.esit("kurgu doğru: yüksek yapı → Yükseltilmiş", _sk["standart"], "Yükseltilmiş")
    r.kontrol("kurgu doğru: şartlı kabul çıkıyor", str(_sk["sonuc"]).startswith("Şartlı"))
    r.kontrol("şartlı sonucu UYGULANAN sınırı yazıyor",
              f"{int(_sk['Izul'])} sn" in _sk["sonuc"] and _sk["standart"] in _sk["sonuc"])
    r.kontrol("şartlı sonucu Standart sütununu ölçüt saymıyor",
              f"{int(_sk['esik_standart'])} sn" not in _sk["sonuc"])
    r.kontrol("şartlı sonucundaki adet, iki ölçütü birden sağlayan adettir",
              f"{_sk['adet_hesap']} adet" in _sk["sonuc"])
    r.kontrol("şartlı cümlesi de aynı adedi veriyor",
              f"{_sk['adet_hesap']} adet" in _sk["sonuc_cumlesi"])

    # ---- "şartlı sınırı için N adet yeterli olurdu" notu taşımayı yok saymamalı
    _TN = dict(bina_tipi="Konut", bina_yuksekligi=18, yapi_yuksekligi=20, N=6, h=3,
               hizli1=36, hizli2=3, P=6, kapi_genisligi=900,
               kapi_tipi="Merkezden Açılan Oto.")
    _s = TR.hesapla_tek(_TN)
    _o = _s["ozet"]
    _not = [b for b in _s["bolumler"] if b["baslik"].startswith("GEREKLİ")][0]["notlar"][0]
    r.kontrol("kurgu doğru: taşıma bekleme'den fazla asansör istiyor",
              _o["tasima_adedi"] > _o["bekleme_adedi"])
    r.kontrol("şartlı notu taşıma adedinin altına inmiyor",
              f"({int(_o['esik_sartli'])} sn) için {int(_o['tasima_adedi'])} adet" in _not)


    # ---- EK NÜFUS: pafta notu KENDİ İÇİNDE TUTARLI olmalı  ( denetim 2.5 )
    #  Kusur:  ⑤/⑥ dışında elle nüfus eklendiğinde not "Daire adedi 44 →
    #  b = 44 × 5 = 1.360 kişi" diye yazıyordu.  44 × 5 = 220'dir; denetimde
    #  bu satır hesap hatası olarak okunur.  Ek kalemler artık ayrı yazılır.
    _EK = [{"aciklama": "Zemin kattaki dükkânlar", "miktar": 420,
            "kalem": "İŞ MERKEZİ — Çalışma alanı"},
           {"aciklama": "1. kat büro", "miktar": 300,
            "kalem": "İŞ MERKEZİ — Çalışma alanı"}]
    _sn = TR.hesapla(g(ek_nufus=_EK))
    _nt = [n for b in _sn["bolumler"] for n in (b.get("notlar") or [])]
    _ana = [n for n in _nt if n.startswith("Daire adedi")]
    r.esit("ek nüfusta ana formül satırı var", len(_ana), 1)
    r.kontrol("ana formül KENDİ toplamını yazıyor ( 44 × 5 = 220 )",
              bool(_ana) and "= 220 kişi" in _ana[0], f"→ {_ana}")
    r.esit("her ek nüfus kalemi ayrı satırda",
           len([n for n in _nt if n.startswith("Ek nüfus —")]), 2)
    _top = [n for n in _nt if n.startswith("Toplam  b = Σc")]
    r.esit("toplam satırı var", len(_top), 1)
    r.kontrol("toplam satırı b ile aynı",
              bool(_top) and f"= {TRS(_sn['ozet']['b'], 0)} kişi" in _top[0].replace(",00", ""),
              f"→ {_top} · b = {_sn['ozet']['b']}")
    #  ek nüfus YOKKEN not değişmemeli
    _nt0 = [n for b in TR.hesapla(g())["bolumler"] for n in (b.get("notlar") or [])]
    r.esit("ek nüfus yokken fazladan satır eklenmiyor",
           len([n for n in _nt0 if n.startswith(("Ek nüfus —", "Toplam  b"))]), 0)

    # ------------------------------- Koruma iletkeni ( PE )  —  Çizelge-8
    #  Elektrik Tesislerinde Topraklamalar Yönetmeliği m.9-e1/ii.
    #  Beklenen değerler ÇİZELGEDEN, motorun kendi çıktısından değil.
    for S, bek in ((1.5, 1.5), (2.5, 2.5), (4, 4), (6, 6), (10, 10), (16, 16),
                   (25, 16), (35, 16), (50, 25), (70, 35),
                   #  S/2 standart kesite düşmeyen satırlar:  BİR ÜST kesit
                   (95, 50), (120, 70), (150, 95), (185, 95),
                   (240, 120), (300, 150), (400, 240)):
        r.esit(f"Çizelge-8  S = {S} → SPE", T.koruma_iletkeni_kesiti(S)[0], bek)
    #  Çizelge bir ASGARİ verir:  seçilen kesit ham değerin ALTINA düşemez.
    r.kontrol("SPE hiçbir S'te ham değerin altına düşmüyor",
              all(T.koruma_iletkeni_kesiti(S)[0] >= T.koruma_iletkeni_kesiti(S)[1]
                  for S in T.STANDART_KESITLER))
    #  Monotonluk:  faz kesiti büyürken PE küçülemez.
    _pe = [T.koruma_iletkeni_kesiti(S)[0] for S in T.STANDART_KESITLER]
    r.kontrol("SPE faz kesitiyle birlikte artıyor  ( azalmıyor )",
              all(a <= b for a, b in zip(_pe, _pe[1:])), f"→ {_pe}")
    #  Seçilen kesit her zaman STANDART merdivende olmalı.
    r.kontrol("SPE her zaman standart bir kesit",
              all(T.koruma_iletkeni_kesiti(S)[0] in T.STANDART_KESITLER
                  for S in (3, 7.5, 22, 44, 77, 111, 199, 333)))
    #  Yuvarlama bayrağı yalnız ham değer standart değilken kalkar.
    r.esit("95 mm² yuvarlandı bayrağı", T.koruma_iletkeni_kesiti(95)[2], True)
    r.esit("50 mm² yuvarlanmadı", T.koruma_iletkeni_kesiti(50)[2], False)
    #  Kenar durumlar sessizce sayı uydurmamalı.
    for bozuk in (None, 0, -5, "6", True):
        r.kontrol(f"SPE({bozuk!r}) kontrol edilemedi",
                  T.koruma_iletkeni_kesiti(bozuk)[0] is None)
    r.kontrol("merdivenin üstünde SPE = None",
              T.koruma_iletkeni_kesiti(900)[0] is None)

    # ---------- Ana potansiyel dengeleme ve topraklama iletkeni  ( m.9-j · m.9/c )
    #  Sapd = 0,5 × en büyük PE ,  en az 6 ,  en çok 25 mm² Cu.
    for pe, bek in ((4, 6), (6, 6), (10, 6), (12, 6), (16, 10), (25, 16),
                    (35, 25), (50, 25), (70, 25), (95, 25), (240, 25)):
        r.esit(f"Çizelge-4b  PE = {pe} → Sapd", T.ana_potansiyel_dengeleme_kesiti(pe)[0], bek)
    r.kontrol("Sapd hiçbir PE'de 6 mm²'nin altına inmiyor",
              all(T.ana_potansiyel_dengeleme_kesiti(pe)[0] >= 6
                  for pe in T.STANDART_KESITLER))
    r.kontrol("Sapd 25 mm²'yi aşmıyor  ( m.9-j/1/i üst sınırı )",
              all(T.ana_potansiyel_dengeleme_kesiti(pe)[0] <= 25
                  for pe in T.STANDART_KESITLER))
    #  ham ARTIK ÜST SINIRSIZ döner ( pafta "0,5·95 = 47,50" yazabilsin diye ),
    #  bu yüzden ölçüt ham'ın kendisi değil, ham ile 25 mm²'nin KÜÇÜĞÜDÜR.
    r.kontrol("Sapd bağlayıcı değerin altına düşmüyor",
              all(T.ana_potansiyel_dengeleme_kesiti(pe)[0]
                  >= min(T.ana_potansiyel_dengeleme_kesiti(pe)[1], T.APD_UST_SINIR)
                  for pe in T.STANDART_KESITLER))
    #  ham, üst sınır uygulanmadan önceki GERÇEK değer olmalı — paftadaki
    #  "0,5 · SPE = …" satırı kendi içinde doğru çıksın.
    for pe in (50, 95, 240):
        r.esit(f"ham = 0,5 × {pe}  ( sınırsız )",
               T.ana_potansiyel_dengeleme_kesiti(pe)[1], max(6, pe / 2))
    r.esit("üst sınır bayrağı  PE = 70", T.ana_potansiyel_dengeleme_kesiti(70)[2], True)
    r.esit("üst sınır bayrağı  PE = 25", T.ana_potansiyel_dengeleme_kesiti(25)[2], False)
    #  Stopr:  m.9-e değeri ile Çizelge-4a'nın 16 mm²'sinin büyüğü.
    for pe, bek in ((4, 16), (10, 16), (16, 16), (25, 25), (95, 95)):
        r.esit(f"Çizelge-4a  PE = {pe} → Stopr", T.topraklama_iletkeni_kesiti(pe)[0], bek)
    r.kontrol("Stopr hiçbir PE'de 16 mm²'nin altına inmiyor",
              all(T.topraklama_iletkeni_kesiti(pe)[0] >= 16
                  for pe in T.STANDART_KESITLER))
    r.kontrol("Stopr koruma iletkeninden küçük olamaz",
              all(T.topraklama_iletkeni_kesiti(pe)[0] >= pe
                  for pe in T.STANDART_KESITLER))
    for bozuk in (None, 0, -5, "6", True):
        r.kontrol(f"Sapd({bozuk!r}) hesaplanmıyor",
                  T.ana_potansiyel_dengeleme_kesiti(bozuk)[0] is None)
        r.kontrol(f"Stopr({bozuk!r}) hesaplanmıyor",
                  T.topraklama_iletkeni_kesiti(bozuk)[0] is None)

    # ==================================================================
    #  KARŞI AĞIRLIK RAYI ( PK ) ve DENGE ZİNCİRİ  —  MMO/697'ye göre
    # ==================================================================
    #  Kitap ( s.20 ):  "kılavuz rayı üzerinde güvenlik tertibatı etki
    #  etmemesinde k1 = 0";  iki çözümlü örnek ( s.55 · s.56 ) Pk'yı "karşı
    #  ağırlıkta güvenlik tertibatı olmadığından" hesaplamaz.  Avan PK'yı her
    #  zaman k1 ile hesaplıyordu.  Kitabın P tanımı ( s.20 ) "dengeleme
    #  halatları/zincirleri ( varsa )" katar;  avanda zincir hiç yoktu ve
    #  zincirli yüksek binada tampon kuvvetleri uygulamadan %17-23 düşüktü.
    _kap = next(k for k, v in T.TABLO_7.items() if v == 1600)
    _O = {"temel_a": 25, "temel_b": 15, "mk_yok": True}
    _A = {"tanim": "A", "kapasite": _kap, "V": 2.5, "eta": 0.85, "Hk": 85,
          "kuyu_genisligi": 2600, "kabin_boyu": 1600, "kabin_genisligi": 2100,
          "i_palanga": 2, "makine_tipi": "Dişlisiz"}

    def _oz(**ek):
        return AV.hesapla({"ortak": _O, "asansorler": [dict(_A, **ek)]})["asansorler"][0]["ozet"]

    _y, _v = _oz(), _oz(agirlik_guvenlik_tertibati="Var")
    _gn = AV.SABIT_A["gn"]
    r.esit("PK · tertibat YOK ( varsayılan ):  yalnız rayın ağırlığı ( k1 = 0 )",
           _y["PK"], tavana_yuvarla(_y["Mg"] * _gn, 10))
    r.esit("PK · tertibat VAR:  k1 · gn · Ga / n + Mg · gn",
           _v["PK"], tavana_yuvarla(_v["k1"] * _gn * _v["Ga"] / AV.SABIT_B_VARSAYILAN["n_ray"]
                                    + _v["Mg"] * _gn, 10))
    r.kontrol("PK · tertibat başka hiçbir kuvveti değiştirmiyor",
              all(_y[k] == _v[k] for k in ("P", "P1", "P2", "PR", "Fs")))

    _z = _oz(denge_zinciri="Var")
    _mz = AV.OFIS_VARSAYILAN["zincir_birim_kutle"]
    r.esit("zincir Var:  P = Gk + Gf + mz · Hk  ( ofis mz )",
           _z["P"], _y["P"] + _mz * _A["Hk"])
    r.kontrol("zincir Var:  tampon ve ray kuvvetleri büyüyor",
              all(_z[k] > _y[k] for k in ("P1", "P2", "PR", "Fs")))
    r.esit("zincir Var:  asansör bazında girilen mz kullanılıyor",
           _oz(denge_zinciri="Var", zincir_birim_kutle=6.1)["P"], _y["P"] + 6.1 * _A["Hk"])
    r.kontrol("zincir YOK iken girilmiş mz hesaba girmiyor",
              _oz(zincir_birim_kutle=6.1)["P"] == _y["P"])
    r.kontrol("aralık dışı mz asansörü durduruyor",
              AV.hesapla({"ortak": _O, "asansorler": [dict(_A, denge_zinciri="Var",
                                                          zincir_birim_kutle=-3)]})
              ["asansorler"][0]["aktif"] is False)
    #  OFİS KABULÜ TEK KAYNAKTAN:  zincir = halat ağırlığı ( λ = %100 ) ve
    #  ofisin varsayılan halat düzeni — uygulama projesiyle AYNI sayı.
    from engine.uygulama import mukavemet_girdi as _MG, mukavemet_tablolari as _MT
    from engine.uygulama import sabitler as _US
    _vg = _MG.varsayilanlar()
    #  İki haneye yuvarlanır ( üç ondalık belirsiz sayı kuralına takılır ).
    r.kontrol("ofis mz = uygulamanın varsayılan halat düzeni × λ  ( 2 haneye )",
              abs(_mz - round(_vg["aski_orani"] * _vg["halat_adedi"]
                              * _MT.halat_agirlik(_vg["halat_capi"])
                              * _US.VARSAYILAN["denge_zinciri_orani"] / 100, 2)) < 1e-9,
              f"→ avan {_mz} · uygulama {_vg['halat_adedi']} × {_vg['halat_capi']} mm × "
              f"{_vg['aski_orani']}:1")
    #  İKİ PROJE AYNI ASANSÖR İÇİN YAKIN SONUÇ VERMELİ:  zincirli yüksek bina,
    #  aynı halatların zinciriyle.  Avan kuyu yüksekliğini ( ≥ seyir ) aldığı
    #  için biraz FAZLA bulur — emniyetli yön;  eksik bulmamalı.
    from engine.uygulama import hesap as _UH, girdi as _UG
    _gu = dict(_UG.varsayilanlar(), sarilma_acisi=180, kasnak_belgesi="Var",
               beyan_yuku=1600, beyan_hizi=2.5, seyir_mesafesi=80, aski_orani=2,
               kabin_genisligi=2100, kabin_derinligi=1600, halat_capi=10, halat_adedi=9,
               tahrik_kasnak_capi=400, saptirma_kasnak_capi=400, denge_zinciri="Var",
               tampon_tipi="Hidrolik  ( enerji yutmalı )", son_kat_yuksekligi=5000,
               kuyu_dibi=2500, kabin_ray_profili="125 x 82 x 16",
               agirlik_ray_profili="89 x 62 x 15,88")
    _ua = _UH.hesapla_coklu([_gu], {"temel_a": 25, "temel_b": 15, "mk_yok": True})["asansorler"][0]
    _kz = _UG.kopru(_ua["girdi"])
    _kz["asansorler"][0].update(denge_zinciri="Var", zincir_birim_kutle=2 * 9 * _MT.halat_agirlik(10))
    _ao = AV.hesapla(_kz)["asansorler"][0]["ozet"]
    for _ad, _av, _uy in (("kabin tamponu", _ao["P1"], _ua["ozet"]["Fkt"]),
                          ("karşı ağırlık tamponu", _ao["P2"], _ua["ozet"]["Fat"])):
        r.kontrol(f"zincirli yüksek bina · {_ad}:  avan uygulamadan eksik değil, en çok %5 fazla",
                  0 <= (_av - _uy) / _uy <= 0.05,
                  f"→ avan {_av:.0f} · uygulama {_uy:.0f}")

    # ------------------------------------------------------------------
    #  HIZ BELİRLENEMEYİNCE MESAJ SEBEBİ SÖYLER
    #  Tablo-2'de olmayan bina tiplerinde ( Karma · Hastane · Poliklinik ·
    #  Otopark ) hız seçilmediğinde ve kat sayısı boş bırakıldığında kullanıcıya
    #  "tg'yi elle girin" deniyordu — oysa eksik olan HIZ ya da KAT SAYISIDIR;
    #  tg hız seçilince tablodan kendiliğinden gelir.
    # ------------------------------------------------------------------
    _tablo2_disi = [bt for bt, t in T.TABLO_10.items() if not t["hiz_grubu"]]
    r.kontrol("Tablo-2 dışı bina tipleri bilinen dördü",
              len(_tablo2_disi) == 4, f"→ {_tablo2_disi}")
    for _bt in _tablo2_disi:
        #  Tablo-9'da k değeri olmayan tiplerde k elle verilir; olanda verilmez.
        _mk = 0.1 if T.TABLO_10[_bt]["k_tipi"] is None else None
        _h = TR.hesapla_tek(g(bina_tipi=_bt, hizli1=60, hizli2=10, manuel_k=_mk)).get("hata") or ""
        r.kontrol(f"{_bt[:24]} · hız seçilmedi → sebep Tablo-2, çare V seçimi",
                  "Tablo-2'de yoktur" in _h and "Manuel değerler" in _h
                  and "tg'yi elle girin" not in _h, f"→ {_h[:120]}")
    _ho = g(bina_tipi="Hastane", hizli1=60, hizli2=None, manuel_k=None)
    r.kontrol("Hastane · ortak hız seçilince hesap yapılıyor",
              TR.hesapla_tek(dict(_ho, manuel_V=1.6)).get("hata") is None)
    r.kontrol("Hastane · hız asansör kutusundan seçilince de hesap yapılıyor  ( tek yol )",
              TR.hesapla(dict(_ho, asansorler=[{"P": 13, "kapi_genisligi": 900,
                                                "kapi_tipi": "Merkezden Açılan Oto.",
                                                "V": 1.6}])).get("hata") is None)
    #  N boşken hız bile türetilemez; mesaj eksik olanı ( N ) söylemeli.
    for _n in (None, ""):
        _h = TR.hesapla_tek(g(N=_n)).get("hata") or ""
        r.kontrol(f"kat sayısı N = {_n!r} → mesaj kat sayısını söylüyor",
                  "③ kat sayısı N" in _h and "tg" not in _h, f"→ {_h[:110]}")
    #  N girilmiş ama aralık dışıysa hız türetilir;  mesaj yine N'yi söyler, tg'yi değil.
    for _n in (0, 31):
        _h = TR.hesapla_tek(g(N=_n)).get("hata") or ""
        r.kontrol(f"kat sayısı N = {_n!r} → mesaj N aralığını söylüyor, tg demiyor",
                  "N" in _h and "30" in _h and "tg" not in _h, f"→ {_h[:110]}")
    #  ÇOKLU YOL:  farklı tipte iki asansör, Tablo-2 dışı bina, hız yok
    _cok = dict(g(bina_tipi="Katlı Otopark", hizli1=40, hizli2=10, manuel_k=None),
                asansorler=[{"P": 13, "kapi_genisligi": 900, "kapi_tipi": "Merkezden Açılan Oto."},
                            {"P": 8, "kapi_genisligi": 800, "kapi_tipi": "Teleskopik Otomatik"}])
    _hc = TR.hesapla(_cok)
    r.kontrol("çoklu · Tablo-2 dışı bina, hız yok → ASANSÖR-1 için hız mesajı",
              _hc.get("yol") == "coklu" and "ASANSÖR-1 — kabin hızı belirlenemedi" in (_hc.get("hata") or ""),
              f"→ {_hc.get('yol')} · {(_hc.get('hata') or '')[:120]}")
    _cok["asansorler"] = [dict(a, V=1.6) for a in _cok["asansorler"]]
    r.kontrol("çoklu · her asansöre hız verilince hesap yapılıyor",
              TR.hesapla(_cok).get("hata") is None, f"→ {TR.hesapla(_cok).get('hata')}")

    #  PAFTADAKİ HIZ KAYNAĞI GERÇEĞİ SÖYLER.  Her durumda "MMO/697 Tablo-2"
    #  basılıyordu — hastanede ( Tablo-2'de satırı yok ) ve hızı kullanıcı
    #  seçtiğinde bile.  Not ekranda kalır;  paftaya kaynak sütunu basılır.
    def _v_kaynak(s):
        _a = [x for b in s.get("bolumler") or [] for x in b.get("adimlar") or []
              if x.get("sembol") == "V" and x.get("aciklama") == "Kabin hızı"]
        return _a[0]["kaynak"] if _a else None
    for _ad, _g, _bek in (
            ("Konut · hız Tablo-2'den", g(), "MMO/697 Tablo-2 (durak = 12)"),
            #  12 durak konutta Tablo-2 asgarisi 1,60 m/s
            ("Konut · ortak hız Tablo-2 minimumunun üstünde", g(manuel_V=2),
             "Proje kararı ( Tablo-2 min. 1,60 m/s )"),
            ("Konut · ortak hız Tablo-2 minimumunun altında", g(manuel_V=1),
             "Proje kararı ( Tablo-2 min. 1,60 m/s )"),
            ("Konut · seçilen hız Tablo-2 minimumuna eşit", g(manuel_V=1.6),
             "MMO/697 Tablo-2 (durak = 12)"),
            ("Hastane · hız asansör kartından", dict(_ho, asansorler=[
                {"P": 13, "kapi_genisligi": 900, "kapi_tipi": "Merkezden Açılan Oto.", "V": 1.6}]),
             "Proje kararı ( Tablo-2'de yok )"),
            ("Karma · hız seçilmedi ( hesap hatası )",
             g(bina_tipi="Karma Binalar (İşyeri ve Konut)", hizli1=None, hizli2=None, manuel_k=0.1),
             "Seçilmedi ( Tablo-2'de yok )")):
        r.esit(f"paftada V kaynağı · {_ad}", _v_kaynak(TR.hesapla(_g)), _bek)

    return r


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)

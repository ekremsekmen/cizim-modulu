# -*- coding: utf-8 -*-
"""
TEST 1  —  AVAN REFERANS TARAMASI

Trafik ( tek asansör / grup ) ve avan motorunun sonuç değerlerini, girdi
uzayını sistemli tarayan senaryolarda DONDURULMUŞ referansa karşı denetler.

Referansın dayanağı:  bu senaryoların her biri ofisin eski Excel çalışma
kitaplarında LibreOffice ile yeniden hesaplanmış ve karşılaştırılan her
değer motorla aynı çıkmıştı.  Sonuçlar o doğrulanmış hâlden donduruldu
( testler/referans_avan.json.gz ).  Program artık Excel kullanmaz;  tek
hesap kaynağı motordur.

Altın çıktıdan ( TEST 7 ) farkı:  altın çıktı her metni kilitler, bu test
yalnız SONUÇ DEĞERLERİNİ ve çok daha geniş bir senaryo yelpazesinde:
bütün bina tipleri, kapasiteler, kat sınırları, hızlar, bodrum eşikleri,
ara değerli kapılar, avan kesit / verim / topraklama çeşitleri.

    python3 testler/tarama_uret.py        →  referansı YENİDEN ÜRETİR

Yeniden üretmek DAVRANIŞI DEĞİŞTİRME İZNİDİR ( bkz. altin_uret ).
"""
import gzip
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.avan import hesap as AV                               # noqa: E402
from engine.avan import tablolar as T                             # noqa: E402
from engine.avan import trafik as TR                              # noqa: E402
from testler.ortak import Rapor                                   # noqa: E402

DOSYA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "referans_avan.json.gz")


# =====================================================================
#  SENARYOLAR  —  rastgele değil, sistemli.  Tablo sınırlarını ve
#  bina tiplerini kasten zorlar.
# =====================================================================
def _nufus(bina_tipi, kucuk=False):
    """Her bina tipi için b < 200 ve b ≥ 200 üreten girdiler (n = 0,30 / 0,25)."""
    if bina_tipi == "Konut":
        return (12, 3) if kucuk else (60, 3)
    if bina_tipi.startswith(("İş Merkezi", "Kamu")):
        return (1200, None) if kucuk else (4800, None)
    if bina_tipi.startswith("Otel"):
        return (120, None) if kucuk else (400, None)
    if bina_tipi == "Hastane":
        return (40, None) if kucuk else (200, None)
    if bina_tipi == "Katlı Otopark":
        return (100, 20) if kucuk else (300, 60)
    return (None, None)


TAM_KAPI = [(800, "Teleskopik Otomatik"), (800, "Merkezden Açılan Oto."),
            (900, "Teleskopik Otomatik"), (900, "Merkezden Açılan Oto."),
            (1100, "Teleskopik Otomatik"), (1100, "Merkezden Açılan Oto."),
            (1300, "Teleskopik Otomatik"), (1300, "Merkezden Açılan Oto.")]


def tek_senaryolar():
    s = []
    # a) her bina tipi — küçük ve büyük nüfus (n katsayısının iki kolu)
    for bt, veri in T.TABLO_10.items():
        for kucuk in (True, False):
            h1, h2 = _nufus(bt, kucuk)
            if h1 is None:
                continue
            g = dict(bina_tipi=bt, bina_yuksekligi=18.0, yapi_yuksekligi=24.0, N=6, h=3.0,
                     hizli1=h1, hizli2=h2, P=10, kapi_genisligi=900,
                     kapi_tipi="Merkezden Açılan Oto.")
            if veri["k_tipi"] is None:
                g["manuel_k"] = 0.12
            if veri["hiz_grubu"] is None:
                g["manuel_V"] = 1.6
            s.append((f"bina={bt[:22]} b{'<' if kucuk else '≥'}200", g))
    # b) tüm kapasiteler  (15 kişi = MMO örnek istisnası dâhil)
    for P in T.GECERLI_KAPASITELER:
        s.append((f"P={P} kişi", dict(bina_tipi="Konut", bina_yuksekligi=30.0,
                  yapi_yuksekligi=34.0, N=10, h=3.0, hizli1=50, hizli2=3, P=P,
                  kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik")))
    # c) N sınırları  (Tablo-3/5 kapsamı 1…30)
    for N in (1, 2, 3, 9, 10, 14, 15, 19, 20, 29, 30):
        s.append((f"N={N} kat", dict(bina_tipi="Konut", bina_yuksekligi=60.0,
                  yapi_yuksekligi=66.0, N=N, h=3.0, hizli1=40, hizli2=3, P=13,
                  kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik")))
    # d) tüm geçerli hızlar  (Tablo-6 tg kademeleri + iki ara değer)
    for V in T.GECERLI_HIZLAR:
        s.append((f"V={V} m/s", dict(bina_tipi="Konut", bina_yuksekligi=45.0,
                  yapi_yuksekligi=50.0, N=15, h=3.0, hizli1=70, hizli2=3, P=16,
                  kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik", manuel_V=V)))
    # e-0) bodrum durakları — Tablo-2 durak adedini değiştirir, H/S'yi değiştirmez
    for nb in (0, 1, 2, 5, 10):
        s.append((f"bodrum={nb} durak", dict(bina_tipi="Konut", bina_yuksekligi=39.0,
                  yapi_yuksekligi=46.0, N=12, h=3.0, hizli1=60, hizli2=3, P=13,
                  kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik", bodrum=nb)))
    #   bodrum + manuel hız + Tablo-2'si olmayan bina tipi
    s.append(("bodrum + manuel V", dict(bina_tipi="Hastane", bina_yuksekligi=26.0,
              yapi_yuksekligi=34.0, N=8, h=3.3, hizli1=180, P=20, bodrum=3,
              manuel_V=1.6, kapi_genisligi=1300, kapi_tipi="Merkezden Açılan Oto.")))
    #   bodrum eşiği: Konut'ta durak 14→15 geçişi hızı 1,6'dan 2,0'a çıkarır
    for nb in (1, 2):
        s.append((f"bodrum eşiği nb={nb}", dict(bina_tipi="Konut", bina_yuksekligi=40.0,
                  yapi_yuksekligi=46.0, N=13, h=3.0, hizli1=60, hizli2=3, P=10,
                  kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik", bodrum=nb)))
    # e-1) ARA DEĞERLİ kapı genişlikleri — Tablo-4 (1000/1200) ve Tablo-8 (700)
    for kg in T.KAPI_GENISLIKLERI:
        for kt in ("Teleskopik Otomatik", "Merkezden Açılan Oto."):
            s.append((f"ara kapı {kg} {kt[:10]}", dict(bina_tipi="Konut",
                      bina_yuksekligi=33.0, yapi_yuksekligi=38.0, N=10, h=3.0,
                      hizli1=48, hizli2=3, P=13, kapi_genisligi=kg, kapi_tipi=kt)))
    #   kabin içi kapı — tabloda olan genişlikler
    for kg in (700, 800, 900, 1000, 1100):
        s.append((f"kabin içi {kg}", dict(bina_tipi="Konut", bina_yuksekligi=33.0,
                  yapi_yuksekligi=38.0, N=10, h=3.0, hizli1=48, hizli2=3, P=13,
                  kapi_genisligi=kg, kapi_tipi="Kabin İçi Oto. Kat K.Ç.")))
    # e) tüm tam hesaplanabilir kapı birleşimleri
    for kg, kt in TAM_KAPI:
        s.append((f"kapı {kg} {kt[:12]}", dict(bina_tipi="Otel (4* ve üzeri)",
                  bina_yuksekligi=40.0, yapi_yuksekligi=45.0, N=12, h=3.2,
                  hizli1=260, hizli2=None, P=16, kapi_genisligi=kg, kapi_tipi=kt)))
    # f) yükseklik eşiği — Standart / Yükseltilmiş sınırı (BYKHY md.4)
    for by, yy, ad in ((21.50, 30.50, "eşikte"), (21.51, 30.50, "bina>21,5"),
                       (21.50, 30.51, "yapı>30,5")):
        s.append((f"standart {ad}", dict(bina_tipi="Konut", bina_yuksekligi=by,
                  yapi_yuksekligi=yy, N=7, h=3.0, hizli1=45, hizli2=3, P=10,
                  kapi_genisligi=900, kapi_tipi="Merkezden Açılan Oto.")))
    # g) elle süre girişleri ve elle asansör adedi
    s.append(("elle ta/tk/tg/tp", dict(bina_tipi="Konut", bina_yuksekligi=30.0,
              yapi_yuksekligi=34.0, N=10, h=3.0, hizli1=50, hizli2=3, P=10,
              kapi_genisligi=900, kapi_tipi="Merkezden Açılan Oto.",
              manuel_ta=2.1, manuel_tk=2.7, manuel_tg=5.9, manuel_tp=1.05)))
    s.append(("elle adet=4", dict(bina_tipi="Konut", bina_yuksekligi=30.0,
              yapi_yuksekligi=34.0, N=10, h=3.0, hizli1=50, hizli2=3, P=10,
              kapi_genisligi=900, kapi_tipi="Merkezden Açılan Oto.", manuel_adet=4)))
    # h) ondalık kat yüksekliği ve ondalık oda sayısı
    s.append(("h=2,85 / oda=2,4", dict(bina_tipi="Konut", bina_yuksekligi=28.5,
              yapi_yuksekligi=33.0, N=10, h=2.85, hizli1=48, hizli2=2.4, P=13,
              kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik")))
    return s


def coklu_senaryolar():
    s = []
    KAP = [(8, 800), (10, 900), (13, 1100), (16, 1100), (20, 1100), (25, 1300)]
    for n in (1, 2, 3, 4):
        s.append((f"{n} asansör", dict(bina_tipi="Konut", bina_yuksekligi=39.98,
                  yapi_yuksekligi=43.0, N=11, h=3.0, hizli1=44, hizli2=3,
                  asansorler=[dict(P=KAP[i][0], kapi_genisligi=KAP[i][1],
                                   kapi_tipi="Teleskopik Otomatik") for i in range(n)])))
    # farklı durak sayısı (asansör bazında N)
    s.append(("farklı durak", dict(bina_tipi="Konut", bina_yuksekligi=39.98,
              yapi_yuksekligi=43.0, N=11, h=3.0, hizli1=44, hizli2=3,
              asansorler=[dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik", durak=12),
                          dict(P=16, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik", durak=6),
                          dict(P=13, kapi_genisligi=1100, kapi_tipi="Merkezden Açılan Oto.", durak=4)])))
    # asansör bazında hız ve kat yüksekliği
    s.append(("asansör bazında V/h", dict(bina_tipi="İş Merkezi (Çok Firmalı)",
              bina_yuksekligi=48.0, yapi_yuksekligi=54.0, N=16, h=3.0, hizli1=7200,
              asansorler=[dict(P=16, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik", V=2.5),
                          dict(P=20, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik", V=3.5, h=3.4)])))
    # Tablo-9'da olmayan bina tipi + manuel k
    s.append(("karma bina, manuel k/V", dict(bina_tipi="Karma Binalar (İşyeri ve Konut)",
              bina_yuksekligi=35.0, yapi_yuksekligi=40.0, N=12, h=3.0, hizli1=None,
              manuel_k=0.13, manuel_V=2.0,
              ek_nufus=[{"aciklama": "Ofis katları", "miktar": 3600,
                         "kalem": "İŞ MERKEZİ — Çalışma alanı"},
                        {"aciklama": "Konut ilk yatak odası", "miktar": 20,
                         "kalem": "KONUT — İlk yatak odası"}],
              asansorler=[dict(P=13, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik"),
                          dict(P=13, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik")])))
    # bodrum: ortak ve asansör bazında
    s.append(("çoklu ortak bodrum", dict(bina_tipi="Konut", bina_yuksekligi=39.98,
              yapi_yuksekligi=46.0, N=11, h=3.0, hizli1=44, hizli2=3, bodrum=3,
              asansorler=[dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik"),
                          dict(P=16, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik")])))
    s.append(("çoklu asansör bazında bodrum", dict(bina_tipi="Konut", bina_yuksekligi=39.98,
              yapi_yuksekligi=46.0, N=11, h=3.0, hizli1=44, hizli2=3, bodrum=1,
              asansorler=[dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik", bodrum=0),
                          dict(P=13, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik", bodrum=4),
                          dict(P=16, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik",
                               bodrum=2, durak=8)])))
    # asansör bazında imalatçı süreleri
    s.append(("çoklu manuel süreler", dict(bina_tipi="Konut", bina_yuksekligi=39.98,
              yapi_yuksekligi=43.0, N=11, h=3.0, hizli1=44, hizli2=3,
              asansorler=[dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik",
                               manuel_ta=2.9, manuel_tk=3.4),
                          dict(P=13, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik",
                               manuel_tg=6.2, manuel_tp=1.15),
                          dict(P=16, kapi_genisligi=1300, kapi_tipi="Kabin İçi Oto. Kat K.Ç.",
                               manuel_ta=6.0, manuel_tk=6.0, manuel_tg=5.5, manuel_tp=0.95)])))
    # ara değerli kapılar (Tablo-4 1000/1200, Tablo-8 700)
    s.append(("çoklu ara kapılar", dict(bina_tipi="Konut", bina_yuksekligi=39.98,
              yapi_yuksekligi=43.0, N=11, h=3.0, hizli1=44, hizli2=3,
              asansorler=[dict(P=10, kapi_genisligi=700, kapi_tipi="Teleskopik Otomatik"),
                          dict(P=13, kapi_genisligi=1000, kapi_tipi="Merkezden Açılan Oto."),
                          dict(P=16, kapi_genisligi=1200, kapi_tipi="Teleskopik Otomatik")])))
    # hastane (Tablo-2'de yok → manuel V)
    s.append(("hastane, manuel V", dict(bina_tipi="Hastane", bina_yuksekligi=26.0,
              yapi_yuksekligi=31.0, N=8, h=3.3, hizli1=180, manuel_V=1.6,
              asansorler=[dict(P=20, kapi_genisligi=1300, kapi_tipi="Merkezden Açılan Oto."),
                          dict(P=25, kapi_genisligi=1300, kapi_tipi="Merkezden Açılan Oto.")])))
    return s


def avan_senaryolar():
    """Senaryo başına en çok 4 asansör."""
    ORT = dict(U=380, kappa=56, eps_max=3, temel_a=26.55, temel_b=16.4, beta=150,
               serit_L=58.5, cubuk_sayisi=4, mk_uzunluk=0, mk_genislik=0)

    def A(**kw):
        t = dict(tanim="A", kapasite=10, V=1.6, eta=0.85, Hk=32.85, kuyu_genisligi=1800,
                 kabin_boyu=1450, kabin_genisligi=1300, gr=17.91, Fmk=350, Fsh=100,
                 Nsc=11, S1=6, L1=32.85, S2=6, L2=3, kablo_tipi="NHXMH FE180")
        t.update(kw)
        return t

    s = []
    # a) tüm kapasiteler (4'erli gruplar)
    kaps = T.GECERLI_KAPASITELER
    for i in range(0, len(kaps), 4):
        grup = kaps[i:i + 4]
        s.append((f"kapasite {grup}", {"ortak": ORT,
                  "asansorler": [A(kapasite=p, tanim=f"{p} kişi") for p in grup]}))
    # b) k1 darbe faktörünün üç kademesi + palanga 1/2
    s.append(("k1 kademeleri", {"ortak": ORT, "asansorler": [
        A(V=0.63, tanim="k1=5"), A(V=1.0, tanim="k1=3"), A(V=1.6, tanim="k1=2"), A(V=2.5, tanim="k1=2")]}))
    s.append(("palanga i=1", {"ortak": ORT, "sabitler": {"i_palanga": 1},
                              "asansorler": [A(tanim="doğrudan askı")]}))
    # b-2) askı ve denge ASANSÖR BAZINDA — dişlili + dişlisiz karışık proje
    s.append(("asansör bazında askı/denge", {"ortak": ORT, "asansorler": [
        A(tanim="2:1 dişlisiz"),
        A(tanim="1:1 dişlili", eta=0.50, i_palanga=1, q_denge=0.40),
        A(tanim="2:1 q=0,45", kapasite=16, q_denge=0.45),
        A(tanim="1:1 q=0,55", kapasite=13, i_palanga=1, q_denge=0.55)]}))
    # b-3) MAKİNE TİPİ × ASKI ORANI — MMO/697 dört birleşimi
    s.append(("makine tipi × askı (MMO)", {"ortak": ORT, "asansorler": [
        A(tanim="dişli 1:1",    makine_tipi="Dişli",    eta=0.50, i_palanga=1),
        A(tanim="dişli 2:1",    makine_tipi="Dişli",    eta=0.50, i_palanga=2),
        A(tanim="dişlisiz 1:1", makine_tipi="Dişlisiz", eta=0.85, i_palanga=1),
        A(tanim="dişlisiz 2:1", makine_tipi="Dişlisiz", eta=0.85, i_palanga=2)]}))
    # b-4) KATALOG VERİMİ — palangalı sistemde η′ = η − 0,10 ( MMO/697 §2.4 )
    s.append(("katalog makine verimi", {"ortak": ORT, "asansorler": [
        A(tanim="dişli 1:1", makine_tipi="Dişli", eta=0.60, i_palanga=1),
        A(tanim="dişlisiz 2:1", makine_tipi="Dişlisiz", eta=0.82, i_palanga=2),
        A(tanim="dişlisiz 2:1 ofis", makine_tipi="Dişlisiz", eta=0.85, i_palanga=2),
        A(tanim="dişlisiz 2:1 katalog", makine_tipi="Dişlisiz", eta=0.78,
          i_palanga=2)]}))
    # b-5) OFİS VARSAYILANLARI — alanlar BOŞ bırakılır, ofis standardına düşer.
    BOS_ORT = dict(temel_a=26.55, temel_b=16.4, serit_L=58.5,
                   mk_uzunluk=0, mk_genislik=0)

    def AB(**kw):
        """Ofis varsayılanına düşen alanları HİÇ vermeyen asansör."""
        t = dict(tanim="A", kapasite=10, V=1.6, eta=0.85, Hk=32.85,
                 kuyu_genisligi=1800, kabin_boyu=1450, kabin_genisligi=1300)
        t.update(kw)
        return t

    s.append(("ofis varsayılanları — alanlar boş", {"ortak": BOS_ORT, "asansorler": [
        AB(tanim="tamamı ofis"),
        AB(tanim="16 kişi — motor otomatik", kapasite=16),
        AB(tanim="ray ezilmiş", gr=23.7),
        AB(tanim="L1 elle", L1=45.5, Nsc=22)]}))
    s.append(("ofis varsayılanı değiştirilmiş", {"ortak": BOS_ORT,
              "sabitler": {"gr": 23.7, "Fmk": 480, "Fsh": 120, "S1": 10, "S2": 10,
                           "L2": 4.5, "L1_pay": 5, "U": 400, "kappa": 58,
                           "eps_max": 4, "beta": 90, "cubuk_sayisi": 6},
              "asansorler": [AB(tanim="yeni ofis standardı"),
                             AB(tanim="25 kişi", kapasite=25, V=2.5)]}))
    s.append(("ofis standardı + asansör bazı", {"ortak": ORT,
              "sabitler": {"i_palanga": 1, "q_denge": 0.42}, "asansorler": [
                  A(tanim="ofis standardı"),
                  A(tanim="ezilmiş", i_palanga=2, q_denge=0.55)]}))
    # c) makine dairesi — kutu işaretli / işaretsiz
    s.append(("makine daireli", {"ortak": dict(ORT, mk_yok=False, mk_uzunluk=4200,
                                               mk_genislik=3100),
                                 "asansorler": [A(), A(kapasite=16)]}))
    s.append(("MRL kutusu işaretli", {"ortak": dict(ORT, mk_yok=True),
                                      "asansorler": [A()]}))
    s.append(("MRL kutusu işaretli ama ölçü var",
              {"ortak": dict(ORT, mk_yok=True, mk_uzunluk=4200, mk_genislik=3100),
               "asansorler": [A()]}))
    # d) topraklama varyasyonları
    s.append(("çubuksuz topraklama", {"ortak": dict(ORT, cubuk_sayisi=0), "asansorler": [A()]}))
    s.append(("β=300, 8 çubuk", {"ortak": dict(ORT, beta=300, cubuk_sayisi=8, serit_L=120),
                                 "asansorler": [A()]}))
    #  d-2) ŞERİT BOYU TÜRETİLEN — ofiste yalnız uzunluk ve genişlik girilir
    #  ( ofis paftası ölçüleri: 31,05 × 18,90 m ).
    TUR_ORT = dict(temel_a=31.05, temel_b=18.9, mk_uzunluk=0, mk_genislik=0)
    s.append(("şerit boyu türetilen — L boş",
              {"ortak": TUR_ORT, "asansorler": [A(tanim="ofis temeli")]}))
    s.append(("şerit boyu türetilen — göz 10 m",
              {"ortak": TUR_ORT, "sabitler": {"goz_araligi": 10},
               "asansorler": [A(tanim="sık karelaj")]}))
    s.append(("şerit boyu türetilen — enine bağ gerekmiyor",
              {"ortak": dict(temel_a=15.0, temel_b=10.0, mk_uzunluk=0, mk_genislik=0),
               "asansorler": [A(tanim="küçük temel")]}))
    # e) elektrik: farklı kesit / uzunluk / gerilim / alüminyum iletken
    s.append(("400 V, alüminyum", {"ortak": dict(ORT, U=400, kappa=35),
                                   "asansorler": [A(S1=10, L1=60), A(S1=16, L1=95, kapasite=20)]}))
    s.append(("kesit yetersiz", {"ortak": ORT, "asansorler": [A(S1=1.5, L1=180, Nsc=18.5)]}))
    # f) Tablo-11 ara değerler + elle Gk / elle Q
    s.append(("Q elle 1125 / Gk elle", {"ortak": ORT, "asansorler": [
        A(kapasite=None, Q_elle=1125, tanim="MMO örneği"),
        A(Gk_elle=740, tanim="imalatçı Gk"),
        A(kapasite=None, Q_elle=900, tanim="ara yük"),
        A(kapasite=None, Q_elle=1400, tanim="ara yük 2")]}))
    # g) uç boyutlar — küçük kabin / uzun kuyu / dişli makine
    s.append(("uç boyutlar", {"ortak": ORT, "asansorler": [
        A(Hk=9.0, kuyu_genisligi=1500, kabin_boyu=1100, kabin_genisligi=1100, tanim="kısa kuyu"),
        A(Hk=70.0, kuyu_genisligi=2650, kabin_boyu=2100, kabin_genisligi=1600, Nsc=18.5, tanim="uzun kuyu"),
        A(eta=0.50, tanim="dişli makine"),
        A(gr=8.9, tanim="T89 ray")]}))
    # h) ofis standardı değiştirilmiş
    s.append(("ofis standardı değişik", {
        "ortak": ORT,
        "sabitler": {"q_denge": 0.45, "gf": 2.0, "Fmt": 120, "kuyu_Dmax": 0,
                     "priz_adedi": 4, "priz_gucu": 250, "cosfi": 0.85,
                     "kuyu_armatur_lm": 2100, "kabin_armatur_lm": 400, "ayd_sutun": 5},
        "asansorler": [A(), A(kapasite=16, V=1.0)]}))
    return s


# =====================================================================
#  KARŞILAŞTIRILAN SONUÇLAR
# =====================================================================
TEK_ANAHTARLAR = ("standart", "p", "b", "n_artis", "B", "V", "H", "S", "ta", "tk",
                  "tg", "tp", "k", "tv", "ts", "TR", "R", "adet", "Ieer",
                  "esik_standart", "esik_yukseltilmis", "sonuc", "yuk_kg",
                  "bodrum", "toplam_seyahat")
COKLU_ANAHTARLAR = ("standart", "b", "n_artis", "B", "k", "Res", "gereken", "TRes",
                    "Izul", "sonuc", "bodrum")
COKLU_ASANSOR_ANAHTARLARI = ("p", "H", "S", "ta", "tk", "tg", "tp", "tv", "ts",
                             "TR", "R", "yuk_kg", "V", "N", "bodrum")
AVAN_ANAHTARLAR = ("Q", "V", "q_denge", "i_palanga", "eta", "N_hes", "Nsc", "Gk", "Gf",
                   "P", "Ga", "k1", "Lr", "Mg", "P1", "P2", "PR", "PK", "Fs",
                   "kabin_a", "kabin_b", "k_kabin", "eta_kabin", "T_kabin", "Z_kabin",
                   "n_kabin", "kuyu_a", "kuyu_b", "k_kuyu", "eta_kuyu", "T_kuyu",
                   "Z_kuyu", "n1_kuyu", "n2_kuyu", "n_kuyu", "g_motor", "g_kuyu",
                   "g_kabin", "g_priz", "P_kurulu", "eps1", "eps2", "eps", "I", "Iz")
TOPRAKLAMA_ANAHTARLARI = ("A", "r", "D", "Ry", "Rc", "Re", "Re_max")
MAKINE_DAIRESI_ANAHTARLARI = ("k", "eta", "T", "Z", "n")


def _kopya(g):
    return json.loads(json.dumps(g))


def tek_sonucu(g):
    s = TR.hesapla_tek(_kopya(g))
    if s.get("hata"):
        return {"hata": s["hata"]}
    return {k: s["ozet"][k] for k in TEK_ANAHTARLAR}


def coklu_sonucu(g):
    s = TR.hesapla_coklu(_kopya(g))
    if s.get("hata"):
        return {"hata": s["hata"]}
    return {"ozet": {k: s["ozet"][k] for k in COKLU_ANAHTARLAR},
            "asansorler": [{k: a[k] for k in COKLU_ASANSOR_ANAHTARLARI}
                           for a in s["asansorler"]]}


def avan_sonucu(v):
    s = AV.hesapla(_kopya(v))
    tp, mk = s["topraklama"], s["makine_dairesi"]
    return {"asansorler": [({k: a["ozet"][k] for k in AVAN_ANAHTARLAR}
                            if a and a.get("aktif") else None)
                           for a in s["asansorler"]],
            "topraklama": ({k: tp[k] for k in TOPRAKLAMA_ANAHTARLARI}
                           if tp.get("aktif") else None),
            "makine_dairesi": ({k: mk[k] for k in MAKINE_DAIRESI_ANAHTARLARI}
                               if mk.get("aktif") else None)}


AILELER = (("tek", tek_senaryolar, tek_sonucu),
           ("coklu", coklu_senaryolar, coklu_sonucu),
           ("avan", avan_senaryolar, avan_sonucu))


def uret():
    """Referans kaydı  —  { aile : [ { ad, girdi, sonuc } ] }."""
    return {aile: [{"ad": ad, "girdi": _kopya(g), "sonuc": _kopya(motor(g))}
                   for ad, g in senaryo()]
            for aile, senaryo, motor in AILELER}


# =====================================================================
#  KARŞILAŞTIRMA
# =====================================================================
def _yapraklar(yol, bulunan, beklenen):
    """İki JSON ağacını yaprak yaprak eşler  →  ( yol, bulunan, beklenen )."""
    if isinstance(beklenen, dict) and isinstance(bulunan, dict):
        for k in sorted(set(beklenen) | set(bulunan)):
            yield from _yapraklar(f"{yol}.{k}" if yol else k,
                                  bulunan.get(k, "<yok>"), beklenen.get(k, "<yok>"))
        return
    if (isinstance(beklenen, list) and isinstance(bulunan, list)
            and len(beklenen) == len(bulunan)):
        for i, (a, b) in enumerate(zip(bulunan, beklenen)):
            yield from _yapraklar(f"{yol}[{i}]", a, b)
        return
    yield yol, bulunan, beklenen


def _ayni(bulunan, beklenen):
    sayi = (int, float)
    if (isinstance(beklenen, sayi) and isinstance(bulunan, sayi)
            and not isinstance(beklenen, bool) and not isinstance(bulunan, bool)):
        return abs(bulunan - beklenen) <= 1e-9 * max(1.0, abs(beklenen))
    return bulunan == beklenen


def karsilastir(r, dosya, simdi, etiket):
    """Her senaryonun her sonuç değeri referansla ayrı bir kontrol olarak."""
    with gzip.open(dosya, "rt", encoding="utf-8") as f:
        referans = json.load(f)
    for aile in referans:
        eski, yeni = referans[aile], simdi.get(aile, [])
        if not r.esit(f"[{etiket} · {aile}] senaryo sayısı", len(yeni), len(eski)):
            continue
        for e, y in zip(eski, yeni):
            ad = e["ad"]
            r.kontrol(f"[{etiket} · {aile}] {ad} · girdi değişmemiş",
                      y["girdi"] == e["girdi"] and y["ad"] == ad,
                      "→ senaryo tanımı değişti; bilerek değiştirildiyse "
                      "referansı yeniden üretin")
            for yol, bulunan, beklenen in _yapraklar("", y["sonuc"], e["sonuc"]):
                r.kontrol(f"[{etiket} · {aile}] {ad} · {yol}", _ayni(bulunan, beklenen),
                          f"→ bulunan {bulunan!r}, referans {beklenen!r}")


def calistir():
    print("\n\033[1mTEST 1 — AVAN REFERANS TARAMASI\033[0m"
          "   (trafik + avan sonuçları dondurulmuş referansa karşı)")
    r = Rapor("Avan referans taraması")
    if not os.path.isfile(DOSYA):
        r.kontrol("referans dosyası var", False,
                  f"→ {os.path.basename(DOSYA)} yok — python3 testler/tarama_uret.py")
        return r
    karsilastir(r, DOSYA, uret(), "avan")
    return r


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)

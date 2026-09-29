# -*- coding: utf-8 -*-
"""
ALTIN ÇIKTI ÜRETİCİ  —  refactor kalkanı

Trafik motorunun TAM çıktısını ( her adım, her uyarı, her not, her pafta
satırı ) çok sayıda senaryo için dondurur.  test_altin.py bunu her koşuda
yeniden üretip karşılaştırır.

NİÇİN:  mevcut testler BELİRLİ DEĞERLERİ ( TR, adet, Izul ) kontrol eder.
Refactor'da asıl risk onlar değil — uyarıların SIRASI, bir notun düşmesi,
bir adım satırının kaybolması gibi kimsenin assert etmediği şeylerdir.
Altın çıktı bunların hepsini kilitler:  bir karakter değişirse test söyler.

    python3 testler/altin_uret.py        → dosyayı YENİDEN ÜRETİR

Yeniden üretmek DAVRANIŞI DEĞİŞTİRME İZNİDİR.  Refactor sırasında ASLA
çalıştırılmaz;  yalnız kasıtlı bir davranış değişikliğinden sonra, diff
gözle incelenip onaylandığında çalıştırılır.
"""
import gzip
import itertools
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.avan import hesap as AV                               # noqa: E402
from engine.avan import tablolar as T                              # noqa: E402
from engine.avan import trafik as TR                            # noqa: E402
from engine.uygulama import hesap as UY                        # noqa: E402

_KLASOR = os.path.dirname(os.path.abspath(__file__))
DOSYA = os.path.join(_KLASOR, "altin_trafik.json.gz")
DOSYA_AVAN = os.path.join(_KLASOR, "altin_avan.json.gz")
DOSYA_UYGULAMA = os.path.join(_KLASOR, "altin_uygulama.json.gz")


def senaryolar():
    """Tek ve çoklu yolu, tablo sınırlarını ve manuel ezmeleri tarayan girdiler."""
    kapilar = [(700, "Teleskopik Otomatik"), (900, "Merkezden Açılan Oto."),
               (1000, "Teleskopik Otomatik"), (1200, "Merkezden Açılan Oto."),
               (1300, "Kabin İçi Oto. Kat K.Ç.")]
    # 1) bina tipi × kat × kapasite  ( tek asansör )
    for bt in T.BINA_TIPLERI:
        for N in (1, 5, 11, 20, 30):
            for P in (6, 10, 16, 30):
                kg, kt = kapilar[(N + P) % len(kapilar)]
                yield {"bina_tipi": bt, "bina_yuksekligi": 39.98, "yapi_yuksekligi": 43,
                       "N": N, "h": 3, "hizli1": 44, "hizli2": 3, "manuel_k": 0.1,
                       "asansorler": [{"P": P, "kapi_genisligi": kg, "kapi_tipi": kt}]}
    # 2) yükseklik / bodrum / hız ezmeleri
    for by, yy in ((10, 12), (21.5, 30.5), (22, 31), (60, 70)):
        for bod in (None, 0, 2, 10):
            for V in (None, 0.63, 1.6, 3.5):
                yield {"bina_tipi": "Konut", "bina_yuksekligi": by, "yapi_yuksekligi": yy,
                       "N": 12, "h": 3.2, "hizli1": 60, "hizli2": 2, "bodrum": bod,
                       "manuel_V": V,
                       "asansorler": [{"P": 13, "kapi_genisligi": 1100,
                                       "kapi_tipi": "Teleskopik Otomatik"}]}
    # 3) manuel süre ezmeleri  ( uyarı metinlerini tetikler )
    for mta, mtk, mtg, mtp in itertools.product((None, 2.4), (None, 3.1),
                                                (None, 5.9), (None, 1.15)):
        yield {"bina_tipi": "Otel (4* ve üzeri)", "bina_yuksekligi": 30,
               "yapi_yuksekligi": 33, "N": 9, "h": 3, "hizli1": 120,
               "asansorler": [{"P": 16, "kapi_genisligi": 1000,
                               "kapi_tipi": "Teleskopik Otomatik",
                               "manuel_ta": mta, "manuel_tk": mtk,
                               "manuel_tg": mtg, "manuel_tp": mtp}]}
    # 4) çoklu yol  —  farklı tipler, asansör bazında durak / h / bodrum
    for n in (2, 3, 4):
        for fark in ("P", "kapi", "V", "durak", "h", "bodrum"):
            liste = []
            for i in range(n):
                a = {"P": 10, "kapi_genisligi": 900, "kapi_tipi": "Teleskopik Otomatik"}
                if fark == "P":      a["P"] = (10, 16, 20, 25)[i]
                if fark == "kapi":   a["kapi_genisligi"] = (900, 1100, 1300, 800)[i]
                if fark == "V":      a["V"] = (1.6, 2, 2.5, 1)[i]
                if fark == "durak":  a["durak"] = (12, 9, 7, 5)[i]
                if fark == "h":      a["h"] = (3, 3.2, 2.9, 3.5)[i]
                if fark == "bodrum": a["bodrum"] = (0, 1, 2, 3)[i]
                liste.append(a)
            yield {"bina_tipi": "Konut", "bina_yuksekligi": 39.98, "yapi_yuksekligi": 43,
                   "N": 11, "h": 3, "hizli1": 44, "hizli2": 3, "asansorler": liste}
    # 4b) çoklu — ARA DEĞER kapılar ve elle süreler.
    #  Bu senaryolar eskiden YOKTU:  Tablo-4 ( 1000 / 1200 mm ) ve Tablo-8
    #  ( 700 mm ) ara değer uyarıları ile "imalatçı verisi" uyarısı çoklu
    #  yolda hiç tetiklenmiyordu — kalkan o metinleri korumuyordu.
    for kg1, kg2, mta, mtp in ((1000, 700, None, None), (1200, 1000, 2.6, None),
                               (700, 1200, None, 1.15), (900, 1300, 2.4, 1.0)):
        yield {"bina_tipi": "Konut", "bina_yuksekligi": 39.98, "yapi_yuksekligi": 43,
               "N": 11, "h": 3, "hizli1": 44, "hizli2": 3,
               "asansorler": [
                   {"P": 10, "kapi_genisligi": kg1, "kapi_tipi": "Teleskopik Otomatik",
                    "manuel_ta": mta},
                   {"P": 16, "kapi_genisligi": kg2, "kapi_tipi": "Teleskopik Otomatik",
                    "manuel_tp": mtp}]}

    # 5) özdeş çoklu  ( tek yola düşer )  +  ek nüfus  +  hata yolları
    for n in (2, 3, 4):
        yield {"bina_tipi": "İş Merkezi (Çok Firmalı)", "bina_yuksekligi": 45,
               "yapi_yuksekligi": 50, "N": 14, "h": 3.6, "hizli1": 4800,
               "asansorler": [{"P": 20, "kapi_genisligi": 1100,
                               "kapi_tipi": "Teleskopik Otomatik"}] * n}
    for ek in ([], [{"aciklama": "Zemin dükkân", "miktar": 30, "kalem": "DOĞRUDAN KİŞİ — Tablo-1 dışı"}],
               [{"aciklama": "Otopark", "miktar": 40, "kalem": "OTOPARK — Özel araç"},
                {"aciklama": "Ofis katı", "miktar": 600, "kalem": "İŞ MERKEZİ — Çalışma alanı"}]):
        yield {"bina_tipi": "Konut", "bina_yuksekligi": 39.98, "yapi_yuksekligi": 43,
               "N": 11, "h": 3, "hizli1": 44, "hizli2": 3, "ek_nufus": ek,
               "asansorler": [{"P": 13, "kapi_genisligi": 900,
                               "kapi_tipi": "Teleskopik Otomatik"}]}
    for bozuk in ({"N": 31}, {"N": 0}, {"h": -3}, {"h": 0}, {"bina_yuksekligi": None},
                  {"hizli1": None}, {"manuel_k": 0.2}, {"bodrum": 11},
                  {"asansorler": [{"P": 7, "kapi_genisligi": 900, "kapi_tipi": "Teleskopik Otomatik"}]},
                  {"asansorler": [{"P": 10, "kapi_genisligi": 900,
                                   "kapi_tipi": "Teleskopik Otomatik", "durak": 5}]},
                  {"asansorler": []}):
        temel = {"bina_tipi": "Konut", "bina_yuksekligi": 39.98, "yapi_yuksekligi": 43,
                 "N": 11, "h": 3, "hizli1": 44, "hizli2": 3,
                 "asansorler": [{"P": 10, "kapi_genisligi": 900,
                                 "kapi_tipi": "Teleskopik Otomatik"}]}
        temel.update(bozuk)
        yield temel


def avan_senaryolar():
    """AVAN motoru — altı hesap bölümü, makine dairesi ve topraklama."""
    ortak = {"temel_a": 26.55, "temel_b": 16.4, "mk_uzunluk": 3000,
             "mk_genislik": 2500, "beta": 150, "cubuk_sayisi": 4}
    # 1) kapasite × hız × verim × askı  ( motor gücü ve kuvvetler )
    for kap in (6, 10, 16, 30):
        for V in (0.63, 1.6, 2.5):
            for eta, i_pal in ((0.85, 2), (0.50, 1), (0.60, 2)):
                yield {"ortak": dict(ortak), "sabitler": {},
                       "asansorler": [{"tanim": "A", "kapasite": kap, "V": V, "eta": eta,
                                       "i_palanga": i_pal, "Hk": 32.85,
                                       "kuyu_genisligi": 1800, "kabin_boyu": 1450,
                                       "kabin_genisligi": 1300,
                                       "makine_tipi": "Dişlisiz" if eta > 0.7 else "Dişli"}]}
    # 2) kuyu yüksekliği  ( aydınlatma n1 / n2 ve gerilim düşümü )
    for Hk in (6.5, 12, 21, 33, 48, 75):
        for S1 in (4, 6, 16, 35):
            yield {"ortak": dict(ortak), "sabitler": {},
                   "asansorler": [{"tanim": "A", "kapasite": 13, "V": 1.6, "eta": 0.85,
                                   "Hk": Hk, "kuyu_genisligi": 1800, "kabin_boyu": 1450,
                                   "kabin_genisligi": 1300, "S1": S1, "S2": 4,
                                   "makine_tipi": "Dişlisiz"}]}
    # 3) elle ezmeler, toplam verim, makine dairesiz, çok asansör
    yield {"ortak": dict(ortak, mk_yok=True), "sabitler": {},
           "asansorler": [{"tanim": "MRL", "kapasite": 10, "V": 1.6, "eta": 0.85,
                           "Hk": 30, "kuyu_genisligi": 1700, "kabin_boyu": 1400,
                           "kabin_genisligi": 1100, "makine_tipi": "Dişlisiz"}]}
    yield {"ortak": dict(ortak), "sabitler": {"kuyu_armatur_lm": 2600, "q_denge": 0.45},
           "asansorler": [{"tanim": "özel", "kapasite": 16, "V": 2, "eta": 0.72,
                           "Hk": 40, "kuyu_genisligi": 2000,
                           "kabin_boyu": 1700, "kabin_genisligi": 1300, "Nsc": 15,
                           "Gk_elle": 1150, "makine_tipi": "Dişlisiz"}]}
    yield {"ortak": dict(ortak), "sabitler": {},
           "asansorler": [{"tanim": f"A{n}", "kapasite": k, "V": 1.6, "eta": 0.85,
                           "Hk": 32.85, "kuyu_genisligi": 1800, "kabin_boyu": 1450,
                           "kabin_genisligi": 1300, "makine_tipi": "Dişlisiz"}
                          for n, k in enumerate((10, 16, 20, 25), 1)]}
    # 3b) DENGE FAKTÖRÜ SÜPÜRMESİ.  q > 0,50'de ağır çalışma yönü boş kabin
    #  aşağıdır ( q·Q ); program eskiden yalnız ( 1−q ) yönünü hesaplıyordu.
    #  Senaryolarda q hep ≤ 0,50 olduğu için kalkan bu hatayı KORUMUYORDU.
    for q in (0.40, 0.45, 0.50, 0.55, 0.60, 0.70):
        for kap in (10, 20):
            yield {"ortak": dict(ortak), "sabitler": {},
                   "asansorler": [{"tanim": f"q{q}", "kapasite": kap, "V": 1.6,
                                   "eta": 0.85, "i_palanga": 2, "q_denge": q,
                                   "Hk": 32.85, "kuyu_genisligi": 1800,
                                   "kabin_boyu": 1450, "kabin_genisligi": 1300,
                                   "makine_tipi": "Dişlisiz"}]}
    # 3c) KABİN ALANI  —  Tablo-11 sınırının altı ve üstü
    for kap, a, b in ((6, 1000, 1250), (6, 2000, 2000), (8, 1100, 1400), (16, 2000, 1400)):
        yield {"ortak": dict(ortak), "sabitler": {},
               "asansorler": [{"tanim": "alan", "kapasite": kap, "V": 1.6, "eta": 0.85,
                               "Hk": 25, "kuyu_genisligi": max(a, b) + 400,
                               "kabin_boyu": a, "kabin_genisligi": b,
                               "makine_tipi": "Dişlisiz"}]}

    # 4) hata yolları  ( pasif asansör mesajları da dondurulur )
    for bozuk in ({"kapasite": None}, {"eta": 10}, {"Q_elle": 0}, {"Q_elle": 5000},
                  {"Hk": -3}, {"kabin_genisligi": 2400}, {"V": None}, {"Nsc": -1},
                  {"gr": 9999}, {"i_palanga": 9}):
        temel = {"tanim": "A", "kapasite": 10, "V": 1.6, "eta": 0.85, "Hk": 32.85,
                 "kuyu_genisligi": 1800, "kabin_boyu": 1450, "kabin_genisligi": 1300,
                 "makine_tipi": "Dişlisiz"}
        temel.update(bozuk)
        yield {"ortak": dict(ortak), "sabitler": {}, "asansorler": [temel]}
    # 5) topraklama ve makine dairesi uçları
    for ta, tb, cs in ((10, 8, 0), (60, 40, 12), (26.55, 16.4, 4)):
        yield {"ortak": dict(ortak, temel_a=ta, temel_b=tb, cubuk_sayisi=cs),
               "sabitler": {}, "asansorler": [
                   {"tanim": "A", "kapasite": 10, "V": 1.6, "eta": 0.85, "Hk": 32.85,
                    "kuyu_genisligi": 1800, "kabin_boyu": 1450, "kabin_genisligi": 1300,
                    "makine_tipi": "Dişlisiz"}]}


def uygulama_senaryolar():
    """Uygulama projesi  ( mukavemet + elektrik + topraklama )  senaryoları.

    HEPSİ ÇOKLU YOLDAN GEÇER.  hesapla_coklu tek asansörde hesapla()'nın TAM
    çıktısını asansorler[0]'da taşır;  böylece tek dosya hem tek hem çoklu
    yolu dondurur ve ikinci bir altın dosyaya gerek kalmaz.

    Kapsam:  taban proje · yük/hız/askı çeşitleri · denge zinciri · katalog
    halat verisi · sığınma duruşları · Tst kontrolü · Ds ayrımı · proje
    geneli hesaplar ( topraklama + makine dairesi ) · çok asansörlü proje ·
    hesabı durduran girdi.
    """
    #  Şerit boyu girdi değildir — temel ölçülerinden türetilir.
    #  Makine dairesi ölçüsü MİLİMETREDİR:  4,0 × 3,0 yazılıydı ve senaryolar
    #  4 mm × 3 mm'lik bir oda hesaplıyordu ( pafta "0,00 · 0,00" basıyordu ).
    PG = {"temel_a": 26.55, "temel_b": 16.4,
          "mk_yok": False, "mk_uzunluk": 4000, "mk_genislik": 3000}

    #  1) Taban — varsayılan proje, proje geneli hesaplar YOK
    yield {"asansorler": [{}], "ortak": {}}
    #  2) Taban + topraklama ve makine dairesi
    yield {"asansorler": [{}], "ortak": dict(PG)}
    #  3) MRL — makine dairesi yok
    yield {"asansorler": [{}], "ortak": dict(PG, mk_yok=True)}

    #  4-7) Yük · hız · askı oranı çeşitleri
    for yuk, hiz, aski in ((630, 1.0, 1), (800, 1.6, 2),
                           (1275, 2.5, 2), (1600, 1.0, 1)):
        yield {"asansorler": [{"beyan_yuku": yuk, "beyan_hizi": hiz,
                               "aski_orani": aski}],
               "ortak": dict(PG)}

    #  8-9) Denge zinciri — var / yok  ( Gmax ve Tst ters yönde değişir )
    for z in ("Yok", "Var"):
        yield {"asansorler": [{"denge_zinciri": z, "aski_orani": 2}],
               "ortak": dict(PG)}

    #  10) Katalog halat verisi tabloyu ezer
    yield {"asansorler": [{"halat_capi": 6.5, "halat_adedi": 7,
                           "halat_birim_kutle": 0.179, "halat_kopma_kN": 31.5}],
           "ortak": dict(PG)}

    #  11-13) Sığınma duruşları  ( kuyu dibi )
    for tip in ("Çömelme", "Yatarak", "Dik duruş"):
        yield {"asansorler": [{"siginma_tipi_dip": tip}], "ortak": dict(PG)}

    #  14-15) Tst kontrolü — geçen ve kalan
    for tst in (3400, 800):
        yield {"asansorler": [{"makine_tst": tst, "motor_gucu": 11}],
               "ortak": dict(PG)}

    #  16) Ds ( en küçük kasnak ) ayrımı
    #  Ds ≤ D2'dir;  ortalama 320 sınırı geçerken EN KÜÇÜK 295 geçmez —
    #  senaryo tam da bu ayrımı dondurur.  ( Eskiden D2 = 295'e Ds = 320
    #  veriliyordu:  en küçük çap ortalamayı aşamaz, geçerli bir tesis
    #  değildi ve dogrula artık reddediyor. )
    yield {"asansorler": [{"tahrik_kasnak_capi": 320, "halat_capi": 8,
                           "saptirma_kasnak_capi": 320, "kasnak_tek_yon": 2,
                           "saptirma_kasnak_min_capi": 295}],
           "ortak": dict(PG)}

    #  17) ÇOK ASANSÖRLÜ — proje geneli bölümler yalnız ilkinde kalmalı
    yield {"asansorler": [{"asansor_adi": "İnsan 1"},
                          {"beyan_yuku": 630, "asansor_adi": "İnsan 2"},
                          {"beyan_yuku": 1275, "asansor_adi": "Yük",
                           "denge_zinciri": "Var"}],
           "ortak": dict(PG)}
    #  18) Dört asansör — azami
    yield {"asansorler": [{"beyan_yuku": y} for y in (630, 800, 1000, 1275)],
           "ortak": dict(PG)}

    #  19-20) Hesabı DURDURAN girdiler — hata metinleri de dondurulur
    yield {"asansorler": [{"halat_adedi": 1}], "ortak": {}}
    yield {"asansorler": [{"kabin_paten_arasi": 30000}], "ortak": {}}

    #  21) Ofis sabiti ezmesi  ( verim + zincir oranı )
    yield {"asansorler": [{"denge_zinciri": "Var"}],
           "ortak": dict(PG, _ofis={"verim_dislisiz": 0.80,
                                    "denge_zinciri_orani": 80})}


def uygulama_motoru(g):
    """Altın karşılaştırmasının çağırdığı sarmalayıcı."""
    return UY.hesapla_coklu(g.get("asansorler"), g.get("ortak"))


def uret():
    kayit = []
    for i, g in enumerate(senaryolar()):
        kayit.append({"no": i, "girdi": g, "cikti": TR.hesapla(json.loads(json.dumps(g)))})
    return kayit


def uret_avan():
    kayit = []
    for i, g in enumerate(avan_senaryolar()):
        kayit.append({"no": i, "girdi": g, "cikti": AV.hesapla(json.loads(json.dumps(g)))})
    return kayit


def _yaz_bir(kayit, dosya, ad):
    ham = json.dumps(kayit, ensure_ascii=False, sort_keys=True, default=str, indent=1)
    with gzip.open(dosya, "wt", encoding="utf-8") as f:
        f.write(ham)
    print(f"  {ad:8} {len(kayit):4} senaryo  ·  {len(ham)/1024:6.0f} KB ham  ·  "
          f"{os.path.getsize(dosya)/1024:5.0f} KB sıkıştırılmış  →  {os.path.basename(dosya)}")


def uret_uygulama():
    kayit = []
    for i, g in enumerate(uygulama_senaryolar()):
        kayit.append({"no": i, "girdi": g,
                      "cikti": uygulama_motoru(json.loads(json.dumps(g)))})
    return kayit


def yaz():
    _yaz_bir(uret(), DOSYA, "TRAFİK")
    _yaz_bir(uret_avan(), DOSYA_AVAN, "AVAN")
    _yaz_bir(uret_uygulama(), DOSYA_UYGULAMA, "UYGULAMA")


if __name__ == "__main__":
    yaz()

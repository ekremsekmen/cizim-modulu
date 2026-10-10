# -*- coding: utf-8 -*-
"""
MMO/697 (2. Baskı, Ocak 2020), TS EN 81-20, ISO 8100-32:2020 ve IEC 60364-5-52
kaynaklı tablolar.
"""

from engine.ortak import ofis as _OFIS
from engine.ortak.steps import sayi_mi

# ---------------------------------------------------------------- TABLO - 1
# Binada sürekli bulunan insan sayısı katsayıları (MMO/697 s.13)
TABLO_1 = {
    "KONUT — İlk yatak odası": {"birim": "oda", "katsayi": 2},
    "KONUT — Diğer oda": {"birim": "oda", "katsayi": 1},
    "OTEL — Yatak": {"birim": "yatak", "katsayi": 1},
    "İŞ MERKEZİ — Çalışma alanı": {"birim": "m²", "katsayi": 1 / 12},
    "HASTANE — Yatak": {"birim": "yatak", "katsayi": 3},
    "RESMİ BİNA — Çalışma alanı": {"birim": "m²", "katsayi": 1 / 12},
    "OTOPARK — Ticari araç": {"birim": "araç", "katsayi": 1.5},
    "OTOPARK — Özel araç": {"birim": "araç", "katsayi": 1},
    "DOĞRUDAN KİŞİ — Tablo-1 dışı": {"birim": "kişi", "katsayi": 1},
}


# ---------------------------------------------------------------- TABLO - 2
# Kabin hızları — durak adedine göre asgari hız (MMO/697 s.13)
def tablo2_min_hiz(hiz_grubu: str, durak_adedi: int):
    """
    durak_adedi = asansörün DURDUĞU toplam kat adedi
                = N (ana giriş üstü kat) + 1 (ana giriş) + Nb (bodrum durağı).
    Grup yoksa None döner (manuel hız gerekir).
    """
    d = durak_adedi
    if hiz_grubu == "Konut":
        return 1 if d <= 9 else 1.6 if d <= 14 else 2 if d <= 19 else 2.5
    if hiz_grubu == "Büro ve İş Merkezi":
        return 1 if d <= 5 else 1.6 if d <= 10 else 2 if d <= 15 else 2.5 if d <= 19 else 3.5
    if hiz_grubu == "Otel":
        return 1 if d <= 6 else 1.6 if d <= 10 else 2 if d <= 15 else 2.5 if d <= 19 else 3.5
    return None


# Bir üst hız (öneri bloğu için)
def bir_ust_hiz(v):
    if v is None:
        return None
    if v < 1:
        return 1
    return {1: 1.6, 1.6: 2, 2: 2.5, 2.5: 3.5, 3.5: 5}.get(v, 6)


GECERLI_HIZLAR = [0.63, 1, 1.6, 1.75, 2, 2.5, 3, 3.5, 5, 6]

# ------------------------------------------------------- TABLO - 3  /  5
# H = N − Σ(i/N)^P   (i = 1..N−1)      — Ortalama en yüksek dönüş katı, s.14
# S = N·(1 − ((N−1)/N)^P)              — Ortalama durak adedi, s.16
# Kapsam: P = 6..34 kişi, N = 1..30 kat  (tablo sınırları birebir korunur)
T3_T5_P_MIN, T3_T5_P_MAX = 6, 34
T3_T5_N_MIN, T3_T5_N_MAX = 1, 30


def kapsam_disi(N, P):
    return not (
        isinstance(N, int)
        and isinstance(P, int)
        and T3_T5_N_MIN <= N <= T3_T5_N_MAX
        and T3_T5_P_MIN <= P <= T3_T5_P_MAX
    )


def tablo3_H(N: int, P: int):
    """Ortalama en yüksek dönüş katı."""
    if kapsam_disi(N, P):
        return None
    return N - sum((i / N) ** P for i in range(1, N))


def tablo5_S(N: int, P: int):
    """Ortalama durak adedi."""
    if kapsam_disi(N, P):
        return None
    return N * (1 - ((N - 1) / N) ** P)


# ---------------------------------------------------------------- TABLO - 4
# Kapı açılma (ta) ve kapanma (tk) zamanları, saniye (MMO/697 s.15)
KAPI_TIPLERI = [
    "Teleskopik Otomatik",
    "Merkezden Açılan Oto.",
    "Kabin İçi Oto. Kat K.Ç.",
]
#
#  1000 ve 1200 mm satırları MMO/697 Tablo-4'te YOKTUR.  Açılır listede bu iki
#  genişlik seçilebildiği hâlde tablo karşılığı bulunmadığından hesap eskiden
#  duruyordu.  Komşu tablo satırları arasında DOĞRUSAL ENTERPOLASYONLA
#  türetildiler — Tablo-6'daki 1,75 ve 3,00 m/s ara değerleriyle aynı yöntem.
#  Paftada kaynağı "Tablo-4 (ara değer — enterpolasyon)" olarak yazılır.
#     1000 mm  =  ( 900 + 1100 ) / 2
#     1200 mm  =  ( 1100 + 1300 ) / 2
#  "Kabin İçi Oto. Kat K.Ç." sütunu 1300 mm'de tabloda yoktur; dolayısıyla
#  1200 mm için de enterpolasyon yapılamaz — bu iki değer boş bırakılmıştır
#  ve program imalatçı değerinin elle girilmesini ister.
TABLO_4 = {
    #  genişlik : { kapı tipi : (ta, tk) }
    700: {
        "Teleskopik Otomatik": (2.5, 3.0),
        "Merkezden Açılan Oto.": (2.0, 2.5),
        "Kabin İçi Oto. Kat K.Ç.": (5.0, 5.0),
    },
    800: {
        "Teleskopik Otomatik": (2.5, 3.0),
        "Merkezden Açılan Oto.": (2.0, 2.5),
        "Kabin İçi Oto. Kat K.Ç.": (5.0, 5.0),
    },
    900: {
        "Teleskopik Otomatik": (2.5, 3.8),
        "Merkezden Açılan Oto.": (2.3, 2.9),
        "Kabin İçi Oto. Kat K.Ç.": (5.0, 5.0),
    },
    1000: {
        "Teleskopik Otomatik": (2.75, 3.9),
        "Merkezden Açılan Oto.": (2.4, 3.2),
        "Kabin İçi Oto. Kat K.Ç.": (5.5, 5.5),
    },
    1100: {
        "Teleskopik Otomatik": (3.0, 4.0),
        "Merkezden Açılan Oto.": (2.5, 3.5),
        "Kabin İçi Oto. Kat K.Ç.": (6.0, 6.0),
    },
    1200: {
        "Teleskopik Otomatik": (3.35, 4.5),
        "Merkezden Açılan Oto.": (2.6, 3.6),
        "Kabin İçi Oto. Kat K.Ç.": (None, None),
    },
    1300: {
        "Teleskopik Otomatik": (3.7, 5.0),
        "Merkezden Açılan Oto.": (2.7, 3.7),
        "Kabin İçi Oto. Kat K.Ç.": (None, None),
    },
}
#  MMO/697 Tablo-4'te basılı olan satırlar (ara değer üretilmemiş olanlar)
TABLO_4_BASILI = (700, 800, 900, 1100, 1300)
#  Ara değerler ELLE YAZILMAZ, basılı satırlardan TÜRETİLİR — iki liste
#  birbirinden ayrışamasın.  ( Eskiden ikisi de elle tutuluyordu ve
#  TABLO_4_BASILI hiçbir yerde okunmuyordu. )
TABLO_4_ARA = tuple(g for g in TABLO_4 if g not in TABLO_4_BASILI)
KAPI_GENISLIKLERI = [700, 800, 900, 1000, 1100, 1200, 1300]


def tablo4_ta_tk(genislik, kapi_tipi):
    """(ta, tk) — tabloda yoksa (None, None)."""
    if kapi_tipi == "Merkezden Açılan Otomatik":
        kapi_tipi = "Merkezden Açılan Oto."
    satir = TABLO_4.get(genislik)
    if not satir:
        return (None, None)
    return satir.get(kapi_tipi, (None, None))


def tablo4_kaynagi(genislik):
    #  KAYNAK TAM ADIYLA YAZILIR:  paftada ISO 8100-32:2020'nin "Tablo 6"sı ile
    #  MMO/697'nin "Tablo-6"sı yan yana basılıyor;  çıplak "Tablo-6" hangisi
    #  olduğunu söylemez.  Bu yüzden MMO tabloları her yerde "MMO/697 Tablo-N".
    return "MMO/697 Tablo-4 (ara değer — enterpolasyon)" if genislik in TABLO_4_ARA else "MMO/697 Tablo-4"


# ---------------------------------------------------------------- TABLO - 6
# Tek katı geçme zamanı tg, saniye (MMO/697 s.17)
# 1,75 ve 3,00 m/s tabloda YOKTUR — komşu noktalar arasında doğrusal
# enterpolasyonla türetilmiştir (paftada "ara değer" olarak yazılır).
def tablo6_tg(V):
    if V is None or not isinstance(V, (int, float)):
        return None
    if V < 1:
        return 10
    if V == 1:
        return 7
    if V == 1.6:
        return 6
    if V == 1.75:
        return 5.8875  # ara değer — enterpolasyon
    if V == 2:
        return 5.7
    if V == 2.5:
        return 5.5
    if V == 3:
        return 5.25  # ara değer — enterpolasyon
    if V == 3.5:
        return 5
    if V == 5:
        return 4.5
    if V > 5:
        return 4.3
    return None


def tg_kaynagi(V):
    return "MMO/697 Tablo-6 (ara değer — enterpolasyon)" if V in (1.75, 3) else "MMO/697 Tablo-6"


# ---------------------------------------------------------------- TABLO - 7
# Kabin kapasitesi → beyan (anma) yükü, kg (MMO/697 s.17)
# 15 kişi / 1125 kg tabloda yoktur; kitabın s.53-54 örneğinde geçtiği için
# "örnek istisnası" olarak desteklenir.
TABLO_7 = {6: 450, 8: 630, 10: 800, 13: 1000, 15: 1125, 16: 1275, 20: 1600, 25: 2000, 30: 2500}
#  15 kişi / 1125 kg MMO/697 Tablo-7'de (s.17) BASILI DEĞİLDİR; kitabın s.53-54
#  örnek hesabında kullanıldığı için "örnek istisnası" olarak tabloya açıkça
#  yazılmıştır (1125 = 15 × 75 kg).  Paftada kaynağı ayrı gösterilir.
TABLO_7_BASILI = (6, 8, 10, 13, 16, 20, 25, 30)
TABLO_7_ORNEK = (15,)
GECERLI_KAPASITELER = [6, 8, 10, 13, 15, 16, 20, 25, 30]


def tablo7_yuk(P):
    if P is None:
        return None
    return TABLO_7.get(P, P * 75 if sayi_mi(P) else None)


def tablo7_kaynagi(P):
    """
    Paftaya basılan KAYNAK metni.  Tabloda BULUNMAYAN bir kapasite için
    "Tablo-7" yazmak, olmayan bir tablo satırına atıf yapmaktır ( ör. 7 kişi
    → 525 kg ); denetimde bu yanlış kaynak gösterimi olarak okunur.
    """
    if P in TABLO_7_ORNEK:
        return "MMO örneği s.53-54 (Tablo-7 dışı)"
    if P in TABLO_7:
        return "MMO/697 Tablo-7"
    if P is None:
        return "—"  # kapasite girilmemiş; pafta zaten hata basar
    return "MMO/697 Tablo-7 DIŞI — Q = P × 75 kg kabulü"


# ---------------------------------------------------------------- TABLO - 8
# Kişi transfer zamanı tp, saniye — net kapı genişliğine göre
# Kaynak: ISO 8100-32:2020 Tablo 6 (800 mm: ISO/CD 8100-32 + Barney/Peters)
#  700 mm ISO 8100-32:2020 Tablo 6'da YOKTUR (tablo 800 mm'de başlar).  Açılır
#  listede seçilebildiğinden, 800→900 mm eğiminden (−0,1 s / 100 mm) DOĞRUSAL
#  DIŞ DEĞERLEME ile 1,3 s alınmıştır.  Dar kapı transferi yavaşlatır; büyük tp
#  TR'yi büyütür, yani emniyetli taraftadır.  İmalatçı verisi varsa manuel tp
#  girilmelidir.  Ayrıca 700 mm net kapı, TS EN 81-70'in erişilebilir asansör
#  için istediği 800 mm asgarisinin altındadır — program bunu ayrıca uyarır.
TABLO_8 = {700: 1.3, 800: 1.2, 900: 1.1, 1000: 1.0, 1100: 1.0, 1200: 0.9, 1300: 0.9}
TABLO_8_BASILI = (800, 900, 1000, 1100, 1200, 1300)
TABLO_8_ARA = tuple(g for g in TABLO_8 if g not in TABLO_8_BASILI)


def tablo8_tp(genislik):
    return TABLO_8.get(genislik)


def tablo8_kaynagi(genislik):
    return (
        "ISO 8100-32:2020 Tablo 6 (kapsam dışı — dış değerleme)"
        if genislik in TABLO_8_ARA
        else "ISO 8100-32:2020, Tablo 6"
    )


# ---------------------------------------------------------------- TABLO - 9
# Taşınacak insan yüzdesi %k (MMO/697 s.17)
TABLO_9 = {
    "Konut": {"Standart": 0.075, "Yükseltilmiş": 0.10},
    "Otel": {"Standart": 0.12, "Yükseltilmiş": 0.15},
    "İş Merkezi": {"Standart": 0.15, "Yükseltilmiş": 0.17},
    "Hastane": {"Standart": 0.10, "Yükseltilmiş": 0.20},
    "Otopark": {"Standart": 0.10, "Yükseltilmiş": 0.20},
}

# --------------------------------------------------------------- TABLO - 10
# İzin verilen en fazla bekleme zamanı Izul, saniye (MMO/697 s.17)
# + bina tipi eşleme tablosu (Tablo-2 hız grubu / Tablo-9 %k tipi)
TABLO_10 = {
    "Konut": {"sartli": 120, "standart": 100, "yukseltilmis": 80, "hiz_grubu": "Konut", "k_tipi": "Konut"},
    "Karma Binalar (İşyeri ve Konut)": {
        "sartli": 60,
        "standart": 50,
        "yukseltilmis": 30,
        "hiz_grubu": None,
        "k_tipi": None,
    },
    "İş Merkezi (Tek Firmalı)": {
        "sartli": 60,
        "standart": 50,
        "yukseltilmis": 40,
        "hiz_grubu": "Büro ve İş Merkezi",
        "k_tipi": "İş Merkezi",
    },
    "İş Merkezi (Çok Firmalı)": {
        "sartli": 50,
        "standart": 40,
        "yukseltilmis": 30,
        "hiz_grubu": "Büro ve İş Merkezi",
        "k_tipi": "İş Merkezi",
    },
    "Otel (3* ve altı)": {
        "sartli": 60,
        "standart": 50,
        "yukseltilmis": 40,
        "hiz_grubu": "Otel",
        "k_tipi": "Otel",
    },
    "Otel (4* ve üzeri)": {
        "sartli": 50,
        "standart": 40,
        "yukseltilmis": 30,
        "hiz_grubu": "Otel",
        "k_tipi": "Otel",
    },
    "Kamu Binaları": {
        "sartli": None,
        "standart": 40,
        "yukseltilmis": 30,
        "hiz_grubu": "Büro ve İş Merkezi",
        "k_tipi": "İş Merkezi",
    },
    "Hastane": {"sartli": None, "standart": 40, "yukseltilmis": 30, "hiz_grubu": None, "k_tipi": "Hastane"},
    "Poliklinik Binaları ve Yaşlı Bakım Ev.": {
        "sartli": 60,
        "standart": 50,
        "yukseltilmis": 40,
        "hiz_grubu": None,
        "k_tipi": None,
    },
    "Katlı Otopark": {
        "sartli": 60,
        "standart": 50,
        "yukseltilmis": 40,
        "hiz_grubu": None,
        "k_tipi": "Otopark",
    },
}
BINA_TIPLERI = list(TABLO_10.keys())

# Yüksek yapı ölçütü — BYKHY md.4
YUKSEK_BINA_YUKSEKLIK = 21.50  # m, kot noktasından saçak seviyesine
YUKSEK_YAPI_YUKSEKLIK = 30.50  # m, bodrum ve çatı arası dâhil


# ================================================================
#  AVAN HESAPLARI TABLOLARI
# ================================================================

# --------------- TABLO 2 (AVAN) — Oda aydınlatma verimi η
# k satırları (bölge indeksi) ve 10 yansıma sütunu
AYD_K_SATIRLARI = [0.6, 0.8, 1, 1.25, 1.5, 2, 2.5, 3, 4, 5]
AYD_VERIM = [
    #  1     2     3     4     5     6     7     8     9    10
    [0.24, 0.23, 0.18, 0.18, 0.20, 0.19, 0.15, 0.15, 0.15, 0.12],
    [0.31, 0.29, 0.24, 0.23, 0.25, 0.24, 0.20, 0.19, 0.17, 0.16],
    [0.36, 0.33, 0.29, 0.28, 0.29, 0.28, 0.24, 0.23, 0.20, 0.20],
    [0.41, 0.38, 0.34, 0.32, 0.33, 0.31, 0.28, 0.27, 0.24, 0.24],
    [0.45, 0.41, 0.38, 0.36, 0.36, 0.34, 0.32, 0.30, 0.26, 0.27],
    [0.51, 0.46, 0.45, 0.41, 0.41, 0.38, 0.37, 0.35, 0.30, 0.31],
    [0.56, 0.49, 0.50, 0.45, 0.45, 0.41, 0.41, 0.38, 0.34, 0.35],
    [0.59, 0.52, 0.54, 0.48, 0.47, 0.43, 0.43, 0.40, 0.36, 0.38],
    [0.63, 0.55, 0.58, 0.51, 0.50, 0.46, 0.47, 0.44, 0.39, 0.41],
    [0.66, 0.57, 0.62, 0.54, 0.53, 0.48, 0.50, 0.46, 0.40, 0.44],
]
# Sütun tanımları (tavan / duvar / zemin yansıma çarpanları)
AYD_SUTUN_ACIKLAMA = {
    1: "tavan 0,80 / duvar 0,50 / zemin 0,30",
    2: "tavan 0,80 / duvar 0,50 / zemin 0,10",
    3: "tavan 0,80 / duvar 0,30 / zemin 0,30",
    4: "tavan 0,80 / duvar 0,30 / zemin 0,10",
    5: "tavan 0,50 / duvar 0,50 / zemin 0,30",
    6: "tavan 0,50 / duvar 0,50 / zemin 0,10",
    7: "tavan 0,50 / duvar 0,30 / zemin 0,30",
    8: "tavan 0,50 / duvar 0,30 / zemin 0,10",
    9: "tavan 0,30 / duvar 0,30 / zemin 0,30",
    10: "tavan 0,30 / duvar 0,30 / zemin 0,10",
}


def ayd_verim(k, sutun=2):
    """k bir ALT satıra yuvarlanarak okunur (emniyetli taraf) — MATCH(...;1)."""
    if k is None:
        return None
    kk = max(k, AYD_K_SATIRLARI[0])
    idx = 0
    for i, v in enumerate(AYD_K_SATIRLARI):
        if v <= kk:
            idx = i
        else:
            break
    try:
        return AYD_VERIM[idx][int(sutun) - 1]
    except (IndexError, TypeError, ValueError):  # sütun tabloda yok ya da sayı değil
        return None


# --------------- ANMA YÜKÜNE GÖRE ORTALAMA BOŞ KABİN KÜTLESİ  ( ofis tablosu )
#  TABLO ARTIK ORTAK DOSYADADIR  ( engine/ortak/ofis.py ):  uygulama projesi de
#  boş kabin ağırlığını aynı tablodan doldurur.  İki kopya tutulsaydı biri
#  güncellenip öteki unutulur, aynı asansör iki projede iki farklı kabin
#  kütlesiyle hesaplanırdı.
#
#  DİKKAT:  Bu tablo MMO/697'nin Tablo-11'i DEĞİLDİR.  Kitabın Tablo-11'i
#  "TS EN 81-20'ye göre kullanılabilir kabin alanı / beyan yükü" tablosudur
#  ve boş kabin kütlesi vermez.  Gk değerleri ofisin imalatçı deneyiminden
#  gelir;  paftada kaynağı da öyle yazılır.  ( Eskiden "Tablo-11" diye
#  gösteriliyordu — yanlış atıf. )
GK_TABLOSU = [tuple(satir) for satir in _OFIS.GK_TABLOSU]

#  Geriye dönük ad ( arayüz ve testler bu adı kullanır )
TABLO_11 = GK_TABLOSU

GK_KAYNAGI = _OFIS.GK_KAYNAGI


def tablo11_Gk(Q):
    """Ara yükler doğrusal enterpolasyonla; sonuç 10 kg'a, yarımı yukarı yuvarlanır."""
    return _OFIS.bos_kabin_kutlesi(Q) if sayi_mi(Q) else None


# --------------- MMO/697 Tablo-11  ( = TS EN 81-20 )
#  BEYAN YÜKÜNE GÖRE KABİNİN KULLANILABİLİR EN BÜYÜK ALANI, m²  —  YOLCU asansörü.
#
#  DİKKAT:  Kitapta ARDIŞIK İKİ tablo vardır ve karıştırılması kolaydır
#  ( OCR'da başlıklar tablolardan SONRA gelir ):
#      Tablo-11  yolcu asansörü               450 kg →  1,30 m²   ← BU
#      Tablo-12  hidrolik YÜK asansörü        450 kg →  1,84 m²
#  Bu program yolcu asansörü hesaplar; Tablo-11 geçerlidir.
#
#  Kitap dipnotları:
#      1) 100 kg  — bir kişilik asansör için en küçük
#      2) 180 kg  — iki kişilik asansör için en küçük
#      3) 2500 kg üzerinde her 100 kg ilave yük başına 0,16 m² eklenir
#      ara yük değerleri için alan lineer enterpolasyonla bulunur
KABIN_AZAMI_ALAN = [
    (100, 0.37),
    (180, 0.58),
    (225, 0.70),
    (300, 0.90),
    (375, 1.10),
    (400, 1.17),
    (450, 1.30),
    (525, 1.45),
    (600, 1.60),
    (630, 1.66),
    (675, 1.75),
    (750, 1.90),
    (800, 2.00),
    (825, 2.05),
    (900, 2.20),
    (975, 2.35),
    (1000, 2.40),
    (1050, 2.50),
    (1125, 2.65),
    (1200, 2.80),
    (1250, 2.90),
    (1275, 2.95),
    (1350, 3.10),
    (1425, 3.25),
    (1500, 3.40),
    (1600, 3.56),
    (2000, 4.20),
    (2500, 5.00),
]


def kabin_azami_alan(Q):
    """Beyan yükü Q ( kg ) için kabinin kullanılabilir en büyük alanı ( m² )."""
    if not sayi_mi(Q) or Q <= 0:
        return None
    xs = [a for a, _ in KABIN_AZAMI_ALAN]
    ys = [b for _, b in KABIN_AZAMI_ALAN]
    if Q <= xs[0]:
        return ys[0]
    if Q >= xs[-1]:  # 2500 kg üstü: her 100 kg'a +0,16 m²
        return ys[-1] + 0.16 * (Q - xs[-1]) / 100.0
    for i in range(len(xs) - 1):
        if xs[i] <= Q <= xs[i + 1]:
            return ys[i] + (Q - xs[i]) * (ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i])
    return None


# --------------- Kablo akım taşıma kapasitesi
# IEC 60364-5-52 Tablo B.52.4 — bakır, PVC, 3 yüklü iletken, Yöntem C
#  25 mm² ve üstü eskiden 101 · 125 · 151 · 192 · 232 · 269 A yazıyordu:
#  başlıktaki tablonun değerleri değildi ve kablonun taşıyabileceğinden
#  %4-5 FAZLAYDI — kesit kontrolünde emniyetsiz taraf.
KABLO_IZ = {
    1.5: 17.5,
    2.5: 24,
    4: 32,
    6: 41,
    10: 57,
    16: 76,
    25: 96,
    35: 119,
    50: 144,
    70: 184,
    95: 223,
    120: 259,
}


def kablo_iz(kesit):
    return KABLO_IZ.get(kesit)


# --------------- Koruma iletkeni ( PE ) kesiti
#  Elektrik Tesislerinde Topraklamalar Yönetmeliği  m.9-e1/ii  ·  Çizelge-8
#  ( harmonize karşılığı:  TS HD / IEC 60364-5-54  Tablo 54.2 )
#
#      S ≤ 16        →   Sp = S
#      16 < S ≤ 35   →   Sp = 16
#      S > 35        →   Sp = S / 2
#
#  YUVARLAMA YÖNÜ MEVZUAT HÜKMÜDÜR.  Çizelge-8'in altındaki cümle:
#  "Çizelge-8'in kullanılması sonunda standart kesit değerler elde edilmez
#  ise bir üst standart kesitli iletken kullanılmak zorundadır."  Çizelge
#  bir ASGARİ verir;  S/2 standart bir kesite düşmediğinde aşağı yuvarlamak
#  asgarinin altına düşmek olur.  ( referans projenin örnek paftası 150 mm² için
#  75 → 70 yazar;  doğrusu 95'tir.  Kendi tablosunun 95 · 120 · 185
#  satırlarında yukarı yuvarladığı hâlde. )
#
#  Çizelge-8 yalnız PE ile ana iletken AYNI MALZEMEDENSE geçerlidir;
#  asansör kolon hattında ikisi de bakırdır.
STANDART_KESITLER = (1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300, 400)


#  Ana potansiyel dengeleme iletkeni        m.9-j/1/i  ·  Çizelge-4b
#      Sapd ≥ 0,5 × tesisteki EN BÜYÜK koruma iletkeni kesiti
#      asgari  6 mm² Cu
#      üst sınır 25 mm² Cu  ( "daha büyük olması gerekmez" )
APD_ASGARI = 6
APD_UST_SINIR = 25

#  Topraklama iletkeni                       m.9/c  ·  Çizelge-4a
#  Çizelge-4a YALNIZ TOPRAĞA DÖŞENEN iletken içindir ( başlığı bunu yazar );
#  üç satırı vardır:
#      korozyona korunmuş + mekanik korumalı   →  Madde 9-e'ye göre  ( = PE )
#      korozyona korunmuş + mekanik korumasız  →  16 mm² Cu
#      korozyona korunmamış                    →  25 mm² Cu
#  Mekanik korumanın olup olmadığı avan aşamasında bilinmez;  program İKİ
#  korozyona-korunmuş satırın BÜYÜĞÜNÜ verir — yani hem m.9-e'yi hem 16 mm²'yi
#  sağlar.  Korozyona karşı korunmamış döşemede 25 mm² gerekir;  bu koşul
#  satırın kaynak sütununda yazılıdır.
TOPRAKLAMA_KORUNMUS = 16
TOPRAKLAMA_KORUNMAMIS = 25


def _ust_standart(deger):
    """Değerden küçük olmayan en küçük standart kesit  ( yoksa None )."""
    ustler = [k for k in STANDART_KESITLER if k >= deger]
    return min(ustler) if ustler else None


def ana_potansiyel_dengeleme_kesiti(en_buyuk_pe):
    """Ana potansiyel dengeleme iletkeni kesiti  ( m.9-j/1/i · Çizelge-4b ).

    Döner:  ( Sapd, ham, sinirlandi_mi )
        ham          0,5 × en büyük PE ile 6 mm²'nin büyüğü  —  ÜST SINIR
                     UYGULANMAMIŞ hâli.  Pafta bunu yazar:  "0,5 · 95 = 25"
                     diye bir satır kendi içinde yanlıştır;  doğrusu
                     "0,5 · 95 = 47,50  →  25 mm² üst sınırı"dır.
        sinirlandi   25 mm² üst sınırı devreye girdiyse True

    Çizelge-4b bir ASGARİ verir;  ham değer standart bir kesite düşmezse
    Çizelge-8'deki mantıkla bir üst standart kesit alınır — aşağı yuvarlamak
    asgarinin altına düşmek olurdu.
    """
    if not sayi_mi(en_buyuk_pe) or en_buyuk_pe <= 0:
        return None, None, False
    ham = max(APD_ASGARI, en_buyuk_pe / 2.0)
    sinirlandi = ham > APD_UST_SINIR
    baglayan = float(APD_UST_SINIR) if sinirlandi else ham
    return _ust_standart(baglayan), ham, sinirlandi


def topraklama_iletkeni_kesiti(en_buyuk_pe):
    """Topraklama iletkeni kesiti  ( m.9/c · Çizelge-4a ).

    Döner:  ( Stopr, belirleyen )
        belirleyen  "m.9-e ( koruma iletkeni )" ya da "Çizelge-4a"  —
                    hangi satırın bağladığını pafta yazabilsin diye.
    """
    if not sayi_mi(en_buyuk_pe) or en_buyuk_pe <= 0:
        return None, None
    if en_buyuk_pe >= TOPRAKLAMA_KORUNMUS:
        return _ust_standart(en_buyuk_pe), "m.9-e  ( koruma iletkeni kesiti )"
    return float(TOPRAKLAMA_KORUNMUS), "Çizelge-4a  ( 16 mm² Cu )"


def koruma_iletkeni_kesiti(S):
    """Faz kesiti S ( mm² ) için asgari koruma iletkeni kesiti  ( mm² ).

    Döner:  ( Sp, ham, yuvarlandi_mi )
        Sp            standart kesite yukarı yuvarlanmış değer
        ham           çizelgenin verdiği ham değer  ( S · 16 · S/2 )
        yuvarlandi_mi ham değer standart kesit değilse True

    S standart merdivenin en büyük değerini aşarsa Sp = None döner;
    sessizce yanlış bir sayı üretmektense kontrol edilemediği söylenir.
    """
    if not sayi_mi(S) or S <= 0:
        return None, None, False
    ham = S if S <= 16 else (16.0 if S <= 35 else S / 2.0)
    ustler = [k for k in STANDART_KESITLER if k >= ham]
    if not ustler:
        return None, ham, False
    Sp = min(ustler)
    return Sp, ham, (Sp != ham)


def kablo_iz_sinir(kesit):
    """
    Tabloda BULUNMAYAN kesitler için GÜVENLİ ALT SINIR verir.

    Iz kesitle birlikte artar ( monoton ).  Bu yüzden tabloda olmayan bir
    kesit için, ondan küçük en büyük tablo satırının değeri güvenle
    kullanılabilir:  gerçek taşıma kapasitesi bundan AZ olamaz.

    Eskiden tablo dışı kesitte Iz = None dönüyor ve pafta "UYGUN DEĞİLDİR —
    kesiti büyütün" diyordu; yani kesiti BÜYÜTMEK sonucu kötüleştiriyor,
    verilen öğüt de hiçbir zaman işe yaramıyordu ( 150 mm² kablo standart
    bir kesittir ).

    Döner:  ( Iz, kesin_mi )
        kesin_mi = True   kesit tabloda birebir var
        kesin_mi = False  Iz bir ALT SINIRDIR ( tablo dışı kesit )
        Iz = None         tablonun en küçük kesitinin de altında — sınır yok
    """
    if not isinstance(kesit, (int, float)) or isinstance(kesit, bool):
        return None, False
    kesin = KABLO_IZ.get(kesit)
    if kesin is not None:
        return kesin, True
    altlar = [k for k in KABLO_IZ if k < kesit]
    if not altlar:
        return None, False
    return KABLO_IZ[max(altlar)], False


# --------------- ARMATÜR IŞIK AKILARI  ( ofis tablosu — MMO/697 DIŞI )
#  DİKKAT:  Bu tablo MMO/697'de YOKTUR.  Kitap trafik, kuvvet, motor gücü ve
#  kabin boyutlarını kapsar;  aydınlatma / topraklama / gerilim düşümü gibi
#  ELEKTRİK hesapları kitapta hiç yer almaz ( "ışık akısı", "lümen", "armatür"
#  sözcükleri kitapta geçmez ).  Kitabın Tablo-4'ü KAPI AÇILMA-KAPANMA
#  ZAMANLARI tablosudur ve bu değerlerle ilgisi yoktur.
#  Aydınlatma hesabının dayanağı TS EN 81-20 asgari aydınlatma şiddetleri +
#  lümen yöntemi + imalatçı katalog değerleridir.
ARMATUR_ISIK_AKISI = [
    ("Akkor telli", "15 W", "120 – 135"),
    ("Akkor telli", "25 W", "215 – 240"),
    ("Akkor telli", "40 W", "340 – 480"),
    ("Akkor telli", "60 W", "620 – 805"),
    ("Akkor telli", "75 W", "855 – 960"),
    ("Akkor telli", "100 W", "1250 – 1380"),
    ("Akkor telli", "150 W", "2100 – 2280"),
    ("Flüoresan", "20 W", "820"),
    ("Flüoresan", "32 W", "1400"),
    ("Flüoresan", "40 W", "2100"),
    ("Flüoresan", "200 W", "2950 – 3220"),
    ("LED spot", "5 W", "300"),
]

# ================================================================
#  ERİŞİLEBİLİRLİK  —  TS EN 81-70 / TS 9111
# ================================================================
#  TS EN 81-70 asansör tipleri:
#     Tip 1 : 450 kg  —  kabin 1000 × 1250 mm — kapı 800 mm
#             (yalnız bir tekerlekli sandalye kullanıcısı, refakatçi sığmaz)
#     Tip 2 : 630 kg  —  kabin 1100 × 1400 mm — kapı 800 mm
#             (tekerlekli sandalye + bir refakatçi)
#     Tip 3 : 1275 kg —  kabin 2000 × 1400 mm — kapı 900 mm
#             (tekerlekli sandalye + sedye)
#  TS 9111 ve Erişilebilirlik Yönetmeliği, erişilebilir olması gereken
#  binalarda pratikte 1100 × 1400 mm (Tip 2 / 630 kg) kabini arar.
ERISILEBILIR_ASGARI_KAPASITE = 8  # kişi  (630 kg — TS EN 81-70 Tip 2)
ERISILEBILIR_ASGARI_KAPI = 800  # mm    (net kapı genişliği)


def erisilebilirlik_uyarilari(P, kapi_genisligi, on_ek=""):
    """
    Erişilebilirlik ölçütü uyarıları.  Hesabı DURDURMAZ; yalnız uyarır —
    her bina erişilebilir olmak zorunda değildir, karar projecinindir.
    """
    u = []
    if sayi_mi(P) and P < ERISILEBILIR_ASGARI_KAPASITE:
        u.append(
            f"{on_ek}⚠ {int(P)} kişi ({tablo7_yuk(P)} kg) — TS EN 81-70 Tip 1 kabini "
            "yalnız tek tekerlekli sandalye kullanıcısına yeter, refakatçi sığmaz. "
            "TS 9111 / Erişilebilirlik Yönetmeliği'nin aradığı 1100 × 1400 mm kabin "
            "için asgari 8 kişi (630 kg) seçilmelidir."
        )
    if sayi_mi(kapi_genisligi) and kapi_genisligi < ERISILEBILIR_ASGARI_KAPI:
        u.append(
            f"{on_ek}⚠ Net kapı genişliği {int(kapi_genisligi)} mm — TS EN 81-70 "
            "erişilebilir asansörde asgari 800 mm ister."
        )
    return u


def erisilebilir_mi(P, kapi_genisligi=None):
    if not sayi_mi(P) or P < ERISILEBILIR_ASGARI_KAPASITE:
        return False
    if sayi_mi(kapi_genisligi) and kapi_genisligi < ERISILEBILIR_ASGARI_KAPI:
        return False
    return True


# ================================================================
#  BODRUM  ( ana giriş altındaki duraklar )
# ================================================================
#  MMO/697 s.14 ve s.16, H (Tablo-3) ve S (Tablo-5) büyüklüklerini ANA GİRİŞİN
#  ÜSTÜNDEKİ kat adedi N üzerinden tanımlar.  Yukarı yoğun trafikte kabin ana
#  giriş katından yola çıkıp en yüksek dönüş katına gidip döner; bodrum katları
#  bu turun içinde değildir.  Bu yüzden bodrum durağı:
#     ·  H, S ve TR'yi DEĞİŞTİRMEZ            (MMO/697 tanımı gereği)
#     ·  Tablo-2 asgari hızını DEĞİŞTİRİR     (durak adedi = N + 1 + Nb)
#     ·  Toplam seyahat mesafesini DEĞİŞTİRİR ((N + Nb) · h → avan Hk)
BODRUM_AZAMI = 10  # makul üst sınır — daha fazlası girdi hatasıdır

BODRUM_NOTU = (
    "Bodrum durağı MMO/697 tanımı gereği H (Tablo-3) ve S (Tablo-5) "
    "değerlerini değiştirmez — bu iki büyüklük ana giriş üstündeki kat "
    "adedi N üzerinden tanımlıdır ve yukarı yoğun trafikte tur ana giriş "
    "katından başlar.  Bodrum durağı yalnız (a) Tablo-2 asgari hız "
    "seçiminde durak adedine ve (b) toplam seyahat mesafesine girer."
)


# ================================================================
#  MAKİNE TİPİ  ve  ASKI ( PALANGA ) ORANI
# ================================================================
#  MAKİNE VERİMİ  ( η )  —  OFİS KABULÜ, MMO/697'DE TABLO YOKTUR.
#        Dişlisiz  η = 0,85          Dişli  η = 0,50
#  Kitabın §2.4 (s.21) motor gücü bölümü formülü ve şu cümleyi verir:
#  "Palangalı sistemlerde verim %10 az alınacaktır."  Verim tablosu vermez;
#  çözümlü örneği ( §4.4, s.56 ) η = 0,50 kullanır.  Yukarıdaki iki sayı
#  ofisin imalatçı deneyiminden gelir.
#
#  AVAN KİTABA GÖRE HESAPLANIR ( avan kitaba göre denetlenir ):  buradaki η
#  kitabın η'sıdır — MAKİNE verimi, askı ( palanga ) kaybı HARİÇ.  Palangalı
#  sistemde ( askı oranı 2:1 ve üstü ) kitabın düşüşü uygulanır:
#        η′ = η − 0,10
#  Kitabın örneği:  "palangalı (2/1) sistem olduğundan verim %10 eksiltilir.
#  η = 0,5 − 0,1 = 0,4"  — yani ORAN değil, 0,10 ÇIKARMA.
#  2026-09-08 ile 2026-09-25 arasında bu düşüş kaldırılmıştı;  avan motoru
#  kitabın bulduğundan küçük seçiyor ( 800 kg · 1,6 m/s · 2:1 · η 0,85:
#  7,5 kW — kitaba göre 8,37 kW, 11 kW ) ve paftaya "artık uygulanmaz"
#  yazıyordu.  Kitaba göre inceleyen bu motoru reddeder.
#
#  UYGULAMA PROJESİ BUNU UYGULAMAZ:  orada η TOPLAM sistem verimidir
#  ( imalatçı kataloğunun η_ins'i, askı kaybı içinde ) — bkz.
#  engine/ortak/ofis.py.  Uygulama elektrik hesabını avan motorunda koştuğu
#  için köprü ( engine/uygulama/girdi.kopru ) "η toplamdır" bayrağını
#  ( ETA_TOPLAM_ANAHTARI ) geçirir;  düşüş o yolda uygulanmaz.
#  Tablo ORTAK ofis standardındadır:  iki taraf aynı sayıları okur.
MAKINE_TIPLERI = _OFIS.MAKINE_VERIMLERI
ASKI_ORANLARI = {"1:1": 1, "2:1": 2}
PALANGA_VERIM_DUSUSU = 0.10  # MMO/697 §2.4 s.21 · örnek §4.4 s.56
ETA_TOPLAM_ANAHTARI = "eta_toplam"  # köprünün bayrağı — avan formunda yoktur


def makine_verimi(makine_tipi):
    """Makine tipine göre η ( ofis kabulü ).  Tanınmayan tip için None."""
    return _OFIS.makine_verimi(makine_tipi)


def aski_orani_metni(i):
    for ad, deger in ASKI_ORANLARI.items():
        if deger == i:
            return ad
    return f"{i}:1" if i else "—"


def palangali_mi(i):
    """Askı oranı 2:1 ve üstü mü  ( MMO/697 §2.4 "palangalı sistem" )."""
    return isinstance(i, (int, float)) and not isinstance(i, bool) and i > 1


VERIM_NOTU = (
    "N = (1−q)·Q·V / (102·η) bir güç bağıntısıdır. Askı oranı denkleme yalnız "
    "verim üzerinden girer: palangalı ( 2:1 ve üstü ) sistemde verim MMO/697 "
    "§2.4 gereği 0,10 düşük alınır ( η′ = η − 0,10 )."
)
MAKINE_VERIM_NOTU = (
    "η makine verimidir ( askı / palanga kaybı hariç ); imalatçı kataloğundan "
    "alınmalı ve paftada marka-model referansı belirtilmelidir."
)

# =====================================================================
#  STANDART MOTOR GÜÇ KADEMELERİ   ( IEC 60072 / TS EN 60034 anma güçleri )
#  Hesaplanan motor gücü N bir ara değer çıkar ( ör. 13,33 kW ); imalatta
#  bunun ÜSTÜNDEKİ ilk standart kademe seçilir.  Elle seçim yapıldığında
#  program "Nsç ≥ N" kontrolünü yine yapar.
# =====================================================================
MOTOR_KADEMELERI = (
    2.2,
    3.0,
    4.0,
    5.5,
    7.5,
    11.0,
    15.0,
    18.5,
    22.0,
    30.0,
    37.0,
    45.0,
    55.0,
    75.0,
    90.0,
    110.0,
    132.0,
    160.0,
)

#  KADEME SEÇİMİ ile "Nsç ≥ N" KONTROLÜ AYNI TOLERANSI KULLANMALIDIR.
#  N = ( 1 − q )·Q·V / ( 102 · η ) kayan noktada tam kademenin bir kıl payı
#  üstüne düşebilir ( ör. 1275 kg · 1,6 m/s · η 0,60 · q 0,55  →
#  N = 15,000000000000002 ).  motor_sec toleranslı seçtiği hâlde kontrol katı
#  olursa program KENDİ seçtiği motoru reddeder ve pafta
#  "Nsç = 15,00  ≥  N = 15,00   →   UYGUN DEĞİL" gibi kendi kendisiyle çelişen
#  bir satır basar.  Tolerans bu yüzden tek yerde durur.
MOTOR_TOLERANS = 1e-9


def motor_sec(N_hes):
    """Hesaplanan güçten büyük ya da ona eşit ilk standart kademe."""
    if N_hes is None or not isinstance(N_hes, (int, float)):
        return None
    if N_hes != N_hes or N_hes in (float("inf"), float("-inf")):
        return None
    for kademe in MOTOR_KADEMELERI:
        if kademe >= N_hes - MOTOR_TOLERANS:
            return kademe
    return None  # listenin üstünde — özel imalat


MOTOR_NOTU = (
    "Seçilen motor gücü, hesaplanan güçten büyük ilk STANDART anma "
    "gücüdür ( IEC 60072 / TS EN 60034 kademeleri ). İmalatçının "
    "kademesi farklıysa alan elle doldurulur; program yine "
    "Nsç ≥ N kontrolünü yapar."
)


# =====================================================================
#  MOTOR KORUMA CİHAZI ( SİGORTA / ŞALTER ) ANMA AKIMI KADEMELERİ
#  IEC 60269 / TS EN 60269 gG serisi.  Motor akımından seçilmesi için.
# =====================================================================
SIGORTA_KADEMELERI = (6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630)

SIGORTA_NOTU = (
    "Motor koruma cihazı anma akımı, motor anma akımının kalkış katsayısı "
    "( ofis standardı, varsayılan 1,25 ) katından büyük ilk standart kademedir "
    "( IEC 60269 gG ). AVAN değeridir: kesin seçim kalkış yöntemine, sürücü "
    "tipine ve kablo koordinasyonuna göre uygulama projesinde yapılır."
)

#  AYNI NOTUN UYGULAMA PROJESİ KARŞILIĞI.  Avan metni "kesin seçim uygulama
#  projesinde yapılır" der;  uygulama paftasında bu cümle kendi kendisiyle
#  çelişir — okuyucunun elindeki BELGE zaten uygulama projesidir.
SIGORTA_NOTU_UYGULAMA = (
    "Motor koruma cihazı anma akımı, motor anma akımının kalkış katsayısı "
    "( ofis standardı, varsayılan 1,25 ) katından büyük ilk standart kademedir "
    "( IEC 60269 gG ). Kesin seçim kalkış yöntemine, sürücü tipine ve kablo "
    "koordinasyonuna göre imalatçı verisiyle doğrulanmalıdır."
)

#  Gerilim düşümü notunun uygulama projesi karşılığı  ( aynı sebep ).
GERILIM_UC_NOKTA_NOTU_UYGULAMA = (
    "Aydınlatma ve priz devrelerinde izin verilen gerilim düşümü %1,5'tir; "
    "uç noktalara kadar olan düşüm devre bazında ayrıca kontrol edilmelidir."
)


def sigorta_sec(I_anma, katsayi=1.25):
    """
    Motor anma akımına göre standart koruma cihazı kademesi.
    Kademe listesinin dışına taşarsa None döner ( paftada 'uygulama projesinde' ).
    """
    if not isinstance(I_anma, (int, float)) or isinstance(I_anma, bool) or I_anma <= 0:
        return None
    if not isinstance(katsayi, (int, float)) or isinstance(katsayi, bool) or katsayi <= 0:
        katsayi = 1.25
    gerekli = I_anma * katsayi
    for x in SIGORTA_KADEMELERI:
        if x >= gerekli - 1e-9:
            return x
    return None

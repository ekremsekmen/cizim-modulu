# -*- coding: utf-8 -*-
"""
PARÇA KÜTÜPHANESİ  —  çizimdeki parçaların GERÇEK biçimleri

Çizimin mantığı ( yerleşim, çakışma, ölçü, testler ) parçaları dikdörtgen
"zarflarıyla" bilir;  bu kütüphane zarfın içine parçanın gerçek biçimini
koyar.  Biçim zarfın "bicim" alanına yazılır ( dünya koordinatında kapalı
çokgenler );  SVG ve DXF dikdörtgen yerine biçimi çizer.  Zarf değişmediği
için hiçbir denetim ve ölçü değişmez.

Her ölçünün KAYNAĞI yanında yazılıdır;  kaynağı olmayan değer ÇİZİM KABULÜ
diye işaretlenir.

    bicim:  [ { "noktalar": [ ( x, y ), … ], "dolu": bool, "kapali": bool, "ince": bool } ]
            dolu:  kesilen çelik kesit ( planda ray ) içi koyu boyanır
            ( ISO 128-50:  ince kesitler dolu gösterilir ).
            kapali:  yoksa True;  False açık çoklu çizgi ( sac profil:  kesitte
            sacın kalınlığı 1/20'de kalem kalınlığından incedir, sac tek
            çizgidir ).
            ince:  ikincil ayrıntı ( eşik oluğu ) 0,18 kalemle.
"""

#  ── KILAVUZ RAYLARI ( ISO 7465 ) ─────────────────────────────────────
#  Eğik tabanlı T profili:  ( b1, h1, k, n, c, f, g )  mm
#      b1 taban eni · h1 yükseklik · k dil kalınlığı · n dil boyu ( kılavuz
#      yüzeyi ) · c tabanı dile bağlayan boyun kalınlığı · f boyun dibinde
#      taban kalınlığı · g taban ucunda kalınlık
#  KAYNAK:  ISO 7465:2007 Tablo 5 ( soğuk çekilmiş, eğik tabanlı:  T70/A,
#  T75/A, T82/A, T89/A, T90/A ) — ISO 8100-33:2022 onun yerini aldı ( aynı
#  tablo, Tablo 6;  kesitin biçimi Şekil 2:  dil uçtan n boyunca k, sonra c
#  kalınlığında boyun, taban boyun dibinde f, uçta g ) — ve ISO 7465 B grubu
#  tablosu ( Türkeli Ray yayımı:  T75/B, T89/B, T90/B, T125/B ).  Ortak
#  profillerde ölçüler aynı;  /A ile /B'nin kesiti aynı, /B talaşlı işlenmiş.
#  ISO 8100-33'ün önsözü:  T125/B'nin g'si 8'den 9'a düzeltildi ( burada 9 ).
#  T127:  hesabın "127 x 89 x 16"sı T127-2/B'dir ( RAY_GEOMETRI f = 15,9 ·
#  A = 2.863 mm² );  n = 51 · c = 10 · g = 12,7 üretici özetinden — KATALOGLA
#  DOĞRULANACAK ( çokgenin alanı 2.869 mm², hesabınkiyle %0,2 ).
#  T70:  hesabın "70 x 65 x 9"u eskiden katalog değeriyle yazılıydı ( "T70-1/A",
#  A = 951 mm² );  6 Eki 2026'dan beri ISO 8100-33'ün T70/A'sı ( 940 ).
#  SINAMA:  her profilin çokgen alanı hesabın kesit alanıyla ( mukavemet_tablolari
#  RAY_PROFILI · ISO'nun S'si ) %1 içinde — testler/test_parcalar.py.
RAY_EGIK = {
    (70, 65): (70, 65, 9, 34, 6, 8, 6),             # T70/A
    (75, 62): (75, 62, 10, 30, 8, 9, 7),            # T75/A · T75/B
    (82, 68): (82, 68, 9, 34, 7.5, 8.25, 6),        # T82/A
    (89, 62): (89, 62, 16, 34, 10, 11.1, 7.9),      # T89/A · T89/B
    (90, 75): (90, 75, 16, 42, 10, 10, 8),          # T90/A · T90/B
    (125, 82): (125, 82, 16, 42, 10, 12, 9),        # T125/B
    (127, 89): (127, 89, 16, 51, 10, 15.9, 12.7),   # T127-2/B
}
#  Paralel tabanlı T profili:  ( b1, h1, k, p )  —  p taban kalınlığı
#  KAYNAK:  ISO 7465:2007 Tablo 3 = ISO 8100-33:2022 Tablo 4 ( T45/A, T50/A ).
RAY_PARALEL = {
    (45, 45): (45, 45, 5, 5),                       # T45/A
    (50, 50): (50, 50, 5, 5),                       # T50/A
}


def ray_kesiti(b, h):
    """Rayın kesiti ( kendi ekseninde ):  u tabanın arkasından dile doğru
    ( 0 … h1 ), v enine ( −b1/2 … b1/2 ).  Tabloda yoksa None ( zarf
    dikdörtgenleri çizilir )."""
    a = (round(b), round(h))
    if a in RAY_EGIK:
        b1, h1, k, n, c, f, g = RAY_EGIK[a]
        dil = h1 - n                                 # dilin başladığı yer
        yari = [(g, b1 / 2.0), (f, c / 2.0), (dil, c / 2.0), (dil, k / 2.0), (h1, k / 2.0)]
    elif a in RAY_PARALEL:
        b1, h1, k, p = RAY_PARALEL[a]
        yari = [(p, b1 / 2.0), (p, k / 2.0), (h1, k / 2.0)]
    else:
        return None
    #  Arka yüzden başlayıp bir yarıdan uca, öbür yarıdan geri
    return [(0.0, -b1 / 2.0), (0.0, b1 / 2.0)] + yari + [(u, -v) for u, v in reversed(yari)]


def ray_bicimi(b, h, uc, eksen, yon, yatay=True):
    """Rayın planda kesiti ( dolu ).  uc:  dilin ucu ( kabine / ağırlığa bakan
    yüz ) — yatay rayda x, düşeyde y;  eksen:  rayın ekseni ( öbür koordinat );
    yon:  dilden tabana doğru ( +1 / −1 ).  Tabloda yoksa None."""
    kesit = ray_kesiti(b, h)
    if kesit is None:
        return None
    arka = uc + h * yon                              # tabanın arka yüzü ( duvar tarafı )
    if yatay:
        nok = [(arka - yon * u, eksen + v) for u, v in kesit]
    else:
        nok = [(eksen + v, arka - yon * u) for u, v in kesit]
    return [{"noktalar": nok, "dolu": True}]


#  ── KAYMALI PATEN ────────────────────────────────────────────────────
#  Planda kesiti:  gövde rayın dilini U biçiminde kavrar ( astarlı yuva ).
#  Zarf ( paten_en × paten_boy ) referans projenin paftasından ( sabitler );
#  yuvanın derinliği zarfın yarısı ( dil ucundan kabine doğru gövde, dilin
#  üstünde yuva ), yuva eni dil kalınlığı + 2 × 2 mm astar boşluğu —
#  ÇİZİM KABULÜ ( tedarikçi çizimi gelince buradan değişir ).
PATEN_ASTAR = 2.0


def paten_bicimi(x0, y0, g, d, uc, k, yon, yatay=True):
    """Patenin U kesiti.  ( x0, y0, g, d ):  zarf;  uc:  dilin ucu;  k:  dil
    kalınlığı;  yon:  dilden tabana doğru ( +1 / −1 ) — yuva o yana açılır;
    yatay:  ray x yönünde ( dil x boyunca uzanır )."""
    if yatay:
        y_orta = y0 + d / 2.0
        a0, a1 = y_orta - k / 2.0 - PATEN_ASTAR, y_orta + k / 2.0 + PATEN_ASTAR
        if yon > 0:                                   # yuva sağa açılır
            nok = [(x0, y0), (x0 + g, y0), (x0 + g, a0), (uc, a0), (uc, a1), (x0 + g, a1),
                   (x0 + g, y0 + d), (x0, y0 + d)]
        else:                                         # yuva sola açılır
            nok = [(x0, y0), (x0 + g, y0), (x0 + g, y0 + d), (x0, y0 + d), (x0, a1), (uc, a1),
                   (uc, a0), (x0, a0)]
    else:
        x_orta = x0 + g / 2.0
        a0, a1 = x_orta - k / 2.0 - PATEN_ASTAR, x_orta + k / 2.0 + PATEN_ASTAR
        if yon > 0:                                   # yuva yukarı açılır
            nok = [(x0, y0), (x0 + g, y0), (x0 + g, y0 + d), (a1, y0 + d), (a1, uc), (a0, uc),
                   (a0, y0 + d), (x0, y0 + d)]
        else:                                         # yuva aşağı açılır
            nok = [(x0, y0), (a0, y0), (a0, uc), (a1, uc), (a1, y0), (x0 + g, y0),
                   (x0 + g, y0 + d), (x0, y0 + d)]
    return [{"noktalar": nok, "dolu": False}]


#  ── KAT KAPISI VE KABİN KAPISI ( planda kesit ) ──────────────────────
#  MARKASIZ:  hiçbir üreticinin birebir kopyası değil;  üç üreticinin
#  ( Wittur Hydra teknik broşürü SB.2.007539 s.7–8 ve 17 · Merih B-01 MLT
#  kataloğu s.8–9 · KONE planlama kılavuzu kapı detayı ) ORTAK biçimi:
#    KASA     sac bükme profil:  kat tarafında yüz, kapı açıklığının kenarı
#             boyunca derinliğe dönüş ( eşiğin önünde biter — arkada dudak
#             yok:  eşiğin ön çizgisine biner, eşiğin ucundan taşardı ), dış
#             kenarda duvara kanca ( Merih planı;  Wittur "standart kasa
#             derinliği DF = 60" — programın kasa_derinlik'i de 60 ).
#    EŞİK     tek parça alüminyum profil, kanat cebinin altından da sürer
#             ( Fermator 40/10:  eşik boyu T2'de 1,5·PL + 40 = açıklık + cep );
#             üstünde HER KANAT DÜZLEMİ İÇİN BİR KILAVUZ OLUĞU ( Wittur eşik
#             kesitleri ).  Derinlikler programda zaten üreticilerle tutuyor:
#             2 kanat teleskopik 90 ( Wittur 90 · Merih 95 ), 3 kanat 135
#             ( Wittur 136 · Merih 135 ).
#    KANAT    sac tepsi:  yüz düz, uçlar dönük, arkada dudak ( Merih planı ).
#  Ölçüler zarftan ( sabitler ) gelir;  dudak ve oluk enleri üreticilerin
#  çizimlerinde ölçülü değil, oranlarından — ÇİZİM KABULÜ.
KASA_DUDAK = 20.0
KANAT_DUDAK = 15.0
OLUK = 10.0


def kasa_bicimi(x0, y0, g, d, acik_sagda):
    """Kasa dikmesinin sac profili.  ( x0, y0, g, d ):  zarf, y0 kat tarafı;
    acik_sagda:  kapı açıklığı zarfın sağında ( sol dikme )."""
    kenar, dis = (x0 + g, x0) if acik_sagda else (x0, x0 + g)
    nok = [(dis, y0 + KASA_DUDAK), (dis, y0), (kenar, y0), (kenar, y0 + d)]
    return [{"noktalar": nok, "kapali": False}]


def kanat_bicimi(x0, y0, g, d, yuz_altta):
    """Kanadın sac tepsi kesiti.  yuz_altta:  yüz y0'da ( kat kapısı — kat
    tarafı );  değilse y0 + d'de ( kabin kapısı — kabin tarafı )."""
    yuz, arka = (y0, y0 + d) if yuz_altta else (y0 + d, y0)
    dudak = min(KANAT_DUDAK, g / 3.0)
    nok = [(x0 + dudak, arka), (x0, arka), (x0, yuz), (x0 + g, yuz), (x0 + g, arka),
           (x0 + g - dudak, arka)]
    return [{"noktalar": nok, "kapali": False}]


def esik_cizgileri(x0, y0, g, d, sol_acik, sag_acik):
    """Eşiğin ( ya da cebin altındaki uzantısının ) dış çizgisi.  sol_acik /
    sag_acik:  o yanda eşik sürer ( cep ya da eşiğin kendisi ) — kenar çizilmez."""
    x1, y1 = x0 + g, y0 + d
    out = [{"noktalar": [(x0, y0), (x1, y0)], "kapali": False},
           {"noktalar": [(x0, y1), (x1, y1)], "kapali": False}]
    for x, acik in ((x0, sol_acik), (x1, sag_acik)):
        if not acik:
            out.append({"noktalar": [(x, y0), (x, y1)], "kapali": False})
    return out


def oluk_cizgileri(x0, x1, merkezler, ortuler):
    """Kanat kılavuz oluklarının görünen kenarları ( ince ).  merkezler:  kanat
    düzlemlerinin orta çizgileri ( y );  ortuler:  üstünde duran parçaların
    kutuları ( x0, y0, x1, y1 ) — oluk onların altında görünmez."""
    out = []
    for m in sorted(set(round(v, 6) for v in merkezler)):
        for y in (m - OLUK / 2.0, m + OLUK / 2.0):
            araliklar = [(x0, x1)]
            for a0, b0, a1, b1 in ortuler:
                if not b0 - 1e-6 <= y <= b1 + 1e-6:
                    continue
                yeni = []
                for p, q in araliklar:
                    if a1 <= p or a0 >= q:
                        yeni.append((p, q))
                        continue
                    if a0 > p:
                        yeni.append((p, a0))
                    if a1 < q:
                        yeni.append((a1, q))
                araliklar = yeni
            out += [{"noktalar": [(p, y), (q, y)], "kapali": False, "ince": True}
                    for p, q in araliklar if q - p > 1.0]
    return out


#  ── RAY KONSOLU, TIRNAK VE CIVATALAR ( planda, yukarıdan ) ───────────
#  KONSOL ÇİFTİ ( TSE K 179 tipi standart konsol ):  duvar konsolu ve ray
#  konsolu, ikisi de L bükme sac;  duvar konsolunun dik ayağı duvarda, ray
#  konsolununki rayın tabanının arkasında, yatay ayaklar üst üste ( ray
#  konsolununki üstte ) ve iki cıvatayla eğik kanallardan bağlı ( ayar payı ).
#  KAYNAK:  İTÜ yüksek lisans tezi "Kılavuz Ray Bağlantı Elemanlarının Gerilme
#  Analizi" ( 2011 ) Şekil 3.16 · Çizelge 3.9 ( Savera'nın standart konsolu )
#  ve Şekil B.3 – B.4 ( montaj );  Sancak · Candaş · İmrak 2021 ( konsol en az
#  S235JR, tırnak S355JR — TSE 2012 ).  LiftDesigner'ın planı da konsolu iki
#  plaka çizer.
#      ray tabanı ≤ b1   A  dik ayak  B  yatay ayak  C  sac J  kanallar arası H  kanal eni E
KONSOL_TIPLERI = (
    (65, (130, 50, 75, 4, 85, 12.0)),        # T45/A · T50/A · T65/A
    (90, (200, 62, 95, 5, 155, 13.5)),       # T70 · T75 · T78/B · T80 · T82 · T89 · T90
    (1e9, (270, 65, 100, 6, 220, 13.5)),     # T114/B · T125/B · T127 · T140
)
#  Konsolun duvar boyunca eni programın sabitidir ( konsol_kabin_boy — ofis
#  standardı;  Savera'nın A'sı T89'da 200 ).  Duvar ile ray arası iki standart
#  ayağın erişiminden büyükse ayaklar uzar:  yatay ayaklar Savera'nın C'si kadar
#  BİNDİRİLİR ( iki kanal da bindirmede kalsın ) — ÇİZİM KABULÜ.  Standart
#  kuyularda duvar – kabin rayı arkası 313:  ayaklar 204'er.
#  Kanal eni → cıvata ( ISO 273 boşluk delikleri:  M12 orta 13,5 · M10 kaba 12 ).
KANAL_CIVATASI = {12.0: 10, 13.5: 12}
#  Altıgen başlı cıvata ve somun ( ISO 4017 · ISO 4032 ):  çap → ( anahtar
#  ağzı s, baş yüksekliği k, somun yüksekliği m )
ISO_CIVATA = {8: (13, 5.3, 6.8), 10: (16, 6.4, 8.4), 12: (18, 7.5, 10.8),
              14: (21, 8.8, 12.8), 16: (24, 10.0, 14.8)}
#  RAY TIRNAĞI ( rayın tabanını konsola bastırır;  her yanda bir tane ):
#  KAYNAK Donati GF serisi ( ürün sayfaları ):  ray dili k → ( boy L, en,
#  topuk yüksekliği h2, dil yüksekliği h1, cıvata )
#      k  5:  GF16647  40 × 34  h 2 / 7    M8   ( T45 · T50 )
#      k  9:  GF16648  70 × 45  h 4 / 7    M12  ( T70-1 · T82;  cıvata GF01036'nın ø13 deliğinden )
#      k 10:  GF16649  60 × 53  h 4 / 11   M12  ( T75-3 · T89-1 )
#      k 16:  GF16650  65 × 52  h 7 / 13   M14  ( T89 · T127-1;  T90 · T125 aynı 16 mm sınıfı )
TIRNAK = {5: (40, 34, 7, 2, 8), 9: (70, 45, 7, 4, 12), 10: (60, 53, 11, 4, 12),
          16: (65, 52, 13, 7, 14)}
#  Tırnağın cıvatası ray tabanının kenarından TIRNAK_PAYI dışarıda ( deliğin
#  kenarı tabana değmez ) — ÇİZİM KABULÜ.
TIRNAK_PAYI = 2.0


def konsol_tipi(b1):
    """Ray tabanı enine göre Savera konsolu:  ( A, B, C, J, H, E )."""
    return next(t for sinir, t in KONSOL_TIPLERI if b1 <= sinir)


def _donustur(duvar, eksen, s, yatay):
    """( u duvardan raya, v duvar boyunca ) → dünya."""
    if yatay:
        return lambda u, v: (duvar + s * u, eksen + v)
    return lambda u, v: (eksen + v, duvar + s * u)


def _altigen(p, s):
    """Yukarıdan görülen altıgen cıvata başı / somun:  merkez p, anahtar ağzı s."""
    import math
    r = s / math.sqrt(3.0)
    return [(p[0] + r * math.cos(math.radians(30 + 60 * i)), p[1] + r * math.sin(math.radians(30 + 60 * i)))
            for i in range(6)]


def konsol_cifti_bicimi(duvar, arka, eksen, boy, b1, yatay=True):
    """Duvar konsolu + ray konsolu ( yukarıdan ).  duvar:  duvarın yüzü;
    arka:  rayın tabanının arka yüzü ( ikisi de yatayda x, düşeyde y );
    eksen:  ray ekseni;  boy:  konsolun duvar boyunca eni;  b1:  ray tabanı."""
    A, B, C, J, H, E = konsol_tipi(b1)
    s = 1.0 if arka > duvar else -1.0
    d = abs(arka - duvar)
    P = _donustur(duvar, eksen, s, yatay)
    a = boy / 2.0
    if d < 3 * J:                                     # ray duvara dayalı:  tek sac
        return [{"noktalar": [P(0, -a), P(d, -a), P(d, a), P(0, a)]}]
    ayak = min(max(C, (d + C) / 2.0), d - J)          # her iki yatay ayak
    ust = d - ayak                                    # ray konsolunun ayağının ucu
    out = [
        #  ray konsolu ( üstte ):  yatay ayağı + dik ayağının üst yüzü
        {"noktalar": [P(ust, -a), P(d, -a), P(d, a), P(ust, a)]},
        {"noktalar": [P(d - J, -a), P(d - J, a)], "kapali": False},
        #  duvar konsolu:  ray konsolunun altında kalmayan kısmı + dik ayağı
        {"noktalar": [P(ust, -a), P(0, -a), P(0, a), P(ust, a)], "kapali": False},
        {"noktalar": [P(J, -a), P(J, a)], "kapali": False},
    ]
    #  Bağlantı cıvataları:  bindirmenin ortasında, kanallar arası H
    sc = ISO_CIVATA[KANAL_CIVATASI[E]][0]
    orta = (ust + min(ayak, d)) / 2.0
    for v in (-H / 2.0, H / 2.0):
        if abs(v) + sc / 2.0 <= a:
            out.append({"noktalar": _altigen(P(orta, v), sc)})
    return out


#  KARŞI AĞIRLIK KONSOL ÇERÇEVESİ ( LiftDesigner gibi ):  ağırlığın çevresinde
#  profillerden bir çerçeve — her ağırlık rayının tabanı, tabanın dış yanındaki
#  bir profile ( ray profili ) dayanır;  ray profilleri yandaki ağırlıkta duvardan
#  kabin tarafındaki boyuna profile ( programın ara kirişi — kabin rayı ona
#  bağlanır ) uzanır;  yer varsa duvarda da boyuna bir profil vardır.
#  KAYNAK:  LiftDesigner paftaları — K431 ( yanda;  çerçeve 310 × 820 ), 1250 KG
#  yanda makine dairesiz, K111 ( arkada ):  dört profil de planda 40 mm.
#  4815-6 ( yanda, ağırlık duvara yakın ):  duvar profili yok, yalnız ray profilleri.
CERCEVE_PROFILI = 40.0


def profil_bicimi(u0, u1, v0, v1, yatay=True):
    """Çerçeve profili:  u ( duvara dik ) u0 … u1, v ( duvar boyunca ) v0 … v1
    — yatayda u = x, düşeyde u = y."""
    a, b = sorted((u0, u1))
    c, d = sorted((v0, v1))
    nok = [(a, c), (b, c), (b, d), (a, d)] if yatay else [(c, a), (c, b), (d, b), (d, a)]
    return [{"noktalar": nok}]


def tirnak_uzanimi(b, h):
    """Tırnakların ray ekseninden en uzak ucu ( taban boyunca );  tırnak yoksa
    tabanın yarısı."""
    k = ray_dil_kalinligi(b, h)
    t = TIRNAK.get(round(k)) if k is not None else None
    if t is None:
        return b / 2.0
    L, _en, _h2, _h1, d = t
    return b / 2.0 + d / 2.0 + TIRNAK_PAYI + L / 2.0


def tirnak_bicimi(arka, eksen, b1, g, k, yon, J=None, yatay=True):
    """Rayın iki tırnağı ve cıvataları ( yukarıdan ).  arka:  tabanın arka
    yüzü;  yon:  arkadan dile doğru ( +1 / −1 );  g:  tabanın uç kalınlığı;
    k:  dil kalınlığı;  J:  arkadaki konsol sacının kalınlığı ( verilirse
    somun sacın arkasında çizilir ).  Tabloda olmayan dilde [ ]."""
    t = TIRNAK.get(round(k))
    if t is None:
        return []
    L, _en, h2, h1, d = t
    sc, kb, m = ISO_CIVATA[d]
    P = _donustur(arka, eksen, yon, yatay)
    out = []
    for z in (-1.0, 1.0):
        vb = b1 / 2.0 + d / 2.0 + TIRNAK_PAYI          # cıvatanın ekseni
        v0, v1 = vb - L / 2.0, vb + L / 2.0            # tırnak ( içte dil, dışta topuk )
        kenar = b1 / 2.0
        alt = max(g, h2 - h1)                          # dilin altı ( tabanın üstünde )
        nok = [(v0, alt), (v0, h2), (v1, h2), (v1, 0.0), (kenar, 0.0), (kenar, alt)] \
            if v0 < kenar else [(v0, 0.0), (v0, h2), (v1, h2), (v1, 0.0)]
        out.append({"noktalar": [P(u, z * v) for v, u in nok]})
        #  cıvata başı tırnağın üstünde, somun konsol sacının arkasında ( yandan )
        bas = [(vb - sc / 2.0, h2), (vb + sc / 2.0, h2), (vb + sc / 2.0, h2 + kb), (vb - sc / 2.0, h2 + kb)]
        out.append({"noktalar": [P(u, z * v) for v, u in bas]})
        if J is not None:
            som = [(vb - sc / 2.0, -J), (vb + sc / 2.0, -J), (vb + sc / 2.0, -J - m), (vb - sc / 2.0, -J - m)]
            out.append({"noktalar": [P(u, z * v) for v, u in som]})
    return out


def alan(noktalar):
    """Kapalı çokgenin alanı ( mm² )."""
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1)
                   in zip(noktalar, noktalar[1:] + noktalar[:1]))) / 2.0


def ray_taban_ucu(b, h):
    """Ray tabanının uçtaki kalınlığı ( eğik tabanda g, paralelde p );  tabloda yoksa None."""
    a = (round(b), round(h))
    if a in RAY_EGIK:
        return RAY_EGIK[a][6]
    if a in RAY_PARALEL:
        return RAY_PARALEL[a][3]
    return None


def ray_dil_kalinligi(b, h):
    """Rayın dil kalınlığı ( k );  tabloda yoksa None."""
    a = (round(b), round(h))
    if a in RAY_EGIK:
        return RAY_EGIK[a][2]
    if a in RAY_PARALEL:
        return RAY_PARALEL[a][2]
    return None

# -*- coding: utf-8 -*-
"""
ÖLÇÜNÜN KAYNAĞI  —  çizimdeki bir ölçü hangi girdilerden çıkar, nasıl değişir

Çizim girdilerden kurulur;  ekranda bir ölçüye tıklanınca program onun hangi
girdiden geldiğini söyler ve değiştirmeyi O GİRDİYE yazar.  Çizim elle
değişmez:  hesap ile çizim aynı sayıyı kullanmaya devam eder.

Kaynak elle etiketlenmez — yüz kadar ölçü var, zincir ölçülerin uçları başka
başka parçalardır, sonradan eklenen bir ölçü etiketsiz kalırdı.  TÜREVLE
bulunur ( turevden ):  çizim bir kez, girdileri izli sayıya sarılarak kurulur
( cizim/izli.py ) ve her ölçünün uzunluğu hangi girdiye hangi eğimle ( girdi
1 artınca ölçü kaç artar ) bağlı olduğunu taşır — tıklama anında yanıtlanır.
Eski yol ( cozumle:  her girdi 1 mm oynatılıp çizim 200 – 280 kez yeniden
kurulur, 3 – 9 sn ) türevin testteki denetçisi ve yedeğidir
( testler/test_olcu_turevi.py ).  Değiştirmede girdinin yeni değeri eğimden
bulunur ve çizim yeniden kurularak DOĞRULANIR ( coz );  bağıntı doğrusal
değilse kiriş yöntemiyle hedefe yaklaşılır.

Kaynak türleri ( aday["tur"] ):
    sayi    sayı kutusu — ölçüden değiştirilebilir
    tam     tam sayılı kutu ( durak adedi, halat adedi ) — yalnız gösterilir
    secim   seçim kutusu ( ray profili … ) — sayılı seçenekler arasından seçilir
    ofis    Sabitler sekmesindeki ofis standardı ( çizimin ürün ölçüleri dahil —
            tek katalog, karar 12 ) — yalnız gösterilir

Bu modül çizimi kurmayı bilmez:  kur( degisiklik , serbest ) işlevi dışarıdan
verilir ( hesap/api/cizim.py — formun girdisinden çizimin ölçülerine ).
"""

import math
from temel import sayi_mi
from cizim import izli
import re

ESIK = 1e-7  # bu kadarlık değişim "değişmedi" sayılır ( kayan nokta )
KAYMA = 200.0  # dizi değiştiyse en yakın aynı sözlü ölçünün en çok kayması ( toplam )
ADIM_OLCU = 15.0  # değiştirirken izleme adımı:  ölçü adım başına en çok bu kadar değişir
DOGRULAMA = 0.05  # ölçü hedefe bu kadar yaklaşınca doğrulandı ( mm )

_SAYI = re.compile(r"[-+]?\d[\d.,]*")


def olculer(elemanlar):
    return [e for e in elemanlar if e.get("tip") == "olcu"]


def _imza(o):
    """Ölçünün kimliğinin sayıdan bağımsız kısmı:  yönü ve yazısının sözü
    ( "KUYU GENİŞLİĞİ 2100" → "KUYU GENİŞLİĞİ #" )."""
    return o["yon"], _SAYI.sub("#", o.get("metin") or "")


def _uzaklik(p, q):
    return (
        abs(p["a"][0] - q["a"][0])
        + abs(p["a"][1] - q["a"][1])
        + abs(p["b"][0] - q["b"][0])
        + abs(p["b"][1] - q["b"][1])
        + abs(p["kot"] - q["kot"])
    )


def _en_yakin(o, liste, tolerans):
    im = _imza(o)
    aday = [(_uzaklik(o, q), j) for j, q in enumerate(liste) if _imza(q) == im]
    if not aday:
        return None
    d, j = min(aday)
    return j if d <= tolerans else None


def _sira_ile(o, i, taban, yeni):
    """Aynı sözlü ölçüler arasındaki sırasıyla:  zincirin SONUNA ölçü eklenince
    ya da sonundan çıkınca ( konsol sayısı değişti ) öndekiler yerini korur."""
    im = _imza(o)
    m = sum(1 for p in taban[:i] if _imza(p) == im)
    ayni = [j for j, q in enumerate(yeni) if _imza(q) == im]
    return ayni[m] if m < len(ayni) else None


def eslestir(taban, yeni, tolerans=None, sira_yedek=False):
    """Taban ölçülerinin yeni listedeki karşılıkları ( indeks ya da None ).

    Ölçü dizisi aynı kaldıysa ( sayısı, sırası, yazılarının sözü ) sırayla:
    küçük bir oynatmada ölçüler yer değiştirmez, ama uzaklar çok kayabilir —
    konsol arası 1 mm artınca 22. konsol 22 mm kayar.  Dizi değiştiyse
    ( sıfır boylu ölçü çıktı ya da kayboldu ):  tolerans None ise eşleşme yok
    ( seçim kutusu gibi kesikli değişimler ), sayıysa aynı sözlü en yakın ölçü;
    sira_yedek ile o da yoksa aynı sözlüler arasındaki sırası ( değiştirirken
    izleme — kaynak çözümlemesinde kullanılmaz, yanlış ölçüyü eşleyebilir )."""
    ayni = len(taban) == len(yeni) and all(_imza(p) == _imza(q) for p, q in zip(taban, yeni))
    if ayni:
        return list(range(len(taban)))
    if tolerans is None:
        return [None] * len(taban)
    m = [_en_yakin(o, yeni, tolerans) for o in taban]
    if sira_yedek:
        m = [j if j is not None else _sira_ile(o, i, taban, yeni) for i, (o, j) in enumerate(zip(taban, m))]
    return m


def _dogrusal(egimler):
    s = sum(egimler) / len(egimler)
    return s, len(egimler) == 2 and abs(egimler[0] - egimler[1]) <= 1e-6 * max(1.0, abs(s))


def _sayisal(kur, taban, ad, kaynak):
    """Sayı girdisi:  ±adım oynatılır ( ofis standardında yalnız + — yalnız
    gösterilir ).  Çizim kurulamazsa girilmiş türetilen alanlar bırakılıp
    yeniden denenir:  kaide girilmişken kuyu dibi ( ya da kabinin şase altı )
    tek başına değişemez ( zincir ), birlikte değişirler — kaynak "bağlı" olur."""
    yonler = (1,) if ad["tur"] == "ofis" else (1, -1)
    #  Tam sayı ( durak, tampon adedi ) 1 mm değil, düzen değiştirir:  çizimin
    #  kendi denetiminden geçmeyen durum sayılmaz.
    denetle = ad["tur"] == "tam"
    egim, bagli = {}, False
    for yon in yonler:
        dx = yon * ad["adim"]
        degisiklik = {ad["kimlik"]: ad["deger"] + dx}
        e, serbest = kur(degisiklik, denetle=denetle), False
        if e is None:
            e = kur(degisiklik, serbest=True, denetle=denetle)
            serbest = e is not None
        if e is taban:
            return  # çizimin girdisini hiç değiştirmiyor ( hesabın girdisi )
        if e is None:
            continue
        bagli = bagli or serbest
        for i, j in enumerate(eslestir(taban, e, KAYMA)):
            if j is not None:
                egim.setdefault(i, []).append((e[j]["uzunluk"] - taban[i]["uzunluk"]) / dx)
    for i, ds in egim.items():
        if all(abs(d * ad["adim"]) <= ESIK for d in ds):
            continue
        s, dog = _dogrusal(ds)
        kaynak[i].append(
            {"kimlik": ad["kimlik"], "tur": ad["tur"], "egim": s, "dogrusal": dog, "bagli": bagli}
        )


def _secim(kur, taban, ad, kaynak):
    """Seçim kutusu:  komşu iki seçenek denenir ( çizimin kendi denetimiyle —
    seçim düzeni değiştirebilir:  makine dairesizde 1:1 reddedilir ).
    Seçenekler sayıysa ( kapı genişliği ) eğim de bulunur."""
    sec = list(ad["secenekler"] or [])
    k = sec.index(ad["deger"]) if ad["deger"] in sec else -1
    alternatif = [sec[j] for j in (k + 1, k - 1) if 0 <= j < len(sec)] if k >= 0 else sec[:2]
    sayisal = sayi_mi(ad["deger"]) and all(sayi_mi(x) for x in sec)
    degisen = {}
    for v in alternatif:
        e = kur({ad["kimlik"]: v}, denetle=True)
        if e is None or e is taban:
            continue
        for i, j in enumerate(eslestir(taban, e)):
            if j is not None and abs(e[j]["uzunluk"] - taban[i]["uzunluk"]) > ESIK:
                degisen.setdefault(i, []).append((v, e[j]["uzunluk"] - taban[i]["uzunluk"]))
    for i, lst in degisen.items():
        s, dog = None, False
        if sayisal:
            s, dog = _dogrusal([du / (v - ad["deger"]) for v, du in lst])
        kaynak[i].append({"kimlik": ad["kimlik"], "tur": "secim", "egim": s, "dogrusal": dog, "bagli": False})


def turevden(olculer_, adaylar):
    """Her ölçünün kaynakları İZLİ kurulumdan ( cizim/izli.py ):  çizim bir kez,
    girdileri izli sayıya sarılarak kurulur;  ölçünün uzunluğu hangi girdiye
    hangi eğimle bağlı olduğunu taşır.  cozumle() ile aynı biçim ( adayların
    sırasıyla );  yalnız adaylar arasındaki girdiler sayılır.

    Türev yereldir:  ölçünün bir eşikte sıçradığını ( dogrusal ) ve girdinin
    tek başına değişemediğini ( bagli ) söylemez — değiştirirken çizim yeniden
    kurularak doğrulanır ( coz ).  Kategori seçimleri ( ray profili … ) türevle
    bulunmaz:  ölçünün tek kaynağıysa ölçü kendisi söyler ( o["secim"] )."""
    aday = {a["kimlik"]: a for a in adaylar}
    sira = {a["kimlik"]: n for n, a in enumerate(adaylar)}
    kaynak = []
    for o in olculer_:
        ks = [
            {"kimlik": k, "tur": aday[k]["tur"], "egim": e, "dogrusal": True, "bagli": False}
            for k, e in izli.turev(o["uzunluk"]).items()
            if k in aday and abs(e * aday[k].get("adim", 1.0)) > ESIK
        ]
        ks += [
            {"kimlik": ("girdi", a), "tur": "secim", "egim": None, "dogrusal": False, "bagli": False}
            for a in o.get("secim") or ()
            if ("girdi", a) in aday and all(x["kimlik"] != ("girdi", a) for x in ks)
        ]
        ks.sort(key=lambda x: sira[x["kimlik"]])
        kaynak.append(ks)
    return kaynak


def cozumle(kur, adaylar):
    """Taban çizimdeki her ölçünün kaynakları.

    kur( degisiklik , serbest=False , denetle=False ) → ölçü listesi ( olculer )
        ya da None
        degisiklik:  { aday kimliği : yeni değer };  serbest:  girilmiş
        türetilen alanlar bırakılır ( çizimden yeniden türetilir );  denetle:
        çizimin kendi doğrulaması da ( kesikli değişimlerde ).  Girdi
        çizimin girdisini değiştirmiyorsa TABAN listesinin kendisi dönebilir
        ( kur({}) ile gelen nesne ) — o aday atlanır.
    adaylar:  [ { kimlik, tur, deger, adim ( sayılarda ), secenekler ( seçimde ) } ]
    Döner:  ( taban ölçüleri , her ölçü için [ { kimlik, tur, egim, dogrusal,
              bagli } ] )  —  taban kurulamıyorsa ( None , None )."""
    taban = kur({})
    if taban is None:
        return None, None
    kaynak = [[] for _ in taban]
    for ad in adaylar:
        (_secim if ad["tur"] == "secim" else _sayisal)(kur, taban, ad, kaynak)
    return taban, kaynak


def coz(kur, taban, i, kimlik, deger, egim, hedef, serbest=False, dogrusal=False):
    """i. ölçü hedef olsun diye girdinin ( kimlik ) yeni değeri.

    Girdi eğimden bulunan değere ADIM ADIM götürülür ve her adımda aynı ölçü
    bulunur ( zincirde uçlar yer değiştirebilir );  sonra ölçü hedefte değilse
    ( bağıntı doğrusal değil ) kiriş yöntemiyle yaklaşılır.  Her adımda çizim
    yeniden kurulur:  sonuç çizimin kendisiyle doğrulanır.
    Ölçü hedefte doğrulanamazsa ve bağıntı DOĞRUSALSA ( çözümlemede iki yönde
    aynı eğim ) ölçü yolda BÖLÜNMÜŞ olabilir:  zincirde bir parça sıfırdan
    geçince uçlar yer değiştirir ( kabin kuyu ortasının öbür yanına geçince
    "995" ölçüsü "5 + 1.000" olur ), sıradaki ölçü başka bir aralıktır — kiriş
    yöntemi o aralığı izleyip saçma değerlere gidiyordu ( 1022:  995 → 1.005
    için kaçıklık 5 → −15, doğrusu −5;  kabin genişliği 58.430, kasnak çapı
    2·10⁻¹² ).  Doğrusal tahminle kurulan çizimde ölçü iki ardışık parçaya
    bölünmüş, toplamları hedefse doğrusal tahmin döner ( bolundu ).  Değilse
    ( sığınma alanı 25 mm'lik adımla kayar:  1 mm'de doğrusal görünen ölçü
    20 mm'de başka yere atlar ) değer yoktur — çağıran reddeder.  Kiriş yöntemi
    hedefi DOĞRULARSA o kullanılır ( 1250 KG'de kabin üstündeki 295 → 305 için
    kabin 1.240 → 1.300;  doğrusal tahmin 1.250'de ölçü 280 olur ).
    Döner:  { deger , olcu ( ulaşılan ) , dogrulandi , bolundu }."""
    u0 = taban[i]["uzunluk"]
    if abs(hedef - u0) <= DOGRULAMA:
        return {"deger": deger, "olcu": u0, "dogrulandi": True, "bolundu": False}
    if not egim:
        return {"deger": deger, "olcu": u0, "dogrulandi": False, "bolundu": False}
    x_hedef = deger + (hedef - u0) / egim
    n = max(1, min(400, math.ceil(abs(hedef - u0) / ADIM_OLCU)))
    liste, j, x = taban, i, deger
    for k in range(1, n + 1):
        x = deger + (x_hedef - deger) * k / n
        e = kur({kimlik: x}, serbest=serbest)
        j = eslestir(liste, e, KAYMA, sira_yedek=True)[j] if e is not None else None
        if j is None:
            return _bolunmus(kur, taban[i], kimlik, x_hedef, hedef, serbest, dogrusal)
        liste = e
    u, xp, up = liste[j]["uzunluk"], deger, u0
    for _ in range(12):
        if abs(u - hedef) <= 1e-7 or abs(u - up) < 1e-12:
            break
        x_yeni = x + (hedef - u) * (x - xp) / (u - up)
        e = kur({kimlik: x_yeni}, serbest=serbest)
        j2 = eslestir(liste, e, KAYMA, sira_yedek=True)[j] if e is not None else None
        if j2 is None:
            break
        xp, up, x, liste, j = x, u, x_yeni, e, j2
        u = liste[j]["uzunluk"]
    if abs(u - hedef) > DOGRULAMA and dogrusal:
        return _bolunmus(kur, taban[i], kimlik, x_hedef, hedef, serbest, dogrusal)
    return {"deger": x, "olcu": u, "dogrulandi": abs(u - hedef) <= DOGRULAMA, "bolundu": False}


def _bolunmus(kur, o, kimlik, x, hedef, serbest, dogrusal):
    """Doğrusal tahminle ( x ) kurulan çizimde ölçü ( o ) iki ardışık parçaya
    bölünmüş mü:  aynı kotta, aynı yönde, uç uca iki ölçünün toplamı hedef."""
    bolundu = False
    e = kur({kimlik: x}, serbest=serbest) if dogrusal else None
    if e is not None:
        ek = 0 if o["yon"] == "yatay" else 1
        zincir = sorted(
            (q for q in e if q["yon"] == o["yon"] and abs(q["kot"] - o["kot"]) < 1.0),
            key=lambda q: min(q["a"][ek], q["b"][ek]),
        )
        bolundu = any(
            abs(max(p["a"][ek], p["b"][ek]) - min(q["a"][ek], q["b"][ek])) < 1e-6
            and abs(p["uzunluk"] + q["uzunluk"] - hedef) <= DOGRULAMA
            for p, q in zip(zincir, zincir[1:])
        )
    return {"deger": x, "olcu": None, "dogrulandi": False, "bolundu": bolundu}

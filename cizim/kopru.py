# -*- coding: utf-8 -*-
"""
HESAP → ÇİZİM KÖPRÜSÜ

Hesap programının bir asansör için topladığı girdiden ( ve hesabın
sonucundan ) çizim girdisini ( cizim/girdi.py sözleşmesi ) kurar.

TEK DOĞRULUK KAYNAĞI.  Hesapta olan bir ölçü çizimde ikinci kez sorulmaz:
kabin ve kuyu ölçüleri, ray profilleri, paten araları, tamponlar, askı oranı,
halatlar, makine ve kaidesi hesabın girdisinden gelir.  Kuyu tabanına ve ray
konsollarına gelen kuvvetler hesabın SONUCUNDAN gelir.  Yalnız çizimin
ihtiyaç duyup hesabın bilmediği ölçüler ( kuyu derinliği, durak adedi, kapının
ve kabinin kuyudaki yeri … ) ayrıca sorulur:  ALANLAR.

İKİSİNİN AYNI ŞEYİ SÖYLEMESİ DENETLENİR.  Aynı fiziksel büyüklük iki yerde
modelleniyorsa ( halat sarılma açısı, askı noktası, kasnak çapları, makine
kirişlerinin mesnet aralığı ) çizimin geometrisi hesabın girdisiyle
karşılaştırılır;  uyuşmazsa çizim durur ve DOĞRU DEĞERİ söyler.  Pafta kendi
içinde çelişmez.

Eksen dönüşümleri ( hesap:  TS EN 81-50 Ek C.1.2 — orijin kabin ray ekseni,
x kabin derinliği boyunca kapıdan arkaya, y rayları birleştiren doğrultu;
çizim:  orijin kuyunun sol-ön iç köşesi, x genişlik, y derinlik ):

    kapı hattı ( kat eşiğinin kabine bakan kenarı )  y = hat
    kabin ray ekseni                                 y = hat + RK
    askı noktası                                     y = hat + RK + xs
"""
import math

from cizim import girdi as CG
from cizim import katlar as CKA
from cizim import sabitler as CS
from tasarim import alanlar as _TS, gorunum as _TG


def _sayi(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


#  ( anahtar , etiket , birim , tür , seçenekler , varsayılan , gelişmiş , açıklama )
#  Varsayılanı None olan alan boş bırakılabilir:  değeri açıklamada yazan
#  kuraldan gelir ( _varsayilan ).  Tanımlar tasarım şemasında
#  ( tasarim/alanlar.py, sözleşmesi CIZ );  formda kendi tasarım grubunda durur.
ALANLAR = tuple((a.anahtar, a.etiket, a.birim, a.tur, a.secenekler, a.varsayilan,
                 a.gelismis, a.bilgi) for a in _TS.ALANLAR if a.sozlesme == _TS.CIZ)
ALAN = {a[0]: a for a in ALANLAR}

#  Makine dairesi binaya aittir:  bütün asansörlerde tek değer.
PROJE_GENELI = _TG.anahtarlar(_TS.CIZ, proje_geneli=True)
#  Makine yerleşimine göre çizime girmeyen alanlar ( ekran gizler ).
YALNIZ_DAIRELI = _TG.anahtarlar(_TS.CIZ, yerlesim="daireli")
YALNIZ_MRL = _TG.anahtarlar(_TS.CIZ, yerlesim="mrl")


#  TEK KATALOG ( karar 12 ):  çizimin bütün ürün ölçüleri hesabın Sabitler
#  sekmesinde ( ofis standardı ) değiştirilir;  çizim, yerleşimin ölçü listesi
#  ve hesabın bölüm 11'i aynı sayıyı kullanır.  hesap anahtarı → çizim sabiti
#  ( cizim/sabitler.py;  adı farklı olan tek:  tavan_payi → tavan_kirisi ).
OFIS_SABITLERI = {CS.ofis_adi(c): c for c in CS.SABIT}


def cizim_sabitleri(A):
    """Hesabın ofis standardındaki ( A["_ofis"] ) çizim sabitleri — ezme
    sözlüğü.  Aralık dışındaki değer çizime geçmez ( CS.aralik — hesap onu
    reddeder ve durur;  sıfır yalnız boşluk ve paylarda geçerlidir ).  Ölçü
    kaynağı çözümlemesi ( olcu_kaynagi ) bir ölçüyü oynatırken de buradan
    geçer."""
    ofis = A.get("_ofis") if isinstance(A.get("_ofis"), dict) else {}
    return {c: float(ofis[o]) for o, c in OFIS_SABITLERI.items()
            if _sayi(ofis.get(o)) and CS.aralik(c)[0] <= ofis[o] <= CS.aralik(c)[1]}


#  BOŞSA KURALLA DOLAN ÇİZİM ALANLARI ( varsayılanı None ):  kutu boşken
#  değer bir kuraldan gelir ( "boşsa Gy + 60" … ).  Ölçü kaynağı çözümlemesi
#  kutunun ETKİN değerini çizimin girdisinden okur — okumasaydı DBGW ölçüsü
#  "karşı ağırlık genişliğinden geliyor" görünür, ölçüyü değiştirmek Gy'yi
#  değiştirirdi.  Yol:  çizim girdisinde ( g ) değerin durduğu yer.
KURALLI = {
    "kuyu_duvar_on": ("kuyu", "duvar_on"),
    "kuyu_duvar_arka": ("kuyu", "duvar_arka"),
    "kuyu_duvar_sol": ("kuyu", "duvar_sol"),
    "kuyu_duvar_sag": ("kuyu", "duvar_sag"),
    "kabin_ray_arasi": ("kabin_ray", "arasi"),
    "agirlik_ray_arasi": ("agirlik", "ray_arasi"),
    "agirlik_ray_duvar": ("agirlik", "ray_duvar"),
    "kabin_kasnak_arasi": ("aski", "kasnak_arasi"),
    "regulator_kaciklik": ("kuyu_dibi", "regulator_kaciklik"),
    "agirlik_tampon_boyu": ("dusey", "agirlik_tampon_boyu"),
    #  Kuralı yok:  tek tamponda boştur ( etkin değeri de yok ),  ikisinde girilir
    "kabin_tampon_arasi": ("kuyu_dibi", "kabin_tampon_arasi"),
    "agirlik_tampon_arasi": ("kuyu_dibi", "agirlik_tampon_arasi"),
    "md_x": ("makine_dairesi", "x"),
    "md_y": ("makine_dairesi", "y"),
}


def etkin_deger(g, anahtar):
    """Kuralla dolan bir çizim alanının çizimde kullanılan değeri ( yoksa None:
    ör. 1:1 askıda kasnak arası, makine dairesizde odanın yeri )."""
    b, a = KURALLI[anahtar]
    v = (g.get(b) or {}).get(a)
    return float(v) if _sayi(v) else None


def _mrl(A):
    """Makine dairesiz mi?  Girdide yoksa hesap programının varsayılanı ( MRL )."""
    return bool(A.get("mk_yok", True))


def uygulanmayan(mk_yok):
    return set(YALNIZ_DAIRELI) if mk_yok else set(YALNIZ_MRL)




def _profil(p):
    """Ray profili "89 x 62 x 15,88"  →  ( b, h )."""
    try:
        b, h = (float(x.strip().replace(",", ".")) for x in str(p).split("x")[:2])
        return b, h
    except (TypeError, ValueError):
        return None


def _en_buyuk(a, kimlik, sembol):
    """Hesap bölümündeki bütün yük durumlarının en büyük |Fx| ya da |Fy|'si."""
    b = next((b for b in a.get("bolumler") or [] if b.get("kimlik") == kimlik), None)
    d = [abs(x["deger"]) for x in (b or {}).get("adimlar") or []
         if str(x.get("formul") or "").startswith(sembol + " =") and _sayi(x.get("deger"))]
    return max(d) if d else None


def kuvvetler(a):
    """Binaya gelen yükler ( N ):  kuyu tabanı 9. bölümden, ray konsollarına
    gelen yatay kuvvetler 7. ve 8. bölümlerin bütün yük durumlarının en
    büyüğünden.  Hesap yapılamadıysa boş ( kutularda yalnız ad yazar )."""
    if not (isinstance(a, dict) and a.get("aktif")):
        return {}
    oz = a.get("ozet") or {}
    k = {s: oz[s] for s in ("FKR", "FAR", "Fkt", "Fat") if _sayi(oz.get(s))}
    for ad, kimlik in (("kabin", "kabin_raylari"), ("agirlik", "agirlik_raylari")):
        for s in ("Fx", "Fy"):
            v = _en_buyuk(a, kimlik, s)
            if v is not None:
                k[f"{s}_{ad}"] = v
    return k


def _deger(A, anahtar):
    """Girilmiş çizim alanı;  boş / girilmemiş ise None."""
    v = A.get(anahtar)
    return None if v is None or (isinstance(v, str) and not v.strip()) else v


def _varsayilan(A, anahtar):
    v = _deger(A, anahtar)
    return ALAN[anahtar][5] if v is None else v


def _bos(v):
    """Kutu boş mu ( girilmemiş, None ya da boşluk )."""
    return v is None or (isinstance(v, str) and not v.strip())


def _dusey_kasnak_arasi(kx, kb_g, Dk, D1, G, ray_duvar, yer, S):
    """Kabin altı 2:1, ağırlık yanda, kasnaklar arası boş:  halat karşı ağırlık
    kasnağına DÜŞEY insin.  Tahrik kasnağının bir teğeti kabinin ağırlık
    tarafındaki halatın üstünde, öbür teğeti ağırlığın ekseninde olmalı:
    halat = ağırlık ekseni − D1 ( ağırlık solda:  + D1 ).  Eski kural ( kabin
    genişliği + 30 ) halatı kabin rayının ara kirişinin 20 mm dibine koyuyor
    ( kasnak 20 mm büyüyünce çizim reddediliyordu ) ve ağırlığa 25 mm eğik
    indiriyordu ( sarım açısı çizimden bulunamıyor, makine dairesinde "halat
    içeride inmeli" hatası ).  Halat kabinin panosuna 20 mm'den yaklaşırsa
    None ( eski kural ).  Ara kirişe ya da konsola çarpıyorsa çizim söyler."""
    y_ = 1.0 if yer == "Sağ" else -1.0
    ex = G - ray_duvar if yer == "Sağ" else ray_duvar
    halat = ex - y_ * D1
    yari = y_ * (halat - kx)                       # kabin ekseninden halata
    if yari < kb_g / 2.0 + S["kabin_pano_yan"] + 20.0:
        return None
    return round(2.0 * yari - Dk, 3)


def cizim_girdisi(A, sonuc=None, proje_adi="", sira=1):
    """Tek asansörün çizim girdisi.

    A:      hesap girdisi ( tamamlanmış — boş alanlar hesabın varsayılanıyla
            dolu ) + çizim alanları ( ALANLAR ) + proje geneli alanlar.
    sonuc:  hesabın o asansör için sonucu ( kuvvetler buradan );  None olabilir.
    Döner:  ( g , hatalar ) — hata varsa g None."""
    ozel = cizim_sabitleri(A)
    S = CS.sabitler(ozel)
    hata = []

    def sayi(anahtar, etiket=None, bos=False, isaretli=False):
        v = A.get(anahtar) if anahtar not in ALAN else _varsayilan(A, anahtar)
        et = etiket or (ALAN[anahtar][1] if anahtar in ALAN else anahtar)
        if v is None and bos:
            return None
        if not _sayi(v):
            hata.append(f"{et}:  girilmemiş." if _bos(v) else f"{et}:  sayı olmalı ( {v!r} ).")
            return None
        if not isaretli and v <= 0:
            hata.append(f"{et}:  sıfırdan büyük olmalı ( {v:g} ).")
            return None
        return float(v)

    def secim(anahtar, etiket=None, secenekler=None):
        """Çizim alanı ya da ( etiket ve seçeneklerle ) hesabın bir seçim alanı."""
        v = _varsayilan(A, anahtar) if anahtar in ALAN else A.get(anahtar)
        et = etiket or ALAN[anahtar][1]
        sec = tuple(secenekler if secenekler is not None else ALAN[anahtar][4])
        if v not in sec:
            liste = " · ".join(str(x) for x in sec)
            hata.append(f"{et}:  seçilmemiş ( {liste} )." if _bos(v)
                        else f"{et}:  {liste} içinden olmalı ( {v!r} ).")
        return v

    mk_yok = _mrl(A)
    #  ── HESAPTAN ──────────────────────────────────────────────────────
    G = sayi("kuyu_genisligi", "Kuyu genişliği")
    kb_g, kb_d = sayi("kabin_genisligi", "Kabin genişliği"), sayi("kabin_derinligi", "Kabin derinliği")
    RK = sayi("ray_kapi_arasi", "Ray – kapı arası ( RK )")
    kapi_g = sayi("kapi_genisligi", "Kat kapısı genişliği")
    Gy, Gx = sayi("agirlik_genisligi", "Karşı ağırlık genişliği ( Gy )"), \
        sayi("agirlik_derinligi", "Karşı ağırlık derinliği ( Gx )")
    kr, ar = _profil(A.get("kabin_ray_profili")), _profil(A.get("agirlik_ray_profili"))
    for p, et, a in ((kr, "Kabin rayı profili", "kabin_ray_profili"),
                     (ar, "Ağırlık rayı profili", "agirlik_ray_profili")):
        if p is None:
            hata.append(f"{et}:  seçilmemiş." if _bos(A.get(a))
                        else f"{et}:  okunamadı ( {A.get(a)!r} ).")
    oran = secim("aski_orani", "Askı oranı", (1, 2))
    #  Hesabın seçimleri çizim modülünün kendi doğrulamasına boş gitmesin:
    #  ileti formdaki adla söylensin ( "agirlik.yeri" değil ).
    from cizim import kabin_ustu as CKU, kuyu_dibi as CKD, makine as CMK
    ag_yeri = secim("agirlik_yeri", "Karşı ağırlık yeri", CG.AGIRLIK_YERLERI)
    sig_ust = secim("siginma_tipi_ust", "Kabin üstü sığınma hacmi tipi", CKU.SIGINMA)
    sig_dip = secim("siginma_tipi_dip", "Kuyu dibi sığınma hacmi tipi", CKD.SIGINMA)
    mk_tip = secim("makine_tipi", "Makine tipi", CMK.TIPLER)
    yan_yatak = secim("yan_yatak", "F  ( yan yatak — makine kirişi ölçüsü )", CMK.NPU)
    halat_n = sayi("halat_adedi", "Askı halatı adedi")
    halat_d = sayi("halat_capi", "Askı halatı çapı")
    D1 = sayi("tahrik_kasnak_capi", "D1 ( tahrik kasnağı çapı )")
    #  Hesabın kaçıklıkları ( ray ekseninden ):  kabin merkezi yc, askı xs · ys
    yc = sayi("kabin_kaciklik", "Kabin merkezinin y kaçıklığı ( yc )", isaretli=True)
    xs = sayi("aski_kaciklik_x", "Askı noktasının x kaçıklığı ( xs )", bos=True, isaretli=True)
    ys = sayi("aski_kaciklik_y", "Askı noktasının y kaçıklığı ( ys )", isaretli=True)
    #  ── ÇİZİMİN KENDİ ALANLARI ───────────────────────────────────────
    KD = sayi("kuyu_derinligi")
    durak = sayi("durak_adedi")
    kacik = sayi("kabin_yana_kaciklik", isaretli=True)
    duvar = sayi("kuyu_duvar_kalinligi")
    montaj = secim("kapi_montaji")
    esik_arasi = sayi("esik_arasi")
    kapi_kacik = sayi("kapi_kaciklik", isaretli=True)
    ag_kacik = sayi("agirlik_eksen_kaciklik", isaretli=True)
    reg_kacik = sayi("regulator_kaciklik", bos=True, isaretli=True)
    reg_yan = secim("regulator_yani")
    if hata:
        return None, hata

    #  ÇİZİMİN MODELLEYEMEDİĞİ KAÇIKLIKLAR.  Çizim kabini raylarının ortasına,
    #  askıyı kabin ekseninin üstüne koyar;  hesap başka bir yer söylüyorsa
    #  pafta hesapla çelişir.
    if abs(yc) > 1e-9:
        hata.append(f"Kabin merkezinin y kaçıklığı ( yc ) {yc:g} mm:  çizim kabini iki rayın "
                    "tam ortasında çizer — kabin raylara göre kaçıksa bu henüz çizilemiyor.")
    if abs(ys) > 1e-9:
        hata.append(f"Askı noktasının y kaçıklığı ( ys ) {ys:g} mm:  çizim askıyı raylar "
                    "arasının ortasında çizer — yana kaçık askı henüz çizilemiyor.")
    if xs is None:
        hata.append("Askı noktasının x kaçıklığı ( xs ) boş — değerini girin.")
    #  MAKARALI KABİN PATENİ ( karar 2 ):  kabin patenlerinin ölçüsü referans
    #  projenin KAYMALI kabin patenlerinden ( paten_yukseklik );  makaralı kabin
    #  pateninin ölçüleri elimizde yok — gelene kadar çizim durur, bölüm 11'in
    #  paten açıklıkları da ölçülmez.  Karşı ağırlık patenleri referans projede
    #  MAKARALIDIR ( çizimin ölçüleri o projeden — sabitler "PATEN" ):  onlar
    #  çizilir.
    if A.get("paten_tipi") == "Makaralı":
        hata.append(f"Kabin paten tipi makaralı:  çizim kabinde yalnız kaymalı patenin ölçüsünü "
                    f"bilir ( yükseklik {S['paten_yukseklik']:g} mm ) — makaralı kabin pateninin "
                    "ölçüleri gelene kadar çizilmez;  'Kaymalı' seçin.")
    if durak < 2 or durak != int(durak):
        hata.append(f"Durak adedi en az 2 olan bir tam sayı olmalı ( {durak:g} ).")
    seyir = sayi("seyir_mesafesi", "Seyir mesafesi")
    kat_yuksekligi = None
    if seyir is not None and durak >= 2 and durak == int(durak):
        kat_yuksekligi, kat_hata = CKA.araliklar(A.get("kat_yukseklikleri"), int(durak), seyir)
        hata += kat_hata
    #  KUYU DİBİ ZİNCİRİ:  kabin en alt durakta dururken kaide + tampon +
    #  çarpma arası + kabinin şase altı kuyu dibine eşittir.  Hesap kaideyi
    #  boşsa buradan alır ( cizimden );  girilmişse zincir kapanmalı.
    KY, baba = sayi("kuyu_dibi", "Kuyu dibi yüksekliği ( KY )"), \
        sayi("kabin_tampon_baba", "Kabin tamponu baba yüksekliği")
    boy, carpma = sayi("kabin_tampon_boyu", "Kabin tamponu uzunluğu"), \
        sayi("kabin_carpma_arasi", "Kabin tamponu – çarpma plakası arası")
    if not hata and abs(baba + boy + carpma + S["sase_alt_derinlik"] - KY) > 0.5:
        dogru = KY - boy - carpma - S["sase_alt_derinlik"]
        hata.append(f"Kuyu dibi zinciri kapanmıyor:  kaide {baba:g} + tampon {boy:g} + çarpma arası "
                    f"{carpma:g} + kabinin şase altı {S['sase_alt_derinlik']:g} = "
                    f"{baba + boy + carpma + S['sase_alt_derinlik']:g}, kuyu dibi {KY:g} — kabin "
                    f"tamponu kaidesine {dogru:g} girin ya da kutuyu boş bırakın ( çizimden gelir ).")
    #  Yükseklikler ( en az 2.000, kapı kabinden yüksek değil ) girdi.dogrula'da:
    #  hesap da o doğrulamada durur ( hesap.hesapla ).
    kabin_h, kapi_h = sayi("kabin_ic_yuksekligi"), sayi("kapi_yuksekligi")
    #  TAMPON ADEDİ:  çizim 1 ya da 2 tampon çizer;  ikisinde aralarındaki
    #  uzaklık girilir.  Eskiden 0 ya da 1,5 sessizce 1 sayılıyor, 2'de istenen
    #  "tamponlar arası"nın formda kutusu yoktu ( kullanıcı kararı 4 Eki ).
    tampon = {}
    for tur, et in (("kabin", "Kabin"), ("agirlik", "Ağırlık")):
        n = sayi(f"{tur}_tampon_adedi", f"{et} tamponu adedi")
        ara = sayi(f"{tur}_tampon_arasi", bos=True)
        if n is not None and n not in (1, 2):
            hata.append(f"{et} tamponu adedi {n:g}:  çizim 1 ya da 2 tampon çizer.")
        elif n == 2 and ara is None:
            hata.append(f"{ALAN[f'{tur}_tampon_arasi'][1]}:  iki tamponda girilmeli.")
        tampon[tur] = (int(n) if n in (1, 2) else None, ara)
    if hata:
        return None, hata

    #  ── KAPI BÖLGESİ ─────────────────────────────────────────────────
    #  Kapı hattı ( kat eşiğinin kabine bakan kenarı ):  kuyu içine montajda
    #  kasa + eşik, duvar boşluğunda yalnız eşik kuyuya taşar.
    #  Eşiklerin derinliği kapı tipinden ( 3 kanatlı teleskopikte 135 — girdi.esik_derinligi ).
    kapi_tip = A.get("kat_kapisi_tipi")
    hat = CG.kapi_bolgesi({"kapi": {"montaj": montaj, "tip": kapi_tip}, "kabin": {"on_pay": 0}}, S)["hat"]
    on_pay = hat + esik_arasi + CG.esik_derinligi(S, kapi_tip, kabin=True)
    kapi_arasi = hat + RK
    kx = G / 2.0 + kacik

    #  ── ASKI ─────────────────────────────────────────────────────────
    #  Askı noktasının derinlikteki yeri hesabın xs'inden:  çizimde askı
    #  merkezi kabin ( pano dahil ) merkezine göre kaydırılarak verilir.
    aski_y = kapi_arasi + xs
    kabin_merkez = on_pay + (kb_d + S["kabin_pano_arka"]) / 2.0
    aralik = sayi("kabin_kasnak_arasi", bos=True)
    D1_, dusey_ara, eski_kural = D1 or 0.0, None, None
    if oran == 1:
        #  1:1:  tek bağlantı, kabin şasesinin üst kirişinin ortasında
        aski = {"duzen": "Doğrudan", "nokta_kaciklik": aski_y - kabin_merkez}
    else:
        duzen, Dk = secim("aski_duzeni"), sayi("kabin_kasnak_capi")
        eski_kural = kb_g + 30.0 if duzen == "Kabin altı" else kb_g - 2 * 200.0 - (Dk or 0)
        if not aralik and duzen == "Kabin altı" and ag_yeri in ("Sağ", "Sol") and Dk:
            ray_duvar = sayi("agirlik_ray_duvar", bos=True) or Gx / 2.0 + 50.0
            dusey_ara = _dusey_kasnak_arasi(kx, kb_g, Dk, D1_, G, ray_duvar, ag_yeri, S)
        aski = {"duzen": duzen, "kasnak_capi": Dk,
                "kasnak_arasi": aralik or dusey_ara or eski_kural,
                "kasnak_kaciklik": aski_y - kabin_merkez}
    aski.update(halat_adedi=halat_n, halat_capi=halat_d)

    #  Ağırlık arkadayken "karşı ağırlığın karşısı" bir yan söylemez:  önce sağ,
    #  gergi orada sığmıyorsa sol ( _regulator_yeri ).
    reg_yan_serbest = reg_yan == "Karşı ağırlığın karşısı" and ag_yeri == "Arka"
    if reg_yan == "Karşı ağırlığın karşısı":
        reg_yan = "Sol" if ag_yeri == "Sağ" else "Sağ"
    #  Regülatör ile kabin halat bağlantısı aynı rayın başındadır:  boşsa
    #  regülatör askı halatlarının çizgisinin öbür yanına ( referans proje:  halatlar
    #  ray ekseninin 250 önünde, regülatör 280 arkasında ).
    reg_bos = reg_kacik is None
    if reg_bos:
        reg_kacik = -280.0 if xs > 0 else 280.0
    agirlik_tampon_boyu = sayi("agirlik_tampon_boyu", bos=True) or sayi("kabin_tampon_boyu",
                                                                          "Kabin tamponu uzunluğu")
    Da = sayi("agirlik_kasnak_capi") if oran == 2 else None
    if hata:
        return None, hata

    g = {
        #  Hesabın Sabitler sekmesindeki kabin ölçüleri:  bütün çizimler okur
        "_cizim_sabitleri": ozel,
        "proje": {"ad": proje_adi or "", "asansor": str(A.get("asansor_adi") or "").strip()
                  or f"ASANSÖR {sira}", "olcek": 20},
        #  Duvarlar ayrı ayrı ( boşsa ortak kalınlık );  kuyu dibinin ve tavanın
        #  döşemesi ortak kalınlıktadır ( eskiden ön duvarınkini kullanıyordu ).
        "kuyu": {"genislik": G, "derinlik": KD, "doseme": duvar,
                 **{f"duvar_{y}": (sayi(f"kuyu_duvar_{y}", bos=True) or duvar) if duvar else None
                    for y in ("on", "arka", "sol", "sag")}},
        "kabin": {"genislik": kb_g, "derinlik": kb_d, "kaciklik_y": kacik, "on_pay": on_pay},
        "kapi": {"genislik": kapi_g, "sol_pay": kx + kapi_kacik - kapi_g / 2.0,
                 "yukseklik": kapi_h, "tip": A.get("kat_kapisi_tipi"),
                 "montaj": montaj},
        "kabin_ray": {"arasi": sayi("kabin_ray_arasi", bos=True) or kb_g + 200.0,
                      "kapi_arasi": kapi_arasi, "b": kr[0], "h": kr[1]},
        "agirlik": {"yeri": ag_yeri, "genislik": Gy, "derinlik": Gx,
                    "ray_arasi": sayi("agirlik_ray_arasi", bos=True) or Gy + _TS.AGIRLIK_PATEN_PAYI,
                    "ray_duvar": sayi("agirlik_ray_duvar", bos=True) or Gx / 2.0 + 50.0,
                    "eksen_kaciklik": ag_kacik, "b": ar[0], "h": ar[1], "kasnak_capi": Da},
        "aski": aski,
        "kabin_ustu": {"siginma_tipi": sig_ust},
        "kuyu_dibi": {"derinlik": sayi("kuyu_dibi", "Kuyu dibi yüksekliği ( KY )"),
                      "siginma_tipi": sig_dip,
                      "kabin_tampon_adedi": tampon["kabin"][0],
                      "kabin_tampon_arasi": tampon["kabin"][1],
                      "agirlik_tampon_adedi": tampon["agirlik"][0],
                      "agirlik_tampon_arasi": tampon["agirlik"][1],
                      "regulator_yan": reg_yan, "regulator_kaciklik": reg_kacik,
                      "regulator_halat_capi": sayi("reg_halat_capi", "Regülatör halatı çapı"),
                      "regulator_kasnak_capi": sayi("reg_kasnak_capi", "Regülatör kasnak çapı"),
                      #  Hesap yapılamadıysa yok ( kutularda yalnız ad yazar )
                      "kuvvetler": kuvvetler(sonuc) or None},
        "dusey": {"kabin_ic_yukseklik": kabin_h,
                  "kabin_paten_arasi": sayi("kabin_paten_arasi", "Kabin paten arası"),
                  "agirlik_paten_arasi": sayi("agirlik_paten_arasi", "Ağırlık paten arası"),
                  "son_kat": sayi("son_kat_yuksekligi", "Son kat yüksekliği"),
                  "beyan_hizi": sayi("beyan_hizi", "Beyan hızı"),
                  "durak_adedi": int(durak),
                  "kat_yuksekligi": kat_yuksekligi,
                  "kabin_tampon_baba": sayi("kabin_tampon_baba", "Kabin tamponu baba yüksekliği"),
                  "kabin_tampon_boyu": sayi("kabin_tampon_boyu", "Kabin tamponu uzunluğu"),
                  "kabin_carpma_arasi": sayi("kabin_carpma_arasi", "Kabin tamponu – çarpma plakası arası"),
                  "kabin_tampon_ezilme": sayi("kabin_tampon_ezilme", "Kabin tamponu ezilme miktarı"),
                  "agirlik_tampon_baba": sayi("agirlik_tampon_baba", "Ağırlık tamponu baba yüksekliği"),
                  "agirlik_tampon_boyu": agirlik_tampon_boyu,
                  "agirlik_carpma_arasi": sayi("agirlik_carpma_arasi",
                                               "Ağırlık tamponu – çarpma plakası arası"),
                  "agirlik_tampon_ezilme": sayi("agirlik_tampon_ezilme", "Ağırlık tamponu ezilme miktarı"),
                  "kabin_konsol_arasi": sayi("kabin_konsol_arasi", "Kabin rayı konsollar arası"),
                  "agirlik_konsol_arasi": sayi("agirlik_konsol_arasi", "Ağırlık rayı konsollar arası")},
        "makine": {"tahrik_kasnak_capi": D1, "yeri": "Kuyu üstü" if mk_yok else "Makine dairesi",
                   "tip": mk_tip, "yan_yatak": yan_yatak,
                   "saptirma_kasnak_capi": sayi("makine_saptirma_capi")},
        "kuyu_ustu": {"acil_pano_yan": secim("acil_pano_yani")},
    }
    if not mk_yok:
        genislik, derinlik = sayi("mk_genislik", "Makine dairesi genişliği"), \
            sayi("mk_uzunluk", "Makine dairesi uzunluğu")
        md_duvar = sayi("md_duvar")
        mx, my = sayi("md_x", bos=True, isaretli=True), sayi("md_y", bos=True, isaretli=True)
        if genislik is not None:
            g["makine_dairesi"] = {
                "genislik": genislik, "derinlik": derinlik, "duvar": md_duvar,
                #  Boşsa oda kuyunun dış genişliğine ortalı, önü kuyunun ön
                #  duvarının dış yüzüyle hizalı ( çizim örneğinin düzeni ).
                "x": mx if mx is not None else -duvar - (genislik - (G + 2 * duvar)) / 2.0,
                "y": my if my is not None else -duvar,
                "kapi_duvar": secim("md_kapi_duvar"), "kapi_konum": sayi("md_kapi_konum"),
                "kapi_genislik": sayi("md_kapi_genislik"), "pano_duvar": secim("md_pano_duvar"),
                "yukseklik": sayi("md_yukseklik"), "kapi_yukseklik": sayi("md_kapi_yukseklik"),
                "tabliye_yuksekligi": sayi("tabliye_yuksekligi", "Tabliye beton yüksekliği"),
                "sase_yuksekligi": sayi("sase_yuksekligi", "Şase yüksekliği"),
                "dikine_kiris": secim("dikine_kiris", "E  ( dikine kiriş ölçüsü )", CMK.NPU)}
    if hata:
        return None, hata
    if dusey_ara:
        _kasnak_arasi_sec(g, eski_kural)
    from cizim import arka_aski as CAA
    if CAA.arkada_iki_bir(g):
        #  Arkadaki ağırlıkla 2:1:  ağırlık – duvar ölçüsü boşsa ağırlık kabine
        #  göre konur ( tahrik kasnağının kabin inişi kabin tavanının arka
        #  kenarında );  kabin kasnaklarının aralığı çapraz geometriden
        #  ( girilmişse uyuşmazlık denetimi karşılaştırır ).
        if _bos(A.get("agirlik_ray_duvar")) and _sayi(D1):
            g["agirlik"]["ray_duvar"] = round(CAA.agirlik_ray_duvari(g, S), 1)
        A_ = CAA.geometri(g, S)
        if "aralik" in A_:
            g["aski"]["kasnak_arasi"] = round(A_["aralik"], 1)
    if reg_bos or reg_yan_serbest:
        _regulator_yeri(g, kaciklik_serbest=reg_bos, yan_serbest=reg_yan_serbest)
    return g, []


def _kasnak_arasi_sec(g, eski_kural):
    """Düşey iniş için bulunan kasnaklar arası halatı kuyudaki bir parçaya
    ( kabin rayının ara kirişi, konsol ) çarptırıyorsa eski kural:  kuyu
    kabinden geniş, ağırlık duvarla birlikte uzaklaşmışsa halat kabine yakın
    kalır, ağırlığa eğik iner ( sapma ölçüsü;  sarım açısı girilmeli )."""
    from cizim import kabin_ustu as CKUS
    try:
        carpar = any(h.startswith("Halat (") for h in CKUS.yerlesim(g)["hata"])
    except Exception:                                      # noqa: BLE001
        carpar = True
    if carpar:
        g["aski"]["kasnak_arasi"] = eski_kural


def _regulator_yeri(g, kaciklik_serbest=True, yan_serbest=False):
    """Regülatör kaçıklığı boşsa:  varsayılan yer ( 280, askı halatlarının
    öbür yanında ) gergiyi bir raya ya da tampona çarptırıyorsa ( sığ kuyuda
    kol döner, ağırlık raya iner — 320 kg kabinlerde ) çarpmayan en yakın yer
    seçilir:  öbür yan, sonra 200 · 360 · 440.  yan_serbest ( ağırlık arkada,
    "karşı ağırlığın karşısı" ):  ilk ray çarpıyorsa öbür kabin rayı da denenir
    ( 12495-18:  sağ ray duvara 50 mm, eski 160'lık gergi ağırlığı duvara 7,5
    kalıyordu;  82'lik ağırlıkla sağ rayın önüne, −280'e iner ).
    Hiçbiri çarpmaktan kurtulmuyorsa varsayılan kalır ( çizim hatayı söyler )."""
    from cizim import kuyu_dibi as CKD
    from cizim import kuyu_ustu as CKT
    from cizim import makine_dairesi as CMD
    kd = g["kuyu_dibi"]
    ilk, ilk_yan = kd["regulator_kaciklik"], kd["regulator_yan"]

    def carpisma(c, yan=ilk_yan):
        #  Gergi kuyu dibinde, regülatörün kendisi kuyu tepesinde ( ya da
        #  makine dairesinde ):  ikisi de çarpmamalı.
        #  Kuyu dibinde çarpıyorsa tepeye bakılmaz ( makine dairesinin bakım
        #  alanını aramak pahalı — ölçü çözümlemesi her çizimi yüzlerce kez kurar ).
        kd["regulator_kaciklik"], kd["regulator_yan"] = c, yan
        try:
            h = [x for x in CKD.yerlesim(g)["hata"] if "egülatör" in x]
            if h:
                return h
            h = (CKT.yerlesim(g) if g["makine"]["yeri"] == "Kuyu üstü"
                 else CMD.yerlesim(g)).get("hata") or []
        except Exception:                                  # noqa: BLE001
            return ["?"]
        return [x for x in h if "egülatör" in x]

    isaret = 1 if ilk > 0 else -1
    kaciklar = [ilk] + ([-ilk, 200.0 * isaret, -200.0 * isaret, 360.0 * isaret,
                         -360.0 * isaret, 440.0 * isaret, -440.0 * isaret]
                        if kaciklik_serbest else [])
    yanlar = [ilk_yan] + ([("Sol" if ilk_yan == "Sağ" else "Sağ")] if yan_serbest else [])
    for yan in yanlar:
        for c in kaciklar:
            if not carpisma(c, yan):
                return
    kd["regulator_kaciklik"], kd["regulator_yan"] = ilk, ilk_yan


#  HESABIN ÇİZİMDEN TÜRETİLEN GİRDİLERİ:  hesapta BOŞ bırakılırsa değeri
#  çizimin geometrisinden gelir ve hesaba o değer girer ( ekranda kutunun
#  içinde gri yazar ).  Girilmişse girilen kullanılır ve çizimle
#  karşılaştırılır ( tutarlilik ).
#  Kuralları tasarım şemasındadır ( Alan.cizimden ).
CIZIMDEN = _TG.cizimden()


def kasnaklar(g):
    """Çizilen saptırma kasnaklarının çapları ( tahrik kasnağı hariç ):  2:1
    askıda iki kabin kasnağı ve karşı ağırlık kasnağı, makine dairesinde
    çizildiyse saptırma kasnağı."""
    a, c = g["aski"], []
    if a["duzen"] != "Doğrudan":
        c += [a["kasnak_capi"], a["kasnak_capi"], g["agirlik"]["kasnak_capi"]]
    if g["makine"]["yeri"] == "Makine dairesi":
        from cizim import makine_dairesi as CMD
        try:
            sap = CMD.yerlesim(g).get("saptirma")
        except Exception:                              # noqa: BLE001 — çizim zaten reddeder
            sap = None
        if sap:
            c.append(sap["D"])
    return c


def _aski_x(A):
    """Askının ray ekseninden kaçıklığı ( xs ).
      2:1   ağırlık yandayken:  tahrik kasnağının iki halat inişi aynı düşey
            düzlemdedir;  kabin kasnaklarının çizgisi karşı ağırlık kasnağının
            kabine yakın teğetindedir ( referans proje:  kasnaklar ağırlık ekseninin
            200, ray ekseninin 250 önünde ).
      1:1   halatlar kabin şasesinin üst kirişinin ortasındaki bağlantıda biter;
            kiriş ray ekseni üstündedir:  0 ( LiftDesigner 12744-3 ).
      2:1   ağırlık arkadayken ( kabin üstünde çapraz kasnaklar — arka_aski ):
            iki düşey halatın ortası kabinin ( pano dahil ) derinlik ortasıdır
            ( kullanıcı kararı:  askı kabin merkezinde ).
    Ölçüsü eksikse None.

    YALNIZ KENDİ ÖLÇÜLERİNDEN hesaplanır:  başka bir girdideki hata ( kuyu
    dibi zinciri, kuyu derinliği … ) türetmeyi durdurmaz — o hata kendi
    iletisiyle söylenir, "xs boş" diye değil."""
    oran = A.get("aski_orani")
    if oran == 1:
        return 0.0
    if oran == 2 and A.get("agirlik_yeri") == "Arka" \
            and _varsayilan(A, "kapi_montaji") in CG.KAPI_MONTAJLARI:
        v = [A.get("ray_kapi_arasi"), A.get("kabin_derinligi"), _varsayilan(A, "esik_arasi")]
        if not all(_sayi(x) for x in v):
            return None
        RK, kb_d, esik = v
        S = CS.sabitler(cizim_sabitleri(A))
        tip = A.get("kat_kapisi_tipi")
        hat = CG.kapi_bolgesi({"kapi": {"montaj": _varsayilan(A, "kapi_montaji"), "tip": tip},
                               "kabin": {"on_pay": 0}}, S)["hat"]
        return (hat + esik + CG.esik_derinligi(S, tip, kabin=True)
                + (kb_d + S["kabin_pano_arka"]) / 2.0 - (hat + RK))
    if (oran != 2 or A.get("agirlik_yeri") not in ("Sağ", "Sol")
            or _varsayilan(A, "kapi_montaji") not in CG.KAPI_MONTAJLARI):
        return None
    v = [A.get("ray_kapi_arasi"), A.get("kabin_derinligi")] + [
        _varsayilan(A, k) for k in ("esik_arasi", "agirlik_eksen_kaciklik")]
    Da = _varsayilan(A, "agirlik_kasnak_capi")
    if not all(_sayi(x) for x in v + [Da]):
        return None
    RK, kb_d, esik, ag_kacik = v
    S = CS.sabitler(cizim_sabitleri(A))
    tip = A.get("kat_kapisi_tipi")
    hat = CG.kapi_bolgesi({"kapi": {"montaj": _varsayilan(A, "kapi_montaji"), "tip": tip},
                           "kabin": {"on_pay": 0}}, S)["hat"]
    ray_y = hat + RK
    kabin = hat + esik + CG.esik_derinligi(S, tip, kabin=True) + (kb_d + S["kabin_pano_arka"]) / 2.0
    ag_y = ray_y + ag_kacik
    return min((ag_y - Da / 2.0, ag_y + Da / 2.0), key=lambda t: abs(t - kabin)) - ray_y


def _saptirma(g):
    """Makine dairesindeki saptırma kasnağı ( yoksa, makine dairesizde ya da
    çizim kurulamıyorsa None ).  Gerekip gerekmediği ve çapı halat aralığı ile
    tahrik kasnağından çıkar — odanın öbür hatalarından bağımsız."""
    if g is None or g["makine"]["yeri"] != "Makine dairesi":
        return None
    from cizim import makine_dairesi as CMD
    try:
        return CMD.yerlesim(g).get("saptirma")
    except Exception:                                  # noqa: BLE001 — çizim kendi hatasını söyler
        return None


def _kasnak_caplari(A, sap):
    """Hesabın D2 / Ds'si için çizilecek saptırma kasnakları — girdilerden
    doğrudan:  2:1 askıda iki kabin kasnağı ve karşı ağırlık kasnağı;  makine
    dairesinde çiziliyorsa saptırma kasnağı ( sap )."""
    c = []
    if A.get("aski_orani") == 2:
        Dk, Da = _varsayilan(A, "kabin_kasnak_capi"), _varsayilan(A, "agirlik_kasnak_capi")
        if not (_sayi(Dk) and _sayi(Da) and Dk > 0 and Da > 0):
            return None
        c = [float(Dk), float(Dk), float(Da)]
    if sap:
        c.append(sap["D"])
    return c


def _cift_sarim(A):
    """Kanal çift sarımlı mı:  halat tahrik kasnağının üzerinden iki kez geçer."""
    return "çift sarım" in str(A.get("kanal_sekli") or "").lower()




def cizimden(A):
    """Boş bırakılmış ( None ) hesap girdilerinin çizimden gelen değerleri.
    Sıra:  kaide ve askı kaçıklığı önce ( makine dairesindeki saptırma
    kasnağının yeri onlarla kurulan çizime bağlı ), sarılma açısı ve
    kasnaklar sonra."""
    d, B = {}, dict(A)
    bos = [k for k in CIZIMDEN if k in A and A[k] is None]
    if not bos:
        return d
    if "kabin_tampon_baba" in bos:
        v = [B.get(k) for k in ("kuyu_dibi", "kabin_tampon_boyu", "kabin_carpma_arasi")]
        if all(_sayi(x) for x in v):
            d["kabin_tampon_baba"] = v[0] - v[1] - v[2] - \
                CS.sabitler(cizim_sabitleri(B))["sase_alt_derinlik"]
    if "aski_kaciklik_x" in bos:
        #  Çizimden bulunamıyorsa ( arkadaki karşı ağırlık ) hesabın eski
        #  varsayılanı:  askı ray ekseninde ( 0 ).
        xs = _aski_x(B)
        d["aski_kaciklik_x"] = 0.0 if xs is None else xs
    B.update(d)
    kasnak = {"saptirma_kasnak_capi", "saptirma_kasnak_min_capi"} & set(bos)
    if kasnak or "sarilma_acisi" in bos:
        gc, _hata = cizim_girdisi(B)
    if "sarilma_acisi" in bos and not _cift_sarim(B):
        #  Çift sarımı çizim çizmez ( tek geçiş );  açısı girilmeli.
        alfa = sarim_acisi(gc) if gc is not None else None
        if alfa is not None:
            d["sarilma_acisi"] = alfa
    if kasnak:
        c = _kasnak_caplari(B, _saptirma(gc))
        if c == [] and _sayi(B.get("tahrik_kasnak_capi")):
            #  Saptırma kasnağı yok ( 1:1, makine dairesinde saptırmasız ):  D2 ve
            #  Ds hesapta etkisizdir — tahrik kasnağının çapı verilir ( Kp = 1,
            #  D/d denetimi tahrik kasnağınınkiyle aynı ).
            c = [float(B["tahrik_kasnak_capi"])]
        if c:
            if "saptirma_kasnak_capi" in bos:
                d["saptirma_kasnak_capi"] = round(sum(c) / len(c), 1)
            #  Ds boşsa D2 girilmiş olsa da çizimden:  hesabın kendi kuralı ( Ds
            #  boşsa D2 ) en küçük kasnağı ortalamayla ölçerdi — 2:1'de 240'lık
            #  kabin kasnaklarının D/d denetimi 294 ile yapılırdı.  Girilen D2
            #  çizimin en küçük kasnağından da küçükse türetilmez:  hesap Ds'yi
            #  D2'ye düşürür ( güvenli yön ), çizim D2'nin uyuşmadığını söyler —
            #  yoksa hesap dokunulmamış Ds'yi "ters girilmiş" diye reddederdi.
            D2 = d.get("saptirma_kasnak_capi", B.get("saptirma_kasnak_capi"))
            if "saptirma_kasnak_min_capi" in bos and not (_sayi(D2) and min(c) > D2):
                d["saptirma_kasnak_min_capi"] = min(c)
    return d


def sarim_acisi(g):
    """Çizimdeki halatın tahrik kasnağını sardığı açı ( ° ) — yalnız çizim onu
    TEK BİR SAYI olarak biliyorsa:
      · iki iniş düşey:  180°
      · makine dairesinde saptırma kasnağı halatın yönünü sabitler:  tahrik
        kasnağı ile saptırma kasnağının ortak teğetlerinden
    Makine dairesizde ağırlık tarafındaki iniş kasnağın düzleminde eğikse
    ( HALAT SAPMASI ) açı ağırlığın konumuyla değişir ( ağırlık tepedeyken
    halat kısa, sapma birkaç derece ):  None — hesabın tek açısı buradan
    seçilemez ( çekiş ve kayma denetimleri açıya ters yönde bağlıdır ).
    Çizim kurulamıyorsa da None."""
    try:
        if g["makine"]["yeri"] == "Kuyu üstü":
            from cizim import kuyu_ustu as CKU
            Y = CKU.yerlesim(g)
            #  Kurma ile denetim ayrı:  kuyu üstündeki bir çakışma açıyı
            #  değiştirmez;  yalnız geometri kurulamadıysa açı yok.
            if "sapma" not in Y:
                return None
            return 180.0 if abs(Y["sapma"][0]) <= 0.5 else None
        from cizim import makine_dairesi as CMD
        Y = CMD.yerlesim(g)
        if "saptirma" not in Y or Y.get("halat_kurulamadi"):
            return None
        sp = Y.get("saptirma")
        if not sp:
            return 180.0
        return round(sp["sarim"], 1) if "sarim" in sp else None
    except Exception:                                  # noqa: BLE001 — çizim zaten reddetti
        return None


def _uyusmazliklar(g, A):
    """[ ( ileti , düzeltme ) ] — hesabın girdisi ile çizimin geometrisinin
    ayrı söylediği büyüklükler.  Düzeltme { girdi : çizimdeki değer } ( ya
    da çizilemeyen bir durumda None ):  ölçüden değiştirmede bağlı büyüklükler
    birlikte güncellenir ( kuyu genişliği değişince L = DBGW … ).  İleti ile
    düzeltme aynı yerde kurulur:  biri değişip öteki eskimesin."""
    liste = []
    #  HALAT SARILMA AÇISI:  tahrik kasnağı ile karşı ağırlığa inen halatın
    #  geometrisinden çıkar;  hesabın tahrik ( kayma ) kontrolüne girer.  Boşsa
    #  çizimden gelir ( cizimden );  girilmişse çizimle aynı olmalı.
    #  ÇİFT SARIM:  çizim halatı kasnağın üzerinden bir kez geçirir;  paftadaki
    #  sarım açısı hesabınkiyle çelişirdi.  Kuyunun geometrisi ( bölüm 11 ) sarım
    #  sayısından bağımsızdır — yalnız çizim durur.
    alfa, sarim = A.get("sarilma_acisi"), sarim_acisi(g)
    if _cift_sarim(A):
        liste.append(("Çift sarımlı kanal:  çizim halatı tahrik kasnağının üzerinden bir kez "
                      "geçirir — çift sarım ( ikinci kasnak, iki geçiş ) henüz çizilemiyor.", None))
        sarim = None
    if sarim is not None and _sayi(alfa) and abs(alfa - sarim) >= 0.5:
        liste.append((f"Halat sarılma açısı:  çizimdeki halat geometrisi α = {sarim:.1f}° veriyor, "
                      f"hesapta {alfa:g}° — α'yı boş bırakın ( çizimden gelir ).",
                      {"sarilma_acisi": round(sarim, 1)}))
    #  SAPTIRMA KASNAKLARI:  hesabın D2'si çizilen kasnakların ortalaması,
    #  Ds'si en küçüğü ( TS EN 81-50 m.5.12:  Dp ortalama çap ).
    cap = kasnaklar(g)
    if cap:
        ort, en_kucuk = sum(cap) / len(cap), min(cap)
        D2, Ds = A.get("saptirma_kasnak_capi"), A.get("saptirma_kasnak_min_capi")
        Ds = Ds if _sayi(Ds) else D2
        yazi = " · ".join(f"{c:g}" for c in cap)
        if _sayi(D2) and abs(D2 - ort) >= 1.0:
            liste.append((f"Saptırma kasnakları:  çizimdeki kasnaklar ( {yazi} ) ortalaması "
                          f"{ort:.1f} mm, hesaptaki D2 {D2:g} — D2'yi boş bırakın ( çizimden gelir ) "
                          "ya da kasnak çaplarını düzeltin.",
                          {"saptirma_kasnak_capi": round(ort, 1)}))
        if _sayi(Ds) and abs(Ds - en_kucuk) >= 0.5:
            liste.append((f"Saptırma kasnakları:  çizimdeki en küçük kasnak {en_kucuk:g} mm, hesaptaki "
                          f"Ds {Ds:g} — Ds'yi boş bırakın ( çizimden gelir ).",
                          {"saptirma_kasnak_min_capi": en_kucuk}))
    #  MAKİNE KİRİŞİ BİNA YAPISINA ( karar 3 ):  makine dairesizde çizim
    #  kirişleri karşı ağırlık raylarına oturtur;  duvardan duvara oturan kiriş
    #  ( kuyu genişliğince platform ) henüz çizilmiyor — çizim durur, hesabın
    #  kiriş açıklığı çizimden gelmez ( bölüm 2 HESAP EKSİK ).  Yan yatak boyu
    #  girdi değildir:  raylara oturan kirişte DBGW, kaidede kaidenin açıklığı.
    arka = g["agirlik"]["yeri"] == "Arka"
    if g["makine"]["yeri"] == "Kuyu üstü" and A.get("makine_raya_biniyor") == "Bina yapısına" \
            and not arka:
        liste.append(("Makine kirişleri bina yapısına ( duvardan duvara ) oturuyor:  bu kiriş henüz "
                      "çizilmiyor ( karar 3 ) — çizim kirişleri karşı ağırlık raylarına oturtur; "
                      "'Makine yükünün yolu' için 'Kılavuz raylara' seçin.", None))
    #  ARKADAKİ AĞIRLIKTA makine dairesizde makine duvardan duvara iki kirişe
    #  oturur ( kullanıcı kararı — 12495-18 ):  yük bina yapısına gider.
    if g["makine"]["yeri"] == "Kuyu üstü" and arka and A.get("makine_raya_biniyor") == "Kılavuz raylara":
        liste.append(("Karşı ağırlık arkadayken makine dairesizde makine duvardan duvara iki kirişe "
                      "oturur ( kuyu derinliğince ) — yük bina yapısına gider:  'Makine yükünün "
                      "yolu' için 'Bina yapısına' seçin.", {"makine_raya_biniyor": "Bina yapısına"}))
    #  Arkadaki ağırlıkla 2:1:  kabin kasnaklarının aralığı çapraz geometriden
    from cizim import arka_aski as CAA
    if CAA.arkada_iki_bir(g) and _sayi(A.get("kabin_kasnak_arasi")) \
            and abs(A["kabin_kasnak_arasi"] - g["aski"]["kasnak_arasi"]) >= 1.0:
        liste.append((f"Arkadaki ağırlıkla 2:1:  kabin kasnaklarının aralığı çapraz düzlemden "
                      f"{g['aski']['kasnak_arasi']:g} mm ( askı kabin merkezinde ), girilen "
                      f"{A['kabin_kasnak_arasi']:g} — kutuyu boş bırakın.",
                      {"kabin_kasnak_arasi": g["aski"]["kasnak_arasi"]}))
    return liste


def tutarlilik(g, A):
    """Hesabın girdisi ile çizimin geometrisi aynı şeyi söylüyor mu?  Aynı
    fiziksel büyüklük iki yerde modelleniyorsa ikisi eşit olmalıdır;
    uyuşmazlık metin listesi olarak döner ( doğru değeriyle ).  g geçerli
    olmalı ( çizimlerin doğrulamasından geçmiş )."""
    return [m for m, _d in _uyusmazliklar(g, A)]


def tutarlilik_duzeltmeleri(g, A):
    """Uyuşmazlıkları gideren girdi değerleri ( { girdi : değer } )."""
    d = {}
    for _m, duz in _uyusmazliklar(g, A):
        d.update(duz or {})
    return d

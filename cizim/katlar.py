"""KATLAR — formdaki kat aralıkları ve kotla girişin okunuşu.

ARALIKLAR ( araliklar ):  isteğe bağlı kat yükseklikleri ( mm );  toplamı seyirle
aynı olmalı.

KOT YAZIMI ( kot_oku · kotlari_oku ):  durak kotları, kuyu dibi ve kuyu tavanı,
makine dairesi zemini mimari paftadaki gibi metreyle ve işaretli yazılır:
"−8,80", "+62,20", "±0,00".
  -  Nokta da virgül de ondalıktır ( paftada "+60.80" noktalı ).  Binlik ayracı
     yoktur:  kot metredir.  Tek belirsiz yazım noktalı üç ondalıktır — "1.200"
     Türkçede bin iki yüz de okunur ( programın bütün sayılarındaki kural );
     virgülle yazılır.
  -  mm'ye kadar okunur;  daha ince ondalık reddedilir, sondaki sıfırlar geçer
     ( ön yüz üç ondalıklı sayının sonuna sıfır ekler — denetim.ts kutuyaYaz ).
  -  Eksi "-" ya da paftadan kopyalanan "−" ( U+2212, "–" de );  "±" yalnız sıfırda.
  -  Değer mm'de TAM SAYI döner:  kottan türeyen ölçüler ( seyir, KY ) kayan
     nokta gürültüsü taşımasın ( float'ta −7,00 − ( −8,80 ) = 1,8000000000000007 ).
Durak kotları en alt duraktan başlayarak, noktalı virgülle ya da satır satır
yazılır;  kesin artan olmalıdır.  Kipi belirleyen de bu alandır ( kot_kipi ).
"""

import math

from temel import sayi_mi
from cizim import izli
from cizim.dusey import ESIK_ARASI
from tasarim import alanlar
import re

#  Kot kutusunun sınırı:  metre alanlarının fiziksel tavanı ( mutlak kotla
#  yazan pafta da içinde kalır — Türkiye'nin en yüksek ili ~ 2.000 m )
KOT_AZAMI_MM = alanlar.BIRIM_AZAMI["m"] * 1000
DURAK_AZAMI = alanlar.AZAMI["durak_adedi"]
#  Durak kotları metninin en çok boyu:  100 durak × 12 karakter ( "+123,456; " )
#  yeter;  daha uzunu parçalanmadan reddedilir ( sunucunun belleği — 17 Eki ).
KOT_METNI_AZAMI = DURAK_AZAMI * 40
_KOT = re.compile(r"(?P<isaret>[+\-−–±]?)(?P<tam>\d+)(?:(?P<ayrac>[.,])(?P<ondalik>\d+))?")
_ORNEK = "−8,80 · +62,20 · ±0,00"


def kot_metni(mm):
    """İletideki kot:  "±0,00", "+3,20", "-8,805" ( mm'si olan üç ondalıkla )."""
    if mm == 0:
        return "±0,00"
    return (f"{mm / 1000.0:+.3f}" if mm % 10 else f"{mm / 1000.0:+.2f}").replace(".", ",")


def kot_oku(ham):
    """Bir kotun yazımı → ( mm tam sayı , None ) ya da ( None , ileti ).  İletinin
    başına alanın adı konur ( kapı ):  "Kuyu dibi kotu:  okunamadı ( … )"."""
    if isinstance(ham, bool) or not isinstance(ham, (int, float, str)):
        return None, f"kot olmalı ( {str(ham)[:40]!r} girildi ) — {_ORNEK}."
    if isinstance(ham, str):
        s = re.sub(r"\s", "", ham)
        m = _KOT.fullmatch(s)
        if not m:
            return None, f"okunamadı ( {ham.strip()[:40]!r} girildi ) — kot metreyle yazılır:  {_ORNEK}."
        tam, ondalik = m["tam"], m["ondalik"] or ""
        if m["ayrac"] == "." and len(ondalik) == 3 and re.fullmatch(r"[1-9]\d{0,2}", tam):
            return None, (
                f"belirsiz yazım ( {s!r} ):  nokta binlik ayracı da okunur — ondalığı virgülle "
                f"yazın ( {s.replace('.', ',')} )."
            )
        if ondalik[3:].strip("0"):
            return None, f"mm'den ince ( {s!r} girildi ) — kot en çok üç ondalıkla ( mm ) yazılır."
        mm = int(tam) * 1000 + int(ondalik[:3].ljust(3, "0"))
        if m["isaret"] == "±" and mm:
            return None, f"'±' yalnız sıfırda yazılır ( {s!r} girildi ) — {_ORNEK}."
        if m["isaret"] in ("-", "−", "–"):
            mm = -mm
    else:
        if not math.isfinite(ham):
            return None, f"kot olmalı ( {ham!r} girildi ) — {_ORNEK}."
        r = round(ham * 1000.0)
        if abs(ham * 1000.0 - r) > 1e-6:
            return None, f"mm'den ince ( {ham!r} girildi ) — kot en çok üç ondalıkla ( mm ) yazılır."
        mm = int(r)
    if abs(mm) > KOT_AZAMI_MM:
        sinir = f"{KOT_AZAMI_MM // 1000:,}".replace(",", ".")
        return None, f"−{sinir} ile +{sinir} m arasında olmalı ( {kot_metni(mm)} girildi )."
    return mm, None


def _tam_yazim(p):
    """Ondalıksız yazılmış kot ( "3200", "-7000" ) — mm ile girilmiş kotun
    belirtisi;  ondalıklıysa ya da okunamıyorsa None."""
    if isinstance(p, int) and not isinstance(p, bool):
        return p
    if isinstance(p, str):
        m = re.fullmatch(r"([+\-−–]?)(\d+)", re.sub(r"\s", "", p))
        if m:
            return -int(m[2]) if m[1] in ("-", "−", "–") else int(m[2])
    return None


def kotlari_oku(ham):
    """Durak kotları ( alttan üste ) → ( [ mm ] , [] ) ya da ( None , [ ileti ] ).
    Metin noktalı virgülle ya da satır satır;  liste de olur ( API )."""
    if isinstance(ham, str):
        if len(ham) > KOT_METNI_AZAMI:
            return None, [f"çok uzun ( {len(ham)} karakter ) — en çok {DURAK_AZAMI} durak girilir."]
        parcalar = [p for p in re.split(r"[;\n]", ham) if p.strip()]
    elif isinstance(ham, (list, tuple)):
        parcalar = list(ham)
    else:
        return None, [f"kotlar noktalı virgülle yazılır ( {str(ham)[:40]!r} girildi ) — −7,00; ±0,00; +3,20."]
    if len(parcalar) > DURAK_AZAMI:
        return None, [f"en çok {DURAK_AZAMI} durak girilir ( {len(parcalar)} kot girildi )."]
    #  BİRİM:  "0; 3200; 6400" mm yazılmıştır — kotun tavanı ya da durağın 11 m
    #  kuralı ( m.5.2.3.1 — çizim ) da reddederdi, ama sebebi söylemeden.  Ölçüt
    #  üçü birden:  hiçbirinde ondalık yok, biri 100'ü aşıyor, ardışık ikisinin
    #  arası 11'den fazla.  Okunuştan önce:  aralık iletisi bunu örtmesin.
    tamlar = [_tam_yazim(p) for p in parcalar]
    if (
        len(tamlar) >= 2
        and None not in tamlar
        and max(abs(t) for t in tamlar) >= 100
        and any(b - a > ESIK_ARASI / 1000.0 for a, b in zip(tamlar, tamlar[1:]))
    ):
        return None, [
            "ardışık iki durak arası 11 m'yi aşıyor — kotlar metreyle yazılır ( −7,00; ±0,00; +3,20 ); "
            "mm girdiyseniz metreye çevirin."
        ]
    kotlar, hata = [], []
    for i, p in enumerate(parcalar, 1):
        mm, ileti = kot_oku(p)
        if ileti:
            hata.append(f"{i}. kot {ileti}")
        else:
            kotlar.append(mm)
    if hata:
        return None, hata
    if len(kotlar) < 2:
        return None, [f"en az iki durak gerekir ( {len(kotlar)} kot girildi )."]
    if all(b < a for a, b in zip(kotlar, kotlar[1:])):
        return None, [
            f"ters sırada yazılmış — en alt duraktan başlayın ( {kot_metni(kotlar[-1])} … "
            f"{kot_metni(kotlar[0])} )."
        ]
    for i, (a, b) in enumerate(zip(kotlar, kotlar[1:]), 1):
        if b == a:
            return None, [f"{i}. ve {i + 1}. durak aynı kotta ( {kot_metni(a)} )."]
        if b < a:
            return None, [
                f"en alt duraktan başlayarak artan sırayla yazılır — {i + 1}. kot ( {kot_metni(b)} ) "
                f"{i}. kottan ( {kot_metni(a)} ) aşağıda."
            ]
    return kotlar, []


def kot_kipi(A):
    """Katlar kotla mı girildi:  durak kotları dolu ( yalnız boşluk değil ) —
    tasarim/alanlar KAT GİRİŞİ.  Okunamayan bir değer de kotla giriştir:  kapı
    onun hatasını söyler."""
    v = (A or {}).get(alanlar.DURAK_KOTLARI)
    if v is None:
        return False
    if isinstance(v, str):
        return bool(v.strip())
    if isinstance(v, (list, tuple)):
        return bool(v)
    return True


def kotlari_yaz(kotlar):
    """Durak kotları ( mm ) → alanın metni ( alttan üste, noktalı virgülle ) —
    ölçü kaynağı bir durağın kotunu oynatırken."""
    return "; ".join(kot_metni(round(float(k))) for k in kotlar)


def iletiler_metni(etiket, iletiler):
    """Bir alanın iletileri tek satırda:  ilk üçü, fazlası sayıyla — kapı ve
    türetme aynı cümleyi kurar."""
    ek = f"  ( + {len(iletiler) - 3} )" if len(iletiler) > 3 else ""
    return f"{etiket}:  " + "  ·  ".join(iletiler[:3]) + ek


def _tam(v):
    """Kapının okuduğu türde:  tam değerli düz sayı int ( "4600" → 4600 — uc_ortak
    _sayi );  izli sayı izini korur ( ölçü kaynağı )."""
    if isinstance(v, izli.Izli):
        return v
    return int(v) if float(v).is_integer() else v


def _mm_metni(x):
    return kot_metni(round(float(x)))


#  Kotla girişte zorunlu kutular.  Makine dairesinin zemini KURAL:  boşsa tabliye
#  beton yüksekliğinin varsayılanı ( ölçüyle girişteki gibi — boş alan varsayılanı
#  alır;  makine dairesize dönen kotlu proje takılmasın )
ZORUNLU = ("kuyu_dibi_kotu", "kuyu_tavani_kotu")
TABLIYE_KURALI = alanlar.ALAN["tabliye_yuksekligi"].varsayilan


def kot_tablosu(A, doseme, daireli):
    """KOTLA GİRİŞİN TÜRETMESİ — tek yer ( KOT_PLANI § 1.2 ):  hesap
    ( mukavemet_girdi.tamamla ) türetilenleri girdiye yazar, çizim onları okur.

        A        girdi:  kot kutuları m ( izlemede izli ), durak kotları metin
        doseme   tavan döşemesinin kalınlığı ( mm — kopru.tavan_dosemesi:  çizimin
                 kullandığı sayının aynısı, türeviyle )
        daireli  makine daireli mi:  tabliye yalnız orada türer

    Döner ( türetilen , kot , hatalar ):
        türetilen  durak_adedi · seyir_mesafesi ( m ) · kat_yukseklikleri ( mm
                   listesi, alttan ) · kuyu_dibi · son_kat_yuksekligi ·
                   tabliye_yuksekligi ( mm;  daireli ) — makine dairesinin zemini
                   boşsa kuralın kotu da ( md_zemini_kotu, m )
        kot        ofset:  en alt durağın kotu ( mm — yalnız yazılar;  iç koordinat
                   0 = en alt durak ) · kaynak:  alan → "+57,60 − ( -7,00 )"
        hatalar    [ ileti ] — doluysa türetilen boştur:  hesap da çizim de durur.
    Kotla giriş değilse ( {} , {} , [] ).

    Kotlar mm'de tam sayıdır ( kot_oku );  kutunun izli değeri mm'ye oturtulur,
    türevi korunur ( izli.oturt ):  ∂KY / ∂kuyu_dibi_kotu = −1.000 mm / m."""
    if not kot_kipi(A):
        return {}, {}, []
    et = {k: alanlar.ALAN[k].etiket for k in (alanlar.DURAK_KOTLARI, "md_zemini_kotu") + ZORUNLU}
    hata = []
    kotlar, iletiler = kotlari_oku(A.get(alanlar.DURAK_KOTLARI))
    if iletiler:
        hata.append(iletiler_metni(et[alanlar.DURAK_KOTLARI], iletiler))
    mm = {}
    for k in ZORUNLU + (("md_zemini_kotu",) if daireli else ()):
        v = A.get(k)
        if v is None or (isinstance(v, str) and not v.strip()):
            if k in ZORUNLU:
                hata.append(f"{et[k]}:  kotla girişte girilmeli.")
            continue
        okunan, ileti = kot_oku(v)
        if ileti:
            hata.append(f"{et[k]}:  {ileti}")
        else:
            mm[k] = izli.oturt(v * 1000.0) if isinstance(v, (int, float)) else float(okunan)
    if hata:
        return {}, {}, hata
    #  İzlemede her durağın kotu kendi kimliğini taşır ( ( "kot" , sıra ) — ölçü
    #  kaynağı:  kat yüksekliği iki durağın kotundan, seyir uçlarınkinden );  çare
    #  onları önermez ( yalnız girdi kutuları — durak kotları mimariden gelir )
    kotlar = [izli.girdi(k, ("kot", j)) for j, k in enumerate(kotlar)]
    alt, ust = kotlar[0], kotlar[-1]
    dip, tavan = mm["kuyu_dibi_kotu"], mm["kuyu_tavani_kotu"]
    if not dip < alt:
        hata.append(
            f"{et['kuyu_dibi_kotu']}:  en alt durağın altında olmalı ( kuyu dibi {_mm_metni(dip)}, "
            f"en alt durak {kot_metni(alt)} )."
        )
    if not tavan > ust:
        hata.append(
            f"{et['kuyu_tavani_kotu']}:  en üst durağın üstünde olmalı ( kuyu tavanı {_mm_metni(tavan)}, "
            f"en üst durak {kot_metni(ust)} )."
        )
    #  Tabliye:  makine dairesinin zemininden tabliyenin üstüne ( kuyu tavanı +
    #  döşeme ).  Döşeme sayı değilse çizim onun iletisini verir;  tabliye türemez.
    tabliye = daireli and sayi_mi(doseme) and doseme > 0
    kuralla = tabliye and "md_zemini_kotu" not in mm
    if kuralla:
        #  Boş kutu:  zemin tabliyenin üstünden varsayılan kadar aşağıda;  izlemede
        #  kutunun kendisine eğim ( kopru._kural gibi — ölçü kaynağı onu gösterir )
        md_m = izli.oz((tavan + doseme - TABLIYE_KURALI) / 1000.0, ("girdi", "md_zemini_kotu"))
        mm["md_zemini_kotu"] = izli.oturt(md_m * 1000.0)
    if tabliye and mm["md_zemini_kotu"] > tavan + doseme:
        hata.append(
            f"{et['md_zemini_kotu']}:  tabliyenin üstünden yukarıda olamaz ( zemin "
            f"{_mm_metni(mm['md_zemini_kotu'])}, tabliyenin üstü {_mm_metni(tavan + doseme)} = kuyu "
            f"tavanı + tavan döşemesi {float(doseme):g} mm )."
        )
    if hata:
        return {}, {}, hata
    turetilen = {
        "durak_adedi": len(kotlar),
        "seyir_mesafesi": _tam((ust - alt) / 1000.0),
        "kat_yukseklikleri": [b - a for a, b in zip(kotlar, kotlar[1:])],
        "kuyu_dibi": _tam(alt - dip),
        "son_kat_yuksekligi": _tam(tavan - ust),
    }
    kaynak = {
        "durak_adedi": f"{len(kotlar)} durak kotu",
        "seyir_mesafesi": f"{kot_metni(ust)} − ( {kot_metni(alt)} )",
        "kat_yukseklikleri": "ardışık durak kotlarının farkı",
        "kuyu_dibi": f"{kot_metni(alt)} − ( {_mm_metni(dip)} )",
        "son_kat_yuksekligi": f"{_mm_metni(tavan)} − ( {kot_metni(ust)} )",
    }
    if tabliye:
        md = mm["md_zemini_kotu"]
        turetilen["tabliye_yuksekligi"] = _tam(tavan + doseme - md)
        kaynak["tabliye_yuksekligi"] = f"{_mm_metni(tavan)} + {float(doseme):g} mm − ( {_mm_metni(md)} )"
        if kuralla:  # ekranın soluk gösterdiği:  kuralın zemin kotu
            turetilen["md_zemini_kotu"] = md_m
    return turetilen, {"ofset": alt, "kaynak": kaynak}, []


def araliklar(ham, durak, seyir):
    if ham is None or (isinstance(ham, str) and not ham.strip()):
        return seyir * 1000.0 / (durak - 1), []
    if isinstance(ham, str):
        parcalar = re.split(r"[;\n]", ham.strip())
    elif isinstance(ham, (list, tuple)):
        parcalar = ham
    else:
        return None, ["Kat yükseklikleri: mm cinsinden, noktalı virgülle ayrılmış bir liste olmalı."]
    if len(parcalar) != durak - 1:
        return None, [
            f"Kat yükseklikleri: {durak:g} durak için {durak - 1:g} aralık girilmeli "
            f"( {len(parcalar)} girildi )."
        ]
    sonuc, hata = [], []
    for i, p in enumerate(parcalar):
        if isinstance(p, str):
            p = p.strip()
            if re.fullmatch(r"[+-]?[1-9]\d{0,2}[.,]\d{3}", p):
                hata.append(
                    f"{i + 1}. kat yüksekliği: belirsiz sayı yazımı {p!r}; "
                    "binlik ayracı kullanmayın ( örnek: 3400 )."
                )
                continue
            try:
                p = float(p.replace(",", "."))
            except ValueError:
                p = None
        if (
            not isinstance(p, (int, float))
            or isinstance(p, bool)
            or not math.isfinite(p)
            or p <= 0
            or p > 1e12
        ):
            hata.append(f"{i + 1}. kat yüksekliği: sıfırdan büyük, sonlu bir sayı olmalı.")
        else:
            sonuc.append(izli.sayi(p))  # kotla girişin listesi izli olabilir ( kot_tablosu )
    if hata:
        return None, hata
    toplam = izli.fsum(sonuc)
    if abs(toplam - seyir * 1000.0) > 0.5:
        return None, [
            f"Kat yükseklikleri toplamı {toplam:g} mm, seyir mesafesi "
            f"{seyir * 1000.0:g} mm — iki değer aynı olmalı."
        ]
    return sonuc, []

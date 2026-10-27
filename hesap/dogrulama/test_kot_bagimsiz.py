"""BAĞIMSIZ KOT DENETİMİ  —  "kotla giriş" için kara kutu denetimi, 27 Eki 2026.

Çalıştırma ( depo kökünden ):
    .venv/bin/python -m pytest -q -p no:cacheprovider hesap/dogrulama/test_kot_bagimsiz.py

NEYİ:  kat girişinin iki kipi ( ölçüyle · kotla ).  Kotlardan türetilen
ölçüler ( TS EN 81-20 tanımlarıyla ), "ne çiziliyorsa o hesaplanır" şartı
( hesap ile "Projeyi paketle"nin DXF'i aynı sayıyı okur ), kotların geometriye
girmemesi ( ikiz ve kaydırma ), hatalı kot tablosunun hesabı ve çizimi AYNI
iletiyle durdurması.

HANGİ KAYNAKTAN:  beklenen değerler altın çıktıdan ya da programın bugünkü
çıktısından ALINMAZ;  kaynağın kendi sayılarından elle hesaplanır:
  -  63444-2 A BLOK — mimarın plan kotları ( döşemenin üstü ) ve tabliye betonu
  -  11 LiftDesigner paftası — kesitlerin bloklarından okunan kotlar;  beklenen
     KY ve seyir LD'nin VERİ BLOĞUNDAKİ sayılardır
  -  BAR 2515 — ofisin ölçü formu ( farklar ölçülmüş;  en alt durak ±0,00 )
  -  TS EN 81-20 tanımları:  seyir = en üst − en alt durak · KY = en alt durak −
     kuyu dibi ( 3.36 ) · son kat = kuyu tavanı ( döşemenin ALTI ) − en üst
     durak ( 3.17 ) · tabliye = ( kuyu tavanı + tavan döşemesi ) − makine
     dairesinin zemini · kuyu boyu = kuyu tavanı − kuyu dibi

NEYİ OKUMADAN:  uygulamanın kot kodu ( cizim/katlar.py, motor/uygulama/
mukavemet_girdi.py, cizim/kopru.py, cizim/dusey.py, uçların iç işlevleri, ön
yüzün kot dosyaları ), onun testleri ( testler/test_kotlar.py ), plan ve
araştırma belgeleri ve dalın farkları okunmadan yazıldı.  Program yalnız
uçlarından ( hesap · çizim · paketin ZIP'i ) ve şemasından
( uygulama_istegi.alanlar ) tanınır;  istek biçimi standart_istek'ten, DXF'i
okuma yolu test_teslim_uyumu'ndan.  Üretim kodunu değiştirmez.  KALAN TEST
AÇIK BULGUDUR ( beklenen kaynağındır;  test programa uydurulmaz ).

DXF'ten ölçmenin yolu:  kesit blokları gerçek mm'dedir ( ölçek, kotla ilgisi
olmayan SD / SW plan ölçüsünden bulunur ).  Kesit kırıktır ( aradaki katlar
çizilmez ):  kırığın boyu, kırığı aşan kat ölçüsünün YAZDIĞI gerçek mesafeden
( "57900" ) − çizilen boyundan, yeri kuyu duvarının kesildiği boşluktan okunur —
kot yazılarından bağımsız;  sonra kot yazıları bu açılmış yüksekliklerle
karşılaştırılır.

SÖZLEŞMENİN DÜZELTMESİ ( 27 Eki, koordinatör;  ilk koşunun üç bulgusu
sözleşmenin eksiğiydi ):
  -  2.2 d:  yalnız NOKTALI ÜÇ ondalık ( "1.200", "+2.834" ) belirsizdir ( bin iki
     yüz de okunur ):  ileti virgüllü yazımı söyler;  virgüllü üç ondalık mm'dir,
     noktalı iki ondalık ( "+3.20" ) okunur.
  -  1.2.5:  tam sayı mm şartı DEĞERDEDİR, türde değil ( metre seyirden türeyen
     kuyu boyu float'tır ama tam mm'dir ).
  -  B4 / 2.2 f:  kot kipinde veri tablosunun notlarına "Kotlar bitmiş döşeme
     kotlarıdır." girer;  ikizde yalnız kot yazıları, raporun kaynak sütunu ve bu
     not farklı olabilir ( not bir satır ekler:  tablo o satır kadar büyür, yeri
     kayar ).

B6 ( dosya gidiş-dönüşü ):  paketin ZIP'inde proje dosyası varsa kotlar orada
yazıldığı gibi ( "−7,00" ) kalmalı;  yoksa kapsam dışı ( ön yüzün dosyası —
uçtan uca testi ), bulgu sayılmaz.
"""

import copy
import io
import json
import logging
import re
import unittest
import zipfile
from collections import Counter

import ezdxf
from ezdxf import bbox, disassemble

from testler.test_yerlesim_saglamligi import standart_istek
from uclar import cizim_uclari, uygulama_istegi, uygulama_uclari

#  ═══════════════════════════════════════════════════════════════════════════
#  KAYNAK VERİLER  ( mm;  kot = mimarın plan kotu, döşemenin ÜSTÜ )
#  ═══════════════════════════════════════════════════════════════════════════

#  63444-2 A BLOK ( mimarın planı ):  kuyunun tabanı −8,80 · duraklar −7,00
#  ( 2. bodrum ), −3,50, ±0,00, sonra +3,20'den +57,60'a 3,20 arayla 18 kat
#  ( toplam 21 durak ) · makine dairesinin zemini +60,80 · kuyunun üstü
#  ( döşemenin ÜSTÜ ) +62,30 · tabliye betonu 100 mm.
A_DURAKLAR = (-7000, -3500, 0, *range(3200, 57601, 3200))
A_KUYU_TABANI = -8800
A_MD_ZEMINI = 60800
A_KUYU_USTU = 62300
A_TABLIYE_BETONU = 100
A_KUYU_TAVANI = A_KUYU_USTU - A_TABLIYE_BETONU  # +62,20:  tavan döşemesinin ALTI
A_DUVAR = 250  # projenin kuyu duvarı
A_MD_YUKSEKLIK = 3700  # makine dairesinin iç yüksekliği ( 1.500 tabliyenin üstünde 2.100 çalışma )
#  Mimariden elle ( görevin "mimariden beklenen" satırı ):
A_BEKLENEN = {
    "durak_adedi": 21,
    "seyir": 64600,  # +57,60 − ( −7,00 )
    "kuyu_dibi": 1800,  # −7,00 − ( −8,80 )
    "son_kat": 4600,  # +62,20 − ( +57,60 )
    "tabliye": 1500,  # ( +62,20 + 0,10 ) − ( +60,80 )
    "kuyu_boyu": 71000,  # +62,20 − ( −8,80 )
    "katlar": [3500, 3500] + [3200] * 18,
}
#  Paftada görünmesi gereken kotlar:  duraklar, kuyu dibi, makine dairesinin
#  zemini, tabliyenin üstü ( = kuyunun üstü +62,30 );  kırık kesitte en az uçlar
A_PAFTA_KOTLARI = (A_KUYU_TABANI, *A_DURAKLAR, A_MD_ZEMINI, A_KUYU_USTU)
A_UCLAR = {A_KUYU_TABANI, A_DURAKLAR[0], A_DURAKLAR[-1], A_MD_ZEMINI, A_KUYU_USTU}

#  LiftDesigner paftaları:  ( ad, en alt durak, en üst durak, kuyu dibi kotu,
#  LD KY, LD seyir ).  İlk üç sayı kesitlerin bloklarından okunan kotlar;  son
#  ikisi LD'nin VERİ BLOĞUNDAKİ KY ve seyir — beklenen bunlardır.
LD_PAFTALARI = (
    ("1022", 0, 9000, -1700, 1700, 9000),
    ("12495-18", 200, 3700, -1500, 1700, 3500),
    ("1250 KG MRL", 0, 12000, -1450, 1450, 12000),
    ("1275", -2500, 24500, -4200, 1700, 27000),
    ("4815-6", 180, 18330, -1520, 1700, 18150),
    ("800 KG", 200, 27700, -1500, 1700, 27500),
    ("K106", 0, 15000, -1700, 1700, 15000),
    ("K111", 0, 9000, -1480, 1480, 9000),
    ("K379", 0, 24000, -1750, 1750, 24000),
    ("K407", -3500, 6000, -5000, 1500, 9500),
    ("K431", -2750, 9250, -4200, 1450, 12000),
)
#  Ara durakları paftada okunmuyor:  ~3.000 arayla eşit bölünür ( kalan mm ilk
#  aralıklara — mm'ye kadar kot da denenmiş olur;  hiçbir aralık 11 m'yi aşmaz ).
#  Tavan:  son kat 4.200 ( görevin şartı:  standart istekle çizilebilsin ).
LD_SON_KAT = 4200

#  BAR 2515 ( mevcut bina, ölçü formu — ölçüler FARK olarak ölçülmüş ):  15
#  durak, seyir 42 m ( eşit 3.000 ), son kat 4.250, kuyu dibi 1.750, makine
#  dairesiz.  Kotla:  en alt durak ±0,00 → kuyu dibi −1,75, tavan +46,25.
B_DURAKLAR = tuple(range(0, 42001, 3000))
B_KUYU_TABANI = -1750
B_KUYU_TAVANI = 46250
B_BEKLENEN = {"durak_adedi": 15, "seyir": 42000, "kuyu_dibi": 1750, "son_kat": 4250, "katlar": [3000] * 14}

#  Programın kaydedici kökleri ( testler/conftest.py'deki liste ):  bunlara
#  düşen ERROR yutulmuş bir hatadır
PROGRAM = frozenset(("temel", "tasarim", "cizim", "motor", "ciktilar", "uclar", "main"))


#  ═══════════════════════════════════════════════════════════════════════════
#  YAZIM:  mimarın yazdığı kot ↔ paftanın kot yazısı
#  ═══════════════════════════════════════════════════════════════════════════


def kot_metni(mm, eksi="−", ondalik=","):
    """Mimarın plandaki yazımı:  −7000 → "−7,00" · 0 → "±0,00" · 3166 → "+3,166"."""
    if mm == 0:
        return f"±0{ondalik}00"
    m, r = divmod(abs(mm), 1000)
    kesir = f"{r:03d}"
    if kesir[2] == "0":
        kesir = kesir[:2]
    if len(kesir) == 3:
        #  2.2 d:  noktalı üç ondalık belirsizdir ( "+2.834" bin iki yüz gibi de
        #  okunur ):  mm'li kot hep virgülle;  nokta yalnız iki ondalıkta
        ondalik = ","
    return f"{'+' if mm > 0 else eksi}{m}{ondalik}{kesir}"


def metre_metni(mm):
    """Formun seyir kutusu ( m ):  64600 → "64,6" · 9000 → "9"."""
    m, r = divmod(mm, 1000)
    kesir = f"{r:03d}".rstrip("0")
    return f"{m},{kesir}" if kesir else str(m)


def pafta_kotu(mm):
    """Sözleşmedeki pafta yazısı:  iki ondalık · "±0,00" · "+3,20" · "-7,00"."""
    if mm == 0:
        return "±0,00"
    m, r = divmod(abs(mm), 1000)
    return f"{'+' if mm > 0 else '-'}{m},{r // 10:02d}"


KOT_YAZISI = re.compile(r"([+-]|±)(\d+),(\d\d)")


def yazi_kotu(metin):
    """Paftadaki kot yazısı → mm ( kot değilse None )."""
    m = KOT_YAZISI.fullmatch(metin.strip())
    if m is None:
        return None
    mm = int(m.group(2)) * 1000 + int(m.group(3)) * 10
    return -mm if m.group(1) == "-" else mm


def ara_duraklar(alt, ust, aralik=3000, azami=11000):
    """Uçları bilinen durak dizisi:  ~3.000 arayla eşit, kalan mm ilk aralıklara."""
    seyir = ust - alt
    n = max(1, round(seyir / aralik))
    while seyir / n > azami:
        n += 1
    taban, kalan = divmod(seyir, n)
    araliklar = [taban + (1 if i < kalan else 0) for i in range(n)]
    kotlar = [alt]
    for x in araliklar:
        kotlar.append(kotlar[-1] + x)
    return kotlar, araliklar


#  ═══════════════════════════════════════════════════════════════════════════
#  İSTEKLER  ( değerler formdaki gibi METİN )
#  ═══════════════════════════════════════════════════════════════════════════


def kotla(taban, duraklar, dip, tavan, md=None, eksi="−", ondalik=",", **ek):
    v = copy.deepcopy(taban)
    a = v["asansorler"][0]
    a["durak_kotlari"] = "; ".join(kot_metni(k, eksi, ondalik) for k in duraklar)
    a["kuyu_dibi_kotu"] = kot_metni(dip, eksi, ondalik)
    a["kuyu_tavani_kotu"] = kot_metni(tavan, eksi, ondalik)
    if md is not None:
        a["md_zemini_kotu"] = kot_metni(md, eksi, ondalik)
    a.update(ek)
    return v


def olcuyle(taban, durak_adedi, seyir, katlar, son_kat, kuyu_dibi, tabliye=None, **ek):
    v = copy.deepcopy(taban)
    a = v["asansorler"][0]
    a.update(
        durak_adedi=str(durak_adedi),
        seyir_mesafesi=metre_metni(seyir),
        kat_yukseklikleri="; ".join(str(k) for k in katlar),
        son_kat_yuksekligi=str(son_kat),
        kuyu_dibi=str(kuyu_dibi),
    )
    if tabliye is not None:
        a["tabliye_yuksekligi"] = str(tabliye)
    a.update(ek)
    return v


def a_taban():
    """63444-2:  makine daireli standart istek ( 1.000 kg, ağırlık sağda )."""
    v = standart_istek(1000, False, "Sağ")
    v["proje_geneli"]["md_yukseklik"] = A_MD_YUKSEKLIK
    v["asansorler"][0].update(kuyu_duvar_kalinligi=str(A_DUVAR), tavan_dosemesi=str(A_TABLIYE_BETONU))
    return v


def a_kotla(kayma=0, **ek):
    """63444-2 kotla;  kayma:  bütün kotlar birlikte ( mm )."""
    return kotla(
        a_taban(),
        [k + kayma for k in A_DURAKLAR],
        A_KUYU_TABANI + kayma,
        A_KUYU_TAVANI + kayma,
        A_MD_ZEMINI + kayma,
        **ek,
    )


def a_olcuyle(**ek):
    """63444-2'nin ölçüyle ikizi:  mimariden elle türetilen ölçüler."""
    b = A_BEKLENEN
    return olcuyle(
        a_taban(), b["durak_adedi"], b["seyir"], b["katlar"], b["son_kat"], b["kuyu_dibi"], b["tabliye"], **ek
    )


def ld_istekleri(ad, alt, ust, dip, ky, seyir):
    """( kotla, ölçüyle ikizi, beklenen ) — makine dairesiz standart istek."""
    taban = standart_istek(1000, True, "Sağ")
    kotlar, araliklar = ara_duraklar(alt, ust)
    #  Yazım çeşitlensin ( 2.2 d:  ondalık için virgül de nokta da olur;  "−",
    #  "-", "+", "±" ):  K'li paftalar ASCII eksi ve ondalık noktayla —
    #  noktalı üç ondalık belirsiz olduğundan mm'li kotlar yine virgülle ( kot_metni )
    nokta = ad.startswith("K")
    v = kotla(taban, kotlar, dip, ust + LD_SON_KAT, eksi="-" if nokta else "−", ondalik="." if nokta else ",")
    bek = {
        "durak_adedi": len(kotlar),
        "seyir": seyir,
        "kuyu_dibi": ky,
        "son_kat": LD_SON_KAT,
        "katlar": araliklar,
    }
    return v, olcuyle(taban, len(kotlar), seyir, araliklar, LD_SON_KAT, ky), bek


def b_kotla(kayma=0, **ek):
    """BAR 2515 kotla ( makine dairesiz );  kayma:  bütün kotlar birlikte ( mm )."""
    return kotla(
        standart_istek(1000, True, "Sağ"),
        [k + kayma for k in B_DURAKLAR],
        B_KUYU_TABANI + kayma,
        B_KUYU_TAVANI + kayma,
        **ek,
    )


def b_olcuyle():
    """BAR 2515 ölçü formundaki gibi:  kat yükseklikleri boş = eşit ( formun bilgisi )."""
    b = B_BEKLENEN
    return olcuyle(
        standart_istek(1000, True, "Sağ"), b["durak_adedi"], b["seyir"], [], b["son_kat"], b["kuyu_dibi"]
    )


def kaynak_ciftleri():
    """( ad, kotla isteği, ölçüyle ikizi, beklenen ) — bütün kaynaklar."""
    cift = [("63444-2", a_kotla(), a_olcuyle(), A_BEKLENEN), ("BAR 2515", b_kotla(), b_olcuyle(), B_BEKLENEN)]
    for satir in LD_PAFTALARI:
        cift.append((satir[0], *ld_istekleri(*satir)))
    return cift


#  ═══════════════════════════════════════════════════════════════════════════
#  UÇLAR ( kara kutu ) — her istek bir kez;  programın kaydına düşen ERROR'lar
#  istekle birlikte saklanır ( yutulan hata da bulgudur )
#  ═══════════════════════════════════════════════════════════════════════════


class _HataKaydi(logging.Handler):
    def __init__(self):
        super().__init__(logging.ERROR)
        self.iletiler = []

    def emit(self, record):
        if record.name.split(".")[0] in PROGRAM:
            self.iletiler.append(f"{record.name}:  {record.getMessage()}")


_ONBELLEK = {}
#  Paketin ZIP'i:  istek → ( dosya adları, proje dosyalarının metni ) — B6 için
_PAKET = {}
#  Programın proje dosyaları ( ön yüzün kaydettiği .uygulama · .avan;  JSON )
PROJE_UZANTILARI = (".uygulama", ".avan", ".json")


def _anahtar(tur, v):
    return (tur, json.dumps(v, sort_keys=True, ensure_ascii=False))


def _dxf_ac(govde):
    """Paketin ZIP'i → ( DXF ya da ucun hata yanıtı, ZIP'teki adlar, proje dosyaları )."""
    try:
        z = zipfile.ZipFile(io.BytesIO(govde))
    except zipfile.BadZipFile:
        #  paket inmedi:  uç hatayı JSON ile söyler ( aktif · hata )
        try:
            return json.loads(govde), [], {}
        except ValueError:
            return {"aktif": False, "hata": [govde.decode("utf-8", "replace")]}, [], {}
    adlar = z.namelist()
    proje = {n: z.read(n).decode("utf-8", "replace") for n in adlar if n.lower().endswith(PROJE_UZANTILARI)}
    ad = next(n for n in adlar if n.endswith(".dxf"))
    return ezdxf.read(io.StringIO(z.read(ad).decode("utf-8"))), adlar, proje


def _cagir(tur, v):
    anahtar = _anahtar(tur, v)
    if anahtar not in _ONBELLEK:
        kayit, kok = _HataKaydi(), logging.getLogger()
        kok.addHandler(kayit)
        try:
            if tur == "hesap":
                s = json.loads(uygulama_uclari.api_uygulama_coklu(copy.deepcopy(v)).body)
            elif tur == "cizim":
                s = json.loads(cizim_uclari.api_cizimler(copy.deepcopy(v)).body)
            else:
                s, adlar, proje = _dxf_ac(uygulama_uclari.indir_uygulama_dwg(copy.deepcopy(v)).body)
                _PAKET[anahtar] = (adlar, proje)
        finally:
            kok.removeHandler(kayit)
        _ONBELLEK[anahtar] = (s, kayit.iletiler)
    return _ONBELLEK[anahtar][0]


def hesap(v):
    return _cagir("hesap", v)


def cizim(v):
    return _cagir("cizim", v)


def dxf(v):
    return _cagir("dxf", v)


def yutulan(v):
    return [m for tur in ("hesap", "cizim", "dxf") for m in _ONBELLEK.get(_anahtar(tur, v), (None, []))[1]]


def iletiler(yanit):
    """Yanıtın hata iletileri ( liste ya da tek metin ) — düz liste."""
    h = yanit.get("hata") if isinstance(yanit, dict) else None
    if not h:
        return []
    return [str(x) for x in (h if isinstance(h, list) else [h])]


def paket_iletisi(p):
    """Paket inmediyse ucun iletisi ( okunur hata için )."""
    return f"paket kurulamadı:  {iletiler(p)}" if isinstance(p, dict) else ""


def asansor(h):
    return (h.get("asansorler") or [{}])[0]


def girdi(h):
    return asansor(h).get("girdi") or {}


def hesap_iletileri(h):
    return iletiler(h) + iletiler(asansor(h))


def hesap_aktif(h):
    return bool(h.get("aktif")) and asansor(h).get("aktif", True) is not False


def _kaynak_serbest(x):
    """Raporun kaynak sütunu:  kotla girişte "KOT  ·  formül", ölçüyle girişte
    "GİRİŞ" — hesapta sözleşmenin tek serbest farkı ( B4 )."""
    if isinstance(x, dict):
        return {k: _kaynak_serbest(d) for k, d in x.items()}
    if isinstance(x, list):
        return [_kaynak_serbest(d) for d in x]
    if isinstance(x, str) and x.startswith("KOT"):
        return "GİRİŞ"
    return x


def rapor(h):
    """Hesabın karşılaştırılan yüzü:  durum · bölümler · özet · uyarılar."""
    a = asansor(h)
    return _kaynak_serbest(
        {
            "aktif": h.get("aktif"),
            "hata": h.get("hata"),
            **{k: a.get(k) for k in ("aktif", "hata", "bolumler", "ozet", "uyarilar")},
        }
    )


def farklar(x, y, azami=12):
    """İki JSON ağacının ilk farkları ( okunur ileti için ) — boş liste = aynı."""
    cikti = []

    def gez(a, b, p):
        if len(cikti) >= azami:
            return
        if isinstance(a, dict) and isinstance(b, dict):
            for k in sorted(set(a) | set(b), key=str):
                if k not in a or k not in b:
                    sol = "—" if k not in a else repr(a[k])[:90]
                    sag = "—" if k not in b else repr(b[k])[:90]
                    cikti.append(f"{p}/{k}:  {sol}  ↔  {sag}")
                else:
                    gez(a[k], b[k], f"{p}/{k}")
        elif isinstance(a, list) and isinstance(b, list):
            if len(a) != len(b):
                cikti.append(f"{p}:  {len(a)} öğe  ↔  {len(b)} öğe")
            for i, (aa, bb) in enumerate(zip(a, b)):
                gez(aa, bb, f"{p}[{i}]")
        elif a != b:
            cikti.append(f"{p}:  {a!r}  ↔  {b!r}"[:300])

    gez(x, y, "")
    return cikti


def katlar_listesi(x):
    """girdi'nin kat yükseklikleri ( liste ya da "3500; 3500; …" ) → sayı listesi."""
    if isinstance(x, list):
        return x
    parcalar = [p for p in re.split(r"\s*;\s*", str(x or "").strip()) if p]
    return [float(p.replace(",", ".")) if re.search(r"[.,]", p) else int(p) for p in parcalar]


#  ═══════════════════════════════════════════════════════════════════════════
#  DXF OKUMA ( test_teslim_uyumu'nun yolu:  paketin ZIP'i → ezdxf )
#  ═══════════════════════════════════════════════════════════════════════════

METIN = frozenset(("TEXT", "MTEXT", "ATTRIB", "ATTDEF"))
#  Düşey kesitler ( test_teslim_uyumu'nun blok adları ) ve ölçekleri bulan plan
#  ölçüsü:  yan kesitte kuyu derinliği ( SD ), ön kesitte kuyu genişliği ( SW )
KESITLER = (
    ("CIZIM_KUYU_KESITI_YAN", "SD", "kuyu_derinligi"),
    ("CIZIM_KUYU_KESITI_ON", "SW", "kuyu_genisligi"),
)
#  En alt durağın kapısını gösteren görünüşler ( sözleşme )
KAPI_GORUNUSLERI = ("CIZIM_GIRIS", "CIZIM_KAPI_KESITI")
#  Veri tablosu ( yazı tablosu ):  ikizde kot notu ( B4 / 2.2 f ) yüzünden ayrı
#  denetlenir ( veri_tablosu_farki )
VERI_TABLOSU = "CIZIM_VERILER"
YAZI_TABLOLARI = frozenset((VERI_TABLOSU,))
#  2.2 f:  kot kipinde veri tablosunun notlarına giren satır ( sözleşmenin metni )
KOT_NOTU = "Kotlar bitmiş döşeme kotlarıdır."


def yazi(e):
    return e.plain_text() if e.dxftype() == "MTEXT" else e.dxf.text


def blok(doc, ad):
    return next((b for b in doc.blocks if b.name.startswith(ad)), None)


def cizim_bloklari(doc):
    """Paftanın çizim blokları ( CIZIM_ ) — ad → blok."""
    return {b.name: b for b in doc.blocks if b.name.startswith("CIZIM_")}


def kot_yazilari(b):
    """Bloğun kot yazıları ( iç içe bloklar açılarak ):  [( kot mm, x, y, metin )]."""
    cikti = []
    for e in disassemble.recursive_decompose(b):
        if e.dxftype() in METIN:
            metin = yazi(e).strip()
            if (k := yazi_kotu(metin)) is not None:
                cikti.append((k, e.dxf.insert.x, e.dxf.insert.y, metin))
    return cikti


def olcek(b, etiket, mm):
    """Bloğun ölçeği ( çizim birimi / mm ):  kuyunun plan ölçüsünü ( SD · SW — kotla
    ilgisi yok ) gösteren yatay ölçünün çizilen boyu / formun değeri."""
    for e in b.query("DIMENSION"):
        if (e.dxf.get("text") or "").startswith(etiket) and abs(e.dxf.get("angle", 0.0)) % 180 < 1e-6:
            return e.get_measurement() / mm
    return None


def kiriklar(b, s):
    """Kesitin kırıkları — kot yazılarından BAĞIMSIZ:  [( alt y, üst y, boy )].
    Boy ( çizim birimi ):  kırığı aşan kat ölçüsünün yazdığı gerçek mesafe
    ( yazısı yalnız sayı:  "57900" ) × ölçek − çizilen boyu.  Yer:  o ölçünün
    aralığında kuyu duvarının ( KUYU-DUVAR ) kesildiği boşluk ( yoksa ölçünün
    aralığı )."""
    olcu = []
    for e in b.query("DIMENSION"):
        t = (e.dxf.get("text") or "").strip()
        if t.isdigit() and int(t) * s - e.get_measurement() > 0.5:
            a, u = sorted((e.dxf.defpoint2.y, e.dxf.defpoint3.y))
            olcu.append((a, u, int(t) * s - e.get_measurement()))
    ortu = sorted(
        (k.extmin.y, k.extmax.y)
        for e in disassemble.recursive_decompose(b)
        if e.dxf.layer == "KUYU-DUVAR" and e.dxftype() not in METIN and (k := bbox.extents([e])).has_data
    )
    bosluk, ust = [], None
    for y0, y1 in ortu:
        if ust is not None and y0 > ust + 0.5:
            bosluk.append((ust, y0))
        ust = y1 if ust is None else max(ust, y1)
    cikti = []
    for a, u, boy in olcu:
        ic = [(p, q) for p, q in bosluk if a - 0.5 <= p and q <= u + 0.5]
        cikti.append((*ic[0], boy) if len(ic) == 1 else (a, u, boy))
    return cikti


def acici(kirik):
    """Kırığı açılmış düşey koordinat ( çizim birimi ):  y + altındaki kırıkların
    boyu.  Bir kırığın içindeki y için None."""

    def u(y):
        ek = 0.0
        for a, b, boy in kirik:
            if y >= b - 0.5:
                ek += boy
            elif y > a + 0.5:
                return None
        return y + ek

    return u


def olculer(b):
    """Bloğun ölçü çizgileri ( DIMENSION ) — geometriden ölçülen boylar."""
    return {round(e.get_measurement(), 1) for e in b.query("DIMENSION")}


def olcu_yazisindaki_sayilar(b):
    """Ölçü yazılarındaki sayılar ( "SEYİR 64600", "KUYU YÜKSEKLİĞİ 71000" … )."""
    return {
        int(m.replace(".", ""))
        for e in b.query("DIMENSION")
        for m in re.findall(r"\d[\d.]*", e.dxf.get("text") or "")
    }


def ray_uclari(b):
    """RAY katmanındaki düşey çizgiler ( x'e göre gruplu, test_teslim_uyumu gibi ):
    her grubun [( en alt y, en üst y )]."""
    gruplar = {}
    for e in disassemble.recursive_decompose(b):
        if e.dxf.layer == "RAY" and e.dxftype() not in METIN:
            k = bbox.extents([e])
            if k.has_data:
                gruplar.setdefault(round(k.extmin.x / 40), []).append(k)
    return [(min(k.extmin.y for k in ks), max(k.extmax.y for k in ks)) for ks in gruplar.values()]


def _r(x):
    return round(float(x), 1) + 0.0


def imza(e, ty=None):
    """Yazı dışı bir çizim öğesinin geometrisi ( 0,1 birime yuvarlanmış ).
    ty:  düşey koordinatlara uygulanacak dönüşüm ( veri tablosunun satır kaydırması )."""
    t, d = e.dxftype(), e.dxf
    ty = ty or (lambda y: y)
    if t == "LINE":
        return (
            t,
            d.layer,
            tuple(sorted(((_r(d.start.x), _r(ty(d.start.y))), (_r(d.end.x), _r(ty(d.end.y)))))),
        )
    if t == "LWPOLYLINE":
        return (
            t,
            d.layer,
            bool(e.closed),
            tuple((_r(x), _r(ty(y)), round(float(w), 4)) for x, y, w in e.get_points("xyb")),
        )
    if t == "CIRCLE":
        return (t, d.layer, _r(d.center.x), _r(ty(d.center.y)), _r(d.radius))
    if t == "ARC":
        return (
            t,
            d.layer,
            _r(d.center.x),
            _r(ty(d.center.y)),
            _r(d.radius),
            _r(d.start_angle),
            _r(d.end_angle),
        )
    kutu = bbox.extents([e])
    if not kutu.has_data:
        return (t, d.layer)
    return (t, d.layer, _r(kutu.extmin.x), _r(ty(kutu.extmin.y)), _r(kutu.extmax.x), _r(ty(kutu.extmax.y)))


def geometri(varliklar):
    """Yazı dışı geometri ( iç içe bloklar açılmış ) — çoklu küme."""
    return Counter(imza(e) for e in disassemble.recursive_decompose(varliklar) if e.dxftype() not in METIN)


def yerlesim(doc, haric=frozenset()):
    """Model ve kâğıt uzayındaki blok yerleşimleri ( ad, yer, ölçek, dönme )."""
    cikti = Counter()
    for duzen in [doc.modelspace(), *doc.layouts]:
        for e in duzen.query("INSERT"):
            d = e.dxf
            if d.name not in haric:
                cikti[
                    (duzen.name, d.name, _r(d.insert.x), _r(d.insert.y), round(d.xscale, 6), _r(d.rotation))
                ] += 1
    return cikti


def geometri_farki(d1, d2, haric=frozenset(), azami=5):
    """İki paftanın yazı dışı geometrisinin farkı ( blok blok, model uzayı, blok
    yerleşimleri ) — boş liste = aynı."""
    b1, b2 = cizim_bloklari(d1), cizim_bloklari(d2)
    cikti = []
    if set(b1) != set(b2):
        cikti.append(
            f"bloklar:  yalnız 1.'de {sorted(set(b1) - set(b2))} · yalnız 2.'de {sorted(set(b2) - set(b1))}"
        )
    ciftler = [(ad, b1[ad], b2[ad]) for ad in sorted(set(b1) & set(b2) - haric)]
    ciftler.append(
        (
            "model uzayı",
            [e for e in d1.modelspace() if e.dxftype() != "INSERT"],
            [e for e in d2.modelspace() if e.dxftype() != "INSERT"],
        )
    )
    for ad, x1, x2 in ciftler:
        g1, g2 = geometri(x1), geometri(x2)
        if g1 != g2:
            fazla, eksik = list((g1 - g2).elements()), list((g2 - g1).elements())
            cikti.append(
                f"{ad}:  {len(fazla)} öğe yalnız 1.'de ( ör. {fazla[:azami]} ) · "
                f"{len(eksik)} yalnız 2.'de ( ör. {eksik[:azami]} )"
            )
    y1, y2 = yerlesim(d1, haric), yerlesim(d2, haric)
    if y1 != y2:
        cikti.append(
            f"blok yerleşimi:  yalnız 1.'de {list((y1 - y2).elements())[:azami]} · yalnız 2.'de {list((y2 - y1).elements())[:azami]}"
        )
    return cikti


def kot_disi_yazilar(b):
    return Counter(
        yazi(e).strip()
        for e in disassemble.recursive_decompose(b)
        if e.dxftype() in METIN and yazi_kotu(yazi(e)) is None
    )


def _yazilar_yerli(b):
    return [
        (yazi(e).strip(), e.dxf.insert.x, e.dxf.insert.y)
        for e in disassemble.recursive_decompose(b)
        if e.dxftype() in METIN
    ]


def veri_tablosu_farki(d_kot, d_olcu):
    """B4 / 2.2 f:  kot kipinin veri tablosu = ölçü kipininki + kot notunun satırı.

    Hoş görülen ( 2.2 f:  "not tabloya bir satır ekler;  tablo o satır kadar
    büyür ve yeri kayar" ):  notun satırı ( yazısı ve numarası ) · satırın
    ALTINDAKİ her şeyin satır yüksekliği kadar aşağıda olması ( satırı aşan
    çizgiler o kadar uzun ) · tablonun paftada satır yüksekliği × ölçek kadar
    düşey kayması · not bölümünün en geniş satırıysa bölümün başlık çizgisinin
    ( satırın üstündeki en yakın yatay çizgi ) yalnız sağ ucunun uzaması.  Başka
    her fark listelenir ( boş liste = sözleşmeye uygun )."""
    b1, b2 = blok(d_kot, VERI_TABLOSU), blok(d_olcu, VERI_TABLOSU)
    if b1 is None or b2 is None:
        return [f"veri tablosu yok:  kot kipinde {b1 is not None} · ölçü kipinde {b2 is not None}"]
    y1, y2 = _yazilar_yerli(b1), _yazilar_yerli(b2)
    notlar = [t for t in y1 if t[0] == KOT_NOTU]
    if len(notlar) != 1:
        return [f"kot kipinin tablosunda kot notu {len(notlar)} kez ( 1 beklenir )"]
    _m, nx, ny = notlar[0]
    numara = [t for t in y1 if abs(t[2] - ny) < 0.5 and t[1] < nx and re.fullmatch(r"\d+\.", t[0])]
    ustte = [t[2] for t in y1 if t[2] > ny + 0.5]
    if len(numara) != 1 or not ustte:
        return [f"kot notunun satırı okunamadı ( numara {numara} · üstte {len(ustte)} yazı )"]
    h = min(ustte) - ny  # satır yüksekliği:  üstteki en yakın satıra uzaklık

    def ty(y):
        #  not satırı çıkarılınca satırın altındaki her şey h yukarı
        return y + h if y < ny - 0.5 else y

    cikti = []
    kalan = Counter((m, _r(x), _r(ty(y))) for m, x, y in y1 if (m, x, y) not in (notlar[0], numara[0]))
    olcu = Counter((m, _r(x), _r(y)) for m, x, y in y2)
    if kalan != olcu:
        cikti.append(
            f"yazılar ( not çıkarılınca ):  yalnız kotta {sorted((kalan - olcu).elements())[:5]} · "
            f"yalnız ölçüde {sorted((olcu - kalan).elements())[:5]}"
        )
    g1 = Counter(imza(e, ty) for e in disassemble.recursive_decompose(b1) if e.dxftype() not in METIN)
    g2 = geometri(b2)
    fazla, eksik = list((g1 - g2).elements()), list((g2 - g1).elements())

    def yatay(s, y=None):
        return s[0] == "LINE" and s[2][0][1] == s[2][1][1] and (y is None or s[2][0][1] == y)

    ustteki = sorted({s[2][0][1] for s in g1 if yatay(s) and s[2][0][1] > ny + 0.5})
    if ustteki:
        uzun = [s for s in fazla if yatay(s, ustteki[0])]
        kisa = [s for s in eksik if yatay(s, ustteki[0])]
        if (
            len(uzun) == len(kisa) == 1
            and uzun[0][1] == kisa[0][1]
            and uzun[0][2][0] == kisa[0][2][0]
            and uzun[0][2][1][0] > kisa[0][2][1][0]
        ):
            fazla.remove(uzun[0])
            eksik.remove(kisa[0])
    if fazla or eksik:
        cikti.append(
            f"geometri ( not satırı çıkarılınca ):  yalnız kotta {fazla[:5]} · yalnız ölçüde {eksik[:5]}"
        )
    p1 = [k for k in yerlesim(d_kot) if k[1] == VERI_TABLOSU]
    p2 = [k for k in yerlesim(d_olcu) if k[1] == VERI_TABLOSU]
    if len(p1) != 1 or len(p2) != 1:
        cikti.append(f"tablonun yerleşimi:  kotta {p1} · ölçüde {p2}")
    else:
        (_d1, _a1, x1, yy1, s1, r1), (_d2, _a2, x2, yy2, s2, r2) = p1[0], p2[0]
        if (x1, s1, r1) != (x2, s2, r2) or abs(abs(yy1 - yy2) - h * s1) > 0.11:
            cikti.append(f"tablonun yeri:  {p1[0]}  ↔  {p2[0]} ( beklenen düşey kayma {h * s1:.2f} )")
    return cikti


def _metinler(x):
    """JSON ağacındaki bütün metinler."""
    if isinstance(x, dict):
        for d in x.values():
            yield from _metinler(d)
    elif isinstance(x, list):
        for d in x:
            yield from _metinler(d)
    elif isinstance(x, str):
        yield x


#  ═══════════════════════════════════════════════════════════════════════════
#  ORTAK DENETİMLER
#  ═══════════════════════════════════════════════════════════════════════════


class _Ortak(unittest.TestCase):
    maxDiff = None

    def kayit_temiz(self, v, ad=""):
        with self.subTest(ad, denetim="programın kaydında ERROR yok ( yutulan hata )"):
            self.assertEqual(yutulan(v), [])

    def kuruldu(self, h, ad):
        with self.subTest(ad, denetim="hesap kuruldu"):
            self.assertTrue(girdi(h), hesap_iletileri(h))
        return girdi(h)

    def turetilen_degerler(self, h, bek, ad):
        """Hesabın gördüğü türetilenler = kaynağın sayıları."""
        g = self.kuruldu(h, ad)
        if not g:
            return
        with self.subTest(ad, alan="durak_adedi"):
            self.assertEqual(g.get("durak_adedi"), bek["durak_adedi"])
        with self.subTest(ad, alan="seyir_mesafesi ( m )"):
            self.assertIsInstance(g.get("seyir_mesafesi"), (int, float))
            self.assertEqual(round(g["seyir_mesafesi"] * 1000), bek["seyir"])
        with self.subTest(ad, alan="seyir_mesafesi kayan nokta gürültüsüz"):
            self.assertEqual(g.get("seyir_mesafesi"), bek["seyir"] / 1000)
        for alan, k in (
            ("kuyu_dibi", "kuyu_dibi"),
            ("son_kat_yuksekligi", "son_kat"),
            ("tabliye_yuksekligi", "tabliye"),
            ("kuyu_boyu", "kuyu_boyu"),
        ):
            if k in bek:
                with self.subTest(ad, alan=alan):
                    self.assertEqual(g.get(alan), bek[k])
        with self.subTest(ad, alan="kat_yukseklikleri"):
            ky = katlar_listesi(g.get("kat_yukseklikleri"))
            if not ky and len(set(bek["katlar"])) == 1:
                ky = [bek["katlar"][0]] * len(bek["katlar"])  # boş = eşit ( formun bilgisi )
            self.assertEqual(ky, bek["katlar"])

    def turetilen_tam_mm(self, h, ad):
        """1.2.5:  türetilen her değer TAM mm'dir ( x == round( x ), kayan nokta
        gürültüsü yok ) — şart değerdedir, türde değil:  metre seyirden türeyen
        kuyu boyu float olabilir ( 71000.0 ).  Seyrin kendisi metredir:  onun
        gürültüsüzlüğü turetilen_degerler'de ( seyir == mm / 1000 )."""
        g = girdi(h)
        if not g:
            return
        for alan in ("durak_adedi", "kuyu_dibi", "son_kat_yuksekligi", "tabliye_yuksekligi", "kuyu_boyu"):
            x = g.get(alan)
            if x is not None:
                with self.subTest(ad, alan=alan):
                    self.assertIsInstance(x, (int, float))
                    self.assertEqual(x, round(x), repr(x))
        with self.subTest(ad, alan="kat_yukseklikleri"):
            ky = katlar_listesi(g.get("kat_yukseklikleri"))
            self.assertTrue(ky and all(x == round(x) for x in ky), ky)


#  ═══════════════════════════════════════════════════════════════════════════
#  B1  KAYNAKTAN TÜRETME
#  ═══════════════════════════════════════════════════════════════════════════


class B1KaynaktanTuretme(_Ortak):
    def test_63444_2_mimarin_kotlari(self):
        v = a_kotla()
        self.turetilen_degerler(hesap(v), A_BEKLENEN, "63444-2")
        self.kayit_temiz(v, "63444-2")

    def test_ld_paftalari(self):
        for satir in LD_PAFTALARI:
            v, _ikiz, bek = ld_istekleri(*satir)
            self.turetilen_degerler(hesap(v), bek, satir[0])
            self.kayit_temiz(v, satir[0])

    def test_bar_2515_olcu_formu(self):
        v = b_kotla()
        self.turetilen_degerler(hesap(v), B_BEKLENEN, "BAR 2515")
        self.kayit_temiz(v, "BAR 2515")

    def test_turetilenler_tam_mm(self):
        #  1.2.5:  şart değerde ( tam mm ), türde değil
        for ad, v, _ikiz, _bek in kaynak_ciftleri():
            self.turetilen_tam_mm(hesap(v), ad)

    def test_noktali_iki_ondalik_virgulluyle_ayni(self):
        """2.2 d:  noktalı iki ondalık ( "+3.20" ) okunur — virgüllü yazımla ( "+3,20" )
        aynı sonuç."""
        virgul = a_kotla()
        nokta = a_kotla()
        kotlar = [kot_metni(k) for k in A_DURAKLAR]
        kotlar[3] = kot_metni(A_DURAKLAR[3], ondalik=".")
        self.assertEqual(kotlar[3], "+3.20")
        nokta["asansorler"][0]["durak_kotlari"] = "; ".join(kotlar)
        self.turetilen_degerler(hesap(nokta), A_BEKLENEN, '"+3.20"')
        with self.subTest(yan="hesap"):
            self.assertEqual(farklar(rapor(hesap(virgul)), rapor(hesap(nokta))), [])
        self.kayit_temiz(nokta, '"+3.20"')

    def test_kotla_giriste_olcu_kutulari_okunmaz(self):
        """Kotla girişte istekte kalan ( yanlış ) ölçü kutuları hiçbir şeyi değiştirmez."""
        temiz = a_kotla()
        kirli = a_kotla(
            seyir_mesafesi="99",
            durak_adedi="5",
            kat_yukseklikleri="3000; 3000; 3000; 3000",
            son_kat_yuksekligi="3900",
            kuyu_dibi="1200",
            tabliye_yuksekligi="900",
        )
        ht, hk = hesap(temiz), hesap(kirli)
        self.turetilen_degerler(hk, A_BEKLENEN, "eski ölçü kutuları")
        with self.subTest(yan="hesap"):
            self.assertEqual(farklar(rapor(ht), rapor(hk)), [])
        with self.subTest(yan="girdi"):
            self.assertEqual(farklar(girdi(ht), girdi(hk), azami=40), [])
        with self.subTest(yan="çizim ( SVG )"):
            ct, ck = cizim(temiz), cizim(kirli)
            self.assertTrue(ct.get("aktif"), iletiler(ct))
            self.assertEqual(
                [(x.get("ad"), x.get("svg")) for x in ct.get("cizimler") or []],
                [(x.get("ad"), x.get("svg")) for x in ck.get("cizimler") or []],
            )
        self.kayit_temiz(kirli, "eski ölçü kutuları")

    def test_olcuyle_giriste_kot_kutulari_okunmaz(self):
        """Ölçüyle girişte ( durak kotları boş ) kot kutuları okunmaz."""
        temiz = a_olcuyle()
        kirli = a_olcuyle(kuyu_dibi_kotu="−99,00", kuyu_tavani_kotu="+99,00", md_zemini_kotu="+50,00")
        ht, hk = hesap(temiz), hesap(kirli)
        self.turetilen_degerler(ht, A_BEKLENEN, "63444-2 ölçüyle")
        with self.subTest(yan="hesap"):
            self.assertEqual(farklar(rapor(ht), rapor(hk)), [])
        with self.subTest(yan="türetilenler"):
            #  istekteki ham kot kutuları girdi'de yankılanabilir:  türetilenler aynı
            ad = (
                "durak_adedi",
                "seyir_mesafesi",
                "kat_yukseklikleri",
                "kuyu_dibi",
                "son_kat_yuksekligi",
                "tabliye_yuksekligi",
                "kuyu_boyu",
            )
            self.assertEqual({k: girdi(ht).get(k) for k in ad}, {k: girdi(hk).get(k) for k in ad})
        self.kayit_temiz(kirli, "ölçüyle + eski kot kutuları")

    def test_makine_dairesi_zemini_bossa_tabliye_1200(self):
        #  Sözleşme:  md_zemini_kotu boşsa tabliye varsayılanı 1.200
        v = a_kotla(md_zemini_kotu="")
        self.turetilen_degerler(hesap(v), {**A_BEKLENEN, "tabliye": 1200}, "MD zemini boş")

    def test_tavan_dosemesi_bossa_duvar_kalinligi(self):
        #  Sözleşme:  tavan_dosemesi boşsa kuyu_duvar_kalinligi ( 250 ):
        #  tabliye = ( +62,20 + 0,25 ) − ( +60,80 ) = 1.650
        v = a_kotla(tavan_dosemesi="")
        self.turetilen_degerler(hesap(v), {**A_BEKLENEN, "tabliye": 1650}, "tavan döşemesi boş")

    def test_makine_dairesizde_md_zemini_okunmaz(self):
        #  Sözleşme:  md_zemini_kotu yalnız daireli projede okunur.  Dairesiz
        #  BAR 2515'te kalan bir zemin kotu ( tavandan da yukarıda ) hiçbir şeyi
        #  değiştirmez, hesabı durdurmaz.
        temiz, kirli = b_kotla(), b_kotla(md_zemini_kotu="+99,00")
        self.turetilen_degerler(hesap(kirli), B_BEKLENEN, "dairesizde MD zemini")
        with self.subTest(yan="hesap"):
            self.assertEqual(farklar(rapor(hesap(temiz)), rapor(hesap(kirli))), [])


#  ═══════════════════════════════════════════════════════════════════════════
#  B2  ÇİZİM = TABLO  ( 63444-2'nin DXF'i )
#  ═══════════════════════════════════════════════════════════════════════════


class B2CizimTablo(_Ortak):
    @classmethod
    def setUpClass(cls):
        cls.v = a_kotla()
        cls.doc = dxf(cls.v)

    def setUp(self):
        self.assertNotIsInstance(self.doc, dict, paket_iletisi(self.doc))

    def test_paket_temiz(self):
        self.kayit_temiz(self.v, "63444-2 paketi")

    def test_kesitlerin_kot_yazilari_girilen_kotlar(self):
        girilen = set(A_PAFTA_KOTLARI)
        for kesit, _e, _a in KESITLER:
            b = blok(self.doc, kesit)
            with self.subTest(kesit, denetim="blok var"):
                self.assertIsNotNone(b)
            if b is None:
                continue
            kotlar = kot_yazilari(b)
            bulunan = {k for k, *_ in kotlar}
            with self.subTest(kesit, denetim="yabancı kot yok"):
                self.assertEqual(sorted(bulunan - girilen), [])
            with self.subTest(kesit, denetim="uç kotlar var"):
                self.assertEqual(sorted(A_UCLAR - bulunan), [])
            with self.subTest(kesit, denetim="biçim:  iki ondalık · ±0,00 · +3,20 · -7,00"):
                self.assertEqual([m for k, *_, m in kotlar if m != pafta_kotu(k)], [])

    def test_kapi_gorunusleri_en_alt_durak(self):
        for ad in KAPI_GORUNUSLERI:
            b = blok(self.doc, ad)
            with self.subTest(ad):
                self.assertIsNotNone(b)
                self.assertEqual(sorted({m for *_, m in kot_yazilari(b)}), [pafta_kotu(A_DURAKLAR[0])])

    def test_kot_yazilari_dogru_yukseklikte(self):
        """Kırığı açılmış yükseklik ( mm ) − ( kot − en alt durak ) bütün kot
        yazılarında AYNI pay:  iki yazının düşey uzaklığı iki kotun farkıdır."""
        alt = A_DURAKLAR[0]
        yukseklik = {}
        for kesit, etiket, alan in KESITLER:
            b = blok(self.doc, kesit)
            s = olcek(b, etiket, int(self.v["asansorler"][0][alan]))
            with self.subTest(kesit, denetim="ölçek ( plan ölçüsünden )"):
                self.assertIsNotNone(s)
                self.assertAlmostEqual(s, 1.0, places=6)  # blok gerçek mm'de
            kirik = kiriklar(b, s)
            with self.subTest(kesit, denetim="kesit kırık ( 71 m kuyu )"):
                self.assertTrue(kirik)
            u = acici(kirik)
            paylar = {}
            for k, _x, y, metin in kot_yazilari(b):
                uy = u(y)
                with self.subTest(kesit, kot=metin, denetim="yazı kırığın dışında"):
                    self.assertIsNotNone(uy)
                if uy is not None:
                    paylar[metin] = round(uy / s - (k - alt), 1)
                    yukseklik.setdefault(metin, set()).add(round(y, 1))
            with self.subTest(kesit, denetim="bütün kot yazıları aynı payla kendi seviyesinde"):
                self.assertTrue(paylar)
                self.assertLessEqual(max(paylar.values()) - min(paylar.values()), 1.0, paylar)
            with self.subTest(kesit, denetim="yazı kendi seviyesinin yanında ( iç 0 = en alt durak )"):
                self.assertTrue(all(abs(c) <= 500 for c in paylar.values()), paylar)
        with self.subTest(denetim="aynı kot iki kesitte aynı yükseklikte"):
            self.assertEqual({m: ys for m, ys in yukseklik.items() if len(ys) > 1}, {})


#  ═══════════════════════════════════════════════════════════════════════════
#  B3  HESAP = ÇİZİM  ( 63444-2 )
#  ═══════════════════════════════════════════════════════════════════════════


class B3HesapCizim(_Ortak):
    @classmethod
    def setUpClass(cls):
        cls.v = a_kotla()
        cls.h = hesap(cls.v)
        cls.doc = dxf(cls.v)

    def setUp(self):
        self.assertNotIsInstance(self.doc, dict, paket_iletisi(self.doc))
        self.assertTrue(girdi(self.h), hesap_iletileri(self.h))

    def _kesit(self, kesit, etiket, alan):
        b = blok(self.doc, kesit)
        s = olcek(b, etiket, int(self.v["asansorler"][0][alan]))
        u = acici(kiriklar(b, s))
        y = {k: yy for k, _x, yy, _m in kot_yazilari(b)}
        return b, s, u, y

    def test_seyir_ky_son_kat_kuyu_boyu(self):
        g = girdi(self.h)
        for kesit, etiket, alan in KESITLER:
            b, s, u, y = self._kesit(kesit, etiket, alan)
            duraklar = [k for k in y if k in A_DURAKLAR]
            alt, ust = min(duraklar), max(duraklar)

            def ara(k0, k1, u=u, y=y, s=s):
                return (u(y[k1]) - u(y[k0])) / s

            seyir = ara(alt, ust)
            ky = ara(A_KUYU_TABANI, alt)
            #  son kat:  tavan döşemesinin ALTI = tabliyenin üstü − döşeme ( 100, kaynak )
            son_kat = ara(ust, A_KUYU_USTU) - A_TABLIYE_BETONU
            with self.subTest(kesit, alan="seyir ( H )"):
                self.assertAlmostEqual(seyir, g["seyir_mesafesi"] * 1000, delta=0.5)
            with self.subTest(kesit, alan="KY"):
                self.assertAlmostEqual(ky, g["kuyu_dibi"], delta=0.5)
                self.assertIn(round(g["kuyu_dibi"], 1), olculer(b))
            with self.subTest(kesit, alan="son kat"):
                self.assertAlmostEqual(son_kat, g["son_kat_yuksekligi"], delta=0.5)
                self.assertIn(round(g["son_kat_yuksekligi"], 1), olculer(b))
            with self.subTest(kesit, alan="kuyu boyu"):
                self.assertAlmostEqual(ky + seyir + son_kat, g["kuyu_boyu"], delta=0.5)
            with self.subTest(kesit, alan="ölçü yazıları hesabın seyri ve kuyu boyu"):
                sayilar = olcu_yazisindaki_sayilar(b)
                self.assertIn(round(g["seyir_mesafesi"] * 1000), sayilar)
                self.assertIn(round(g["kuyu_boyu"]), sayilar)

    def test_ray_boyu(self):
        """Hesabın ray boyu ( özet;  raporda "ÇİZİMDEN · en uzun kabin rayı" ) =
        çizilen en uzun ray;  ray kuyunun içinde ( kaynağın kuyu dibi ve tavanı )."""
        ray_boyu = asansor(self.h)["ozet"]["ray_boyu"]  # m
        alt = A_DURAKLAR[0]
        for kesit, etiket, alan in KESITLER:
            b, s, u, _y = self._kesit(kesit, etiket, alan)
            uclar = [(u(a), u(c)) for a, c in ray_uclari(b)]
            with self.subTest(kesit, denetim="ray uçları kırığın dışında"):
                self.assertTrue(uclar)
                self.assertTrue(all(a is not None and c is not None for a, c in uclar), uclar)
            uclar = [(a / s, c / s) for a, c in uclar if a is not None and c is not None]
            if not uclar:
                continue
            with self.subTest(kesit, denetim="en uzun ray = hesabın ray boyu"):
                #  rapor ray boyunu cm'yle yazar ( "70,80 m" ):  yarım cm pay
                self.assertAlmostEqual(max(c - a for a, c in uclar), ray_boyu * 1000, delta=5)
            with self.subTest(kesit, denetim="ray kuyu dibinin üstünde, tavanın altında"):
                self.assertGreaterEqual(min(alt + a for a, _c in uclar), A_KUYU_TABANI - 0.5)
                self.assertLessEqual(max(alt + c for _a, c in uclar), A_KUYU_TAVANI + 0.5)


#  ═══════════════════════════════════════════════════════════════════════════
#  B4  İKİZ VE KAYMA
#  ═══════════════════════════════════════════════════════════════════════════

KAYMALAR = (10000, 850000)  # +10,00 ve mutlak kot +850 m


class B4IkizVeKaymaHesap(_Ortak):
    def test_kotla_olcuyle_ikizi_ayni_hesap(self):
        for ad, v, ikiz, _bek in kaynak_ciftleri():
            with self.subTest(ad):
                self.assertEqual(farklar(rapor(hesap(v)), rapor(hesap(ikiz))), [])
            self.kayit_temiz(ikiz, f"{ad} ikizi")

    def test_butun_kotlar_kayinca_hesap_ayni(self):
        for kayma in KAYMALAR:
            with self.subTest("63444-2", kayma=pafta_kotu(kayma)):
                self.assertEqual(farklar(rapor(hesap(a_kotla())), rapor(hesap(a_kotla(kayma)))), [])
            self.kayit_temiz(a_kotla(kayma), pafta_kotu(kayma))
        #  Makine dairesiz yol da ( BAR 2515;  en alt durak ±0,00 → +10,00 )
        with self.subTest("BAR 2515", kayma=pafta_kotu(KAYMALAR[0])):
            self.assertEqual(farklar(rapor(hesap(b_kotla())), rapor(hesap(b_kotla(KAYMALAR[0])))), [])


class B4IkizVeKaymaCizim(_Ortak):
    @classmethod
    def setUpClass(cls):
        cls.taban = dxf(a_kotla())
        cls.ikiz = dxf(a_olcuyle())
        cls.kayik = {k: dxf(a_kotla(k)) for k in KAYMALAR}

    def setUp(self):
        for d in (self.taban, self.ikiz, *self.kayik.values()):
            self.assertNotIsInstance(d, dict, paket_iletisi(d))

    def _kotlar(self, doc, konumlu):
        cikti = {}
        for ad, b in cizim_bloklari(doc).items():
            for k, x, y, m in kot_yazilari(b):
                cikti.setdefault(ad, Counter())[(k, _r(x), _r(y)) if konumlu else k] += 1
                self.assertEqual(m, pafta_kotu(k), (ad, m))
        return cikti

    def _kaydir(self, kotlar, kayma, konumlu):
        return {
            ad: Counter({((k[0] + kayma, *k[1:]) if konumlu else k + kayma): n for k, n in c.items()})
            for ad, c in kotlar.items()
        }

    def test_ikizin_cizimleri_ayni_geometri(self):
        #  B4 / 2.2 f:  veri tablosu kot notu yüzünden ayrı denetlenir ( aşağıda );
        #  öteki bütün çizimler, model uzayı ve blok yerleşimleri birebir
        self.assertEqual(geometri_farki(self.taban, self.ikiz, haric=YAZI_TABLOLARI), [])

    def test_ikizin_veri_tablosu_yalniz_kot_notu(self):
        """B4 / 2.2 f:  ikizin veri tablosu yalnız kot notunun satırıyla ( ve onun
        büyüttüğü / kaydırdığı kadar ) farklı;  not çıkarılınca birebir aynı."""
        self.assertEqual(veri_tablosu_farki(self.taban, self.ikiz), [])

    def test_ikizin_kot_yazilari_en_alt_durak_sifir(self):
        #  Ölçüyle girişte en alt durak ±0,00:  ikizin kotları = kotlanın + 7,00
        kayma = 0 - A_DURAKLAR[0]
        self.assertEqual(
            self._kotlar(self.ikiz, False), self._kaydir(self._kotlar(self.taban, False), kayma, False)
        )

    def test_kayinca_geometri_ayni(self):
        for kayma, doc in self.kayik.items():
            with self.subTest(kayma=pafta_kotu(kayma)):
                self.assertEqual(geometri_farki(self.taban, doc), [])

    def test_kayinca_kot_disi_yazilar_ayni(self):
        for kayma, doc in self.kayik.items():
            for ad, b in cizim_bloklari(self.taban).items():
                with self.subTest(pafta_kotu(kayma), blok=ad):
                    y1, y2 = kot_disi_yazilar(b), kot_disi_yazilar(blok(doc, ad))
                    self.assertEqual((sorted((y1 - y2).elements()), sorted((y2 - y1).elements())), ([], []))

    def test_kayinca_kot_yazilari_kayik(self):
        #  +10,00:  içerik kayık, konum aynı.  +850 m:  yazılar uzar, yerleştirici
        #  yer açabilir — yalnız içerik
        for kayma, doc in self.kayik.items():
            konumlu = kayma == 10000
            with self.subTest(kayma=pafta_kotu(kayma), konumlu=konumlu):
                self.assertEqual(
                    self._kotlar(doc, konumlu),
                    self._kaydir(self._kotlar(self.taban, konumlu), kayma, konumlu),
                )


#  ═══════════════════════════════════════════════════════════════════════════
#  B5  HATALI TABLOLAR — hesap durur, çizim AYNI iletiyle durur
#  ═══════════════════════════════════════════════════════════════════════════


def _a_ile(**degis):
    v = a_kotla()
    v["asansorler"][0].update(degis)
    return v


def _duraklar(*kotlar):
    return "; ".join(kot_metni(k) for k in kotlar)


#  Sözleşmenin hatalı tabloları ( 63444-2'nin kotlarında tek bir bozukluk )
HATALI_TABLOLAR = (
    ("sırasız duraklar", {"durak_kotlari": _duraklar(-7000, 0, -3500, *A_DURAKLAR[3:])}),
    ("aynı kotta iki durak", {"durak_kotlari": _duraklar(-7000, -3500, -3500, *A_DURAKLAR[2:])}),
    ("tek durak", {"durak_kotlari": _duraklar(-7000)}),
    ("kuyu dibi en alt durağın kotunda", {"kuyu_dibi_kotu": kot_metni(-7000)}),
    ("kuyu dibi en alt duraktan yukarıda", {"kuyu_dibi_kotu": kot_metni(-6000)}),
    ("kuyu tavanı en üst durağın kotunda", {"kuyu_tavani_kotu": kot_metni(57600)}),
    ("kuyu tavanı en üst duraktan aşağıda", {"kuyu_tavani_kotu": kot_metni(55000)}),
    #  tabliyenin üstü = +62,20 + 0,10 = +62,30;  zemin onun 100 mm üstünde
    ("makine dairesi zemini tabliyenin üstünden yukarıda", {"md_zemini_kotu": kot_metni(62400)}),
    ("kuyu dibi kotu boş", {"kuyu_dibi_kotu": ""}),
    ("kuyu tavanı kotu boş", {"kuyu_tavani_kotu": ""}),
)
#  Okunamayan kot:  kapıda reddedilir, ileti alanın adını taşır
OKUNAMAYAN = (
    ("kuyu_dibi_kotu", "8,80m"),
    ("durak_kotlari", _duraklar(-7000, -3500) + "; ±0,0x; " + _duraklar(*A_DURAKLAR[3:])),
)


class B5HataliTablolar(_Ortak):
    def _durur(self, ad, v):
        h, c = hesap(v), cizim(v)
        with self.subTest(ad, yan="hesap durur"):
            self.assertFalse(
                hesap_aktif(h),
                {
                    k: girdi(h).get(k)
                    for k in ("durak_adedi", "seyir_mesafesi", "kuyu_dibi", "son_kat_yuksekligi")
                },
            )
        with self.subTest(ad, yan="çizim durur"):
            self.assertFalse(c.get("aktif"), f"{len(c.get('cizimler') or [])} çizim")
        with self.subTest(ad, yan="çizimin iletisi hesabın iletileri arasında"):
            ci, hi = iletiler(c), hesap_iletileri(h)
            self.assertTrue(ci, "çizim iletisiz durdu")
            for m in ci:
                self.assertIn(m, hi)
        with self.subTest(ad, yan="paket ( DXF ) inmez, ileti aynı"):
            p = dxf(v)
            self.assertIsInstance(p, dict, "hatalı tabloyla pafta indi")
            self.assertFalse(p.get("aktif"))
            self.assertTrue(iletiler(p), "paket iletisiz durdu")
            for m in iletiler(p):
                self.assertIn(m, hi)
        self.kayit_temiz(v, ad)
        return h, c

    def test_hatali_tablo_durdurur(self):
        for ad, degis in HATALI_TABLOLAR:
            self._durur(ad, _a_ile(**degis))

    def test_okunamayan_kot_kapida_alanin_adiyla(self):
        etiket = {
            f["anahtar"]: f["etiket"] for gr in uygulama_istegi.alanlar()["gruplar"] for f in gr["alanlar"]
        }
        for alan, deger in OKUNAMAYAN:
            adi = etiket[alan].split("  (")[0].strip()
            h, c = self._durur(f"okunamayan {alan}", _a_ile(**{alan: deger}))
            with self.subTest(alan, yan="hesabın iletisi alanın adını taşır"):
                self.assertTrue(any(adi in m for m in hesap_iletileri(h)), (adi, hesap_iletileri(h)))
            with self.subTest(alan, yan="çizimin iletisi alanın adını taşır"):
                self.assertTrue(any(adi in m for m in iletiler(c)), (adi, iletiler(c)))

    def test_noktali_uc_ondalik_belirsiz(self):
        """2.2 d:  noktalı üç ondalık ( "+2.834" — bin iki yüz gibi de okunur )
        belirsizdir:  hesap ve çizim AYNI iletiyle durur, ileti aynı kotun virgüllü
        yazımını ( "+2,834" ) anar.  ( Ondalık okunsaydı dizi sıralı kalırdı;  binlik
        okunsaydı ileti sırayı söylerdi — ikisi de bulgudur. )"""
        kotlar = [kot_metni(k) for k in A_DURAKLAR]
        kotlar[3] = "+2.834"
        h, c = self._durur('noktalı üç ondalık "+2.834"', _a_ile(durak_kotlari="; ".join(kotlar)))
        with self.subTest(yan="hesabın iletisi virgüllü yazımı anar"):
            self.assertTrue(any("+2,834" in m for m in hesap_iletileri(h)), hesap_iletileri(h))
        with self.subTest(yan="çizimin iletisi virgüllü yazımı anar"):
            self.assertTrue(any("+2,834" in m for m in iletiler(c)), iletiler(c))


#  ═══════════════════════════════════════════════════════════════════════════
#  B6  DOSYA GİDİŞ-DÖNÜŞÜ — paketin ZIP'inde proje dosyası varsa
#  ═══════════════════════════════════════════════════════════════════════════


class B6ProjeDosyasi(_Ortak):
    def test_paketteki_proje_dosyasinda_kotlar_yazildigi_gibi(self):
        """Proje dosyası paketteyse kotlar orada mimarın yazdığı gibi ( "−7,00" )
        kalır;  yoksa kapsam dışı ( ön yüzün dosyası — uçtan uca testi ), bulgu değil."""
        v = a_kotla()
        dxf(v)
        adlar, proje = _PAKET.get(_anahtar("dxf", v), ([], {}))
        if not proje:
            self.skipTest(f"kapsam dışı:  ön yüzün dosyası ( paketin ZIP'inde proje dosyası yok:  {adlar} )")
        a = v["asansorler"][0]
        yazilan = [a["durak_kotlari"], a["kuyu_dibi_kotu"], a["kuyu_tavani_kotu"], a["md_zemini_kotu"]]
        for ad, metin in proje.items():
            try:
                icerik = list(_metinler(json.loads(metin)))
            except ValueError:
                icerik = [metin]
            for k in yazilan:
                with self.subTest(ad, kot=k):
                    self.assertTrue(any(k in t for t in icerik))


if __name__ == "__main__":
    unittest.main()

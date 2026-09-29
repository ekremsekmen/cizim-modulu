# -*- coding: utf-8 -*-
"""
API ORTAK KATMANI

İki proje türünün de kullandığı yardımcılar:  metin → sayı çevirme, belirsiz
yazım denetimi, proje kimliği, dosya adı ve indirme yanıtı.

Buradaki hiçbir şey hesap YAPMAZ;  hesap motorları engine/ altındadır.
"""
import json
import math
import os
import re
import threading

from fastapi.responses import JSONResponse, Response

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BELIRSIZ_SAYI = re.compile(r"^[+-]?[1-9]\d{0,2}[.,]\d{3}$")

def belirsiz_sayi_mi(x) -> bool:
    if not isinstance(x, str):
        return False
    return bool(BELIRSIZ_SAYI.match(x.strip().replace(" ", "").replace("\u00a0", "")))


def _sayi(x):
    """
    Metni sayıya çevirir.  Kabul edilen biçimler:
        "1,60"  "1.60"  "1.234,56"  "1,234.56"  "  3  "  12  3.0
    Geçersiz, boş, sonsuz, NaN veya BELİRSİZ değerlerde None döner —
    bu sayede bozuk girdi hesabı çökertmez, "eksik girdi" olarak işlenir.
    """
    if x is None or isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        return x if math.isfinite(x) else None
    if not isinstance(x, str):
        return None
    s = x.strip().replace(" ", "").replace("\u00a0", "")
    if s == "":
        return None
    if BELIRSIZ_SAYI.match(s):        # "1.200" / "1,200" → hangisi belli değil
        return None
    # Hangi ayraç SONDA ise ondalık ayracıdır; diğeri binlik ayracıdır.
    son_virgul, son_nokta = s.rfind(","), s.rfind(".")
    if son_virgul >= 0 and son_nokta >= 0:
        if son_virgul > son_nokta:                    # 1.234,56  → TR biçimi
            s = s.replace(".", "").replace(",", ".")
        else:                                         # 1,234.56  → EN biçimi
            s = s.replace(",", "")
    elif son_virgul >= 0:
        s = s.replace(",", ".")                       # 1,60
    try:
        f = float(s)
    except ValueError:
        return None
    if not math.isfinite(f):                          # inf / -inf / nan
        return None
    if abs(f) > 1e12:                                 # anlamsız büyüklükler
        return None
    return int(f) if f.is_integer() else f


#  Belirsiz yazılmış alanların adları burada toplanır ki kullanıcıya
#  "eksik girdi" yerine gerçek sebep söylenebilsin.
#
#  İSTEK BAŞINA AYRI LİSTE:  FastAPI'de `def` ( async olmayan ) uç noktalar bir
#  iş parçacığı havuzunda koşar, yani İKİ İSTEK AYNI ANDA çalışabilir.  Ortak
#  bir liste kullanılsaydı biri listeyi temizlerken diğeri okuyabilir ve
#  geçerli bir indirme "belirsiz sayı" diye reddedilebilir ya da tersi, bozuk
#  bir girdi denetimden kaçabilirdi.  ( Ekran her tuş vuruşunda hesap
#  isterken indirmeye basılması bu iki isteği gerçekten çakıştırır. )
class _BelirsizListesi(threading.local):
    def __init__(self):
        self.kalemler = []

    def clear(self):
        self.kalemler = []

    def append(self, x):
        self.kalemler.append(x)

    def __bool__(self):
        return bool(self.kalemler)

    def __iter__(self):
        return iter(self.kalemler)


_BELIRSIZ = _BelirsizListesi()
#  BELİRSİZLİKTEN BAŞKA SEBEPLE REDDEDİLEN GİRDİLER ( negatif miktar, seçilmemiş
#  kalem … ).  Ayrı tutulur çünkü belirsiz-sayı açıklaması ( "binlik ayracı mı
#  ondalık mı" ) bunlar için YANLIŞ olur.
_RED = _BelirsizListesi()


def _bos_mu(ham) -> bool:
    """Alan doldurulmamış mı?  ( yok · boş · yalnız boşluk )"""
    return ham is None or (isinstance(ham, str) and not ham.strip())


def _sayi_oku(ham, etiket):
    """KULLANICININ YAZDIĞI bir sayıyı okur  —  okuyamazsa SEBEBİNİ kaydeder.

        boş                →  None   ( alan doldurulmamış — varsayılan / eksik )
        belirsiz yazım     →  None + _BELIRSIZ
        okunamayan yazım   →  None + _RED

    Okunamayan yazım BOŞ sayılmaz:  "1000 kg" yazılmış anma yükü sessizce
    None'a düşüyor, motor da tablodaki yükle hesap yapıyordu — kullanıcı
    yazdığı sayının kullanılmadığını hiçbir yerde görmüyordu.  Çağıran taraf
    reddedilen girdi varken hesap yapmaz ( bkz. _belirsiz_hata ).
    """
    if _bos_mu(ham):
        return None
    if belirsiz_sayi_mi(ham):
        _BELIRSIZ.append(f"{etiket} = {str(ham).strip()}")
        return None
    d = _sayi(ham)
    if d is None:
        _RED.append(f"{etiket} = {str(ham).strip()[:20]}  ( sayı değil )")
    return d


def _temiz(d: dict, sayisal: tuple, on_ek: str = "", etiket=None) -> dict:
    """``sayisal`` alanlarını sayıya çevirir;  ``etiket`` red metnindeki adlar."""
    etiket = etiket or {}
    out = dict(d or {})
    for k in sayisal:
        out[k] = _sayi_oku(out.get(k), f"{on_ek}{etiket.get(k, k)}")
    return out


def _sabitler_coz(ham, metin=(), etiket=None):
    """Ofis standardı ( Sabitler sekmesi )  —  ham metinler → motorun sözlüğü.

    İKİ PROJE AYNI KURALLA OKUR.  Avan tarafı her değere _sayi() uyguluyordu:
    "1.200" ( belirsiz ) ve "abc" ( sayı değil ) sessizce None'a düşüyor,
    motor da varsayılanı kullanıyordu — β = 1.200 yazan kullanıcının
    topraklama direnci 150 Ω·m ile hesaplanıyordu.  Kablo tipine yazılan
    "NYY" de aynı yoldan NHXMH FE180'e dönüyordu.

        metin alanı       →  metin kalır
        boş               →  yazılmaz ( varsayılan )
        belirsiz yazım    →  _BELIRSIZ ( hesap durur, sebebi söylenir )
        okunamayan yazım  →  _RED      ( hesap durur, sebebi söylenir )
    """
    etiket = etiket or (lambda k: k)
    out = {}
    for k, x in (ham if isinstance(ham, dict) else {}).items():
        if k in metin:
            m = "" if x is None else str(x).strip()
            if m:
                out[k] = m
            continue
        d = _sayi_oku(x, etiket(k))
        if d is not None:
            out[k] = d
    return out


def _belirsiz_hata():
    """Reddedilen girdi varsa açık hata metni, yoksa None."""
    if _BELIRSIZ:
        liste = "  ·  ".join(sorted(set(_BELIRSIZ.kalemler))[:6])
        return ("HESAP HATASI: Belirsiz sayı yazımı  —  " + liste +
                "   ·   Bu yazımda binlik ayracı mı ondalık ayracı mı olduğu "
                "anlaşılmıyor ( Türkçede 1.200 = bin iki yüz, 1,200 = bir virgül iki; "
                "program ikisini de ondalık kabul ediyor ). Binlik ayracı KULLANMAYIN: "
                "bin iki yüz için 1200, bir virgül iki için 1,2 yazın.")
    if _RED:
        return ("HESAP HATASI: Girdi kabul edilmedi  —  "
                + "  ·  ".join(sorted(set(_RED.kalemler))[:6])
                + "   ·   Satırı düzeltin ya da kaldırın; sessizce yok sayılmaz.")
    return None


def _sozluk_listesi(x):
    """Yalnız sözlük öğelerini geçiren güvenli liste — bozuk gövdede çökmez."""
    if not isinstance(x, (list, tuple)):
        return []
    return [e for e in x if isinstance(e, dict)]


def _proje_kimligi(veri):
    """
    KAPAK SEKMESİNDEKİ PROJE ADI  →  indirilen dosyanın adı.

    Bu bağlanmadan önce her indirme aynı adla iniyordu:  aynı klasördeki iki
    projenin dosyaları birbirinden ayırt edilemiyor, ikincisi "(1)" olarak
    kaydediliyordu.  Pafta içeriği değişmez — proje adı yalnız KAPAK
    sayfasında yazılıdır.
    """
    k = veri.get("kapak") if isinstance(veri.get("kapak"), dict) else {}
    return {"proje_adi": str(k.get("project_title") or "").strip()}


def _dosya_adi(proje, ek, uzanti):
    ad = (proje or {}).get("proje_adi") or "Asansor"
    ad = "".join(c for c in str(ad) if c.isalnum() or c in " -_")[:48].strip() or "Asansor"
    return f"{ad} - {ek}.{uzanti}"


def _indir(icerik: bytes, ad: str, tur: str):
    from urllib.parse import quote
    return Response(icerik, media_type=tur, headers={
        "Content-Disposition": f"attachment; filename*=UTF-8''{quote(ad)}"})


#  "Projeyi paketle":  teslim paketi ile GERİ DÖNÜŞ NOKTASI aynı arşivde.
#  Çıktılar ( PDF · DXF/DWG ) projeyi anlatır, proje dosyası ise onu geri
#  getirir.  İkisi ayrı yerlerde durursa arşivden dönmek imkânsızlaşır.
PROJE_UZANTI = {"avan": ".avan", "uygulama": ".uygulama"}


def _paket_ekleri(veri, mod):
    """ZIP'e konacak ek dosyalar — [ ( ad, bayt ) ].

    Arayüz proje dosyasının gövdesini ``proje_dosyasi`` alanında yollar;
    sunucu onu OLDUĞU GİBİ pakete koyar.  Biçimi arayüz belirler ( tek
    kaynak orasıdır ), sunucu yalnız taşır.
    """
    ekler = []
    govde = (veri or {}).get("proje_dosyasi")
    if isinstance(govde, dict) and govde:
        ad = _dosya_adi(_proje_kimligi(veri), "", "").rstrip(" -.") or "Asansor"
        ekler.append((ad + PROJE_UZANTI.get(mod, ".avan"),
                      json.dumps(govde, ensure_ascii=False, indent=1).encode("utf-8")))
    return ekler


def _uretilemedi(e: Exception):
    """
    Dosya üretilemediğinde JSON hata döndürür.  Arayüz Content-Type'a bakarak
    bunu bozuk bir dosya olarak indirmek yerine ekranda mesaj olarak gösterir.
    """
    return JSONResponse({"hata": f"DOSYA ÜRETİLEMEDİ — {e}"}, status_code=422)



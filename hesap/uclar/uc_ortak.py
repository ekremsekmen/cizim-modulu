# -*- coding: utf-8 -*-
"""
API ORTAK KATMANI

İki proje türünün de kullandığı yardımcılar:  metin → sayı çevirme, belirsiz
yazım denetimi, proje kimliği, dosya adı ve indirme yanıtı.

Buradaki hiçbir şey hesap YAPMAZ;  hesap motorları engine/ altındadır.
"""

import asyncio
import base64
import json
import logging
import math
import os
import re
import threading
import time
import zlib

from fastapi.responses import JSONResponse, Response, StreamingResponse
from starlette.concurrency import run_in_threadpool
from urllib.parse import quote, unquote

from cizim import asamalar

#  Bağlantının kapanıp kapanmadığına bakma aralığı ( sn;  bir sınama ~0,1 – 1 sn )
BAGLANTI_ARALIGI = 0.25


async def baglantiyi_izle(istek, birakildi):
    """İstemci bağlantıyı kapatınca ( ekran isteği bıraktı ) birakildi ( threading.Event ) kurulur:
    iş parçacığındaki uzun iş ( seçici — avan_secici.korumali ) ona bakıp durur.  Görev olarak
    koşar;  iş bitince çağıran olayı kurar ve görevi iptal eder.  AKIŞLI YANITTA KULLANILMAZ
    ( orada Starlette kopmayı kendisi dinler — akisli_yanit )."""
    while not birakildi.is_set():
        if await istek.is_disconnected():
            birakildi.set()
            return
        await asyncio.sleep(BAGLANTI_ARALIGI)


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
        try:
            return x if math.isfinite(x) else None
        except OverflowError:  # JSON'da 400 basamaklı tam sayı:  float'a sığmaz
            return None
    if not isinstance(x, str):
        return None
    s = x.strip().replace(" ", "").replace("\u00a0", "")
    if s == "":
        return None
    if BELIRSIZ_SAYI.match(s):  # "1.200" / "1,200" → hangisi belli değil
        return None
    # Hangi ayraç SONDA ise ondalık ayracıdır; diğeri binlik ayracıdır.
    son_virgul, son_nokta = s.rfind(","), s.rfind(".")
    if son_virgul >= 0 and son_nokta >= 0:
        if son_virgul > son_nokta:  # 1.234,56  → TR biçimi
            s = s.replace(".", "").replace(",", ".")
        else:  # 1,234.56  → EN biçimi
            s = s.replace(",", "")
    elif son_virgul >= 0:
        s = s.replace(",", ".")  # 1,60
    try:
        f = float(s)
    except ValueError:
        return None
    if not math.isfinite(f):  # inf / -inf / nan
        return None
    if abs(f) > 1e12:  # anlamsız büyüklükler
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
        return (
            "HESAP HATASI: Belirsiz sayı yazımı  —  "
            + liste
            + "   ·   Bu yazımda binlik ayracı mı ondalık ayracı mı olduğu "
            "anlaşılmıyor ( Türkçede 1.200 = bin iki yüz, 1,200 = bir virgül iki; "
            "program ikisini de ondalık kabul ediyor ). Binlik ayracı KULLANMAYIN: "
            "bin iki yüz için 1200, bir virgül iki için 1,2 yazın."
        )
    if _RED:
        return (
            "HESAP HATASI: Girdi kabul edilmedi  —  "
            + "  ·  ".join(sorted(set(_RED.kalemler))[:6])
            + "   ·   Satırı düzeltin ya da kaldırın; sessizce yok sayılmaz."
        )
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

    return Response(
        icerik, media_type=tur, headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(ad)}"}
    )


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
        ekler.append(
            (
                ad + PROJE_UZANTI.get(mod, ".avan"),
                json.dumps(govde, ensure_ascii=False, indent=1).encode("utf-8"),
            )
        )
    return ekler


GENEL_HATA = (
    "beklenmeyen bir hata oluştu ve kayda geçti — girdileri kontrol edip yeniden deneyin;  sürerse bildirin."
)


def _girdi_reddi_mi(e: Exception) -> bool:
    """Girdiden doğan ret ( ValueError ) mi?  Metin kodlama hatası ( UnicodeError —
    yarım vekil karakterli ad — o da bir ValueError ) Python'un cümlesidir, ret değildir."""
    return isinstance(e, ValueError) and not isinstance(e, UnicodeError)


def hata_iletisi(onek: str, e: Exception, ayrac: str = ": ") -> str:
    """Uçların genel except'inde kullanıcıya dönen ileti.  Girdiden doğan ret
    ( ValueError ) her zaman kendi metniyle;  programın kendi hatası web
    sunucusunda ( AVAN_SUNUCU — `main.py --sunucu` koyar ) genel iletiyle:
    Python'un metni ( "KeyError: 'x'" ) kullanıcıya bir şey söylemez, iç yapıyı
    gösterir.  Ayrıntı kayıtta ( hata_kaydi ).  Kendi bilgisayarında çalışırken
    metin eskisi gibi görünür ( 17 Eki )."""
    if _girdi_reddi_mi(e) or os.environ.get("AVAN_SUNUCU") != "1":
        return f"{onek}{ayrac}{e}"
    return f"{onek}{ayrac}{GENEL_HATA}"


def hata_kaydi(log: logging.Logger, e: Exception):
    """Uçların genel except'inde kayıt:  girdiden doğan ret ( ValueError — ör.
    "pafta çizilemiyor" ) bilgi düzeyinde, öbürü ( programlama hatası ) izle
    birlikte hata düzeyinde.  Kullanıcı yine iletiyi görür;  kayıt sunucuda
    sorunun nerede çıktığını söyler ( eskiden hiçbir yere yazılmıyordu )."""
    if _girdi_reddi_mi(e):
        log.info("uç girdiyi reddetti:  %s", e)
    else:
        log.error("uçta beklenmeyen hata — kullanıcıya ileti döndü", exc_info=e)


def _uretilemedi(e: Exception):
    """
    Dosya üretilemediğinde JSON hata döndürür.  Arayüz Content-Type'a bakarak
    bunu bozuk bir dosya olarak indirmek yerine ekranda mesaj olarak gösterir.
    """
    return JSONResponse({"hata": hata_iletisi("DOSYA ÜRETİLEMEDİ", e, " — ")}, status_code=422)


# ══════════════════════════════════════════════════════════════════════
#  AKIŞLI YANIT  —  uzun işin aşamaları satır satır, en sonda sonuç
# ══════════════════════════════════════════════════════════════════════
#  17 Kas avan aramasında başladı ( avan_cizim_uclari );  20 Kas genellendi:  paketler ve
#  düzeltme önerisi aynı sözleşmeyle konuşur.  İstek Accept'te AKIS_TURU'nü isterse her satır bir
#  JSON — { ilerleme:  { asamalar , sinama , gecen [ , plan ] } } … , sonda { sonuc:  ucun olağan
#  yanıtı }.  İstemiyorsa uç eskisi gibi tek yanıt verir ( testler, eski istemciler ).
#  İLERLEME AYRI BİR İSTEKLE SORULMAZ:  sunucu dört işçiyle çalışır, ikinci istek başka işçiye
#  düşerdi ( 17 Kas ) — ilerleme ve sonuç aynı yanıtta akar.
AKIS_TURU = "application/x-ndjson"
#  Satırlar en çok bu aralıkta bir ( sn ), yalnız yeni bir şey varsa …
ILERLEME_ARALIGI = 0.2
#  … ya da bu kadar sn yazılmadıysa:  uzun tek adımda ( PDF'ler, dar kuyuda arama ) vekil
#  sunucunun ( nginx / Caddy ) okuma zaman aşımı akışı kesmesin
CANLI_TUT = 10.0


def akis_isteniyor(istek):
    """İstek akışlı yanıt istiyor mu ( Accept )."""
    return AKIS_TURU in istek.headers.get("accept", "")


def akisli_yanit(istek, is_, ilerleme, birakildi):
    """is_'i ( argümansız, sonucu JSON'a dönüşen ) iş parçacığında ilerleme bağlamıyla koşar,
    aşamalarını akıtır.  SIKIŞTIRMA BURADA ( main'deki GZipMiddleware bu türü dışlar ):  ara katman
    küçük satırları biriktirirdi;  her satır gzip akışına yazılıp hemen boşaltılır ( Z_SYNC_FLUSH ).

    BAĞLANTI KAPANINCA ( ekran isteği bıraktı ) birakildi kurulur:  StreamingResponse kopmayı
    kendisi dinler ( ASGI 2.3 — uvicorn ) ve üreteci iptal eder.  Burada AYRICA is_disconnected
    yoklanmaz:  akış sürerken ikinci bir dinleyici bağlantıyı bozuyordu ( 17 Kas ).  İş, bir sonraki
    aşamada ( asamalar.Birakildi ) ya da kendi iptal yoklamasında ( seçici ) durur."""
    gz = "gzip" in istek.headers.get("accept-encoding", "")

    def calis():
        try:
            with asamalar.bagla(ilerleme):
                return is_()
        except asamalar.Birakildi:  # bağlantı kapandı:  sonucu okuyan yok
            return None

    async def satirlar():
        sikistir = zlib.compressobj(6, zlib.DEFLATED, 31) if gz else None

        def bayt(nesne, son=False):
            b = (json.dumps(nesne, ensure_ascii=False, default=str) + "\n").encode("utf-8")
            if sikistir is None:
                return b
            return sikistir.compress(b) + sikistir.flush(zlib.Z_FINISH if son else zlib.Z_SYNC_FLUSH)

        is_gorevi = asyncio.ensure_future(run_in_threadpool(calis))
        gonderilen, yazildi = -1, time.monotonic()
        try:
            while True:
                await asyncio.wait({is_gorevi}, timeout=ILERLEME_ARALIGI)
                if is_gorevi.done():
                    break
                surum, durum = ilerleme.durum()
                if surum != gonderilen or time.monotonic() - yazildi >= CANLI_TUT:
                    gonderilen, yazildi = surum, time.monotonic()
                    yield bayt({"ilerleme": durum})
            yield bayt({"sonuc": is_gorevi.result()}, son=True)
        finally:
            #  Bağlantı kapandıysa Starlette üreteci iptal eder ( buraya gelinir ):  iş durur
            birakildi.set()

    basliklar = {"Cache-Control": "no-store", "X-Accel-Buffering": "no"}
    if gz:
        basliklar.update({"Content-Encoding": "gzip", "Vary": "Accept-Encoding"})
    return StreamingResponse(satirlar(), media_type=AKIS_TURU, headers=basliklar)


def akis_sonucu(yanit):
    """Ucun yanıtı akıştaki sonuç satırı olarak:  JSON yanıt ( ret, hata ) olduğu gibi;  DOSYA
    { dosya:  { ad , tur , veri ( base64 ) } , notlar } — ad Content-Disposition'dan, notlar
    X-Avan-Not'tan ( akışsız yanıtta başlıkta taşınanlar ).  Akışta dosya %33 büyür ( base64 ),
    gzip bir kısmını geri alır;  paketler 0,6 – 1,7 MB."""
    tur = (yanit.media_type or "").split(";")[0]
    if tur == "application/json":
        return json.loads(yanit.body)
    ad = re.search(r"filename\*=UTF-8''([^;]+)", yanit.headers.get("content-disposition", ""))
    return {
        "dosya": {
            "ad": unquote(ad.group(1)) if ad else "",
            "tur": tur,
            "veri": base64.b64encode(yanit.body).decode("ascii"),
        },
        "notlar": [n for n in (yanit.headers.get("x-avan-not") or "").split(",") if n],
    }


#  PAKETİN ADIMLARI ( uygulama ve avan paketi — dxf_cikti.proje_paketi ):  ölçüldü 20 Kas, 4 asansör
#  10,4 sn — hesap sayfaları ( PDF + vektöre okuma + pafta DXF ) 3,6 · çizimler 2,5 · PDF'ler 3,8 sn
PAKET_ASAMALARI = {
    "sayfalar": ("Hesap sayfaları paftaya diziliyor", "Hesap sayfaları paftaya dizildi"),
    "cizimler": ("Çizimler paftaya diziliyor", "Çizimler paftaya dizildi"),
    "dwg": ("DWG'ye çevriliyor", "DWG'ye çevrildi"),
    "pdf": ("PDF'ler hazırlanıyor", "PDF'ler hazırlandı"),
}


def paket_plani(cizimli, dwg, pdf):
    """Paketin sayfalardan sonraki adımları ( asamalar.planla ):  çizimler, DWG ( çevirici kuruluysa ),
    PDF'ler ( pypdf varsa )."""
    return (
        ["sayfalar"] + (["cizimler"] if cizimli else []) + (["dwg"] if dwg else []) + (["pdf"] if pdf else [])
    )


def asamali_islemler(son_islem, pdf_islem, dwg):
    """dxf_cikti.proje_paketi'nin son işlemleri aşama bildirerek:  ( son_islem , pdf_islem ).
    Paket önce çizimleri paftaya ekler ( son_islem ), hemen ardından DWG'ye çevirir ( çevirici
    kuruluysa — dwg ), sonra PDF'leri kurar ( pdf_islem ):  aşamalar bu sırayla bildirilir."""

    def son(dxf, kagit):
        asamalar.asama("cizimler")
        sonuc = son_islem(dxf, kagit)
        if dwg:
            asamalar.asama("dwg")
        return sonuc

    def pdf(dxf, kagit):
        asamalar.asama("pdf")
        return pdf_islem(dxf, kagit)

    return (son if son_islem else None), (pdf if pdf_islem else None)

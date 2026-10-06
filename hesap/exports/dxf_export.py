# -*- coding: utf-8 -*-
"""
DXF / DWG DIŞA AKTARIM  —  "AVAN PROJESİNİ DWG AL"

Programın ürettiği bütün paftalar ( kapak · trafik · avan ) tek bir CAD
dosyasında, A4 boyutunda ve YAN YANA dizilmiş olarak verilir.  Kullanıcı
dosyayı AutoCAD'de açtığında sayfalar zaten yerleşmiştir; ayrıca PDFIMPORT
çalıştırması gerekmez.

YÖNTEM  —  neden PDF'ten okuyoruz
---------------------------------
Paftaların çizim mantığı `pdf_export.py` içinde bir kez yazılıdır.  CAD
çıktısı için İKİNCİ BİR ÇİZİCİ yazılsaydı iki çıktı zamanla ayrışırdı:
biri düzeltilir, öbürü unutulurdu.  Bunun yerine programın KENDİ ÜRETTİĞİ
PDF okunur ve içindeki vektör geometri ( çizgiler ) ile metinler CAD
varlıklarına çevrilir.  Böylece DWG, PDF'in birebir aynısıdır — AutoCAD'in
PDFIMPORT komutunun yaptığı işin aynısı, ama program tarafında ve elle
adım gerektirmeden.

AutoCAD'in PDFIMPORT'una göre iki üstünlüğü var:
  · metinler GERÇEK TEXT varlığıdır ( PDFIMPORT çoğu zaman yazıyı
    poligonlara çevirir — düzenlenemez, dosyayı şişirir ),
  · çizgiler tek tek LINE'dır, kırpma ( clip ) ve gereksiz katman üretmez.

BİÇİM  —  ASIL ÇIKTI DXF'tir
----------------------------
DXF saf Python ile ( ezdxf ) yazılır; hiçbir dış program gerektirmez ve
AutoCAD DXF'i eksiksiz açar — çift tıkla açılır, "Farklı Kaydet" ile tek
adımda DWG olur.

DWG kapalı bir biçimdir ve Python'da yazıcısı yoktur.  Makinede ODA File
Converter kuruluysa ( ücretsiz, opendesign.com ) program DWG'yi de üretir.
LibreDWG'nin dxf2dwg aracı DENENDİ VE ÇIKARILDI:  ürettiği dosyayı AutoCAD
"Drawing file is not valid" diyerek açmıyor.
"""
import io
import math
import os
import shutil
import subprocess
import tempfile
import zipfile

import ezdxf
from ezdxf import zoom
from reportlab.pdfbase import pdfmetrics

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar, LTCurve, LTLine, LTRect

#  PDF birimi punto, CAD birimi milimetre.
PT_MM = 25.4 / 72.0

#  A4 ve sayfalar arası boşluk ( mm ).  Sayfalar BİTİŞİK dizilir:  A4
#  çerçeveleri arasında boşluk yoktur, komşu iki pafta ortak kenarı paylaşır
#  ( kullanıcı 6 Eki 2026 ).
A4_G, A4_Y = 210.0, 297.0
ARA = 0.0

# =====================================================================
#  OFİSİN TİP PROJE FORMATI  —  şablon
#
#  Paftalar boşluğa değil, ofisin KENDİ pafta formatının içine dizilir:
#  solda değişmeyen antet bloğu, sağında paftaların yerleştiği büyük alan.
#  Şablon `templates/proje_formati.dxf` dosyasıdır ve ofisin kendi çiziminden
#  ( TİP PROJE FORMATI.dwg ) alınmıştır — program formatı yeniden çizmez,
#  hazır olanı doldurur.
#
#  Aşağıdaki ölçüler ŞABLONUN KENDİ KOORDİNATLARIDIR ( mm ).  Şablon
#  değişirse `_sablon_dogrula` bunu yakalar ve dosya üretilmez — sessizce
#  yanlış yere pafta koymaktansa hiç koymamak doğrudur.
# =====================================================================
SABLON_DOSYA = "proje_formati.dxf"
#  dış çerçeve  ( sol, alt, sağ, üst )
BANT = (-4215.8, 1159.4, -973.8, 1759.4)
#  A4 kapak hücresi — programın kapağı buraya oturur
KAPAK_HUCRESI = (-4215.8, 1159.4, -4012.5, 1448.3)
#  kapak hücresinin İÇ çerçevesi — şablondaki boş antet bunun içindedir
KAPAK_IC = (-4211.9, 1163.4, -4016.5, 1444.3)
#  hesap paftalarının dizileceği serbest alan
SERBEST = (-4012.5, 1159.4, -973.8, 1759.4)
#  serbest alandaki sayfa aralıkları — sayfalar bitişik ( bkz. ARA )
SUTUN_ARA = 0.0
SATIR_ARA = 0.0
#  ilk sütunun antet bloğundan uzaklığı ( mm ) — yalnız soldaki pay
SOL_PAY = 10.0

#  DXF SÜRÜMÜ  —  R2007 ve sonrası UTF-8'dir.
#  R2000 kullanılamaz:  o biçim ASCII'dir ve Türkçe harfleri "\\U+0130" kaçış
#  koduyla yazar; AutoCAD bunu TEXT varlığında ÇÖZMEZ, ekrana olduğu gibi basar
#  ( "YÜKLEN\\U+0130C\\U+0130" ).  R2013 hem UTF-8'dir hem de eski sürümlerce
#  açılır.
DXF_SURUMU = "R2013"

#  AutoCAD'de TrueType yazının "height" değeri BÜYÜK HARF yüksekliğidir;
#  PDF'teki punto ise em boyudur.  Paftaların yazı tipi DejaVu Sans, büyük harf
#  oranı 1493/2048.
CAP_ORAN = 0.729

#  CAD tarafındaki yazı tipi.  Arial her Windows ve macOS'ta kuruludur ve
#  Türkçe harflerin tamamını taşır — kurulu olmayan bir font seçmek, AutoCAD'in
#  yerine ne koyacağını belirsiz bırakırdı.
#  DİKKAT — HER İKİ BİÇİM DE AYNI DOSYAYI GÖSTERİR.
#  "arialbd.ttf" bir WINDOWS dosya adıdır; macOS'ta böyle bir dosya yoktur ve
#  AutoCAD kalın yazıyı bulamayıp varsayılan SHX fontuna düşer.  O fontta
#  İ · ′ − gibi harfler olmadığı için ekranda "?" görünür ve yazı genişler.
#  Kalınlık DOSYA ADIYLA değil, biçimin GENİŞLETİLMİŞ FONT VERİSİNDEKİ
#  ( AutoCAD'in TTF biçimleri için kullandığı yer ) "bold" bayrağıyla verilir.
#  Böylece kötü ihtimalde bile yazı OKUNUR kalır, yalnız kalınlığını yitirir.
CAD_FONT_DOSYA = "arial.ttf"
CAD_FONT_AILE = "Arial"
#  Arial'ın büyük harf oranı ( metrik ikizi Helvetica ile aynı ).
CAD_CAP_ORAN = 0.716
#  Genişlik ölçümü için Helvetica kullanılır:  Arial ile METRİK OLARAK AYNIDIR
#  ve reportlab'da gömülü olduğu için ek dosya gerekmez.
CAD_OLCU_FONT = {False: "Helvetica", True: "Helvetica-Bold"}

KATMAN_CIZGI = "AVAN-CIZGI"
KATMAN_YAZI = "AVAN-YAZI"
#  A4 ÇERÇEVELERİ 0 KATMANINDA VE BEYAZ ( ACI 7 ).  Eskiden ayrı bir katmanda
#  gri ( 8 ) çiziliyordu ve paftada soluk görünüyordu ( kullanıcı 6 Eki 2026 ).
#  0 katmanında şablonun kendi varlıkları da durduğu için A4 çerçevesi katman
#  adıyla değil ŞEKLİYLE tanınır:  bkz. a4_cerceveleri.
KATMAN_CERCEVE = "0"
RENK_CERCEVE = 7
YAZI_BICIMI = "AVAN"
YAZI_BICIMI_K = "AVAN-KALIN"

#  CAD'DE GÜVENLİ OLMAYAN SİMGELER
#  Arial ( ve AutoCAD'in bulabildiği yazı tiplerinin tamamı ) WGL4 kümesini
#  taşır:  ▪ → ≤ ≥ √ × bu kümededir.  Ama ✔ ✘ ⚠ WGL4 DIŞINDADIR ve yazı
#  tipinde bulunmayan harf AutoCAD'de "?" olarak çıkar.  Bu üçü, aynı anlamı
#  taşıyan ve her yazı tipinde bulunan karşılıklarına çevrilir.  Anlam kaybı
#  yoktur: satırlar zaten "UYGUN / UYGUN DEĞİL", "sağlanıyor / aşılıyor" der.
#
#  ŞAPKA ( ^ )  —  AUTOCAD'İ ÇÖKERTİYOR, sadece çirkin görünmüyor.
#  AutoCAD metinde "^" + karakteri DENETİM KARAKTERİ diye yorumlar ( ^8 → 0x18,
#  ^( → 0x08 ).  Yazı tipinde o kodun glifi yoktur ve macOS'ta arama
#  FontCacheOSX::getCharData içinde ÇÖKER:  AutoCAD 2027 "A software problem
#  has caused application to close unexpectedly" verip kapanır, çizim hiç
#  açılmaz.  AutoCAD 2027 for Mac'in kendi başsız motorunda ( AcCoreConsole )
#  ölçüldü:  "^8" ve "e^(f·α)" çökertiyor, "^^8" · "%%948" · "**8" · "ˆ8"
#  çökertmiyor.  Şapka paftada ÜS işareti olarak geçiyor  —  10^[…], e^(f·α),
#  (Dt/dh)^8,567  —  yani kaçınılmaz.
#  Yerine U+02C6 ( düzeltme imi ) konur:  görünüşü şapkanın aynısıdır, CP1252'de
#  0x88'de durduğu için HER ANSI yazı tipinde bulunur ve hiçbir CAD onu denetim
#  karakteri saymaz.  "**" ya da "%%94" de çökertmiyordu ama biri gösterimi
#  bozar, öteki yalnız AutoCAD'in anladığı bir kaçıştır.
CAD_SIMGE = {
    "✔": "√",     # ✔ → √   onay
    "✓": "√",     # ✓ → √
    "✘": "×",     # ✘ → ×   olumsuz
    "✕": "×",     # ✕ → ×
    "⚠": "!",          # ⚠ → !   uyarı
    "ℹ": "i",          # ℹ → i   bilgi
    "^": "ˆ",     # ^ → ˆ   ÜS  ( denetim karakteri olarak yorumlanmasın )
}

#  Aynı satırda sayılan iki karakter arasındaki azami boşluk ( em oranı ).
#  Bundan büyük boşluk yeni bir metin öğesi başlatır — böylece tablo
#  hücreleri birbirine yapışmaz.
BOSLUK_ORANI = 0.6


# =====================================================================
#  PDF → geometri
# =====================================================================
def _yuvarla(x, n=4):
    return round(float(x), n)


def _cizgiler(nesne, cikti):
    """LTLine / LTRect / LTCurve → [(x0,y0,x1,y1), …]  ( punto )"""
    if isinstance(nesne, LTLine):
        x0, y0, x1, y1 = nesne.bbox
        p = list(getattr(nesne, "pts", None) or [(x0, y0), (x1, y1)])
        for i in range(len(p) - 1):
            cikti.append((p[i][0], p[i][1], p[i + 1][0], p[i + 1][1], nesne.linewidth))
        return
    if isinstance(nesne, (LTRect, LTCurve)):
        p = list(getattr(nesne, "pts", None) or [])
        if len(p) < 2:
            return
        if isinstance(nesne, LTRect) and len(p) > 2:
            p = p + [p[0]]                      # dikdörtgeni kapat
        for i in range(len(p) - 1):
            cikti.append((p[i][0], p[i][1], p[i + 1][0], p[i + 1][1], nesne.linewidth))


def _metin_kumeleri(karakterler):
    """
    Karakterleri okunabilir METİN ÖĞELERİNE toplar.

    pdfminer her harfi ayrı verir; her harf için ayrı bir TEXT varlığı üretmek
    CAD'de binlerce düzenlenemez parça demektir.  Aynı yazı tipinde, aynı boyda,
    aynı taban çizgisinde ve BİTİŞİK olan harfler tek metinde birleştirilir.

    İki incelik var:

    · DÖNDÜRÜLMÜŞ YAZI ( kapaktaki dikey "İMZASI" ):  harfler yazının kendi
      ekseninde ilerler, bu yüzden karşılaştırma metin matrisinin DÖNDÜRÜLMÜŞ
      koordinatlarında ( u = ilerleme, v = taban çizgisi ) yapılır.
    · pdfminer, döndürülmüş harfte `size` alanına YAZI BOYUNU değil harfin
      ilerleme genişliğini koyar; punto o durumda `width` alanındadır.  Bu
      ayırt edilmezse her harf ayrı boyda görünür ve hiçbiri birleşmez.

    Karakterler ayrıca kendi eksenlerinde SIRALANIR:  pdfminer'ın verdiği sıra
    her zaman soldan sağa değildir ( dikey yazıda ters geliyordu ).
    """
    hazir = []
    for k in karakterler:
        metin = k.get_text()
        if metin in ("\n", "\r") or not metin:
            continue
        a, b, _c, _d, e, f = k.matrix
        aci = math.degrees(math.atan2(b, a))
        cos, sin = math.cos(math.radians(aci)), math.sin(math.radians(aci))
        boy = k.width if abs(b) > 1e-6 else k.size      # bkz. yukarıdaki incelik
        hazir.append({
            "metin": metin, "aci": round(aci, 2),
            "u": e * cos + f * sin, "v": -e * sin + f * cos,
            "x": e, "taban": f, "boy": boy,
            "ilerleme": getattr(k, "adv", 0.0) or 0.0,
            "font": k.fontname,
        })
    hazir.sort(key=lambda k: (k["aci"], -round(k["v"], 2), k["u"]))

    kumeler, aktif = [], None
    for k in hazir:
        anahtar = (k["font"], round(k["boy"], 3), k["aci"], round(k["v"], 2))
        if (aktif is not None and aktif["anahtar"] == anahtar
                and k["u"] - aktif["u_son"] <= BOSLUK_ORANI * k["boy"]
                and k["u"] >= aktif["u_son"] - 0.5 * k["boy"]):
            bosluk = k["u"] - aktif["u_son"]
            if (bosluk > 0.18 * k["boy"] and not aktif["metin"].endswith(" ")
                    and k["metin"] != " "):
                aktif["metin"] += " "
            aktif["metin"] += k["metin"]
            aktif["u_son"] = k["u"] + k["ilerleme"]
            continue
        aktif = {"anahtar": anahtar, "metin": k["metin"], "x": k["x"],
                 "taban": k["taban"], "boy": k["boy"], "aci": k["aci"],
                 "font": k["font"], "u_bas": k["u"],
                 "u_son": k["u"] + k["ilerleme"]}
        kumeler.append(aktif)
    return [k for k in kumeler if k["metin"].strip()]


def _sayfa_geometrisi(pdf_baytlari):
    """Her PDF sayfası için ( çizgiler, metinler, sayfa_boyutu ) döner."""
    sayfalar = []
    for sayfa in extract_pages(io.BytesIO(pdf_baytlari), laparams=None):
        cizgiler, karakterler = [], []

        def gez(nesne):
            for e in nesne:
                if isinstance(e, LTChar):
                    karakterler.append(e)
                elif isinstance(e, (LTLine, LTRect, LTCurve)):
                    _cizgiler(e, cizgiler)
                if hasattr(e, "__iter__"):
                    gez(e)

        gez(sayfa)
        sayfalar.append({
            "cizgiler": cizgiler,
            "metinler": _metin_kumeleri(karakterler),
            "genislik": sayfa.bbox[2] - sayfa.bbox[0],
            "yukseklik": sayfa.bbox[3] - sayfa.bbox[1],
        })
    return sayfalar


# =====================================================================
#  geometri → DXF
# =====================================================================
def _cad_metni(t):
    """CAD'de görüntülenemeyecek simgeleri güvenli karşılıklarıyla değiştirir."""
    if not t:
        return t
    for kaynak, hedef in CAD_SIMGE.items():
        if kaynak in t:
            t = t.replace(kaynak, hedef)
    return t


def _kalin_mi(m):
    """Paftadaki yazı KALIN mı?  ( PDF'teki font adından okunur. )"""
    ad = str(m.get("font") or "").lower()
    return "bold" in ad or "kalin" in ad


def _genislik_carpani(m):
    """
    Yazının CAD'de PDF'tekiyle AYNI GENİŞLİĞİ kaplamasını sağlayan çarpan.

    Paftalar DejaVu Sans ile dizilir, CAD tarafında ise Arial kullanılır ve
    Arial bazı dizilerde %14'e kadar DAHA GENİŞTİR.  Düzeltilmezse yazı
    hücresinden ve hatta A4 çerçevesinden taşar — nitekim taşıyordu.

    Çarpan, PDF'in ÖLÇÜLEN ilerleme genişliğinin ( pdfminer'dan ) Arial'ın aynı
    büyük-harf yüksekliğindeki genişliğine oranıdır.  Ölçüm Helvetica ile
    yapılır: Arial'ın metrik ikizidir ve reportlab'da gömülü gelir.
    """
    pdf_genislik = (m.get("u_son") or 0.0) - (m.get("u_bas") or 0.0)
    if pdf_genislik <= 0:
        return 1.0
    kalin = _kalin_mi(m)
    #  Aynı büyük harf yüksekliğini veren Arial punto boyu
    punto = m["boy"] * CAP_ORAN / CAD_CAP_ORAN
    try:
        cad_genislik = pdfmetrics.stringWidth(_cad_metni(m["metin"]),
                                              CAD_OLCU_FONT[kalin], punto)
    except Exception:                                       # noqa: BLE001
        return 1.0
    if cad_genislik <= 0:
        return 1.0
    #  Uç değerler bozuk bir ölçümün belirtisidir; yazıyı okunmaz hâle
    #  getirmektense çarpansız bırakmak yeğdir.
    return min(3.0, max(0.3, pdf_genislik / cad_genislik))


def _katmanlari_kur(d):
    """Programın çizdiği varlıklar için katman ve yazı biçimlerini hazırlar."""
    for ad, renk in ((KATMAN_CIZGI, 7), (KATMAN_YAZI, 7), (KATMAN_CERCEVE, RENK_CERCEVE)):
        if ad not in d.layers:
            d.layers.add(ad, color=renk)
    #  İKİ YAZI BİÇİMİ:  paftada kalın yazı ANLAM TAŞIR ( başlıklar, sonuç
    #  satırları, hesaplanan değerler ).  Tek biçim kullanılsaydı CAD çıktısında
    #  bu vurgu kaybolur, pafta PDF'ten farklı görünürdü.
    for _ad, _kalin in ((YAZI_BICIMI, False), (YAZI_BICIMI_K, True)):
        if _ad in d.styles:
            continue
        _b = d.styles.add(_ad, font=CAD_FONT_DOSYA)
        #  AutoCAD TTF biçimlerinde aileyi ve kalın/italik bayrağını burada
        #  arar; dosya adı yalnız yedektir.
        _b.set_extended_font_data(CAD_FONT_AILE, bold=_kalin, italic=False)
    #  ŞABLONUN KENDİ YAZI BİÇİMLERİ ( antet, notlar ):  yalnız dosya adıyla
    #  tanımlı ( times.ttf … ).  Mac'teki AutoCAD bu adla bulamayıp ince
    #  simplex.shx'e düşürüyordu ( AcCoreConsole:  "Substituting [simplex.shx]
    #  for [times.ttf]" ).  Aile adı yazılınca AutoCAD yazıyı sistemin
    #  fontundan bulur ( Windows'ta da dosya adı yerinde kalır ).
    for _b in d.styles:
        _aile = _SABLON_AILELERI.get(str(_b.dxf.get("font") or "").lower())
        if _aile and not _b.get_extended_font_data()[0]:
            _b.set_extended_font_data(_aile, bold=False, italic=False)
    return d


#  Şablondaki TrueType dosya adı → aile adı
_SABLON_AILELERI = {"times.ttf": "Times New Roman", "arial.ttf": "Arial",
                    "arialuni.ttf": "Arial Unicode MS"}


def _sayfayi_ciz(msp, sayfa, ox, oy):
    """Bir PDF sayfasını ( ox, oy ) sol-alt köşesine, mm biriminde çizer."""
    for x0, y0, x1, y1, _kalinlik in sayfa["cizgiler"]:
        if abs(x1 - x0) < 1e-9 and abs(y1 - y0) < 1e-9:
            continue
        msp.add_line(
            (_yuvarla(ox + x0 * PT_MM), _yuvarla(oy + y0 * PT_MM)),
            (_yuvarla(ox + x1 * PT_MM), _yuvarla(oy + y1 * PT_MM)),
            dxfattribs={"layer": KATMAN_CIZGI},
        )
    for m in sayfa["metinler"]:
        boy = m["boy"] * CAP_ORAN * PT_MM
        if boy <= 0:
            continue
        kalin = _kalin_mi(m)
        oz = {"layer": KATMAN_YAZI,
              "style": YAZI_BICIMI_K if kalin else YAZI_BICIMI,
              "height": _yuvarla(boy, 3)}
        carpan = _genislik_carpani(m)
        if abs(carpan - 1.0) > 1e-4:
            oz["width"] = _yuvarla(carpan, 4)
        if abs(m.get("aci") or 0.0) > 0.01:
            oz["rotation"] = _yuvarla(m["aci"], 2)
        t = msp.add_text(_cad_metni(m["metin"]), dxfattribs=oz)
        t.set_placement((_yuvarla(ox + m["x"] * PT_MM), _yuvarla(oy + m["taban"] * PT_MM)))


def _a4_cercevesi(msp, ox, oy, g=A4_G, y=A4_Y):
    msp.add_lwpolyline(
        [(ox, oy), (ox + g, oy), (ox + g, oy + y), (ox, oy + y)],
        close=True, dxfattribs={"layer": KATMAN_CERCEVE, "color": RENK_CERCEVE})


def a4_cerceveleri(msp, tol=0.5):
    """Programın çizdiği A4 çerçevelerinin kutuları  [ ( x0, y0, x1, y1 ) … ].

    Çerçeveler 0 katmanındadır ve şablonun kendi çizgileri de orada durur;
    bu yüzden katman adı yetmez:  kapalı, dört köşeli ve A4 boyutunda olan
    LWPOLYLINE'lar alınır ( şablonda A4 boyutunda kapalı çoklu çizgi yoktur ).
    """
    kutular = []
    for e in msp.query('LWPOLYLINE[layer=="%s"]' % KATMAN_CERCEVE):
        p = list(e.get_points("xy"))
        if not (e.closed and len(p) == 4):
            continue
        x0, y0 = min(q[0] for q in p), min(q[1] for q in p)
        x1, y1 = max(q[0] for q in p), max(q[1] for q in p)
        if abs(x1 - x0 - A4_G) <= tol and abs(y1 - y0 - A4_Y) <= tol:
            kutular.append((x0, y0, x1, y1))
    return kutular


def sayfalari_topla(paftalar):
    """PDF'leri bir kez okur; her sayfanın geometrisini sırayla döner."""
    sayfalar = []
    for ad, ham in paftalar:
        if not ham:
            continue
        for sayfa in _sayfa_geometrisi(ham):
            sayfa["ad"] = ad
            sayfalar.append(sayfa)
    return sayfalar


# ------------------------------------------------------------ şablon
def _sablon_yolu():
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "templates", SABLON_DOSYA)


def _nokta(e):
    t = e.dxftype()
    if t == "LINE":
        return [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
    if t == "LWPOLYLINE":
        return [(q[0], q[1]) for q in e.get_points("xy")]
    if t in ("TEXT", "MTEXT", "INSERT"):
        return [(e.dxf.insert.x, e.dxf.insert.y)]
    return []


def _kutuda(noktalar, kutu, pay=0.0):
    return bool(noktalar) and all(
        kutu[0] - pay <= x <= kutu[2] + pay and kutu[1] - pay <= y <= kutu[3] + pay
        for x, y in noktalar)


def _sablon_dogrula(d):
    """
    Şablon, programın beklediği format mı?

    Ofis çizimi değişirse paftalar yanlış yere düşer ve bu EKRANDA GÖRÜNMEZ —
    hata yalnız teslim edilen çizimde ortaya çıkar.  Bu yüzden dış çerçeve ile
    kapak hücresinin yerleri ölçülür; tutmazsa dosya ÜRETİLMEZ.
    """
    hata = []
    msp = d.modelspace()
    kutular = []
    for e in msp.query("LWPOLYLINE"):
        p = _nokta(e)
        xs = [q[0] for q in p]
        ys = [q[1] for q in p]
        kutular.append((min(xs), min(ys), max(xs), max(ys)))

    def var_mi(hedef, tol=0.5):
        return any(all(abs(a - b) <= tol for a, b in zip(k, hedef)) for k in kutular)

    if not var_mi(KAPAK_HUCRESI):
        hata.append(f"kapak hücresi {KAPAK_HUCRESI} bulunamadı")
    #  Dış çerçeve LINE'lardan oluşur — köşelerini ara.
    kose = {(round(p[0], 1), round(p[1], 1))
            for e in msp.query("LINE") for p in _nokta(e)}
    for x, y in ((BANT[0], BANT[1]), (BANT[2], BANT[1]),
                 (BANT[0], BANT[3]), (BANT[2], BANT[3])):
        if not any(abs(kx - x) <= 0.5 and abs(ky - y) <= 0.5 for kx, ky in kose):
            hata.append(f"dış çerçeve köşesi ({x}, {y}) bulunamadı")
    if hata:
        raise ValueError("PROJE FORMATI ŞABLONU UYUŞMUYOR — " + " · ".join(hata)
                         + ".  templates/" + SABLON_DOSYA + " dosyasını kontrol edin.")


def _kapak_hucresini_bosalt(d):
    """
    Şablondaki BOŞ anteti siler; yerine programın DOLU kapağı konacaktır.

    Yalnız iç çerçevenin İÇİNDE kalan varlıklar silinir — çerçevelerin
    kendisi ( ofisin pafta kenarı ) yerinde kalır.
    """
    msp = d.modelspace()
    ic = (KAPAK_IC[0] + 0.5, KAPAK_IC[1] + 0.5, KAPAK_IC[2] - 0.5, KAPAK_IC[3] - 0.5)
    silinen = 0
    for e in list(msp):
        if _kutuda(_nokta(e), ic):
            msp.delete_entity(e)
            silinen += 1
    return silinen


def _sutun_sayisi(genislik):
    """`genislik` mm'lik alana soldaki pay düşüldükten sonra kaç sütun sığar."""
    return max(1, int((genislik - SOL_PAY + SUTUN_ARA) // (A4_G + SUTUN_ARA)))


def _uzatma(adet):
    """Sayfalar sığsın diye formatın SAĞA uzatılacağı miktar  ( mm ).

    Ofis formatının serbest alanı iki satırda 14 bitişik A4 alır ( 28 sayfa ).  Uygulama
    projesi asansör başına ~21 sayfadır;  iki asansörlü bir proje 45 sayfa
    eder ve sayfalar çerçevenin ALTINA taşıyordu — çizimde duruyor ama baskıya
    giden çerçevenin dışındaydı.  Artık satır sayısı sabit kalır ( formatın
    yüksekliği ) ve çerçeve gerektiği kadar SÜTUN kadar sağa uzar.  Sığan
    projede uzatma sıfırdır, format olduğu gibi kalır.
    """
    sol, alt, sag, ust = SERBEST
    sutun = _sutun_sayisi(sag - sol)
    satir_azami = max(1, int((ust - alt + SATIR_ARA) // (A4_Y + SATIR_ARA)))
    if adet <= sutun * satir_azami:
        return 0.0
    return (-(-adet // satir_azami) - sutun) * (A4_G + SUTUN_ARA)


def _yerlesim(adet):
    """
    Serbest alanda `adet` A4 sayfanın sol-alt köşelerini verir.

    Sayfalar SOLDAN SAĞA, ÜST SATIRDAN başlayarak dizilir ( okuma sırası ) ve
    SOLA YASLANIR:  ilk sayfa antet bloğunun hemen yanından başlar, sonradan
    eklenen sayfalar sağa doğru büyür.  Ortalansaydı proje büyüdükçe bütün
    sayfaların yeri kayardı.  Dikeyde ise alanın ortasına oturur.

    Sayfalar formatın yüksekliğine sığmıyorsa aşağı taşmaz:  alan SAĞA
    uzatılır ( bkz. _uzatma ) — dönen `tasti` bu yüzden şablonlu çizimde
    hep yanlıştır.
    """
    sol, alt, sag, ust = SERBEST
    sag += _uzatma(adet)
    gen, yuk = sag - sol, ust - alt
    sutun = _sutun_sayisi(gen)
    satir = max(1, -(-adet // sutun))
    kullanilan_y = satir * A4_Y + (satir - 1) * SATIR_ARA
    x0 = sol + SOL_PAY
    y_ust = ust - max(0.0, (yuk - kullanilan_y) / 2)
    yerler = []
    for i in range(adet):
        r, c = divmod(i, sutun)
        yerler.append((x0 + c * (A4_G + SUTUN_ARA),
                       y_ust - (r + 1) * A4_Y - r * SATIR_ARA))
    return yerler, (kullanilan_y > yuk + 0.5)


def _cerceveyi_uzat(d, uzatma):
    """Formatın dış çerçevesini `uzatma` mm sağa uzatır.

    Şablonda sağ kenara dayanan yalnız ÇERÇEVE ÇİZGİLERİ vardır:  sağ dikey
    kenar ile ona bağlanan üst / alt yatay kenarlar ( antet ve kapak hücresi
    solda durur ).  Ucu sağ kenarda olan her LINE ucu kaydırılır:  dikey kenar
    bütünüyle sağa geçer, yatay kenarlar uzar.  Başka hiçbir varlığa dokunulmaz.
    """
    if uzatma <= 0:
        return 0
    kayan = 0
    for e in d.modelspace().query("LINE"):
        for uc in ("start", "end"):
            p = e.dxf.get(uc)
            if abs(p.x - BANT[2]) <= 0.5:
                e.dxf.set(uc, (p.x + uzatma, p.y, p.z))
                kayan += 1
    return kayan


def _gorunumu_ayarla(d, kutu):
    """
    Çizim AÇILDIĞINDA EKRANDA GÖRÜNSÜN diye sınırları ve kayıtlı görünümü kurar.

    İKİ AYRI ŞEY DÜZELTİLİR:

    ·  $EXTMIN / $EXTMAX  —  ezdxf bu başlıkları dosyayı YAZARKEN model
       sekmesinin kendi değerlerinden YENİDEN ÜRETİR ( Drawing.update_extents ).
       Başlığa doğrudan yazmak bu yüzden hiçbir işe yaramıyordu:  şablondan
       gelen 1e+20 / -1e+20  —  "hiç hesaplanmadı" işareti  —  dosyaya olduğu
       gibi geçiyor, ZOOM EXTENTS'in dayanağı kalmıyordu.  Değer artık
       sekmenin üstüne yazılıyor; başlığı ezdxf oradan doldurur.

    ·  KAYITLI GÖRÜNÜM ( *Active VPORT )  —  şablonda ORİJİNDE ve 1000 birim
       yüksekliğinde duruyor;  oysa ofisin pafta formatı x ≈ -4000'de.  Dosya
       bu yüzden AutoCAD'de BOMBOŞ bir ekranla açılıyordu:  çizim ekranın
       kilometrelerce dışında kalıyor, kullanıcı "dosya açılmadı" sanıyordu.
    """
    x0, y0, x1, y1 = kutu
    msp = d.modelspace()
    msp.dxf.extmin = (x0, y0, 0)
    msp.dxf.extmax = (x1, y1, 0)
    msp.dxf.limmin = (x0, y0)
    msp.dxf.limmax = (x1, y1)
    zoom.window(msp, (x0, y0), (x1, y1))


def _dxf_yaz(sayfalar, surum=None) -> bytes:
    """Şablonsuz yedek yol:  sayfaları yan yana bir şerit olarak yazar."""
    d = ezdxf.new(surum or DXF_SURUMU, setup=True)
    d.header["$INSUNITS"] = 4              # milimetre
    d.header["$MEASUREMENT"] = 1           # metrik
    _katmanlari_kur(d)
    msp = d.modelspace()
    ox = 0.0
    for sayfa in sayfalar:
        g = sayfa["genislik"] * PT_MM
        y = sayfa["yukseklik"] * PT_MM
        _a4_cercevesi(msp, ox, 0.0, g, y)
        _sayfayi_ciz(msp, sayfa, ox, 0.0)
        ox += g + ARA
    _gorunumu_ayarla(d, (0.0, 0.0, max(ox - ARA, A4_G), A4_Y))
    return _kaydet(d)


def _kaydet(d) -> bytes:
    #  KODLAMA:  dosyayı KENDİMİZ kodlamıyoruz.  ezdxf'in kendi yazıcısı
    #  sürüme uygun kodlamayı uygular; bu yüzden geçici dosyaya kaydedip
    #  bayt olarak geri okuyoruz.
    with tempfile.TemporaryDirectory() as klasor:
        yol = os.path.join(klasor, "proje.dxf")
        d.saveas(yol)
        with open(yol, "rb") as f:
            return f.read()


def _copleri_sil(msp):
    """Şablondaki görünmez çöp çizgileri siler:  boyu 0,01 mm'den kısa ya da
    düzlemin milyonlarca mm altında ( YAZı1 katmanında iki çizgi z = −150
    milyon mm'de ) — dosyanın sınırlarını ( EXTMIN ) bozuyorlardı.  Şablon
    dosyasına dokunulmaz."""
    for e in list(msp.query("LINE")):
        a, b = e.dxf.start, e.dxf.end
        if (a - b).magnitude < 0.01 or max(abs(a.z), abs(b.z)) > 1e6:
            msp.delete_entity(e)


def _formata_yerlestir(sayfalar):
    """
    Sayfaları OFİSİN TİP PROJE FORMATININ içine yerleştirir.

    · Kapak, şablondaki A4 hücresine oturur ( şablondaki boş antet silinir ).
    · Hesap paftaları sağdaki büyük alana, soldan sağa ve üst satırdan
      başlayarak dizilir.
    · Soldaki sabit blok ve dış çerçeve OLDUĞU GİBİ KALIR.
    """
    d = ezdxf.readfile(_sablon_yolu())
    _sablon_dogrula(d)
    _katmanlari_kur(d)
    msp = d.modelspace()
    _copleri_sil(msp)

    kapak = next((s for s in sayfalar if s.get("ad") == "Kapak"), None)
    digerleri = [s for s in sayfalar if s is not kapak]

    if kapak is not None:
        _kapak_hucresini_bosalt(d)
        #  A4 sayfa, hücrenin ortasına 1:1 oturur;  ofisin çerçeveleri yerinde
        #  kaldığı için kapağa ayrıca çerçeve çizilmez.
        ox = KAPAK_HUCRESI[0] - (A4_G - (KAPAK_HUCRESI[2] - KAPAK_HUCRESI[0])) / 2
        oy = KAPAK_HUCRESI[1] - (A4_Y - (KAPAK_HUCRESI[3] - KAPAK_HUCRESI[1])) / 2
        _sayfayi_ciz(msp, kapak, ox, oy)

    yerler, tasti = _yerlesim(len(digerleri))
    uzatma = _uzatma(len(digerleri))
    _cerceveyi_uzat(d, uzatma)
    for sayfa, (ox, oy) in zip(digerleri, yerler):
        _a4_cercevesi(msp, ox, oy, sayfa["genislik"] * PT_MM,
                      sayfa["yukseklik"] * PT_MM)
        _sayfayi_ciz(msp, sayfa, ox, oy)

    _gorunumu_ayarla(d, (BANT[0] - 10,
                         min([BANT[1]] + [y for _x, y in yerler]) - 10,
                         BANT[2] + uzatma + 10, BANT[3] + 10))
    return _kaydet(d), tasti


def _proje_cizimi(sayfalar, surum=None):
    """
    ÇİZİMİ ÜRETEN TEK YER.  Dönen:  ( dxf_baytlari, sablon_kullanildi, tasti )

    Hem "Projeyi DWG al" düğmesi ( proje_paketi ) hem de proje_dxf buradan
    geçer;  böylece düğmenin verdiği dosya ile testlerin ölçtüğü dosya
    BİRBİRİNDEN AYRILAMAZ.
    """
    if surum is None and os.path.exists(_sablon_yolu()):
        dxf, tasti = _formata_yerlestir(sayfalar)
        return dxf, True, tasti
    return _dxf_yaz(sayfalar, surum), False, False


def proje_dxf(paftalar, surum=None) -> bytes:
    """
    paftalar : [( ad, pdf_baytlari ), …]   sırayla dizilir.
    Dönen    : DXF dosyası ( bayt )

    Şablon varsa paftalar ofisin TİP PROJE FORMATININ içine dizilir; yoksa
    yan yana serbest bir şerit olarak verilir ( program yine de çalışır ).
    """
    return _proje_cizimi(sayfalari_topla(paftalar), surum)[0]


# =====================================================================
#  DXF → DWG   ( makinede dönüştürücü varsa )
# =====================================================================
#  YALNIZ ODA File Converter KULLANILIR.
#
#  LibreDWG'nin "dxf2dwg" aracı da DWG üretiyor ve kendi okuyucusundan
#  geçiyor — ama AutoCAD ürettiği dosyayı "Drawing file is not valid" diyerek
#  AÇMIYOR ( AutoCAD for Mac 2027'de ölçüldü ).  Açılmayan bir dosyayı pakete
#  koymak, kullanıcının vaktini boşa harcamaktan başka bir işe yaramaz;
#  bu yüzden o araç listeden ÇIKARILDI.
#
#  ODA File Converter, DWG biçimini tanımlayan Open Design Alliance'ın kendi
#  aracıdır ve çıktısını AutoCAD sorunsuz açar.  Kurulu değilse DWG üretilmez
#  ve kullanıcıya sebebi söylenir — DXF zaten AutoCAD'de birebir açılıyor.
DONUSTURUCULER = ("ODAFileConverter",)


def donusturucu():
    """Kurulu bir DXF→DWG dönüştürücüsü varsa yolunu döner."""
    for ad in DONUSTURUCULER:
        yol = shutil.which(ad)
        if yol:
            return yol
    return None


def dwg_uret(dxf_baytlari, surum="ACAD2018"):
    """DXF'ten DWG üretir; dönüştürücü yoksa ( None, sebep ) döner."""
    arac = donusturucu()
    if not arac:
        return None, ("Bu bilgisayarda ODA File Converter kurulu olmadığı için "
                      "DWG üretilmedi — çizim DXF olarak verildi.  AutoCAD DXF'i "
                      "birebir açar;  DWG istiyorsanız dosyayı açıp "
                      "'Farklı Kaydet → AutoCAD Çizimi (*.dwg)' demeniz yeterli.")
    with tempfile.TemporaryDirectory() as klasor:
        girdi = os.path.join(klasor, "girdi")
        cikti = os.path.join(klasor, "cikti")
        os.makedirs(girdi, exist_ok=True)
        os.makedirs(cikti, exist_ok=True)
        with open(os.path.join(girdi, "proje.dxf"), "wb") as f:
            f.write(dxf_baytlari)
        try:
            subprocess.run([arac, girdi, cikti, surum, "DWG", "0", "1"],
                           capture_output=True, timeout=300, check=False)
        except Exception as e:                                   # noqa: BLE001
            return None, f"DWG dönüştürücü çalıştırılamadı : {e}"
        dwg = os.path.join(cikti, "proje.dwg")
        if os.path.exists(dwg) and os.path.getsize(dwg) > 1024:
            with open(dwg, "rb") as f:
                return f.read(), None
    return None, "DWG dönüştürücü dosya üretemedi — DXF verildi."


def _okubeni(dosya_adi, dwg_var, sebep, sablonlu=False, tasti=False, ekler=()):
    satir = [f"{dosya_adi}   —   Asansör Proje Programı", "",
             "PAKETİN İÇİNDEKİLER", ""]
    if dwg_var:
        satir.append(f"  {dosya_adi}.dwg    AutoCAD çizimi ( doğrudan açılır )")
    satir += [
        f"  {dosya_adi}.dxf    Aynı çizimin DXF'i — AutoCAD birebir açar",
        "  pafta pdf/         Çizime dönüştürülen kaynak paftalar",
    ]
    satir += [f"  {a}" for a in ekler]
    satir += [
        "",
        "ÇİZİM NASIL KURULDU",
        "  Paftaların vektör geometrisi okunup CAD varlığına çevrildi:  çizgiler",
        "  LINE, yazılar TEXT oldu.  Ayrıca PDFIMPORT çalıştırmanız gerekmez.",
        ("  Sayfalar OFİSİN TİP PROJE FORMATININ içine A4 boyutunda dizildi:"
         "\n  kapak sol üstteki antet hücresinde, hesaplar sağdaki büyük alanda."
         if sablonlu else
         "  Şablon bulunamadığı için sayfalar yan yana serbest dizildi."),
        "",
        "  Yazı tipi Arial'dir ( her makinede kurulu ).  ✔ ✘ ⚠ işaretleri hiçbir",
        "  CAD yazı tipinde bulunmadığı için çizimde √ × ! olarak yazılır;",
        "  anlam aynıdır — satırlar zaten UYGUN / UYGUN DEĞİL diyor.",
        "",
        "  Çizimde bir tuhaflık görürseniz 'pafta pdf' klasöründeki dosyaları",
        "  AutoCAD'de PDFATTACH ile ekleyip PDFIMPORT ile gömebilirsiniz.",
    ]
    if tasti:
        satir += ["", "DİKKAT",
                  "  Pafta sayısı formatın çerçevesine sığmadı; alta taşan",
                  "  sayfalar var.  Çerçeveyi büyütün ya da paftaları azaltın."]
    if any(a.endswith((".avan", ".uygulama")) for a in ekler):
        satir += ["", "PROJE DOSYASI",
                  "  Paketteki .avan / .uygulama dosyası projenin BÜTÜN",
                  "  girdilerini taşır.  Aylar sonra revizyon gerektiğinde onu",
                  "  programa yükleyin:  her şey yerine oturur, değişeni",
                  "  düzeltip çıktıları yeniden alırsınız.  Hiçbir girdiyi",
                  "  baştan girmeniz gerekmez."]
    if not dwg_var:
        satir += ["", "DWG İSTERSENİZ", "  " + (sebep or "")]
    return "\n".join(satir) + "\n"


def proje_paketi(paftalar, dosya_adi="Avan Projesi", ekler=None, son_islem=None):
    """`ekler`:  pakete konacak ek dosyalar  —  [ ( ad, bayt ) ].

    "Projeyi paketle" düğmesi buradan geçer:  paftaların yanına PROJE
    DOSYASI da girer, böylece teslim paketi ile geri dönüş noktası aynı
    arşivde durur.

    `son_islem`:  DXF baytlarını alıp yenisini döner — uygulama projesinde
    çizim modülü çizimleri son hesap sayfasının sağına ekler.  DWG de ondan
    sonra üretilir, iki dosya aynı paftayı taşır.
    """
    return _proje_paketi(paftalar, dosya_adi, ekler, son_islem)


def _proje_paketi(paftalar, dosya_adi="Avan Projesi", ekler=None, son_islem=None):
    """
    Butonun indirdiği ZIP:  içinde DXF ( her zaman ) ve DWG ( üretilebildiyse ).
    Dönen: ( zip_baytlari, dwg_yoksa_sebebi, paftalar_tasti_mi )

    `tasti` doğruysa pafta sayısı ofis formatının çerçevesine sığmamıştır ve
    alta taşan sayfalar vardır.  Bu, yalnız OKUBENI'de kalmamalı — çağıran
    kullanıcıya SÖYLEMELİDİR; taşmış bir pafta baskıya gidebilir.
    """
    dxf, sablonlu, tasti = _proje_cizimi(sayfalari_topla(paftalar))
    if son_islem is not None:
        dxf = son_islem(dxf)
    dwg, sebep = dwg_uret(dxf)
    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{dosya_adi}.dxf", dxf)
        if dwg:
            z.writestr(f"{dosya_adi}.dwg", dwg)
        #  KAYNAK PAFTALAR da pakete konur.  Çizimde bir tuhaflık görülürse
        #  bu PDF'ler AutoCAD'de PDFATTACH ile eklenip PDFIMPORT ile
        #  gömülebilir — elle yapılan yol her zaman açık kalır.
        for _sira, (_ad, _ham) in enumerate(paftalar, 1):
            if _ham:
                z.writestr(f"pafta pdf/{_sira} - {_ad}.pdf", _ham)
        for _ad, _ham in (ekler or ()):
            if _ham:
                z.writestr(_ad, _ham)
        z.writestr("OKUBENI.txt",
                   _okubeni(dosya_adi, bool(dwg), sebep, sablonlu, tasti,
                            [a for a, h in (ekler or ()) if h]))
    tampon.seek(0)
    return tampon.read(), sebep, tasti

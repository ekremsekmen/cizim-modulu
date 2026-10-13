# -*- coding: utf-8 -*-
"""
PAFTA  —  çizimlerin ofisin TİP PROJE FORMATINA yerleştirilmesi

Şablon `sablon/proje_formati.dxf`:  ofisin kendi çiziminden ( TİP PROJE
FORMATI.dwg ) alınmış, hesap programının kullandığıyla AYNI dosya.  3.242 ×
600 mm'lik bir şerit:  solda notlar ve antet ( A4 hücresi ), sağda serbest
alan.  Şablonun birimi PAFTA milimetresidir;  çizimler gerçek ölçüde
( mm ) blok olarak tanımlanır ve paftaya 1/ölçek ile yerleştirilir —
CAD'de blok açılınca ölçüler gerçek boyundadır.

YERLEŞİM ( ofisin 477-8 uygulama projesindeki düzen ):  önce düşey
kesitler ( 1/50 ), sonra planlar ( 1/20 ) konu sırasıyla
sütunlara dizilir;  çizim sütuna sığmazsa yeni sütun açılır.  Düşey
kesitler paftanın yüksekliğine sığmazsa ara katlar kırılır ( referans proje ve
LiftDesigner gibi ).  Serbest alan yetmezse çerçeve SAĞA uzatılır — hesap
programının yaptığı gibi;  aşağı taşmaz.

ANTET:  bilinen değerler çizim girdisinden yazılır;  çizimin bilmediği
değerler ( taşıma kapasitesi, asansör sınıfı, motor gücü ) BOŞ bırakılır —
şablondaki örnek değerler ( "300 KG", "2,67 KW" … ) projeyi yanlış tanıtırdı.
"""

import io
import os
import tempfile

import ezdxf
from ezdxf import zoom

from cizim import cizimler
from cizim import dxf
from cizim import dusey
from cizim import eleman
from cizim import geometri
import math

SABLON = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sablon", "proje_formati.dxf"
)
#  Şablonun kendi koordinatları ( pafta mm ) — hesap programının dxf_export.py
#  sabitleriyle aynı;  şablon değişirse _sablon_dogrula yakalar.
BANT = (-4215.8, 1159.4, -973.8, 1759.4)
KAPAK_HUCRESI = (-4215.8, 1159.4, -4012.5, 1448.3)
SERBEST = (-4012.5, 1159.4, -973.8, 1759.4)
KENAR = 10.0  # serbest alanın kenarından ilk çizime
ARA = 12.0  # çizimler arası

#  Antetteki DEĞER hücreleri:  ( şablondaki örnek yazı, yeri ) — örnek yazı
#  yerinde değilse şablon değişmiş demektir, pafta üretilmez.
ANTET = {
    "yuk": ("300 KG (4 KİŞİ)", (-4188.7, 1400.7)),
    "hiz": ("1,00 m/sn", (-4162.0, 1400.7)),
    "durak": ("0,1/2 DURAK", (-4143.2, 1400.7)),
    "seyir": ("3500", (-4112.1, 1400.7)),
    "kabin_g": ("950", (-4092.8, 1400.3)),
    "kabin_d": ("950", (-4078.3, 1400.5)),
    "standart": ("TS EN 81-20", (-4063.5, 1400.4)),
    "sinif": ("Sınıf I", (-4187.5, 1392.0)),
    "aski": ("2:1", (-4162.3, 1392.0)),
    "adet": ("1", (-4134.6, 1392.3)),
    "tahrik": ("Elektrikli", (-4115.1, 1392.4)),
    "ray": ("70*70*9", (-4091.8, 1392.6)),
    "motor": ("2,67 KW", (-4185.6, 1385.2)),
    "olcek": ("1/20 1/30 1/50  ", (-4169.4, 1384.9)),
}

#  Paftadaki çizimler, sırasıyla ( makine dairesizde kuyu üstü planı,
#  makine dairelide makine dairesi ve delik planı )
#  Sonda LiftDesigner'ın görünüşleri:  kasnak düzenlemesi, giriş ve kapı yan kesiti;
#  en sonda asansörün veri tablosu ( veri_tablosu ).
SIRA_MRL = (
    "kuyu_kesiti_yan",
    "kuyu_kesiti_on",
    "kuyu_plani",
    "kabin_ustu",
    "kuyu_dibi",
    "kuyu_ustu",
    "kasnak_duzeni",
    "giris",
    "kapi_kesiti",
    "veriler",
)
SIRA_MD = (
    "kuyu_kesiti_yan",
    "kuyu_kesiti_on",
    "kuyu_plani",
    "kabin_ustu",
    "kuyu_dibi",
    "makine_dairesi",
    "delik_plani",
    "kasnak_duzeni",
    "giris",
    "kapi_kesiti",
    "veriler",
)


def _nokta(e):
    t = e.dxftype()
    if t == "LINE":
        return [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
    if t == "LWPOLYLINE":
        return [(q[0], q[1]) for q in e.get_points("xy")]
    return []


def _a4_mu(e, tol=0.5):
    """Hesap programının A4 çerçevesi mi:  kapalı, dört köşeli, 210 × 297 mm."""
    p = _nokta(e)
    if not (e.dxftype() == "LWPOLYLINE" and e.closed and len(p) == 4):
        return False
    xs, ys = [q[0] for q in p], [q[1] for q in p]
    return abs(max(xs) - min(xs) - 210.0) <= tol and abs(max(ys) - min(ys) - 297.0) <= tol


def _sablon_dogrula(d):
    """Dış çerçevenin köşeleri, kapak hücresi ve antetin değer hücreleri yerinde mi."""
    msp = d.modelspace()
    hata = []
    kutular = []
    for e in msp.query("LWPOLYLINE"):
        p = _nokta(e)
        kutular.append(
            (min(q[0] for q in p), min(q[1] for q in p), max(q[0] for q in p), max(q[1] for q in p))
        )
    if not any(all(abs(a - b) <= 0.5 for a, b in zip(k, KAPAK_HUCRESI)) for k in kutular):
        hata.append(f"kapak hücresi {KAPAK_HUCRESI} yok")
    kose = {(round(p[0], 1), round(p[1], 1)) for e in msp.query("LINE") for p in _nokta(e)}
    for x, y in ((BANT[0], BANT[1]), (BANT[2], BANT[1]), (BANT[0], BANT[3]), (BANT[2], BANT[3])):
        if not any(abs(kx - x) <= 0.5 and abs(ky - y) <= 0.5 for kx, ky in kose):
            hata.append(f"dış çerçeve köşesi ({x}, {y}) yok")
    for ad, (ornek, yer) in ANTET.items():
        if _antet_yazisi(d, yer, ornek) is None:
            hata.append(f"antette {ad} hücresi ( '{ornek.strip()}' ) yok")
    if hata:
        raise ValueError("PROJE FORMATI ŞABLONU UYUŞMUYOR — " + " · ".join(hata))


def _antet_yazisi(d, yer, ornek=None):
    for e in d.modelspace().query("TEXT"):
        p = e.dxf.insert
        if abs(p.x - yer[0]) <= 0.2 and abs(p.y - yer[1]) <= 0.2 and (ornek is None or e.dxf.text == ornek):
            return e
    return None


def antet_degerleri(g, olcekler):
    """Antete yazılacaklar;  boş dize = çizimin bilmediği değer ( boş kalır )."""
    dy, kb, kr = g["dusey"], g["kabin"], g["kabin_ray"]
    kotlar = dusey.durak_kotlari(g)[0]
    return {
        "yuk": "",
        "sinif": "",
        "motor": "",
        "hiz": f"{dy['beyan_hizi']:.2f} m/sn".replace(".", ","),
        "durak": f"{dy['durak_adedi']} DURAK",
        "seyir": f"{kotlar[-1]:g}",
        "kabin_g": f"{kb['genislik']:g}",
        "kabin_d": f"{kb['derinlik']:g}",
        "standart": "TS EN 81-20",
        "aski": "1:1" if (g.get("aski") or {}).get("duzen") == "Doğrudan" else "2:1",
        "adet": "1",
        "tahrik": "Elektrikli",
        "ray": f"{kr['b']:g}*{kr['h']:g}",
        "olcek": " ".join(f"1/{o:g}" for o in sorted(set(olcekler))),
    }


def _antet(d, g, olcekler):
    msp = d.modelspace()
    for ad, deger in antet_degerleri(g, olcekler).items():
        e = _antet_yazisi(d, ANTET[ad][1])
        if deger:
            e.dxf.text = deger
        else:
            msp.delete_entity(e)


def sira(g):
    """Bu projenin paftasındaki çizimler, sırasıyla."""
    return SIRA_MD if (g.get("makine") or {}).get("yeri") == "Makine dairesi" else SIRA_MRL


def cizim_listesi(g, seritler=()):
    """( ad, başlık, ölçek, elemanlar — çerçeveli ) ;  hata varsa ValueError.
    seritler:  çizimlerin künye şeridine yazılacaklar ( çok asansörlü
    projede asansörün adı — hangi kuyunun çizimi olduğu okunsun )."""
    cikti, hata = [], []
    #  Serbest alanın yüksekliği ( kenarlar düşülünce ), çizim biriminde
    yukseklik = SERBEST[3] - SERBEST[1] - 2 * KENAR
    for ad in sira(g):
        dogrula, ciz, baslik = cizimler.CIZIMLER[ad]
        h = dogrula(g)
        if h:
            hata += [f"{ad}: {x}" for x in h]
            continue
        olcek = cizimler.OLCEKLER.get(ad, 20)
        e = ciz(g, azami=yukseklik * olcek) if ad in cizimler.OLCEKLER else ciz(g)
        cikti.append(
            (
                ad,
                cizimler.plan_basligi(g, ad, baslik),
                olcek,
                geometri.cerceveli(
                    e,
                    cizimler.plan_basligi(g, ad, baslik),
                    olcek,
                    seritler=seritler,
                    olcekli=ad not in cizimler.OLCEKSIZ,
                ),
            )
        )
    if hata:
        raise ValueError("Pafta çizilemiyor:  " + " · ".join(hata))
    return cikti


def yerlesim(boyutlar, x0=None, sag=None):
    """Pafta mm'sinde çizim boyutlarından ( g, y ) sol-alt köşeler ve
    gereken sağ kenar:  sütun sütun, üstten aşağı, soldan sağa.  x0:  ilk
    sütunun solu ( hesap sayfalarından sonra ), sag:  çerçevenin şimdiki sağı."""
    _, alt, x1, ust = SERBEST
    x0 = SERBEST[0] if x0 is None else x0
    x1 = x1 if sag is None else sag
    x = x0 + KENAR
    y = ust - KENAR
    sutun_eni = 0.0
    yerler = []
    for g_, y_ in boyutlar:
        if yerler and y - y_ < alt + KENAR - 1e-6:
            x += sutun_eni + ARA
            y, sutun_eni = ust - KENAR, 0.0
        yerler.append((x, y - y_))
        y -= y_ + ARA
        sutun_eni = max(sutun_eni, g_)
    return yerler, max(x1, x + sutun_eni + KENAR)


def _cerceveyi_uzat(d, sag, eski=None):
    """Serbest alan yetmezse çerçevenin sağ kenarı `sag`a kayar ( üst ve alt
    kenar uzar ) — hesap programının dxf_export._cerceveyi_uzat'ı gibi.
    eski:  çerçevenin şimdiki sağı ( hesap programı uzatmış olabilir )."""
    eski = BANT[2] if eski is None else eski
    if sag <= eski + 1e-6:
        return
    for e in d.modelspace().query("LINE"):
        for uc in ("start", "end"):
            p = e.dxf.get(uc)
            if abs(p.x - eski) <= 0.5:
                e.dxf.set(uc, (sag, p.y, p.z))


def _copleri_sil(msp):
    """Şablondaki görünmez çöp çizgileri siler ( hesap programının
    dxf_export._copleri_sil'i gibi ):  boyu 0,01 mm'den kısa ya da düzlemin
    milyonlarca mm altında — YAZı1 katmanında iki çizgi z = −150 milyon mm'de,
    dosyanın sınırlarını ( EXTMIN ) bozuyordu."""
    for e in list(msp.query("LINE")):
        a, b = e.dxf.start, e.dxf.end
        if (a - b).magnitude < 0.01 or max(abs(a.z), abs(b.z)) > 1e6:
            msp.delete_entity(e)


def _katmanlari_onar(d):
    """Şablonun kendi katmanlarından dördü ( ÇERÇ, YAZı, t-çap, YAZı1 ) dosyada
    olmayan malzeme ve çizim stili kayıtlarını gösteriyor;  AutoCAD'in AUDIT'i
    bunları 16 hata sayıyordu ( AcCoreConsole ile ölçüldü ).  Geçerli
    kayıtlara ( "Global" malzeme, "Normal" çizim stili ) bağlanır."""
    db = d.entitydb
    malzeme = d.materials.get("Global").dxf.handle
    stil = d.rootdict.get("ACAD_PLOTSTYLENAME").get("Normal").dxf.handle

    def tur(h):
        e = db.get(h) if h else None
        return e.dxftype() if e is not None else None

    #  "EE" ve "F" dosyada VAR ama malzeme / çizim stili değil — türüne bakılır
    for k in d.layers:
        if tur(k.dxf.get("material_handle")) != "MATERIAL":
            k.dxf.material_handle = malzeme
        if tur(k.dxf.get("plotstyle_handle")) != "ACDBPLACEHOLDER":
            k.dxf.plotstyle_handle = stil


def bloklar(g):
    """Paftanın çizimleri, sırasıyla:  [ ( ad, başlık, ölçek, elemanlar ) ] —
    blok adı "CIZIM_" + ad.upper().  g:  tek asansörün girdisi ya da çok
    asansörlü projede girdilerin listesi ( asansörler sırayla, her çizimin
    şeridinde asansörün adı ).  DXF ( _yerlestir ) ve PDF ( ciktilar/pafta_pdf )
    aynı listeyi kullanır."""
    gler = g if isinstance(g, (list, tuple)) else [g]
    liste = []
    for i, g_ in enumerate(gler):
        coklu = len(gler) > 1
        for ad, baslik, olcek, e in cizim_listesi(g_, (g_["proje"]["asansor"],) if coklu else ()):
            #  Blok adı asansörle birlikte:  iki kuyunun kesiti aynı bloğu ezmesin
            liste.append((f"{ad}_{i + 1}" if coklu else ad, baslik, olcek, e))
    return liste


def kunyeler(g):
    """bloklar( g ) ile aynı sırada her çizimin projesi ve asansörü:
    [ { proje, asansor } ] — ayrı sayfalı PDF'in anteti ( pdf.sayfalar )."""
    gler = g if isinstance(g, (list, tuple)) else [g]
    return [
        {"proje": g_["proje"]["ad"], "asansor": g_["proje"]["asansor"]} for g_ in gler for _ad in sira(g_)
    ]


def blok_adi(ad):
    return f"CIZIM_{ad.upper()}"


def _yerlestir(d, g, x0=None, sag_eski=None):
    """Çizimleri belgeye blok olarak yerleştirir;  gerekirse çerçeveyi uzatır."""
    liste = bloklar(g)
    dxf.hazirla(d)
    boyutlar, kutular = [], []
    for _ad, _baslik, olcek, e in liste:
        bx0, by0, bx1, by1 = geometri.sinir(e)
        kutular.append((bx0, by0))
        boyutlar.append(((bx1 - bx0) / olcek, (by1 - by0) / olcek))
    yerler, sag = yerlesim(boyutlar, x0, sag_eski)
    _cerceveyi_uzat(d, sag, sag_eski)
    msp = d.modelspace()
    yerlesen = []
    for (ad, baslik, olcek, e), (bx, by), (px, py), (w, h) in zip(liste, kutular, yerler, boyutlar):
        blok = d.blocks.new(name=blok_adi(ad), base_point=(bx, by))
        dxf.ciz(blok, e, olcek, blokta=True)
        msp.add_blockref(
            blok.name, (px, py), dxfattribs={"xscale": 1.0 / olcek, "yscale": 1.0 / olcek, "layer": "0"}
        )
        yerlesen.append({"ad": ad, "baslik": baslik, "olcek": olcek, "kutu": (px, py, px + w, py + h)})
    x0_, y0_, x1_, y1_ = BANT[0], BANT[1], sag, BANT[3]
    msp.dxf.extmin, msp.dxf.extmax = (x0_, y0_, 0), (x1_, y1_, 0)
    msp.dxf.limmin, msp.dxf.limmax = (x0_, y0_), (x1_, y1_)
    zoom.window(msp, (x0_ - 10, y0_ - 10), (x1_ + 10, y1_ + 10))
    return {"cizimler": yerlesen, "sag": sag, "olcekler": [c[2] for c in liste]}


def belge(g):
    """Doldurulmuş pafta ( ezdxf belgesi ) ve yerleşim bilgisi."""
    d = ezdxf.readfile(SABLON)
    _sablon_dogrula(d)
    _katmanlari_onar(d)
    _copleri_sil(d.modelspace())
    bilgi = _yerlestir(d, g)
    _antet(d, g, bilgi["olcekler"])
    _kullanilmayanlari_sil(d)
    return d, bilgi


def birlestir(hesap_dxf, g):
    """TAM PROJE:  hesap programının TİP PROJE FORMATINA dizdiği DXF'e
    ( kapak + hesap sayfaları ) çizimleri ekler — son hesap sayfasının
    sağından başlayarak;  çerçeve gerekirse sağa uzar.  Antete dokunulmaz:
    hesap programının kapağı onun yerindedir.

    hesap_dxf:  dosya yolu.  g:  tek girdi ya da asansörlerin girdileri
    ( listede sırayla dizilir ).  Dönen:  ( belge, bilgi )."""
    d = ezdxf.readfile(hesap_dxf)
    msp = d.modelspace()
    #  Çerçevenin şimdiki sağ kenarı:  üst kenar çizgisinin en sağ ucu
    ust = [p.x for e in msp.query("LINE") for p in (e.dxf.start, e.dxf.end) if abs(p.y - BANT[3]) <= 0.5]
    if not ust or min(ust) > BANT[0] + 0.5:
        raise ValueError("Hesap DXF'inde TİP PROJE FORMATI çerçevesi bulunamadı.")
    sag_eski = max(ust)
    #  Hesap sayfalarının sağı:  A4 çerçevelerinin en sağ ucu.  Hesap programı
    #  çerçeveleri 0 katmanına çizer ( orada şablonun kendi çizgileri de var ),
    #  bu yüzden çerçeve ŞEKLİYLE tanınır:  kapalı, dört köşeli, 210 × 297.
    sayfalar = [q[0] for e in msp.query("LWPOLYLINE") if _a4_mu(e) for q in _nokta(e)]
    x0 = max(sayfalar) if sayfalar else SERBEST[0]
    _katmanlari_onar(d)
    bilgi = _yerlestir(d, g, x0, sag_eski)
    bilgi["hesap_sagi"] = x0
    _kullanilmayanlari_sil(d)
    return d, bilgi


AILELER = {"times.ttf": "Times New Roman", "arialuni.ttf": "Arial Unicode MS", "arial.ttf": "Arial"}


def _kullanilmayanlari_sil(d):
    """Hiçbir yazının ve ölçü stilinin kullanmadığı yazı stillerini, hiçbir
    ölçünün kullanmadığı ölçü stillerini siler ( AutoCAD'in PURGE'ü gibi ).
    Şablon ve hesap programının DXF'i 30'a yakın stil taşıyordu ( "dddddddddd",
    "STYLE1", "ODA" … — 12 Eki );  AutoCAD açılışta bulamadığı yazı tiplerini
    simplex.shx'e düşürüp tek tek bildiriyordu.  Kalanlar şablonun kendi antet
    yazılarınındır.  Dosyanın varsayılan stilleri ( AutoCAD'de yeni yazı ve
    ölçü bunlarla çizilir ) çizimin stilleri olur — şablonunki ezdxf'in
    "EZDXF" ölçü stiliydi ( OpenSans yazı tipi, DIMLFAC 100 )."""
    if dxf.YAZI_TIPI in d.styles:
        d.header["$TEXTSTYLE"] = dxf.YAZI_TIPI
    #  Şablonun stillerine yazı tipinin AİLE adı da:  AutoCAD TrueType'ı önce
    #  aileden bulur — Mac'te dosya adları farklı ( times.ttf, ARIALUNI.TTF
    #  bulunamayıp simplex.shx'e düşüyordu;  dxf.hazirla'daki Arial gibi )
    for st in d.styles:
        aile = AILELER.get(st.dxf.get("font", "").lower())
        if aile and not st.has_extended_font_data:
            st.set_extended_font_data(aile, bold=False, italic=False)
    varsayilan = dxf.olcu_stili(d, 20)
    d.header["$DIMSTYLE"] = varsayilan
    yazilar, olculer = set(), set()
    for yer in [d.modelspace(), *d.blocks]:
        for e in yer:
            if e.dxftype() in ("TEXT", "MTEXT", "ATTRIB", "ATTDEF"):
                yazilar.add(e.dxf.get("style", "Standard").upper())
            elif e.dxftype() == "INSERT":
                yazilar.update(a.dxf.get("style", "Standard").upper() for a in e.attribs)
            elif e.dxftype() == "DIMENSION":
                olculer.add(e.dxf.get("dimstyle", "Standard").upper())
    olculer.add(str(d.header.get("$DIMSTYLE", "Standard")).upper())
    for s in list(d.dimstyles):
        if s.dxf.name.upper() not in olculer | {"STANDARD"}:
            d.dimstyles.remove(s.dxf.name)
    yazilar.update(s.dxf.get("dimtxsty", "Standard").upper() for s in d.dimstyles)
    yazilar.add(str(d.header.get("$TEXTSTYLE", "Standard")).upper())
    for s in list(d.styles):
        #  Biçim ( shape ) dosyaları adsızdır ve çizgi tiplerinden kullanılır
        if s.dxf.name and not s.dxf.flags & 1 and s.dxf.name.upper() not in yazilar | {"STANDARD"}:
            d.styles.remove(s.dxf.name)


def yaz(g) -> bytes:
    d, _ = belge(g)
    with tempfile.TemporaryDirectory() as klasor:
        yol = os.path.join(klasor, "pafta.dxf")
        d.saveas(yol)
        with open(yol, "rb") as f:
            return f.read()


def _maskeleri_ac(d):
    """Yazı maskelerini ( MTEXT arka planı, ölçüde dimtfill ) ezdxf'in çizdiği
    WIPEOUT'a çevirir:  ezdxf ( 1.4 ) MTEXT'in arka planını çizmiyor, AutoCAD
    çiziyor ( CDX.MASKE_PAYI ).  Yalnız önizlemenin kopyasında;  her maskenin
    WIPEOUT'u yazısıyla birlikte bloğun sonuna alınır ( örtü kendinden önce
    çizileni örter ).  Kutu yazının kendisinden:  tek satır, ortası ( 4 · 5 · 6 )
    ya da altı ( 7 · 8 · 9 ) hizalı;  en harflerin gerçek eninden
    ( eleman.yazi_eni — ezdxf'in MTEXT kutusu bu yazılarda kayıktı )."""

    for blok in d.blocks:
        for m in list(blok.query("MTEXT")):
            if not m.dxf.get("bg_fill", 0):
                continue
            h = m.dxf.char_height
            w = eleman.yazi_eni(m.plain_text(), h / dxf.BUYUK_HARF)
            ap = m.dxf.get("attachment_point", 1)
            x0 = {0: 0.0, 1: -w / 2.0, 2: -w}[(ap - 1) % 3]
            y0 = {0: -h, 1: -h / 2.0, 2: 0.0}[(ap - 1) // 3]
            pay = (m.dxf.get("box_fill_scale", 1.5) - 1.0) * h / 2.0
            a = math.radians(m.dxf.get("rotation", 0.0))
            c, s_ = math.cos(a), math.sin(a)
            ix, iy = m.dxf.insert.x, m.dxf.insert.y
            koseler = [
                (x0 - pay, y0 - pay),
                (x0 + w + pay, y0 - pay),
                (x0 + w + pay, y0 + h + pay),
                (x0 - pay, y0 + h + pay),
            ]
            blok.add_wipeout([(ix + u * c - v * s_, iy + u * s_ + v * c) for u, v in koseler])
            yazi = m.copy()
            blok.delete_entity(m)
            blok.add_entity(yazi)


def onizleme(d) -> str:
    """Paftanın SVG önizlemesi ( ezdxf'in kendi çizicisiyle, DXF'ten ) —
    ekranda görmek için;  asıl çıktı DXF'tir.

    ezdxf ( 1.4 ) ölçekli bloğun içindeki taramanın desen çizgilerini
    ölçeklemiyor:  desen blok ölçeğinin tersi kadar seyrek çıkıyordu ( 1/50
    kesitte duvarda tek çizgi ).  AutoCAD deseni doğru ölçekler;  DXF'e
    dokunulmaz — önizleme bir KOPYADA yalnız taramaları bloklardan çıkarır
    ( öbür parçalar blokta kalır:  bütün blok açılınca ölçü yazıları da
    yanlış ölçekleniyordu ), desenlerini adından ve ( doğru ölçeklenmiş )
    desen ölçeğinden yeniden kurar."""
    #  Çizim eklentisi ( matplotlib'siz SVG ) yalnız önizlemede gerekir ve
    #  ağırdır:  program açılırken yüklenmesin diye burada import edilir.
    from ezdxf.addons.drawing import Frontend, RenderContext, config, layout, svg
    from ezdxf.entities import factory

    akis = io.StringIO()
    d.write(akis)
    akis.seek(0)
    k = ezdxf.read(akis)
    msp, bloklar = k.modelspace(), set()
    for ins in list(msp.query("INSERT")):
        for e in ins.virtual_entities():
            if e.dxftype() == "HATCH" and e.pattern and e.dxf.pattern_name in ezdxf.pattern.ISO_PATTERN:
                e.set_pattern_fill(
                    e.dxf.pattern_name,
                    color=e.dxf.color,
                    angle=e.dxf.pattern_angle,
                    scale=e.dxf.pattern_scale,
                )
                factory.bind(e, k)
                msp.add_entity(e)
                bloklar.add(ins.dxf.name)
    for ad in bloklar:
        blok = k.blocks[ad]
        for e in list(blok.query("HATCH")):
            if e.pattern and e.dxf.pattern_name in ezdxf.pattern.ISO_PATTERN:
                blok.delete_entity(e)
    _maskeleri_ac(k)
    #  Beyaz zeminde camgöbeği ölçü okunmaz:  önizlemede mavi ( CDX.KATMAN )
    if "OLCU" in k.layers:
        k.layers.get("OLCU").dxf.color = 5
    d = k
    arka = svg.SVGBackend()
    ayar = config.Configuration(
        background_policy=config.BackgroundPolicy.WHITE, color_policy=config.ColorPolicy.COLOR
    )
    Frontend(RenderContext(d), arka, config=ayar).draw_layout(d.modelspace())
    return arka.get_string(layout.Page(0, 0, layout.Units.mm, margins=layout.Margins.all(5)))

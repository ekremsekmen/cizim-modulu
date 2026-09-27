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
kesitler ( 1/50 ), sonra planlar ve detay kesitler ( 1/20 ) konu sırasıyla
sütunlara dizilir;  çizim sütuna sığmazsa yeni sütun açılır.  Düşey
kesitler paftanın yüksekliğine sığmazsa ara katlar kırılır ( ELEport ve
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

from cizim import cizimler as CZ
from cizim import dxf as CDX
from cizim import dusey as CDU
from cizim import geometri as CGE

SABLON = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "sablon", "proje_formati.dxf")
#  Şablonun kendi koordinatları ( pafta mm ) — hesap programının dxf_export.py
#  sabitleriyle aynı;  şablon değişirse _sablon_dogrula yakalar.
BANT = (-4215.8, 1159.4, -973.8, 1759.4)
KAPAK_HUCRESI = (-4215.8, 1159.4, -4012.5, 1448.3)
SERBEST = (-4012.5, 1159.4, -973.8, 1759.4)
KENAR = 10.0                # serbest alanın kenarından ilk çizime
ARA = 12.0                  # çizimler arası

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
SIRA_MRL = ("kuyu_kesiti_yan", "kuyu_kesiti_on", "kuyu_plani", "kabin_ustu", "kuyu_dibi",
            "kuyu_dibi_kesiti", "kuyu_ustu", "kuyu_ustu_kesiti")
SIRA_MD = ("kuyu_kesiti_yan", "kuyu_kesiti_on", "kuyu_plani", "kabin_ustu", "kuyu_dibi",
           "kuyu_dibi_kesiti", "makine_dairesi", "delik_plani", "kuyu_ustu_kesiti")


def _nokta(e):
    t = e.dxftype()
    if t == "LINE":
        return [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
    if t == "LWPOLYLINE":
        return [(q[0], q[1]) for q in e.get_points("xy")]
    return []


def _sablon_dogrula(d):
    """Dış çerçevenin köşeleri, kapak hücresi ve antetin değer hücreleri yerinde mi."""
    msp = d.modelspace()
    hata = []
    kutular = []
    for e in msp.query("LWPOLYLINE"):
        p = _nokta(e)
        kutular.append((min(q[0] for q in p), min(q[1] for q in p),
                        max(q[0] for q in p), max(q[1] for q in p)))
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
        if abs(p.x - yer[0]) <= 0.2 and abs(p.y - yer[1]) <= 0.2 and \
                (ornek is None or e.dxf.text == ornek):
            return e
    return None


def antet_degerleri(g, olcekler):
    """Antete yazılacaklar;  boş dize = çizimin bilmediği değer ( boş kalır )."""
    dy, kb, kr = g["dusey"], g["kabin"], g["kabin_ray"]
    kotlar = CDU.durak_kotlari(g)[0]
    return {
        "yuk": "", "sinif": "", "motor": "",
        "hiz": f"{dy['beyan_hizi']:.2f} m/sn".replace(".", ","),
        "durak": f"{dy['durak_adedi']} DURAK",
        "seyir": f"{kotlar[-1]:g}",
        "kabin_g": f"{kb['genislik']:g}", "kabin_d": f"{kb['derinlik']:g}",
        "standart": "TS EN 81-20",
        "aski": "1:1" if (g.get("aski") or {}).get("duzen") == "Doğrudan" else "2:1",
        "adet": "1", "tahrik": "Elektrikli",
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


def cizim_listesi(g):
    """( ad, başlık, ölçek, elemanlar — çerçeveli ) ;  hata varsa ValueError."""
    oda = (g.get("makine") or {}).get("yeri") == "Makine dairesi"
    cikti, hata = [], []
    #  Serbest alanın yüksekliği ( kenarlar düşülünce ), çizim biriminde
    yukseklik = SERBEST[3] - SERBEST[1] - 2 * KENAR
    for ad in (SIRA_MD if oda else SIRA_MRL):
        dogrula, ciz, baslik = CZ.CIZIMLER[ad]
        h = dogrula(g)
        if h:
            hata += [f"{ad}: {x}" for x in h]
            continue
        olcek = CZ.OLCEKLER.get(ad, 20)
        e = ciz(g, azami=yukseklik * olcek) if ad in CZ.OLCEKLER else ciz(g)
        cikti.append((ad, CZ.plan_basligi(g, ad, baslik), olcek,
                      CGE.cerceveli(e, CZ.plan_basligi(g, ad, baslik), olcek)))
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


def _yerlestir(d, g, x0=None, sag_eski=None):
    """Çizimleri belgeye blok olarak yerleştirir;  gerekirse çerçeveyi uzatır."""
    CDX.hazirla(d)
    cizimler = cizim_listesi(g)
    boyutlar, kutular = [], []
    for ad, baslik, olcek, e in cizimler:
        bx0, by0, bx1, by1 = CGE.sinir(e)
        kutular.append((bx0, by0))
        boyutlar.append(((bx1 - bx0) / olcek, (by1 - by0) / olcek))
    yerler, sag = yerlesim(boyutlar, x0, sag_eski)
    _cerceveyi_uzat(d, sag, sag_eski)
    msp = d.modelspace()
    yerlesen = []
    for (ad, baslik, olcek, e), (bx, by), (px, py), (w, h) in zip(cizimler, kutular, yerler, boyutlar):
        blok = d.blocks.new(name=f"CIZIM_{ad.upper()}", base_point=(bx, by))
        CDX.ciz(blok, e, olcek)
        msp.add_blockref(blok.name, (px, py), dxfattribs={"xscale": 1.0 / olcek, "yscale": 1.0 / olcek,
                                                           "layer": "0"})
        yerlesen.append({"ad": ad, "baslik": baslik, "olcek": olcek, "kutu": (px, py, px + w, py + h)})
    x0_, y0_, x1_, y1_ = BANT[0], BANT[1], sag, BANT[3]
    msp.dxf.extmin, msp.dxf.extmax = (x0_, y0_, 0), (x1_, y1_, 0)
    msp.dxf.limmin, msp.dxf.limmax = (x0_, y0_), (x1_, y1_)
    zoom.window(msp, (x0_ - 10, y0_ - 10), (x1_ + 10, y1_ + 10))
    return {"cizimler": yerlesen, "sag": sag, "olcekler": [c[2] for c in cizimler]}


def belge(g):
    """Doldurulmuş pafta ( ezdxf belgesi ) ve yerleşim bilgisi."""
    d = ezdxf.readfile(SABLON)
    _sablon_dogrula(d)
    _katmanlari_onar(d)
    bilgi = _yerlestir(d, g)
    _antet(d, g, bilgi["olcekler"])
    return d, bilgi


def birlestir(hesap_dxf, g):
    """TAM PROJE:  hesap programının TİP PROJE FORMATINA dizdiği DXF'e
    ( kapak + hesap sayfaları ) çizimleri ekler — son hesap sayfasının
    sağından başlayarak;  çerçeve gerekirse sağa uzar.  Antete dokunulmaz:
    hesap programının kapağı onun yerindedir.

    hesap_dxf:  dosya yolu.  Dönen:  ( belge, bilgi )."""
    d = ezdxf.readfile(hesap_dxf)
    msp = d.modelspace()
    #  Çerçevenin şimdiki sağ kenarı:  üst kenar çizgisinin en sağ ucu
    ust = [p.x for e in msp.query("LINE") for p in (e.dxf.start, e.dxf.end)
           if abs(p.y - BANT[3]) <= 0.5]
    if not ust or min(ust) > BANT[0] + 0.5:
        raise ValueError("Hesap DXF'inde TİP PROJE FORMATI çerçevesi bulunamadı.")
    sag_eski = max(ust)
    #  Hesap sayfalarının sağı:  A4 çerçevelerinin ( hesap programının
    #  AVAN-A4 katmanı ) en sağ ucu
    sayfalar = [q[0] for e in msp.query('LWPOLYLINE LINE[layer=="AVAN-A4"]') for q in _nokta(e)]
    x0 = max(sayfalar) if sayfalar else SERBEST[0]
    _katmanlari_onar(d)
    bilgi = _yerlestir(d, g, x0, sag_eski)
    bilgi["hesap_sagi"] = x0
    return d, bilgi


def yaz(g) -> bytes:
    d, _ = belge(g)
    with tempfile.TemporaryDirectory() as klasor:
        yol = os.path.join(klasor, "pafta.dxf")
        d.saveas(yol)
        with open(yol, "rb") as f:
            return f.read()


def onizleme(d) -> str:
    """Paftanın SVG önizlemesi ( ezdxf'in kendi çizicisiyle, DXF'ten ) —
    ekranda görmek için;  asıl çıktı DXF'tir."""
    from ezdxf.addons.drawing import Frontend, RenderContext, config, layout, svg
    arka = svg.SVGBackend()
    ayar = config.Configuration(background_policy=config.BackgroundPolicy.WHITE,
                                color_policy=config.ColorPolicy.COLOR)
    Frontend(RenderContext(d), arka, config=ayar).draw_layout(d.modelspace())
    return arka.get_string(layout.Page(0, 0, layout.Units.mm, margins=layout.Margins.all(5)))

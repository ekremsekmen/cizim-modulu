# -*- coding: utf-8 -*-
"""
ÇİZİM  →  DXF   ( CAD )

SVG ile AYNI eleman listesini okur.  Birim milimetredir;  AutoCAD dosyayı
1:1 açar, ölçek yalnız paftaya yerleştirirken kullanılır.

KATMAN DÜZENİ:  her eleman türü kendi katmanına girer ki CAD'de katman
katman kapatılabilsin.  Renkler ACI numarasıdır.
"""

import io
import re
from decimal import ROUND_HALF_UP, Decimal

import ezdxf
from ezdxf.enums import TextEntityAlignment

from cizim import geometri
from cizim import uslup

#  Katmanların rengi ( ACI ), kalınlığı ( 1/100 mm ) ve çizgi tipi
#  cizim/uslup.py'de — ekranla aynı tablo.  Ölçü katmanı CAMGÖBEĞİ ( 4 ):
#  AutoCAD'in koyu zemininde mavi ( 5 ) ölçü yazıları zor okunuyordu
#  ( kullanıcı 5 Eki );  ölçünün çizgisi ve yazısı katmanın rengini alır
#  ( dimclr* BYLAYER ) — katmanın rengini değiştirmek hepsini değiştirir.
#  Önizleme ( beyaz zemin ) ölçüleri mavi çizer.
YAZI_TIPI = "ASANSOR"
#  Yazı yüksekliği:  geometri yazının boyunu SVG'deki gibi EM ( font-size ) olarak
#  verir;  DXF'te TEXT ve ölçü yazısı yüksekliği BÜYÜK HARF yüksekliğidir.  Arial'de
#  büyük harf = 0,716 em ( 1467 / 2048 ).  Çarpılmazsa DXF yazısı 1,4 kat büyük
#  çıkıyor, yerleşimin ayırdığı yere sığmıyordu ( pafta ve DWG'de yazılar birbirine
#  ve kutularına biniyordu ).
BUYUK_HARF = 0.716


def _katmanlari_kur(d):
    for ad, k in uslup.KATMAN.items():
        if ad not in d.layers:
            d.layers.add(ad)
        katman = d.layers.get(ad)
        katman.dxf.color = k.aci
        katman.dxf.lineweight = round(k.kalinlik * 100)
        katman.dxf.linetype = uslup.DESENLER[k.desen].dxf if k.desen else "Continuous"


def _cizgi_tiplerini_kur(d):
    """AutoCAD'in ISO çizgi tipleri ( acadiso.lin'deki tanımlarıyla )."""
    for ad, des in uslup.DESENLER.items():
        if des.dxf not in d.linetypes:
            d.linetypes.add(
                des.dxf,
                pattern=[sum(abs(v) for v in des.tanim), *des.tanim],
                description=f"ISO ( {ad.lower()} )",
            )


def _dikdortgen(msp, el, lt=None):
    x, y, g, h = el["x"], el["y"], el["g"], el["d"]
    msp.add_lwpolyline(
        [(x, y), (x + g, y), (x + g, y + h), (x, y + h)],
        close=True,
        dxfattribs={"layer": el["katman"], **(lt or {})},
    )


def _bicim(hedef, el, lt=None):
    """Parçanın gerçek biçimi ( parcalar ):  LWPOLYLINE ( kapalı çokgen ya da
    açık sac profil );  "dolu" kesit katmanının renginde SOLID taramayla
    boyanır;  "ince" ayrıntı 0,18 mm çizgi kalınlığıyla."""
    for p in el["bicim"]:
        nok = [(float(x), float(y)) for x, y in p["noktalar"]]
        ek = {"lineweight": round(uslup.INCE * 100)} if p.get("ince") else {}
        hedef.add_lwpolyline(
            nok, close=p.get("kapali", True), dxfattribs={"layer": el["katman"], **(lt or {}), **ek}
        )
        if p.get("dolu"):
            dolgu = hedef.add_hatch(color=256, dxfattribs={"layer": el["katman"]})
            dolgu.paths.add_polyline_path(nok, is_closed=True)


#  ÖLÇÜ STİLİ — ölçeğe göre adlı ( "ASANSOR-20", "ASANSOR-50" ):  boylar
#  kâğıtta mm, DIMSCALE ölçek ( AutoCAD'in alışılmış kurulumu;  LiftDesigner'ın
#  "LIFT" stili gibi ).  Eskiden her ölçü ezdxf'in "EZDXF" stilinde ve 11 alanlık
#  override taşıyordu;  o stilin DIMLFAC'ı 100'dü — AutoCAD'de metni sıfırlayan
#  2100 yerine 210000 görürdü ( 12 Eki ).
#    dimse1 / dimse2:  uzatma çizgisi yok — kısa uzatma çizgisi ucun bloğunda
#    ( UC_BLOGU;  uzun uzatma çizgileri planı kesiyordu — kullanıcı kararı ).
#    dimtxsty:  çizimin Arial'i ( ezdxf'in OpenSans'ını AutoCAD bulamayıp
#    simplex.shx'e düşürüyordu — 5 Eki ).  dimtfill:  yazının arkası zemin
#    rengiyle örtülür ( MASKE ).  dimclr* 256 ( BYLAYER ):  çizgi, uç ve yazı
#    OLCU katmanının rengini alır — katmanın rengi hepsini değiştirir.  BYBLOCK
#    ( 0 ) AutoCAD'de de aynı sonucu verir ama ezdxf'in önizlemesi ( ve başka
#    görüntüleyiciler ) onu beyaz çiziyordu.
#    dimdsep "," · dimzin 8:  "1022,5", "2100" ( sondaki sıfırlar yazılmaz ).
UC_BLOGU = "ASANSOR_UC"
OLCU_ONDALIK = 1


def _uc_blogu(d):
    """Ölçü ucu:  45° eğik çizgi + dik kısa uzatma çizgisi.  Birim boyda
    ( DIMASZ = 2 · TIK ile büyür ), AutoCAD ucu ölçü çizgisi yönünde döndürür."""
    if UC_BLOGU in d.blocks:
        return
    b = d.blocks.new(UC_BLOGU)
    s = uslup.SAPLAMA / (2 * uslup.TIK)
    #  0 katmanında, ByLayer:  ucun INSERT'inin katmanını ( OLCU ) alır
    b.add_line((-0.5, -0.5), (0.5, 0.5), dxfattribs={"lineweight": round(uslup.TIK_KALEM * 100)})
    b.add_line((0, -s), (0, s), dxfattribs={"lineweight": round(uslup.KATMAN["OLCU"].kalinlik * 100)})


def olcu_stili(d, olcek):
    """Ölçeğin ölçü stilinin adı ( yoksa kurar )."""
    ad = f"ASANSOR-{olcek:g}"
    if ad in d.dimstyles:
        return ad
    _uc_blogu(d)
    stil = d.dimstyles.new(
        ad,
        dxfattribs={
            "dimscale": olcek,
            "dimtxt": uslup.kagitta(uslup.NORMAL, 20),
            "dimtxsty": YAZI_TIPI,
            "dimasz": 2 * uslup.TIK,
            "dimgap": uslup.OLCU_BOSLUGU,
            "dimexe": 0.0,
            "dimexo": 0.0,
            "dimse1": 1,
            "dimse2": 1,
            "dimtad": 0,
            "dimtih": 0,
            "dimtoh": 0,
            "dimtmove": 2,
            "dimtfill": 1,
            "dimclrd": 256,
            "dimclre": 256,
            "dimclrt": 256,
            "dimlunit": 2,
            "dimdec": OLCU_ONDALIK,
            "dimzin": 8,
            "dimdsep": ord(","),
            "dimlfac": 1.0,
            #  dimrnd yazılmaz:  AutoCAD'de 0 "yuvarlama yok", ezdxf'in çizicisi
            #  0'ı tam sayıya yuvarlıyordu ( önizlemede 1022,5 → 1022 )
        },
    )
    stil.set_arrows(blk=UC_BLOGU)
    return ad


_SAYI = re.compile(r"\d+(?:,\d+)?")


def _olculen(uzunluk):
    """AutoCAD'in yazacağı değer ( OLCU_ONDALIK basamak, sondaki sıfırsız, virgül )."""
    v = Decimal(repr(float(uzunluk))).quantize(Decimal(1).scaleb(-OLCU_ONDALIK), rounding=ROUND_HALF_UP)
    m = format(v, "f").rstrip("0").rstrip(".")
    return m.replace(".", ",")


def olcu_metni(el):
    """Ölçünün DXF metni:  yazıdaki sayı ölçülen değerse onun yerine "<>" —
    AutoCAD kendisi ölçer, çizim uzatılınca sayı da değişir ( LiftDesigner
    "SW<>" ).  Değilse ( kırık kesitte "3 × 3000" ) yazı olduğu gibi."""
    deger = _olculen(el["uzunluk"])
    for m in _SAYI.finditer(el["metin"]):
        if m.group() == deger:
            return el["metin"][: m.start()] + "<>" + el["metin"][m.end() :]
    return el["metin"]


def _olcu(hedef, el, olcek):
    """Gerçek DIMENSION varlığı — CAD'de ölçü olarak tanınır, metin değil."""
    a, b, kot = el["a"], el["b"], el["kot"]
    #  Tanım noktaları ölçü çizgisinin üstünde:  geometri ölçülmeyen ekseni 0
    #  verir ( uzatma çizgileri çizilmez — dimse1/2 ).  Eskiden noktalar o 0'da
    #  kalıyordu:  kuyunun tepesindeki kasnak düzenlemesinin ölçüleri 25 m
    #  aşağıya uzanıyor, AutoCAD açılışta paftayı 1,2 m boşlukla küçültüyordu.
    if el["yon"] == "yatay":
        p1, p2 = (a[0], kot), (b[0], kot)
        aci = 0
    else:
        p1, p2 = (kot, a[1]), (kot, b[1])
        aci = 90
    yz = el["yazi"]
    #  Yazı boyu stilin boyu değilse ( ölçeğin 2,5 mm'si ) yalnız o ölçüde
    ozel = {}
    if abs(yz["h"] - uslup.NORMAL * olcek / 20.0) > 1e-6:
        ozel["dimtxt"] = uslup.kagitta(yz["h"], olcek)
    #  Yazı geometrinin bulduğu yerde durur  ( SVG ile aynı merkez ).
    olcu = hedef.add_linear_dim(
        base=p1,
        p1=p1,
        p2=p2,
        angle=aci,
        location=(yz["x"], yz["y"]),
        text_rotation=yz["aci"],
        text=olcu_metni(el),
        dimstyle=olcu_stili(hedef.doc, olcek),
        dxfattribs={"layer": "OLCU"},
        override=ozel or None,
    )
    olcu.render()


#  YAZI MASKESİ:  çizgi yazının üstünden geçmez, yazının olduğu yerde kesilir
#  ( ISO 128 ).  Eksen çizgileri, gizli çizgiler, tarama ve komşu ölçülerin
#  çizgileri yazıların içinden geçiyordu ( "KABİN 1350 x 1400" kabinin iki
#  ekseninin kesiştiği yerde, "ASKI ARASI" askı ekseninin üstünde — 5 Eki ).
#  Etiket arka planı çizimin zemin rengiyle örtülen MTEXT'tir ( AutoCAD'de
#  "Background Mask · Use drawing background color" ), ölçü yazısı dimtfill.
#  Örtünün yazıdan taşma çarpanı ( AutoCAD:  Border offset factor — uslup ):
MASKE_PAYI = uslup.MASKE_PAYI
_MTEXT_HIZA = {"sol": 4, "sag": 6}  # MIDDLE_LEFT · MIDDLE_RIGHT;  yoksa 5 ( orta )


def _mtext_kacis(metin):
    """MTEXT biçim kodlarını ( \\  {  } ) düz yazıya çevirir."""
    return metin.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def _etiket(hedef, el):
    m = hedef.add_mtext(
        _mtext_kacis(el["metin"]),
        dxfattribs={
            "layer": el["katman"],
            "style": YAZI_TIPI,
            "char_height": el["yukseklik"] * BUYUK_HARF,
            "insert": (el["x"], el["y"]),
            "rotation": el.get("aci", 0),
            "attachment_point": _MTEXT_HIZA.get(el.get("hiza"), 5),
        },
    )
    m.set_bg_color("canvas", scale=MASKE_PAYI)


#  Çizgi tipi ölçeği ( varlığın ltscale'i ):  desen kâğıtta uslup.DESENLER'deki
#  boyda olsun diye
#  * tek başına açılan DXF gerçek ölçüde ( mm ) çizilir — desen çarpanı × ölçek;
#  * paftada çizim 1/ölçek küçültülmüş bir BLOKTUR ve AutoCAD bloğun içindeki
#    çizgi desenini bloğun ölçeğiyle KÜÇÜLTMEZ ( desen dünya biriminde kurulur;
#    LiftDesigner da 0,05'lik bloklarında ltscale 1 kullanır ) — desen çarpanı.
#    Eskiden blokta da ölçek çarpılıyordu:  desen paftada 254 mm oluyor, eksen
#    ve gizli çizgiler AutoCAD'de DÜZ çizgi görünüyordu ( 5 Eki ).
def _cizgi_tipi(el, olcek, blokta):
    """Elemanın çizgi tipi ölçeği ( ve eksen elemanında tipi ) — sürekli çizgide boş."""
    ad = "EKSEN" if el["tip"] == "eksen" else uslup.KATMAN[el["katman"]].desen
    if not ad:
        return {}
    des = uslup.DESENLER[ad]
    ek = {"linetype": des.dxf} if el["tip"] == "eksen" else {}
    return {"ltscale": des.olcek * (1 if blokta else olcek), **ek}


def hazirla(d):
    """Belgeye çizimin katmanlarını ve yazı biçimini ekler ( şablon da olabilir ).

    Yazı biçimi Arial:  dosya adının yanında AİLE ADI da yazılır — AutoCAD
    TrueType'ı önce aileden bulur ( Mac'te dosya adları farklı ).  Çizgi
    kalınlıkları katmanlardadır, baskıda çıkar;  ekranda GÖSTERİLMEZ
    ( LWDISPLAY kapalı — LiftDesigner ve ofis şablonu gibi ):  model alanında
    kalınlık piksel olarak çizildiğinden pafta bütünüyle bakarken duvarlar
    kalın şeritlere, karşı ağırlık bloğa dönüşüyordu ( kullanıcı 5 Eki )."""
    _cizgi_tiplerini_kur(d)
    _katmanlari_kur(d)
    if YAZI_TIPI not in d.styles:
        d.styles.add(YAZI_TIPI, font="arial.ttf")
    d.styles.get(YAZI_TIPI).set_extended_font_data("Arial", bold=False, italic=False)


#  PARÇA BLOKLARI ( 13 Eki — çizim kalitesi 6. adımı ):  adı olan parçanın her
#  örneği kendi adlı bloğunda ( geometri.parca_ornekleri — ekran da aynı örnekleri
#  vurgular ) — AutoCAD'de tıklanınca bütün parça seçilir, adı özelliklerde görünür.


def _blok_adi(d, onek, ad, n):
    ad_ = re.sub(r"[^A-Z0-9_]", "_", f"{onek}_{ad}".upper())
    while f"{ad_}_{n}" in d.blocks:
        n += 1
    return f"{ad_}_{n}"


def ciz(hedef, elemanlar, olcek=20, blokta=False):
    """Elemanları `hedef` yerleşimine ( model alanı ya da blok ) yazar;  adı olan
    parçalar kendi bloklarında ( geometri.parca_ornekleri ).

    blokta:  hedef paftaya 1/ölçek ile eklenen bir blok ( çizgi deseni
    küçülmez — _cizgi_tipi )."""
    d = hedef.doc
    #  Blok adının öneki çizimin adı ( paftada "CIZIM_KUYU_PLANI" → "KUYU_PLANI" )
    onek = "PARCA" if getattr(hedef, "is_modelspace", False) else re.sub(r"^CIZIM_", "", hedef.name)
    ornek = {}
    for ad, liste in geometri.parca_ornekleri(elemanlar):
        for el in liste:
            ornek[id(el)] = (ad, liste)
    yazilan = set()
    sayac = {}
    #  Önce parçalar, sonra ölçüler, en son etiketler:  maske yalnız kendinden
    #  ÖNCE çizileni örter ( AutoCAD'in çizim sırası ).
    sira = {"olcu": 1, "yazi": 2}
    for el in sorted(elemanlar, key=lambda el: sira.get(el["tip"], 0)):
        if id(el) not in ornek:
            _eleman(hedef, el, olcek, blokta)
            continue
        ad, liste = ornek[id(el)]
        if id(liste) in yazilan:
            continue
        yazilan.add(id(liste))
        sayac[ad] = sayac.get(ad, 0) + 1
        x0, y0, _x1, _y1 = geometri.sinir(liste)
        blok = d.blocks.new(name=_blok_adi(d, onek, ad, sayac[ad]), base_point=(x0, y0))
        for p in liste:
            _eleman(blok, p, olcek, blokta)
        hedef.add_blockref(blok.name, (x0, y0), dxfattribs={"layer": "0"})


def _eleman(hedef, el, olcek, blokta):
    """Tek elemanı `hedef`e yazar."""
    k = olcek / 20.0  # ok ve boşluklar 1/20'ye göre
    tur, kat = el["tip"], el["katman"]
    lt = _cizgi_tipi(el, olcek, blokta)
    if tur == "dikdortgen" and "bicim" in el:
        _bicim(hedef, el, lt)
    elif tur in ("dikdortgen", "tarama", "tarama_tugla"):
        _dikdortgen(hedef, el, lt)
        if tur in ("tarama", "tarama_tugla"):
            #  Duvar kesiti taraması:  CAD'in kendi HATCH varlığı
            tarama = hedef.add_hatch(color=uslup.KATMAN[kat].aci, dxfattribs={"layer": kat})
            tarama.set_pattern_fill(uslup.TARAMALAR[tur].dxf, scale=uslup.tarama_olcegi(tur, olcek))
            tarama.paths.add_polyline_path(
                [
                    (el["x"], el["y"]),
                    (el["x"] + el["g"], el["y"]),
                    (el["x"] + el["g"], el["y"] + el["d"]),
                    (el["x"], el["y"] + el["d"]),
                ],
                is_closed=True,
            )
    elif tur in ("cizgi", "eksen"):
        hedef.add_line(
            (el["x1"], el["y1"]),
            (el["x2"], el["y2"]),
            dxfattribs={"layer": kat, **lt},
        )
    elif tur == "daire":
        hedef.add_circle((el["x"], el["y"]), el["r"], dxfattribs={"layer": kat, **lt})
    elif tur == "ok":
        hedef.add_line((el["x1"], el["y1"]), (el["x2"], el["y2"]), dxfattribs={"layer": kat})
        dx, dy = el["x2"] - el["x1"], el["y2"] - el["y1"]
        boy = max((dx * dx + dy * dy) ** 0.5, 1e-6)
        ux, uy, u = dx / boy, dy / boy, 55 * k
        hedef.add_solid(
            [
                (el["x2"], el["y2"]),
                (el["x2"] - ux * u - uy * u * 0.4, el["y2"] - uy * u + ux * u * 0.4),
                (el["x2"] - ux * u + uy * u * 0.4, el["y2"] - uy * u - ux * u * 0.4),
            ],
            dxfattribs={"layer": kat},
        )
    elif tur == "olcu":
        _olcu(hedef, el, olcek)
    elif tur == "yazi":
        _etiket(hedef, el)


def belge(elemanlar, baslik="", olcek=20):
    """Eleman listesinden ezdxf belgesi kurar."""
    #  setup YOK:  ezdxf'in hazır kurulumu 25 yazı stili ( OpenSans, Liberation …
    #  — AutoCAD açılışta 20'sini bulamayıp simplex.shx'e düşürüyordu ), 12 ölçü
    #  stili getiriyordu.  Gerekenleri hazirla kurar ( 12 Eki ).
    d = ezdxf.new("R2018")
    d.header["$INSUNITS"] = 4  # milimetre
    hazirla(d)
    msp = d.modelspace()
    ciz(msp, elemanlar, olcek)
    if baslik:
        x1 = min(el.get("x", el.get("x1", 0)) for el in elemanlar if el["tip"] != "olcu")
        y1 = min(el.get("y", el.get("y1", 0)) for el in elemanlar if el["tip"] != "olcu")
        msp.add_text(
            f"{baslik}   1/{olcek:g}",
            height=90 * BUYUK_HARF,
            dxfattribs={"layer": "YAZI", "style": YAZI_TIPI},
        ).set_placement((x1, y1 - 400), align=TextEntityAlignment.LEFT)
    return d


def yaz(elemanlar, baslik="", olcek=20) -> bytes:
    """DXF baytları  ( AutoCAD çift tıkla açar )."""
    d = belge(elemanlar, baslik, olcek)
    akis = io.StringIO()
    d.write(akis)
    return akis.getvalue().encode("utf-8")

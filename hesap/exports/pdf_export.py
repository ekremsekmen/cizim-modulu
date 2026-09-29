# -*- coding: utf-8 -*-
"""
PDF DIŞA AKTARIM  —  baskıya hazır pafta / hesap raporu

Sayfa düzeni ofis paftasının işlem akışını izler:  başlık → girdi
satırları → denklem → sayıların yerine konmuş hâli → sonuç → kontrol → notlar.
"""
import io
import threading
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Flowable, Frame, KeepTogether,
                                PageBreak, PageTemplate, Paragraph, Spacer,
                                Table, TableStyle)

from engine.ortak.steps import tr, trn

FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")

# ----------------------------------------------------------------- yazı tipi
def _fontlari_yukle():
    try:
        pdfmetrics.getFont("Gov")
        return "Gov", "Gov-Bold"
    except Exception:
        pass
    adaylar = [
        (os.path.join(FONT_DIR, "DejaVuSans.ttf"), os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("/Library/Fonts/Arial Unicode.ttf", "/Library/Fonts/Arial Unicode.ttf"),
        ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
    ]
    for normal, bold in adaylar:
        if os.path.exists(normal) and os.path.exists(bold):
            pdfmetrics.registerFont(TTFont("Gov", normal))
            pdfmetrics.registerFont(TTFont("Gov-Bold", bold))
            return "Gov", "Gov-Bold"
    return "Helvetica", "Helvetica-Bold"


F, FB = _fontlari_yukle()

# ------------------------------------------------------------------ renkler
# ------------------------------------------------------------------ palet
#  PAFTA SİYAH BEYAZ BASILIR ve AutoCAD'e PDFIMPORT ile alınır.  Bu iki
#  koşul birlikte tasarımı belirler:
#
#   · DOLGU YOK.  Renkli zeminler gri baskıda birbirinden ayrılmaz; AutoCAD'de
#     ise her dolgu bir SOLID/HATCH nesnesine dönüşür ve monokrom çizim
#     ayarında ( monochrome.ctb ) siyah bir bloğa döner.  Zeminin üstündeki
#     BEYAZ yazı da beyaz geometri olarak gelir — beyaz kâğıtta kaybolur.
#     Bu yüzden hiçbir yerde "beyaz yazı / koyu zemin" kullanılmaz.
#   · RENK ANLAM TAŞIMAZ.  Uygun / uygun değil ayrımı SÖZCÜKLE ve ✔ / ✘
#     işaretiyle verilir, yeşil-kırmızı ile değil.
#   · ÇİZGİLER SAÇ TELİ OLMAZ.  0,4 pt'nin altı hem gri baskıda hem
#     plotterda kaybolur; en ince çizgi 0,4 pt'dir.
SIYAH = colors.HexColor("#000000")
MAVI = SIYAH                       # başlık ve formül metni — düz siyah
MAVI_AC = colors.white             # zemin kullanılmıyor
GRI = colors.HexColor("#444444")   # ikincil metin ( kaynak kolonu )
GRI_AC = colors.white              # zemin kullanılmıyor
CIZGI = SIYAH
YESIL = SIYAH
KIRMIZI = SIYAH
SARI_AC = colors.white

#  TABLO GENİŞLİK ÇARPANI
#  Pafta küçültülerek basıldığında ( bkz. _Belge.olcek ) çerçeve 1/olcek
#  büyüklüğünde kurulur.  Tablolar sabit mm genişlikte olduğu için, çarpan
#  uygulanmazsa ortada dar bir sütun hâlinde kalır ve sayfanın iki yanı boş
#  gider.  Bu çarpan tabloları da aynı oranda genişletir; ölçekten sonra
#  tam A4 yazı alanına otururlar.
#
#  İSTEK BAŞINA AYRI DEĞER:  FastAPI'de `def` uç noktalar bir iş parçacığı
#  havuzunda koşar, yani İKİ İNDİRME AYNI ANDA çalışabilir.  Bu çarpan modül
#  düzeyinde tek bir sayı olarak tutulunca, trafik paftası küçültülürken
#  ( _GEN = 1/0,9 ) aynı anda üretilen AVAN paftasının tabloları da o oranda
#  genişliyor ve sayfanın sağından taşıyordu.  Ölçüldü:  eş zamanlı üretilen
#  25 avan PDF'inin 25'i de tek başına üretilenden FARKLI çıkıyordu.
#  ( main.py'deki belirsiz-sayı listesi ile aynı çözüm. )
class _Olcek(threading.local):
    def __init__(self):
        self.gen = 1.0


_OLCEK = _Olcek()


def _w(x):
    return x * _OLCEK.gen


def _c(x):
    """
    ÇİZGİ KALINLIĞI  —  pafta küçültülerek basıldığında ( bkz. _Belge.olcek )
    çizgiler de küçülür ve 0,4 pt istediğimiz çizgi 0,31 pt'ye düşüp SİLİK
    çıkardı.  Genişlik çarpanı ile bölerek son kalınlığın istenen değerde
    kalması sağlanır.
    """
    return x * _OLCEK.gen


S = {
    "h1": ParagraphStyle("h1", fontName=FB, fontSize=13.5, leading=17, textColor=MAVI,
                         alignment=TA_CENTER, spaceAfter=1),
    "h2": ParagraphStyle("h2", fontName=FB, fontSize=9.5, leading=13, textColor=SIYAH),
    "h2k": ParagraphStyle("h2k", fontName=F, fontSize=7.4, leading=9.5, textColor=GRI,
                          alignment=2),
    "alt": ParagraphStyle("alt", fontName=F, fontSize=7.6, leading=10, textColor=GRI,
                          alignment=TA_CENTER),
    "n": ParagraphStyle("n", fontName=F, fontSize=8.2, leading=11.2),
    "nb": ParagraphStyle("nb", fontName=FB, fontSize=8.2, leading=11.2),
    "sag": ParagraphStyle("sag", fontName=FB, fontSize=8.6, leading=11.2, alignment=2),
    "kaynak": ParagraphStyle("kaynak", fontName=F, fontSize=6.9, leading=9, textColor=GRI),
    "formul": ParagraphStyle("formul", fontName=FB, fontSize=8.4, leading=11.5, textColor=MAVI),
    "islem": ParagraphStyle("islem", fontName=F, fontSize=8.2, leading=11.5, textColor=colors.HexColor("#333333")),
    "not": ParagraphStyle("not", fontName=F, fontSize=7.2, leading=9.6, textColor=GRI),
    "sonuc": ParagraphStyle("sonuc", fontName=FB, fontSize=9, leading=12.5, textColor=SIYAH),
    #  Paftanın NİHAİ CEVABI — "1 adet 8 kişilik (630 kg), 1,00 m/s ...".
    #  Sayfadaki en önemli cümle budur; en büyük punto onundur.
    "karar": ParagraphStyle("karar", fontName=FB, fontSize=13, leading=17,
                            alignment=TA_CENTER, textColor=MAVI),
    #  Kararın DAYANAĞI — iki belirleyici ölçüt, sonucun hemen altında.
    "olcut": ParagraphStyle("olcut", fontName=F, fontSize=7.6, leading=10.5,
                            textColor=colors.HexColor("#333333")),
    "olcut_ad": ParagraphStyle("olcut_ad", fontName=FB, fontSize=7.6, leading=10.5,
                               textColor=GRI),
}


_IZINLI = (("<b>", "\x01"), ("</b>", "\x02"), ("<br/>", "\x03"), ("<i>", "\x04"), ("</i>", "\x05"))


def _p(metin, stil="n"):
    """XML kaçışı yapar ama <b>, </b>, <br/>, <i>, </i> etiketlerini korur."""
    if metin is None:
        metin = ""
    s = str(metin)
    for etiket, yer in _IZINLI:
        s = s.replace(etiket, yer)
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    for etiket, yer in _IZINLI:
        s = s.replace(yer, etiket)
    return Paragraph(s, S[stil])


def _kisalt(metin, font, boy, en):
    """Metni verilen genişliğe sığdırır;  sığmazsa sonuna "…" koyar."""
    t = str(metin or "")
    if pdfmetrics.stringWidth(t, font, boy) <= en:
        return t
    while t and pdfmetrics.stringWidth(t + "…", font, boy) > en:
        t = t[:-1]
    return t + "…"


def _isaret_adi(onek, ad):
    """Yürüyen bölüm adı:  "ASANSÖR 2 · Yolcu  ›  4 - Askı halatları"."""
    onek = str(onek or "").strip()
    return f"{onek}  ›  {ad}" if onek else str(ad or "")


# ------------------------------------------------- yürüyen bölüm adı
class _BolumIsareti(Flowable):
    """Görünmez işaret — sayfa altındaki "şu an bu bölümdesiniz" yazısını besler.

    21 sayfalık bir paftada 6. sayfayı açan kişi hangi bölüme baktığını
    göremiyordu:  bölüm başlığı sayfalar önce kalmış olabiliyor.  Bu işaret
    bölüm başlığının hemen önüne konur ve ÇİZİLDİĞİNDE belgeye hangi bölümde
    olduğumuzu söyler.

    SAYFANIN BÖLÜMÜ, SAYFANIN TEPESİNDEKİ BÖLÜMDÜR.  Bir sayfa önceki
    bölümün kuyruğuyla başlayıp ortasında yeni bölüme geçebilir;  o sayfanın
    yazısı BAŞTAKİNİ göstermelidir.  Bu yüzden işaret, yalnız sayfanın
    tepesinde çizildiyse "bu sayfanın bölümü" olur;  aşağıda çizilirse
    yalnız SONRAKİ sayfalar için geçerli olacak "son bölüm"ü günceller.
    """

    width = height = 0

    #  Sayfanın ÜST ŞERİDİ:  bir bölüm bu kadar yukarıda başlıyorsa sayfayı
    #  o bölüm açıyor demektir.  ( asansör bandı + aile bandı + bölüm başlığı
    #  üst üste geldiğinde ilk bölüm işareti tepeden ~23 mm aşağıdadır. )
    UST_SERIT = 30 * mm

    def __init__(self, ad):
        super().__init__()
        self.ad = str(ad or "")

    def wrap(self, *_a):                       # noqa: ANN002
        return (0, 0)

    def draw(self):
        belge = getattr(self.canv, "_belge", None)
        if belge is None:
            return
        if not belge.sayfa_isaretli:
            belge.sayfa_isaretli = True        # bu sayfada ilk söz hakkı
            try:
                _x, y = self.canv.absolutePosition(0, 0)
            except Exception:                                 # noqa: BLE001
                y = 0.0
            #  Sayfa bu bölümle AÇILIYORSA yazı budur.  Değilse sayfanın
            #  tepesinde önceki bölümün kuyruğu vardır ve yazı — sayfa
            #  başında konan taşıma değeri — olduğu gibi kalır.
            #  BELGENİN İLK İŞARETİ her hâlükârda geçerlidir:  ondan önce
            #  hiçbir bölüm yoktur, sayfanın tepesinde uyarı kutusu ya da
            #  aile bandı olsa bile o sayfa bu bölüme aittir.
            if belge.son_bolum is None or y >= belge.ust_sinir - self.UST_SERIT:
                belge.sayfa_bolumu = self.ad
        belge.son_bolum = self.ad


# ---------------------------------------------------------------- belge iskeleti
class _Belge(BaseDocTemplate):
    """
    `olcek` < 1 ise içerik KÜÇÜLTÜLEREK sayfaya sığdırılır.

    Kâğıt yine A4'tür; yalnız iç çerçeve 1/olcek büyüklüğünde kurulur ve
    çizim anında olcek ile küçültülür.  Böylece dizgi daha geniş bir alana
    yapılır ( satırlar daha az kırılır ), sonra tamamı orantılı olarak
    A4 yazı alanına oturur.  Üst bant ve alt bilgi ölçekten etkilenmez —
    onlar gerçek A4 koordinatlarında çizilir.
    """

    def __init__(self, buf, ust_baslik, alt_baslik, olcek=1.0, **kw):
        # Pafta PDF'leri proje antedi taşımaz; bu bilgiler yalnız kapaktadır.
        baslik = ust_baslik
        #  KENAR BOŞLUKLARI DARALDI.  Eskiden içerik 15/15/28/22 mm içeriden
        #  başlıyor, ÜSTÜNE de 12 mm içeriden bir çerçeve dikdörtgeni
        #  çiziliyordu;  DXF'te A4 çerçevesi ile pafta arasında görünen
        #  boşluk buydu.  Dikdörtgen kalktı, içerik A4'ün kendisine oturuyor.
        super().__init__(buf, pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm,
                         topMargin=20 * mm, bottomMargin=16 * mm,
                         title=baslik, author="",
                         subject=alt_baslik, creator="Asansör Proje Programı", **kw)
        self.ust_baslik, self.alt_baslik = ust_baslik, alt_baslik
        self.olcek = k = float(olcek) if olcek else 1.0
        cerceve = Frame(self.leftMargin / k, self.bottomMargin / k,
                        self.width / k, self.height / k, id="ana")
        #  YÜRÜYEN BÖLÜM ADI.  onPage sayfanın BAŞINDA, içerik çizilmeden
        #  çalışır — orada henüz o sayfada hangi bölüm olduğu bilinmez.  Bu
        #  yüzden yazı sayfa BİTİMİNDE ( onPageEnd ) konur;  o an
        #  _BolumIsareti işaretleri çizilmiş olur.
        self.son_bolum = None          # en son çizilen bölüm ( sayfalar arası taşınır )
        self.sayfa_bolumu = None       # bu sayfanın TEPESİNDEKİ bölüm
        self.sayfa_isaretli = False    # bu sayfada işaret çizildi mi
        self.ust_sinir = A4[1] - self.topMargin
        self.addPageTemplates([PageTemplate(id="std", frames=cerceve,
                                            onPage=self._sayfa,
                                            onPageEnd=self._sayfa_sonu)])

    def _sayfa_sonu(self, cnv, doc):    # noqa: ARG002
        """Sayfanın bölümünü alt şeride yazar  ( içerik çizildikten sonra )."""
        ad = self.sayfa_bolumu
        if not ad:
            return
        #  YAZI ALT ŞERİTTEDİR, üstte değil:  üst şeridin ortasında 100 mm
        #  genişliğinde pafta başlığı durur ( sol kenarı 55 mm ), yanına ancak
        #  40 mm sığardı — bölüm adı sürekli kırpılırdı.  Alt şeritte sayfa
        #  numarasının karşısında 150 mm boş yer var ve okuyucu zaten sayfa
        #  numarasına bakarken görüyor.
        cnv.saveState()
        cnv.setFillColor(GRI)
        cnv.setFont(F, 6.4)
        cnv.drawString(14 * mm, 6.6 * mm, _kisalt(ad, F, 6.4, 150 * mm))
        cnv.restoreState()

    #  reportlab'in onPage geri çağrısı ( canvas, doc ) imzasıyla çağrılır;
    #  `doc` bu paftada kullanılmaz ama imzadan çıkarılamaz.
    def _sayfa(self, cnv, doc):        # noqa: ARG002
        """
        PAFTA ÇERÇEVESİ  —  ofisin kendi paftasındaki düzen:
        tüm hesap kalın bir çerçeve içinde, üstte tek başlık şeridi,
        altta sayfa numarası.  Dolgu yoktur; yalnız çizgi.
        """
        cnv._belge = self          # _BolumIsareti buradan belgeye ulaşır
        #  Yeni sayfa, önceki sayfanın bölümüyle AÇILIR;  sayfanın tepesinde
        #  yeni bir bölüm başlıyorsa işaret bunu değiştirir.
        self.sayfa_bolumu = self.son_bolum
        self.sayfa_isaretli = False
        cnv.saveState()
        w, h = A4
        sol, sag = 14 * mm, w - 14 * mm
        #  SAYFA ÇERÇEVESİ ÇİZİLMEZ.  Eskiden 12 mm içeriden kalın bir
        #  dikdörtgen vardı;  paftayı bir tablo gibi kutuluyordu, sayfa başına
        #  dört çizgi ediyordu ve DXF'te A4 çerçevesinin içinde ikinci bir
        #  çerçeve olarak görünüp aradaki boşluğu yaratıyordu.  Sayfanın
        #  sınırını A4'ün kendisi ve DXF şablonundaki çerçeve gösterir.
        #  Kalan iki çizgi GERÇEK bir ayrım yapar:  başlığın altı ve
        #  sayfa numarasının üstü.
        cnv.setStrokeColor(SIYAH)
        cnv.setFillColor(SIYAH)
        cnv.setFont(FB, 12)
        cnv.drawCentredString((sol + sag) / 2, h - 13.6 * mm, self.ust_baslik)
        cnv.setLineWidth(0.8)
        cnv.line(sol, h - 16.6 * mm, sag, h - 16.6 * mm)
        #  Alt şerit: sayfa numarası ( sağda ), üstünde çizgi
        alt = 0.0
        cnv.line(sol, alt + 11.0 * mm, sag, alt + 11.0 * mm)
        cnv.setFillColor(GRI)
        cnv.setFont(F, 6.4)
        #  KAYNAK DİZESİ PAFTAYA BASILMAZ.  Standart ve baskı bilgisi zaten her
        #  hesap satırının "kaynak" kolonunda yazılı; alt bilgide tekrarlanması
        #  paftayı kalabalıklaştırıyordu.  Bilgi dosyanın ÖZELLİKLERİNDE
        #  ( subject ) taşınmaya devam eder.
        cnv.drawRightString(sag, alt + 6.6 * mm, f"Sayfa {cnv.getPageNumber()}")
        cnv.restoreState()
        #  Çerçeve içeriği bundan sonra çizilir; ölçek yalnız ONU etkiler.
        #  Sayfa değişiminde çizim durumu sıfırlandığı için her sayfada
        #  yeniden uygulanır.
        if self.olcek != 1.0:
            cnv.scale(self.olcek, self.olcek)


def _baslik_seridi(metin, kaynak=""):
    #  Yükseklik SABİT DEĞİLDİR: uzun bir bölüm başlığı iki satıra düştüğünde
    #  şerit de büyür, yoksa ikinci satır mavi bandın dışına taşıyordu.
    #  Dolgu yerine KURAL ÇİZGİSİ: üstte kalın, altta ince.  Baskıda ve
    #  AutoCAD'de aynı görünür, siyah blok üretmez.
    t = Table([[_p(metin, "h2"), _p(kaynak, "h2k")]],
              colWidths=[_w(108 * mm), _w(72 * mm)])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        #  Kutu değil, İKİ KURAL:  üstte kalın ( bölümün başladığı yer ),
        #  altta ince ( başlığı satırlardan ayırır ).  Kutu dört çizgi ederdi,
        #  ikisi her bölümde gereksizdi.
        ("LINEABOVE", (0, 0), (-1, 0), _c(1.1), SIYAH),
        ("LINEBELOW", (0, 0), (-1, 0), _c(0.4), SIYAH),
        ("TOPPADDING", (0, 0), (-1, -1), 3.4), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.0),
        ("LEFTPADDING", (0, 0), (0, 0), 3), ("RIGHTPADDING", (1, 0), (1, 0), 3),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
    ]))
    return t


# ------------------------------------------------------------ adım tabloları
def _adim_tablosu(adimlar):
    """
    veri  satırı : sembol | açıklama | = | değer | birim | kaynak
    hesap satırı : denklem (tam genişlik)  +  '= sayılar'  |  sonuç | birim | kaynak
    """
    veriler, stil, i = [], [], 0
    for j, a in enumerate(adimlar):
        tip = a.get("tip")
        bas = i                       # bu adımın ilk satırı
        if tip == "metin":
            #  KARAR SATIRI mı, ALT BAŞLIK mı?  kontrol() adımında `aciklama`
            #  karşılaştırmanın KENDİSİDİR ( "Dt / dh = 36,92 ≥ 40" ) ve vurgu
            #  açıktır;  metin() alt başlığında ise aciklama boştur.  İkisi de
            #  aynı biçimde basılıyordu:  karar satırı alt başlık gibi
            #  görünüyor, KARŞILAŞTIRMA ise paftaya hiç geçmiyordu — oysa
            #  denetime giden çıktıda kararın dayanağı görünmelidir.
            if a.get("vurgu") and str(a.get("aciklama") or "").strip():
                veriler.append(["", _p(a["aciklama"], "n"), "",
                                _p(f"<b>{a['deger']}</b>", "sag"), "", ""])
                stil += [("SPAN", (1, i), (2, i)), ("SPAN", (3, i), (5, i)),
                         ("TOPPADDING", (0, i), (-1, i), 1.4),
                         ("BOTTOMPADDING", (0, i), (-1, i), 4.6)]
                i += 1
                continue
            veriler.append([_p(f"<b>{a['deger']}</b>", "n"), "", "", "", "", ""])
            stil += [("SPAN", (0, i), (2, i)),
                     ("TOPPADDING", (0, i), (-1, i), 4), ("BOTTOMPADDING", (0, i), (-1, i), 3)]
            i += 1
            #  ALT BAŞLIK ile ardındaki ilk birim AYRILMAZ: "A - KUYU ALT
            #  BOŞLUĞU TABANINA GELEN KUVVET" bir sayfanın dibinde, denklemi
            #  öbür sayfada kalmasın.
            if j + 1 < len(adimlar):
                stil.append(("NOSPLIT", (0, bas), (-1, bas +
                             (2 if adimlar[j + 1].get("tip") == "hesap" else 1))))
            continue
        if tip == "hesap":
            veriler.append([_p(a["formul"], "formul"), "", "", "", "", ""])
            stil += [("SPAN", (0, i), (2, i)), ("TOPPADDING", (0, i), (-1, i), 5),
                     ("BOTTOMPADDING", (0, i), (-1, i), 0)]
            i += 1
            veriler.append(["", _p(a["islem"], "islem"), "",
                            _p(a["metin"], "sag"), _p(a["birim"], "n"), _p(a["kaynak"], "kaynak")])
            stil += [("SPAN", (1, i), (2, i)),
                     ("BOTTOMPADDING", (0, i), (-1, i), 4),
                     #  DENKLEM ile sayıların yerine konmuş hâli AYRILMAZ.
                     ("NOSPLIT", (0, bas), (-1, i))]
            i += 1
            continue
        veriler.append([_p(f"<b>{a['sembol']}</b>", "n"), _p(a["aciklama"], "n"),
                        _p("=", "n") if a["sembol"] or a["aciklama"] else "",
                        _p(a["metin"], "sag"), _p(a["birim"], "n"), _p(a["kaynak"], "kaynak")])
        i += 1

    #  IZGARA YOK.  Hesap satırları bir çizelge değil, okunacak bir metindir:
    #  yapıyı HİZA ve TİPOGRAFİ taşır, çizgi değil.  Eskiden her satırın altı
    #  çizgiliydi, tablo kutuluydu ve değer / kaynak kolonları dikey
    #  ayraçlarla bölünüyordu — sayfa başına 46 çizgi ediyordu ve pafta
    #  hesap yerine hesap TABLOSU gibi görünüyordu.  O çizgilerin hepsi
    #  DXF'e de birebir geçiyor, CAD'de gereksiz binlerce nesne yaratıyordu.
    #
    #  Kalan tek yapısal çizgi bölüm başlığının altı ile SONUÇ şerididir
    #  ( bkz. _baslik_seridi · _sonuc_kutusu ) — onlar gerçekten bir sınır
    #  gösterir.  Satır aralığı biraz açıldı ki çizgisiz de ayrışsınlar.
    #  DEĞER SÜTUNU GENİŞ.  30 mm iken "1.450 × 1.350" ve "Altı Kesik V
    #  Kanal" gibi değerler ikiye bölünüyordu;  sayı sütununda satır kırılması
    #  okumayı bozar.
    #  SEMBOL SÜTUNU 13 mm iken "Nequiv (t)" ikiye düşüyordu;  sembol tek
    #  satırda okunmalı, açıklama sütunu 3 mm'yi rahat verir.
    t = Table(veriler, colWidths=[_w(16 * mm), _w(75 * mm), _w(5 * mm),
                                  _w(40 * mm), _w(14 * mm), _w(30 * mm)])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.9), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.9),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
    ] + stil))
    return t


def _sonuc_kutusu(sonuc):
    if not sonuc:
        return None
    _bas = str(sonuc.get("baslik", "SONUÇ"))
    _hkm = str(sonuc.get("metin", ""))
    #  BAŞLIK SÜTUNU KENDİ İÇERİĞİNE GÖRE.  Sabit genişlikte iki dert birden
    #  çıkıyordu:  dar tutulunca "KONTROL Amin ≤ Akabin ≤ Amax" ikiye düşüyor,
    #  geniş tutulunca hükmün kendisi ( "… olduğundan temel topraklaması
    #  yeterlidir." 126 mm ) kırılıyordu.  Ölçü yazının gerçeğinden alınır.
    _bg = pdfmetrics.stringWidth(_bas, FB, 9) + 4 * mm
    #  ÇOK UZUN BAŞLIK YAN YANA DİZİLMEZ.  "KONTROL Dreg/dreg ≥ 30 · Fçekme ≥
    #  max( 300 N ; 2 × 1.000,00 N ) · T'min/F'reg ≥ 8" üç satıra düşüyor ve
    #  yanında tek başına "UYGUNDUR." kalıyordu — okunmuyordu.  Böyle bir
    #  başlık kendi satırını alır, hüküm altına geçer.
    if _bg > 78 * mm:
        satirlar = [[_p(_bas, "sonuc")], [_p(_hkm, "sonuc")]]
        t = Table(satirlar, colWidths=[_w(180 * mm)])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LINEABOVE", (0, 0), (-1, 0), 1.2, SIYAH),
            ("LINEBELOW", (0, 1), (-1, 1), 0.5, SIYAH),
            ("TOPPADDING", (0, 0), (-1, 0), 4), ("BOTTOMPADDING", (0, 0), (-1, 0), 0.5),
            ("TOPPADDING", (0, 1), (-1, 1), 0.5), ("BOTTOMPADDING", (0, 1), (-1, 1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 2), ("LEFTPADDING", (0, 1), (0, 1), 10),
        ]))
    else:
        satirlar = [[_p(_bas, "sonuc"), _p(_hkm, "sonuc")]]
        _bg = max(_bg, 46 * mm)
        t = Table(satirlar, colWidths=[_w(_bg), _w(180 * mm - _bg)])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LINEABOVE", (0, 0), (-1, 0), 1.2, SIYAH),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, SIYAH),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ]))
    ogeler = [Spacer(1, 1.5 * mm), t]
    for alt in sonuc.get("alt", []) or []:
        ogeler.append(_p(alt, "not"))
    return ogeler


def _karar_kutusu(metin, olcutler=None, verdikt=None, uygun=True):  # noqa: ARG001
    """
    Paftanın NİHAİ CEVABI  —  "Toplamda 1 adet 8 kişilik (630 kg), 1,00 m/s
    hızında asansör yapılması uygundur."

    Bu cümle sayfadaki en önemli bilgidir: projeci paftaya baktığında önce
    bunu arar.  Küçük punto bir not satırı olarak değil, sonuç şeridinin
    hemen altında ÇERÇEVELİ ve BÜYÜK yazılır.
    """
    if not metin:
        return []
    #  Uygun / uygun değil ayrımı RENKLE DEĞİL, sözcük ve ✔ / ✘ ile verilir;
    #  çıktı siyah beyazdır.  Kutu dolgusuzdur, yalnız kalın çerçevesi vardır.
    #  SONUÇ ŞERİDİ ve NİHAİ CEVAP tek bloktur — ofis paftasındaki gibi.
    satirlar, stil, sira = [], [], 0
    if verdikt:
        ust = Table([[_p("SONUÇ", "sonuc"), _p(str(verdikt), "sonuc")]],
                    colWidths=[_w(30 * mm), _w(146 * mm)])
        ust.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        satirlar.append([ust])
        stil += [("TOPPADDING", (0, 0), (0, 0), 4), ("BOTTOMPADDING", (0, 0), (0, 0), 4),
                 ("LINEBELOW", (0, 0), (0, 0), _c(0.6), SIYAH)]
        sira = 1
    satirlar.append([_p(str(metin), "karar")])
    stil += [
        ("BOX", (0, 0), (-1, -1), _c(1.4), SIYAH),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, sira), (0, sira), 7), ("BOTTOMPADDING", (0, sira), (0, sira), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]
    #  Kararın dayanağı: hangi ölçüt, hangi sayıyla sağlandı.  Sonuçla AYNI
    #  kutuda durur — bölüm dip notu olarak ayrı yerde aranmasın.
    for i, o in enumerate(olcutler or [], start=sira + 1):
        isaret = "✔" if o.get("uygun") else "✘"
        ic = Table([[_p(f"{isaret}  {o.get('ad','')}", "olcut_ad"),
                     _p(o.get("metin", ""), "olcut")]],
                   colWidths=[_w(22 * mm), _w(142 * mm)])
        ic.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TEXTCOLOR", (0, 0), (0, 0), SIYAH),
        ]))
        satirlar.append([ic])
        stil += [("TOPPADDING", (0, i), (0, i), 0),
                 ("BOTTOMPADDING", (0, i), (0, i), 3 if i == sira + len(olcutler or []) else 0)]
        if i == sira + 1:
            stil.append(("LINEABOVE", (0, i), (0, i), _c(0.5), SIYAH))
    t = Table(satirlar, colWidths=[_w(180 * mm)])
    t.setStyle(TableStyle(stil))
    return [t]


def _notlar(notlar):
    if not notlar:
        return []
    #  Not satırları da bir bütündür: bir cümlenin ortasından sayfa
    #  değişmesin diye hepsi tek blok hâlinde taşınır.
    #  DİKKAT — burada KeepTogether KULLANILMAZ.  İç içe KeepTogether'da
    #  dış blok, iç bloğun yüksekliğini "sonsuz" okur ( wrap 0xffffff döner )
    #  ve sayfada yer olsa bile her seferinde sayfa atlar.  Notlar zaten
    #  bölümün kuyruk bloğunun içinde, tek parça hâlinde taşınıyor.
    #  ÇİFTE MADDE İMİ OLMAZ.  Bazı notlar metnin kendisinde "▪" ya da "⚠"
    #  ile başlıyor;  önüne bir de burası "▪" koyunca "▪  ▪ …" çıkıyordu.
    o = [_p(("" if str(n).lstrip()[:1] in ("▪", "⚠", "•") else "▪  ") + str(n), "not")
         for n in notlar]
    o[0].spaceBefore = 1.2 * mm
    return o


# ------------------------------------------------------- sayfa bölme öbekleri
def _birim_sinirlari(adimlar):
    """
    Adım listesini BÖLÜNMEZ BİRİMLERE ayırır ve ( başlangıç, bitiş ) verir.

    Bir birim:  tek bir veri satırı,  bir denklem ( formül + sayıların yerine
    konmuş hâli ),  ya da bir alt başlık ile hemen ardındaki birim.
    """
    sinir, i, n = [], 0, len(adimlar)
    while i < n:
        j = i + 1
        if adimlar[i].get("tip") == "metin" and j < n:
            j += 1                       # alt başlık, ardındaki birimle bir bütün
        sinir.append((i, j))
        i = j
    return sinir


def _bas_orta_son(adimlar):
    """
    Adımları üçe böler:  BAŞ ( başlıkla birlikte kalacak ilk birim ),
    ORTA ( serbest — sayfayı doldurur, güvenli satırlardan bölünür ),
    SON ( SONUÇ satırıyla birlikte kalacak son birim ).

    Böylece ne bölüm başlığı sayfanın dibinde yalnız kalır, ne de "UYGUNDUR"
    satırı bir sonraki sayfaya tek başına düşer;  arada kalan satırlar ise
    sayfayı sonuna kadar doldurur ( bkz. _adim_tablosu içindeki NOSPLIT ).
    """
    u = _birim_sinirlari(adimlar)
    if not u:
        return [], [], []
    if len(u) == 1:
        return adimlar, [], []
    return adimlar[:u[0][1]], adimlar[u[0][1]:u[-1][0]], adimlar[u[-1][0]:]


#  Bir bölümün TAMAMI bu alana sığıyorsa sayfaya bölünmeden basılır.
#  ( A4 eksi kenar boşlukları — bkz. _Belge.__init__ )
SAYFA_ALANI = (A4[0] - 28 * mm, A4[1] - 36 * mm)
#  Bir bölüm sayfanın bu kadarından KISAYSA hiç bölünmez.  Sınır yoksa uzun
#  bölümler de bütün hâlde atlar ve arkalarında yarım sayfa boşluk bırakır —
#  bölünmüş bir hesaptan daha kötü görünür.
SAYFA_TAM_ORAN = 0.60


def _yukseklik(akis, gen, yuk):
    """Akışın toplam yüksekliği.  Ölçülemezse None döner ( o zaman bölünür )."""
    toplam = 0.0
    for f in akis:
        try:
            _g, h = f.wrap(gen, yuk)
        except Exception:                                    # noqa: BLE001
            return None
        if h >= 0x7FFFFF:            # KeepTogether ölçülemez
            return None
        toplam += h + float(getattr(f, "spaceBefore", 0) or 0)
    return toplam


def _bolum(b, ust=None, bosluk=None, sayfa=None, onek=None):
    """
    Bir hesap bölümünü basar.

    SAYFA DÜZENİ KURALI —  hiçbir parça yarıda kalmaz:
      · bölüm başlığı ( ve varsa üstündeki asansör başlığı ) İLK birimle,
      · SONUÇ satırı ve notlar SON birimle birlikte yolculuk eder,
      · aradaki satırlar serbesttir, sayfayı doldururlar;  bölünme yalnız
        güvenli satır sınırlarında olur ( _adim_tablosu / NOSPLIT ).
    Parçalar aynı kolon genişliğinde ardışık tablolardır; aralarında boşluk
    olmadığı için baskıda tek bir tablo gibi görünürler.
    """
    #  Başlık ile tablosu ARASINDA boşluk yok: ofis paftasındaki gibi tek
    #  bloktur, başlığın alt çizgisi tablonun üst çizgisidir.
    bas = _baslik_seridi(b["baslik"], b.get("kaynak", ""))
    #  onek None ise sayfa üstü bölüm yazısı istenmiyor demektir ( trafik
    #  paftası tek sayfadır, orada üst yazının anlamı yok ).
    isaret = ([_BolumIsareti(_isaret_adi(onek, b["baslik"]))]
              if onek is not None else [])
    parcalar = [_adim_tablosu(g)
                for g in _bas_orta_son(b.get("adimlar") or []) if g]
    if b.get("cetvel"):
        parcalar.append(_cetvel_tablosu(b["cetvel"]))
    #  Paftada iki liste de basılır: "notlar" bu bölümün sonucuna ait satırlar,
    #  "aciklamalar" yöntemi anlatan bilgi metinleri.  Ekranda ikincisi ⓘ
    #  simgesine toplanır; çıktıda hiçbir şey eksilmez.
    #  PAFTAYA NOT BASILMAZ.  Bölüm biter bitmez SONUÇ gelir.
    #
    #  Eskiden her bölümün altına "notlar" ve "aciklamalar" listeleri birden
    #  basılıyordu:  yöntem anlatımları, kabullerin gerekçeleri, kaynak
    #  kitaptan ayrılma sebepleri…  23 sayfalık bir paftanın 3 sayfası buydu
    #  ve hiçbiri hesabın kendisine bir şey katmıyordu — sayılar zaten
    #  satırlarda, hüküm zaten SONUÇ şeridinde, her satırın dayanağı zaten
    #  kaynak kolonunda yazılı.
    #
    #  BİLGİ KAYBOLMAZ:  ikisi de motorun çıktısında durmaya devam eder ve
    #  ARAYÜZDE bölüm başlığının yanındaki ⓘ altında okunur.  Pafta ise
    #  denetime giden belgedir;  orada hesap olur, ders anlatımı olmaz.
    kuyruk = list(_sonuc_kutusu(b.get("sonuc")) or [])
    ustluk = ([ust] if ust is not None else []) + [bas] + isaret
    #  Bloklar arası boşluk SPACER olarak değil, ilk öğenin "spaceBefore"u
    #  olarak verilir.  ReportLab sayfanın tepesindeki spaceBefore'u yok sayar;
    #  ayrı bir Spacer konsaydı hem her sayfa boşlukla başlar hem de
    #  KeepTogether kendini "sayfa başında değil" sanıp önüne BOŞ SAYFA atardı.
    ustluk[0].spaceBefore = bosluk if bosluk is not None else \
        (6 * mm if ust is not None else 3.2 * mm)

    if not parcalar:
        return [KeepTogether(ustluk + kuyruk)]
    if len(parcalar) == 1:
        return [KeepTogether(ustluk + parcalar + kuyruk)]
    #  BÖLÜM BİR SAYFAYA SIĞIYORSA HİÇ BÖLÜNMEZ.  Baş/orta/son ayrımı yalnız
    #  gerçekten bir sayfadan UZUN bölümler için gerekir;  kısa bir bölümün
    #  başlığı ile ilk denklemi sayfanın dibinde kalıp gerisi öbür sayfaya
    #  geçerse pafta yarım görünür ( denetime giden çıktıda istenmez ).
    if sayfa is not None:
        _tam = _yukseklik(ustluk + parcalar + kuyruk, sayfa[0], sayfa[1])
        if _tam is not None and _tam <= sayfa[1] * SAYFA_TAM_ORAN:
            return [KeepTogether(ustluk + parcalar + kuyruk)]
    return ([KeepTogether(ustluk + [parcalar[0]])]
            + list(parcalar[1:-1])
            + [KeepTogether([parcalar[-1]] + kuyruk)])


def _cetvel_tablosu(cetvel):
    basliklar = ["Lin", "Sorti", "", "Gücü", "Birim", "Sigorta A"]
    veriler = [[_p(f"<b>{x}</b>", "n") for x in basliklar]]
    toplam = 0
    for c in cetvel:
        toplam += c["guc"]
        veriler.append([_p(str(c["lin"]), "n"), _p(c["sorti"], "n"), _p("=", "n"),
                        _p(trn(c["guc"], 0), "sag"), _p(c["birim"], "n"), _p(c["sigorta"], "n")])
    veriler.append(["", _p("<b>ASANSÖRÜN KURULU GÜCÜ</b>", "n"), _p("=", "n"),
                    _p(trn(toplam, 0), "sag"), _p("W", "n"), ""])
    t = Table(veriler, colWidths=[_w(13 * mm), _w(78 * mm), _w(5 * mm),
                                  _w(40 * mm), _w(14 * mm), _w(30 * mm)])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), _c(0.4), CIZGI),
    ]))
    return t


def _uyari_kutusu(metinler, hata=False):
    if not metinler:
        return []
    #  Motor iletileri zaten "⚠ " ile başlayabilir; kutu kendi simgesini
    #  çizdiği için baştaki tekrarı temizliyoruz (çift ⚠ görünmesin).
    def _sadelestir(m):
        m = str(m).lstrip()
        while m[:1] in ("⚠", "✕", "!", "ℹ"):
            m = m[1:].lstrip()
        return m

    def _simge(m):
        if hata:
            return "✕  "
        return "ℹ  " if str(m).lstrip()[:1] == "ℹ" else "⚠  "

    satirlar = [[_p(_simge(m) + _sadelestir(m), "n")] for m in metinler]
    t = Table(satirlar, colWidths=[_w(180 * mm)])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), _c(0.8), SIYAH),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return [Spacer(1, 2 * mm), t]


def _kv_tablo(satirlar, genislikler=(70 * mm, 110 * mm), vurgu_son=False):
    veriler = [[_p(f"<b>{a}</b>", "n"), _p(b, "n")] for a, b in satirlar]
    t = Table(veriler, colWidths=[_w(x) for x in genislikler])
    #  TAM IZGARA DEĞİL, YALNIZ SATIR ÇİZGİLERİ.  Bu iki kolonlu bir
    #  "büyüklük → değer" listesidir;  hesap sayfaları çizgisizken burada tam
    #  ızgara olması paftanın geri kalanıyla ayrışıyordu.  Yatay çizgiler
    #  satırları ayırmaya yeter, dikey ayraç okumaya bir şey katmıyor.
    stil = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 2.9), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.9),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("LINEABOVE", (0, 0), (-1, 0), _c(0.4), CIZGI),
            ("LINEBELOW", (0, 0), (-1, -1), _c(0.4), CIZGI),]
    if vurgu_son:
        stil.append(("LINEABOVE", (0, len(veriler) - 1), (-1, len(veriler) - 1), 0.9, SIYAH))
    t.setStyle(TableStyle(stil))
    return t


# =====================================================================
#  TRAFİK HESABI PDF   (PAFTA / PAFTA-COKLU karşılığı)
# =====================================================================
#  Trafik paftası TEK SAYFA olmalıdır.  İçerik sığmazsa küçültülür.
#  Ölçek büyükten küçüğe denenir ve SIĞAN İLK ( yani en büyük ) ölçek
#  seçilir — yazı gereğinden fazla küçülmesin diye adım 0,02'dir.
#  Alt sınır 0,40: bunun altında okunmaz olurdu, orada iki sayfaya izin verilir.
TRAFIK_OLCEKLERI = tuple(round(1.0 - 0.02 * i, 2) for i in range(31))


def trafik_pdf(sonuc: dict, proje: dict = None) -> bytes:   # noqa: ARG001
    """
    ASANSÖR TRAFİK HESABI paftası  —  her zaman TEK SAYFA.

    ``proje`` eski çağrılarla uyumluluk için kabul edilir, PAFTAYA YAZILMAZ:
    proje antedi paftada değil KAPAK sayfasındadır ( bkz. kapak_export ).

    Pafta SONUÇ ile biter.  İçerik A4'e sığmazsa yazı ve tablolar orantılı
    olarak küçültülür; hiçbir satır atılmaz, ikinci sayfaya taşma olmaz.
    """
    for _olcek in TRAFIK_OLCEKLERI:
        cikti, sayfa = _trafik_bas(sonuc, _olcek)
        if sayfa <= 1:
            return cikti
    return cikti


def _trafik_bas(sonuc: dict, olcek: float):
    """Paftayı verilen ölçekle basar; ( bayt, sayfa adedi ) döner."""
    _OLCEK.gen = 1.0 / (olcek or 1.0)
    try:
        return _trafik_bas_ic(sonuc, olcek)
    finally:
        _OLCEK.gen = 1.0


def _trafik_bas_ic(sonuc: dict, olcek: float):
    coklu = sonuc.get("tip") == "coklu"
    # Başlıklar ofis paftasınınkilerle aynıdır:
    #   aynı tip   -> "ASANSÖR TRAFİK HESABI"
    #   grup       -> "ÇOKLU ASANSÖR TRAFİK HESABI"
    baslik = "ÇOKLU ASANSÖR TRAFİK HESABI" if coklu else "ASANSÖR TRAFİK HESABI"
    buf = io.BytesIO()
    doc = _Belge(buf, baslik,
                 "MMO / 697  “Asansör Avan Projesi Hazırlama Teknik Esasları”, 2. Baskı, Ocak 2020, s.11-17"
                 "   ·   ISO 8100-32:2020   ·   BYKHY md.4",
                 olcek=olcek)
    # Hesap tamamlanamadıysa da geçerli bir belge üretilir; hata paftaya yazılır.
    o = sonuc.get("ozet") or {}
    #  Başlık ÇERÇEVENİN ÜST ŞERİDİNDE yazılır ( _Belge._sayfa ); gövdede
    #  ikinci kez tekrarlanmaz.
    ic = []

    if sonuc.get("hata"):
        ic += _uyari_kutusu([sonuc["hata"]], hata=True)
    if sonuc.get("uyarilar"):
        ic += _uyari_kutusu(sonuc["uyarilar"])

    for b in (sonuc.get("bolumler") or []):
        ic += _bolum(b)

    # çoklu: asansör bazında tablo
    if coklu and sonuc.get("asansorler"):
        ic += [Spacer(1, 3.5 * mm), _baslik_seridi("ASANSÖR BAZINDA HESAP", "MMO/697 s.11-12"),
               Spacer(1, 1.2 * mm), _coklu_tablo(sonuc["asansorler"])]

    #  NÜFUS DÖKÜMÜ PAFTAYA BASILMAZ.  b = Σc değeri ve nasıl bulunduğu
    #  zaten ilk bölümde ( "BİNADA BULUNAN İNSAN SAYISININ TESPİTİ" ) satır
    #  satır yazılı; kalem kalem döküm ekranda durur.  Pafta tek sayfadır.
    # sonuç
    ic += [Spacer(1, 4 * mm)]
    _sonuc_metni = (o.get("sonuc") or sonuc.get("hata")
                    or "Hesap tamamlanamadı — girdileri kontrol edin.")
    #  Burada eskiden bir _sonuc_kutusu ÜRETİLİYOR ama sayfaya hiç
    #  EKLENMİYORDU ( ölü nesne ).  Paftanın sonuç bloğu _karar_kutusu'dur.
    _uygun = not str(_sonuc_metni).startswith(("Kabul", "YETERSİZ", "HESAP"))
    ic += _karar_kutusu(o.get("sonuc_cumlesi") or o.get("pafta_satiri"),
                        o.get("karar_olcutleri"), _sonuc_metni, uygun=_uygun)

    #  TRAFİK PAFTASI TEK SAYFADIR.  Pafta SONUÇ ile biter: otomatik öneri
    #  tablosu ( bilgi amaçlıydı ) ve imza kutusu paftadan çıkarıldı — öneri
    #  ekranda duruyor, imza bilgisi kapak sayfasındadır.
    doc.build(ic)
    buf.seek(0)
    return buf.read(), doc.page


def _coklu_tablo(asansorler):
    satirlar = [
        ("P — Kabin kapasitesi (kişi)", lambda a: trn(a["P"], 0)),
        ("Beyan yükü (kg)", lambda a: trn(a["yuk_kg"], 0)),
        ("Kapı genişliği (mm) / tipi", lambda a: f"{trn(a['kapi_genisligi'],0)} / {a['kapi_tipi']}"),
        ("Durak adedi (ana giriş dâhil)", lambda a: trn(a["durak"], 0)),
        ("V — Kabin hızı (m/s)", lambda a: tr(a["V"])),
        ("h — Katlar arası mesafe (m)", lambda a: tr(a["h"])),
        ("p = 0,8·P", lambda a: tr(a["p"], 1)),
        ("H — Ort. en yüksek dönüş katı", lambda a: tr(a["H"], 4)),
        ("S — Ortalama durak adedi", lambda a: tr(a["S"], 4)),
        ("ta / tk  (kapı aç / kapa) (s)", lambda a: f"{tr(a['ta'],1)} / {tr(a['tk'],1)}"),
        ("tg / tp  (geçiş / transfer) (s)", lambda a: f"{tr(a['tg'],1)} / {tr(a['tp'],1)}"),
        ("tv = h / V  (s)", lambda a: tr(a["tv"], 3)),
        ("ts = ta+tk+tg−tv  (s)", lambda a: tr(a["ts"], 3)),
        ("TR = 2·H·tv+(S+1)·ts+2·p·tp  (s)", lambda a: tr(a["TR"], 2)),
        ("R = 5·60·p / TR  (kişi/5dk)", lambda a: tr(a["R"], 2)),
    ]
    basliklar = [_p("<b>Büyüklük</b>", "n")] + [_p(f"<b>{a['ad']}</b>", "sag") for a in asansorler]
    veriler = [basliklar]
    for etiket, fn in satirlar:
        veriler.append([_p(etiket, "n")] + [_p(fn(a), "sag") for a in asansorler])
    gen = [72 * mm] + [(108 / len(asansorler)) * mm] * len(asansorler)
    t = Table(veriler, colWidths=[_w(x) for x in gen], repeatRows=1)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), _c(0.4), CIZGI),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def _nufus_tablo(nufus, b):
    veriler = [[_p("<b>Grup / açıklama</b>", "n"), _p("<b>Miktar</b>", "n"),
                _p("<b>Tablo-1 kalemi</b>", "n"), _p("<b>Birim</b>", "n"),
                _p("<b>Katsayı</b>", "n"), _p("<b>c (kişi)</b>", "n")]]
    for s in nufus:
        veriler.append([_p(s["aciklama"], "n"), _p(trn(s["miktar"], 2), "sag"),
                        _p(s["kalem"], "n"), _p(s["birim"], "n"),
                        _p(trn(s["katsayi"], 4), "sag"), _p(trn(s["c"], 2), "sag")])
    veriler.append([_p("<b>TOPLAM  b = Σc</b>", "n"), "", "", "", "", _p(trn(b, 2), "sag")])
    t = Table(veriler, colWidths=[_w(58 * mm), _w(20 * mm), _w(48 * mm), _w(16 * mm), _w(18 * mm), _w(20 * mm)], repeatRows=1)
    n = len(veriler) - 1
    t.setStyle(TableStyle([
        ("SPAN", (0, n), (4, n)),
        ("GRID", (0, 0), (-1, -1), _c(0.4), CIZGI),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


# =====================================================================
#  AVAN HESAPLARI PDF
# =====================================================================
def avan_pdf(sonuc: dict, proje: dict = None) -> bytes:     # noqa: ARG001
    #  ``proje`` eski çağrılarla uyumluluk için kabul edilir, paftaya yazılmaz —
    #  proje antedi KAPAK sayfasındadır ( bkz. kapak_export ).
    buf = io.BytesIO()
    doc = _Belge(buf, "ASANSÖR AVAN PROJE HESAPLARI",
                 "MMO / 697  “Asansör Avan Projesi Hazırlama Teknik Esasları”, 2. Baskı, Ocak 2020, s.18-21"
                 "   ·   TS EN 81-20   ·   IEEE Std 80   ·   IEC 60364-5-52")
    ic = []                       # başlık çerçevenin üst şeridindedir
    if sonuc.get("hata"):
        ic += _uyari_kutusu([sonuc["hata"]], hata=True)
    if sonuc.get("uyarilar"):
        ic += _uyari_kutusu(sonuc["uyarilar"])

    #  SIRA:  önce hesaplar, EN SONDA sonuç özeti.  Özet, kendisinden önce
    #  gelen hesapların çıktısıdır; paftanın başında dururken okuyucu neyin
    #  nereden geldiğini göremiyordu.

    # ---- her asansör  ( grup başlığı ilk bölümün ilk öbeğine yapışıktır )
    for a in (sonuc.get("asansorler") or []):
        if not a.get("aktif"):
            continue
        ust = _baslik_seridi(f"{a['baslik']}" + (f"   —   {a['tanim']}" if a["tanim"] else ""),
                             "AVAN PROJE HESAPLARI")
        _onek = f"{a['baslik']}" + (f" · {a['tanim']}" if a["tanim"] else "")
        for i, b in enumerate(a["bolumler"]):
            ic += _bolum(b, ust=ust if i == 0 else None, sayfa=SAYFA_ALANI,
                         onek=_onek)

    # ---- makine dairesi
    #  MAKİNE DAİRESİZ ( MRL ) SİSTEMDE BU BÖLÜM HİÇ BASILMAZ.  Makine dairesi
    #  yoksa aydınlatma hesabının konusu da yoktur; "bu hesap uygulanmaz"
    #  satırı paftada yer kaplamaktan başka bir işe yaramıyordu.
    #  Tek istisna EKSİK GİRDİdir:  MRL kutusu işaretli DEĞİL ama A × B ölçüsü
    #  de girilmemişse bu bir tercih değil, unutulmuş bir girdidir — o zaman
    #  uyarı basılır, yoksa eksik hesap sessizce gizlenmiş olurdu.
    #
    #  Bölümün kendi başlığı zaten "MAKİNE DAİRESİ AYDINLATMA HESABI"; üstüne
    #  ayrıca grup başlığı konunca aynı yazı iki kez basılıyordu.  Grup başlığı
    #  yalnız uyarı metni için gerekli.
    mk = sonuc.get("makine_dairesi") or {}
    if mk.get("aktif"):
        ic += _bolum(mk["bolum"], bosluk=6 * mm, sayfa=SAYFA_ALANI, onek="")
    elif mk.get("mk_yok") is False:
        ust = _baslik_seridi("MAKİNE DAİRESİ AYDINLATMASI", "TS EN 81-20")
        ust.spaceBefore = 6 * mm
        ic += [KeepTogether([ust, Spacer(1, 1.5 * mm), _p(mk.get("uyari", ""), "nb")])]

    # ---- topraklama
    tp = sonuc.get("topraklama") or {}
    ust = _baslik_seridi("TEMEL TOPRAKLAMA HESABI",
                         "Temel ( ızgara ) + paralel çubuk topraklayıcı")
    if tp.get("aktif"):
        for i, b in enumerate(tp["bolumler"]):
            ic += _bolum(b, ust=ust if i == 0 else None, sayfa=SAYFA_ALANI,
                         onek="")
    else:
        ust.spaceBefore = 6 * mm
        ic += [KeepTogether([ust] + _uyari_kutusu([tp.get("uyari", "")], hata=True))]

    # ---- SONUÇ ÖZETİ  ( en sonda )  —  tek blok, bölünmez.
    #  İMZA KUTUSU YOK:  "Hesabı yapan · Kontrol eden · Onay" kutusu boş
    #  kalıyordu;  imza bilgisi kapak sayfasındadır ( trafik paftası gibi ).
    ozet_bas = _baslik_seridi("SONUÇ ÖZETİ", "tüm asansörler")
    ozet_bas.spaceBefore = 6 * mm
    ic += [KeepTogether([ozet_bas, _BolumIsareti("SONUÇ ÖZETİ"),
                         Spacer(1, 1.2 * mm), _avan_ozet_tablo(sonuc)])]
    doc.build(ic)
    buf.seek(0)
    return buf.read()


def _avan_ozet_tablo(sonuc):
    aktif = [a for a in (sonuc.get("asansorler") or []) if a.get("aktif")]
    if not aktif:
        return _p("Tanımlı asansör yok.", "n")
    satirlar = [
        ("Asansör tanımı", lambda o: o["tanim"] or "—", "—"),
        ("P — Kabin kapasitesi", lambda o: trn(o["kapasite"], 0), "kişi"),
        ("Q — Anma yükü", lambda o: trn(o["Q"], 0), "kg"),
        ("V — Kabin hızı", lambda o: tr(o["V"]), "m/s"),
        ("N — Hesaplanan motor gücü", lambda o: tr(o["N_hes"]), "kW"),
        ("Nsç — Seçilen motor gücü", lambda o: tr(o["Nsc"]), "kW"),
        ("Kontrol  ( Nsç ≥ N )", lambda o: "UYGUN" if o["motor_uygun"] else "UYGUN DEĞİL", ""),
        ("P1 — Kuyu alt boşluğu tabanına", lambda o: trn(o["P1"], 0), "N"),
        ("P2 — Karşı ağırlık tamponu altına", lambda o: trn(o["P2"], 0), "N"),
        ("PR — Bir kabin kılavuz rayına", lambda o: trn(o["PR"], 0), "N"),
        ("PK — Bir karşı ağırlık rayına", lambda o: trn(o["PK"], 0), "N"),
        ("Fs — Kuyu üstü betonuna", lambda o: trn(o["Fs"], 0), "N"),
        ("Kabin armatür sayısı", lambda o: trn(o["n_kabin"], 0), "adet"),
        ("Kuyu armatür sayısı", lambda o: trn(o["n_kuyu"], 0), "adet"),
        ("P — Asansörün kurulu gücü", lambda o: trn(o["P_kurulu"], 0), "W"),
        ("ε — Toplam gerilim düşümü", lambda o: tr(o["eps"], 3), "%"),
        ("Kontrol  ( ε ≤ εmax )", lambda o: "UYGUN" if o["eps_uygun"] else "UYGUN DEĞİL", ""),
        ("I — Hat akımı  /  Iz", lambda o: f"{tr(o['I'],1)} / {trn(o['Iz'],1)}", "A"),
    ]
    basliklar = [_p("<b>Büyüklük</b>", "n")] + \
                [_p(f"<b>{a['no']} NOLU</b>", "sag") for a in aktif] + [_p("<b>Birim</b>", "n")]
    veriler = [basliklar]
    for etiket, fn, birim in satirlar:
        veriler.append([_p(etiket, "n")] + [_p(fn(a["ozet"]), "sag") for a in aktif] + [_p(birim, "n")])
    oz = sonuc.get("ozet") or {"tesis_kurulu_guc": 0, "Re": None, "topraklama_uygun": None}
    veriler.append([_p("<b>Tesisin toplam kurulu gücü</b>", "n"),
                    _p(trn(oz["tesis_kurulu_guc"], 0), "sag")] +
                   [""] * (len(aktif) - 1) + [_p("W", "n")])
    veriler.append([_p("<b>Re — Temel topraklama direnci</b>", "n"),
                    _p(tr(oz["Re"], 3) if oz["Re"] is not None else "—", "sag")] +
                   [""] * (len(aktif) - 1) + [_p("Ω", "n")])
    veriler.append([_p("<b>Topraklama kontrolü  ( Re ≤ UL / IΔn )</b>", "n"),
                    _p("UYGUN" if oz["topraklama_uygun"] else "UYGUN DEĞİL", "sag")] +
                   [""] * (len(aktif) - 1) + [""])
    gen = [70 * mm] + [(94 / len(aktif)) * mm] * len(aktif) + [16 * mm]
    t = Table(veriler, colWidths=[_w(x) for x in gen], repeatRows=1)
    n = len(veriler)
    stil = [
        ("GRID", (0, 0), (-1, -1), _c(0.4), CIZGI),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.4), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("FONTSIZE", (0, 0), (-1, -1), 7.8),
    ]
    for r in (n - 3, n - 2, n - 1):
        stil.append(("LINEABOVE", (0, r), (-1, r), 0.9, SIYAH))
        if len(aktif) > 1:
            stil.append(("SPAN", (1, r), (len(aktif), r)))
    t.setStyle(TableStyle(stil))
    return t


# =====================================================================
#  MUKAVEMET HESAPLARI PDF          ( UYGULAMA PROJESİ — avandan ayrı )
# =====================================================================
def mukavemet_pdf(sonuc: dict, proje: dict = None) -> bytes:   # noqa: ARG001
    """Mukavemet paftası.

    ``proje`` eski çağrılarla uyumluluk için kabul edilir, paftaya yazılmaz —
    proje antedi KAPAK sayfasındadır ( bkz. kapak_export ).

    Bölümler engine/mukavemet.py'den olduğu gibi gelir;  avan paftasıyla aynı
    çizim yardımcıları kullanılır, böylece iki çıktının biçimi ayrışmaz.
    """
    buf = io.BytesIO()
    doc = _Belge(buf, "ASANSÖR MUKAVEMET HESAPLARI",
                 "TS EN 81-20   ·   TS EN 81-50   ·   TS 12385-5   ·   ISO 7465"
                 "   ·   MMO 208/4   ·   MMO 208/7")
    ic = []
    if not sonuc.get("aktif"):
        ic += _uyari_kutusu(list(sonuc.get("hata") or ["Hesap yapılamadı."]), hata=True)
        doc.build(ic)
        buf.seek(0)
        return buf.read()

    if sonuc.get("uyarilar"):
        ic += _uyari_kutusu(sonuc["uyarilar"])

    ust = _baslik_seridi("ASANSÖR MUKAVEMET HESAPLARI", "UYGULAMA PROJESİ")
    for i, b in enumerate(sonuc.get("bolumler") or []):
        ic += _bolum(b, ust=ust if i == 0 else None, sayfa=SAYFA_ALANI, onek="")

    ozet_bas = _baslik_seridi("SONUÇ ÖZETİ", "on hesap bölümü")
    ozet_bas.spaceBefore = 6 * mm
    ic += [KeepTogether([ozet_bas, _BolumIsareti("SONUÇ ÖZETİ"),
                         Spacer(1, 1.2 * mm), _mukavemet_ozet(sonuc)])]
    doc.build(ic)
    buf.seek(0)
    return buf.read()


def _mukavemet_ozet(sonuc):
    """Bölüm bölüm sonuç + kuyu tabanına aktarılan yükler."""
    o = sonuc.get("ozet") or {}
    satirlar = []
    for b in (sonuc.get("bolumler") or []):
        s = b.get("sonuc") or {}
        satirlar.append((b.get("baslik", ""), s.get("metin", "—")))
    satirlar += [
        ("N — Hesaplanan motor gücü", f"{tr(o.get('N_hesap'))} kW"),
        ("Kullanılabilir kabin alanı", f"{tr(o.get('kabin_alani'))} m²"
                                       f"   ·   {trn(o.get('kabin_kisi'), 0)} kişi"),
        ("Sf — Halat güvenlik katsayısı", tr(o.get("Sf"))),
        ("Kılavuz ray boyu", f"{tr(o.get('ray_boyu'))} m"),
        ("FKR — Bir kabin rayına gelen kuvvet", f"{trn(o.get('FKR'), 0)} N"),
        ("FAR — Bir ağırlık rayına gelen kuvvet", f"{trn(o.get('FAR'), 0)} N"),
        ("Fkt — Kabin tamponlarına gelen kuvvet", f"{trn(o.get('Fkt'), 0)} N"),
        ("Fat — Ağırlık tamponlarına gelen kuvvet", f"{trn(o.get('Fat'), 0)} N"),
        #  HÜKÜM MOTORDAN GELİR ( mukavemet.genel_hukum ):  "uygun değil" >
        #  "hesap eksik" > "uygundur".  Burada yeniden kurulursa ekranla
        #  ayrışır — zaten bir kez öyle ayrışmıştı.
        ("GENEL SONUÇ", o.get("genel_sonuc")
         or ("UYGUNDUR." if o.get("tumu_uygun") else "UYGUN DEĞİLDİR.")),
    ]
    return _kv_tablo(satirlar, genislikler=(105 * mm, 75 * mm), vurgu_son=True)


# =====================================================================
#  UYGULAMA PROJESİ PDF        ( mukavemet + elektrik + topraklama )
# =====================================================================
def _uygulama_govdesi(sonuc, ust_ek=""):
    """Bir asansörün bütün bölümleri + sonuç özeti  ( akış öğeleri ).

    Tek ve çoklu pafta AYNI gövdeyi basar;  ikisi ayrı yazılsaydı biçim
    zamanla ayrışırdı.  ``ust_ek`` çoklu paftada şerit sağına asansörün
    adını yazar.
    """
    ic = []
    if sonuc.get("uyarilar"):
        ic += _uyari_kutusu(sonuc["uyarilar"])

    kaynak = ust_ek or "UYGULAMA PROJESİ"
    #  Mukavemet ve elektrik bölümleri ayrı şeritlerle açılır ki paftada
    #  hangi ailenin nerede bittiği görünsün.
    muk_sayi = int(sonuc.get("mukavemet_bolum_sayisi") or 0)
    for i, b in enumerate(sonuc.get("bolumler") or []):
        ust = None
        if i == 0:
            ust = _baslik_seridi("MUKAVEMET HESAPLARI", kaynak)
        elif i == muk_sayi:
            ust = _baslik_seridi("ELEKTRİK VE TOPRAKLAMA HESAPLARI", kaynak)
            ust.spaceBefore = 6 * mm
        ic += _bolum(b, ust=ust, sayfa=SAYFA_ALANI, onek=ust_ek)

    ozet_bas = _baslik_seridi(
        "SONUÇ ÖZETİ", f"{len(sonuc.get('bolumler') or [])} hesap bölümü")
    ozet_bas.spaceBefore = 6 * mm
    ic += [KeepTogether([ozet_bas, _BolumIsareti(_isaret_adi(ust_ek, "SONUÇ ÖZETİ")),
                         Spacer(1, 1.2 * mm), _uygulama_ozet(sonuc)])]
    return ic


def uygulama_pdf(sonuc: dict, proje: dict = None) -> bytes:   # noqa: ARG001
    """Uygulama projesi paftası — 1 - 4 asansör, hepsi TEK belgede.

    GİRDİSİ PROJE SONUCUDUR ( engine/uygulama/hesap.hesapla_coklu ), tek bir
    asansörün sonucu değil.  Bir süre iki ayrı fonksiyon vardı — tek asansöre
    ``uygulama_pdf``, çoğuna ``uygulama_coklu_pdf`` — ve hangisinin
    çağrılacağına API karar veriyordu.  İkisi zamanla ayrıştı:  proje geneli
    hesaplar çoklu paftada en sona alınmış, tek asansörlükte asansörün
    bölümlerinin arasında kalmıştı.  Aynı program aynı projeyi asansör
    sayısına göre iki türlü basıyordu.  Artık tek yol var.

    TEK ASANSÖRDE ASANSÖR ŞERİDİ BASILMAZ:  "ASANSÖR 1 · —" başlığı tek
    asansörlük bir paftada bilgi taşımaz, yalnız yer kaplar.

    PROJE GENELİ HESAPLAR ( topraklama · makine dairesi aydınlatması ) motor
    tarafında HER asansörden ayrılır ve burada EN SONA, kendi sayfasına bir
    kez basılır — asansör sayısından bağımsız olarak.
    """
    buf = io.BytesIO()
    doc = _Belge(buf, "ASANSÖR UYGULAMA PROJESİ HESAPLARI",
                 "TS EN 81-20   ·   TS EN 81-50   ·   TS 12385-5   ·   ISO 7465"
                 "   ·   MMO 208/4   ·   MMO 208/7   ·   IEEE Std 80"
                 "   ·   IEC 60364-5-52")
    asansorler = sonuc.get("asansorler") or []
    ic = []
    if not sonuc.get("aktif") or not asansorler:
        ic += _uyari_kutusu(list(sonuc.get("hata") or ["Hesap yapılamadı."]),
                            hata=True)
        doc.build(ic)
        buf.seek(0)
        return buf.read()

    tek = len(asansorler) == 1
    for i, a in enumerate(asansorler):
        etiket = f"{a.get('no', i + 1)} · {a.get('tanim') or ''}".strip(" ·")
        if not tek:
            if i:
                ic.append(PageBreak())
            ic.append(_baslik_seridi(f"ASANSÖR {etiket}",
                                     f"{len(asansorler)} asansörden {i + 1}."))
            ic.append(Spacer(1, 1.5 * mm))
        if not a.get("aktif"):
            ic += _uyari_kutusu(list(a.get("hata") or ["Hesap yapılamadı."]),
                                hata=True)
            continue
        ic += _uygulama_govdesi(a, ust_ek="" if tek else f"ASANSÖR {etiket}")

    #  PROJE GENELİ HESAPLAR — bütün asansörlerin ARKASINDA, bir kez.
    pg = sonuc.get("proje_geneli") or []
    if pg:
        ic.append(PageBreak())
        #  Yalnız başlık:  "bütün asansörler için bir kez" yan yazısı ve
        #  "BİNAYA aittir" açıklama kutusu paftadan çıkarıldı — paftayı okuyana
        #  bilgi vermiyordu ( tek asansörde de aynı cümleyi basıyordu ).
        ic.append(_baslik_seridi("PROJE GENELİ HESAPLAR"))
        #  Bu sayfayı açan şey PROJE GENELİ bandıdır;  üst yazıyı band koyar.
        ic.append(_BolumIsareti("PROJE GENELİ HESAPLAR"))
        ic.append(Spacer(1, 1.5 * mm))
        for b in pg:
            ic += _bolum(b, sayfa=SAYFA_ALANI, onek="PROJE GENELİ")
    doc.build(ic)
    buf.seek(0)
    return buf.read()


def _uygulama_ozet(sonuc):
    o = sonuc.get("ozet") or {}
    satirlar = [(b.get("baslik", ""), (b.get("sonuc") or {}).get("metin", "—"))
                for b in (sonuc.get("bolumler") or [])]
    satirlar += [
        ("N — Hesaplanan motor gücü", f"{tr(o.get('N_hesap'))} kW"),
        ("Kullanılabilir kabin alanı", f"{tr(o.get('kabin_alani'))} m²"
                                       f"   ·   {trn(o.get('kabin_kisi'), 0)} kişi"),
        ("Sf — Halat güvenlik katsayısı", tr(o.get("Sf"))),
        ("Kılavuz ray boyu", f"{tr(o.get('ray_boyu'))} m"),
        ("FKR — Bir kabin rayına gelen kuvvet", f"{trn(o.get('FKR'), 0)} N"),
        ("FAR — Bir ağırlık rayına gelen kuvvet", f"{trn(o.get('FAR'), 0)} N"),
        ("Fkt — Kabin tamponlarına gelen kuvvet", f"{trn(o.get('Fkt'), 0)} N"),
        ("Fat — Ağırlık tamponlarına gelen kuvvet", f"{trn(o.get('Fat'), 0)} N"),
    ]
    if o.get("elektrik_var"):
        satirlar += [
            ("Kabin armatür sayısı", f"{trn(o.get('n_kabin'), 0)} adet"),
            ("Kuyu armatür sayısı", f"{trn(o.get('n_kuyu'), 0)} adet"),
            ("Asansörün kurulu gücü", f"{trn(o.get('P_kurulu'), 0)} W"),
            ("ε — Toplam gerilim düşümü",
             f"{tr(o.get('eps'), 3)} %   —   "
             + ("UYGUN" if o.get("eps_uygun") else "UYGUN DEĞİL")),
            ("I — Hat akımı / Iz",
             f"{tr(o.get('I'), 1)} / {trn(o.get('Iz'), 1)} A   —   "
             + ("UYGUN" if o.get("akim_uygun") else "UYGUN DEĞİL")),
        ]
    if o.get("Re") is not None:
        satirlar.append(("Re — Temel topraklama direnci",
                         f"{tr(o.get('Re'), 3)} Ω   —   "
                         + ("UYGUN" if o.get("topraklama_uygun") else "UYGUN DEĞİL")))
    satirlar.append(("GENEL SONUÇ", o.get("genel_sonuc")
                     or ("UYGUNDUR." if o.get("tumu_uygun") else "UYGUN DEĞİLDİR.")))
    return _kv_tablo(satirlar, genislikler=(105 * mm, 75 * mm), vurgu_son=True)

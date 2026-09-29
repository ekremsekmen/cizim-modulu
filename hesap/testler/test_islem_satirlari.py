# -*- coding: utf-8 -*-
"""
TEST 14  —  PAFTA İŞLEM SATIRLARI  ( her satır kendi sonucunu vermeli )

Paftadaki her hesap satırı üç parçadır:  bağıntı, sayıların yerine konmuş
İŞLEM ve sonuç.  Denetçi işlemi hesap makinesine yazar ve sonucu bulmayı
bekler.  Bu test onu yapar:  bütün senaryolarda ( trafik · avan · uygulama ·
mukavemet taraması ) işlem metnini okuyup yeniden hesaplar ve basılan sonucu
verip vermediğine bakar.

NİÇİN AYRI TEST:  öteki testler SONUCU denetler.  Sonuç doğru olup işlem
satırı yanlış yazıldığında hiçbiri görmez.  Bu turda böyle altı bağıntı
bulundu ( hepsi motor testlerinden geçiyordu ):

    lh      2:1 askıda köşeli parantez yoktu  →  "… / 1000 + 5 × 2"  ( %46 )
    σF      | Fx | bağıntısına işaretli Fx yazılıyordu              ( eksi sonuç )
    B       sonuç yukarı yuvarlanıyor, satır yuvarlamayı yazmıyordu
    Sapd    "0,5 · 4 = 6"  —  6 mm² asgarisi ve standart kesit adımı yoktu
    ε1 ε2   κ = 44,4 "44" diye basılıyordu
    P1…Fs   10 N'a yuvarlama yazılı değildi

YUVARLAMA TOLERANSI KESTİRME DEĞİLDİR:  işlemdeki her sayı basıldığı hane
kadar belirsizdir ( "36,35" gerçekte 36,345 … 36,355 ).  Satır ARALIK
aritmetiğiyle hesaplanır;  basılan sonuç bu aralığın içinde değilse, satırdaki
sayılarla o sonuca varmak MÜMKÜN DEĞİLDİR.  Tam sayılar:  binlik ayraçlı ya da
üç haneli olanlar ±0,5 ( "713" kg ),  bir-iki haneli olanlar tam kabul edilir
( "2" ray, "4" katsayı ) — yoksa her satır gevşer ve test bir şey yakalamaz.

SATIR İŞLEM DEĞİL, PARAMETRE LİSTESİYSE ( "l = 3.000 mm ,  Iy = 524.100 mm⁴" )
ya da sonuç sayı değilse denetlenmez;  bu satırların sayısı raporda yazılır ve
bilinen bağıntıların gerçekten denetlendiği ayrıca doğrulanır ( ayrıştırıcı
sessizce gevşeyip her şeyi "denetlenemedi"ye atamasın diye ).
"""
import ast
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.avan import hesap as AV                               # noqa: E402
from engine.avan import trafik as TR                              # noqa: E402
from engine.uygulama import mukavemet as MK                       # noqa: E402
from testler import test_mukavemet_tarama as T10                  # noqa: E402
from testler.altin_uret import (avan_senaryolar, senaryolar,      # noqa: E402
                                uygulama_motoru, uygulama_senaryolar)
from testler.ortak import Rapor                                   # noqa: E402


# =====================================================================
#  ARALIK ARİTMETİĞİ
# =====================================================================
class Aralik:
    __slots__ = ("alt", "ust")

    def __init__(self, alt, ust=None):
        self.alt, self.ust = alt, (alt if ust is None else ust)

    def __add__(self, o):
        return Aralik(self.alt + o.alt, self.ust + o.ust)

    def __sub__(self, o):
        return Aralik(self.alt - o.ust, self.ust - o.alt)

    def __mul__(self, o):
        c = (self.alt * o.alt, self.alt * o.ust, self.ust * o.alt, self.ust * o.ust)
        return Aralik(min(c), max(c))

    def __truediv__(self, o):
        if o.alt <= 0 <= o.ust:
            raise ValueError("bölen sıfırı içeriyor")
        return self * Aralik(min(1 / o.alt, 1 / o.ust), max(1 / o.alt, 1 / o.ust))

    def __pow__(self, o):
        if o.alt != o.ust:
            raise ValueError("üs belirsiz")
        e = o.alt
        if self.alt < 0 and e != int(e):
            raise ValueError("negatif tabanın kesirli üssü")
        u = [self.alt ** e, self.ust ** e]
        if self.alt < 0 < self.ust and e % 2 == 0:
            u.append(0.0)
        return Aralik(min(u), max(u))

    def __neg__(self):
        return Aralik(-self.ust, -self.alt)


def _tekduze(f):
    """Aralıkta tekdüze fonksiyon — uçlarda hesaplanır."""
    def g(a):
        u = (f(a.alt), f(a.ust))
        return Aralik(min(u), max(u))
    return g


def _mutlak(a):
    if a.alt <= 0 <= a.ust:
        return Aralik(0.0, max(-a.alt, a.ust))
    u = (abs(a.alt), abs(a.ust))
    return Aralik(min(u), max(u))


def _roundup(a, n=Aralik(0)):
    k = 10 ** n.alt
    return Aralik(math.ceil(a.alt * k - 1e-9) / k, math.ceil(a.ust * k - 1e-9) / k)


FONKSIYON = {
    "sqrt": _tekduze(math.sqrt), "exp": _tekduze(math.exp), "ln": _tekduze(math.log),
    "log": _tekduze(math.log10), "atan": _tekduze(math.atan), "abs": _mutlak,
    #  Paftadaki açılar 0-90° arasındadır;  orada sin ve tan tekdüzedir.
    "sin": _tekduze(math.sin), "tan": _tekduze(math.tan),
    "max": lambda *a: Aralik(max(x.alt for x in a), max(x.ust for x in a)),
    "min": lambda *a: Aralik(min(x.alt for x in a), min(x.ust for x in a)),
    "roundup": _roundup,
}
ISLEC = {ast.Add: "__add__", ast.Sub: "__sub__", ast.Mult: "__mul__",
         ast.Div: "__truediv__", ast.Pow: "__pow__"}


def _degerlendir(dugum, sayilar):
    if isinstance(dugum, ast.Expression):
        return _degerlendir(dugum.body, sayilar)
    if isinstance(dugum, ast.Name) and dugum.id in sayilar:
        return sayilar[dugum.id]
    if isinstance(dugum, ast.Constant) and isinstance(dugum.value, (int, float)):
        return Aralik(float(dugum.value))
    if isinstance(dugum, ast.BinOp):
        sol = _degerlendir(dugum.left, sayilar)
        return getattr(sol, ISLEC[type(dugum.op)])(_degerlendir(dugum.right, sayilar))
    if isinstance(dugum, ast.UnaryOp) and isinstance(dugum.op, (ast.USub, ast.UAdd)):
        v = _degerlendir(dugum.operand, sayilar)
        return -v if isinstance(dugum.op, ast.USub) else v
    if (isinstance(dugum, ast.Call) and isinstance(dugum.func, ast.Name)
            and dugum.func.id in FONKSIYON):
        return FONKSIYON[dugum.func.id](*[_degerlendir(a, sayilar) for a in dugum.args])
    raise ValueError("desteklenmeyen ifade")


# =====================================================================
#  PAFTA METNİ  →  İFADE
# =====================================================================
_SAYI = re.compile(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+,\d+|\d+")
_BIRIM = re.compile(r"(\d)\s+(kg/m|kg|mm⁴|mm³|mm²|mm|m/s²|m/s|m|N|W|kW)(?=\s|$|[×·*/+)\-−])")
#  Sondaki açıklama parantezi:  "( ix = 19,48 · iy = 18,23 )",
#  "( pervaz 90 mm ≤ 100 mm — girinti alana katılmaz )".  Harf içerir,
#  iç içe parantez içermez ve işlemden en az iki boşlukla ayrılır.
_ACIKLAMA = re.compile(r"\s{2,}\(([^()]*[A-Za-zÇĞİÖŞÜçğıöşü][^()]*)\)\s*$")
_KALAN = re.compile(r"\b(?:sqrt|exp|sin|tan|ln|log|max|min|abs|atan|roundup|S\d+|DERECE)\b")


def _sayi_araligi(metin):
    binlik = "." in metin
    duz = metin.replace(".", "") if binlik else metin
    hane = len(duz.split(",")[1]) if "," in duz else 0
    v = float(duz.replace(",", "."))
    if hane:
        yarim = 0.5 * 10 ** -hane
    elif binlik or len(duz) >= 3:
        yarim = 0.5
    else:
        yarim = 0.0
    return Aralik(v - yarim, v + yarim)


def aralik_hesapla(ifade):
    """Pafta işlem metnini aralık olarak hesaplar;  çözülemezse None."""
    #  Bölünmez boşluk ( U+00A0 ) paftada satır kırılmasını yönetir;
    #  okuyan için sıradan boşluktur.
    s = _ACIKLAMA.sub("", str(ifade).replace("\u00a0", " ")).strip()
    s = re.sub(r"\|([^|]+)\|", r"abs(\1)", s)
    s = s.replace("10⁶", "(10**6)").replace("10³", "(10**3)")
    s = re.sub(r"(\d)\s*%", r"\1/100", s)
    s = _BIRIM.sub(r"\1", s)
    for eski, yeni in (("−", "-"), ("–", "-"), ("×", "*"), ("·", "*"), ("÷", "/"),
                       ("²", "**2"), ("³", "**3"), ("⁴", "**4"), ("√", "sqrt"),
                       ("[", "("), ("]", ")"), ("ROUNDUP", "roundup"),
                       ("MAX", "max"), ("MIN", "min"), (";", ",")):
        s = s.replace(eski, yeni)
    s = re.sub(r"(\d)\s*°", r"\1*DERECE", s)
    sayilar = {"DERECE": Aralik(math.pi / 180)}

    def yer(m):
        ad = f"S{len(sayilar)}"
        sayilar[ad] = _sayi_araligi(m.group(0))
        return ad
    s = _SAYI.sub(yer, s)
    if re.search(r"[A-Za-zÇĞİÖŞÜçğıöşü_]", _KALAN.sub("", s)):
        return None
    try:
        return _degerlendir(ast.parse(s, mode="eval"), sayilar)
    except (ValueError, SyntaxError, ZeroDivisionError, OverflowError, TypeError):
        return None


def _icinde(a, deger):
    pay = 1e-6 * max(1.0, abs(deger))
    return a.alt - pay <= deger <= a.ust + pay


def denetle(adim):
    """None → denetlenemedi.  Aksi hâlde ( tutarlı_mı, ayrıntı )."""
    d = adim.get("deger")
    if not isinstance(d, (int, float)) or isinstance(d, bool) or not math.isfinite(d):
        return None
    islem = _ACIKLAMA.sub("", str(adim.get("islem") or ""))
    parcalar = [p.strip() for p in islem.split("=") if p.strip()]
    if not parcalar or "→" in parcalar[0]:
        return None
    #  ZİNCİR:  "ifade  =  ara  →  kural  →  …"  —  ifade ARA değeri vermeli;
    #  sonrası yazılı bir kuraldır ( asgari, üst sınır, standart kesit ).
    if "→" in islem:
        if len(parcalar) < 2:
            return None
        hedef = aralik_hesapla(parcalar[1].split("→")[0])
        v = aralik_hesapla(parcalar[0])
        if hedef is None or v is None:
            return None
        return (v.ust >= hedef.alt - 1e-9 and v.alt <= hedef.ust + 1e-9,
                f"işlem {v.alt:.6g}…{v.ust:.6g}  ≠  yazılan ara değer "
                f"{hedef.alt:.6g}…{hedef.ust:.6g}")
    v = aralik_hesapla(parcalar[0])
    if v is None:
        return None
    etiket = f"{adim.get('formul') or ''}  {adim.get('kaynak') or ''}"
    if "aşağı yuvarlan" in etiket:
        v = Aralik(math.floor(v.alt + 1e-9), math.floor(v.ust + 1e-9))
    if "10 N'a yukarı yuvarlan" in etiket:
        v = Aralik(math.ceil(v.alt / 10 - 1e-9) * 10, math.ceil(v.ust / 10 - 1e-9) * 10)
    return _icinde(v, d), f"işlem {v.alt:.6g}…{v.ust:.6g}  ≠  basılan {d:.6g}"


# =====================================================================
#  SENARYOLAR
# =====================================================================
def _hesap_satirlari(sonuc, etiket, cikti):
    if isinstance(sonuc, dict):
        if isinstance(sonuc.get("adimlar"), list) and "baslik" in sonuc:
            for a in sonuc["adimlar"]:
                if isinstance(a, dict) and a.get("tip") == "hesap":
                    cikti.append((etiket, sonuc["baslik"], a))
        for k, v in sonuc.items():
            if k != "adimlar":
                _hesap_satirlari(v, etiket, cikti)
    elif isinstance(sonuc, list):
        for v in sonuc:
            _hesap_satirlari(v, etiket, cikti)


def _kopya(g):
    return json.loads(json.dumps(g))


def satirlar():
    out = []
    for i, g in enumerate(senaryolar()):
        _hesap_satirlari(TR.hesapla(_kopya(g)), f"trafik #{i}", out)
    for i, g in enumerate(avan_senaryolar()):
        _hesap_satirlari(AV.hesapla(_kopya(g)), f"avan #{i}", out)
    for i, g in enumerate(uygulama_senaryolar()):
        _hesap_satirlari(uygulama_motoru(_kopya(g)), f"uygulama #{i}", out)
    for aile, uretici in T10.AILELER:
        for ad, g in uretici():
            _hesap_satirlari(MK.hesapla(_kopya(g)), f"mukavemet {aile} · {ad}", out)
    return out


#  Bu bağıntılar en az bir senaryoda GERÇEKTEN yeniden hesaplanmış olmalı.
#  Ayrıştırıcı bozulup onları "denetlenemedi"ye atarsa test yeşil kalırdı.
DENETLENMESI_ZORUNLU = (
    "lh = ", "σF = | Fx |", "σF = 1,85 × | Fx |", "B  =  ROUNDUP", "Sapd", "ε1", "ε2",
    "P1  =", "PK  =", "Fs  =", "k   =   a · b", "Ry  =", "f = μ / sin", "λ = l / imin",
    "Kabin alanı = ", "a)  Q / 75",
)


def calistir():
    r = Rapor("TEST 14 — PAFTA İŞLEM SATIRLARI (işlem → sonuç)")
    tum = satirlar()
    sayac = Counter()
    hatali = defaultdict(list)
    denetlenen_bagintilar = set()
    for etiket, baslik, adim in tum:
        s = denetle(adim)
        if s is None:
            sayac["denetlenemedi"] += 1
            continue
        sayac["denetlendi"] += 1
        formul = str(adim.get("formul") or "")
        denetlenen_bagintilar.add(formul)
        if not s[0]:
            ad = re.sub(r"^\d+\s*-\s*", "", str(baslik))
            hatali[(ad, formul)].append((etiket, adim.get("islem"), s[1]))

    r.kontrol(f"hesap satırı taranan: {len(tum)}", len(tum) > 30000, f"→ {len(tum)}")
    r.kontrol(f"yeniden hesaplanan satır: {sayac['denetlendi']}  "
              f"( denetlenemeyen {sayac['denetlenemedi']} — parametre listesi / metin )",
              sayac["denetlendi"] > 0.75 * len(tum), f"→ {dict(sayac)}")
    for bas in DENETLENMESI_ZORUNLU:
        r.kontrol(f"bağıntı gerçekten denetlendi: {bas}",
                  any(f.startswith(bas) for f in denetlenen_bagintilar))
    if not hatali:
        r.gecti += 1
        return r
    for (ad, formul), liste in sorted(hatali.items(), key=lambda x: -len(x[1])):
        etiket, islem, ayrinti = liste[0]
        r.kontrol(f"{ad} · {formul}  —  {len(liste)} satırda işlem sonucu vermiyor",
                  False, f"→ örn {etiket}:  {str(islem)[:120]!r}  ·  {ayrinti}")
    return r


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)

# -*- coding: utf-8 -*-
"""
VERİLER VE KISALTMALAR — asansörün veri tablosu, ölçü kodlarının Türkçesi ve
çizimlerin genel notları;  paftada her asansörün çizimlerinin yanında kendi
çerçevesinde ( LiftDesigner'ın veri bloğu gibi — kullanıcı kararı 13 Eki ).

13 Eki'ye kadar kuyu planının sağında üç satırlık VERİLER ( kabin, kapı,
askı ) ve KISALTMALAR vardı;  yük, hız, makine, halat, ray hiçbir çizimde
yazmıyordu.  Değerlerin hepsi girdiden ( g ) ya da hesabın özetinden
( g["veri"] — kopru ):  boş olan satır yazılmaz, sayı uydurulmaz.
"""

import re

from cizim import arka_aski
from cizim import avan_kipi
from cizim import donanim
from cizim import dusey
from cizim import eleman
from cizim import geometri
from cizim import katlar
from cizim import kisaltmalar
from cizim import kuyu_dibi
from cizim import sabitler
from cizim import standart
from cizim import uslup

BASLIK = "VERİLER VE KISALTMALAR"

#  Genel notlar:  yalnız çizimlerin kendisinden bilinenler
NOTLAR = ("Ölçüler mm, kotlar m.",)
#  Kotla girişte ( g["dusey"]["kot_ofseti"] ) kotlar mimarinindir:  ±0,00 onun datumu
KOT_NOTU = "Kotlar bitmiş döşeme kotlarıdır."
#  NOTLAR tablosunda notun sola uzaklığı ( 1/20'de;  solda sıra numarası )
NOT_SUTUNU = 120.0


def dogrula(g):
    """Kısaltmalar planın kodlarından:  plan çizilemiyorsa tablo da çıkmaz."""
    return geometri.dogrula(g)


def _aski(g):
    aski = g.get("aski") or {}
    duzen = aski.get("duzen") or "—"
    oran = "1:1" if duzen == "Doğrudan" else "2:1"
    if arka_aski.arkada_iki_bir(g):
        capraz = arka_aski.geometri(g, sabitler.sabitler(g.get("_cizim_sabitleri")))
        duzen += f"  ·  çapraz {capraz['aci']:.0f}°"
    return f"{duzen}  ·  {oran}"


def satirlar(g):
    """ASANSÖR VERİLERİ:  [ ( ad , değer ) ] — değeri olmayan satır yok."""
    v = g.get("veri") or {}
    dy, kb, kp, ku = g["dusey"], g["kabin"], g["kapi"], g["kuyu"]
    kr, ag, ak, mk = g["kabin_ray"], g["agirlik"], g.get("aski") or {}, g.get("makine") or {}
    kd = g.get("kuyu_dibi") or {}
    r = []
    #  Avanda ürün seçilmemiştir ( cizim/avan_kipi.py ):  ürün değerleri yazılmaz
    urun = not g["proje"].get("avan")

    def ekle(ad, *degerler):
        #  str:  geçersiz bir seçim sayı olarak gelebilir ( kat kapısı tipi −1 — API;
        #  hesap reddeder, çizim sorunlu kurulur ) — 21 Eki:  tablo çöküyordu
        dolu = [str(d) for d in degerler if d]
        if dolu:
            r.append((ad, "  ·  ".join(dolu)))

    def profil(metin):
        #  Formun profil adı "89 x 62 x 15,88":  çarpı işaretiyle ( tablonun öbür ölçüleri gibi )
        return metin.replace(" x ", " × ") if metin else None

    def birimli(x, birim):
        return f"{x:g} {birim}" if x else None

    ekle("Asansör", v.get("tip"))
    #  Kişi:  avanda avan hesabınınki ( trafiğin kapasitesi — MMO/697 Tablo-7 ), hazır asansörün
    #  kabininden hesaplanan değil ( 18 Kas:  1600 kg'da kapak ve hesap 20, pafta 21 kişi diyordu )
    kisi = v.get("kisi") if urun else g["proje"].get("avan_kisi")
    ekle("Beyan yükü", birimli(v.get("yuk"), "kg"), birimli(kisi, "kişi"))
    ekle("Beyan hızı", f"{dy['beyan_hizi']:.2f} m/s")
    kotlar, _hata = dusey.durak_kotlari(g)
    ekle("Durak  ·  seyir", f"{dy['durak_adedi']} durak", f"{kotlar[-1]:g} mm" if kotlar else None)
    #  Binanın giriş katı ( KAT_ADLARI_PLANI ):  adı ve kotu
    if kotlar:
        adlar, giris = katlar.adlar_ve_giris(g)
        ekle("Giriş katı", adlar[giris], dusey.kot_yazisi(kotlar[giris], dusey.kot_ofseti(g)))
    ekle("Askı", _aski(g))
    #  Motor gücü:  avanda avan hesabının seçtiği ( Nsç ), seçicinin motoru değil
    motor = v.get("motor_gucu") if urun else g["proje"].get("avan_motor_gucu")
    ekle("Tahrik", mk.get("tip"), mk.get("yeri"), birimli(motor, "kW"))
    if urun:
        ekle("Tahrik kasnağı", f"ø{mk['tahrik_kasnak_capi']:g}" if mk.get("tahrik_kasnak_capi") else None)
    if urun and ak.get("halat_adedi") and ak.get("halat_capi"):
        ekle("Halat", f"{ak['halat_adedi']:g} × ø{ak['halat_capi']:g}")
    ch = dy.get("kabin_ic_yukseklik")
    ekle("Kabin", f"CW × CD  {kb['genislik']:g} × {kb['derinlik']:g}", f"iç yükseklik {ch:g}" if ch else None)
    dh = kp.get("yukseklik")
    ekle("Kapı", f"DW × DH  {kp['genislik']:g} × {dh:g}" if dh else f"DW  {kp['genislik']:g}", kp.get("tip"))
    ekle("Kuyu", f"SW × SD  {ku['genislik']:g} × {ku['derinlik']:g}")
    dip, oh = kd.get("derinlik"), dy.get("son_kat")
    ekle("Kuyu dibi  ·  üst boşluk", f"{dip:g}" if dip else None, kisaltmalar.kodlu("OH", oh) if oh else None)

    #  Konsol arası:  kesitte zincirin adı aralığa sığmayınca yalnız değer yazılır
    #  ( 6 Kas çizim denetimi, karar D4 ) — hangi rayın olduğu burada
    def konsol(ad):
        return f"konsol arası {dy[ad]:g}" if urun and dy.get(ad) else None

    ekle(
        "Kabin rayı",
        profil(v.get("kabin_rayi")) if urun else None,
        kisaltmalar.kodlu("DBG", kr["arasi"]),
        konsol("kabin_konsol_arasi"),
    )
    ekle(
        "Ağırlık rayı",
        profil(v.get("agirlik_rayi")) if urun else None,
        kisaltmalar.kodlu("DBGW", ag["ray_arasi"]),
        konsol("agirlik_konsol_arasi"),
    )
    ekle("Karşı ağırlık", f"{ag['genislik']:g} × {ag['derinlik']:g}", ag.get("yeri"))
    if kd.get("kabin_tampon_adedi"):
        adet = f"kabin {kd['kabin_tampon_adedi']}  ·  ağırlık {kd.get('agirlik_tampon_adedi') or 0}"
        ekle("Tamponlar", v.get("tampon"), adet)
    ekle("Güvenlik tertibatı", v.get("guvenlik"))
    #  Makine dairesinin açıklıkları ve uygunluğu ( m.5.2.6.3.2 ):  kesitin ölçüleri
    #  yalnız değer, "≥" burada ( 6 Kas çizim denetimi, karar D2 — aynı sayılar:
    #  donanim.oda_acikliklari ).  İki satır:  tek satırda tablo 149 mm'den 189 mm'ye
    #  genişliyordu
    if mk.get("yeri") == "Makine dairesi":
        Y = dusey.yerlesim(g)
        if isinstance(Y, dict) and Y.get("M") and Y["M"].get("oda_tavan") is not None:
            acik = donanim.oda_acikliklari(g, Y["M"])
            ekle("Makine dairesi", *(f"{ad} {d:g} ≥ {en:g}" for ad, d, en in acik if ad != "kasnak üstü"))
            ekle("Tahrik kasnağı üstü", *(f"{d:g} ≥ {en:g}" for ad, d, en in acik if ad == "kasnak üstü"))
    if urun and kd.get("regulator_kasnak_capi"):
        ekle(
            "Regülatör",
            kd.get("regulator_yan"),
            f"kasnak ø{kd['regulator_kasnak_capi']:g}",
            f"halat ø{kd['regulator_halat_capi']:g}" if kd.get("regulator_halat_capi") else None,
        )
    return r


def ciz(g):
    """Üç tablo alt alta:  ASANSÖR VERİLERİ, KISALTMALAR ( paftanın bütün
    çizimlerinin kodları ), NOTLAR.  Sol üst köşe ( 0 , 0 )."""
    veri = satirlar(g)
    sutun = max(kisaltmalar.KOD_SUTUNU, max(eleman.yazi_eni(ad, uslup.NORMAL) for ad, _ in veri) + 120.0)
    t1, alt = kisaltmalar.tablo(0.0, 0.0, "ASANSÖR VERİLERİ", veri, "veriler", sutun=sutun)
    kodlar = [
        (k, kisaltmalar.KODLAR[k])
        for k in kisaltmalar.projede(g, kisaltmalar.kullanilanlar(geometri.plan(g)))
    ]
    t2, alt = kisaltmalar.tablo(0.0, alt - 2 * kisaltmalar.SATIR, "KISALTMALAR", kodlar, "kisaltmalar")
    kotla = "kot_ofseti" in (g.get("dusey") or {})
    ek = ((KOT_NOTU,) if kotla else ()) + ((avan_kipi.NOT,) if g["proje"].get("avan") else ())
    #  m.5.2.2.4 a:  derin kuyu dibinde merdiven çizilmez, kapı gerekir ( 22 Kas )
    if standart.kuyu_dibi_kapisi_gerekir((g.get("kuyu_dibi") or {}).get("derinlik")):
        ek += (standart.KUYU_DIBI_KAPISI_NOTU,)
    notlar = [(f"{i}.", n) for i, n in enumerate(NOTLAR + ek, 1)]
    #  Kuyu dibinde sabit merdivene yer yok ( 27 Kas — merdiven çizime engel değil:  kuyu_dibi ).
    #  Uzun not tablonun enine sarılır:  tek satırda blok iki katından geniş olurdu
    merdiven = _merdiven_notu(g)
    if merdiven:
        en = max(
            kisaltmalar.tablo_eni("ASANSÖR VERİLERİ", veri, sutun=sutun),
            kisaltmalar.tablo_eni("KISALTMALAR", kodlar),
            kisaltmalar.tablo_eni("NOTLAR", notlar, sutun=NOT_SUTUNU),
        )
        s = _sar(merdiven, en - NOT_SUTUNU, uslup.NORMAL)
        notlar += [(f"{len(notlar) + 1}.", s[0])] + [("", x) for x in s[1:]]
    t3, _ = kisaltmalar.tablo(0.0, alt - 2 * kisaltmalar.SATIR, "NOTLAR", notlar, "notlar", sutun=NOT_SUTUNU)
    return t1 + t2 + t3


def _merdiven_notu(g):
    """Kuyu dibinde sabit merdivene yer yoksa notu ( kuyu_dibi.yerlesim — istekte
    önbellekli;  standart.KUYU_DIBI_MERDIVEN_NOTU ), yoksa None."""
    Y = kuyu_dibi.yerlesim(g)
    return Y.get("merdiven_notu") if isinstance(Y, dict) else None


#  Sarılan notta bölünmeyen kısa ayracın en çok sözcüğü ( "( F.5 c )" )
KISA_AYRAC = 3


def _parcalar(metin):
    """Notun bölünmez parçaları ( sözcük, ardındaki boşlukla ):  kısa ayraç ( KISA_AYRAC )
    tek parça;  uzun ayraçta ")" önceki, tek başına "(" sonraki sözcüğe yapışık — satır ")"
    ile başlamaz, "(" ile bitmez ( tarayıcıda görüldü:  satır ");" ile başlıyordu )."""
    sozcukler, out, i = re.findall(r"\S+\s*", metin), [], 0
    while i < len(sozcukler):
        p = sozcukler[i]
        if p.strip() == "(":
            j = next((k for k in range(i + 1, len(sozcukler)) if sozcukler[k].startswith(")")), None)
            if j is not None and j - i - 1 <= KISA_AYRAC:
                out.append("".join(sozcukler[i : j + 1]))
                i = j + 1
                continue
        #  Birim sayısından ayrılmaz ( "800 mm" — satır "mm" ile başlıyordu )
        birim = re.match(r"(mm|cm|m|kg)\b", p) and re.search(r"\d\s*$", out[-1] if out else "")
        if out and (p.startswith(")") or out[-1].strip() == "(" or birim):
            out[-1] += p
        else:
            out.append(p)
        i += 1
    return out


def _sar(metin, en, h):
    """Notu en'e sığan satırlara böler ( _parcalar'dan;  boşluklar korunur )."""
    satirlar, s = [], ""
    for p in _parcalar(metin):
        if s and eleman.yazi_eni((s + p).rstrip(), h) > en:
            satirlar.append(s.rstrip())
            s = ""
        s += p
    return satirlar + ([s.rstrip()] if s.strip() else [])

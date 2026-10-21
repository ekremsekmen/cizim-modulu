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

from cizim import arka_aski
from cizim import dusey
from cizim import eleman
from cizim import geometri
from cizim import kisaltmalar
from cizim import sabitler
from cizim import uslup

BASLIK = "VERİLER VE KISALTMALAR"

#  Genel notlar:  yalnız çizimlerin kendisinden bilinenler
NOTLAR = ("Ölçüler mm, kotlar m.",)


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

    def ekle(ad, *degerler):
        dolu = [d for d in degerler if d]
        if dolu:
            r.append((ad, "  ·  ".join(dolu)))

    def profil(metin):
        #  Formun profil adı "89 x 62 x 15,88":  çarpı işaretiyle ( tablonun öbür ölçüleri gibi )
        return metin.replace(" x ", " × ") if metin else None

    def birimli(x, birim):
        return f"{x:g} {birim}" if x else None

    ekle("Asansör", v.get("tip"))
    ekle("Beyan yükü", birimli(v.get("yuk"), "kg"), birimli(v.get("kisi"), "kişi"))
    ekle("Beyan hızı", f"{dy['beyan_hizi']:.2f} m/s")
    kotlar, _hata = dusey.durak_kotlari(g)
    ekle("Durak  ·  seyir", f"{dy['durak_adedi']} durak", f"{kotlar[-1]:g} mm" if kotlar else None)
    ekle("Askı", _aski(g))
    ekle("Tahrik", mk.get("tip"), mk.get("yeri"), birimli(v.get("motor_gucu"), "kW"))
    ekle("Tahrik kasnağı", f"ø{mk['tahrik_kasnak_capi']:g}" if mk.get("tahrik_kasnak_capi") else None)
    if ak.get("halat_adedi") and ak.get("halat_capi"):
        ekle("Halat", f"{ak['halat_adedi']:g} × ø{ak['halat_capi']:g}")
    ch = dy.get("kabin_ic_yukseklik")
    ekle("Kabin", f"CW × CD  {kb['genislik']:g} × {kb['derinlik']:g}", f"iç yükseklik {ch:g}" if ch else None)
    dh = kp.get("yukseklik")
    ekle("Kapı", f"DW × DH  {kp['genislik']:g} × {dh:g}" if dh else f"DW  {kp['genislik']:g}", kp.get("tip"))
    ekle("Kuyu", f"SW × SD  {ku['genislik']:g} × {ku['derinlik']:g}")
    dip, oh = kd.get("derinlik"), dy.get("son_kat")
    ekle("Kuyu dibi  ·  üst boşluk", f"{dip:g}" if dip else None, kisaltmalar.kodlu("OH", oh) if oh else None)
    ekle("Kabin rayı", profil(v.get("kabin_rayi")), kisaltmalar.kodlu("DBG", kr["arasi"]))
    ekle("Ağırlık rayı", profil(v.get("agirlik_rayi")), kisaltmalar.kodlu("DBGW", ag["ray_arasi"]))
    ekle("Karşı ağırlık", f"{ag['genislik']:g} × {ag['derinlik']:g}", ag.get("yeri"))
    if kd.get("kabin_tampon_adedi"):
        adet = f"kabin {kd['kabin_tampon_adedi']}  ·  ağırlık {kd.get('agirlik_tampon_adedi') or 0}"
        ekle("Tamponlar", v.get("tampon"), adet)
    ekle("Güvenlik tertibatı", v.get("guvenlik"))
    if kd.get("regulator_kasnak_capi"):
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
    notlar = [(f"{i}.", n) for i, n in enumerate(NOTLAR, 1)]
    t3, _ = kisaltmalar.tablo(0.0, alt - 2 * kisaltmalar.SATIR, "NOTLAR", notlar, "notlar", sutun=120.0)
    return t1 + t2 + t3

# -*- coding: utf-8 -*-
"""
YERLEŞİMİN ÖLÇÜ LİSTESİ — hesabın çizimden aldığı geometri

Çizim kabini, rayları, makineyi, kasnakları ve halatları kullanıcının
girdilerinden yerleştirir.  Hesap aynı büyüklükleri eskiden kendi kaba
formülleriyle TAHMİN ediyordu ( kabin merkezi için sabit bir 130 mm, halat
boyu için "kuyu boyu − yığın + 5 m" … );  iki sayı ayrışınca pafta kendi
içinde çelişiyordu.  Burada o büyüklükler çizimin kurduğu yerleşimden
ölçülür ve hesaba girer ( engine/uygulama/girdi.yerlesim_olculeri ).

    kabin_merkezi_x     kabinin iç tabanının ortası − kabin ray ekseni ( mm, arkaya + )
    esik_x              kabin eşiğinin ortası − kabin ray ekseni ( mm;  m.5.7.2.3.6
                        eşik kuvvetini "kabin girişinin eşiğinin ortasına" koyar )
    kabin_ray_boyu      en uzun kabin rayı:  kuyu tabanından üst ucuna ( m )
    agirlik_ray_boyu    en uzun karşı ağırlık rayı ( m )
    aski_halat_boyu     bir askı halatının kabin tarafındaki boyu, kabin en alt
                        durakta ( m ):  tahrik kasnağından kabine;  2:1'de kabin
                        kasnaklarının altından geçip kuyu tavanındaki bağlantıya
    reg_halat_boyu      regülatör halatı ( m ):  regülatör kasnağı ile gergi
                        kasnağı arası iki kez + iki yarım sarım
    kasnak_tek_yon      Nps ( EN 81-50 Ek E ):  halatın bir kesitinin üzerinden
                        geçtiği çizilen kasnaklar ( tahrik kasnağı hariç )
    kasnak_ters_yon     Npr:  çizilen düzenlerde halat hep aynı yöne bükülür — 0
    kasnak_kabin_adedi  kabinle hareket eden kasnaklar ( atalet:  iPcar )
    kasnak_agirlik_adedi  karşı ağırlıkla hareket eden kasnaklar ( iPcwt )
    saptirma_agirlik_capi  makine dairesinde karşı ağırlık tarafındaki sabit
                        saptırma kasnağının çapı ( atalet:  mDP );  yoksa 0
    yan_yatak_boyu      makine kirişinin mesnet aralığı ( bölüm 2'nin L'si ):  makine
                        dairesizde kirişler karşı ağırlık raylarına oturur ( DBGW ),
                        makine dairesinde kaidenin dikine kirişleri arası ( kaide
                        halatlara ortalı, makineyi sarar — makine_dairesi.yerlesim )
    makine_yuku_x       makine yükünün ( tahrik kasnağının ) aynı kirişte mesnede
                        uzaklığı ( bölüm 2'nin X'i )

KURMA İLE DENETİM AYRIDIR:  çizimin denetim hataları ( sığınma alanı,
çakışma … ) bu ölçüleri durdurmaz;  yalnız geometri hiç kurulamazsa ilgili
ölçü listede yer almaz ve hesap kendi yaklaşığını kullanır ( raporda yazar ).
"""

import logging
import math

from temel import sayi_mi
from cizim import arka_aski as CAA
from cizim import donanim as CDN
from cizim import dusey as CDY
from cizim import girdi as CG
from cizim import kuyu_dibi as CKD
from cizim import makine_dairesi as CMD
from cizim import sabitler as CS

log = logging.getLogger(__name__)


def plan_olculeri(g, S):
    """Kabinin ve eşiğinin ray eksenine uzaklığı — planın kendi tanımıyla
    ( cizim/girdi:  kabin merkezi = ön yüz + derinlik / 2 )."""
    kb, ray_y = g["kabin"], g["kabin_ray"]["kapi_arasi"]
    return {
        "kabin_merkezi_x": round(kb["on_pay"] + kb["derinlik"] / 2.0 - ray_y, 3),
        "esik_x": round(
            kb["on_pay"] - CG.esik_derinligi(S, g["kapi"].get("tip"), kabin=True) / 2.0 - ray_y, 3
        ),
    }


def kasnak_sayilari(g, saptirma):
    """Nps · Npr ve atalete giren kasnaklar — çizilen askı düzeninden.

    Kabin tarafındaki kesit kabin kasnaklarından ( 2:1'de iki ), karşı ağırlık
    tarafındaki kesit ağırlık kasnağından ve makine dairesindeki saptırma
    kasnağından geçer;  Nps bu ikisinin büyüğüdür ( Ek E:  en olumsuz kesit )."""
    iki_bir = (g.get("aski") or {}).get("duzen") != "Doğrudan"
    kabin = 2 if iki_bir else 0
    agirlik = 1 if iki_bir else 0
    sap = 1 if saptirma else 0
    return {
        "kasnak_tek_yon": max(kabin, agirlik + sap),
        "kasnak_ters_yon": 0,
        "kasnak_kabin_adedi": kabin,
        "kasnak_agirlik_adedi": agirlik,
        "saptirma_agirlik_capi": float(saptirma["D"]) if saptirma else 0.0,
    }


def _mrl_kiris_yuku(g, S, KU):
    """Makine dairesizde makine kirişleri karşı ağırlık raylarına oturur:
    mesnetler rayların birbirine bakan yüzleri ( aralık DBGW ), yük tahrik
    kasnağının düzleminde ( iki halat inişi de oradadır ).  X mesnetten yüke."""
    taban = KU["taban"]
    raylar = sorted(CKD._raylar(taban, "agirlik_ray"), key=lambda r: r[1])
    if len(raylar) < 2:
        return None, None
    a, b = raylar[0][3], raylar[-1][1]  # ön rayın arka, arka rayın ön yüzü
    y0 = (KU["kasnak"][1] + KU["kasnak"][3]) / 2.0
    X = y0 - a
    return (round(X, 3) if 0.0 < X < b - a else None), round(b - a, 3)


def _duvar_kiris_yuku(KU):
    """Arkadaki ağırlıkta makine dairesizde makine duvardan duvara iki kirişe
    oturur ( kuyu_ustu._arka ):  mesnetler ön ve arka duvarın iç yüzü ( uçlarda
    bağlantı levhası — "duvarlara monteli" ), açıklık kuyu derinliği;  yük
    tahrik kasnağının merkezinde ( iki kirişin ortasında:  her birine F / 2 )."""
    sase, ks = KU["sase"], KU["kasnak"]
    L = sase[3] - sase[1]
    X = (ks[1] + ks[3]) / 2.0 - sase[1]
    return (round(X, 3) if 0.0 < X < L else None), round(L, 3)


def _md_kiris_yuku(g, S, MD):
    """Makine dairesinde makine kaidenin yan yataklarındadır:  mesnetler
    dikine kirişlerin eksenleri ( uçlardan E.h / 2 içeride — mesnet aralığı yan
    yatak boyu ), yük tahrik kasnağının merkezinde."""
    c, K = MD.get("cerceve"), MD.get("kaide")
    if c is None or not K:
        return None, None
    kasnak = MD["M"]["kasnak"]
    u0 = (c[0] if K["uzun_x"] else c[1]) + K["E"]["h"] / 2.0
    u1 = (c[2] if K["uzun_x"] else c[3]) - K["E"]["h"] / 2.0
    yuk = ((kasnak[0] + kasnak[2]) / 2.0) if K["uzun_x"] else ((kasnak[1] + kasnak[3]) / 2.0)
    X = yuk - u0
    return (round(X, 3) if 0.0 < X < u1 - u0 else None), round(u1 - u0, 3)


def _kiris(X, L):
    """Kirişin açıklığı ve yükün yeri:  açıklık varsa L;  X yalnız açıklığın
    içindeyse ( yoksa hesap ofis kabulüyle sürer, raporda KABUL )."""
    out = {}
    if L is not None:
        out["yan_yatak_boyu"] = L
        if X is not None:
            out["makine_yuku_x"] = X
    return out


def hesap_olculeri(g):
    """Hesabın çizimden aldığı ölçüler ( sözlük ).  g:  kurulmuş çizim girdisi
    ( cizim/kopru.cizim_girdisi ).  Kurulamayan ölçü sözlükte yer almaz."""
    S = CS.sabitler(g.get("_cizim_sabitleri"))
    out = plan_olculeri(g, S)
    mk = g.get("makine") or {}
    mrl = mk.get("yeri") == "Kuyu üstü"

    saptirma, halat = None, True
    if not mrl:
        try:
            MD = CMD.yerlesim(g, S)
        except Exception:
            log.debug("yedek değer kullanılıyor ( çizim kendi hatasını söyler )", exc_info=True)
            MD = {}
        #  Ağırlık halatının yolu kurulamadıysa saptırma kasnağı var mı yok mu
        #  bilinmez:  kasnak sayıları çizimden verilmez.
        halat = "M" in MD and not MD.get("halat_kurulamadi")
        if "M" in MD:
            saptirma = MD.get("saptirma")
            out.update(_kiris(*_md_kiris_yuku(g, S, MD)))
    if halat:
        out.update(kasnak_sayilari(g, saptirma))

    #  ── DÜŞEY:  kabin en alt durakta ( kot 0 ) ──────────────────────────
    dy = g.get("dusey") or {}
    try:
        kotlar, _h = CDY.durak_kotlari(g)
        H = kotlar[-1]
        KY = g["kuyu_dibi"]["derinlik"]
        M = CDN.yerlesim(g, S, H, H + dy["son_kat"], -KY)
    except Exception:
        log.debug("yedek değer kullanılıyor ( çizim kurulamadı )", exc_info=True)
        return out
    if "raylar" not in M or "kasnak" not in M:
        return out
    if mrl and "KU" in M:
        KU = M["KU"]
        out.update(
            _kiris(*(_duvar_kiris_yuku(KU) if KU.get("duvardan_duvara") else _mrl_kiris_yuku(g, S, KU)))
        )

    for tur, anahtar in (("kabin", "kabin_ray_boyu"), ("agirlik", "agirlik_ray_boyu")):
        boy = [r["ust"] - r["alt"] for r in M["raylar"] if r["tur"] == tur]
        if boy:
            out[anahtar] = round(max(boy) / 1000.0, 4)

    #  Regülatör halatı:  iki düşey kol + kasnaklardaki iki yarım sarım
    reg, ger = M.get("regulator_kasnak"), M.get("gergi")
    if reg and ger and sayi_mi(ger.get("cap")):
        Dr = g["kuyu_dibi"]["regulator_kasnak_capi"]
        out["reg_halat_boyu"] = round(
            (2.0 * (reg[-1] - ger["merkez"]) + math.pi * (Dr + ger["cap"]) / 2.0) / 1000.0, 4
        )

    #  Askı halatı, kabin tarafı, kabin en alt durakta:  tahrik kasnağının
    #  merkezinden ( halat kasnağı merkez kotunda teğet bırakır ) kabine.
    aski = g.get("aski") or {}

    #  Karşı ağırlık dolgusuna kalan yükseklik ( karar 11 ):  patenler
    #  çerçevenin dışındadır, çerçeve paten arasından bir paten boyu kısadır;
    #  dolgu alt kirişin üstünden üst kirişin altına, 2:1'de ağırlık
    #  kasnağının altına kadardır.
    AG = M.get("agirlik")
    if AG and sayi_mi(AG.get("yukseklik")):
        alt, ust = CDN.agirlik_dolgu_kotlari(g, S, CDN.agirlik_kotlari(M, 0.0))
        out["agirlik_dolgu_yuksekligi"] = round(ust - alt, 1)
    zk = M["kasnak"][4]
    kab = CDN.kabin_kotlari(dy, S, 0.0, aski, CAA.arkada_iki_bir(g))
    if aski.get("duzen") == "Doğrudan":
        #  1:1:  halatlar kabin şasesinin üst kirişindeki bağlantıda biter
        out["aski_halat_boyu"] = round((zk - kab["baglanti_ust"]) / 1000.0, 4)
    elif M.get("kabin_baglanti") and sayi_mi(aski.get("kasnak_capi")) and sayi_mi(aski.get("kasnak_arasi")):
        #  2:1:  kasnaktan kabin kasnağına iner, iki kasnağın altından ( ya da
        #  kabin üstünde kasnakların altından ) geçer, kuyu tavanındaki
        #  bağlantıya çıkar;  her kasnakta çeyrek sarım.
        zc = kab["kasnak_merkez"]
        z_bag = M["kabin_baglanti"][4]
        Dk, ara = aski["kasnak_capi"], aski["kasnak_arasi"]
        out["aski_halat_boyu"] = round(((zk - zc) + (z_bag - zc) + ara + math.pi * Dk / 2.0) / 1000.0, 4)
    return out

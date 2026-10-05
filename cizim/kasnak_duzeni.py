# -*- coding: utf-8 -*-
"""
KASNAK DÜZENLEMESİ  —  tahrik kasnağı, saptırma kasnağı ve halatlar
( LiftDesigner "kasnak düzenlemesi" gibi, 1/20 )

Tahrik kasnağının ekseni boyunca bakılır ( kasnak daire görünür — halat
düzleminde ):  makine ve kaidesi ( makine dairesizde şasesi ), saptırma kasnağı,
makine dairesinde döşeme, halatların kasnaktan inişleri, tahrik kasnağında
halatın sardığı yay ve sarım açısı.  Düşey kesitlerle aynı yerleşimden çizilir
( donanim · makine_dairesi · kuyu_ustu ):  pafta kendi içinde çelişmez, açı
hesabın kullandığıyla aynıdır ( kopru.sarim_acisi ).

Ölçüler:  tahrik ve saptırma kasnağının çapı, merkezleri arası ( yatay, düşey ),
iki halat inişinin arası ( LiftDesigner RDA / RDB ), kasnak merkezlerinin
tabliyenin üstünden ( makine dairesizde kuyu tavanından ) yüksekliği.
LiftDesigner'ın her projede aynı 1.600'ü çizilmez ( anlamı belli değil —
kullanıcı kararı 1 Eki );  LiftDesigner makine dairesizde sarım açısını "0"
yazar — burada çizimin açısı ( düşey inişte 180° ).
"""
import math

from cizim import geometri as CGE
from cizim import kesit_parcalari as CKP
from cizim import kuyu_kesiti as CKK
from cizim import makine as CMK

#  Makine dairesinin döşemesinden gösterilen kalınlık ( altı kırık çizgi ) —
#  çizimin görünüşü ( ölçü değildir )
DOSEME_GOSTERIM = 300.0


def dogrula(g):
    return CKK.dogrula(g)


def _inisler(KU):
    """Tahrik kasnağından inen iki halatın planda geçtiği noktalar:  ( kabin
    tarafı , ağırlık tarafı ) — saptırma kasnağı yokken ağırlık tarafı düşeydir."""
    if "kabin_inis" in KU:                  # arkadaki ağırlıkla 2:1 ( çapraz )
        kab = KU["kabin_inis"]
    elif "kabin_nokta" in KU:               # 1:1
        kab = KU["kabin_nokta"]
    else:                                   # 2:1, ağırlık yanda
        kab = (KU["yakin"], KU["halatlar"][0][1])
    return kab, KU["ag_dusus"]


def ciz(g, cizim_sabitleri=None):
    """Kasnak düzenlemesinin elemanları."""
    from cizim import kopru as CK
    Y = CKK.yerlesim(g, cizim_sabitleri)
    M = Y["M"]
    KU = M["KU"]
    G = g["kuyu"]["genislik"]
    duz = KU.get("duzlem")
    #  Kasnağın daire göründüğü bakış ( kesit_parcalari.donanim ile aynı kural )
    B = CKP.Bakis("yan" if duz is not None and duz.yon == "y" else "on", G)
    e = CMK.gorunus(M["sase_parcalari"] + M["makine"], B, CGE._dik, CGE._daire, CGE._cizgi)
    ks = M["kasnak"]
    D1 = g["makine"]["tahrik_kasnak_capi"]
    R1 = D1 / 2.0
    uc, zt = B.u((ks[0] + ks[2]) / 2.0, (ks[1] + ks[3]) / 2.0), ks[4]
    #  Saptırma kasnağı ( makine dairesinde, gerekiyorsa ):  merkezi döşemeden
    md = M.get("MD") or {}
    sp = md.get("saptirma")
    if sp:
        zd = M["tabliye_ustu"]
        sx, sy = md["duzlem"].p(sp["u"])
        us, zs, R2 = B.u(sx, sy), zd + sp["z"], sp["D"] / 2.0
    #  Halatlar:  kabin tarafı kasnağın yanından düşey;  ağırlık tarafı
    #  saptırmaya ortak teğetle, ondan düşey ( yoksa kasnağın öbür yanından )
    kab, ag = _inisler(KU)
    uk = B.u(*kab)
    p0, q0, p1_, q1 = CGE.sinir(e)                   # makine ve kaide ( ya da şase )
    #  Makinenin oturduğu tabliye ( kuyunun üstündeki beton ) yalnız üstünden
    #  DOSEME_GOSTERIM kadar, kırık çizgiyle gösterilir.
    oda = M.get("tabliye_ustu")
    if oda is not None:
        t_ciz = min(M["tabliye"]["doseme"], DOSEME_GOSTERIM)
    alt_parca = min(q0, zt - R1, oda - t_ciz if oda is not None else q0)
    z_alt = alt_parca - 650                          # alt ölçüler döşemenin altında
    halat = [(uk, zt, uk, z_alt)]
    if M.get("agirlik_yolu"):
        for p, q in M["agirlik_yolu"]:
            halat.append((B.u(p[0], p[1]), p[2], B.u(q[0], q[1]), q[2]))
        dx, dy_, dz = M["agirlik_dusus"]
        ua, za_ = B.u(dx, dy_), dz
        p1 = M["agirlik_yolu"][0][0]
        teget = (B.u(p1[0], p1[1]), p1[2])
    else:
        ua, za_ = B.u(*ag), zt
        teget = (ua, zt)
    halat.append((ua, za_, ua, z_alt))
    for u0, z0, u1, z1 in halat:
        e.append(CGE._ad(CGE._cizgi("HALAT", u0, z0, u1, z1), "aski_halati"))
    e.append(CGE._ad(CGE._yazi(uk, z_alt - 90, "KABİNE", 45), "halat_adi"))
    e.append(CGE._ad(CGE._yazi(ua, z_alt - 90, "AĞIRLIĞA", 45), "halat_adi"))
    #  Makine dairesinde döşeme ( tabliye ) — halatlar delikten geçer
    u0_, u1_ = min(p0, uk, ua) - 200, max(p1_, uk, ua) + 200
    if oda is not None:
        za = oda - t_ciz
        e.append(CGE._ad(CGE._dik("TARAMA", u0_, za, u1_ - u0_, t_ciz, tip="tarama"), "tabliye"))
        for a, b in (((u0_, za), (u0_, oda)), ((u0_, oda), (u1_, oda)), ((u1_, oda), (u1_, za))):
            e.append(CGE._ad(CGE._cizgi("KUYU-DUVAR", a[0], a[1], b[0], b[1]), "tabliye"))
        #  Kırık çizgi ( döşeme aşağı devam eder )
        n = max(2, int((u1_ - u0_) / 150))
        kir = [(u0_ + (u1_ - u0_) * i / n, za + (35 if i % 2 else -35) * (0 < i < n)) for i in range(n + 1)]
        for a, b in zip(kir, kir[1:]):
            e.append(CGE._cizgi("KUYU-IC", a[0], a[1], b[0], b[1]))
    else:
        #  Makine dairesiz:  kuyu tavanı ( şasenin üstünde )
        tavan = Y["kotlar"][-1] + g["dusey"]["son_kat"]
        e.append(CGE._ad(CGE._cizgi("KUYU-DUVAR", u0_, tavan, u1_, tavan), "kuyu_tavani"))
    #  Sarım:  halatın tahrik kasnağında sardığı yay ( kabin tarafının yatay
    #  ucundan kasnağın üstünden ağırlık tarafının teğetine ) ve açısı
    alfa = M.get("sarim_acisi")
    if alfa is None:
        alfa = CK.sarim_acisi(g)
    a0 = 0.0 if uk > uc else math.pi
    a1 = math.atan2(teget[1] - zt, teget[0] - uc)
    yon = 1.0 if a0 == 0.0 else -1.0                  # kasnağın üstünden
    fark = (yon * (a1 - a0)) % (2 * math.pi)
    rr, n = R1 + 25, 24
    nokta = [(uc + rr * math.cos(a0 + yon * fark * i / n), zt + rr * math.sin(a0 + yon * fark * i / n))
             for i in range(n + 1)]
    for p, q in zip(nokta, nokta[1:]):
        e.append(CGE._ad(CGE._cizgi("HALAT", p[0], p[1], q[0], q[1]), "sarim_yayi"))
    #  Tahrik kasnağı en üstte:  dişli makinede dişli kutusu önüne düşüyordu —
    #  görünüşün konusu kasnaklar ve halat
    e.append(CGE._ad(CGE._daire("KASNAK", uc, zt, R1), "tahrik_kasnagi"))
    metin = (f"SARIM AÇISI {alfa:.0f}°" if alfa is not None
             else "SARIM AÇISI ağırlığın konumuyla değişir ( halat sapması — hesapta girdi )")
    e.append(CGE._ad(CGE._yazi(uc, max(q1, zt + R1) + 420, metin, 60), "sarim_acisi"))

    O = CGE._olcu
    #  Çaplar ( LiftDesigner:  kasnağın üstünde )
    e.append(O("yatay", (uc - R1, 0), (uc + R1, 0), zt + R1 + 150, f"Ø {D1:g}"))
    if sp:
        e.append(O("yatay", (us - R2, 0), (us + R2, 0), zs - R2 - 150, f"Ø {2 * R2:g}"))
    #  Alt:  merkezler arası ( yatay ) ve iki halat inişinin arası
    k1 = z_alt + 150
    if sp and abs(us - uc) > 1e-6:
        e.append(O("yatay", (min(us, uc), 0), (max(us, uc), 0), k1 + 230, None))
    e.append(O("yatay", (min(uk, ua), 0), (max(uk, ua), 0), k1, f"HALAT ARASI {abs(ua - uk):.0f}"))
    #  Sağ:  merkezlerin döşemeden ( makine dairesizde kuyu tavanına ) yüksekliği
    s = u1_ + 150
    if oda is not None:
        zinc = [oda] + ([zs] if sp else []) + [zt]
        for a, b in zip(zinc, zinc[1:]):
            e.append(O("dusey", (0, a), (0, b), s, None))
    else:
        e.append(O("dusey", (0, zt), (0, tavan), s, None))
    e = [el for el in e if not (el["tip"] == "olcu" and el["uzunluk"] < 1e-6)]
    CGE._yazilari_yerlestir(e)
    return e

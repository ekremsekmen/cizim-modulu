# -*- coding: utf-8 -*-
"""
KUYU DONANIMININ DÜŞEY YERLERİ

Planlar donanımın YATAY yerini verir ( kuyu_plani, kuyu_dibi, kuyu_ustu );
bu modül aynı parçaların KOTLARINI ekler ki düşey kesitler çizebilsin ve
açıklıkları denetleyebilsin:

  · makine, şasesi, tahrik kasnağı                ( makine dairesizde kuyu tepesinde )
  · kabin ve ağırlık halat bağlantıları           ( 2:1 askıda kuyu tepesinde )
  · hız regülatörü ( tepede ) ve gergi düzeni ( kuyu dibinde )
  · rayların üst uçları, konsolları, ek yerleri
  · karşı ağırlığın çerçevesi, kasnağı, patenleri

Kotlar sabitler.py'deki referans proje ölçüleridir.  Düşey eksen döşeme kotudur
( 0 = en alt durak );  kuyu tavanı = en üst durak + son kat.

Makine daireli projede makine, bağlantılar, regülatör ve kumanda panosu
kuyunun üstündeki odadadır ( yerleri makine_dairesi.yerlesim ):  kuyunun
üstünü kuyu döşemesi kalınlığında bir beton kapatır ( TABLİYE );  makine,
bağlantılar ve regülatör onun üstüne oturur, halatlar döşeme deliklerinden
kuyuya iner.  Oda zemini tabliyenin üstünden "tabliye beton yüksekliği" kadar
aşağıdadır ( makine_dairesi.tabliye ).  Kuyuda raylar ve karşı ağırlık kalır;
rayların üst ucu kuyu tavanının en alt kısmının ( tavan_kirisi ) kabin_rayi_tepe
kadar altındadır — tavana değmez ( referans proje:  tavanın 50 altı ).

MAKİNE DAİRESİNİN DENETİMLERİ ( TS EN 81-20 )
  m.5.2.6.3.2.1  çalışma alanlarında temiz yükseklik ≥ 2,10 m — odanın
                 zemininde ve makinenin durduğu tabliyenin üstünde
  m.5.2.6.3.2.3  korumasız dönen parçaların ( tahrik kasnağı ) üstünde ≥ 0,30 m
  m.5.2.3.2 a    makine dairesi kapısı ≥ 2,0 m yüksek ( eni makine_dairesi.py'de )
"""

from temel import ortusur, sayi_mi
from cizim import sorun
from cizim import istek_onbellegi
from cizim import kuyu_dibi
from cizim import kuyu_ustu
from cizim import makine
from cizim import makine_dairesi

MAKINE_YERLERI = ("Kuyu üstü", "Makine dairesi")
ODA_YUKSEKLIK = 2100.0  # m.5.2.6.3.2.1
DONEN_PARCA_USTU = 300.0  # m.5.2.6.3.2.3
ODA_KAPI_YUKSEKLIK = 2000.0  # m.5.2.3.2 a


def konsol_kotlari(taban, ust, aralik, S):
    """Konsolların ÜST kotları:  tabandan konsol_ilk, sonra `aralik`;  rayın
    üst ucunu geçmez ( referans proje:  500 + 1.500 · n )."""
    z, kotlar = taban + S["konsol_ilk"], []
    while z <= ust + 1e-6:
        kotlar.append(z)
        z += aralik
    return kotlar


def ek_kotlari(taban, ust, S):
    """Ray eklerinin kotları:  kuyu tabanından her ray boyunda bir."""
    z, kotlar = taban + S["ray_boyu"], []
    while z < ust - 1e-6:
        kotlar.append(z)
        z += S["ray_boyu"]
    return kotlar


@istek_onbellegi.sakla
def yerlesim(g, S, H, tavan, taban):
    """H:  en üst durağın kotu ( seyir ),  tavan:  kuyu tavanı ( döşeme altı ),
    taban:  kuyu tabanı.  Dönen sözlükte her parça ( plandaki kutu, z0, z1 )."""
    mk, dy = g.get("makine") or {}, g.get("dusey") or {}
    hata = []
    yeri = mk.get("yeri")
    if yeri not in MAKINE_YERLERI:
        hata.append(f"makine.yeri: {MAKINE_YERLERI} içinden olmalı ( {yeri!r} ).")
    for alan in ("kabin_konsol_arasi", "agirlik_konsol_arasi"):
        if not (sayi_mi(dy.get(alan)) and dy[alan] > 0):
            hata.append(f"dusey.{alan}: sıfırdan büyük bir sayı olmalı ( {dy.get(alan)!r} ).")
    if hata:
        return {"hata": hata}
    KD = kuyu_dibi.yerlesim(g, S)
    #  KURMA İLE DENETİM AYRI.  Kuyu dibinin, kuyu üstünün, makine dairesinin
    #  DENETİM hatası ( sığınma alanı sığmıyor, gergi çarpıyor, parçalar üst
    #  üste biniyor … ) kotları durdurmaz:  hesabın çizimden aldığı ölçüler
    #  ( halat, ray, regülatör halatı boyları — cizim/olculer.py ) kurulan
    #  geometriden okunur;  hatalar M["hata"] ile çağırana yine gider.  Yalnız
    #  girdi eksikse ( geometri hiç kurulamadıysa ) durulur.
    if "taban" not in KD:
        return {"hata": KD["hata"]}
    hata.extend(KD["hata"])
    mrl = yeri == "Kuyu üstü"
    kabin_raylari = sorted(KD["kabin_raylari"], key=lambda r: r[0])
    agirlik_raylari = KD["agirlik_raylari"]
    tavan_alti = tavan - S["tavan_kirisi"]
    M = {"mrl": mrl, "KD": KD, "hata": hata, "tavan": tavan, "tavan_alti": tavan_alti, "parcalar": []}

    if mrl:
        durdu = _kuyu_ustundeki_makine(g, S, tavan, M, kabin_raylari, agirlik_raylari)
        if durdu is not None:
            return {"hata": hata + durdu}
    else:
        ray_ust = tavan_alti - S["kabin_rayi_tepe"]
        M["raylar"] = [("kabin", r, ray_ust) for r in kabin_raylari] + [
            ("agirlik", r, ray_ust) for r in agirlik_raylari
        ]
        rg = KD["gergi"]
        M["regulator_x"] = (rg[0] + rg[2]) / 2.0
        M["regulator_y"] = (rg[1] + rg[3]) / 2.0
        oda = _makine_dairesi(g, S, tavan, M)
        if "kasnak" not in M:
            return {"hata": hata + oda}
        hata.extend(oda)

    #  ── GERGİ DÜZENİ ( kuyu dibi ) ──────────────────────────────────────
    #  R4K tipi kollu gergi ( kuyu_dibi.gergi_geometrisi ):  plan zarfları
    #  kuyu dibinden, kotlar kasnağın merkezinden ( geometrinin kökü ).
    gp = KD["gergi_donanim"]
    zc = taban + S["gergi_kasnak_merkez"]
    geo = kuyu_dibi.gergi_geometrisi(S, KD["gergi"])
    yon, yan = kuyu_dibi.gergi_yonu(g, KD["gergi"])
    K = geo["kutular"]
    M["gergi"] = {
        "merkez": zc,
        "cap": g["kuyu_dibi"]["regulator_kasnak_capi"],
        "plan": KD["gergi"],
        "yon": yon,
        "yan": yan,
        "geo": geo,
        #  ( y0 , y1 , z0 , z1 ) — planın y aralığı, kesitin kotları
        **{
            ad: (gp[ad][1], gp[ad][3], zc + K[ad][2], zc + K[ad][3])
            for ad in ("kol", "agirlik", "plaka", "kontak")
        },
        #  En yüksek noktası ( koruma kapağı ya da ağırlığın askısı ):  m.5.2.5.8.2 b
        "tepe": zc + geo["tepe"],
    }
    #  ── RAYLAR:  konsollar ve ekler ─────────────────────────────────────
    M["raylar"] = [
        {
            "tur": tur,
            "kutu": kutu,
            "alt": taban,
            "ust": ust,
            "konsollar": konsol_kotlari(
                taban, ust, dy["kabin_konsol_arasi"] if tur == "kabin" else dy["agirlik_konsol_arasi"], S
            ),
            "ekler": ek_kotlari(taban, ust, S),
        }
        for tur, kutu, ust in M["raylar"]
    ]
    hata += _gergi_konsolda(M, S, taban)
    #  ── KARŞI AĞIRLIK ────────────────────────────────────────────────────
    #  Çerçevenin yüksekliği hesabın ağırlık paten arasıdır ( kabin şasesi gibi )
    M["agirlik"] = {
        "kutu": KD["blok"],
        "yukseklik": dy["agirlik_paten_arasi"],
        "kasnak_ust": S["agirlik_kasnak_ust"],
        "paten": S["paten_yukseklik"],
        "paten_arasi": dy["agirlik_paten_arasi"],
        "tampon_ustu": taban + dy["agirlik_tampon_baba"] + dy["agirlik_tampon_boyu"],
    }
    return M


def _gergi_konsolda(M, S, taban):
    """Gerginin plakası ve kontağı bağlı olduğu kabin rayının arkasındadır,
    konsollar gibi:  planda hep üst üste ( kuyu dibi planı yüksekliği bilmez );
    kotları konsollarınkine binmemeli."""
    gr = M["gergi"]
    gx = (gr["plan"][0] + gr["plan"][2]) / 2.0
    ray = next((r for r in M["raylar"] if r["tur"] == "kabin" and r["kutu"][0] <= gx <= r["kutu"][2]), None)
    hata = []
    for ad in ("plaka", "kontak") if ray else ():
        z0, z1 = gr[ad][2], gr[ad][3]
        for z in ray["konsollar"]:
            if z0 < z and z - S["konsol_yukseklik"] < z1:
                hata.append(
                    sorun.Sorun(
                        f"Regülatör gergisinin {kuyu_dibi.GERGI_PARCA[ad]} kabin rayının konsoluna "
                        f"çarpıyor:  konsol tabandan {z - S['konsol_yukseklik'] - taban:g} – {z - taban:g}, "
                        f"{kuyu_dibi.GERGI_PARCA[ad]} {z0 - taban:.0f} – {z1 - taban:.0f} — Sabitler:  "
                        "gergi kasnağının yüksekliği ya da ilk konsol.",
                        (
                            f"gergi_{ad}",
                            "gergi_plakasi" if ad == "plaka" else "gergi_kontagi",
                            "kabin_konsolu",
                        ),
                        "kuyu_kesiti_on",
                    )
                )
                break
    return hata


def _kuyu_ustundeki_makine(g, S, tavan, M, kabin_raylari, agirlik_raylari):
    """Makine dairesizde:  makine şasesi ve makine, bağlantılar, regülatör,
    tavanın altındaki parçalar, rayların üst uçları ( M'ye yazılır ).  Kuyu
    üstünün yerleşimi kurulamazsa hataları ( dur ), yoksa None."""
    hata, tavan_alti = M["hata"], M["tavan_alti"]
    KU = kuyu_ustu.yerlesim(g, S, acil_pano=False)
    if "kasnak" not in KU:
        return KU["hata"]
    hata.extend(KU["hata"])
    M["KU"] = KU
    sol = g["agirlik"]["yeri"] == "Sol"
    #  ── MAKİNE ŞASESİ ve MAKİNE ────────────────────────────────────
    yakin_ray = kabin_raylari[0] if sol else kabin_raylari[-1]
    uzak_ray = kabin_raylari[-1] if sol else kabin_raylari[0]
    #  Duvardan duvara kirişte makine kirişlerin üstünde, tavana yakın
    #  ( 12495-18 );  raylara oturan makinede tavanın 250 altında.
    z_ust = tavan - (
        S["duvar_kirisi_tepe_boslugu"] if KU.get("duvardan_duvara") else S["makine_tepe_boslugu"]
    )
    zs = z_ust - S["makine_kapak_yukseklik"] - S["makine_en"]  # şase üstü
    sase = KU["sase"] + (zs - KU["yan_yatak"]["h"], zs)  # plandaki yeri kuyu_ustu'dan
    kx0, ky0, kx1, ky1 = KU["kasnak"]
    gx0, gy0, gx1, gy1 = KU["govde"]
    mx, my = (kx0 + kx1) / 2.0, (gy0 + gy1) / 2.0
    zk = zs + S["makine_en"] / 2.0  # kasnak merkezi
    #  Kapak ( klemens kutusu ) gövdenin üstünde:  kasnağın düzlem boyundaki
    #  ortası, gövdenin düzleme dik ortası ( makine dairesindeki gibi kanonik ).
    #  21 Eki:  x / y sabitti — arkadaki ağırlıkta kasnak ekseni x olunca kapak
    #  gövdenin değil kasnağın üstüne düşüyor, B-B'de havada duruyordu.
    d = KU.get("duzlem") or kuyu_ustu.Duzlem("x", 0.0)
    ku0, _, ku1, _ = d.kanonik(KU["kasnak"])
    _, gv0, _, gv1 = d.kanonik(KU["govde"])
    ku, gv = (ku0 + ku1) / 2.0, (gv0 + gv1) / 2.0
    kapak = d.kutu(
        ku - S["makine_kapak_en"] / 2.0,
        ku + S["makine_kapak_en"] / 2.0,
        gv - S["makine_kapak_boy"] / 2.0,
        gv + S["makine_kapak_boy"] / 2.0,
    ) + (zs + S["makine_en"], z_ust)
    M.update(
        {
            "makine": _makine_parcalari(g, KU, zk, kapak),
            "sase_parcalari": makine.sase_parcalari(
                sase, (mx, my), KU["yan_yatak"], KU["sase_delikleri"], KU.get("kiris_yonu", "y")
            ),
            "sase": sase,
            "govde": (gx0, gy0, gx1, gy1, zs, zs + S["makine_en"]),
            "kapak": kapak,
            "kasnak": KU["kasnak"] + (zk,),  # + merkez kotu
            "agirlik_baglanti": KU["agirlik_baglanti"] + (zs, zs + S["agirlik_baglanti_yukseklik"]),
            "kabin_baglanti": KU["kabin_baglanti"]
            + (tavan - S["kabin_baglanti_alt"], tavan - S["kabin_baglanti_ust"]),
            #  Regülatör ayağının ( konsol ) üstünde:  kasnak tavandan
            #  regulator_kasnak_merkez, gövde onun eksen altında / tepe üstünde
            "regulator": KU["reg_govde"]
            + (
                tavan - S["regulator_kasnak_merkez"] - KU["reg_cizim"]["geo"]["eksen"],
                tavan - S["regulator_kasnak_merkez"] + KU["reg_cizim"]["geo"]["tepe"],
            ),
            "regulator_kasnak": KU["reg_kasnak"] + (tavan - S["regulator_kasnak_merkez"],),
        }
    )
    M["halat_konsolu"] = makine.kaydir(
        KU["halat_konsolu"], (M["kabin_baglanti"][4] + M["kabin_baglanti"][5]) / 2
    )
    _tavan_alti_parcalari(M, KU, mx, my)
    #  Öbür kabin rayı referans projede tavanın 50 altına çıkar;  tavanın en alt
    #  kısmı ( tavan_kirisi payı ) hesaba katılınca onun 50 altına — eskiden
    #  payın alt yüzüne tam değiyordu.
    ray_ust = {
        "yakin": zs - S["ray_sase_icinde"],
        "uzak": tavan_alti - S["kabin_rayi_tepe"],
        "agirlik": zs - S["ray_sase_icinde"],
    }
    if KU.get("duvardan_duvara"):
        #  Makine raylara oturmaz ( duvardan duvara kirişler ):  raylar
        #  kirişlerin altında biter ( kiriş kuyunun derinliğince uzanır ).
        alt_ = zs - KU["yan_yatak"]["h"] - S["kabin_rayi_tepe"]
        ray_ust = {"yakin": alt_, "uzak": alt_, "agirlik": alt_}
    M["raylar"] = [("kabin", yakin_ray, ray_ust["yakin"]), ("kabin", uzak_ray, ray_ust["uzak"])] + [
        ("agirlik", r, ray_ust["agirlik"]) for r in agirlik_raylari
    ]
    M["regulator_x"], M["regulator_y"] = KU["rgx"], KU["rgy"]
    return None


def _tavan_alti_parcalari(M, KU, mx, my):
    """Tavanın altındaki parçalar:  sığınma ve açıklıklar bunlara da ölçülür
    ( m.5.2.5.7.2:  "kuyu tavanının en alt kısımları — kirişler ve tavanın
    altına yerleştirilmiş parçalar dahil" )."""
    for ad in ("sase", "kabin_baglanti", "agirlik_baglanti", "regulator"):
        p = M[ad]
        if ad == "sase" and KU.get("duvardan_duvara"):
            #  Duvardan duvara iki kiriş kabinin üstünden geçer:  aralarındaki
            #  boşluk engel değil ( çapraz kasnaklar oradan yükselir ) —
            #  kirişler ve motor plakası ayrı parçalar.  Kirişler y boyunca
            #  ( arkadaki ağırlık ) ya da x boyunca ( yandaki ağırlık ).
            b_, yarim = KU["yan_yatak"]["b"], makine.MOTOR_PLAKASI_BOY / 2.0
            if KU.get("kiris_yonu") == "x":
                kutular = (
                    (p[0], p[1], p[2], p[1] + b_),
                    (p[0], p[3] - b_, p[2], p[3]),
                    (mx - yarim, p[1] + b_, mx + yarim, p[3] - b_),
                )
            else:
                kutular = (
                    (p[0], p[1], p[0] + b_, p[3]),
                    (p[2] - b_, p[1], p[2], p[3]),
                    (p[0] + b_, my - yarim, p[2] - b_, my + yarim),
                )
            for kutu in kutular:
                M["parcalar"].append((ad, kutu, p[4]))
            continue
        M["parcalar"].append((ad, p[:4], p[4]))


def _makine_parcalari(g, KU, zk, kapak):
    """Makinenin cisimleri ( makine.py ) kasnak merkezi zk kotunda;  dişlisizde
    üstteki kapak ( referans projenin makinesinde 47 mm ) klemens kutusu olarak."""
    p = makine.kaydir(KU["makine"], zk)
    if g["makine"]["tip"] == "Dişlisiz":
        p.append(makine.kutu(*kapak[:4], kapak[4], kapak[5], parca="klemens_kutusu"))
    return p


def _makine_dairesi(g, S, tavan, M):
    """Makine dairesindeki parçaların kotları;  hata listesi döner ( boşsa tamam ).

    TABLİYE ( makine_dairesi.tabliye ):  kuyunun üstünü kuyu döşemesi
    kalınlığında beton kapatır;  makine, bağlantılar ve regülatör onun üstüne
    oturur ( zd ).  Oda zemini ( zo ) tabliyenin üstünden "tabliye beton
    yüksekliği" kadar aşağıdadır — LiftDesigner'ın makine dairesi kesiti:
    zemin 30.670, tabliye 1.200 yüksek, döşemesi 120;  en üst durak 27.700 +
    son kat 4.050 = kuyu tavanı 31.750 = 30.670 + 1.200 − 120.  Eskiden tabliye
    kuyu tavanının üstünde 1.200 kalınlığında beton sanılıyor, oda zemini onun
    üstüne konuyordu ( kullanıcı 5 Eki ).  Bağlantılar ve regülatör kuyu
    üstündekiyle aynı ürünlerdir ( referans proje ölçüleri ).
    Makine hesap programının kaidesindedir ( bölüm 2 ):  dikine kirişler
    döşemeden şase yüksekliği kadar çıkar, yan yataklar üstleri hizasında;
    saptırma kasnağı gerekiyorsa yan yataklara asılır ( LiftDesigner ).
    """
    md = g.get("makine_dairesi") or {}
    hata = []
    for alan in ("yukseklik", "kapi_yukseklik"):
        if not (sayi_mi(md.get(alan)) and md[alan] > 0):
            hata.append(f"makine_dairesi.{alan}: sıfırdan büyük bir sayı olmalı ( {md.get(alan)!r} ).")
    if not (sayi_mi(md.get("tabliye_yuksekligi")) and md["tabliye_yuksekligi"] >= 0):
        hata.append(
            f"makine_dairesi.tabliye_yuksekligi: sıfır ya da pozitif bir sayı olmalı ( {md.get('tabliye_yuksekligi')!r} )."
        )
    if hata:
        return hata
    MD = makine_dairesi.yerlesim(g, S)
    #  Kaide makineye sığmıyorsa çerçeve hiç kurulmaz:  kurma hatası, dur.
    if "M" not in MD or MD.get("cerceve") is None:
        return hata + MD["hata"]
    hata.extend(MD["hata"])
    KU = MD["M"]
    d = MD["duzlem"]  # halat düzlemi ( kuyu_ustu.Duzlem )
    TB = makine_dairesi.tabliye(g)
    zd = tavan + TB["doseme"]  # tabliyenin üstü:  makine buraya oturur
    zo = zd - TB["yukseklik"]  # oda zemini
    ztv = zo + md["yukseklik"]  # oda tavanı
    gx0, gy0, gx1, gy1 = KU["govde"]
    #  Kasnağın düzlem boyundaki ortası, gövdenin düzleme dik ortası ( kanonik )
    ku0, _, ku1, _ = d.kanonik(KU["kasnak"])
    _, gv0, _, gv1 = d.kanonik(KU["govde"])
    mx, my = (ku0 + ku1) / 2.0, (gv0 + gv1) / 2.0
    kab = S["kabin_baglanti_alt"] - S["kabin_baglanti_ust"]
    rgeo = KU["reg_cizim"]["geo"]  # regülatör odanın döşemesinde ( ayakları )
    zs = zd + md["sase_yuksekligi"]  # makine hesap programının kaidesine oturur
    dis = g["makine"]["tip"] == "Dişli"
    zk = zs - makine.DISLI_ZARF["z"][0] if dis else zs + S["makine_en"] / 2.0  # kasnak merkezi
    kapak = d.kutu(
        mx - S["makine_kapak_en"] / 2.0,
        mx + S["makine_kapak_en"] / 2.0,
        my - S["makine_kapak_boy"] / 2.0,
        my + S["makine_kapak_boy"] / 2.0,
    ) + (zs + S["makine_en"], zs + S["makine_en"] + S["makine_kapak_yukseklik"])
    kaide_parcalari, sarim, yol, dusus_z = _kaide_ve_saptirma(MD, md, S, d, zd, zs, zk)
    M.update(
        {
            "makine": _makine_parcalari(g, KU, zk, kapak),
            "sase_parcalari": kaide_parcalari,
            "sarim_acisi": sarim,
            "agirlik_yolu": yol,
            "agirlik_dusus": MD["agirlik_dusus"] + (dusus_z,),
            "KU": KU,
            "MD": MD,
            "tabliye_ustu": zd,
            "oda_doseme": zo,
            "oda_tavan": ztv,
            "tabliye": TB,
            "cati": S["md_cati_kalinlik"],
            "sase": MD["cerceve"] + (zd, zs),
            "govde": (gx0, gy0, gx1, gy1, zs, zs + S["makine_en"]),
            "kapak": kapak,
            "kasnak": KU["kasnak"] + (zk,),
            #  1:1 askıda tepede halat bağlantısı yok ( halatlar kabinde ve ağırlıkta biter )
            "agirlik_baglanti": KU["agirlik_baglanti"] + (zd, zd + S["agirlik_baglanti_yukseklik"])
            if KU["agirlik_baglanti"]
            else None,
            "kabin_baglanti": KU["kabin_baglanti"] + (zd, zd + kab) if KU["kabin_baglanti"] else None,
            "regulator": KU["reg_govde"] + (zd, zd + rgeo["eksen"] + rgeo["tepe"]),
            "regulator_kasnak": KU["reg_kasnak"] + (zd + rgeo["eksen"],),
            #  Pano odaya sığmadıysa yok ( denetim hatası;  kurma sürer — hesabın
            #  ölçüleri için çizilmesi gerekmez ).
            #  Pano bulunduğu zeminde:  tabliyenin üstünde ya da oda zemininde
            "pano": MD["pano"] + (MD["pano_kotu"] + zo, MD["pano_kotu"] + zo + S["kumanda_pano_yukseklik"])
            if MD["pano"]
            else None,
            "regulator_x": KU["rgx"],
            "regulator_y": KU["rgy"],
        }
    )
    #  Kapının zemini:  izi tabliyedeyse tabliyenin üstü, değilse oda zemini
    #  ( kuyu_kesiti.yan_kesit'in çizdiği gibi )
    zkapi = zd if makine_dairesi.icinde(MD["kapi"], TB["izi"]) else zo
    return hata + _oda_yukseklikleri(
        md, TB, zd, ztv, M["kasnak"][4] + g["makine"]["tahrik_kasnak_capi"] / 2.0, zkapi
    )


def _kaide_ve_saptirma(MD, md, S, d, zd, zs, zk):
    """Makinenin kaidesinin parçaları ( zd:  tabliyenin üstü, zs:  şase üstü ).
    Halatın tahrik kasnağındaki sarım açısı ve ağırlık tarafının yolu:
    saptırma kasnağı varsa kasnaktan ona ( ortak teğet ), ondan dik iner.
    Saptırma kasnağının kotu ve teğet makine dairesi yerleşiminde ( döşemeden;
    plakadaki delik de oradan );  askı levhaları makine plakasına asılır.
    ( kaide parçaları, sarım açısı, ağırlık halatının yolu, iniş kotu )"""
    K = MD["kaide"]
    kaide_parcalari = makine.kaide(
        MD["cerceve"],
        zd,
        md["sase_yuksekligi"],
        K["E"],
        K["F"],
        K["uzun_x"],
        S,
        K["plaka"],
        MD["kaide_delikleri"],
    )
    sp = MD["saptirma"]
    if sp:
        zd_ = zd + sp["z"]
        kaide_parcalari += d.parcalar(
            makine.saptirma((sp["u"], d.v0, zd_), sp["D"], sp["bk"], zs, makine.MOTOR_PLAKASI_KALINLIK)
        )
        P1, P2 = (sp["P1"][0], sp["P1"][1] + zd), (sp["P2"][0], sp["P2"][1] + zd)
        sarim = sp["sarim"]
        yol = [(d.p(P1[0]) + (P1[1],), d.p(P2[0]) + (P2[1],))]
        dusus_z = zd_
    else:
        sarim, yol, dusus_z = 180.0, [], zk
    return kaide_parcalari, sarim, yol, dusus_z


def _oda_yukseklikleri(md, TB, zd, ztv, kasnak_ustu, zkapi):
    """Makine dairesinin temiz yüksekliği, tabliyenin ve tahrik kasnağının
    üstündeki boşluk, kapısının yüksekliği ( TS EN 81-20 m.5.2.6.3.2 · m.5.2.3.2 )
    ve kapının zemininden ( zkapi ) tavana sığması."""
    hata = []
    if md["yukseklik"] < ODA_YUKSEKLIK - 1e-9:
        hata.append(
            f"Makine dairesinin temiz yüksekliği {md['yukseklik']:g} mm < {ODA_YUKSEKLIK:g} mm ( TS EN 81-20 m.5.2.6.3.2.1 )."
        )
    elif ztv - zd < ODA_YUKSEKLIK - 1e-9:
        #  Makinenin başındaki çalışma alanı tabliyenin üstündedir
        hata.append(
            f"Tabliyenin üstünde temiz yükseklik {ztv - zd:g} mm < {ODA_YUKSEKLIK:g} mm:  "
            f"makinenin başındaki çalışma alanı tabliyededir ( TS EN 81-20 m.5.2.6.3.2.1 ) — "
            f"makine dairesi yüksekliği en az {ODA_YUKSEKLIK + TB['yukseklik']:g} olmalı ya da "
            f"tabliye alçalmalı."
        )
    if ztv - kasnak_ustu < DONEN_PARCA_USTU - 1e-9:
        hata.append(
            f"Tahrik kasnağının üstünde {ztv - kasnak_ustu:g} mm boşluk < {DONEN_PARCA_USTU:g} mm ( TS EN 81-20 m.5.2.6.3.2.3 )."
        )
    if md["kapi_yukseklik"] < ODA_KAPI_YUKSEKLIK - 1e-9:
        hata.append(
            f"Makine dairesi kapısı {md['kapi_yukseklik']:g} mm yüksek < {ODA_KAPI_YUKSEKLIK:g} mm ( TS EN 81-20 m.5.2.3.2 a )."
        )
    elif zkapi + md["kapi_yukseklik"] > ztv + 1e-9:
        #  21 Eki bulanık tarama:  tabliyedeki kapı ( 1.500 + 2.425 ) oda tavanını
        #  ( 3.700 ) aşıyor, kesitte çatının betonuna giriyordu
        hata.append(
            sorun.Sorun(
                f"Makine dairesi kapısı ( {md['kapi_yukseklik']:g} mm ) tavana sığmıyor:  kapının "
                f"durduğu zeminden ( {'tabliyenin üstünden' if zkapi > ztv - md['yukseklik'] + 1e-9 else 'oda zemininden'} ) "
                f"tavana {ztv - zkapi:g} mm var — kapıyı alçaltın ya da makine dairesini yükseltin.",
                ("oda_kapisi",),
                "kuyu_kesiti_yan",
                fark=(ztv - zkapi) - md["kapi_yukseklik"],
            )
        )
    return hata


#  Tavanın altındaki parçaların okunur adları ( hesabın bölüm 11'i basar )
TAVAN_PARCASI = {
    "sase": "makine şasesi",
    "kabin_baglanti": "kabin halat bağlantısı",
    "agirlik_baglanti": "ağırlık halat bağlantısı",
    "regulator": "regülatör",
    "kuyu tavanı": "kuyu tavanı",
}


def tavan_engeli(M, kutu):
    """`kutu`nun üstündeki en alçak tavan parçası:  ( kot, ad ).  Hiçbiri
    örtüşmüyorsa kuyu tavanının en alt kısmı ( kiriş )."""
    en = (M["tavan_alti"], "kuyu tavanı")
    for ad, p, z in M["parcalar"]:
        if ortusur(p, kutu) and z < en[0]:
            en = (z, ad)
    return en

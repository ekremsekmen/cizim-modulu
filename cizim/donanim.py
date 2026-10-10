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
from cizim import kuyu_dibi as CKD
from cizim import kuyu_ustu as CKT
from cizim import makine as CMK
from cizim import makine_dairesi as CMD
from cizim import parcalar as CP

MAKINE_YERLERI = ("Kuyu üstü", "Makine dairesi")
ODA_YUKSEKLIK = 2100.0      # m.5.2.6.3.2.1
DONEN_PARCA_USTU = 300.0    # m.5.2.6.3.2.3
ODA_KAPI_YUKSEKLIK = 2000.0 # m.5.2.3.2 a
#  Kabin önlüğü ( etek ) — m.5.4.5:  dik kısmı en az 0,75 m ( m.5.4.5.2 ), altında
#  pah ( m.5.4.5.1;  parcalar.ONLUK_PAH × ONLUK_PAH_DUSEY ).  Önlüğün EN ALT
#  noktası pahın ucudur:  kuyu dibi açıklığı ( m.5.2.5.8.2 a 1 ) oradan ölçülür
#  ( 7 Eki;  eskiden pah yoktu, dik kısmın altından ölçülüyordu — 35 mm iyimser ).
ETEK_BOYU = CP.ONLUK_DIK
ETEK_PAH_DUSEY = CP.ONLUK_PAH_DUSEY


def _sayi(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _ortusur(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def kabin_kotlari(dy, S, z, aski=None, tavanda=False):
    """Döşemesi z kotundaki kabinin parça kotları ( ofisin kabini — Sabitler ).

    ŞASE ( LiftDesigner'ın ön kesitleri ve referans proje — 8 Eki ):  PATENLER
    KİRİŞLERİN DIŞINDADIR.  Döşemenin sase_alt_derinlik altı şasenin altıdır
    ( tamponun çarptığı yer );  alt patenin merkezi onun alt_paten_payi üstünde
    ( referans projede altında );  alt kiriş alt patenin üstünden ( ya da şasenin
    altından ) sase_alt_kiris yükselir;  üst patenin merkezi alt patenden paten
    arası ( hesabın h'si:  patenlerin MERKEZLERİ arası — TS EN 81-50 kuvvet kolu )
    yukarıda;  üst kiriş üst patenin hemen altında, sase_ust_kiris yüksek.
    sase_ust:  üst kirişin üstü ( kasnaklar ve 1:1 bağlantısı oraya oturur ).
    Eskiden ( 30 Eyl – 8 Eki ) patenler kirişlerin yerindeydi, kiriş 10 mm'lik
    simgeydi:  LiftDesigner'ın kirişleri paten sanılmıştı.

    aski:  çizim girdisinin askı düzeni — kabin kasnaklarının kotu ona bağlı:
    kabin altında döşemenin kabin_kasnak_derinlik altında, kabin üstünde
    şasenin üst kirişinin üstünde ( alt uçları kabin_ustu_kasnak_boslugu kadar
    yukarıda ).  tavanda:  kabin üstü kasnaklar kabin tavanına oturur ( alt
    uçları kabin_tavani_kasnak_boslugu kadar yukarıda ) — arkadaki ağırlıkla
    2:1'in çapraz kasnakları ( arka_aski.arkada_iki_bir;  LiftDesigner
    12495-18 ve 1275 ).  Doğrudan ( 1:1 ) askıda halatlar üst kirişin üstündeki
    bağlantıya biter:  bağlantının tepesi, referans projenin kuyu tepesindeki
    kabin halat bağlantısı boyunda ( kabin_baglanti_alt − kabin_baglanti_ust )."""
    aski = aski or {}
    P = S["paten_yukseklik"]
    tavan = z + dy["kabin_ic_yukseklik"] + S["kabin_tavan_kalinlik"]
    sase_alt = z - S["sase_alt_derinlik"]
    alt_paten = sase_alt + S["alt_paten_payi"]              # alt patenin merkezi
    ust_paten = alt_paten + dy["kabin_paten_arasi"]         # üst patenin merkezi
    alt_kiris_alt = max(sase_alt, alt_paten + P / 2.0)
    sase_ust = ust_paten - P / 2.0                          # üst kirişin üstü
    if aski.get("duzen") == "Kabin üstü":
        kasnak_alti = (tavan + S["kabin_tavani_kasnak_boslugu"] if tavanda
                       else sase_ust + S["kabin_ustu_kasnak_boslugu"])
        kasnak_merkez = kasnak_alti + (aski.get("kasnak_capi") or 0) / 2.0
    else:
        kasnak_merkez = z - S["kabin_kasnak_derinlik"]
    return {"doseme": z, "taban_alti": z - S["kabin_taban_kalinlik"],
            "etek_dik_alti": z - ETEK_BOYU, "etek_alti": z - ETEK_BOYU - ETEK_PAH_DUSEY,
            "fren_alti": z - S["kabin_taban_kalinlik"]
            - S["fren_blogu_yukseklik"], "sase_alt": sase_alt, "sase_ust": sase_ust,
            "alt_kiris_alt": alt_kiris_alt, "alt_kiris_ust": alt_kiris_alt + S["sase_alt_kiris"],
            "ust_kiris_alt": sase_ust - S["sase_ust_kiris"], "ust_kiris_ust": sase_ust,
            "alt_paten": alt_paten - P / 2.0, "alt_paten_ust": alt_paten + P / 2.0,
            "ust_paten_alt": ust_paten - P / 2.0, "ust_paten": ust_paten + P / 2.0,
            "ic_ust": z + dy["kabin_ic_yukseklik"], "tavan": tavan,
            "kasnak_merkez": kasnak_merkez,
            "baglanti_ust": sase_ust + S["kabin_baglanti_alt"] - S["kabin_baglanti_ust"]}


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


def yerlesim(g, S, H, tavan, taban):
    """H:  en üst durağın kotu ( seyir ),  tavan:  kuyu tavanı ( döşeme altı ),
    taban:  kuyu tabanı.  Dönen sözlükte her parça ( plandaki kutu, z0, z1 )."""
    mk, dy = g.get("makine") or {}, g.get("dusey") or {}
    hata = []
    yeri = mk.get("yeri")
    if yeri not in MAKINE_YERLERI:
        hata.append(f"makine.yeri: {MAKINE_YERLERI} içinden olmalı ( {yeri!r} ).")
    for alan in ("kabin_konsol_arasi", "agirlik_konsol_arasi"):
        if not (_sayi(dy.get(alan)) and dy[alan] > 0):
            hata.append(f"dusey.{alan}: sıfırdan büyük bir sayı olmalı ( {dy.get(alan)!r} ).")
    if hata:
        return {"hata": hata}
    KD = CKD.yerlesim(g, S)
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
    ag = g["agirlik"]
    sol = ag["yeri"] == "Sol"
    kabin_raylari = sorted(KD["kabin_raylari"], key=lambda r: r[0])
    agirlik_raylari = KD["agirlik_raylari"]
    tavan_alti = tavan - S["tavan_kirisi"]
    M = {"mrl": mrl, "KD": KD, "hata": hata, "tavan": tavan, "tavan_alti": tavan_alti,
         "parcalar": []}

    if mrl:
        KU = CKT.yerlesim(g, S, acil_pano=False)
        if "kasnak" not in KU:
            return {"hata": hata + KU["hata"]}
        hata.extend(KU["hata"])
        M["KU"] = KU
        G = g["kuyu"]["genislik"]
        #  ── MAKİNE ŞASESİ ve MAKİNE ────────────────────────────────────
        yakin_ray = kabin_raylari[0] if sol else kabin_raylari[-1]
        uzak_ray = kabin_raylari[-1] if sol else kabin_raylari[0]
        #  Duvardan duvara kirişte makine kirişlerin üstünde, tavana yakın
        #  ( 12495-18 );  raylara oturan makinede tavanın 250 altında.
        z_ust = tavan - (S["duvar_kirisi_tepe_boslugu"] if KU.get("duvardan_duvara")
                         else S["makine_tepe_boslugu"])
        zs = z_ust - S["makine_kapak_yukseklik"] - S["makine_en"]      # şase üstü
        sase = KU["sase"] + (zs - KU["yan_yatak"]["h"], zs)            # plandaki yeri kuyu_ustu'dan
        kx0, ky0, kx1, ky1 = KU["kasnak"]
        gx0, gy0, gx1, gy1 = KU["govde"]
        mx, my = (kx0 + kx1) / 2.0, (gy0 + gy1) / 2.0
        zk = zs + S["makine_en"] / 2.0                                  # kasnak merkezi
        kapak = (mx - S["makine_kapak_en"] / 2.0, my - S["makine_kapak_boy"] / 2.0,
                 mx + S["makine_kapak_en"] / 2.0, my + S["makine_kapak_boy"] / 2.0,
                 zs + S["makine_en"], z_ust)
        M.update({
            "makine": _makine_parcalari(g, KU, zk, kapak),
            "sase_parcalari": CMK.upn_sase(sase, my, KU["yan_yatak"], KU["sase_delikleri"]),
            "sase": sase,
            "govde": (gx0, gy0, gx1, gy1, zs, zs + S["makine_en"]),
            "kapak": kapak,
            "kasnak": KU["kasnak"] + (zk,),                            # + merkez kotu
            "agirlik_baglanti": KU["agirlik_baglanti"] + (zs, zs + S["agirlik_baglanti_yukseklik"]),
            "kabin_baglanti": KU["kabin_baglanti"] + (tavan - S["kabin_baglanti_alt"],
                                                      tavan - S["kabin_baglanti_ust"]),
            "regulator": KU["reg_govde"] + (tavan - S["regulator_govde_alt"],
                                            tavan - S["regulator_govde_ust"]),
            "regulator_kasnak": KU["reg_kasnak"] + (tavan - S["regulator_kasnak_merkez"],),
        })
        M["halat_konsolu"] = CMK.kaydir(KU["halat_konsolu"],
                                         (M["kabin_baglanti"][4] + M["kabin_baglanti"][5]) / 2)
        #  Tavanın altındaki parçalar:  sığınma ve açıklıklar bunlara da ölçülür
        #  ( m.5.2.5.7.2:  "kuyu tavanının en alt kısımları — kirişler ve
        #  tavanın altına yerleştirilmiş parçalar dahil" ).
        for ad in ("sase", "kabin_baglanti", "agirlik_baglanti", "regulator"):
            p = M[ad]
            if ad == "sase" and KU.get("duvardan_duvara"):
                #  Duvardan duvara iki kiriş kabinin üstünden geçer:  aralarındaki
                #  boşluk engel değil ( çapraz kasnaklar oradan yükselir ) —
                #  kirişler ve motor plakası ayrı parçalar.
                b_ = KU["yan_yatak"]["b"]
                for kutu in ((p[0], p[1], p[0] + b_, p[3]), (p[2] - b_, p[1], p[2], p[3]),
                             (p[0] + b_, my - CMK.MOTOR_PLAKASI_BOY / 2.0,
                              p[2] - b_, my + CMK.MOTOR_PLAKASI_BOY / 2.0)):
                    M["parcalar"].append((ad, kutu, p[4]))
                continue
            M["parcalar"].append((ad, p[:4], p[4]))
        #  Öbür kabin rayı referans projede tavanın 50 altına çıkar;  tavanın en alt
        #  kısmı ( tavan_kirisi payı ) hesaba katılınca onun 50 altına — eskiden
        #  payın alt yüzüne tam değiyordu.
        ray_ust = {"yakin": zs - S["ray_sase_icinde"],
                   "uzak": tavan_alti - S["kabin_rayi_tepe"],
                   "agirlik": zs - S["ray_sase_icinde"]}
        if KU.get("duvardan_duvara"):
            #  Makine raylara oturmaz ( duvardan duvara kirişler ):  raylar
            #  kirişlerin altında biter ( kiriş kuyunun derinliğince uzanır ).
            alt_ = zs - KU["yan_yatak"]["h"] - S["kabin_rayi_tepe"]
            ray_ust = {"yakin": alt_, "uzak": alt_, "agirlik": alt_}
        M["raylar"] = [("kabin", yakin_ray, ray_ust["yakin"]),
                       ("kabin", uzak_ray, ray_ust["uzak"])] + \
                      [("agirlik", r, ray_ust["agirlik"]) for r in agirlik_raylari]
        M["regulator_x"], M["regulator_y"] = KU["rgx"], KU["rgy"]
    else:
        ray_ust = tavan_alti - S["kabin_rayi_tepe"]
        M["raylar"] = [("kabin", r, ray_ust) for r in kabin_raylari] + \
                      [("agirlik", r, ray_ust) for r in agirlik_raylari]
        rg = KD["gergi"]
        M["regulator_x"] = (rg[0] + rg[2]) / 2.0
        M["regulator_y"] = (rg[1] + rg[3]) / 2.0
        oda = _makine_dairesi(g, S, tavan, M)
        if "kasnak" not in M:
            return {"hata": hata + oda}
        hata.extend(oda)

    #  ── GERGİ DÜZENİ ( kuyu dibi ) ──────────────────────────────────────
    kd = g["kuyu_dibi"]
    gp = KD["gergi_donanim"]
    kol = (gp["kol"][1], gp["kol"][3])
    agr = (gp["agirlik"][1], gp["agirlik"][3])
    M["gergi"] = {"merkez": taban + S["gergi_kasnak_merkez"], "cap": kd["regulator_kasnak_capi"],
                  "kol": (kol[0], kol[1], taban + S["gergi_kol_alt"],
                          taban + S["gergi_kol_alt"] + S["gergi_kol_yukseklik"]),
                  "agirlik": (agr[0], agr[1], taban + S["gergi_agirlik_alt"],
                              taban + S["gergi_agirlik_alt"] + S["gergi_agirlik_yukseklik"]),
                  "plan": KD["gergi"]}
    #  ── RAYLAR:  konsollar ve ekler ─────────────────────────────────────
    raylar = []
    for tur, kutu, ust in M["raylar"]:
        aralik = dy["kabin_konsol_arasi"] if tur == "kabin" else dy["agirlik_konsol_arasi"]
        raylar.append({"tur": tur, "kutu": kutu, "alt": taban, "ust": ust,
                       "konsollar": konsol_kotlari(taban, ust, aralik, S),
                       "ekler": ek_kotlari(taban, ust, S)})
    M["raylar"] = raylar

    #  ── KARŞI AĞIRLIK ────────────────────────────────────────────────────
    #  Çerçevenin yüksekliği hesabın ağırlık paten arasıdır ( kabin şasesi gibi )
    M["agirlik"] = {"kutu": KD["blok"], "yukseklik": dy["agirlik_paten_arasi"],
                    "kasnak_ust": S["agirlik_kasnak_ust"], "paten": S["paten_yukseklik"],
                    "paten_arasi": dy["agirlik_paten_arasi"],
                    "tampon_ustu": taban + dy["agirlik_tampon_baba"] + dy["agirlik_tampon_boyu"]}
    return M


def _makine_parcalari(g, KU, zk, kapak):
    """Makinenin cisimleri ( makine.py ) kasnak merkezi zk kotunda;  dişlisizde
    üstteki kapak ( referans projenin makinesinde 47 mm ) klemens kutusu olarak."""
    p = CMK.kaydir(KU["makine"], zk)
    if g["makine"]["tip"] == "Dişlisiz":
        p.append(CMK.kutu(*kapak[:4], kapak[4], kapak[5], parca="klemens_kutusu"))
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
        if not (_sayi(md.get(alan)) and md[alan] > 0):
            hata.append(f"makine_dairesi.{alan}: sıfırdan büyük bir sayı olmalı ( {md.get(alan)!r} ).")
    if not (_sayi(md.get("tabliye_yuksekligi")) and md["tabliye_yuksekligi"] >= 0):
        hata.append(f"makine_dairesi.tabliye_yuksekligi: sıfır ya da pozitif bir sayı olmalı "
                    f"( {md.get('tabliye_yuksekligi')!r} ).")
    if hata:
        return hata
    MD = CMD.yerlesim(g, S)
    #  Kaide makineye sığmıyorsa çerçeve hiç kurulmaz:  kurma hatası, dur.
    if "M" not in MD or MD.get("cerceve") is None:
        return hata + MD["hata"]
    hata.extend(MD["hata"])
    KU = MD["M"]
    d = MD["duzlem"]                            # halat düzlemi ( kuyu_ustu.Duzlem )
    TB = CMD.tabliye(g)
    zd = tavan + TB["doseme"]                   # tabliyenin üstü:  makine buraya oturur
    zo = zd - TB["yukseklik"]                   # oda zemini
    ztv = zo + md["yukseklik"]                  # oda tavanı
    gx0, gy0, gx1, gy1 = KU["govde"]
    #  Kasnağın düzlem boyundaki ortası, gövdenin düzleme dik ortası ( kanonik )
    ku0, _, ku1, _ = d.kanonik(KU["kasnak"])
    _, gv0, _, gv1 = d.kanonik(KU["govde"])
    mx, my = (ku0 + ku1) / 2.0, (gv0 + gv1) / 2.0
    kab = S["kabin_baglanti_alt"] - S["kabin_baglanti_ust"]
    rg = S["regulator_govde_alt"] - S["regulator_govde_ust"]
    #  Makinenin oturduğu yer:  hesap programının kaidesi
    K = MD["kaide"]
    zs = zd + md["sase_yuksekligi"]
    sase = MD["cerceve"] + (zd, zs)
    parcalar = CMK.kaide(MD["cerceve"], zd, md["sase_yuksekligi"], K["E"], K["F"], K["uzun_x"], S,
                         K["plaka"], MD["kaide_delikleri"])
    dis = g["makine"]["tip"] == "Dişli"
    zk = zs - CMK.DISLI_ZARF["z"][0] if dis else zs + S["makine_en"] / 2.0     # kasnak merkezi
    kapak = d.kutu(mx - S["makine_kapak_en"] / 2.0, mx + S["makine_kapak_en"] / 2.0,
                   my - S["makine_kapak_boy"] / 2.0, my + S["makine_kapak_boy"] / 2.0) + \
        (zs + S["makine_en"], zs + S["makine_en"] + S["makine_kapak_yukseklik"])
    #  Halatın tahrik kasnağındaki sarım açısı ve ağırlık tarafının yolu:
    #  saptırma kasnağı varsa kasnaktan ona ( ortak teğet ), ondan dik iner.
    #  Saptırma kasnağının kotu ve teğet makine dairesi yerleşiminde ( döşemeden;
    #  plakadaki delik de oradan );  askı levhaları makine plakasına asılır.
    sp = MD["saptirma"]
    if sp:
        zd_ = zd + sp["z"]
        parcalar += d.parcalar(CMK.saptirma((sp["u"], d.v0, zd_), sp["D"], sp["bk"], zs,
                                            CMK.MOTOR_PLAKASI_KALINLIK))
        P1, P2 = (sp["P1"][0], sp["P1"][1] + zd), (sp["P2"][0], sp["P2"][1] + zd)
        sarim = sp["sarim"]
        yol = [(d.p(P1[0]) + (P1[1],), d.p(P2[0]) + (P2[1],))]
        dusus_z = zd_
    else:
        sarim, yol, dusus_z = 180.0, [], zk
    M.update({
        "makine": _makine_parcalari(g, KU, zk, kapak),
        "sase_parcalari": parcalar,
        "sarim_acisi": sarim, "agirlik_yolu": yol,
        "agirlik_dusus": MD["agirlik_dusus"] + (dusus_z,),
        "KU": KU, "MD": MD, "tabliye_ustu": zd, "oda_doseme": zo, "oda_tavan": ztv,
        "tabliye": TB, "cati": S["md_cati_kalinlik"],
        "sase": sase,
        "govde": (gx0, gy0, gx1, gy1, zs, zs + S["makine_en"]),
        "kapak": kapak,
        "kasnak": KU["kasnak"] + (zk,),
        #  1:1 askıda tepede halat bağlantısı yok ( halatlar kabinde ve ağırlıkta biter )
        "agirlik_baglanti": KU["agirlik_baglanti"] + (zd, zd + S["agirlik_baglanti_yukseklik"])
        if KU["agirlik_baglanti"] else None,
        "kabin_baglanti": KU["kabin_baglanti"] + (zd, zd + kab) if KU["kabin_baglanti"] else None,
        "regulator": KU["reg_govde"] + (zd, zd + rg),
        "regulator_kasnak": KU["reg_kasnak"] + (zd + S["regulator_govde_alt"]
                                                - S["regulator_kasnak_merkez"],),
        #  Pano odaya sığmadıysa yok ( denetim hatası;  kurma sürer — hesabın
        #  ölçüleri için çizilmesi gerekmez ).
        #  Pano bulunduğu zeminde:  tabliyenin üstünde ya da oda zemininde
        "pano": MD["pano"] + (MD["pano_kotu"] + zo, MD["pano_kotu"] + zo + S["kumanda_pano_yukseklik"])
        if MD["pano"] else None,
        "regulator_x": KU["rgx"], "regulator_y": KU["rgy"],
    })
    kasnak_ustu = M["kasnak"][4] + g["makine"]["tahrik_kasnak_capi"] / 2.0
    if md["yukseklik"] < ODA_YUKSEKLIK - 1e-9:
        hata.append(f"Makine dairesinin temiz yüksekliği {md['yukseklik']:g} mm < "
                    f"{ODA_YUKSEKLIK:g} mm ( TS EN 81-20 m.5.2.6.3.2.1 ).")
    elif ztv - zd < ODA_YUKSEKLIK - 1e-9:
        #  Makinenin başındaki çalışma alanı tabliyenin üstündedir
        hata.append(f"Tabliyenin üstünde temiz yükseklik {ztv - zd:g} mm < {ODA_YUKSEKLIK:g} mm:  "
                    f"makinenin başındaki çalışma alanı tabliyededir ( TS EN 81-20 m.5.2.6.3.2.1 ) — "
                    f"makine dairesi yüksekliği en az {ODA_YUKSEKLIK + TB['yukseklik']:g} olmalı ya da "
                    f"tabliye alçalmalı.")
    if ztv - kasnak_ustu < DONEN_PARCA_USTU - 1e-9:
        hata.append(f"Tahrik kasnağının üstünde {ztv - kasnak_ustu:g} mm boşluk < "
                    f"{DONEN_PARCA_USTU:g} mm ( TS EN 81-20 m.5.2.6.3.2.3 ).")
    if md["kapi_yukseklik"] < ODA_KAPI_YUKSEKLIK - 1e-9:
        hata.append(f"Makine dairesi kapısı {md['kapi_yukseklik']:g} mm yüksek < "
                    f"{ODA_KAPI_YUKSEKLIK:g} mm ( TS EN 81-20 m.5.2.3.2 a ).")
    return hata


def agirlik_kotlari(M, alt):
    """Alt kirişi `alt` kotundaki karşı ağırlığın parça kotları.  PATENLER
    ÇERÇEVENİN DIŞINDADIR ( üstte ve altta — LiftDesigner 1022'nin kesiti:
    2.000'lik çerçeve, 100'lük patenler;  kabin şasesindeki gibi ):  merkezleri
    arası hesabın paten arası, çerçeve ondan bir paten boyu kısa.  8 Eki'ye dek
    patenler çerçevenin uçlarına ortalıydı ( çerçeve = paten arası );  daha
    önce çerçevenin ortasına göre 1.500 aralıkla diziliyorlardı."""
    A = M["agirlik"]
    ust = alt + A["yukseklik"] - A["paten"]
    return {"alt": alt, "ust": ust, "kasnak_merkez": ust - A["kasnak_ust"],
            "alt_paten": alt - A["paten"], "alt_paten_ust": alt,
            "ust_paten_alt": ust, "ust_paten": ust + A["paten"]}


def agirlik_dolgu_kotlari(g, S, AK):
    """Karşı ağırlık dolgusunun alt ve üst kotu:  alt kirişin üstünden üst
    kirişin altına;  2:1'de ağırlık kasnağının altına kadar ( karar 11 ).
    Kesit ve hesabın dolgu yüksekliği ( olculer ) bunu kullanır — kesit
    eskiden dolguyu kasnağın içine kadar çiziyordu ( 2:1'de 300 mm )."""
    alt, ust = AK["alt"] + S["agirlik_kiris"], AK["ust"] - S["agirlik_kiris"]
    cap = (g.get("agirlik") or {}).get("kasnak_capi")
    if (g.get("aski") or {}).get("duzen") != "Doğrudan" and _sayi(cap):
        ust = min(ust, AK["kasnak_merkez"] - cap / 2.0)
    return alt, ust


#  Tavanın altındaki parçaların okunur adları ( hesabın bölüm 11'i basar )
TAVAN_PARCASI = {"sase": "makine şasesi", "kabin_baglanti": "kabin halat bağlantısı",
                 "agirlik_baglanti": "ağırlık halat bağlantısı", "regulator": "regülatör",
                 "kuyu tavanı": "kuyu tavanı"}


def tavan_engeli(M, kutu):
    """`kutu`nun üstündeki en alçak tavan parçası:  ( kot, ad ).  Hiçbiri
    örtüşmüyorsa kuyu tavanının en alt kısmı ( kiriş )."""
    en = (M["tavan_alti"], "kuyu tavanı")
    for ad, p, z in M["parcalar"]:
        if _ortusur(p, kutu) and z < en[0]:
            en = (z, ad)
    return en

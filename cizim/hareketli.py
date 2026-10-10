# -*- coding: utf-8 -*-
"""
HAREKETLİ PARÇALAR — kabin ve karşı ağırlığın parçaları TEK TANIMDAN

Her parça:  ( ad, plandaki kutu ( x0, y0, x1, y1 ), alt kot, üst kot ).
Plandaki yer kuyu planının elemanlarından ( geometri.plan ), kotlar parçanın
o konumdaki kot sözlüğünden ( donanim.kabin_kotlari / agirlik_kotlari ) gelir:
aynı fonksiyon kabinin her konumu için çağrılır.

Sığınma alanlarının yeri ( kuyu_dibi, kabin_ustu ), açıklıklar ve çarpışma
denetimleri ( dusey ) parçaları BURADAN okur.  Eskiden her denetim kendi
listesini tutuyordu:  kuyu dibinde yalnız kabin altı kasnakları, kabin
üstünde yalnız kasnak kutuları sayılıyor;  alt şase kirişi kuyu dibindeki
sığınma alanının üstünden, çapraz kasnaklar arasındaki halat kabin üstündeki
alanın içinden geçtiği hâlde proje UYGUN çıkıyordu ( denetim 9–10 Eki ).
Yeni bir parça buraya eklenince bütün denetimlere girer.

Şasenin kirişleri, dikmeleri ve patenleri planda ayrı elemanlardır ( alt ve
üst kiriş aynı izde, kotları ayrı ).  Fren bloğu alt patenin izinde, alt
patenle platformun altı arasında ( kesit_parcalari'nın çizdiği gibi ).
Kabin eteği ( önlük ) burada yok:  eşiğin önündedir, kabinin izinin dışında;
kendi açıklığı ( m.5.2.5.8.2 a 1 ) ayrı denetlenir.
"""

from temel import eleman_kutusu, ortusur

#  Kabin parçalarının adları — açıklık ve hata iletilerinde görünür
KABIN = "kabin tabanı"
ALT_KIRIS = "alt şase kirişi"
UST_KIRIS = "üst şase kirişi"
DIKME = "şase dikmesi"
ALT_PATEN = "alt paten"
UST_PATEN = "üst paten"
FREN = "fren bloğu"
KASNAK = "kabin kasnağı"
HALAT = "kasnaklar arasındaki halat"
BAGLANTI = "kabindeki halat bağlantısı"

#  Rayın 0,15 m yakınındaki parçalar:  m.5.2.5.8.2 a 2 ( Şekil 7 ) ayrı ölçülür,
#  "kabinin en alt kısmı" ( a ) onları saymaz.
RAYA_YAKIN = frozenset((DIKME, ALT_PATEN, UST_PATEN, FREN))

#  Çapraz halatın plandaki şeridi bu boyda dikdörtgenlere bölünür ( sığınma
#  alanı yerleşimi dikdörtgenlerle çalışır;  şeridi çevreleyen tek kutu
#  bütün tavanı kapatırdı ).
HALAT_ADIMI = 50.0

#  Karşı ağırlık parçalarının adları
AG_CERCEVE = "karşı ağırlık çerçevesi"
AG_ALT_PATEN = "karşı ağırlığın alt pateni"
AG_UST_PATEN = "karşı ağırlığın üst pateni"
AG_KASNAK = "karşı ağırlık kasnağı"


def _serit(p, q, en):
    """p–q doğru parçasını saran `en` genişliğindeki şerit:  HALAT_ADIMI
    boyunda dilimlerin çevreleyen kutuları."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    boy = (dx * dx + dy * dy) ** 0.5
    if boy < 1e-9:
        return [(p[0] - en / 2.0, p[1] - en / 2.0, p[0] + en / 2.0, p[1] + en / 2.0)]
    nx, ny = -dy / boy * en / 2.0, dx / boy * en / 2.0
    adet = max(1, int(boy / HALAT_ADIMI + 0.999999))
    out = []
    for i in range(adet):
        a = (p[0] + dx * i / adet, p[1] + dy * i / adet)
        b = (p[0] + dx * (i + 1) / adet, p[1] + dy * (i + 1) / adet)
        xs = (a[0] + nx, a[0] - nx, b[0] + nx, b[0] - nx)
        ys = (a[1] + ny, a[1] - ny, b[1] + ny, b[1] - ny)
        out.append((min(xs), min(ys), max(xs), max(ys)))
    return out


def kabin_parcalari(g, S, plan, kt):
    """Kabinin parçaları — `plan`:  kuyu planının elemanları, `kt`:  kabinin o
    konumdaki kotları ( donanim.kabin_kotlari ).  Kabin altı ve kabin üstü
    askıda kasnaklar ve aralarındaki halat ( kasnakların alt teğetinde ),
    çapraz düzende ( arkadaki ağırlıkla 2:1 ) döndürülmüş kasnakların kutuları
    ve aralarındaki çapraz halat şeridi, doğrudan ( 1:1 ) askıda üst kirişin
    üstündeki halat bağlantısı."""
    from cizim import arka_aski as CAA

    out = []
    kabin = next((eleman_kutusu(el) for el in plan if el.get("ad") == "kabin_dis"), None)
    if kabin is not None:
        out.append((KABIN, kabin, kt["taban_alti"], kt["tavan"]))
    for el in plan:
        ad = el.get("ad")
        if ad == "sase_kiris":
            k = eleman_kutusu(el)
            out.append((ALT_KIRIS, k, kt["alt_kiris_alt"], kt["alt_kiris_ust"]))
            out.append((UST_KIRIS, k, kt["ust_kiris_alt"], kt["ust_kiris_ust"]))
        elif ad == "sase_dikme":
            out.append((DIKME, eleman_kutusu(el), kt["alt_kiris_alt"], kt["ust_kiris_ust"]))
        elif el["katman"] == "PATEN" and el["tip"] == "dikdortgen" and ad != "agirlik_pateni":
            k = eleman_kutusu(el)
            out.append((ALT_PATEN, k, kt["alt_paten"], kt["alt_paten_ust"]))
            out.append((UST_PATEN, k, kt["ust_paten_alt"], kt["ust_paten"]))
            out.append((FREN, k, kt["fren_alti"], kt["taban_alti"]))
    aski = g.get("aski") or {}
    duzen = aski.get("duzen")
    halat = aski.get("halat_capi") or 0.0
    if duzen in ("Kabin altı", "Kabin üstü"):
        zc = kt["kasnak_merkez"]
        if CAA.arkada_iki_bir(g):
            A = CAA.geometri(g, S)
            if "kutular" in A:
                Rk = A["Rk"]
                for k in A["kutular"]:
                    out.append((KASNAK, k, zc - Rk, zc + Rk))
                p, q = A["kasnaklar"]
                for k in _serit(p, q, S["kabin_kasnak_genislik"]):
                    out.append((HALAT, k, zc - Rk, zc - Rk + halat))
        else:
            R = (aski.get("kasnak_capi") or 0.0) / 2.0
            kasnak = [eleman_kutusu(el) for el in plan if el.get("ad") == "kabin_kasnak"]
            for k in kasnak:
                out.append((KASNAK, k, zc - R, zc + R))
            if len(kasnak) >= 2:
                k = (
                    min(k[0] for k in kasnak),
                    min(k[1] for k in kasnak),
                    max(k[2] for k in kasnak),
                    max(k[3] for k in kasnak),
                )
                out.append((HALAT, k, zc - R, zc - R + halat))
    elif duzen == "Doğrudan":
        for el in plan:
            if el.get("ad") == "aski_nokta" and el["tip"] == "daire":
                out.append(
                    (
                        BAGLANTI,
                        (el["x"] - 70, el["y"] - 70, el["x"] + 70, el["y"] + 70),
                        kt["sase_ust"],
                        kt["baglanti_ust"],
                    )
                )
    return out


def agirlik_parcalari(g, S, plan, AK):
    """Karşı ağırlığın parçaları — `AK`:  ağırlığın o konumdaki kotları
    ( donanim.agirlik_kotlari ).  Patenler çerçevenin altında ve üstünde,
    2:1'de kasnak çerçevenin içinde ( merkezi üst kirişin kasnak_ust altında )
    — tepesi üst patenin de üstüne çıkabilir."""
    out = []
    for el in plan:
        ad = el.get("ad")
        if ad == "agirlik_blok":
            out.append((AG_CERCEVE, eleman_kutusu(el), AK["alt"], AK["ust"]))
        elif ad == "agirlik_pateni":
            k = eleman_kutusu(el)
            out.append((AG_ALT_PATEN, k, AK["alt_paten"], AK["alt_paten_ust"]))
            out.append((AG_UST_PATEN, k, AK["ust_paten_alt"], AK["ust_paten"]))
        elif ad == "agirlik_kasnak":
            R = ((g.get("agirlik") or {}).get("kasnak_capi") or 0.0) / 2.0
            out.append((AG_KASNAK, eleman_kutusu(el), AK["kasnak_merkez"] - R, AK["kasnak_merkez"] + R))
    return out


def ustundeki_en_alt(parcalar, kutu, varsayilan=None):
    """`kutu`nun üstündeki ( planda örtüşen ) en alçak parça:  ( alt kot, ad ).
    Hiçbiri örtüşmüyorsa `varsayilan`."""
    return min(((p[2], p[0]) for p in parcalar if ortusur(p[1], kutu)), default=varsayilan)

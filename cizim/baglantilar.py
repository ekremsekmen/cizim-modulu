"""Ölçülendirilmemiş bağlantı yolları (imalat profili veya dayanım hesabı değildir).

Taşıyıcı ürünün kesiti/yatağı/cıvatası verilmediğinde yalnız bağlanan
noktalar gösterilir. Plan ve kesit aynı üç boyutlu çizgilerden üretilir.
"""

from cizim import makine


def kasnak_tasiyicilari(g, S, z):
    if g["aski"]["duzen"] != "Kabin altı":
        return []
    kb, kr, a = g["kabin"], g["kabin_ray"], g["aski"]
    kx = g["kuyu"]["genislik"] / 2.0 + kb["kaciklik_y"]
    ky = kb["on_pay"] + (kb["derinlik"] + S["kabin_pano_arka"]) / 2 + a.get("kasnak_kaciklik", 0)
    ry = kr["kapi_arasi"]
    yon = 1 if ry >= ky else -1
    yz = ky + yon * S["kabin_kasnak_genislik"] / 2
    yol = []
    #  Şase dikmesinin sırtının ortası ( geometri.plan:  sırt patenin arkasında,
    #  dil ucundan paten_en / 2 … sase_dikme )
    sirt = kr["arasi"] / 2 - (S["paten_en"] / 2 + S["sase_dikme"]) / 2
    for yan in (-1, 1):
        x = kx + yan * a["kasnak_arasi"] / 2
        sx = kx + yan * sirt
        noktalar = ((x, ky, z), (x, yz, z), (sx, yz, z), (sx, ry, z))
        yol += [
            makine.cizgi(p0, p1, "SASE", "kasnak_tasiyici_sematik", "baglanti_yolu")
            for p0, p1 in zip(noktalar, noktalar[1:])
            if p0 != p1
        ]
    return yol


def agirlik_patenleri(g, S, blok, raylar, z0, z1):
    """Karşı ağırlığın patenleri:  her ağırlık rayının ağırlığa bakan yüzünü
    kavrar ( kabin patenleri gibi — geometri.plan ).  Ağırlık yandaysa raylar
    önünde ve arkasındadır ( y ), arkadaysa iki yanındadır ( x ).  Eskiden
    paten her düzende çerçevenin önüne / arkasına konuyordu:  arkadaki
    ağırlıkta raydan uzakta, çerçevenin arka yüzünde duruyordu."""
    arka = g["agirlik"]["yeri"] == "Arka"
    cx, cy = (blok[0] + blok[2]) / 2, (blok[1] + blok[3]) / 2
    en, boy = S["paten_en"] / 2, S["paten_boy"] / 2
    out = []
    for r in raylar:
        k = r["kutu"]
        rx, ry = (k[0] + k[2]) / 2, (k[1] + k[3]) / 2
        if arka:
            x = k[2] if rx < cx else k[0]
            pk = (x - en, ry - boy, x + en, ry + boy)
        else:
            y = k[3] if ry < cy else k[1]
            pk = (rx - boy, y - en, rx + boy, y + en)
        out.append(makine.kutu(*pk, z0, z1, "PATEN", "agirlik_paten"))
    return out


def halat_konsolu(baglanti, ray, z):
    bx, by = (baglanti[0] + baglanti[2]) / 2, (baglanti[1] + baglanti[3]) / 2
    rx, ry = (ray[0] + ray[2]) / 2, (ray[1] + ray[3]) / 2
    noktalar = ((bx, by, z), (rx, by, z), (rx, ry, z))
    return [
        makine.cizgi(p0, p1, "BAGLANTI", "halat_konsolu_sematik", "baglanti_yolu")
        for p0, p1 in zip(noktalar, noktalar[1:])
        if p0 != p1
    ]

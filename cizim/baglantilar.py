"""Ölçülendirilmemiş bağlantı yolları (imalat profili veya dayanım hesabı değildir).

Taşıyıcı ürünün kesiti/yatağı/cıvatası verilmediğinde yalnız bağlanan
noktalar gösterilir. Plan ve kesit aynı üç boyutlu çizgilerden üretilir.
"""
from cizim import makine as CMK


def kasnak_tasiyicilari(g, S, z):
    if g['aski']['duzen'] != 'Kabin altı':
        return []
    kb, kr, a = g['kabin'], g['kabin_ray'], g['aski']
    kx = g['kuyu']['genislik'] / 2.0 + kb['kaciklik_y']
    ky = kb['on_pay'] + (kb['derinlik'] + S['kabin_pano_arka']) / 2 + a.get('kasnak_kaciklik', 0)
    ry = kr['kapi_arasi']
    yon = 1 if ry >= ky else -1
    yz = ky + yon * S['kabin_kasnak_genislik'] / 2
    yol = []
    for yan in (-1, 1):
        x = kx + yan * a['kasnak_arasi'] / 2
        sx = kx + yan * (kb['genislik'] / 2 + S['kabin_pano_yan'] + S['sase_dikme'] / 2)
        noktalar = ((x, ky, z), (x, yz, z), (sx, yz, z), (sx, ry, z))
        yol += [CMK.cizgi(p0, p1, 'SASE', 'kasnak_tasiyici_sematik', 'baglanti_yolu')
                for p0, p1 in zip(noktalar, noktalar[1:]) if p0 != p1]
    return yol


def halat_konsolu(baglanti, ray, z):
    bx, by = (baglanti[0] + baglanti[2]) / 2, (baglanti[1] + baglanti[3]) / 2
    rx, ry = (ray[0] + ray[2]) / 2, (ray[1] + ray[3]) / 2
    noktalar = ((bx, by, z), (rx, by, z), (rx, ry, z))
    return [CMK.cizgi(p0, p1, 'BAGLANTI', 'halat_konsolu_sematik', 'baglanti_yolu')
            for p0, p1 in zip(noktalar, noktalar[1:]) if p0 != p1]

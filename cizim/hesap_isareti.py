# -*- coding: utf-8 -*-
"""
HESABIN UYGUN BULMADIĞI BÖLÜMLER ÇİZİMDE ( 1 Kas )

Hesap bir bölümü "UYGUN DEĞİLDİR" bulduğunda ( tampon hıza uygun değil, karşı
ağırlık dolgusu çerçeveye sığmıyor … ) çizim yine kuruluyordu ve paftada hiçbir
iz kalmıyordu:  çizimi tek başına gören ( şantiye, kontrol mühendisi ) sorunu
göremezdi ( 30 Eki taraması:  589 çizilen düzenin 205'inde dolgu sığmıyor,
69'unda tampon hıza uygun değil ).  Kullanıcı kararı:

  · ekranda bölümün parçaları hep turuncu;  Uygunluk panelinde bölüme
    tıklanınca vurgulanır ( geometri sorunlarının kırmızısından ayrı )
  · teslim paftalarında her çizimin künyesinin altında not ( parçalar
    paftada boyanmaz — teknik resim temiz kalır )
  · paket ayrıca onayla iner ( on-yuz Teslim )

Bölümün parçaları çizimdeki ADLARIYLA ( cizim/parca_adlari.py ) — ekran
SVG'nin data-ad'ını işaretler.  Parçası çizimde olmayan bölüm ( kabin alanı
değil;  aydınlatma, gerilim düşümü, kurulu güç ) yalnız notta söylenir.
"""

from cizim import parca_adlari

#  Bölümün ( hesap kimliği ) çizimdeki parçaları ( elemanın ad'ı )
BOLUM_PARCALARI = {
    "motor_gucu": ("makine", "tahrik_kasnagi"),
    "makine_konstruksiyonu": ("makine_sasesi",),
    "kabin_alani": ("kabin",),
    "aski_halatlari": ("halat", "tahrik_kasnagi", "kabin_kasnagi", "agirlik_kasnagi"),
    "regulator_halati": ("regulator", "regulator_kasnagi", "gergi", "gergi_kasnagi"),
    "tahrik_yetenegi": ("tahrik_kasnagi", "halat"),
    "kabin_raylari": ("kabin_rayi", "kabin_konsolu"),
    "agirlik_raylari": ("agirlik_rayi", "agirlik_konsolu"),
    "ayirma_kirisi": ("ayirma_kirisi",),
    "kuyu_tabani": ("kabin_kaidesi", "agirlik_kaidesi"),
    "tamponlar": ("kabin_tamponu", "agirlik_tamponu"),
}
#  Ağırlık rayları bölümü dolguyu da denetler:  "dolgu çerçeveye sığmıyor"
#  hükmünde sorun raylarda değil, karşı ağırlıktadır
DOLGU = ("agirlik_dolgu", "agirlik")

#  Notun kısa adları ( bölümün başlığı paftaya sığmayacak kadar uzun:
#  "KARŞI AĞIRLIK KILAVUZ RAYLARININ HESAPLANMASI" )
KISA_AD = {
    "motor_gucu": "Motor gücü",
    "makine_konstruksiyonu": "Makine konstrüksiyonu",
    "kabin_alani": "Kabin alanı",
    "aski_halatlari": "Askı halatları",
    "regulator_halati": "Regülatör halatı",
    "tahrik_yetenegi": "Tahrik yeteneği",
    "kabin_raylari": "Kabin rayları",
    "agirlik_raylari": "Karşı ağırlık rayları",
    "ayirma_kirisi": "Ayırma kirişi",
    "kuyu_tabani": "Kuyu tabanı",
    "tamponlar": "Tamponlar",
    "siginma_alanlari": "Sığınma alanları",
    "kabin_aydinlatma": "Kabin aydınlatması",
    "kuyu_aydinlatma": "Kuyu aydınlatması",
    "kurulu_guc": "Kurulu güç",
    "gerilim_dusumu": "Gerilim düşümü",
}


def _parcalar(kimlik, metin):
    adlar = list(BOLUM_PARCALARI.get(kimlik, ()))
    if kimlik == "agirlik_raylari" and "dolgu" in metin.lower():
        adlar += DOLGU
    return list(dict.fromkeys(parca_adlari.ad(a) for a in adlar))


def uygun_olmayanlar(sonuc):
    """Asansörün hesap sonucunda ( uygulama_hesabi.hesapla_coklu → asansorler[i] )
    UYGUN bulunmayan bölümler:  [ { kimlik, ad, metin, eksik, parcalar } ].
    eksik:  hüküm verilemedi ( "HESAP EKSİK — …" ) — uygun değil sayılmaz,
    notta ayrı söylenir.  Hesap yapılamadıysa ( sonuç yok, durdu ) boş liste:
    durmanın sebebi ekranda ve çizimin kendi sorunlarında."""
    if not sonuc or not sonuc.get("aktif"):
        return []
    liste = []
    for b in sonuc.get("bolumler") or []:
        s = b.get("sonuc") or {}
        if s.get("uygun") is not False:
            continue
        kimlik, metin = b.get("kimlik") or "", s.get("metin") or ""
        liste.append(
            {
                "kimlik": kimlik,
                "ad": KISA_AD.get(kimlik) or (b.get("ad") or kimlik).capitalize(),
                "metin": metin,
                "eksik": metin.upper().startswith("HESAP EKSİK"),
                "parcalar": _parcalar(kimlik, metin),
            }
        )
    return liste


def not_satirlari(liste):
    """Paftanın notu:  iki satır ( yoksa boş ).  Önce uygun olmayanlar, sonra
    hükmü eksik kalanlar."""
    uygun_degil = [b["ad"] for b in liste if not b["eksik"]]
    eksik = [b["ad"] for b in liste if b["eksik"]]
    if not uygun_degil and not eksik:
        return []
    parca = []
    if uygun_degil:
        parca.append(f"{len(uygun_degil)} bölüm UYGUN DEĞİLDİR")
    if eksik:
        parca.append(f"{len(eksik)} bölümün hesabı EKSİK")
    return [
        "HESAP:  " + "  ·  ".join(parca) + "  —  bkz. hesap raporu",
        "  ·  ".join(uygun_degil + [f"{a} ( eksik )" for a in eksik]),
    ]

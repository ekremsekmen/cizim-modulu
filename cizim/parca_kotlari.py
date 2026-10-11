"""KABİN VE KARŞI AĞIRLIĞIN KOTLARI — döşemesi ( ya da alt kirişi ) verilen
kotta duran kabinin / ağırlığın parçalarının düşey yerleri.

Saf hesap:  girdinin düşey ölçüleri ve çizim sabitleri ( S ).  Planlar,
kesitler, açıklık denetimleri ve hesabın çizimden ölçtükleri buradan okur
( donanim, dusey, kuyu_dibi, kabin_ustu, hareketli, olculer … ).  Eskiden
donanim.py'nin içindeydi ve kuyu_dibi ile kabin_ustu onu fonksiyon içinden
import ediyordu:  donanim de onları import ettiği için modüller birbirine
dolanmıştı.
"""

from cizim import parcalar
from temel import sayi_mi

#  Kabin önlüğü ( etek ) — m.5.4.5:  dik kısmı en az 0,75 m ( m.5.4.5.2 ), altında
#  pah ( m.5.4.5.1;  parcalar.ONLUK_PAH × ONLUK_PAH_DUSEY ).  Önlüğün EN ALT
#  noktası pahın ucudur:  kuyu dibi açıklığı ( m.5.2.5.8.2 a 1 ) oradan ölçülür
#  ( 7 Eki;  eskiden pah yoktu, dik kısmın altından ölçülüyordu — 35 mm iyimser ).
ETEK_BOYU = parcalar.ONLUK_DIK
ETEK_PAH_DUSEY = parcalar.ONLUK_PAH_DUSEY


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
    alt_paten = sase_alt + S["alt_paten_payi"]  # alt patenin merkezi
    ust_paten = alt_paten + dy["kabin_paten_arasi"]  # üst patenin merkezi
    alt_kiris_alt = max(sase_alt, alt_paten + P / 2.0)
    sase_ust = ust_paten - P / 2.0  # üst kirişin üstü
    if aski.get("duzen") == "Kabin üstü":
        kasnak_alti = (
            tavan + S["kabin_tavani_kasnak_boslugu"] if tavanda else sase_ust + S["kabin_ustu_kasnak_boslugu"]
        )
        kasnak_merkez = kasnak_alti + (aski.get("kasnak_capi") or 0) / 2.0
    else:
        kasnak_merkez = z - S["kabin_kasnak_derinlik"]
    return {
        "doseme": z,
        "taban_alti": z - S["kabin_taban_kalinlik"],
        "etek_dik_alti": z - ETEK_BOYU,
        "etek_alti": z - ETEK_BOYU - ETEK_PAH_DUSEY,
        "fren_alti": z - S["kabin_taban_kalinlik"] - S["fren_blogu_yukseklik"],
        "sase_alt": sase_alt,
        "sase_ust": sase_ust,
        "alt_kiris_alt": alt_kiris_alt,
        "alt_kiris_ust": alt_kiris_alt + S["sase_alt_kiris"],
        "ust_kiris_alt": sase_ust - S["sase_ust_kiris"],
        "ust_kiris_ust": sase_ust,
        "alt_paten": alt_paten - P / 2.0,
        "alt_paten_ust": alt_paten + P / 2.0,
        "ust_paten_alt": ust_paten - P / 2.0,
        "ust_paten": ust_paten + P / 2.0,
        "ic_ust": z + dy["kabin_ic_yukseklik"],
        "tavan": tavan,
        "kasnak_merkez": kasnak_merkez,
        "baglanti_ust": sase_ust + S["kabin_baglanti_alt"] - S["kabin_baglanti_ust"],
    }


def agirlik_kotlari(M, alt):
    """Alt kirişi `alt` kotundaki karşı ağırlığın parça kotları.  PATENLER
    ÇERÇEVENİN DIŞINDADIR ( üstte ve altta — LiftDesigner 1022'nin kesiti:
    2.000'lik çerçeve, 100'lük patenler;  kabin şasesindeki gibi ):  merkezleri
    arası hesabın paten arası, çerçeve ondan bir paten boyu kısa.  8 Eki'ye dek
    patenler çerçevenin uçlarına ortalıydı ( çerçeve = paten arası );  daha
    önce çerçevenin ortasına göre 1.500 aralıkla diziliyorlardı."""
    A = M["agirlik"]
    ust = alt + A["yukseklik"] - A["paten"]
    return {
        "alt": alt,
        "ust": ust,
        "kasnak_merkez": ust - A["kasnak_ust"],
        "alt_paten": alt - A["paten"],
        "alt_paten_ust": alt,
        "ust_paten_alt": ust,
        "ust_paten": ust + A["paten"],
    }


def agirlik_dolgu_kotlari(g, S, AK):
    """Karşı ağırlık dolgusunun alt ve üst kotu:  alt kirişin üstünden üst
    kirişin altına;  2:1'de ağırlık kasnağının altına kadar ( karar 11 ).
    Kesit ve hesabın dolgu yüksekliği ( olculer ) bunu kullanır — kesit
    eskiden dolguyu kasnağın içine kadar çiziyordu ( 2:1'de 300 mm )."""
    alt, ust = AK["alt"] + S["agirlik_kiris"], AK["ust"] - S["agirlik_kiris"]
    cap = (g.get("agirlik") or {}).get("kasnak_capi")
    if (g.get("aski") or {}).get("duzen") != "Doğrudan" and sayi_mi(cap):
        ust = min(ust, AK["kasnak_merkez"] - cap / 2.0)
    return alt, ust

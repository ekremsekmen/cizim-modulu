# -*- coding: utf-8 -*-
"""
ASANSÖR TRAFİK HESABI  —  MMO/697, 2. Baskı, Ocak 2020, s.11-17

  · aynı tip asansörler   ->  hesapla_tek()      ( MMO/697 s.11-12 )
  · farklı tip asansörler ->  hesapla_coklu()    ( grup formülü, s.12 )
"""
from engine.avan import tablolar as T
from engine.ortak.steps import (Bolum, veri, hesap, tr, trn, yukari_yuvarla,
                    yuvarla, sayi_mi)


# =====================================================================
#  ORTAK YARDIMCILAR
# =====================================================================
def _bodrum_oku(deger):
    """
    Bodrum (ana giriş altı) durak adedini okur.
    Dönen: (Nb, hata)   —  boş / None  →  (0, None)
    """
    if deger is None or deger == "":
        return 0, None
    if not sayi_mi(deger):
        return 0, ("HESAP HATASI: ⑪ bodrum durak adedi sayı olmalıdır "
                   f"(0 – {T.BODRUM_AZAMI} arası tam sayı ya da boş).")
    if float(deger) != int(deger) or deger < 0 or deger > T.BODRUM_AZAMI:
        return 0, (f"HESAP HATASI: ⑪ bodrum durak adedi 0 ile {T.BODRUM_AZAMI} arasında "
                   "tam sayı olmalıdır (ana giriş altında hizmet verilen durak adedi).")
    return int(deger), None


#  TAAHHÜTNAME  —  MMO/697 Tablo-10 "Şartlı Kabul" sütunu.
#  Tek asansör tanımında program adedi KENDİ bulur ( n = MAX[taşıma; bekleme] )
#  ve bunu uygulanan sınırla ( Standart / Yükseltilmiş ) yapar.  Taahhütname
#  verilecekse bekleme ölçütü şartlı kabul sınırıdır; o sınırda yeten adet
#  seçilebilmelidir.  Eskiden "şartlı kabulle 1 adet yeterli olurdu" yazılıyor
#  ama bu adedi seçmenin hiçbir yolu yoktu.
def _taahhut_oku(deger):
    """Dönen: (var_mi, hata)   —  boş / Yok  →  (False, None)"""
    m = "" if deger is None else str(deger).strip().casefold()
    if m in ("", "yok"):
        return False, None
    if m == "var":
        return True, None
    return False, (f"HESAP HATASI: taahhütname seçimi okunamadı ( {str(deger).strip()[:20]!r} ) "
                   "— 'Yok' ya da 'Var' seçilmelidir.")


#  DURAK ADEDİ  ( ana giriş dâhil )  —  tek ve çoklu hesapta AYNI kural.
#  Boş bırakılırsa asansör ana giriş üstündeki bütün katlara hizmet eder
#  ( Ni = N ).  Kural TEK YERDE dursun ki iki hesap yolu ayrışmasın:
#  çoklu yol alanı okuyup H / S / TR'yi ona göre kurarken tek yol alanı hiç
#  görmüyordu — kullanıcı bir sayı yazıyor, hiçbir şey olmuyordu.
def _durak_oku(deger, N, on_ek=""):
    """
    Asansörün durduğu kat adedini ana giriş ÜSTÜ kat adedine çevirir.
    Dönen: (Ni, hata)   —  boş / None  →  (N, None)
    """
    if deger is None or deger == "":
        return N, None
    if not (sayi_mi(deger) and float(deger).is_integer()
            and 2 <= deger <= (N or 0) + 1):
        return None, (f"HESAP HATASI: {on_ek}durak sayısı geçersiz — 2 ile ortak durak sayısı "
                      "(N+1) arasında tam sayı girin veya boş bırakın")
    return int(deger) - 1, None


#  SÜRELERİN ÇÖZÜMÜ  —  ta / tk / tg / tp   ( tek ve çoklu hesapta AYNI kural )
#
#  Tek ve çoklu hesap bu değerleri AYNI Tablo-4 / Tablo-6 / Tablo-8'den okur.
#  Tablo OKUMA zaten ortaktı ( tablolar.py ) ama tablonun ETRAFINDAKİ katman —  elle
#  ezme, uyarı metinleri, kaynak yazısı — iki kez yazılmıştı ve ayrışmıştı:
#  çoklu pafta, Tablo-4 / Tablo-8 ara değer uyarılarının KISALTILMIŞ hâlini
#  basıyor, "imalatçı katalog değeri varsa manuel girin" öğüdünü hiç
#  yazmıyordu.  Kural artık tek yerde.
def _sure_cozumle(kaynak, kg_, kt, V, P, on_ek=""):
    """
    kaynak : manuel_ta / manuel_tk / manuel_tg / manuel_tp taşıyan girdi sözlüğü
    on_ek  : uyarıların başına konur ( çoklu hesapta "ASANSÖR-2: " )

    Dönen sözlük:  ta, tk, tg, tp, kaynak{...}, uyarilar[...], elle
    """
    m = {ad: (kaynak or {}).get("manuel_" + ad) for ad in ("ta", "tk", "tg", "tp")}
    t4_ta, t4_tk = T.tablo4_ta_tk(kg_, kt)
    tablo = {"ta": t4_ta, "tk": t4_tk, "tg": T.tablo6_tg(V), "tp": T.tablo8_tp(kg_)}
    deger = {ad: (m[ad] if sayi_mi(m[ad]) else tablo[ad]) for ad in tablo}

    tablo_kaynagi = {"ta": T.tablo4_kaynagi(kg_), "tk": T.tablo4_kaynagi(kg_),
                     "tg": T.tg_kaynagi(V), "tp": T.tablo8_kaynagi(kg_)}
    kaynaklar = {ad: ("İmalatçı verisi" if sayi_mi(m[ad]) else tablo_kaynagi[ad])
                 for ad in tablo}

    U = []
    elle = sum(1 for x in m.values() if sayi_mi(x))
    if elle:
        U.append(f"⚠ {on_ek}{elle} adet süre imalatçı verisiyle değiştirildi "
                 "(MMO Tablo-4/6/8 yerine). Paftada marka-model ve teknik föy "
                 "referansı belirtilmelidir.")
    if kg_ in T.TABLO_4_ARA and not (sayi_mi(m["ta"]) and sayi_mi(m["tk"])):
        U.append(f"⚠ {on_ek}{kg_} mm MMO/697 Tablo-4'te basılı değildir; ta/tk komşu "
                 "satırlar arasında doğrusal enterpolasyonla bulunmuştur. İmalatçı "
                 "katalog değeri varsa manuel ta/tk girilmesi tercih edilir.")
    if kg_ in T.TABLO_8_ARA and not sayi_mi(m["tp"]):
        U.append(f"⚠ {on_ek}{kg_} mm ISO 8100-32:2020 Tablo 6 kapsamı dışındadır "
                 "(tablo 800 mm'de başlar); tp = 1,3 s, 800→900 mm eğiminden dış "
                 "değerlemeyle alınmıştır (emniyetli taraf). İmalatçı verisi varsa "
                 "manuel tp girin.")
    U += T.erisilebilirlik_uyarilari(P, kg_, on_ek=on_ek)
    return {**deger, "kaynak": kaynaklar, "uyarilar": U, "elle": elle}


#  ts = ta + tk + tg − tv   FİZİKSEL BİR SÜREDİR:  sıfır ya da negatif olamaz.
#  Süreleri tek tek denetlemek YETMİYOR:  ta = tk = tg = tp = 0,1 s ( izin verilen
#  tam alt sınır ) girildiğinde her biri geçerli ama ts = −1,57 s çıkıyor, TR
#  129 sn'den 28 sn'ye düşüyor ve program 2 yerine 1 asansör yetiyor diyordu.
#  Denetim TÜREYEN değer üzerinde yapılmalıdır.
def _ts_hatasi(ts, ta, tk, tg, tv, on_ek=""):
    if not sayi_mi(ts) or ts > 0:
        return None
    return (f"HESAP HATASI: {on_ek}kapı bekleme süresi ts = {tr(ts)} s çıkıyor "
            f"( ts = ta + tk + tg − tv = {tr(ta)} + {tr(tk)} + {tr(tg)} − {tr(tv)} ). "
            "Bir süre sıfır ya da negatif olamaz: girilen ta/tk/tg değerleri kabinin "
            "bir katı geçme süresinden ( tv ) küçük kalıyor. İmalatçı değerlerini "
            "kontrol edin ya da alanları boşaltıp tablo değerlerini kullanın.")


#  GİRDİ KUTULARININ ADLARI  —  arayüz etiketi ile red metni AYNI kaynaktan.
#  Okunamayan bir girdi "hizli1 = 1.200" diye bildiriliyordu:  kullanıcı
#  ekranda "hizli1" diye bir kutu görmez.  ⑤ / ⑥ kutularının adı bina tipine
#  göre değişir;  arayüz de etiketini buradan okur ( /api/secenekler ).
#  Her kutu:  ( ad, ipucu )  —  etiket = ad + ipucu,  red metni yalnız ad.
_HIZLI_YOK = ("⑥", "(bu bina tipinde gerekmiyor — boş bırakın)")


def hizli_etiketleri(bina_tipi):
    """⑤ / ⑥ hızlı nüfus girişi kutularının bina tipine göre adı.

    Dönen:  {"hizli1": (ad, ipucu), "hizli2": (ad, ipucu)}  —  dallanma
    _nufus_satirlari() ile aynıdır ( hangi kutu hangi Tablo-1 kalemine gider ).
    """
    bt = bina_tipi if isinstance(bina_tipi, str) else ""
    if not bt:
        return {"hizli1": ("⑤", "—"), "hizli2": _HIZLI_YOK}
    if bt == "Konut":
        return {"hizli1": ("⑤ Daire sayısı", "(bağımsız bölüm adedi)"),
                "hizli2": ("⑥ Daire başına DİĞER oda sayısı", "(ilk yatak odası hariç)")}
    if bt.startswith("İş Merkezi") or bt.startswith("Kamu"):
        return {"hizli1": ("⑤ Toplam çalışma alanı", "(m²)  →  12 m² = 1 kişi"),
                "hizli2": _HIZLI_YOK}
    if bt.startswith("Otel") or bt == "Hastane":
        return {"hizli1": ("⑤ Toplam yatak sayısı", ""), "hizli2": _HIZLI_YOK}
    if bt == "Katlı Otopark":
        return {"hizli1": ("⑤ Özel amaçlı araç adedi", ""),
                "hizli2": ("⑥ Ticari amaçlı araç adedi", "")}
    return {"hizli1": ("⑤", "Bu bina tipinde hızlı giriş yok — ek nüfus kalemlerini kullanın"),
            "hizli2": _HIZLI_YOK}


#  Bina ( ortak ) kutuları — arayüzdeki etiketlerin aynısı.  ⑤ / ⑥ yukarıda.
GIRDI_ETIKET = {
    "bina_yuksekligi": "② Bina yüksekliği",
    "N": "③ Kat sayısı N",
    "yapi_yuksekligi": "④ Yapı yüksekliği",
    "h": "⑦ Kat yüksekliği h",
    "P": "⑧ Kapasite P",
    "kapi_genisligi": "⑨ Kapı genişliği",
    "bodrum": "⑪ Bodrum durağı",
    "manuel_V": "Manuel ortak V",
    "manuel_k": "Manuel k",
    "manuel_adet": "Asansör adedi",
    "manuel_ta": "ta ( imalatçı )", "manuel_tk": "tk ( imalatçı )",
    "manuel_tg": "tg ( imalatçı )", "manuel_tp": "tp ( imalatçı )",
}

#  Asansör kartı kutuları ( ASANSÖR-i ) — kartta "boş = ortak" olanlar
#  ortak kutudan ayırt edilsin diye numarasız yazılır.
ASANSOR_ETIKET = {
    "P": "⑧ Kapasite P",
    "kapi_genisligi": "⑨ Kapı genişliği",
    "V": "V — kabin hızı",
    "durak": "Durak",
    "h": "h — kat yüksekliği",
    "bodrum": "Bodrum durağı",
    "manuel_ta": "ta ( imalatçı )", "manuel_tk": "tk ( imalatçı )",
    "manuel_tg": "tg ( imalatçı )", "manuel_tp": "tp ( imalatçı )",
}


def girdi_etiketleri(bina_tipi):
    """Bina kutularının red metnindeki adları — ⑤ / ⑥ bina tipine göre."""
    return {**GIRDI_ETIKET,
            **{k: ad for k, (ad, _ipucu) in hizli_etiketleri(bina_tipi).items()}}


#  ⑤ / ⑥ NÜFUS GİRDİLERİ  —  tek ve çoklu hesapta AYNI denetim.
#  Üst sınır vardı ( "ondalık ayracı olarak virgül kullanın" ), ALT sınır yoktu:
#  ⑥ diğer oda sayısına −1 girilince bir dairedeki kişi 2 + (−1) = 1 oluyor,
#  nüfus 500'den 100'e düşüyor ve gereken asansör 4'ten 2'ye iniyordu — hatasız.
#  Negatif oda / yatak / araç / alan diye bir şey yoktur.
def _nufus_girdi_hatasi(bt, h1, h2, on_ek=""):
    bt = bt or ""
    for deger, ad in ((h1, "⑤"), (h2, "⑥")):
        if sayi_mi(deger) and deger < 0:
            return (f"HESAP HATASI: {on_ek}{ad} girdisi negatif ( {tr(deger)} ) — "
                    "oda / yatak / araç adedi ya da çalışma alanı negatif olamaz.")
    if ((bt == "Konut" and ((sayi_mi(h1) and h1 > 2000) or (sayi_mi(h2) and h2 > 20)))
            or ((bt.startswith("Otel") or bt == "Hastane") and sayi_mi(h1) and h1 > 20000)
            or (bt == "Katlı Otopark" and ((sayi_mi(h1) and h1 > 20000)
                                           or (sayi_mi(h2) and h2 > 20000)))):
        return (f"HESAP HATASI: {on_ek}⑤/⑥ değeri olağandışı — girdiyi kontrol edin "
                "(ondalık ayracı olarak virgül kullanın).")
    return None


def _hesap_standardi(bina_yuksekligi, yapi_yuksekligi):
    """BYKHY md.4 — yüksek yapı ölçütü."""
    by = bina_yuksekligi or 0
    yy = yapi_yuksekligi or 0
    return "Yükseltilmiş" if (by > T.YUKSEK_BINA_YUKSEKLIK or yy > T.YUKSEK_YAPI_YUKSEKLIK) else "Standart"


def _nufus_satirlari(bina_tipi, hizli1, hizli2, ek_satirlar=None):
    """
    ⑤/⑥ hızlı giriş kutularını Tablo-1 kalemlerine çevirir.
    Dönen: (satırlar, b)   satır = {aciklama, miktar, kalem, birim, katsayi, c}
    """
    satirlar = []

    def kalem_ekle(aciklama, miktar, kalem):
        if kalem and sayi_mi(miktar):
            t = T.TABLO_1[kalem]
            satirlar.append({
                "aciklama": aciklama, "miktar": miktar, "kalem": kalem,
                "birim": t["birim"], "katsayi": t["katsayi"],
                "c": miktar * t["katsayi"],
            })

    bt = bina_tipi or ""
    if bt == "Konut":
        kalem_ekle("↑ ⑤ hızlı girişinden (daire adedi)", hizli1, "KONUT — İlk yatak odası")
        if sayi_mi(hizli1) and sayi_mi(hizli2):
            kalem_ekle("↑ ⑥ hızlı girişinden (daire × diğer oda)", hizli1 * hizli2, "KONUT — Diğer oda")
    elif bt.startswith("İş Merkezi"):
        kalem_ekle("↑ ⑤ toplam çalışma alanı", hizli1, "İŞ MERKEZİ — Çalışma alanı")
    elif bt.startswith("Kamu"):
        kalem_ekle("↑ ⑤ toplam çalışma alanı", hizli1, "RESMİ BİNA — Çalışma alanı")
    elif bt.startswith("Otel"):
        kalem_ekle("↑ ⑤ toplam yatak sayısı", hizli1, "OTEL — Yatak")
    elif bt == "Hastane":
        kalem_ekle("↑ ⑤ toplam yatak sayısı", hizli1, "HASTANE — Yatak")
    elif bt == "Katlı Otopark":
        kalem_ekle("↑ ⑤ özel amaçlı araç adedi", hizli1, "OTOPARK — Özel araç")
        kalem_ekle("↑ ⑥ ticari amaçlı araç adedi", hizli2, "OTOPARK — Ticari araç")

    for s in (ek_satirlar or []):
        kalem = s.get("kalem")
        miktar = s.get("miktar")
        if kalem in T.TABLO_1 and sayi_mi(miktar):
            t = T.TABLO_1[kalem]
            satirlar.append({
                "aciklama": s.get("aciklama") or "Ek nüfus kalemi", "miktar": miktar,
                "kalem": kalem, "birim": t["birim"], "katsayi": t["katsayi"],
                "c": miktar * t["katsayi"],
                #  Bu satır ⑤/⑥ girdilerinden DEĞİL, "ek nüfus" listesinden
                #  gelir.  Pafta notunun doğru yazılabilmesi için ayırt edilir
                #  ( bkz. _nufus_bolunmus ).
                "ek": True,
            })

    b = yuvarla(sum(s["c"] for s in satirlar), 6)
    return satirlar, b


def _nufus_bolunmus(bina_tipi, hizli1, hizli2, b, nufus_satirlari=None):
    """
    (aciklamalar, notlar) — ilk satır Tablo-1 KURALIDIR (yöntem açıklaması,
    ekranda ⓘ içinde), kalanlar bu projenin türetimidir (ekranda görünür).

    EK NÜFUS:  ⑤/⑥ girdilerinin dışında elle eklenen nüfus kalemleri varsa
    ana formül YALNIZ kendi toplamını yazar ( "44 × 5 = 220 kişi" ), her ek
    kalem kendi satırında gösterilir ve en sona toplam konur.  Aksi hâlde
    pafta "44 × 5 = 1.360 kişi" gibi KENDİ İÇİNDE ÇELİŞEN bir satır basar;
    denetimde bu hesap hatası olarak okunur.
    """
    ek = [x for x in (nufus_satirlari or []) if x.get("ek")]
    b_ana = (yuvarla(sum(x["c"] for x in nufus_satirlari if not x.get("ek")), 6)
             if nufus_satirlari else b)
    satirlar = [x for x in _nufus_aciklamasi(bina_tipi, hizli1, hizli2, b_ana) if x]
    if not satirlar:
        return [], []
    for x in ek:
        satirlar.append(
            f"Ek nüfus — {x['aciklama']}: {trn(x['miktar'], 2)} {x['birim']} × "
            f"{trn(x['katsayi'], 4)} = {trn(x['c'], 2)} kişi  ({x['kalem']})")
    if ek:
        satirlar.append(
            f"Toplam  b = Σc = {trn(b_ana, 2)} + {trn(b - b_ana, 2)} = {trn(b, 2)} kişi")
    return satirlar[:1], satirlar[1:]


def _nufus_aciklamasi(bina_tipi, hizli1, hizli2, b):
    """PAFTA sayfasındaki nüfus cümlesi."""
    bt = bina_tipi or ""
    if bt == "Konut":
        t1 = ("Tablo-1: Her dairenin ilk yatak odası için 2 kişi, diğer odaların her biri için "
              "1 kişi alınır; mutfak ve ıslak hacimler hesaba katılmaz.")
        if sayi_mi(hizli2):
            if float(hizli2).is_integer():
                t2 = (f"Daireler {trn(hizli2,0)}+1 olup bir dairede sayılan oda adedi "
                      f"{trn(hizli2+1,0)} olarak alınmıştır (1 ilk yatak odası + {trn(hizli2,0)} diğer oda). "
                      f"Bir dairedeki kişi sayısı = 2 + ({trn(hizli2,0)} × 1) = {trn(2+hizli2,0)} kişi.")
            else:
                t2 = (f"Daire başına ortalama diğer oda adedi {tr(hizli2)} alınmıştır. "
                      f"Bir dairedeki ortalama kişi sayısı = 2 + {tr(hizli2)} = {tr(2+hizli2)} kişi.")
            t3 = f"Daire adedi {trn(hizli1,0)}  →  b = {trn(hizli1,0)} × {trn(2+hizli2,2)} = {trn(b,2)} kişi"
        else:
            t2, t3 = "", f"b = Σc = {trn(b,2)} kişi"
        return [t1, t2, t3]
    if bt.startswith("İş Merkezi") or bt.startswith("Kamu"):
        return ["Tablo-1: Çalışma alanının her 12 m²si için 1 kişi alınır.",
                f"Binadaki toplam çalışma alanı {trn(hizli1,2)} m² olarak alınmıştır.",
                f"b = {trn(hizli1,2)} ÷ 12 = {trn(b,2)} kişi"]
    if bt.startswith("Otel"):
        return ["Tablo-1: Her yatak için 1 kişi alınır.",
                f"Binadaki toplam yatak sayısı {trn(hizli1,0)} olarak alınmıştır.",
                f"b = {trn(hizli1,0)} × 1 = {trn(b,2)} kişi"]
    if bt == "Hastane":
        return ["Tablo-1: Her yatak için 3 kişi alınır.",
                f"Binadaki toplam yatak sayısı {trn(hizli1,0)} olarak alınmıştır.",
                f"b = {trn(hizli1,0)} × 3 = {trn(b,2)} kişi"]
    if bt == "Katlı Otopark":
        return ["Tablo-1: Özel amaçlı araç başına 1 kişi, ticari amaçlı araç başına 1,5 kişi alınır.",
                f"Özel amaçlı araç adedi {trn(hizli1,0)}, ticari amaçlı araç adedi {trn(hizli2 or 0,0)} olarak alınmıştır.",
                f"b = ({trn(hizli1,0)} × 1) + ({trn(hizli2 or 0,0)} × 1,5) = {trn(b,2)} kişi"]
    return ["Nüfus MMO/697 Tablo-1'e göre hesaplanmıştır.",
            "Nüfus, ayrıntılı nüfus tablosundan alınmıştır.",
            f"b = Σc = {trn(b,2)} kişi  (ayrıntılı nüfus tablosundan)"]


# =====================================================================
#  TEK ASANSÖR   —   HESAPLAMA sayfası  ->  PAFTA
# =====================================================================
def hesapla_tek(g: dict) -> dict:
    """
    g (girdiler):
      bina_tipi, bina_yuksekligi, yapi_yuksekligi, N, hizli1, hizli2, h, P,
      kapi_genisligi, kapi_tipi
      opsiyonel: bodrum, manuel_k, manuel_V, manuel_ta, manuel_tk, manuel_tg,
                 manuel_tp, manuel_adet, taahhutname ( Yok / Var ), ek_nufus[],
                 proje_adi, isveren, pafta_no, tarih
    """
    U = []                       # uyarılar
    hata = None

    bina_tipi = g.get("bina_tipi")
    if not isinstance(bina_tipi, str):
        bina_tipi = str(bina_tipi) if bina_tipi is not None else ""
    t10 = T.TABLO_10.get(bina_tipi)
    if t10 is None:
        return {"hata": "HESAP HATASI: Bina tipi listeden seçilmelidir."}

    N   = g.get("N")
    P   = g.get("P")
    h   = g.get("h")
    kg_ = g.get("kapi_genisligi")
    kt  = g.get("kapi_tipi")
    by  = g.get("bina_yuksekligi")
    yy  = g.get("yapi_yuksekligi")

    # ---- Nb : ana giriş ALTINDA hizmet verilen durak adedi (bodrum)
    Nb, Nb_hata = _bodrum_oku(g.get("bodrum"))
    if Nb_hata:
        hata = Nb_hata

    standart = _hesap_standardi(by, yy)                       # C8
    hiz_grubu = t10["hiz_grubu"]                              # C17
    k_tipi    = t10["k_tipi"]                                 # C6
    yuk_kg    = T.tablo7_yuk(P)                               # E13
    p         = 0.8 * P if sayi_mi(P) else None               # C15

    # ---- nüfus
    nufus_satirlari, b = _nufus_satirlari(bina_tipi, g.get("hizli1"), g.get("hizli2"),
                                          g.get("ek_nufus"))
    n_artis = 0.3 if (b or 0) < 200 else 0.25                 # C21
    B = yukari_yuvarla(b * (1 + n_artis), 0) if sayi_mi(b) else None   # C22

    # ---- k (taşınacak insan yüzdesi)
    manuel_k = g.get("manuel_k")
    k_notu = ""
    if bina_tipi.startswith("Kamu") and sayi_mi(manuel_k) and 0 < manuel_k <= 1:
        k = manuel_k
        k_notu = "Manuel giriş"
    elif k_tipi is None:
        if sayi_mi(manuel_k) and 0 < manuel_k <= 1:
            k, k_notu = manuel_k, "Manuel giriş (Tablo-9'da bu bina tipi yok)"
        else:
            k, k_notu = None, "Manuel k gerekli"
    else:
        k = T.TABLO_9[k_tipi][standart]
        k_notu = "MMO/697 Tablo-9"
        if bina_tipi.startswith("Kamu"):
            k_notu = "Tablo-9'da kamu yok → İş Merkezi %k varsayıldı"
            U.append("Kamu binaları MMO/697 Tablo-9'da yoktur; %k için İŞ MERKEZİ "
                     "satırı varsayılmıştır. Farklı bir oran gerekiyorsa manuel k girin.")
    if bina_tipi.startswith("Kamu"):
        U.append("Kamu binaları MMO/697 Tablo-2'de de yoktur; asgari hız için "
                 "BÜRO VE İŞ MERKEZİ grubu varsayılmıştır. Bu iki varsayım paftaya "
                 "yazılmıştır.")

    # ---- V (kabin hızı)
    #  Tablo-2 asgari hızı, asansörün DURDUĞU toplam kat adedine göre seçilir:
    #  ana giriş üstü N kat + ana giriş + bodrumdaki Nb durak.
    durak = (N + 1 + Nb) if sayi_mi(N) else None
    V_min = T.tablo2_min_hiz(hiz_grubu, durak) if (hiz_grubu and durak) else None   # I68
    manuel_V = g.get("manuel_V")
    if sayi_mi(manuel_V) and manuel_V not in T.GECERLI_HIZLAR:
        hata = ("HESAP HATASI: Manuel hız geçersiz — listeden seçin "
                "(0,63 / 1 / 1,6 / 1,75 / 2 / 2,5 / 3 / 3,5 / 5 / 6 m/s)")
        V = None
    elif sayi_mi(manuel_V):
        V = manuel_V
    else:
        V = V_min

    V_notu = ""
    if V is None:
        V_notu = "Tablo-2'de bu bina tipi yok — hız proje kararıdır; gerekçesini paftaya yazın."
    elif V_min is None:
        V_notu = "Tablo-2'de bu bina tipi yok — hız tümüyle proje kararıdır; gerekçesini paftaya yazın."
    elif V < V_min:
        V_notu = (f"⚠ Tablo-2 minimumu {tr(V_min)} m/s — seçilen {tr(V)} m/s bunun ALTINDA. "
                  f"Bekleme süresi sağlandığı için hesap geçerlidir; gerekçeyi paftaya yazın.")
        U.append(V_notu)
    elif V > V_min:
        V_notu = f"Tablo-2 minimumu {tr(V_min)} m/s — seçilen {tr(V)} m/s (üstü)."
    else:
        V_notu = f"Tablo-2 minimumu uygulandı: {tr(V)} m/s."
    #  PAFTADAKİ KAYNAK HIZIN GERÇEKTEN NEREDEN GELDİĞİNİ SÖYLER.  Her durumda
    #  "MMO/697 Tablo-2" basılıyordu:  hastane paftasında, Tablo-2'de hastane
    #  satırı yokken ve hızı kullanıcı seçmişken bile.  ( Not ekranda kalır,
    #  paftaya basılmaz — kaynak sütunu basılır. )
    if sayi_mi(V) and sayi_mi(V_min) and V == V_min:
        V_kaynak = f"MMO/697 Tablo-2 (durak = {durak})"
    elif sayi_mi(V_min):
        V_kaynak = f"Proje kararı ( Tablo-2 min. {tr(V_min)} m/s )"
    elif sayi_mi(V):
        V_kaynak = "Proje kararı ( Tablo-2'de yok )"
    else:
        V_kaynak = "Seçilmedi ( Tablo-2'de yok )"

    # ---- tablo değerleri
    H = T.tablo3_H(N, P) if (sayi_mi(N) and sayi_mi(P)) else None
    S = T.tablo5_S(N, P) if (sayi_mi(N) and sayi_mi(P)) else None

    _s = _sure_cozumle(g, kg_, kt, V, P)
    ta, tk, tg, tp = _s["ta"], _s["tk"], _s["tg"], _s["tp"]
    mtg = g.get("manuel_tg")            # yalnız öneri tablosuna geçer
    U += _s["uyarilar"]

    # ---- doğrulama (E45 / H45 karşılığı)
    if hata is None:
        hata = _dogrula_tek(g, b, N, P, kg_, kt, ta, tk, tg, tp, k, V, h, by, yy, k_tipi)

    # ---- toplam seyahat mesafesi (avan Hk için) — bodrum dâhil
    toplam_seyahat = ((N + Nb) * h) if (sayi_mi(N) and sayi_mi(h)) else None

    # ---- tur süresi
    tv = h / V if (sayi_mi(h) and sayi_mi(V) and V) else None                 # C33
    ts = (ta + tk + tg - tv) if all(sayi_mi(x) for x in (ta, tk, tg, tv)) else None  # C34
    TR = (2 * H * tv + (S + 1) * ts + 2 * p * tp) \
        if all(sayi_mi(x) for x in (H, tv, S, ts, p, tp)) else None           # C35
    R = (300 * p / TR) if (sayi_mi(TR) and TR and sayi_mi(p)) else None       # C36
    hata = hata or _ts_hatasi(ts, ta, tk, tg, tv)

    Izul = t10["yukseltilmis"] if standart == "Yükseltilmiş" else t10["standart"]  # K68

    # ---- asansör adedi
    #  GEREKLİ ADET İKİ ÖLÇÜTÜN BİRLİKTE SAĞLANMASIDIR.  Yalnız bekleme
    #  süresinden bir sayı türetmek yanıltıcıdır: taşıma kapasitesi daha çok
    #  asansör gerektiriyorsa taahhütname o eksiği kapatmaz.
    def _gerekli_adet(sinir):
        """Verilen bekleme sınırında HER İKİ ölçütü de sağlayan asansör adedi."""
        if not (sayi_mi(TR) and sayi_mi(sinir) and sinir > 0):
            return None
        bek = yukari_yuvarla(TR / sinir, 0)
        tas = tasima_adedi if sayi_mi(tasima_adedi) else 0
        return int(max(1, tas, bek))

    adet_hesap = None
    tasima_adedi = bekleme_adedi = None
    if all(sayi_mi(x) for x in (B, k, R, TR, Izul)) and R and Izul:
        tasima_adedi = yukari_yuvarla(B * k / R, 0)
        bekleme_adedi = yukari_yuvarla(TR / Izul, 0)
        adet_hesap = int(max(1, tasima_adedi, bekleme_adedi))
    sartli = t10["sartli"]
    esik_standart = t10["standart"]
    esik_yukseltilmis = t10["yukseltilmis"]

    #  Taahhütname yalnız ADEDİ PROGRAMIN BULDUĞU yolda ( tek kolon ) anlamlıdır.
    #  İki ve daha fazla kolonda adet kullanıcınındır; o yol şartlı kabulü
    #  zaten kendiliğinden sınıflandırır ( aşağıdaki SONUÇ dalları ).
    manuel_adet = g.get("manuel_adet")
    elle_adet = sayi_mi(manuel_adet) and manuel_adet >= 1
    taahhut, t_hata = _taahhut_oku(g.get("taahhutname"))
    taahhut = taahhut and not elle_adet
    taahhut_adet = None
    if t_hata and not elle_adet:
        hata = hata or t_hata
    elif taahhut:
        if not (sayi_mi(sartli) and sartli):
            hata = hata or (f"HESAP HATASI: {bina_tipi} için MMO/697 Tablo-10'da şartlı kabul "
                            "sınırı yoktur — taahhütname 'Yok' seçilmelidir.")
        else:
            taahhut_adet = _gerekli_adet(sartli)
    adet = (int(manuel_adet) if elle_adet
            else taahhut_adet if taahhut_adet is not None else adet_hesap)
    Ieer = (TR / adet) if (sayi_mi(TR) and adet) else None                    # C38
    #  Taahhütname seçili ama uygulanan sınır aynı adetle zaten sağlanıyorsa
    #  taahhütnameye gerek yoktur — sessiz kalmasın.
    taahhut_gereksiz = (taahhut_adet is not None and taahhut_adet == adet_hesap)
    if taahhut_gereksiz:
        U.append(f"ℹ Taahhütname seçildi ama gerekmiyor: {standart} sınırı "
                 f"( {trn(Izul,0)} sn ) {adet_hesap} adetle zaten sağlanıyor.")

    # ---- SONUÇ (C44)
    #  İKİ ÖLÇÜT AYRI AYRI TUTULUR:  hangisinin sağlanmadığı sonuç cümlesinde
    #  DOĞRU yazılmalıdır.  Eskiden her olumsuz sonuçta "bekleme süresi
    #  sağlanmıyor" yazıyordu; oysa elle seçilen adette çoğu zaman sağlanmayan
    #  TAŞIMA kapasitesidir ( bekleme sağlanıyor olabilir ) — paftanın en
    #  görünür cümlesi yanlış gerekçe söylüyordu.
    tasima_ok = (all(sayi_mi(x) for x in (adet, R, B, k)) and adet * R >= B * k)
    bekleme_ok = (sayi_mi(Ieer) and sayi_mi(Izul) and Ieer <= Izul)
    bekleme_sartli_ok = (sayi_mi(Ieer) and sayi_mi(sartli) and bool(sartli)
                         and Ieer <= sartli)
    if hata:
        sonuc = hata
    elif tasima_ok and bekleme_ok:
        sonuc = f"{standart} kriteri karşılanıyor"
    elif tasima_ok and bekleme_sartli_ok:
        #  UYGULANAN sınır esas alınır.  Bina yüksek yapıysa geçerli sınır
        #  "Yükseltilmiş"tir; "Standart" sütunu o bina için ölçüt değildir —
        #  oradan adet vermek gereken asansör sayısını OLDUĞUNDAN AZ gösterir.
        sonuc = (f"Şartlı Kabul (taahhütname ile) — {standart} sınırı "
                 f"( {trn(Izul,0)} sn ) için {adet_hesap} adet gerekir")
    elif sayi_mi(manuel_adet):
        sonuc = (f"Kabul Edilmez — seçilen {int(manuel_adet)} adet asansör bu bina için "
                 f"UYGUN DEĞİLDİR; en az {adet_hesap} adet gerekir")
    else:
        sonuc = "Kabul Edilmez — girdileri/kriteri kontrol edin"

    if hata:
        sonuc_cumlesi = hata
    elif sonuc.startswith("Kabul"):
        _eksik = ([] if tasima_ok else ["taşıma kapasitesi"]) + \
                 ([] if bekleme_ok else ["bekleme süresi"])
        _ad = " ve ".join(_eksik) if _eksik else "uygunluk"
        sonuc_cumlesi = (_ad[0].upper() + _ad[1:] +
                         (" kriterleri" if len(_eksik) > 1 else " kriteri") +
                         " sağlanmıyor; kabin kapasitesi, hız veya asansör adedi "
                         "gözden geçirilmelidir" +
                         (f". En az {adet_hesap} adet gerekir." if sayi_mi(adet_hesap) else "."))
    elif sonuc.startswith("Şartlı"):
        sonuc_cumlesi = (f"Toplamda {adet} adet {trn(P,0)} kişilik ({trn(yuk_kg,0)} kg), {tr(V)} m/s "
                         f"hızında asansör önerilmektedir. Bekleme süresi {tr(Ieer,1)} sn olup "
                         f"MMO/697 Tablo-10 şartlı kabul sınırı {trn(sartli,0)} sn içindedir; taahhütname ile "
                         f"uygundur. Bu bina için uygulanan {standart} sınırı "
                         f"( {trn(Izul,0)} sn ) sağlanacaksa {adet_hesap} adet gerekir.")
    else:
        sonuc_cumlesi = (f"Toplamda {adet} adet {trn(P,0)} kişilik ({trn(yuk_kg,0)} kg), {tr(V)} m/s "
                         f"hızında asansör yapılması uygundur.")

    # ================================================================
    #  PAFTA BÖLÜMLERİ
    # ================================================================
    b1 = Bolum("BİNADA BULUNAN İNSAN SAYISININ TESPİTİ (B)", "MMO/697 Tablo-1")
    b1["adimlar"] = [
        veri("", "Bina tipi / hesap standardı", f"{bina_tipi} / {standart}", "", "MMO/697 Tablo-9/10"),
        veri("N", "Kat sayısı (ana giriş üstü)", N, "kat", "Projeden", 0),
        veri("Nb", "Bodrum durak adedi (ana giriş altı)", Nb, "durak", "Projeden", 0),
        veri("", "Toplam durak adedi  =  N + 1 + Nb", durak, "durak", "MMO/697 Tablo-2", 0),
        veri("", "Bina / yapı yüksekliği", f"{tr(by)} / {tr(yy)}", "m", "BYKHY md.4"),
    ]
    if Nb:
        b1["aciklamalar"].append(T.BODRUM_NOTU)
    _ac, _no = _nufus_bolunmus(bina_tipi, g.get("hizli1"), g.get("hizli2"), b,
                              nufus_satirlari)
    b1["aciklamalar"] += _ac
    b1["notlar"] += _no
    b1["adimlar"] += [
        veri("b", "Binada sürekli bulunan kişi (Σc)", b, "kişi", "MMO/697 Tablo-1"),
        veri("n", "Nüfus artış oranı (b<200 → 0,30 / b≥200 → 0,25)", n_artis, "—", "MMO/697"),
        hesap("B  =  ROUNDUP( b + ( n · b ) )",
              f"=  ROUNDUP( {trn(b,1)} + ( {tr(n_artis)} · {trn(b,1)} ) )", B, "kişi", "MMO/697", 0),
    ]

    b2 = Bolum("HESAP DEĞERLERİ", "MMO/697 Tablo-2 … Tablo-8")
    b2["adimlar"] = [
        veri("h", "Katlar arası mesafe", h, "m", "Projeden"),
        veri("", "Toplam seyahat mesafesi  =  ( N + Nb ) · h", toplam_seyahat, "m",
             "Projeden — avan kuyu yüksekliği bu değerden türer"),
        veri("V", "Kabin hızı", V, "m/s", V_kaynak),
        veri("H", "Ortalama en yüksek dönüş katı", H, "—", "MMO/697 Tablo-3", 4),
        hesap("tv  =  h / V", f"=  {tr(h)} / {tr(V)}", tv, "s", "h/V"),
        veri("S", "Ortalama durak adedi", S, "—", "MMO/697 Tablo-5", 4),
        hesap("ts  =  ta + tk + tg − tv",
              f"=  {tr(ta)} + {tr(tk)} + {tr(tg)} − {tr(tv)}", ts, "s", "MMO/697"),
        veri("P", "Kabin kişi adedi", P, "kişi", T.tablo7_kaynagi(P), 0),
        veri("p", "İndirgenmiş kişi sayısı  p = 0,8·P", p, "kişi", "MMO/697", 1),
        veri("tp", "Kişi transfer zamanı", tp, "s", _s["kaynak"]["tp"]),
        veri("ta", "Kapı açılma zamanı", ta, "s", _s["kaynak"]["ta"]),
        veri("tk", "Kapı kapanma zamanı", tk, "s", _s["kaynak"]["tk"]),
        veri("tg", "Tek katı geçme zamanı", tg, "s", _s["kaynak"]["tg"]),
    ]
    b2["notlar"] = [x for x in [V_notu] if x]

    b3 = Bolum("ASANSÖRÜN BİR SEFERİ İÇİN GEREKLİ SEYİR ZAMANI (TR)", "MMO/697 s.11-12")
    b3["adimlar"] = [
        hesap("TR  =  2·H·tv  +  ( S + 1 )·ts  +  2·p·tp",
              (f"=  2·{tr(H)}·{tr(tv)} + ( {tr(S)}+1 )·{tr(ts)} + 2·{tr(p,1)}·{tr(tp,1)}"
               if all(sayi_mi(x) for x in (H, tv, S, ts, p, tp)) else "—"),
              TR, "s", "MMO/697 s.11"),
    ]

    b4 = Bolum("GEREKLİ ASANSÖR SAYISININ HESABI", "MMO/697 s.12")
    b4["adimlar"] = [
        hesap("R  =  5 · 60 · p  /  TR",
              f"=  5·60·{tr(p,1)} / {tr(TR)}" if all(sayi_mi(x) for x in (p, TR)) else "—",
              R, "kişi / 5 dk", "MMO/697", 1),
        veri("k", "Taşınacak insan yüzdesi", k, "—", k_notu, 4),
    ]
    if all(sayi_mi(x) for x in (tasima_adedi, bekleme_adedi)):
        satir = (f"Taşıma adedi = {int(tasima_adedi)};  Bekleme adedi = {int(bekleme_adedi)}  "
                 f"(uygulanan sınır Izul = {trn(Izul,0)} sn — Tablo-10 {standart})"
                 f"  →  Nihai gerekli sayı = {adet_hesap} adet")
        if taahhut_adet is not None and not taahhut_gereksiz:
            satir += (f"   |   Taahhütname ile Şartlı Kabul sınırı ({trn(sartli,0)} sn) "
                      f"uygulandı  →  {taahhut_adet} adet")
        elif sayi_mi(sartli) and sartli:
            #  Bu sayı da İKİ ölçütü birden sağlamalıdır: taşıma kapasitesi
            #  daha çoğunu gerektiriyorsa taahhütname o eksiği kapatmaz.
            satir += (f"   |   Şartlı Kabul sınırı ({trn(sartli,0)} sn) için "
                      f"{_gerekli_adet(sartli)} adet yeterli olurdu (taahhütname gerekir)")
        b4["notlar"].append(satir)
    b4["adimlar"].append(veri("n", "Uygulanan asansör adedi", adet, "adet",
                              "Elle seçildi" if elle_adet
                              else ("Taahhütname — Tablo-10 şartlı kabul"
                                    if (taahhut_adet is not None and not taahhut_gereksiz)
                                    else "MAX[taşıma; bekleme]"), 0))

    b5 = Bolum("BEKLEME ZAMANI (Izul) KONTROLÜ", "MMO/697 Tablo-10")
    b5["adimlar"] = [
        hesap("Ieer  =  TR / n", f"=  {tr(TR)} / {adet}" if (sayi_mi(TR) and adet) else "—",
              Ieer, "s", "MMO/697", 1),
        veri("Izul", f"İzin verilen bekleme süresi ({standart})", Izul, "s", "MMO/697 Tablo-10", 0),
    ]
    sartli_uygulandi = taahhut_adet is not None and not taahhut_gereksiz
    if sartli_uygulandi:
        b5["adimlar"].append(veri("", "İzin verilen bekleme süresi (Şartlı Kabul — taahhütname ile)",
                                  sartli, "s", "MMO/697 Tablo-10", 0))
    #  BELİRLEYİCİ ÖLÇÜTLER  —  paftanın SONUÇ kutusunda gösterilir.
    #  Eskiden bu satır "Bekleme Zamanı" bölümünün dip notuydu; oysa nihai
    #  kararın DAYANAĞI odur: hangi sınır, hangi sayıyla sağlandı.  Sonuçla
    #  aynı yerde durması gerekir — bölümde Ieer ve Izul satırları zaten var.
    karar_olcutleri = []
    _gerekli_tasima = (B * k) if all(sayi_mi(x) for x in (B, k)) else None
    if all(sayi_mi(x) for x in (R, _gerekli_tasima)) and sayi_mi(adet):
        _toplam_R = R * adet
        karar_olcutleri.append({
            "ad": "Taşıma",
            "metin": (f"{int(adet)} × R = {tr(_toplam_R,1)}" if adet > 1 else f"R = {tr(R,1)}")
                     + ("  ≥  " if _toplam_R >= _gerekli_tasima else "  <  ")
                     + f"B·k = {tr(_gerekli_tasima,1)} kişi/5dk",
            "uygun": bool(_toplam_R >= _gerekli_tasima)})
    if sayi_mi(Ieer) and sayi_mi(Izul) and sartli_uygulandi and Ieer > Izul:
        #  Taahhütname verildi:  ölçüt şartlı kabul sınırıdır.  Aşılan
        #  Standart / Yükseltilmiş sınırı da aynı satırda açıkça yazılır.
        karar_olcutleri.append({
            "ad": "Bekleme",
            "metin": f"Ieer = {tr(Ieer,1)} s" + ("  ≤  " if Ieer <= sartli else "  >  ")
                     + f"Şartlı Kabul = {trn(sartli,0)} s ( taahhütname ile )   ·   "
                     f"{standart} {trn(Izul,0)} s aşılıyor",
            "uygun": bool(Ieer <= sartli)})
    elif sayi_mi(Ieer) and sayi_mi(Izul):
        ek = ""
        if sayi_mi(sartli) and sartli:
            ek = (f"   ·   Şartlı Kabul {trn(sartli,0)} sn: "
                  + ("sağlanıyor" if Ieer <= sartli else "aşılıyor"))
        karar_olcutleri.append({
            "ad": "Bekleme",
            "metin": f"Ieer = {tr(Ieer,1)} s" + ("  ≤  " if Ieer <= Izul else "  >  ")
                     + f"Izul = {trn(Izul,0)} s ( {standart} ){ek}",
            "uygun": bool(Ieer <= Izul)})

    return {
        "tip": "tek",
        "hata": hata,
        "uyarilar": U,
        "girdiler": g,
        "ozet": {
            "bina_tipi": bina_tipi, "standart": standart, "N": N, "P": P, "yuk_kg": yuk_kg,
            "bodrum": Nb, "durak": durak, "toplam_seyahat": toplam_seyahat,
            "p": p, "V": V, "V_min": V_min, "h": h, "b": b, "n_artis": n_artis, "B": B, "k": k,
            "H": H, "S": S, "ta": ta, "tk": tk, "tg": tg, "tp": tp, "tv": tv, "ts": ts,
            "TR": TR, "R": R, "Izul": Izul, "adet": adet, "adet_hesap": adet_hesap,
            #  Yalnız taahhütname adedi belirlediğinde yazılır:  seçilmeyen
            #  projelerin çıktısı ( ve altın kopyası ) bit bit aynı kalır.
            **({"taahhutname": True} if sartli_uygulandi else {}),
            "Ieer": Ieer, "sonuc": sonuc, "sonuc_cumlesi": sonuc_cumlesi,
            "esik_sartli": sartli, "esik_standart": esik_standart,
            "esik_yukseltilmis": esik_yukseltilmis,
            "kapi_genisligi": kg_, "kapi_tipi": kt,
            "tasima_adedi": tasima_adedi, "bekleme_adedi": bekleme_adedi,
            "karar_olcutleri": karar_olcutleri,
            "pafta_satiri": (hata if hata else
                             f"  {trn(P,0)} kişilik, {tr(V)} m/s hızında, {adet} adet asansör → {sonuc}"),
        },
        "nufus": nufus_satirlari,
        "bolumler": [b1, b2, b3, b4, b5],
        #  ÖNERİ TABLOSU YALNIZ GEÇERLİ BİR HESAPTA ÜRETİLİR.
        #  Tablo, kullanıcının kendi ta/tk/tg/tp değerlerini taban alır; bu
        #  değerler reddedilmişse ( ör. ts < 0 ) tablonun tamamı o geçersiz
        #  tabana dayanır.  Eskiden ana hesap dururken tablo "uygun / önerilen"
        #  satırlar basmaya devam ediyordu.
        "oneriler": ([] if hata else
                     _oneri_tablosu(N, B, k, Izul, standart, sartli,
                                    V_min, h, kg_, kt, P, ta, tk, tp, mtg, V)),
    }


#  MANUEL SÜRELERİN FİZİKSEL SINIRLARI
#  ta / tk / tg / tp bir SÜREdir: sıfır ya da negatif olamaz.  Denetimsizken
#  dördü de 0 girilince TR = 24,5 sn çıkıyor, ts = −1,88 sn gibi imkânsız bir
#  ara değer oluşuyor ve program 44 daireli binaya 2 yerine 1 asansör
#  yetiyor diyordu.  Üst sınırlar da imalatçı katalog aralığının çok
#  üstündeki yazım hatalarını ( 999 sn ) yakalar.
MANUEL_SURE_SINIRI = {
    "manuel_ta": (0.1, 30, "ta — kapı açılma süresi"),
    "manuel_tk": (0.1, 30, "tk — kapı kapanma süresi"),
    "manuel_tg": (0.1, 60, "tg — tek katı geçme süresi"),
    "manuel_tp": (0.1, 20, "tp — kişi transfer süresi"),
}


def _manuel_sure_hatasi(g, on_ek=""):
    """Elle girilmiş ta/tk/tg/tp değerlerini fiziksel sınırlara göre denetler."""
    for anahtar, (alt, ust, ad) in MANUEL_SURE_SINIRI.items():
        deger = (g or {}).get(anahtar)
        if deger in (None, ""):
            continue
        if not sayi_mi(deger) or not (alt <= deger <= ust):
            return (f"HESAP HATASI: {on_ek}{ad} elle {tr(deger)} s girilmiş — "
                    f"süre {tr(alt)} - {tr(ust)} s aralığında olmalıdır. "
                    "Sıfır ya da negatif bir süre fiziksel olarak imkânsızdır; "
                    "boş bırakırsanız tablo değeri kullanılır.")
    return None


#  BİNA GİRDİLERİ  —  tek ve çoklu hesapta AYNI kural.  ( Çoklu hesap bu
#  denetimleri hiç yapmıyordu: h = −3 m ile "Yükseltilmiş kriteri
#  karşılanıyor" sonucu üretiyordu. )
def _bina_hatasi(N, h, by, yy):
    if not (sayi_mi(N) and 1 <= N <= 30):
        return ("HESAP HATASI: ③ kat sayısı N girilmedi ya da geçersiz — "
                "1 ile 30 arasında olmalıdır.")
    if not sayi_mi(h) or not (0 < h <= 10):
        return (f"HESAP HATASI: ⑦ kat yüksekliği h = {tr(h)} m — "
                "0 ile 10 m arasında olmalıdır.")
    if not (sayi_mi(by) and by >= 0):
        return ("HESAP HATASI: ② bina yüksekliği girilmedi ya da geçersiz — "
                "hesap standardı ( Standart / Yükseltilmiş ) buna göre seçilir.")
    if not (sayi_mi(yy) and yy >= 0):
        return ("HESAP HATASI: ④ yapı yüksekliği girilmedi ya da geçersiz — "
                "hesap standardı ( Standart / Yükseltilmiş ) buna göre seçilir.")
    return None


#  HIZ BELİRLENEMEDİ  —  tek ve çoklu hesapta AYNI mesaj.
#  Hız ne seçilmiş ne de Tablo-2'den okunabilmişse Tablo-6'dan tg de
#  okunamaz.  Kullanıcıya eskiden "tg'yi elle girin" deniyordu — oysa eksik
#  olan tg değil HIZDIR:  tg, hız seçilince tablodan kendiliğinden gelir.
#  Tablo-2 yalnız Konut · Büro ve İş Merkezi · Otel gruplarını kapsar;
#  öteki bina tiplerinde asgari hız proje kararıdır.
def _hiz_yok_hatasi(bina_tipi, on_ek=""):
    return (f"HESAP HATASI: {on_ek}kabin hızı belirlenemedi — {bina_tipi} MMO/697 "
            "Tablo-2'de yoktur, asgari hız tablodan okunamaz. Kabin hızını ( V ) "
            "asansörün kendi V kutusundan ya da 'Manuel değerler' bölümündeki ortak "
            "hızdan seçin;  seçilen hız paftaya proje kararı olarak yazılır.")


def _dogrula_tek(g, b, N, P, kg_, kt, ta, tk, tg, tp, k, V, h, by, yy, k_tipi):
    """HESAPLAMA!E45 + H45 doğrulama zinciri."""
    if kg_ not in T.KAPI_GENISLIKLERI:
        return ("HESAP HATASI: ⑨ kapı genişliği listeden seçilmelidir "
                "(700/800/900/1000/1100/1200/1300 mm).")
    if sayi_mi(N) and N > 30:
        return (f"HESAP HATASI: N = {int(N)} > 30. MMO/697 Tablo-3 ve Tablo-5 en fazla 30 katı "
                "kapsar; bu yükseklikte tek bölgeli hesap geçerli değildir, bölgeli (zoned) "
                "trafik hesabı yapılmalıdır.")
    if not sayi_mi(ta) or not sayi_mi(tk):
        return (f"HESAP HATASI: {kg_} mm / {kt} için Tablo-4'te ta-tk karşılığı yok — "
                "'Kabin İçi Oto. Kat K.Ç.' sütunu 1200 ve 1300 mm'de tabloda bulunmaz. "
                "İmalatçı katalog değerini manuel ta/tk alanlarına girin ya da kapı tipini "
                "'Teleskopik Otomatik' / 'Merkezden Açılan Oto.' olarak seçin.")
    if not sayi_mi(tp):
        return (f"HESAP HATASI: {kg_} mm için tp değeri bulunamadı. "
                "İmalatçı değerini manuel tp alanına girin.")
    bt = g.get("bina_tipi") or ""
    #  HIZ YOKSA SEBEBİ SÖYLENİR  —  tg denetiminden ÖNCE.  Tablo-2 hızı
    #  durak adedinden okur:  kat sayısı eksikse sebep odur;  değilse bina
    #  tipi Tablo-2'de yoktur ( bkz. _hiz_yok_hatasi ).
    if not sayi_mi(V):
        if not (sayi_mi(N) and 1 <= N <= 30):
            return _bina_hatasi(N, h, by, yy)                    # ③ kat sayısı
        return _hiz_yok_hatasi(bt)
    if not sayi_mi(tg):
        return f"HESAP HATASI: V = {tr(V)} m/s için Tablo-6'da tg değeri yok. tg'yi elle girin."
    nufus_h = _nufus_girdi_hatasi(bt, g.get("hizli1"), g.get("hizli2"))
    if nufus_h:
        return nufus_h
    if not sayi_mi(b) or b <= 0:
        return "HESAP HATASI: Nüfus girilmedi — ⑤ (ve gerekiyorsa ⑥) kutusunu doldurun"
    if k_tipi is not None and not bt.startswith("Kamu") and sayi_mi(g.get("manuel_k")):
        return "HESAP HATASI: Tablo-9 varken manuel k girilemez"
    if T.kapsam_disi(N, P):
        return "HESAP HATASI: P/N aralık dışı (P: 6-34 kişi, N: 1-30 kat)"
    nb = g.get("bodrum")
    if nb not in (None, "") and _bodrum_oku(nb)[1]:
        return _bodrum_oku(nb)[1]
    bina = _bina_hatasi(N, h, by, yy)
    if bina:
        return bina
    #  DURAK ADEDİ  —  çokluyla aynı kural.  Tek hesap yolunda tanımlı
    #  asansörlerin hepsi AYNI TİPTİR, dolayısıyla en yüksek durağa çıkan da
    #  onlardır:  durak adedi N + 1 olmalıdır.  ( Çoklu yol bunu
    #  "kat sayısı N, aktif asansörlerin en yüksek durak sayısına göre
    #  girilmelidir" diye reddediyordu; tek yol alanı hiç okumuyordu. )
    Ni, d_hata = _durak_oku(g.get("durak"), N)
    if d_hata:
        return d_hata
    if sayi_mi(Ni) and sayi_mi(N) and Ni != N:
        return (f"HESAP HATASI: durak adedi {int(Ni) + 1} girilmiş; asansör ana giriş "
                f"üstündeki {int(N)} katın tümüne hizmet ettiğinden durak adedi "
                f"N + 1 = {int(N) + 1} olmalıdır. Asansör daha az durakta duruyorsa "
                "③ kat sayısı N'yi o asansöre göre girin ya da durak alanını boşaltın.")
    sure = _manuel_sure_hatasi(g)
    if sure:
        return sure
    kontroller = [
        (P in T.GECERLI_KAPASITELER),
        (sayi_mi(k) and 0 < k <= 1), (sayi_mi(V) and V > 0),
    ]
    if not all(kontroller):
        return "HESAP HATASI: girdileri ve tablo eşleşmelerini kontrol edin"
    if sayi_mi(h) and not (2 <= h <= 6):
        pass  # yalnız uyarı — hesabı durdurmaz
    return None


def _oneri_tablosu(N, B, k, Izul, standart, esik_sartli,
                   V_min, h, kg_, kt, P_secili, ta_secili, tk_secili, tp_secili,
                   manuel_tg, V_secili):
    """
    HESAPLAMA 6) OTOMATİK ÖNERİ bloğu (satır 70-83).
    7 kapasite × 2 hız (Tablo-2 minimumu + bir üst hız).
    """
    if not all(sayi_mi(x) for x in (N, B, k, Izul, h)) or V_min is None:
        return []
    V_ust = T.bir_ust_hiz(V_min)
    satirlar = []
    for kap in (6, 8, 10, 13, 16, 20, 25):
        for V, etiket in ((V_min, "Tablo-2 min"), (V_ust, "bir üst hız")):
            # kapasiteye uygun kapı genişliği — ISO 8100-32:2020 Ek C, Tablo 8
            W = kg_ if kap == P_secili else (800 if kap <= 8 else 900 if kap <= 10
                                             else 1100 if kap <= 20 else 1300)
            if W == kg_:
                ta, tk, tp = ta_secili, tk_secili, tp_secili
            else:
                ta, tk = T.tablo4_ta_tk(W, kt)
                tp = T.tablo8_tp(W)
            tg = manuel_tg if (sayi_mi(manuel_tg) and V == V_secili) else T.tablo6_tg(V)
            H = T.tablo3_H(N, kap)
            S = T.tablo5_S(N, kap)
            if not all(sayi_mi(x) for x in (H, S, ta, tk, tg, tp, V)) or not V:
                continue
            tv = h / V
            ts = ta + tk + tg - tv
            #  ts FİZİKSEL BİR SÜREDİR.  Elle girilmiş ta/tk/tg değerleri kabinin
            #  bir katı geçme süresinden küçük kalınca ts negatif çıkar; ana hesap
            #  bunu reddediyordu ( bkz. _ts_hatasi ) ama öneri tablosu aynı
            #  sürelerle "uygun" satırlar üretmeye devam ediyordu.
            if ts <= 0:
                continue
            TR = 2 * H * tv + (S + 1) * ts + 2 * (0.8 * kap) * tp
            if TR <= 0:
                continue
            R = 300 * 0.8 * kap / TR
            tas = yukari_yuvarla(B * k / R, 0)        # taşıma kapasitesinin istediği adet
            adet = int(max(1, tas, yukari_yuvarla(TR / Izul, 0)))
            Ieer = TR / adet
            #  ADET ZATEN HER İKİ ÖLÇÜTÜ SAĞLAYACAK ŞEKİLDE SEÇİLİYOR, bu yüzden
            #  Ieer ≤ Izul bir SINIFLANDIRMA değil, bir ÖZDEŞLİKTİR.  Burada eskiden
            #  "Şartlı kabul" ve "Kriteri aşıyor" dalları vardı;  25.116 üretilmiş
            #  satırın hiçbirinde çalışmadılar — çalışamazlar da, çünkü adedi
            #  artırmak Ieer'i her zaman düşürür.  ( İkisi de aynı sıralama
            #  anahtarını aldığından, çalışsalardı kriteri AŞAN bir seçenek şartlı
            #  kabul edilebilir olanın önüne geçebilirdi. )
            #
            #  ŞARTLI KABULÜN GERÇEK KARŞILIĞI ŞU SORUDUR:  taahhütnameyle
            #  ( MMO/697 Tablo-10 şartlı sınırı ) bu seçenek DAHA AZ asansörle
            #  yapılabilir miydi?  Taahhütname yalnız BEKLEME süresini gevşetir —
            #  taşıma kapasitesi ölçütü aynen durur;  bu yüzden alt sınır yine
            #  `tas`tır.  ( hesapla_tek içindeki _gerekli_adet ile birebir aynı kural. )
            sinif = f"{standart} ✔"
            adet_sartli = None
            if sayi_mi(esik_sartli) and esik_sartli and esik_sartli > Izul:
                _as = int(max(1, tas, yukari_yuvarla(TR / esik_sartli, 0)))
                if _as < adet:
                    adet_sartli = _as
                    sinif += f"  ·  şartlı kabulle {_as} adet (taahhütname)"
            # TS EN 81-70 / TS 9111 erişilebilirlik ölçütünü karşılamayan seçenek
            # (630 kg altı kabin veya 800 mm altı kapı) sıralamaya alınmaz.
            erisim = T.erisilebilir_mi(kap, W)
            siralama = 999_999_999 if not erisim else adet * 10_000 + kap * 10
            satirlar.append({
                "secenek": (f"{kap} kişilik ({trn(T.tablo7_yuk(kap),0)} kg) — {tr(V)} m/s"
                            f"  ·  {W} mm kapı ({etiket})"
                            + ("" if erisim else "  ⚠ TS EN 81-70 erişilebilirlik ölçütü dışı")),
                "kapasite": kap, "V": V, "kapi": W, "adet": adet, "Ieer": Ieer,
                "adet_sartli": adet_sartli,
                "sinif": sinif, "TR": TR, "R": R, "_siralama": siralama,
                "erisilebilir": erisim,
            })
    if satirlar:
        en_iyi = min(satirlar, key=lambda s: s["_siralama"])
        if en_iyi["_siralama"] < 999_999_999:
            en_iyi["onerilen"] = True
    return satirlar


# =====================================================================
#  ÇOKLU ASANSÖR   —   ÇOKLU ASANSÖR sayfası  ->  PAFTA-COKLU
# =====================================================================
def hesapla_coklu(g: dict) -> dict:
    """
    g: bina_tipi, bina_yuksekligi, yapi_yuksekligi, N, hizli1, hizli2, h,
       bodrum (ortak), manuel_k, manuel_V (ortak), ek_nufus[],
       asansorler: [{P, kapi_genisligi, kapi_tipi, V, durak, h, bodrum,
                     manuel_ta, manuel_tk, manuel_tg, manuel_tp}, ...]  (1-4 adet)
    """
    U, hata = [], None
    bina_tipi = g.get("bina_tipi")
    if not isinstance(bina_tipi, str):
        bina_tipi = str(bina_tipi) if bina_tipi is not None else ""
    t10 = T.TABLO_10.get(bina_tipi)
    if t10 is None:
        return {"hata": "HESAP HATASI: Bina tipi listeden seçilmelidir."}

    N  = g.get("N")
    h  = g.get("h")
    by = g.get("bina_yuksekligi")
    yy = g.get("yapi_yuksekligi")
    Nb_ortak, Nb_hata = _bodrum_oku(g.get("bodrum"))
    if Nb_hata:
        hata = Nb_hata

    #  BİNA GİRDİLERİ  —  tek asansör hesabıyla AYNI denetim zinciri.
    #  ( Bu blok yokken h = −3 m, h = 0, h = 99 ya da boş bırakılmış bina /
    #    yapı yüksekliği çokluda hata vermeden geçiyordu: yükseklikler boşken
    #    hesap sessizce "Standart" sınıfına düşüyordu. )
    bina = _bina_hatasi(N, h, by, yy)
    if bina:
        return {"hata": bina}
    #  Ortak manuel süreler + asansör bazında girilenler
    sure = _manuel_sure_hatasi(g)
    if sure:
        return {"hata": sure}
    for i, a in enumerate(g.get("asansorler") or [], 1):
        sure = _manuel_sure_hatasi(a, on_ek=f"ASANSÖR-{i} — ")
        if sure:
            return {"hata": sure}

    standart = _hesap_standardi(by, yy)
    hiz_grubu = t10["hiz_grubu"]
    k_tipi = t10["k_tipi"]

    nufus_satirlari, b = _nufus_satirlari(bina_tipi, g.get("hizli1"), g.get("hizli2"),
                                          g.get("ek_nufus"))
    n_artis = 0.3 if (b or 0) < 200 else 0.25
    B = yukari_yuvarla(b * (1 + n_artis), 0) if sayi_mi(b) else None

    manuel_k = g.get("manuel_k")
    if bina_tipi.startswith("Kamu") and sayi_mi(manuel_k) and 0 < manuel_k <= 1:
        k, k_notu = manuel_k, "Manuel giriş"
    elif k_tipi is None:
        if sayi_mi(manuel_k) and 0 < manuel_k <= 1:
            k, k_notu = manuel_k, "Manuel giriş (Tablo-9'da bu bina tipi yok)"
        else:
            k, k_notu = None, "Manuel k gerekli"
    else:
        #  Tablo-9'da değeri olan bir bina tipinde manuel k SESSİZCE yok
        #  sayılmamalıdır — tek asansör hesabında olduğu gibi burada da
        #  açıkça reddedilir.  ( Aksi hâlde kullanıcı bir değer yazar, program
        #  onu görmezden gelir ve hiçbir şey söylemezdi. )
        if sayi_mi(manuel_k):
            return {"hata": "HESAP HATASI: Tablo-9 varken manuel k girilemez"}
        k, k_notu = T.TABLO_9[k_tipi][standart], "MMO/697 Tablo-9"
        if bina_tipi.startswith("Kamu"):
            k_notu = "Tablo-9'da kamu yok → İş Merkezi %k varsayıldı"
            U.append("Kamu binaları MMO/697 Tablo-9'da yoktur; %k için İŞ MERKEZİ "
                     "satırı varsayılmıştır. Farklı bir oran gerekiyorsa manuel k girin.")
    if bina_tipi.startswith("Kamu"):
        U.append("Kamu binaları MMO/697 Tablo-2'de de yoktur; asgari hız için "
                 "BÜRO VE İŞ MERKEZİ grubu varsayılmıştır. Bu iki varsayım paftaya "
                 "yazılmıştır.")

    durak_ortak = (N + 1 + Nb_ortak) if sayi_mi(N) else None
    V_grup_min = T.tablo2_min_hiz(hiz_grubu, durak_ortak) if (hiz_grubu and durak_ortak) else None
    manuel_V = g.get("manuel_V")
    #  Ortak manuel hız da tek hesaptaki gibi GEÇERLİ LİSTEDEN olmalıdır.
    if sayi_mi(manuel_V) and manuel_V not in T.GECERLI_HIZLAR:
        return {"hata": "HESAP HATASI: Manuel hız geçersiz — listeden seçin "
                        "(0,63 / 1 / 1,6 / 1,75 / 2 / 2,5 / 3 / 3,5 / 5 / 6 m/s)"}
    V_ortak = manuel_V if sayi_mi(manuel_V) else V_grup_min

    girisler = [a for a in (g.get("asansorler") or []) if sayi_mi(a.get("P"))]
    if not girisler:
        hata = "HESAP HATASI: en az bir asansör girin"

    asansorler = []
    for i, a in enumerate(girisler, 1):
        P = a.get("P")
        kg_ = a.get("kapi_genisligi")
        kt = a.get("kapi_tipi")
        # durak sayısı (ana giriş dâhil) — boşsa ortak N+1
        Ni, d_hata = _durak_oku(a.get("durak"), N)
        if d_hata:
            hata = hata or d_hata
        hi = a.get("h") if sayi_mi(a.get("h")) else h
        #  ASANSÖRE ÖZEL KAT YÜKSEKLİĞİ de ortak h ile AYNI sınırlara tabidir.
        #  ( Denetimsizken h = −3 m kabul ediliyor, seyahat mesafesi −33 m
        #    çıkıyor ve grup "Yükseltilmiş kriteri karşılanıyor" diyordu. )
        if a.get("h") not in (None, "") and not (sayi_mi(hi) and 0 < hi <= 10):
            hata = hata or (f"HESAP HATASI: ASANSÖR-{i} — kat yüksekliği h = {tr(a.get('h'))} m; "
                            "0 ile 10 m arasında olmalıdır.")
        # bodrum: asansör bazında; boş bırakılırsa ortak değer kullanılır
        if a.get("bodrum") in (None, ""):
            Nbi = Nb_ortak
        else:
            Nbi, nb_h = _bodrum_oku(a.get("bodrum"))
            if nb_h:
                hata = hata or f"HESAP HATASI: ASANSÖR-{i} — " + nb_h.split(": ", 1)[-1]
        Vmin_i = (T.tablo2_min_hiz(hiz_grubu, (Ni + 1 + Nbi))
                  if (hiz_grubu and sayi_mi(Ni)) else None)
        Vi_in = a.get("V")
        if sayi_mi(Vi_in) and Vi_in not in T.GECERLI_HIZLAR:
            hata = hata or "HESAP HATASI: Manuel V geçersiz — geçerli hız listesinden seçin"
            Vi = None
        else:
            #  HIZ ÖNCELİĞİ  —  tek hesapla AYNI:
            #     1) asansörün kendi V'si   2) ORTAK manuel hız
            #     3) o asansörün Tablo-2 minimumu   4) grup Tablo-2 minimumu
            #  Ortak manuel hız eskiden yalnız 3 ve 4 yoksa devreye giriyordu:
            #  arayüzde 2,50 m/s seçiliyken iki asansör de 1,60 m/s hesaplanıyordu.
            Vi = (Vi_in if sayi_mi(Vi_in)
                  else manuel_V if sayi_mi(manuel_V)
                  else Vmin_i if sayi_mi(Vmin_i) else V_ortak)
        if sayi_mi(Vi) and sayi_mi(Vmin_i) and Vi < Vmin_i:
            U.append(f"⚠ ASANSÖR-{i}: seçilen {tr(Vi)} m/s, Tablo-2 minimumu {tr(Vmin_i)} m/s "
                     "altındadır — bekleme kriteri esas alındı, gerekçeyi paftaya yazın.")

        # ---- süreler: tablo değeri, imalatçı verisi varsa onunla ezilir
        _s = _sure_cozumle(a, kg_, kt, Vi, P, on_ek=f"ASANSÖR-{i}: ")
        ta, tk, tg, tp = _s["ta"], _s["tk"], _s["tg"], _s["tp"]
        elle_i = _s["elle"]
        U += _s["uyarilar"]
        H = T.tablo3_H(Ni, P) if (sayi_mi(Ni) and sayi_mi(P)) else None
        S = T.tablo5_S(Ni, P) if (sayi_mi(Ni) and sayi_mi(P)) else None
        p = 0.8 * P if sayi_mi(P) else None
        tv = hi / Vi if (sayi_mi(hi) and sayi_mi(Vi) and Vi) else None
        ts = (ta + tk + tg - tv) if all(sayi_mi(x) for x in (ta, tk, tg, tv)) else None
        TR = (2 * H * tv + (S + 1) * ts + 2 * p * tp) \
            if all(sayi_mi(x) for x in (H, tv, S, ts, p, tp)) else None
        R = (300 * p / TR) if (sayi_mi(TR) and TR) else None
        hata = hata or _ts_hatasi(ts, ta, tk, tg, tv, on_ek=f"ASANSÖR-{i} — ")

        if not sayi_mi(ta) or not sayi_mi(tk):
            hata = hata or (f"HESAP HATASI: ASANSÖR-{i} — {kg_} mm / {kt} için Tablo-4'te ta-tk "
                            "karşılığı yok ('Kabin İçi Oto. Kat K.Ç.' sütunu 1200 ve 1300 mm'de "
                            "tabloda bulunmaz). İmalatçı değerini manuel ta/tk alanlarına girin.")
        if not sayi_mi(tp):
            hata = hata or (f"HESAP HATASI: ASANSÖR-{i} — {kg_} mm için tp değeri bulunamadı; "
                            "imalatçı değerini manuel tp alanına girin.")
        #  Hız yoksa tg de yoktur — eksik olan HIZDIR ( bkz. _hiz_yok_hatasi ).
        #  Kat sayısı bu yolda en başta denetlenir;  buraya gelindiyse sebep
        #  bina tipinin Tablo-2'de olmamasıdır.
        if not sayi_mi(Vi):
            hata = hata or _hiz_yok_hatasi(bina_tipi, on_ek=f"ASANSÖR-{i} — ")
        elif not sayi_mi(tg):
            hata = hata or (f"HESAP HATASI: ASANSÖR-{i} — hızı için Tablo-6'da tg değeri yok; "
                            "manuel tg girin.")
        if T.kapsam_disi(Ni, P):
            hata = hata or f"HESAP HATASI: ASANSÖR-{i} — P/N aralık dışı (P: 6-34, N: 1-30)"
        #  KAPASİTE TABLO-7'DE OLMALIDIR  —  tek hesap yolunda ( _dogrula_tek )
        #  zaten aranıyordu, çokluda aranmıyordu:  P = 7 sessizce geçiyor,
        #  Q = 7 × 75 = 525 kg türetiliyor ve pafta bu değere kaynak olarak
        #  "Tablo-7" yazıyordu — tabloda böyle bir satır YOK.
        if P not in T.GECERLI_KAPASITELER:
            hata = hata or (
                f"HESAP HATASI: ASANSÖR-{i} — kabin kapasitesi P = {trn(P, 0)} kişi "
                "MMO/697 Tablo-7'de yoktur; listedeki kapasitelerden birini seçin ( "
                + " / ".join(str(x) for x in T.GECERLI_KAPASITELER) + " kişi ).")

        asansorler.append({
            "no": i, "ad": f"ASANSÖR-{i}", "P": P, "yuk_kg": T.tablo7_yuk(P),
            "kapi_genisligi": kg_, "kapi_tipi": kt, "N": Ni,
            "durak": (Ni + 1) if sayi_mi(Ni) else None,
            "bodrum": Nbi,
            "durak_toplam": (Ni + 1 + Nbi) if sayi_mi(Ni) else None,
            "toplam_seyahat": ((Ni + Nbi) * hi) if (sayi_mi(Ni) and sayi_mi(hi)) else None,
            "h": hi, "V": Vi, "V_min": Vmin_i, "p": p, "H": H, "S": S,
            "ta": ta, "tk": tk, "tg": tg, "tp": tp, "tv": tv, "ts": ts, "TR": TR, "R": R,
            "elle_sure": elle_i,
            "kaynak_ta": _s["kaynak"]["ta"],
            "kaynak_tk": _s["kaynak"]["tk"],
            "kaynak_tg": _s["kaynak"]["tg"],
            "kaynak_tp": _s["kaynak"]["tp"],
            "kaynak_P": T.tablo7_kaynagi(P),
        })

    if sayi_mi(N) and N > 30:
        hata = (f"HESAP HATASI: N = {int(N)} > 30. MMO/697 Tablo-3 ve Tablo-5 en fazla 30 katı "
                "kapsar; bu yükseklikte bölgeli (zoned) trafik hesabı gerekir.")
    hata = hata or _nufus_girdi_hatasi(bina_tipi, g.get("hizli1"), g.get("hizli2"))
    if not sayi_mi(b) or b <= 0:
        hata = hata or "HESAP HATASI: Nüfus girilmedi — ⑤/⑥ kutularını doldurun"
    if not sayi_mi(k) or not (0 < k <= 1):
        hata = hata or "HESAP HATASI: k değeri geçersiz — Tablo-9'da yoksa manuel k girin"
    #  BÖLGELİ HİZMET  —  MMO/697'de zoned trafik yöntemi YOKTUR.
    #  Grup kontrolü Reş = ΣRi ≥ B·k, bütün asansörlerin AYNI talebe hizmet
    #  ettiğini varsayar.  Asansörler farklı katlara çıkıyorsa bu varsayım
    #  kırılır:  yalnız alt katlara çalışan bir asansörün kapasitesi, üst
    #  katların talebine sayılamaz.  ( Ölçüldü:  20 kata çıkan A1 ile 2 durakta
    #  duran A2 grubunda Reş = 89,96 ≥ B·k = 75 çıkıp "kriter karşılanıyor"
    #  deniyor, oysa üst katlara yalnız A1 çıkıyor ve tek başına R = 18,32. )
    #  Program bölge hesabı YAPMAZ; varsayımı açıkça söyler.
    _bolgeler = sorted({a["N"] for a in asansorler if sayi_mi(a.get("N"))})
    if len(_bolgeler) > 1:
        U.append(
            "⚠ Asansörler FARKLI KATLARA hizmet ediyor ( ana giriş üstü kat adedi: "
            + " / ".join(str(int(x)) for x in _bolgeler)
            + " ). Grup kontrolü ( Reş = ΣRi ≥ B·k ) bütün asansörlerin AYNI talebe "
              "hizmet ettiğini varsayar; MMO/697'de bölgeli ( zoned ) trafik yöntemi "
              "yoktur. Üst bölgeye çıkmayan asansörün kapasitesi o bölgenin talebini "
              "karşılamaz — nüfusu ve talebi bölgelere elle ayırıp her bölgeyi ayrı "
              "hesaplayın, gerekçesini paftaya yazın.")

    if asansorler and sayi_mi(N):
        en_yuksek = max((a["N"] for a in asansorler if sayi_mi(a["N"])), default=None)
        if en_yuksek is not None and en_yuksek != N:
            hata = hata or ("HESAP HATASI: kat sayısı N, aktif asansörlerin en yüksek durak "
                            "sayısına göre girilmelidir")

    # ---- grup kontrolü (MMO/697 s.12)
    Res = sum(a["R"] for a in asansorler if sayi_mi(a["R"])) if not hata else None
    gereken = (B * k) if all(sayi_mi(x) for x in (B, k)) else None
    ters_toplam = sum(1 / a["TR"] for a in asansorler if sayi_mi(a["TR"]) and a["TR"]) if not hata else None
    TRes = (1 / ters_toplam) if (sayi_mi(ters_toplam) and ters_toplam) else None
    Izul = t10["yukseltilmis"] if standart == "Yükseltilmiş" else t10["standart"]
    sartli = t10["sartli"]

    if hata:
        sonuc = hata
    elif not all(sayi_mi(x) for x in (Res, gereken, TRes)):
        sonuc = "HESAP HATASI: grup değerleri hesaplanamadı"
    elif Res < gereken:
        sonuc = "YETERSİZ — taşıma kapasitesi düşük (Reş<B·k)"
    elif TRes <= Izul:
        sonuc = f"{standart} kriteri karşılanıyor"
    elif sayi_mi(sartli) and sartli and TRes <= sartli:
        sonuc = "Şartlı Kabul (taahhütname ile)"
    else:
        sonuc = "Kabul Edilmez — bekleme süresi şartlı sınırı aşıyor"

    pafta_satiri = hata or ("  " + "  +  ".join(
        f"1 adet {trn(a['P'],0)} kişilik {tr(a['V'])} m/s" for a in asansorler)
        + f"  →  {len(asansorler)} adet asansör  →  {sonuc}")

    # ---- bölümler
    b1 = Bolum("ORTAK BİNA BİLGİLERİ", "MMO/697 Tablo-1")
    b1["adimlar"] = [
        veri("", "Bina tipi / hesap standardı", f"{bina_tipi} / {standart}", "", "MMO/697 Tablo-9/10"),
        veri("N", "Kat sayısı (ana giriş üstü) — grup maksimumu", N, "kat", "Projeden", 0),
        veri("Nb", "Bodrum durak adedi (ana giriş altı) — ortak", Nb_ortak, "durak", "Projeden", 0),
        veri("", "Bina / yapı yüksekliği", f"{tr(by)} / {tr(yy)}", "m", "BYKHY md.4"),
        veri("b", "Binada sürekli bulunan kişi (Σc)", b, "kişi", "MMO/697 Tablo-1"),
        veri("n", "Nüfus artış oranı", n_artis, "—", "MMO/697"),
        hesap("B  =  ROUNDUP( b + ( n · b ) )",
              f"=  ROUNDUP( {trn(b,1)} + ( {tr(n_artis)} · {trn(b,1)} ) )",
              B, "kişi", "MMO/697", 0),
        veri("k", "Taşınacak insan yüzdesi", k, "—", k_notu, 4),
    ]
    _ac, _no = _nufus_bolunmus(bina_tipi, g.get("hizli1"), g.get("hizli2"), b,
                              nufus_satirlari)
    b1["aciklamalar"] = _ac
    b1["notlar"] = _no
    if Nb_ortak or any(a.get("bodrum") for a in asansorler):
        b1["aciklamalar"].insert(0, T.BODRUM_NOTU)

    b3 = Bolum("GRUP KONTROLÜ", "MMO/697 s.12 — farklı kapasiteli asansörler")
    b3["aciklamalar"] = ["Reş = ΣRi ≥ B·k    ve    1/TReş = Σ(1/TRi),  TReş ≤ Izul"]
    #  BELİRLEYİCİ ÖLÇÜTLER  —  bölüm dip notu değil, SONUÇ kutusunun dayanağı.
    karar_olcutleri = []
    if not hata and all(sayi_mi(x) for x in (Res, gereken, TRes)):
        karar_olcutleri = [
            {"ad": "Taşıma",
             "metin": "Reş = " + " + ".join(f"R{a['no']}={tr(a['R'],1)}" for a in asansorler)
                      + f" = {tr(Res,1)}" + ("  ≥  " if Res >= gereken else "  <  ")
                      + f"B·k = {tr(gereken,1)} kişi/5dk",
             "uygun": bool(Res >= gereken)},
            {"ad": "Bekleme",
             "metin": "1/TReş = " + " + ".join(f"1/{tr(a['TR'],1)}" for a in asansorler)
                      + f"  →  TReş = {tr(TRes,1)} s" + ("  ≤  " if TRes <= Izul else "  >  ")
                      + f"Izul = {trn(Izul,0)} s ( {standart} )",
             "uygun": bool(TRes <= Izul)},
        ]
    b3["adimlar"] = [
        veri("Reş", "Grubun 5 dk taşıma kapasitesi = ΣR", Res, "kişi/5dk", "MMO/697 s.12", 1),
        veri("B·k", "Gerekli taşıma kapasitesi", gereken, "kişi/5dk", "MMO/697", 1),
        veri("1/TReş", "Ters tur süreleri toplamı = Σ(1/TR)", ters_toplam, "1/s", "MMO/697 s.12", 6),
        veri("TReş", "Grup efektif tur süresi ( = Ieer )", TRes, "s", "MMO/697 s.12", 1),
        veri("Izul", f"İzin verilen bekleme süresi ({standart})", Izul, "s", "MMO/697 Tablo-10", 0),
        veri("n", "Kullanılan asansör adedi", len(asansorler), "adet", "Projeden", 0),
    ]

    return {
        "tip": "coklu",
        "hata": hata,
        "uyarilar": U,
        "girdiler": g,
        "ozet": {
            "bina_tipi": bina_tipi, "standart": standart, "N": N, "h": h,
            "bodrum": Nb_ortak, "durak": durak_ortak,
            "b": b, "n_artis": n_artis, "B": B, "k": k,
            "Res": Res, "gereken": gereken, "TRes": TRes, "Izul": Izul,
            "karar_olcutleri": karar_olcutleri,
            "esik_sartli": sartli, "esik_standart": t10["standart"],
            "esik_yukseltilmis": t10["yukseltilmis"],
            "adet": len(asansorler), "sonuc": sonuc, "pafta_satiri": pafta_satiri,
            "V_grup_min": V_grup_min,
        },
        "asansorler": asansorler,
        "nufus": nufus_satirlari,
        "bolumler": [b1, b3],
    }


# =====================================================================
#  TRAFİK  →  AVAN  KÖPRÜSÜ
# =====================================================================
def trafik_ozeti(sonuc: dict) -> dict:
    """
    Trafik hesabının avan tarafını ilgilendiren küçük özeti.
    Avan hesabı bunu alıp kapasite / hız / kuyu yüksekliği tutarlılığını
    denetler; böylece trafikte yapılan bir revizyon avan sekmesinde sessizce
    eski değerle kalmaz.
    """
    if not isinstance(sonuc, dict) or sonuc.get("hata"):
        return {}
    o = sonuc.get("ozet") or {}
    if sonuc.get("tip") == "tek":
        n = o.get("adet") or 1
        bir = {"P": o.get("P"), "V": o.get("V"), "toplam_seyahat": o.get("toplam_seyahat")}
        return {"tip": "tek", "N": o.get("N"), "bodrum": o.get("bodrum"), "h": o.get("h"),
                "adet": n, "asansorler": [dict(bir) for _ in range(int(n) if sayi_mi(n) else 1)]}
    if sonuc.get("tip") == "coklu":
        return {"tip": "coklu", "N": o.get("N"), "bodrum": o.get("bodrum"), "h": o.get("h"),
                "adet": o.get("adet"),
                "asansorler": [{"P": a.get("P"), "V": a.get("V"),
                                "toplam_seyahat": a.get("toplam_seyahat")}
                               for a in (sonuc.get("asansorler") or [])]}
    return {}


# =====================================================================
#  TEK GİRİŞ  —  YÖNTEMİ VERİ BELİRLER
#
#  Kullanıcı artık "tek mi çoklu mu" seçmez: binayı ve planladığı
#  asansör(ler)i tanımlar, yöntemi program çıkarır.
#
#      hepsi AYNI tipse   →  hesapla_tek( manuel_adet = tanımlanan adet )
#                            ( HESAPLAMA → PAFTA;  "kaç gerekir" de söylenir )
#      farklı tip varsa   →  hesapla_coklu
#                            ( ÇOKLU ASANSÖR → PAFTA-COKLU )
#
#  İki yolun ÖZDEŞ asansörlerde aynı sonucu verdiği ölçüldü:
#      ΣRi = n·R   ve   1/TReş = Σ(1/TRi) = n/TR   →   TReş = TR/n
#  ( fark 0,00e+00 ).  Yani seçim doğruluğu değil, BELGEYİ belirler:
#  PAFTA türetmeyi adım adım gösterir, PAFTA-COKLU asansör bazında tablo verir.
# =====================================================================

#  Asansörleri "aynı tip" yapan alanlar.  Biri bile farklıysa her asansörün
#  kendi H, S, ts, TR'si olur ve grup ( çoklu ) yolu gerekir.
OZDESLIK_ALANLARI = ("P", "kapi_genisligi", "kapi_tipi", "V", "durak", "h",
                     "bodrum", "manuel_ta", "manuel_tk", "manuel_tg", "manuel_tp")


def _bos(x):
    return x is None or (isinstance(x, str) and not x.strip())


def _ayni(x, y):
    if _bos(x) and _bos(y):
        return True
    if _bos(x) or _bos(y):
        return False
    if sayi_mi(x) and sayi_mi(y):
        return abs(float(x) - float(y)) < 1e-9
    return str(x).strip() == str(y).strip()


def ozdes_mi(asansorler) -> bool:
    """Tanımlı asansörlerin hepsi aynı tip mi?  ( 0 ya da 1 asansör → evet )"""
    liste = [a for a in (asansorler or []) if isinstance(a, dict)]
    if len(liste) <= 1:
        return True
    ilk = liste[0]
    return all(_ayni(ilk.get(k), a.get(k)) for a in liste[1:] for k in OZDESLIK_ALANLARI)


def tekil_girdi(g: dict):
    """
    ÖZDEŞ asansör listesini, HESAPLAMA sayfasının beklediği DÜZ girdi biçimine
    çevirir ( P / kapı / süreler / adet üst seviyeye taşınır ).

    Arayüz girdileri `asansorler` listesinde gönderir;  tek asansör yolu
    düz alanları bekler.  Eşleme yalnız burada yapılır.

    Dönen:  düz girdi sözlüğü;  asansörler ÖZDEŞ DEĞİLSE None ( çoklu yol ).
    """
    g = g if isinstance(g, dict) else {}
    liste = [a for a in (g.get("asansorler") or []) if isinstance(a, dict)]
    #  Kapasitesi girilmemiş kolon "tanımlanmamış" sayılır.
    liste = [a for a in liste if not _bos(a.get("P"))]
    if not ozdes_mi(liste):
        return None

    bir = dict(liste[0]) if liste else {}
    tekil = dict(g)
    tekil.pop("asansorler", None)
    for k in ("P", "kapi_genisligi", "kapi_tipi", "durak",
              "manuel_ta", "manuel_tk", "manuel_tg", "manuel_tp"):
        if not _bos(bir.get(k)):
            tekil[k] = bir[k]
    #  Asansör bazında verilen h / bodrum / V ortak değeri ezer.
    for kaynak, hedef in (("h", "h"), ("bodrum", "bodrum"), ("V", "manuel_V")):
        if not _bos(bir.get(kaynak)):
            tekil[hedef] = bir[kaynak]
    #  TEK KOLON  =  "boyutlandır"  :  adet verilmez, program
    #     n = MAX[ taşıma ; bekleme ] ile kaç gerektiğini söyler.
    #  İKİ VE DAHA FAZLA KOLON  =  "doğrula"  :  tanımlanan adet
    #     uygulanan adettir; program ayrıca gerekli adedi ( adet_hesap )
    #     yine hesaplar, böylece fazla/eksik olduğu görünür.
    if len(liste) >= 2:
        tekil["manuel_adet"] = len(liste)
    return tekil


def hesapla(g: dict) -> dict:
    """
    Tek giriş noktası.  `g` içinde bina girdileri ve `asansorler` listesi bulunur.
    Dönen sözlüğe iki alan eklenir:

        yol    : "tek" | "coklu"      —  kullanılan hesap yolu
    """
    tekil = tekil_girdi(g)
    if tekil is not None:
        s = hesapla_tek(tekil)
        s["yol"] = "tek"
        return s

    s = hesapla_coklu(g if isinstance(g, dict) else {})
    s["yol"] = "coklu"
    return s

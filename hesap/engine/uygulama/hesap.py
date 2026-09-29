# -*- coding: utf-8 -*-
"""
UYGULAMA PROJESİ HESAP MOTORU        ( orkestratör )

Kendi başına HESAP YAPMAZ.  İki mevcut motoru tek girdi setiyle koşturur ve
sonuçlarını tek çıktıda birleştirir:

    engine/mukavemet.py     10 bölüm  —  mukavemet
    engine/avan.py          3-6. bölümler  —  kabin ve kuyu aydınlatması,
                            kurulu güç cetveli, gerilim düşümü ve kesit
                            kontrolü;  ayrıca makine dairesi aydınlatması
                            ve temel topraklama

NİÇİN AVAN MOTORU YENİDEN YAZILMADI:  bu dört hesap avan projesinde zaten
var ve doğrulanmış durumda ( TEST 1 · 6 · 7 ).  Kopyalamak ikinci bir
doğruluk kaynağı yaratır ve ikisi zamanla ayrışır.  Burada yapılan tek şey
ORTAK GİRDİYİ KÖPRÜLEMEK ( engine/uygulama_girdi.kopru ).

AVANIN 1. VE 2. BÖLÜMÜ ALINMAZ:
  · Motor gücü — mukavemet bölüm 1 aynı hesabı MMO 208/7 §2.4'e göre yapar.
    İkisini birden basmak paftada iki farklı motor gücü gösterirdi.
  · Kuvvet hesapları — mukavemet bölüm 9 kuyu tabanı yüklerini TS EN 81-20
    m.5.2.1.8'e göre, ray kuvvetlerini de bölüm 7-8'de ayrıntılı verir.
"""
from engine.avan import hesap as E_AVAN
from engine.ortak.steps import numarala
from engine.uygulama import mukavemet as E_MUK
from engine.avan import tablolar as T
from engine.uygulama import girdi as UG
from engine.uygulama import mukavemet_girdi as MG

#  Avanın uygulama projesine giren bölümleri  ( 0-tabanlı sıra )
ELEKTRIK_BOLUMLERI = (2, 3, 4, 5)          # kabin ayd. · kuyu ayd. · TAS · ε

#  AVAN METNİNİN UYGULAMA KARŞILIĞI.  Bu iki not avan paftasında doğrudur —
#  "kesin seçim uygulama projesinde yapılır" der.  Uygulama paftasında ise
#  kendi kendisiyle çelişir:  okuyucunun elindeki belge ZATEN uygulama
#  projesidir.  Bölüm alınırken metin değiştirilir, hesap aynen kalır.
NOT_KARSILIGI = {
    T.SIGORTA_NOTU: T.SIGORTA_NOTU_UYGULAMA,
    ("Aydınlatma ve priz devrelerinde izin verilen gerilim düşümü %1,5'tir; "
     "bu devrelerin uç noktalara kadar düşümü uygulama projesinde kontrol "
     "edilecektir."): T.GERILIM_UC_NOKTA_NOTU_UYGULAMA,
}


#  Kurulu güç cetvelinde sigorta kademesi tablonun dışına taşarsa avan
#  "uygulama projesinde" yazar — burada aynı çelişki.
CETVEL_KARSILIGI = {"uygulama projesinde": "imalatçı verisiyle"}


def _notlari_uyarla(b):
    """Avandan alınan bölümün proje adı geçen metinlerini uygulamaya çevirir.

    Yalnız METİN değişir;  hiçbir sayı ya da kontrol sonucu etkilenmez.
    """
    b = dict(b)
    for alan in ("notlar", "aciklamalar", "ekran_notlari"):
        if b.get(alan):
            b[alan] = [NOT_KARSILIGI.get(x, x) for x in b[alan]]
    if b.get("cetvel"):
        b["cetvel"] = [dict(c, sigorta=CETVEL_KARSILIGI.get(c.get("sigorta"),
                                                            c.get("sigorta")))
                       for c in b["cetvel"]]
    return b


def _proje_geneli_bolumleri(av, g):
    """Binaya ait bölümler ve yapılamayan zorunlu hesaplar  —  ( bölümler , eksik ).

    Makine dairesi aydınlatması ve temel topraklama BİNAYA aittir, asansöre
    değil:  bir binada dört asansör varsa topraklama tektir.  Bölümler
    işaretlenir ( proje_geneli ) ve numarasızdır;  numarayı çağıran verir.
    ``av`` avan motorunun sonucudur:  topraklama iletkenlerini oradaki
    asansörlerin EN BÜYÜK koruma iletkeninden türetir ( bkz. hesapla_coklu ).
    """
    bolumler, eksik = [], []
    mk = av.get("makine_dairesi") or {}
    if mk.get("aktif"):
        bolumler.append(dict(_notlari_uyarla(mk["bolum"]), proje_geneli=True))
    elif mk.get("mk_yok") is False:
        #  Makine dairesi VAR denmiş ama aydınlatması hesaplanamamış:  zorunlu
        #  bir hesap eksiktir, proje "uygun" sayılamaz.
        eksik.append("MAKİNE DAİRESİ AYDINLATMA HESABI YAPILAMADI: "
                     + str(mk.get("uyari") or ""))

    tp = av.get("topraklama") or {}
    if tp.get("aktif"):
        bolumler += [dict(_notlari_uyarla(b), proje_geneli=True)
                     for b in (tp.get("bolumler") or [])]
    elif g.get("temel_a") or g.get("temel_b"):
        #  Temel ölçüsü girilmiş ama topraklama hesaplanamamış — eksik hesap.
        eksik.append("TOPRAKLAMA HESABI YAPILAMADI: "
                     + str(tp.get("uyari") or av.get("hata") or ""))
    return bolumler, eksik


def hesapla(veriler=None):
    """TEK ASANSÖRÜN hesabı  —  mukavemet + elektrik + topraklama.

    Bu bir PARÇADIR, proje girişi değildir:  projeyi ``hesapla_coklu``
    koşturur ve tek asansörlük projede de o çağrılır.  Doğrudan çağırmak
    yalnız birim denemeleri içindir — proje geneli bölümler ( topraklama ·
    makine dairesi ) burada asansörün bölüm listesinin İÇİNDE kalır, oysa
    projede ayrılıp en sona alınırlar.
    """
    eksik = []          # yapılamayan ZORUNLU hesaplar
    g = UG.varsayilanlar()
    g.update(veriler or {})
    g = UG.tamamla(g)
    hata = UG.dogrula(g)
    if hata:
        return {"aktif": False, "hata": hata, "girdi": g}

    muk = E_MUK.hesapla(g)
    if not muk.get("aktif"):                       # olmamalı — dogrula geçti
        return {"aktif": False, "hata": muk.get("hata") or [], "girdi": g}

    eksik.extend(muk.get("ozet", {}).get("eksik_hesap", []))
    av = E_AVAN.hesapla(UG.kopru(g))
    asansor = (av.get("asansorler") or [{}])[0]
    uyarilar = list(muk.get("uyarilar") or [])

    elektrik = []
    if asansor.get("aktif"):
        tum = asansor.get("bolumler") or []
        elektrik = [tum[i] for i in ELEKTRIK_BOLUMLERI if i < len(tum)]
        uyarilar += [u for u in (asansor.get("uyarilar") or [])
                     #  Avanın trafik karşılaştırması uygulama projesinde
                     #  anlamsızdır — burada trafik hesabı yoktur.
                     if "TRAFİK" not in u.upper()]
    else:
        # Zorunlu hesap eksikliği genel uygunluğu da engeller.
        # Uyarı aşağıda eksik listesinden tek kez üretilir.
        #  Sebep asansörün kendi uyarısıdır;  proje geneli bir girdi
        #  reddedildiyse avan motoru hiç hesaplamaz ve sebebi "hata"dadır.
        eksik.append("ELEKTRİK HESAPLARI YAPILAMADI: "
                     + str(asansor.get("uyari") or av.get("hata") or "girdiler eksik"))

    #  Bölüm numaraları uygulama projesinin kendi sırasına göre yeniden
    #  yazılır;  avandan gelen "3 - ..." başlığı burada 11. sıradadır.
    #  Numarayı yalnız steps.numarala koyar ve bölümün KİMLİĞİNE dokunmaz —
    #  sonuçtan girdiye atlama gibi bölümü tanıması gereken her şey kimliğe
    #  bakar, numaraya değil.
    bolumler = list(muk.get("bolumler") or [])
    sira = len(bolumler)
    for b in elektrik:
        sira += 1
        bolumler.append(numarala(_notlari_uyarla(b), sira))

    #  PROJE GENELİ BÖLÜMLER.  İşaretlenirler ki çoklu projede yalnız BİR
    #  KEZ paftaya girsinler — ve orada bütün asansörlerle yeniden
    #  hesaplanırlar ( bkz. hesapla_coklu ).
    _pg, _pg_eksik = _proje_geneli_bolumleri(av, g)
    for b in _pg:
        sira += 1
        bolumler.append(numarala(b, sira))
    eksik += _pg_eksik

    #  GENEL SONUÇ:  bölüm sonuçları + ENGELLEYİCİ uyarılar + EKSİK hesaplar.
    #  Bilgilendirici uyarılar ( reddedilen ofis girdisi, kabin alanı uyarısı … )
    #  uygunluğu engellemez;  engelleyici olanlar ve yapılamayan zorunlu
    #  hesaplar engeller.  Yoksa "bütün bölümler uygun" diye bir proje, içinde
    #  yapılamamış bir hesapla ya da kurulamaz bir geometriyle teslim edilirdi.
    engelleyici = list(av.get("engelleyici") or [])
    uyarilar += [x for x in engelleyici if x not in uyarilar]
    #  AYNI EKSİKLİK İKİ KEZ YAZILMASIN.  Sarılma açısı girilmemişse girdi
    #  denetimi ne yapılacağını anlatan uyarıyı zaten koymuştur
    #  ( MG.ALFA_UYARI );  altına bir de "HESAP EKSİK — α girilmedi"
    #  basılınca paftanın ilk satırları aynı şeyi iki kez söylüyordu.
    #  Eksik LİSTESİ ( özet · genel hüküm ) aynen kalır;  yalnız uyarı
    #  kutusundaki tekrar düşer.
    _anlatilan = {E_MUK.ALFA_YOK} if MG.ALFA_UYARI in uyarilar else set()
    uyarilar += [f"⚠ {x}" for x in eksik if x not in _anlatilan]
    uygunlar = [b["sonuc"]["uygun"] for b in bolumler
                if b.get("sonuc") and b["sonuc"].get("uygun") is not None]
    uygunlar += [False] * (len(engelleyici) + len(eksik))
    ozet = dict(muk.get("ozet") or {})
    ao = asansor.get("ozet") or {}
    ozet.update({
        "P_kurulu": ao.get("P_kurulu"), "eps": ao.get("eps"),
        "eps_uygun": ao.get("eps_uygun"), "I": ao.get("I"), "Iz": ao.get("Iz"),
        "akim_uygun": ao.get("akim_uygun"),
        "n_kabin": ao.get("n_kabin"), "n_kuyu": ao.get("n_kuyu"),
        #  Yuvarlanmamış armatür sayıları:  ekranda gösterilmez ama ortak
        #  girdi köprüsünün kopmadığını YUVARLAMA GİZLEMESİN diye özete girer
        #  ( bkz. testler/test_uygulama.py ).
        "Z_kabin": ao.get("Z_kabin"), "Z_kuyu": ao.get("Z_kuyu"),
        "Re": (av.get("ozet") or {}).get("Re"),
        "topraklama_uygun": (av.get("ozet") or {}).get("topraklama_uygun"),
        "elektrik_var": bool(elektrik),
        "tumu_uygun": all(uygunlar),
        "engelleyici": engelleyici, "eksik_hesap": eksik,
    })
    #  HÜKÜM MOTORDAN ÇIKAR ( bkz. E_MUK.genel_hukum ):  "uygun değil" >
    #  "hesap eksik" > "uygundur".  Ekran ve PDF bunu yalnız basar.
    _hukum = E_MUK.genel_hukum(bolumler, all(uygunlar), eksik)
    ozet["genel_sonuc"], ozet["genel_sonuc_kisa"] = _hukum
    return {
        "aktif": True,
        "baslik": "ASANSÖR UYGULAMA PROJESİ HESAPLARI",
        "girdi": g,
        "bolumler": bolumler,
        "mukavemet_bolum_sayisi": len(muk.get("bolumler") or []),
        "sabitler": muk.get("sabitler"),
        "ozet": ozet,
        "uyarilar": uyarilar,
        "ara": muk.get("ara", {}),
    }


# =====================================================================
#  ÇOKLU ASANSÖR        ( 1 - 4 asansör, tek proje )
# =====================================================================
#  Bir binada farklı kuyularda dört asansör olabilir;  hesap her biri için
#  AYNIDIR, değişen yalnız girdilerdir.  Motor tek asansörlük kalır ve
#  burada birden çok kez koşturulur — ikinci bir hesap yolu açılmaz, yoksa
#  zamanla ayrışırlar.
#
#  PROJE GENELİ HESAPLAR BİR KEZ GİRER.  Temel topraklama ve makine dairesi
#  aydınlatması binaya aittir;  dört paftada dört kez aynı topraklama
#  hesabını basmak hem yer kaplar hem de "hangisi geçerli" sorusunu doğurur.
#  Asansörlerden düşülür ve BÜTÜN asansörlerle bir kez hesaplanır.
ASANSOR_AZAMI = 4


def _tesis_bolumleri(aktifler):
    """Binaya ait bölümler  —  bütün asansörlerin sonuçlarıyla BİR KEZ.

    TOPRAKLAMA İLETKENLERİ TESİSTEKİ EN BÜYÜK KORUMA İLETKENİNDEN TÜRER
    ( Elektrik Tesislerinde Topraklamalar Yönetmeliği m.9 ).  Bölümler önce
    ilk asansörün kendi hesabından alınıyordu;  o hesap yalnız KENDİ koruma
    iletkenini gördüğü için sonuç asansörlerin SIRASINA bağlıydı:  kolon
    kesiti 16 ve 95 mm² olan iki asansörde 16'lık önce gelince topraklama
    iletkeni 16 mm², ana potansiyel dengeleme 10 mm² çıkıyordu — 95'lik önce
    gelince 50 ve 25.  Avan projesi bunu zaten tesis düzeyinde yapar;  burada
    aynı motor, bütün asansörler tek tesis olarak verilerek bir kez koşturulur.
    """
    if not aktifler:
        return []
    ilk = aktifler[0]["girdi"]
    tesis = UG.kopru(ilk)                       # ortak · ofis sabitleri binanındır
    tesis["asansorler"] = [UG.kopru(s["girdi"])["asansorler"][0] for s in aktifler]
    bolumler, _eksik = _proje_geneli_bolumleri(E_AVAN.hesapla(tesis), ilk)
    #  KENDİ NUMARALARINI ALIRLAR:  bir asansörün bölümleri değil, ayrı bir
    #  başlığın altındadırlar.
    return [numarala(b, n) for n, b in enumerate(bolumler, 1)]


def hesapla_coklu(asansorler=None, ortak=None):
    """1 - ASANSOR_AZAMI arası asansörü aynı motorla koşturur.

    asansorler   her biri hesapla()'nın beklediği girdi sözlüğü
    ortak        bütün asansörlerde geçerli değerler ( ofis sabitleri … );
                 asansörün kendi girdisi bunu EZER — PROJE GENELİ alanlar
                 hariç ( UG.PROJE_GENELI_ALANLAR ):  onlarda ortak kazanır.

    Döner:  { aktif , asansorler:[ … ] , ozet , … }
    Tek asansörlü çağrıda da aynı yapı döner;  arayüz tek koda bakar.
    """
    ham = [a for a in (asansorler or []) if isinstance(a, dict)]
    if not ham:
        ham = [{}]
    ham = ham[:ASANSOR_AZAMI]
    ortak = ortak if isinstance(ortak, dict) else {}

    #  PROJE GENELİ BÖLÜMLER HİÇBİR ASANSÖRDE KALMAZ.
    #  Önce yalnız İLK asansörde bırakılıyorlardı;  dört asansörlük paftada
    #  bu, topraklamayı 1 nolu asansörün sonuna, yani BELGENİN ORTASINA
    #  koyuyordu — 2, 3 ve 4 nolu asansörler ondan sonra geliyordu.  Binaya
    #  ait hesap, asansörlerin arasında değil HEPSİNİN ARKASINDA durmalıdır.
    #  Burada ayrılıp üst seviyeye alınırlar;  paftayı basan taraf onları en
    #  sona, kendi şeridiyle bir kez koyar ( bkz. pdf_export.uygulama_coklu_pdf ).
    #  PROJE GENELİ ALANLARDA ORTAK KAZANIR.  Asansörün kendi değeri önce
    #  geliyordu:  eski bir proje dosyasından kalmış temel_a = 10 taşıyan
    #  asansör, proje genelinde 20 yazılıyken binanın topraklamasını 10 ile
    #  hesaplatıyordu ( tesis bölümleri 1 nolu asansörün girdisinden kurulur ).
    #  Ortakta OLMAYAN alan asansörden alınır — eski tek asansörlük çağrılar
    #  bunları asansörün içinde taşır.
    pg = {k: ortak[k] for k in UG.PROJE_GENELI_ALANLAR if k in ortak}
    sonuclar = []
    for i, g in enumerate(ham, 1):
        s = hesapla({**ortak, **g, **pg})
        s["no"] = i
        s["tanim"] = str(g.get("asansor_adi") or "").strip() or f"{i} nolu asansör"
        if s.get("aktif"):
            #  Asansörün kalan bölümleri boşluksuz 1..N diye yeniden
            #  numaralanır — paftada 11-12-13 diye gitsin.
            s["bolumler"] = [
                numarala(b, n) for n, b in
                enumerate([x for x in s["bolumler"]
                           if not x.get("proje_geneli")], 1)]
        sonuclar.append(s)

    aktifler = [s for s in sonuclar if s.get("aktif")]
    proje_geneli = _tesis_bolumleri(aktifler)
    #  PROJE GENELİ HESAP DA "HEPSİ UYGUN"A GİRER.  Bölümler asansörlerden
    #  çıkınca onların ozet.tumu_uygun bayrağı bunları artık saymaz;  ayrıca
    #  katılmasaydı topraklaması yetersiz bir proje "UYGUNDUR" görünürdü.
    pg_uygun = all((b.get("sonuc") or {}).get("uygun") is not False
                   for b in proje_geneli)
    return {
        "aktif": bool(aktifler),
        "baslik": "ASANSÖR UYGULAMA PROJESİ HESAPLARI",
        "asansorler": sonuclar,
        "proje_geneli": proje_geneli,
        "adet": len(sonuclar),
        #  KULLANILAN YOL SONUCUN İÇİNDE YAZAR.  Çağıran taraf "bu proje tek
        #  mi çoklu mu" diye karar VERMEZ, sonuca bakar — avan trafik motoru
        #  da böyle yapar ( engine/avan/trafik.hesapla ).  Bir süre kararı API
        #  veriyordu ve aynı dallanma PDF · CAD · ZIP uçlarında üç kez
        #  tekrarlanıyordu;  iki yol zamanla ayrıştı.
        "yol": "tek" if len(sonuclar) == 1 else "coklu",
        #  Aynı metin bir kez:  reddedilen bir ofis değeri bütün asansörleri
        #  aynı cümleyle durdurur, dört kez basılması okumayı zorlaştırır.
        "hata": list(dict.fromkeys(h for s in sonuclar if not s.get("aktif")
                                   for h in (s.get("hata") or []))),
        "ozet": {
            "adet": len(sonuclar),
            "tumu_uygun": bool(aktifler) and pg_uygun and all(
                (s.get("ozet") or {}).get("tumu_uygun") for s in aktifler)
            and len(aktifler) == len(sonuclar),
            "proje_geneli_uygun": pg_uygun,
            "proje_geneli_adet": len(proje_geneli),
            "asansorler": [{"no": s["no"], "tanim": s["tanim"],
                            "aktif": bool(s.get("aktif")),
                            "tumu_uygun": (s.get("ozet") or {}).get("tumu_uygun"),
                            "eksik_hesap": (s.get("ozet") or {}).get("eksik_hesap", []),
                            "genel_sonuc": (s.get("ozet") or {}).get("genel_sonuc"),
                            "N_hesap": (s.get("ozet") or {}).get("N_hesap")}
                           for s in sonuclar],
        },
    }

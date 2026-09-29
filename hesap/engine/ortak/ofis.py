# -*- coding: utf-8 -*-
"""
OFİS STANDARDI  —  HER İKİ PROJENİN ORTAK KABULLERİ

Burada yalnız AVAN ve UYGULAMA projelerinin İKİSİNİN BİRDEN kullandığı,
projeye değil OFİSE ait kabuller durur.  İki proje ayrı klasörlerdedir
( engine/avan · engine/uygulama );  ama aynı fiziksel büyüklüğün iki yerde iki farklı sayı olması hata demektir.

NİÇİN AYRI DOSYA:
    Makine verimi η bir süre iki yerde ayrı ayrı duruyordu — avan tarafında
    makine tipine bağlı ( dişlisiz 0,85 · dişli 0,50 ), mukavemet tarafında
    ise makine tipinden bağımsız sabit 0,92.  Aynı asansör için iki pafta
    farklı motor gücü veriyordu ve mukavemetinki DÜŞÜK, yani emniyetsiz
    olandı ( dişli makinede gerçek ihtiyacın yarısı ).  Tek kaynağa
    alınmasının sebebi budur:  buradan okuyan iki taraf bir daha ayrışamaz.
"""
from engine.ortak.steps import yuvarla


#  Makine tipine göre TOPLAM SİSTEM VERİMİ  ( ofis kabulü ).  Anahtarlar
#  arayüzün seçenekleridir ve kayıtlı proje dosyalarında da bu metinlerle
#  durur — değiştirilirse eski projeler tabloda bulunamaz.
MAKINE_VERIMLERI = {
    "Dişlisiz": 0.85,
    "Dişli":    0.50,
}

#  ---------------------------------------------------------------------
#  PALANGA VERİM DÜŞÜŞÜ ( Δη = 0,10 )  —  UYGULAMADA YOK, AVANDA KİTAPTAN
#  ---------------------------------------------------------------------
#  MMO/697 §2.4 "palangalı sistemlerde verim %10 az alınacaktır" der
#  ( örnek §4.4:  η = 0,5 − 0,1 = 0,4 ).
#
#  AVAN PROJESİ kitaba göre denetlenir ve düşüşü UYGULAR:  orada buradaki
#  sayılar kitabın η'sı, yani MAKİNE verimidir ( bkz. engine/avan/tablolar
#  PALANGA_VERIM_DUSUSU ).  2026-09-08'de avandan da kaldırılmış, 2026-09-25'te
#  geri getirilmiştir:  avan motoru kitabın bulduğundan küçük seçiyordu.
#
#  UYGULAMA PROJESİ düşüşü UYGULAMAZ;  orada buradaki sayılar ve projeye
#  girilen η TOPLAM SİSTEM VERİMİDİR.  Uygulamada kural üç yönden yanlıştır:
#
#  1) TOPLAMSAL.  Makara kayıpları ( halatın bükülüp açılmasındaki tel içi
#     sürtünme + yatak sürtünmesi ) fiziksel olarak ÇARPIMSALDIR:  her
#     geçiş η_makara ≈ 0,98 ( burçlu makarada ≈ 0,95 ) ile çarpar.  Sabit
#     bir sayı çıkarmak, aynı fiziksel kaybı dişlisizde %11,8, dişlide %20
#     göreli ceza yapıyordu — oysa makaralar üstlerinde redüktör olup
#     olmadığını bilmez.
#  2) MAKARA SAYISINA GÖRE ÖLÇEKLENMİYORDU.  i > 1 olan her sistem aynı
#     0,10'u alıyordu;  4:1 ile 2:1 eşitti.
#  3) NEGATİFE DÜŞEBİLİYORDU.  η = 0,08 → η′ = −0,02.  İki projede de bunun
#     için ayrı kalkanlar yazılmıştı;  o kalkanlara ihtiyaç duyulması
#     girdinin değil MODELİN bozuk olduğunun belirtisiydi.
#
#  Uygulamadaki kural:  buradaki değerler ve projeye girilen η TOPLAM
#  SİSTEM VERİMİDİR — askı ( palanga ) kaybı zaten içindedir, ikinci kez
#  uygulanmaz.  İmalatçı kataloğu da bu büyüklüğü verir ( η_ins ), yani
#  girilen sayı ile hesaplanan sayı aynı şeydir.
#
#  DİKKAT — 0,85 / 0,50 MAKİNE verimidir ( avan böyle okur ).  Uygulamada
#  toplam sistem verimi olarak okunduklarında 2:1 askıda İYİMSERDİRLER
#  ( gerçekçi: dişlisiz 2:1 ≈ 0,80 · dişli 2:1 ≈ 0,48 ).  Ofis bu iki
#  varsayılanı katalog verisiyle güncellemelidir;  asansör bazında girilen
#  η zaten bunları ezer.

#  Tanınmayan makine tipinde kullanılacak verim.  Yalnız GERİYE DÖNÜK uyum
#  içindir ( makine tipi taşımayan eski projeler );  yeni hesaplarda makine
#  tipi her zaman girilir.
VARSAYILAN_VERIM = 0.92


#  ---------------------------------------------------------------------
#  ANMA YÜKÜNE GÖRE ORTALAMA BOŞ KABİN KÜTLESİ  Gk   ( ofis tablosu )
#  ---------------------------------------------------------------------
#  BU TABLO STANDARTTAN GELMİYOR — böyle bir çizelge yoktur.
#  TS EN 81-20 ve TS EN 81-50 boş kabin kütlesini ( P ) her yerde GİRDİ
#  olarak tanımlar:  "P is the mass of the empty car and components
#  supported by the car…".  Dokuz ayrı yerde geçer, hiçbirinde sayı ya da
#  çizelge verilmez;  kabinin kaç kilo geleceğini imalatçı belirler.
#  ISO 4190-1 aynı yük serisi için ( 320 · 450 · 630 · 800 · 1000 · 1275 ·
#  1600 · 1800 · 2000 kg ) kabin ÖLÇÜLERİNİ verir, kütle vermez.
#
#  BU MMO/697'NİN TABLO-11'İ DEĞİLDİR.  Kitabın Tablo-11'i "beyan yüküne
#  göre kullanılabilir en büyük kabin alanı"dır ( 450 kg → 1,30 m² ) ve
#  boş kabin kütlesi vermez.  Aşağıdaki değerler OFİSİN KENDİ İMALATÇI
#  DENEYİMİNDEN gelir;  paftada kaynağı da öyle yazılır.
#
#  NİÇİN ORTAK DOSYADA:  avan tarafı bu tabloyu zaten kullanıyordu;  şimdi
#  uygulama projesi de boş kabin ağırlığını buradan doldurur.  İki yerde iki
#  ayrı kopya tutulsaydı biri güncellenip öteki unutulur, aynı asansör iki
#  projede iki farklı kabin kütlesiyle hesaplanırdı.
GK_TABLOSU = ((450, 500), (630, 650), (800, 800), (1000, 950), (1125, 1020),
              (1275, 1100), (1600, 1350), (2000, 1600), (2500, 1900))

GK_KAYNAGI = "KABUL  ·  ortalama boş kabin kütlesi  ( standart sayısı değildir )"

#  Tablonun kapsadığı yük aralığı.  Dışında UÇ DEĞERE SABİTLENİR:  100 kg'lık
#  bir asansöre 500 kg'lık kabin gelir.  Sayı ekranda görünür ve elle
#  değiştirilebilir;  kapsam dışında tabloya güvenilmemelidir.
GK_ALT, GK_UST = GK_TABLOSU[0][0], GK_TABLOSU[-1][0]


def bos_kabin_kutlesi(Q):
    """Anma yüküne göre ortalama boş kabin kütlesi  ( kg ) — TAHMİNDİR.

    Ara yükler doğrusal ara değerle bulunur ve 10 kg'a, yarımı yukarı
    yuvarlanır.  Aralık dışında uç değere sabitlenir.
    """
    if not isinstance(Q, (int, float)) or isinstance(Q, bool):
        return None
    if Q <= GK_ALT:
        return float(GK_TABLOSU[0][1])
    if Q >= GK_UST:
        return float(GK_TABLOSU[-1][1])
    for (x0, y0), (x1, y1) in zip(GK_TABLOSU, GK_TABLOSU[1:]):
        if x0 <= Q <= x1:
            y = y0 + (Q - x0) * (y1 - y0) / (x1 - x0)
            #  Yarım YUKARI yuvarlanır;  Python'un round()'u bankacı
            #  yuvarlaması yapar ( 865 → 860 ).  Fark 10 kg'lık kademede
            #  görünür.  Kural tek yerdedir ( steps.yuvarla ).
            return yuvarla(y, -1)
    return None


def makine_verimi(makine_tipi):
    """Makine tipine göre η.  Tanınmayan tip için None."""
    return MAKINE_VERIMLERI.get(makine_tipi)


def sistem_verimi(makine_tipi):
    """η  —  makine tipine göre TOPLAM SİSTEM VERİMİ.

    Uygulama projesi içindir:  askı ( palanga ) kaybı bu değerin İÇİNDEDİR,
    askı oranına bağlı ayrı bir düzeltme uygulanmaz ( bkz. yukarıdaki
    "PALANGA VERİM DÜŞÜŞÜ" notu;  avan kitaba göre 0,10 düşer ).
    Tanınmayan makine tipinde VARSAYILAN_VERIM'e dönülür.
    """
    eta = makine_verimi(makine_tipi)
    return VARSAYILAN_VERIM if eta is None else eta

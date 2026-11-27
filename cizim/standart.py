"""TS EN 81-20'NİN ÇİZİMLERDE KULLANILAN SAYILARI ( mm ) — maddeleriyle.

Bir modülün kendi işine ait olmayan, birkaç modülün kullandığı standart
sayıları burada durur:  kabin üstü korkuluğu hem kabin üstü planı
( kabin_ustu ) hem arkadaki ağırlıkla 2:1'in kasnak yerleşimi ( arka_aski )
kullanır.  Eskiden kabin_ustu.py'deydi ve arka_aski onu fonksiyon içinden
import ediyordu ( iki modül birbirine dolanmıştı ).
"""

#  TS EN 81-20 m.5.4.7.2 b:  tavan kenarından kuyu duvarına yatay boşluk
#  0,30 m'yi AŞARSA korkuluk gerekir.
KORKULUK_BOSLUK = 300.0
#  m.5.4.7.4 c:  korkuluk tavan kenarından en çok 0,15 m içeride durur.
KORKULUK_KENAR_AZAMI = 150.0
#  m.5.4.7.4 d:  küpeştenin dış kenarı kuyudaki parçalardan ( karşı ağırlık,
#  raylar, konsollar … ) en az 0,10 m uzakta olmalıdır.
KORKULUK_PARCA_ASGARI = 100.0
#  m.5.4.7.4 b:  küpeştenin iç kenarından duvara boşluk 0,50 m'ye kadar ise
#  yükseklik en az 0,70 m, aşarsa en az 1,10 m.
KORKULUK_YUKSEKLIK_SINIRI = 500.0
KORKULUK_ALCAK, KORKULUK_YUKSEK = 700.0, 1100.0
#  m.5.2.5.7.2 c 1 · Şekil 5:  korkuluğun en üst kısmı ile kuyu tavanının en alt kısımları
#  ( kirişler ve tavanın altındaki parçalar ) arası — kabinin izdüşümünde, küpeştenin kabin
#  tarafında 0,40 m yatay uzaklık içinde DÜŞEY en az 0,30 m;  küpeştenin dışındaki parçaya en
#  az 0,10 m.  Kabin üstü ( küpeştenin yeri ) ve dusey ( açıklık denetimi ) ortak okur.
KORKULUK_TAVAN_IC, KORKULUK_TAVAN_DIS, KORKULUK_TAVAN_BOLGE = 300.0, 100.0, 400.0
#  m.5.2.5.5.1 b:  karşı ağırlık perdesi kuyu tabanından en az 2,0 m yükseğe uzanır
#  ( alt ucu tabandan en çok 0,30 m — c;  kuyu dibi planı, kuyu_dibi._perdeyi_uzat ).
AGIRLIK_PERDESI_YUKSEKLIGI = 2000.0
#  m.5.2.5.5.2:  kuyuda birden çok asansör varsa hareketli parçaları arasında perde.
#  .1  kuyu tabanının en çok 0,30 m üstünden en alt durak döşemesinin 2,50 m üstüne;
#      eni bir kuyu dibinden ötekine geçilemeyecek kadar ( kuyu grubu, cizim/grup.py ).
#  .2  herhangi bir korkuluğun iç kenarı ile komşu asansörün hareketli parçası
#      ( kabin, karşı ağırlık ) arası 0,50 m'den azsa kuyu boyunca;  eni parçanın
#      eni ve iki yanda 0,10 m.
PERDE_TABANDAN = 300.0
PERDE_DURAK_USTU = 2500.0
#  m.5.2.2.4:  kuyu dibine erişim — derinlik 2,50 m'yi AŞARSA erişim kapısı ( a;  kapı
#  m.5.2.3'e uyar ), aşmıyorsa kuyu içinde merdiven ( b, Ek F ) ya da kapı.  Merdiven kuyu
#  dibi planında çizilir ( kuyu_dibi.merdiven_adaylari );  kapı mimarinindir — çizilmez, VERİLER'in
#  notunda ve hesabın uyarısında söylenir ( 22 Kas denetimi:  eskiden hiçbir yerde yoktu ).
KUYU_DIBI_MERDIVEN_AZAMI = 2500.0
KUYU_DIBI_KAPISI_NOTU = (
    "Kuyu dibi 2,50 m'yi aştığı için kuyu dibine merdiven değil erişim kapısı gerekir "
    "( TS EN 81-20 m.5.2.2.4 a · kapı m.5.2.3 ) — mimari projede gösterilir."
)
#  MERDİVEN ÇİZİME ENGEL DEĞİLDİR ( 27 Kas, kullanıcı:  "merdiven hiç bir türlü çizime engel
#  olmamalı … gerçekten kuyuya sığan bir asansörü reddetmek fazla sert" ):  m.5.2.2.4 b bir ürün
#  değil şart koyar — erişim kapısı YA DA Ek F'ye uyan merdiven ( altı tip:  sabit, sürgülü,
#  eğik konan, tabanda saklanan, katlanır ).  Program yalnız sabit merdiveni ( Tip 1 — saklıyken
#  de eşiğin 1,10 m üstüne uzanır ) yerleştirir ( kuyu_dibi.merdiven_adaylari );  yeri yoksa
#  merdiven çizilmez ( öbür tiplerin yeri ürüne bağlı — uydurulmaz ), bu not söyler:  VERİLER'in
#  NOTLAR'ında ( veri_tablosu ) ve ekranda ( çizim yanıtının "notlar"ı ).  Piyasada:  eşiğe takılan
#  eğik, kollu katlanır, katlanır basamaklı merdivenler ( W+W Typ 5 / 7B, StufiKlapp — kontaklı ).
KUYU_DIBI_MERDIVEN_NOTU = (
    "Kuyu dibinde sabit merdivene ( TS EN 81-20 Ek F Tip 1 ) kat girişine 800 mm içinde, kabinin "
    "yolu ve sığınma alanı dışında yer yok.  Erişim kapısı ya da Ek F'ye uyan başka bir merdiven "
    "( katlanır, tabanda saklanan, duvar nişinde ) seçilir ( m.5.2.2.4 b ):  saklı konumu kat "
    "girişine en çok 800 mm ( F.5 b ), kullanımda basamakların ortası en çok 600 mm ( F.5 c );  "
    "açıkken hareketli parçalara çarpabilecekse elektrik güvenlik kontağı, tabanda saklanıyorsa "
    "sığınma alanları korunur ( m.5.2.2.4 )."
)


def kuyu_dibi_kapisi_gerekir(derinlik):
    """Kuyu dibi derinliği ( mm ) erişim kapısı istiyor mu ( m.5.2.2.4 a )."""
    return (
        isinstance(derinlik, (int, float))
        and not isinstance(derinlik, bool)
        and derinlik > KUYU_DIBI_MERDIVEN_AZAMI
    )


PERDE_KORKULUK_ASGARI = 500.0
PERDE_YAN_PAYI = 100.0

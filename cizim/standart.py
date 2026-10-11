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

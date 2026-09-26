# -*- coding: utf-8 -*-
"""
ÇİZİM MODÜLÜ  —  hesap motorundan BAĞIMSIZ

Bu paket `engine/` içindeki hiçbir şeyi import ETMEZ.  Girdisi, aşağıdaki
sözleşmeye uyan düz bir sözlüktür ( bkz. cizim/girdi.py ) ve çıktısı çizim
elemanlarıdır;  bunlar SVG ( ekran ) ya da DXF ( CAD ) olarak yazılır.

NİÇİN AYRI:  hesap motoru dondurulmuş referanslarla korunuyor ve çizim
denemeleri orayı riske atmamalı.  Çizimin ihtiyaç duyduğu geometri
( duvar kalınlığı, kapı yeri, kat kotları ) hiçbir hesaba girmiyor.

TEK DOĞRULUK KAYNAĞI:  çizim SAYI TÜRETMEZ.  Kuyu boyu, ray boyu, tampon
stroku gibi değerler girdiden gelir;  ileride köprü ( cizim/kopru.py )
bunları hesabın kendi sonuçlarından dolduracaktır.
"""

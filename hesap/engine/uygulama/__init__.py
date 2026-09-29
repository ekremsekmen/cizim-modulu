# -*- coding: utf-8 -*-
#  BİRLEŞİK PROGRAM:  uygulama projesinin hesabı çizim modülünü kullanır
#  ( sığınma açıklıkları çizimin geometrisinden, boş bırakılan bazı girdiler
#  çizimden — cizim/kopru.py ).  Çizim modülü hesap/ klasörünün bir üstündedir;
#  yolun SONUNA eklenir ki hesabın kendi paketleri ( testler … ) önce bulunsun.
import os as _os
import sys as _sys

_KOK = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))))
if _KOK not in _sys.path:
    _sys.path.append(_KOK)

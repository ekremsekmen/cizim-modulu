"""İMPORT KÖKLERİ — programın kökleri tek yerden.

Program iki kökten import eder:  depo kökü ( cizim, tasarim, araclar,
testler ) ve hesap/ ( api, engine, exports, dogrulama ).  Örnek proje
girdileri ornekler/'dedir ( hesap_girdi ).  Kütüphane modülleri sys.path'e
DOKUNMAZ:  giriş noktaları ( hesap/main.py, calistir.py, kontrol.py'nin
çağırdığı betikler ) kur()'u bir kez çağırır;  pytest aynı kökleri
pyproject.toml'dan ( pythonpath ) alır.

Eskiden yol ayarı kütüphane modüllerinin içine dağılmıştı ( api/cizim,
engine/uygulama, tasarim/alanlar ve her test dosyası ) ve iki ayrı "testler"
paketi olduğu için SIRAYA bağlıydı ( "sona eklenir ki hesabınki önce
bulunsun" );  hesabın test paketi dogrulama/ adını alınca çakışma kalktı.
"""

import os
import sys

KOK = os.path.dirname(os.path.abspath(__file__))
KOKLER = (KOK, os.path.join(KOK, "hesap"), os.path.join(KOK, "ornekler"))


def kur():
    """Kökleri sys.path'e ekler ( zaten varsa dokunmaz )."""
    for yol in KOKLER:
        if yol not in sys.path:
            sys.path.append(yol)

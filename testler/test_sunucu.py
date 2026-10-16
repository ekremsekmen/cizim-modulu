"""WEB SUNUCUSU KİPİ — hesap/main.py --sunucu.

Masaüstü kipi tarayıcı açar, 127.0.0.1'i dinler, port doluysa sıradakine
geçer;  sunucuda üçü de yanlıştır.  Sunucu kipi adresi, portu ve işçi
sayısını ortamdan alır ( barındırma servisleri portu PORT'ta verir ).
"""

import json
import os
import socket
import subprocess
import sys
import time
import urllib.request

import main

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_varsayilanlar():
    assert main.sunucu_ayari({}) == {"host": "0.0.0.0", "port": 8780, "workers": 1}


def test_port_once_PORT_sonra_AVAN_PORT():
    assert main.sunucu_ayari({"PORT": "10000", "AVAN_PORT": "8800"})["port"] == 10000
    assert main.sunucu_ayari({"AVAN_PORT": "8800"})["port"] == 8800
    #  boş değişken yok sayılır ( kapsayıcıda PORT= tanımlı ama boş olabilir )
    assert main.sunucu_ayari({"PORT": "", "AVAN_PORT": "8800"})["port"] == 8800


def test_adres_ve_isci():
    a = main.sunucu_ayari({"AVAN_HOST": "127.0.0.1", "WEB_CONCURRENCY": "3"})
    assert (a["host"], a["workers"]) == ("127.0.0.1", 3)


def _bos_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_sunucu_acilir_ve_cevap_verir():
    """Gerçek açılış:  iki işçiyle ( uvicorn "main:app" içe aktarma yolu )
    ayağa kalkar, sağlık ucu ve ana sayfa cevap verir."""
    port = _bos_port()
    ortam = dict(os.environ, AVAN_HOST="127.0.0.1", PORT=str(port), WEB_CONCURRENCY="2")
    p = subprocess.Popen(
        [sys.executable, os.path.join(KOK, "hesap", "main.py"), "--sunucu"],
        env=ortam,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        url = f"http://127.0.0.1:{port}"
        saglik = None
        for _ in range(120):
            try:
                with urllib.request.urlopen(url + "/api/saglik", timeout=2) as c:
                    saglik = json.loads(c.read())
                break
            except OSError:
                time.sleep(0.25)
        assert saglik == {"durum": "calisiyor", "surum": main.SURUM}
        with urllib.request.urlopen(url + "/", timeout=10) as c:
            assert c.status == 200 and b"<html" in c.read().lower()
    finally:
        p.terminate()
        cikti = p.communicate(timeout=30)[0].decode("utf-8", "replace")
    assert "Started server process" in cikti, cikti

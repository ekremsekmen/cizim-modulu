"""BÜTÜN TESTLERDE:  programın kaydına beklenmeyen ERROR düşerse test kırılır.

Uçların son savunması ( uclar/uc_ortak.hata_kaydi ) ve yedek yollar
programın hatasını kullanıcıya genel iletiyle ya da eksik çizimle gösterir,
ayrıntıyı kayda ERROR yazar ( cizim/sorun.py BILINEN dışındaki her istisna ).
Yanıtı denetlemeyen bir test o hatayı görmezdi:  21 Eki son denetiminde
yutulan hatalar ancak istisnaları izleyen ayrı bir araçla bulunmuştu.

ERROR bekleyen test onu assertLogs ile yakalar ( yakalanan kayıt buraya
düşmez )."""

import logging

import pytest

#  Programın kaydedicileri:  logging.getLogger(__name__) — paket adları
PROGRAM = frozenset(("temel", "tasarim", "cizim", "motor", "ciktilar", "uclar", "main"))


@pytest.fixture(autouse=True)
def _beklenmeyen_hata_kaydi(caplog):
    yield
    hatalar = [
        r
        for r in caplog.get_records("call")
        if r.levelno >= logging.ERROR and r.name.split(".")[0] in PROGRAM
    ]
    if hatalar:
        pytest.fail(
            "programın kaydına beklenmeyen ERROR düştü ( yutulan hata ):\n"
            + "\n".join(f"  {r.name}:  {r.getMessage()}" for r in hatalar),
            pytrace=False,
        )

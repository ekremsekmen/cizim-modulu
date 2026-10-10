"""YAVAŞ TESTLER — hızlı denetimde ( kontrol.py hizli:  KONTROL_HIZLI=1 ) atlanır,
tam denetimde ve doğrudan unittest ile koşar.

Yalnız tek başına bir dakikayı aşan testler işaretlenir;  atlandıkları
unittest çıktısında "skipped" olarak görünür ( sessizce kaybolmaz )."""

import os
import unittest


def yavas(sure):
    """`sure`:  testin yaklaşık süresi ( iletide görünür )."""
    return unittest.skipIf(
        os.environ.get("KONTROL_HIZLI") == "1", f"yavaş ( ~{sure} ) — tam denetimde koşar:  kontrol.py tam"
    )

# -*- coding: utf-8 -*-
"""Test paketi için ortak yardımcılar."""
import os
import sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if KOK not in sys.path:
    sys.path.insert(0, KOK)

YESIL, KIRMIZI, SARI, GRI, SIFIR = "\033[32m", "\033[31m", "\033[33m", "\033[90m", "\033[0m"
if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
    YESIL = KIRMIZI = SARI = GRI = SIFIR = ""


class Rapor:
    """Basit test toplayıcı — geçen / kalan / atlanan sayar, ayrıntıyı biriktirir."""

    def __init__(self, baslik):
        self.baslik = baslik
        self.gecti = self.kaldi = self.atlandi = 0
        self.hatalar = []

    def kontrol(self, ad, kosul, ayrinti=""):
        if kosul:
            self.gecti += 1
        else:
            self.kaldi += 1
            self.hatalar.append(f"{ad}  {ayrinti}".strip())
        return bool(kosul)

    def esit(self, ad, bulunan, beklenen, tol=1e-6):
        if isinstance(beklenen, (int, float)) and isinstance(bulunan, (int, float)):
            ok = abs(bulunan - beklenen) <= tol * max(1.0, abs(beklenen))
        else:
            ok = bulunan == beklenen
        return self.kontrol(ad, ok, f"→ bulunan {bulunan!r}, beklenen {beklenen!r}")

    def atla(self, sebep):
        self.atlandi += 1
        print(f"   {SARI}⊘ atlandı{SIFIR}  {sebep}")

    def yazdir(self):
        toplam = self.gecti + self.kaldi
        if self.kaldi == 0:
            print(f"   {YESIL}✔ {self.gecti}/{toplam} geçti{SIFIR}"
                  + (f"  {GRI}({self.atlandi} atlandı){SIFIR}" if self.atlandi else ""))
        else:
            print(f"   {KIRMIZI}✘ {self.kaldi} BAŞARISIZ{SIFIR}  ({self.gecti}/{toplam} geçti)")
            for h in self.hatalar[:25]:
                print(f"       {KIRMIZI}·{SIFIR} {h}")
            if len(self.hatalar) > 25:
                print(f"       {GRI}… ve {len(self.hatalar)-25} tane daha{SIFIR}")
        return self.kaldi == 0


def P_std(sonuc):
    """TS EN 81-20'nin P'si  —  MOTORDAN OKUNMAZ, tablolardan yeniden kurulur.

    m.5.2.1.8.5 · m.5.2.1.8.6 · m.5.7.2.3.2 üçü de aynı cümleyle tanımlar:
    "P is the mass of the empty car and components supported by the car,
    i.e. part of the travelling cable, compensating ropes/chains (if any),
    etc."  Yani boş kabin kütlesi DEĞİL.

    Testler bu değeri bağımsız kursun diye burada durur;  motorun kendi
    ``P_std``ini okumak, hesabı kendisiyle doğrulamak olurdu.
    """
    from engine.uygulama import mukavemet_tablolari as T
    from engine.uygulama import sabitler as S
    g = sonuc["girdi"]
    r = 2 if str(g["aski_orani"]).strip() in ("2", "2:1") else 1
    H = g["seyir_mesafesi"]
    MSR = r * H * T.halat_agirlik(g["halat_capi"]) * g["halat_adedi"]
    lam = ((S.VARSAYILAN["denge_zinciri_orani"] or 0) / 100.0
           if str(g.get("denge_zinciri") or "").strip() == "Var" else 0.0)
    mt = sum(T.kablo_agirligi(g.get(k)) or 0.0
             for k in ("kablo_tipi_1", "kablo_tipi_2"))
    return g["kabin_agirligi"] + lam * MSR + 0.5 * H * mt

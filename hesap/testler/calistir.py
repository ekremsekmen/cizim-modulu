# -*- coding: utf-8 -*-
"""
TÜM TESTLERİ ÇALIŞTIR

    python3 testler/calistir.py            → hepsi
    python3 testler/calistir.py 2 3        → yalnız 2. ve 3. testler

Arayüz testleri ( 5 · 6 ) için program açık olmalıdır ( baslat.command ).
Eksik olan bileşenlerin testi atlanır, diğerleri yine çalışır.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from testler.ortak import GRI, KIRMIZI, SIFIR, YESIL      # noqa: E402

TESTLER = [
    ("1", "Avan referans taraması", "testler.test_avan_tarama"),
    ("2", "Kenar durumlar", "testler.test_kenar_durum"),
    ("3", "Girdi dayanıklılığı", "testler.test_dayaniklilik"),
    ("4", "Çıktı bütünlüğü", "testler.test_ciktilar"),
    ("5", "Arayüz", "testler.test_arayuz"),
    ("6", "Proje dosyası geri yükleme", "testler.test_geri_yukleme"),
    ("7", "Altın çıktı", "testler.test_altin"),
    ("8", "Mukavemet tabloları", "testler.test_mukavemet_tablolari"),
    ("9", "Mukavemet motoru", "testler.test_mukavemet"),
    ("10", "Mukavemet referans taraması", "testler.test_mukavemet_tarama"),
    ("11", "Uygulama projesi", "testler.test_uygulama"),
    #  Dış referanslar:  öteki testlerin hepsi motoru KENDİ kaynağımıza
    #  ( dondurulmuş referans · altın çıktı ) karşı denetler;  bu, bizden
    #  bağımsız iki programın yayımlanmış paftalarına karşı denetler.
    ("12", "Dış referans paftaları", "testler.test_referans_paftalar"),
    #  Canlı hesap:  motor doğru hesaplasa bile ekran eski bir girdinin
    #  sonucunu gösterebilir ya da eski bir değeri sonraki hesaba taşıyabilir.
    #  Her girdi değişikliğinden sonra ekran = formun taze hesabı = çıktı.
    ("13", "Canlı hesap tutarlılığı", "testler.test_canli_hesap"),
    #  İşlem satırları:  sonuç doğru olsa bile paftadaki işlem satırı o sonucu
    #  vermeyebilir ( eksik parantez, yazılmamış yuvarlama, eksik hane ).  Her
    #  satır, basıldığı hanelerle yeniden hesaplanır.
    ("14", "Pafta işlem satırları", "testler.test_islem_satirlari"),
]


def main(argv):
    secim = [a for a in argv if a.isdigit()]
    print("\n" + "═" * 68)
    print("  ASANSÖR AVAN HESAPLAMA PROGRAMI  —  DOĞRULAMA PAKETİ")
    print("═" * 68)

    baslangic = time.time()
    sonuclar = []
    for no, ad, modul_adi in TESTLER:
        if secim and no not in secim:
            continue
        modul = __import__(modul_adi, fromlist=["calistir"])
        t0 = time.time()
        try:
            rapor = modul.calistir()
        except Exception as e:                                   # noqa: BLE001
            import traceback
            print(f"   {KIRMIZI}✘ test çalıştırılamadı: {e}{SIFIR}")
            traceback.print_exc()
            sonuclar.append((no, ad, False, 0, 0, 0, time.time() - t0))
            continue
        tamam = rapor.yazdir()
        sonuclar.append((no, ad, tamam, rapor.gecti, rapor.kaldi, rapor.atlandi,
                         time.time() - t0))

    print("\n" + "═" * 68)
    print("  ÖZET")
    print("═" * 68)
    tg = tk = ta = 0
    for no, ad, tamam, gecti, kaldi, atlandi, sure in sonuclar:
        tg += gecti; tk += kaldi; ta += atlandi
        isaret = f"{YESIL}✔{SIFIR}" if tamam else f"{KIRMIZI}✘{SIFIR}"
        ek = f"  {GRI}({atlandi} atlandı){SIFIR}" if atlandi else ""
        print(f"  {isaret}  TEST {no}  {ad:<26} {gecti:>5} geçti  "
              f"{kaldi:>3} kaldı  {GRI}{sure:5.1f} sn{SIFIR}{ek}")
    print("─" * 68)
    #  ÇÖKEN TEST DE BAŞARISIZLIKTIR.  Bir test modülü istisna atınca
    #  ( kaldi = 0 ) sayaç artmıyor, özet "0 başarısız" diyor ve çıkış kodu 0
    #  oluyordu:  sürekli tümleştirme YEŞİL görünürken test hiç koşmamış
    #  oluyordu.  `tamam` bayrağı yalnız ✔/✘ simgesinde kullanılıyordu.
    coken = [no for no, _ad, tamam, _g, kaldi, _a, _s in sonuclar
             if not tamam and kaldi == 0]
    renk = YESIL if (tk == 0 and not coken) else KIRMIZI
    print(f"  {renk}TOPLAM : {tg} kontrol geçti, {tk} başarısız{SIFIR}"
          f"{f'  ({ta} bölüm atlandı)' if ta else ''}"
          f"   {GRI}· {time.time()-baslangic:.1f} sn{SIFIR}")
    if coken:
        print(f"  {KIRMIZI}✘ ÇALIŞTIRILAMAYAN TEST : {', '.join(coken)}"
              f"   —   bu bir BAŞARISIZLIKTIR{SIFIR}")
    print("═" * 68 + "\n")
    return 0 if (tk == 0 and not coken) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

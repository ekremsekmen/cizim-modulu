# -*- coding: utf-8 -*-
"""
TEST 5  —  ARAYÜZ (tarayıcı)

Playwright kurulu değilse ya da sunucu kapalıysa zarifçe atlanır.
Kurmak için:  pip install playwright  &&  python3 -m playwright install chromium
"""
import json
import os
import sys
import urllib.request

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KOK)

from testler.ortak import Rapor      # noqa: E402

BASE = os.environ.get("AVAN_TEST_URL", "http://127.0.0.1:8780")


def _sunucu_var():
    try:
        urllib.request.urlopen(BASE + "/api/saglik", timeout=5).read()
        return True
    except Exception:                                    # noqa: BLE001
        return False


def uygulamayaGir(pg):
    """
    AÇILIŞ EKRANI ( 2.6 ):  program önce hangi projenin hazırlanacağını
    sorar.  Sayfa her yüklendiğinde / yenilendiğinde tekrar oraya döner,
    bu yüzden hesap ekranına geçmek için Avan Proje seçilir.
    """
    if pg.is_visible("#giris"):
        pg.click("#gk_avan")
        pg.wait_for_timeout(350)


def adetSec(pg, n):
    """
    Trafik sekmesinde KAÇ ASANSÖR TANIMLANDIĞINI seçer.
    Gövde tektir ( #s-coklu ); yöntemi ( PAFTA / PAFTA-COKLU ) program
    asansörlerin aynı tip olup olmamasına bakarak kendisi seçer.
    Dönen: o an açık olan gövdenin kimliği ( her zaman "s-coklu" ).
    """
    pg.click('.sekme[data-sekme="trafik"]')
    pg.wait_for_timeout(250)
    if pg.evaluate("TRAFIK_ADET") != n:
        pg.click(f'.sayfa:not([hidden]) .adet-dg:nth-child({n})')
        pg.wait_for_timeout(1500)
    acik = pg.evaluate("[...document.querySelectorAll('.sayfa')]"
                       ".filter(s=>!s.hidden).map(s=>s.id)")
    return acik[0] if acik else None


def _mrl_sec(pg, mrl):
    """Makine dairesi seçimi — İKİ DÜĞMELİ görünüm.

    Alan veri modelinde hâlâ bir onay kutusudur ama ekranda iki düğmeyle
    gösterilir ve kutu görsel olarak saklanır ( .gorsel-gizli ).  Playwright
    saklı kutuya dokunamaz;  test de KULLANICI GİBİ düğmeye basar — zaten
    doğrusu budur, ekranda olmayan bir şeyi sürmek gerçek kullanımı sınamaz.
    """
    #  Düğme kapalı bir akordeonun içindeyse tıklanamaz;  gruplar açılır.
    pg.evaluate("mTumGruplariAc()")
    pg.click(f'.secim-ikili[data-icin="m_mk_yok"] .secim-dg[data-deger="{1 if mrl else 0}"]')
    pg.wait_for_timeout(300)


def calistir():
    print("\n\033[1mTEST 5 — ARAYÜZ (tarayıcı)\033[0m")
    r = Rapor("Arayüz")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        r.atla("Playwright kurulu değil — arayüz testi atlandı "
               "(pip install playwright && python3 -m playwright install chromium)")
        return r
    if not _sunucu_var():
        r.atla(f"Sunucu {BASE} adresinde çalışmıyor — arayüz testi atlandı")
        return r

    with sync_playwright() as pw:
        try:
            tarayici = pw.chromium.launch()
        except Exception as e:                           # noqa: BLE001
            r.atla(f"Chromium başlatılamadı: {e}")
            return r
        pg = tarayici.new_page(viewport={"width": 1440, "height": 1000})
        konsol = []
        pg.on("console", lambda m: konsol.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: konsol.append("PAGEERROR " + str(e)))
        pg.goto(BASE, wait_until="networkidle")
        pg.wait_for_timeout(800)

        r.kontrol("sayfa başlığı doğru", "Asansör Proje" in pg.title(),
                  f"→ {pg.title()!r}")

        # ---------------------------------------------------------------
        #  EKRAN ve PAFTA AYNI SAYIYI AYNI YAZAR
        #  Ekran sayıyı JavaScript'in toLocaleString'iyle, pafta Python'un
        #  biçimlendirmesiyle yuvarlıyordu;  ikisi de sayının İKİLİ değerine
        #  bakıyor ama tam yarımda farklı kural uyguluyordu:  0,125 ekranda
        #  "0,13", paftada "0,12";  9,325 ( ikilide 9,32499… ) ikisinde de
        #  "9,32".  Artık ikisi aynı kuralla ( yarımı yukarı, 12 anlamlı
        #  haneden gürültü atılarak ) yuvarlar.
        # ---------------------------------------------------------------
        import random as _rnd
        from engine.ortak.steps import tr as _tr_py
        _rnd.seed(20260922)
        _ozel = (0.125, 0.375, 2.5, 3.5, 0.5, 1.5, 1.005, -1.005, 9.325, 9.625,
                 2.675, 347.835, 4978.575, 279.085, 1234.5, 1234567.895, 0.001,
                 -0.001, 0, 1e-7, 12.3456789, 99.995, 999999.995, 7, -7.5)
        _degerler = [[x, d] for x in _ozel for d in range(5)]
        _degerler += [[round(_rnd.uniform(-5000, 5000), _rnd.randint(0, 6)),
                       _rnd.randint(0, 4)] for _ in range(3000)]
        _js = pg.evaluate("V => V.map(([x, d]) => tr(x, d))", _degerler)
        _ayri = [(x, d, _tr_py(x, d), j) for (x, d), j in zip(_degerler, _js)
                 if _tr_py(x, d) != j]
        r.kontrol(f"ekran ve pafta {len(_degerler)} sayıyı aynı biçimde yazıyor",
                  not _ayri, f"→ {len(_ayri)} fark, ör. {_ayri[:4]}")
        r.esit("ekran 9,325'i 9,33 yazıyor ( ikili gürültü )",
               pg.evaluate("tr(9.325, 2)"), "9,33")
        r.esit("ekran 2,5'i 3 yazıyor ( bankacı kuralı değil )",
               pg.evaluate("tr(2.5, 0)"), "3")

        # ---------------------------------------------------------------
        #  AÇILIŞ EKRANI  ( 2.6 )
        #  Program doğrudan hesap ekranına düşmez:  önce hangi projenin
        #  hazırlanacağı seçilir.  İki mod da hazırdır ve ŞERİTLERİ AYRIDIR —
        #  avan sekmeleri uygulama modunda, mukavemet sekmesi avan modunda
        #  görünmemelidir;  yoksa iki ayrı hesap birbirine karışır.
        # ---------------------------------------------------------------
        pg.on("dialog", lambda d: d.dismiss())
        r.kontrol("açılışta proje seçim ekranı görünüyor", pg.is_visible("#giris"))
        r.kontrol("açılışta hesap sekmeleri gizli",
                  not pg.is_visible('.sekme[data-sekme="avan"]'))
        r.esit("açılışta iki seçenek var",
               pg.eval_on_selector_all(".giris-kart", "e=>e.length"), 2)
        r.kontrol("avan seçeneği hazır işaretli", "HAZIR" in (pg.inner_text("#gk_avan") or ""))
        r.kontrol("uygulama projesi hazır işaretli",
                  "HAZIR" in (pg.inner_text("#gk_uygulama") or ""))

        #  --- uygulama projesi ( mukavemet ) ---
        pg.click("#gk_uygulama")
        pg.wait_for_timeout(2000)
        r.kontrol("uygulama projesi açılıyor",
                  (not pg.is_visible("#giris"))
                  and pg.is_visible('.sekme[data-sekme="mukavemet"]'))
        r.kontrol("uygulama modunda avan sekmeleri gizli",
                  not pg.is_visible('.sekme[data-sekme="avan"]')
                  and not pg.is_visible('.sekme[data-sekme="trafik"]'))
        #  Sabitler / Ofis Standardı İKİ MODA DA aittir:  elektrik ve
        #  topraklama hesapları oradaki değerleri kullanır.
        r.kontrol("uygulama modunda Sabitler sekmesi görünür",
                  pg.is_visible('.sekme[data-sekme="sabitler"]'))

        #  ── PROJE SEKMESİ / ASANSÖR SEKMELERİ
        #  Uygulama modu artık doğrudan girdi formuna düşmez.  Bir PROJE'de
        #  dörde kadar asansör olabilir;  PROJE sekmesinde binaya ait olan
        #  şeyler ( kapak · asansör adedi · proje geneli girdiler · çıktılar )
        #  BİR KEZ durur, her asansörün kendi hesabı KENDİ SEKMESİNDEDİR.
        r.kontrol("uygulama modu PROJE sekmesiyle açılıyor",
                  pg.is_visible("#s-uygproje") and not pg.is_visible("#s-mukavemet"))
        #  PROJE GENELİ ALANLAR ASANSÖR FORMUNDA, kendi grubunun içinde ve
        #  HER sekmede.  Bir süre ayrı bir karta çekilmişlerdi;  topraklamayı
        #  girmek için sekme değiştirmek gerekiyordu.  Değer TEKTİR — rozet
        #  bunu söyler, mAsansorKaydet de onları asansöre kopyalamaz.
        r.kontrol("proje geneli alanlar asansör formunda",
                  pg.evaluate("MUK.proje_geneli.every(a=>"
                              "!!document.querySelector('#m_form #'+M_ID(a)))"))
        r.esit("proje geneli alanların hepsi rozetli",
               pg.eval_on_selector_all("#m_form .pg-rozet", "e=>e.length"),
               pg.evaluate("MUK.proje_geneli.length"))
        r.kontrol("ayrı proje geneli kartı kalmadı",
                  pg.query_selector("#p_form") is None)
        r.esit("asansör adedi seçmeli  ( 1 - 4 )",
               pg.eval_on_selector_all("#m_adet option", "e=>e.map(x=>x.value)"),
               ["1", "2", "3", "4"])
        r.esit("açılışta tek asansör sekmesi",
               pg.eval_on_selector_all("#m_asansor_sekmeleri .sekme", "e=>e.length"), 1)
        #  Girdi formu asansör sekmesindedir — sonraki kontroller oradan okur.
        pg.evaluate("mAsansorSekmesi(0)")
        pg.wait_for_timeout(1200)
        r.kontrol("asansör sekmesi hesap formunu açıyor",
                  pg.is_visible("#s-mukavemet") and not pg.is_visible("#s-uygproje"))
        #  YENİ PROJEDE KABİN AĞIRLIĞI TABLODAN.  Alan Gelişmiş'te gizli durur;
        #  örnek projenin 700 kg'ıyla açılınca 800 kg yükte "elle girilmiş"
        #  sayılıyor ve farkına varılmadan tablo dışı bir kütleyle hesap yapılıyordu.
        pg.wait_for_function("() => SON.m && SON.m.aktif && $('m_kabin_agirligi').value !== ''",
                             timeout=8000)
        from engine.ortak import ofis as _OFg
        r.esit("yeni projede kabin ağırlığı ofis tablosundan",
               pg.input_value("#m_kabin_agirligi"),
               str(int(_OFg.bos_kabin_kutlesi(int(pg.input_value("#m_beyan_yuku"))))))
        r.kontrol("yeni projede kabin ağırlığının kaynağı tablo",
                  "KABUL" in (pg.evaluate("SON.m.girdi.kabin_agirligi_kaynak") or ""))
        #  FORMUN BAŞINDAKİ AÇIKLAMA KUTULARI KALDIRILDI.  Ortak girdi
        #  köprüsü ve "bu bölüm uygulama projesine aittir" metni her açılışta
        #  girdilerin önünü kapatıyordu;  köprü zaten görünmez çalışıyor.
        #  Eski hücre adresleri de ( "· B132" ) etiketten çıkarıldı.
        r.kontrol("form açıklama kutusuyla başlamıyor",
                  "Ortak girdiler bir kez girilir" not in pg.inner_text("#m_form")
                  and "uygulama projesine" not in pg.inner_text("#m_form"))
        r.esit("etiketlerde hücre adresi yok",
               pg.eval_on_selector_all(
                   "#m_form label",
                   "e=>e.filter(x=>/·\\s*[A-Z]{1,2}[0-9]{1,4}\\b/.test(x.textContent))"
                   ".map(x=>x.textContent.trim())"), [])
        r.kontrol("başlık uygulama projesini gösteriyor",
                  "UYGULAMA" in pg.inner_text("#ust_ad"),
                  f"→ {pg.inner_text('#ust_ad')!r}")
        #  GRUP SAYISI SÖZLEŞMEDEN OKUNUR ( API'nin forma verdiği gruplar:
        #  motorunkiler + çizim grubu ).  Çivili sayı, forma bir grup
        #  eklendiğinde ( "Makine yerleşimi" ) sessizce eskiyordu.
        from engine.uygulama import girdi as _UGrp
        from api import uygulama as _UAp
        from cizim import kopru as _CKp
        _grup_sayisi = len(_UAp.uygulama_alanlari()["gruplar"])
        r.esit(f"uygulama formu {_grup_sayisi} grup üretti",
               pg.eval_on_selector_all("#m_form .m-grup", "e=>e.length"),
               _grup_sayisi)

        #  ── GİRDİ AKORDEONU  ( 86 girdi tek sütunda bulunamıyordu )
        #  Kapalı grup DOM'da KALIR;  yalnız görünmez.  Hesabın okuduğu alan
        #  kümesi açık/kapalı durumdan ETKİLENMEMELİ — asıl kontrol budur.
        r.esit("akordeon: tek grup açık başlıyor",
               pg.eval_on_selector_all("#m_form .m-grup.acik", "e=>e.length"), 1)
        _ga = pg.evaluate("Object.keys(mukavemetGirdi()).length")
        pg.evaluate("mGrupAc(6)")
        _gb = pg.evaluate("Object.keys(mukavemetGirdi()).length")
        pg.evaluate("document.getElementById('m_ara').value='halat';mAramaUygula()")
        _gc = pg.evaluate("Object.keys(mukavemetGirdi()).length")
        _bulunan = pg.eval_on_selector_all(
            "#m_form .alan", "e=>e.filter(x=>!x.hidden).length")
        pg.evaluate("document.getElementById('m_ara').value='';mAramaUygula()")
        _gd = pg.evaluate("Object.keys(mukavemetGirdi()).length")
        r.kontrol("akordeon: okunan girdi kümesi HİÇ değişmiyor",
                  len({_ga, _gb, _gc, _gd}) == 1,
                  f"→ {_ga} · {_gb} · {_gc} · {_gd}")
        r.kontrol("akordeon: arama alanları süzüyor",
                  0 < _bulunan < _ga, f"→ {_bulunan} alan kaldı")
        r.kontrol("akordeon: arama temizlenince sayaçlar geri geliyor",
                  pg.eval_on_selector_all(
                      "#m_form .m-grup-adet",
                      "e=>e.every(x=>x.textContent.trim()===x.dataset.toplam)"),
                  "→ arama sayaçları başlıkta kaldı")
        #  SONUÇTAN GİRDİYE ATLAMA — eşleme motordan gelir ( BOLUM_GRUBU ).
        #  Bir hesap bölümü İKİ girdi grubundan beslenebilir ve kalan
        #  kontrolün alanı ikincisinde olabilir:  4. bölüm "tahrik kasnağı
        #  çapını büyütün" der ama Dt alanı MAKİNE VE MOTOR grubundadır,
        #  10. bölümün kuyu dibi sığınma yüksekliği ise TAMPONLAR'daki baba
        #  yüksekliğinden gelir.  Eskiden tek grup açılıyordu ve mühendis
        #  aradığı alanı açılan grupta bulamıyordu.
        #  ANAHTAR BÖLÜMÜN KİMLİĞİDİR, NUMARASI DEĞİL:  numara projeye göre
        #  kayıyor ve proje geneli bölümler hiç eşlenemiyordu.
        for _k in ("motor_gucu", "makine_konstruksiyonu", "aski_halatlari",
                   "kabin_raylari", "siginma_alanlari", "kabin_aydinlatma",
                   "kuyu_aydinlatma", "gerilim_dusumu"):
            pg.evaluate(f"mGirdiyeGit('{_k}')")
            r.esit(f"bölüm {_k} → girdi grupları",
                   sorted(pg.eval_on_selector_all(
                       "#m_form .m-grup.acik", "e=>e.map(x=>x.dataset.ad)")),
                   sorted(pg.evaluate(f"mBolumGruplari('{_k}')")))
        #  Sonuç satırı kimliği taşımalı — numaradan ayıklamıyoruz artık
        r.kontrol("sonuç bölümleri kimlik taşıyor",
                  pg.evaluate("SON.m.bolumler.every(b=>!!b.kimlik)"),
                  f"→ {pg.evaluate('SON.m.bolumler.map(b=>b.kimlik)')}")
        r.esit("aynı bölüm numarası kaysa da kimliği duruyor",
               pg.evaluate("SON.m.bolumler.map(b=>b.kimlik)")[:4],
               ["motor_gucu", "makine_konstruksiyonu", "kabin_alani",
                "aski_halatlari"])
        pg.evaluate("mGirdiyeGit('aski_halatlari')")
        r.kontrol("halat bölümü hem halatı hem tahrik kasnağını açıyor",
                  pg.is_visible("#m_halat_capi")
                  and pg.is_visible("#m_tahrik_kasnak_capi"))
        pg.evaluate("mGirdiyeGit('siginma_alanlari')")
        #  Kabin tamponu kaidesi formda sorulmaz ( kuyu dibi zincirinden );
        #  tampon grubunun görünür alanı ağırlık tamponu kaidesidir.
        r.kontrol("sığınma bölümü hem kuyuyu hem tamponları açıyor",
                  pg.is_visible("#m_son_kat_yuksekligi")
                  and pg.is_visible("#m_agirlik_tampon_baba"))
        #  ÜÇ GRUP AÇILMAZ — akordeon listeye dönerse aranan alan yine kaybolur
        r.esit("atlama en çok iki grup açıyor",
               pg.evaluate("Math.max(...Object.values(MUK.bolum_grubu)"
                           ".map(v=>v.length))"), 2)
        #  Öteki gruplar KAPANIR:  atlama akordeonu açık bırakmaz
        r.esit("atlamadan sonra yalnız eşlemedeki gruplar açık",
               pg.eval_on_selector_all("#m_form .m-grup.acik", "e=>e.length"),
               len(pg.evaluate("mBolumGruplari('siginma_alanlari')")))
        #  BAŞLIK AÇ/KAPADIR.  Açık gruba yeniden tıklamak eskiden hiçbir şey
        #  yapmıyordu — grup bir açıldı mı kapanmıyordu.
        pg.evaluate("mGrupAc(5)")
        _ac1 = pg.eval_on_selector_all("#m_form .m-grup.acik", "e=>e.length")
        pg.click('#m_form .m-grup[data-grup="5"] .m-grup-bas')
        pg.wait_for_timeout(300)
        _ac2 = pg.eval_on_selector_all("#m_form .m-grup.acik", "e=>e.length")
        pg.click('#m_form .m-grup[data-grup="5"] .m-grup-bas')
        pg.wait_for_timeout(300)
        _ac3 = pg.eval_on_selector_all("#m_form .m-grup.acik", "e=>e.length")
        r.esit("başlığa tıklamak grubu açıp kapatıyor", [_ac1, _ac2, _ac3], [1, 0, 1])
        #  Kapalıyken de okunan girdi kümesi AYNI kalmalı  ( görünüm ≠ hesap )
        pg.evaluate("mGruplariKapat()")
        r.esit("hepsi kapalıyken okunan girdi kümesi değişmiyor",
               pg.evaluate("Object.keys(mukavemetGirdi()).length"), _ga)

        #  ── GELİŞMİŞ BÖLÜMLERİ  ( ofisin / ürünün hep aynı girilen değerleri )
        #  Grubun altında KAPALI durur;  alanlar okunur ve hesaba girer.
        #  Gizli değer sessiz kalmamalı:  sayaç · işaret · hatada açılma · arama.
        from engine.uygulama import mukavemet_girdi as _MGg
        r.esit("gelişmiş: her gelişmiş alan kapalı bölümde",
               pg.evaluate("mAlanlar(f=>f.gelismis).filter(f=>{const e=$(M_ID(f.anahtar));"
                           "return !e || !e.closest('.m-gelismis-ic');}).map(f=>f.anahtar)"), [])
        r.esit("gelişmiş: görünür alan gelişmiş bölümde değil",
               pg.evaluate("mAlanlar(f=>!f.gelismis).filter(f=>{const e=$(M_ID(f.anahtar));"
                           "return e && e.closest('.m-gelismis-ic');}).map(f=>f.anahtar)"), [])
        #  Hesaba girmediği için kaldırılan alanlar hesabın gruplarına dönmez;
        #  çizim kullanıyorsa ( KD, ağırlık ray ekseni – duvar ) kendi tasarım
        #  grubunda bir kez sorulur ( tasarım şeması ).
        for _yok, _grup in (("kuyu_derinligi", "Kuyu ve katlar"),
                            ("agirlik_ray_duvar", "Karşı ağırlık"),
                            ("dikine_kiris_tipi", None), ("yan_yatak_tipi", None)):
            if _grup:
                r.kontrol(f"gelişmiş: '{_yok}' bir kez, '{_grup}' grubunda",
                          pg.evaluate(f"MUK.gruplar.filter(g=>g.alanlar.some(f=>f.anahtar==="
                                      f"'{_yok}')).map(g=>g.ad)") == [_grup])
            else:
                r.kontrol(f"gelişmiş: kaldırılan '{_yok}' formda yok",
                          pg.query_selector(f"#m_{_yok}") is None)
        _gi = pg.evaluate("MUK.gruplar.findIndex(g=>g.ad==='Askı ve halatlar')")
        pg.evaluate(f"mGrupAc({_gi})")
        pg.wait_for_timeout(200)
        r.kontrol("gelişmiş: grup açılınca görünür alan görünüyor, gelişmiş kapalı",
                  pg.is_visible("#m_halat_capi") and not pg.is_visible("#m_acil_frenleme_a"))
        _bas = f'#m_form .m-gelismis[data-grup="{_gi}"] .m-gelismis-bas'
        pg.click(_bas)
        pg.wait_for_timeout(200)
        _acik = pg.is_visible("#m_acil_frenleme_a")
        pg.click(_bas)
        pg.wait_for_timeout(200)
        r.kontrol("gelişmiş: başlığa tıklamak açıp kapatıyor",
                  _acik and not pg.is_visible("#m_acil_frenleme_a"))
        r.esit("gelişmiş: kapalıyken okunan girdi kümesi değişmiyor",
               pg.evaluate("Object.keys(mukavemetGirdi()).length"), _ga)
        _sayac = f'#m_form .m-gelismis[data-grup="{_gi}"] .m-gelismis-sayac'
        _once = pg.inner_text(_sayac).strip()
        #  Varsayılan SAYI OLARAK YAZILMAZ, açılıştaki değer okunur:  0,8
        #  çivilenmişti ve varsayılan 0,5'e ( EN 81-50 m.5.11.2.2.2 tabanı )
        #  çekilince "varsayılana dön" adımı aslında 0,8'i YENİ bir değer
        #  olarak giriyordu — arayüz doğruydu, test bayattı.
        _varsayilan_a = pg.input_value("#m_acil_frenleme_a")
        pg.evaluate("(()=>{const e=$('m_acil_frenleme_a');const v=e.value;"
                    "e.value = (v==='0,5'?'0,6':'0,5');"
                    "e.dispatchEvent(new Event('input',{bubbles:true}));})()")
        pg.wait_for_timeout(300)
        _sonra = pg.evaluate(f"document.querySelector('{_sayac}').textContent")
        r.kontrol("gelişmiş: değer değişince sayaç artıyor ve alan işaretleniyor",
                  _sonra != _once and "değiştirildi" in _sonra
                  and pg.evaluate("$('m_acil_frenleme_a').closest('.alan')"
                                  ".classList.contains('degisti')"),
                  f"→ {_once!r} → {_sonra!r}")
        pg.evaluate("(v)=>{const e=$('m_acil_frenleme_a');e.value=v;"
                    "e.dispatchEvent(new Event('input',{bubbles:true}));}",
                    _varsayilan_a)
        pg.wait_for_timeout(300)
        r.kontrol("gelişmiş: varsayılana dönünce işaret kalkıyor",
                  not pg.evaluate("$('m_acil_frenleme_a').closest('.alan')"
                                  ".classList.contains('degisti')"))
        #  Nps · Npr çizilen kasnaklardan sayılır ( cizim/olculer ):  formda
        #  kutuları yok — girilen bir sayı çizimle çelişemez.
        r.kontrol("Nps · Npr formda yok ( çizimden gelir )",
                  pg.evaluate("['m_kasnak_tek_yon','m_kasnak_ters_yon']"
                              ".every(k => document.getElementById(k) === null)"))
        #  BOŞ BIRAKILAN ALAN "DEĞİŞTİRİLDİ" SAYILMAZ  ( S1 · S2 boşken motor
        #  varsayılana düşer;  işaret "2 değiştirildi" diyordu ).
        _s1 = pg.input_value("#m_kolon_kesit")
        pg.evaluate("(()=>{const e=$('m_kolon_kesit');e.value='';"
                    "e.dispatchEvent(new Event('input',{bubbles:true}));})()")
        pg.wait_for_timeout(400)
        r.kontrol("gelişmiş: boş bırakılan S1 değiştirilmiş sayılmıyor",
                  not pg.evaluate("$('m_kolon_kesit').closest('.alan')"
                                  ".classList.contains('degisti')"))
        pg.evaluate(f"(()=>{{const e=$('m_kolon_kesit');e.value={_s1!r};"
                    "e.dispatchEvent(new Event('input',{bubbles:true}));})()")
        pg.wait_for_timeout(400)
        #  HESABI DURDURAN HATA GİZLİ ALANDAYSA bölüm kendiliğinden açılır
        pg.evaluate("mGruplariKapat(); mGelismisleriKapat()")
        _kpa = pg.input_value("#m_kabin_paten_arasi")
        pg.evaluate("(()=>{const e=$('m_kabin_paten_arasi');e.value='-5';"
                    "e.dispatchEvent(new Event('input',{bubbles:true}));})()")
        pg.wait_for_function("() => SON.m && SON.m.aktif === false", timeout=8000)
        r.kontrol("gelişmiş: gizli alandaki hata bölümünü açıyor",
                  pg.evaluate("!$('m_kabin_paten_arasi').closest('.m-gelismis-ic').hidden"))
        pg.evaluate(f"(()=>{{const e=$('m_kabin_paten_arasi');e.value={_kpa!r};"
                    "e.dispatchEvent(new Event('input',{bubbles:true}));})()")
        pg.wait_for_function("() => SON.m && SON.m.aktif === true", timeout=8000)
        #  ARAMA GİZLİ ALANLARI DA BULUR, temizlenince bölüm yine kapanır
        pg.evaluate("mGelismisleriKapat();"
                    "document.getElementById('m_ara').value='regülatör kanal';mAramaUygula()")
        r.kontrol("gelişmiş: arama gizli alanı buluyor",
                  pg.is_visible("#m_reg_kanal_acisi"))
        pg.evaluate("document.getElementById('m_ara').value='';mAramaUygula()")
        r.kontrol("gelişmiş: arama temizlenince bölüm kapanıyor",
                  pg.evaluate("$('m_reg_kanal_acisi').closest('.m-gelismis-ic').hidden"))
        r.esit("gelişmiş: tüm grupları aç gelişmişleri de açıyor",
               pg.evaluate("mTumGruplariAc(); [...document.querySelectorAll("
                           "'#m_form .m-gelismis-ic')].filter(x=>x.hidden).length"), 0)
        pg.evaluate("mGelismisleriKapat(); mGruplariKapat()")
        r.esit("gelişmiş: sözleşmedeki gelişmiş alan sayısı formda",
               pg.evaluate("mAlanlar(f=>f.gelismis).length"),
               len(_MGg.GELISMIS_ALANLAR) + len(_UGrp.EK_GELISMIS)
               + sum(1 for _a in _CKp.ALANLAR if _a[6]))
        #  BÖLÜMLERİN HEPSİ TIKLANABİLİR.  Elektrik bölümleri bir süre
        #  eşlemede yoktu:  mukavemet satırları girdisine götürüyor,
        #  aydınlatma ve gerilim düşümü satırları ölü duruyordu.
        #  SAYI ELLE YAZILMAZ — motora bölüm eklenince ( ör. TAMPONLAR )
        #  test kendiliğinden takip etsin;  aranan şey "hepsi gidilebilir".
        _satir = pg.eval_on_selector_all(
            "#m_sonuc tr.m-gidilir td.etiket",
            "e=>e.map(x=>x.textContent.trim().split(' ')[0])")
        r.esit("sonuç tablosunda bölüm satırlarının hepsi tıklanabilir",
               _satir,
               [str(_i) for _i in
                range(1, pg.evaluate("SON.m.bolumler.length") + 1)])

        #  ── ÇOKLU ASANSÖR  ( 1 - 4 asansör, tek proje )
        #  Asansör adedi SEÇİLİR ( ekle/sil değil ):  bir binada kaç asansör
        #  olduğu baştan bellidir, mühendis onu sayar — sırayla ekleyip
        #  silmez.  Form TEK KOPYADIR;  aktif asansörün değerleri onda durur.
        #  Asansör değişince değerler kaybolmamalı — asıl kontrol budur.
        r.esit("çoklu: açılışta tek asansör", pg.evaluate("MUK_ADET"), 1)
        pg.evaluate("mTumGruplariAc()")
        pg.fill("#m_asansor_adi", "İnsan 1")
        pg.fill("#m_motor_gucu", "7.5")
        pg.evaluate("mAdetDegisti(2)")
        pg.wait_for_timeout(1400)
        r.esit("çoklu: adet 2 seçildi", pg.evaluate("MUK_ADET"), 2)
        r.esit("çoklu: şeritte iki asansör sekmesi",
               pg.eval_on_selector_all("#m_asansor_sekmeleri .sekme", "e=>e.length"), 2)
        #  Adet seçmek AKTİF ASANSÖRÜ DEĞİŞTİRMEZ — mühendis 1'i doldururken
        #  adedi 3 yapınca formu altından çekilmiş olmaz.
        r.esit("çoklu: adet seçimi aktif asansörü değiştirmiyor",
               pg.evaluate("MUK_AKTIF"), 0)
        r.kontrol("çoklu: 1. asansörün değerleri yerinde",
                  pg.input_value("#m_asansor_adi") == "İnsan 1")
        pg.evaluate("mAsansorSekmesi(1)")
        pg.wait_for_timeout(1400)
        r.esit("çoklu: sekmeyle 2. asansöre geçiliyor", pg.evaluate("MUK_AKTIF"), 1)
        r.kontrol("çoklu: yeni asansör 1 nolunun kopyası olarak açılıyor",
                  pg.input_value("#m_motor_gucu") == "7.5",
                  f"→ {pg.input_value('#m_motor_gucu')!r}")
        r.esit("çoklu: kopyanın adı boş", pg.input_value("#m_asansor_adi"), "")
        pg.evaluate("mTumGruplariAc()")
        pg.fill("#m_asansor_adi", "Yük")
        pg.fill("#m_motor_gucu", "15")
        pg.evaluate("mAsansorSec(0)")
        pg.wait_for_timeout(1400)
        r.kontrol("çoklu: 1. asansöre dönünce KENDİ değerleri geliyor",
                  pg.input_value("#m_asansor_adi") == "İnsan 1"
                  and pg.input_value("#m_motor_gucu") == "7.5",
                  f"→ {pg.input_value('#m_asansor_adi')!r} · "
                  f"{pg.input_value('#m_motor_gucu')!r}")
        pg.evaluate("mAsansorSec(1)")
        pg.wait_for_timeout(1400)
        r.kontrol("çoklu: 2. asansörün değerleri korunmuş",
                  pg.input_value("#m_asansor_adi") == "Yük"
                  and pg.input_value("#m_motor_gucu") == "15")
        #  Hesap İKİ asansörü birden döner ve özet tablosu çizilir
        pg.evaluate("hesapMukavemet()")
        pg.wait_for_timeout(2200)
        r.esit("çoklu: sunucu iki asansör hesapladı",
               pg.evaluate("SON.mc && SON.mc.adet"), 2)
        r.kontrol("çoklu: SON.m aktif asansörün sonucu  ( geriye dönük )",
                  pg.evaluate("!!(SON.m && SON.m.bolumler && SON.m.bolumler.length)"))
        r.esit("çoklu: özet iki asansörü listeliyor",
               pg.evaluate("SON.mc.ozet.asansorler.length"), 2)
        r.esit("çoklu: özetteki adlar",
               pg.evaluate("SON.mc.ozet.asansorler.map(a=>a.tanim)"),
               ["İnsan 1", "Yük"])
        #  ASANSÖR LİSTESİ YALNIZ PROJE SEKMESİNDE.  Bir süre her asansörün
        #  sonuç panelinin başına da basılıyordu;  ASANSÖR 2 sekmesinde "1 · 2"
        #  listesi görmek, o sekmenin zaten 2 nolu asansöre ait olduğunu bile
        #  bile tekrar söylemekti — hangi sekmede olunduğu üstteki şeritte yazılı.
        r.kontrol("asansör listesi hesap sayfasında YOK",
                  "ASANSÖRLER" not in pg.inner_text("#m_sonuc"))
        r.esit("hesap panelinin ilk şeridi bölüm sonuçları",
               pg.eval_on_selector("#m_sonuc .serit span", "e=>e.textContent.trim()"),
               "BÖLÜM SONUÇLARI")
        r.kontrol("asansör listesi PROJE sekmesinde duruyor",
                  "PROJE ÖZETİ" in pg.inner_text("#p_ozet"),
                  f"→ {pg.inner_text('#p_ozet')[:60]!r}")
        r.esit("proje özeti iki asansörü listeliyor",
               pg.eval_on_selector_all("#p_ozet table tr", "e=>e.length"), 3)
        #  ── KARŞI AĞIRLIĞIN ÖLÇÜLERİ  ( TS EN 81-50 Ek C.2.2 · Gx · Gy )
        #  Eskiden ikisi de türetiliyordu:  genişlik RAY ARASINDAN ( üç
        #  değere kilitli açılır liste ), derinlik MALZEMEDEN.  Standart
        #  karşı ağırlığın KENDİ ölçülerini veri olarak ister;  türetme
        #  kaldırıldı.  Malzeme seçimi artık yalnız kutuyu DOLDURUR — hesap
        #  her hâlükârda kutudaki sayıyı okur.
        pg.evaluate("mTumGruplariAc()")
        #  Ağırlık ray arası hesaba girmez;  kuyu planını kurar ( DBGW — boşsa
        #  Gy + 60 ) ve karşı ağırlık grubunda bir kez sorulur.
        r.kontrol("ağırlık ray arası bir kez, karşı ağırlık grubunda",
                  pg.evaluate("MUK.gruplar.filter(g=>g.alanlar.some(f=>f.anahtar==="
                              "'agirlik_ray_arasi')).map(g=>g.ad)") == ["Karşı ağırlık"])
        r.kontrol("karşı ağırlık ölçüleri formda",
                  pg.eval_on_selector_all("#m_agirlik_genisligi", "e=>e.length") == 1
                  and pg.eval_on_selector_all("#m_agirlik_derinligi", "e=>e.length") == 1)
        pg.select_option("#m_agirlik_malzemesi", "Pik Döküm")
        pg.wait_for_timeout(1800)
        r.esit("malzeme seçimi derinlik kutusunu dolduruyor",
               pg.input_value("#m_agirlik_derinligi"), "100")
        r.esit("hesap kutudaki derinliği kullanıyor",
               pg.evaluate("SON.m.girdi.agirlik_derinligi"), 100)
        pg.fill("#m_agirlik_derinligi", "180")
        pg.wait_for_timeout(1800)
        r.esit("elle girilen ölçü tabloyu eziyor",
               pg.evaluate("SON.m.girdi.agirlik_derinligi"), 180)
        #  TEMİZLİK — sonraki kontrolleri bozmasın
        pg.select_option("#m_agirlik_malzemesi", "Barit")
        pg.wait_for_timeout(600)
        pg.fill("#m_agirlik_genisligi", "960")
        pg.wait_for_timeout(1800)

        #  ── FORM ALANLARININ TEK GEZİNTİSİ
        #  "Alan nedir, nasıl okunur, nasıl yazılır" bilgisi BİR YERDE
        #  durmalı.  Bir süre aynı gezinti beş ayrı yerde elle yazılıydı ve
        #  hepsi "checkbox ise checked, değilse value" kuralının kendi
        #  kopyasını taşıyordu:  yeni bir alan türü eklendiğinde birinde
        #  unutulur ve asansör değiştirince o alan SESSİZCE kaybolurdu.
        #  Ayrıca ikisi ayrışmıştı — kovadan geri yükleme alanaYaz()
        #  kullanıyor ( seçim kutusunda "6.5" ile "6,5"i eşleştirir ),
        #  asansör yükleme ise ham `e.value =` yapıyordu.
        _js = open(os.path.join(KOK, "static", "uygulama.js"),
                   encoding="utf-8").read()
        for _fn in ("mukavemetGirdi", "mAsansorKaydet", "mAsansorYukle",
                    "mukavemetIstek"):
            _bas = _js.index(f"function {_fn}(")
            _govde = _js[_bas:_js.index("\n}\n", _bas)]
            r.kontrol(f"{_fn} okuma/yazma kuralını KENDİ kopyasında taşımıyor",
                      "checkbox" not in _govde, f"→ {_fn} hâlâ elle okuyor")
        for _yardimci in ("mAlanlar", "mAlanOku", "mAlanYaz",
                          "mFormOku", "mFormaYaz"):
            r.kontrol(f"ortak yardımcı var: {_yardimci}",
                      pg.evaluate(f"typeof {_yardimci} === 'function'"))
        #  KAYDEDİLEN küme = OKUNAN küme − proje geneli.
        #  İkisi ayrışırsa asansör değiştirince alan sessizce kaybolur.
        r.esit("kaydedilen ve okunan alan kümeleri tutarlı",
               pg.evaluate("""() => {
                   mAsansorKaydet();
                   const tum = Object.keys(mukavemetGirdi());
                   const kayit = Object.keys(MUK_ASANSORLER[MUK_AKTIF])
                                       .filter(k => k[0] !== '_');
                   const bek = tum.filter(k => !mProjeGeneliMi(k));
                   return {eksik: bek.filter(k => !kayit.includes(k)),
                           fazla: kayit.filter(k => !bek.includes(k))};
               }"""), {"eksik": [], "fazla": []})
        #  SEÇİM KUTUSU asansörler arasında korunuyor mu — ham `e.value =`
        #  ile yazılırken seçenekle birebir eşleşmeyen değer sessizce düşerdi.
        pg.evaluate("mTumGruplariAc()")
        pg.select_option("#m_halat_capi", "8")
        pg.select_option("#m_makine_tipi", "Dişli")
        pg.evaluate("mAsansorSec(0)")
        pg.wait_for_timeout(1400)
        pg.evaluate("mAsansorSec(1)")
        pg.wait_for_timeout(1400)
        r.esit("seçim kutuları asansör değişince korunuyor",
               [pg.input_value("#m_halat_capi"), pg.input_value("#m_makine_tipi")],
               ["8", "Dişli"])
        pg.evaluate("mTumGruplariAc()")
        pg.select_option("#m_halat_capi", "6,5")
        pg.select_option("#m_makine_tipi", "Dişlisiz")
        pg.wait_for_timeout(1200)

        #  PROJE GENELİ HESAPLAR:  girdi asansör formunda, SONUÇ PROJE
        #  sekmesinde ve paftanın en sonunda — asansör sekmelerinde
        #  tekrarlanmaz.  Makine dairesi ve temel girilince bölümler doğar.
        pg.evaluate("mTumGruplariAc()")
        _mrl_sec(pg, False)
        for _a, _d in (("m_mk_uzunluk", "4"), ("m_mk_genislik", "3"),
                       ("m_temel_a", "20"), ("m_temel_b", "12")):
            pg.fill(f"#{_a}", _d)
        pg.wait_for_timeout(2500)
        #  1 makine dairesi aydınlatması + 4 topraklama  ( 4. bölüm:
        #  topraklama ve potansiyel dengeleme iletkeni kesitleri )
        r.esit("proje geneli bölümler üst seviyede",
               pg.evaluate("(SON.mc.proje_geneli||[]).length"), 5)
        r.esit("proje geneli bölüm hiçbir asansörde kalmıyor",
               pg.evaluate("SON.mc.asansorler.map(a=>a.bolumler.filter("
                           "b=>b.proje_geneli).length)"), [0, 0])
        r.kontrol("proje geneli hesaplar asansörün bölüm listesinde YOK",
                  "TOPRAKLAYICI" not in pg.inner_text("#m_sonuc"))
        #  BLOK ASANSÖR SEKMESİNDEDİR, Proje sayfasında değil:  girdileri
        #  ( MRL · temel ölçüleri · şerit boyu ) da bu sekmede duruyor.
        r.kontrol("proje geneli hesaplar kendi bloğunda",
                  "TOPRAKLAYICI" in pg.inner_text("#p_geneli")
                  and "PROJE GENELİ HESAPLAR" in pg.inner_text("#p_geneli"))
        r.esit("proje geneli bloğu asansör sayfasında",
               pg.eval_on_selector("#p_geneli", "e=>e.closest('section').id"),
               "s-mukavemet")
        #  MRL İŞARETLİYKEN MAKİNE DAİRESİ ÖLÇÜLERİ GİZLENİR.  Ortada duran
        #  ve doldurulabilen kutular "hesap yapılacak" izlenimi veriyordu.
        _gor = ("e=>{const a=e.closest('.alan')||e;"
                " return !(a.hidden||getComputedStyle(a).display==='none');}")
        r.kontrol("MRL kaldırılınca makine dairesi ölçüleri görünür",
                  pg.eval_on_selector("#m_mk_uzunluk", _gor))
        _mrl_sec(pg, True)
        pg.wait_for_timeout(1800)
        r.kontrol("MRL işaretlenince makine dairesi ölçüleri gizlenir",
                  not pg.eval_on_selector("#m_mk_uzunluk", _gor))
        r.kontrol("MRL'de makine dairesi bölümü hesaba girmiyor",
                  pg.evaluate("(SON.mc.proje_geneli||[]).every("
                              "b=>b.baslik.indexOf('MAKİNE DAİRESİ')<0)"),
                  f"→ {pg.evaluate('(SON.mc.proje_geneli||[]).map(b=>b.baslik)')}")
        #  MAKİNE YÜKÜNÜN YOLU YALNIZ MRL'DE SORULUR  ( TS EN 81-20 m.5.7.2.3.7 ).
        #  Makine dairesi varsa makine kendi kaidesindedir;  aynı yükü raya da
        #  bindirmek onu iki kez saymak olur.
        r.kontrol("MRL'de makine yükü yolu soruluyor",
                  pg.eval_on_selector("#m_makine_raya_biniyor", _gor))
        #  BİR RAYA DÜŞEN YÜK SORULMAZ:  "bina yapısına"da hesaba girmez,
        #  "kılavuz raylara"da makine yükü raylara eşit dağıtılır.
        r.kontrol("bir raya düşen makine yükü kutusu yok",
                  pg.evaluate("!document.getElementById('m_raya_binen_yuk')"))
        _mrl_sec(pg, False)
        pg.wait_for_timeout(1800)
        r.kontrol("makine dairesi varken makine yükü yolu SORULMUYOR",
                  not pg.eval_on_selector("#m_makine_raya_biniyor", _gor))
        #  KURAL GİZLEMESİ ARAMA SÜZGECİYLE KAVGA ETMEMELİ.
        #  mTumGruplariAc() ve mAramaUygula() [hidden] üzerinde çalışır;  kural
        #  gizlemesi aynı niteliği kullanırsa grupları açmak gizlenen alanı
        #  GERİ GETİRİYORDU — bu, mk_uzunluk için de geçerli eski bir hataydı.
        pg.evaluate("mTumGruplariAc()")
        pg.wait_for_timeout(900)
        r.kontrol("tüm grupları aç, kural gizlemesini BOZMUYOR",
                  not pg.eval_on_selector("#m_makine_raya_biniyor", _gor),
                  "→ mTumGruplariAc() gizli alanı geri getirdi")
        pg.fill("#m_ara", "makine")
        pg.wait_for_timeout(900)
        r.kontrol("arama süzgeci de kural gizlemesini bozmuyor",
                  not pg.eval_on_selector("#m_makine_raya_biniyor", _gor))
        pg.fill("#m_ara", "")
        pg.wait_for_timeout(900)
        #  Arama temizlenince YALNIZ son seçili grup açık kalır;  kutuya
        #  ulaşabilmek için gruplar yeniden açılır.
        pg.evaluate("mTumGruplariAc()")
        pg.wait_for_timeout(600)
        _mrl_sec(pg, True)
        pg.wait_for_timeout(1500)
        pg.evaluate("mTumGruplariAc()")
        pg.wait_for_timeout(900)
        r.kontrol("MRL'de tüm grupları aç, ölçüleri geri getirmiyor",
                  not pg.eval_on_selector("#m_mk_uzunluk", _gor))
        #  İKİ DÜĞMELİ SEÇİM:  düğme, alttaki kutuyu ve hesabı sürmeli.
        r.kontrol("MRL düğmesi seçili görünüyor",
                  pg.eval_on_selector(
                      '.secim-ikili[data-icin="m_mk_yok"] .secim-dg[data-deger="1"]',
                      "e=>e.classList.contains('secili')"))
        r.kontrol("düğme alttaki onay kutusunu sürüyor",
                  pg.evaluate("document.getElementById('m_mk_yok').checked"))
        #  SEÇİM KUTUSU BOŞA DÜŞMEZ.  Listede olmayan bir değer yazılırsa
        #  ( eski proje dosyası · tablodan kalkan profil ) varsayılan korunur;
        #  boşalan bir <select> "" gönderip motoru "boş bırakılamaz" dedirtiyordu.
        _onceki = pg.input_value("#m_makine_raya_biniyor")
        pg.evaluate("alanaYaz(document.getElementById('m_makine_raya_biniyor'),"
                    " 'artik-olmayan-bir-secenek')")
        r.esit("listede olmayan değer seçim kutusunu BOŞALTMIYOR",
               pg.input_value("#m_makine_raya_biniyor"), _onceki)
        _mrl_sec(pg, False)
        pg.wait_for_timeout(1800)
        #  Girdi hangi asansör sekmesinde yazılırsa yazılsın TEK değerdir
        pg.evaluate("mAsansorSec(0)")
        pg.wait_for_timeout(1600)
        r.esit("proje geneli girdi asansör değişince duruyor",
               pg.input_value("#m_temel_a"), "20")
        pg.evaluate("mAsansorSec(1)")
        pg.wait_for_timeout(1600)
        #  Temizlik — sonraki koşuyu bozmasın
        pg.evaluate("mTumGruplariAc()")
        #  ÖNCE ölçüler boşaltılır, SONRA MRL işaretlenir:  MRL işaretliyken
        #  makine dairesi kutuları gizlenir ve doldurulamaz.
        for _a in ("m_mk_uzunluk", "m_mk_genislik", "m_temel_a",
                   "m_temel_b"):
            pg.fill(f"#{_a}", "")
        _mrl_sec(pg, True)
        pg.wait_for_timeout(2000)
        #  HER ASANSÖR KENDİ GİRDİSİYLE hesaplanır:  sonuçta girdi de dönüyor,
        #  aktif asansörün girdisi ikisine birden gönderilmiş olsa iki motor
        #  gücü aynı görünürdü.
        r.esit("çoklu: her asansör KENDİ girdisiyle hesaplandı",
               pg.evaluate("SON.mc.asansorler.map(a=>a.girdi.motor_gucu)"),
               [7.5, 15.0])
        #  Sekme rozeti ASANSÖRE ÖZELDİR — dördünde aynı rozet çıkmamalı
        r.esit("çoklu: her sekme kendi rozetini taşıyor",
               pg.eval_on_selector_all(
                   "#m_asansor_sekmeleri .sekme",
                   "e=>e.map(x=>x.textContent.trim().slice(0,9))"),
               ["ASANSÖR 1", "ASANSÖR 2"])
        #  PROJE GENELİ alanlar asansörden asansöre TAŞINMAZ
        r.kontrol("çoklu: proje geneli alanlar asansör haritasında yok",
                  pg.evaluate("MUK.proje_geneli.every(a=>"
                              "MUK_ASANSORLER.every(d=>!(a in d)))"),
                  "→ topraklama/makine dairesi asansöre kopyalanmış")
        #  ADEDİ AZALTMAK VERİYİ SİLMEZ:  3→2→3 yapan mühendis girdilerini
        #  geri bulmalı.  Harita dizide kalır, yalnız hesaba girmez.
        pg.evaluate("mAdetDegisti(1)")
        pg.wait_for_timeout(1400)
        r.esit("çoklu: adet 1'e indi", pg.evaluate("MUK_ADET"), 1)
        r.esit("çoklu: tek asansör sekmesi kaldı",
               pg.eval_on_selector_all("#m_asansor_sekmeleri .sekme", "e=>e.length"), 1)
        r.esit("çoklu: azaltmak 2. asansörün verisini SİLMİYOR",
               pg.evaluate("(MUK_ASANSORLER[1]||{}).asansor_adi"), "Yük")
        r.esit("çoklu: hesap yalnız seçilen adedi kapsıyor",
               pg.evaluate("SON.mc && SON.mc.adet"), 1)
        pg.evaluate("mAdetDegisti(2)")
        pg.wait_for_timeout(1400)
        r.esit("çoklu: geri artırınca eski girdi geliyor",
               pg.evaluate("SON.mc.ozet.asansorler.map(a=>a.tanim)"), ["İnsan 1", "Yük"])
        #  TEMİZLİK.  Girdiler tarayıcıda saklanıyor ve testler arasında
        #  silinmiyor;  bu blok motor gücünü değiştirdiği için bırakıldığı
        #  gibi kalırsa BİR SONRAKİ KOŞUDA daha erken bir kontrolü
        #  ( "varsayılanda iki bölüm kalıyor" ) bozar.  Dokunulan alanlar
        #  varsayılanına döndürülür ve ikinci asansör atılır.
        pg.evaluate("mAdetDegisti(1); MUK_ASANSORLER = [{}]; MUK_AKTIF = 0;")
        pg.wait_for_timeout(1200)
        pg.evaluate("mTumGruplariAc()")
        pg.fill("#m_motor_gucu", "4,9")
        pg.fill("#m_asansor_adi", "")
        pg.evaluate("mAsansorKaydet(); yaz()")
        pg.wait_for_timeout(700)
        #  KATLAR TEK TEK SORULMAZ:  seyir mesafesi ve son kat yüksekliği
        #  sıradan iki alandır;  durak kutusu ve ekle / sil düğmeleri yoktur.
        r.esit("varsayılan seyir mesafesi", pg.input_value("#m_seyir_mesafesi"), "21")
        #  4200 ( 29 Eyl, kullanıcı ):  projelerde girilen değer;  3750'de
        #  varsayılan asansörün üst pateni kuyu tavanına giriyordu.
        r.esit("varsayılan son kat yüksekliği",
               pg.input_value("#m_son_kat_yuksekligi"), "4200")
        r.kontrol("durak listesi kutusu ve düğmeleri yok",
                  pg.evaluate("!document.getElementById('m_durak_kutu') && "
                              "!document.getElementById('m_durak_ekle') && "
                              "typeof MUK_DURAK === 'undefined'"))
        pg.set_viewport_size({"width": 1440, "height": 1000})
        pg.wait_for_timeout(400)
        #  VARSAYILAN PROJE İKİ BÖLÜMDEN KALIR — ikisi de kaynak kitabın
        #  gizlediği gerçek yetersizliklerdir:
        #    · ASKI HALATLARI — TS EN 81-20 m.5.5.2.1 kasnak/halat oranını en
        #      az 40 ister, örnekte 240 / 6,5 = 36,9  ( sapma ① ).
        #    · MOTOR GÜCÜ — verim makine tipine bağlı;  dişlisiz + 2:1'de
        #      η′ = 0,75 → 5,90 kW gerekir, seçilen motor 4,9 kW  ( sapma ⑨ ).
        #  Beklenen davranış budur.
        r.kontrol("uygulama hesabı koştu", pg.evaluate("SON.m && SON.m.aktif"),
                  f"→ {pg.evaluate('SON.m && SON.m.hata')}")
        #    · HIZ REGÜLATÖRÜ artık kalmıyor:  devreye sokma kuvveti yoksa
        #      300 N denetlenir, fren bloğuna Fçekme / 2 şartı yazılır ( ⑲ ).
        _kalan = pg.evaluate("SON.m.bolumler.filter(b=>b.sonuc && "
                             "b.sonuc.uygun===false).map(b=>b.baslik)")
        #    · TAHRİK YETENEĞİ artık kalmıyor:  α boşken çizimden gelir —
        #      varsayılan asansörde halat ağırlığa düşey iner, α = 180°.
        #      ( Kitabın örneği 139°'lik sarılma ve sertleştirilmemiş kanalla
        #      acil frenlemede sınırı aşıyordu — sapma ㊳. )
        r.esit("varsayılanda iki bölüm kalıyor", len(_kalan), 2)
        r.kontrol("kalanlar motor gücü ve askı halatları",
                  sorted(x[:1] for x in _kalan) == ["1", "4"], f"→ {_kalan}")
        r.esit("tahrik α'yı çizimden alıyor ( kutu boş, halat düşey iner )",
               (pg.input_value("#m_sarilma_acisi"), pg.evaluate("SON.m.girdi.sarilma_acisi")),
               ("", 180))
        #  GİRDİ AKORDEONU.  Alanlar artık gruplara ayrıldı ve kapalı gruptaki
        #  alan "görünür değil" sayılır — Playwright dolduramaz.  Test alanları
        #  id ile doldurduğu için bütün grupları açıyoruz;  akordeonun kendi
        #  davranışı aşağıda ayrıca denetleniyor.
        pg.evaluate("mTumGruplariAc()")
        #  İkisi de giderilince hepsi geçmeli.  D2 formda sorulmaz:  çizilen
        #  kasnaklardan gelir ( tasarım şeması ).
        pg.fill("#m_tahrik_kasnak_capi", "280")
        pg.fill("#m_motor_gucu", "7.5")
        pg.fill("#m_guvenlik_devreye_kuvvet", "200")
        #  Tahrik için iki bileşen bilgisi daha:  sertleştirilmiş kanal
        #  ( f = μ / sin(γ/2) ) ve denge zinciri.
        #  STANDART DIŞI KANAL SEÇTİRİLMEZ  ( TS EN 81-50 m.5.11.2.3.1.2 ):
        #  sertleştirilmemiş V kanalın alt kesilmesi olmalıdır.  İki liste
        #  birbirini görmüyordu;  artık karşı listedeki uyumsuz seçenek kapalı.
        _v_kapali = 'document.querySelector(\'#m_kanal_sekli option[value="V Kanal"]\').disabled'
        _y_kapali = ('document.querySelector(\'#m_kanal_isleme option'
                     '[value="Sertleştirilmemiş"]\').disabled')
        r.kontrol("işleme sertleştirilmemişken düz V kanal seçtirilmiyor",
                  pg.evaluate(_v_kapali) is True)
        pg.select_option("#m_kanal_isleme", "Sertleştirilmiş")
        r.kontrol("işleme sertleştirilmiş olunca düz V kanal açılıyor",
                  pg.evaluate(_v_kapali) is False)
        pg.select_option("#m_kanal_sekli", "V Kanal")
        r.kontrol("düz V kanal seçiliyken sertleştirilmemiş seçtirilmiyor",
                  pg.evaluate(_y_kapali) is True)
        r.kontrol("kapalı seçeneğin üstünde sebep yazıyor",
                  "5.11.2.3.1.2" in (pg.evaluate(
                      'document.querySelector(\'#m_kanal_isleme option'
                      '[value="Sertleştirilmemiş"]\').title') or ""))
        pg.select_option("#m_kanal_sekli", "Altı Kesik V Kanal")
        r.kontrol("altı kesik V'de sertleştirilmemiş yine seçilebiliyor",
                  pg.evaluate(_y_kapali) is False)
        pg.select_option("#m_denge_zinciri", "Var")
        #  6,5 mm HALAT 8 mm'NİN ALTINDADIR ( m.5.5.1.2 a) ):  sahadaki gibi
        #  onaylanmış kuruluş belgesiyle kullanılır — seçim formda yapılabilmeli.
        pg.select_option("#m_kasnak_belgesi", "Var")
        #  Sarılma açısının varsayılanı yoktur:  boşsa açı çizimden kesin
        #  bulunabiliyorsa oradan gelir, yoksa tahrik sınırları hesaplanmaz.
        #  Formda gerçekten doldurulabildiği de böylece sınanır.
        r.kontrol("sarılma açısı alanı formda ve boş başlıyor",
                  pg.is_visible("#m_sarilma_acisi")
                  and pg.input_value("#m_sarilma_acisi") == "",
                  f"→ görünür {pg.is_visible('#m_sarilma_acisi')}")
        r.kontrol("kaldırılan C · D · halat arası alanları formda yok",
                  not any(pg.query_selector(x) for x in
                          ("#m_sap_kasnak_yuk", "#m_makine_yatak_yuk",
                           "#m_halat_arasi_yan")))
        pg.fill("#m_sarilma_acisi", "180")
        pg.wait_for_timeout(1500)
        r.kontrol("kasnak 280 mm · motor 7,5 kW · imalatçı kuvveti · "
                  "sertleştirilmiş kanal · denge zinciri · halat belgesi girilince "
                  "bütün bölümler uygun",
                  pg.evaluate("SON.m.ozet.tumu_uygun === true"),
                  f"→ {pg.evaluate('SON.m.bolumler.filter(b=>b.sonuc && b.sonuc.uygun===false).map(b=>b.baslik)')}")
        r.esit("on dört hesap bölümü çizildi",
               pg.eval_on_selector_all("#m_sonuc .serit", "e=>e.length") >= 14, True)
        #  Ekranda gerçekten SAYI var mı — boş tablo "geçti" sayılmasın.
        #  Sayı ELLE yazılmaz:  hesap değişince test sessizce eskiyor.
        _ng = pg.evaluate("SON.m.ozet.N_hesap").__format__(".2f").replace(".", ",")
        r.kontrol(f"motor gücü ekrana yazıldı  ( {_ng} )",
                  _ng in pg.inner_text("#m_sonuc"),
                  f"→ {pg.inner_text('#m_sonuc')[:120]!r}")
        #  Makine tipi seçimi ekranda gerçekten hesabı değiştiriyor mu
        pg.select_option("#m_makine_tipi", "Dişli")
        pg.wait_for_timeout(1400)
        _nd = pg.evaluate("SON.m.ozet.N_hesap")
        pg.select_option("#m_makine_tipi", "Dişlisiz")
        pg.wait_for_timeout(1400)
        r.kontrol("makine tipi ekranda motor gücünü değiştiriyor",
                  _nd > pg.evaluate("SON.m.ozet.N_hesap"),
                  f"→ dişli {_nd}, dişlisiz {pg.evaluate('SON.m.ozet.N_hesap')}")
        pg.fill("#m_motor_gucu", "7.5")
        pg.wait_for_timeout(1200)

        #  Girdi değişince yeniden hesaplanmalı ve sonuç DÖNMELİ
        #  50'lik rayda λ = 3000 / 10,51 = 285 > 250:  ω tanımsız kalır,
        #  BURKULMA kontrolü düşer ama hesap durmaz ( uyarı verilir ).
        pg.select_option("#m_kabin_ray_profili", "50 x 50 x 5")
        pg.wait_for_timeout(1400)
        r.kontrol("küçük ray profili hesabı DURDURMUYOR",
                  pg.evaluate("SON.m && SON.m.aktif === true"),
                  f"→ {pg.evaluate('SON.m && SON.m.hata')}")
        r.kontrol("küçük ray profili narinlik uyarısı veriyor",
                  pg.evaluate("(SON.m.uyarilar||[]).some(u=>u.indexOf('narin')>=0)"),
                  f"→ {pg.evaluate('SON.m.uyarilar')}")
        r.kontrol("küçük ray profili uygunsuz sonuç veriyor",
                  pg.evaluate("SON.m.ozet.tumu_uygun === false"))
        r.kontrol("takılan bölüm kılavuz raylar",
                  pg.evaluate("SON.m.bolumler.filter(b=>b.sonuc && "
                              "b.sonuc.uygun===false).map(b=>b.baslik).join('|')")
                  .find("KILAVUZ RAY") >= 0)
        pg.select_option("#m_kabin_ray_profili", "89 x 62 x 15,88")
        pg.wait_for_timeout(1400)
        r.kontrol("geri alınınca kılavuz ray bölümü yeniden uygun",
                  pg.evaluate("SON.m.bolumler.filter(b=>b.sonuc && "
                              "b.sonuc.uygun===false && "
                              "b.baslik.includes('KILAVUZ RAY')).length === 0"),
                  f"→ {pg.evaluate('SON.m.bolumler.filter(b=>b.sonuc && b.sonuc.uygun===false).map(b=>b.baslik)')}")

        #  Seyir mesafesi ve son kat yüksekliği kuyu boyuna ve ray boyuna iner
        pg.fill("#m_seyir_mesafesi", "24,75")
        pg.fill("#m_son_kat_yuksekligi", "4000")
        pg.wait_for_timeout(1400)
        r.esit("kuyu boyu = seyir + son kat + kuyu dibi",
               pg.evaluate("SON.m.girdi.kuyu_boyu"), 24750 + 4000 + 1600)
        #  Ray boyu çizimden ( cizim/olculer ):  en uzun kabin rayı kuyu
        #  tabanından ( kuyu dibi 1.600 ) kuyu tavanının 200 altına çizilir.
        r.esit("ray boyu çizimdeki raydan  ( seyir + son kat − 200 + kuyu dibi )",
               pg.evaluate("SON.m.ozet.ray_boyu"), (24750 + 4000 - 200 + 1600) / 1000)
        r.esit("ray boyu çizimin ölçüsüyle aynı",
               pg.evaluate("SON.m.ozet.ray_boyu"), pg.evaluate("SON.m.girdi.kabin_ray_boyu"))
        pg.fill("#m_seyir_mesafesi", "21")
        pg.fill("#m_son_kat_yuksekligi", "3750")
        pg.wait_for_timeout(1400)
        r.esit("seyir mesafesi geri alındı", pg.evaluate("SON.m.girdi.kuyu_boyu"), 26350)

        #  BOŞ KABİN AĞIRLIĞI ARTIK ZORUNLU DEĞİL — boş bırakılırsa ofis
        #  tablosundan dolar ( beyan yükü 800 kg → 800 kg ) ve paftada
        #  kaynağı "KABUL  ·  ortalama boş kabin kütlesi" yazar.
        pg.fill("#m_kabin_agirligi", "")
        pg.wait_for_timeout(1400)
        r.kontrol("boş kabin ağırlığı hesabı durdurmuyor",
                  pg.evaluate("SON.m.aktif === true"),
                  f"→ {pg.evaluate('SON.m && SON.m.hata')}")
        r.esit("boş bırakılan kabin ağırlığı tablodan doluyor",
               pg.evaluate("SON.m.girdi.kabin_agirligi"), 800)
        r.kontrol("paftada kaynağı ofis tablosu yazıyor",
                  "KABUL" in pg.evaluate(
                      "SON.m.girdi.kabin_agirligi_kaynak"),
                  f"→ {pg.evaluate('SON.m.girdi.kabin_agirligi_kaynak')!r}")

        #  Boş ZORUNLU alan → hesap durmalı, sebebi ekranda yazmalı
        pg.fill("#m_makine_agirligi", "")
        pg.wait_for_timeout(1400)
        r.kontrol("boş makine ağırlığı hesabı durduruyor",
                  pg.evaluate("SON.m.aktif === false"))
        r.kontrol("hata ekranda görünüyor",
                  "boş bırakılamaz" in pg.inner_text("#m_sonuc"),
                  f"→ {pg.inner_text('#m_sonuc')[:140]!r}")
        pg.fill("#m_makine_agirligi", "300")      # sözleşmenin varsayılanı
        pg.fill("#m_kabin_agirligi", "700")
        pg.wait_for_timeout(1400)
        r.kontrol("düzeltilince hesap geri geliyor",
                  pg.evaluate("SON.m.aktif === true"))

        #  BEYAN YÜKÜ DEĞİŞİNCE KABİN AĞIRLIĞI TABLODAN YENİLENİR
        #  ( avandaki trafik → kapasite izlemesinin aynısı )
        pg.select_option("#m_beyan_yuku", "1275")
        pg.wait_for_timeout(1600)
        r.esit("beyan yükü değişince kabin ağırlığı tablodan geliyor",
               pg.input_value("#m_kabin_agirligi"), "1100")
        #  Elle girilen değer, beyan yükü değişmedikçe korunur
        pg.fill("#m_kabin_agirligi", "1150")
        pg.wait_for_timeout(1400)
        r.esit("elle girilen kabin ağırlığı korunuyor",
               pg.input_value("#m_kabin_agirligi"), "1150")
        pg.select_option("#m_beyan_yuku", "800")
        pg.wait_for_timeout(1600)
        r.esit("beyan yükü yeniden değişince tablo yine izliyor",
               pg.input_value("#m_kabin_agirligi"), "800")
        #  SEÇİMİN HEMEN ARDINDAN YAZILAN DEĞER EZİLMEZ.  Beyan yükü seçilip
        #  220 ms'lik gecikme dolmadan kabin ağırlığı yazılınca istek alanı boş
        #  gönderiyor, dönen tablo değeri de yazılanın üstüne basılıyordu
        #  ( bağımsız referans proje denemesinde çıktı:  950 yazıldı, kutu 800 oldu ).
        pg.evaluate("""() => {
            const by = document.getElementById('m_beyan_yuku');
            by.value = '1000';
            by.dispatchEvent(new Event('change', {bubbles: true}));
            const gk = document.getElementById('m_kabin_agirligi');
            gk.value = '950';
            gk.dispatchEvent(new Event('input', {bubbles: true}));
        }""")
        pg.wait_for_timeout(1800)
        r.esit("beyan yükünden hemen sonra yazılan kabin ağırlığı ekranda kalıyor",
               pg.input_value("#m_kabin_agirligi"), "950")
        r.esit("… ve hesaba o değer giriyor",
               pg.evaluate("SON.m.girdi.kabin_agirligi"), 950)
        pg.select_option("#m_beyan_yuku", "800")
        pg.wait_for_timeout(1600)
        #  YOLDAKİ ESKİ YANIT TAZELEMEYİ İPTAL ETMEZ.  Beyan yükü değiştirildiği
        #  anda eski değerlerle giden bir istek yanıtlanınca bayrak kapanıyor ve
        #  eski kütle kutuya yazılıyordu:  sonraki istek boş alan göndermediği
        #  için 1000 kg'da kabin 950 yerine 800 kg kaldı ( bağımsız incelemede
        #  yeniden üretildi ).  Yanıt 100 ms geciktirilerek yarış kurulur.
        from engine.ortak import ofis as _OFK
        _bek1000 = _OFK.bos_kabin_kutlesi(1000)
        _yaris = pg.evaluate("""async () => {
            const bek = ms => new Promise(r => setTimeout(r, ms));
            const f0 = window.fetch;
            window.fetch = async (...a) => { const r = await f0(...a);
                if (String(a[0]).includes('/api/uygulama/coklu')) await bek(100);
                return r; };
            try {
                hesapMukavemet();                                  // eski istek yolda
                const by = document.getElementById('m_beyan_yuku');
                by.value = '1000';
                by.dispatchEvent(new Event('change', {bubbles: true}));
                await bek(2500);
            } finally { window.fetch = f0; }
            return {kutu: document.getElementById('m_kabin_agirligi').value,
                    hesap: SON.m.girdi.kabin_agirligi};
        }""")
        r.esit("yoldaki eski yanıt tazelemeyi iptal etmiyor — kutu tablo değerinde",
               _yaris["kutu"], str(int(_bek1000)))
        r.esit("… ve hesaba tablo değeri gidiyor", _yaris["hesap"], _bek1000)

        #  AYNI ASANSÖRDE İKİ HIZLI DEĞİŞİKLİK.  1000 kg'ın isteği yoldayken
        #  yük 1600 kg yapılınca iki değişiklik aynı asansör sırasını taşıyordu:
        #  eski yanıt bayrağı kapatıp 950'yi kutuya yazıyor, 1600 kg'lık hesap
        #  950 ile gidiyordu ( bağımsız incelemede yeniden üretildi ).  İlk
        #  yanıt elle bekletilir ve ikinci değişiklikten HEMEN sonra bırakılır —
        #  zamanlamaya bağlı değildir.
        _bek1600 = _OFK.bos_kabin_kutlesi(1600)
        _yaris2 = pg.evaluate("""async () => {
            const bek = ms => new Promise(r => setTimeout(r, ms));
            const by = document.getElementById('m_beyan_yuku');
            const sec = v => { by.value = v;
                by.dispatchEvent(new Event('change', {bubbles: true})); };
            const f0 = window.fetch;
            let birak; const kapi = new Promise(r => birak = r);
            let ilk = true;
            const giden = [];
            window.fetch = async (u, o) => {
                const coklu = String(u).includes('/api/uygulama/coklu');
                if (coklu) { const b = JSON.parse(o.body).asansorler[0];
                             giden.push([b.beyan_yuku, b.kabin_agirligi]); }
                const r = await f0(u, o);
                if (coklu && ilk) { ilk = false; await kapi; }
                return r; };
            try {
                sec('1000');
                await bek(600);                 // 1000 kg'ın isteği yolda, yanıt bekletiliyor
                sec('1600');
                birak();                        // eski yanıt, yeni istek çıkmadan döner
                await bek(2500);
            } finally { window.fetch = f0; }
            return {kutu: document.getElementById('m_kabin_agirligi').value,
                    hesap: SON.m.girdi.kabin_agirligi, giden};
        }""")
        r.kontrol("hızlı yük değişiminde eski yanıt yeni yükün kabin ağırlığını ezmiyor",
                  _yaris2["kutu"] == str(int(_bek1600)),
                  f"→ kutu {_yaris2['kutu']!r}, beklenen {int(_bek1600)} · gönderilenler {_yaris2['giden']}")
        r.esit("… ve 1600 kg'lık hesaba 1600 kg'ın tablo değeri gidiyor",
               _yaris2["hesap"], _bek1600)
        pg.select_option("#m_beyan_yuku", "800")
        pg.wait_for_timeout(1600)
        pg.fill("#m_kabin_agirligi", "700")
        pg.wait_for_timeout(1400)
        #  Standarda uyan kasnak korunuyor — testin geri kalanı temiz koşsun
        r.kontrol("kasnak 280 mm hâlâ yerinde",
                  pg.input_value("#m_tahrik_kasnak_capi") == "280")

        #  Çıktı düğmeleri:  varlıkları YETMEZ, gerçekten dosya dönmeli.
        #  PROJE sekmesindedirler — çıktı bütün asansörleri kapsar, tek bir
        #  asansörün sekmesine ait değildir.
        r.esit("uygulama çıktı ve proje dosyası düğmeleri",
               pg.eval_on_selector_all(
                   "#s-uygproje .dugmeler .dg",
                   "e=>e.map(x=>x.textContent.trim())"),
               ["Projeyi kaydet", "Proje aç (.uygulama)", "Tümünü temizle",
                "Uygulama Projesi PDF", "Projeyi paketle (ZIP)"])
        _ind = pg.evaluate("""async () => {
            const dene = async uc => {
              const r = await fetch('/api/indir/'+uc, {method:'POST',
                headers:{'Content-Type':'application/json'},
                body: JSON.stringify({kapak: kapakGirdi(), girdiler: mukavemetGirdi()})});
              const b = await r.arrayBuffer();
              return {tur: (r.headers.get('Content-Type')||'').split(';')[0],
                      boyut: b.byteLength};
            };
            return {pdf: await dene('uygulama-pdf')};
        }""")
        r.esit("arayüzden uygulama PDF iniyor", _ind["pdf"]["tur"], "application/pdf")
        r.kontrol("inen PDF boş değil", _ind["pdf"]["boyut"] > 20_000,
                  f"→ {_ind['pdf']['boyut']} bayt")

        #  Proje kimliği dosya adına giriyor mu  ( avan kapağı BASILMAMALI )
        #  Kimlik PROJE sekmesindedir:  bir kapak dört asansörü birden
        #  taşır, tek asansörün sekmesine ait değildir.
        pg.click('.sekme[data-sekme="uygproje"]')
        pg.wait_for_timeout(400)
        pg.fill("#mk_proje_adi", "Güneş Apartmanı")
        pg.evaluate("mAsansorSekmesi(0)")
        pg.wait_for_timeout(900)
        _ad = pg.evaluate("""async () => {
            const r = await fetch('/api/indir/uygulama-pdf', {method:'POST',
              headers:{'Content-Type':'application/json'},
              body: JSON.stringify({kapak: mukavemetKimlik(),
                                    girdiler: mukavemetGirdi(),
                                    sabitler: ofisSabitleri()})});
            const cd = r.headers.get('Content-Disposition')||'';
            await r.arrayBuffer();
            const m = cd.match(/filename\*=UTF-8''(.+)$/);
            return m ? decodeURIComponent(m[1]) : null;
        }""")
        r.esit("proje adı dosya adına giriyor", _ad,
               "Güneş Apartmanı - Uygulama Projesi Hesaplari.pdf")
        r.kontrol("mukavemet indirmesi avan kapağını göndermiyor",
                  pg.evaluate("Object.keys(mukavemetKimlik()).sort().join(',')")
                  == "owner,project_title,sheet_no")

        #  REVİZYON AKIŞI:  proje dosyası al → formu boz → dosyayı geri yükle
        pg.select_option("#m_beyan_yuku", "1000")
        pg.fill("#m_kabin_agirligi", "950")
        pg.fill("#m_seyir_mesafesi", "24,75")
        pg.wait_for_timeout(1600)
        _once = pg.evaluate("({yuk: SON.m.girdi.beyan_yuku, "
                            "ag: SON.m.girdi.kabin_agirligi, "
                            "seyir: SON.m.girdi.seyir_mesafesi, ray: SON.m.ozet.ray_boyu})")
        _geri = pg.evaluate("""async () => {
            const govde = JSON.parse(JSON.stringify(projeGovdesi('uygulama')));
            //  formu boz
            document.getElementById('m_beyan_yuku').value = '450';
            document.getElementById('m_kabin_agirligi').value = '500';
            document.getElementById('m_seyir_mesafesi').value = '15';
            mukavemetPlanla();
            await new Promise(x=>setTimeout(x, 1500));
            const bozuk = {yuk: SON.m.girdi.beyan_yuku, seyir: SON.m.girdi.seyir_mesafesi};
            //  dosyayı geri yükle
            projeUygula(govde, 'muk.uygulama');
            await new Promise(x=>setTimeout(x, 2000));
            return {bozuk, sonra: {yuk: SON.m.girdi.beyan_yuku,
                    ag: SON.m.girdi.kabin_agirligi, seyir: SON.m.girdi.seyir_mesafesi,
                    ray: SON.m.ozet.ray_boyu},
                    durum: document.getElementById('durum').textContent};
        }""")
        r.kontrol("form gerçekten bozulmuştu",
                  _geri["bozuk"]["yuk"] == 450 and _geri["bozuk"]["seyir"] != _once["seyir"],
                  f"→ {_geri['bozuk']}")
        r.esit("proje dosyasından geri yükleme girdileri aynen döndürüyor",
               _geri["sonra"], _once)
        r.kontrol("yükleme durum satırında bildiriliyor",
                  "Proje açıldı" in _geri["durum"], f"→ {_geri['durum'][:90]!r}")

        #  Sayfa yenilenince girdiler duruyor mu  ( tarayıcıda saklama )
        pg.reload(wait_until="networkidle")
        pg.wait_for_timeout(600)
        pg.click("#gk_uygulama")
        pg.wait_for_timeout(2200)
        r.esit("yenilemeden sonra beyan yükü duruyor",
               pg.input_value("#m_beyan_yuku"), "1000")
        r.esit("yenilemeden sonra seyir mesafesi duruyor",
               pg.input_value("#m_seyir_mesafesi"), "24,75")
        r.esit("yenilemeden sonra proje adı duruyor",
               pg.input_value("#mk_proje_adi"), "Güneş Apartmanı")
        #  ─────────── AVAN VE UYGULAMA AYRI KOVALARDA ───────────
        #  Tek kova varken iki proje yan yana yaşıyordu:  avan üzerinde
        #  çalışıp uygulamaya geçince avan verisi orada duruyordu ve
        #  "Tümünü temizle" ikisini birden siliyordu.
        _kovalar = pg.evaluate(
            "Object.keys(localStorage).filter(k=>/program_v1/.test(k)).sort()")
        r.kontrol("uygulama kendi kovasına yazıyor",
                  "uygulama_program_v1" in _kovalar, f"→ {_kovalar}")
        _uk = pg.evaluate(
            "JSON.parse(localStorage.getItem('uygulama_program_v1')||'{}')")
        r.esit("uygulama kovası kendi modunu yazıyor", _uk.get("__mod"), "uygulama")
        r.esit("uygulama kovasında AVAN alanı yok",
               [k for k in _uk if k[:2] in ("c_", "a_", "k_") or k[:3] in ("of_", "sb_")], [])
        r.kontrol("uygulama kovasında mukavemet alanları var",
                  any(k.startswith("m_") for k in _uk), f"→ {sorted(_uk)[:6]}")
        r.kontrol("uygulamanın kendi ofis sabitleri de kovada",
                  any(k.startswith("uof_") for k in _uk), f"→ {sorted(_uk)[:6]}")

        #  Testin geri kalanı temiz girdiyle koşsun
        pg.evaluate("localStorage.removeItem(KOVA[MOD])")
        pg.reload(wait_until="networkidle")
        pg.wait_for_timeout(600)
        pg.click("#gk_uygulama")
        pg.wait_for_timeout(2200)

        #  ─────────── UYGULAMANIN KENDİ OFİS SABİTLERİ ───────────
        #  Avanınkinden AYRI:  avan ön tasarımdır, uygulama kesin tasarım.
        #  σem ve k1 bugüne kadar KODDA GÖMÜLÜYDÜ, ekrana çıkarıldı.
        pg.click(".sekme[data-sekme='sabitler']")
        pg.wait_for_timeout(500)
        r.kontrol("uygulamada KENDİ sabitler gövdesi görünüyor",
                  pg.is_visible("#sabitler_uygulama"))
        r.kontrol("uygulamada AVAN sabitleri görünmüyor",
                  not pg.is_visible("#sabitler_avan"))
        _uof = pg.eval_on_selector_all("[id^='uof_']", "e=>e.length")
        r.kontrol("uygulama ofis sabitleri çizildi", _uof >= 40, f"→ {_uof} alan")
        for _a in ("uof_sigma_em", "uof_k1_kaymali", "uof_verim_dislisiz",
                   "uof_verim_disli", "uof_tavan_payi"):
            r.kontrol(f"ofis sabiti ekranda: {_a}", pg.is_visible(f"#{_a}"))

        #  Ekrandan değiştirilen sabit HESABI değiştirmeli
        pg.click(".sekme[data-sekme='mukavemet']")
        pg.wait_for_timeout(400)
        _n0 = pg.evaluate("SON.m.ozet.N_hesap")
        pg.click(".sekme[data-sekme='sabitler']")
        pg.wait_for_timeout(300)
        pg.fill("#uof_verim_dislisiz", "0,95")
        pg.wait_for_timeout(2200)
        _n1 = pg.evaluate("SON.m.ozet.N_hesap")
        r.kontrol("ofis verimi motor gücünü değiştiriyor", _n1 < _n0,
                  f"→ önce {_n0}, sonra {_n1}")
        #  NPU 140 makine kirişinde σe:  makine dairesizde ≈ 72 ( kiriş DBGW
        #  açıklığında ), makine dairelide ≈ 65 N/mm² ( kaide halatlara ortalı ve
        #  makineyi sarar — açıklığı kısa ):  σem 50'ye inince ikisi de kalmalı.
        pg.fill("#uof_sigma_em", "50")
        #  KAİDE HESABI ( kolon burkulması dahil ) MAKİNE DAİRESİ İSTER —
        #  σem'i düşürmenin etkisini tam kaidede görmek için makine dairesi açılır.
        #  ( Kutu akordeon içindedir;  gruplar önce açılır. )
        pg.click(".sekme[data-sekme='mukavemet']")
        pg.wait_for_timeout(300)
        pg.evaluate("mTumGruplariAc()")
        _mrl_sec(pg, False)
        #  MAKİNE DAİRESİ AÇILINCA ÖLÇÜSÜ ZORUNLU OLUR ( girdi doğrulaması );
        #  doldurulmazsa hesap hiç koşmaz ve SON.m boş kalır.
        pg.fill("#m_mk_uzunluk", "4000")
        pg.fill("#m_mk_genislik", "3000")
        pg.wait_for_timeout(2200)
        #  TABLİYE YALNIZ MAKİNE DAİRELİDE SORULUR — görünür alanda, Gelişmiş'te değil.
        r.kontrol("daireli: tabliye beton yüksekliği görünür alanda soruluyor",
                  pg.evaluate("(()=>{const a=$('m_tabliye_yuksekligi').closest('.alan');"
                              "return !a.classList.contains('kural-disi') && !a.closest('.m-gelismis-ic');})()"))
        _b2 = pg.evaluate("SON.m.bolumler.find(b=>b.baslik.startsWith('2')).sonuc")
        r.kontrol("σem düşürülünce makine kaidesi kalıyor",
                  _b2.get("uygun") is False, f"→ {_b2}")
        r.kontrol("σem satırı kaynağını OFİS STANDARDI diye yazıyor",
                  "KABUL" in pg.evaluate(
                      "SON.m.bolumler.find(b=>b.baslik.startsWith('2'))"
                      ".adimlar.find(a=>a.sembol==='σem').kaynak"))
        #  MRL'ye dönünce bölüm 2 MAKİNE KİRİŞİNİ denetler:  tabliye ve kolon
        #  yoktur, burkulma satırı basılmaz;  σem 50'de kiriş kalır.
        _mrl_sec(pg, True)
        pg.wait_for_timeout(2200)
        _b2m = pg.evaluate("SON.m.bolumler.find(b=>b.baslik.startsWith('2')).sonuc")
        r.kontrol("MRL'de bölüm 2 makine kirişini denetliyor ( σem 50'de kalıyor )",
                  _b2m.get("uygun") is False and "makine kirişleri" in _b2m.get("baslik", ""),
                  f"→ {_b2m}")
        r.kontrol("MRL: tabliye beton yüksekliği gizli",
                  pg.evaluate("$('m_tabliye_yuksekligi').closest('.alan').classList.contains('kural-disi')"))
        r.kontrol("MRL'de bölüm 2'de burkulma satırı yok",
                  pg.evaluate("!SON.m.bolumler.find(b=>b.baslik.startsWith('2'))"
                              ".adimlar.some(a=>String(a.formul||'').includes('σb'))"))
        r.kontrol("MRL'de kaide kirişi ve makine dairesi alanları gizli",
                  pg.evaluate("MUK.yerlesime_gore_gizli.mrl.length > 0 && "
                              "MUK.yerlesime_gore_gizli.mrl.every("
                              "a => document.getElementById('m_' + a).closest('.alan')"
                              ".classList.contains('kural-disi'))"))
        #  Kutu VARSAYILAN durumunda ( MRL ) bırakılır ve SABİTLER sekmesine
        #  dönülür — aşağıdaki "Tümünü varsayılana döndür" düğmesi oradadır.
        pg.click(".sekme[data-sekme='sabitler']")
        pg.wait_for_timeout(600)
        pg.click("button:has-text('Tümünü varsayılana döndür')")
        pg.wait_for_timeout(2200)
        r.kontrol("sabitler varsayılana dönüyor",
                  abs(pg.evaluate("SON.m.ozet.N_hesap") - _n0) < 1e-9,
                  f"→ {pg.evaluate('SON.m.ozet.N_hesap')} ≠ {_n0}")

        #  ─────────── UYGULAMANIN KENDİ TABLOLARI ───────────
        #  Bugüne kadar YOKTU:  Tablolar sekmesi yalnız avan modundaydı,
        #  uygulama yapan mühendis kullandığı ray tablosuna bakamıyordu.
        pg.click(".sekme[data-sekme='tablolar']")
        pg.wait_for_timeout(600)
        r.kontrol("uygulamada KENDİ tablolar gövdesi görünüyor",
                  pg.is_visible("#tablolar_uygulama"))
        r.kontrol("uygulamada AVAN tabloları görünmüyor",
                  not pg.is_visible("#tablolar_avan"))
        _tb = pg.eval_on_selector_all("#utablolar_ic table", "e=>e.length")
        r.kontrol("uygulama tabloları çizildi", _tb >= 12, f"→ {_tb} tablo")
        #  BAŞLIKLAR CSS İLE BÜYÜK HARFE ÇEVRİLİYOR ve Türkçede bu dönüşüm
        #  geri alınamaz ( KILAVUZ → kilavuz, PROFİLLERİ → profi̇lleri̇ ).
        #  Bu yüzden görüntülenen metin değil, DOM'daki textContent okunur —
        #  text-transform onu değiştirmez.
        _tm = pg.eval_on_selector("#utablolar_ic", "e=>e.textContent")
        for _ara in ("Kılavuz ray profilleri", "NPU profilleri", "Askı halatları",
                     "burkulma", "Kabin alanı"):
            r.kontrol(f"uygulama tablosu: {_ara}", _ara in _tm,
                      f"→ {_tm[:130]!r}")
        #  Tablo İÇERİĞİ de basılmalı — boş başlık listesi "geçti" sayılmasın
        r.kontrol("ray tablosunda gerçek profil var", "50 x 50 x 5" in _tm)
        r.kontrol("halat tablosunda TS 12385-5 yazılı", "12385" in _tm)

        #  ─────────── PROJE DOSYASI  (.uygulama) ───────────
        pg.click('.sekme[data-sekme="uygproje"]')
        pg.wait_for_timeout(400)
        _pd = pg.evaluate("projeGovdesi('uygulama')")
        r.esit("proje dosyası modunu yazıyor", _pd.get("__mod"), "uygulama")
        r.kontrol("proje dosyası SÜRÜM taşıyor", bool(_pd.get("__surum")),
                  f"→ {_pd.get('__surum')}")
        r.esit("proje dosyasında AVAN alanı yok",
               [k for k in _pd["alanlar"]
                if k[:2] in ("c_", "a_", "k_") or k[:3] in ("of_", "sb_")], [])
        r.kontrol("proje dosyası ofis sabitlerini de taşıyor",
                  any(k.startswith("uof_") for k in _pd["alanlar"]))
        pg.fill("#mk_proje_adi", "Jan Mühendislik")
        pg.wait_for_timeout(300)
        r.esit("dosya adı proje adından üretiliyor",
               pg.evaluate("projeDosyaAdi('uygulama')"), "Jan Mühendislik.uygulama")
        #  YANLIŞ MODA yükleme reddedilmeli
        pg.evaluate("projeUygula({__mod:'avan',__surum:1,alanlar:{c_N:'11'}}, 'x.avan')")
        pg.wait_for_timeout(400)
        r.kontrol("avan dosyası uygulamaya yüklenmiyor",
                  "AVAN projesine ait" in pg.inner_text("#durum"),
                  f"→ {pg.inner_text('#durum')[:80]}")
        r.esit("reddedilen dosya girdiyi bozmadı",
               pg.input_value("#mk_proje_adi"), "Jan Mühendislik")

        pg.click("#dg_ana_ekran")
        pg.wait_for_timeout(300)
        r.kontrol("ana ekran düğmesi seçim ekranına döndürüyor", pg.is_visible("#giris"))

        #  --- avan moduna geçiş ---
        pg.click("#gk_avan")
        pg.wait_for_timeout(600)
        r.kontrol("avan seçilince uygulama açılıyor",
                  (not pg.is_visible("#giris")) and pg.is_visible('.sekme[data-sekme="avan"]'))
        r.kontrol("avan modunda mukavemet sekmesi gizli",
                  not pg.is_visible('.sekme[data-sekme="mukavemet"]'))
        r.kontrol("başlık avan programına döndü",
                  "AVAN" in pg.inner_text("#ust_ad"))
        pg.click("#dg_ana_ekran")
        pg.wait_for_timeout(300)
        pg.click("#gk_avan")
        pg.wait_for_timeout(300)
        r.kontrol("geri dönülüp yeniden girilebiliyor", not pg.is_visible("#giris"))

        # ---------------------------------------------------------------
        #  SEKME SIRASI  ( 2.7 )
        #  Şerit işlem sırasını anlatır:  1 trafik · 2 avan · 3 proje kapağı.
        #  "Sabitler" ve "Tablolar" birer adım değil, gerektikçe bakılan
        #  kaynaklardır — akışın ortasında değil, şeridin sağ ucundadırlar.
        # ---------------------------------------------------------------
        #  Şeritte HER İKİ MODUN sekmeleri durur, moda ait olmayanlar
        #  gizlenir;  sıra kontrolü GÖRÜNENLER üzerinden yapılır.
        r.esit("sekme sırası işlem sırası",
               pg.eval_on_selector_all(
                   ".sekme", "e=>e.filter(x=>!x.hidden).map(x=>x.dataset.sekme)"),
               ["trafik", "avan", "proje", "sabitler", "tablolar"])
        r.esit("açılışta 1. adım etkin",
               pg.eval_on_selector(".sekme.etkin", "e=>e.dataset.sekme"), "trafik")
        r.kontrol("açılışta trafik gövdesi görünür", pg.is_visible("#s-coklu"))
        r.kontrol("proje kapağı 3. adım olarak yazılı",
                  "3" in (pg.inner_text('.sekme[data-sekme="proje"]') or ""))
        _yer = pg.evaluate("""() => {
            const q = s => document.querySelector(s).getBoundingClientRect();
            return {kapak: q('.sekme[data-sekme="proje"]').right,
                    sabit: q('.sekme[data-sekme="sabitler"]').left,
                    serit: q('.sekmeler-ic').right,
                    tablo: q('.sekme[data-sekme="tablolar"]').right};
        }""")
        r.kontrol("başvuru sekmeleri sağ uca itildi",
                  _yer["sabit"] - _yer["kapak"] > 100, f"→ {_yer}")
        r.kontrol("son sekme şeridin sağ ucunda",
                  _yer["serit"] - _yer["tablo"] < 40, f"→ {_yer}")

        # örnek proje yüklensin
        pg.evaluate("ornekYukle()")
        pg.wait_for_timeout(1800)

        # --- her sekme açılıyor ve içerik üretiyor
        r.esit("avan modunda görünen sekme sayısı 5",
               pg.eval_on_selector_all(".sekme", "e=>e.filter(x=>!x.hidden).length"), 5)
        r.esit("şeritteki toplam sekme 6  ( + uygulama projesi )",
               pg.eval_on_selector_all(".sekme", "e=>e.length"), 6)
        r.kontrol("ayrı 'çoklu' sekmesi kalmadı",
                  pg.query_selector('.sekme[data-sekme="coklu"]') is None)
        for sekme, ic_id in (("proje", None), ("trafik", None),
                             ("avan", "a_sonuc"), ("sabitler", "sabit_b_form"),
                             ("tablolar", "tablolar_ic")):
            pg.click(f'.sekme[data-sekme="{sekme}"]')
            pg.wait_for_timeout(450)
            if sekme == "trafik":
                acik = pg.evaluate("[...document.querySelectorAll('.sayfa')]"
                                   ".filter(s=>!s.hidden).map(s=>s.id)")
                r.kontrol("trafik sekmesinde tek gövde açık", len(acik) == 1, f"→ {acik}")
                r.esit("trafik gövdesi tek ( yöntem seçimi kalktı )",
                       acik and acik[0], "s-coklu")
                hedef = "c_sonuc"
                uzunluk = pg.eval_on_selector(f"#{hedef}", "e => e.innerText.length")
                r.kontrol("trafik sekmesi içerik üretti", uzunluk > 200, f"→ {uzunluk} karakter")
                continue
            r.kontrol(f"sekme '{sekme}' görünür", not pg.is_hidden(f"#s-{sekme}"))
            if ic_id:
                uzunluk = pg.eval_on_selector(f"#{ic_id}", "e => e.innerText.length")
                r.kontrol(f"sekme '{sekme}' içerik üretti", uzunluk > 200, f"→ {uzunluk} karakter")

        # ==============================================================
        #  v3.3 — KAPAK ASANSÖR BİLGİLERİ HESAPTAN DOLAR
        #  Gri yer tutucular sabit örneklerdi ( "10 kişi", "7,5 kW" ): dolu
        #  görünüp boş basılıyordu.  Artık yer tutucu hesabın değeridir ve
        #  boş kutunun yerine çıktıya o basılır.  Örnek proje:  10 + 16
        #  kişilik iki asansör, 1,6 m/s, N = 11, h = 3 m, MRL, dişlisiz.
        # ==============================================================
        pg.click('.sekme[data-sekme="proje"]')
        pg.wait_for_timeout(300)
        _yer = pg.evaluate("""() => Object.fromEntries([...document.querySelectorAll(
            '#s-proje input[id^="k_"]')].map(e => [e.id.slice(2), e.placeholder]))""")
        _bek = {"usage": "Konut", "stops": "12", "travel": "33,00 m",
                "capacity": "10 / 16 kişi", "speed": "1,60 m/s",
                "cabin_width": "1300/2100", "cabin_depth": "1450/1350",
                "suspension": "2:1", "elevator_count": "2",
                "drive_type": "Dişlisiz (MRL)", "standard": "TS EN 81-20"}
        r.esit("kapak · yer tutucular projenin hesabını gösteriyor",
               {k: _yer.get(k) for k in _bek}, _bek)
        _nsc = pg.evaluate("SON.a.ozet.asansorler.map(a => a.Nsc)")
        r.esit("kapak · motor gücü avandaki seçilen Nsç",
               _yer.get("motor_power"),
               " / ".join(dict.fromkeys(f"{x:g}".replace(".", ",") for x in _nsc)) + " kW")
        r.esit("kapak · hesaptan çıkmayan alanlarda örnek değer yok",
               {k: _yer.get(k) for k in ("block", "elevator_class", "rail_size", "scale")},
               {"block": "", "elevator_class": "", "rail_size": "", "scale": ""})
        r.esit("kapak · türeyen alan listesi motordan ( /api/secenekler )",
               pg.evaluate("SEC.kapak_turetilen").__len__(), 12)
        #  Çıktıya giden kapak:  boş kutu → hesabın değeri,  yazılan → yazılan
        _cik = pg.evaluate("kapakCiktisi()")
        r.esit("kapak · boş kutunun yerine çıktıya hesabın değeri gidiyor",
               {k: _cik.get(k) for k in _bek}, _bek)
        pg.fill("#k_capacity", "630 kg")
        pg.wait_for_timeout(200)
        r.esit("kapak · yazılan değer hesabın önüne geçiyor",
               pg.evaluate("kapakCiktisi().capacity"), "630 kg")
        r.esit("kapak · uygulama paketine giden form olduğu gibi ( türetme yok )",
               pg.evaluate("[kapakGirdi().capacity, kapakGirdi().speed]"), ["630 kg", ""])
        #  Kapak PDF'i:  yazılan değer ile hesaptan gelenler birlikte basılıyor
        _gov = pg.evaluate("indirGovdesi('kapak-pdf')")
        _pdf = urllib.request.urlopen(urllib.request.Request(
            BASE + "/api/indir/kapak-pdf", method="POST", data=json.dumps(_gov).encode(),
            headers={"Content-Type": "application/json"}), timeout=30).read()
        try:
            import pypdfium2 as _pdfium
            _d = _pdfium.PdfDocument(_pdf)
            _m = "".join(_d[0].get_textpage().get_text_range().split())
            _yok = [v for v in ("630 kg", "1,60 m/s", "12", "33,00 m", "1300/2100",
                                "Dişlisiz (MRL)", "Konut", "TS EN 81-20")
                    if "".join(v.split()) not in _m]
            r.kontrol("kapak PDF'i · hesaptan gelenler ve yazılan değer basıldı", not _yok,
                      f"→ basılmayan: {_yok}")
        except ImportError:
            r.atla("kapak PDF metni okunamadı — pypdfium2 kurulu değil")
        pg.fill("#k_capacity", "")
        #  Trafik hesabı hata verince trafikten gelen yer tutucular boşalır —
        #  eski değer "doğru" gibi basılmaz.
        pg.click('.sekme[data-sekme="trafik"]')
        pg.fill("#c_N", "")
        pg.wait_for_timeout(1500)
        r.esit("kapak · trafik hatalıyken durak / seyir / kullanım amacı boş",
               pg.evaluate("['usage','stops','travel'].map(k => $('k_'+k).placeholder)"),
               ["", "", ""])
        r.esit("kapak · trafik hatalıyken çıktıya da gitmiyor",
               pg.evaluate("[kapakCiktisi().stops, kapakCiktisi().travel]"), ["", ""])
        #  Kat sayısı boşken mesaj eksik olanı söyler, tg'yi değil
        _hm = pg.inner_text("#c_sonuc")
        r.kontrol("trafik · N boşken mesaj kat sayısını söylüyor",
                  "③ kat sayısı N" in _hm and "tg'yi elle girin" not in _hm, f"→ {_hm[:140]!r}")
        pg.fill("#c_N", "11")
        pg.wait_for_timeout(1500)
        r.esit("kapak · trafik düzelince yer tutucular geri geliyor",
               pg.evaluate("['usage','stops','travel'].map(k => $('k_'+k).placeholder)"),
               ["Konut", "12", "33,00 m"])

        # ==============================================================
        #  v3.3 — ⑤ / ⑥ ETİKETİ VE HATA METNİ AYNI ADI SÖYLER
        #  Red metni "hizli1 = 1.200" diyordu;  ekranda "hizli1" diye bir kutu
        #  yoktur.  Etiket de hata metni de motordaki tek tanımdan gelir.
        # ==============================================================
        _et = lambda: pg.evaluate("[$('c_l_hizli1').textContent, $('c_l_hizli2').textContent]")
        r.esit("⑤/⑥ etiketleri · Konut", _et(),
               ["⑤ Daire sayısı (bağımsız bölüm adedi)",
                "⑥ Daire başına DİĞER oda sayısı (ilk yatak odası hariç)"])
        pg.fill("#c_hizli1", "1.200")
        pg.wait_for_timeout(1200)
        _hm = pg.inner_text("#c_sonuc")
        r.kontrol("trafik · belirsiz ⑤ ekrandaki adıyla bildiriliyor",
                  "⑤ Daire sayısı = 1.200" in _hm and "hizli1" not in _hm, f"→ {_hm[:160]!r}")
        pg.fill("#c_hizli1", "44")
        pg.select_option("#c_bina_tipi", "Katlı Otopark")
        pg.wait_for_timeout(1500)
        r.esit("⑤/⑥ etiketleri · Katlı Otopark", _et(),
               ["⑤ Özel amaçlı araç adedi", "⑥ Ticari amaçlı araç adedi"])
        #  Tablo-2'de olmayan bina tipinde hız seçilmemişse mesaj sebebi ve
        #  çareyi söyler ( eskiden "V = — m/s için tg'yi elle girin" ).
        _hm = pg.inner_text("#c_sonuc")
        r.kontrol("trafik · Tablo-2 dışı bina, hız yok → sebep ve çare",
                  "Tablo-2'de yoktur" in _hm and "tg'yi elle girin" not in _hm,
                  f"→ {_hm[:160]!r}")
        pg.select_option("#c_bina_tipi", "Otel (3* ve altı)")
        pg.wait_for_timeout(300)
        r.esit("⑤/⑥ etiketleri · Otel", _et(),
               ["⑤ Toplam yatak sayısı", "⑥ (bu bina tipinde gerekmiyor — boş bırakın)"])
        pg.select_option("#c_bina_tipi", "Konut")
        pg.wait_for_timeout(1500)
        r.kontrol("örnek projeye dönüldü — trafik yine hatasız",
                  "HESAP HATASI" not in pg.inner_text("#c_sonuc"))

        # --- trafik sonucu doğru mu (sunucudaki motorla aynı olmalı)
        adetSec(pg, 1)
        pg.wait_for_timeout(400)
        ekran = pg.inner_text("#c_sonuc")
        istek = urllib.request.Request(
            BASE + "/api/trafik", method="POST",
            data=json.dumps({"mod": "tek", "girdiler": {
                "bina_tipi": "Konut", "bina_yuksekligi": "39,98", "yapi_yuksekligi": "43",
                "N": "11", "h": "3", "hizli1": "44", "hizli2": "3", "P": "10",
                "kapi_genisligi": "900", "kapi_tipi": "Merkezden Açılan Oto."}}).encode(),
            headers={"Content-Type": "application/json"})
        api = json.loads(urllib.request.urlopen(istek, timeout=30).read())
        r.kontrol("ekrandaki sonuç API ile aynı", api["ozet"]["sonuc"] in ekran,
                  f"→ {api['ozet']['sonuc']!r}")
        r.kontrol("adım adım işlem gösteriliyor", "TR = 2·H·tv" in ekran)
        r.kontrol("kaynak referansları gösteriliyor", "Tablo-3" in ekran and "Tablo-5" in ekran)

        # --- canlı yeniden hesap
        pg.fill("#c_N", "25")
        pg.wait_for_timeout(900)
        a = pg.inner_text("#c_sonuc .olcut .k:first-child .dg2")
        pg.fill("#c_N", "11")
        pg.wait_for_timeout(900)
        b = pg.inner_text("#c_sonuc .olcut .k:first-child .dg2")
        r.kontrol("girdi değişince sonuç güncelleniyor", a != b, f"→ N=25:{a}  N=11:{b}")

        # --- hata mesajı görünür
        pg.fill("#c_hizli1", "")
        pg.wait_for_timeout(900)
        r.kontrol("nüfus silinince hata kutusu çıkıyor",
                  "HESAP HATASI" in pg.inner_text("#c_sonuc"))
        pg.fill("#c_hizli1", "44")
        pg.wait_for_timeout(900)
        r.kontrol("girdi geri gelince hata kalkıyor",
                  "HESAP HATASI" not in pg.inner_text("#c_sonuc"))

        # --- trafikten avana OTOMATİK aktarım  ( v1.5 )
        #     Örnek proje 10 + 16 kişilik iki asansörlük bir gruptur.  Avandaki
        #     kapasite ve hız alanları BOŞALTILIP hiçbir düğmeye basılmadan
        #     trafikten geri gelmelidir; adet de kendiliğinden eşitlenmelidir.
        adetSec(pg, 2)
        pg.wait_for_timeout(900)
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(400)
        pg.evaluate("['a_kapasite1','a_kapasite2','a_V1','a_V2']"
                    ".forEach(i=>{document.getElementById(i).value='';}); planla();")
        pg.wait_for_timeout(1800)
        r.esit("otomatik: 1. asansör kapasitesi", pg.input_value("#a_kapasite1"), "10")
        r.esit("otomatik: 2. asansör kapasitesi", pg.input_value("#a_kapasite2"), "16")
        r.kontrol("otomatik: kabin hızı da doldu",
                  pg.input_value("#a_V1") not in ("", None), f"→ {pg.input_value('#a_V1')!r}")
        r.esit("avan adedi trafik adediyle eşitlendi",
               pg.inner_text("#adet_dugmeler_a .adet-dg.secili").strip(), "2")
        r.kontrol("1. asansör 'trafik grubundan' etiketli",
                  "trafik grubundan" in pg.evaluate(
                      "document.getElementById('a_etiket1').textContent"))
        r.kontrol("3. asansör kartı kapalı",
                  "pasif" in (pg.get_attribute("#a_kutu3", "class") or ""))
        r.kontrol("'kullan' kutuları artık gizli",
                  pg.is_hidden("#a_aktif1"))
        adetSec(pg, 1)
        pg.wait_for_timeout(700)

        # --- avan sonucu
        avan_ekran = pg.inner_text("#a_sonuc")
        for beklenen in ("SONUÇ ÖZETİ", "MOTOR GÜCÜ HESABI", "KUVVET HESAPLARI",
                         "KABİN AYDINLATMA", "KUYU AYDINLATMA", "KURULU GÜÇ",
                         "GERİLİM DÜŞÜMÜ", "TEMEL TOPRAKLAMA"):
            r.kontrol(f"avan ekranında '{beklenen}' bölümü var", beklenen in avan_ekran)

        # ===================================================================
        #  v1.3 — bodrum, imalatçı süreleri, askı/denge, tutarlılık köprüsü
        # ===================================================================
        adetSec(pg, 1)
        pg.wait_for_timeout(400)
        r.kontrol("⑪ bodrum alanı var", pg.is_visible("#c_bodrum"))
        pg.fill("#c_N", "13"); pg.fill("#c_h", "3")
        pg.fill("#c_bodrum", "")
        pg.wait_for_timeout(1100)
        _v0 = pg.inner_text("#c_sonuc")
        pg.fill("#c_bodrum", "2")
        pg.wait_for_timeout(1100)
        _v2 = pg.inner_text("#c_sonuc")
        r.kontrol("bodrum girilince hesap değişiyor", _v0 != _v2)
        r.kontrol("bodrum satırı paftada görünüyor",
                  "Bodrum durak adedi" in _v2)
        r.kontrol("toplam durak adedi paftada",
                  "Toplam durak adedi" in _v2)
        r.kontrol("bodrum açıklaması ( ! ) balonunda",
                  "H (Tablo-3)" in pg.eval_on_selector_all(
                      "#c_sonuc .bilgi-balon", "e=>e.map(x=>x.textContent).join(' ')"))
        r.kontrol("toplam seyahat mesafesi paftada",
                  "Toplam seyahat mesafesi" in _v2)
        pg.fill("#c_bodrum", "99")
        pg.wait_for_timeout(1100)
        r.kontrol("geçersiz bodrum hata veriyor",
                  "HESAP HATASI" in pg.inner_text("#c_sonuc"))
        pg.fill("#c_bodrum", "")
        #  N'yi örnek projedeki değere geri al: adet değişince ortak girdiler
        #  çoklu gövdeye aynalanıyor, sonraki adımlar örnek projeyi bekliyor.
        pg.fill("#c_N", "11")
        pg.wait_for_timeout(1000)

        # sekme uyarı rozeti — 6 kişilik kabin erişilebilirlik uyarısı üretir
        pg.select_option("#c_P1", "6")
        pg.wait_for_timeout(1100)
        r.kontrol("uyarıda sekme rozeti çıkıyor",
                  pg.is_visible('.sekme[data-sekme="trafik"] .sekme-rozet'))
        r.kontrol("6 kişi erişilebilirlik uyarısı ekranda GÖRÜNÜR (balonda değil)",
                  "81-70" in pg.inner_text("#c_sonuc"))
        pg.select_option("#c_P1", "10")
        pg.wait_for_timeout(1100)
        r.kontrol("uyarı bitince rozet kalkıyor",
                  not pg.is_visible('.sekme[data-sekme="trafik"] .sekme-rozet'))

        # ara değerli kapı genişlikleri artık hesaplanıyor
        for _kg in ("700", "1000", "1200"):
            pg.select_option("#c_kg1", _kg)
            pg.wait_for_timeout(1000)
            r.kontrol(f"kapı {_kg} mm hesaplanıyor",
                      "HESAP HATASI" not in pg.inner_text("#c_sonuc"))
        pg.select_option("#c_kg1", "900")
        pg.wait_for_timeout(900)

        # çoklu: asansör bazında bodrum ve imalatçı süreleri
        adetSec(pg, 2)
        r.kontrol("çoklu ortak bodrum alanı var", pg.is_visible("#c_bodrum"))
        pg.click('#s-coklu .katla:has-text("İleri seçenekler") >> nth=0')
        pg.wait_for_timeout(300)
        for _id in ("#c_bodrum1", "#c_mta1", "#c_mtk1", "#c_mtg1", "#c_mtp1"):
            r.kontrol(f"çoklu {_id} alanı açıldı", pg.is_visible(_id))
        _c0 = pg.inner_text("#c_sonuc")
        pg.fill("#c_mta1", "2,9")
        pg.wait_for_timeout(1200)
        _c1 = pg.inner_text("#c_sonuc")
        r.kontrol("çoklu manuel ta hesabı değiştiriyor", _c0 != _c1)
        r.kontrol("çoklu manuel süre uyarısı çıkıyor", "imalatçı verisiyle" in _c1)
        r.kontrol("uyarı balona girmedi, açıkta",
                  "imalatçı verisiyle" not in pg.eval_on_selector_all(
                      "#c_sonuc .bilgi-balon", "e=>e.map(x=>x.textContent).join(' ')"))
        pg.fill("#c_mta1", "")
        pg.wait_for_timeout(1000)
        adetSec(pg, 1)

        # avan: asansör bazında askı ve denge
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(400)
        #  v1.4: askı oranı artık normal girdi ( açılır liste ), denge faktörü
        #  ise ofis standardında kalıp katlanır bölümden ezilebiliyor.
        r.kontrol("askı oranı doğrudan görünür", pg.is_visible("#a_i_palanga1"))
        _a0 = pg.inner_text("#a_sonuc")
        pg.select_option("#a_i_palanga1", "1")
        pg.wait_for_timeout(1300)
        _a1 = pg.inner_text("#a_sonuc")
        r.kontrol("askı oranı değişince avan hesabı değişiyor", _a0 != _a1)
        pg.select_option("#a_i_palanga1", "2")
        pg.wait_for_timeout(1200)
        pg.click('#s-avan .katla:has-text("Ofis standardından farklı") >> nth=0')
        pg.wait_for_timeout(300)
        r.kontrol("denge faktörü alanı açıldı", pg.is_visible("#a_q_denge1"))
        _b0 = pg.inner_text("#a_sonuc")
        pg.fill("#a_q_denge1", "0,45")
        pg.wait_for_timeout(1300)
        _b1 = pg.inner_text("#a_sonuc")
        r.kontrol("denge faktörü değişince hesap değişiyor", _b0 != _b1)
        r.kontrol("asansör bazı kaynağı görünüyor", "asansör bazında" in _b1)
        pg.fill("#a_q_denge1", "")
        pg.wait_for_timeout(1200)

        # trafik ↔ avan tutarlılık köprüsü
        #  Örnek proje kendi doğal hâlinde ( 2 asansörlük grup ) sınanır.
        adetSec(pg, 2)
        pg.wait_for_timeout(900)
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(300)
        pg.select_option("#a_kapasite1", "25")
        pg.wait_for_timeout(1400)
        r.kontrol("kapasite tutarsızlığı uyarısı çıkıyor",
                  "kapasite trafik hesabında" in pg.inner_text("#a_sonuc"))
        pg.click('#s-avan button:has-text("Trafikten güncelle")')
        pg.wait_for_timeout(1600)
        r.kontrol("güncellemeden sonra tutarsızlık uyarısı kalkıyor",
                  "kapasite trafik hesabında" not in pg.inner_text("#a_sonuc"))
        #  örnek proje kendi içinde tutarlı olmalı — hiç uyarı üretmemeli
        r.kontrol("örnek projede tutarlılık uyarısı yok",
                  "NOLU ASANSÖR:" not in pg.inner_text("#a_sonuc"))
        #  blok başında değiştirilen girdiyi geri al (sonraki adımlar N=11 bekler)
        adetSec(pg, 1)
        pg.wait_for_timeout(300)
        pg.fill("#c_N", "11")
        pg.wait_for_timeout(1100)

        # ===================================================================
        #  ( ! ) açıklama simgesi — uzun yöntem metinleri balonda
        # ===================================================================
        adetSec(pg, 1)
        pg.wait_for_timeout(500)
        _n = pg.eval_on_selector_all(".bilgi", "e=>e.length")
        r.kontrol("sayfada ( ! ) simgeleri var", _n >= 8, f"→ {_n} adet")
        _bilgi = pg.query_selector('label:has-text("Bodrum durağı") .bilgi')
        r.kontrol("bodrum alanında ( ! ) var", _bilgi is not None)
        _balon = _bilgi.query_selector(".bilgi-balon")
        r.kontrol("balon kapalıyken görünmüyor", not _balon.is_visible())
        _bilgi.hover()
        pg.wait_for_timeout(400)
        r.kontrol("üzerine gelince balon açılıyor", _balon.is_visible())
        r.kontrol("balonda bodrum açıklaması var", "H (Tablo-3)" in _balon.inner_text())
        #  balon kırpılmıyor / ekrandan taşmıyor
        _k = _balon.bounding_box()
        _vp = pg.viewport_size
        r.kontrol("balon ekranın sağına taşmıyor",
                  _k["x"] + _k["width"] <= _vp["width"] - 4,
                  f"→ sağ kenar {_k['x']+_k['width']:.0f} / {_vp['width']}")
        r.kontrol("balon ekranın soluna taşmıyor", _k["x"] >= 4)
        r.kontrol("balon alta taşmıyor",
                  _k["y"] + _k["height"] <= _vp["height"] - 4)
        pg.mouse.move(0, 0)
        pg.wait_for_timeout(350)
        r.kontrol("mouse çekilince balon kapanıyor", not _balon.is_visible())
        #  dokunmatik: tıklayınca fare çekilse bile açık kalır, Esc kapatır
        _bilgi.click()
        pg.mouse.move(0, 0)
        pg.wait_for_timeout(350)
        r.kontrol("tıklayınca fare çekilse de balon açık kalıyor", _balon.is_visible())
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(300)
        r.kontrol("Esc balonu kapatıyor", not _balon.is_visible())
        #  klavye ile de açılmalı (erişilebilirlik)
        _bilgi.focus()
        pg.wait_for_timeout(300)
        r.kontrol("klavye odağıyla balon açılıyor", _balon.is_visible())
        pg.mouse.click(5, 5)
        pg.wait_for_timeout(250)
        #  sağ paneldeki bölüm başlığında da olmalı
        r.kontrol("bölüm başlığında ( ! ) var",
                  pg.query_selector("#c_sonuc .serit .bilgi") is not None)

        # ===================================================================
        #  v1.4 — birleşik trafik sekmesi, makine tipi, MRL kutusu
        # ===================================================================
        #  Adet seçici iki gövdeyi doğru değiştiriyor ve ortak girdiler duruyor
        r.esit("adet 1 → aynı gövde ( tek ekran )", adetSec(pg, 1), "s-coklu")
        r.esit("adet 1: N korundu", pg.input_value("#c_N"), "11")
        r.esit("adet 1: nüfus korundu", pg.input_value("#c_hizli1"), "44")
        r.kontrol("adet 1: hesap yapıldı", "HESAP HATASI" not in pg.inner_text("#c_sonuc"))
        #  Tek hesap "n adet gerekir" diyorsa tek tıkla gruba geçilebilmeli
        _ekran = pg.inner_text("#c_sonuc")
        r.kontrol("gerekli adet > 1 iken geçiş düğmesi çıkıyor",
                  "asansör olarak tanımla" in _ekran, f"→ {_ekran[:60]!r}")
        r.esit("adet 3 → grup gövdesi", adetSec(pg, 3), "s-coklu")
        r.esit("adet 3: ortak N aynalandı", pg.input_value("#c_N"), "11")
        r.esit("adet 3: nüfus aynalandı", pg.input_value("#c_hizli1"), "44")
        r.esit("adet 3: görünen kolon sayısı",
               pg.evaluate("[1,2,3,4].filter(i=>!document.getElementById('c_kutu'+i).hidden).length"), 3)
        r.kontrol("adet 3: kolonlar dolduruldu",
                  all(pg.input_value(f"#c_P{i}") for i in (1, 2, 3)))
        r.esit("adet 3: 4. kolon boşaltıldı", pg.input_value("#c_P4"), "")
        r.kontrol("adet 3: grup hesabı yapıldı",
                  "HESAP HATASI" not in pg.inner_text("#c_sonuc"))
        r.esit("adet 1'e dönüş", adetSec(pg, 1), "s-coklu")
        r.esit("dönüşte N hâlâ duruyor", pg.input_value("#c_N"), "11")

        #  Avan: makine tipi η'yı dolduruyor, askı oranı ayrı girdi
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(600)
        r.kontrol("makine tipi alanı var", pg.is_visible("#a_makine_tipi1"))
        r.kontrol("askı oranı alanı var", pg.is_visible("#a_i_palanga1"))
        pg.select_option("#a_makine_tipi1", "Dişli")
        pg.wait_for_timeout(1300)
        r.esit("dişli seçilince η = 0,50", pg.input_value("#a_eta1"), "0,50")
        pg.select_option("#a_makine_tipi1", "Dişlisiz")
        pg.wait_for_timeout(1300)
        r.esit("dişlisiz seçilince η = 0,85", pg.input_value("#a_eta1"), "0,85")
        #  askı oranı yalnız verim üzerinden etkili: 1:1 → η′ = η
        pg.select_option("#a_i_palanga1", "1")
        pg.wait_for_timeout(1300)
        _m = pg.inner_text("#a_sonuc")
        r.kontrol("1:1 askıda η aynen kullanılıyor", "0,85" in _m)
        #  Satır 1. asansörün KENDİ motor bölümünde aranır:  "η′" açıklama
        #  balonunda ve öteki asansörlerde de geçer.
        _eta_satiri = ("() => SON.a.asansorler[0].bolumler[0].adimlar"
                       ".filter(a => String(a.formul || '').startsWith('η′'))"
                       ".map(a => [a.islem, a.deger, a.kaynak])")
        r.esit("1:1 askıda η′ satırı yok", pg.evaluate(_eta_satiri), [])
        pg.select_option("#a_i_palanga1", "2")
        pg.wait_for_timeout(1300)
        _m = pg.inner_text("#a_sonuc")
        r.esit("2:1 askıda η′ = 0,85 − 0,10 = 0,75  ( MMO/697 §2.4 )", pg.evaluate(_eta_satiri),
               [["=   0,85 − 0,10", 0.75, "palangalı sistem  ·  MMO/697 §2.4"]])
        r.kontrol("η′ satırı ekrana basılmış", "0,85 − 0,10" in _m)
        r.kontrol("toplam sistem verimi kutusu ekrandan kalktı",
                  not pg.is_visible("#a_toplam_verim1"))
        pg.fill("#a_eta1", "0,82")
        pg.wait_for_timeout(1400)
        _m = pg.inner_text("#a_sonuc")
        r.kontrol("girilen η'dan 0,10 düşülüyor ( 0,82 − 0,10 )", "0,82 − 0,10" in _m)
        r.kontrol("makine verimi notu paftada", "η makine verimidir" in _m)
        r.kontrol("paftada 'artık uygulanmaz' notu yok", "uygulanmaz" not in _m)
        pg.fill("#a_eta1", "0,85")
        pg.wait_for_timeout(1300)

        #  MRL işaret kutusu
        r.kontrol("MRL kutusu var", pg.is_visible("#a_mk_yok"))
        pg.check("#a_mk_yok")
        pg.wait_for_timeout(1300)
        r.kontrol("MRL işaretliyken ölçüler kapanıyor",
                  pg.evaluate("document.getElementById('a_mk_uzunluk').disabled"))
        #  MRL işaretliyse makine dairesi bölümü EKRANDA DA hiç görünmez —
        #  makine dairesi yoksa aydınlatma hesabının konusu da yoktur.
        r.kontrol("MRL işaretliyken makine dairesi bölümü hiç görünmüyor",
                  "MAKİNE DAİRESİ" not in pg.inner_text("#a_sonuc"))
        pg.uncheck("#a_mk_yok")
        pg.wait_for_timeout(1300)
        r.kontrol("MRL kapalı + ölçü yok → açık uyarı",
                  "ÖLÇÜLERİ GİRİLMEDİ" in pg.inner_text("#a_sonuc"))
        pg.fill("#a_mk_uzunluk", "4200")
        pg.fill("#a_mk_genislik", "3100")
        pg.wait_for_timeout(1400)
        r.kontrol("ölçü girilince makine dairesi hesaplanıyor",
                  "MAKİNE DAİRESİ AYDINLATMA HESABI" in pg.inner_text("#a_sonuc"))
        pg.check("#a_mk_yok")
        pg.wait_for_timeout(1200)

        # ===================================================================
        #  v1.5 — asansör adedi TEK YERDE: avan trafiği takip eder
        # ===================================================================
        pg.check("#a_mk_yok")
        adetSec(pg, 2)
        pg.wait_for_timeout(1000)
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(700)
        r.esit("avan adedi 2'ye eşitlendi",
               pg.inner_text("#adet_dugmeler_a .adet-dg.secili").strip(), "2")

        # ===================================================================
        #  v1.6 — ofis varsayılanları: değişmeyenler bir kez ayarlanır
        # ===================================================================
        pg.click('.sekme[data-sekme="sabitler"]')
        pg.wait_for_timeout(500)
        r.kontrol("ofis standardı paneli var",
                  pg.query_selector("#sabit_b_form") is not None)
        #  Sabitler HESAP BAZINDA gruplu olmalı ( v1.7 )
        _gruplar = pg.eval_on_selector_all(
            "#sabit_b_form .bolum-bas",
            "e=>e.map(x=>x.textContent.split('—')[0].trim())")
        for _g in ("MOTOR GÜCÜ VE KUVVETLER", "AYDINLATMA",
                   "KURULU GÜÇ VE GERİLİM DÜŞÜMÜ", "TEMEL TOPRAKLAMA"):
            r.kontrol(f"sabit grubu var: {_g}",
                      any(_g in x for x in _gruplar), f"→ {_gruplar}")
        r.kontrol("gruba yazılmamış sabit kalmadı",
                  "DİĞER" not in pg.inner_text("#sabit_b_form"))
        for _k in ("q_denge", "n_ray", "gf", "Fmt", "kabin_armatur_W", "kuyu_armatur_W",
                   "priz_adedi", "cosfi", "motor_elektrik_verimi",
                   "UL", "IDn", "lc", "ayd_sutun"):
            r.kontrol(f"SABİTLER alanı yerinde: {_k}",
                      pg.query_selector("#sb_" + _k) is not None)
        for _k in ("U", "kappa", "eps_max", "gr", "Fmk", "Fsh", "S1", "S2",
                   "L2", "kablo_tipi", "L1_pay", "beta", "cubuk_sayisi"):
            r.kontrol(f"ofis varsayılanı alanı var: {_k}",
                      pg.query_selector("#of_" + _k) is not None)
        #  Kat yüksekliği ve kapı tipi ofis sabiti DEĞİL — her projede değişirler
        for _k in ("h", "kapi_tipi"):
            r.kontrol(f"ofis sabitlerinde YOK: {_k}",
                      pg.query_selector("#of_" + _k) is None)
        r.kontrol("kat yüksekliği trafik sekmesinde",
                  pg.query_selector("#c_h") is not None
                  and pg.query_selector("#c_h") is not None)
        r.kontrol("kapı tipi trafik sekmesinde",
                  pg.query_selector("#c_kt1") is not None)
        r.kontrol("taşındı bilgi bandı kaldırıldı",
                  pg.query_selector("#sabit_tasindi") is None)
        r.esit("U ofis varsayılanı 380", pg.input_value("#of_U"), "380")
        r.esit("çubuk adedi 4 ( ofis varsayılanı )", pg.input_value("#of_cubuk_sayisi"), "4")

        #  Avan ortak panelinden kalkmış olmalı
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(500)
        for _k in ("a_U", "a_kappa", "a_eps_max"):
            r.kontrol(f"{_k} avan panelinden kalktı", pg.query_selector("#" + _k) is None)
        #  v1.7: β ve çubuk adedi de ofis standardına taşındı
        for _k in ("a_beta", "a_cubuk_sayisi"):
            r.kontrol(f"{_k} avan panelinden kalktı", pg.query_selector("#" + _k) is None)
        #  Şerit boyu da kutu değildir:  her zaman temelden türetilir.
        r.kontrol("şerit boyu kutusu avan panelinden kalktı",
                  pg.query_selector("#a_serit_L") is None)

        #  Asansör kartı: malzeme alanları katlanır bölüme indi
        pg.evaluate("document.getElementById('a_ozel1').style.display='none';")
        pg.wait_for_timeout(200)
        r.kontrol("ray kütlesi kartta doğrudan görünmüyor", pg.is_hidden("#a_gr1"))
        r.esit("ray kütlesi boş ( ofis standardından gelecek )",
               pg.input_value("#a_gr1"), "")
        r.esit("ray kütlesi yer tutucusu ofis değeri",
               pg.get_attribute("#a_gr1", "placeholder"), "17,91")
        _s = pg.inner_text("#a_sonuc")
        r.kontrol("paftada ofis değerinin kaynağı KABUL yazıyor", "KABUL" in _s)
        r.kontrol("hesap yapılıyor ( eksik girdi uyarısı yok )",
                  "girdi tamamlanmadı" not in _s)

        #  Nsç otomatik: 16 kişilik asansör 11 kW ile UYGUN DEĞİL çıkıyordu
        r.kontrol("motor gücü otomatik seçildi",
                  "otomatik — standart kademe" in _s)
        r.kontrol("16 kişilik asansöre 15 kW seçildi", "15,00" in _s)
        r.kontrol("motor kontrolü uygun", "UYGUN DEĞİL" not in _s)
        r.esit("Nsç alanı boş, yer tutucu otomatik",
               pg.get_attribute("#a_Nsc1", "placeholder"), "otomatik")

        #  L1 = Hk + yatay güzergâh payı  ( paftada ne olduğu yazılır )
        r.kontrol("L1 Hk + yatay güzergâh payından türetildi", "Hk + yatay güzergâh" in _s)

        #  Ofis değeri değişince asansör hesabı da değişir ( tek yerden )
        pg.click('.sekme[data-sekme="sabitler"]')
        pg.wait_for_timeout(300)
        pg.fill("#of_gr", "23,7")
        pg.wait_for_timeout(1500)
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(600)
        r.kontrol("ofis ray kütlesi değişince hesap değişti",
                  "23,70" in pg.inner_text("#a_sonuc"))
        r.esit("yer tutucu da güncellendi",
               pg.get_attribute("#a_gr1", "placeholder"), "23,7")

        #  Asansör bazında ezme + rozet
        #  ( katlanır bölüm önceki bloklarda açılmış olabilir — tıklamak yerine
        #    doğrudan açık duruma getiriyoruz ki tekrar kapanmasın )
        pg.evaluate("document.getElementById('a_ozel1').style.display='';")
        pg.wait_for_timeout(250)
        pg.fill("#a_gr1", "17,91")
        pg.wait_for_timeout(1500)
        r.kontrol("özel değer rozeti çıktı",
                  "özel" in pg.evaluate(
                      "document.getElementById('a_ozel_rozet1').textContent"))
        r.kontrol("ezilen değer paftada asansör bazında görünüyor",
                  "GİRİŞ — asansör bazında" in pg.inner_text("#a_sonuc"))
        pg.fill("#a_gr1", "")
        pg.click('.sekme[data-sekme="sabitler"]')
        pg.wait_for_timeout(300)
        pg.fill("#of_gr", "17,91")
        pg.wait_for_timeout(1400)

        #  Q ve Gk artık GİRDİ değil, türetilen değer  ( v1.7 )
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(600)
        r.kontrol("Q alanı salt okunur",
                  pg.get_attribute("#a_Q_goster1", "readonly") is not None)
        r.kontrol("Gk alanı salt okunur",
                  pg.get_attribute("#a_Gk_goster1", "readonly") is not None)
        r.kontrol("Q alanı sarı ( girdi ) değil, gri gösterilir",
                  "salt" in (pg.get_attribute("#a_Q_goster1", "class") or ""))
        #  ( katlanır bölüm önceki bloklarda açılmış olabilir — kapalı duruma
        #    getirip "ana kartta görünmüyor" iddiasını sınıyoruz )
        pg.evaluate("document.getElementById('a_ozel1').style.display='none';")
        pg.wait_for_timeout(200)
        r.kontrol("Q elle ana kartta görünmüyor", pg.is_hidden("#a_Q_elle1"))
        r.kontrol("Gk elle ana kartta görünmüyor", pg.is_hidden("#a_Gk_elle1"))
        _kap = pg.input_value("#a_kapasite1")
        r.kontrol("Q kapasiteden geliyor",
                  pg.input_value("#a_Q_goster1") not in ("", None),
                  f"→ kapasite {_kap}, Q {pg.input_value('#a_Q_goster1')!r}")
        pg.select_option("#a_kapasite1", "25")
        pg.wait_for_timeout(1600)
        r.esit("kapasite 25 kişi → Q = 2.000 kg", pg.input_value("#a_Q_goster1"), "2.000")
        r.esit("Q = 2.000 kg → Gk = 1.600 kg ( Tablo-11 )",
               pg.input_value("#a_Gk_goster1"), "1.600")
        pg.select_option("#a_kapasite1", "10")
        pg.wait_for_timeout(1600)
        r.esit("kapasite 10 kişi → Q = 800 kg", pg.input_value("#a_Q_goster1"), "800")
        #  Tablo dışına çıkmak: katlanır bölümdeki Q elle
        pg.evaluate("document.getElementById('a_ozel1').style.display='';")
        pg.wait_for_timeout(250)
        pg.fill("#a_Q_elle1", "1500")
        pg.wait_for_timeout(1700)
        r.esit("Q elle girilince gösterim onu yansıtıyor",
               pg.input_value("#a_Q_goster1"), "1.500")
        r.kontrol("Q elle rozette sayılıyor",
                  "özel" in pg.evaluate(
                      "document.getElementById('a_ozel_rozet1').textContent"))
        pg.fill("#a_Q_elle1", "")
        pg.wait_for_timeout(1700)
        r.esit("Q elle silinince tablo değerine dönüyor",
               pg.input_value("#a_Q_goster1"), "800")
        r.kontrol("türetilen alanlar proje dosyasına yazılmıyor",
                  pg.evaluate("!('a_Q_goster1' in tumGirdiler()) "
                              "&& !('a_Gk_goster1' in tumGirdiler())"))

        #  L1 yer tutucusu hesaplanan değeri gösteriyor ( "Hk + pay" görünür olsun )
        r.kontrol("L1 yer tutucusu Hk + payı gösteriyor",
                  "Hk +" in (pg.get_attribute("#a_L11", "placeholder") or ""),
                  f"→ {pg.get_attribute('#a_L11', 'placeholder')!r}")
        pg.fill("#a_Hk1", "45")
        pg.wait_for_timeout(1700)
        r.kontrol("Hk değişince L1 yer tutucusu izliyor",
                  "48,50" in (pg.get_attribute("#a_L11", "placeholder") or ""),
                  f"→ {pg.get_attribute('#a_L11', 'placeholder')!r}")
        pg.fill("#a_Hk1", "38,50")
        pg.wait_for_timeout(1500)
        #  Topraklama L'si ile asansör L1'i karışmasın — çevre karşılaştırması
        r.kontrol("temel çevresi karşılaştırma notu çıkıyor",
                  "çevresi" in pg.evaluate(
                      "document.getElementById('a_temel_cevre').textContent"))
        r.kontrol("şerit boyu satırı topraklama diye etiketli",
                  "topraklama" in pg.eval_on_selector(
                      "#a_serit_tahmin", "e=>e.closest('.alan').querySelector('label').textContent"))

        # ------------------------------------------------------------------
        #  ŞERİT BOYU TEMEL ÖLÇÜLERİNDEN TÜRETİLİR  ( kutu yok )
        #  Kullanılan boy ekranda açılımıyla görünmeli.
        # ------------------------------------------------------------------
        _ac = pg.evaluate("document.getElementById('a_serit_tahmin').textContent")
        r.kontrol("türetme açılımı ekranda", "ring" in _ac and "102,30" in _ac,
                  f"→ {_ac!r}")
        #  Göz aralığı ofis standardında olmalı
        pg.click('.sekme[data-sekme="sabitler"]')
        pg.wait_for_timeout(500)
        r.kontrol("karelaj gözü ofis standardında",
                  pg.query_selector("#of_goz_araligi") is not None)
        r.esit("karelaj gözü varsayılanı 20", pg.input_value("#of_goz_araligi"), "20")
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(400)

        #  Excel şablonu kalktı:  Sabitler sekmesinde şablon durumu kartı yok
        pg.click('.sekme[data-sekme="sabitler"]')
        pg.wait_for_timeout(700)
        r.kontrol("şablon durumu kartı kaldırıldı",
                  pg.query_selector("#sablon_durumu") is None
                  and "ŞABLON" not in pg.inner_text("#s-sabitler"))

        #  Manuel k / manuel V ana akıştan kalktı — katlanır bölümde
        adetSec(pg, 2)
        pg.wait_for_timeout(900)
        r.kontrol("çokluda manuel k doğrudan görünmüyor", pg.is_hidden("#c_manuel_k"))
        r.kontrol("çokluda manuel V doğrudan görünmüyor", pg.is_hidden("#c_manuel_V"))
        pg.click('#s-coklu .katla:has-text("Manuel değerler")')
        pg.wait_for_timeout(400)
        r.kontrol("manuel değerler bölümü açıldı", pg.is_visible("#c_manuel_k"))
        pg.fill("#c_manuel_k", "0,08")
        pg.wait_for_timeout(1300)
        r.kontrol("elle girilen değer rozette görünüyor",
                  "elle" in pg.evaluate(
                      "document.getElementById('c_manuel_rozet').textContent"))
        #  Tablo-9'da değeri olan bina tipinde manuel k reddedilmeli
        r.kontrol("Tablo-9 varken manuel k reddediliyor",
                  "manuel k girilemez" in pg.inner_text("#c_sonuc"))
        pg.fill("#c_manuel_k", "")
        pg.wait_for_timeout(1300)
        r.kontrol("manuel k silinince hesap düzeliyor",
                  "HESAP HATASI" not in pg.inner_text("#c_sonuc"))
        r.esit("rozet de temizlendi",
               pg.evaluate("document.getElementById('c_manuel_rozet').textContent"), "")
        adetSec(pg, 1)
        pg.wait_for_timeout(700)

        #  Askı oranı OFİS SABİTİ DEĞİL — B) panelinden kalkmış olmalı
        pg.click('.sekme[data-sekme="sabitler"]')
        pg.wait_for_timeout(500)
        r.kontrol("askı oranı ofis standardı panelinde YOK",
                  pg.query_selector("#sb_i_palanga") is None)
        r.kontrol("denge faktörü ofis standardında duruyor",
                  pg.query_selector("#sb_q_denge") is not None)
        r.kontrol("diğer ofis sabitleri yerinde",
                  all(pg.query_selector("#sb_" + k) is not None
                      for k in ("n_ray", "gf", "Fmt", "cosfi", "UL")))
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(400)
        r.kontrol("askı oranı asansör kartında", pg.is_visible("#a_i_palanga1"))

        #  TRAFİK DEĞİŞİRSE AVAN İZLER  —  hiçbir düğmeye basmadan
        adetSec(pg, 2)
        pg.select_option("#c_P1", "13")
        pg.wait_for_timeout(1700)
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(800)
        r.esit("trafikte kapasite değişince avan kendiliğinden izliyor",
               pg.input_value("#a_kapasite1"), "13")
        r.kontrol("izlediği için tutarsızlık uyarısı yok",
                  "kapasite trafik hesabında" not in pg.inner_text("#a_sonuc"))

        #  Elle girilen değer, TRAFİK DEĞİŞMEDİKÇE korunur ( ezilmez )
        pg.select_option("#a_kapasite1", "16")
        pg.wait_for_timeout(1600)
        r.esit("elle girilen değer korunuyor", pg.input_value("#a_kapasite1"), "16")
        r.kontrol("elle değiştirilince uyarı çıkıyor",
                  "kapasite trafik hesabında" in pg.inner_text("#a_sonuc"))
        pg.wait_for_timeout(900)
        r.esit("ikinci hesapta da ezilmedi", pg.input_value("#a_kapasite1"), "16")

        #  Trafik yeniden değişince avan yine izler ( elle girilen değer aşılır )
        adetSec(pg, 2)
        pg.select_option("#c_P1", "10")
        pg.wait_for_timeout(1700)
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(800)
        r.esit("trafik yeniden değişince avan tekrar izliyor",
               pg.input_value("#a_kapasite1"), "10")
        r.kontrol("izleme sonrası uyarı kalmadı",
                  "kapasite trafik hesabında" not in pg.inner_text("#a_sonuc"))

        #  Trafik adedi artınca avan kartı kendiliğinden açılır
        adetSec(pg, 3)
        pg.wait_for_timeout(1200)
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(800)
        r.esit("trafik 3 olunca avan adedi de 3",
               pg.inner_text("#adet_dugmeler_a .adet-dg.secili").strip(), "3")
        r.kontrol("3. asansör kartı kendiliğinden açıldı", pg.is_checked("#a_aktif3"))
        r.esit("3. asansörün kapasitesi trafikten doldu",
               pg.input_value("#a_kapasite3"),
               pg.evaluate("document.getElementById('c_P3').value") or "10")
        r.kontrol("açılan kart 'trafik grubundan' etiketli",
                  "trafik grubundan" in pg.evaluate(
                      "document.getElementById('a_etiket3').textContent"))
        r.kontrol("eksik girdi uyarısı görünür ( sessiz kalmıyor )",
                  "3 NOLU ASANSÖR" in pg.inner_text("#a_sonuc"))

        #  Trafik adedinin ALTINA inilemez
        pg.evaluate("avanAdediSec(1)")
        pg.wait_for_timeout(700)
        r.esit("avan adedi trafiğin altına inmedi",
               pg.inner_text("#adet_dugmeler_a .adet-dg.secili").strip(), "3")
        r.kontrol("1 ve 2 düğmeleri kilitli görünüyor",
                  pg.evaluate("[...document.querySelectorAll('#adet_dugmeler_a .adet-dg')]"
                              ".slice(0,2).every(b=>b.classList.contains('kilitli'))"))

        #  Trafik grubu DIŞI asansör: adedi elle artır → not çıkar, uyarı değil
        pg.evaluate("avanAdediSec(4)")
        pg.wait_for_timeout(900)
        r.esit("elle 4'e çıkarıldı",
               pg.inner_text("#adet_dugmeler_a .adet-dg.secili").strip(), "4")
        r.kontrol("4. asansör 'trafik grubu dışı' etiketli",
                  "trafik grubu dışı" in pg.evaluate(
                      "document.getElementById('a_etiket4').textContent"))
        pg.select_option("#a_kapasite4", "6")
        pg.wait_for_timeout(1500)
        _s = pg.inner_text("#a_sonuc")
        r.kontrol("trafik dışı asansör NOT olarak bildiriliyor",
                  "trafik grubunda olmayan" in _s, f"→ {_s[:80]!r}")
        r.kontrol("bu bir uyarı değil, mavi not kutusunda",
                  pg.evaluate("[...document.querySelectorAll('#a_sonuc .uyari.mavi')]"
                              ".some(e=>e.textContent.includes('trafik grubunda olmayan'))"))

        #  Trafik grubu küçülünce DOLU kart kapanmaz — trafik dışına alınır
        adetSec(pg, 2)
        pg.wait_for_timeout(1200)
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(800)
        r.kontrol("dolu 4. asansör kapanmadı", pg.is_checked("#a_aktif4"))
        r.kontrol("3. asansör hâlâ açık ( kapasitesi dolu )", pg.is_checked("#a_aktif3"))

        #  Temizlik: sonraki bloklar 2 asansörlük örnek projeyi bekler
        pg.evaluate("['a_kapasite3','a_kapasite4'].forEach(i=>{"
                    "const e=document.getElementById(i); e.value='';}); AVAN_EK=0; planla();")
        pg.wait_for_timeout(1400)
        r.esit("boşaltılınca avan adedi 2'ye döndü",
               pg.inner_text("#adet_dugmeler_a .adet-dg.secili").strip(), "2")

        #  "Q elle" dolu kart, trafik kapasitesini yazmış ( otomatik işaretli )
        #  olsa bile kapanmaz;  eşitleme ikinci kez çalışınca hiçbir şey
        #  değişmez.  Eskiden kart kapanıyor, Q elle kalıyor, bir sonraki
        #  eşitlemede yeniden açılıyordu ( TEST 13 rastgele dizide buldu ).
        _q = pg.evaluate("""() => {
            const taban = avanTaban();
            alanaYaz($('a_Q_elle4'), '1000');  AVAN_OTO[4] = true;
            avanSenkron();
            const once = JSON.stringify(avanGirdi());
            const r = {taban, aktif: $('a_aktif4').checked, qelle: v('a_Q_elle4')};
            avanSenkron();
            r.ayni = once === JSON.stringify(avanGirdi());
            $('a_Q_elle4').value = '';  delete AVAN_OTO[4];  AVAN_EK = 0;  avanSenkron();
            return r; }""")
        r.kontrol("Q elle dolu kart denemesi trafik grubunun dışında", _q["taban"] < 4,
                  f"→ {_q}")
        r.kontrol("Q elle dolu, otomatik işaretli kart kapanmadı",
                  _q["aktif"] and _q["qelle"] == "1000", f"→ {_q}")
        r.kontrol("avan eşitlemesi ikinci kez çalışınca kartlar değişmiyor", _q["ayni"],
                  f"→ {_q}")
        adetSec(pg, 1)
        pg.wait_for_timeout(800)
        pg.fill("#c_N", "11")
        pg.wait_for_timeout(1100)

        # --- kalıcılık: sayfa yenilenince girdiler duruyor
        #  Proje kimliği artık PROJE KAPAĞI sekmesindedir ( k_* alanları );
        #  eski "Proje Bilgileri" kartı ( p_proje_adi … ) kaldırıldı.
        #  Kalıcılık kapak alanı üzerinden denetlenir.
        pg.click('.sekme[data-sekme="proje"]')
        pg.wait_for_timeout(250)
        pg.fill("#k_owner", "Kalıcılık Denemesi A.Ş.")
        pg.fill("#k_city", "İstanbul")
        pg.wait_for_timeout(700)
        pg.click('.sekme[data-sekme="trafik"]')
        pg.wait_for_timeout(250)
        pg.reload(wait_until="networkidle")
        pg.wait_for_timeout(1500)
        uygulamayaGir(pg)
        r.esit("yenileme sonrası N korundu", pg.input_value("#c_N"), "11")
        r.esit("yenileme sonrası kapak alanı korundu",
               pg.input_value("#k_owner"), "Kalıcılık Denemesi A.Ş.")
        r.esit("yenileme sonrası kapak alanı korundu ( il )",
               pg.input_value("#k_city"), "İstanbul")

        # --- indirme düğmeleri gerçekten dosya veriyor
        #  Trafik tek gövdedir; 1 ve 2 asansör tanımıyla iki kez denenir —
        #  ilki PAFTA, ikincisi PAFTA-COKLU yolunu üretmelidir.
        r.esit("arayüzde Excel düğmesi yok",
               pg.eval_on_selector_all(
                   "button", "e=>e.filter(x=>/xlsx|excel/i.test(x.textContent)).length"), 0)
        for adet, govde, metin, uzanti in ((1, "coklu", "PDF indir  (pafta)", ".pdf"),
                                           (2, "coklu", "PDF indir  (pafta)", ".pdf"),
                                           (0, "avan", "PDF indir", ".pdf")):
            sekme = "trafik" if govde == "coklu" else govde
            if adet:
                adetSec(pg, adet)
            else:
                pg.click(f'.sekme[data-sekme="{sekme}"]')
            pg.wait_for_timeout(300)
            try:
                with pg.expect_download(timeout=45000) as bilgi:
                    pg.click(f'#s-{govde} button:has-text("{metin}")')
                d = bilgi.value
                ad = d.suggested_filename
                r.kontrol(f"[{sekme}/{adet or 'avan'}] '{metin}' indirdi → {ad}",
                          ad.lower().endswith(uzanti))
            except Exception as e:                       # noqa: BLE001
                r.kontrol(f"[{sekme}/{adet or 'avan'}] '{metin}' indirme", False, f"→ {e}")

        # --- proje dosyası kaydet
        pg.click('.sekme[data-sekme="proje"]')
        pg.wait_for_timeout(200)
        pg.evaluate("document.querySelector('details.proje-araclari').open = true;")
        pg.wait_for_timeout(200)
        r.kontrol("proje araçları katlanır bölümde",
                  pg.query_selector("details.proje-araclari") is not None)
        try:
            with pg.expect_download(timeout=20000) as bilgi:
                pg.click('button:has-text("Projeyi kaydet")')
            r.kontrol("proje dosyası kaydedildi",
                      bilgi.value.suggested_filename.endswith(".avan"))
        except Exception as e:                           # noqa: BLE001
            r.kontrol("proje dosyası kaydetme", False, f"→ {e}")

        # --- REVİZYON: proje dosyasından geri yükleme
        #     Girdiler doldurulur, proje dosyası alınır, program sıfırlanır,
        #     dosya geri yüklenir ve girdilerin yerine oturduğu doğrulanır.
        import tempfile as _tempfile
        _D = _tempfile.mkdtemp(prefix="avan_arayuz_")
        pg.evaluate("""() => {
            uygula({c_bina_tipi:'Konut', c_bina_yuksekligi:'39,98', c_yapi_yuksekligi:'43',
                    c_N:'11', c_h:'3', c_hizli1:'44', c_hizli2:'3', c_bodrum:'2',
                    c_P1:'10', c_kg1:'900', c_kt1:'Merkezden Açılan Oto.',
                    a_temel_a:'26,55', a_temel_b:'16,4', a_serit_L:'58,5',
                    a_mk_yok:true, a_aktif1:true, a_tanim1:'İnsan', a_kapasite1:'10',
                    a_V1:'1,6', a_eta1:'0,85', a_Hk1:'32,85', a_kuyu_genisligi1:'1800',
                    a_kabin_boyu1:'1450', a_kabin_genisligi1:'1300',
                    a_makine_tipi1:'Dişlisiz', a_i_palanga1:'1', a_q_denge1:'0,45',
                    k_owner:'Kalıcılık Denemesi A.Ş.', __trafik_adet:1, __avan_ek:0});
            yaz(); hesaplaHepsi();
        }""")
        pg.wait_for_timeout(1500)
        _govde = pg.evaluate("JSON.parse(JSON.stringify(projeGovdesi('avan')))")

        pg.evaluate("localStorage.clear()")
        pg.reload(wait_until="networkidle")
        pg.wait_for_timeout(1200)
        uygulamayaGir(pg)
        adetSec(pg, 1)
        pg.wait_for_timeout(300)
        r.esit("sıfırlandıktan sonra N boş", pg.input_value("#c_N"), "")

        pg.evaluate("g => projeUygula(g, 'deneme.avan')", _govde)
        pg.wait_for_timeout(2500)
        r.kontrol("yükleme durum satırında bildiriliyor",
                  "Proje açıldı" in pg.inner_text("#durum"), f"→ {pg.inner_text('#durum')[:80]}")
        r.esit("proje dosyası kapak alanını da geri getiriyor",
               pg.input_value("#k_owner"), "Kalıcılık Denemesi A.Ş.")
        adetSec(pg, 1)
        pg.wait_for_timeout(400)
        for alan, beklenen in (("#c_N", "11"), ("#c_hizli1", "44"), ("#c_hizli2", "3"),
                               ("#c_bina_yuksekligi", "39,98"), ("#c_P1", "10"),
                               ("#c_bodrum", "2"), ("#c_kg1", "900")):
            r.esit(f"trafik girdisi geri geldi {alan}", pg.input_value(alan), beklenen)
        r.kontrol("hesap yeniden yapıldı", "HESAP HATASI" not in pg.inner_text("#c_sonuc"))
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(400)
        for alan, beklenen in (("#a_kuyu_genisligi1", "1800"), ("#a_Hk1", "32,85"),
                               ("#a_kapasite1", "10"), ("#a_temel_a", "26,55"),
                               ("#a_i_palanga1", "1"), ("#a_q_denge1", "0,45")):
            r.esit(f"avan girdisi geri geldi {alan}", pg.input_value(alan), beklenen)
        r.kontrol("1. asansör etkin", pg.is_checked("#a_aktif1"))
        #  v1.5: adet trafikten gelir — trafik birden çok asansör istiyorsa
        #  eksik kart kendiliğinden açılır, tek asansör istiyorsa açılmaz.
        _taban = pg.evaluate("avanTaban()")
        r.esit("avan adedi trafik grubuyla en az eşit",
               pg.evaluate("avanAdedi() >= avanTaban()"), True)
        r.esit("2. asansör kartı trafik adedine göre",
               pg.is_checked("#a_aktif2"), _taban >= 2)
        # Açılır listelerde ondalık ayracı tuzağı: dosyada "1,6" durur, seçeneğin
        # değeri "1.6"dır.  Eşleşmezse seçim boş kalır ve panel sessizce boşalır.
        r.kontrol("ondalıklı hız açılır listeye oturdu",
                  pg.input_value("#a_V1") not in ("", None),
                  f"→ {pg.input_value('#a_V1')!r}")
        r.kontrol("avan paneli hesap gösteriyor (boş kalmadı)",
                  "MOTOR GÜCÜ HESABI" in pg.inner_text("#a_sonuc"))

        # revizyon: bir girdiyi değiştir, sonuç güncellensin
        pg.fill("#a_kuyu_genisligi1", "2400")
        pg.wait_for_timeout(1200)
        _avan_metin = pg.inner_text("#a_sonuc")
        r.kontrol("revizyon sonrası avan hesabı güncellendi",
                  "2,40" in _avan_metin, "→ kuyu genişliği 2400 mm = 2,40 m görünmeli")

        # bozuk proje dosyası anlaşılır hata vermeli
        _kotu = os.path.join(_D, "bozuk.avan")
        open(_kotu, "wb").write(b"bu bir proje dosyasi degil")
        pg.click('.sekme[data-sekme="proje"]')
        pg.wait_for_timeout(200)
        pg.set_input_files("#dosya_ac", [_kotu])
        pg.wait_for_timeout(1200)
        r.kontrol("bozuk proje dosyası için hata gösterildi",
                  "geçerli bir proje dosyası değil" in pg.inner_text("#durum"),
                  f"→ {pg.inner_text('#durum')[:80]}")

        # --- dar ekran (telefon) düzeni bozulmuyor
        pg.set_viewport_size({"width": 390, "height": 844})
        pg.wait_for_timeout(600)
        tasma = pg.evaluate("document.documentElement.scrollWidth - window.innerWidth")
        r.kontrol("dar ekranda yatay taşma yok", tasma <= 2, f"→ {tasma} px taşma")

        # ==============================================================
        #  v2.9 — YÜKLEMEDE ÖNCEKİ PROJENİN ARTIKLARI
        #  uygula() yalnız GELEN alanları yazıyordu;  dosyada olmayan alanlar
        #  önceki projeden kalıyordu.  Tek asansörlük bir dosya, formda duran
        #  eski 2. ve 3. kolonlar yüzünden ÜÇLÜ GRUP olarak hesaplanabiliyordu.
        # ==============================================================
        pg.set_viewport_size({"width": 1440, "height": 900})
        pg.wait_for_timeout(400)
        pg.evaluate("trafikAdedi(3)")
        pg.wait_for_timeout(400)
        for _i, (_P, _kg) in enumerate((("10", "900"), ("16", "1100"), ("20", "1100")), 1):
            pg.select_option(f"#c_P{_i}", _P)
            pg.select_option(f"#c_kg{_i}", _kg)
        pg.wait_for_timeout(700)
        _once = pg.evaluate("[1,2,3,4].map(i=>(document.getElementById('c_P'+i)||{}).value)")
        r.kontrol("üç kolon dolduruldu", _once[:3] == ["10", "16", "20"], f"→ {_once}")

        pg.evaluate("""() => projeUygula({__mod:'avan', __surum:1, alanlar:{
            c_bina_tipi:'Konut', c_bina_yuksekligi:'39,98', c_yapi_yuksekligi:'43',
            c_N:'11', c_h:'3', c_hizli1:'44', c_hizli2:'3',
            c_P1:'10', c_kg1:'900', c_kt1:'Teleskopik Otomatik', __trafik_adet:1}}, 'tek.avan')""")
        pg.wait_for_timeout(3000)
        _sonra = pg.evaluate("[1,2,3,4].map(i=>(document.getElementById('c_P'+i)||{}).value)")
        r.kontrol("tek asansörlük dosya eski kolonları temizliyor",
                  not any(_sonra[1:]), f"→ {_sonra}")
        r.esit("tek asansörlük dosyada adet 1", pg.evaluate("TRAFIK_ADET"), 1)

        #  Dosyadaki avan kapasitesi / hızı, formdaki trafikle EZİLMEMELİ
        pg.evaluate("""() => projeUygula({__mod:'avan', __surum:1, alanlar:{
            c_bina_tipi:'Konut', c_bina_yuksekligi:'39,98', c_yapi_yuksekligi:'43',
            c_N:'11', c_h:'3', c_hizli1:'44', c_hizli2:'3',
            c_P1:'10', c_kg1:'900', c_kt1:'Teleskopik Otomatik', __trafik_adet:1,
            a_temel_a:'26,55', a_temel_b:'16,4', a_mk_yok:true,
            a_aktif1:true, a_tanim1:'A', a_kapasite1:'16', a_V1:'2.5', a_eta1:'0,85',
            a_Hk1:'32,85', a_kuyu_genisligi1:'2000', a_kabin_boyu1:'1700',
            a_kabin_genisligi1:'1300', a_makine_tipi1:'Dişlisiz'}}, 'avan16.avan')""")
        pg.wait_for_timeout(3500)
        r.esit("yüklenen avan kapasitesi korunuyor",
               pg.evaluate("(document.getElementById('a_kapasite1')||{}).value"), "16")
        r.kontrol("yüklenen avan hızı korunuyor",
                  pg.evaluate("(document.getElementById('a_V1')||{}).value")
                  in ("2,5", "2.5"))

        #  v2.9 — TIRNAK İÇEREN METİN KESİLMEMELİ.  kacis() yalnız & < >
        #  kaçırıyordu;  value="${kacis(...)}" özniteliğinde çift tırnak
        #  özniteliği erken kapatıyor, `Daire "A" bloğu` yazıp yeniden açınca
        #  alanda yalnız `Daire ` kalıyordu.
        pg.evaluate("""() => {
            document.getElementById('c_eknufus_liste').innerHTML = '';
            ekNufusEkle('c', {aciklama: 'Daire "A" bloğu & <ek>', miktar: '12',
                              kalem: 'DOĞRUDAN KİŞİ — Tablo-1 dışı'});
        }""")
        pg.wait_for_timeout(400)
        _ac = pg.evaluate(
            "(document.querySelector('#c_eknufus_liste .en-ac')||{}).value")
        r.esit("tırnak içeren açıklama korunuyor", _ac, 'Daire "A" bloğu & <ek>')
        _mi = pg.evaluate(
            "(document.querySelector('#c_eknufus_liste .en-mi')||{}).value")
        r.esit("miktar korunuyor", _mi, "12")

        # ==============================================================
        #  v3.1 — ÜST ŞERİT VE SOL PANEL YAPIŞKAN KALIR
        #  CSS'te position:sticky yazılıydı ama html/body'deki
        #  overflow-x:hidden body'yi kaydırma kabına çeviriyor, şerit ve
        #  panel sayfayla birlikte kayıp gidiyordu:  900 px aşağıda girdi
        #  paneli ekranın 781 px üstündeydi.  Uzun panel KENDİ İÇİNDE kayar;
        #  sayfanın sonunda bile başı sekmelerin altına girmez.
        # ==============================================================
        _olc = """sec => {
            const k = s => document.querySelector(s).getBoundingClientRect();
            return {y: scrollY, ust: k('.ust').top, sekme: k('.sekmeler').bottom,
                    ust_p: k(sec + ' .sol').top, alt_p: k(sec + ' .sol').bottom,
                    ekran: innerHeight};
        }"""

        def _yapiskan(etiket, sec):
            for _yer, _y in (("aşağıdayken", 1200), ("en alttayken", 10 ** 7)):
                pg.evaluate(f"window.scrollTo(0, {_y})")
                pg.wait_for_timeout(250)
                k = pg.evaluate(_olc, sec)
                r.kontrol(f"{etiket}: sayfa gerçekten kaydırıldı ( {_yer} )",
                          k["y"] > 300, f"→ {k}")
                r.kontrol(f"{etiket}: {_yer} üst şerit görünür",
                          abs(k["ust"]) < 1, f"→ {k}")
                #  Ölçü EKRANA göredir:  şeride göre ölçülseydi, ikisi birlikte
                #  kayıp gittiğinde aradaki mesafe değişmez, kontrol geçerdi.
                r.kontrol(f"{etiket}: {_yer} sol panel sekmelerin hemen altında",
                          0 < k["sekme"] <= k["ust_p"] <= k["sekme"] + 20, f"→ {k}")
                r.kontrol(f"{etiket}: {_yer} sol panelin tamamı ekranda",
                          0 < k["ust_p"] and k["alt_p"] <= k["ekran"], f"→ {k}")
            pg.evaluate("window.scrollTo(0, 0)")

        pg.set_viewport_size({"width": 1440, "height": 900})
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(1500)
        _yapiskan("avan", "#s-avan")
        #  Panelin altındaki düğme, panel kendi içinde kaydırılınca ekrana gelir
        pg.evaluate("document.querySelector('#s-avan .sol').scrollTop = 1e6")
        pg.wait_for_timeout(250)
        _d = pg.evaluate("""() => {
            const r = document.getElementById('dg_proje_dwg').getBoundingClientRect();
            return {ust: r.top, alt: r.bottom, sekme:
                    document.querySelector('.sekmeler').getBoundingClientRect().bottom,
                    ekran: innerHeight};
        }""")
        r.kontrol("avan: panelin en altındaki paket düğmesine ulaşılıyor",
                  _d["sekme"] <= _d["ust"] and _d["alt"] <= _d["ekran"], f"→ {_d}")
        pg.evaluate("document.querySelector('#s-avan .sol').scrollTop = 0")

        #  Uygulama projesi temiz girdiyle:  kasnaklar arası boşken halat karşı
        #  ağırlığa düşey iner, α çizimden 180 gelir ( kutu boş, içinde gri ).
        pg.evaluate("localStorage.removeItem('uygulama_program_v1')")
        pg.reload(wait_until="networkidle")
        pg.wait_for_timeout(600)
        pg.click("#gk_uygulama")
        pg.wait_for_timeout(2200)
        pg.click('.sekme[data-sekme="mukavemet"]')
        pg.wait_for_timeout(1500)
        _yapiskan("uygulama", "#s-mukavemet")
        r.esit("temiz projede α çizimden geliyor ( halat düşey iner )",
               (pg.input_value("#m_sarilma_acisi"),
                pg.get_attribute("#m_sarilma_acisi", "placeholder")), ("", "çizimden:  180"))
        #  Kasnaklar arası eski kurala ( varsayılan kabin 1.450 + 30 ):  halat
        #  ağırlığa eğik iner, açı çizimden bulunamaz — girilmezse tahrik
        #  bölümü HESAP EKSİK kalır, tabloda en az bir "uygun değil" satırı
        #  bulunur.  Aşağıdaki "α girilince" denetimleri bu projeyi okur.
        pg.evaluate("""() => { const e = document.getElementById('m_kabin_kasnak_arasi');
            e.value = '1480'; e.dispatchEvent(new Event('input', {bubbles: true}));
            e.dispatchEvent(new Event('change', {bubbles: true})); }""")
        pg.wait_for_timeout(1800)
        r.esit("halat eğik inince α çizimden gelmiyor",
               pg.get_attribute("#m_sarilma_acisi", "placeholder"), "")

        # ==============================================================
        #  v3.1 — SONUÇ HÜCRESİ HÜKMÜN RENGİYLE YAZILIR
        #  Arayüz "uygun değil" hücresine hata, "uygun" hücresine ok sınıfını
        #  veriyordu ama CSS'te kuralı yoktu:  "UYGUN DEĞİLDİR" ile
        #  "UYGUNDUR" aynı siyahla yazılıyordu.  Beklenen renk sayfanın kendi
        #  renk değişkenlerinden okunur — elle yazılmaz.
        # ==============================================================
        _renk = pg.evaluate("""() => {
            const renk = v => {
                const e = document.createElement('span');
                e.style.color = `var(${v})`;
                document.body.appendChild(e);
                const c = getComputedStyle(e).color;
                e.remove();
                return c;
            };
            const bek = u => u === true ? renk('--yesil')
                           : u === false ? renk('--kirmizi') : renk('--yazi');
            const satir = [...document.querySelectorAll('#m_sonuc tr.m-gidilir')];
            const ozet = [...document.querySelectorAll('#p_ozet tr.m-gidilir')];
            return {
                bolum: satir.map((tr, i) => [(SON.m.bolumler[i].sonuc || {}).uygun,
                    bek((SON.m.bolumler[i].sonuc || {}).uygun),
                    getComputedStyle(tr.lastElementChild).color]),
                bolum_sayisi: SON.m.bolumler.length,
                ozet: ozet.map((tr, i) => [SON.mc.ozet.asansorler[i].tumu_uygun,
                    bek(SON.mc.ozet.asansorler[i].tumu_uygun),
                    getComputedStyle(tr.lastElementChild).color]),
            };
        }""")
        r.esit("bölüm sonuçları: her bölümün bir satırı var",
               len(_renk["bolum"]), _renk["bolum_sayisi"])
        r.kontrol("bölüm sonuçları: hem uygun hem uygun değil satırı var",
                  {True, False} <= {u for u, _b, _g in _renk["bolum"]},
                  f"→ {[u for u, _b, _g in _renk['bolum']]}")
        _yanlis = [(i + 1, u, g) for i, (u, b, g) in enumerate(_renk["bolum"]) if b != g]
        r.kontrol("bölüm sonuçları: uygun yeşil, uygun değil kırmızı yazılıyor",
                  not _yanlis, f"→ ( bölüm, hüküm, renk ) {_yanlis}")
        r.kontrol("proje özeti: her asansörün sonucu hükmünün renginde",
                  _renk["ozet"] and all(b == g for _u, b, g in _renk["ozet"]),
                  f"→ {_renk['ozet']}")

        # ==============================================================
        #  v3.2 — SONUÇ TABLOSU ↔ AYRINTILI HESAP
        #  Satır tıklaması yalnız girdileri açar, sayfayı oynatmaz.  "Hesaba
        #  git" bölümün hesabına iner ve girdilerini de açar;  bölüm
        #  şeridindeki "Özete dön" tablodaki satırına geri getirir.  Canlı
        #  hesap sonucu yeniden çizdiğinde okunan bölüm yerinde kalır;
        #  kaydırma sürerken çizim gelirse gidiş yarıda kalmaz.
        # ==============================================================
        pg.set_viewport_size({"width": 1440, "height": 900})
        pg.evaluate("window.scrollTo(0, 0)")
        #  Sayaçlar — sarmalayan ifade 0 döndürür:  Playwright dönen işlevi
        #  çağırmaya kalkar.
        pg.evaluate("""window.__grup = 0; window.__ciz = 0;
            const _g = mGrupAc; mGrupAc = function(){ __grup++; return _g.apply(this, arguments); };
            const _c = cizMukavemet; cizMukavemet = function(){ __ciz++; return _c.apply(this, arguments); };
            0""")
        _say = pg.evaluate("""() => ({
            bolum: SON.m.bolumler.length,
            git: document.querySelectorAll('#m_sonuc tr[data-kimlik] .m-hesaba-git').length,
            don: document.querySelectorAll('#m_sonuc .serit[id] .m-ozete-don').length})""")
        r.kontrol("her bölüm satırında 'Hesaba git', her bölüm şeridinde 'Özete dön' var",
                  _say["bolum"] > 0 and _say["git"] == _say["bolum"] == _say["don"], f"→ {_say}")

        #  Ortadaki bölüm — sayı elle yazılmaz, motora bölüm eklenince kaymasın
        _kim = pg.evaluate("SON.m.bolumler[Math.floor(SON.m.bolumler.length / 2)].kimlik")
        _tr = f'#m_sonuc tr[data-kimlik="{_kim}"]'
        _ac = ("() => [...document.querySelectorAll('#m_form .m-grup.acik')]"
               ".map(g => MUK.gruplar[+g.dataset.grup].ad).sort()")

        pg.evaluate(f"window.scrollTo(0, document.querySelector('{_tr}')"
                    ".getBoundingClientRect().top + scrollY - 300)")
        pg.wait_for_timeout(300)
        _y0 = pg.evaluate("scrollY")
        pg.click(f"{_tr} td:nth-child(2)")
        pg.wait_for_timeout(800)
        r.esit("satır tıklaması sayfayı oynatmıyor", pg.evaluate("scrollY"), _y0)
        r.esit("satır tıklaması bölümün girdilerini açıyor", pg.evaluate(_ac),
               sorted(pg.evaluate(f"mBolumGruplari('{_kim}')")))

        pg.evaluate("__grup = 0")
        pg.click(f"{_tr} .m-hesaba-git")
        pg.wait_for_timeout(1500)
        _k = pg.evaluate(f"""() => {{
            const b = document.getElementById(mBolumCapa('{_kim}')).getBoundingClientRect();
            const p = document.querySelector('#s-mukavemet .sol').getBoundingClientRect();
            const g = document.querySelector('#m_form .m-grup[data-grup="'
                          + mBolumGrupNolari('{_kim}')[0] + '"]').getBoundingClientRect();
            return {{baslik: b.top, sekme: document.querySelector('.sekmeler').getBoundingClientRect().bottom,
                    grup: [g.top, g.top + 40], panel: [p.top, p.bottom], cagri: __grup,
                    odak: document.activeElement.className, odak_kimlik: document.activeElement.dataset.kimlik}};
        }}""")
        r.kontrol("'Hesaba git' bölüm başlığını sekmelerin hemen altına getiriyor",
                  0 < _k["sekme"] <= _k["baslik"] <= _k["sekme"] + 20, f"→ {_k}")
        r.esit("'Hesaba git' bölümün girdilerini de açıyor", pg.evaluate(_ac),
               sorted(pg.evaluate(f"mBolumGruplari('{_kim}')")))
        r.kontrol("açılan ilk girdi grubu sol panelde görünür",
                  _k["panel"][0] <= _k["grup"][0] and _k["grup"][1] <= _k["panel"][1], f"→ {_k}")
        r.esit("'Hesaba git' satırın tıklamasını ayrıca tetiklemiyor", _k["cagri"], 1)
        r.esit("odak bölümün 'Özete dön' düğmesinde",
               (_k["odak"], _k["odak_kimlik"]), ("m-ozete-don", _kim))

        #  CANLI HESAP:  α girilince üstteki iki uyarı kalkar ( içerik kısalır );
        #  okunan bölüm yine de yerinde kalmalı.
        _once = pg.evaluate(f"""() => [document.getElementById(mBolumCapa('{_kim}')).getBoundingClientRect().top,
                                      document.querySelectorAll('#m_sonuc .uyari').length, __ciz]""")
        pg.evaluate("""() => { const e = document.getElementById('m_sarilma_acisi');
            e.value = '180'; e.dispatchEvent(new Event('input', {bubbles: true}));
            e.dispatchEvent(new Event('change', {bubbles: true})); }""")
        pg.wait_for_timeout(1600)
        _sonra = pg.evaluate(f"""() => [document.getElementById(mBolumCapa('{_kim}')).getBoundingClientRect().top,
                                       document.querySelectorAll('#m_sonuc .uyari').length, __ciz]""")
        r.kontrol("canlı hesap: üstteki içerik değişti ( sınama anlamlı )",
                  _sonra[2] > _once[2] and _sonra[1] < _once[1], f"→ {_once} → {_sonra}")
        r.kontrol("canlı hesap: okunan bölüm yerinde kaldı",
                  abs(_sonra[0] - _once[0]) <= 2, f"→ {_once[0]} → {_sonra[0]}")

        #  KAYDIRMA SÜRERKEN ÇİZİM:  α kutusu odaktayken "Özete dön"e basmak
        #  kutudan çıkarır, hesap tazelenir ve çizim kaydırmanın ortasına
        #  denk gelir.  Gidiş yarıda kalmamalı.
        #  Kutuya KULLANICI GİBİ yazılır:  betikle değiştirilen kutudan
        #  çıkılınca tarayıcı "change" üretmez, çizim araya girmezdi.
        pg.evaluate("mGrupAc(+document.getElementById('m_sarilma_acisi')"
                    ".closest('.m-grup').dataset.grup, true)")
        pg.fill("#m_sarilma_acisi", "170")
        pg.wait_for_timeout(1200)
        _c0 = pg.evaluate("__ciz")
        pg.click(f"#{pg.evaluate(f'mBolumCapa({_kim!r})')} .m-ozete-don")
        pg.wait_for_timeout(2000)
        _d = pg.evaluate(f"""() => {{
            const t = document.querySelector('{_tr}').getBoundingClientRect();
            return {{ust: t.top, alt: t.bottom, ekran: innerHeight, cizim: __ciz,
                    sekme: document.querySelector('.sekmeler').getBoundingClientRect().bottom,
                    odak: document.activeElement.className, odak_kimlik: document.activeElement.dataset.kimlik}};
        }}""")
        r.kontrol("özete dönerken sonuç yeniden çizildi ( sınama anlamlı )",
                  _d["cizim"] > _c0, f"→ {_c0} → {_d['cizim']}")
        r.kontrol("'Özete dön' satırı ekrana getiriyor — araya giren çizime rağmen",
                  _d["sekme"] <= _d["ust"] and _d["alt"] <= _d["ekran"], f"→ {_d}")
        r.esit("odak satırın 'Hesaba git' düğmesinde — çizimden sonra da",
               (_d["odak"], _d["odak_kimlik"]), ("m-hesaba-git", _kim))

        #  Kullanıcı tekerleği çevirince ya da başka bir yere tıklayınca gidiş
        #  biter:  sonraki bir çizim onu hedefe geri çekmemeli, tıkladığı
        #  kutudan odağı çalmamalı.
        for _olay, _js in (("tekerlek", "new WheelEvent('wheel', {deltaY: -100})"),
                           ("fare", "new PointerEvent('pointerdown')")):
            pg.evaluate("window.scrollTo(0, 0)")
            pg.click(f"{_tr} .m-hesaba-git")
            pg.wait_for_timeout(60)
            _once_g = pg.evaluate("M_GIDIS !== null")
            pg.evaluate(f"dispatchEvent({_js})")
            r.kontrol(f"{_olay} süren gidişi bitiriyor",
                      _once_g and pg.evaluate("M_GIDIS === null"),
                      f"→ gidiş başlamış mıydı: {_once_g}")
            pg.wait_for_timeout(1200)

        #  Avan ve trafik bölümleri değişmedi:  ek verilmeden çizilen şerit
        #  eskisinin birebir aynısı ( kimlik yok, sağda düğme yok ).
        r.kontrol("ek verilmeyen bölüm şeridi eskisinin aynısı ( avan · trafik )",
                  pg.evaluate("""() => bolumCiz({baslik: 'B', kaynak: 'K'}) ===
                      '<div class="serit"><span>B' + bilgiSimgesi([]) +
                      '</span><span class="kaynak">K</span></div>'"""))

        #  ── ÇİZİMLER:  ÖLÇÜYE TIKLAMA ──────────────────────────────────
        #  Ölçü tıklanınca hangi girdiden geldiği söylenir;  yeni değer ölçünün
        #  geldiği GİRDİ KUTUSUNA yazılır, çizim ve hesap birlikte yenilenir
        #  ( çizim elle değişmez ).
        pg.evaluate("window.scrollTo(0, 0); mGorunumSec('cizim')")
        pg.wait_for_selector("#m_cizimler .cizim-svg .olcu", timeout=30000)
        r.kontrol("çizimler satır içi SVG, ölçüler tıklanır",
                  pg.evaluate("document.querySelectorAll('#m_cizimler .cizim-svg svg').length") >= 5
                  and pg.evaluate("document.querySelectorAll('#m_cizimler .olcu').length") > 50)
        r.esit("çizimlerin kimlikleri birbiriyle çakışmıyor",
               pg.evaluate("(() => { const i = [...document.querySelectorAll('#m_cizimler [id]')]"
                           ".map(e => e.id); return i.length - new Set(i).size; })()"), 0)
        #  TUVAL:  çizimler tek düzlemde yan yana ( CAD'in model alanı gibi ),
        #  açılışta hepsi sığar;  tekerlek imlecin altında yakınlaştırır,
        #  sürükleme kaydırır ( ölçü açmaz ), "Sığdır" hepsini geri getirir.
        pg.evaluate("window.scrollTo(0, 0)")
        pg.wait_for_timeout(300)
        _sigiyor = """() => { const t = document.getElementById('m_tuval').getBoundingClientRect();
            return [...document.querySelectorAll('#m_tuval figure.cizim')].every(f => {
                const b = f.getBoundingClientRect();
                return b.left >= t.left - 1 && b.right <= t.right + 1 && b.top >= t.top - 1
                       && b.bottom <= t.bottom + 1; }); }"""
        r.kontrol("çizimler tuvalde yan yana, açılışta hepsi sığıyor", pg.evaluate(_sigiyor))
        r.kontrol("tuval pencerenin altını aşmıyor",
                  pg.evaluate("document.getElementById('m_tuval').getBoundingClientRect().bottom")
                  <= pg.evaluate("innerHeight") + 1)
        _kut = pg.evaluate("""() => { const b = document.querySelector(
                '#m_tuval figure[data-cizim="kuyu_plani"]').getBoundingClientRect();
            return [Math.round(b.left + b.width / 2), Math.round(b.top + b.height / 2)]; }""")
        _dunya = ("(x, y) => { const t = document.getElementById('m_tuval').getBoundingClientRect(),"
                  " v = M_TUVAL.gorunum; return [v.x + (x - t.left) / v.s, v.y + (y - t.top) / v.s]; }")
        _once = pg.evaluate(f"({_dunya})({_kut[0]}, {_kut[1]})")
        _s0 = pg.evaluate("M_TUVAL.gorunum.s")
        pg.mouse.move(*_kut)
        pg.mouse.wheel(0, -400)
        pg.wait_for_timeout(300)
        _sonra = pg.evaluate(f"({_dunya})({_kut[0]}, {_kut[1]})")
        r.kontrol("tekerlek imlecin altındaki noktayı yerinde tutarak yakınlaştırıyor",
                  pg.evaluate("M_TUVAL.gorunum.s") > _s0 * 1.5
                  and abs(_once[0] - _sonra[0]) < 0.5 and abs(_once[1] - _sonra[1]) < 0.5,
                  f"→ {_s0} → {pg.evaluate('M_TUVAL.gorunum.s')}, {_once} / {_sonra}")
        _x0 = pg.evaluate("M_TUVAL.gorunum.x")
        pg.mouse.move(*_kut)
        pg.mouse.down()
        pg.mouse.move(_kut[0] - 120, _kut[1] - 60, steps=6)
        pg.mouse.up()
        pg.wait_for_timeout(300)
        r.kontrol("sürükleme kaydırıyor, ölçü kutusu açmıyor",
                  abs(pg.evaluate("M_TUVAL.gorunum.x") - _x0) > 10
                  and pg.evaluate("document.querySelectorAll('.olcu-kutu').length") == 0)
        pg.click("#m_tuval .tuval-arac >> text=Sığdır")
        pg.wait_for_timeout(300)
        r.kontrol("'Sığdır' hepsini yeniden sığdırıyor", pg.evaluate(_sigiyor))
        _kp = '#m_cizimler figure[data-cizim="kuyu_plani"] .olcu'
        _kg = pg.evaluate(f"""() => {{
            const g = [...document.querySelectorAll('{_kp}')].find(
                x => /^KUYU GENİŞLİĞİ/.test(x.querySelector('text').textContent));
            mTuvalGoster(g);
            return +g.querySelector('text').textContent.replace(/\\D+/g, '');
        }}""")
        pg.wait_for_timeout(300)
        pg.locator(_kp).filter(has_text="KUYU GENİŞLİĞİ").first.locator("text").click()
        pg.wait_for_selector(".olcu-kutu #m_olcu_hedef", timeout=20000)
        r.kontrol("ölçü kutusu kaynağı söylüyor", "Kuyu genişliği" in pg.inner_text(".olcu-kutu"),
                  f"→ {pg.inner_text('.olcu-kutu')[:200]!r}")
        #  Çizimi bozan değer önce sorulur:  varsayılan asansörde kuyu 100 mm
        #  genişleyince kabin – duvar 0,30 m'yi aşar, korkuluk gerekir ve tavana
        #  sığmaz — "Yine de uygula" ya da "Vazgeç".
        pg.fill("#m_olcu_hedef", str(_kg + 100))
        pg.press("#m_olcu_hedef", "Enter")
        pg.wait_for_selector(".olcu-kutu .cizim-liste", timeout=30000)
        r.kontrol("çizimi bozacak değer önce soruluyor ( sebebiyle )",
                  "Korkuluk" in pg.inner_text(".olcu-kutu"), f"→ {pg.inner_text('.olcu-kutu')[:200]!r}")
        r.esit("sorulan değer henüz kutuya yazılmadı", pg.input_value("#m_kuyu_genisligi"), str(_kg))
        pg.click(".olcu-kutu >> text=Vazgeç")
        r.esit("vazgeçince kutu kapanıyor, değer aynı",
               (pg.evaluate("document.querySelectorAll('.olcu-kutu').length"),
                pg.input_value("#m_kuyu_genisligi")), (0, str(_kg)))
        #  İNSAN GİBİ YAZMA:  rakamlar arasında 200 ms.  Kutudaki her rakam
        #  formun genel dinleyicisine ( ortak.js ) kaçıp 220 ms sonra hesabı ve
        #  çizimi yeniliyordu;  yenilenen çizim kutuyu kapatıyordu ( kullanıcı:
        #  "2 yazıyorum kapanıyor" ) — fill + Enter bunu göremiyordu.
        pg.locator(_kp).filter(has_text="KUYU GENİŞLİĞİ").first.locator("text").click()
        pg.wait_for_selector(".olcu-kutu #m_olcu_hedef", timeout=20000)
        _istek = pg.evaluate("[ISTEK.mukavemet, ISTEK.cizim]")
        pg.fill("#m_olcu_hedef", "")
        pg.type("#m_olcu_hedef", str(_kg - 50), delay=200)
        pg.wait_for_timeout(1200)
        r.kontrol("ölçü kutusuna yavaş yazınca kutu açık, yazılan duruyor",
                  pg.evaluate("document.querySelectorAll('.olcu-kutu #m_olcu_hedef').length") == 1
                  and pg.input_value("#m_olcu_hedef") == str(_kg - 50))
        r.esit("ölçü kutusuna yazmak hesabı ve çizimi tetiklemiyor",
               pg.evaluate("[ISTEK.mukavemet, ISTEK.cizim]"), _istek)
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(200)
        #  Alan arama da formun alanı değil:  her harfte hesap yapılıyordu
        _istek = pg.evaluate("ISTEK.mukavemet")
        pg.type("#m_ara", "kuyu", delay=120)
        pg.wait_for_timeout(600)
        r.esit("alan aramaya yazmak hesabı tetiklemiyor", pg.evaluate("ISTEK.mukavemet"), _istek)
        pg.fill("#m_ara", "")
        pg.evaluate("mAramaUygula()")
        #  Kurulabilen değer doğrudan uygulanır
        pg.locator(_kp).filter(has_text="KUYU GENİŞLİĞİ").first.locator("text").click()
        pg.wait_for_selector(".olcu-kutu #m_olcu_hedef", timeout=20000)
        _gorunum = pg.evaluate("JSON.stringify(M_TUVAL.gorunum)")
        pg.fill("#m_olcu_hedef", str(_kg - 50))
        pg.press("#m_olcu_hedef", "Enter")
        pg.wait_for_function(
            f"[...document.querySelectorAll('{_kp}')].some(g => "
            f"g.querySelector('text').textContent === 'KUYU GENİŞLİĞİ {_kg - 50}')", timeout=30000)
        r.esit("ölçüden yazılan değer girdi kutusunda", pg.input_value("#m_kuyu_genisligi"),
               str(_kg - 50))
        r.esit("çizim yenilenince görünüm yerinde ( zıplamıyor )",
               pg.evaluate("JSON.stringify(M_TUVAL.gorunum)"), _gorunum)
        r.kontrol("değişiklik bildiriliyor",
                  "→" in (pg.evaluate("(document.getElementById('m_olcu_bildirim') || {}).textContent")
                          or ""))
        #  Girdiye bağlı olmayan ölçü kuralını söyler ( sığınma alanının yeri )
        pg.evaluate("""() => { const g = [...document.querySelectorAll(
                '#m_cizimler figure[data-cizim="kabin_ustu"] .olcu')].find(
                x => x.querySelector('text') && /^\\d+$/.test(x.querySelector('text').textContent));
            mTuvalGoster(g); }""")
        _kural = pg.evaluate("""async () => {
            for (const g of document.querySelectorAll('#m_cizimler figure[data-cizim="kabin_ustu"] .olcu')) {
                g.dispatchEvent(new MouseEvent('click', {bubbles: true}));
                for (let n = 0; n < 60 && !(document.querySelector('.olcu-kutu .olcu-deger')
                                             || document.querySelector('.olcu-kutu .uyari')); n++)
                    await new Promise(r => setTimeout(r, 100));
                const k = document.querySelector('.olcu-kural');
                if (k) return k.textContent;
            }
            return null; }""")
        r.kontrol("kurala bağlı ölçü kuralını söylüyor", bool(_kural), f"→ {_kural!r}")
        pg.keyboard.press("Escape")
        r.esit("Esc ölçü kutusunu kapatıyor",
               pg.evaluate("document.querySelectorAll('.olcu-kutu').length"), 0)
        #  "Formda göster":  alanın grubu açılır, alan odaklanır.  Sonra kuyu
        #  genişliği eski değerine ( sonraki denetimler varsayılan projeyi okur ).
        pg.evaluate("mAlanGoster('kuyu_genisligi')")
        pg.wait_for_timeout(400)
        r.kontrol("'Formda göster' alanı açıp odaklıyor",
                  pg.is_visible("#m_kuyu_genisligi")
                  and pg.evaluate("document.activeElement.id") == "m_kuyu_genisligi")
        pg.fill("#m_kuyu_genisligi", str(_kg))
        pg.wait_for_timeout(1500)
        pg.evaluate("mGorunumSec('hesap')")

        pg.emulate_media(media="print")
        r.esit("yazdırırken 'Hesaba git' ve 'Özete dön' basılmıyor",
               pg.evaluate("[...document.querySelectorAll('.m-hesaba-git, .m-ozete-don')]"
                           ".filter(e => getComputedStyle(e).display !== 'none').length"), 0)
        pg.emulate_media(media="screen")

        r.kontrol("konsol hatası yok", not konsol, f"→ {konsol[:4]}")
        tarayici.close()
    return r


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)

# -*- coding: utf-8 -*-
"""
TEST 13  —  CANLI HESAP TUTARLILIĞI  ( tarayıcı )

Kural tek cümledir:

    Girdiler NASIL değiştirilirse değiştirilsin, hesap durulduğunda
    EKRANDAKİ SONUÇ  =  FORMDAKİ GİRDİLERİN SUNUCUDAKİ TAZE HESABI.

Öteki testler motorun doğru hesapladığını kanıtlar;  bu test ekranın o
hesabı GÜNCEL tuttuğunu kanıtlar.  Yarışlar ( yolda kalmış eski yanıt,
gecikmeli hesap, türetilen alanın geri yazılması ) tam burada saklanır:
motor doğrudur ama ekran eski bir girdinin sonucunu gösterir ya da eski bir
değeri bir sonraki hesaba taşır.

  1. HER ALAN TEK TEK  —  uygulama ve avan projesinin formundaki her girdi
     ( ofis sabitleri dâhil ) değiştirilir, hesap durulur, kural denetlenir;
     değer geri alınır ve bir sonraki alana HEMEN geçilir ( geri alma ile
     sonraki değişiklik de üst üste biner ).
  2. HIZLI DEĞİŞİKLİK DİZİLERİ  —  tohumlu rastgele eylemler ( alan
     değiştirme · beyan yükü · elle kabin ağırlığı · asansör adedi / sekmesi
     · makine dairesi · trafik adedi ) rastgele aralıklarla
     ve YAPAY AĞ GECİKMESİYLE ( her yanıt 0 - 500 ms ) art arda uygulanır;
     her dizinin sonunda kural denetlenir.
  3. TÜRETİLEN ALAN  —  bir asansörde son olay beyan yükü değişikliğiyse o
     asansörün kabin ağırlığı yeni yükün OFİS TABLOSU değeridir;  son olay
     elle yazılan değerse o değerdir.
  4. İNDİRİLEN ÇIKTI  —  PDF ve paketin sunucuya gönderdiği girdi, ekranın
     hesapladığı girdiyle aynı sonucu verir ( çok asansörlü projede de ).
  5. KAYDEDİLEN PROJE  —  yük değiştirilip hesap gelmeden kaydedilen proje
     ( dosya ya da tarayıcı belleği ) açılınca yeni yükün kabin ağırlığıyla
     hesaplanır.

"Aynı" kelimenin tam anlamıyladır:  sonucun JSON'u bayt bayt karşılaştırılır
ve ekrana basılan bölüm hükümleri de aranır.

Sunucu ( baslat.command ) ve Playwright gerekir;  yoksa test atlanır.
"""

import os
import random
import sys
import urllib.request

#  Giriş noktası:  programın kökleri ( depo kökü, hesap/ ) — yollar.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import yollar

yollar.kur()

from motor.ortak import ofis
from dogrulama.rapor import Rapor
from dogrulama.pencere import pencere_dinle

BASE = os.environ.get("AVAN_TEST_URL", "http://127.0.0.1:8780")
TOHUM = 20260914
DIZI_ADEDI = 18

#  Hesap isteklerini sayar, isteğe bağlı gecikme ekler, olay zamanını tutar.
_ALET = """() => {
  if (window.__T) return;
  const f0 = window.fetch;
  const T = window.__T = {f0, ucus: 0, son: 0, olay: 0, gecikme: () => 0};
  window.fetch = async (u, o) => {
    if (!/\\/api\\/(uygulama\\/coklu|trafik|avan)$/.test(String(u))) return f0(u, o);
    T.ucus++;
    try {
      const r = await f0(u, o);
      const g = T.gecikme();
      if (g) await new Promise(z => setTimeout(z, g));
      return r;
    } finally { T.ucus--; T.son = performance.now(); }
  };
  const isaretle = () => { T.olay = performance.now(); };
  document.addEventListener('input', isaretle, true);
  document.addEventListener('change', isaretle, true);
  document.addEventListener('click', isaretle, true);
  T.sakin = async () => {
    const bek = ms => new Promise(z => setTimeout(z, ms));
    for (let i = 0; i < 400; i++) {
      await bek(60);
      const t = performance.now();
      if (T.ucus === 0 && t - T.son > 330 && t - T.olay > 330) return true;
    }
    return false;
  };
  //  Girdi kimliği → değiştirilecek yeni değer
  T.yeni = (e, i) => {
    if (e.type === 'checkbox') return !e.checked;
    if (e.tagName === 'SELECT') {
      const ops = [...e.options].map(o => o.value).filter(v => v !== e.value);
      return ops.length ? ops[i % ops.length] : e.value;
    }
    const v = String(e.value || '').trim();
    if (v === '') return String(2 + (i % 9));
    const s = Number(v.replace(',', '.'));
    if (isFinite(s)) {
      if (s === 0) return '1';
      if (Number.isInteger(s)) { const y = Math.round(s * 1.1); return String(y === s ? s + 1 : y); }
      return String(+(s * 1.1).toFixed(3)).replace('.', ',');
    }
    return v + ' x';
  };
  T.yaz = (e, deger) => {
    if (e.type === 'checkbox') e.checked = !!deger; else e.value = deger;
    e.dispatchEvent(new Event('input', {bubbles: true}));
    e.dispatchEvent(new Event('change', {bubbles: true}));
  };
  //  Sonuç nesnesindeki bütün bölüm hükümleri ve hata metinleri
  T.metinler = r => {
    const out = [];
    const gez = (x, anahtar) => {
      if (out.length > 40 || x === null || typeof x !== 'object') return;
      if (anahtar === 'sonuc' && typeof x.metin === 'string') out.push(x.metin);
      for (const [k, d] of Object.entries(x)) gez(d, k);
    };
    gez(r, '');
    if (typeof r.hata === 'string') out.push(r.hata);
    if (Array.isArray(r.hata)) out.push(...r.hata.filter(h => typeof h === 'string'));
    return out;
  };
  T.ilkFark = (a, b) => {
    const f = [];
    const gez = (x, y, yol) => {
      if (f.length >= 4) return;
      if (x === null || y === null || typeof x !== 'object' || typeof y !== 'object') {
        if (JSON.stringify(x) !== JSON.stringify(y))
          f.push(`${yol}: ekranda ${String(JSON.stringify(x)).slice(0, 70)} · taze ${String(JSON.stringify(y)).slice(0, 70)}`);
        return;
      }
      for (const k of new Set([...Object.keys(x), ...Object.keys(y)])) gez(x[k], y[k], yol + '.' + k);
    };
    gez(a, b, '');
    return f;
  };
  const tek = s => String(s).replace(/\\s+/g, ' ');
  T.post = async (u, b) => await (await f0(u, {method: 'POST',
      headers: {'Content-Type': 'application/json'}, body: JSON.stringify(b)})).json();
  //  KURAL:  ekrandaki sonuç = formun taze hesabı  ( + ekrana basılmış mı )
  T.denetle = async (mod) => {
    const sonuc = {farklar: [], dom: []};
    //  secici:  sonucun EKRANDA gösterilen kısmı ( uygulamada aktif asansör )
    const kiyas = async (ad, ekranda, istek, uc, kutu, secici = x => x) => {
      const taze = await T.post(uc, istek);
      if (JSON.stringify(ekranda) !== JSON.stringify(taze))
        sonuc.farklar.push(ad + ' — ' + (T.ilkFark(ekranda, taze).join(' | ') || 'yapı farklı'));
      const metin = tek(document.getElementById(kutu).innerText);
      for (const m of T.metinler(secici(taze)))
        if (!metin.includes(tek(m))) { sonuc.dom.push(`${ad}: ekranda yok → ${m.slice(0, 80)}`); break; }
    };
    //  İndirilen çıktının gövdesi ekranın sonucunu vermeli
    const cikti = async (ad, ekranda, govde, uc) => {
      const taze = await T.post(uc, govde);
      if (JSON.stringify(ekranda) !== JSON.stringify(taze))
        sonuc.farklar.push(`${ad} çıktısı ekrandan farklı — ` + (T.ilkFark(ekranda, taze).join(' | ') || 'yapı farklı'));
    };
    if (mod === 'uygulama' && SON.mc && SON.mc.on_yuz) {
      //  ÖN YÜZ GİRDİYİ DURDURDU ( uygulama.js mGirdiDenetle ):  istek gitmedi,
      //  ekranda ön yüzün iletisi var.  Kural:  sunucu da reddeder ( hesap ya
      //  da — çizim alanında — çizim ucu ) — ön yüz sunucudan sıkı olamaz.
      const ist = mukavemetIstek();
      const taze = await T.post('/api/uygulama/coklu', ist);
      let red = taze.aktif === false || ((taze.asansorler || [])[MUK_AKTIF] || {}).aktif === false;
      if (!red) red = (await T.post('/api/uygulama/cizimler', {...ist, asansor: MUK_AKTIF})).aktif === false;
      if (!red) sonuc.farklar.push('ön yüz girdiyi durdurdu, sunucu kabul ediyor — ' + SON.mc.hata.join(' · '));
      const metin = tek(document.getElementById('m_sonuc').innerText);
      for (const m of SON.mc.hata) if (!metin.includes(tek(m))) sonuc.dom.push(`ön yüz: ekranda yok → ${m.slice(0, 80)}`);
      sonuc.kabin = MUK_ASANSORLER.slice(0, MUK_ADET).map((a, j) => [a.beyan_yuku, a.kabin_agirligi, false, mGkTazelenecek(j)]);
    } else if (mod === 'uygulama') {
      const ist = mukavemetIstek();
      await kiyas('uygulama', SON.mc, ist, '/api/uygulama/coklu', 'm_sonuc',
                  c => ({...((c.asansorler || [])[MUK_AKTIF] || c), proje_geneli: null}));
      await cikti('uygulama PDF', SON.mc, indirGovdesi('uygulama-pdf'), '/api/uygulama/coklu');
      await cikti('uygulama paketi', SON.mc, indirGovdesi('uygulama-dwg'), '/api/uygulama/coklu');
      //  [ yük , kabin , hesabı yapıldı mı , tablodan yenilenmeyi bekliyor mu ]
      sonuc.kabin = MUK_ASANSORLER.slice(0, MUK_ADET).map((a, j) => [a.beyan_yuku, a.kabin_agirligi,
        !!(SON.mc && SON.mc.asansorler && SON.mc.asansorler[j] && SON.mc.asansorler[j].girdi),
        mGkTazelenecek(j)]);
    } else {
      await kiyas('trafik', SON.t, {girdiler: trafikGirdi()}, '/api/trafik', 'c_sonuc');
      await kiyas('avan', SON.a, {girdiler: avanGirdi()}, '/api/avan', 'a_sonuc');
      await cikti('trafik PDF', SON.t, indirGovdesi('trafik-pdf'), '/api/trafik');
      await cikti('avan PDF', SON.a, indirGovdesi('avan-pdf'), '/api/avan');
      //  Trafikten türeyen avan kartları DURULMUŞ olmalı:  eşitleme bir kez
      //  daha çalıştırılınca avanın girdisi değişmemeli.
      const once = JSON.stringify(avanGirdi());
      avanSenkron();
      if (JSON.stringify(avanGirdi()) !== once) sonuc.farklar.push('avan kartları trafikle eşit değil');
    }
    return sonuc;
  };
}"""


def _sunucu_var():
    try:
        urllib.request.urlopen(BASE + "/api/saglik", timeout=5).read()
        return True
    except Exception:  # noqa: BLE001
        return False


def _ac(pg, mod):
    pg.goto(BASE, wait_until="networkidle")
    pg.evaluate("localStorage.clear()")
    pg.goto(BASE, wait_until="networkidle")
    pg.wait_for_timeout(500)
    if pg.is_visible("#giris"):
        pg.click("#gk_" + mod)
    pg.wait_for_timeout(2500)
    pg.evaluate(_ALET)


def _sakin(pg):
    return pg.evaluate("__T.sakin()")


def _kural(r, pg, mod, etiket):
    if not _sakin(pg):
        r.kontrol(f"[{mod}] {etiket} · hesap duruluyor", False, "→ 24 sn içinde durulmadı")
        return None
    d = pg.evaluate("m => __T.denetle(m)", mod)
    r.kontrol(
        f"[{mod}] {etiket} · ekrandaki sonuç = formun taze hesabı",
        not d["farklar"],
        "→ " + " || ".join(d["farklar"])[:600],
    )
    r.kontrol(f"[{mod}] {etiket} · sonuç ekrana basılmış", not d["dom"], "→ " + " || ".join(d["dom"])[:300])
    return d


# ---------------------------------------------------------------- 1. alanlar
_ALANLAR = """(mod) => [...document.querySelectorAll('input,select')]
  .filter(e => e.id && e.id.indexOf('_goster') < 0 && e.type !== 'file' && e.type !== 'search')
  .filter(e => alanModu(e.id) === mod)
  .filter(e => !/^(a_aktif|k_|mk_proje|mk_isveren|mk_pafta|m_dosya)/.test(e.id))
  .map(e => e.id)"""


def _her_alan(r, pg, mod):
    kimlikler = pg.evaluate(_ALANLAR, mod)
    r.kontrol(f"[{mod}] denetlenecek alan sayısı", len(kimlikler) > 60, f"→ {len(kimlikler)}")
    for i, kimlik in enumerate(kimlikler):
        eski = pg.evaluate(
            """([id, i]) => { const e = document.getElementById(id);
            const eski = e.type === 'checkbox' ? e.checked : e.value;
            __T.yaz(e, __T.yeni(e, i)); return eski; }""",
            [kimlik, i],
        )
        _kural(r, pg, mod, f"alan {kimlik}")
        #  Geri al ve BEKLEMEDEN sonraki alana geç — üst üste binen değişiklik
        pg.evaluate("([id, v]) => __T.yaz(document.getElementById(id), v)", [kimlik, eski])
    _kural(r, pg, mod, "bütün alanlar geri alındıktan sonra")


# ---------------------------------------------------------------- 2-3. diziler
def _uygulama_dizileri(r, pg, rnd):
    tablo = {q: ofis.bos_kabin_kutlesi(q) for q in (450, 630, 800, 1000, 1275, 1600)}
    alanlar = pg.evaluate(_ALANLAR, "uygulama")
    #  Makine dairesi seçimi iki yönde de geçerli kalsın
    pg.evaluate("""() => { const e = id => document.getElementById(id);
        __T.yaz(e('m_mk_uzunluk'), '4000'); __T.yaz(e('m_mk_genislik'), '3000'); }""")
    _gecersizden_donus(r, pg)
    _ardisik_iki_asansor(r, pg)
    _hemen_kaydet(r, pg)
    pg.evaluate("__T.gecikme = () => Math.floor(Math.random() * 500)")
    for n in range(DIZI_ADEDI):
        son_olay = {}  # asansör sırası → ( 'beyan', yük ) | ( 'elle', değer )
        olaylar = []  # hata iletisi için
        for _ in range(rnd.randint(3, 8)):
            eylem = rnd.choice(("beyan", "beyan", "elle", "alan", "alan", "adet", "sekme", "mrl"))
            aktif = pg.evaluate("MUK_AKTIF")
            olaylar.append(f"{eylem}@{aktif + 1}")
            if eylem == "beyan":
                q = rnd.choice(sorted(tablo))
                pg.evaluate("q => __T.yaz(document.getElementById('m_beyan_yuku'), String(q))", q)
                son_olay[aktif] = ("beyan", q)
            elif eylem == "elle":
                deger = rnd.choice((650, 777, 900, 1111))
                pg.evaluate("v => __T.yaz(document.getElementById('m_kabin_agirligi'), String(v))", deger)
                son_olay[aktif] = ("elle", deger)
            elif eylem == "alan":
                #  Bir alanı değiştirip kısa süre sonra geri al ( yanlış yazıp
                #  düzelten kullanıcı ) — proje kalıcı olarak bozulmasın ki kabin
                #  ağırlığı beklentisi her dizide denetlenebilsin.
                kimlik = rnd.choice(alanlar)
                if kimlik in ("m_beyan_yuku", "m_kabin_agirligi", "m_adet"):
                    continue
                eski = pg.evaluate(
                    "([id, i]) => { const e = document.getElementById(id);"
                    " const eski = e.type === 'checkbox' ? e.checked : e.value;"
                    " __T.yaz(e, __T.yeni(e, i)); return eski; }",
                    [kimlik, rnd.randint(0, 9)],
                )
                pg.wait_for_timeout(rnd.randint(0, 300))
                pg.evaluate("([id, v]) => __T.yaz(document.getElementById(id), v)", [kimlik, eski])
            elif eylem == "adet":
                once = pg.evaluate("MUK_ASANSORLER.length")
                sonra = pg.evaluate(
                    "n => { mAdetDegisti(n); return MUK_ASANSORLER.length; }", rnd.randint(1, 3)
                )
                #  Yeni açılan asansör 1. asansörün kopyasıdır — beklentisini de alır
                for j in range(once, sonra):
                    if 0 in son_olay:
                        son_olay[j] = son_olay[0]
            elif eylem == "sekme":
                pg.evaluate("i => mAsansorSekmesi(Math.min(i, MUK_ADET - 1))", rnd.randint(0, 2))
            elif eylem == "mrl":
                pg.evaluate(
                    "v => document.querySelector("
                    '`.secim-ikili[data-icin="m_mk_yok"] .secim-dg[data-deger="${v}"]`)'
                    ".click()",
                    rnd.randint(0, 1),
                )
            pg.wait_for_timeout(rnd.randint(0, 400))
        d = _kural(r, pg, "uygulama", f"dizi {n + 1}")
        if not d:
            continue
        _kabin_beklentisi(r, d, son_olay, tablo, f"dizi {n + 1}", olaylar)
    pg.evaluate("__T.gecikme = () => 0")


def _gecersizden_donus(r, pg):
    """İstek bütünüyle reddedilirken yük değişirse tablo değeri gelemez;
    girdi düzeltilince yenileme GELMELİ ( işaret açık kalmış olmalı ).

    Tek bir alanı geçersiz asansörde sunucu kabin ağırlığını yine tablodan
    doldurur;  BÜTÜN isteği reddeden durum belirsiz yazılmış bir sayıdır
    ( "1.350" — bin üç yüz elli mi, bir virgül otuz beş mi )."""
    q = 1600
    pg.evaluate("""() => { const e = id => document.getElementById(id);
        __T.yaz(e('m_kabin_agirligi'), '777'); }""")
    _sakin(pg)
    pg.evaluate(
        """q => { const e = id => document.getElementById(id);
        __T.yaz(e('m_kabin_genisligi'), '1.350');
        __T.yaz(e('m_beyan_yuku'), String(q)); }""",
        q,
    )
    _sakin(pg)
    ara = pg.evaluate(
        "() => ({aktif: SON.mc.aktif, bekliyor: mGkTazelenecek(MUK_AKTIF),"
        " kutu: document.getElementById('m_kabin_agirligi').value})"
    )
    r.kontrol(
        "[uygulama] istek reddedilirken yük değişince kabin ağırlığı yenilenmeyi bekliyor",
        #  Kutu boştur:  eski kütle yeni yükün yanında durmaz, tablo değeri gelecek
        ara["aktif"] is False and ara["bekliyor"] and ara["kutu"] == "",
        f"→ {ara}",
    )
    pg.evaluate("() => __T.yaz(document.getElementById('m_kabin_genisligi'), '1350')")
    d = _kural(r, pg, "uygulama", "geçersizden dönüş")
    if d:
        beyan, kabin, hesaplandi, bekliyor = d["kabin"][pg.evaluate("MUK_AKTIF")]
        r.kontrol(
            "[uygulama] girdi düzeltilince kabin ağırlığı yeni yükün tablo değeri",
            hesaplandi and not bekliyor and float(str(kabin).replace(",", ".")) == ofis.bos_kabin_kutlesi(q),
            f"→ yük {beyan} · kabin {kabin!r} · beklenen {ofis.bos_kabin_kutlesi(q)}",
        )


def _ardisik_iki_asansor(r, pg):
    """İki asansörün yükü art arda değişir, yanıtlar ancak ikisinden SONRA döner.

    Tek bir "tazelenecek asansör" tutulduğunda ikinci değişiklik birincinin
    işaretini siliyor ve 2. asansörün kabin ağırlığı eski değerde kalıyordu.
    Yanıtlar elle bekletilir — zamanlamaya bağlı değildir."""
    pg.evaluate("""async () => { const e = id => document.getElementById(id);
        mAsansorSekmesi(1); __T.yaz(e('m_kabin_agirligi'), '650'); await __T.sakin();
        mAsansorSekmesi(0); __T.yaz(e('m_kabin_agirligi'), '650'); await __T.sakin(); }""")
    sonuc = pg.evaluate("""async () => {
        const e = id => document.getElementById(id);
        const bek = ms => new Promise(z => setTimeout(z, ms));
        let birak; const kapi = new Promise(z => birak = z);
        __T.gecikme = () => 0;
        const eski = window.fetch;
        window.fetch = async (u, o) => { const r = await eski(u, o);
            if (String(u).includes('/api/uygulama/coklu')) await kapi; return r; };
        try {
            mAsansorSekmesi(1); __T.yaz(e('m_beyan_yuku'), '1000');
            await bek(400);                          // 2. asansörün isteği yolda, bekletiliyor
            mAsansorSekmesi(0); __T.yaz(e('m_beyan_yuku'), '1275');
            birak();                                 // yanıtlar ancak şimdi döner
            await bek(50);
        } finally { window.fetch = eski; }
        await __T.sakin();
        mukavemetIstek();
        return MUK_ASANSORLER.slice(0, 2).map(a => [a.beyan_yuku, a.kabin_agirligi]);
    }""")
    for sira, (q, beklenen) in enumerate(
        ((1275, ofis.bos_kabin_kutlesi(1275)), (1000, ofis.bos_kabin_kutlesi(1000)))
    ):
        yuk, kabin = sonuc[sira]
        r.kontrol(
            f"[uygulama] iki asansörde art arda yük değişimi · asansör {sira + 1} "
            "kabin ağırlığı yeni yükün tablo değeri",
            str(yuk) == str(q) and float(str(kabin).replace(",", ".")) == beklenen,
            f"→ yük {yuk} · kabin {kabin!r} · beklenen {beklenen}",
        )
    _kural(r, pg, "uygulama", "iki asansörde art arda yük değişimi")


def _hemen_kaydet(r, pg):
    """Yük değişir, tablo değeri gelmeden proje kaydedilir.

    Kutu yeni değeri beklerken eski kütleyi taşıyordu:  o anda kaydedilen
    dosyaya ve tarayıcı belleğine 1600 kg yükün yanına eski kabin ağırlığı
    yazılıyor, açılınca hesap o değerle yapılıyordu ( kabin tamponu
    116,29 kN yerine 94,71 kN — bağımsız incelemede bulundu )."""
    q = 1600
    beklenen = ofis.bos_kabin_kutlesi(q)
    pg.evaluate("""async () => { __T.yaz(document.getElementById('m_kabin_agirligi'), '777');
        await __T.sakin(); }""")
    kayit = pg.evaluate(
        """q => {
        __T.yaz(document.getElementById('m_beyan_yuku'), String(q));
        return {dosya: JSON.stringify(projeGovdesi('uygulama')),
                kova: localStorage.getItem(KOVA.uygulama)};   // HEMEN — yanıt beklenmez
    }""",
        q,
    )
    _sakin(pg)

    def _denetle(etiket):
        d = pg.evaluate("""() => ({kutu: document.getElementById('m_kabin_agirligi').value,
            yuk: SON.mc.asansorler[MUK_AKTIF].girdi.beyan_yuku,
            kabin: SON.mc.asansorler[MUK_AKTIF].girdi.kabin_agirligi})""")
        r.kontrol(
            f"[uygulama] {etiket} · yeni yükün kabin ağırlığıyla hesaplanıyor",
            d["yuk"] == q and d["kabin"] == beklenen and float(str(d["kutu"]).replace(",", ".")) == beklenen,
            f"→ {d} · beklenen {beklenen}",
        )
        _kural(r, pg, "uygulama", etiket)

    #  1) Dosyadan
    pg.evaluate(
        "d => { localStorage.clear(); projeUygula(JSON.parse(d), 'hemen.uygulama'); }", kayit["dosya"]
    )
    _sakin(pg)
    _denetle("hemen kaydedilen dosya açıldı")
    #  2) Tarayıcı belleğinden ( sayfa yenilenir )
    pg.evaluate("k => localStorage.setItem(KOVA.uygulama, k)", kayit["kova"])
    pg.goto(BASE, wait_until="networkidle")
    pg.wait_for_timeout(500)
    if pg.is_visible("#giris"):
        pg.click("#gk_uygulama")
    pg.wait_for_timeout(2500)
    pg.evaluate(_ALET)
    _sakin(pg)
    _denetle("hemen kaydedilen tarayıcı belleğiyle sayfa yenilendi")


def _kabin_beklentisi(r, d, son_olay, tablo, etiket, olaylar):
    for sira, (tur, deger) in son_olay.items():
        if sira >= len(d["kabin"]):
            continue
        beyan, kabin, hesaplandi, bekliyor = d["kabin"][sira]
        if not hesaplandi:
            #  Sunucu hesabı reddetti:  tablo değeri gelemez.  Yük değiştiyse
            #  yenileme işareti AÇIK kalmalı ki girdi düzelince tablo gelsin.
            if tur == "beyan":
                r.kontrol(
                    f"[uygulama] {etiket} · asansör {sira + 1} hesap yapılamadı, "
                    "kabin ağırlığı yenilenmeyi bekliyor",
                    bekliyor,
                    f"→ olaylar {olaylar}",
                )
            continue
        beklenen = tablo[int(float(str(beyan).replace(",", ".")))] if tur == "beyan" else deger
        bulunan = float(str(kabin).replace(",", ".")) if str(kabin).strip() else None
        r.kontrol(
            f"[uygulama] {etiket} · asansör {sira + 1} kabin ağırlığı son olayı izliyor ( {tur} )",
            bulunan == beklenen,
            f"→ yük {beyan} · kabin {kabin!r} · beklenen {beklenen} · olaylar {olaylar}",
        )


#  Adedi düğmesiz değiştirmek bir DOM olayı değildir:  avan hesabı 220 ms sonra
#  gider ( ortak.js planla ).  Olay işaretlenmezse __T.sakin hesap daha
#  gönderilmeden "duruldu" sanabilir, ekrandaki eski sonuç taze hesapla
#  kıyaslanırdı ( 13 Eki CI:  dizi 14 "… → trafikAdedi(3) → 113 ms" — önceki
#  hesabın gecikmesi kısa düşünce ).  Uygulamanın adet / sekme çağrıları hesabı
#  beklemeden gönderir, onlarda bu boşluk yok.
_ADET_OLAYLI = "n => { trafikAdedi(n); __T.olay = performance.now(); }"


def _avan_dizileri(r, pg, rnd):
    alanlar = pg.evaluate(_ALANLAR, "avan")
    pg.evaluate("__T.gecikme = () => Math.floor(Math.random() * 500)")
    for n in range(DIZI_ADEDI):
        for _ in range(rnd.randint(3, 8)):
            eylem = rnd.choice(("alan", "alan", "alan", "adet", "kapasite"))
            if eylem == "alan":
                pg.evaluate(
                    "([id, i]) => { const e = document.getElementById(id); __T.yaz(e, __T.yeni(e, i)); }",
                    [rnd.choice(alanlar), rnd.randint(0, 9)],
                )
            elif eylem == "adet":
                pg.evaluate(_ADET_OLAYLI, rnd.randint(1, 3))
            elif eylem == "kapasite":
                pg.evaluate(
                    "p => __T.yaz(document.getElementById('c_P1'), String(p))", rnd.choice((6, 8, 10, 13, 16))
                )
            pg.wait_for_timeout(rnd.randint(0, 400))
        _kural(r, pg, "avan", f"dizi {n + 1}")
    pg.evaluate("__T.gecikme = () => 0")


def calistir():
    print("\n\033[1mTEST 13 — CANLI HESAP TUTARLILIĞI (tarayıcı)\033[0m")
    r = Rapor("Canlı hesap tutarlılığı")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        r.atla("Playwright kurulu değil — canlı hesap testi atlandı")
        return r
    if not _sunucu_var():
        r.atla(f"Sunucu {BASE} adresinde çalışmıyor — canlı hesap testi atlandı")
        return r

    with sync_playwright() as pw:
        try:
            tarayici = pw.chromium.launch()
        except Exception as e:  # noqa: BLE001
            r.atla(f"Chromium başlatılamadı: {e}")
            return r
        pg = tarayici.new_page(viewport={"width": 1440, "height": 1000})
        konsol = []
        pg.on("console", lambda m: konsol.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: konsol.append("PAGEERROR " + str(e)))
        pg.on("dialog", lambda d: d.dismiss())
        pencere_dinle(pg)  # programın kendi penceresi de kapatılır

        #  UYGULAMA:  iki asansörlü, açısı girilmiş proje
        _ac(pg, "uygulama")
        pg.evaluate(
            "() => { __T.yaz(document.getElementById('m_sarilma_acisi'), '180');"
            " mAdetDegisti(2); mAsansorSekmesi(0); }"
        )
        _kural(r, pg, "uygulama", "başlangıç")
        _her_alan(r, pg, "uygulama")
        _uygulama_dizileri(r, pg, random.Random(TOHUM))

        #  AVAN:  örnek proje, iki asansörlü trafik grubu
        _ac(pg, "avan")
        pg.evaluate("() => { ornekYukle(); }")
        pg.wait_for_timeout(1500)
        pg.evaluate(_ADET_OLAYLI, 2)
        _kural(r, pg, "avan", "başlangıç")
        _her_alan(r, pg, "avan")
        _avan_dizileri(r, pg, random.Random(TOHUM + 1))

        r.kontrol("konsol hatası yok", not konsol, f"→ {konsol[:4]}")
        tarayici.close()
    return r


if __name__ == "__main__":
    _r = calistir()
    if os.environ.get("CANLI_HATA_DOSYASI"):
        with open(os.environ["CANLI_HATA_DOSYASI"], "w", encoding="utf-8") as _f:
            _f.write("\n".join(_r.hatalar))
    sys.exit(0 if _r.yazdir() else 1)

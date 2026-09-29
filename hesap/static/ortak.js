/* ═══════════════════════════════════════════════════════════════════
   ASANSÖR PROJE PROGRAMI  —  ORTAK ARAYÜZ

   İki proje türünün de kullandığı kısım:  genel durum, biçimleme,
   sekme şeridi ve MOD anahtarı, çizim yardımcıları, indirme, kalıcılık,
   proje dosyası, açılış ekranı.

   Yükleme sırası ÖNEMLİDİR:   ortak.js → avan.js → uygulama.js
   kur() en sonda, uygulama.js'in ardından çağrılır.
   ═══════════════════════════════════════════════════════════════════ */

/* ═══════════════════════════════════════════════════════════════════
   ASANSÖR AVAN HESAPLAMA PROGRAMI  —  arayüz
   ═══════════════════════════════════════════════════════════════════ */
let SEC = {};                 // sunucudan gelen seçenekler / tablolar
let SON = {t:null, c:null, a:null, m:null};
let TRAFIK_ADET = 1;          // 1 → tek hesap (adet hesaplanır) · 2-4 → grup kontrolü
let AVAN_EK = 0;              // avanda TRAFİK GRUBUNA girmeyen asansör adedi (yük/sedye)
let AVAN_OTO = {};            // kapasite/hızı trafikten OTOMATİK gelen asansörler
let AVAN_TRF = {};            // her asansöre en son YANSITILAN trafik değeri
let AVAN_TABAN = null;        // trafik grubunun SON BİLİNEN adedi — tek hesapta adedi
                              // trafik sonucu verir;  sonuç yokken ( proje yeni açıldı,
                              // hesap yolda, girdi geçici hatalı ) bu kullanılır
/*  İSTEK SIRA SAYACI.  Ekran her tuş vuruşunda hesap ister; ağ gecikmesiyle
    ESKİ bir isteğin yanıtı YENİSİNDEN SONRA gelebilir.  Sayaç olmadan geç gelen
    eski yanıt ekranı ve avana aktarılan kapasite/hızı geri alıyordu — kullanıcı
    16 kişilik yazmışken sonuç 8 kişilik kalıyordu.  Yalnız EN SON istek çizer. */
const ISTEK = {trafik: 0, avan: 0, mukavemet: 0};
/*  PROGRAM İKİ MODLUDUR.  Açılış ekranında seçilen mod, sekme şeridinin hangi
    adımları göstereceğini belirler:
        'avan'      →  trafik · avan · kapak  ( + başvuru sekmeleri )
        'uygulama'  →  mukavemet
    İkisi AYRI hesaplardır; ortak girdi yoktur, karışmasınlar diye şerit de
    ayrılır.  MUK: mukavemet girdi sözleşmesi ( /api/mukavemet/alanlar ). */
let MOD = 'avan';
let MUK = null;
const $  = id => document.getElementById(id);
const el = (t,s,h)=>{const e=document.createElement(t); if(s)e.className=s; if(h!=null)e.innerHTML=h; return e;};

/* ---------------------------------------------------------- biçimleme */
/*  YARIMI SIFIRDAN UZAĞA YUVARLAR  —  sunucudaki steps.yuvarla ile AYNI kural.
    toLocaleString sayının İKİLİ değerini yuvarlar:  9,325 ikilide 9,32499…
    diye saklandığı için ekran "9,32", pafta "9,33" basıyordu.  Sayı önce
    12 anlamlı haneye indirilip gürültüden arındırılır, yuvarlama ONDALIK
    haneler üzerinde tam sayıyla yapılır. */
function yuvarla(x, d=0){
  if(!isFinite(x) || x===0) return x;
  const [govde, us] = Math.abs(x).toExponential(11).split('e');
  const hane = BigInt(govde.replace('.', ''));           // 12 anlamlı hane
  const at = -d - (Number(us) - 11);                     // atılacak hane sayısı
  if(at <= 0) return x;                                  // istenen hane 12 haneden ince
  const bolen = 10n ** BigInt(at);
  const tam = hane / bolen + (2n * (hane % bolen) >= bolen ? 1n : 0n);
  return Math.sign(x) * Number(tam) / 10 ** d;
}
function tr(x, d=2){
  if(x===null||x===undefined||x==='') return '—';
  if(typeof x==='string') return x;
  if(!isFinite(x)) return '—';
  return yuvarla(Number(x), d).toLocaleString('tr-TR',{minimumFractionDigits:d, maximumFractionDigits:d});
}
function trn(x, d=2){
  if(x===null||x===undefined||x==='') return '—';
  if(typeof x==='string') return x;
  if(!isFinite(x)) return '—';
  return Math.abs(x-Math.round(x))<1e-9 ? tr(Math.round(x),0) : tr(x,d);
}
/*  TIRNAKLAR DA KAÇIRILIR.  Bu işlev yalnız metin içeriğinde değil,
    value="${kacis(...)}" gibi ÖZNİTELİK içinde de kullanılıyor;  çift tırnak
    kaçırılmayınca özniteliği erken kapatıyordu:  ek nüfus açıklamasına
    `Daire "A" bloğu` yazıp yeniden açınca alanda yalnız `Daire ` kalıyordu.  */
const kacis = s => String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;')
  .replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');

function durum(msg, hata){
  const d=$('durum'); d.textContent=msg; d.className='durum gorunur'+(hata?' hata':'');
  clearTimeout(d._t); d._t=setTimeout(()=>d.className='durum',2600);
}

/* ---------------------------------------------------------- sekmeler */
/* Trafik hesabı TEK sekmedir; asansör adedine göre iki gövdeden biri
   gösterilir:  1 asansör → #s-trafik (adet hesaplanır),
                2-4       → #s-coklu  (grup kontrolü).
   İkisi de "trafik" sekmesine aittir. */
function sekmeGoster(ad){
  document.querySelectorAll('.sekme').forEach(x=>
    x.classList.toggle('etkin', x.dataset.sekme===ad));
  document.querySelectorAll('.sayfa').forEach(s=>s.hidden=true);
  //  Trafik ARTIK TEK GÖVDEDİR ( #s-coklu ) — 1..4 asansör aynı formda
  //  tanımlanır, yöntemi program veriden çıkarır.
  $('s-' + (ad==='trafik' ? 'coklu' : ad)).hidden=false;
  //  Asansör sekmeleri "mukavemet" gövdesini paylaşır;  hangisinin etkin
  //  göründüğü açık gövdeye bağlıdır, o yüzden her geçişte tazelenir.
  if(typeof mAsansorSekmeleriTazele === 'function') mAsansorSekmeleriTazele();
  window.scrollTo({top:0,behavior:'instant'});
}
/*  Şeritte yalnız seçili modun adımları durur.  Gizlenen sekmenin sayfası da
    kapatılır — yoksa moddan moda geçişte iki formu birden gösterebiliyordu. */
function modAyarla(m){
  MOD = (m === 'uygulama') ? 'uygulama' : 'avan';
  document.body.dataset.mod = MOD;
  //  Bir sekme birden çok moda ait olabilir ( "avan uygulama" ) — Sabitler
  //  ve Tablolar iki projede de vardır, ama İÇERİKLERİ ayrıdır.
  document.querySelectorAll('.sekme[data-mod]').forEach(b=>{
    b.hidden = !b.dataset.mod.split(/\s+/).includes(MOD);
  });
  //  AYNI SEKME, AYRI GÖVDE:  uygulamanın kendi ofis sabitleri ve kendi
  //  tabloları vardır;  kimse öbürünün ayarını ya da tablosunu görmez.
  const uyg = MOD === 'uygulama';
  [['sabitler_uygulama', uyg], ['sabitler_avan', !uyg],
   ['tablolar_uygulama', uyg], ['tablolar_avan', !uyg]].forEach(([id, gorunsun])=>{
    const e = $(id); if(e) e.hidden = !gorunsun;
  });
  //  Başlık ve kaynak şeridi de moda uyar — hangi projede olduğu üst
  //  şeritten okunabilmeli, ekran görüntüsü alındığında da belli olsun.
  const ad = $('ust_ad'), kaynak = $('ust_kaynak');
  if(ad) ad.textContent = MOD === 'uygulama'
    ? 'ASANSÖR UYGULAMA PROJESİ — MUKAVEMET'
    : 'ASANSÖR AVAN HESAPLAMA PROGRAMI';
  if(kaynak) kaynak.innerHTML = MOD === 'uygulama'
    ? 'TS EN 81-20 &nbsp;·&nbsp; TS EN 81-50 &nbsp;·&nbsp; TS 12385-5 &nbsp;·&nbsp; ISO 7465<br>'
      + 'MMO 208/4 &nbsp;·&nbsp; MMO 208/7'
    : 'MMO/697, 2. Baskı, Ocak 2020 &nbsp;·&nbsp; TS EN 81-20 &nbsp;·&nbsp; ISO 8100-32:2020<br>'
      + 'IEEE Std 80 &nbsp;·&nbsp; IEC 60364-5-52 &nbsp;·&nbsp; BYKHY md.4';
}
document.querySelectorAll('.sekme').forEach(b=>b.onclick=()=>sekmeGoster(b.dataset.sekme));
function katla(bas, hedef){
  bas.classList.toggle('kapali');
  $(hedef).style.display = bas.classList.contains('kapali') ? 'none' : '';
}

/* ---------------------------------------------------------- kurulum */
async function kur(){
  SEC = await (await fetch('/api/secenekler')).json();
  const opts=(a,f)=>a.map(v=>`<option value="${f?f(v):v}">${f?f(v):v}</option>`).join('');
  $('c_bina_tipi').innerHTML = opts(SEC.bina_tipleri);
  $('c_manuel_V').innerHTML = '<option value="">Tablo-2 minimumu</option>' +
      SEC.hizlar.map(v=>`<option value="${v}">${tr(v)} m/s</option>`).join('');

  cokluAsansorleriKur();
  avanAsansorleriKur();
  sabitFormuKur();
  sabitATablosu();
  tablolariKur();

  /*  Hangi hesabın yeniden koşacağını MOD belirler.  Sabitler / Ofis
      Standardı sekmesi İKİ MODA DA aittir:  uygulama projesindeyken oradaki
      bir değişiklik uygulama hesabını tetiklemeli — yoksa kullanıcı armatür
      ışık akısını değiştirir, ekranda hiçbir şey olmazdı. */
  const _girdiOlayi = e => {
    if(e.target.closest('#s-proje')){ yaz(); return; }
    if(MOD === 'uygulama' || e.target.closest('#s-mukavemet')){
      mukavemetPlanla(e.target); return;
    }
    planla(e.target);
  };
  document.body.addEventListener('input', _girdiOlayi);
  document.body.addEventListener('change', _girdiOlayi);

  oku();
  cokluKolonlariGoster();
  avanKartlariGoster();
  adetDugmeleriKur();
  mkYokUygula();
  ofisTazele();
  etiketleriGuncelle();
  hesaplaHepsi();
}

let zaman=null;
function planla(hedef){
  if(hedef && hedef.closest('#s-proje')){ yaz(); return; }
  /*  Kullanıcı kapasite / hız alanına dokunduysa o asansör artık "otomatik"
      değildir: değeri korunur ve kartı kendiliğinden kapanmaz. */
  if(hedef && hedef.id){
    const m = /^a_(kapasite|Q_elle|V)([1-4])$/.exec(hedef.id);
    if(m) delete AVAN_OTO[m[2]];
  }
  etiketleriGuncelle();
  clearTimeout(zaman);
  zaman=setTimeout(()=>{ yaz(); hesaplaHepsi(); }, 220);
}

function etiketleriGuncelle(){
  ofisTazele();
  temelCevresi();
  [['c','c_bina_tipi']].forEach(([p,id])=>{
    /*  Adlar motordan gelir ( trafik.hizli_etiketleri ):  hata metni de
        kutuyu bu adla söyler, ikisi ayrışamaz. */
    const bt=$(id).value||'';
    const e=(SEC.hizli_etiketleri||{})[bt]||(SEC.hizli_etiketleri||{})['']
            ||{hizli1:['⑤','—'],hizli2:['⑥','']};
    const etiket=([ad,ipucu])=>ipucu?ad+' '+ipucu:ad;
    $(p+'_l_hizli1').textContent=etiket(e.hizli1); $(p+'_l_hizli2').textContent=etiket(e.hizli2);
  });
}

/* ---------------------------------------------------------- çizim: ortak */
function adimTablosu(adimlar){
  let h='<div class="kaydir"><table class="hesap">';
  for(const a of adimlar){
    if(a.tip==='metin'){ h+=`<tr class="baslik-satir"><td colspan="6">${kacis(a.deger)}</td></tr>`; continue; }
    if(a.tip==='hesap'){
      h+=`<tr class="formul"><td colspan="6">${kacis(a.formul)}</td></tr>`
       + `<tr class="islem"><td></td><td class="islem" colspan="2">${kacis(a.islem)}</td>`
       + `<td class="deger">${kacis(a.metin)}</td><td class="birim">${kacis(a.birim)}</td>`
       + `<td class="kaynak">${kacis(a.kaynak)}</td></tr>`;
      continue;
    }
    h+=`<tr><td class="sembol">${kacis(a.sembol)}</td><td class="aciklama">${kacis(a.aciklama)}</td>`
     + `<td class="esit">=</td><td class="deger">${kacis(a.metin)}</td>`
     + `<td class="birim">${kacis(a.birim)}</td><td class="kaynak">${kacis(a.kaynak)}</td></tr>`;
  }
  return h+'</table></div>';
}
function cetvelTablosu(c){
  let t=0, h='<div class="kaydir"><table class="veri"><tr><th>Lin</th><th>Sorti</th><th style="text-align:right">Gücü</th><th>Birim</th><th>Sigorta A</th></tr>';
  c.forEach(x=>{t+=x.guc; h+=`<tr><td>${x.lin}</td><td>${kacis(x.sorti)}</td><td class="sag">${trn(x.guc,0)}</td><td>${x.birim}</td><td>${x.sigorta}</td></tr>`;});
  return h+`<tr class="toplam"><td></td><td>ASANSÖRÜN KURULU GÜCÜ</td><td class="sag">${trn(t,0)}</td><td>W</td><td></td></tr></table></div>`;
}
/* Yöntem açıklamalarını başlığın yanındaki ( ! ) dairesine toplar; üzerine
   gelince açılır, dokunmatik ekranda tıklayınca kalır.  Uyarılar buraya
   girmez — onlar açıkta durur.  Paftada bu metinler yine tam basılır. */
function bilgiSimgesi(metinler, sinif, harf){
  const liste=(Array.isArray(metinler)?metinler:[metinler])
    .filter(x=>x!==null&&x!==undefined&&String(x).trim()!=='');
  if(!liste.length) return '';
  /*  İKİ AYRI SİMGE, İKİ AYRI İŞ:
        ( ! )  sonuç bölümlerinde YÖNTEM açıklaması — "bu sayı nasıl çıktı".
        ( i )  girdi kutularında TANIM — "bu kutuya ne yazılır".
      Aynı harf kullanılsaydı okuyan, sonucun yanındaki uyarı tonundaki
      açıklamayla kutunun yanındaki tarifi ayırt edemezdi.                  */
  return `<span class="bilgi${sinif?' '+sinif:''}" tabindex="0" role="button"`
    + ` aria-label="Açıklamayı göster" onclick="bilgiAc(this,event)">`
    + `<span class="bilgi-im">${harf||'!'}</span><span class="bilgi-balon">`
    + liste.map(x=>`<p>${kacis(String(x))}</p>`).join('')
    + `</span></span>`;
}
/* Balon fixed konumlandırılır; yoksa kartların overflow'u kırpıyor.
   Ekranın sağına / altına taşacaksa kendini içeri alır. */
function bilgiKonumla(e){
  const balon=e.querySelector('.bilgi-balon'); if(!balon) return;
  balon.style.maxWidth=Math.min(430,window.innerWidth-24)+'px';
  balon.style.left='0px'; balon.style.top='0px';
  const r=e.getBoundingClientRect(), b=balon.getBoundingClientRect();
  let x=r.left-8, y=r.bottom+8;
  if(x+b.width > window.innerWidth-12) x=window.innerWidth-12-b.width;
  if(x<12) x=12;
  if(y+b.height > window.innerHeight-12) y=Math.max(12, r.top-8-b.height);
  balon.style.left=Math.round(x)+'px'; balon.style.top=Math.round(y)+'px';
}
function bilgiAc(e, olay){
  if(olay) olay.stopPropagation();
  const acik=e.classList.contains('acik');
  document.querySelectorAll('.bilgi.acik').forEach(x=>x.classList.remove('acik'));
  if(!acik){ e.classList.add('acik'); bilgiKonumla(e); }
}
function _bilgiHedef(ev){
  const t=ev.target;
  return (t && t.closest) ? t.closest('.bilgi') : null;
}
document.addEventListener('mouseover',ev=>{const e=_bilgiHedef(ev); if(e) bilgiKonumla(e);}, true);
document.addEventListener('focusin',ev=>{const e=_bilgiHedef(ev); if(e) bilgiKonumla(e);});
document.addEventListener('click',()=>document.querySelectorAll('.bilgi.acik')
  .forEach(x=>x.classList.remove('acik')));
document.addEventListener('keydown',ev=>{
  if(ev.key!=='Escape') return;
  document.querySelectorAll('.bilgi.acik').forEach(x=>x.classList.remove('acik'));
  /* Esc'ten sonra tarayıcı odağı :focus-visible'a yükseltiyor ve balon açık
     kalıyordu; kapatırken odağı da bırakıyoruz. */
  const o=document.activeElement;
  if(o && o.classList && o.classList.contains('bilgi')) o.blur();
});
addEventListener('scroll',()=>{const a=document.querySelector('.bilgi.acik');
  if(a) bilgiKonumla(a);}, true);
addEventListener('resize',()=>document.querySelectorAll('.bilgi.acik')
  .forEach(x=>x.classList.remove('acik')));

/*  ek ( isteğe bağlı ):  {id, sag}  —  şeride kimlik ve sağ uca bir düğme
    ( uygulama projesinin "Özete dön"ü ).  Verilmezse şerit eskisinin
    birebir aynısıdır;  avan ve trafik bölümleri böyle çizilir. */
function bolumCiz(b, ek){
  //  "ekran_notlari":  paftaya basılmayan ama ekranda kalması gereken
  //  açıklamalar ( bkz. engine/avan.py — topraklama kontrolü ).
  const bilgi = [...(b.aciklamalar||[]), ...(b.ekran_notlari||[])];
  const kaynak = `<span class="kaynak">${kacis(b.kaynak||'')}</span>`;
  let h=`<div class="serit"${ek && ek.id ? ` id="${kacis(ek.id)}"` : ''}>`
      + `<span>${kacis(b.baslik)}${bilgiSimgesi(bilgi)}</span>`
      + (ek && ek.sag ? `<span class="serit-sag">${kaynak}${ek.sag}</span>` : kaynak)
      + '</div>';
  if(b.adimlar&&b.adimlar.length) h+=adimTablosu(b.adimlar);
  if(b.cetvel&&b.cetvel.length) h+=cetvelTablosu(b.cetvel);
  if(b.sonuc) h+=`<div class="sonuc-kutu ${b.sonuc.uygun?'ok':'hata'}"><span class="et">${kacis(b.sonuc.baslik)}</span><span>${kacis(b.sonuc.metin)}</span></div>`
    + (b.sonuc.alt||[]).map(x=>`<div class="notlar"><div>${kacis(x)}</div></div>`).join('');
  if(b.notlar&&b.notlar.length) h+='<div class="notlar">'+b.notlar.map(n=>`<div>${kacis(n)}</div>`).join('')+'</div>';
  return h;
}
const kutu = (et,dg,bi,sinif='') => `<div class="k ${sinif}"><div class="et">${et}</div><div class="dg2">${dg}</div><div class="bi">${bi||''}</div></div>`;

/* ═══════════════ OFİS STANDARDI  —  HESAP BAZINDA GRUPLU ═══════════════
   Sabitler iki ayrı yerde tutulur ve öyle kalmalıdır:

     sb_*  →  motorun "sabitler" sözlüğüne gider  ( engine/avan/hesap.py SABIT_B_VARSAYILAN )
     of_*  →  asansör alanı boşsa kullanılan ofis varsayılanıdır
              ( bkz. engine/avan/hesap.py OFIS_VARSAYILAN )

   Ama KULLANICI için bu ayrımın hiçbir anlamı yok; onun sorusu "bu sabit
   hangi hesaba giriyor".  Bu yüzden ekranda tek panel var ve alanlar
   HESABA göre gruplanıyor.  Kimlik ön ekleri ( sb_ / of_ ) değişmediği için
   proje dosyası bundan etkilenmez. */
const SABIT_ETIKET = {
  //  sb_*
  i_palanga:['i — Palanga ( askı ) katsayısı','Doğrudan askı 1 / Palangalı 2'],
  q_denge:['q — Denge faktörü','karşı ağırlığın dengelediği yük oranı'],
  n_ray:['n — Kabin kılavuz ray sayısı','kabin daima iki raya oturur'],
  gf:['gf — Gezici kablo ( flexbil ) birim kütlesi (kg/m)',''],
  Fmt:['Fmt — Montör ağırlığı (kg)','kuyu üstü yükünde'],
  kabin_armatur_W:['Kabin armatürü gücü (W)','LED spot'],
  kabin_armatur_lm:['Kabin armatürü ışık akısı (lm)','5 W LED ≈ 300 lm'],
  kabin_ustu_armatur:['Kabin üstü armatür adedi','kurulu güce eklenir'],
  kuyu_armatur_W:['Kuyu armatürü gücü (W)','flüoresan'],
  kuyu_armatur_lm:['Kuyu armatürü ışık akısı (lm)','ofis teamülü 2600 lm'],
  kuyu_Dmax:['Kuyu armatürü azami aralığı (m)','0 = kontrol kapalı'],
  priz_adedi:['Priz adedi',''], priz_gucu:['Priz başına güç (W)',''],
  cosfi:['cosφ — Güç katsayısı','hat akımı hesabında'],
  UL:['UL — İzin verilen temas gerilimi (V)','TT sistem'],
  IDn:['IΔn — Kaçak akım rölesi (A)','300 mA = 0,30 A'],
  lc:['lç — Çubuk topraklayıcı boyu (m)',''],
  ayd_sutun:['Aydınlatma verimi sütunu (1-10)','Tablo-2 yansıma çifti'],
  //  of_*
  U:['U — Şebeke gerilimi (V)','fazlar arası'],
  kappa:['κ — İletken iletkenliği','bakır 56 m/Ω·mm²'],
  eps_max:['εmax — İzin verilen gerilim düşümü (%)','yönetmelik sınırı'],
  gr:['gr — Kılavuz ray birim kütlesi (kg/m)','ofis ray profili'],
  Fmk:['Fmk — Makine ağırlığı (kg)',''],
  Fsh:['Fsh — Makine sehpası ağırlığı (kg)',''],
  zincir_birim_kutle:['mz — Denge zinciri birim kütlesi (kg/m)','yalnız zincir Var seçilen asansörde;  zincir = halat ağırlığı ( λ = %100 ) · ofisin halat düzeni 7 × Ø6,5 mm · 2:1'],
  S1:['S1 — Kolon hattı kesiti (mm²)',''],
  S2:['S2 — Makine besleme kesiti (mm²)',''],
  L2:['L2 — Makine besleme uzunluğu (m)','pano – makine arası'],
  kablo_tipi:['Kablo tipi','paftaya metin olarak yazılır'],
  L1_pay:['L1 yatay güzergâh payı (m)','ana pano → kuyu → asansör panosu yatay kablo yolu + bağlantı payı;  L1 = kuyu yüksekliği Hk + bu pay'],
  beta:['β — Toprak özgül direnci (Ω·m)','zemin etüdü varsa o değeri yazın'],
  cubuk_sayisi:['Is — Çubuk topraklayıcı adedi','paralel bağlı çubuk sayısı'],
  goz_araligi:['Karelaj gözü (m)','şerit boyu temel ölçülerinden türetilirken kullanılır'],
  sigorta_katsayisi:['Motor sigortası kalkış katsayısı','sigorta = bu katsayı × motor akımı, standart kademeye yuvarlanır'],
  motor_elektrik_verimi:['Motorun elektrik verimi ηm','şebekeden çekilen güç = mil gücü / ηm;  kablo ve sigorta bu akıma göre seçilir'],
};

/*  Her sabitin HANGİ HESABA girdiği.  [ başlık, açıklama, alanlar ]
    alan = "sb:anahtar" ya da "of:anahtar" */
const SABIT_GRUP = [
  //  Kat yüksekliği ve kapı tipi burada DEĞİL — her projede değişirler,
  //  trafik hesabı sekmesinde girilirler.
  ['① MOTOR GÜCÜ VE KUVVETLER', 'MMO/697 s.18-21 — motor gücü, karşı ağırlık, ray ve kuyu dibi kuvvetleri',
   ['sb:q_denge', 'of:gr', 'sb:n_ray', 'sb:gf', 'of:zincir_birim_kutle', 'of:Fmk', 'of:Fsh', 'sb:Fmt']],
  ['② AYDINLATMA', 'kabin · kuyu · makine dairesi aydınlatma hesapları',
   ['sb:kabin_armatur_W', 'sb:kabin_armatur_lm', 'sb:kabin_ustu_armatur',
    'sb:kuyu_armatur_W', 'sb:kuyu_armatur_lm', 'sb:kuyu_Dmax', 'sb:ayd_sutun']],
  ['③ KURULU GÜÇ VE GERİLİM DÜŞÜMÜ', 'IEC 60364-5-52 — kurulu güç, hat akımı, kablo ve gerilim düşümü',
   ['of:U', 'of:kappa', 'of:eps_max', 'sb:cosfi', 'sb:motor_elektrik_verimi',
    'sb:priz_adedi', 'sb:priz_gucu',
    'of:S1', 'of:S2', 'of:L2', 'of:L1_pay', 'of:kablo_tipi', 'of:sigorta_katsayisi']],
  ['④ TEMEL TOPRAKLAMA', 'IEEE Std 80 · BYKHY — temel ve çubuk topraklayıcı',
   ['of:beta', 'of:cubuk_sayisi', 'of:goz_araligi', 'sb:lc', 'sb:UL', 'sb:IDn']],
];


/*  ŞERİT BOYU  —  artık GİRDİ değil, TÜRETİLEN değerdir.
    Avan aşamasında elektrik projesinin topraklama planı çizilmemiş olur;
    ofiste de temel için yalnız UZUNLUK ve GENİŞLİK giriliyor.  Uygulamadaki
    kural: band temelin çevresini KAPALI RİNG olarak dolaşır, gözler
    20 × 20 m'yi geçmeyecek şekilde enine bağ atılır.  Buradan:

        L  =  2·( a + b )  +  enine bağlar

    Hesabı MOTOR yapar ( engine/avan.py · serit_boyu_tahmin ); burada yalnız
    sonucu yer tutucuda gösteririz — iki yerde iki ayrı formül bulunmasın.
    Alan boş bırakılırsa türetilen değer kullanılır; topraklama planı
    çizildiğinde plandaki gerçek boy yazılır ve o değer türetileni ezer. */


/* Şerit boyu — motorun temel ölçülerinden kurduğu değer ve açılımı.
   Kutu kalktı ( boy her zaman türetilir );  "ne kullanıldı" sorusu yine
   ekrandan cevaplanır. */
function seritGoster(r){
  const not = $('a_serit_tahmin'); if(!not) return;
  const oz = (r && r.ozet) || {};
  const L = oz.serit_L, ring = oz.serit_L_ring, na = oz.serit_L_na, nb = oz.serit_L_nb;
  if(!(typeof L === 'number' && isFinite(L))){
    not.textContent = 'Temel uzunluğu ve genişliği girilince hesaplanır.';
    return;
  }
  const a = sayiOku(v('a_temel_a')), b = sayiOku(v('a_temel_b'));
  const bag = [];
  if(na) bag.push(`${na} × ${tr(b)}`);
  if(nb) bag.push(`${nb} × ${tr(a)}`);
  not.textContent = `Kullanılan: ring ${tr(ring)} m`
    + (bag.length ? `  +  enine bağ ${bag.join(' + ')}` : '  ·  enine bağ gerekmiyor')
    + `  =  ${tr(L)} m`;
}

/* Türkçe / İngilizce ondalık ayracını kabul eden basit okuyucu ( yalnız
   ekranda gösterim için; hesabın kendisi sunucuda ayrıştırılır ). */
function sayiOku(x){
  const s=String(x||'').trim().replace(/\s/g,'');
  if(!s) return NaN;
  const sv=s.lastIndexOf(','), sn=s.lastIndexOf('.');
  let t=s;
  if(sv>=0 && sn>=0) t = sv>sn ? s.replace(/\./g,'').replace(',','.') : s.replace(/,/g,'');
  else if(sv>=0) t = s.replace(',','.');
  const f=parseFloat(t);
  return isFinite(f) ? f : NaN;
}


/* Adet değişince ek nüfus kalemleri de taşınır — karma yapıda bunlar
   nüfusun tamamını belirlediği için kaybolmaları hesabı bozardı. */


/* ---------------------------------------------------------- indir */
/*  İNDİRİLEN ÇIKTININ GÖVDESİ  —  ekranın hesap isteğinin AYNISI.
    Uygulama çıktısı yalnız açık asansörün formunu gönderiyordu:  iki
    asansörlü projede ekran iki asansörü hesaplarken PDF ve paket yalnız
    birini içeriyordu.  Çıktı ekranla aynı girdiden üretilmelidir. */
function indirGovdesi(uc){
  //  KAPAK HER İSTEKTE GİDER:  sunucu proje adını yalnız dosyanın ADI için
  //  kullanır — paftanın içeriği değişmez.
  return uc==='kapak-pdf'
    ? {kapak:kapakCiktisi()}
    : uc.startsWith('trafik')
    ? {kapak:kapakGirdi(), girdiler:trafikGirdi()}
    : uc.startsWith('uygulama')
    ? {kapak:mukavemetKimlik(), ...mukavemetIstek()}
    : {kapak:kapakGirdi(), girdiler:avanGirdi()};
}
async function indir(uc){
  durum('Dosya hazırlanıyor…');
  const govde = indirGovdesi(uc);
  //  PAKETLEME ( ZIP ):  teslim edilecek çıktıların yanına PROJE DOSYASI da
  //  konur — arşivden dönebilmek için tek gereken odur.  Uygulama paketine
  //  ayrıca kapak sayfası girer ( avanınki zaten "kapak" alanından gider ).
  if(uc.endsWith('-dwg')){
    govde.proje_dosyasi = projeGovdesi(MOD);
    if(uc.startsWith('uygulama')) govde.kapak_sayfasi = kapakGirdi();
  }
  try{
    const r = await fetch('/api/indir/'+uc, {method:'POST',
      headers:{'Content-Type':'application/json'}, body:JSON.stringify(govde)});
    // Sunucu dosya yerine JSON döndürdüyse bu bir hata iletisidir — bozuk dosya indirme
    const tur = r.headers.get('Content-Type')||'';
    if(tur.includes('application/json')){
      const h = await r.json();
      durum(h.hata || 'Dosya üretilemedi', true);
      alert(h.hata || 'Dosya üretilemedi');
      return;
    }
    if(!r.ok) throw new Error('sunucu hatası '+r.status);
    const cd = r.headers.get('Content-Disposition')||'';
    let ad = 'cikti'; const m = cd.match(/filename\*=UTF-8''(.+)$/);
    if(m) ad = decodeURIComponent(m[1]);
    const b = await r.blob(), u = URL.createObjectURL(b);
    const a = document.createElement('a'); a.href=u; a.download=ad; document.body.appendChild(a); a.click();
    a.remove(); setTimeout(()=>URL.revokeObjectURL(u),3000);
    durum('İndirildi: '+ad);
  }catch(e){ durum('İndirme başarısız: '+e.message, true); }
}

/* ---------------------------------------------------------- kalıcılık */
/*  AVAN VE UYGULAMA AYRI KOVALARDA DURUR.
    Tek kova varken iki proje yan yana yaşıyordu:  avan üzerinde çalışıp
    uygulamaya geçince avan verisi orada duruyor, "Tümünü temizle" ikisini
    birden siliyor, aynı anda bir avan ve bir uygulama projesi tutulamıyordu.
    Ayrı kova, ayrı ön ek:  hiçbiri diğerini görmez.                        */
const KOVA = { avan:'avan_program_v1', uygulama:'uygulama_program_v1' };
//  UYARI:  ön ekler ÇAKIŞMAMALI.  'mk_' ( uygulamanın proje kimliği ) ile
//  'm_' ( mukavemet alanları ) ayrı ayrı yazılır;  'k_' ( avan kapağı ) ise
//  'mk_' ile karışmasın diye uygulama listesi ÖNCE denenir ( bkz. alanModu ).
const ONEK = { avan:['c_','a_','k_','of_','sb_'], uygulama:['m_','mk_','uof_'] };

/*  Bir alan hangi projeye ait?  Kimlik ön ekinden bilinir;  ortak olan
    ( Sabitler sekmesindeki eski of_/sb_ ) avana aittir, uygulamanın kendi
    sabitleri uof_ ön ekiyle durur.                                        */
function alanModu(id){
  for(const m of ['uygulama','avan'])
    if(ONEK[m].some(p => id.startsWith(p))) return m;
  return null;
}
function tumGirdiler(mod){
  const m = mod || MOD, o = { __mod:m, __surum:PROJE_SURUM };
  document.querySelectorAll('input,select').forEach(e=>{
    //  "_goster" alanları TÜRETİLMİŞTİR ( Q, Gk ) — girdi değildir, kaydedilmez;
    //  her hesapta yeniden doldurulurlar.
    if(!e.id || e.id.indexOf('_goster') >= 0) return;
    if(alanModu(e.id) !== m) return;
    o[e.id] = e.type==='checkbox' ? e.checked : e.value;
  });
  if(m === 'uygulama'){
    //  ÇOKLU ASANSÖR.  Form yalnız AKTİF asansörü taşır;  ötekiler dizide
    //  durur.  Kaydetmeden önce form diziye işlenir, yoksa son düzenlemeler
    //  kaybolurdu.
    if(typeof mAsansorKaydet === 'function') mAsansorKaydet();
    if(typeof MUK_ASANSORLER !== 'undefined'){
      o.__muk_asansorler = MUK_ASANSORLER;
      o.__muk_aktif = MUK_AKTIF;
      o.__muk_adet = MUK_ADET;
    }
  }else{
    o.__eknufus_c = ekNufusTopla('c');
    o.__trafik_adet = TRAFIK_ADET;
    o.__avan_ek = AVAN_EK;
    o.__avan_oto = AVAN_OTO;
    o.__avan_trf = AVAN_TRF;
  }
  return o;
}
function yaz(){
  try{ localStorage.setItem(KOVA[MOD], JSON.stringify(tumGirdiler(MOD))); }catch(e){}
}
function oku(){
  let o; try{ o=JSON.parse(localStorage.getItem(KOVA[MOD])||'null'); }catch(e){ o=null; }
  if(o) taninmayanBildir(uygula(o), 'Tarayıcıda kayıtlı avan projesinde');
}
/*  Bir değerin seçim kutusundaki karşılığı  ( seçeneğin kendi değeri ) ;
    listede yoksa undefined.  Açılır listelerde ondalık ayracı farkı olabilir:
    kayıtlı dosyada "1,6" durabilir ama seçeneğin değeri "1.6"dır — bu durumda
    sayısal karşılaştırma ile eşleştirilir. */
function secenekKarsiligi(e, val){
  const s = (val===null||val===undefined) ? '' : String(val);
  const secenekler = [...e.options].map(o=>o.value);
  if(secenekler.includes(s)) return s;
  const sayi = parseFloat(s.replace(',','.'));
  if(isFinite(sayi)){
    const esles = secenekler.find(o=>{
      const x = parseFloat(o); return isFinite(x) && Math.abs(x-sayi) < 1e-9; });
    if(esles !== undefined) return esles;
  }
  return undefined;
}
/* Bir alana değer yazar.  Seçim kutusu değeri TANIMADIYSA false döner
   ( boş değer tanınmayan sayılmaz );  çağıran bunu kullanıcıya söyler —
   aksi hâlde proje sessizce başka bir değerle hesaplanırdı. */
function alanaYaz(e, val){
  if(e.type==='checkbox'){ e.checked = !!val; return true; }
  const s = (val===null||val===undefined) ? '' : String(val);
  if(e.tagName!=='SELECT'){ e.value = s; return true; }
  const karsilik = secenekKarsiligi(e, s);
  if(karsilik !== undefined){ e.value = karsilik; return true; }
  const secenekler = [...e.options].map(o=>o.value);
  //  EŞLEŞME YOK:  SEÇİM KUTUSU BOŞA DÜŞMEZ.
  //  Boş bir <select> value olarak "" gönderir ve motor "boş bırakılamaz"
  //  der — oysa kullanıcı hiçbir şey yapmamıştır.  Bu yola şunlar düşer:
  //    · eski bir proje dosyasındaki artık geçersiz bir seçenek,
  //    · tarayıcıda saklı ESKİ BİÇİM bir değer  ( ör. onay kutusundan
  //      seçime çevrilmiş bir alanın true/false'u ),
  //    · tablo değişince kalkan bir profil/ölçü.
  //  Bu durumda listenin KENDİ varsayılanı korunur:  form açılışta doğru
  //  seçenekle çizilmiştir, ona dokunulmaz.
  //  "KENDİ VARSAYILANI" GERÇEKTEN VARSAYILANDIR:  kutuda o an duran değer
  //  değil.  Başka bir proje ya da başka bir asansör açıkken kutu ONUN
  //  değerini taşır;  tanınmayan değer sessizce o değere dönüşüyordu.
  //  Varsayılan, formun çizildiği seçenektir ( selected ) ya da ilk seçenek.
  //  Boş değerde eski davranış korunur ( kutuya dokunulmaz ).
  //  AMA SESSİZ KALINMAZ:  değer değişmiştir — false döner, yükleyen söyler.
  if(secenekler.includes('')){ e.value = ''; }
  else if(s.trim() !== ''){ e.value = secimVarsayilani(e); }
  return s.trim() === '';
}

/*  Seçim kutusunun KENDİ varsayılanı:  boş seçenek varsa o ( "ofis
    standardı" ), yoksa formun çizildiği seçenek ( selected ) ya da ilki.
    Tanınmayan değerin döndüğü yer budur — form da, asansör dizisi de. */
function secimVarsayilani(e){
  if([...e.options].some(o => o.value === '')) return '';
  const d = [...e.options].find(o => o.defaultSelected) || e.options[0];
  return d ? d.value : '';
}

/*  Alanın ekrandaki adı ( uyarı metinleri için ) ;  asansör kartındaki ya da
    trafik sütunundaki alanda asansörün numarası da eklenir. */
function alanEtiketi(e){
  const l = e.closest('.alan') && e.closest('.alan').querySelector('label');
  let ad = l ? [...l.childNodes].filter(n => n.nodeType === 3)
                 .map(n => n.textContent).join(' ').replace(/\s+/g, ' ').trim() : '';
  if(!ad) ad = e.id;
  const kart = e.closest('[id^="a_kutu"]');
  const no = kart ? kart.id.slice(-1)
    : ((/^c_(P|kg|kt|V|durak|h|bodrum|mta|mtk|mtg|mtp)([1-4])$/.exec(e.id) || [])[2]);
  return no ? `${ad} ( ${no}. asansör )` : ad;
}

/*  TANINMAYAN DEĞERLER SESSİZ GEÇMEZ.  Dosyadaki ( ya da tarayıcıda saklı )
    bir seçim değeri bu sürümün listesinde yoksa — program güncellenmiş, bir
    seçenek kalkmış ya da adı değişmiştir — alan varsayılanına döner ve proje
    artık o değerle hesaplanır.  Bu bir veri değişikliğidir;  durum satırı
    birkaç saniyede kaybolduğu için ayrıca pencereyle söylenir.
    ``liste``:  [ { etiket , deger , yeni } ]                               */
function taninmayanBildir(liste, kaynak){
  if(!liste || !liste.length) return '';
  const satir = x => `• ${x.etiket} :  "${x.deger}"  →  ${x.yeni === '' ? '( boş — ofis standardı )' : `"${x.yeni}"`}`;
  const kisa = `${liste.length} değer bu sürümde yok, VARSAYILAN kullanıldı`;
  console.warn(kaynak + ' tanınmayan değerler:', liste);
  alert(`${kaynak} ${kisa}:\n\n${liste.map(satir).join('\n')}\n\n`
        + 'Hesap artık bu yeni değerlerle yapılıyor.  Doğru değerleri seçip projeyi yeniden kaydedin.');
  return kisa;
}

/*  Yeni proje yüklenmeden önce ilgili bölüm TEMİZLENİR.
    uygula() yalnız GELEN alanları yazar; dosyada olmayan alanlar önceki
    projeden kalıyordu.  Tek asansörlük bir dosya, formda duran eski 2. ve 3.
    kolonlar yüzünden 10+16+20 kişilik üçlü grup olarak hesaplanabiliyordu.   */
function bolumuTemizle(tur){
  const bosalt = id => { const e=$(id); if(e) alanaYaz(e, ''); };
  if(tur==='tek' || tur==='coklu'){
    for(let i=1;i<=4;i++){
      ['P','kg','kt','V','durak','h','bodrum','mta','mtk','mtg','mtp']
        .forEach(k=>bosalt('c_'+k+i));
    }
    ['bodrum','manuel_k','manuel_V'].forEach(k=>bosalt('c_'+k));
    const l=$('c_eknufus_liste'); if(l) l.innerHTML='';
  }
  if(tur==='mukavemet' && MUK){
    //  Önceki projeden bekleyen kabin ağırlığı yenilemesi yeni projenin
    //  değerini ezmesin.
    MUK_GK_TAZELE = {};
    //  Dosyada BOŞ kalan alanlar, önceki projeden kalma değerle karışmasın:
    //  bölüm önce varsayılanlarına döner.
    for(const gr of MUK.gruplar) for(const f of gr.alanlar){
      const e=$(M_ID(f.anahtar)); if(!e) continue;
      if(e.type === 'checkbox') e.checked = !!f.varsayilan;
      else alanaYaz(e, f.varsayilan===null||f.varsayilan===undefined ? '' : mSayi(f.varsayilan));
    }
    //  Uygulamanın ofis sabitleri de:  boş = varsayılan.
    Object.keys(((MUK.sabitler||{}).varsayilan)||{}).forEach(k=>bosalt('uof_'+k));
  }
  if(tur==='avan'){
    for(let i=1;i<=4;i++){
      ['tanim','kapasite','Q_elle','V','eta','Hk','kuyu_genisligi','kabin_boyu',
       'kabin_genisligi','Gk_elle','gr','Fmk','Fsh','Nsc','S1','L1','S2','L2',
       'kablo_tipi','i_palanga','q_denge'].forEach(k=>bosalt('a_'+k+i));
    }
    ['temel_a','temel_b','mk_uzunluk','mk_genislik'].forEach(k=>bosalt('a_'+k));
    //  Yüklenen avan değerleri trafikle EZİLMESİN:  bu asansörler artık
    //  "otomatik" değildir ( bkz. avanDoldur ).
    AVAN_OTO = {};
  }
}

/*  Kayıtlı bir projeyi ( dosya · tarayıcı belleği · örnek ) forma basar.
    Döner:  TANINMAYAN seçim değerleri  [ { etiket , deger , yeni } ] —
    bu sürümün listesinde olmadığı için varsayılana dönenler ( bkz.
    taninmayanBildir ).  */
function uygula(o){
  if(o.__tur) bolumuTemizle(o.__tur);
  //  VERİ HANGİ PROJENİN?  Avan durumu ( trafik adedi · ek asansör · otomatik
  //  alan izleri ) YALNIZ avan verisinden kurulur.  Eskiden .uygulama dosyası
  //  açılınca da yeniden kuruluyordu:  bellekteki avan projesinin otomatik
  //  izleri siliniyor, ek asansör sayısı ekrandaki kutulardan yanlış
  //  türetiliyordu — avana dönülüp bir şey değişince bozuk hâli kaydedilirdi.
  const avanVerisi = o.__mod ? o.__mod !== 'uygulama'
                             : Object.keys(o).some(k => /^(c_|a_|k_|of_|sb_)/.test(k));
  const mukDizi = typeof MUK_ASANSORLER !== 'undefined'
                  && Array.isArray(o.__muk_asansorler) && o.__muk_asansorler.length;
  const taninmayan = [];
  Object.entries(o).forEach(([k,val])=>{
    if(k.startsWith('__')) return;
    const e=$(k); if(!e) return;
    //  Uygulamada asansöre ait alanın asıl kaynağı asansör dizisidir;  onun
    //  tanınmayan değerleri aşağıda, asansör numarasıyla birlikte sayılır.
    if(!alanaYaz(e, val) && !(mukDizi && typeof mAsansorAlaniMi === 'function' && mAsansorAlaniMi(k)))
      taninmayan.push({etiket: alanEtiketi(e), deger: String(val), yeni: e.value});
  });
  // Ek nüfus listeleri yalnız o bölüm gerçekten verilmişse yeniden kurulur;
  // böylece kısmi yükleme (yalnız trafik ya da yalnız avan) diğerini bozmaz.
  //  Eski projelerde ek nüfus 't' ( tek gövde ) altında saklanmış olabilir;
  //  tek gövde kalktığı için 'c' boşsa oradan taşınır.
  ['c','t'].forEach(p=>{
    if(!(('__eknufus_'+p) in o)) return;
    const liste = o['__eknufus_'+p] || [];
    if(p==='t' && (o.__eknufus_c || []).length) return;
    $('c_eknufus_liste').innerHTML='';
    liste.forEach(s=>ekNufusEkle('c', s));
  });
  if(avanVerisi){
    /* Asansör adedi: kaydedilmişse ondan, yoksa dolu çoklu kolon sayısından
       türetilir — eski proje dosyalarında da doğru gövde açılsın. */
    let adet = parseInt(o.__trafik_adet, 10);
    if(!(adet>=1 && adet<=4)){
      const dolu=[1,2,3,4].filter(i=>$('c_P'+i) && $('c_P'+i).value!=='').length;
      adet = dolu>1 ? dolu : TRAFIK_ADET;
    }
    TRAFIK_ADET = Math.max(1, Math.min(4, adet));
    /* Trafik grubu dışı asansör adedi: kaydedilmişse ondan, yoksa "kullan"
       kutularından türetilir ( eski dosyalar için ). */
    let ek = parseInt(o.__avan_ek, 10);
    const ekYazili = ek>=0 && ek<=3;
    if(!ekYazili){
      const etkin=[1,2,3,4].filter(i=>$('a_aktif'+i) && $('a_aktif'+i).checked).length;
      ek = Math.max(0, etkin - TRAFIK_ADET);
    }
    AVAN_EK = Math.max(0, Math.min(3, ek));
    /*  ÖNCEKİ PROJENİN TRAFİK SONUCU GEÇMEZ.  Kart sayısı trafik grubunun
        adedinden kurulur;  ekranda başka bir projenin sonucu dururken o
        projenin adedi okunuyor, ek asansör sayısı ona göre yeniden
        hesaplanıyordu.  Sonuçlar yeni proje hesaplanınca yeniden gelir.
        Grubun adedi kaydedildiği andaki AÇIK KART sayısından türetilir:
        açık kart = grup + ek ( bkz. avanAdedi ) — dosya ikisini de taşır. */
    SON.c = SON.t = SON.a = null;
    const acik = [1,2,3,4].filter(i => o['a_aktif'+i] === true).length;
    AVAN_TABAN = (ekYazili && acik >= 1) ? Math.max(1, acik - AVAN_EK) : null;
    AVAN_OTO = (o.__avan_oto && typeof o.__avan_oto==='object') ? {...o.__avan_oto} : {};
    AVAN_TRF = (o.__avan_trf && typeof o.__avan_trf==='object') ? {...o.__avan_trf} : {};
  }
  /*  Çoklu asansör dizisi de bir form alanı DEĞİLDİR.  Proje dosyasından
      ( .uygulama ) geri yüklenirken buradan kurulur;  form ayaktaysa aktif
      asansör hemen basılır, değilse mukavemetKur() onu yerine oturtur. */
  if(mukDizi){
    MUK_ASANSORLER = o.__muk_asansorler
      .slice(0, (MUK && MUK.asansor_azami) || 4)
      .map(x => (x && typeof x === 'object') ? {...x} : {});
    //  Asansörlerin tanınmayan seçim değerleri HEPSİNDE aynı biçimde
    //  varsayılana çekilir ve sayılır ( bkz. mTaninmayanAyikla ).
    if(typeof mTaninmayanAyikla === 'function' && $('m_form') && $('m_form').innerHTML)
      MUK_ASANSORLER.forEach((x, i) => taninmayan.push(
        ...mTaninmayanAyikla(x, MUK_ASANSORLER.length > 1 ? i + 1 : null)));
    MUK_ADET = Math.min(Math.max(1, Number(o.__muk_adet) || MUK_ASANSORLER.length),
                        MUK_ASANSORLER.length);
    MUK_AKTIF = Math.min(Math.max(0, Number(o.__muk_aktif) || 0), MUK_ADET - 1);
    if($('m_form') && $('m_form').innerHTML){
      mAsansorYukle(MUK_AKTIF);
      if($('m_adet')) $('m_adet').value = String(MUK_ADET);
      mAsansorSekmeleriTazele();
    }
  }
  /*  UYGULAMA FORMUNUN GÖRÜNÜMÜ DEĞERLERE UYDURULUR.  Değerler yazılır ama
      onlardan türeyen ekran durumu kendiliğinden yenilenmez:  makine dairesi
      düğmesi, yerleşime göre gizlenen alanlar, kanal uyumu, Gelişmiş sayaçları.
      Proje dosyası açılınca makine daireli projede düğme "Yok ( MRL )"
      gösteriyor, tabliye ve makine dairesi ölçüleri gizli kalıyordu — hesap
      doğru yapılırken form başka bir yerleşimi gösteriyordu.  ( Form henüz
      kurulmadıysa bunu mukavemetKur yapar. ) */
  if($('m_form') && $('m_form').innerHTML && typeof mMakineDairesiKutulari === 'function'){
    mMakineDairesiKutulari();
    mIkiliTazele();
    mKanalUyumu();
    mGelismisTazele();
  }
  cokluKolonlariGoster();
  avanKartlariGoster();
  adetDugmeleriKur();
  mkYokUygula();
  ofisTazele();
  etiketleriGuncelle();
  return taninmayan;
}

/* ═══════════════════════════ PROJE DOSYASI ═══════════════════════════
   Projenin bütün girdilerinin GERİ DÖNÜŞ NOKTASI.  Ne PDF ne DXF —
   yalnız programın okuyup yazdığı veri.  Aylar sonra revizyon gerektiğinde
   dosya yüklenir, değişen düzeltilir, çıktılar yeniden alınır.

   İKİ AYRI UZANTI:  avan ve uygulama ayrı projelerdir, dosyaları da ayrıdır.
   Her dosya YALNIZ kendi projesinin alanlarını taşır;  yanlış dosyayı yanlış
   moda yüklemek de böyle engellenir.

   SÜRÜM ALANI:  girdi sözleşmesi zamanla değişir ( bugün makine tipi eklendi ).
   Sürüm yazılı olmasaydı eski bir dosyadaki eksik alan SESSİZCE varsayılana
   düşerdi.  Yazılı olduğu için program eksiği sayıp söyleyebiliyor.        */
const PROJE_SURUM = 1;
const PROJE_UZANTI = { avan:'.avan', uygulama:'.uygulama' };

function projeDosyaAdi(mod){
  //  Proje adı her modun KENDİ kimlik alanından okunur:  uygulamanınki
  //  mk_proje_adi, avanınki kapak formundadır.  Karıştırılırsa dosya adı
  //  hep "Asansor" çıkar.
  //  kapakGirdi() alanı "project_title" adıyla döndürür;  "proje_adi"
  //  aranırsa hep boş çıkar ve dosya adı her projede "Asansor" olurdu.
  const p = (mod === 'uygulama')
    ? (($('mk_proje_adi') || {}).value || '')
    : ((kapakGirdi() || {}).project_title || '');
  const ad = String(p).replace(/[^\p{L}\p{N} \-_]/gu,'').trim().slice(0,48) || 'Asansor';
  return ad + PROJE_UZANTI[mod];
}
/*  Ofis sabitleri de dosyaya girer:  proje o günkü kabullerle hesaplandı,
    üç yıl sonra açıldığında AYNI sonucu vermelidir.  Ama karşı bilgisayarın
    ofis standardını sessizce ezmemeli — yüklerken sorulur.                */
function projeGovdesi(mod){
  const m = mod || MOD;
  return { __mod:m, __surum:PROJE_SURUM, __program:'Asansör Proje Programı',
           __tarih:new Date().toISOString().slice(0,10),
           alanlar: tumGirdiler(m) };
}
function projeKaydet(){
  const ad = projeDosyaAdi(MOD);
  const b = new Blob([JSON.stringify(projeGovdesi(MOD),null,1)],{type:'application/json'});
  const u = URL.createObjectURL(b), a = document.createElement('a');
  a.href=u; a.download=ad; a.click(); setTimeout(()=>URL.revokeObjectURL(u),3000);
  durum('Proje kaydedildi: '+ad);
}
function projeAc(ev){
  const f=ev.target.files[0]; if(!f) return;
  const fr=new FileReader();
  fr.onload=()=>{
    let d; try{ d=JSON.parse(fr.result); }catch(e){ durum('Dosya okunamadı — geçerli bir proje dosyası değil', true); return; }
    projeUygula(d, f.name);
  };
  fr.readAsText(f); ev.target.value='';
}
function projeUygula(d, dosyaAdi){
  //  Eski biçim ( başlıksız düz girdi sözlüğü ) da okunur.
  const govde = (d && d.alanlar) ? d.alanlar : d;
  const mod = (d && d.__mod) || (govde && govde.__mod) || null;
  if(mod && mod !== MOD){
    const ad = mod === 'uygulama' ? 'UYGULAMA' : 'AVAN';
    durum(`Bu dosya ${ad} projesine ait — o bölümü açıp yeniden deneyin.`, true);
    return;
  }
  //  SÜRÜM:  dosyada olmayan alanlar varsayılana döner;  sessiz kalmamalı.
  const surum = (d && d.__surum) || 0;
  const eksik = eksikAlanlar(govde, MOD);
  bolumuTemizle(MOD === 'uygulama' ? 'mukavemet' : 'avan');
  if(MOD !== 'uygulama'){ bolumuTemizle('tek'); bolumuTemizle('coklu'); }
  const taninmayan = uygula(govde) || [];
  yaz();
  if(MOD === 'uygulama'){ mGkBoslariIsaretle(); hesapMukavemet(); } else hesaplaHepsi();
  let m = 'Proje açıldı: ' + dosyaAdi;
  if(surum && surum !== PROJE_SURUM) m += `  ( dosya sürüm ${surum}, program sürüm ${PROJE_SURUM} )`;
  if(eksik.length) m += `  ·  dosyada bulunmayan ${eksik.length} alan VARSAYILANA döndü`;
  const t = taninmayanBildir(taninmayan, `"${dosyaAdi}" dosyasında`);
  if(t) m += '  ·  ' + t;
  durum(m, eksik.length > 0 || !!t);
  if(eksik.length) console.warn('Varsayılana dönen alanlar:', eksik);
}
/*  Dosyada olmayan ama formda bulunan alanlar.  Sürüm farkının somut
    karşılığı budur — kaç alan sessizce varsayılana döndü.                 */
function eksikAlanlar(govde, mod){
  const eksik = [];
  document.querySelectorAll('input,select').forEach(e=>{
    if(!e.id || e.id.indexOf('_goster') >= 0) return;
    if(alanModu(e.id) !== mod) return;
    if(govde[e.id] === undefined) eksik.push(e.id);
  });
  return eksik;
}
function hepsiniTemizle(){
  const ad = MOD === 'uygulama' ? 'uygulama projesinin' : 'avan projesinin';
  //  YALNIZ İÇİNDE BULUNULAN PROJE silinir — öbürü ayrı kovadadır.
  if(!confirm(`Bu ${ad} tüm girdileri silinecek. Emin misiniz?\n\n( Öbür proje etkilenmez. )`)) return;
  localStorage.removeItem(KOVA[MOD]); location.reload();
}
function ornekYukle(){
  const O={c_bina_tipi:'Konut', c_bina_yuksekligi:'39,98', c_yapi_yuksekligi:'43', c_N:'11', c_h:'3',
    c_hizli1:'44', c_hizli2:'3',
    c_P1:'10', c_kg1:'900', c_kt1:'Teleskopik Otomatik',
    c_P2:'16', c_kg2:'1100', c_kt2:'Teleskopik Otomatik', c_P3:'', c_P4:'',
    /*  Ofis varsayılanı olan alanlar ( U, κ, εmax, β, çubuk adedi, ray, makine,
        sehpa, kesitler, kablo, L1, Nsç ) BİLEREK boş bırakıldı — örnek proje
        de gerçek kullanımdaki gibi bunları ofis standardından alır.
        Şerit boyu da boş: ofiste yalnız temel uzunluğu ve genişliği girilir,
        band boyu bunlardan türetilir. */
    a_temel_a:'26,55', a_temel_b:'16,4',
    a_mk_yok:true, a_mk_uzunluk:'0', a_mk_genislik:'0',
    a_aktif1:true, a_tanim1:'İnsan', a_kapasite1:'10', a_V1:'1.6', a_eta1:'0,85', a_Hk1:'38,50',
    a_makine_tipi1:'Dişlisiz', a_i_palanga1:'2',
    a_kuyu_genisligi1:'1800', a_kabin_boyu1:'1450', a_kabin_genisligi1:'1300',
    a_aktif2:true, a_tanim2:'Sedye + Yük', a_kapasite2:'16', a_V2:'1.6', a_eta2:'0,85', a_Hk2:'38,50',
    a_makine_tipi2:'Dişlisiz', a_i_palanga2:'2',
    a_kuyu_genisligi2:'2650', a_kabin_boyu2:'1350', a_kabin_genisligi2:'2100',
    a_aktif3:false, a_aktif4:false, __eknufus_c:[],
    /* Ofisin örnek projesi 10 + 16 kişilik İKİ asansörlük bir gruptur —
       trafik adedi 2, avanda trafik dışı asansör yok. */
    __trafik_adet:2, __avan_ek:0};
  uygula(O); yaz(); hesaplaHepsi();
  durum('Örnek proje yüklendi');
}

/* ═══════════════════════════════════════════════════════════════════════
   AÇILIŞ EKRANI
   Program açıldığında hangi projenin hazırlanacağı seçilir.  Şimdilik
   yalnız "Avan Proje" hazır;  uygulama projesi bölümü sonra eklenecek.
   ═══════════════════════════════════════════════════════════════════════ */
function uygulamaAc(hangi){
  modAyarla(hangi);
  document.body.classList.remove('giriste');
  window.scrollTo(0, 0);
  if(MOD === 'uygulama'){
    sekmeGoster('uygproje');
    mukavemetKur();
    durum('Uygulama projesi — mukavemet hesabı.');
  }else{
    sekmeGoster('trafik');
    durum('Avan proje — 1 · Trafik Hesabı ile başlayabilirsiniz.');
  }
}

function anaEkran(){
  document.body.classList.add('giriste');
  window.scrollTo(0, 0);
}

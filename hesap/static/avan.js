/* ═══════════════════════════════════════════════════════════════════
   AVAN PROJE  —  arayüz

   Trafik hesabı, avan hesapları ve proje kapağı.  Uygulama projesinden
   BAĞIMSIZDIR;  ortak kısım için bkz. ortak.js
   ═══════════════════════════════════════════════════════════════════ */

/* ------------------------------------------------- trafik: asansör adedi */
/*  Tek ve çoklu hesap AYNI SORUYU sormaz:
      1 asansör  →  "yeter mi, yetmiyorsa kaç adet gerekir?"  (HESAPLAMA → PAFTA)
      2-4        →  "bu grup yeterli mi?"                     (ÇOKLU → PAFTA-COKLU)
    Bu yüzden iki motor yolu da korunur; kullanıcı yalnız adedi seçer.
    Ortak bina girdileri iki gövde arasında aynalanır, hiçbir şey kaybolmaz. */
const TRAFIK_ORTAK = ['bina_tipi','bina_yuksekligi','yapi_yuksekligi','N','h','bodrum',
                      'hizli1','hizli2','manuel_k','manuel_V'];

function adetDugmeleriKur(){
  const kt=$('adet_dugmeler_c');
  if(kt) kt.innerHTML=[1,2,3,4].map(n=>
      `<button type="button" class="adet-dg${n===TRAFIK_ADET?' secili':''}"
        onclick="trafikAdedi(${n})">${n}</button>`).join('');

  /* Avan sekmesindeki adet seçici — trafik adedinin ALTINA inemez, çünkü
     trafik grubundaki her asansörün elektrik hesabı da yapılmalıdır. */
  const ka=$('adet_dugmeler_a');
  if(ka){
    const taban=avanTaban(), n=avanAdedi();
    ka.innerHTML=[1,2,3,4].map(x=>
      `<button type="button" class="adet-dg${x===n?' secili':''}${x<taban?' kilitli':''}"
        ${x<taban?`title="Trafik hesabı ${taban} asansör veriyor"`:''}
        onclick="avanAdediSec(${x})">${x}</button>`).join('');
    const aa=$('a_adet_aciklama');
    if(aa) aa.textContent = n>taban
      ? `${taban} asansör trafik grubundan  ·  ${n-taban} adet trafik grubu dışı ( yük / sedye )`
      : `Trafik hesabıyla eşitlendi — ${n} asansör`;
  }
}

/*  Adet artık YÖNTEM değil, VERİ:  kaç asansör tanımlandığını söyler.
    Kapanan kolonun DEĞERİ SİLİNMEZ, yalnız gizlenir — 2 → 1 → 2 gidip
    gelindiğinde grupta tanımlı farklı kapasiteler ( ör. 10 + 16 kişilik )
    kaybolmasın.  Hesaba yalnız GÖRÜNEN kolonlar gönderilir ( trafikGirdi ).
    Yeni açılan boş kolon 1. asansörden doldurulur. */
function trafikAdedi(n){
  n=Math.max(1,Math.min(4,parseInt(n,10)||1));
  if(n===TRAFIK_ADET){ return; }
  TRAFIK_ADET=n;
  AVAN_TABAN = null;            // hesap yöntemi değişti — eski grup adedi geçmez
  for(let i=2;i<=n;i++){
    if($('c_P'+i) && !$('c_P'+i).value){
      alanaYaz($('c_P'+i),  v('c_P1'));
      alanaYaz($('c_kg'+i), v('c_kg1'));
      alanaYaz($('c_kt'+i), v('c_kt1'));
    }
  }
  cokluKolonlariGoster();
  avanSenkron();                 // avan adedi trafik adedini takip eder
  sekmeGoster('trafik');
  yaz(); planla();
  durum(n>1 ? `${n} asansör tanımlandı — grup denetlenecek`
            : 'Tek asansör tanımlandı — gerekli adet hesaplanacak');
}

function cokluKolonlariGoster(){
  for(let i=1;i<=4;i++){
    const k=$('c_kutu'+i);
    if(k) k.hidden = (i>TRAFIK_ADET);
  }
  /*  Taahhütname yalnız adedi PROGRAMIN bulduğu tek tanımda anlamlıdır. */
  const t=$('c_taahhut_alan');
  if(t) t.hidden = (TRAFIK_ADET>1);
}

/* ------------------------------------------- avan: asansör adedi
   ADET TEK YERDE BELİRLENİR.  Avandaki asansör adedi, trafik hesabının
   verdiği asansör adedini kendiliğinden takip eder:

     · 1 asansör seçiliyken   →  trafik hesabının BULDUĞU adet
       ( "1 asansör yetmiyor, 3 gerekir" derse avanda 3 kart açılır )
     · 2 - 4 asansör seçiliyken →  grupta tanımlanan adet

   Binada trafik grubuna girmeyen bir asansör varsa ( ör. ayrı bir yük ya da
   sedye asansörü ) avan adedi ELLE artırılır; fazlalar "trafik grubu dışı"
   diye işaretlenir — kurulu güce girer, trafik kontrolüne girmez.  Bu fark
   ( AVAN_EK ) kalıcıdır, trafik adedi değişince korunur.

   DOLDURULMUŞ bir kart kendiliğinden KAPANMAZ: trafik grubu küçülürse o
   asansör trafik dışına alınır, sessizce hesap dışı kalmaz.  Kapatmak
   kullanıcının açık kararıdır. */
function trafikGrupAdedi(){
  const k = trafikKoprusu();
  const n = k && Array.isArray(k.asansorler) ? k.asansorler.length : 0;
  if(n > 0) return n;                      // ham değer — 4'ten büyük olabilir
  //  TRAFİK SONUCU YOKKEN.  Grup hesabında adet kullanıcınındır ( TRAFIK_ADET ).
  //  Tek hesapta ise adedi trafik bulur;  sonuç henüz yokken 1 sanılırsa
  //  "dolu kart kapanmaz" kuralı ( avanAdedi ) ek asansörü trafik grubu dışı
  //  sayıp AVAN_EK'i şişiriyordu:  2 + 1 asansörlük proje her açılışta
  //  2 + 2 = 4 kartla açılıyordu.  Son bilinen adet ( dosyadan ya da son
  //  hesaptan ) kullanılır.
  return (TRAFIK_ADET === 1 && AVAN_TABAN) ? AVAN_TABAN : TRAFIK_ADET;
}
function avanTaban(){ return Math.max(1, Math.min(4, trafikGrupAdedi())); }

/* Kullanıcının ELLE doldurduğu en yüksek asansör numarası.
   Trafikten otomatik gelen değerler sayılmaz — yoksa trafik grubu küçüldüğünde
   kendi doldurduğumuz kart "kullanıcı verisi" sanılıp sonsuza dek açık kalırdı.
   "Q elle" ise HER ZAMAN kullanıcınındır ( trafik onu hiç yazmaz ):  kart
   otomatik işaretli olsa da sayılır.  Eskiden sayılmıyordu;  trafik kartın
   kapasitesini bir kez yazınca kart otomatik sayılıyor, grup küçülünce
   kapanıyor, kapasite / hız siliniyor ama Q elle kalıyordu — bir sonraki
   eşitlemede kart yeniden açılıyor, arada gösterilen hesapta o asansör
   yoktu ( TEST 13'ün rastgele dizisi buldu ). */
function avanDoluUst(){
  let u = 0;
  for(let i=1;i<=4;i++){
    if(v('a_Q_elle'+i)!=='' || (!AVAN_OTO[i] && v('a_kapasite'+i)!=='')) u = i;
  }
  return u;
}

function avanAdedi(){
  const taban = avanTaban();
  AVAN_EK = Math.max(0, Math.min(4 - taban, AVAN_EK));
  let n = Math.min(4, taban + AVAN_EK);
  const dolu = Math.min(4, avanDoluUst());
  if(dolu > n){ AVAN_EK = dolu - taban; n = dolu; }   // dolu kart kapanmaz
  return Math.max(1, n);
}

function avanAdediSec(n){
  const taban = avanTaban();
  n = Math.max(1, Math.min(4, parseInt(n,10)||1));
  if(n < taban){
    durum(`Trafik hesabı ${taban} asansör veriyor — avan adedi bunun altına inemez`, true);
    return;
  }
  const dolu = avanDoluUst();
  if(n < dolu){
    durum(`${dolu} nolu asansörün girdileri dolu — kapatmak için önce kapasitesini boşaltın`, true);
    return;
  }
  AVAN_EK = n - taban;
  avanSenkron();
  yaz(); planla();
  const ek = n - taban;
  durum(ek > 0 ? `${n} asansör  —  ${ek} adedi trafik grubu dışı ( yük / sedye )`
               : `${n} asansör  —  tamamı trafik grubundan`);
}

/* Kart aç / kapa + "trafik grubundan / dışı" etiketi.
   a_aktif kutuları artık ADETTEN türetilir; kullanıcı tek tek işaretlemez. */
function avanKartlariGoster(){
  const n = avanAdedi(), taban = avanTaban();
  for(let i=n+1;i<=4;i++){          // kapanan OTOMATİK kartın izi kalmasın
    if(!AVAN_OTO[i]) continue;
    const sp=$('a_kapasite'+i), sv=$('a_V'+i);
    if(sp) sp.value=''; if(sv) sv.value='';
    delete AVAN_OTO[i]; delete AVAN_TRF[i];
  }
  for(let i=1;i<=4;i++){
    //  Zincir YOK iken birim kütle hesaba girmez:  kutu soluk ( disabled )
    //  durur ki içinde kalmış bir sayı kullanılıyor sanılmasın.
    const z=$('a_zincir_birim_kutle'+i);
    if(z) z.disabled = v('a_denge_zinciri'+i) !== 'Var';
    const c=$('a_aktif'+i), k=$('a_kutu'+i), e=$('a_etiket'+i);
    if(c) c.checked = (i<=n);
    if(k) k.classList.toggle('pasif', i>n);
    if(e){
      e.textContent = i>n ? '' : (i<=taban ? 'trafik grubundan' : 'trafik grubu dışı');
      e.className = 'as-etiket' + (i>taban && i<=n ? ' dis' : '');
    }
  }
}

/* Kapasite ve hızı trafikten doldurur — YALNIZ BOŞ alanları.
   Elle girilmiş bir değerin üzerine hiçbir zaman yazılmaz; uyuşmazlık
   varsa motor uyarı üretir, kullanıcı "Trafikten güncelle" ile eşitler. */
function avanDoldur(){
  const k = trafikKoprusu();
  if(!k || !Array.isArray(k.asansorler)) return false;
  const taban = avanTaban();
  let degisti = false, yansiyan = 0;

  /*  Bir alan iki durumda trafikten yazılır:
        1) alan BOŞSA                                     → ilk doldurma
        2) TRAFİKTEKİ DEĞER DEĞİŞTİYSE                    → avan onu izler
      Trafik değişmediği sürece alana dokunulmaz; kullanıcının elle girdiği
      değer orada durur.  ( Her hesapta körü körüne yazılsaydı elle
      düzeltmek imkânsız olurdu: yazdığınız değer 0,2 sn sonra geri
      dönerdi. )  AVAN_TRF, her asansöre EN SON YANSITILAN trafik değerini
      tutar; karşılaştırma buna göre yapılır. */
  const yaz1 = (alan, yeni, i) => {
    if(!alan || yeni==null || yeni==='') return false;
    alanaYaz(alan, yeni);
    if(alan.value===''){ return false; }
    degisti = true; AVAN_OTO[i] = true;
    return true;
  };

  for(let i=1;i<=Math.min(taban, k.asansorler.length, 4);i++){
    const t = k.asansorler[i-1] || {};
    const onceki = AVAN_TRF[i] || {};
    const sp = $('a_kapasite'+i), sv = $('a_V'+i);

    //  Kapasite —  'Q elle' doluysa dokunulmaz ( kullanıcı Tablo-7 dışına çıkmış )
    if(sp && t.P!=null && t.P!==''){
      const bos = (sp.value==='' && v('a_Q_elle'+i)==='');
      const trafikDegisti = ('P' in onceki) && String(onceki.P)!==String(t.P);
      /*  DOLU BİR ALAN İLK SENKRONDA EZİLMEZ.  Eskiden "ilk kez" durumunda
          alan dolu olsa bile üzerine yazılıyordu;  dosyadan yüklenen
          16 kişi / 2,50 m/s, formdaki eski trafik yüzünden 10 kişi / 1,60'a
          dönüyordu.  Boş alan zaten `bos` ile dolduruluyor;  trafik gerçekten
          değiştiyse `trafikDegisti` güncelliyor ve kullanıcı bilgilendiriliyor. */
      if(bos || trafikDegisti){
        const eskiDeger = sp.value;
        if(yaz1(sp, t.P, i) && eskiDeger!=='' && eskiDeger!==sp.value) yansiyan++;
      }
      AVAN_TRF[i] = Object.assign({}, AVAN_TRF[i], {P: t.P});
    }

    //  Kabin hızı
    if(sv && t.V!=null && t.V!==''){
      const trafikDegisti = ('V' in onceki) && String(onceki.V)!==String(t.V);
      if(sv.value==='' || trafikDegisti){
        const eskiDeger = sv.value;
        if(yaz1(sv, t.V, i) && eskiDeger!=='' && eskiDeger!==sv.value) yansiyan++;
      }
      AVAN_TRF[i] = Object.assign({}, AVAN_TRF[i], {V: t.V});
    }
  }
  if(yansiyan) durum('Trafik hesabı değişti — avandaki kapasite / hız güncellendi');
  return degisti;
}

function avanSenkron(){
  const degisti = avanDoldur();          // önce doldur — adet dolu karta bakar
  avanKartlariGoster();
  adetDugmeleriKur();
  return degisti;
}

/* ---------------------------------------------------------- girdi topla */
const v = id => { const e=$(id); return e ? e.value.trim() : ''; };

/*  TEK GİRDİ BİÇİMİ:  bina alanları + asansör listesi.
    Yöntemi ( PAFTA / PAFTA-COKLU ) sunucu, asansörlerin aynı tip olup
    olmamasına bakarak seçer — kullanıcı seçmez. */
function trafikGirdi(){
  return {
    bina_tipi:v('c_bina_tipi'), bina_yuksekligi:v('c_bina_yuksekligi'),
    yapi_yuksekligi:v('c_yapi_yuksekligi'), N:v('c_N'), h:v('c_h'),
    bodrum:v('c_bodrum'),
    hizli1:v('c_hizli1'), hizli2:v('c_hizli2'),
    manuel_k:v('c_manuel_k'), manuel_V:v('c_manuel_V'),
    //  Gizliyken ( 2-4 asansör ) değer korunur ama hesaba girmez.
    taahhutname: TRAFIK_ADET===1 ? v('c_taahhut') : '',
    ek_nufus:ekNufusTopla('c'),
    //  YALNIZ GÖRÜNEN kolonlar hesaba girer; gizli kolonlar değerlerini
    //  korur ama tanımlanmamış sayılır.
    asansorler:[1,2,3,4].filter(i=>i<=TRAFIK_ADET).map(i=>({
      P:v('c_P'+i), kapi_genisligi:v('c_kg'+i), kapi_tipi:v('c_kt'+i),
      V:v('c_V'+i), durak:v('c_durak'+i), h:v('c_h'+i), bodrum:v('c_bodrum'+i),
      manuel_ta:v('c_mta'+i), manuel_tk:v('c_mtk'+i),
      manuel_tg:v('c_mtg'+i), manuel_tp:v('c_mtp'+i)
    })).filter(a=>a.P!=='')
  };
}
function avanGirdi(){
  /*  U · κ · εmax · β · Is alanları avan panelinden kaldırıldı ( ofis
      standardında ).  v() olmayan alan için '' döndürür, motor da boş
      değeri ofis varsayılanına çevirir — liste yine de tam bırakıldı ki
      eski proje dosyalarındaki değerler taşınabilsin. */
  const ortak={}; ['U','kappa','eps_max','temel_a','temel_b','beta','cubuk_sayisi',
    'mk_uzunluk','mk_genislik'].forEach(k=>ortak[k]=v('a_'+k));
  ortak.mk_yok = !!($('a_mk_yok') && $('a_mk_yok').checked);
  const asansorler=[1,2,3,4].map(i=>{
    const o={aktif:$('a_aktif'+i).checked};
    ['tanim','kapasite','Q_elle','V','eta','Hk','kuyu_genisligi','kabin_boyu','kabin_genisligi',
     'Gk_elle','gr','Fmk','Fsh','Nsc','S1','L1','S2','L2','kablo_tipi',
     'i_palanga','q_denge','makine_tipi',
     'denge_zinciri','agirlik_guvenlik_tertibati','zincir_birim_kutle']
      .forEach(k=>o[k]=v('a_'+k+i));
    return o;
  });
  const sabitler={}; Object.keys(SEC.sabit_b).forEach(k=>{const x=v('sb_'+k); if(x!=='')sabitler[k]=x;});
  Object.keys(SEC.ofis_varsayilan||{}).forEach(k=>{const x=v('of_'+k); if(x!=='')sabitler[k]=x;});
  return {ortak, asansorler, sabitler, trafik:trafikKoprusu()};
}
/* Sekme başlığındaki uyarı rozeti — sağ paneldeki uyarılar sekme kapalıyken
   gözden kaçmasın diye sekmenin üstünde sayı olarak da görünür. */
function sekmeRozeti(sekme, hata, sayi){
  const b=document.querySelector('.sekme[data-sekme="'+sekme+'"]');
  if(!b) return;
  let r=b.querySelector('.sekme-rozet');
  if(!hata && !sayi){ if(r) r.remove(); return; }
  if(!r){ r=document.createElement('span'); b.appendChild(r); }
  r.className='sekme-rozet '+(hata?'kirmizi':'sari');
  r.textContent = hata ? '!' : String(sayi);
  r.title = hata ? 'Hesap hatası var' : sayi+' uyarı';
}

/* ---------------------------------------------------------- hesap */
/* Önce trafik hesaplanır — avan adedi ve kapasite/hız oradan gelir; avan
   ondan SONRA hesaplanır ki ilk çizimde eksik asansör görünmesin. */
async function hesaplaHepsi(){
  await hesapTrafik();
  avanSenkron();
  await hesapAvan();
}

/*  TEK HESAP YOLU.  Kullanıcı yöntem seçmez; sunucu, tanımlanan asansörler
    aynı tipte mi diye bakıp PAFTA ya da PAFTA-COKLU yolunu kendisi seçer
    ( engine.traffic.hesapla ).  Dönen sonuçta `yol` ve `pafta` alanları var. */
async function hesapTrafik(){
  const sira = ++ISTEK.trafik;
  try{
    const r = await (await fetch('/api/trafik',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({girdiler:trafikGirdi()})})).json();
    if(sira !== ISTEK.trafik) return;          // daha yeni bir istek var — bu yanıt eski
    SON.c=r; SON.t=r; ciz('c_sonuc', r, r.yol||'tek'); kapakYerTutuculari();
    const _kopru = trafikKoprusu();
    if(_kopru) AVAN_TABAN = _kopru.asansorler.length;   // son bilinen grup adedi
    sekmeRozeti('trafik', !!r.hata, (r.uyarilar||[]).length);
    const rz=$('c_std_rozet');
    if(rz) rz.innerHTML = r.ozet && r.ozet.standart
      ? `<span class="rozet ${r.ozet.standart==='Yükseltilmiş'?'sari':'ok'}">Hesap standardı: ${r.ozet.standart}</span>` : '';
  }catch(e){ $('c_sonuc').innerHTML=`<div class="kart-ic"><div class="uyari kirmizi">Bağlantı hatası: ${kacis(e)}</div></div>`; }
}
async function hesapAvan(){
  const sira = ++ISTEK.avan;
  try{
    const r = await (await fetch('/api/avan',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({girdiler:avanGirdi()})})).json();
    if(sira !== ISTEK.avan) return;            // daha yeni bir istek var — bu yanıt eski
    SON.a=r; cizAvan(r); turetilenGoster(r); seritGoster(r); kapakYerTutuculari();
    sekmeRozeti('avan', !!r.hata, (r.uyarilar||[]).length);
  }catch(e){ $('a_sonuc').innerHTML=`<div class="kart-ic"><div class="uyari kirmizi">Bağlantı hatası: ${kacis(e)}</div></div>`; }
}

/* "ℹ" ile başlayan iletiler UYARI değil NOT'tur — mavi kutuda gösterilir. */
function uyariSinifi(u){ return String(u||'').trim().startsWith('ℹ') ? 'mavi' : 'sari'; }

/* ---------------------------------------------------------- çizim: trafik */
function ciz(hedef, r, mod){
  const o=r.ozet||{};
  let h=`<div class="pafta-bas"><h2>ASANSÖR TRAFİK HESABI${mod==='coklu'?'  —  ÇOKLU ASANSÖR':''}</h2>
         <div class="alt">MMO/697, 2. Baskı, Ocak 2020, s.11-17</div></div><div class="kart-ic">`;
  /*  Hangi yolun kullanıldığı SESSİZ kalmasın:  kullanıcı yöntemi seçmiyor,
      o hâlde ne seçildiğini görmeli. */
  if(!r.hata && r.yol){
    const ayni = r.yol!=='coklu';
    h += `<div class="uyari mavi" style="margin:0 0 10px">
      ${ayni ? 'Asansörlerin hepsi <b>aynı tip</b> — MMO/697 s.11-12 yolu.'
             : 'Asansörler <b>farklı tipte</b> — grup formülü ( MMO/697 s.12 ).'}</div>`;
  }
  if(r.hata) h+=`<div class="uyari kirmizi">${kacis(r.hata)}</div>`;
  (r.uyarilar||[]).forEach(u=>h+=`<div class="uyari ${uyariSinifi(u)}">${kacis(u)}</div>`);

  if(!r.hata){
    h+='<div class="olcut">';
    if(mod==='coklu'){
      const okR = o.Res>=o.gereken, okT = o.TRes<=o.Izul;
      h+=kutu('Asansör adedi', o.adet, 'adet')
       + kutu('Reş / B·k', tr(o.Res,1)+' / '+tr(o.gereken,1), 'kişi / 5 dk', okR?'ok':'hata')
       + kutu('Bekleme TReş', tr(o.TRes,1), 'sn  ·  sınır '+trn(o.Izul,0)+' sn', okT?'ok':'hata')
       + kutu('Tasarım nüfusu B', trn(o.B,0), 'kişi')
       + kutu('Taşınacak yüzde k', '%'+tr((o.k||0)*100,1), 'Tablo-9');
    }else{
      /*  Taahhütname adedi belirlediyse ölçüt şartlı kabul sınırıdır;
          Standart / Yükseltilmiş için gereken adet yine yazılır. */
      const tah = !!o.taahhutname;
      const sinir = tah ? o.esik_sartli : o.Izul;
      const ok = o.Ieer<=sinir;
      /*  Tanımlanan adet ile GEREKLİ adet ayrı gösterilir: kullanıcı
          fazla ya da eksik koyduğunu görsün.  Eşitse tek satır yeter. */
      const gerekli = o.adet_hesap;
      h+=kutu('Asansör adedi', o.adet, tah
               ? `adet  ·  taahhütname ile  ( ${o.standart} için ${trn(gerekli,0)} )`
               : (gerekli!=null && gerekli!==o.adet)
               ? `adet  ·  gerekli ${trn(gerekli,0)}` : 'adet  ·  '+trn(o.P,0)+' kişilik',
               (!tah && gerekli!=null && o.adet<gerekli) ? 'hata' : '')
       + kutu('Bekleme Ieer', tr(o.Ieer,1), 'sn  ·  '+(tah?'şartlı sınır ':'sınır ')+trn(sinir,0)+' sn', ok?'ok':'hata')
       + kutu('Kabin hızı V', tr(o.V), 'm/s')
       + kutu('Tur süresi TR', tr(o.TR,1), 'sn')
       + kutu('5 dk taşıma R', tr(o.R,1), 'kişi')
       + kutu('Tasarım nüfusu B', trn(o.B,0), 'kişi');
    }
    h+='</div>';
  }
  (r.bolumler||[]).forEach(b=>h+=bolumCiz(b));

  if(mod==='coklu' && r.asansorler && r.asansorler.length) h+=cokluTablo(r.asansorler);
  if(r.nufus && r.nufus.length) h+=nufusTablo(r.nufus, o.b);

  if(o.sonuc){
    const kotu = /^(Kabul|YETERSİZ|HESAP)/.test(o.sonuc);
    h+=`<div class="sonuc-kutu ${kotu?'hata':'ok'}"><span class="et">SONUÇ</span><span>${kacis(o.sonuc)}</span></div>`;
    /*  NİHAİ CEVAP ve DAYANAĞI  —  paftadaki karar kutusunun ekran karşılığı.
        Hangi ölçütün hangi sayıyla sağlandığı sonucun yanında durur; bölüm
        dip notu olarak ayrı yerde aranmaz. */
    const c = o.sonuc_cumlesi||o.pafta_satiri;
    const olc = o.karar_olcutleri||[];
    if((c && c!==o.sonuc) || olc.length){
      h+=`<div class="karar-kutu ${kotu?'hata':'ok'}">`;
      if(c && c!==o.sonuc) h+=`<div class="karar-metin">${kacis(c)}</div>`;
      if(olc.length) h+=`<div class="karar-olcut">` + olc.map(x=>
        `<div><span class="im ${x.uygun?'ok':'hata'}">${x.uygun?'✔':'✘'}</span>
         <b>${kacis(x.ad)}</b><span>${kacis(x.metin)}</span></div>`).join('') + `</div>`;
      h+=`</div>`;
    }
    /* Tek asansör hesabı "n adet gerekir" diyorsa, o n asansörü tek tıkla
       tanımlamaya geçiş — kullanıcı adedi elle değiştirmek zorunda kalmasın. */
    if(mod!=='coklu' && o.adet>1 && o.adet<=4 && !r.hata){
      h+=`<div class="dugmeler" style="margin-top:10px">
        <button class="dg ana" onclick="trafikAdedi(${o.adet})">
          → ${o.adet} asansör olarak tanımla ve grubu kontrol et</button></div>
        <div class="notlar" style="margin-top:6px"><div>Aynı tipte ${o.adet} asansör
        kolonlara kopyalanır; farklı kapasitede olacaksa kolonları düzeltebilirsiniz.</div></div>`;
    } else if(mod!=='coklu' && o.adet>4 && !r.hata){
      h+=`<div class="uyari sari" style="margin-top:10px">Hesap ${trn(o.adet,0)} adet asansör
        gerektiriyor; program en çok 4 asansörlü grubu kontrol eder. Daha büyük gruplarda
        bölgeli (zoned) trafik hesabı yapılmalıdır.</div>`;
    }
  }
  if(r.oneriler && r.oneriler.length) h+=oneriTablo(r.oneriler);
  $(hedef).innerHTML = h+'</div>';
}

function cokluTablo(as){
  const S=[['P — Kabin kapasitesi (kişi)',a=>trn(a.P,0)],['Beyan yükü (kg)',a=>trn(a.yuk_kg,0)],
    ['Kapı genişliği (mm) / tipi',a=>trn(a.kapi_genisligi,0)+' / '+(a.kapi_tipi||'')],
    ['Durak adedi (ana giriş dâhil)',a=>trn(a.durak,0)],['V — Kabin hızı (m/s)',a=>tr(a.V)],
    ['h — Katlar arası mesafe (m)',a=>tr(a.h)],['p = 0,8·P',a=>tr(a.p,1)],
    ['H — Ort. en yüksek dönüş katı',a=>tr(a.H,4)],['S — Ortalama durak adedi',a=>tr(a.S,4)],
    ['ta / tk  (s)',a=>tr(a.ta,1)+' / '+tr(a.tk,1)],['tg / tp  (s)',a=>tr(a.tg,1)+' / '+tr(a.tp,1)],
    ['tv = h / V  (s)',a=>tr(a.tv,3)],['ts = ta+tk+tg−tv  (s)',a=>tr(a.ts,3)],
    ['TR = 2·H·tv+(S+1)·ts+2·p·tp  (s)',a=>tr(a.TR,2)],['R = 5·60·p / TR  (kişi/5dk)',a=>tr(a.R,2)]];
  let h=`<div class="serit"><span>ASANSÖR BAZINDA HESAP</span><span class="kaynak">MMO/697 s.11-12</span></div>
         <div class="kaydir"><table class="veri"><tr><th>Büyüklük</th>`+
         as.map(a=>`<th style="text-align:right">${kacis(a.ad)}</th>`).join('')+'</tr>';
  S.forEach(([et,fn])=>{ h+=`<tr><td class="etiket">${kacis(et)}</td>`+
    as.map(a=>`<td class="sag">${kacis(fn(a))}</td>`).join('')+'</tr>'; });
  return h+'</table></div>';
}
function nufusTablo(n,b){
  let h=`<div class="serit"><span>NÜFUSUN AYRINTISI  ( b = Σc )</span><span class="kaynak">MMO/697 Tablo-1</span></div>
    <div class="kaydir"><table class="veri"><tr><th>Grup / açıklama</th><th style="text-align:right">Miktar</th>
    <th>Tablo-1 kalemi</th><th>Birim</th><th style="text-align:right">Katsayı</th><th style="text-align:right">c (kişi)</th></tr>`;
  n.forEach(s=>h+=`<tr><td>${kacis(s.aciklama)}</td><td class="sag">${trn(s.miktar,2)}</td>
    <td>${kacis(s.kalem)}</td><td>${kacis(s.birim)}</td><td class="sag">${trn(s.katsayi,4)}</td>
    <td class="sag">${trn(s.c,2)}</td></tr>`);
  return h+`<tr class="toplam"><td colspan="5">TOPLAM  b = Σc</td><td class="sag">${trn(b,2)}</td></tr></table></div>`;
}
function oneriTablo(o){
  let h=`<div class="serit"><span>OTOMATİK ÖNERİ — hangi kabin ve hız kaç asansör gerektirir?`
    + bilgiSimgesi([`TS EN 81-70 / TS 9111 erişilebilirlik ölçütünü karşılamayan seçenekler ( 630 kg altı kabin ya da 800 mm altı net kapı ) satırda işaretlenir ve öneri sıralamasına alınmaz; hesaptan çıkarılmaz.`,`Her satırda kapasiteye uygun kapı genişliği varsayılır — ISO 8100-32:2020 Ek C, Tablo 8.`,`Bu blok bilgi amaçlıdır; kesin hesap sizin ⑧ / ⑨ / ⑩ girdilerinizle yapılır.`]) + `</span>
    <span class="kaynak">bilgi amaçlıdır</span></div><div class="kaydir"><table class="veri">
    <tr><th>Seçenek (kabin — hız)</th><th style="text-align:right">Adet</th><th style="text-align:right">Bekleme (sn)</th>
    <th>Sınıf</th><th style="text-align:right">TR (sn)</th><th style="text-align:right">R</th></tr>`;
  o.forEach(s=>h+=`<tr class="${s.onerilen?'onerilen':''}"><td>${kacis(s.secenek)}${s.onerilen?' &nbsp;<span class="rozet ok">ÖNERİLEN</span>':''}</td>
    <td class="sag">${s.adet}</td><td class="sag">${tr(s.Ieer,1)}</td><td>${kacis(s.sinif)}</td>
    <td class="sag">${tr(s.TR,1)}</td><td class="sag">${tr(s.R,1)}</td></tr>`);
  return h+`</table></div>`;
}

/* ---------------------------------------------------------- çizim: avan */
function cizAvan(r){
  let h=`<div class="pafta-bas"><h2>ASANSÖR AVAN PROJE HESAPLARI</h2>
    <div class="alt">MMO/697, 2. Baskı, Ocak 2020, s.18-21  ·  TS EN 81-20</div></div><div class="kart-ic">`;
  /* Uyarılar PDF'te basılıyordu ama ekranda görünmüyordu; trafik ↔ avan
     tutarsızlığı da buradan bildirilir. */
  (r.uyarilar||[]).forEach(u=>h+=`<div class="uyari ${uyariSinifi(u)}">${kacis(u)}</div>`);
  if(r.hata){ $('a_sonuc').innerHTML=h+`<div class="uyari kirmizi">${kacis(r.hata)}</div></div>`; return; }
  const aktif=(r.asansorler||[]).filter(a=>a.aktif);
  if(!aktif.length){
    $('a_sonuc').innerHTML = h+`<div class="bos">Henüz asansör tanımlanmadı.<br>
      Trafik hesabını yapın — asansör adedi, kapasite ve hız buraya kendiliğinden gelir.</div></div>`;
    (r.asansorler||[]).forEach(a=>{}); return;
  }
  const oz=r.ozet||{};
  h+='<div class="olcut">'
    + kutu('Tanımlı asansör', aktif.length, 'adet')
    + kutu('Tesisin kurulu gücü', trn(oz.tesis_kurulu_guc,0), 'W')
    + (oz.Re!=null ? kutu('Re — Topraklama', tr(oz.Re,3), 'Ω', oz.topraklama_uygun?'ok':'hata') : '')
    + '</div>';

  /* özet tablo */
  const S=[['Asansör tanımı',o=>o.tanim||'—'],['P — Kabin kapasitesi (kişi)',o=>trn(o.kapasite,0)],
    ['Q — Anma yükü (kg)',o=>trn(o.Q,0)],['V — Kabin hızı (m/s)',o=>tr(o.V)],
    ['N — Hesaplanan motor gücü (kW)',o=>tr(o.N_hes)],['Nsç — Seçilen motor gücü (kW)',o=>tr(o.Nsc)],
    ['Kontrol  ( Nsç ≥ N )',o=>o.motor_uygun?'UYGUN':'UYGUN DEĞİL'],
    ['P1 — Kuyu alt boşluğu tabanına (N)',o=>trn(o.P1,0)],
    ['P2 — Karşı ağırlık tamponu altına (N)',o=>trn(o.P2,0)],
    ['PR — Bir kabin kılavuz rayına (N)',o=>trn(o.PR,0)],
    ['PK — Bir karşı ağırlık rayına (N)',o=>trn(o.PK,0)],
    ['Fs — Kuyu üstü betonuna (N)',o=>trn(o.Fs,0)],
    ['Kabin armatür sayısı (adet)',o=>trn(o.n_kabin,0)],['Kuyu armatür sayısı (adet)',o=>trn(o.n_kuyu,0)],
    ['P — Asansörün kurulu gücü (W)',o=>trn(o.P_kurulu,0)],
    ['ε — Toplam gerilim düşümü (%)',o=>tr(o.eps,3)],
    ['Kontrol  ( ε ≤ εmax )',o=>o.eps_uygun?'UYGUN':'UYGUN DEĞİL'],
    ['I — Hat akımı / Iz (A)',o=>tr(o.I,1)+' / '+trn(o.Iz,1)]];
  h+=`<div class="serit"><span>SONUÇ ÖZETİ</span><span class="kaynak">tüm asansörler</span></div>
      <div class="kaydir"><table class="veri"><tr><th>Büyüklük</th>`+
      aktif.map(a=>`<th style="text-align:right">${a.no} NOLU</th>`).join('')+'</tr>';
  S.forEach(([et,fn])=>{h+=`<tr><td class="etiket">${kacis(et)}</td>`+
    aktif.map(a=>`<td class="sag">${kacis(fn(a.ozet))}</td>`).join('')+'</tr>';});
  h+=`<tr class="toplam"><td>Tesisin toplam kurulu gücü (W)</td>
      <td class="sag" colspan="${aktif.length}">${trn(oz.tesis_kurulu_guc,0)}</td></tr>`;
  if(oz.Re!=null) h+=`<tr class="toplam"><td>Re — Temel topraklama direnci (Ω)</td>
      <td class="sag" colspan="${aktif.length}">${tr(oz.Re,3)}  —  ${oz.topraklama_uygun?'UYGUN':'UYGUN DEĞİL'}</td></tr>`;
  h+='</table></div>';

  /* uyarılar */
  (r.asansorler||[]).forEach(a=>{ if(!a.aktif && a.uyari && a.uyari.includes('TABLO-7'))
    h+=`<div class="uyari sari" style="margin-top:10px">${kacis(a.uyari)}</div>`; });

  /* her asansör */
  aktif.forEach(a=>{
    h+=`<div class="serit" style="margin-top:22px;background:#0E3357"><span>${kacis(a.baslik)}${a.tanim?'  —  '+kacis(a.tanim):''}</span>
        <span class="kaynak">AVAN PROJE HESAPLARI</span></div>`;
    a.bolumler.forEach(b=>h+=bolumCiz(b));
  });

  /* makine dairesi
     MRL ( makine dairesiz ) sistemde bu bölüm HİÇ GÖSTERİLMEZ — makine dairesi
     yoksa aydınlatma hesabının konusu da yoktur.  Ekran ile pafta aynı kuralı
     uygular ( bkz. pdf_export.avan_pdf ).
     Tek istisna EKSİK GİRDİ:  MRL kutusu işaretli değil ama A × B ölçüsü de
     girilmemişse bu bir tercih değil unutulmuş bir girdidir — kırmızı uyarı
     basılır, yoksa eksik hesap sessizce gizlenmiş olurdu. */
  const mk=r.makine_dairesi||{};
  if(mk.aktif || mk.mk_yok === false){
    h+=`<div class="serit" style="margin-top:22px;background:#0E3357"><span>MAKİNE DAİRESİ AYDINLATMASI</span>
        <span class="kaynak">TS EN 81-20</span></div>`;
    h += mk.aktif ? bolumCiz(mk.bolum)
       : `<div class="uyari kirmizi" style="margin-top:8px">${kacis(mk.uyari||'')}</div>`;
  }

  /* topraklama */
  const tp=r.topraklama||{};
  h+=`<div class="serit" style="margin-top:22px;background:#0E3357"><span>TEMEL TOPRAKLAMA HESABI</span>
      <span class="kaynak">Temel ( ızgara ) + paralel çubuk</span></div>`;
  if(tp.aktif) tp.bolumler.forEach(b=>h+=bolumCiz(b));
  else h+=`<div class="uyari kirmizi" style="margin-top:8px">${kacis(tp.uyari||'')}</div>`;

  $('a_sonuc').innerHTML = h+'</div>';
}

/* ---------------------------------------------------------- dinamik formlar */
function cokluAsansorleriKur(){
  let h='';
  for(let i=1;i<=4;i++){
    h+=`<div class="as-kutu" id="c_kutu${i}">
      <div class="as-bas">ASANSÖR-${i}</div>
      <div class="as-ic">
        <div class="satir i2">
          <div class="alan"><label>⑧ Kapasite P (kişi)</label><select id="c_P${i}" class="girdi">
            <option value="">— seçilmedi —</option>
            ${SEC.kapasiteler.map(p=>`<option value="${p}">${p} kişi — ${SEC.tablo_7[p]||p*75} kg</option>`).join('')}</select></div>
          <div class="alan"><label>⑨ Kapı genişliği (mm)</label><select id="c_kg${i}" class="girdi">
            ${SEC.kapi_genislikleri.map(k=>`<option value="${k}"${k===900?' selected':''}>${k}</option>`).join('')}</select></div>
        </div>
        <div class="alan"><label>⑩ Kapı tipi</label><select id="c_kt${i}" class="girdi">
          ${SEC.kapi_tipleri.map(k=>`<option value="${k}">${k}</option>`).join('')}</select></div>
        <div class="satir i3">
          <div class="alan"><label>V (m/s) <span class="ipucu">boş = Tablo-2</span></label><select id="c_V${i}" class="girdi">
            <option value="">Tablo-2 min</option>${SEC.hizlar.map(x=>`<option value="${x}">${tr(x)}</option>`).join('')}</select></div>
          <div class="alan"><label>Durak <span class="ipucu">boş = N+1</span></label><input id="c_durak${i}" class="girdi"></div>
          <div class="alan"><label>h (m) <span class="ipucu">boş = ortak</span></label><input id="c_h${i}" class="girdi"></div>
        </div>
        <div class="bolum-bas katla kapali" onclick="katla(this,'c_ileri${i}')">İleri seçenekler
          <span class="ipucu">— bodrum ve imalatçı süreleri</span></div>
        <div id="c_ileri${i}" style="display:none">
          <div class="alan"><label>Bodrum durağı <span class="ipucu">(ana giriş altı) boş = ortak</span>
            ${bilgiSimgesi(['Bu asansörün ana giriş altında hizmet verdiği durak adedi. Boş bırakırsanız ortak değer (⑪) kullanılır.','Bodrum durağı H (Tablo-3) ve S (Tablo-5) değerlerini değiştirmez; yalnız bu asansörün Tablo-2 asgari hızındaki durak adedine ve seyahat mesafesine girer.'])}</label>
            <input id="c_bodrum${i}" class="girdi"></div>
          <div class="satir i4">
            <div class="alan"><label>ta (s) ${bilgiSimgesi(['İmalatçı katalog değeri girilirse MMO Tablo-4 / Tablo-6 / ISO Tablo 6 değerinin yerine bu kullanılır.','Manuel süre girildiğinde paftada marka-model ve teknik föy referansı belirtilmelidir — program bunu uyarı olarak hatırlatır.'])}</label><input id="c_mta${i}" class="girdi" placeholder="T-4"></div>
            <div class="alan"><label>tk (s)</label><input id="c_mtk${i}" class="girdi" placeholder="T-4"></div>
            <div class="alan"><label>tg (s)</label><input id="c_mtg${i}" class="girdi" placeholder="T-6"></div>
            <div class="alan"><label>tp (s)</label><input id="c_mtp${i}" class="girdi" placeholder="T-8"></div>
          </div>
        </div>
      </div></div>`;
  }
  $('c_asansorler').innerHTML=h;
}

function avanAsansorleriKur(){
  let h='';
  const kesitOpt = () => SEC.kesitler.map(x=>`<option value="${x}">${tr(x,1)} mm²</option>`).join('');
  for(let i=1;i<=4;i++){
    /*  "kullan" kutusu artık ADETTEN türetilir — kullanıcı tek tek işaretlemez.
        Kutu gizli olarak durur; avanGirdi() ve geri yükleme onu kullanır. */
    h+=`<div class="as-kutu ${i>2?'pasif':''}" id="a_kutu${i}">
      <div class="as-bas">
        <span>${i} NOLU ASANSÖR</span>
        <span class="as-etiket" id="a_etiket${i}"></span>
        <input type="checkbox" id="a_aktif${i}" ${i<=2?'checked':''} hidden></div>
      <div class="as-ic">
        <div class="alan"><label>Asansör tanımı</label><input id="a_tanim${i}" class="girdi" placeholder="İnsan / Sedye + Yük"></div>
        <div class="satir i2">
          <div class="alan"><label>P — Kapasite (kişi) <span class="ipucu">trafikten</span></label>
            <select id="a_kapasite${i}" class="girdi"><option value="">—</option>
            ${SEC.kapasiteler.map(p=>`<option value="${p}">${p} kişi — ${SEC.tablo_7[p]||p*75} kg</option>`).join('')}</select></div>
          <div class="alan"><label>Q — Anma yükü (kg) <span class="ipucu">kapasiteden</span>
            ${bilgiSimgesi(['Soldaki kapasiteyi seçince MMO/697 Tablo-7\'deki anma yükü kendiliğinden gelir — burası girdi değildir, elle doldurulmaz.','Tablo-7 dışında bir anma yükü gerekiyorsa ( ör. özel bir yük asansörü ) "Ofis standardından farklı değerler" bölümündeki Q elle alanına yazın; o zaman bu satır girilen değeri gösterir.'])}</label>
            <input id="a_Q_goster${i}" class="girdi salt" readonly tabindex="-1" aria-readonly="true"></div>
        </div>
        <div class="satir i2">
          <div class="alan"><label>V — Kabin hızı (m/s) <span class="ipucu">trafikten</span></label>
            <select id="a_V${i}" class="girdi"><option value="">—</option>
            ${SEC.hizlar.map(x=>`<option value="${x}">${tr(x)}</option>`).join('')}</select></div>
          <div class="alan"><label>Makine tipi</label>
            <select id="a_makine_tipi${i}" class="girdi" onchange="verimTazele(${i});planla()">
              ${Object.keys(SEC.makine_tipleri||{}).map(k=>`<option value="${k}">${k}</option>`).join('')}
            </select></div>
        </div>
        <div class="satir i2">
          <div class="alan"><label>i — Askı ( palanga ) oranı
            ${bilgiSimgesi(['Doğrudan askı 1:1 / palangalı 2:1. Asansörün kendi özelliğidir — kapasite ve hız gibi burada girilir.','Palangalı ( 2:1 ) sistemde motor gücü hesabında verim 0,10 düşük alınır: η′ = η − 0,10 ( MMO/697 §2.4 ). 1:1 askıda verim olduğu gibi kullanılır.'])}</label>
            <select id="a_i_palanga${i}" class="girdi" onchange="verimTazele(${i});planla()">
              ${Object.keys(SEC.aski_oranlari||{}).map(k=>
                `<option value="${SEC.aski_oranlari[k]}"${SEC.aski_oranlari[k]===2?' selected':''}>${k}</option>`).join('')}
            </select></div>
          <div class="alan"><label>η — Makine verimi
            ${bilgiSimgesi(['MMO/697 s.21\'deki η: makinenin verimi, askı ( palanga ) kaybı HARİÇ. Ofis kabulü: dişlisiz 0,85 · dişli 0,50 — makine tipini seçince kendiliğinden dolar, üzerine yazabilirsiniz.','Palangalı ( 2:1 ) sistemde program kitabın gereğini kendisi uygular: η′ = η − 0,10. Buraya düşülmemiş değeri girin.','İmalatçı kataloğundan alınmalı; paftada marka-model referansı belirtilmelidir.'])}</label>
            <input id="a_eta${i}" class="girdi" value="0,85"></div>
        </div>
        <div class="bolum-bas">Boyutlar</div>
        <div class="satir i2">
          <div class="alan"><label>Hk — Kuyu yüksekliği (m)</label><input id="a_Hk${i}" class="girdi"></div>
          <div class="alan"><label>Kuyu genişliği (mm)</label><input id="a_kuyu_genisligi${i}" class="girdi"></div>
        </div>
        <div class="satir i2">
          <div class="alan"><label>Kabin boyu a (mm)</label><input id="a_kabin_boyu${i}" class="girdi"></div>
          <div class="alan"><label>Kabin genişliği b (mm)</label><input id="a_kabin_genisligi${i}" class="girdi"></div>
        </div>
        <div class="bolum-bas">Ağırlık ve motor</div>
        <div class="satir i2">
          <div class="alan"><label>Gk — Boş kabin kütlesi (kg) <span class="ipucu">Tablo-11'den</span>
            ${bilgiSimgesi(['Anma yüküne göre MMO/697 Tablo-11\'den gelir; ara yükler doğrusal enterpolasyonla bulunur.','İmalatçı verisi varsa "Ofis standardından farklı değerler" bölümündeki Gk elle alanına yazın.'])}</label>
            <input id="a_Gk_goster${i}" class="girdi salt" readonly tabindex="-1" aria-readonly="true"></div>
          <div class="alan"><label>Nsç — Motor gücü (kW) <span class="ipucu">boş = otomatik</span>
            ${bilgiSimgesi(['Boş bırakılırsa hesaplanan motor gücünden büyük ilk STANDART anma gücü seçilir ( IEC 60072 / TS EN 60034 kademeleri: 2,2 · 3 · 4 · 5,5 · 7,5 · 11 · 15 · 18,5 · 22 · 30 · 37 · 45 kW ).','İmalatçının kademesi farklıysa buraya elle yazın; program yine Nsç ≥ N kontrolünü yapar ve uymuyorsa uyarır.'])}</label>
            <input id="a_Nsc${i}" class="girdi" placeholder="otomatik"></div>
        </div>
        <div class="satir i2">
          <div class="alan"><label>Denge zinciri
            ${bilgiSimgesi(['Askı halatlarının ağırlığını dengeleyen zincir ya da halat. Hızlı ve yüksek binalarda kullanılır ( 3 m/s üstünde halat zorunludur, TS EN 81-20 m.5.5.6.1 ).','Var seçilirse zincirin kütlesi kabin tarafı kütlesine ( P ) eklenir ve tampon, ray ve kuyu üstü kuvvetleri buna göre büyür ( MMO/697 s.20 P tanımı ).','Kütlesi ofis kabulüdür ( Sabitler · zincir = halat ağırlığı ); ağır bir asansörde "Ofis standardından farklı değerler" bölümünden girilir.'])}</label>
            <select id="a_denge_zinciri${i}" class="girdi" onchange="avanKartlariGoster()"><option value="Yok">Yok</option><option value="Var">Var</option></select></div>
          <div class="alan"><label>Karşı ağırlıkta güvenlik tertibatı
            ${bilgiSimgesi(['Karşı ağırlıkta güvenlik tertibatı yalnız kuyunun altında insanların girebileceği bir boşluk varsa gerekir.','Yok ise karşı ağırlık rayına yalnız rayın kendi ağırlığı gelir ( k1 = 0, MMO/697 s.20 ); kitabın çözümlü örnekleri de böyle hesaplar.'])}</label>
            <select id="a_agirlik_guvenlik_tertibati${i}" class="girdi"><option value="Yok">Yok</option><option value="Var">Var</option></select></div>
        </div>
        <div class="bolum-bas katla kapali" onclick="katla(this,'a_ozel${i}')">Ofis standardından farklı değerler
          <span class="ipucu">— boş = ofis standardı</span><span class="ozel-rozet" id="a_ozel_rozet${i}"></span></div>
        <div id="a_ozel${i}" style="display:none">
          <div class="uyari mavi" style="margin:0 0 10px">Bu alanlar <b>boş bırakıldığında</b>
            Sabitler sekmesindeki <b>ofis standardı</b> kullanılır. Yalnız bu asansörde
            farklı bir değer gerekiyorsa doldurun.</div>
          <div class="satir i2">
            <div class="alan"><label>Q elle (kg) <span class="ipucu">yalnız Tablo-7 dışı</span>
              ${bilgiSimgesi(['Normalde BOŞ kalır: anma yükü kapasiteden ( Tablo-7 ) gelir.','Yalnız tabloda karşılığı olmayan bir yük gerekiyorsa doldurun. MMO/697 Tablo-11 kapsamı 450 - 2.500 kg\'dır; bunun dışında bir yük girerseniz boş kabin kütlesini de ( Gk elle ) vermeniz gerekir, program bunu uyarır.'])}</label>
              <input id="a_Q_elle${i}" class="girdi"></div>
            <div class="alan"><label>Gk elle (kg) <span class="ipucu">boş = Tablo-11</span></label><input id="a_Gk_elle${i}" class="girdi"></div>
          </div>
          <div class="satir i2">
            <div class="alan"><label>gr — Ray birim kütlesi (kg/m)</label><input id="a_gr${i}" class="girdi ofis-alan" data-ofis="gr"></div>
            <div class="alan"><label>Fmk — Makine ağırlığı (kg)</label><input id="a_Fmk${i}" class="girdi ofis-alan" data-ofis="Fmk"></div>
          </div>
          <div class="satir i2">
            <div class="alan"><label>Fsh — Sehpa ağırlığı (kg)</label><input id="a_Fsh${i}" class="girdi ofis-alan" data-ofis="Fsh"></div>
            <div class="alan"><label>q — Denge faktörü <span class="ipucu">0 – 1</span>
              ${bilgiSimgesi(['Karşı ağırlığın dengelediği anma yükü oranı; uygulamada 0,50 alınır.','Motor gücü N = (1−q)·Q·V / (102·η) ve karşı ağırlık Ga = P + q·Q bağıntılarına girer.','Boş bırakırsanız Sabitler / Ofis Standardı sekmesindeki değer kullanılır.'])}</label>
              <input id="a_q_denge${i}" class="girdi" placeholder="Sabitler B"></div>
          </div>
          <div class="satir i2">
            <div class="alan"><label>S1 — Kolon hattı kesiti</label>
              <select id="a_S1${i}" class="girdi ofis-alan" data-ofis="S1"><option value="">ofis standardı</option>${kesitOpt()}</select></div>
            <div class="alan"><label>L1 — Kolon hattı uzunluğu (m) <span class="ipucu">elektrik</span>
              ${bilgiSimgesi(['Boş bırakılırsa L1 = kuyu yüksekliği ( Hk ) + Sabitler sekmesindeki yatay güzergâh payı kullanılır — ana pano → kuyu → asansör panosu yatay kablo yolu ve bağlantı payı.','Plandan ölçtüğünüz değer farklıysa buraya yazın.'])}</label>
              <input id="a_L1${i}" class="girdi" placeholder="Hk + pay"></div>
          </div>
          <div class="satir i2">
            <div class="alan"><label>S2 — Makine besleme kesiti</label>
              <select id="a_S2${i}" class="girdi ofis-alan" data-ofis="S2"><option value="">ofis standardı</option>${kesitOpt()}</select></div>
            <div class="alan"><label>L2 — Makine besleme uzunluğu (m)</label><input id="a_L2${i}" class="girdi ofis-alan" data-ofis="L2"></div>
          </div>
          <div class="alan"><label>Kablo tipi <span class="ipucu">metne yazılır</span></label><input id="a_kablo_tipi${i}" class="girdi ofis-alan" data-ofis="kablo_tipi"></div>
          <div class="alan"><label>mz — Denge zinciri birim kütlesi (kg/m) <span class="ipucu">yalnız zincir Var ise</span>
            ${bilgiSimgesi(['Kabinin 1 m hareketine düşen zincir kütlesi — zincir halat ağırlığını dengeler, yaklaşık halat adedi × halat 1 m kütlesi × askı oranı.','Boş bırakılırsa Sabitler\'deki ofis kabulü ( 7 × Ø6,5 mm · 2:1 ) kullanılır. Ağır asansörde ( ör. 9 × Ø10 · 2:1 ≈ 6,1 kg/m ) buraya yazın.'])}</label>
            <input id="a_zincir_birim_kutle${i}" class="girdi ofis-alan" data-ofis="zincir_birim_kutle"></div>
        </div>
      </div></div>`;
  }
  $('a_asansorler').innerHTML=h;
}

/* Makine tipi seçilince η'yı MMO/697 s.21 değeriyle doldurur.
   Kullanıcı elle bir değer yazdıysa ona dokunmaz — yalnız hâlâ bir MMO
   değeri duruyorsa günceller, böylece "dişli seçtim ama 0,85 kaldı" olmaz. */
function verimTazele(i){
  const tip=$('a_makine_tipi'+i), alan=$('a_eta'+i);
  if(!tip||!alan) return;
  const tablo=SEC.makine_tipleri||{};
  const yeni=tablo[tip.value];
  if(yeni===undefined) return;
  const simdiki=parseFloat(String(alan.value).replace(',','.'));
  const mmoDegerleri=Object.values(tablo);
  const dokunulmamis = !isFinite(simdiki)
    || mmoDegerleri.some(x=>Math.abs(x-simdiki)<1e-9);
  if(dokunulmamis) alan.value=tr(yeni);
}

/* MRL işaretliyken makine dairesi ölçüleri kapanır — 0 yazma alışkanlığı
   yerine açık bir tercih. */
function mkYokUygula(){
  const k=$('a_mk_yok'), kutu=$('a_mk_olculer');
  if(!k||!kutu) return;
  const yok=k.checked;
  kutu.classList.toggle('sonuk', yok);
  ['a_mk_uzunluk','a_mk_genislik'].forEach(id=>{
    const e=$(id); if(!e) return;
    e.disabled=yok;
    if(yok) e.value='0';
  });
}

/* ---------------------------------------------------------- aktarım
   Adet ve BOŞ alanlar kendiliğinden gelir ( avanSenkron ).  Bu düğme, elle
   girilmiş kapasite / hız değerlerini trafik hesabındakiyle ZORLA eşitler —
   yani "trafikte 10 kişi, avanda 13 kişi" uyarısının tek tıklık karşılığıdır.
   Trafik grubu DIŞINDAKİ asansörlere ( yük / sedye ) dokunmaz. */
function trafiktenAktar(){
  const k = trafikKoprusu();
  const liste = (k && Array.isArray(k.asansorler)) ? k.asansorler : [];
  if(!liste.length){ durum('Aktarılacak geçerli trafik hesabı yok', true); return; }
  const kaynak = k.tip==='coklu' ? 'asansör grubu trafik hesabı' : 'tek asansör trafik hesabı';
  const n = Math.min(avanTaban(), liste.length, 4);
  for(let i=1;i<=n;i++){
    const t=liste[i-1]||{};
    if(t.P!=null && t.P!=='') alanaYaz($('a_kapasite'+i), t.P);
    if(t.V!=null && t.V!=='') alanaYaz($('a_V'+i), t.V);
    delete AVAN_OTO[i];
  }
  avanSenkron();
  yaz(); planla();
  durum(`${n} asansörün kapasite ve hızı güncellendi — ${kaynak}`);
}

/* ---------------------------------------------------------- BÜTÜN PROJE — CAD
   Kapak, trafik ve avan girdilerinin ÜÇÜ BİRDEN gönderilir; sunucu her biri
   için paftayı üretip tek bir çizim dosyasına dizer.  Hesap burada YAPILMAZ —
   ekranda ne görünüyorsa CAD çıktısı da odur ( tek kaynak motordur ). */
async function indirProjeDwg(){
  const dg = $('dg_proje_dwg');
  const eskiYazi = dg ? dg.textContent : '';
  if(dg){ dg.disabled = true; dg.textContent = 'Çizim hazırlanıyor…'; }
  durum('Proje çizimi hazırlanıyor — bütün paftalar CAD varlığına çevriliyor…');
  try{
    const govde = {kapak: kapakCiktisi(),
                   girdiler: {trafik: trafikGirdi(), avan: avanGirdi()},
                   //  Paket teslim edilecek çıktıları TAŞIR;  proje dosyası
                   //  onu geri getirir.  İkisi aynı arşivde durmalı.
                   proje_dosyasi: projeGovdesi('avan')};
    const r = await fetch('/api/indir/proje-dwg', {method:'POST',
      headers:{'Content-Type':'application/json'}, body:JSON.stringify(govde)});
    const tur = r.headers.get('Content-Type')||'';
    if(tur.includes('application/json')){
      const h = await r.json();
      durum(h.hata || 'Çizim üretilemedi', true); alert(h.hata || 'Çizim üretilemedi'); return;
    }
    if(!r.ok) throw new Error('sunucu hatası '+r.status);
    const cd = r.headers.get('Content-Disposition')||'';
    let ad = 'Avan Projesi.zip'; const m = cd.match(/filename\*=UTF-8''(.+)$/);
    if(m) ad = decodeURIComponent(m[1]);
    const notlar = (r.headers.get('X-Avan-Not')||'').split(',');
    const sadeceDxf = notlar.includes('DXF'), tasti = notlar.includes('TASMA');
    const b = await r.blob(), u = URL.createObjectURL(b);
    const a = document.createElement('a'); a.href=u; a.download=ad;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(()=>URL.revokeObjectURL(u),3000);
    /*  DXF BİR EKSİKLİK DEĞİLDİR.  Çizim yalnız LINE + TEXT içerir; DWG'nin
        taşıyıp DXF'in taşıyamayacağı hiçbir şey yok ve AutoCAD DXF'i doğrudan
        açar.  Eski metin "bulunamadı" diye başlayıp kullanıcıya bir şey
        kaçırdığını düşündürüyordu. */
    const bicim = sadeceDxf
      ? '  —  ZIP içinde DXF var; AutoCAD birebir açar (DWG isterseniz açıp Farklı Kaydet demeniz yeterli).'
      : '  —  ZIP içinde hem DWG hem DXF var.';
    const uyarilar = [];
    if(tasti) uyarilar.push('pafta sayısı proje formatının çerçevesine sığmadı, '
              + 'alta taşan sayfalar var. Çizimi baskıya göndermeden kontrol edin.');
    if(uyarilar.length){
      const u = 'DİKKAT: ' + uyarilar.join('  —  ');
      durum('İndirildi: '+ad+bicim+'  '+u, true); alert(u);
    }else{
      durum('İndirildi: '+ad+bicim);
    }
  }catch(e){ durum('İndirme başarısız: '+e.message, true); }
  finally{ if(dg){ dg.disabled = false; dg.textContent = eskiYazi; } }
}

/*  KAPAĞIN HESAPTAN TÜREYEN ALANLARI  ( engine/avan/kapak.py )
    Boş bırakılan kutunun gri yer tutucusu hesabın değerini gösterir ve
    çıktıya O basılır:  ekranda görünen = kâğıda basılan.  Eskiden yer
    tutucular sabit örneklerdi ( "10 kişi", "7,5 kW" ) — dolu görünüp boş
    basılıyordu.  Hesap hatalıysa ya da yapılmadıysa yer tutucu boştur. */
const kapakTuretilenAlanlar = () => SEC.kapak_turetilen || [];
function kapakTuretilen(){
  const al = r => (r && !r.hata && r.kapak_bilgileri) || {};
  return {...al(SON.t), ...al(SON.a)};
}
function kapakYerTutuculari(){
  const d = kapakTuretilen();
  for(const k of kapakTuretilenAlanlar()){ const e = $('k_'+k); if(e) e.placeholder = d[k] || ''; }
}
/*  Çıktıya giden kapak:  yazılan değer, yoksa hesabın değeri.  Yalnız avan
    kapağı içindir — uygulama paketine giden kapak formu olduğu gibi gider. */
function kapakCiktisi(){
  const g = kapakGirdi(), d = kapakTuretilen();
  for(const k of kapakTuretilenAlanlar()) if(!g[k] && d[k]) g[k] = d[k];
  return g;
}

function kapakGirdi(){
  const al = id => ($(id)?.value || '').trim();
  return {
    project_title:al('k_project_title'), owner:al('k_owner'), usage:al('k_usage'),
    contractor:al('k_contractor'), contractor_tax:al('k_contractor_tax'),
    city:al('k_city'), district:al('k_district'), neighborhood:al('k_neighborhood'),
    area:al('k_area'), sheet_no:al('k_sheet_no'), island_no:al('k_island_no'), parcel_no:al('k_parcel_no'),
    block:al('k_block'), capacity:al('k_capacity'), speed:al('k_speed'), stops:al('k_stops'),
    travel:al('k_travel'), cabin_width:al('k_cabin_width'), cabin_depth:al('k_cabin_depth'),
    standard:al('k_standard'), elevator_class:al('k_elevator_class'), suspension:al('k_suspension'),
    elevator_count:al('k_elevator_count'), drive_type:al('k_drive_type'), rail_size:al('k_rail_size'),
    motor_power:al('k_motor_power'), scale:al('k_scale'),
    mech_tax:al('k_mech_tax'), mech_registry:al('k_mech_registry'), mech_surname:al('k_mech_surname'),
    mech_name:al('k_mech_name'), mech_chamber:al('k_mech_chamber'),
    elec_tax:al('k_elec_tax'), elec_registry:al('k_elec_registry'), elec_surname:al('k_elec_surname'),
    elec_name:al('k_elec_name'), elec_chamber:al('k_elec_chamber'),
    company_name:al('k_company_name'), company_tax:al('k_company_tax'),
    company_tax_office:al('k_company_tax_office'), company_address:al('k_company_address')
  };
}

/* ---------------------------------------------------------- tablolar sekmesi */
function tablolariKur(){
  const T=SEC;
  let h='';
  h+=`<div class="serit" style="margin-top:0"><span>TABLO-1 — Binada sürekli bulunan insan sayısı</span>
      <span class="kaynak">MMO/697 s.13</span></div><div class="kaydir"><table class="veri">
      <tr><th>Kalem</th><th>Birim</th><th style="text-align:right">Kişi katsayısı</th></tr>`;
  Object.entries(T.tablo_1).forEach(([k,x])=>{
    h+=`<tr><td class="etiket">${k}</td><td>${x.birim}</td><td class="sag">${trn(x.katsayi,4)}</td></tr>`; });
  h+='</table></div>';

  h+=`<div class="serit"><span>TABLO-2 — Kabin hızları (durak adedine göre asgari)</span><span class="kaynak">MMO/697 s.13</span></div>
      <div class="kaydir"><table class="veri"><tr><th>Bina tipi</th><th>Durak adedi</th><th>Hız (m/s)</th></tr>
      <tr><td rowspan="4" class="etiket">Konut</td><td>2 – 9</td><td>1,00</td></tr>
      <tr><td>10 – 14</td><td>1,60</td></tr><tr><td>15 – 19</td><td>2,00</td></tr><tr><td>20 ve üzeri</td><td>≥ 2,50</td></tr>
      <tr><td rowspan="5" class="etiket">Büro ve İş Merkezi</td><td>2 – 5</td><td>1,00</td></tr>
      <tr><td>6 – 10</td><td>1,60</td></tr><tr><td>11 – 15</td><td>2,00</td></tr><tr><td>16 – 19</td><td>2,50</td></tr><tr><td>20 ve üzeri</td><td>&gt; 2,50</td></tr>
      <tr><td rowspan="5" class="etiket">Otel</td><td>2 – 6</td><td>1,00</td></tr>
      <tr><td>7 – 10</td><td>1,60</td></tr><tr><td>11 – 15</td><td>2,00</td></tr><tr><td>16 – 19</td><td>2,50</td></tr><tr><td>20 ve üzeri</td><td>&gt; 2,50</td></tr>
      </table></div>`;

  h+=`<div class="serit"><span>TABLO-3 / TABLO-5 — H ve S</span><span class="kaynak">MMO/697 s.14 ve s.16</span></div>
      <div class="notlar" style="margin-top:8px">
      <div><b>H = N − Σ(i/N)^P</b> &nbsp;(i = 1…N−1) &nbsp;—&nbsp; Ortalama en yüksek dönüş katı</div>
      <div><b>S = N · ( 1 − ((N−1)/N)^P )</b> &nbsp;—&nbsp; Ortalama durak adedi</div>
      <div>Kapsam: P = 6…34 kişi, N = 1…30 kat. Program bu kapalı formülleri kullanır; değerler
        MMO/697 tablolarıyla 10⁻¹³ mertebesinde örtüşür.</div></div>`;

  h+=`<div class="serit"><span>TABLO-4 — Kapı açılma (ta) ve kapanma (tk) zamanları</span><span class="kaynak">MMO/697 s.15</span></div>
      <div class="kaydir"><table class="veri"><tr><th>Kapı genişliği (mm)</th>`+
      T.kapi_tipleri.map(k=>`<th colspan="2" style="text-align:center">${k}</th>`).join('')+'</tr><tr><th></th>'+
      T.kapi_tipleri.map(()=>'<th style="text-align:right">ta (s)</th><th style="text-align:right">tk (s)</th>').join('')+'</tr>';
  Object.keys(T.tablo_4).sort((a,b)=>a-b).forEach(g=>{
    h+=`<tr><td class="etiket">${g}</td>`+T.kapi_tipleri.map(k=>{
      const p=T.tablo_4[g][k]||[null,null];
      return `<td class="sag">${p[0]==null?'—':tr(p[0],1)}</td><td class="sag">${p[1]==null?'—':tr(p[1],1)}</td>`;}).join('')+'</tr>';
  });
  h+='</table></div>'+
      `<div class="notlar"><div>1000 ve 1200 mm satırları MMO/697 Tablo-4'te <b>basılı değildir</b>;
      komşu satırlar arasında doğrusal enterpolasyonla türetilmiştir
      ( 1000 = (900+1100)/2 ,  1200 = (1100+1300)/2 ) ve paftada "ara değer" olarak yazılır.</div>
      <div>"Kabin İçi Oto. Kat K.Ç." sütunu 1300 mm'de tabloda yoktur; 1200 mm için de bu yüzden
      üretilememiştir — bu iki durumda imalatçı ta/tk değeri elle girilmelidir.</div></div>`;

  h+=`<div class="serit"><span>TABLO-6 — Tek katı geçme zamanı tg</span><span class="kaynak">MMO/697 s.17</span></div>
      <div class="kaydir"><table class="veri"><tr><th>V (m/s)</th><th>&lt; 1</th><th>1,00</th><th>1,60</th>
      <th>1,75*</th><th>2,00</th><th>2,50</th><th>3,00*</th><th>3,50</th><th>5,00</th><th>&gt; 5,00</th></tr>
      <tr><td class="etiket">tg (s)</td><td>10</td><td>7</td><td>6</td><td>5,8875</td><td>5,7</td><td>5,5</td>
      <td>5,25</td><td>5</td><td>4,5</td><td>4,3</td></tr></table></div>
      <div class="notlar"><div>* 1,75 ve 3,00 m/s MMO/697 Tablo-6 satır başlıklarında yoktur; komşu noktalar
      arasında doğrusal enterpolasyonla türetilmiştir ve paftada "ara değer" olarak yazılır.</div></div>`;

  h+=`<div class="serit"><span>TABLO-7 — Kabin kapasitesi / anma yükü</span><span class="kaynak">MMO/697 s.17</span></div>
      <div class="kaydir"><table class="veri"><tr><th>Kapasite (kişi)</th>`+
      Object.keys(T.tablo_7).map(p=>`<th style="text-align:right">${p}</th>`).join('')+'</tr>'+
      '<tr><td class="etiket">Anma yükü (kg)</td>'+Object.values(T.tablo_7).map(q=>`<td class="sag">${q}</td>`).join('')+'</tr></table></div>'+
      `<div class="notlar"><div>15 kişi / 1125 kg Tablo-7'de yer almaz; MMO/697'nin s.53-54 örnek projesinde
      kullanıldığı için program tarafından "örnek istisnası" olarak desteklenir.</div></div>`;

  h+=`<div class="serit"><span>TABLO-8 — Kişi transfer zamanı tp</span><span class="kaynak">ISO 8100-32:2020, Tablo 6</span></div>
      <div class="kaydir"><table class="veri"><tr><th>Kapı genişliği (mm)</th>`+
      Object.keys(T.tablo_8).map(g=>`<th style="text-align:right">${g}</th>`).join('')+'</tr>'+
      '<tr><td class="etiket">tp (s)</td>'+Object.values(T.tablo_8).map(x=>`<td class="sag">${tr(x,1)}</td>`).join('')+'</tr></table></div>'+
      `<div class="notlar"><div>tp, tek yolcunun kabine giriş <b>veya</b> çıkış süresidir; TR denkleminde
      <b>2·p·tp</b> olarak kullanılır.</div>
      <div>700 mm ISO 8100-32 tablosunda yoktur (tablo 800 mm'de başlar); 800→900 mm eğiminden
      dış değerleme ile <b>1,3 s</b> alınır — büyük tp, TR'yi büyüttüğü için emniyetli taraftır.
      İmalatçı verisi varsa manuel tp girin.</div></div>`;

  h+=`<div class="serit"><span>TABLO-9 — Taşınacak insan yüzdesi %k</span><span class="kaynak">MMO/697 s.17</span></div>
      <div class="kaydir"><table class="veri"><tr><th>Bina tipi</th><th style="text-align:right">Standart</th>
      <th style="text-align:right">Yükseltilmiş</th></tr>`;
  Object.entries(T.tablo_9).forEach(([k,x])=>h+=`<tr><td class="etiket">${k}</td>
    <td class="sag">% ${tr(x['Standart']*100,1)}</td><td class="sag">% ${tr(x['Yükseltilmiş']*100,1)}</td></tr>`);
  h+=`</table></div><div class="notlar"><div>Yüksek yapı ölçütü: bina yüksekliği &gt; 21,50 m <b>veya</b>
      yapı yüksekliği &gt; 30,50 m ise Yükseltilmiş seçilir (BYKHY md.4). Program bunu kendiliğinden yapar.</div></div>`;

  h+=`<div class="serit"><span>TABLO-10 — İzin verilen en fazla bekleme zamanı Izul</span><span class="kaynak">MMO/697 s.17</span></div>
      <div class="kaydir"><table class="veri"><tr><th>Sınıf</th><th style="text-align:right">Şartlı Kabul</th>
      <th style="text-align:right">Standart</th><th style="text-align:right">Yükseltilmiş</th>
      <th>Tablo-2 hız grubu</th><th>Tablo-9 %k tipi</th></tr>`;
  Object.entries(T.tablo_10).forEach(([k,x])=>h+=`<tr><td class="etiket">${k}</td>
    <td class="sag">${x.sartli??'—'}</td><td class="sag">${x.standart??'—'}</td><td class="sag">${x.yukseltilmis??'—'}</td>
    <td>${x.hiz_grubu||'<i>manuel gerekli</i>'}</td><td>${x.k_tipi||'<i>manuel gerekli</i>'}</td></tr>`);
  h+='</table></div>';

  h+=`<div class="serit"><span>TABLO-11 — Anma yüküne göre ortalama boş kabin kütlesi</span><span class="kaynak">avan hesapları</span></div>
      <div class="kaydir"><table class="veri"><tr><th style="text-align:right">Q (kg)</th>`+
      T.tablo_11.map(x=>`<th style="text-align:right">${x[0]}</th>`).join('')+'</tr>'+
      '<tr><td class="etiket">Gk (kg)</td>'+T.tablo_11.map(x=>`<td class="sag">${x[1]}</td>`).join('')+'</tr></table></div>'+
      `<div class="notlar"><div>Standart yolcu asansörü kabini için <b>ortalama</b> değerlerdir (kabin iskeleti,
      panel, tavan, zemin, kapı, süspansiyon ve paraşüt dâhil; mermer/granit kaplama ve özel dekor hariç).
      Ara yükler doğrusal enterpolasyonla bulunur. İmalatçı verisi varsa "Gk elle" alanına yazın.</div></div>`;

  h+=`<div class="serit"><span>KABLO AKIM TAŞIMA KAPASİTESİ</span>
      <span class="kaynak">IEC 60364-5-52 Tablo B.52.4 — bakır, PVC, 3 yüklü iletken, Yöntem C</span></div>
      <div class="kaydir"><table class="veri"><tr><th style="text-align:right">Kesit (mm²)</th>`+
      Object.keys(T.kablo_iz).map(k=>`<th style="text-align:right">${tr(Number(k),1)}</th>`).join('')+'</tr>'+
      '<tr><td class="etiket">Iz (A)</td>'+Object.values(T.kablo_iz).map(x=>`<td class="sag">${tr(x,1)}</td>`).join('')+'</tr></table></div>';

  $('tablolar_ic').innerHTML=h;
}



/* ═══════════════════════════════════════════════════════════════
   ORTAK DOSYADAN TAŞINANLAR
   Bunlar ortak.js'te duruyordu ama hiçbiri UYGULAMA projesini
   ilgilendirmiyor:  ek nüfus, trafik köprüsü, avanın ofis standardı
   formu, MMO/697 sabit tablosu, avan rozetleri, temel çevresi.
   Ortak dosyada durmaları "ortak" olduklarını sanmaya yol açıyordu.
   ═══════════════════════════════════════════════════════════════ */

/* ek nüfus satırları */
function ekNufusEkle(p, veri){
  const liste=$(p+'_eknufus_liste');
  const d=el('div','satir i3'); d.style.marginBottom='8px';
  d.innerHTML=`<div class="alan" style="margin:0"><input class="girdi en-ac" placeholder="Açıklama" value="${kacis(veri?.aciklama||'')}"></div>
    <div class="alan" style="margin:0"><input class="girdi en-mi" placeholder="Miktar" value="${kacis(veri?.miktar??'')}"></div>
    <div class="alan" style="margin:0;display:flex;gap:6px"><select class="girdi en-ka" style="flex:1">
      ${SEC.nufus_kalemleri.map(k=>`<option value="${k}"${veri?.kalem===k?' selected':''}>${k}</option>`).join('')}</select>
      <button class="dg kucuk" onclick="this.closest('.satir').remove();planla()">×</button></div>`;
  liste.appendChild(d);
  if(!veri) planla();
}

function ekNufusTopla(p){
  const kok = $(p+'_eknufus_liste');
  if(!kok) return [];                      //  tek gövde kalktı: 't' listesi yok
  return [...kok.querySelectorAll('.satir')].map(r=>({
    aciklama:r.querySelector('.en-ac').value, miktar:r.querySelector('.en-mi').value,
    kalem:r.querySelector('.en-ka').value })).filter(x=>x.miktar!=='');
}

/* Avan sekmesi trafik sonucuyla karşılaştırılır: kapasite / hız / kuyu
   yüksekliği tutarsızlığı uyarı olarak görünür.  Çoklu hesap varsa o,
   yoksa tek hesap esas alınır — aktarım düğmesiyle aynı öncelik. */
function trafikKoprusu(){
  const al = x => (x && !x.hata && x.avan_koprusu
                   && (x.avan_koprusu.asansorler||[]).length) ? x.avan_koprusu : null;
  /*  Tek hesap yolu kaldı — hangi yöntemin kullanıldığı sonucun içindedir. */
  return al(SON.c);
}

function sabitATablosu(){
  const ET={gn:['gn','Yerçekimi ivmesi','m/s²','MMO/697 s.18 — TS EN 81-20'],
    tampon_katsayi:['—','Tampon altı zemin kuvvet katsayısı','—','MMO/697 §2.3.3.1-2  F = 4·gn·(P+Q)'],
    k1_hizli:['k1','Darbe faktörü — V > 1,00 m/s','—','MMO/697 Çizelge-1'],
    k1_orta:['k1','Darbe faktörü — 0,63 < V ≤ 1,00 m/s','—','MMO/697 Çizelge-1'],
    k1_yavas:['k1','Darbe faktörü — 0,15 < V ≤ 0,63 m/s','—','MMO/697 Çizelge-1'],
    motor_sabiti:['—','Motor gücü denklem sabiti','kg·m/s','MMO/697 §2.4'],
    kirlenme_faktoru:['d','Aydınlatmada kirlenme (bakım) faktörü','—','Aydınlatma tekniği teamülü'],
    E_makine_dairesi:['E','Aydınlatma şiddeti — makine dairesi','lüx','TS EN 81-20'],
    E_kabin:['E','Aydınlatma şiddeti — kabin','lüx','TS EN 81-20'],
    E_kuyu:['E','Aydınlatma şiddeti — kuyu','lüx','TS EN 81-20'],
    kuyu_ek_armatur:['—','Kuyu aydınlatmasına eklenen armatür','adet','Kuyu dibi + kuyu üstü'],
    h_armatur:['h','Armatür ile çalışma düzlemi arası yükseklik — kabin · kuyu','m','Bölge indeksi k hesabında'],
    h_makine_dairesi:['h','Armatür ile döşeme arası yükseklik — makine dairesi','m','TS EN 81-20 m.5.2.1.4.2 · m.5.2.6.3.2.1'],
    ray_dusumu:['—','Ray uzunluğu düşümü','m','I = Hk − 0,20'],
    flexbil_sabiti:['—','Flexbil uzunluğu sabiti','m','Flexbil boyu = Hk / 2 + 3']};
  let h='<tr><th>Sembol</th><th>Büyüklük</th><th style="text-align:right">Değer</th><th>Birim</th><th>Kaynak</th></tr>';
  Object.entries(SEC.sabit_a).forEach(([k,val])=>{
    const [s,b,bi,kay]=ET[k]||[k,k,'',''];
    h+=`<tr><td><b>${s}</b></td><td>${b}</td><td class="sag">${trn(val,3)}</td><td>${bi}</td><td style="font-size:11px;color:#98A2AE">${kay}</td></tr>`;
  });
  $('sabit_a_tablo').innerHTML=h;
}

/* Katlanır "manuel değerler" bölümü kapalıyken de elle girilmiş bir değer
   olduğu görünsün — gizlenen bir ezme sessiz kalmamalı. */
function manuelRozet(){
  [['c_manuel_rozet', ['c_manuel_V','c_manuel_k']]].forEach(([rozet, alanlar])=>{
    const r=$(rozet); if(!r) return;
    const n = alanlar.filter(id=>v(id)!=='').length;
    r.textContent = n ? `${n} elle` : '';
    r.className = 'ozel-rozet' + (n ? ' dolu' : '');
  });
}

/* Asansör kartında ofis standardından SAPAN alan sayısı — katlanır bölüm
   kapalıyken de görünsün diye başlıkta rozet olarak yazılır. */
function ozelRozet(i){
  const r = $('a_ozel_rozet'+i); if(!r) return;
  const alanlar = ['Q_elle','Gk_elle','gr','Fmk','Fsh','S1','S2','L2',
                   'kablo_tipi','L1','q_denge','zincir_birim_kutle'];
  const n = alanlar.filter(k=>v('a_'+k+i)!=='').length;
  r.textContent = n ? `${n} özel` : '';
  r.className = 'ozel-rozet' + (n ? ' dolu' : '');
}

/* Temel çevresi — L ( şerit boyu ) için KARŞILAŞTIRMA bilgisi.
   Kural değildir: şeridin temelde nasıl dolaştığı projeye göre değişir,
   bazen çevreden kısa ( yalnız bir bölüm ), bazen enine bağlarla uzun olur.
   Yalnız "yazdığım sayı mantıklı mı" diye bakabilmek için gösterilir. */
function temelCevresi(){
  const e=$('a_temel_cevre'); if(!e) return;
  const a=sayiOku(v('a_temel_a')), b=sayiOku(v('a_temel_b'));
  e.textContent = (a>0 && b>0)
    ? `Karşılaştırma için: bu temelin çevresi 2·( ${tr(a)} + ${tr(b)} ) = ${tr(2*(a+b))} m.`
    : '';
}

/* Q ve Gk artık GİRDİ değil, TÜRETİLEN değerdir:
     Q  = kapasiteden ( Tablo-7 ),  Gk = anma yükünden ( Tablo-11 ).
   Ana kartta salt okunur gösterilir; tablo dışına çıkmak gerekirse
   katlanır bölümdeki "Q elle" / "Gk elle" alanları kullanılır ve bu
   satırlar o zaman GİRİLEN değeri gösterir — yani her zaman hesapta
   kullanılan değer görünür. */
function turetilenGoster(r){
  const liste = (r && r.asansorler) || [];
  for(let i=1;i<=4;i++){
    const oz = (liste[i-1] || {}).ozet || null;
    const q = $('a_Q_goster'+i), g = $('a_Gk_goster'+i);
    if(q){
      q.value = (oz && oz.Q!=null) ? trn(oz.Q,0)
              : (v('a_Q_elle'+i) || (SEC.tablo_7||{})[v('a_kapasite'+i)] || '');
    }
    if(g){
      g.value = (oz && oz.Gk!=null) ? trn(oz.Gk,0) : (v('a_Gk_elle'+i) || '');
    }
    //  L1 yer tutucusu HESAPLANAN değeri gösterir: "42,00  ( Hk + 3,50 )".
    //  Böylece "kuyu yüksekliğinden mi geliyor" sorusu ekrandan cevaplanır.
    const l1 = $('a_L1'+i);
    if(l1){
      const pay = sayiOku((($('of_L1_pay')||{}).value) || (SEC.ofis_varsayilan||{}).L1_pay);
      const hk  = sayiOku(v('a_Hk'+i));
      const hes = (oz && oz.L1!=null) ? oz.L1 : ((hk>0 && pay>=0) ? hk+pay : NaN);
      l1.placeholder = isFinite(hes)
        ? `${tr(hes)}   ( Hk + ${tr(pay)} )` : 'Hk + yatay güzergâh payı';
    }
  }
}

function sabitFormuKur(){
  const yedek = new Set(SEC.sabit_b_yedek || []);
  const B = SEC.sabit_b || {}, C = SEC.ofis_varsayilan || {};
  const deger = (kaynak, k) => (kaynak === 'sb' ? B[k] : C[k]);
  let h = '', basilan = new Set();

  SABIT_GRUP.forEach(([baslik, aciklama, alanlar]) => {
    const gecerli = alanlar.filter(x => {
      const [kaynak, k] = x.split(':');
      return !yedek.has(k) && deger(kaynak, k) !== undefined;
    });
    if(!gecerli.length) return;
    h += `<div class="bolum-bas">${baslik}${aciklama ? ` <span class="ipucu">— ${aciklama}</span>` : ''}</div>`;
    gecerli.forEach(x => {
      const [kaynak, k] = x.split(':');
      basilan.add(k);
      const [et, ip] = SABIT_ETIKET[k] || [k, ''];
      const d = String(deger(kaynak, k)).replace('.', ',');
      const girdi = (k === 'kapi_tipi')
        ? `<select id="of_${k}" class="girdi">${(SEC.kapi_tipleri||[])
             .map(v=>`<option value="${v}"${v===C[k]?' selected':''}>${v}</option>`).join('')}</select>`
        : `<input id="${kaynak}_${k}" class="girdi" value="${d}">`;
      h += `<div class="alan"><label>${et} ${ip?`<span class="ipucu">— ${ip}</span>`:''}</label>${girdi}</div>`;
    });
  });

  /*  Gruplara yazılmamış bir sabit kalırsa SESSİZCE kaybolmasın — yeni bir
      sabit eklenip SABIT_GRUP güncellenmezse burada görünür. */
  const artan = [];
  Object.keys(B).forEach(k=>{ if(!yedek.has(k) && !basilan.has(k)) artan.push(['sb',k]); });
  Object.keys(C).forEach(k=>{ if(!yedek.has(k) && !basilan.has(k)) artan.push(['of',k]); });
  if(artan.length){
    h += `<div class="bolum-bas">DİĞER <span class="ipucu">— henüz bir hesap grubuna yazılmadı</span></div>`;
    artan.forEach(([kaynak,k])=>{
      const [et,ip] = SABIT_ETIKET[k] || [k,''];
      const d = String(deger(kaynak,k)).replace('.',',');
      h += `<div class="alan"><label>${et} ${ip?`<span class="ipucu">— ${ip}</span>`:''}</label>
            <input id="${kaynak}_${k}" class="girdi" value="${d}"></div>`;
    });
  }

  //  Panelde görünmeyen alanlar ( SABIT_B_YEDEK — askı oranı ) kart
  //  başlığındaki ( ! ) balonunda anlatılır; ekranı kalabalıklaştıran
  //  bilgi bandına gerek yok.
  $('sabit_b_form').innerHTML = h;
}

function sabitleriSifirla(){
  //  İki kaynak da sıfırlanır: sb_* ( SABİTLER sayfası ) + of_* ( GİRİŞ hücreleri )
  Object.entries(SEC.sabit_b||{}).forEach(([k,val])=>{
    const e=$('sb_'+k); if(e) alanaYaz(e, String(val).replace('.',','));
  });
  Object.entries(SEC.ofis_varsayilan||{}).forEach(([k,val])=>{
    const e=$('of_'+k); if(e) alanaYaz(e, String(val).replace('.',','));
  });
  ofisTazele(); planla(); durum('Ofis standardının tamamı varsayılana döndürüldü');
}

function ofisSifirla(){ sabitleriSifirla(); }

/* Ofis varsayılanı olan alanların YER TUTUCUSU her zaman güncel değeri
   gösterir: kullanıcı panelde ray kütlesini değiştirdiğinde asansör
   kartındaki boş alan da yeni değeri "hayalet" olarak gösterir. */
function ofisTazele(){
  document.querySelectorAll('.ofis-alan').forEach(e=>{
    const k = e.dataset.ofis; if(!k) return;
    const kaynak = $('of_'+k);
    const deger = kaynak ? kaynak.value.trim() : '';
    if(e.tagName==='SELECT'){
      const ilk = e.options[0];
      if(ilk && ilk.value==='') ilk.textContent = deger ? `ofis standardı ( ${deger} )` : 'ofis standardı';
    }else{
      e.placeholder = deger || 'ofis standardı';
    }
  });
  for(let i=1;i<=4;i++) ozelRozet(i);
  manuelRozet();
}

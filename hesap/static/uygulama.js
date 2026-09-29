/* ═══════════════════════════════════════════════════════════════════
   UYGULAMA PROJESİ  —  arayüz

   Mukavemet + elektrik + topraklama.  Avan tarafından BAĞIMSIZDIR;
   ortak kısım için bkz. ortak.js
   ═══════════════════════════════════════════════════════════════════ */

/* ═══════════════════════════════════════════════════════════════════════
   UYGULAMA PROJESİ  ·  MUKAVEMET HESABI
   Form kendini SUNUCUDAN gelen girdi sözleşmesinden üretir
   ( /api/mukavemet/alanlar → engine/mukavemet_girdi.GRUPLAR ).  Böylece
   alan eklemek / çıkarmak için arayüze dokunmak gerekmez;  tek doğruluk
   kaynağı motorun yanındaki sözleşmedir.
   ═══════════════════════════════════════════════════════════════════════ */
const M_ID = a => 'm_' + a;

/*  ÇOKLU ASANSÖR.  Bir binada farklı kuyularda 1-4 asansör olabilir;  hesap
    her biri için AYNIDIR, değişen yalnız girdilerdir.

    FORM TEK KOPYADIR.  Dört kopya DOM ( 4 × 86 alan ) hem ağır olurdu hem de
    akordeonu dörde katlardı.  Bunun yerine aktif asansörün değerleri formda
    durur;  asansör değişince form kaydedilip ötekinin değerleri yüklenir.
    MUK_ASANSORLER[i] = { alan anahtarı: değer } */
//  MUK_ASANSORLER her zaman 4 haritaya kadar tutar;  MUK_ADET kaçının
//  KULLANILDIĞINI söyler.  Adedi azaltmak veri SİLMEZ — 3→2→3 yapan mühendis
//  girdilerini geri bulur.
let MUK_ASANSORLER = [{}];
let MUK_AKTIF = 0;
let MUK_ADET = 1;

/*  Proje geneli alanlar asansörden asansöre TAŞINMAZ:  topraklama ve makine
    dairesi binaya aittir.  Liste sunucudan gelir ( MUK.proje_geneli ). */
const mProjeGeneliMi = a => !!(MUK && (MUK.proje_geneli||[]).includes(a));

/*  Sayı biçimi:  sözleşme 0,63 gibi ondalıkları nokta ile taşır, kullanıcı
    virgül görür.  Seçenek listesinde DEĞER değişmez, yalnız etiket çevrilir. */
const mSayi = x => (typeof x === 'number')
  ? String(x).replace('.', ',') : String(x ?? '');

async function mukavemetKur(){
  if(MUK) return;                       // bir kez kurulur
  try{
    MUK = await (await fetch('/api/uygulama/alanlar')).json();
  }catch(e){
    $('m_form').innerHTML = `<div class="uyari kirmizi">Girdi tanımları alınamadı: ${kacis(e)}</div>`;
    return;
  }
  let h = '';
  //  ORTAK GİRDİ KÖPRÜSÜ ( MUK.ortak_kopru ) BURADA YAZILMAZ.  Bir süre
  //  formun başında "beyan yükü → Q · beyan hızı → V …" diye duruyordu;
  //  köprü zaten görünmez çalışıyor ( alan zaten formda, ikinci kez
  //  sorulmuyor ) ve o kutu her açılışta okunacak bir şey değil, girdilerin
  //  önünü kapatan sabit bir metindi.  Sözleşme API'de duruyor.
  //  AKORDEON.  86 girdi tek sütunda alt alta durunca aranan alanı bulmak
  //  zorlaşıyordu.  Girdi sütunu 440 px'tir — yatay sekme şeridi sığmaz;
  //  akordeon bu genişliğe oturur ve KAPALIYKEN DE bütün bölüm adları
  //  görünür, yani harita hep ortadadır.
  //  Alanlar DOM'dan SİLİNMEZ, yalnız gizlenir:  mukavemetGirdi() bütün
  //  grupları dolaşıp okur ve kapalı gruptaki alan da okunur.  Görünüm
  //  değişikliği hesabın hiçbir noktasına dokunmaz.
  h += `<div class="m-ara-satir">
          <input id="m_ara" class="m-ara" type="search" placeholder="alan ara…"
                 oninput="mAramaUygula()" autocomplete="off">
        </div>`;
  //  PROJE GENELİ ALANLAR AKORDEONDA, kendi grubunun ( Elektrik ve
  //  topraklama ) içinde durur ve HER asansör sekmesinde görünür.  Bir süre
  //  ayrı bir PROJE sekmesine çekilmişlerdi;  topraklamayı girmek için sekme
  //  değiştirmek gerekiyordu ve alanlar zaten ait oldukları grubun dışına
  //  düşüyordu.  Karışmasınlar diye üzerlerinde "proje geneli" etiketi var:
  //  değer TEKTİR, hangi sekmede yazılırsa yazılsın aynı yere gider ve
  //  asansörden asansöre kopyalanmaz ( mAsansorKaydet onları atlar ).
  for(const [i, g] of MUK.gruplar.entries()){
    //  GELİŞMİŞ ALANLAR grubun ALTINDA, kapalı bir bölümde durur
    //  ( engine/uygulama/mukavemet_girdi.GELISMIS_ALANLAR ):  ofisin ya da
    //  ürünün hep aynı girilen değerleri.  DOM'dan silinmezler — okunur,
    //  kaydedilir ve hesaba girerler;  yalnız ilk bakışta görünmezler.
    const ic = mSatirlar(g.alanlar.filter(f => !f.gelismis));
    const gel = mSatirlar(g.alanlar.filter(f => f.gelismis));
    if(!ic && !gel) continue;
    h += `<div class="m-grup" data-grup="${i}" data-ad="${kacis(g.ad)}">
            <button type="button" class="m-grup-bas" onclick="mGrupDegistir(${i})">
              <span class="m-grup-ok">▸</span>
              <span class="m-grup-ad">${kacis(g.ad)}</span>
              <span class="m-grup-adet" data-toplam="${g.alanlar.length}"
                    >${g.alanlar.length}</span>
            </button>
            <div class="m-grup-ic" hidden>${ic}${gel ? `
              <div class="m-gelismis" data-grup="${i}">
                <button type="button" class="m-gelismis-bas" aria-expanded="false"
                        onclick="mGelismisDegistir(this.parentElement)">
                  <span class="m-gelismis-ok">▸</span>
                  <span>Gelişmiş</span>
                  <span class="m-gelismis-sayac"></span>
                </button>
                <div class="m-gelismis-ic" hidden>${gel}</div>
              </div>` : ''}</div>
          </div>`;
  }
  $('m_form').innerHTML = h;
  //  Uygulamanın KENDİ ofis sabitleri ve KENDİ tabloları — avanınkinden ayrı.
  uygulamaSabitFormuKur();
  uygulamaTablolariKur();
  mukavemetGeriYukle();
  //  Son bakılan grup açık gelsin — sayfa yenilenince baştan başlamasın.
  let _g0 = 0; try{ _g0 = Number(localStorage.getItem('m_grup')) || 0; }catch(e){}
  mGrupAc(_g0 < MUK.gruplar.length ? _g0 : 0, true);
  //  Asansör durumu:  geri yükleme diziyi doldurmuşsa aktif olanı forma bas.
  if(!Array.isArray(MUK_ASANSORLER) || !MUK_ASANSORLER.length) MUK_ASANSORLER = [{}];
  if(MUK_AKTIF >= MUK_ASANSORLER.length) MUK_AKTIF = 0;
  if(MUK_ASANSORLER.length > 1 || Object.keys(MUK_ASANSORLER[0]||{}).length)
    mAsansorYukle(MUK_AKTIF);
  if($('m_adet')) $('m_adet').value = String(MUK_ADET);
  mMakineDairesiKutulari();
  mIkiliTazele();
  mKanalUyumu();
  mAsansorSekmeleriTazele();
  mGkBoslariIsaretle();
  mGelismisTazele();
  mGorunumTazele();
  //  Kovaya İLK AÇILIŞTA da yazılır:  yoksa kullanıcı hiçbir alana dokunmadan
  //  sayfayı yenilediğinde uygulama projesi boş açılırdı ( avan tarafında bu
  //  sorun yok, orada form açılışta kuruluyor ).
  yaz();
  hesapMukavemet();
}

/*  Form SONRADAN kurulduğu için açılıştaki uygula() bu alanları bulamaz;
    saklanan değerler burada, form ayağa kalktıktan sonra yerine oturur.
    Yoksa uygulama projesi her açılışta varsayılanlara dönüyordu. */
function mukavemetGeriYukle(){
  //  Uygulamanın KENDİ kovası okunur — avanınki ayrı dosyadadır.
  let o; try{ o = JSON.parse(localStorage.getItem(KOVA.uygulama)||'null'); }catch(e){ o = null; }
  if(!o) return;
  const mukDizi = Array.isArray(o.__muk_asansorler) && o.__muk_asansorler.length;
  //  TANINMAYAN DEĞERLER ( bkz. taninmayanBildir ) — kimliğe göre bir kez.
  //  Dizi varsa asansöre ait alanların asıl kaynağı odur;  onlar aşağıda
  //  asansör numarasıyla sayılır.
  const taninmayan = new Map();
  const say = (e, v) => { if(!taninmayan.has(e.id) && !(mukDizi && mAsansorAlaniMi(e.id)))
    taninmayan.set(e.id, {etiket: alanEtiketi(e), deger: String(v), yeni: e.value}); };
  //  KOVA ALAN KİMLİĞİYLE ( "m_beyan_yuku" ) anahtarlanır, sözleşme
  //  anahtarıyla değil;  o yüzden burada mFormaYaz kullanılamaz.  Gezinti
  //  yine ortak, yalnız kaynağı ve boş-değer kuralı farklı:  kovada boş
  //  duran alan formdakini EZMEZ.
  for(const f of mAlanlar()){
    const e = $(M_ID(f.anahtar));
    if(!e || o[e.id] === undefined) continue;
    //  Kovada BOŞ duran alan formdakini ezmez ( onay kutusu hariç:  orada
    //  "false" geçerli bir değerdir ).
    if(e.type !== 'checkbox' && o[e.id] === '') continue;
    if(!mAlanYaz(f, o[e.id])) say(e, o[e.id]);
  }
  //  UYGULAMAYA AİT HER ALAN geri yazılır — yalnız sözleşmedekiler değil.
  //  Proje kimliği ( mk_… ) ve ofis sabitleri ( uof_… ) de buradadır;
  //  yoksa sayfa yenilendiğinde proje adı ve ofis ayarları kayboluyordu.
  //  Sözleşme alanı yine mAlanYaz'dan geçer:  tanınmayan değer kutuda duranı
  //  ( öncekinin değerini ) değil alanın varsayılanını bıraksın.
  const sozlesme = new Map(mAlanlar().map(f => [M_ID(f.anahtar), f]));
  document.querySelectorAll('input,select').forEach(e=>{
    if(!e.id || e.id.indexOf('_goster') >= 0) return;
    if(alanModu(e.id) !== 'uygulama') return;
    if(o[e.id] === undefined) return;
    if(e.type === 'checkbox'){ e.checked = !!o[e.id]; return; }
    const f = sozlesme.get(e.id);
    if(!(f ? mAlanYaz(f, o[e.id]) : alanaYaz(e, o[e.id]))) say(e, o[e.id]);
  });
  //  Çoklu asansör dizisi.  Form kurulduktan SONRA aktif olan basılır
  //  ( bkz. mukavemetKur ) — burada yalnız durum geri alınır.
  const liste = [...taninmayan.values()];
  if(mukDizi){
    MUK_ASANSORLER = o.__muk_asansorler
      .slice(0, (MUK && MUK.asansor_azami) || 4)
      .map(x => (x && typeof x === 'object') ? {...x} : {});
    MUK_ASANSORLER.forEach((x, i) => liste.push(
      ...mTaninmayanAyikla(x, MUK_ASANSORLER.length > 1 ? i + 1 : null)));
    MUK_ADET = Math.min(Math.max(1, Number(o.__muk_adet) || MUK_ASANSORLER.length),
                        MUK_ASANSORLER.length);
    MUK_AKTIF = Math.min(Math.max(0, Number(o.__muk_aktif) || 0), MUK_ADET - 1);
  }
  taninmayanBildir(liste, 'Tarayıcıda kayıtlı uygulama projesinde');
}

const mSatir = alanlar => `<div class="satir i${alanlar.length}">${alanlar.join('')}</div>`;
/*  Alanları ikişerli satırlara dizer;  alan yoksa boş metin. */
function mSatirlar(alanlar){
  let ic = '', acik = [];
  for(const f of alanlar){
    acik.push(mAlan(f));
    if(acik.length === 2){ ic += mSatir(acik); acik = []; }
  }
  if(acik.length) ic += mSatir(acik);
  return ic;
}

/*  UYGULAMA PROJESİNİN KAPAĞI AYRI BİR MMO KİTABINDADIR — elimizde yok.
    Bu yüzden avan kapağı buraya BASILMAZ;  sunucuya yalnız dosya adı ve
    belge özellikleri için gereken proje kimliği gönderilir. */
/*  Sabitler / Ofis Standardı sekmesindeki değerler.  Avan tarafında
    avanGirdi() aynı işi yapar;  uygulama projesinin elektrik ve topraklama
    hesapları da bunları kullanır. */
/* ═════════════ UYGULAMANIN KENDİ OFİS STANDARDI ═════════════
   Avanınkinden AYRIDIR ( ön ek uof_ ).  Avan ön tasarımdır ve genel
   kabullerle çalışır;  uygulama kesin tasarımdır ve imalatçı verisi vardır.
   İkisinin aynı sayıyı tutma zorunluluğu yoktur — ama ikisi de ekranda
   durur, paftaya kaynağıyla basılır ve bilerek ayrışır.                  */
const UOF = k => 'uof_' + k;

function ofisSabitleri(){
  const o = {}, S = (MUK && MUK.sabitler) || {};
  Object.keys(S.varsayilan || {}).forEach(k=>{
    const x = v(UOF(k)); if(x !== '') o[k] = x; });
  return o;
}

function uygulamaSabitFormuKur(){
  const S = (MUK && MUK.sabitler) || {}, kutu = $('usabit_form');
  if(!kutu || !S.gruplar) return;
  const metin = new Set(S.metin || []);
  let h = '';
  (S.gruplar || []).forEach(gr=>{
    h += `<div class="bolum-bas">${kacis(gr.baslik)}`
       + (gr.aciklama ? ` <span class="ipucu">— ${kacis(gr.aciklama)}</span>` : '')
       + `</div>`;
    const alanlar = gr.alanlar.map(k=>{
      const [et, ip] = S.etiket[k] || [k, ''];
      const d = String(S.varsayilan[k]).replace('.', ',');
      //  Boş bırakılan alan varsayılanı kullanır;  yer tutucu o değeri gösterir.
      const giris = `<input id="${UOF(k)}" class="girdi" placeholder="${kacis(d)}"${metin.has(k) ? '' : ' inputmode="decimal"'}>`;
      return `<div class="alan"><label>${kacis(et)}`
        + (ip ? ` <span class="ipucu">${kacis(ip)}</span>` : '')
        + `</label>${giris}</div>`;
    });
    for(let i=0; i<alanlar.length; i+=3)
      h += `<div class="satir i3">${alanlar.slice(i, i+3).join('')}</div>`;
  });
  kutu.innerHTML = h;
}
function uygulamaSabitleriSifirla(){
  const S = (MUK && MUK.sabitler) || {};
  Object.keys(S.varsayilan || {}).forEach(k=>{ const e=$(UOF(k)); if(e) e.value=''; });
  yaz(); hesapMukavemet();
  durum('Uygulama projesinin ofis sabitleri varsayılana döndürüldü.');
}

/* ═════════════ UYGULAMANIN TABLOLARI ═════════════
   Bugüne kadar yalnız motorun içindeydiler:  hesaba giriyorlardı ama
   ekranda görünmüyorlardı.  Tablolar KOPYALANMAZ — sunucu motorun kendi
   sözlüklerinden üretir ( engine/uygulama/tablolar_gorunum.py ).       */
function uygulamaTablolariKur(){
  const kutu = $('utablolar_ic'); if(!kutu) return;
  const t = (MUK && MUK.tablolar) || [];
  kutu.innerHTML = t.map(x=>{
    const bas = x.basliklar.map(b=>`<th>${kacis(b)}</th>`).join('');
    const sat = x.satirlar.map(r=>
      `<tr>${r.map(c=>`<td>${kacis(String(c))}</td>`).join('')}</tr>`).join('');
    return `<div class="bolum-bas">${kacis(x.ad)}`
      + (x.kaynak ? ` <span class="ipucu">— ${kacis(x.kaynak)}</span>` : '') + `</div>`
      + (x.aciklama ? `<div class="yardim">${kacis(x.aciklama)}</div>` : '')
      + `<div class="kaydir"><table class="veri"><thead><tr>${bas}</tr></thead>`
      + `<tbody>${sat}</tbody></table></div>`;
  }).join('');
}

function mukavemetKimlik(){
  const al = id => ($(id)?.value || '').trim();
  return {project_title: al('mk_proje_adi'), owner: al('mk_isveren'),
          sheet_no: al('mk_pafta_no')};
}

/*  ONAY ALANLARININ İKİ DÜĞMELİ GÖRÜNÜMÜ.
    { etiket , [ kapalı şıkkı , açık şıkkı ] }

    ETİKET DE DEĞİŞİR:  alanın kendi adı olumsuz kurulmuştur ( "Makine
    dairesiz" ) ve düğmelerin üstünde tekrar edince kafa karıştırıyordu —
    "Makine dairesiz" başlığı altında "Makine daireli" düğmesi.  Başlık
    SORUYU sorar ( "Makine dairesi" ), düğmeler CEVABI verir ( "Var" / "Yok" ).
    Kısa şıklar ayrıca satır sarmaz, düğmeler tek satırda durur.

    Yalnız GÖRÜNÜMdür;  alanın türü ve kaydedilen değer değişmez.           */
const IKILI_ETIKET = {
  mk_yok: { etiket: 'Makine dairesi', secenek: ['Var', 'Yok  ( MRL )'] },
};

/*  Düğmeye basılınca alttaki checkbox'ı günceller ve hesabı tetikler.
    Kutu tek doğruluk kaynağıdır;  düğmeler yalnız onu gösterir.            */
function mIkiliSec(id, deger){
  const e = $(id); if(!e) return;
  e.checked = !!deger;
  e.dispatchEvent(new Event('change', {bubbles:true}));
  mIkiliTazele();
}

/*  SERTLEŞTİRİLMEMİŞ DÜZ V KANAL SEÇTİRİLMEZ  ( TS EN 81-50 m.5.11.2.3.1.2 ).
    Sertleştirilmemiş V kanalın ALT KESİLMESİ olmalıdır.  Kanal şekli ile
    kanal işlemesi iki ayrı listedir ve birbirini görmüyordu:  kullanıcı
    ikisini ayrı ayrı değiştirip standart dışı birleşimi kurabiliyordu.
    Karşı listedeki uyumsuz seçenek KAPATILIR ve sebebi üstüne yazılır.
    Mevcut seçim SESSİZCE DEĞİŞTİRİLMEZ — o, gerçek kasnağın özelliğini
    değiştirmek olurdu;  eski bir dosyadan böyle gelirse motor açık hata verir. */
const M_KANAL_NEDEN = 'TS EN 81-50 m.5.11.2.3.1.2 — sertleştirilmemiş V kanalın alt kesilmesi olmalıdır';
function mKanalUyumu(){
  const k = $(M_ID('kanal_sekli')), i = $(M_ID('kanal_isleme'));
  if(!k || !i) return;
  const kapat = (o, kosul) => {
    o.disabled = !!kosul;
    o.title = kosul ? M_KANAL_NEDEN : '';
  };
  for(const o of i.options) kapat(o, k.value === 'V Kanal' && o.value === 'Sertleştirilmemiş');
  for(const o of k.options) kapat(o, i.value === 'Sertleştirilmemiş' && o.value === 'V Kanal');
}

/*  Checkbox nereden değişirse değişsin ( düğme · geri yükleme · test )
    düğmelerin işaretli olanı ona uydurulur.                                */
function mIkiliTazele(){
  document.querySelectorAll('#m_form .secim-ikili').forEach(k=>{
    const e = $(k.dataset.icin); if(!e) return;
    k.querySelectorAll('.secim-dg').forEach(d=>{
      const secili = (d.dataset.deger === '1') === !!e.checked;
      d.classList.toggle('secili', secili);
      d.setAttribute('aria-checked', secili ? 'true' : 'false');
    });
  });
}

function mAlan(f){
  //  PROJE GENELİ ROZETİ.  Alan asansöre değil BİNAYA aitse söylenir:  dört
  //  asansörün sekmesinde de aynı kutu görünür ve aynı değeri taşır.
  const pg = mProjeGeneliMi(f.anahtar)
    ? ` <span class="pg-rozet" title="Binaya aittir: bütün asansörlerde tek`
      + ` değer, hesaba bir kez girer">proje geneli</span>` : '';
  //  ALANIN TANIMI ( i ) DAİRESİNDE.  Metin motordan gelir ( MG.ACIKLAMA ·
  //  UG.EK_ACIKLAMA );  burada bir kopyası tutulsaydı alan değişince ikisi
  //  ayrışırdı.  Özellikle üç kaçıklık ( kabin merkezi · askı noktası · boş
  //  kabin ağırlık merkezi ) birbirine karıştırılmaya çok açık.
  const bilgi = bilgiSimgesi(f.bilgi, 'bilgi-alan', 'i');
  const et = kacis(f.etiket)
    + (f.birim && f.birim !== '—' ? ` <span class="ipucu">(${kacis(f.birim)})</span>` : '')
    + pg + bilgi;
  if(f.tur === 'onay'){
    //  İKİLİ SEÇİM GÖRÜNÜMÜ.  Bazı onay alanları aslında İKİ ŞIKLI bir
    //  tercihtir ( makine daireli / dairesiz ) ve işaretsiz bir kutu
    //  "seçim yapılmadı" gibi durur.  İki düğme olarak gösterilir;  VERİ
    //  MODELİ DEĞİŞMEZ — altta gerçek bir checkbox durur, kaydetme, geri
    //  yükleme ve testler ona bakmaya devam eder.  Kutu ekrandan kalkmaz,
    //  yalnız görsel olarak saklanır ( .gorsel-gizli ):  klavye ve ekran
    //  okuyucu erişimi korunur.
    const ik = IKILI_ETIKET[f.anahtar];
    if(ik){
      const id = M_ID(f.anahtar), a = f.varsayilan ? 1 : 0;
      return `<div class="alan"><label>${kacis(ik.etiket)}${pg}${bilgi}</label>`
        + `<input type="checkbox" class="gorsel-gizli" id="${id}"${f.varsayilan?' checked':''}>`
        + `<div class="secim-ikili" role="group" aria-label="${kacis(ik.etiket)}"`
        + ` data-icin="${id}">`
        + ik.secenek.map((m, i)=>
            `<button type="button" class="secim-dg${i===a?' secili':''}"`
            + ` role="radio" aria-checked="${i===a}"`
            + ` data-deger="${i}" onclick="mIkiliSec('${id}',${i})">${kacis(m)}</button>`
          ).join('')
        + `</div></div>`;
    }
    return `<div class="alan"><label class="kutu-satir">`
      + `<input type="checkbox" id="${M_ID(f.anahtar)}"${f.varsayilan?' checked':''}>`
      + `<span>${kacis(f.etiket)}${pg}${bilgi}</span></label></div>`;
  }
  let giris;
  if(f.secenekler){
    //  GÖRÜNEN YAZI DEĞERDEN AYRI OLABİLİR ( f.secenek_metni ).  Değer sayı
    //  kalır — hesap, kayıt ve geri yükleme ona bakar;  yalnız kullanıcının
    //  okuduğu metin değişir.  Askı oranında çıplak "2", 2:1 mi 1:2 mi
    //  belli olmuyordu.
    const sm = f.secenek_metni || null;
    const oku = o => (sm && sm[o] !== undefined) ? sm[o] : mSayi(o);
    giris = `<select id="${M_ID(f.anahtar)}" class="girdi">`
      + f.secenekler.map(o=>
          `<option value="${kacis(o)}"${o===f.varsayilan?' selected':''}>${kacis(oku(o))}</option>`
        ).join('') + '</select>';
  }else{
    //  Varsayılanı olmayan alan BOŞ açılır ( temel ölçüleri, kolon boyu … );
    //  "0" yazmak kullanıcıyı yanıltırdı.
    //  KABİN AĞIRLIĞI DA BOŞ AÇILIR:  ilk hesapta beyan yükünün tablo değeriyle
    //  dolar ( mGkBoslariIsaretle ).  Sözleşmedeki 700 örnek projenin değeridir
    //  ve 800 kg yükün tablo değeri ( 800 ) değildir;  alan Gelişmiş'te gizli
    //  durduğu için yeni proje farkına varılmadan "elle girilmiş" 700 ile
    //  hesaplanıyordu.
    const v = (f.varsayilan===null||f.varsayilan===undefined||f.anahtar==='kabin_agirligi')
      ? '' : mSayi(f.varsayilan);
    giris = `<input id="${M_ID(f.anahtar)}" class="girdi" value="${kacis(v)}">`;
  }
  return `<div class="alan"><label>${et}</label>${giris}</div>`;
}

/* ---- hesap ---- */
/*  BOŞ KABİN AĞIRLIĞI BEYAN YÜKÜNÜ İZLER.
    Beyan yükü değiştiğinde kabin ağırlığı ofis tablosundan yenilenir
    ( engine/ortak/ofis.py — avan tarafının da okuduğu tablo ).  Avandaki
    "trafik → kapasite" izlemesinin aynısıdır:  türetilen alan kaynağını
    izler, elle girilen değer beyan yükü değişmediği sürece korunur.

    TABLO TARAYICIDA TUTULMAZ.  Alan boş gönderilir, sunucu doldurur ve
    dönen değer alana yazılır;  yoksa aynı tablonun ikinci bir kopyası
    JS'de durur ve motorunkiyle ayrışırdı. */
//  KABİN AĞIRLIĞI TABLODAN YENİLENECEK ASANSÖRLER  —  { sıra : değişiklik no }.
//  HER ASANSÖR AYRI TUTULUR.  Tek bir "tazelenecek asansör" tutulduğunda
//  2. asansörün yükü değiştirilip hemen 1. asansörünki de değiştirilince
//  ikincisi birincinin işaretini siliyor, 2. asansörün kabin ağırlığı eski
//  değerde kalıyordu.
//  DEĞİŞİKLİK NO her beyan yükü değişikliğinde artar.  Aynı asansörde
//  1000 kg'ın isteği yoldayken yük 1600 kg yapılınca eski yanıt işareti
//  kapatıp 1000 kg'ın tablo değerini ( 950 ) yazıyor, 1600 kg'lık hesap o
//  değerle gidiyordu ( 1350 olmalıydı ).  Yanıt artık bir asansöre yalnız
//  KENDİ değişikliği hâlâ o asansörün en sonuncusuysa yazar.
let MUK_GK_TAZELE = {};
let MUK_GK_SURUM = 0;
const mGkTazelenecek = i => MUK_GK_TAZELE[i] !== undefined;

/*  BOŞ KABİN AĞIRLIĞI TABLOYU İZLER.  Proje açılınca ya da sayfa yenilenince
    kutusu boş gelen asansörler tablodan yenilenmeyi bekler — boşluk, tablo
    değeri gelmeden kaydedilmiş bir projenin izidir ( bkz. mukavemetPlanla ). */
function mGkBoslariIsaretle(){
  MUK_ASANSORLER.forEach((a, i) => {
    const gk = $('m_kabin_agirligi');
    const deger = (i === MUK_AKTIF && gk) ? gk.value : (a || {}).kabin_agirligi;
    if(String(deger ?? '').trim() === '' && !mGkTazelenecek(i))
      MUK_GK_TAZELE[i] = ++MUK_GK_SURUM;
  });
}

/* ==========================================================================
   FORM ALANLARININ TEK GEZİNTİSİ

   "Alan nedir, nasıl okunur, nasıl yazılır" bilgisi BİR YERDE durur.  Bir
   süre aynı gezinti dört ayrı yerde elle yazılıydı — hesaba gönderilecek
   girdiyi toplarken, asansör değiştirirken kaydederken, yüklerken ve
   tarayıcı kovasından geri yüklerken.  Dördü de "checkbox ise checked,
   değilse value" kuralını kendi kopyasında taşıyordu:  yeni bir alan türü
   ( radyo · çoklu seçim ) eklendiğinde birinde unutulur ve asansör
   değiştirince o alan SESSİZCE kaybolurdu.

   Ayrıca ikisi ayrışmıştı:  kovadan geri yükleme alanaYaz() kullanıyor —
   seçim kutusunda "6.5" ile "6,5"i eşleştiren ortak yardımcı — asansör
   yükleme ise ham `e.value =` yapıyordu, yani o eşleştirmeyi atlıyordu.
   ========================================================================== */

/*  Sözleşmedeki alanlar, isteğe bağlı süzgeçle.  Sıra GRUP SIRASIDIR. */
function mAlanlar(sec){
  const c = [];
  for(const gr of ((MUK && MUK.gruplar) || [])) for(const f of gr.alanlar)
    if(!sec || sec(f)) c.push(f);
  return c;
}

/*  ASANSÖRE AİT alan:  proje geneli alanlar binaya aittir ve asansörden
    asansöre kopyalanmaz. */
const M_ASANSOR_ALANI = f => !mProjeGeneliMi(f.anahtar);

/*  Tek alanın değeri.  Alan formda yoksa undefined döner — çağıran o
    anahtarı hiç yazmaz, "boş string" ile karıştırmasın. */
function mAlanOku(f){
  const e = $(M_ID(f.anahtar));
  if(!e) return undefined;
  return (e.type === 'checkbox') ? e.checked : e.value;
}

/*  Tek alana değer basar.  Yazma her yerde alanaYaz() üzerinden gider.
    Seçim kutusu değeri TANIMAZSA false döner;  kutu alanın varsayılanına
    döner ( secimVarsayilani — form seçenekleri alanın varsayılanı seçili
    çizilir ).  Eskiden kutuda duran kalıyordu:  asansör değiştirilirken o
    bir önceki asansörün değeriydi — tanınmayan değer sessizce BAŞKA
    asansörün değeri oluyordu. */
function mAlanYaz(f, deger){
  const e = $(M_ID(f.anahtar));
  return !e || alanaYaz(e, deger);
}

/*  Asansöre ait ( proje geneli olmayan ) bir sözleşme alanının kimliği mi? */
function mAsansorAlaniMi(id){
  return mAlanlar(M_ASANSOR_ALANI).some(f => M_ID(f.anahtar) === id);
}

/*  BİR ASANSÖRÜN TANINMAYAN SEÇİM DEĞERLERİ.  Dosyada ( ya da tarayıcıda )
    duran asansör haritasında bu sürümün listesinde olmayan bir seçim değeri
    varsa alanın varsayılanına çekilir ve listelenir.  Yalnız açık asansör
    forma basıldığı için öbürlerinin değerleri ham kalıyor ve hesap onlarda
    "geçersiz seçim" diye duruyordu;  açık olanınki ise sessizce
    değişiyordu.  Artık hepsi aynı kuralla düzelir ve söylenir.
    ``no``:  asansör numarası ( tek asansörlü projede null ).            */
function mTaninmayanAyikla(harita, no){
  const liste = [];
  for(const f of mAlanlar(M_ASANSOR_ALANI)){
    const e = $(M_ID(f.anahtar)), v = harita[f.anahtar];
    if(!e || e.tagName !== 'SELECT' || v === undefined || v === null || String(v).trim() === '') continue;
    if(secenekKarsiligi(e, v) !== undefined) continue;
    harita[f.anahtar] = secimVarsayilani(e);
    liste.push({etiket: f.etiket + (no ? ` ( ${no}. asansör )` : ''),
                deger: String(v), yeni: harita[f.anahtar]});
  }
  return liste;
}

function mFormOku(sec){
  const g = {};
  for(const f of mAlanlar(sec)){
    const deger = mAlanOku(f);
    if(deger !== undefined) g[f.anahtar] = deger;
  }
  return g;
}

/*  Haritadaki değerleri forma basar.  Haritada OLMAYAN alana dokunulmaz —
    yeni açılan asansör, kopyalandığı asansörün değerleriyle kalır. */
function mFormaYaz(harita, sec){
  for(const f of mAlanlar(sec)){
    if(harita[f.anahtar] === undefined) continue;
    mAlanYaz(f, harita[f.anahtar]);
  }
  mKanalUyumu();
}

function mukavemetGirdi(){
  const g = mFormOku();
  if(mGkTazelenecek(MUK_AKTIF)) g.kabin_agirligi = '';   // sunucu tablodan doldursun
  return g;
}

let mZaman = null;
/*  MALZEME SEÇİNCE DERİNLİK KUTUSU DOLAR — hesabı bu doldurmaz.
    Motor yalnız kutudaki sayıyı okur ( TS EN 81-50 Ek C.2.2 karşı ağırlığın
    KENDİ ölçüsünü ister ).  Ama malzeme seçince ekranda hiçbir şeyin
    değişmemesi sessiz bir tuzaktı:  eskiden derinliği malzeme belirliyordu,
    "Pik Döküm" seçen biri 100 mm ile hesaplandığını sanmaya devam ederdi. */
function mMalzemeDerinligi(){
  const tablo = (MUK && MUK.malzeme_derinligi) || {};
  const m = $(M_ID('agirlik_malzemesi')), d = $(M_ID('agirlik_derinligi'));
  if(!m || !d) return;
  const v = tablo[m.value];
  if(v !== undefined && v !== null) d.value = mSayi(v);
}

/*  MAKİNE DAİRESİ ÖLÇÜLERİ MRL'DE GİZLENİR.
    Avan sayfası bunu zaten yapıyordu ( a_mk_olculer );  uygulama sayfasında
    kutular MRL işaretliyken de duruyordu.  Ortada duran ve doldurulabilen
    iki kutu, "makine dairesi hesabı yapılacak" izlenimi veriyor;  hesap ise
    -doğru olarak- MRL'de o bölümü hiç üretmiyor.  Kutuyu gizlemek çelişkiyi
    kaynağında bitirir.  Değer SİLİNMEZ:  MRL kaldırılırsa geri gelir. */
function mMakineDairesiKutulari(){
  const k = $(M_ID('mk_yok'));
  if(!k) return;
  //  SINIF KULLANILIR, [hidden] DEĞİL.  Arama süzgeci ( mAramaUygula ) ve
  //  "tüm grupları aç" ( mTumGruplariAc ) [hidden] üzerinde çalışır;  kural
  //  gizlemesi de aynı niteliği kullanırsa ikisi birbirini siler — grupları
  //  açmak MRL'de gizlenmesi gereken kutuyu geri getiriyordu.
  const gizle = (ad, nezaman) => {
    const e = $(M_ID(ad));
    const kap = e && (e.closest('.alan') || e);
    if(kap) kap.classList.toggle('kural-disi', !!nezaman);
  };
  //  LİSTE MOTORDAN GELİR ( engine/uygulama/girdi.uygulanmayan_alanlar ):
  //  ekranın gizlediği alanla motorun hesaba almadığı alan aynı olmalı.
  //    MRL      → makine dairesi ölçüleri ve kaide kirişleri ( bölüm 2 yok )
  //    daireli  → makine yükünün yolu ( makine kendi kaidesinde durur;  yükü
  //               raya bindirmek onu İKİ KEZ saymak olur )
  const gizli = (MUK && MUK.yerlesime_gore_gizli) || {mrl: [], daireli: []};
  for(const a of gizli.mrl) gizle(a, k.checked);
  for(const a of gizli.daireli) gizle(a, !k.checked);
}

function mukavemetPlanla(hedef){
  //  YÜK DEĞİŞİNCE ESKİ KÜTLE HEMEN SİLİNİR.  Kutu tablo değeri gelene kadar
  //  eski kütleyi taşıyordu:  o arada proje kaydedilirse ( ya da sayfa
  //  yenilenirse ) dosyaya 1600 kg yükün yanına 800 kg kabin yazılıyor, açılınca
  //  hesap o değerle yapılıyordu.  Boş kutu "tablodan gelecek" demektir;
  //  dosya da, tarayıcı belleği de, istek de aynı şeyi taşır.
  if(hedef && hedef.id === 'm_beyan_yuku'){
    MUK_GK_TAZELE[MUK_AKTIF] = ++MUK_GK_SURUM;
    const gk = $('m_kabin_agirligi');
    if(gk) gk.value = '';
  }
  //  KULLANICININ YAZDIĞI KABİN AĞIRLIĞI KAZANIR.  Beyan yükü seçilip hemen
  //  ardından kabin ağırlığı yazılınca bayrak hâlâ açıktı:  istek alanı boş
  //  gönderiyor, dönen tablo değeri de yazılan sayının ÜSTÜNE basılıyordu
  //  ( 950 yazıldı, kutu ve hesap 800'e döndü ).  Elle giriş tazelemeyi iptal
  //  eder;  yolda olan yanıt da artık kutuya dokunmaz.
  if(hedef && hedef.id === 'm_kabin_agirligi') delete MUK_GK_TAZELE[MUK_AKTIF];
  if(hedef && hedef.id === M_ID('agirlik_malzemesi')) mMalzemeDerinligi();
  mMakineDairesiKutulari();
  mIkiliTazele();
  mKanalUyumu();
  mGelismisTazele();
  yaz();                              // girdiler tarayıcıda saklansın
  clearTimeout(mZaman);
  mZaman = setTimeout(hesapMukavemet, 220);
}

async function hesapMukavemet(){
  if(!MUK) return;
  const sira = ++ISTEK.mukavemet;
  //  TAZELEMEYİ YALNIZ ONU İSTEYEN İSTEK TAMAMLAR.  Bayrak yanıtta okunuyordu:
  //  beyan yükü değiştirildiği sırada YOLDA olan eski bir istek ( kabin
  //  ağırlığını eski değerle taşıyan ) yanıtlanınca bayrağı kapatıyor ve eski
  //  kütleyi kutuya yazıyordu — sonraki istek artık boş alan göndermediği için
  //  tablo değeri hiç gelmiyordu ( 800 → 1000 kg'da kabin 950 yerine 800 kaldı ).
  //  Tazelenecek asansörler ( ve değişiklik numaraları ) İSTEK ANINDA yakalanır.
  const tazele = {...MUK_GK_TAZELE};
  try{
    const c = await (await fetch('/api/uygulama/coklu', {method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify(mukavemetIstek())})).json();
    if(sira !== ISTEK.mukavemet) return;      // daha yeni istek var
    SON.mc = c;
    //  SON.m AKTİF ASANSÖRÜN sonucudur.  Tek asansörlük kodun ( ve testlerin )
    //  baktığı yer burasıdır;  çoklu sonuç SON.mc'de durur.
    const aktif = (c.asansorler || [])[MUK_AKTIF] || (c.asansorler || [])[0] || c;
    SON.m = aktif;
    //  Boş alanla giden BU istekse ve bu arada o asansörde yeni bir değişiklik
    //  olmadıysa ( yük yeniden değişince numara artar, kutuya yazınca işaret
    //  silinir ).  Değer HER ZAMAN kendi asansörüne yazılır;  kutuya yalnız o
    //  asansör açıksa basılır.  Hesaba girmeyen ( adedin üstündeki ) ya da
    //  hesabı yapılamayan asansörün işareti açık kalır — sonraki istek yine
    //  tablodan ister.
    let yazildi = false;
    for(const [s, no] of Object.entries(tazele)){
      const i = Number(s);
      if(MUK_GK_TAZELE[i] !== no) continue;
      const hedef = (c.asansorler || [])[i];
      const yeni = hedef && hedef.girdi && hedef.girdi.kabin_agirligi;
      if(yeni === null || yeni === undefined) continue;
      delete MUK_GK_TAZELE[i];
      if(MUK_ASANSORLER[i]) MUK_ASANSORLER[i].kabin_agirligi = mSayi(yeni);
      const gk = $('m_kabin_agirligi');
      if(gk && i === MUK_AKTIF) gk.value = mSayi(yeni);
      yazildi = true;
    }
    if(yazildi) yaz();
    mYeriKoruyarakCiz(()=>cizMukavemet(aktif));
    mGelismisTazele();
    mCizimdenTazele(aktif);
    //  Çizimler aynı girdiden:  görünürse onlar da tazelenir.
    cizimleriGetir();
    //  Asansör listesi YALNIZ PROJE sekmesindedir.  Bir süre her asansörün
    //  sonuç panelinin başına da basılıyordu;  ASANSÖR 1 sekmesinde "1 · 2"
    //  listesi görmek, o sekmenin zaten 1 nolu asansöre ait olduğunu bile
    //  bile tekrar söylemektir — hangi sekmede olduğun üstteki şeritte yazılı.
    mProjeOzetiCiz(c);
    mProjeGeneliCiz(c);
    //  Genel rozet PROJE sekmesindedir:  asansör sekmelerininki kendilerine
    //  aittir ( bkz. mAsansorSekmeleriTazele ).
    const hatali = !c.aktif;
    sekmeRozeti('uygproje', hatali, hatali ? 0 : (aktif.uyarilar||[]).length);
    mAsansorSekmeleriTazele();
  }catch(e){
    $('m_sonuc').innerHTML =
      `<div class="kart-ic"><div class="uyari kirmizi">Bağlantı hatası: ${kacis(e)}</div></div>`;
  }
}

function cizMukavemet(r){
  let h = `<div class="pafta-bas"><h2>ASANSÖR UYGULAMA PROJESİ HESAPLARI</h2>
    <div class="alt">TS EN 81-20 · TS EN 81-50 · TS 12385-5 · ISO 7465 · MMO 208
      · IEEE Std 80 · IEC 60364-5-52</div>
    </div><div class="kart-ic">`;
  if(!r.aktif){
    mGelismisHataAc(r.hata);
    h += (r.hata||['Hesap yapılamadı.']).map(x=>
      `<div class="uyari kirmizi">${kacis(x)}</div>`).join('');
    $('m_sonuc').innerHTML = h + '</div>';
    return;
  }
  (r.uyarilar||[]).forEach(u=>h+=`<div class="uyari ${uyariSinifi(u)}">${kacis(u)}</div>`);
  const o = r.ozet || {};
  h += '<div class="olcut">'
     + kutu('N — Hesaplanan motor gücü', tr(o.N_hesap), 'kW', o.motor_uygun?'ok':'hata')
     + kutu('Kabin alanı', tr(o.kabin_alani), 'm²')
     + kutu('Kılavuz ray boyu', tr(o.ray_boyu), 'm')
     + (o.P_kurulu!=null ? kutu('Asansörün kurulu gücü', trn(o.P_kurulu,0), 'W') : '')
     + (o.eps!=null ? kutu('ε — Gerilim düşümü', tr(o.eps,3), '%', o.eps_uygun?'ok':'hata') : '')
     + (o.Re!=null ? kutu('Re — Topraklama', tr(o.Re,3), 'Ω', o.topraklama_uygun?'ok':'hata') : '')
     /* hüküm MOTORDAN gelir ( mukavemet.genel_hukum ) — burada yeniden
        kurulursa PDF ile ayrışır */
     + kutu('Sonuç', o.genel_sonuc_kisa || (o.tumu_uygun?'UYGUN':'UYGUN DEĞİL'), '', o.tumu_uygun?'ok':'hata')
     + '</div>';

  /* bölüm sonuçları — hangi bölüm takıldı, bir bakışta görünsün */
  h += `<div class="serit"><span>BÖLÜM SONUÇLARI</span>
        <span class="kaynak">${(r.bolumler||[]).length} hesap bölümü</span></div>
        <div class="kaydir"><table class="veri"><tr><th>Bölüm</th><th>Kaynak</th><th>Sonuç</th></tr>`;
  (r.bolumler||[]).forEach(b=>{
    const sn = b.sonuc || {};
    const sinif = sn.uygun === true ? 'ok' : (sn.uygun === false ? 'hata' : '');
    //  Bölüm satırı GİRDİLERİNE bir kısayoldur:  revizyonda insan "4. bölüm
    //  kaldı" diye düşünür ve doğrudan onun girdilerini arar.
    //  BÖLÜMÜ KİMLİĞİYLE TANIYORUZ.  Eskiden başlıktan numara ayıklanıyordu
    //  ( "4 - ASKI…" → "4" );  numara projeye göre kaydığı için proje geneli
    //  bölümler hiç eşlenemiyordu.  Kimlik bölümün doğduğu yerde verilir.
    const kim = b.kimlik || '';
    const gidilir = mBolumGruplari(kim).join('  ·  ');
    //  "Hesaba git" satırın İÇİNDEDİR ama satırın tıklamasını tetiklemez:
    //  satır girdileri açar ve sayfayı oynatmaz, düğme hesaba iner.
    const git = kim ? `<button type="button" class="m-hesaba-git" data-kimlik="${kacis(kim)}"
              onclick="event.stopPropagation(); mHesabaGit('${kacis(kim)}')"
              title="Bu bölümün hesap adımlarına in  ·  girdileri solda açılır">Hesaba git ↓</button>` : '';
    h += `<tr data-kimlik="${kacis(kim)}"${gidilir ? ` class="m-gidilir" onclick="mGirdiyeGit('${kacis(kim)}')"
              title="Girdilerine git — ${kacis(gidilir)}"` : ''}>
            <td class="etiket">${kacis(b.baslik)}${git}</td>
            <td>${kacis(b.kaynak||'')}</td>
            <td class="${sinif}">${kacis(sn.metin||'—')}</td></tr>`;
  });
  h += '</table></div>';

  /* kuyu tabanı yükleri — inşaat projesine bildirilecek değerler */
  if(o.FKR != null){
    h += `<div class="serit"><span>KUYU TABANINA GELEN YÜKLER</span>
          <span class="kaynak">inşaat projesine bildirilir</span></div>
          <div class="olcut">`
       + kutu('FKR — Bir kabin rayına', trn(o.FKR,0), 'N')
       + kutu('FAR — Bir ağırlık rayına', trn(o.FAR,0), 'N')
       + kutu('Fkt — Kabin tamponları', trn(o.Fkt,0), 'N')
       + kutu('Fat — Ağırlık tamponları', trn(o.Fat,0), 'N')
       + '</div>';
  }

  (r.bolumler||[]).forEach(b=>{
    h += bolumCiz(b, b.kimlik ? {id: mBolumCapa(b.kimlik),
      sag: `<button type="button" class="m-ozete-don" data-kimlik="${kacis(b.kimlik)}"
              onclick="mOzeteDon('${kacis(b.kimlik)}')"
              title="Bölüm sonuçları tablosunda bu bölümün satırına dön">↑ Özete dön</button>`} : undefined);
  });
  $('m_sonuc').innerHTML = h + '</div>';
}


/* ═══════════════════════════════════════════════════════════════════
   BAŞLATMA  —  en sonda, üç dosya da yüklendikten sonra
   ═══════════════════════════════════════════════════════════════════ */
kur();


/* ==========================================================================
   GİRDİ AKORDEONU
   Kapalı grup DOM'da durur, yalnız görünmez.  mukavemetGirdi() alanları
   id ile okur;  açık/kapalı olması okunan değeri DEĞİŞTİRMEZ.
   ========================================================================== */
/*  i  tek bir grup numarası ya da NUMARA DİZİSİ olabilir.  Dizi verilince
    hepsi birden açılır ve İLKİNE kaydırılır:  bir hesap bölümü iki gruptan
    besleniyorsa ( ör. 4. bölüm — halat + kasnak ) ikisini de görmek gerekir.
    Öteki bütün gruplar yine kapanır;  akordeon listeye dönüşmez. */
function mGrupAc(i, sessiz){
  const ac = (Array.isArray(i) ? i : [i]).map(Number).filter(x=>x >= 0);
  if(!ac.length) return;
  i = ac[0];
  const ara = $('m_ara');
  if(ara && ara.value){ ara.value = ''; }        // arama açıkken gruba geçilirse temizle
  document.querySelectorAll('#m_form .m-grup').forEach(gr=>{
    const bu = ac.includes(Number(gr.dataset.grup));
    gr.classList.toggle('acik', bu);
    gr.querySelector('.m-grup-ic').hidden = !bu;
    gr.querySelector('.m-grup-ok').textContent = bu ? '▾' : '▸';
    //  Arama tek tek alanları gizlemiş olabilir — gruba dönerken geri aç.
    gr.querySelectorAll('.alan[hidden]').forEach(a=>{ a.hidden = false; });
    //  ve sayaç aramanın bıraktığı değerde kalmasın
    const sy = gr.querySelector('.m-grup-adet');
    if(sy) sy.textContent = sy.dataset.toplam;
  });
  try{ localStorage.setItem('m_grup', String(i)); }catch(e){}
  if(!sessiz){
    const gr = document.querySelector(`#m_form .m-grup[data-grup="${i}"]`);
    if(gr) gr.scrollIntoView({block:'nearest', behavior:'smooth'});
  }
}

/*  BAŞLIĞA TIKLAMA AÇ/KAPADIR.  Açık gruba yeniden tıklamak eskiden hiçbir
    şey yapmıyordu ( mGrupAc her zaman AÇIYORDU ) — üç kez tıklayıp "bozuk mu"
    diye bakılıyordu.  Kapatmak son seçili grubu DEĞİŞTİRMEZ:  sayfa
    yenilendiğinde aynı grup yine açık gelir, hepsi kapalı bir form değil. */
function mGrupDegistir(i){
  const gr = document.querySelector(`#m_form .m-grup[data-grup="${i}"]`);
  if(gr && gr.classList.contains('acik')){ mGruplariKapat(); return; }
  mGrupAc(i);
}

function mGruplariKapat(){
  const ara = $('m_ara');
  if(ara && ara.value){ ara.value = ''; }
  document.querySelectorAll('#m_form .m-grup').forEach(gr=>{
    gr.classList.remove('acik');
    gr.querySelector('.m-grup-ic').hidden = true;
    gr.querySelector('.m-grup-ok').textContent = '▸';
    gr.querySelectorAll('.alan[hidden]').forEach(a=>{ a.hidden = false; });
    const sy = gr.querySelector('.m-grup-adet');
    if(sy) sy.textContent = sy.dataset.toplam;
  });
}

/*  BÜTÜN grupları açar.  Otomatik testler alanları id ile doldurur;
    kapalı gruptaki alan "görünür değil" sayılıp doldurulamaz. */
function mTumGruplariAc(){
  document.querySelectorAll('#m_form .m-grup').forEach(gr=>{
    gr.classList.add('acik');
    gr.querySelector('.m-grup-ic').hidden = false;
    gr.querySelector('.m-grup-ok').textContent = '▾';
    gr.querySelectorAll('.alan[hidden]').forEach(a=>{ a.hidden = false; });
    const sy = gr.querySelector('.m-grup-adet');
    if(sy) sy.textContent = sy.dataset.toplam;
  });
  document.querySelectorAll('#m_form .m-gelismis').forEach(k=>mGelismisAc(k, true));
}

/*  Alan etiketinde geçen metne göre süzer;  eşleşme olan gruplar açılır.
    Boşaltılınca son seçili gruba dönülür. */
function mAramaUygula(){
  const q = ($('m_ara').value || '').trim().toLocaleLowerCase('tr');
  if(!q){
    //  Aramanın açtığı Gelişmiş bölümleri de kapanır:  form aramadan önceki
    //  sade hâline döner.
    mGelismisleriKapat();
    let i = 0; try{ i = Number(localStorage.getItem('m_grup')) || 0; }catch(e){}
    mGrupAc(i, true);
    return;
  }
  document.querySelectorAll('#m_form .m-grup').forEach(gr=>{
    let bulunan = 0;
    gr.querySelectorAll('.alan').forEach(a=>{
      //  Kural gereği kapalı alan aramada da sayılmaz:  görünmeyen bir alanı
      //  "1 sonuç" diye göstermek kullanıcıyı boş yere gruba sokar.
      const kural = a.classList.contains('kural-disi');
      const es = !kural && (a.textContent || '').toLocaleLowerCase('tr').includes(q);
      a.hidden = !es;
      if(es) bulunan++;
    });
    gr.classList.toggle('acik', bulunan > 0);
    gr.querySelector('.m-grup-ic').hidden = bulunan === 0;
    gr.querySelector('.m-grup-ok').textContent = bulunan ? '▾' : '▸';
    gr.querySelector('.m-grup-adet').textContent = bulunan || gr.querySelectorAll('.alan').length;
    //  ARAMA GELİŞMİŞ ALANLARI DA BULUR:  eşleşme varsa bölümü açılır.
    gr.querySelectorAll('.m-gelismis').forEach(k=>
      mGelismisAc(k, !!k.querySelector('.alan:not([hidden]):not(.kural-disi)')));
  });
}

/*  SONUÇTAN GİRDİYE ATLAMA.  Sonuç tablosundaki bölüme tıklanınca o bölümü
    besleyen girdi grubu açılır.  Eşleme motordan gelir
    ( mukavemet_girdi.BOLUM_GRUBU ) — arayüzde tutulsaydı motor değişince
    sessizce bayatlardı. */
function mGirdiyeGit(kimlik){
  const no = mBolumGrupNolari(kimlik);
  if(!no.length) return;
  mGrupAc(no);
}
/*  Bölümü besleyen girdi gruplarının formdaki sıra numaraları. */
function mBolumGrupNolari(kimlik){
  if(!MUK || !MUK.bolum_grubu) return [];
  return mBolumGruplari(kimlik).map(ad=>MUK.gruplar.findIndex(g=>g.ad === ad))
                               .filter(i=>i >= 0);
}

/* ==========================================================================
   SONUÇ TABLOSU  ↔  AYRINTILI HESAP
   Satıra tıklamak yalnız girdileri açar, sayfayı oynatmaz.  "Hesaba git"
   bölümün hesap adımlarına iner ve girdilerini de açar:  sol panel
   yapışkan olduğu için girdi solda, hesap sağda yan yana durur.  Bölümün
   şeridindeki "Özete dön" tablodaki satırına geri getirir.
   ========================================================================== */
const mBolumCapa = kimlik => 'mh-' + kimlik;

function mKaydirma(){
  return matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';
}

/*  Yapışkan üst şerit ve sekmelerin kapladığı yükseklik:  kaydırılan yer
    onların altında kalmasın.  Dar ekranda yalnız sekmeler yapışkandır. */
function mUstPay(){
  let pay = 8;
  for(const s of ['.ust', '.sekmeler']){
    const e = document.querySelector(s);
    if(e && getComputedStyle(e).position === 'sticky') pay += e.offsetHeight;
  }
  return pay;
}

/*  Sayfa kaydırmasının hedefi — belgenin sınırları içinde ( son bölüme
    inerken hedef sayfa sonunu aşabilir, oraya hiç varılmaz ). */
function mSayfaHedefi(y){
  return Math.max(0, Math.min(Math.round(y),
                              document.documentElement.scrollHeight - innerHeight));
}
const mBolumDugmesi = (sinif, kimlik) =>
  [...document.querySelectorAll('#m_sonuc .' + sinif)].find(x=>x.dataset.kimlik === kimlik);

/*  Bölümün girdi gruplarını açar ve sol paneli ilkine kaydırır — BİR KEZ
    yapılır;  süren gidiş yeniden çizimde yenilenirken tekrarlanmaz ( o
    arada kullanıcı solda başka bir grup açtıysa kapanmasın ). */
function mBolumGirdileriniAc(kimlik){
  //  Gruplar SESSİZ açılır:  mGrupAc'ın kendi kaydırması sayfayı da
  //  oynatabilir;  burada paneli ve sayfayı ayrı ayrı biz kaydırıyoruz.
  const no = mBolumGrupNolari(kimlik);
  if(!no.length) return;
  mGrupAc(no, true);
  const gr = document.querySelector(`#m_form .m-grup[data-grup="${no[0]}"]`);
  const panel = gr && gr.closest('.sol');
  //  Panel yalnız geniş ekranda kendi içinde kayar;  dar ekranda normal akıştadır.
  if(panel && panel.scrollHeight > panel.clientHeight)
    panel.scrollTo({top: panel.scrollTop + gr.getBoundingClientRect().top
                         - panel.getBoundingClientRect().top - 8, behavior: mKaydirma()});
}

function mBolumeIn(kimlik){
  const hedef = document.getElementById(mBolumCapa(kimlik));
  if(!hedef) return null;
  const y = mSayfaHedefi(hedef.getBoundingClientRect().top + scrollY - mUstPay());
  window.scrollTo({top: y, behavior: mKaydirma()});
  const don = mBolumDugmesi('m-ozete-don', kimlik);
  if(don) don.focus({preventScroll: true});      // klavyeyle hemen geri dönülebilsin
  return y;
}

function mSatiraCik(kimlik){
  const tr = [...document.querySelectorAll('#m_sonuc tr[data-kimlik]')]
               .find(x=>x.dataset.kimlik === kimlik);
  if(!tr) return null;
  //  Satır, yapışkan şeridin altında kalan alanın ortasına gelir.
  const pay = mUstPay(), r = tr.getBoundingClientRect();
  const orta = pay + Math.max(0, (innerHeight - pay - r.height) / 2);
  const y = mSayfaHedefi(r.top + scrollY - orta);
  window.scrollTo({top: y, behavior: mKaydirma()});
  tr.classList.remove('m-vurgu'); void tr.offsetWidth; tr.classList.add('m-vurgu');
  const git = mBolumDugmesi('m-hesaba-git', kimlik);
  if(git) git.focus({preventScroll: true});
  return y;
}

/*  SÜREN GİDİŞ.  Kaydırma sürerken sonuç yeniden çizilebilir:  α kutusuna
    yazıp doğrudan "Özete dön"e basınca kutudan çıkılır, hesap tazelenir ve
    çizim kaydırmanın ortasına denk gelir.  Eski öğeler silindiği için gidiş
    yeni çizim üzerinde YENİDEN yapılır ( bkz. mYeriKoruyarakCiz ).  Gidiş
    hedefe varınca, kullanıcı tekerleği / fareyi / dokunmayı / klavyeyi
    kullanınca ya da en geç 2,5 sn sonra biter — yenilenen gidiş, kullanıcının
    o arada tıkladığı kutudan odağı çalmasın. */
let M_GIDIS = null;
function mGit(yap){
  M_GIDIS = {yap, hedef: null, bitis: performance.now() + 2500};
  M_GIDIS.hedef = yap();
  if(M_GIDIS.hedef === null) M_GIDIS = null;
}
function mGidisSuruyor(){
  if(M_GIDIS && performance.now() > M_GIDIS.bitis) M_GIDIS = null;
  return !!M_GIDIS;
}
addEventListener('scroll', ()=>{
  if(M_GIDIS && Math.abs(scrollY - M_GIDIS.hedef) < 2) M_GIDIS = null;
}, {passive: true});
for(const olay of ['wheel', 'pointerdown', 'keydown'])
  addEventListener(olay, ()=>{ M_GIDIS = null; }, {passive: true, capture: true});

function mHesabaGit(kimlik){
  if(!document.getElementById(mBolumCapa(kimlik))) return;
  mBolumGirdileriniAc(kimlik);
  mGit(()=>mBolumeIn(kimlik));
}
function mOzeteDon(kimlik){ mGit(()=>mSatiraCik(kimlik)); }

/*  CANLI HESAPTA YER KAYBOLMASIN.  Her girdi değişikliğinde sonuç baştan
    çizilir;  üstteki bir uyarı kalkınca ya da bir bölüm kısalınca, okunan
    hesap ekranda yukarı kayıyordu ( "Hesaba git" ile inip α girildiğinde
    iki uyarı birden kalkar ).
      · süren bir gidiş varsa yeni çizimde yeniden yapılır;
      · yoksa ekranın başındaki bölüm çizimden sonra aynı yere getirilir
        ( özet tablodayken — henüz bir bölüme inilmemişken — yer değişmez );
      · odak "Hesaba git" / "Özete dön" düğmesindeyse yenisine geçer —
        klavyeyle gezen kullanıcı yerini kaybetmez. */
function mGorunenBolum(){
  const pay = mUstPay();
  let son = null;
  for(const s of document.querySelectorAll('#m_sonuc .serit[id]')){
    if(s.getBoundingClientRect().top > pay + 1) break;
    son = s;
  }
  return son ? {id: son.id, ust: son.getBoundingClientRect().top} : null;
}
function mYeriKoruyarakCiz(ciz){
  const gidis = mGidisSuruyor() ? M_GIDIS : null;
  const yer = gidis ? null : mGorunenBolum();
  const e = document.activeElement;
  const odak = e && e.matches && e.matches('#m_sonuc .m-hesaba-git, #m_sonuc .m-ozete-don')
    ? {sinif: e.classList.contains('m-hesaba-git') ? 'm-hesaba-git' : 'm-ozete-don',
       kimlik: e.dataset.kimlik} : null;
  ciz();
  if(gidis){
    gidis.hedef = gidis.yap();
    if(gidis.hedef === null) M_GIDIS = null;
  }else{
    const s = yer && document.getElementById(yer.id);
    if(s) window.scrollBy(0, s.getBoundingClientRect().top - yer.ust);
  }
  const yeni = odak && mBolumDugmesi(odak.sinif, odak.kimlik);
  if(yeni && document.activeElement !== yeni) yeni.focus({preventScroll: true});
}

/* ==========================================================================
   GELİŞMİŞ BÖLÜMLERİ
   Her grubun altında kapalı durur;  ofisin ya da ürünün hep aynı girilen
   değerlerini taşır ( engine/uygulama/mukavemet_girdi.GELISMIS_ALANLAR ).
   GİZLİ DEĞER SESSİZ KALMAMALI:
     · varsayılandan farklı değer sayısı bölüm başlığında yazar ve o alanlar
       işaretlenir — bölümü açmadan "burada değişen bir şey var" görünür;
     · hesabı durduran hata gizli bir alandansa bölüm kendiliğinden açılır;
     · arama gizli alanları da bulur.
   ========================================================================== */
function mGelismisAc(kutu, ac){
  if(!kutu) return;
  kutu.classList.toggle('acik', !!ac);
  kutu.querySelector('.m-gelismis-ic').hidden = !ac;
  kutu.querySelector('.m-gelismis-ok').textContent = ac ? '▾' : '▸';
  kutu.querySelector('.m-gelismis-bas').setAttribute('aria-expanded', ac ? 'true' : 'false');
}

function mGelismisDegistir(kutu){
  if(kutu) mGelismisAc(kutu, !kutu.classList.contains('acik'));
}

function mGelismisleriKapat(){
  document.querySelectorAll('#m_form .m-gelismis').forEach(k=>mGelismisAc(k, false));
}

/*  Alanın değeri sözleşmenin varsayılanından farklı mı?
    Kabin ağırlığının varsayılanı sabit bir sayı değil, beyan yükünün TABLO
    değeridir:  onu hesabın bildirdiği kaynak söyler ( "GİRİŞ" = elle ). */
function mVarsayilandanFarkli(f){
  const e = $(M_ID(f.anahtar));
  if(!e) return false;
  if(f.anahtar === 'kabin_agirligi')
    return !mGkTazelenecek(MUK_AKTIF)
      && ((SON.m && SON.m.girdi) || {}).kabin_agirligi_kaynak === 'GİRİŞ';
  const s = String(e.value ?? '').trim(), d = f.varsayilan;
  //  BOŞ KUTU "DEĞİŞTİRİLDİ" SAYILMAZ.  Boşluk kullanıcının girdiği bir değer
  //  değildir:  S1 · S2 · kuyu genişliği gibi alanlarda motor varsayılana düşer
  //  ( sonuç birebir aynıdır ), öteki alanlarda hesap durur ve sebebini hata
  //  mesajı söyler.  sayiOku('') NaN döndüğü için boş S1/S2 "2 değiştirildi"
  //  diye işaretleniyordu.
  if(s === '') return false;
  if(d === null || d === undefined) return true;
  if(e.tagName === 'SELECT' || typeof d !== 'number') return s !== String(d);
  const x = sayiOku(s);
  return !(isFinite(x) && Math.abs(x - d) < 1e-9);
}

function mGelismisTazele(){
  if(!MUK) return;
  const alan = {};
  for(const f of mAlanlar(x => x.gelismis)) alan[M_ID(f.anahtar)] = f;
  document.querySelectorAll('#m_form .m-gelismis').forEach(k=>{
    let n = 0, gorunur = 0;
    k.querySelectorAll('.m-gelismis-ic .alan').forEach(a=>{
      //  Makine yerleşimine göre hesaba girmeyen alan sayılmaz.
      if(a.classList.contains('kural-disi')) return;
      gorunur++;
      const e = a.querySelector('input,select');
      const f = e && alan[e.id];
      const farkli = !!f && mVarsayilandanFarkli(f);
      a.classList.toggle('degisti', farkli);
      if(farkli) n++;
    });
    //  Bütün alanları bu yerleşimde hesaba girmiyorsa bölüm de görünmez.
    k.hidden = gorunur === 0;
    k.querySelector('.m-gelismis-sayac').textContent = n ? `${n} değiştirildi` : '';
  });
}

/*  Hata metni gizli bir alanın adını taşıyorsa o alanın bölümünü açar.
    Motor hatayı alanın etiketiyle yazar ( mukavemet_girdi.dogrula ). */
function mGelismisHataAc(metinler){
  const liste = (metinler || []).map(String);
  if(!liste.length || !MUK) return;
  for(const f of mAlanlar(x => x.gelismis)){
    if(!liste.some(m => m.includes(f.etiket))) continue;
    const e = $(M_ID(f.anahtar));
    mGelismisAc(e && e.closest('.m-gelismis'), true);
  }
}

/*  Bir bölümü besleyen grup adları.  Anahtar bölümün KİMLİĞİDİR
    ( "aski_halatlari" ) — başlıktaki numara değil.  Motor eskiden tek ad
    döndürüyordu;  dizi gelmeyen ( eski ) sunucuya karşı ikisi de kabul edilir. */
function mBolumGruplari(kimlik){
  const g = (MUK && MUK.bolum_grubu || {})[String(kimlik || '')];
  return !g ? [] : (Array.isArray(g) ? g : [g]);
}


/* ==========================================================================
   ÇOKLU ASANSÖR
   Form tek kopyadır;  aktif asansörün değerleri onda durur.  Asansör
   değişince form MUK_ASANSORLER'e kaydedilir ve ötekinin değerleri yüklenir.
   Proje geneli alanlar ( topraklama · makine dairesi ) TAŞINMAZ — binaya
   aittir, dört asansörde de aynıdır.
   ========================================================================== */
function mAsansorSekmeleriTazele(){
  const k = $('m_asansor_sekmeleri'); if(!k) return;
  if(MOD !== 'uygulama'){ k.innerHTML = ''; return; }
  let h = '';
  for(let i = 0; i < MUK_ADET; i++){
    const ad = ((MUK_ASANSORLER[i] || {}).asansor_adi || '').trim();
    const etkin = i === MUK_AKTIF && !$('s-mukavemet').hidden;
    //  ROZET ASANSÖRE ÖZELDİR.  sekmeRozeti() querySelector ile İLK eşleşeni
    //  bulur;  dört sekmede hepsine aynı rozeti basardı ve hangi asansörün
    //  kaldığı görünmezdi.  Her sekme kendi sonucundan okur.
    const d = ((SON.mc && SON.mc.ozet && SON.mc.ozet.asansorler) || [])[i];
    let rozet = '';
    if(d && d.aktif === false)
      rozet = `<span class="sekme-rozet kirmizi" title="Hesap yapılamadı">!</span>`;
    else if(d && d.tumu_uygun === false)
      rozet = `<span class="sekme-rozet kirmizi" title="Bir ya da daha çok bölüm uygun değil">✕</span>`;
    h += `<button class="sekme${etkin ? ' etkin' : ''}" data-sekme="mukavemet"
                  data-asansor="${i}" onclick="mAsansorSekmesi(${i})"
                  title="${kacis(ad || (i + 1) + ' nolu asansör')}"
          >ASANSÖR ${i + 1}${ad ? ' · ' + kacis(ad.slice(0, 12)) : ''}${rozet}</button>`;
  }
  k.innerHTML = h;
}

/*  Sekmeye tıklamak hem gövdeyi açar hem aktif asansörü değiştirir.
    Dört ayrı sayfa yerine TEK gövde kullanılır ( 4 × 86 alanlık DOM olmasın );
    sekmeler yalnız hangi asansörün formda olduğunu belirler. */
function mAsansorSekmesi(i){
  if(i >= MUK_ADET) i = 0;
  const gecis = i !== MUK_AKTIF;
  if(gecis){ mAsansorKaydet(); MUK_AKTIF = i; mAsansorYukle(i); }
  sekmeGoster('mukavemet');
  mAsansorSekmeleriTazele();
  if(gecis){ yaz(); hesapMukavemet(); }
}

/*  ADET SEÇİMİ.  Azaltmak veriyi SİLMEZ:  haritalar dizide kalır, yalnız
    hesaba ve paftaya girmezler.  3→2→3 yapan mühendis girdilerini geri bulur.
    Artırırken eksik haritalar 1 NOLU ASANSÖRÜN kopyası olarak açılır — bir
    binanın asansörleri çoğunlukla benzerdir, sıfırdan 86 alan doldurtmak
    işkence olurdu. */
function mAdetDegisti(n){
  const azami = (MUK && MUK.asansor_azami) || 4;
  n = Math.max(1, Math.min(azami, parseInt(n, 10) || 1));
  mAsansorKaydet();
  while(MUK_ASANSORLER.length < n){
    const kopya = JSON.parse(JSON.stringify(MUK_ASANSORLER[0] || {}));
    kopya.asansor_adi = '';               // ad kopyalanmaz, karışmasın
    MUK_ASANSORLER.push(kopya);
    //  1. asansörün kabin ağırlığı tablodan yenilenmeyi bekliyorsa kopya da
    //  bekler — yoksa yeni yükün yanına eski kütle kopyalanmış olurdu.
    if(mGkTazelenecek(0)) MUK_GK_TAZELE[MUK_ASANSORLER.length - 1] = ++MUK_GK_SURUM;
  }
  MUK_ADET = n;
  if(MUK_AKTIF >= MUK_ADET){ MUK_AKTIF = MUK_ADET - 1; mAsansorYukle(MUK_AKTIF); }
  if($('m_adet')) $('m_adet').value = String(n);
  mAsansorSekmeleriTazele();
  yaz();
  hesapMukavemet();
}

function mAsansorKaydet(){
  if(!MUK || !Array.isArray(MUK_ASANSORLER) || !MUK_ASANSORLER[MUK_AKTIF]) return;
  MUK_ASANSORLER[MUK_AKTIF] = mFormOku(M_ASANSOR_ALANI);
}

function mAsansorYukle(i){
  const d = MUK_ASANSORLER[i]; if(!d) return;
  mFormaYaz(d, M_ASANSOR_ALANI);
  mGelismisTazele();
}

function mAsansorSec(i){
  if(i < 0 || i >= MUK_ADET) return;
  mAsansorSekmesi(i);
}



/*  Sunucuya gidecek istek:  bütün asansörler + proje geneli.
    Aktif asansör formdan TAZE okunur;  ötekiler haritadan gelir. */
function mukavemetIstek(){
  mAsansorKaydet();
  const pg = mFormOku(f => mProjeGeneliMi(f.anahtar));
  //  Adedin ÜSTÜNDEKİ haritalar dizide durur ama hesaba GİRMEZ.
  const asansorler = MUK_ASANSORLER.slice(0, MUK_ADET).map(d=>({...d}));
  //  Boş kabin kütlesi sunucudan tazelenecekse O ASANSÖRLERDE boşaltılır.
  for(const s of Object.keys(MUK_GK_TAZELE))
    if(asansorler[s]) asansorler[s].kabin_agirligi = '';
  return {asansorler, proje_geneli: pg, sabitler: ofisSabitleri()};
}


/*  PROJE GENELİ HESAPLAR.  Temel topraklama ve makine dairesi aydınlatması
    binaya aittir;  motor bunları her asansörden ayırıp tek listede döndürür
    ( hesap.hesapla_coklu ) ve pafta en sona basar.  Ekranda da asansör
    sekmelerinde değil, PROJE sekmesinde bir kez görünürler. */
function mProjeGeneliCiz(c){
  const kutu = $('p_geneli'); if(!kutu) return;
  const bolumler = (c && c.proje_geneli) || [];
  if(!bolumler.length){ kutu.innerHTML = ''; kutu.parentElement.hidden = true; return; }
  kutu.parentElement.hidden = false;
  const o = (c.ozet || {});
  let h = `<div class="kart-ic"><div class="serit"><span>PROJE GENELİ HESAPLAR</span>
             <span class="kaynak">${bolumler.length} bölüm · bütün asansörler için bir kez</span></div>
           <div class="uyari ${o.proje_geneli_uygun === false ? 'kirmizi' : 'mavi'}"
                style="margin:0 0 12px">Temel topraklama ve makine dairesi
             aydınlatması <b>binaya</b> aittir, asansöre değil: projedeki
             ${o.adet || 1} asansör için bir kez hesaplanır ve paftanın
             <b>en sonunda</b> bir kez basılır.</div>`;
  bolumler.forEach(b=>{ h += bolumCiz(b); });
  kutu.innerHTML = h + '</div>';
}

/*  PROJE sekmesinin sağ sütunu:  bütün asansörlerin durumu bir arada.
    Ayrıntı asansör sekmelerinde;  burada yalnız "hangisi kaldı" görünür. */
function mProjeOzetiCiz(c){
  const kutu = $('p_ozet'); if(!kutu) return;
  if(!c || !c.asansorler){ kutu.innerHTML = ''; return; }
  const liste = (c.ozet && c.ozet.asansorler) || [];
  let h = `<div class="kart-ic"><div class="serit"><span>PROJE ÖZETİ</span>
             <span class="kaynak">${liste.length} asansör</span></div>
           <div class="kaydir"><table class="veri">
             <tr><th>No</th><th>Asansör</th><th>N ( kW )</th><th>Sonuç</th></tr>`;
  liste.forEach(a=>{
    const sinif = a.aktif === false ? 'hata'
                : (a.tumu_uygun === true ? 'ok' : (a.tumu_uygun === false ? 'hata' : ''));
    const metin = a.aktif === false ? 'HESAP YAPILAMADI'
                : (a.genel_sonuc || (a.tumu_uygun ? 'UYGUNDUR.' : 'UYGUN DEĞİLDİR'));
    h += `<tr class="m-gidilir" onclick="mAsansorSec(${a.no - 1})"
              title="${kacis(a.tanim || '')} sekmesine git">
            <td class="etiket">${a.no}</td><td>${kacis(a.tanim || '')}</td>
            <td>${a.N_hesap == null ? '—' : tr(a.N_hesap)}</td>
            <td class="${sinif}">${metin}</td></tr>`;
  });
  kutu.innerHTML = h + '</table></div></div>';
}


/* ═══════════════════════════════════════════════════════════════════
   ÇİZİMLER  —  aynı girdinin ikinci görünümü

   Sağ sütun ya hesabı ya çizimleri gösterir ( m_sag[data-gorunum] ).
   Çizimler AKTİF ASANSÖRÜNDÜR;  girdi değiştikçe hesapla birlikte
   tazelenir — yalnız görünürken, gizliyken boşuna çizilmez.  SVG sunucuda
   çizim modülünden gelir ( cizim/svg.py ) ve pakete giren DXF paftasıyla
   AYNI eleman listesinden çıkar.

   Her çizim kendi <img>'inde durur:  SVG'ler sayfaya gömülünce tarama
   desenlerinin kimlikleri ( #tarama ) çakışıyor, 1/50 kesit 1/20 planın
   desenini alıyordu.
   ═══════════════════════════════════════════════════════════════════ */
ISTEK.cizim = 0;
let M_GORUNUM = 'hesap';
try{ if(localStorage.getItem('m_gorunum') === 'cizim') M_GORUNUM = 'cizim'; }catch(e){}
let M_CIZIM_DURUM = null;          // son çizim yanıtı:  rozet için

function mGorunumSec(ad){
  M_GORUNUM = ad === 'cizim' ? 'cizim' : 'hesap';
  try{ localStorage.setItem('m_gorunum', M_GORUNUM); }catch(e){}
  mGorunumTazele();
  if(M_GORUNUM === 'cizim') cizimleriGetir();
}

function mGorunumTazele(){
  const s = $('m_sag'); if(s) s.dataset.gorunum = M_GORUNUM;
  document.querySelectorAll('#m_gorunum .gorunum-dg').forEach(b=>{
    const secili = b.dataset.gorunum === M_GORUNUM;
    b.classList.toggle('secili', secili);
    b.setAttribute('aria-selected', String(secili));
  });
  //  Çizimler kurulamadıysa düğmede işaret:  hesaba bakan da görsün.
  const dg = document.querySelector('#m_gorunum .gorunum-dg[data-gorunum="cizim"]');
  if(dg){
    const hatali = M_CIZIM_DURUM && M_CIZIM_DURUM.aktif === false;
    dg.innerHTML = 'Çizimler' + (hatali
      ? '<span class="sekme-rozet kirmizi" title="Çizimler kurulamadı">!</span>' : '');
  }
}

async function cizimleriGetir(){
  if(M_GORUNUM !== 'cizim' || !MUK) return;
  const sira = ++ISTEK.cizim;
  const kutu = $('m_cizimler'); if(!kutu) return;
  kutu.classList.add('yukleniyor');
  try{
    const c = await (await fetch('/api/uygulama/cizimler', {method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({kapak: mukavemetKimlik(), ...mukavemetIstek(), asansor: MUK_AKTIF})})).json();
    if(sira !== ISTEK.cizim) return;          // daha yeni istek var
    M_CIZIM_DURUM = c;
    cizCizimler(c);
    mGorunumTazele();
  }catch(e){
    if(sira === ISTEK.cizim)
      kutu.innerHTML = `<div class="kart-ic"><div class="uyari kirmizi">Bağlantı hatası: ${kacis(e)}</div></div>`;
  }finally{
    if(sira === ISTEK.cizim) kutu.classList.remove('yukleniyor');
  }
}

function cizCizimler(c){
  const kutu = $('m_cizimler'); if(!kutu) return;
  const ad = ((MUK_ASANSORLER[MUK_AKTIF] || {}).asansor_adi || '').trim();
  let h = `<div class="pafta-bas"><h2>ÇİZİMLER  ·  ASANSÖR ${MUK_AKTIF + 1}${ad ? ' · ' + kacis(ad) : ''}</h2>
    <div class="alt">Kuyu düşey kesitleri ve planları — hesabın girdisinden ve sonucundan.
      Paftaya "Projeyi paketle" ile hesap sayfalarının sağına girer.</div></div><div class="kart-ic">`;
  if(!c.aktif){
    h += `<div class="uyari kirmizi"><b>Çizimler kurulamadı.</b> Aşağıdakiler düzeltilince
            çizilir ( girdiler solda:  hesabın grupları ve "Çizim" grubu ).
            <ul class="cizim-liste">${(c.hata || []).map(x => `<li>${kacis(x)}</li>`).join('')}</ul></div>`;
  }else{
    if(!c.hesap)
      h += `<div class="uyari sari">Hesap yapılamadı:  kuyu tabanına ve ray konsollarına gelen
              kuvvetler çizimlere yazılmadı.</div>`;
    for(const z of c.cizimler || []){
      const src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(z.svg);
      h += `<figure class="cizim" data-cizim="${kacis(z.ad)}">
              <figcaption>${kacis(z.baslik)} <span class="ipucu">1/${kacis(z.olcek)}</span></figcaption>
              <img alt="${kacis(z.baslik)}" src="${src}"></figure>`;
    }
  }
  kutu.innerHTML = h + '</div>';
}

/*  ÇİZİMDEN GELEN HESAP GİRDİLERİ ( MUK.cizimden ):  kutu boşsa değer
    çizimin geometrisinden gelir ve hesaba o girer.  Kutunun içinde gri
    yazar — hangi sayıyla hesaplandığı görünsün;  kutu boş kalır, değer
    geometriyi izlemeye devam eder. */
function mCizimdenTazele(aktif){
  const g = (aktif && aktif.girdi) || {};
  for(const a of ((MUK && MUK.cizimden) || [])){
    const e = $(M_ID(a)); if(!e) continue;
    const v = g[a];
    e.placeholder = (v === null || v === undefined) ? '' : 'çizimden:  ' + mSayi(v);
  }
}

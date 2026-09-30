// Sunucu yanıtlarının sırasını denetleyerek gerçek arayüz işlevlerini çalıştırır.
// Çalıştırma: node --test testler/olcu_arayuz.test.cjs
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const kaynak = fs.readFileSync(path.join(__dirname, '../hesap/static/uygulama.js'), 'utf8');

async function dene(senaryo) {
  const ctx = vm.createContext({
    assert, ISTEK: {mukavemet: 0}, MUK: {asansor_azami: 4},
    localStorage: {getItem: () => null}, addEventListener() {}, kur() {},
    Event: class {}, kacis: x => String(x),
  });
  vm.runInContext(kaynak, ctx);
  return vm.runInContext(`(async () => {
    const sinif = {add() {}, remove() {}};
    const alan = {tagName: 'INPUT', value: '2100', dispatchEvent() { mAsansorKaydet(); }};
    const cizimler = {classList: sinif, innerHTML: 'ESKİ ÇİZİM'};
    $ = id => id === 'm_cizimler' ? cizimler : id === 'm_kuyu_genisligi' ? alan : null;
    document = {createElement: () => ({style: {}, classList: sinif,
      setAttribute() {}, remove() {}, querySelector: () => ({innerHTML: ''})})};
    const svg = {getBoundingClientRect: () => ({left: 0, top: 0, width: 800}), appendChild() {}};
    const fig = {dataset: {cizim: 'kuyu_plani'}, querySelector: () => svg};
    const olcu = {dataset: {olcu: '0'}, classList: sinif, closest: () => fig,
      querySelector: () => ({textContent: 'KUYU GENİŞLİĞİ 2100'}),
      getBoundingClientRect: () => ({left: 0, bottom: 0})};
    mFormOku = () => ({kuyu_genisligi: alan.value});
    mFormaYaz = g => { alan.value = String(g.kuyu_genisligi); };
    mGelismisTazele = mAsansorSekmeleriTazele = sekmeGoster = yaz = mGorunumTazele = () => {};
    hesapMukavemet = () => new Promise(() => {});
    mOlcuYaz = mOlcuBildir = () => {};
    mOlcuPost = async () => ({aktif: true});
    MUK_ADET = 2;
    MUK_ASANSORLER = [{kuyu_genisligi: '2100'}, {kuyu_genisligi: '2500'}];
    await mOlcuAc(olcu, null);
    const yanit = {aktif: true, dogrulandi: true, degisiklikler: [
      {anahtar: 'kuyu_genisligi', etiket: 'Kuyu genişliği', eski: 2100, deger: 2300}]};
    const genislikler = () => MUK_ASANSORLER.map(a => a.kuyu_genisligi).join(',');
    let yanitla;
    mOlcuPost = () => new Promise(resolve => { yanitla = resolve; });
    ${senaryo}
  })()`, ctx);
}

test('aynı asansörde ölçü değişikliği uygulanır', () => dene(`
  const islem = mOlcuDegistir('kuyu_genisligi', 2300);
  yanitla(yanit); await islem;
  assert.equal(genislikler(), '2300,2500');
`));

test('ölçü yazımı sayıya çevrilmeden sunucuya gider ve ret kutuda gösterilir', () => dene(`
  const hata = {hidden: true, textContent: ''};
  let giden;
  mOlcuPost = async (_yol, ek) => {
    giden = ek.hedef;
    return {aktif: false, hata: ['Belirsiz sayı yazımı']};
  };
  for(const ham of ['2.200', '2,200', '2.200,5', '2,200.5', '2200,5']) {
    M_OLCU.kutu.querySelector = sec => sec === '#m_olcu_hedef' ? {value: ham} : hata;
    await mOlcuUygula('kuyu_genisligi');
    assert.equal(giden, ham);
    assert.equal(hata.hidden, false);
    assert.equal(hata.textContent, 'Belirsiz sayı yazımı');
    assert.equal(genislikler(), '2100,2500');
  }
`));

test('sekme değişince gecikmiş yanıt diğer asansöre yazılmaz', () => dene(`
  const islem = mOlcuDegistir('kuyu_genisligi', 2300);
  mAsansorSekmesi(1);
  yanitla(yanit); await islem;
  assert.equal(genislikler(), '2100,2500');
  assert.equal(alan.value, '2500');
  assert.equal(M_OLCU, null);
`));

test('ilk asansöre geri dönmek iptal edilmiş işlemi canlandırmaz', () => dene(`
  const islem = mOlcuDegistir('kuyu_genisligi', 2300);
  mAsansorSekmesi(1); mAsansorSekmesi(0);
  yanitla(yanit); await islem;
  assert.equal(genislikler(), '2100,2500');
`));

test('asansör adedi azaltılınca açık ölçü iptal edilir', () => dene(`
  mAsansorSekmesi(1);
  mOlcuPost = async () => ({aktif: true});
  await mOlcuAc(olcu, null);
  mOlcuPost = () => new Promise(resolve => { yanitla = resolve; });
  const islem = mOlcuDegistir('kuyu_genisligi', 2300);
  mAdetDegisti(1);
  yanitla(yanit); await islem;
  assert.equal(genislikler(), '2100,2500');
  assert.equal(alan.value, '2100');
`));

test('uyarı onayı bekleyen ölçü sekme değişince uygulanamaz', () => dene(`
  const islem = mOlcuDegistir('kuyu_genisligi', 2300);
  yanitla({...yanit, uyarilar: ['Yerleşim kontrol edilmeli.']}); await islem;
  mAsansorSekmesi(1);
  mOlcuYazdir();
  assert.equal(genislikler(), '2100,2500');
`));

test('eski çizim kaldırılır ve gecikmiş çizim yanıtı geri getiremez', () => dene(`
  M_GORUNUM = 'cizim';
  let cizimYanitla, cizildi = false;
  fetch = () => new Promise(resolve => { cizimYanitla = resolve; });
  mukavemetKimlik = () => ({}); ofisSabitleri = () => ({});
  cizCizimler = () => { cizildi = true; };
  const islem = cizimleriGetir();
  mAsansorSekmesi(1);
  assert.ok(!cizimler.innerHTML.includes('ESKİ ÇİZİM'));
  cizimYanitla({json: async () => ({aktif: true, hesap: true, cizimler: []})});
  await islem;
  assert.equal(cizildi, false);
`));

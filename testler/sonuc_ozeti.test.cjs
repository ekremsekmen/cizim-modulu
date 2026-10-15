// Uygulama sonuç özetinin yardımcıları:  uygun olmayan bölümleri sayma,
// sekme rozeti ve proje özeti ( 15 Eki ).
// Çalıştırma: node --test testler/sonuc_ozeti.test.cjs
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const kaynak = fs.readFileSync(path.join(__dirname, '../hesap/static/uygulama.js'), 'utf8');

function baglam() {
  const kutular = {};
  const ctx = vm.createContext({
    ISTEK: {}, MUK: {asansor_azami: 4},
    localStorage: {getItem: () => null}, addEventListener() {}, kur() {},
    Event: class {}, kacis: x => String(x), tr: x => String(x),
  });
  vm.runInContext(kaynak, ctx);
  ctx.kutular = kutular;
  vm.runInContext(`$ = id => (kutular[id] = kutular[id] || {innerHTML: '', id});`, ctx);
  return ctx;
}

const bolum = (baslik, uygun, metin) => ({baslik, kimlik: baslik, sonuc: {uygun, metin}});

test('uygun olmayanlar:  bilgi bölümü ( uygun:null ) sayılmaz', () => {
  const ctx = baglam();
  const l = ctx.mUygunOlmayanlar({bolumler: [
    bolum('1', false, 'UYGUN DEĞİLDİR'), bolum('2', true, 'UYGUNDUR'), bolum('9', null, 'FKR = …'),
  ]});
  assert.equal(l.length, 1);
  assert.equal(ctx.mUygunOlmayanlar(null).length, 0);
});

test('hesabı eksik bölüm "uygun değil" diye sayılmaz', () => {
  const ctx = baglam();
  const l = [bolum('4', false, 'UYGUN DEĞİLDİR — dh < 8'), bolum('6', false, 'HESAP EKSİK — α girilmedi')];
  assert.equal(ctx.mUygunOlmayanMetni(l), '1 bölüm uygun değil · 1 bölümün hesabı eksik');
  assert.equal(ctx.mUygunOlmayanMetni([l[0]]), '1 bölüm uygun değil');
  assert.equal(ctx.mUygunOlmayanMetni([l[1]]), '1 bölümün hesabı eksik');
});

test('proje özeti:  proje geneli reddedilince sebep yazılır ( boş kalmaz )', () => {
  const ctx = baglam();
  ctx.mProjeOzetiCiz({aktif: false, hata: ['Ofis standardı · Toprak özgül direnci aralık dışı']});
  const h = ctx.kutular.p_ozet.innerHTML;
  assert.match(h, /hesap yapılamadı/);
  assert.match(h, /Toprak özgül direnci aralık dışı/);
});

test('proje özeti:  proje geneli hesaplar da satır olarak görünür', () => {
  const ctx = baglam();
  const c = {
    asansorler: [{}],
    proje_geneli: [bolum('3 - TOPRAKLAMA', false, 'Re > sınır'), bolum('1 - YATAY', null, '')],
    ozet: {proje_geneli_uygun: false, asansorler: [{no: 1, tanim: '1 nolu', aktif: true, tumu_uygun: true, N_hesap: 5}]},
  };
  ctx.mProjeOzetiCiz(c);
  const h = ctx.kutular.p_ozet.innerHTML;
  assert.match(h, /Proje geneli \( 2 bölüm \)/);
  assert.match(h, /1 bölüm uygun değil/);
  assert.match(h, /mProjeGeneline\(\)/);
  c.ozet.proje_geneli_uygun = true;
  c.proje_geneli[0].sonuc.uygun = true;
  ctx.mProjeOzetiCiz(c);
  assert.match(ctx.kutular.p_ozet.innerHTML, /Proje geneli[\s\S]*UYGUNDUR\./);
});

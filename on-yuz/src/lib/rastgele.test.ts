/*  RASTGELE İŞLEM DİZİLERİ ( 24 Eki ) — örnek testleri hatanın kendisini korur,
    bunlar TÜRÜNÜ arar:  "asansöre ait her veri kendi asansörüyle gider".
    Tohumlu rastgele dizilerde ( ekle, kaldır, adet, geri al, kapağa yaz, girdi,
    temiz çizim, dosyaya kaydet / aç, yeniden yükle ) her adımdan sonra uygulamanın
    SIRAYLA tuttuğu durum, asansörün KİMLİĞİYLE tutulan bir modelle karşılaştırılır.
    İşlemler ekranın yaptığının aynısıdır ( Calisma, ProjeBilgileri, AvanCalisma ).
    Kırılan dizi tohumu ve adımlarıyla yazılır:  yeniden üretilir.            */
import { afterEach, describe, expect, it, vi } from "vitest";
import { alanYaz, asansorAdedi, asansorEkle, asansorKaldir, projeOku, siraKaydir, type Ham, type UygulamaProjesi } from "./proje";
import { dosyaGovdesi, dosyaOku } from "./dosya";
import { avanDosyaGovdesi, avanOku, BOS_AVAN, trafikSutunuKaldir, trafikSutununuYaz, type AvanProjesi } from "./avan";
import type { AvanKoprusu } from "./api";
import { rastgele, SECENEKLER, SEMA, TOHUM_SAYISI } from "./test-semasi";

const AZAMI = 4;
const ADIM = 40;

/**  Kırılan ilk tohum:  hangi adımda, hangi diziden sonra  */
function dene(ad: string, tek: (tohum: number, iz: string[]) => void) {
  for (let tohum = 1; tohum <= TOHUM_SAYISI; tohum++) {
    const iz: string[] = [];
    try {
      tek(tohum, iz);
    } catch (e) {
      throw new Error(`${ad} — tohum ${tohum}, ${iz.length}. adımda kırıldı:\n  ${iz.join("\n  ")}\n${(e as Error).message}`, {
        cause: e,
      });
    }
  }
}

/**  Tarayıcıdaki kayıttan okuma ( yeniden yükleme ve dosyadan açılan proje bu yoldan )  */
function kayittan(p: UygulamaProjesi): UygulamaProjesi {
  vi.stubGlobal("localStorage", { getItem: () => JSON.stringify(p) });
  return projeOku(p.id)!;
}
afterEach(() => vi.unstubAllGlobals());

/* ───────────────────────────── uygulama:  asansörler ve kapak */
//  Kuyu genişliği varsayılandan ( 2400 ) farklı:  dosya varsayılana eşit değeri yazılmamış sayar
const KUYU = ["1800", "2000", "2200"];
const OZGU = ["capacity", "speed", "stops", "cabin_width"];

interface Model {
  adlar: string[];
  kuyu: Record<string, string | undefined>;
  /**  Asansörün kimliği → kapakta ona özgü değerler  */
  ozgu: Record<string, Record<string, string>>;
  hepsi: Record<string, string>;
}

function beklenenKapak(m: Model) {
  const k: Record<string, string> = { ...m.hepsi };
  m.adlar.forEach((ad, i) => Object.entries(m.ozgu[ad] ?? {}).forEach(([alan, v]) => (k[`${alan}.${i + 1}`] = v)));
  return k;
}
const dolu = (k: Ham | undefined) => Object.fromEntries(Object.entries(k ?? {}).filter(([, v]) => v !== ""));

function uygulamaDizisi(tohum: number, iz: string[]) {
  const R = rastgele(tohum);
  let sayac = 1;
  let p: UygulamaProjesi = {
    id: "t",
    tur: "uygulama",
    kimlik: { project_title: "", owner: "", sheet_no: "" },
    asansorler: [{ asansor_adi: "A1", kuyu_genisligi: "2000" }],
    proje_geneli: {},
    kapak: {},
    guncellendi: 0,
  };
  let m: Model = { adlar: ["A1"], kuyu: { A1: "2000" }, ozgu: { A1: {} }, hepsi: {} };
  //  Kaldırmanın "Geri al"ı:  önceki proje ve model ( Calisma:  girdi, kapak, ekleme kapatır )
  let geri: { p: UygulamaProjesi; m: Model } | null = null;
  //  Ekranın sırayla tuttuğu son temiz girdi ( useSunucu ):  sıra → çizildiği asansörün adı
  let temiz: Record<number, string> = {};
  const yeniler = (once: number) => {
    for (let i = once; i < p.asansorler.length; i++) {
      const ad = `A${++sayac}`;
      p = alanYaz(p, SEMA, i, "asansor_adi", ad);
      m.adlar.push(ad);
      m.kuyu[ad] = m.kuyu[m.adlar[0]];
      m.ozgu[ad] = {};
    }
  };
  const unut = (adlar: string[]) => adlar.forEach((ad) => (delete m.ozgu[ad], delete m.kuyu[ad]));

  for (let s = 0; s < ADIM; s++) {
    const n = p.asansorler.length;
    const once = p.asansorler;
    const islem = R.sec(["ekle", "kaldir", "kaldir", "adet", "geri", "kapak", "kapak", "hepsi", "girdi", "temiz", "dosya", "yenile"]);
    if (islem === "ekle" && n < AZAMI) {
      p = asansorEkle(p, AZAMI);
      yeniler(n);
      geri = null;
      iz.push("ekle");
    } else if (islem === "kaldir" && n > 1) {
      const i = R.tam(n);
      geri = { p, m: structuredClone(m) };
      p = asansorKaldir(p, i);
      unut(m.adlar.splice(i, 1));
      iz.push(`kaldır ${i + 1}`);
    } else if (islem === "adet") {
      const k = 1 + R.tam(AZAMI);
      if (k < n) {
        geri = { p, m: structuredClone(m) };
        p = asansorAdedi(p, k, AZAMI);
        unut(m.adlar.splice(k));
      } else if (k > n) {
        p = asansorAdedi(p, k, AZAMI);
        yeniler(n);
        geri = null;
      }
      iz.push(`adet ${k}`);
    } else if (islem === "geri" && geri) {
      p = { ...p, asansorler: geri.p.asansorler, kapak: geri.p.kapak };
      m = geri.m;
      geri = null;
      iz.push("geri al");
    } else if (islem === "kapak") {
      //  ProjeBilgileri:  "N. asansör" seçili kutuya yazılan ( boş = silinen )
      const i = R.tam(n);
      const alan = R.sec(OZGU);
      const v = R.olasi(0.15) ? "" : `${m.adlar[i]}:${alan}:${R.tam(1000)}`;
      p = { ...p, kapak: { ...p.kapak, [`${alan}.${i + 1}`]: v } };
      if (v) m.ozgu[m.adlar[i]][alan] = v;
      else delete m.ozgu[m.adlar[i]][alan];
      geri = null;
      iz.push(`kapak ${alan}.${i + 1}`);
    } else if (islem === "hepsi") {
      const alan = R.sec(OZGU);
      const v = `hepsi:${alan}:${R.tam(1000)}`;
      p = { ...p, kapak: { ...p.kapak, [alan]: v } };
      m.hepsi[alan] = v;
      geri = null;
      iz.push(`kapak ${alan} ( hepsi )`);
    } else if (islem === "girdi") {
      const i = R.tam(n);
      const v = R.sec(KUYU);
      p = alanYaz(p, SEMA, i, "kuyu_genisligi", v);
      m.kuyu[m.adlar[i]] = v;
      geri = null;
      iz.push(`kuyu ${i + 1} = ${v}`);
    } else if (islem === "temiz") {
      //  Seçili asansörün çizimi temiz geldi ( useSunucu:  son temiz girdi yazılır )
      const i = R.tam(n);
      temiz = { ...temiz, [i]: m.adlar[i] };
      iz.push(`temiz çizim ${i + 1}`);
    } else if (islem === "dosya") {
      const o = dosyaOku(JSON.stringify(dosyaGovdesi(p, SEMA, {})), SEMA, {});
      if (!o.tamam) throw new Error(o.hata);
      p = kayittan({ ...p, ...o.icerik });
      geri = null;
      iz.push("dosyaya kaydet → aç");
    } else if (islem === "yenile") {
      p = kayittan(p);
      geri = null;
      iz.push("yeniden yükle");
    } else continue;

    temiz = siraKaydir(temiz, once, p.asansorler);
    expect({
      adlar: p.asansorler.map((h) => h.asansor_adi),
      kuyu: p.asansorler.map((h) => h.kuyu_genisligi),
      kapak: dolu(p.kapak),
      temiz: Object.entries(temiz).filter(([i, ad]) => ad !== m.adlar[Number(i)]),
    }).toEqual({ adlar: m.adlar, kuyu: m.adlar.map((ad) => m.kuyu[ad]), kapak: beklenenKapak(m), temiz: [] });
  }
}

/* ───────────────────────────── avan:  trafik sütunları ve avan kartları
    Kartlar trafiğin verdiği asansörlerin sırasıyladır ( köprü:  kapasiteli her
    sütunun asansörü;  tek kapasiteli sütunda gereken adet kadar — burada yalnız
    ilk kart denetlenir ).  Kullanıcı k. karta yazarken k. kapasiteli sütunun
    asansörüne yazar ( kart onun kapasitesini gösterir ).  Sütunun kimliği
    durak kutusunda taşınır ( dosyadan da geçer ).  Denetlenen:  bir kartta
    BAŞKA bir sütunun asansörünün değeri durmaz.                               */
function avanDizisi(tohum: number, iz: string[]) {
  const R = rastgele(tohum);
  let sayac = 11;
  //  Yeni avan projesinde 1. sütunun kapasitesi seçilmemiştir ( BOS_AVAN );  eklenen sütun onun kopyası
  let p: AvanProjesi = {
    ...BOS_AVAN,
    trafikAsansorleri: [R.olasi(0.5) ? { durak: "11" } : { P: "8", durak: "11" }],
    avanAsansorleri: [{}, {}, {}, {}],
  };
  const kapasiteli = () => p.trafikAsansorleri.filter((a) => (a.P ?? "") !== "");
  const kopru = (): AvanKoprusu | null => {
    const k = kapasiteli();
    if (!k.length) return null;
    const bir = (a: Ham) => ({ P: Number(a.P), V: 1, toplam_seyahat: 30 });
    return { tip: "Konut", N: 10, bodrum: 0, h: 3, adet: k.length, asansorler: k.map(bir) };
  };

  for (let s = 0; s < ADIM; s++) {
    const n = p.trafikAsansorleri.length;
    const islem = R.sec(["ekle", "kaldir", "kapasite", "kart", "kart", "dosya"]);
    if (islem === "ekle" && n < AZAMI) {
      //  AvanCalisma "Asansör tipi ekle":  1. sütunun kopyası;  kimliği yeni
      p = { ...p, trafikAsansorleri: [...p.trafikAsansorleri, { ...p.trafikAsansorleri[0], durak: String(++sayac) }] };
      iz.push("sütun ekle");
    } else if (islem === "kaldir" && n > 1) {
      const i = 1 + R.tam(n - 1);
      p = trafikSutunuKaldir(p, i);
      iz.push(`sütun ${i + 1} kaldır`);
    } else if (islem === "kapasite") {
      //  AvanCalisma TrafikAdimi ay():  kapasite seçilir ( ekranın listesinde boş seçenek
      //  yok;  boşaltma yine denenir — işlev iki yönde de kartı taşır )
      const i = R.tam(n);
      const d = R.olasi(0.1) ? "" : R.sec(["8", "10", "13"]);
      p = trafikSutununuYaz(p, i, "P", d);
      iz.push(`sütun ${i + 1} kapasite ${d || "boş"}`);
    } else if (islem === "kart") {
      const k = kapasiteli();
      if (!k.length) continue;
      const i = k.length === 1 ? 0 : R.tam(Math.min(k.length, AZAMI));
      const v = `${k[i].durak}:${R.tam(1000)}`;
      p = { ...p, avanAsansorleri: p.avanAsansorleri.map((a, j) => (j === i ? { ...a, tanim: v } : a)) };
      iz.push(`kart ${i + 1} ( sütun ${k[i].durak} )`);
    } else if (islem === "dosya") {
      const o = avanOku(JSON.stringify(avanDosyaGovdesi(p, SECENEKLER, {}, kopru())), SECENEKLER, {});
      if (!o.tamam) throw new Error(o.hata);
      p = o.proje;
      iz.push("dosyaya kaydet → aç");
    } else continue;

    const k = kapasiteli();
    const goster = k.length === 1 ? 1 : Math.min(k.length, AZAMI);
    for (let i = 0; i < goster; i++) {
      const t = p.avanAsansorleri[i]?.tanim;
      if (t !== undefined && !t.startsWith(`${k[i].durak}:`))
        throw new Error(`${i + 1}. kart ( sütun ${k[i].durak} ) başka sütunun değerini taşıyor:  ${t}`);
    }
  }
}

describe("rastgele işlem dizileri:  asansöre ait veri kendi asansörüyle gider", () => {
  it("uygulama:  kapağın asansöre özgü değerleri, girdiler ve son temiz girdi ( ekle, kaldır, adet, geri al, dosya, yenile )", () => {
    dene("uygulama", uygulamaDizisi);
  });
  it("avan:  trafik sütunu ile avan kartı ( ekle, kaldır, kapasite, kart, dosya )", () => {
    dene("avan", avanDizisi);
  });
});

/**  MAKİNE DAİRESİ KAPISINI SÜRÜKLEME ( 17 Kas — kullanıcı:  "sağdaki soldaki karşıdaki duvara
     da geçmesi lazım" ):  kapı işaretçiye en yakın duvara oturur, o duvar boyunca kayar.

     Çizimin düzlemi ( mm, y yukarı — sunucu:  makine_dairesi._duvar_seridi ):  ön duvar y0'da,
     arka y1'de, sol x0'da, sağ x1'de;  "köşeden uzaklık" ön / arka duvarda x0'dan x boyunca,
     yan duvarlarda y0'dan y boyunca.  Kapı boşluğu duvarın kalınlığı içinde çizilir.  */

export type Duvar = "Ön" | "Arka" | "Sol" | "Sağ";
export const DUVARLAR: Duvar[] = ["Ön", "Arka", "Sol", "Sağ"];

/**  Sunucunun çizimle gönderdiği ( cizim_uclari._kapi_bilgisi ):  kapının duvarı, köşeden
     uzaklığı, eni ve odanın iç ölçüleri ( genislik x, derinlik y boyunca )  */
export interface KapiBilgisi {
  duvar: Duvar;
  konum: number;
  en: number;
  genislik: number;
  derinlik: number;
}
export interface Kutu {
  x: number;
  y: number;
  w: number;
  h: number;
}
/**  Odanın iç köşeleri ve duvarın kalınlığı  */
export interface Oda {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
  t: number;
}
export interface KapiYeri {
  duvar: Duvar;
  konum: number;
}

/**  Taşımanın adımı ( mm ) ve köşeden en küçük uzaklık ( girdi sıfırdan büyük olmalı )  */
export const ADIM_MM = 10;
export const ASGARI_KONUM = 10;

const yatay = (d: Duvar) => d === "Ön" || d === "Arka";

/**  Duvarın iç boyu ( kapının kaydığı uzunluk )  */
export const duvarBoyu = (k: Pick<KapiBilgisi, "genislik" | "derinlik">, d: Duvar) => (yatay(d) ? k.genislik : k.derinlik);

/**  Odanın çizimdeki yeri, kapı boşluğunun çizimdeki kutusundan ( b — getBBox ):  çizim nereye
     ötelenmiş olursa olsun doğrudur.  */
export function odayiBul(k: KapiBilgisi, b: Kutu): Oda {
  const t = yatay(k.duvar) ? b.h : b.w;
  const x0 = k.duvar === "Sol" ? b.x + t : k.duvar === "Sağ" ? b.x - k.genislik : b.x - k.konum;
  const y0 = k.duvar === "Ön" ? b.y + t : k.duvar === "Arka" ? b.y - k.derinlik : b.y - k.konum;
  return { x0, y0, x1: x0 + k.genislik, y1: y0 + k.derinlik, t };
}

/**  Kapı boşluğunun kutusu ( makine_dairesi._oda_ve_kapi )  */
export function kapiKutusu(o: Oda, y: KapiYeri, en: number): Kutu {
  if (y.duvar === "Ön") return { x: o.x0 + y.konum, y: o.y0 - o.t, w: en, h: o.t };
  if (y.duvar === "Arka") return { x: o.x0 + y.konum, y: o.y1, w: en, h: o.t };
  if (y.duvar === "Sol") return { x: o.x0 - o.t, y: o.y0 + y.konum, w: o.t, h: en };
  return { x: o.x1, y: o.y0 + y.konum, w: o.t, h: en };
}

/**  Kapının bir duvarda alabileceği en büyük köşeden uzaklık ( adıma yuvarlanmış );  kapı o
     duvara sığmıyorsa null  */
export function azamiKonum(k: Pick<KapiBilgisi, "genislik" | "derinlik" | "en">, d: Duvar): number | null {
  const m = Math.floor((duvarBoyu(k, d) - k.en + 1e-6) / ADIM_MM) * ADIM_MM;
  return m >= ASGARI_KONUM ? m : null;
}

/**  İşaretçinin ( n — çizim düzleminde ) gösterdiği kapı yeri:  en yakın duvar ( iç yüzünün
     doğru parçasına uzaklık ), o duvar boyunca tutuş noktası ( tutus:  kapının başından
     işaretçiye, mm ) korunarak;  adıma yuvarlanır, duvarın iki ucunda durur.  simdiki:  geçerli
     duvar — öteki duvar ancak belirgin biçimde ( GECIS_PAYI ) daha yakınsa geçilir, köşede
     kapı iki duvar arasında titremez.  */
const GECIS_PAYI = 40;
export function kapiYeri(o: Oda, k: KapiBilgisi, n: { x: number; y: number }, tutus: number, simdiki: Duvar = k.duvar): KapiYeri {
  const sik = (v: number, a: number, b: number) => Math.min(Math.max(v, a), b);
  let en: Duvar = simdiki;
  let enUzak = Infinity;
  for (const d of DUVARLAR) {
    if (azamiKonum(k, d) === null) continue;
    //  İç yüzün doğru parçasına uzaklık
    const dx = yatay(d) ? n.x - sik(n.x, o.x0, o.x1) : n.x - (d === "Sol" ? o.x0 : o.x1);
    const dy = yatay(d) ? n.y - (d === "Ön" ? o.y0 : o.y1) : n.y - sik(n.y, o.y0, o.y1);
    const uzak = Math.hypot(dx, dy) - (d === simdiki ? GECIS_PAYI : 0);
    if (uzak < enUzak) {
      en = d;
      enUzak = uzak;
    }
  }
  const azami = azamiKonum(k, en) ?? ASGARI_KONUM;
  //  Duvar değişince kapı işaretçiye ortalanır ( tutuş eski duvarın eksenindeydi )
  const pay = en === simdiki && en === k.duvar ? tutus : k.en / 2;
  const boyunca = yatay(en) ? n.x - o.x0 : n.y - o.y0;
  const konum = sik(Math.round((boyunca - pay) / ADIM_MM) * ADIM_MM, ASGARI_KONUM, azami);
  return { duvar: en, konum };
}

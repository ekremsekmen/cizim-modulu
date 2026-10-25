/*  PROJENİN DURUMU — açılış listesindeki ( "Son projeler" ) hüküm.

    PROJENİN BÜTÜNÜNÜN hükmüdür — ekranda seçili asansörün ya da bağlantının değil.
    24 Eki:  ikinci asansör hesaplanamazken birinciye geçilince proje "Uygun"
    görünüyordu;  hesabı eksik proje ve proje geneli "uygun değil" ( topraklama )
    de "Uygun" sayılıyordu — liste hükmü kendisi kuruyordu.  Uygulama projesinin
    hükmü artık MOTORDAN ( uygulama_hesabi.proje_hukmu — asansörlerinkiyle aynı
    kural ):  burada yalnız okunur.

    GİRDİSİNİNDİR:  durum hesaplandığı girdinin iziyle ( izi ) saklanır;  liste
    yalnız kayıttaki girdinin — bugünkü ofis standardıyla — durumunu gösterir,
    yoksa "Hesaplanmadı" ( girdi değişip sonuç gelmeden sekme kapanınca eski
    hüküm yeni girdinin sanılmasın ).

    PROJE KAYDINDAN AYRI DURUR ( asansor:durum:<kimlik> ):  türetilmiş değerdir.
    24 Eki:  sekmeler arası eşitlenen proje kaydına yazılıyordu;  aynı proje iki
    sekmede farklı asansör seçili açıkken her sekme öbürünün yazdığını görüp
    kendi hükmünü yeniden yazıyordu ( 4,5 sn'de sekme başına 1.100 kayıt ).  Bu
    anahtarı dinleyen yoktur:  döngü kurulamaz;  aynı girdinin hükmü her sekmede
    aynıdır, aynı değer yeniden yazılmaz.                                      */
import type { AvanKoprusu, AvanYaniti, Bolum, CokluYanit, ProjeHukmu, TrafikYaniti } from "./api";
import { depoOku, depoSil, depoYaz } from "./depo";

/**  Motorun durum adları ( uygulama_hesabi.proje_hukmu ):  durdu — kural dışı girdi
     ya da hesaplanamayan asansör / adım;  eksik — yapılamayan zorunlu hesap  */
export type Hukum = ProjeHukmu["durum"];

export interface ProjeDurumu {
  /**  Hesaplandığı girdinin izi  */
  iz: string;
  hukum: Hukum;
  /**  Asansör sayısı  */
  adet: number;
  /**  "Uygun değil" bölüm sayısı ( proje geneli dahil )  */
  uygunDegil: number;
}

const anahtar = (kimlik: string) => `asansor:durum:${kimlik}`;
const HUKUMLER: Hukum[] = ["durdu", "eksik", "uygun_degil", "uygun"];

export function durumOku(kimlik: string): ProjeDurumu | null {
  try {
    const d = JSON.parse(depoOku(anahtar(kimlik)) || "null");
    return d && typeof d.iz === "string" && HUKUMLER.includes(d.hukum) ? (d as ProjeDurumu) : null;
  } catch {
    return null;
  }
}

/**  Değişmediyse yazılmaz  */
export function durumYaz(kimlik: string, d: ProjeDurumu) {
  const m = JSON.stringify(d);
  if (depoOku(anahtar(kimlik)) !== m) depoYaz(anahtar(kimlik), m);
}

export function durumSil(kimlik: string) {
  depoSil(anahtar(kimlik));
}

/**  Saklanan durum bu girdinin mi ( değilse liste göstermez )  */
export function girdininDurumu(kimlik: string, iz: string): ProjeDurumu | undefined {
  const d = durumOku(kimlik);
  return d?.iz === iz ? d : undefined;
}

/**  Değerin izi:  anahtar sırasından bağımsız ( aynı değerler → aynı iz );  53 bitlik özet  */
export function izi(deger: unknown): string {
  const m = kararliMetin(deger);
  let h1 = 0xdeadbeef;
  let h2 = 0x41c6ce57;
  for (let i = 0; i < m.length; i++) {
    const c = m.charCodeAt(i);
    h1 = Math.imul(h1 ^ c, 2654435761);
    h2 = Math.imul(h2 ^ c, 1597334677);
  }
  h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
  h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
  return (4294967296 * (2097151 & h2) + (h1 >>> 0)).toString(36);
}

function kararliMetin(d: unknown): string {
  if (Array.isArray(d)) return `[${d.map(kararliMetin).join(",")}]`;
  if (d && typeof d === "object") {
    const o = d as Record<string, unknown>;
    const k = Object.keys(o)
      .filter((x) => o[x] !== undefined)
      .sort();
    return `{${k.map((x) => `${JSON.stringify(x)}:${kararliMetin(o[x])}`).join(",")}}`;
  }
  return JSON.stringify(d) ?? "null";
}

/**  UYGULAMA PROJESİ ( /api/uygulama/coklu ):  motorun hükmü.  İstek bütünüyle
     reddedildiyse hesap durdu;  yanıt hükümsüzse bilinmiyor ( yazılmaz ).
     adet:  projenin asansör sayısı ( reddedilen yanıtta liste gelmez ).  */
export function uygulamaHukmu(y: CokluYanit, adet: number): Omit<ProjeDurumu, "iz"> | undefined {
  if (!y.aktif) return { hukum: "durdu", adet, uygunDegil: 0 };
  const h = y.ozet?.proje_hukmu;
  return h && { hukum: h.durum, adet, uygunDegil: h.uygun_degil };
}

/**  AVAN PROJESİ ( trafik + avan hesapları ) — motorun avan için bütün hükmü yok:
     avan ekranının gösterdikleri birleşir.  Trafik ya da bir asansörün avan hesabı
     yapılamadıysa hesap durdu ( ekranın "eksik" adımı );  sunucunun "uygun değil"
     dediği bölüm, trafik ölçütü ya da engelleyici uyarı varsa uygun değil;  yoksa
     uygun.  avan:  trafik avan asansörü verdiyse ( kopru ) onun hesabı.  */
export function avanHukmu(t: TrafikYaniti, kopru: AvanKoprusu | null, avan?: AvanYaniti): Omit<ProjeDurumu, "iz"> {
  const adet = kopru?.asansorler.length ?? 0;
  const durdu = { hukum: "durdu" as const, adet, uygunDegil: 0 };
  if (t.hata || !kopru || !avan || avan.hata) return durdu;
  //  Avan ekranı da bunu "eksik" sayar:  girdisi tamamlanmamış asansörün hesabı yok
  if ((avan.asansorler ?? []).some((a) => !a.aktif && a.uyari)) return durdu;
  const bolumler: Bolum[] = [
    ...(t.bolumler ?? []),
    ...(avan.asansorler ?? []).flatMap((a) => a.bolumler ?? []),
    ...(avan.makine_dairesi?.bolumler ?? []),
    ...(avan.topraklama?.bolumler ?? []),
  ];
  const uygunDegil = bolumler.filter((b) => b.sonuc?.uygun === false).length;
  const olcutKaldi = (t.ozet?.karar_olcutleri ?? []).some((k) => !k.uygun);
  const hukum = uygunDegil || olcutKaldi || avan.engelleyici?.length ? "uygun_degil" : "uygun";
  return { hukum, adet, uygunDegil };
}

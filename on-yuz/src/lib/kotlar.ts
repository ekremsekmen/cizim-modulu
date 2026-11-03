/*  KOTLA GİRİŞ ( sunucu:  cizim/katlar.py · tasarim/alanlar KAT GİRİŞİ )
    Durak kotları doluysa katlar KOTLA girilir:  durak adedi, seyir, kat
    yükseklikleri, kuyu dibi, son kat ve tabliye kotlardan TÜRER — sunucuda, tek
    yerde ( katlar.kot_tablosu ).  Bu dosya yalnız GİRİŞİ kolaylaştırır:  kotu okur
    ve yazar, farkı kota çevirir ( kat-kat arası:  üstündekiler birlikte kayar ),
    ölçüleri kotlara çevirir ( kotsuz proje açılırken — proje.kotlayaCevir;  2 Kas'tan
    beri ekranda yalnız kotla giriş var ).  Türetilenin kendisini sunucunun kullandığı
    değerden alır ( yanıtın girdisi ).  Ön yüz sunucudan SIKI OLAMAZ:  okunamayan
    yazım olduğu gibi gider, sebebini sunucu söyler — burada okunamayan kot yalnız
    hesaplanmaz ( null ).                                                      */
import type { Deger } from "./api";

type Ham = Record<string, string>;

/**  Kotla girişin kot kutuları ( sunucunun şemasında kip "kot" + kipi belirleyen alan )  */
export const DURAK_KOTLARI = "durak_kotlari";
export const KUYU_DIBI_KOTU = "kuyu_dibi_kotu";
export const KUYU_TAVANI_KOTU = "kuyu_tavani_kotu";
export const MD_ZEMINI_KOTU = "md_zemini_kotu";
/**  Ölçüden türeyen ( kotla girişte okunmayan ) kutular — sunucunun kot_kipi.gizli.kotla'sı  */
export const TURETILEN = [
  "durak_adedi",
  "seyir_mesafesi",
  "kat_yukseklikleri",
  "kuyu_dibi",
  "son_kat_yuksekligi",
  "tabliye_yuksekligi",
] as const;

const KOT = /^([+\-−–±]?)(\d+)(?:([.,])(\d+))?$/;

/**  Bir kotun yazımı → mm ( tam sayı ):  metre, işaretli, nokta da virgül de ondalık,
     mm'ye kadar ( sondaki sıfırlar geçer ).  Okunamazsa null:  noktalı üç ondalık
     ( "1.200" — sunucuda belirsiz ), mm'den ince, sıfır dışında "±".  */
export function kotOku(m: string | undefined): number | null {
  const r = KOT.exec((m ?? "").replace(/\s/g, ""));
  if (!r) return null;
  const [, isaret, tam, ayrac, ondalik = ""] = r;
  if (ayrac === "." && ondalik.length === 3 && /^[1-9]\d{0,2}$/.test(tam)) return null;
  if (ondalik.slice(3).replace(/0/g, "") !== "") return null;
  const mm = Number(tam) * 1000 + Number(ondalik.slice(0, 3).padEnd(3, "0"));
  if (isaret === "±" && mm !== 0) return null;
  return isaret === "-" || isaret === "−" || isaret === "–" ? -mm : mm;
}

/**  mm → kot yazısı ( sunucunun kot_metni'si ):  "±0,00", "+3,20", "-8,805".  */
export function kotYaz(mm: number): string {
  if (mm === 0) return "±0,00";
  const s = (mm / 1000).toFixed(mm % 10 !== 0 ? 3 : 2).replace(".", ",");
  return mm > 0 ? `+${s}` : s;
}

/**  Durak kotlarının metni → kotlar ( alttan üste;  okunamayan null )  */
export function kotlariOku(metin: string | undefined): (number | null)[] {
  return (metin ?? "")
    .split(/[;\n]/)
    .map((x) => x.trim())
    .filter((x) => x !== "")
    .map(kotOku);
}

export function kotlariYaz(kotlar: number[]): string {
  return kotlar.map(kotYaz).join("; ");
}

/**  Hepsi okundu mu ( hesaplamaya elverişli liste )  */
function tamKotlar(metin: string | undefined): number[] | null {
  const k = kotlariOku(metin);
  return k.length && k.every((x) => x !== null) ? (k as number[]) : null;
}

/**  Kotla giriş mi ( sunucu:  katlar.kot_kipi — yalnız boşluk değil )  */
export function kotlaMi(h: Ham | undefined): boolean {
  return (h?.[DURAK_KOTLARI] ?? "").trim() !== "";
}

/**  Yapıştırılan metin ( mimarın kesitinden, Excel'den ):  satır sonu, sekme ve noktalı
     virgül ayırır;  yukarıdan aşağı yazılmışsa ( kesin azalan ) alttan üste çevrilir.
     Okunamayan parça olduğu gibi kalır — sunucu söyler.  */
export function yapistir(metin: string): string {
  const parcalar = metin
    .split(/[;\n\t\r]/)
    .map((x) => x.trim())
    .filter((x) => x !== "");
  const k = parcalar.map(kotOku);
  const azalan = k.length > 1 && k.every((x, i) => x !== null && (i === 0 || x < (k[i - 1] as number)));
  return (azalan ? [...parcalar].reverse() : parcalar).join("; ");
}

/**  Hızlı doldur:  n durak, en alt durak alt ( mm ), aralar h ( mm ).  */
export function hizliDoldur(n: number, alt: number, h: number): string {
  return kotlariYaz(Array.from({ length: Math.max(n, 0) }, (_, i) => alt + i * h));
}

/**  Değişiklik:  { alan : yeni değer ( "" = sil ) } — formun yaz'ıyla sırayla yazılır.  */
export type Degisiklik = Record<string, string>;

/**  j. durağın altındaki aralık ( mm ):  o durak ve üstündekiler — kuyu tavanı ve
     makine dairesinin zemini dahil — birlikte kayar ( kat-kat arası ).  Kotlar
     okunamıyorsa null.  */
export function araligiYaz(h: Ham, j: number, aralik: number): Degisiklik | null {
  const k = tamKotlar(h[DURAK_KOTLARI]);
  if (!k || j < 1 || j >= k.length) return null;
  const kayma = k[j - 1] + aralik - k[j];
  const y: Degisiklik = { [DURAK_KOTLARI]: kotlariYaz(k.map((x, i) => (i >= j ? x + kayma : x))) };
  for (const a of [KUYU_TAVANI_KOTU, MD_ZEMINI_KOTU]) {
    const v = kotOku(h[a]);
    if (v !== null) y[a] = kotYaz(v + kayma);
  }
  return y;
}

/**  Bütün kotlar birlikte kayar ( mimarın ±0,00'ına geçmek:  en alt durak −7,00 ).  */
export function kaydir(h: Ham, kayma: number): Degisiklik | null {
  const k = tamKotlar(h[DURAK_KOTLARI]);
  if (!k) return null;
  const y: Degisiklik = { [DURAK_KOTLARI]: kotlariYaz(k.map((x) => x + kayma)) };
  for (const a of [KUYU_DIBI_KOTU, KUYU_TAVANI_KOTU, MD_ZEMINI_KOTU]) {
    const v = kotOku(h[a]);
    if (v !== null) y[a] = kotYaz(v + kayma);
  }
  return y;
}

/**  Ölçüyle → Kotla:  bugünkü ölçülerden kotlar, en alt durak ±0,00 ( mimarın ±0,00'ına
     "kaydır"la geçilir ).  d:  alanın etkin sayısı ( yazılmışsa o, yoksa sunucunun
     kullandığı, o da yoksa şemanın varsayılanı );  katlar:  kat yükseklikleri metni
     ( boşsa eşit ).  Eşit katlar mm'ye yuvarlanır, seyir aynı kalır.  Ölçü kutuları
     silinir ( kotla girişte okunmaz ).  */
export function kotlaGecis(
  d: (anahtar: string) => number | undefined,
  katlar: string | undefined,
  daireli: boolean,
): Degisiklik {
  const n = Math.round(d("durak_adedi") ?? 2);
  const H = Math.round((d("seyir_mesafesi") ?? 0) * 1000);
  const ara = (katlar ?? "")
    .split(";")
    .map((x) => Number(x.trim().replace(",", ".")))
    .filter((x) => Number.isFinite(x) && x > 0);
  const kotlar = [0];
  for (let i = 1; i < n; i++)
    kotlar.push(ara.length === n - 1 ? kotlar[i - 1] + Math.round(ara[i - 1]) : Math.round((i * H) / (n - 1)));
  const tavan = kotlar[kotlar.length - 1] + Math.round(d("son_kat_yuksekligi") ?? 0);
  const y: Degisiklik = {
    [DURAK_KOTLARI]: kotlariYaz(kotlar),
    [KUYU_DIBI_KOTU]: kotYaz(-Math.round(d("kuyu_dibi") ?? 0)),
    [KUYU_TAVANI_KOTU]: kotYaz(tavan),
  };
  if (daireli) {
    const doseme = d("tavan_dosemesi") ?? d("kuyu_duvar_kalinligi") ?? 0;
    y[MD_ZEMINI_KOTU] = kotYaz(tavan + Math.round(doseme) - Math.round(d("tabliye_yuksekligi") ?? 0));
  }
  for (const a of TURETILEN) y[a] = "";
  return y;
}

/*  KAT ADLARI VE GİRİŞ KATI ( sunucu:  katlar.durak_adlari — KAT_ADLARI_PLANI ):  adlar
    durak kotlarıyla aynı sırada ( alttan ), noktalı virgülle;  boş ad kuraldandır ( giriş
    katı 0, altı −1, üstü 1 … ).  Giriş katı kaçıncı durak ( 1'den );  boşsa kotu ±0,00'a
    en yakın durak.  Kuraldan adları ve giriş katını sunucu gönderir ( yanıtın girdisinin
    "_kot"u — katlar.ad_tablosu ):  ön yüz hesaplamaz.  */
export const DURAK_ADLARI = "durak_adlari";
export const GIRIS_DURAGI = "giris_duragi";

/**  Durak adlarının metni → adlar ( alttan, SIRASIYLA:  boş ad "" — kuraldan )  */
export function adlariOku(metin: string | undefined): string[] {
  const p = (metin ?? "").split(/[;\n]/).map((x) => x.trim());
  while (p.length && p[p.length - 1] === "") p.pop();
  return p;
}

/**  Adlar → metin:  sondaki boşlar atılır ( hepsi boşsa "" — alan silinir, adlar kuraldan )  */
export function adlariYaz(adlar: string[]): string {
  return adlariOku(adlar.map((x) => x.replace(/[;\n]/g, " ")).join(";")).join("; ");
}

/**  Girilmiş giriş katı ( 1'den );  girilmemişse ya da okunamıyorsa null  */
export function girisOku(v: string | undefined): number | null {
  const n = Number((v ?? "").trim());
  return (v ?? "").trim() !== "" && Number.isInteger(n) && n >= 1 ? n : null;
}

/**  j. durak silinir:  kotu, adı ( üstündekilerin adı bir aşağı kayar ) ve giriş katı
     ( o duraksa kurala döner, üstündeyse bir azalır ).  */
export function durakSil(h: Ham, j: number): Degisiklik {
  const kotlar = (h[DURAK_KOTLARI] ?? "")
    .split(/[;\n]/)
    .map((x) => x.trim())
    .filter((x) => x !== "");
  const y: Degisiklik = { [DURAK_KOTLARI]: kotlar.filter((_, i) => i !== j).join("; ") };
  const adlar = adlariOku(h[DURAK_ADLARI]);
  if (j < adlar.length) y[DURAK_ADLARI] = adlariYaz(adlar.filter((_, i) => i !== j));
  const g = girisOku(h[GIRIS_DURAGI]);
  if (g !== null && g >= j + 1) y[GIRIS_DURAGI] = g === j + 1 ? "" : String(g - 1);
  return y;
}

/**  Durak sayısı n olunca ( hızlı doldur, yapıştır ):  fazla adlar ve n'yi aşan giriş katı
     düşer, öbürleri yerinde kalır.  */
export function durakSayisi(h: Ham, n: number): Degisiklik {
  const y: Degisiklik = {};
  const adlar = adlariOku(h[DURAK_ADLARI]);
  if (adlar.length > n) y[DURAK_ADLARI] = adlariYaz(adlar.slice(0, n));
  const g = girisOku(h[GIRIS_DURAGI]);
  if (g !== null && g > n) y[GIRIS_DURAGI] = "";
  return y;
}

/**  Sunucunun kat adları ( yanıtın girdisinin "_kot"u ):  kuraldan adlar ( girilenler de
     içinde ), giriş katı ( 1'den ), adların hatası.  Yanıt yoksa boş.  */
export interface AdTablosu {
  adlar: string[];
  giris: number | null;
  hata: string[];
}

export function adTablosu(kullanilan: Record<string, unknown> | undefined): AdTablosu {
  const k = kullanilan?._kot;
  const t = k && typeof k === "object" ? (k as Record<string, unknown>) : {};
  return {
    adlar: Array.isArray(t.adlar) ? t.adlar.map(String) : [],
    giris: typeof t.giris === "number" ? t.giris : null,
    hata: Array.isArray(t.ad_hatasi) ? t.ad_hatasi.map(String) : [],
  };
}

/**  Sunucunun kullandığı değer sayı mı ( yanıtın girdisi — kotla girişte türetilen )  */
export function sayiDegeri(v: Deger | unknown): number | undefined {
  return typeof v === "number" && Number.isFinite(v) ? v : undefined;
}

/*  ÖN YÜZ DENETİMİ ( kurallar sunucudan ) — saf işlevler, bağımlılıksız.
    ÖN YÜZ SUNUCUDAN SIKI OLAMAZ:  yalnız tartışmasız okunan sayı denetlenir.
    "abc", "1 200", "1e3" ve belirsiz "1.200" sunucuya gider — kabul ya da
    reddi, sebebiyle birlikte, sunucunundur.  Eski dosyanın onay kutusu da
    sunucunun okuduğu gibi okunur ( evetMi · eskiOnayIsaretli ).
    Bu dosya YALNIZ tür içe aktarır:  testler/test_on_yuz_denetimi.py onu Node
    ile ( TypeScript doğrudan ) koşar;  değer içe aktarması koşuyu bozar.      */
import type { AlanSemasi } from "./api";

const BELIRSIZ = /^[+-]?[1-9]\d{0,2}[.,]\d{3}$/;
const ACIK_SAYI = /^[+-]?\d+([.,]\d+)?$/;

export function sayiOku(m: string): number | null {
  const t = m.trim();
  if (!ACIK_SAYI.test(t) || BELIRSIZ.test(t)) return null;
  return Number(t.replace(",", "."));
}

export function alanHatasi(sema: AlanSemasi, anahtar: string, ham: string | undefined): string | null {
  if (ham === undefined || ham.trim() === "") return null;
  const k = sema.kurallar[anahtar];
  if (!k) return null;
  const n = sayiOku(ham);
  if (n === null) return null;
  if (k.tam_sayi && !Number.isInteger(n)) return "Tam sayı olmalı";
  //  null = o yönde sınır yok ( "n < null" JavaScript'te n < 0 olurdu )
  if (k.en_az != null && (k.en_az_dahil ? n < k.en_az : n <= k.en_az))
    return k.en_az_dahil ? `En az ${k.en_az.toLocaleString("tr-TR")}` : `${k.en_az.toLocaleString("tr-TR")} üstünde olmalı`;
  if (k.en_cok != null && n > k.en_cok) return `En çok ${k.en_cok.toLocaleString("tr-TR")}`;
  return null;
}

/**  Sunucunun döndürdüğü sayıyı kutuya yazar.  Ondalık virgülle;  "123,456"
     gibi üç ondalıklı yazım sunucuda BELİRSİZ sayılır ( binlik mi ondalık mı ) —
     sona sıfır eklenir, değer aynı kalır.  */
export function kutuyaYaz(n: number): string {
  const m = String(n).replace(".", ",");
  return BELIRSIZ.test(m) ? m + "0" : m;
}

/*  ESKİ DOSYANIN ONAY KUTUSU:  mantıksal "true" / "false" yazımıyla gelir ( dosya
    okuyucusunun ice'si ).  Listeler sunucununkiyle birebir:  ayrılırlarsa aynı
    dosya ekranda ve hesapta başka okunur.                                    */
const EVET = ["evet", "e", "var", "true", "1", "yes"];

/**  Onay alanı işaretli mi — sunucunun evet_mi'si ( motor/ortak/adimlar.py ):
     eski dosyada "EVET" / "HAYIR" de durabilir  */
export function evetMi(m: string): boolean {
  return [...EVET, "on", "x", "✓"].includes(m.trim().toLowerCase());
}

/**  Eskiden onay kutusu olan seçim ( şemanın eski_onay'ı ) işaretli mi — sunucunun
     makine_raya_mi'si ( motor/uygulama/mukavemet_tablolari.py ):  evet yazımları
     ya da işaretli seçeneğin kendi adı  */
export function eskiOnayIsaretli(m: string, isaretli: string): boolean {
  return [...EVET, isaretli.toLowerCase()].includes(m.trim().toLowerCase());
}

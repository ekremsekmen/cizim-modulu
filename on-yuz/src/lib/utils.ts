import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...siniflar: ClassValue[]) {
  return twMerge(clsx(siniflar));
}

const _tr = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 4 });
const _tam = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 10 });

/**  Ekranda sayı:  Türkçe ondalık virgül, binlik nokta ( paftayla aynı ).
     tam:  tablolar gibi kaynağı olduğu gibi gösterilecek yerler — kırpılmaz.  */
export function sayiYaz(x: unknown, tam = false): string {
  if (x === null || x === undefined || x === "") return "";
  if (typeof x === "number") return (tam ? _tam : _tr).format(x);
  if (typeof x === "boolean") return x ? "evet" : "hayır";
  return String(x);
}

/**  Şemanın etiketindeki "( … )" açıklamasını ayırır:
     "Ön duvar kalınlığı  ( kapının duvarı — boşsa … )" → [ad, açıklama]  */
export function etiketBol(etiket: string): [string, string] {
  const i = etiket.indexOf("(");
  if (i <= 0) return [etiket.trim(), ""];
  const ad = etiket.slice(0, i).trim();
  const ack = etiket
    .slice(i)
    .replace(/^\(\s*/, "")
    .replace(/\s*\)\s*$/, "")
    .trim();
  return [ad, ack];
}

/**  Bölüm başlığından numara ve ad:  "4 - ASKI HALATLARININ …" → [4, "Askı halatlarının …"]  */
export function bolumAdi(baslik: string): [string, string] {
  const m = baslik.match(/^(\d+)\s*-\s*(.*)$/);
  const ad = (m ? m[2] : baslik).toLocaleLowerCase("tr-TR");
  return [m ? m[1] : "", ad.charAt(0).toLocaleUpperCase("tr-TR") + ad.slice(1)];
}

/**  Sunucunun BÜYÜK HARF başlığı → cümle düzeni ( "③a RAY VE KONSOL" → "③a Ray ve konsol" ).  */
export function cumleDuzeni(b: string): string {
  const m = b.match(/^([^A-Za-zÇĞİÖŞÜçğıöşü]*[a-z]?\s+)?(.*)$/);
  const on = m?.[1] ?? "";
  const govde = (m?.[2] ?? b).toLocaleLowerCase("tr-TR");
  return on + govde.charAt(0).toLocaleUpperCase("tr-TR") + govde.slice(1);
}

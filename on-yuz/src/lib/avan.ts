/*  AVAN PROJESİ — durum, ofis standardı ve proje dosyası ( .avan ).

    DOSYA ESKİ ARAYÜZÜN BİÇİMİNDEDİR ( 19 Eki kaldırıldı;  biçim değişmedi ):
    eskide kaydedilmiş bütün .avan dosyaları açılır.  Dosya eski formun kutu
    kimlikleriyle düz bir sözlüktür:

      { __mod:"avan", __surum:1, __program, __tarih,
        alanlar: { c_<bina>,  c_<kısa><i>     trafik ( i = 1…4 sütun ),
                   a_<alan><i>, a_aktif<i>    avan asansörleri,
                   a_temel_a … a_mk_yok       bina,
                   k_<kapak alanı>,
                   of_<k> / sb_<k>            ofis standardı,
                   __eknufus_c, __trafik_adet, __avan_ek, __avan_oto, __avan_trf } }

    İKİ FARK BİLEREK VAR:
    · Avanın kapasitesi ve hızı yenide TRAFİKTEN gelir ( eskide ayrı kutuydu ).
      Dosyadaki değer trafikten farklıysa açılışta söylenir.
    · Ofis standardı bütün avan projelerinde geçerlidir ( uygulamadaki gibi ):
      dosyadaki uygulanmaz, farklıysa söylenir.                              */
import { useCallback, useEffect, useState } from "react";
import type { AvanKoprusu, Deger, Secenekler } from "./api";
import { KAPAK_GRUPLARI } from "./kapak";
import { sayiOku, type Ham } from "./proje";
import { useSekmeEsitle } from "./sekme";

/**  Ek nüfus kalemi ( Tablo-1 ):  hızlı girişi olmayan bina tiplerinde nüfus buradan  */
export interface EkNufus {
  kalem: string;
  miktar: string;
  aciklama: string;
}

/**  Avan sunucuya en çok 4 asansör hesaplatır ( avan_hesabi )  */
export const AVAN_AZAMI = 4;
/**  Trafik en çok 4 asansör tipi alır ( eski formun 4 sütunu )  */
export const TRAFIK_AZAMI = 4;

export interface AvanProjesi {
  trafik: Ham;
  ekNufus: EkNufus[];
  trafikAsansorleri: Ham[];
  ortak: Ham;
  avanAsansorleri: Ham[];
  kapak: Ham;
}

export const BOS_AVAN: AvanProjesi = {
  trafik: {},
  ekNufus: [],
  trafikAsansorleri: [{}],
  ortak: {},
  avanAsansorleri: [{}, {}, {}, {}],
  kapak: {},
};

const PROJE = "asansor:avan";
const OFIS = "asansor:avan-ofis";
const ACILIS = "asansor:avan-acilis";

function oku<T extends object>(anahtar: string, yedek: T): T {
  try {
    return { ...yedek, ...JSON.parse(localStorage.getItem(anahtar) || "{}") };
  } catch {
    return yedek;
  }
}
function yaz(anahtar: string, deger: unknown) {
  try {
    localStorage.setItem(anahtar, JSON.stringify(deger));
  } catch {
    /*  özel pencere:  proje dosyası yine kaydedilir  */
  }
}

export function avanProjesiniOku(): AvanProjesi {
  return oku(PROJE, BOS_AVAN);
}
export function avanProjesiniYaz(p: AvanProjesi) {
  yaz(PROJE, p);
}

export function useAvanProjesi() {
  const [p, setP] = useState<AvanProjesi>(avanProjesiniOku);
  useEffect(() => yaz(PROJE, p), [p]);
  //  Başka sekmede değişti:  o hâl alınır ( silindiyse boş proje )
  useSekmeEsitle(PROJE, useCallback((d: Partial<AvanProjesi> | null) => setP({ ...BOS_AVAN, ...(d ?? {}) }), []));
  return [p, setP] as const;
}

/**  Avan ofis standardı — bütün avan projelerinde geçerli;  boş = varsayılan  */
export function avanOfisiniOku(): Ham {
  return oku<Ham>(OFIS, {});
}
export function useAvanOfisi() {
  const [ofis, setOfis] = useState<Ham>(avanOfisiniOku);
  useEffect(() => yaz(OFIS, ofis), [ofis]);
  useSekmeEsitle(OFIS, useCallback((d: Ham | null) => setOfis(d ?? {}), []));
  return [ofis, setOfis] as const;
}

/**  İsteğin "sabitler"i:  yalnız yazılan değerler ( boş = sunucunun varsayılanı )  */
export function avanSabitleri(ofis: Ham): Ham {
  return Object.fromEntries(Object.entries(ofis).filter(([, v]) => String(v).trim() !== ""));
}

/**  Bir sabitin etkin değeri ( yazılan, yoksa varsayılan ) — ekranda yazılan biçimiyle  */
export function sabitDegeri(sec: Secenekler, ofis: Ham, k: string): string {
  const v = (ofis[k] ?? "").trim();
  return v || virgullu(sec.sabit_sema.varsayilan[k]);
}

function virgullu(v: Deger): string {
  return v === null || v === undefined ? "" : String(v).replace(".", ",");
}

/* ───────────────────────────── dosyanın alanları */
/**  Trafik bina alanları ( eski kutu c_<anahtar> );  taahhütname c_taahhut  */
const TRAFIK_BINA = [
  "bina_tipi",
  "bina_yuksekligi",
  "yapi_yuksekligi",
  "N",
  "h",
  "bodrum",
  "hizli1",
  "hizli2",
  "manuel_k",
  "manuel_V",
] as const;

/**  Trafik sütunu:  istekteki ad → eski kutu c_<kısa><i>  */
const TRAFIK_SUTUNU: Record<string, string> = {
  P: "P",
  kapi_genisligi: "kg",
  kapi_tipi: "kt",
  V: "V",
  durak: "durak",
  h: "h",
  bodrum: "bodrum",
  manuel_ta: "mta",
  manuel_tk: "mtk",
  manuel_tg: "mtg",
  manuel_tp: "mtp",
};

/**  Avan asansörü ( eski kutu a_<anahtar><i> );  kapasite ve hız trafikten  */
const AVAN_ASANSORU = [
  "tanim",
  "makine_tipi",
  "eta",
  "i_palanga",
  "Hk",
  "kuyu_genisligi",
  "kabin_boyu",
  "kabin_genisligi",
  "Nsc",
  "denge_zinciri",
  "agirlik_guvenlik_tertibati",
  "Q_elle",
  "Gk_elle",
  "gr",
  "Fmk",
  "Fsh",
  "q_denge",
  "S1",
  "L1",
  "S2",
  "L2",
  "kablo_tipi",
  "zincir_birim_kutle",
] as const;

const AVAN_ORTAK = ["temel_a", "temel_b", "mk_uzunluk", "mk_genislik"] as const;

/**  Seçimlerin varsayılanı ( eski formun açılış değeri ):  boş istek de bunu demektir  */
export const AVAN_SECIM_VARSAYILANI: Record<string, string> = {
  makine_tipi: "Dişlisiz",
  i_palanga: "2",
  denge_zinciri: "Yok",
  agirlik_guvenlik_tertibati: "Yok",
};

const VAR_YOK = ["Yok", "Var"];

/**  Seçim alanlarının geçerli değerleri ( dosyadan gelen değer bunlardan biri olmalı )  */
function secimListeleri(sec: Secenekler): Record<string, (string | number)[]> {
  return {
    bina_tipi: sec.bina_tipleri,
    manuel_V: sec.hizlar,
    taahhutname: VAR_YOK,
    P: sec.kapasiteler,
    kapi_genisligi: sec.kapi_genislikleri,
    kapi_tipi: sec.kapi_tipleri,
    V: sec.hizlar,
    makine_tipi: Object.keys(sec.makine_tipleri),
    i_palanga: Object.values(sec.aski_oranlari),
    S1: sec.kesitler,
    S2: sec.kesitler,
    denge_zinciri: VAR_YOK,
    agirlik_guvenlik_tertibati: VAR_YOK,
  };
}

/**  Ekrandaki ad ( tanınmayan değer bildirimi için )  */
const AD: Record<string, string> = {
  bina_tipi: "Bina tipi",
  manuel_V: "Manuel ortak V",
  taahhutname: "Taahhütname",
  P: "Kapasite",
  kapi_genisligi: "Kapı genişliği",
  kapi_tipi: "Kapı tipi",
  V: "Hız",
  makine_tipi: "Makine tipi",
  i_palanga: "Askı oranı",
  S1: "S1",
  S2: "S2",
  denge_zinciri: "Denge zinciri",
  agirlik_guvenlik_tertibati: "Karşı ağırlıkta güvenlik tertibatı",
};

/* ───────────────────────────── yazma */
export function avanDosyaGovdesi(p: AvanProjesi, sec: Secenekler, ofis: Ham, kopru: AvanKoprusu | null) {
  const a: Record<string, unknown> = { __mod: "avan", __surum: 1 };
  for (const k of TRAFIK_BINA) a[`c_${k}`] = p.trafik[k] ?? "";
  a.c_taahhut = p.trafik.taahhutname || "Yok";
  //  Dört sütun da yazılır ( boşu boş ):  eski arayüz eksik kutuyu "dosyada yok" sayar
  for (let i = 0; i < TRAFIK_AZAMI; i++) {
    const h = p.trafikAsansorleri[i] ?? {};
    for (const [k, kisa] of Object.entries(TRAFIK_SUTUNU)) a[`c_${kisa}${i + 1}`] = h[k] ?? "";
  }
  a.__trafik_adet = Math.min(Math.max(1, p.trafikAsansorleri.length), TRAFIK_AZAMI);
  a.__eknufus_c = p.ekNufus.filter((x) => x.miktar.trim() !== "");

  //  Avan kartları trafikten:  eski arayüz açık kart sayısını a_aktif'ten,
  //  kapasite / hızın trafikten geldiğini __avan_trf'ten bilir ( avanDoldur )
  const ka = (kopru?.asansorler ?? []).slice(0, AVAN_AZAMI);
  const trf: Record<string, { P: number; V: number }> = {};
  for (let i = 0; i < AVAN_AZAMI; i++) {
    const h = p.avanAsansorleri[i] ?? {};
    const n = i + 1;
    a[`a_aktif${n}`] = !!ka[i];
    a[`a_kapasite${n}`] = ka[i] ? String(ka[i].P) : "";
    a[`a_V${n}`] = ka[i] ? String(ka[i].V) : "";
    for (const k of AVAN_ASANSORU) a[`a_${k}${n}`] = h[k] ?? "";
    //  Seçimler eski formda hep doludur:  etkin değer yazılır
    for (const [k, d] of Object.entries(AVAN_SECIM_VARSAYILANI)) a[`a_${k}${n}`] = h[k] || d;
    if (ka[i]) {
      a[`a_eta${n}`] = h.eta || virgullu(sec.makine_tipleri[(a[`a_makine_tipi${n}`] as string)] ?? "");
      trf[n] = { P: ka[i].P, V: ka[i].V };
    }
  }
  a.__avan_ek = 0;
  a.__avan_oto = {};
  a.__avan_trf = trf;
  for (const k of AVAN_ORTAK) a[`a_${k}`] = p.ortak[k] ?? "";
  a.a_mk_yok = (p.ortak.mk_yok ?? "true") === "true";

  for (const g of KAPAK_GRUPLARI) for (const [k] of g.alanlar) a[`k_${k}`] = p.kapak[k] ?? "";

  //  Ofis standardı eski formda hep doludur ( boş kutu yok )
  for (const k of Object.keys(sec.sabit_sema.varsayilan))
    a[`${k in sec.ofis_varsayilan ? "of" : "sb"}_${k}`] = sabitDegeri(sec, ofis, k);

  return {
    __mod: "avan",
    __surum: 1,
    __program: "Asansör Proje Programı",
    __tarih: new Date().toISOString().slice(0, 10),
    alanlar: a,
  };
}

export function avanDosyaAdi(p: AvanProjesi): string {
  const ad = (p.kapak.project_title || "Asansor").replace(/[^\p{L}\p{N} _-]/gu, "").trim().slice(0, 48);
  return `${ad || "Asansor"}.avan`;
}

export function avanDosyayaKaydet(p: AvanProjesi, sec: Secenekler, ofis: Ham, kopru: AvanKoprusu | null) {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(avanDosyaGovdesi(p, sec, ofis, kopru), null, 1)], { type: "application/json" }),
  );
  const a = Object.assign(document.createElement("a"), { href: url, download: avanDosyaAdi(p) });
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 3000);
}

/* ───────────────────────────── okuma */
export type AvanOkumasi =
  | {
      tamam: true;
      proje: AvanProjesi;
      /**  Dosyadaki avan kartlarının kapasite / hızı ( trafikle karşılaştırılır )  */
      dosyaAvani: { P: string; V: string }[];
      /**  Dosyadaki ofis standardının bu tarayıcınınkinden farklı değerleri ( etiketleriyle )  */
      ofisFarki: string[];
      taninmayan: string[];
    }
  | { tamam: false; hata: string };

function ice(v: unknown): string | null {
  if (typeof v === "boolean") return v ? "true" : "false";
  if (typeof v === "number") return Number.isFinite(v) ? String(v) : null;
  if (typeof v === "string") return v.trim() === "" ? null : v.trim();
  return null;
}

/**  "1,6" ile 1.6 aynı seçenektir ( eski secenekKarsiligi )  */
function secenekKarsiligi(v: string, liste: (string | number)[]): string | null {
  const s = liste.find((x) => String(x) === v);
  if (s !== undefined) return String(s);
  const n = Number(v.replace(",", "."));
  if (!Number.isFinite(n)) return null;
  const e = liste.find((x) => typeof x === "number" && Math.abs(x - n) < 1e-9);
  return e === undefined ? null : String(e);
}

/**  Dosya bir avan projesi mi?  ( başlıklı ya da eski düz biçim )  */
export function avanDosyasiMi(d: unknown): boolean {
  if (!d || typeof d !== "object") return false;
  const o = d as Record<string, unknown>;
  const govde = (o.alanlar && typeof o.alanlar === "object" ? o.alanlar : o) as Record<string, unknown>;
  const mod = o.__mod ?? govde.__mod;
  if (mod) return mod === "avan";
  return Object.keys(govde).some((k) => /^(c_|a_|k_|of_|sb_)/.test(k));
}

export function avanOku(metin: string, sec: Secenekler, ofis: Ham): AvanOkumasi {
  let d: unknown;
  try {
    d = JSON.parse(metin);
  } catch {
    return { tamam: false, hata: "Dosya okunamadı — geçerli bir proje dosyası değil." };
  }
  if (!d || typeof d !== "object") return { tamam: false, hata: "Dosya okunamadı — geçerli bir proje dosyası değil." };
  const o = d as Record<string, unknown>;
  const govde = (o.alanlar && typeof o.alanlar === "object" ? o.alanlar : o) as Record<string, unknown>;
  const mod = o.__mod ?? govde.__mod;
  if (mod === "uygulama")
    return { tamam: false, hata: "Bu bir uygulama projesi dosyası — açılış sayfasındaki “Dosya seç” ile açın." };
  if (!avanDosyasiMi(d)) return { tamam: false, hata: "Tanınmayan proje dosyası." };

  const listeler = secimListeleri(sec);
  const taninmayan: string[] = [];
  /**  Dosyadaki değer;  seçimse listedeki karşılığı ( yoksa bildirilir, alınmaz )  */
  const al = (kutu: string, k: string, ek = ""): string | null => {
    const v = ice(govde[kutu]);
    if (v === null) return null;
    const liste = listeler[k];
    if (!liste) return v;
    const s = secenekKarsiligi(v, liste);
    if (s === null) taninmayan.push(`${AD[k] ?? k}${ek} = ${v}`);
    return s;
  };
  const doldur = (hedef: Ham, k: string, v: string | null) => {
    if (v !== null) hedef[k] = v;
  };

  //  Trafik
  const trafik: Ham = {};
  for (const k of TRAFIK_BINA) doldur(trafik, k, al(`c_${k}`, k));
  const taahhut = al("c_taahhut", "taahhutname");
  if (taahhut === "Var") trafik.taahhutname = taahhut;

  //  Sütun adedi:  yazılıysa ondan, yoksa dolu kapasite sütunlarından ( eski dosyalar )
  let adet = parseInt(String(govde.__trafik_adet ?? ""), 10);
  if (!(adet >= 1 && adet <= TRAFIK_AZAMI)) {
    const dolu = [1, 2, 3, 4].filter((i) => ice(govde[`c_P${i}`]) !== null).length;
    adet = Math.max(1, dolu);
  }
  const trafikAsansorleri: Ham[] = [];
  for (let i = 1; i <= adet; i++) {
    const h: Ham = {};
    for (const [k, kisa] of Object.entries(TRAFIK_SUTUNU)) doldur(h, k, al(`c_${kisa}${i}`, k, adet > 1 ? ` ( ${i}. asansör )` : ""));
    trafikAsansorleri.push(h);
  }

  //  Ek nüfus:  eski dosyalarda tek gövdenin 't' listesinde olabilir
  const liste = (Array.isArray(govde.__eknufus_c) && govde.__eknufus_c.length ? govde.__eknufus_c : govde.__eknufus_t) as unknown;
  const ekNufus: EkNufus[] = [];
  for (const x of Array.isArray(liste) ? liste : []) {
    if (!x || typeof x !== "object") continue;
    const y = x as Record<string, unknown>;
    const miktar = ice(y.miktar);
    if (miktar === null) continue;
    const kalem = String(y.kalem ?? "");
    if (!sec.nufus_kalemleri.includes(kalem)) {
      taninmayan.push(`Nüfus kalemi = ${kalem || "( boş )"}`);
      continue;
    }
    ekNufus.push({ kalem, miktar, aciklama: typeof y.aciklama === "string" ? y.aciklama : "" });
  }

  //  Avan asansörleri ( yalnız açık kartlar anlamlıdır;  ötekiler de korunur )
  const avanAsansorleri: Ham[] = [];
  const dosyaAvani: { P: string; V: string }[] = [];
  for (let i = 1; i <= AVAN_AZAMI; i++) {
    const h: Ham = {};
    const ek = ` ( ${i}. avan asansörü )`;
    for (const k of AVAN_ASANSORU) doldur(h, k, al(`a_${k}${i}`, k, ek));
    //  Eski form seçimleri ve verimi hep dolu yazar:  varsayılanla aynıysa yazılmamış sayılır
    for (const [k, v] of Object.entries(AVAN_SECIM_VARSAYILANI)) if (h[k] === v) delete h[k];
    const verim = sec.makine_tipleri[h.makine_tipi || AVAN_SECIM_VARSAYILANI.makine_tipi];
    if (h.eta !== undefined && sayiOku(h.eta) === verim) delete h.eta;
    avanAsansorleri.push(h);
    if (govde[`a_aktif${i}`] === true) dosyaAvani.push({ P: ice(govde[`a_kapasite${i}`]) ?? "", V: ice(govde[`a_V${i}`]) ?? "" });
  }

  const ortak: Ham = {};
  for (const k of AVAN_ORTAK) doldur(ortak, k, al(`a_${k}`, k));
  if (typeof govde.a_mk_yok === "boolean") ortak.mk_yok = String(govde.a_mk_yok);

  const kapak: Ham = {};
  for (const g of KAPAK_GRUPLARI) for (const [k] of g.alanlar) doldur(kapak, k, al(`k_${k}`, k));

  //  Boş kutu = varsayılan;  karşılaştırma etkin değerle ( "380" ile boş aynıdır )
  const sema = sec.sabit_sema;
  const ofisFarki = Object.keys(sema.varsayilan)
    .filter((k) => {
      const dosyada = ice(govde[`of_${k}`]) ?? ice(govde[`sb_${k}`]);
      if (dosyada === null) return false;
      const b = sabitDegeri(sec, ofis, k);
      const na = sayiOku(dosyada);
      const nb = sayiOku(b);
      return na !== null && nb !== null ? na !== nb : dosyada !== b.trim();
    })
    .map((k) => sema.etiket[k]?.[0] ?? k);

  return {
    tamam: true,
    proje: { trafik, ekNufus, trafikAsansorleri, ortak, avanAsansorleri, kapak },
    dosyaAvani,
    ofisFarki,
    taninmayan,
  };
}

/**  Açılış bildirimi:  ne açıldı, ne uygulanmadı  */
export function acilisBildirimi(ad: string, o: Extract<AvanOkumasi, { tamam: true }>): string {
  const satirlar = [`"${ad}" açıldı.`];
  if (o.ofisFarki.length)
    satirlar.push(
      `Dosyadaki ofis standardı bu tarayıcınınkinden ${o.ofisFarki.length} değerde farklı — hesap bu tarayıcınınkiyle yapılıyor ( Ofis standardı → Avan ):  ${o.ofisFarki.join(" · ")}`,
    );
  if (o.taninmayan.length)
    satirlar.push(`Bu sürümde olmayan ${o.taninmayan.length} seçim alınmadı:  ${o.taninmayan.join(" · ")}`);
  return satirlar.join("\n");
}

/**  Açılan dosya:  bildirimi, trafikle karşılaştırılacak avanı, geri alınacak proje  */
export interface Acilis {
  proje: AvanProjesi;
  bildirim: string;
  dosyaAvani: { P: string; V: string }[];
  onceki?: AvanProjesi;
}

/**  Açılış bildirimi ve önceki proje ( "Geri al" ) — sayfa yenilenince de durur  */
export function acilisiOku(): Acilis | null {
  try {
    const d = JSON.parse(localStorage.getItem(ACILIS) || "null");
    return d && typeof d === "object" && typeof d.bildirim === "string" ? (d as Acilis) : null;
  } catch {
    return null;
  }
}
export function acilisiYaz(a: Acilis | null) {
  try {
    if (a) localStorage.setItem(ACILIS, JSON.stringify(a));
    else localStorage.removeItem(ACILIS);
  } catch {
    /*  özel pencere:  bildirim yalnız bu açılışta kalır  */
  }
}

/**  Dosyayı okur;  hata ya da açılış  */
export function avanDosyasiniAc(metin: string, ad: string, sec: Secenekler, ofis: Ham): Acilis | string {
  const o = avanOku(metin, sec, ofis);
  if (!o.tamam) return o.hata;
  return { proje: o.proje, bildirim: acilisBildirimi(ad, o), dosyaAvani: o.dosyaAvani };
}

/**  Dosyadaki avan kartlarının kapasite / hızı trafiğin verdiğinden farklı mı?
     Yenide avan trafikten hesaplanır;  fark sessiz geçmez.  */
export function trafikFarki(dosyaAvani: { P: string; V: string }[], kopru: AvanKoprusu | null): string | null {
  if (!kopru || !dosyaAvani.length) return null;
  const ka = kopru.asansorler.slice(0, AVAN_AZAMI);
  const ayni = (a: string, b: number) => a === "" || sayiOku(a) === b;
  const farkli = dosyaAvani.length !== ka.length || dosyaAvani.some((x, i) => !ka[i] || !ayni(x.P, ka[i].P) || !ayni(x.V, ka[i].V));
  if (!farkli) return null;
  const yaz = (l: { P: string | number; V: string | number }[]) =>
    l.map((x) => `${x.P} kişi · ${String(x.V).replace(".", ",")} m/s`).join(" + ");
  return `Dosyada avan ${yaz(dosyaAvani)} idi;  trafik hesabı ${yaz(ka)} veriyor — avan trafiğe göre hesaplanıyor.`;
}

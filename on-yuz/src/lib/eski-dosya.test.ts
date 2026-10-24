/*  ESKİ DOSYA ÜRETECİ ( 24 Eki ) — eski arayüzün .avan / .uygulama biçiminde
    tohumlu rastgele dosyalar:  arada boş sütun, yazılmamış ya da bozuk adet,
    eksik alan, sayı yerine metin, ondalık virgül, listede olmayan seçim,
    başlıksız eski biçim.  Kurallar:
      ·  okuma hiç fırlatmaz, okunan her değer metindir ( Ham )
      ·  DOLU HER DEĞER YA OKUNUR YA SÖYLENİR ( tanınmayan ) — varsayılana eşitse
         yazılmamış sayılır ( eski arayüz kutuyu varsayılanla doldurur );  eski
         arayüzün de göstermediği sütun / asansör ( adedin dışı ) okunmaz
      ·  okunan proje yeniden yazılıp okununca aynıdır
    Eski arayüzün yazdığı biçim:  lib/avan.ts ve lib/dosya.ts'in başı.          */
import { describe, expect, it } from "vitest";
import { avanDosyaGovdesi, avanOku, AVAN_SECIM_VARSAYILANI } from "./avan";
import { dosyaGovdesi, dosyaOku } from "./dosya";
import { eskiOnayIsaretli, evetMi } from "./denetim";
import { sayiOku } from "./proje";
import type { AvanKoprusu, Deger } from "./api";
import { rastgele, SECENEKLER as SEC, SEMA, TOHUM_SAYISI } from "./test-semasi";

type Uretici = ReturnType<typeof rastgele>;

/**  Dosyadaki ham değerin okunduğu biçim ( lib/avan ice ):  boş → null  */
function ice(v: unknown): string | null {
  if (typeof v === "boolean") return v ? "true" : "false";
  if (typeof v === "number") return Number.isFinite(v) ? String(v) : null;
  if (typeof v === "string") return v.trim() === "" ? null : v.trim();
  return null;
}

/**  Bütün tohumlar denenir;  bulunanlar TÜRÜNE göre ( değerler ve sıra numaraları
     atılmış ileti ) bir örnek, tohumu ve kaç dosyada çıktığıyla yazılır.
     Okumanın fırlatması da bir türdür.  */
function dene(ad: string, tek: (R: Uretici) => { dosya: unknown; kayip: string[] }) {
  const turler = new Map<string, { sayi: number; ornek: string; tohum: number }>();
  const ekle = (ileti: string, tohum: number) => {
    const tur = ileti.replace(/ = .*$| → .*$|: {2}.*$/s, "").replace(/\d+/g, "#");
    const t = turler.get(tur) ?? { sayi: 0, ornek: ileti, tohum };
    turler.set(tur, { ...t, sayi: t.sayi + 1 });
  };
  for (let tohum = 1; tohum <= TOHUM_SAYISI; tohum++) {
    try {
      const s = tek(rastgele(tohum));
      new Set(s.kayip).forEach((k) => ekle(k, tohum));
    } catch (e) {
      ekle(`okuma fırlattı:  ${(e as Error).message}`, tohum);
    }
  }
  const rapor = [...turler.values()].map((t) => `· ${t.sayi} dosyada ( ilk tohum ${t.tohum} ):  ${t.ornek.slice(0, 400)}`);
  expect(rapor, `${ad}:  okunmayan ve söylenmeyen dolu değerler\n${rapor.join("\n")}`).toEqual([]);
}

const metinMi = (o: Record<string, unknown>) => Object.values(o).every((v) => typeof v === "string");

/* ───────────────────────────── .avan */
const VAR_YOK = ["Yok", "Var"];
//  Trafik sütunu:  dosyadaki kısa ad → projedeki ad;  seçimse listesi
const SUTUN: [string, string, (string | number)[] | null][] = [
  ["P", "P", SEC.kapasiteler],
  ["kg", "kapi_genisligi", SEC.kapi_genislikleri],
  ["kt", "kapi_tipi", SEC.kapi_tipleri],
  ["V", "V", SEC.hizlar],
  ["durak", "durak", null],
  ["h", "h", null],
  ["bodrum", "bodrum", null],
  ["mta", "manuel_ta", null],
  ["mtk", "manuel_tk", null],
  ["mtg", "manuel_tg", null],
  ["mtp", "manuel_tp", null],
];
const BINA: [string, (string | number)[] | null][] = [
  ["bina_tipi", SEC.bina_tipleri],
  ["bina_yuksekligi", null],
  ["yapi_yuksekligi", null],
  ["N", null],
  ["h", null],
  ["bodrum", null],
  ["hizli1", null],
  ["hizli2", null],
  ["manuel_k", null],
  ["manuel_V", SEC.hizlar],
];
const KART: [string, (string | number)[] | null][] = [
  ["tanim", null],
  ["makine_tipi", Object.keys(SEC.makine_tipleri)],
  ["eta", null],
  ["i_palanga", Object.values(SEC.aski_oranlari)],
  ["Hk", null],
  ["kuyu_genisligi", null],
  ["kabin_boyu", null],
  ["Nsc", null],
  ["denge_zinciri", VAR_YOK],
  ["S1", SEC.kesitler],
  ["L1", null],
];
const ORTAK = ["temel_a", "temel_b", "mk_uzunluk", "mk_genislik"];
const KAPAK = ["project_title", "owner", "city", "capacity", "speed"];

/**  Seçimin listedeki yazımı ( "1,6" → "1.6" ) ya da null  */
function karsilik(v: string, liste: (string | number)[]): string | null {
  const s = liste.find((x) => String(x) === v);
  if (s !== undefined) return String(s);
  const n = Number(v.replace(",", "."));
  const e = Number.isFinite(n) ? liste.find((x) => typeof x === "number" && Math.abs(x - n) < 1e-9) : undefined;
  return e === undefined ? null : String(e);
}

const sayiYaDa = (R: Uretici, metinler: unknown[]) =>
  R.olasi(0.3) ? R.sec(metinler) : R.sec(["", "12", 12, "3,5", " 7 ", "abc", null, true]);

function avanUret(R: Uretici) {
  const a: Record<string, unknown> = {};
  for (const [k, liste] of BINA)
    if (R.olasi(0.7)) a[`c_${k}`] = liste ? R.sec([...liste, "1,6", "Eski tip", ""]) : sayiYaDa(R, ["39,98", 11]);
  a.c_taahhut = R.sec(["Yok", "Var", "", undefined]);
  //  Sütunlar:  kapasitesi rastgele boş ( aradaki boş sütun );  eski arayüz kapı
  //  genişliğini ve tipini hep dolu yazar
  for (let i = 1; i <= 4; i++)
    for (const [kisa, , liste] of SUTUN) {
      if (kisa === "P") a[`c_P${i}`] = R.olasi(0.55) ? R.sec([...SEC.kapasiteler, "13", "99"]) : R.sec(["", null]);
      else if (liste) a[`c_${kisa}${i}`] = R.sec([...liste, "1,6", "Eski", ""]);
      else if (R.olasi(0.3)) a[`c_${kisa}${i}`] = sayiYaDa(R, ["2,1", 12]);
    }
  const adet = R.sec(["yok", "yok", "gecerli", "bozuk"]);
  if (adet === "gecerli") a.__trafik_adet = 1 + R.tam(4);
  if (adet === "bozuk") a.__trafik_adet = R.sec([0, 5, "x", null, "2", -1, 2.5]);
  //  Avan kartları:  açık olanlar baştan ( eski arayüz adetten türetir )
  const acik = R.tam(5);
  for (let i = 1; i <= 4; i++) {
    a[`a_aktif${i}`] = i <= acik;
    a[`a_kapasite${i}`] = i <= acik ? R.sec(["8", "10", ""]) : "";
    for (const [k, liste] of KART) {
      if (k === "eta") a[`a_eta${i}`] = R.sec(["0,85", "0,5", "0,7", "", 0.85]);
      else if (liste) a[`a_${k}${i}`] = R.sec([...liste, ...(AVAN_SECIM_VARSAYILANI[k] ? [AVAN_SECIM_VARSAYILANI[k]] : []), "Eski", "7"]);
      else if (R.olasi(0.4)) a[`a_${k}${i}`] = sayiYaDa(R, ["İnsan", "1800"]);
    }
  }
  for (const k of ORTAK) if (R.olasi(0.5)) a[`a_${k}`] = sayiYaDa(R, ["26,55", 4000]);
  a.a_mk_yok = R.sec([true, false, undefined, "true", "false"]);
  for (const k of KAPAK) if (R.olasi(0.5)) a[`k_${k}`] = R.sec(["A Blok", "", 5, "Konya", " boşluklu "]);
  if (R.olasi(0.6))
    a[R.olasi(0.8) ? "__eknufus_c" : "__eknufus_t"] = Array.from({ length: R.tam(4) }, () =>
      R.olasi(0.1)
        ? R.sec([null, "bozuk", 3])
        : { kalem: R.sec([...SEC.nufus_kalemleri, "Eski kalem", ""]), miktar: R.sec(["", "3", 4, null]), aciklama: R.sec(["", "çatı", 5]) },
    );
  if (R.olasi(0.2)) a.of_U = R.sec(["380", "400", ""]);
  return R.olasi(0.75) ? { __mod: "avan", __surum: 1, alanlar: a } : a;
}

function avanDenetle(R: Uretici) {
  const dosya = avanUret(R);
  const g = ((dosya as { alanlar?: Record<string, unknown> }).alanlar ?? dosya) as Record<string, unknown>;
  const o = avanOku(JSON.stringify(dosya), SEC, {});
  if (!o.tamam) throw new Error(`açılmadı:  ${o.hata}`);
  const p = o.proje;
  const kayip: string[] = [];
  const soylendi = (v: string) => o.taninmayan.some((t) => t.endsWith(`= ${v}`));
  /**  dolu değer okunmuş ( seçimse listedeki yazımıyla ) ya da söylenmiş mi  */
  const bak = (yer: string, ham: unknown, okunan: string | undefined, liste: (string | number)[] | null, varsayilan?: (v: string) => boolean) => {
    const v = ice(ham);
    if (v === null) return;
    const beklenen = liste ? karsilik(v, liste) : v;
    if (okunan !== undefined && okunan === beklenen) return;
    if (okunan === undefined && beklenen === null && soylendi(v)) return;
    if (okunan === undefined && varsayilan?.(beklenen ?? v)) return;
    kayip.push(`${yer} = ${JSON.stringify(ham)} → ${okunan === undefined ? "okunmadı" : JSON.stringify(okunan)}`);
  };

  //  Okunan her değer metin
  const hamlar = [p.trafik, p.ortak, p.kapak, ...p.trafikAsansorleri, ...p.avanAsansorleri];
  if (!hamlar.every(metinMi) || !p.ekNufus.every((x) => metinMi(x as unknown as Record<string, unknown>)))
    kayip.push(`metin olmayan değer okundu:  ${JSON.stringify(p)}`);

  for (const [k, liste] of BINA) bak(`c_${k}`, g[`c_${k}`], p.trafik[k], liste);
  bak("c_taahhut", g.c_taahhut, p.trafik.taahhutname, VAR_YOK, (v) => v === "Yok");

  //  Sütun adedi:  geçerli yazılmışsa o ( eski arayüz fazlasını göstermez ), yoksa son dolu kapasiteye kadar
  const yazilan = parseInt(String(g.__trafik_adet ?? ""), 10);
  const sonDolu = Math.max(1, ...[1, 2, 3, 4].filter((i) => ice(g[`c_P${i}`]) !== null));
  const beklenenAdet = yazilan >= 1 && yazilan <= 4 ? yazilan : sonDolu;
  if (p.trafikAsansorleri.length !== beklenenAdet)
    kayip.push(`sütun adedi ${p.trafikAsansorleri.length}, beklenen ${beklenenAdet}`);
  for (let i = 1; i <= Math.min(beklenenAdet, p.trafikAsansorleri.length); i++)
    for (const [kisa, k, liste] of SUTUN) bak(`c_${kisa}${i}`, g[`c_${kisa}${i}`], p.trafikAsansorleri[i - 1][k], liste);

  for (let i = 1; i <= 4; i++) {
    const h = p.avanAsansorleri[i - 1] ?? {};
    const tip = h.makine_tipi || AVAN_SECIM_VARSAYILANI.makine_tipi;
    for (const [k, liste] of KART) {
      const varsayilan =
        k === "eta"
          ? (v: string) => sayiOku(v) === SEC.makine_tipleri[tip]
          : AVAN_SECIM_VARSAYILANI[k]
            ? (v: string) => v === AVAN_SECIM_VARSAYILANI[k]
            : undefined;
      bak(`a_${k}${i}`, g[`a_${k}${i}`], h[k], liste, varsayilan);
    }
  }
  for (const k of ORTAK) bak(`a_${k}`, g[`a_${k}`], p.ortak[k], null);
  bak("a_mk_yok", g.a_mk_yok, p.ortak.mk_yok, ["true", "false"]);
  for (const k of KAPAK) bak(`k_${k}`, g[`k_${k}`], p.kapak[k], null);

  //  Ek nüfus:  miktarı dolu kalem okunur ya da ( tanınmayan kalem ) söylenir
  const liste = Array.isArray(g.__eknufus_c) && g.__eknufus_c.length ? g.__eknufus_c : g.__eknufus_t;
  const okunan = [...p.ekNufus];
  for (const x of Array.isArray(liste) ? liste : []) {
    if (!x || typeof x !== "object") continue;
    const y = x as Record<string, unknown>;
    const miktar = ice(y.miktar);
    if (miktar === null) continue;
    const j = okunan.findIndex((e) => e.kalem === y.kalem && e.miktar === miktar);
    if (j >= 0) okunan.splice(j, 1);
    else if (!o.taninmayan.some((t) => t.startsWith("Nüfus kalemi")))
      kayip.push(`ek nüfus ${JSON.stringify(y)} okunmadı`);
  }

  //  Yeniden yaz → oku:  aynı proje ( köprü:  kapasiteli sütunlar )
  const kap = p.trafikAsansorleri.filter((a) => a.P);
  const kopru: AvanKoprusu | null = kap.length
    ? { tip: "Konut", N: 10, bodrum: 0, h: 3, adet: kap.length, asansorler: kap.map((a) => ({ P: Number(a.P), V: 1, toplam_seyahat: 30 })) }
    : null;
  const ikinci = avanOku(JSON.stringify(avanDosyaGovdesi(p, SEC, {}, kopru)), SEC, {});
  //  Makine dairesi yazılmamışsa dosyaya varsayılanı ( dairesiz ) yazılır:  aynı anlam
  const sade = (q: typeof p) => JSON.stringify({ ...q, ortak: { ...q.ortak, mk_yok: q.ortak.mk_yok ?? "true" } });
  if (!ikinci.tamam || sade(ikinci.proje) !== sade(p))
    kayip.push(`yeniden yazılınca değişti:  ${JSON.stringify(ikinci.tamam ? ikinci.proje : ikinci.hata)}`);
  return { dosya, kayip };
}

/* ───────────────────────────── .uygulama */
const ASANSOR_ALANLARI = SEMA.gruplar.flatMap((g) => g.alanlar).filter((a) => !SEMA.proje_geneli.includes(a.anahtar));
const GENEL_ALANLARI = SEMA.gruplar.flatMap((g) => g.alanlar).filter((a) => SEMA.proje_geneli.includes(a.anahtar));
const HAM: Record<string, unknown[]> = {
  asansor_adi: ["", "A", 3, " B "],
  beyan_yuku: [630, "630", "1.000", "1000", 900, "", "800", 800],
  mk_yok: [true, false, "EVET", "HAYIR", "true", "x"],
  aski_orani: [1, 2, "2", "2:1", "", "3"],
  makine_raya_biniyor: ["Bina yapısına", "Kılavuz raylara", true, false, "EVET", "HAYIR", "x"],
  kuyu_genisligi: [2400, "2400", "1800", "1,8", "", "abc", 1800],
  durak_adedi: [8, "8", "12", "", 12.5],
  kabin_agirligi: ["", "650", 650],
  mk_uzunluk: ["", "4000", 4000, "4,5"],
};

function uygulamaUret(R: Uretici) {
  const a: Record<string, unknown> = {
    mk_proje_adi: R.sec(["", "Proje", 5]),
    mk_isveren: R.sec(["", "İşveren"]),
    mk_pafta_no: R.sec(["", "12"]),
  };
  for (const al of GENEL_ALANLARI) if (R.olasi(0.7)) a[`m_${al.anahtar}`] = R.sec(HAM[al.anahtar]);
  const asansor = () => {
    const h: Record<string, unknown> = {};
    for (const al of ASANSOR_ALANLARI) if (R.olasi(0.7)) h[al.anahtar] = R.sec(HAM[al.anahtar]);
    return h;
  };
  const n = R.tam(6);
  if (R.olasi(0.8)) {
    const dizi = Array.from({ length: n }, () => (R.olasi(0.1) ? R.sec([null, "bozuk", 5]) : asansor()));
    a.__muk_asansorler = dizi;
    a.__muk_adet = R.sec([n, n, n, Math.max(1, n), undefined, 0, 9, "x", n + 1, n - 1]);
    a.m_adet = String(n);
  } else {
    //  Tek asansörlü çok eski dosya:  asansörün alanları da m_<anahtar>
    for (const al of ASANSOR_ALANLARI) if (R.olasi(0.7)) a[`m_${al.anahtar}`] = R.sec(HAM[al.anahtar]);
    if (R.olasi(0.3)) a.__muk_adet = R.sec([1, 2, "x"]);
  }
  if (R.olasi(0.3)) a.uof_sigma_em = R.sec(["130", "140", ""]);
  if (R.olasi(0.4)) a.__yeni_kapak = { "capacity.1": "1000 kg", "capacity.3": R.sec(["x", 5]), owner: R.sec(["İşveren", 7]), city: "Konya" };
  return R.olasi(0.8) ? { __mod: "uygulama", __surum: 1, alanlar: a } : a;
}

/**  Şemanın varsayılanına eşit mi ( lib/dosya ayniDeger:  yazılmamış sayılır ).  Eskiden
     onay kutusu olan seçimin true / false'u önce seçeneğine çevrilir ( eski_onay )  */
function varsayilanaEsit(v: string, d: Deger, tur: string, anahtar: string) {
  const eski = SEMA.eski_onay[anahtar];
  if (eski && !eski.includes(v)) v = eski[eskiOnayIsaretli(v, eski[1]) ? 1 : 0];
  if (tur === "onay") return String(evetMi(v)) === String(d);
  if (d === null || d === undefined) return false;
  const n = sayiOku(v);
  return typeof d === "number" && n !== null ? n === d : v === String(d);
}

function uygulamaDenetle(R: Uretici) {
  const dosya = uygulamaUret(R);
  const g = ((dosya as { alanlar?: Record<string, unknown> }).alanlar ?? dosya) as Record<string, unknown>;
  const o = dosyaOku(JSON.stringify(dosya), SEMA, {});
  if (!o.tamam) throw new Error(`açılmadı:  ${o.hata}`);
  const p = o.icerik;
  const kayip: string[] = [];
  if (![p.proje_geneli, ...p.asansorler, p.kapak ?? {}].every(metinMi)) kayip.push(`metin olmayan değer okundu:  ${JSON.stringify(p)}`);

  const bak = (yer: string, ham: unknown, okunan: string | undefined, al: (typeof ASANSOR_ALANLARI)[number]) => {
    if (SEMA.bos_tablodan.includes(al.anahtar) && ham === "") {
      if (okunan !== "") kayip.push(`${yer} = "" ( tablodan ) → ${JSON.stringify(okunan)}`);
      return;
    }
    const v = ice(ham);
    if (v === null || okunan !== undefined) return;
    if (varsayilanaEsit(v, al.varsayilan, al.tur, al.anahtar)) return;
    if (o.taninmayan.some((t) => t.endsWith(`= ${v}`) || t.endsWith(`= ${String(ham)}`))) return;
    kayip.push(`${yer} = ${JSON.stringify(ham)} okunmadı ve söylenmedi`);
  };

  for (const al of GENEL_ALANLARI) bak(`m_${al.anahtar}`, g[`m_${al.anahtar}`], p.proje_geneli[al.anahtar], al);
  //  Asansör adedi eski arayüzün kuralıyla:  dizideki kadar, en çok yazılan adet ( MUK_ADET )
  const dizi = Array.isArray(g.__muk_asansorler) ? g.__muk_asansorler : null;
  const yazilan = Number(g.__muk_adet);
  const beklenen = dizi?.length ? Math.min(Math.max(1, yazilan || dizi.length), dizi.length, SEMA.asansor_azami) : 1;
  if (p.asansorler.length !== beklenen)
    kayip.push(`asansör adedi ${p.asansorler.length}, eski arayüz ${beklenen} gösterirdi ( dizi ${dizi?.length ?? "yok"}, adet ${JSON.stringify(g.__muk_adet)} )`);
  for (let i = 0; i < Math.min(beklenen, p.asansorler.length); i++) {
    const kaynak = dizi ? dizi[i] : Object.fromEntries(ASANSOR_ALANLARI.map((al) => [al.anahtar, g[`m_${al.anahtar}`]]));
    if (!kaynak || typeof kaynak !== "object") continue;
    for (const al of ASANSOR_ALANLARI)
      bak(`${i + 1}. asansör ${al.anahtar}`, (kaynak as Record<string, unknown>)[al.anahtar], p.asansorler[i][al.anahtar], al);
  }
  const kapak = g.__yeni_kapak as Record<string, unknown> | undefined;
  for (const [k, v] of Object.entries(kapak ?? {}))
    if (ice(v) !== null && p.kapak?.[k] === undefined) kayip.push(`kapak ${k} = ${JSON.stringify(v)} okunmadı`);

  //  Yeniden yaz → oku:  aynı proje
  const proje = { id: "t", tur: "uygulama" as const, guncellendi: 0, ...p };
  const ikinci = dosyaOku(JSON.stringify(dosyaGovdesi(proje, SEMA, {})), SEMA, {});
  if (!ikinci.tamam || JSON.stringify(ikinci.icerik) !== JSON.stringify(p))
    kayip.push(`yeniden yazılınca değişti:  ${JSON.stringify(ikinci.tamam ? ikinci.icerik : ikinci.hata)}`);
  return { dosya, kayip };
}

describe("eski dosya üreteci:  dolu her değer ya okunur ya söylenir", () => {
  it(".avan ( arada boş sütun, bozuk adet, virgül, tanınmayan seçim, başlıksız biçim )", () => {
    dene(".avan", avanDenetle);
  });
  it(".uygulama ( asansör dizisi, adet, eski onay, tek asansörlü eski biçim, kapak )", () => {
    dene(".uygulama", uygulamaDenetle);
  });
});


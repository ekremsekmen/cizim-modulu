/*  SUNUCU SÖZLEŞMESİ
    Her ekran yalnız bu uçlardan beslenir;  arayüz kural / hesap üretmez.
      GET  /api/uygulama/alanlar      form şeması ( gruplar, kurallar, ofis standardı, tablolar )
      POST /api/uygulama/coklu        1 - 4 asansörün hesabı ( bölümler, hükümler )
      POST /api/uygulama/cizimler     seçili asansörün çizimleri ( sunucu SVG'si )
      POST /api/uygulama/olcu         tıklanan ölçünün kaynak girdileri
      POST /api/uygulama/olcu_degistir ölçüyü hedefe getiren girdi değişikliği
      POST /api/indir/uygulama-pdf | uygulama-dwg   teslim
      GET  /api/secenekler · POST /api/trafik · /api/avan · /api/indir/…   avan      */

export type AlanTuru = "sayi" | "secim" | "metin" | "onay";
export type AlanKaynagi = "GİRDİ" | "KURAL" | "KATALOG" | "ÇİZİM";
export type Deger = string | number | boolean | null;

export interface Alan {
  anahtar: string;
  etiket: string;
  birim: string;
  tur: AlanTuru;
  secenekler: (string | number)[] | null;
  varsayilan: Deger;
  gelismis: boolean;
  bilgi: string;
  secenek_metni: Record<string, string> | null;
  kaynak: AlanKaynagi;
  secenek_kosulu: Record<string, { yerlesim: string; sebep: string }> | null;
}

export interface Grup {
  ad: string;
  alanlar: Alan[];
}

/**  Sınırı olmayan yön null gelir ( kaçıklıklar eksi olabilir:  en_az null )  */
export interface Kural {
  en_az?: number | null;
  en_az_dahil?: boolean;
  en_cok?: number | null;
  tam_sayi?: boolean;
}

export interface Tablo {
  ad: string;
  kaynak: string;
  aciklama: string;
  basliklar: string[];
  satirlar: (string | number | null)[][];
}

export interface AlanSemasi {
  gruplar: Grup[];
  bolum_grubu: Record<string, string[]>;
  hesaplanan: string[];
  kurallar: Record<string, Kural>;
  /**  Boş metni "tablodan al" demek olan alanlar ( gönderilmeyen = varsayılan;  boş = tablo )  */
  bos_tablodan: string[];
  proje_geneli: string[];
  yerlesime_gore_gizli: { mrl: string[]; daireli: string[] };
  cizimden: string[];
  ortak_kopru: { mukavemet: string; anahtar: string; avan: string }[];
  sabitler: {
    varsayilan: Record<string, Deger>;
    metin: string[];
    gruplar: { baslik: string; aciklama: string; alanlar: string[] }[];
    etiket: Record<string, string[]>;
  };
  tablolar: Tablo[];
  asansor_azami: number;
}

export interface Adim {
  sembol: string;
  aciklama: string;
  deger: Deger;
  birim: string;
  kaynak: string;
  formul: string;
  islem: string;
  tip: string;
  metin: string;
  vurgu: boolean;
}

export interface Sonuc {
  baslik: string;
  metin: string;
  uygun: boolean | null;
  alt?: string[];
}

export interface Bolum {
  baslik: string;
  kaynak: string;
  adimlar: Adim[];
  sonuc: Sonuc;
  notlar: string[];
  aciklamalar: string[];
  kimlik: string;
  ad: string;
  sira: number;
}

/**  Bir asansörün sonucu.  Çok asansörlü projede biri reddedilirse yanıtın
     kendisi yine aktiftir;  reddedilenin yalnız aktif:false, no, tanim, girdi
     ve hata'sı gelir — bölüm, uyarı ve özeti YOKTUR ( 22 Eki:  ikinci asansöre
     dar kuyu girilince ön yüz olmayan listeyi okuyup çöküyordu ).  */
export interface AsansorSonucu {
  aktif: boolean;
  no: number;
  tanim: string;
  girdi?: Record<string, Deger>;
  hata?: string[];
  bolumler?: Bolum[];
  uyarilar?: string[];
  ozet?: Record<string, unknown>;
  /**  Elektrik projesinin değerleri ( avan_hesabi._elektrik_projesi );  elektrik
       hesabı yapılamadıysa yok — pakette o asansörün elektrik projesi olmaz  */
  elektrik?: Record<string, unknown> | null;
}

export interface CokluYanit {
  aktif: boolean;
  hata?: string[];
  asansorler?: AsansorSonucu[];
  proje_geneli?: Bolum[];
  ozet?: {
    adet: number;
    tumu_uygun: boolean;
    asansorler: { no: number; tanim: string; tumu_uygun: boolean; genel_sonuc: string }[];
  };
}

export interface Cizim {
  ad: string;
  baslik: string;
  olcek: number;
  olceksiz: boolean;
  svg: string;
}

/**  Çizimin bir sorunu ( sunucu:  cizim/sorun.py ) — parçalar çizimdeki adlarıyla
     ( SVG'nin data-ad'ı ), cizim:  sorunun en iyi görüldüğü çizim  */
export interface CizimSorunu {
  metin: string;
  parcalar: string[];
  cizim: string | null;
}

/**  Bir sorunun doğrulanmış çaresi ( sunucu:  uclar/care_uclari.py ) — uygulanıp
     hesap ve çizim yeniden kurularak sınanmıştır  */
export interface CareOnerisi {
  anahtar: string;
  etiket: string;
  /**  Bugünkü etkin değer ( boş kutuda kuralın / varsayılanın değeri;  seçimde metin )  */
  eski: number | string | null;
  girilmis: boolean;
  yeni: number | string;
  /**  Bu değişiklikle giden sorunlar ( metinleri )  */
  gider: string[];
  /**  Bu değişiklikten sonra görünür olacak sorunlar:  bugün de var ama denetim
       ilk hatada durduğu için gizli ( yeni sorun DEĞİL )  */
  ortaya_cikan: string[];
  bina: boolean;
  yontem: "türev" | "son değişiklik" | "seçim";
}

export interface CareYanit {
  aktif: boolean;
  careler?: { metin: string; oneriler: CareOnerisi[] }[];
  /**  Yapılan sınama ( hesap + çizim yeniden kurulumu ) — bütçe saat değil, sayıdır  */
  sinama?: number;
  /**  false:  arama bütçeye ( neden "sinama" ) ya da güvenlik süresine ( "sure" )
       takıldı — çareler eksik olabilir  */
  tamamlandi?: boolean;
  neden?: "sinama" | "sure" | null;
  sure?: number;
  hata?: string[];
}

/**  Son temiz girdi ( son değişikliğin sınırı için ):  asansörün girdisi ve proje geneli  */
export interface OncekiGirdi {
  asansor: Record<string, string>;
  proje_geneli: Record<string, string>;
}

/**  aktif:  çizim uygun.  Aktif değilse hata sebebidir;  çizimler de geldiyse
     çizim SORUNLU kuruldu ( ekranda gösterilir, paket inmez ), gelmediyse girdi
     çizime hiç çevrilemedi.  */
export interface CizimYanit {
  aktif: boolean;
  cizimler?: Cizim[];
  hata?: string[];
  /**  Sorunlu girdiyle kurulamayan çizimlerin başlıkları  */
  kurulamayan?: string[];
  /**  hata'nın yapılı hâli ( sorunlu çizimde )  */
  sorunlar?: CizimSorunu[];
}

export interface OlcuKaynagi {
  anahtar: string;
  tur: string;
  deger: number;
  egim: number;
  etiket: string;
  birim: string;
  yer: "asansor" | "proje" | "ofis" | string;
  degistirilir: boolean;
}

export interface OlcuYanit {
  aktif: boolean;
  metin?: string;
  deger?: number;
  kural?: string | null;
  kaynaklar?: OlcuKaynagi[];
  hata?: string[];
}

export interface OlcuDegisikligi {
  aktif: boolean;
  degisiklikler?: { anahtar: string; etiket: string; eski: number; deger: number }[];
  olcu?: number;
  dogrulandi?: boolean;
  uyarilar?: string[];
  hata?: string[];
}

/**  Uygulama isteği:  ham metinler ( sunucu okur, doğrular, reddeder ).
     kapak:  proje kimliği — çizimin antetinde ve indirilen dosyanın adında;
     hesaba girmez ( bu yüzden hesap isteğinde yok, değişince hesap tekrarlanmaz ).  */
export interface UygulamaIstegi {
  asansorler: Record<string, string>[];
  proje_geneli: Record<string, string>;
  sabitler: Record<string, string>;
  kapak?: { project_title: string; owner: string; sheet_no: string };
}

/* ───────────────────────────── avan */
export interface Secenekler {
  bina_tipleri: string[];
  hizli_etiketleri: Record<string, { hizli1: [string, string]; hizli2: [string, string] }>;
  kapasiteler: number[];
  hizlar: number[];
  kapi_genislikleri: number[];
  kapi_tipleri: string[];
  nufus_kalemleri: string[];
  tablo_1: Record<string, { birim: string; katsayi: number }>;
  makine_tipleri: Record<string, number>;
  aski_oranlari: Record<string, number>;
  kesitler: number[];
  tablo_7: Record<string, number>;
  /**  Tablo-10:  bina tipinin %k satırı ( k_tipi null:  Tablo-9'da yok, manuel k zorunlu )  */
  tablo_10?: Record<string, { k_tipi: string | null }>;
  kapak_turetilen: string[];
  ofis_varsayilan: Record<string, Deger>;
  sabit_b: Record<string, Deger>;
  /**  Avan ofis standardının formu ( gruplar · etiketler · varsayılanlar )  */
  sabit_sema: AvanSabitSemasi;
}

export interface AvanSabitSemasi {
  gruplar: { baslik: string; aciklama: string; alanlar: string[] }[];
  etiket: Record<string, [string, string]>;
  varsayilan: Record<string, Deger>;
  metin: string[];
}

export interface AvanKoprusu {
  tip: string;
  N: number;
  bodrum: number;
  h: number;
  adet: number;
  asansorler: { P: number; V: number; toplam_seyahat: number }[];
}

export interface TrafikYaniti {
  hata: string | null;
  uyarilar?: string[];
  bolumler?: Bolum[];
  ozet?: {
    bina_tipi: string;
    standart: string;
    B: number;
    TR: number;
    R: number;
    Ieer: number;
    Izul: number;
    adet: number;
    sonuc_cumlesi: string;
    karar_olcutleri?: { ad: string; metin: string; uygun: boolean }[];
  } | null;
  oneriler?: { secenek: string; adet: number; Ieer: number; erisilebilir: boolean }[];
  avan_koprusu?: AvanKoprusu | null;
  kapak_bilgileri?: Record<string, string>;
}

/**  Bina hesabı ( makine dairesi aydınlatması, topraklama ):  uygulanmıyorsa
     ya da girdi eksikse aktif:false ve sebebi uyari'da.  */
export interface AvanBinaHesabi {
  aktif: boolean;
  uyari?: string;
  bolumler?: Bolum[];
}

export interface AvanYaniti {
  hata?: string;
  asansorler?: { no: number; aktif: boolean; tanim?: string; uyari?: string; bolumler?: Bolum[] }[];
  makine_dairesi?: AvanBinaHesabi;
  topraklama?: AvanBinaHesabi;
  uyarilar?: string[];
  engelleyici?: string[];
  kapak_bilgileri?: Record<string, string>;
}

/* ───────────────────────────── istekler */
async function al<T>(yol: string): Promise<T> {
  const r = await fetch(yol);
  if (!r.ok) throw new Error(`Sunucu yanıt vermedi ( ${r.status} )`);
  return r.json();
}

/**  POST:  sunucu reddederken de çoğu zaman JSON döner ( 413 istek çok büyük:
     {"aktif":false,"hata":[…]} ) — o metin ekranda görünsün diye yanıt olarak
     verilir.  JSON olmayan hata ( vekil, çökme ) ve bağlantı kopması fırlatır:
     sorgu hata durumuna geçer, ekran "güncel değil" der.  */
async function gonder<T>(yol: string, govde: unknown, sinyal?: AbortSignal): Promise<T> {
  const r = await fetch(yol, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(govde),
    signal: sinyal,
  });
  if (r.ok || (r.headers.get("Content-Type") || "").includes("application/json")) return r.json();
  throw new Error(`Sunucu yanıt vermedi ( ${r.status} )`);
}

export const api = {
  alanlar: () => al<AlanSemasi>("/api/uygulama/alanlar"),
  hesap: (i: UygulamaIstegi, s?: AbortSignal) => gonder<CokluYanit>("/api/uygulama/coklu", i, s),
  cizimler: (i: UygulamaIstegi, asansor: number, s?: AbortSignal) =>
    gonder<CizimYanit>("/api/uygulama/cizimler", { ...i, asansor }, s),
  care: (i: UygulamaIstegi, asansor: number, onceki: OncekiGirdi | null) =>
    gonder<CareYanit>("/api/uygulama/care", { ...i, asansor, onceki }),
  olcu: (i: UygulamaIstegi, asansor: number, cizim: string, olcu: number, metin: string) =>
    gonder<OlcuYanit>("/api/uygulama/olcu", { ...i, asansor, cizim, olcu, metin }),
  olcuDegistir: (
    i: UygulamaIstegi,
    asansor: number,
    cizim: string,
    olcu: number,
    metin: string,
    anahtar: string,
    hedef: string,
  ) => gonder<OlcuDegisikligi>("/api/uygulama/olcu_degistir", { ...i, asansor, cizim, olcu, metin, anahtar, hedef }),
  secenekler: () => al<Secenekler>("/api/secenekler"),
  trafik: (girdiler: unknown, s?: AbortSignal) => gonder<TrafikYaniti>("/api/trafik", { girdiler }, s),
  avan: (girdiler: unknown, s?: AbortSignal) => gonder<AvanYaniti>("/api/avan", { girdiler }, s),
};

export interface IndirmeSonucu {
  hata?: string;
  /**  Paketin notları ( X-Avan-Not ):  DXF — DWG çevrilemedi, ZIP'te DXF var;
       TASMA — paftalar formatın çerçevesine sığmadı, baskıdan önce bakılmalı.  */
  notlar?: string[];
}

/**  İndirme uçları dosya döndürür;  sunucu reddederse JSON hata gelir.  */
export async function indir(uc: string, govde: unknown): Promise<IndirmeSonucu> {
  let r: Response;
  try {
    r = await fetch(`/api/indir/${uc}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(govde),
    });
  } catch {
    return { hata: "Sunucuya ulaşılamadı — bağlantıyı denetleyip yeniden deneyin." };
  }
  if ((r.headers.get("Content-Type") || "").includes("application/json")) {
    const j = await r.json();
    return { hata: Array.isArray(j.hata) ? j.hata.join("\n") : String(j.hata ?? "Üretilemedi") };
  }
  if (!r.ok) return { hata: `Sunucu yanıt vermedi ( ${r.status} )` };
  const ad = /filename\*?=(?:UTF-8'')?"?([^";]+)/i.exec(r.headers.get("Content-Disposition") || "")?.[1];
  const url = URL.createObjectURL(await r.blob());
  const a = Object.assign(document.createElement("a"), { href: url, download: decodeURIComponent(ad || uc) });
  document.body.appendChild(a);
  a.click();
  a.remove();
  //  Hemen geri alınırsa bazı tarayıcılar indirmeyi başlatmadan keser
  setTimeout(() => URL.revokeObjectURL(url), 3000);
  const notlar = (r.headers.get("X-Avan-Not") || "").split(",").filter(Boolean);
  return notlar.length ? { notlar } : {};
}

/**  Paket notlarının Türkçesi ( eski arayüzle aynı anlamlar ).  */
export function paketNotu(not: string): string {
  //  DXF bir eksiklik değildir:  çizim yalnız çizgi ve yazıdır, AutoCAD DXF'i birebir açar
  if (not === "DXF") return "ZIP'te çizim DXF olarak var;  AutoCAD birebir açar ( DWG isterseniz açıp Farklı Kaydet ).";
  if (not === "TASMA") return "Pafta sayısı proje formatının çerçevesine sığmadı, alta taşan sayfalar var — baskıdan önce bakın.";
  return not;
}

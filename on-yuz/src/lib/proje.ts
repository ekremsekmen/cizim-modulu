/*  PROJE DURUMU
    Sunucu proje saklamaz:  proje tarayıcıda ( localStorage ) ve .uygulama /
    .avan dosyasında yaşar.  Yalnız KULLANICININ YAZDIĞI değerler tutulur —
    boş alan isteğe girmez, sunucu kendi varsayılanını ya da kuralını uygular.
    Ekran o değeri soluk gösterir ( "siz girmediniz" ).                       */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { AlanSemasi, UygulamaIstegi } from "./api";

export type Ham = Record<string, string>;

export interface UygulamaProjesi {
  id: string;
  tur: "uygulama";
  ornek?: boolean;
  kimlik: { project_title: string; owner: string; sheet_no: string };
  asansorler: Ham[];
  proje_geneli: Ham;
  /**  Kapak sayfasının öbür alanları ( kimliktekiler hariç;  bkz. lib/kapak )  */
  kapak?: Ham;
  guncellendi: number;
  /**  Son hesabın özeti — açılış listesinde gösterilir.  */
  son?: { adet: number; uygunDegil: number; hata: boolean };
}

export interface ProjeOzeti {
  id: string;
  tur: "uygulama" | "avan";
  ad: string;
  ornek?: boolean;
  guncellendi: number;
  son?: UygulamaProjesi["son"];
}

const LISTE = "asansor:projeler";
const OFIS = "asansor:ofis";

function oku<T>(anahtar: string, yedek: T): T {
  try {
    const m = localStorage.getItem(anahtar);
    return m ? (JSON.parse(m) as T) : yedek;
  } catch {
    return yedek;
  }
}
function yaz(anahtar: string, deger: unknown) {
  try {
    localStorage.setItem(anahtar, JSON.stringify(deger));
  } catch {
    /*  özel pencere ya da dolu bellek:  proje dosyası yine kaydedilir  */
  }
}

export function projeListesi(): ProjeOzeti[] {
  return oku<ProjeOzeti[]>(LISTE, []).sort((a, b) => b.guncellendi - a.guncellendi);
}

function yeniKimlik() {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID().slice(0, 8)
    : Math.random().toString(36).slice(2, 10);
}

/**  Yeni proje ( boş ya da dosyadan okunan içerikle ) — tarayıcıya hemen yazılır.  */
export function yeniUygulama(
  ornek = false,
  icerik?: Pick<UygulamaProjesi, "kimlik" | "asansorler" | "proje_geneli" | "kapak">,
): UygulamaProjesi {
  const p: UygulamaProjesi = {
    id: yeniKimlik(),
    tur: "uygulama",
    ornek,
    kimlik: icerik?.kimlik ?? { project_title: ornek ? "Örnek proje" : "", owner: "", sheet_no: "" },
    asansorler: icerik?.asansorler.length ? icerik.asansorler : [{}],
    proje_geneli: icerik?.proje_geneli ?? {},
    kapak: icerik?.kapak ?? {},
    guncellendi: Date.now(),
  };
  kaydet(p);
  return p;
}

export function projeOku(id: string): UygulamaProjesi | null {
  const p = oku<UygulamaProjesi | null>(`asansor:proje:${id}`, null);
  return p && Array.isArray(p.asansorler) && p.asansorler.length ? p : null;
}

export function projeSil(id: string) {
  try {
    localStorage.removeItem(`asansor:proje:${id}`);
  } catch {
    /* özel pencere */
  }
  yaz(
    LISTE,
    oku<ProjeOzeti[]>(LISTE, []).filter((x) => x.id !== id),
  );
}

function kaydet(p: UygulamaProjesi) {
  yaz(`asansor:proje:${p.id}`, p);
  const liste = oku<ProjeOzeti[]>(LISTE, []).filter((x) => x.id !== p.id);
  liste.push({
    id: p.id,
    tur: p.tur,
    ad: p.kimlik.project_title || "Adsız uygulama projesi",
    ornek: p.ornek,
    guncellendi: p.guncellendi,
    son: p.son,
  });
  yaz(LISTE, liste);
}

/**  Proje ve değiştiricileri.  Her değişiklik tarayıcıya hemen yazılır.
     Proje var olmalı:  yoksa yönlendirici açılışa döndürür ( bkz. UygulamaRota ) —
     bilinmeyen adres sessizce yeni proje kurmaz.  */
export function useUygulamaProjesi(baslangic: UygulamaProjesi) {
  const [proje, setProje] = useState<UygulamaProjesi>(baslangic);
  const silindi = useRef(false);
  useEffect(() => {
    if (!silindi.current) kaydet(proje);
  }, [proje]);

  const guncelle = useCallback((f: (p: UygulamaProjesi) => UygulamaProjesi) => {
    setProje((p) => ({ ...f(p), guncellendi: Date.now() }));
  }, []);
  /**  Silinen proje sonradan yeniden yazılmasın  */
  const sil = useCallback(() => {
    silindi.current = true;
    projeSil(proje.id);
  }, [proje.id]);
  return [proje, guncelle, sil] as const;
}

/**  Alan değeri:  proje geneli alanlar binaya aittir ( bütün asansörlerde aynı ).
     Boş değer alanı siler:  isteğe girmez, sunucu varsayılanını uygular.
     bos_tablodan alanlarında boş, BOŞ olarak kalır ve gönderilir:  sunucu
     tablonun değerini kullanır ( boş kabin kütlesi;  gönderilmezse varsayılan 700 olurdu ).  */
export function alanYaz(p: UygulamaProjesi, sema: AlanSemasi, asansor: number, anahtar: string, deger: string) {
  const geneli = sema.proje_geneli.includes(anahtar);
  const temizle = (h: Ham) => {
    const y = { ...h };
    if (deger.trim() !== "") y[anahtar] = deger;
    else if (sema.bos_tablodan.includes(anahtar)) y[anahtar] = "";
    else delete y[anahtar];
    //  YÜK DEĞİŞİNCE KABİN AĞIRLIĞI TABLOYA DÖNER ( eski arayüzün kuralı:
    //  yeni yükün yanında eski yükün kabin kütlesi kalmasın;  boş = tablodan )
    if (anahtar === "beyan_yuku" && h.beyan_yuku !== y.beyan_yuku) y.kabin_agirligi = "";
    return y;
  };
  if (geneli) return { ...p, proje_geneli: temizle(p.proje_geneli) };
  return { ...p, asansorler: p.asansorler.map((h, i) => (i === asansor ? temizle(h) : h)) };
}

/**  Makine dairesiz mi ( yazılmadıysa şemanın varsayılanı ).  */
export function mrlMi(sema: AlanSemasi, p: UygulamaProjesi): boolean {
  const ham = p.proje_geneli.mk_yok;
  if (ham !== undefined) return ham !== "false";
  const v = sema.gruplar.flatMap((g) => g.alanlar).find((a) => a.anahtar === "mk_yok")?.varsayilan;
  return v !== false && v !== "false";
}

/**  Makine yerleşimine göre hesaba girmeyen alanlar:  ekranda gizli, sunucu
     okumaz, ön yüz de DENETLEMEZ — kullanıcının göremediği alan projeyi durdurmasın.  */
export function gizliAlanlar(sema: AlanSemasi, p: UygulamaProjesi): Set<string> {
  return new Set(mrlMi(sema, p) ? sema.yerlesime_gore_gizli.mrl : sema.yerlesime_gore_gizli.daireli);
}

/**  Kullanıcının yazdığı değer;  yazılmamışsa undefined.  Boş metin ( bos_tablodan:
     "tablodan" ) de yazılmamış sayılır — kutu sunucunun kullandığını soluk gösterir.  */
export function alanOku(p: UygulamaProjesi, sema: AlanSemasi, asansor: number, anahtar: string): string | undefined {
  const v = sema.proje_geneli.includes(anahtar) ? p.proje_geneli[anahtar] : p.asansorler[asansor]?.[anahtar];
  return v === "" ? undefined : v;
}

/* ───────────────────────────── Ofis standardı:  bütün projelerde geçerli */
export function useOfisStandardi() {
  const [ofis, setOfis] = useState<Ham>(() => oku<Ham>(OFIS, {}));
  useEffect(() => yaz(OFIS, ofis), [ofis]);
  return [ofis, setOfis] as const;
}

/**  Hesap isteği.  Ofis standardının boş kutuları gönderilmez ( eski arayüz gibi:
     boş = varsayılan ).  Proje kimliği hesaba girmez;  çizim isteği ekler.  */
export function istekKur(p: UygulamaProjesi, ofis: Ham): UygulamaIstegi {
  const sabitler = Object.fromEntries(Object.entries(ofis).filter(([, v]) => String(v).trim() !== ""));
  return { asansorler: p.asansorler, proje_geneli: p.proje_geneli, sabitler };
}

/* ───────────────────────────── Ön yüz denetimi ( kurallar sunucudan )
    ÖN YÜZ SUNUCUDAN SIKI OLAMAZ:  yalnız tartışmasız okunan sayı denetlenir.
    "abc", "1 200", "1e3" ve belirsiz "1.200" sunucuya gider — kabul ya da
    reddi, sebebiyle birlikte, sunucunundur.                                   */
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

export interface FormHatasi {
  anahtar: string;
  hata: string;
  /**  null:  binaya ait alan  */
  asansor: number | null;
}

/**  Projenin kural dışı girdileri — gizli alanlar hariç.  */
export function formHatalari(sema: AlanSemasi, p: UygulamaProjesi): FormHatasi[] {
  const gizli = gizliAlanlar(sema, p);
  const l: FormHatasi[] = [];
  p.asansorler.forEach((h, i) =>
    Object.entries(h).forEach(([k, v]) => {
      const e = !gizli.has(k) && alanHatasi(sema, k, v);
      if (e) l.push({ anahtar: k, hata: e, asansor: i });
    }),
  );
  Object.entries(p.proje_geneli).forEach(([k, v]) => {
    const e = !gizli.has(k) && alanHatasi(sema, k, v);
    if (e) l.push({ anahtar: k, hata: e, asansor: null });
  });
  return l;
}

/**  Sunucunun döndürdüğü sayıyı kutuya yazar.  Ondalık virgülle;  "123,456"
     gibi üç ondalıklı yazım sunucuda BELİRSİZ sayılır ( binlik mi ondalık mı ) —
     sona sıfır eklenir, değer aynı kalır.  */
export function kutuyaYaz(n: number): string {
  const m = String(n).replace(".", ",");
  return BELIRSIZ.test(m) ? m + "0" : m;
}

/**  Kısa gecikmeli değer — yazarken her tuşta istek gitmesin.
     null gelen değer beklenmez:  son geçerli değer kalır ( kural dışı girdi
     sunucuya gitmez, ekran son geçerli girdinin sonucunu gösterir ).  */
export function useGecikmeli<T>(deger: T, ms = 280): T {
  const [g, setG] = useState(deger);
  useEffect(() => {
    if (deger === null) return;
    const t = setTimeout(() => setG(deger), ms);
    return () => clearTimeout(t);
  }, [deger, ms]);
  return g;
}

export function useGoreceZaman(t: number) {
  //  "Şimdi" ekran açıldığında bir kez alınır ( render saf kalsın )
  const [simdi] = useState(() => Date.now());
  return useMemo(() => {
    const s = Math.round((simdi - t) / 1000);
    if (s < 60) return "az önce";
    if (s < 3600) return `${Math.round(s / 60)} dk önce`;
    if (s < 86400) return `${Math.round(s / 3600)} saat önce`;
    return new Date(t).toLocaleDateString("tr-TR", { day: "numeric", month: "long" });
  }, [t, simdi]);
}

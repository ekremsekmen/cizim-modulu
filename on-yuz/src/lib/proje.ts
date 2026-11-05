/*  PROJE DURUMU
    Sunucu proje saklamaz:  proje tarayıcıda ( localStorage — lib/depo;
    yazılamazsa bu sekmenin belleğinde ) ve .uygulama / .avan dosyasında yaşar.  Yalnız KULLANICININ YAZDIĞI değerler tutulur —
    boş alan isteğe girmez, sunucu kendi varsayılanını ya da kuralını uygular.
    Ekran o değeri soluk gösterir ( "siz girmediniz" ).                       */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Alan, AlanSemasi, Deger, UygulamaIstegi } from "./api";
import { alanHatasi, sayiOku } from "./denetim";
import { DURAK_KOTLARI, KUYU_DIBI_KOTU, KUYU_TAVANI_KOTU, TURETILEN, kotlaGecis, kotlaMi, kotlariOku, kotYaz } from "./kotlar";
import { depoOku, depoSil, depoYaz } from "./depo";
import { durumSil, girdininDurumu, izi, type ProjeDurumu } from "./durum";
import { kapakSirala } from "./kapak";
import { useSekmeEsitle } from "./sekme";
import { ORNEK_ASANSOR, ORNEK_SURUMU } from "./ornek";

export type Ham = Record<string, string>;

export interface UygulamaProjesi {
  id: string;
  tur: "uygulama";
  ornek?: boolean;
  /**  Örneğin değerlerinin sürümü ( lib/ornek ):  eskiyse örnek yenilenir  */
  ornekSurumu?: number;
  kimlik: { project_title: string; owner: string; sheet_no: string };
  asansorler: Ham[];
  proje_geneli: Ham;
  /**  Kapak sayfasının öbür alanları ( kimliktekiler hariç;  bkz. lib/kapak )  */
  kapak?: Ham;
  /**  Kullanıcının son değişikliği ( hesabın durumu değiştirmez — durum lib/durum'da ayrı )  */
  guncellendi: number;
}

/**  Açılış listesinin satırı ( durumu lib/durum'dan, girdisine aitse )  */
export interface ProjeOzeti {
  id: string;
  tur: "uygulama" | "avan";
  ad: string;
  ornek?: boolean;
  /**  0:  bilinmiyor ( 24 Eki'den önce kaydedilmiş avan )  */
  guncellendi: number;
  /**  Asansör sayısı ( uygulama;  avanınki trafikten — durumda )  */
  adet?: number;
}

const LISTE = "asansor:projeler";
const OFIS = "asansor:ofis";

function oku<T>(anahtar: string, yedek: T): T {
  try {
    const m = depoOku(anahtar);
    return m ? (JSON.parse(m) as T) : yedek;
  } catch {
    return yedek;
  }
}
function yaz(anahtar: string, deger: unknown) {
  depoYaz(anahtar, JSON.stringify(deger));
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
    ...(ornek && !icerik && { ornekSurumu: ORNEK_SURUMU }),
    kimlik: icerik?.kimlik ?? { project_title: ornek ? "Örnek proje" : "", owner: "", sheet_no: "" },
    asansorler: icerik?.asansorler.length ? icerik.asansorler : [ornek ? { ...ORNEK_ASANSOR } : {}],
    proje_geneli: icerik?.proje_geneli ?? {},
    kapak: icerik?.kapak ?? {},
    guncellendi: Date.now(),
  };
  kaydet(p);
  return p;
}

/**  Örnek proje TEKTİR:  varsa o açılır ( her açılışta yeni kopya listeyi dolduruyordu ),
     yoksa kurulur.  Değerlerini baştan almak için örnekSifirla.  Örneğin değerleri
     programla değiştiyse ( ORNEK_SURUMU ) tarayıcıdaki eski örnek yenilenir.  */
export function ornekProjesi(): UygulamaProjesi {
  for (const x of projeListesi()) {
    const p = x.ornek ? projeOku(x.id) : null;
    if (!p) continue;
    if (p.ornekSurumu === ORNEK_SURUMU) return p;
    const y = { ...ornekSifirla(p), guncellendi: Date.now() };
    kaydet(y);
    return y;
  }
  return yeniUygulama(true);
}

/**  Örneğin değerleri baştan ( kimliği aynı kalır )  */
export function ornekSifirla(p: UygulamaProjesi): UygulamaProjesi {
  return {
    ...p,
    ornekSurumu: ORNEK_SURUMU,
    kimlik: { project_title: "Örnek proje", owner: "", sheet_no: "" },
    asansorler: [{ ...ORNEK_ASANSOR }],
    proje_geneli: {},
    kapak: {},
  };
}

export function projeOku(id: string): UygulamaProjesi | null {
  const p = oku<UygulamaProjesi | null>(`asansor:proje:${id}`, null);
  if (!p || !Array.isArray(p.asansorler) || !p.asansorler.length) return null;
  //  Olmayan asansörün kapak değeri atılır ( 24 Eki'den önce kaldırılanınki kalıyordu:
  //  görünmeden "dolu alan" sayılıyor, yeni asansöre geçiyordu;  dosyadan da gelebilir )
  return p.kapak ? { ...p, kapak: kapakSirala(p.kapak, (n) => (n > p.asansorler.length ? null : n)) } : p;
}

export function projeSil(id: string) {
  depoSil(`asansor:proje:${id}`);
  durumSil(id);
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
    adet: p.asansorler.length,
  });
  yaz(LISTE, liste);
}

/**  Hesabın girdisinin izi ( lib/durum ):  asansörler, proje geneli ve ofis standardı —
     hesap isteğinin kendisi ( kimlik ve kapak hesaba girmez )  */
export function uygulamaIzi(p: UygulamaProjesi, ofis: Ham): string {
  return izi(istekKur(p, ofis));
}

/**  Açılış listesindeki durum:  kayıttaki girdinin ve bugünkü ofis standardının hesabıysa  */
export function uygulamaListeDurumu(id: string): ProjeDurumu | undefined {
  const p = projeOku(id);
  return p ? girdininDurumu(id, uygulamaIzi(p, oku<Ham>(OFIS, {}))) : undefined;
}

/**  Proje ve değiştiricileri.  Her değişiklik tarayıcıya hemen yazılır.
     Proje var olmalı:  yoksa yönlendirici açılışa döndürür ( bkz. UygulamaRota ) —
     bilinmeyen adres sessizce yeni proje kurmaz.  */
export function useUygulamaProjesi(baslangic: UygulamaProjesi) {
  const [proje, setProje] = useState<UygulamaProjesi>(baslangic);
  const silindi = useRef(false);
  //  Başka sekmede silindiyse bu sekme onu yeniden yazmaz ( ekran söyler )
  const [baskaSekmedeSilindi, setBaskaSekmedeSilindi] = useState(false);
  useEffect(() => {
    if (!silindi.current) kaydet(proje);
  }, [proje]);
  //  Aynı proje başka sekmede değişti:  o hâl alınır
  const disaridan = useCallback((d: UygulamaProjesi | null) => {
    if (d === null) {
      silindi.current = true;
      setBaskaSekmedeSilindi(true);
    } else if (Array.isArray(d.asansorler) && d.asansorler.length) setProje(d);
  }, []);
  useSekmeEsitle(`asansor:proje:${proje.id}`, disaridan);

  const guncelle = useCallback((f: (p: UygulamaProjesi) => UygulamaProjesi) => {
    setProje((p) => ({ ...f(p), guncellendi: Date.now() }));
  }, []);
  /**  Silinen proje sonradan yeniden yazılmasın  */
  const sil = useCallback(() => {
    silindi.current = true;
    projeSil(proje.id);
  }, [proje.id]);
  return [proje, guncelle, sil, baskaSekmedeSilindi] as const;
}

/**  Alan değeri:  proje geneli alanlar binaya aittir ( bütün asansörlerde aynı ).
     Boş değer alanı siler:  isteğe girmez, sunucu varsayılanını uygular.
     bos_tablodan alanlarında boş, BOŞ olarak kalır ve gönderilir:  sunucu
     tablonun değerini kullanır ( boş kabin kütlesi;  gönderilmezse varsayılan 700 olurdu ).  */
export function alanYaz(p: UygulamaProjesi, sema: AlanSemasi, asansor: number, anahtar: string, deger: string) {
  const q = alanYaz1(p, sema, asansor, anahtar, deger);
  //  TEK KUYUYA GEÇİNCE kuyunun ortak girdileri 1. asansörünkidir:  öbürüne yazılır
  //  ( sunucu da 1. asansörünkini okur;  ekran öbüründe eski değeri göstermesin )
  if (anahtar === sema.kuyu_duzeni.alan && tekKuyuMu(sema, q) && !tekKuyuMu(sema, p)) {
    const ilk = q.asansorler[0];
    return {
      ...q,
      asansorler: q.asansorler.map((h, i) => {
        if (i === 0) return h;
        const y = { ...h };
        for (const k of sema.kuyu_duzeni.ortak) {
          if (k in ilk) y[k] = ilk[k];
          else delete y[k];
        }
        return y;
      }),
    };
  }
  return q;
}

function alanYaz1(p: UygulamaProjesi, sema: AlanSemasi, asansor: number, anahtar: string, deger: string) {
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
  //  Tek kuyuda kuyunun ortak girdisi iki asansöre birden yazılır
  const ortak = kuyununOrtaklari(sema, p).has(anahtar);
  return { ...p, asansorler: p.asansorler.map((h, i) => (i === asansor || ortak ? temizle(h) : h)) };
}

/**  İki asansör tek kuyuda mı ( sunucu:  tasarim/gorunum.tek_kuyu_mu — yalnız iki
     asansörlü projede ).  */
export function tekKuyuMu(sema: AlanSemasi, p: UygulamaProjesi): boolean {
  return p.asansorler.length === 2 && p.proje_geneli[sema.kuyu_duzeni.alan] === sema.kuyu_duzeni.tek;
}

/**  Tek kuyuda iki asansörde aynı olan alanlar ( "kuyu" rozeti );  değilse boş.  */
export function kuyununOrtaklari(sema: AlanSemasi, p: UygulamaProjesi): Set<string> {
  return new Set(tekKuyuMu(sema, p) ? sema.kuyu_duzeni.ortak : []);
}

/* ───────────────────────────── asansör ekleme / kaldırma
    Kapağın asansöre özgü değerleri ( "capacity.2" ) asansörün sırasıyla gider
    ( lib/kapak kapakSirala ):  sıra kayınca onlar da kayar.                 */
/**  Yeni asansör 1 nolunun kopyasıdır ( aynı kuyu düzeni sık );  adı kopyalanmaz —
     iki sekme aynı adla görünmesin.  Kapağın asansöre özgü değeri kopyalanmaz,
     kaldırılmış bir asansörden kalmışsa da alınmaz.  */
export function asansorEkle(p: UygulamaProjesi, azami: number): UygulamaProjesi {
  if (p.asansorler.length >= azami) return p;
  const { asansor_adi: _ad, ...kopya } = p.asansorler[0] ?? {};
  const no = p.asansorler.length + 1;
  return {
    ...p,
    asansorler: [...p.asansorler, kopya],
    kapak: p.kapak && kapakSirala(p.kapak, (n) => (n >= no ? null : n)),
  };
}

/**  i. asansörü kaldırır;  son asansör kaldırılmaz ( proje en az bir asansördür ).  */
export function asansorKaldir(p: UygulamaProjesi, i: number): UygulamaProjesi {
  if (p.asansorler.length <= 1 || i < 0 || i >= p.asansorler.length) return p;
  const no = i + 1;
  return {
    ...p,
    asansorler: p.asansorler.filter((_, j) => j !== i),
    kapak: p.kapak && kapakSirala(p.kapak, (n) => (n === no ? null : n > no ? n - 1 : n)),
  };
}

/**  SIRAYLA TUTULAN ASANSÖR VERİSİ ASANSÖRÜYLE GİDER ( 24 Eki ):  asansör listesi
     değişince eski sıradaki veri asansörün yeni sırasına taşınır.  Asansör
     nesnesinden tanınır:  kaldırma, ekleme ve geri alma kalan nesnelere dokunmaz;
     girdisi yazılan asansör yeni nesnedir ama liste boyu aynı kalır ( yerinde ).
     Boyu değişmiş listede tanınmayan ( geri alınan, başka sekmeden gelen ) unutulur.  */
export function siraKaydir<T>(veri: Record<number, T>, eski: Ham[], yeni: Ham[]): Record<number, T> {
  const y: Record<number, T> = {};
  yeni.forEach((h, i) => {
    const k = eski.indexOf(h);
    const j = k >= 0 ? k : eski.length === yeni.length ? i : -1;
    if (j >= 0 && veri[j] !== undefined) y[i] = veri[j];
  });
  return y;
}

/**  Adet:  artınca 1 nolunun kopyaları eklenir, azalınca sondakiler kaldırılır.  */
export function asansorAdedi(p: UygulamaProjesi, n: number, azami: number): UygulamaProjesi {
  let q = p;
  while (q.asansorler.length < Math.min(n, azami)) q = asansorEkle(q, azami);
  if (!(n >= 1 && q.asansorler.length > n)) return q;
  return {
    ...q,
    asansorler: q.asansorler.slice(0, n),
    kapak: q.kapak && kapakSirala(q.kapak, (k) => (k > n ? null : k)),
  };
}

/**  Makine dairesiz mi ( yazılmadıysa şemanın varsayılanı ).  */
export function mrlMi(sema: AlanSemasi, p: UygulamaProjesi): boolean {
  const ham = p.proje_geneli.mk_yok;
  if (ham !== undefined) return ham !== "false";
  const v = sema.gruplar.flatMap((g) => g.alanlar).find((a) => a.anahtar === "mk_yok")?.varsayilan;
  return v !== false && v !== "false";
}

/**  YERLEŞİME BAĞLI SEÇENEK ( şemanın secenek_kosulu'su:  seçenek YALNIZ o
     yerleşimde seçilir — 1:1 askı yalnız makine dairelide ):  öbür yerleşimde
     seçenek kapalıdır, dönen sebep altına yazılır.  21 Eki:  koşul ters
     okunuyordu — makine daireli projede 1:1 kapalı, dairesizde açıktı.  */
export function secenekKapali(a: Alan, s: Deger, mrl: boolean): string | undefined {
  const k = a.secenek_kosulu?.[String(s)];
  return k && k.yerlesim !== (mrl ? "mrl" : "daireli") ? k.sebep : undefined;
}

/**  Makine yerleşimine göre hesaba girmeyen alanlar:  ekranda gizli, sunucu
     okumaz, ön yüz de DENETLEMEZ — kullanıcının göremediği alan projeyi durdurmasın.  */
export function gizliAlanlar(sema: AlanSemasi, p: UygulamaProjesi): Set<string> {
  const g = new Set(mrlMi(sema, p) ? sema.yerlesime_gore_gizli.mrl : sema.yerlesime_gore_gizli.daireli);
  //  Kuyu düzeni yalnız iki asansörlü projede seçilir;  tek kuyunun alanları tek kuyuda
  //  ( sunucu:  gorunum.tek_kuyu_disi )
  if (!tekKuyuMu(sema, p)) sema.kuyu_duzeni.gizli.forEach((k) => g.add(k));
  if (p.asansorler.length !== 2) g.add(sema.kuyu_duzeni.alan);
  return g;
}

/**  KAT GİRİŞİNİN KİPİ ( asansör başına — sunucu:  cizim/katlar.kot_kipi ):  durak
     kotları doluysa kotla.  Öbür kipin alanları ekranda gizli, sunucu okumaz, ön yüz de
     denetlemez ( kotla girişte ölçüden türeyenler, ölçüyle girişte kotlar ).  */
export function kipGizlileri(sema: AlanSemasi, h: Ham | undefined): Set<string> {
  const kotla = (h?.[sema.kot_kipi.alan] ?? "").trim() !== "";
  return new Set(kotla ? sema.kot_kipi.gizli.kotla : sema.kot_kipi.gizli.olcuyle);
}

/**  YALNIZ YANDAKİ AĞIRLIKTA OKUNAN ALANLAR ( sunucu:  şemanın agirlik_yeri — tasarim/alanlar
     agirlik="yan" ):  karşı ağırlık yanda değilse gizli.  Ağırlığın yeri yazılmış, yoksa
     sunucunun kullandığı, yoksa şemanın varsayılanı.  Sunucu o alanı zaten okumaz;  gizlemek
     yalnız "değiştirince bir şey olur" sanılmasın diye ( 5 Kas yok sayılan girdi taraması ).  */
export function agirligaGoreGizli(sema: AlanSemasi, h: Ham | undefined, kullanilan?: Record<string, Deger>): string[] {
  const ay = sema.agirlik_yeri;
  if (!ay) return [];
  const varsayilan = sema.gruplar.flatMap((g) => g.alanlar).find((a) => a.anahtar === ay.alan)?.varsayilan;
  const yer = String(h?.[ay.alan] ?? kullanilan?.[ay.alan] ?? varsayilan ?? "");
  return yer && !ay.yan.includes(yer) ? ay.yalniz_yan : [];
}

/**  YALNIZ KOTLA GİRİŞ ( kullanıcı kararı 2 Kas:  "ölçüyle kısmı karışıklık yaratıyor,
     gereksiz" ):  katlar her asansörde kot tablosuyla girilir — durak adedi, seyir,
     kat yükseklikleri, kuyu dibi, son kat ve tabliye kotlardan türer ( sunucuda,
     katlar.kot_tablosu ).  Kotla girilmemiş asansör ( yeni proje, eski dosya ) açılırken
     kotlara çevrilir:  yazılı ölçüleri, yazılmamışsa şemanın varsayılanı;  en alt durak
     ±0,00 ( kotlar.kotlaGecis — sunucu aynı sayıları türetir ).  Sunucu ölçüyle girişi
     okumaya devam eder ( eski istekler ).  Kotla girilmiş proje aynen döner.  */
export function kotlayaCevir(sema: AlanSemasi, p: UygulamaProjesi): UygulamaProjesi {
  if (p.asansorler.every((h) => kotlaMi(h))) return p;
  const daireli = !mrlMi(sema, p);
  return { ...p, asansorler: p.asansorler.map((h) => (kotlaMi(h) ? h : kotlarla(sema, h, daireli))) };
}

function kotlarla(sema: AlanSemasi, h: Ham, daireli: boolean): Ham {
  const varsayilan = (a: string) => {
    const v = sema.gruplar.flatMap((g) => g.alanlar).find((x) => x.anahtar === a)?.varsayilan;
    return typeof v === "number" ? v : undefined;
  };
  const y: Ham = { ...h, ...kotlaGecis((a) => sayiOku(h[a] ?? "") ?? varsayilan(a), h.kat_yukseklikleri, daireli) };
  for (const a of TURETILEN) delete y[a];
  return y;
}

/**  Asansörün kotları programın varsayılan tablosu mu ( yeni projenin;  kullanıcı hiç
     değiştirmedi ):  Teslim onu "girmediğiniz değer" sayar, girilen sayısına katılmaz.  */
export function varsayilanKotlarMi(sema: AlanSemasi, p: UygulamaProjesi, asansor: number): boolean {
  const h = p.asansorler[asansor];
  if (!h || !kotlaMi(h)) return false;
  const v = kotlarla(sema, {}, !mrlMi(sema, p));
  return [DURAK_KOTLARI, KUYU_DIBI_KOTU, KUYU_TAVANI_KOTU].every((a) => h[a] === v[a]);
}

/**  Kot tablosunun kısa özeti:  "8 durak · ±0,00 … +21,00"  */
export function kotOzeti(h: Ham | undefined): string {
  const k = kotlariOku(h?.[DURAK_KOTLARI]).filter((x): x is number => x !== null);
  return k.length ? `${k.length} durak · ${kotYaz(k[0])} … ${kotYaz(k[k.length - 1])}` : "";
}

/**  Asansörün görünür ( gelişmiş olmayan ) alanlarından kullanıcının YAZMADIKLARI —
     hesap şemanın varsayılanıyla yapıldı, Teslim onaylatır.  Gizliler sayılmaz:
     makine yerleşimine göre hesaba girmeyenler ve KAT GİRİŞİNİN öbür kipi.  Kotla
     girişte durak adedi, seyir, kat yükseklikleri, kuyu dibi, son kat ve tabliye
     kotlardan türer;  2 Kas'a kadar "girmediğiniz değer" sayılıp onaylatılıyordu
     ( formun kendisi ve formHatalari kipe bakıyordu, Teslim bakmıyordu ).  */
export function girilmeyenler(sema: AlanSemasi, p: UygulamaProjesi, asansor: number): { grup: string; alan: Alan }[] {
  const gizli = new Set([...gizliAlanlar(sema, p), ...kipGizlileri(sema, p.asansorler[asansor])]);
  const varsayilanKot = varsayilanKotlarMi(sema, p, asansor);
  return sema.gruplar.flatMap((g) =>
    g.alanlar
      .filter(
        (a) =>
          (varsayilanKot && a.anahtar === DURAK_KOTLARI) ||
          (!a.gelismis &&
            !gizli.has(a.anahtar) &&
            a.tur !== "metin" &&
            alanOku(p, sema, asansor, a.anahtar) === undefined &&
            (a.varsayilan !== null || a.kaynak === "KATALOG")),
      )
      .map((alan) => ({ grup: g.ad, alan })),
  );
}

/**  Kullanıcının yazdığı değer;  yazılmamışsa undefined.  Boş metin ( bos_tablodan:
     "tablodan" ) de yazılmamış sayılır — kutu sunucunun kullandığını soluk gösterir.  */
export function alanOku(p: UygulamaProjesi, sema: AlanSemasi, asansor: number, anahtar: string): string | undefined {
  //  Tek kuyuda ortak alan 1. asansörünkidir ( sunucu onu okur )
  const no = kuyununOrtaklari(sema, p).has(anahtar) ? 0 : asansor;
  const v = sema.proje_geneli.includes(anahtar) ? p.proje_geneli[anahtar] : p.asansorler[no]?.[anahtar];
  return v === "" ? undefined : v;
}

/* ───────────────────────────── Ofis standardı:  bütün projelerde geçerli */
export function useOfisStandardi() {
  const [ofis, setOfis] = useState<Ham>(() => oku<Ham>(OFIS, {}));
  useEffect(() => yaz(OFIS, ofis), [ofis]);
  //  Başka sekmede değişti ( silindiyse boş = varsayılanlar )
  useSekmeEsitle(OFIS, useCallback((d: Ham | null) => setOfis(d ?? {}), []));
  return [ofis, setOfis] as const;
}

/**  Hesap isteği.  Ofis standardının boş kutuları gönderilmez ( eski arayüz gibi:
     boş = varsayılan ).  Proje kimliği hesaba girmez;  çizim isteği ekler.  */
export function istekKur(p: UygulamaProjesi, ofis: Ham): UygulamaIstegi {
  const sabitler = Object.fromEntries(Object.entries(ofis).filter(([, v]) => String(v).trim() !== ""));
  return { asansorler: p.asansorler, proje_geneli: p.proje_geneli, sabitler };
}

/**  İki istek aynı girdiyi mi taşıyor ( kapak / antet hesabı, ölçüyü ve düzeltmeyi değiştirmez )  */
export function ayniGirdi(a: UygulamaIstegi | null, b: UygulamaIstegi | null) {
  if (!a || !b) return false;
  if (a === b) return true;
  const g = (x: UygulamaIstegi) => JSON.stringify({ ...x, kapak: undefined });
  return g(a) === g(b);
}

/* ───────────────────────────── Ön yüz denetimi:  saf işlevler lib/denetim.ts'te
    ( bağımlılıksız — testler/test_on_yuz_denetimi.py onu Node ile doğrudan koşar ) */
export { alanHatasi, kutuyaYaz, sayiOku } from "./denetim";

export interface FormHatasi {
  anahtar: string;
  hata: string;
  /**  null:  binaya ait alan  */
  asansor: number | null;
}

/**  Projenin kural dışı girdileri — gizli alanlar hariç.  */
export function formHatalari(sema: AlanSemasi, p: UygulamaProjesi): FormHatasi[] {
  const gizli = gizliAlanlar(sema, p);
  const ortak = kuyununOrtaklari(sema, p);
  const l: FormHatasi[] = [];
  p.asansorler.forEach((h, i) => {
    const kip = kipGizlileri(sema, h);
    Object.entries(h).forEach(([k, v]) => {
      //  Tek kuyuda ortak alan bir kez ( 1. asansörde ) söylenir
      const e = !gizli.has(k) && !kip.has(k) && !(i > 0 && ortak.has(k)) && alanHatasi(sema, k, v);
      if (e) l.push({ anahtar: k, hata: e, asansor: i });
    });
  });
  Object.entries(p.proje_geneli).forEach(([k, v]) => {
    const e = !gizli.has(k) && alanHatasi(sema, k, v);
    if (e) l.push({ anahtar: k, hata: e, asansor: null });
  });
  return l;
}

/**  Kısa gecikmeli değer — yazarken her tuşta istek gitmesin.
     null gelen değer beklenmez:  son geçerli değer kalır ( kural dışı girdi
     sunucuya gitmez, ekran son geçerli girdinin sonucunu gösterir ).
     hemen değişince beklenmez ( useSunucu:  asansör sayısı ):  o render'da güncel
     değer döner — DURUMDAN TÜRETİLİR, render sırasında duruma yazılmaz.  25 Eki:
     render sırasında yazılıyordu;  aynı duruma zamanlayıcının ( değer aynı olduğu
     için atlanmış ) güncellemesi kuyrukta beklerken React render sırasındaki
     güncellemeyi temel duruma işlemiyor, sonraki render eski değeri geri getiriyordu:
     yeniden açılan projede asansör eklenince çizim eski listeyle isteniyordu.  */
export function useGecikmeli<T>(deger: T, ms = 280, hemen?: unknown): T {
  const [g, setG] = useState({ deger, hemen });
  const hemenDegisti = hemen !== g.hemen && deger !== null;
  useEffect(() => {
    if (deger === null) return;
    //  hemen değiştiyse render güncel değeri zaten döndürdü:  beklemeden saklanır
    const t = setTimeout(
      () => setG((o) => (o.deger === deger && o.hemen === hemen ? o : { deger, hemen })),
      hemenDegisti ? 0 : ms,
    );
    return () => clearTimeout(t);
  }, [deger, ms, hemen, hemenDegisti]);
  return hemenDegisti ? deger : g.deger;
}

export function useGoreceZaman(t: number) {
  //  "Şimdi" ekran açıldığında bir kez alınır ( render saf kalsın )
  const [simdi] = useState(() => Date.now());
  return useMemo(() => {
    if (!t) return "—";
    const s = Math.round((simdi - t) / 1000);
    if (s < 60) return "az önce";
    if (s < 3600) return `${Math.round(s / 60)} dk önce`;
    if (s < 86400) return `${Math.round(s / 3600)} saat önce`;
    return new Date(t).toLocaleDateString("tr-TR", { day: "numeric", month: "long" });
  }, [t, simdi]);
}

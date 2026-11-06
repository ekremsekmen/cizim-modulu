/*  TUVAL — sunucunun çizimleri, gerçek boyutlarıyla ( SVG width / height mm ).
    TEK ÇİZİM ( Ö3 · K1 ):  tuvalde bir çizim;  alttaki şerit çizimler arasında
    geçer ( K2 ), "Tümü" bütün çizimleri eşit kartlarda gösterir ( K4 ) — karta
    tıklamak onu açar.  Açılışta son bakılan çizim ( ilk açılışta kuyu planı;
    çizimde sorun varsa sorunun çizimi ).  Bütün çizimler sayfada kalır, yalnız
    seçili olan görünür:  sorun ve parça aramaları hepsinde yapılır.
    Tekerlek yakınlaştırır ( imleç çevresinde ), sürükleme kaydırır, ölçüye
    tıklamak kaynağını, parçaya tıklamak onu belirleyen girdileri açar.
    Parçanın üstüne gelince adı yazar ve parça vurgulanır.  Uzak görünümde
    çizim yazıları gizlenir ( ayrıntı kademesi ).                           */
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { Check, CircleHelp, LayoutGrid, Layers, Loader2, Maximize, Minus, Plus, Scan } from "lucide-react";
import type { Cizim, CizimSorunu } from "@/lib/api";
import { depoOku, depoYaz } from "@/lib/depo";
import { cn } from "@/lib/utils";
import { Acilir, AcilirIcerik, AcilirTetik, Dugme, Ipucu } from "@/components/ui";

export interface OlcuSecimi {
  cizim: string;
  index: number;
  metin: string;
  aciklama: string;
}

/**  Fare altındaki ( ya da tıklanan ) parça:  çizimi, ekrandaki kimliği ( "ad-n" ) ve görünen adı.  */
export interface Parca {
  cizim: string;
  id: string;
  adi: string;
}

/**  Seçili ölçünün tuvaldeki kutusu ve tuvalin boyu ( piksel ).  */
export interface OlcuKonumu {
  sol: number;
  sag: number;
  ust: number;
  alt: number;
  w: number;
  h: number;
}

interface Yer {
  c: Cizim;
  x: number;
  y: number;
  w: number;
  h: number;
  /**  Levhadaki ölçeği:  tek çizimde 1, Tümü'de kartına sığacak kadar  */
  s: number;
  /**  Tümü'de kartın sol üst köşesi ( çizim kartına ortalanır;  adı kartın enince )  */
  kx?: number;
  ky?: number;
}

/**  Tümü'nün kartı ( levha birimi = kâğıt mm ) ve aralığı  */
const KART_EN = 1200;
const KART_BOY = 900;
const KART_ARA = 160;
/**  Alttaki çizim şeridinin tuvalde kapladığı yer ( piksel )  */
const SERIT = 52;
const ACILIS = "kuyu_plani";

function boyut(svg: string) {
  const w = /width="([\d.]+)mm"/.exec(svg)?.[1];
  const h = /height="([\d.]+)mm"/.exec(svg)?.[1];
  return { w: Number(w) || 300, h: Number(h) || 300 };
}

/**  Tek çizim:  her çizim levhanın başında, kendi boyunda ( yalnız seçili görünür ).  */
function tekYerler(cizimler: Cizim[]): Yer[] {
  return cizimler.map((c) => ({ c, x: 0, y: 0, s: 1, ...boyut(c.svg) }));
}

/**  Tümü ( K4 ):  eşit kartlar, satır satır;  sütun sayısı tuvalin en-boy oranından —
     kartlar en büyük boyla sığsın.  Her çizim kartına ortalanır.  */
function kartYerleri(cizimler: Cizim[], en: number, boy: number): Yer[] {
  const n = cizimler.length;
  if (!n) return [];
  let iyi = { sutun: 1, k: 0 };
  for (let sutun = 1; sutun <= n; sutun++) {
    const satir = Math.ceil(n / sutun);
    const k = Math.min(en / (sutun * (KART_EN + KART_ARA)), boy / (satir * (KART_BOY + KART_ARA)));
    if (k > iyi.k) iyi = { sutun, k };
  }
  return cizimler.map((c, i) => {
    const b = boyut(c.svg);
    const s = Math.min(KART_EN / b.w, KART_BOY / b.h);
    const kx = (i % iyi.sutun) * (KART_EN + KART_ARA);
    const ky = Math.floor(i / iyi.sutun) * (KART_BOY + KART_ARA);
    return { c, x: kx + (KART_EN - b.w * s) / 2, y: ky + (KART_BOY - b.h * s) / 2, s, kx, ky, ...b };
  });
}

/**  Çizimin içinde geçen parça adları ( data-ad ) — şeridin rozetleri için  */
function parcaAdlari(svg: string) {
  return new Set([...svg.matchAll(/data-ad="([^"]+)"/g)].map((m) => m[1].replace(/&amp;/g, "&").replace(/&quot;/g, '"')));
}


/*  EKRAN KALEMİ ( mevcut programdan ):  her çizgi kâğıttaki kalemine göre
    işaretlenir ( data-k="050" ), ekranda en az kalınlığı korunur — uzaktan
    ince kalemler kaybolmaz, yakından kâğıttaki oranlar görünür.            */
const KALEMLER: [number, number][] = [[0.7, 2.5], [0.5, 2.0], [0.35, 1.6], [0.25, 1.3], [0.18, 1.1], [0.13, 1.0]];
const kalemAdi = (mm: number) => String(Math.round(mm * 100)).padStart(3, "0");

function kalemleriIsaretle(fig: HTMLElement, olcek: number) {
  //  İşaret svg'nin üstünde:  yeni yanıt svg'yi değiştirince yeniden işaretlenir
  const svg = fig.querySelector("svg");
  if (!svg || svg.dataset.kalem) return;
  svg.dataset.kalem = "1";
  for (const el of svg.querySelectorAll("line, rect, polyline, polygon, circle, path, ellipse")) {
    const sw = parseFloat(el.getAttribute("stroke-width") ?? "");
    const renk = el.getAttribute("stroke");
    if (!(sw > 0) || !renk || renk === "none" || renk === "transparent" || el.classList.contains("tut")) continue;
    const mm = sw / olcek;
    const k = KALEMLER.reduce((a, b) => (Math.abs(b[0] - mm) < Math.abs(a[0] - mm) ? b : a));
    if (Math.abs(k[0] - mm) <= 0.3 * k[0]) el.setAttribute("data-k", kalemAdi(k[0]));
  }
}

/**  Ekrandaki noktanın altındaki parça:  üst üste gelenlerden EN KÜÇÜĞÜ ( kabinin
     içindeki tampon kabin değil tampon;  eski arayüzle aynı kural ).  Ölçünün,
     araç şeridinin ya da bir kutunun üstündeyse yok.  */
function parcaBul(x: number, y: number, kap: HTMLElement | null): Parca | null {
  let en: Element | null = null;
  let alan = Infinity;
  for (const s of document.elementsFromPoint(x, y)) {
    if (s === kap) break;
    if (s.closest(".olcu, [data-tuval-arac], [data-olcu-kutu]")) return null;
    const g = s.closest("[data-parca]");
    if (!g || !(s instanceof SVGGraphicsElement)) continue;
    const b = s.getBBox();
    const a = Math.max(b.width, 1) * Math.max(b.height, 1);
    if (a < alan) {
      en = g;
      alan = a;
    }
  }
  if (!en) return null;
  const fig = en.closest("figure[data-cizim]") as HTMLElement | null;
  const id = (en as SVGGElement).dataset.parca!;
  return { cizim: fig?.dataset.cizim ?? "", id, adi: (en as SVGGElement).dataset.ad ?? id.slice(0, id.lastIndexOf("-")) };
}

/**  Tuvaldeki kutunun ( ölçü ) yeri:  seçileni ÖRTMEZ — önce sağında,
     sığmazsa solunda, o da olmazsa altında ya da üstünde;  tuvalin dışına
     taşmaz.  Tuval kutudan darsa kutu tuvalin enine iner ( dar pencerede kutu
     sola taşıp kesiliyordu — 19 Eki ).  */
/**  Ölçü kutusunun tuvalde başlayabileceği en üst yer ( araç şeridinin altı )  */
export const KUTU_UST = 64;

export function kutuYeri(konum: OlcuKonumu, istenenEn: number, boy: number) {
  const ARA = 16;
  const KENAR = 12;
  //  Üstte araç şeridi ( görünüm, yakınlık, katmanlar ):  kutu onun altında başlar
  const UST = KUTU_UST;
  const en = Math.min(istenenEn, konum.w - 2 * KENAR);
  let sol: number;
  let ust: number;
  if (konum.sag + ARA + en < konum.w - KENAR) sol = konum.sag + ARA;
  else if (konum.sol - ARA - en > KENAR) sol = konum.sol - ARA - en;
  else sol = Math.min(Math.max(KENAR, konum.sol), konum.w - en - KENAR);
  if (sol >= konum.sag || sol + en <= konum.sol) ust = (konum.ust + konum.alt) / 2 - 80;
  else ust = konum.alt + ARA + boy < konum.h ? konum.alt + ARA : konum.ust - ARA - boy;
  ust = Math.max(UST, Math.min(ust, konum.h - boy - KENAR));
  return { sol, ust, en };
}

function kisaAd(baslik: string) {
  return baslik.split("(")[0].trim();
}

export function Tuval({
  cizimler,
  durum,
  secili,
  olcuSec,
  odak,
  hatirla,
  sorunluParcalar = [],
  sorunOdak = null,
  hesapParcalari = [],
  hesapSecili = [],
  seciliParca = null,
  parcaSec,
  parcaKutusu,
  hesapOdak = null,
  geciciCizim = null,
  sorunSayisi = 0,
  sorunlaraGit,
  children,
}: {
  /**  Uygunluk kartının "Çizimde göster"i:  bu parçaları en çok gösteren çizime geçer
       ( n her istekte artar )  */
  hesapOdak?: { parcalar: string[]; n: number } | null;
  /**  Verildikçe tuval bu çizimde ( kat tablosu açıkken düşey kesit — K5 );  kalkınca
       önceki görünüme döner.  Son bakılan çizim olarak saklanmaz.  */
  geciciCizim?: string | null;
  /**  Hesap / çizim durunca sorunların sayısı ( sorunlar Uygunluk panelinde — K3 )  */
  sorunSayisi?: number;
  sorunlaraGit?: () => void;
  /**  Sorunlu parçalar ( data-ad ) — kırmızı işaretlenir  */
  sorunluParcalar?: string[];
  /**  Hesabın uygun bulmadığı bölümlerin parçaları ( data-ad ) — turuncu  */
  hesapParcalari?: string[];
  /**  Uygunluk panelinde seçilen bölümün parçaları — turuncu, yanıp söner  */
  hesapSecili?: string[];
  /**  Kartta seçilen sorun:  parçaları öne çıkar, tuval onun çizimine gider
       ( n her seçimde artar — aynı soruna yeniden tıklamak da götürür )  */
  sorunOdak?: { sorun: CizimSorunu; n: number } | null;
  /**  Açılışta gösterilecek çizim ( adres:  ?cizim=kuyu_plani ) — son bakılanın önünde  */
  odak?: string | null;
  /**  Son bakılan çizimin saklandığı anahtar ( projeye göre;  yoksa saklanmaz )  */
  hatirla?: string;
  cizimler: Cizim[];
  /**  sorunlu:  çizim güncel ama kuralları sağlamıyor ( sorunlar kartta )  */
  durum: "guncel" | "yukleniyor" | "eski" | "sorunlu";
  secili: OlcuSecimi | null;
  olcuSec: (o: OlcuSecimi | null, kutu?: DOMRect) => void;
  /**  Tıklanan parça ( kutusu açık ) — vurgulu  */
  seciliParca?: Parca | null;
  /**  Parçaya tıklanınca ( boşluğa tıklayınca null );  verilmezse parça seçilmez  */
  parcaSec?: (p: Parca | null) => void;
  /**  Seçili parçanın kutusu ( konumu tuvale göre )  */
  parcaKutusu?: (konum: OlcuKonumu) => React.ReactNode;
  children?: (konum: OlcuKonumu | null) => React.ReactNode;
}) {
  const kap = useRef<HTMLDivElement>(null);
  const [g, setG] = useState({ x: 40, y: 60, k: 0.3 });
  //  NETLİK ( 20 Eki — kullanıcı:  "çizim ekranının bulanıklaşması kritik" ):
  //  levha yalnız CSS ölçeğiyle büyütülünce tarayıcı ( Safari ) çizimi bir kez
  //  resme çevirip büyütüyordu — yakında bulanık.  Gezinirken ölçek hızlı
  //  ( transform ), durunca 120 ms sonra çizimler kendi boyunda yeniden çizilir
  //  ( vektör, keskin ):  kNet figürlerin boyutuna geçer, transform yalnız
  //  aradaki farkı taşır.  Ekrandaki ölçek ( g.k ) ve kalemler değişmez.
  const [kNet, setKNet] = useState(g.k);
  useEffect(() => {
    if (g.k === kNet) return;
    const t = setTimeout(() => setKNet(g.k), 120);
    return () => clearTimeout(t);
  }, [g.k, kNet]);
  const [gizli, setGizli] = useState<Set<string>>(new Set());
  //  Görünüm:  tek çizim ( aktif ) ya da Tümü
  const [kipSecimi, setKip] = useState<"tek" | "tumu">("tek");
  const [aktifSecimi, setAktif] = useState<string | null>(null);
  //  Geçici çizim ( kat tablosu açıkken ) seçimin önündedir;  kalkınca seçim olduğu gibi döner
  const gecici = !!geciciCizim && cizimler.some((c) => c.ad === geciciCizim);
  const kip = gecici ? "tek" : kipSecimi;
  //  Seçilen çizim yeni yanıtta yoksa ( düzen değişti ) kuyu planı, o da yoksa ilki
  const aktif = gecici
    ? geciciCizim!
    : cizimler.some((c) => c.ad === aktifSecimi)
      ? aktifSecimi!
      : (cizimler.find((c) => c.ad === ACILIS) ?? cizimler[0])?.ad ?? null;
  const [boyut, setBoyut] = useState<{ en: number; boy: number } | null>(null);
  useLayoutEffect(() => {
    const el = kap.current;
    if (!el) return;
    const olc = () => {
      const b = { en: el.clientWidth, boy: el.clientHeight };
      if (b.en && b.boy) setBoyut(b);
    };
    //  İlk ölçü hemen ( gözlemcinin ilk bildirimi sayfa çizilene kadar gecikebilir )
    olc();
    const ro = new ResizeObserver(olc);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  const yerler = useMemo(
    () => (kip === "tumu" && boyut ? kartYerleri(cizimler, boyut.en - 64, boyut.boy - 104 - SERIT) : tekYerler(cizimler)),
    [cizimler, kip, boyut],
  );
  const katmanlar = useMemo(() => {
    const s = new Set<string>();
    for (const c of cizimler) for (const m of c.svg.matchAll(/data-katman="([^"]+)"/g)) s.add(m[1]);
    return [...s].sort();
  }, [cizimler]);
  //  Şeridin rozetleri:  çizimde sorunlu ( kırmızı ) ya da hesabın uygun bulmadığı ( turuncu ) parça var mı
  const adlar = useMemo(() => new Map(cizimler.map((c) => [c.ad, parcaAdlari(c.svg)])), [cizimler]);
  const iceren = (ad: string, parcalar: string[]) => parcalar.some((p) => adlar.get(ad)?.has(p));

  //  Görünen çizimler ( tek kipte yalnız aktif )
  const gorunen = useMemo(() => (kip === "tumu" ? yerler : yerler.filter((y) => y.c.ad === aktif)), [kip, yerler, aktif]);
  const sigdir = useCallback(() => {
    const el = kap.current;
    if (!el || !gorunen.length) return;
    const x0 = Math.min(...gorunen.map((y) => y.x));
    const y0 = Math.min(...gorunen.map((y) => y.y));
    const x1 = Math.max(...gorunen.map((y) => y.x + y.w * y.s));
    const y1 = Math.max(...gorunen.map((y) => y.y + y.h * y.s));
    const W = el.clientWidth;
    const Hh = el.clientHeight - SERIT;
    const ust = 64;
    const k = Math.min((W - 64) / (x1 - x0), (Hh - ust - 40) / (y1 - y0));
    setG({ k, x: (W - (x1 - x0) * k) / 2 - x0 * k, y: ust + (Hh - ust - 40 - (y1 - y0) * k) / 2 - y0 * k });
  }, [gorunen]);

  //  Levhadaki bir kutuya ( 1 px = 1 mm kâğıt ) yakınlaş:  çevresiyle ( kutunun
  //  yarısı kadar, en az 30 ), en çok 5× ( parça okunur, yanındakiler de görünür ).
  //  Kutu çizimin kendisinden büyük çıkarsa çizim sığdırılır ( uzaklaşılmaz ).
  const kutuyaGit = useCallback(
    (hedef: string, x0: number, y0: number, x1: number, y1: number) => {
      const el = kap.current;
      const yer = yerler.find((y) => y.c.ad === hedef);
      if (!el || !yer) return;
      const pay = Math.max(30, Math.max(x1 - x0, y1 - y0) / 2);
      const [a0, b0, a1, b1] = [x0 - pay, y0 - pay, x1 + pay, y1 + pay];
      const W = el.clientWidth;
      const Hh = el.clientHeight - SERIT;
      const ust = 64;
      const k = Math.min(5, (W - 64) / (a1 - a0), (Hh - ust - 40) / (b1 - b0));
      const cizimin = Math.min((W - 64) / yer.w, (Hh - ust - 40) / yer.h);
      if (k <= cizimin) return sigdir();
      setG({ k, x: (W - (a1 - a0) * k) / 2 - a0 * k, y: ust + (Hh - ust - 40 - (b1 - b0) * k) / 2 - b0 * k });
    },
    [yerler, sigdir],
  );

  /**  Çizime geç ( şerit, Tümü'nün kartı, sorun ):  tek kip, son bakılan saklanır  */
  const goster = useCallback(
    (ad: string) => {
      setKip("tek");
      setAktif(ad);
      if (hatirla) depoYaz(hatirla, ad);
    },
    [hatirla],
  );

  //  AÇILIŞ ( K1 ):  adresteki çizim;  sorunlu çizimde sorunun çizimi;  son bakılan;  kuyu planı
  const ilk = useRef(true);
  useLayoutEffect(() => {
    const el = kap.current;
    if (!ilk.current || !cizimler.length || !el) return;
    ilk.current = false;
    const var_ = (ad: string | null | undefined) => !!ad && cizimler.some((c) => c.ad === ad);
    const sorunun = sorunluParcalar.length
      ? cizimler.find((c) => sorunluParcalar.some((p) => adlar.get(c.ad)?.has(p)))?.ad
      : undefined;
    const son = hatirla ? depoOku(hatirla) : null;
    setAktif(var_(odak) ? odak! : var_(sorunun) ? sorunun! : var_(son) ? son! : null);
  }, [cizimler, odak, hatirla, sorunluParcalar, adlar]);
  //  Görünüm değişince ( çizim, kip ) sığdırılır;  aynı çizimin yeni yanıtında yerinde kalır
  const sigdirilan = useRef<string | null>(null);
  useLayoutEffect(() => {
    const hedef = kip === "tumu" ? "tumu" : aktif;
    if (!hedef || !gorunen.length || !boyut || hedef === sigdirilan.current) return;
    sigdirilan.current = hedef;
    sigdir();
  }, [kip, aktif, gorunen, boyut, sigdir]);

  //  Tekerlek:  imlecin altındaki nokta yerinde kalır
  useEffect(() => {
    const el = kap.current;
    if (!el) return;
    const tekerlek = (e: WheelEvent) => {
      e.preventDefault();
      const r = el.getBoundingClientRect();
      const mx = e.clientX - r.left;
      const my = e.clientY - r.top;
      const f = Math.exp(-e.deltaY * (e.ctrlKey ? 0.01 : 0.0015));
      setG((o) => {
        const k = Math.min(8, Math.max(0.05, o.k * f));
        return { k, x: mx - ((mx - o.x) * k) / o.k, y: my - ((my - o.y) * k) / o.k };
      });
    };
    el.addEventListener("wheel", tekerlek, { passive: false });
    return () => el.removeEventListener("wheel", tekerlek);
  }, []);

  const surukle = useRef<{ x: number; y: number; gx: number; gy: number } | null>(null);
  const kaydi = useRef(false);
  const [surukluyor, setSurukluyor] = useState(false);
  //  Portaldaki öğelerin olayları da React ağacından tuvale yayılır ( ölçü kutusundaki
  //  seçim listesi body'de çizilir ):  tuval onları yok sayar — yoksa seçeneğe
  //  basmak sürüklemeyi başlatıp fareyi tuvale bağlıyor, seçim hiç olmuyordu
  const disarida = (e: React.SyntheticEvent) => !kap.current?.contains(e.target as Node);
  const basildi = (e: React.PointerEvent) => {
    if (disarida(e) || e.button !== 0 || (e.target as Element).closest(".olcu, [data-tuval-arac], [data-olcu-kutu]")) return;
    surukle.current = { x: e.clientX, y: e.clientY, gx: g.x, gy: g.y };
    kaydi.current = false;
    setSurukluyor(true);
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
  };
  //  Üstündeki parça:  durum yalnız parça değişince;  ipucu fareyi DOM'dan izler
  //  ( her harekette tuval yeniden çizilmesin )
  const [ustunde, setUstunde] = useState<Parca | null>(null);
  const ipucu = useRef<HTMLDivElement>(null);
  const ipucunuKoy = (x: number, y: number) => {
    const el = kap.current;
    const t = ipucu.current;
    if (!el || !t) return;
    const r = el.getBoundingClientRect();
    t.style.left = `${Math.min(x - r.left + 14, r.width - t.offsetWidth - 6)}px`;
    t.style.top = `${Math.max(y - r.top - 30, 6)}px`;
  };
  const oynadi = (e: React.PointerEvent) => {
    if (disarida(e)) return;
    const s = surukle.current;
    if (!s || !kaydi.current) {
      const p = kip === "tek" ? parcaBul(e.clientX, e.clientY, kap.current) : null;
      if (p?.id !== ustunde?.id || p?.cizim !== ustunde?.cizim) setUstunde(p);
      if (p) ipucunuKoy(e.clientX, e.clientY);
    }
    if (!s) return;
    if (Math.abs(e.clientX - s.x) + Math.abs(e.clientY - s.y) > 4) {
      kaydi.current = true;
      setUstunde(null);
    }
    setG((o) => ({ ...o, x: s.gx + e.clientX - s.x, y: s.gy + e.clientY - s.y }));
  };
  const birakti = () => {
    surukle.current = null;
    setSurukluyor(false);
  };

  const olcuyuSec = (o: Element) => {
    const fig = o.closest("[data-cizim]") as HTMLElement;
    parcaSec?.(null);
    olcuSec({
      cizim: fig.dataset.cizim!,
      index: Number((o as SVGGElement).dataset.olcu),
      metin: o.querySelector("text")?.textContent ?? "",
      aciklama: (o as SVGGElement).dataset.aciklama ?? "",
    });
  };
  //  Sunucunun ölçüleri odaklanabilir ( tabindex, role=button ):  Enter / boşluk tıklama gibidir
  const tusa = (e: React.KeyboardEvent) => {
    if (disarida(e)) return;
    const o = (e.target as Element).closest?.(".olcu");
    if (o && (e.key === "Enter" || e.key === " ")) {
      e.preventDefault();
      olcuyuSec(o);
    }
  };

  const tiklandi = (e: React.MouseEvent) => {
    if (disarida(e)) return;
    const hedef = e.target as Element;
    if (hedef.closest("[data-tuval-arac], [data-olcu-kutu]")) return;
    if (kaydi.current) return; //  kaydırma bırakılışı tıklama değil
    //  Tümü'de karta tıklamak çizimi açar.  Hedef noktadan bulunur:  sürükleme için
    //  işaretçi tuvale bağlı ( setPointerCapture ), tıklamanın hedefi tuvalin kendisi olur
    if (kip === "tumu") {
      const fig = document
        .elementsFromPoint(e.clientX, e.clientY)
        .map((x) => x.closest("figure[data-cizim]"))
        .find(Boolean) as HTMLElement | undefined;
      if (fig?.dataset.cizim) goster(fig.dataset.cizim);
      return;
    }
    const o = hedef.closest(".olcu") as SVGGElement | null;
    if (o) return olcuyuSec(o);
    //  Parçaya tıklamak onu belirleyen girdileri açar;  boşluğa tıklamak kutuları kapatır
    const p = parcaSec ? parcaBul(e.clientX, e.clientY, kap.current) : null;
    olcuSec(null);
    parcaSec?.(p);
  };

  //  Seçili ölçünün ( ya da parçanın ) vurgusu ve kutunun yeri ( tuvale göre )
  const [konum, setKonum] = useState<OlcuKonumu | null>(null);
  useLayoutEffect(() => {
    const el = kap.current;
    el?.querySelectorAll(".olcu.secili").forEach((x) => x.classList.remove("secili"));
    if (!el || !secili) return setKonum(null);
    const o = el.querySelector(`[data-cizim="${secili.cizim}"] .olcu[data-olcu="${secili.index}"]`);
    if (!o) return setKonum(null);
    o.classList.add("secili");
    const r = el.getBoundingClientRect();
    const b = o.getBoundingClientRect();
    setKonum({ sol: b.left - r.left, sag: b.right - r.left, ust: b.top - r.top, alt: b.bottom - r.top, w: r.width, h: r.height });
  }, [secili, g, cizimler, aktif, kip]);
  const [parcaKonumu, setParcaKonumu] = useState<OlcuKonumu | null>(null);
  useLayoutEffect(() => {
    const el = kap.current;
    el?.querySelectorAll(".parca-secili").forEach((x) => x.classList.remove("parca-secili"));
    if (!el || !seciliParca) return setParcaKonumu(null);
    const ogeler = [
      ...el.querySelectorAll(`[data-cizim="${seciliParca.cizim}"] [data-parca="${CSS.escape(seciliParca.id)}"]`),
    ];
    ogeler.forEach((x) => x.classList.add("parca-secili"));
    const kutular = ogeler.map((o) => o.getBoundingClientRect()).filter((b) => b.width > 0 || b.height > 0);
    if (!kutular.length) return setParcaKonumu(null);
    const r = el.getBoundingClientRect();
    setParcaKonumu({
      sol: Math.min(...kutular.map((b) => b.left)) - r.left,
      sag: Math.max(...kutular.map((b) => b.right)) - r.left,
      ust: Math.min(...kutular.map((b) => b.top)) - r.top,
      alt: Math.max(...kutular.map((b) => b.bottom)) - r.top,
      w: r.width,
      h: r.height,
    });
  }, [seciliParca, g, cizimler, aktif, kip]);

  //  Sorunlu parçalar ( sunucu:  cizim/sorun.py ) kırmızı;  seçilen sorununki öne çıkar.
  //  Hesabın uygun bulmadığı bölümlerin parçaları ( cizim/hesap_isareti.py ) turuncu;
  //  Uygunluk panelinde seçilen bölümünkiler yanıp söner.  Kırmızı turuncunun önündedir.
  useLayoutEffect(() => {
    const el = kap.current;
    if (!el) return;
    const siniflar = ["parca-sorunlu", "parca-sorun-secili", "parca-hesap", "parca-hesap-secili"];
    el.querySelectorAll(siniflar.map((s) => "." + s).join(", ")).forEach((x) => x.classList.remove(...siniflar));
    const isaretle = (adlar: string[], sinif: string) => {
      for (const ad of adlar) el.querySelectorAll(adSecici(ad)).forEach((x) => x.classList.add(sinif));
    };
    isaretle(hesapParcalari, "parca-hesap");
    isaretle(hesapSecili, "parca-hesap-secili");
    isaretle(sorunluParcalar, "parca-sorunlu");
    isaretle(sorunOdak?.sorun.parcalar ?? [], "parca-sorun-secili");
  }, [sorunluParcalar, sorunOdak, hesapParcalari, hesapSecili, cizimler]);

  //  Seçilen sorunun yerine git:  sunucunun söylediği çizim ( parçası oradaysa ),
  //  yoksa parçanın göründüğü ilk çizim;  önce o çizime geçilir, görününce
  //  parçaların kutusuna yakınlaşılır ( bütün kesit sığınca tepedeki parça
  //  okunmuyordu ).  Her seçim bir kez götürür.
  const gidilenSorun = useRef(0);
  useLayoutEffect(() => {
    const el = kap.current;
    if (!el || !sorunOdak || sorunOdak.n === gidilenSorun.current) return;
    const { cizim, parcalar } = sorunOdak.sorun;
    const ogeler = (ad: string) =>
      parcalar.flatMap((p) => [...el.querySelectorAll(`[data-cizim="${ad}"] ${adSecici(p)}`)]);
    const hedef = cizim && ogeler(cizim).length ? cizim : yerler.find((y) => ogeler(y.c.ad).length)?.c.ad;
    const yer = yerler.find((y) => y.c.ad === hedef);
    if (!hedef || !yer) return;
    if (kip !== "tek" || aktif !== hedef) return goster(hedef);
    const fig = el.querySelector(`figure[data-cizim="${hedef}"]`);
    if (!fig) return;
    gidilenSorun.current = sorunOdak.n;
    //  Ekrandaki kutular levhaya:  figürün içindeki oranı × figürün levhadaki boyu
    const f = fig.getBoundingClientRect();
    //  Boyutsuz öğe ( gizli, boş ) ( 0, 0 ) noktasında döner:  kutuyu ekranın köşesine uzatırdı
    const kutular = ogeler(hedef)
      .map((o) => o.getBoundingClientRect())
      .filter((r) => r.width > 0 || r.height > 0);
    if (!f.width || !f.height || !kutular.length) return sigdir();
    const lx = (x: number) => yer.x + ((x - f.left) / f.width) * yer.w;
    const ly = (y: number) => yer.y + ((y - f.top) / f.height) * yer.h;
    kutuyaGit(
      hedef,
      lx(Math.min(...kutular.map((r) => r.left))),
      ly(Math.min(...kutular.map((r) => r.top))),
      lx(Math.max(...kutular.map((r) => r.right))),
      ly(Math.max(...kutular.map((r) => r.bottom))),
    );
  }, [sorunOdak, yerler, sigdir, kutuyaGit, kip, aktif, goster]);

  //  "Çizimde göster" ( hesabın bölümü ):  parçalarının en çok göründüğü çizim
  const gidilenHesap = useRef(0);
  useLayoutEffect(() => {
    const el = kap.current;
    if (!el || !hesapOdak || hesapOdak.n === gidilenHesap.current) return;
    gidilenHesap.current = hesapOdak.n;
    const say = (ad: string) =>
      hesapOdak.parcalar.reduce((t, p) => t + el.querySelectorAll(`[data-cizim="${ad}"] ${adSecici(p)}`).length, 0);
    const [en] = yerler.map((y) => ({ ad: y.c.ad, n: say(y.c.ad) })).sort((a, b) => b.n - a.n);
    if (!en?.n) return;
    if (kip !== "tek" || aktif !== en.ad) goster(en.ad);
    else sigdir();
  }, [hesapOdak, yerler, kip, aktif, goster, sigdir]);

  //  Parça vurgusu:  fare altındaki parçanın bütün öğeleri
  useLayoutEffect(() => {
    const el = kap.current;
    if (!el) return;
    el.querySelectorAll(".parca-ustunde").forEach((x) => x.classList.remove("parca-ustunde"));
    if (ustunde)
      el.querySelectorAll(`[data-cizim="${ustunde.cizim}"] [data-parca="${CSS.escape(ustunde.id)}"]`).forEach((x) =>
        x.classList.add("parca-ustunde"),
      );
  }, [ustunde, cizimler]);

  useLayoutEffect(() => {
    kap.current?.querySelectorAll<HTMLElement>("figure[data-cizim]").forEach((f) => {
      const y = yerler.find((q) => q.c.ad === f.dataset.cizim);
      if (y) kalemleriIsaretle(f, y.c.olcek || 20);
    });
  }, [yerler]);

  const dpr = typeof window !== "undefined" ? window.devicePixelRatio || 1 : 1;
  const kalemStili = Object.fromEntries(
    KALEMLER.map(([mm, enaz]) => [`--k${kalemAdi(mm)}`, `${Math.max(enaz / dpr, mm * g.k).toFixed(3)}px`]),
  ) as React.CSSProperties;

  //  Yakınlık yüzdesi "sığdı" görünümüne göre ( görünen çizimler )
  const sigdirmaOrani = useMemo(() => {
    if (!boyut || !gorunen.length) return 1;
    const x0 = Math.min(...gorunen.map((y) => y.x));
    const y0 = Math.min(...gorunen.map((y) => y.y));
    const x1 = Math.max(...gorunen.map((y) => y.x + y.w * y.s));
    const y1 = Math.max(...gorunen.map((y) => y.y + y.h * y.s));
    return Math.min((boyut.en - 64) / (x1 - x0), (boyut.boy - SERIT - 104) / (y1 - y0));
  }, [gorunen, boyut]);

  const uzak = kip === "tumu" || 2.5 * g.k * dpr < 5;
  const katmanStili = [...gizli].map((k) => `.tuval-svg [data-katman="${k}"]{display:none}`).join("");

  return (
    <div
      ref={kap}
      className={cn("relative h-full w-full touch-none overflow-hidden bg-tuval select-none", uzak && "tuval-uzak")}
      onPointerDown={basildi}
      onPointerMove={oynadi}
      onPointerUp={birakti}
      onPointerLeave={() => setUstunde(null)}
      onClick={tiklandi}
      onKeyDown={tusa}
      //  Odak ( ölçü kutusundaki girdi ) tuvali kaydırmasın:  görünüm yalnız g'den
      onScroll={(e) => {
        e.currentTarget.scrollTop = 0;
        e.currentTarget.scrollLeft = 0;
      }}
      style={{ cursor: surukluyor ? "grabbing" : kip === "tumu" ? "pointer" : "default" }}
    >
      <style>{katmanStili}</style>
      {/*  Çizim levhası:  1 px = 1 mm, bütün levha ölçeklenir  */}
      <div
        className={cn("absolute top-0 left-0 origin-top-left transition-opacity", durum === "eski" && "opacity-40")}
        style={{ transform: `translate(${g.x}px, ${g.y}px) scale(${g.k / kNet})`, ...kalemStili }}
      >
        {yerler.map((y) => (
          <figure
            key={y.c.ad}
            data-cizim={y.c.ad}
            aria-label={y.c.baslik}
            hidden={kip === "tek" && y.c.ad !== aktif}
            className={cn("tuval-svg absolute m-0", kip === "tumu" && "rounded-sm ring-1 ring-white/10 hover:ring-olcu/60")}
            style={{
              left: y.x * kNet,
              top: y.y * kNet,
              width: y.w * y.s * kNet,
              height: y.h * y.s * kNet,
              ["--mu" as string]: ((g.k * y.s) / (y.c.olcek || 20)).toPrecision(6),
            }}
            dangerouslySetInnerHTML={{ __html: y.c.svg }}
          />
        ))}
      </div>

      {/*  Çizim adları — Tümü'nün kartlarında ( tek çizimin adı şeritte )  */}
      {kip === "tumu" &&
        yerler.map((y) => (
          <div
            key={y.c.ad}
            //  Ad sığmazsa kesilmez, iki satıra iner;  alt kenarı kartın 6 px üstünde
            className="pointer-events-none absolute line-clamp-2 -translate-y-full text-[11.5px] leading-tight font-medium tracking-wide text-tuval-metin-2"
            style={{ left: g.x + (y.kx ?? y.x) * g.k, top: g.y + (y.ky ?? y.y) * g.k - 6, maxWidth: Math.max(80, KART_EN * g.k) }}
          >
            {kisaAd(y.c.baslik)}
            {!y.c.olceksiz && <span className="sayi ml-2 whitespace-nowrap text-tuval-metin-2/70">1:{y.c.olcek}</span>}
          </div>
        ))}

      {/*  Araç şeridi  */}
      <div
        data-tuval-arac
        className="absolute top-3 left-3 flex items-center gap-1 rounded-buyuk border border-white/[0.08] bg-tuval-2/95 p-1 shadow-tuval backdrop-blur"
      >
        <Ipucu metin="Uzaklaştır">
          <Dugme tur="tuval" boy="simge-kucuk" aria-label="Uzaklaştır" onClick={() => setG((o) => yakinlik(o, 1 / 1.25, kap.current))}>
            <Minus />
          </Dugme>
        </Ipucu>
        <span className="sayi w-11 text-center text-[11.5px] text-tuval-metin-2">
          {Math.round((g.k / sigdirmaOrani) * 100)}%
        </span>
        <Ipucu metin="Yakınlaştır">
          <Dugme tur="tuval" boy="simge-kucuk" aria-label="Yakınlaştır" onClick={() => setG((o) => yakinlik(o, 1.25, kap.current))}>
            <Plus />
          </Dugme>
        </Ipucu>
        <Ipucu metin="Sığdır">
          <Dugme tur="tuval" boy="simge-kucuk" aria-label="Sığdır" onClick={sigdir}>
            <Scan />
          </Dugme>
        </Ipucu>
        <span className="mx-0.5 h-4 w-px bg-white/10" />
        <Acilir>
          <AcilirTetik asChild>
            <Dugme tur="tuval" boy="kucuk" aria-label="Katmanlar">
              <Layers /> Katmanlar
              {gizli.size > 0 && <span className="sayi text-olcu">{gizli.size} gizli</span>}
            </Dugme>
          </AcilirTetik>
          <AcilirIcerik align="start" className="w-60 p-1.5" data-tuval-arac>
            <p className="px-2 pt-1 pb-1.5 text-[11.5px] font-medium text-metin-3">DXF ile aynı katmanlar</p>
            <div className="max-h-72 overflow-y-auto">
              {katmanlar.map((k) => {
                const acik = !gizli.has(k);
                return (
                  <button
                    key={k}
                    type="button"
                    role="menuitemcheckbox"
                    aria-checked={acik}
                    onClick={() => {
                      const y = new Set(gizli);
                      if (acik) y.add(k);
                      else y.delete(k);
                      setGizli(y);
                    }}
                    className="flex w-full items-center gap-2 rounded-kucuk px-2 py-1.5 text-left font-mono text-[12px] hover:bg-black/[0.04]"
                  >
                    <span
                      className={cn(
                        "flex size-3.5 items-center justify-center rounded-[3px] border",
                        acik ? "border-vurgu bg-vurgu text-white" : "border-cizgi-2",
                      )}
                    >
                      {acik && <Check className="size-2.5" strokeWidth={3} />}
                    </span>
                    {k}
                  </button>
                );
              })}
            </div>
          </AcilirIcerik>
        </Acilir>
        <Ipucu metin="Tam ekran">
          <Dugme
            tur="tuval"
            boy="simge-kucuk"
            aria-label="Tam ekran"
            onClick={() => (document.fullscreenElement ? document.exitFullscreen() : kap.current?.requestFullscreen())}
          >
            <Maximize />
          </Dugme>
        </Ipucu>
        {/*  Yardım ( eskiden tuvalin altındaki ipucu satırı — çizimin üstüne biniyordu )  */}
        <Acilir>
          <AcilirTetik asChild>
            <Dugme tur="tuval" boy="simge-kucuk" aria-label="Tuval yardımı">
              <CircleHelp />
            </Dugme>
          </AcilirTetik>
          <AcilirIcerik align="start" className="w-72 p-3 text-[12.5px] leading-relaxed" data-tuval-arac>
            <ul className="space-y-1.5">
              <li>Tekerlek yakınlaştırır, sürüklemek kaydırır.</li>
              <li>Ölçüye tıklayın:  kaynağı ve ölçüden değiştirme.</li>
              <li>Parçaya tıklayın:  onu belirleyen girdiler.</li>
              <li>Alttaki şeritten çizim seçin;  Tümü bütün çizimleri gösterir, karta tıklamak açar.</li>
            </ul>
          </AcilirIcerik>
        </Acilir>
      </div>

      {/*  Çizimin durumu:  güncel mi, yolda mı, eski mi, uygun değil mi  */}
      <div data-tuval-arac className="absolute top-3 right-3">
        {durum === "yukleniyor" ? (
          <DurumHapi>
            <Loader2 className="size-3 animate-spin" /> Çiziliyor
          </DurumHapi>
        ) : durum === "eski" ? (
          <DurumHapi uyari>Çizim güncel değil</DurumHapi>
        ) : durum === "sorunlu" || sorunSayisi > 0 ? (
          //  Sorunlar Uygunluk panelinde ( K3 ):  hap oraya götürür
          <button type="button" onClick={sorunlaraGit} aria-label={`Sorunlara git — ${sorunSayisi} sorun`}>
            <DurumHapi tehlike>
              <span className="size-1.5 rounded-full bg-[#f97066]" /> {durum === "sorunlu" ? "Uygun değil" : "Hesap durdu"}
              {sorunSayisi > 0 && <span className="sayi opacity-80">· {sorunSayisi} sorun</span>}
            </DurumHapi>
          </button>
        ) : (
          <DurumHapi>
            <span className="size-1.5 rounded-full bg-[#4ade80]" /> Güncel
          </DurumHapi>
        )}
      </div>

      {/*  Parçanın adı ( fareyi izler )  */}
      <div
        ref={ipucu}
        role="tooltip"
        hidden={!ustunde || surukluyor}
        className="pointer-events-none absolute z-20 rounded-orta border border-white/10 bg-tuval-2/95 px-2 py-1 text-[12px] font-medium whitespace-nowrap text-tuval-metin shadow-tuval"
      >
        {ustunde?.adi}
      </div>

      {/*  ÇİZİM ŞERİDİ ( K2 ):  tuvalin altında;  rozet çizimde sorunlu ( kırmızı ) ya da
           hesabın uygun bulmadığı ( turuncu ) parça olduğunu söyler  */}
      {cizimler.length > 0 && (
        <nav
          data-tuval-arac
          aria-label="Çizimler"
          //  Hepsi sığar ( 6 Kas — kullanıcı:  sağdakiler görünmüyor, tıklanamıyordu ):  düğmeler
          //  şeridi eşit paylaşır, ad cümle düzeninde, sığmayan ad kesilir — tam adı üstüne gelince
          className="absolute inset-x-0 bottom-0 flex items-center gap-0.5 border-t border-white/[0.08] bg-tuval-2/95 px-2 backdrop-blur"
          style={{ height: SERIT }}
        >
          <SeritDugmesi secili={kip === "tumu"} onClick={() => setKip("tumu")} sabit>
            <LayoutGrid className="size-3.5" /> Tümü
          </SeritDugmesi>
          <span className="mx-1 h-5 w-px shrink-0 bg-white/10" />
          {cizimler.map((c) => (
            <SeritDugmesi
              key={c.ad}
              secili={kip === "tek" && c.ad === aktif}
              onClick={() => goster(c.ad)}
              baslik={c.baslik}
              ad={kisaAd(c.baslik)}
            >
              {iceren(c.ad, sorunluParcalar) ? (
                <span aria-hidden title="Sorunlu parça var" className="size-1.5 shrink-0 rounded-full bg-[#f97066]" />
              ) : iceren(c.ad, hesapParcalari) ? (
                <span aria-hidden title="Hesabın uygun bulmadığı parça var" className="size-1.5 shrink-0 rounded-full bg-[#ff9f1a]" />
              ) : null}
              <span className="truncate">{seritAdi(kisaAd(c.baslik))}</span>
            </SeritDugmesi>
          ))}
        </nav>
      )}

      {children?.(konum)}
      {seciliParca && parcaKonumu && parcaKutusu?.(parcaKonumu)}
    </div>
  );
}

/**  Şeritteki kısa ad ( tam başlık üstüne gelince ):  kesit harfi önde, "düşey" / "planı"
     atılır, kuyu kesiti "kesit" olur ( "KUYU ÜSTÜ PLANI F-F" → "F-F kuyu üstü",
     "A-A KUYU DÜŞEY KESİTİ" → "A-A kesit" );  harfsiz çizimde ilk söz ( "Kasnak" ).
     Erişilebilir ad başlığın kendisidir.  */
function seritAdi(ad: string) {
  const kucuk = (x: string) => x.replace(/I/g, "ı").replace(/İ/g, "i").toLowerCase();
  const sozler = ad.split(/\s+/).filter(Boolean);
  const harf = sozler.find((x) => /^[A-ZÇĞİÖŞÜ]-[A-ZÇĞİÖŞÜ]$/.test(x));
  if (!harf) {
    const k = kucuk(sozler[0] ?? ad);
    return k.charAt(0).replace("i", "İ").replace("ı", "I").toUpperCase() + k.slice(1);
  }
  const kalan = sozler.filter((x) => x !== harf && x !== "DÜŞEY" && x !== "PLANI");
  const govde = kalan.at(-1) === "KESİTİ" ? "kesit" : kucuk(kalan.join(" "));
  return `${harf} ${govde}`;
}

function SeritDugmesi({
  secili,
  onClick,
  baslik,
  ad,
  sabit,
  children,
}: {
  secili: boolean;
  onClick: () => void;
  baslik?: string;
  /**  Erişilebilir ad ( görünen kısaltılmış olabilir )  */
  ad?: string;
  /**  Daralmaz ( Tümü )  */
  sabit?: boolean;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      aria-pressed={secili}
      aria-label={ad}
      title={baslik}
      onClick={onClick}
      className={cn(
        "inline-flex h-8 items-center gap-1.5 rounded-orta px-2 text-[12px] font-medium whitespace-nowrap",
        sabit ? "shrink-0" : "max-w-[220px] min-w-0 flex-1 basis-auto justify-center",
        secili ? "bg-white/[0.12] text-white" : "text-tuval-metin-2 hover:bg-white/[0.06] hover:text-tuval-metin",
      )}
    >
      {children}
    </button>
  );
}

/**  data-ad ( parçanın ekrandaki adı ) seçicisi  */
function adSecici(ad: string) {
  return `[data-ad="${ad.replace(/["\\]/g, "\\$&")}"]`;
}

function yakinlik(o: { x: number; y: number; k: number }, f: number, el: HTMLDivElement | null) {
  const mx = (el?.clientWidth ?? 0) / 2;
  const my = (el?.clientHeight ?? 0) / 2;
  const k = Math.min(8, Math.max(0.05, o.k * f));
  return { k, x: mx - ((mx - o.x) * k) / o.k, y: my - ((my - o.y) * k) / o.k };
}

function DurumHapi({ children, uyari, tehlike }: { children: React.ReactNode; uyari?: boolean; tehlike?: boolean }) {
  return (
    <span
      className={cn(
        "inline-flex h-7 items-center gap-1.5 rounded-full border px-2.5 text-[11.5px] font-medium shadow-tuval backdrop-blur",
        uyari
          ? "border-[#f5a524]/40 bg-[#3a2c12]/90 text-[#fbbf24]"
          : tehlike
            ? "border-[#f97066]/40 bg-[#2b1d1f]/90 text-[#fecdca]"
            : "border-white/[0.08] bg-tuval-2/95 text-tuval-metin",
      )}
    >
      {children}
    </span>
  );
}

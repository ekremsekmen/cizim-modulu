/*  TUVAL — sunucunun çizimleri, gerçek boyutlarıyla ( SVG width / height mm ).
    Kesitler solda yan yana, planlar sağda sütun sütun:  paftadaki düzen.
    Tekerlek yakınlaştırır ( imleç çevresinde ), sürükleme kaydırır, ölçüye
    tıklamak kaynağını açar.  Parçanın üstüne gelince adı yazar ve parça
    vurgulanır.  Uzak görünümde çizim yazıları gizlenir, çizimin
    adı tuvalin üstünde okunur ( ayrıntı kademesi ).                        */
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { Check, Layers, Loader2, Maximize, Minus, Plus, Scan } from "lucide-react";
import type { Cizim, CizimSorunu } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Acilir, AcilirIcerik, AcilirTetik, Dugme, Ipucu, Secim } from "@/components/ui";

export interface OlcuSecimi {
  cizim: string;
  index: number;
  metin: string;
  aciklama: string;
}

/**  Fare altındaki parça:  çizimi, ekrandaki kimliği ( "ad-n" ) ve görünen adı.  */
interface Parca {
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
}

const ARALIK = 90;
const KESITLER = new Set(["kuyu_kesiti_yan", "kuyu_kesiti_on"]);

function boyut(svg: string) {
  const w = /width="([\d.]+)mm"/.exec(svg)?.[1];
  const h = /height="([\d.]+)mm"/.exec(svg)?.[1];
  return { w: Number(w) || 300, h: Number(h) || 300 };
}

/**  Kesitler yan yana, planlar sütun sütun.  Sütun yüksekliği tuvalin en-boy
     oranına göre seçilir:  bütün çizimler en büyük ölçekle sığsın.          */
function yerlestir(cizimler: Cizim[], en: number, boy: number): Yer[] {
  const kesit = cizimler.filter((c) => KESITLER.has(c.ad)).map((c) => ({ c, ...boyut(c.svg) }));
  const plan = cizimler.filter((c) => !KESITLER.has(c.ad)).map((c) => ({ c, ...boyut(c.svg) }));
  const dene = (H: number) => {
    const yerler: Yer[] = [];
    let x = 0;
    for (const k of kesit) {
      yerler.push({ ...k, x, y: 0 });
      x += k.w + ARALIK;
    }
    let y = 0;
    let sw = 0;
    for (const p of plan) {
      if (y > 0 && y + p.h > H) {
        x += sw + ARALIK;
        y = 0;
        sw = 0;
      }
      yerler.push({ ...p, x, y });
      y += p.h + ARALIK;
      sw = Math.max(sw, p.w);
    }
    const bw = Math.max(...yerler.map((q) => q.x + q.w));
    const bh = Math.max(...yerler.map((q) => q.y + q.h));
    return { yerler, k: Math.min(en / bw, boy / bh) };
  };
  const enAz = Math.max(600, ...kesit.map((k) => k.h), ...plan.map((p) => p.h));
  const toplam = plan.reduce((t, p) => t + p.h + ARALIK, 0);
  let en_iyi = dene(enAz);
  for (let H = enAz; H <= Math.max(enAz, toplam); H += 60) {
    const d = dene(H);
    if (d.k > en_iyi.k * 1.001) en_iyi = d;
  }
  return en_iyi.yerler;
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
  sorunluParcalar = [],
  sorunOdak = null,
  children,
}: {
  /**  Sorunlu parçalar ( data-ad ) — kırmızı işaretlenir  */
  sorunluParcalar?: string[];
  /**  Kartta seçilen sorun:  parçaları öne çıkar, tuval onun çizimine gider
       ( n her seçimde artar — aynı soruna yeniden tıklamak da götürür )  */
  sorunOdak?: { sorun: CizimSorunu; n: number } | null;
  /**  İlk açılışta yakınlaşılacak çizim ( adres:  ?cizim=kuyu_plani )  */
  odak?: string | null;
  cizimler: Cizim[];
  /**  sorunlu:  çizim güncel ama kuralları sağlamıyor ( sorunlar kartta )  */
  durum: "guncel" | "yukleniyor" | "eski" | "sorunlu";
  secili: OlcuSecimi | null;
  olcuSec: (o: OlcuSecimi | null, kutu?: DOMRect) => void;
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
  const [sigdirilan, setSigdirilan] = useState<string>("tumu");
  //  Tuvalin ölçüsü ( ResizeObserver ).  Yerleşim İLK ölçüyle kurulur:  pencere
  //  değişince çizimler yer değiştirmez, yalnız yakınlık oranı güncellenir.
  const [boyut, setBoyut] = useState<{ en: number; boy: number } | null>(null);
  const [ilkBoyut, setIlkBoyut] = useState<{ en: number; boy: number } | null>(null);
  useLayoutEffect(() => {
    const el = kap.current;
    if (!el) return;
    const olc = () => {
      const b = { en: el.clientWidth, boy: el.clientHeight };
      if (!b.en || !b.boy) return;
      setBoyut(b);
      setIlkBoyut((o) => o ?? b);
    };
    const ro = new ResizeObserver(olc);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  const yerler = useMemo(
    () => (ilkBoyut ? yerlestir(cizimler, ilkBoyut.en - 64, ilkBoyut.boy - 104) : []),
    [cizimler, ilkBoyut],
  );
  const katmanlar = useMemo(() => {
    const s = new Set<string>();
    for (const c of cizimler) for (const m of c.svg.matchAll(/data-katman="([^"]+)"/g)) s.add(m[1]);
    return [...s].sort();
  }, [cizimler]);

  const sigdir = useCallback(
    (hedef: string) => {
      const el = kap.current;
      if (!el || !yerler.length) return;
      const secilen = hedef === "tumu" ? yerler : yerler.filter((y) => y.c.ad === hedef);
      const x0 = Math.min(...secilen.map((y) => y.x));
      const y0 = Math.min(...secilen.map((y) => y.y));
      const x1 = Math.max(...secilen.map((y) => y.x + y.w));
      const y1 = Math.max(...secilen.map((y) => y.y + y.h));
      const W = el.clientWidth;
      const Hh = el.clientHeight;
      const ust = 64;
      const k = Math.min((W - 64) / (x1 - x0), (Hh - ust - 40) / (y1 - y0));
      setG({ k, x: (W - (x1 - x0) * k) / 2 - x0 * k, y: ust + (Hh - ust - 40 - (y1 - y0) * k) / 2 - y0 * k });
      setSigdirilan(hedef);
    },
    [yerler],
  );

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
      const Hh = el.clientHeight;
      const ust = 64;
      const k = Math.min(5, (W - 64) / (a1 - a0), (Hh - ust - 40) / (b1 - b0));
      const cizimin = Math.min((W - 64) / yer.w, (Hh - ust - 40) / yer.h);
      if (k <= cizimin) return sigdir(hedef);
      setG({ k, x: (W - (a1 - a0) * k) / 2 - a0 * k, y: ust + (Hh - ust - 40 - (b1 - b0) * k) / 2 - b0 * k });
    },
    [yerler, sigdir],
  );

  //  İlk çizim gelince sığdır;  sonraki yanıtlarda görünüm yerinde kalır
  const ilk = useRef(true);
  useLayoutEffect(() => {
    if (ilk.current && yerler.length) {
      ilk.current = false;
      sigdir(odak && yerler.some((y) => y.c.ad === odak) ? odak : "tumu");
    }
  }, [yerler, sigdir, odak]);

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
      const p = parcaBul(e.clientX, e.clientY, kap.current);
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
    const o = hedef.closest(".olcu") as SVGGElement | null;
    if (!o) {
      //  Boşluğa tıklamak kutuyu kapatır;  kaydırma bırakılışı kapatmaz
      if (!kaydi.current) olcuSec(null);
      return;
    }
    olcuyuSec(o);
  };

  //  Seçili ölçünün vurgusu ve kutunun yeri ( tuvale göre )
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
  }, [secili, g, cizimler]);

  //  Sorunlu parçalar ( sunucu:  cizim/sorun.py ) kırmızı;  seçilen sorununki öne çıkar
  useLayoutEffect(() => {
    const el = kap.current;
    if (!el) return;
    el.querySelectorAll(".parca-sorunlu, .parca-sorun-secili").forEach((x) =>
      x.classList.remove("parca-sorunlu", "parca-sorun-secili"),
    );
    for (const ad of sorunluParcalar) el.querySelectorAll(adSecici(ad)).forEach((x) => x.classList.add("parca-sorunlu"));
    for (const ad of sorunOdak?.sorun.parcalar ?? [])
      el.querySelectorAll(adSecici(ad)).forEach((x) => x.classList.add("parca-sorun-secili"));
  }, [sorunluParcalar, sorunOdak, cizimler]);

  //  Seçilen sorunun yerine git:  sunucunun söylediği çizim ( parçası oradaysa ),
  //  yoksa parçanın göründüğü ilk çizim;  o çizimdeki parçaların kutusuna
  //  yakınlaşılır ( bütün kesit sığınca tepedeki parça okunmuyordu ).  Her
  //  seçim bir kez götürür.
  const gidilenSorun = useRef(0);
  useLayoutEffect(() => {
    const el = kap.current;
    if (!el || !sorunOdak || sorunOdak.n === gidilenSorun.current) return;
    const { cizim, parcalar } = sorunOdak.sorun;
    const ogeler = (ad: string) =>
      parcalar.flatMap((p) => [...el.querySelectorAll(`[data-cizim="${ad}"] ${adSecici(p)}`)]);
    const hedef = cizim && ogeler(cizim).length ? cizim : yerler.find((y) => ogeler(y.c.ad).length)?.c.ad;
    const yer = yerler.find((y) => y.c.ad === hedef);
    const fig = el.querySelector(`figure[data-cizim="${hedef}"]`);
    if (!hedef || !yer || !fig) return;
    gidilenSorun.current = sorunOdak.n;
    setSigdirilan(hedef);
    //  Ekrandaki kutular levhaya:  figürün içindeki oranı × figürün levhadaki boyu
    const f = fig.getBoundingClientRect();
    //  Boyutsuz öğe ( gizli, boş ) ( 0, 0 ) noktasında döner:  kutuyu ekranın köşesine uzatırdı
    const kutular = ogeler(hedef)
      .map((o) => o.getBoundingClientRect())
      .filter((r) => r.width > 0 || r.height > 0);
    if (!f.width || !f.height || !kutular.length) return sigdir(hedef);
    const lx = (x: number) => yer.x + ((x - f.left) / f.width) * yer.w;
    const ly = (y: number) => yer.y + ((y - f.top) / f.height) * yer.h;
    kutuyaGit(
      hedef,
      lx(Math.min(...kutular.map((r) => r.left))),
      ly(Math.min(...kutular.map((r) => r.top))),
      lx(Math.max(...kutular.map((r) => r.right))),
      ly(Math.max(...kutular.map((r) => r.bottom))),
    );
  }, [sorunOdak, yerler, sigdir, kutuyaGit]);

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

  //  Yakınlık yüzdesi "hepsi sığdı" görünümüne göre
  const sigdirmaOrani = useMemo(() => {
    if (!boyut || !yerler.length) return 1;
    const x1 = Math.max(...yerler.map((y) => y.x + y.w));
    const y1 = Math.max(...yerler.map((y) => y.y + y.h));
    return Math.min((boyut.en - 64) / x1, (boyut.boy - 104) / y1);
  }, [yerler, boyut]);

  const uzak = 2.5 * g.k * dpr < 5;
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
      style={{ cursor: surukluyor ? "grabbing" : "default" }}
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
            className="tuval-svg absolute m-0"
            style={{
              left: y.x * kNet,
              top: y.y * kNet,
              width: y.w * kNet,
              height: y.h * kNet,
              ["--mu" as string]: (g.k / (y.c.olcek || 20)).toPrecision(6),
            }}
            dangerouslySetInnerHTML={{ __html: y.c.svg }}
          />
        ))}
      </div>

      {/*  Çizim adları — uzak görünümde, ekran pikselinde ( yakında çizimin kendi anteti okunur )  */}
      {uzak && yerler.map((y) => (
        <div
          key={y.c.ad}
          className="pointer-events-none absolute flex items-baseline gap-2 truncate text-[11.5px] font-medium tracking-wide text-tuval-metin-2"
          style={{ left: g.x + y.x * g.k, top: g.y + y.y * g.k - 22, maxWidth: Math.max(80, (y.w + ARALIK * 0.6) * g.k) }}
        >
          <span className="truncate">{kisaAd(y.c.baslik)}</span>
          {!y.c.olceksiz && <span className="sayi shrink-0 text-tuval-metin-2/70">1:{y.c.olcek}</span>}
        </div>
      ))}

      {/*  Araç şeridi  */}
      <div
        data-tuval-arac
        className="absolute top-3 left-3 flex items-center gap-1 rounded-buyuk border border-white/[0.08] bg-tuval-2/95 p-1 shadow-tuval backdrop-blur"
      >
        <Secim
          etiket="Görünüm"
          deger={sigdirilan}
          degisti={sigdir}
          className="h-7 w-48 border-transparent bg-transparent text-tuval-metin hover:border-white/10 focus:border-white/20 focus:ring-0 [&_svg]:text-tuval-metin-2"
          secenekler={[
            { deger: "tumu", ad: "Bütün çizimler" },
            ...yerler.map((y) => ({ deger: y.c.ad, ad: kisaAd(y.c.baslik) })),
          ]}
        />
        <span className="mx-0.5 h-4 w-px bg-white/10" />
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
          <Dugme tur="tuval" boy="simge-kucuk" aria-label="Sığdır" onClick={() => sigdir(sigdirilan)}>
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
      </div>

      {/*  Çizimin durumu:  güncel mi, yolda mı, eski mi, uygun değil mi  */}
      <div data-tuval-arac className="absolute top-3 right-3">
        {durum === "yukleniyor" ? (
          <DurumHapi>
            <Loader2 className="size-3 animate-spin" /> Çiziliyor
          </DurumHapi>
        ) : durum === "eski" ? (
          <DurumHapi uyari>Çizim güncel değil</DurumHapi>
        ) : durum === "sorunlu" ? (
          <DurumHapi tehlike>
            <span className="size-1.5 rounded-full bg-[#f97066]" /> Uygun değil
          </DurumHapi>
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

      <p className="pointer-events-none absolute bottom-3 left-3 text-[11.5px] text-tuval-metin-2/80">
        Tekerlek yakınlaştırır · sürükleyin · ölçüye tıklayın:  kaynağı ve değiştirme
      </p>

      {children?.(konum)}
    </div>
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

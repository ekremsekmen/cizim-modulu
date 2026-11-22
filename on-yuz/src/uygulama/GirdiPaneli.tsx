/*  GİRDİ PANELİ — formun tamamı şemadan ( /api/uygulama/alanlar ).
    22 Kas:  BÖLÜM BÖLÜM.  Eskiden 11 grup alt alta açılır-kapanır listeydi;  birkaç grup
    açılınca başlıklar kaydırmada kayboluyor, "nerdeyim" sorusunun cevabı yoktu.  Şimdi
    solda hep görünen BÖLÜM ŞERİDİ ( her bölümün durumu:  kırmızı = o bölümün girdilerine
    bağlı uygun olmayan hesap, mavi nokta = girilen alan ) ve sağında YALNIZ SEÇİLİ BÖLÜM:
    başlığı ( "3 / 11" ) sabit, Temel / Gelişmiş ayrı sekme, dipte önceki / sonraki.
    Çizim ve uygunluk hep görünür kalır — girdiler pencereye ( modal ) taşınmadı, çünkü
    her yazışta tuvalin ve hükmün değiştiğini görmek programın asıl geri bildirimi.
    Yazılmamış alan sunucunun kullandığı değeri SOLUK gösterir:  hesap onunla yapıldı,
    ama siz girmediniz.  */
import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowDownToLine,
  ArrowUpDown,
  Building,
  Cable,
  ChevronLeft,
  ChevronRight,
  CircleAlert,
  CircleQuestionMark,
  Cog,
  Columns2,
  DoorOpen,
  Gauge,
  RotateCcw,
  Search,
  Undo2,
  Warehouse,
  Weight,
  X,
  Zap,
  type LucideIcon,
} from "lucide-react";
import type { Alan, AlanSemasi, Deger } from "@/lib/api";
import { agirligaGoreGizli, alanHatasi, alanOku, gizliAlanlar, kipGizlileri, kuyununOrtaklari, mrlMi, sayiOku, secenekKapali, type Ham, type UygulamaProjesi } from "@/lib/proje";
import { DURAK_ADLARI, DURAK_KOTLARI, GIRIS_DURAGI, KUYU_DIBI_KOTU, KUYU_TAVANI_KOTU, MD_ZEMINI_KOTU, kotYaz, kotlariOku } from "@/lib/kotlar";
import { KatGirisi } from "./KotTablosu";
import { cn, etiketBol, sayiYaz } from "@/lib/utils";
import { Anahtar, Bolumlu, Dugme, Girdi, Ipucu, Secim } from "@/components/ui";

const KAYNAK_YAZISI: Record<string, string> = { KURAL: "kuraldan", ÇİZİM: "çizimden", KATALOG: "katalog" };

/**  Bölüm şeridindeki kısa ad ve simge;  bilinmeyen grup ( şemaya yeni eklenen ) adının
     ilk sözcüğüyle ve genel simgeyle görünür — şerit şemadan kurulur, burası yalnız süs  */
const BOLUM_GORUNUMU: Record<string, { kisa: string; simge: LucideIcon }> = {
  "Asansör ve düzen": { kisa: "Asansör", simge: ArrowUpDown },
  "Kuyu ve katlar": { kisa: "Kuyu, kat", simge: Building },
  "Kabin ve kapı": { kisa: "Kabin, kapı", simge: DoorOpen },
  "Raylar ve patenler": { kisa: "Raylar", simge: Columns2 },
  "Karşı ağırlık": { kisa: "Ağırlık", simge: Weight },
  "Askı ve halatlar": { kisa: "Halatlar", simge: Cable },
  Makine: { kisa: "Makine", simge: Cog },
  "Makine dairesi": { kisa: "Makine dairesi", simge: Warehouse },
  Tamponlar: { kisa: "Tampon", simge: ArrowDownToLine },
  "Hız regülatörü": { kisa: "Regülatör", simge: Gauge },
  "Elektrik ve topraklama": { kisa: "Elektrik", simge: Zap },
};
const gorunumu = (ad: string) => BOLUM_GORUNUMU[ad] ?? { kisa: ad.split(" ")[0], simge: Cog };

export function GirdiPaneli({
  sema,
  proje,
  asansor,
  yaz,
  bolum,
  bolumSec,
  odak,
  vurgulu,
  vurguluAlanlar = [],
  grupHatasi,
  kullanilan,
  katlarAcik = false,
  katlarDegisti,
}: {
  /**  KAT TABLOSU ÇEKMECESİ ( Ö3 · K5 ):  tablo panelin yerinde açılan sütunda ( açıkken
       panel gizli ) — panelde özet ve "Kotları düzenle";  açıkken tuval düşey kesitte  */
  katlarAcik?: boolean;
  katlarDegisti?: (a: boolean) => void;
  vurguluAlanlar?: string[];
  sema: AlanSemasi;
  proje: UygulamaProjesi;
  asansor: number;
  yaz: (anahtar: string, deger: string) => void;
  /**  Seçili bölüm ( grup adı ) — panel yalnız onu gösterir  */
  bolum: string;
  bolumSec: (g: string) => void;
  /**  Bir alana götür ( kural maddesi ):  bölümü ve sekmesi açılır, kutu odak alır  */
  odak?: { anahtar: string; n: number } | null;
  vurgulu: string[];
  grupHatasi: Record<string, number>;
  /**  Sunucunun hesapta kullandığı değerler ( yanıtın "girdi" alanı ).  */
  kullanilan: Record<string, Deger> | undefined;
}) {
  const [ara, setAra] = useState("");
  //  Bölüm başına seçili sekme ( Temel / Gelişmiş ) — bölümden çıkıp dönünce aynı yer
  //  ( seçimin yapıldığı andaki hedef de saklanır:  yeni hedef gelince sekme ona uyar )
  const [sekmeler, setSekmeler] = useState<Record<string, { kip: "temel" | "gelismis"; hedef: string }>>({});
  //  Son yazılan alan:  başka bölüme geçilince başlıkta "Son değişiklik" olarak görünür
  //  ( asansörüyle:  öbür asansöre geçince o asansörün değişikliği değildir — bina alanı hariç )
  const [son, setSon] = useState<{ anahtar: string; grup: string; asansor: number } | null>(null);
  const govde = useRef<HTMLDivElement>(null);
  const oku = (a: string) => alanOku(proje, sema, asansor, a);

  //  Makine yerleşimine göre hesaba girmeyen alanlar gizlenir ( sunucu da okumaz );
  //  kat girişinin öbür kipininkiler de ( asansör başına ).  Kot kutuları, durak adları
  //  ve giriş katı düz kutu olarak çizilmez:  kot tablosundadır ( KatGirisi ).
  const mrl = mrlMi(sema, proje);
  const kuyunun = kuyununOrtaklari(sema, proje);
  const h = proje.asansorler[asansor];
  const gizli = useMemo(
    () =>
      new Set([
        ...gizliAlanlar(sema, proje),
        ...kipGizlileri(sema, h),
        ...[DURAK_KOTLARI, KUYU_DIBI_KOTU, KUYU_TAVANI_KOTU, MD_ZEMINI_KOTU, DURAK_ADLARI, GIRIS_DURAGI],
        ...agirligaGoreGizli(sema, h, kullanilan),
      ]),
    [sema, proje, h, kullanilan],
  );
  //  Kot tablosu kipi belirleyen alanın grubunda ( "Kuyu ve katlar" )
  const katGrubu = sema.gruplar.find((g) => g.alanlar.some((a) => a.anahtar === sema.kot_kipi.alan))?.ad;
  //  Alanın etkin sayısı:  yazılmış, yoksa sunucunun kullandığı, yoksa şemanın varsayılanı
  const etkin = (anahtar: string): number | undefined => {
    const y = oku(anahtar);
    const n = y === undefined ? null : sayiOku(y);
    if (n !== null) return n;
    const k = kullanilan?.[anahtar];
    if (typeof k === "number") return k;
    const v = sema.gruplar.flatMap((g) => g.alanlar).find((a) => a.anahtar === anahtar)?.varsayilan;
    return typeof v === "number" ? v : undefined;
  };

  const aranan = ara.trim().toLocaleLowerCase("tr-TR");

  //  Şeritteki bölümler:  görünür alanlarıyla ( gizliler dışı );  bütün alanı gizli kalan
  //  bölüm ( MRL'de makine dairesi — kat grubu hariç:  kot tablosu orada ) şeritte yok
  const gruplar = useMemo(
    () =>
      sema.gruplar
        .map((g) => ({ ...g, alanlar: g.alanlar.filter((a) => !gizli.has(a.anahtar)) }))
        .filter((g) => g.alanlar.length > 0 || g.ad === katGrubu),
    [sema, gizli, katGrubu],
  );
  //  Aramada:  yalnız eşleşen alanlar, bölüm bölüm
  const bulunan = useMemo(
    () =>
      aranan
        ? gruplar
            .map((g) => ({ ...g, alanlar: g.alanlar.filter((a) => a.etiket.toLocaleLowerCase("tr-TR").includes(aranan)) }))
            .filter((g) => g.alanlar.length > 0)
        : [],
    [gruplar, aranan],
  );
  //  Adresteki bölüm yoksa ( eski bağlantı, MRL'de makine dairesi ) ilk bölüm — sıra da onun:
  //  -1 kalınca başlık "0 / 10" yazıyor, önceki / sonraki ikisi de kapanıyordu ( 22 Kas )
  const sira = Math.max(0, gruplar.findIndex((g) => g.ad === bolum));
  const secili = gruplar[sira];
  const girildiSay = (g: { alanlar: Alan[] }) => g.alanlar.filter((a) => oku(a.anahtar) !== undefined).length;

  //  Yazılanı kaydet:  "Son değişiklik" bağı için
  const yazVeAnimsa = (anahtar: string, deger: string) => {
    const g = sema.gruplar.find((x) => x.alanlar.some((a) => a.anahtar === anahtar))?.ad;
    if (g) setSon({ anahtar, grup: g, asansor });
    yaz(anahtar, deger);
  };

  //  Vurgulanan ( ölçünün kaynağı ) ya da götürülen alan Gelişmiş'teyse sekme oraya
  const hedefler = useMemo(() => [...vurguluAlanlar, ...(odak ? [odak.anahtar] : [])], [vurguluAlanlar, odak]);
  const hedefKimligi = `${vurguluAlanlar.join(",")}|${odak ? `${odak.anahtar}#${odak.n}` : ""}`;
  const sekme = (g: { ad: string; alanlar: Alan[] }): "temel" | "gelismis" => {
    const temelVar = g.alanlar.some((a) => !a.gelismis);
    if (!temelVar) return "gelismis";
    if (!g.alanlar.some((a) => a.gelismis)) return "temel";
    const secim = sekmeler[g.ad];
    if (secim?.hedef === hedefKimligi) return secim.kip;
    if (g.alanlar.some((a) => a.gelismis && hedefler.includes(a.anahtar))) return "gelismis";
    return secim?.kip ?? "temel";
  };

  //  Ölçünün kaynağı gelince ilk alan görünür olsun;  götürülen alan odak alır
  useEffect(() => {
    if (!vurguluAlanlar.length) return;
    const t = setTimeout(
      () => document.getElementById(`alan-${vurguluAlanlar[0]}`)?.closest("[data-alan]")?.scrollIntoView({ block: "center", behavior: "smooth" }),
      60,
    );
    return () => clearTimeout(t);
  }, [vurguluAlanlar]);
  useEffect(() => {
    if (!odak) return;
    const t = setTimeout(() => {
      const k = document.getElementById(`alan-${odak.anahtar}`);
      k?.closest("[data-alan]")?.scrollIntoView({ block: "center" });
      k?.focus();
    }, 60);
    return () => clearTimeout(t);
  }, [odak]);
  //  Bölüm değişince gövde başa döner ( eski bölümün kaydırması yeni bölümde yanıltır )
  useEffect(() => {
    govde.current?.scrollTo({ top: 0 });
  }, [secili?.ad]);

  const katTablosu = (
    <KatGirisi
      h={h ?? {}}
      kullanilan={kullanilan}
      daireli={!mrl}
      doseme={etkin("tavan_dosemesi") ?? etkin("kuyu_duvar_kalinligi") ?? 0}
      etkin={etkin}
      yaz={yazVeAnimsa}
    />
  );
  //  ÇEKMECE AÇIKKEN PANEL GİZLİ, çekmece onun yerinde ( 6 Kas — kullanıcının seçimi ):
  //  ikisi yan yana tuvali 1280 px ekranda 88, 1440'ta 248 px'e indiriyordu;  Uygunluk
  //  paneli kot değişirken hesabın sonucunu göstermek için görünür kalır.  Panel
  //  yerinde kalır ( seçili bölüm, arama ):  yalnız gizlenir.  Odak çekmeceye geçer,
  //  kapanınca — odak kaybolduysa ( kapat düğmesi gitti ) — özetin düğmesine döner;  başka
  //  bir eylem kapattıysa ( "İlgili girdiler", kural maddesi ) odak onundur.
  const cekmeceAcik = katlarAcik && !!katlarDegisti;
  const oncekiCekmece = useRef(cekmeceAcik);
  useEffect(() => {
    if (oncekiCekmece.current === cekmeceAcik) return;
    oncekiCekmece.current = cekmeceAcik;
    const odaksiz = !document.activeElement || document.activeElement === document.body;
    if (cekmeceAcik) document.getElementById("kat-tablosu")?.focus();
    else if (odaksiz) document.getElementById("kat-ozeti-dugmesi")?.focus();
  }, [cekmeceAcik]);

  const sec = (g: string) => {
    setAra("");
    bolumSec(g);
  };
  //  Şeritte ↑ / ↓ bölümler arasında gezer ( odak da gider )
  const seritTusu = (e: React.KeyboardEvent) => {
    if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
    e.preventDefault();
    const i = Math.max(0, Math.min(gruplar.length - 1, sira + (e.key === "ArrowDown" ? 1 : -1)));
    sec(gruplar[i].ad);
    requestAnimationFrame(() => document.querySelector<HTMLElement>(`[data-bolum="${CSS.escape(gruplar[i].ad)}"]`)?.focus());
  };

  const alanlariCiz = (g: { ad: string; alanlar: Alan[] }, kip: "temel" | "gelismis" | "hepsi") => (
    <GrupAlanlari
      ust={
        g.ad === katGrubu && !aranan ? (
          katlarDegisti ? <KatOzeti h={h ?? {}} acik={katlarAcik} ac={() => katlarDegisti(!katlarAcik)} /> : katTablosu
        ) : null
      }
      vurguluAlanlar={hedefler}
      alanlar={kip === "hepsi" ? g.alanlar : g.alanlar.filter((a) => (kip === "gelismis") === !!a.gelismis)}
      sema={sema}
      oku={oku}
      yaz={yazVeAnimsa}
      kullanilan={kullanilan}
      mrl={mrl}
      kuyunun={kuyunun}
    />
  );

  const onceki = sira > 0 ? gruplar[sira - 1] : null;
  const sonraki = sira >= 0 && sira < gruplar.length - 1 ? gruplar[sira + 1] : null;
  const sonEtiket = son ? etiketBol(sema.gruplar.flatMap((g) => g.alanlar).find((a) => a.anahtar === son.anahtar)?.etiket ?? "")[0] : "";

  return (
    <>
    <aside aria-label="Girdiler" className={cn("flex w-[380px] shrink-0 border-r border-cizgi bg-yuzey", cekmeceAcik && "hidden")}>
      {/*  BÖLÜM ŞERİDİ — hep görünür:  nerede olduğunuz ve hangi bölümde sorun olduğu  */}
      <nav
        aria-label="Girdi bölümleri"
        onKeyDown={seritTusu}
        className="flex w-[76px] shrink-0 flex-col gap-0.5 overflow-y-auto border-r border-cizgi bg-yuzey-2 px-1.5 py-2"
      >
        {gruplar.map((g, i) => {
          const { kisa, simge: Simge } = gorunumu(g.ad);
          const hata = grupHatasi[g.ad] ?? 0;
          const girildi = girildiSay(g);
          const etkinMi = !aranan && g.ad === secili?.ad;
          const ilgili = vurgulu.includes(g.ad) || hedefler.some((a) => g.alanlar.some((x) => x.anahtar === a));
          //  Aramada eşleşmesi olmayan bölüm soluk
          const sonucsuz = !!aranan && !bulunan.some((b) => b.ad === g.ad);
          return (
            <button
              key={g.ad}
              type="button"
              data-bolum={g.ad}
              tabIndex={etkinMi || (aranan && i === 0) ? 0 : -1}
              aria-current={etkinMi ? "step" : undefined}
              aria-label={`${g.ad}${hata ? ` — ${hata} bölüm uygun değil` : ""}${girildi ? ` — ${girildi} alan girildi` : ""}`}
              title={g.ad}
              onClick={() => sec(g.ad)}
              className={cn(
                "relative flex flex-col items-center gap-1 rounded-orta px-1 pt-2 pb-1.5 text-center text-metin-2 transition-colors outline-none hover:bg-black/[0.05] hover:text-metin focus-visible:ring-2 focus-visible:ring-vurgu",
                etkinMi && "bg-yuzey text-vurgu-koyu shadow-panel ring-1 ring-cizgi hover:bg-yuzey hover:text-vurgu-koyu",
                ilgili && !etkinMi && "bg-vurgu-acik/70 ring-1 ring-vurgu-cizgi",
                sonucsuz && "opacity-40",
              )}
            >
              {etkinMi && <span aria-hidden className="absolute top-2 bottom-2 -left-1.5 w-[3px] rounded-r bg-vurgu" />}
              <Simge aria-hidden className="size-[18px]" strokeWidth={1.75} />
              <span aria-hidden className="line-clamp-2 text-[10.5px] leading-[1.15] font-medium">{kisa}</span>
              {hata > 0 ? (
                <span aria-hidden className="absolute top-1 right-1 inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-red px-1 text-[10px] font-semibold text-white">
                  {hata}
                </span>
              ) : (
                girildi > 0 && <span aria-hidden className="absolute top-1.5 right-1.5 size-1.5 rounded-full bg-vurgu" />
              )}
            </button>
          );
        })}
      </nav>

      <div className="flex min-w-0 flex-1 flex-col">
        <div className="space-y-2.5 border-b border-cizgi px-3 pt-3 pb-3">
          <label className="flex h-8 items-center gap-2 rounded-kucuk border border-cizgi-2 bg-yuzey px-2.5 focus-within:border-vurgu focus-within:ring-3 focus-within:ring-vurgu/15">
            <Search className="size-3.5 text-metin-3" />
            <input
              value={ara}
              onChange={(e) => setAra(e.target.value)}
              placeholder="Bütün bölümlerde alan ara"
              aria-label="Alan ara"
              className="min-w-0 flex-1 bg-transparent text-[13px] outline-none placeholder:text-metin-3"
            />
            {ara && (
              <button type="button" aria-label="Aramayı temizle" onClick={() => setAra("")}>
                <X className="size-3.5 text-metin-3" />
              </button>
            )}
          </label>
          {aranan ? (
            <p className="px-0.5 text-[12px] text-metin-3">
              {bulunan.reduce((n, g) => n + g.alanlar.length, 0)} alan · {bulunan.length} bölümde
            </p>
          ) : (
            secili && (
              <div className="px-0.5">
                <div className="flex items-baseline justify-between gap-2">
                  <h2 className="truncate text-[14px] font-semibold">{secili.ad}</h2>
                  <span className="sayi shrink-0 text-[11.5px] text-metin-3">
                    {sira + 1} / {gruplar.length}
                  </span>
                </div>
                <p className="mt-0.5 flex flex-wrap items-center gap-x-2 text-[12px] text-metin-3">
                  <span>{girildiSay(secili) ? `${girildiSay(secili)} alan girildi` : "Hepsi varsayılan"}</span>
                  {(grupHatasi[secili.ad] ?? 0) > 0 && (
                    <span className="inline-flex items-center gap-1 font-medium text-red">
                      <CircleAlert aria-hidden className="size-3" />
                      {grupHatasi[secili.ad]} bölüm uygun değil
                    </span>
                  )}
                </p>
                {son && son.grup !== secili.ad && (son.asansor === asansor || sema.proje_geneli.includes(son.anahtar)) && (
                  <button
                    type="button"
                    onClick={() => sec(son.grup)}
                    className="mt-2 flex w-full items-center gap-1.5 rounded-kucuk bg-black/[0.035] px-2 py-1 text-left text-[11.5px] text-metin-2 hover:bg-black/[0.06] hover:text-metin"
                  >
                    <Undo2 aria-hidden className="size-3 shrink-0" />
                    <span className="truncate">
                      Son değişiklik:  <span className="font-medium">{sonEtiket}</span> · {son.grup}
                    </span>
                  </button>
                )}
                {sekmeDugmesi(secili)}
              </div>
            )
          )}
        </div>

        <div ref={govde} className="min-h-0 flex-1 overflow-y-auto px-2 py-2">
          {aranan ? (
            bulunan.length === 0 ? (
              <p className="px-2 py-6 text-center text-[12.5px] text-metin-3">Bu adla alan yok.</p>
            ) : (
              bulunan.map((g) => (
                <section key={g.ad} data-grup={g.ad} className="mb-2">
                  <button
                    type="button"
                    onClick={() => sec(g.ad)}
                    className="flex h-7 w-full items-center gap-1 px-1.5 text-left text-[11.5px] font-semibold tracking-wide text-metin-3 uppercase hover:text-metin"
                  >
                    {g.ad}
                    <ChevronRight aria-hidden className="size-3" />
                  </button>
                  {alanlariCiz(g, "hepsi")}
                </section>
              ))
            )
          ) : (
            secili && (
              <section data-grup={secili.ad} aria-label={secili.ad} className={cn("rounded-orta", vurgulu.includes(secili.ad) && "bg-vurgu-acik/40")}>
                {alanlariCiz(secili, sekme(secili))}
              </section>
            )
          )}
        </div>

        {!aranan && (
          <div className="flex shrink-0 items-center justify-between gap-2 border-t border-cizgi px-2 py-2">
            <Dugme tur="hayalet" boy="kucuk" disabled={!onceki} onClick={() => onceki && sec(onceki.ad)} className="max-w-[48%] min-w-0">
              <ChevronLeft />
              <span className="truncate">{onceki ? gorunumu(onceki.ad).kisa : "Önceki"}</span>
            </Dugme>
            <Dugme tur="hayalet" boy="kucuk" disabled={!sonraki} onClick={() => sonraki && sec(sonraki.ad)} className="max-w-[48%] min-w-0">
              <span className="truncate">{sonraki ? gorunumu(sonraki.ad).kisa : "Sonraki"}</span>
              <ChevronRight />
            </Dugme>
          </div>
        )}
      </div>
    </aside>
    {cekmeceAcik && katlarDegisti && (
      //  Akışta ( örtmez ):  panelin yerinde;  tuval daralır, düşey kesit görünür kalır
      <section
        id="kat-tablosu"
        tabIndex={-1}
        aria-label="Kat tablosu"
        className="flex w-[520px] shrink-0 flex-col border-r border-cizgi bg-yuzey outline-none"
      >
        <div className="flex items-start justify-between gap-3 border-b border-cizgi px-4 py-3">
          <div>
            <h2 className="text-[13px] font-semibold">Katlar ve kotlar</h2>
            <p className="mt-0.5 text-[12px] text-metin-3">
              Tuval düşey kesitte;  kapatınca Girdiler ve önceki çizim geri gelir.
            </p>
          </div>
          <Dugme tur="hayalet" boy="simge-kucuk" aria-label="Kat tablosunu kapat" onClick={() => katlarDegisti(false)}>
            <X />
          </Dugme>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto px-3 py-3">{katTablosu}</div>
      </section>
    )}
    </>
  );

  /**  Temel / Gelişmiş — ikisi de olan bölümde;  sayılar:  alan sayısı ve girilenler  */
  function sekmeDugmesi(g: { ad: string; alanlar: Alan[] }) {
    const temel = g.alanlar.filter((a) => !a.gelismis);
    const ileri = g.alanlar.filter((a) => a.gelismis);
    if (!temel.length || !ileri.length) return null;
    const ileriGirilen = ileri.filter((a) => oku(a.anahtar) !== undefined).length;
    return (
      <div className="mt-2.5">
        <Bolumlu
          etiket={`${g.ad} — alan türü`}
          deger={sekme(g)}
          degisti={(d) => setSekmeler((s) => ({ ...s, [g.ad]: { kip: d, hedef: hedefKimligi } }))}
          secenekler={[
            { deger: "temel", ad: <>Temel <span className="sayi text-metin-3">{temel.length}</span></> },
            {
              deger: "gelismis",
              ad: (
                <>
                  Gelişmiş <span className="sayi text-metin-3">{ileri.length}</span>
                  {ileriGirilen > 0 && <span aria-label={`${ileriGirilen} değişti`} className="size-1.5 rounded-full bg-vurgu" />}
                </>
              ),
            },
          ]}
        />
      </div>
    );
  }
}

/**  Paneldeki kat özeti:  durak sayısı, en alt ve en üst kot;  tablo çekmecede  */
function KatOzeti({ h, acik, ac }: { h: Ham; acik: boolean; ac: () => void }) {
  const k = kotlariOku(h[DURAK_KOTLARI] as string | undefined).filter((x): x is number => x !== null);
  return (
    <div className="mb-2 flex items-center gap-2 rounded-orta border border-cizgi bg-yuzey-2 px-3 py-2">
      <div className="min-w-0 flex-1 text-[12.5px]">
        <p className="font-medium">{k.length ? `${k.length} durak` : "Durak kotu yok"}</p>
        {k.length > 0 && (
          <p className="sayi text-[11.5px] text-metin-3">
            {kotYaz(k[0])} … {kotYaz(k[k.length - 1])}
          </p>
        )}
      </div>
      <Dugme id="kat-ozeti-dugmesi" boy="kucuk" aria-expanded={acik} onClick={ac}>
        {acik ? "Tabloyu kapat" : "Kotları düzenle"}
      </Dugme>
    </div>
  );
}

function GrupAlanlari({
  ust,
  vurguluAlanlar,
  alanlar,
  sema,
  oku,
  yaz,
  kullanilan,
  mrl,
  kuyunun,
}: {
  /**  Grubun başında ( kat girişi )  */
  ust?: React.ReactNode;
  alanlar: Alan[];
  sema: AlanSemasi;
  oku: (a: string) => string | undefined;
  yaz: (a: string, d: string) => void;
  kullanilan: Record<string, Deger> | undefined;
  mrl: boolean;
  /**  Tek kuyuda iki asansörde aynı olan alanlar  */
  kuyunun: Set<string>;
  vurguluAlanlar: string[];
}) {
  return (
    <div className="space-y-px pt-0.5 pb-2">
      {ust}
      {alanlar.map((a) => (
        <AlanSatiri
          key={a.anahtar}
          a={a}
          sema={sema}
          ham={oku(a.anahtar)}
          yaz={yaz}
          kullanilan={kullanilan?.[a.anahtar]}
          mrl={mrl}
          kuyunun={kuyunun.has(a.anahtar)}
          vurgulu={vurguluAlanlar.includes(a.anahtar)}
        />
      ))}
    </div>
  );
}

/**  Kutudaki değer listedeki yazımıyla:  tarayıcıda "1,6" saklı kalmış olabilir ( seçenek "1.6" )  */
function secimDegeri(secenekler: Deger[], d: string): string {
  const s = secenekler.find((x) => String(x) === d || (typeof x === "number" && sayiOku(d) === x));
  return s === undefined ? d : String(s);
}

/**  Dar kutuya sığan en uzun seçenek ( birimiyle, karakter )  */
const SECIM_SIGAR = 13;
function enUzunSecenek(a: Alan): number {
  const birim = a.birim && a.birim !== "—" ? a.birim.length + 1 : 0;
  return Math.max(0, ...(a.secenekler ?? []).map((s) => (a.secenek_metni?.[String(s)] ?? sayiYaz(s)).length + birim));
}

function AlanSatiri({
  a,
  sema,
  ham,
  yaz,
  kullanilan,
  mrl,
  kuyunun,
  vurgulu,
}: {
  vurgulu?: boolean;
  kuyunun: boolean;
  a: Alan;
  sema: AlanSemasi;
  ham: string | undefined;
  yaz: (a: string, d: string) => void;
  kullanilan: Deger | undefined;
  mrl: boolean;
}) {
  const [ad, ack] = etiketBol(a.etiket);
  const hata = alanHatasi(sema, a.anahtar, ham);
  const girildi = ham !== undefined;
  const geneli = sema.proje_geneli.includes(a.anahtar);
  const id = `alan-${a.anahtar}`;
  //  Kutuda görünen:  yazılan, yoksa sunucunun kullandığı, yoksa şemanın varsayılanı
  const etkin = kullanilan ?? a.varsayilan;
  const yer =
    etkin !== null && etkin !== undefined && etkin !== ""
      ? sayiYaz(etkin)
      : (KAYNAK_YAZISI[a.kaynak] ?? "");

  let kutu: React.ReactNode;
  if (a.anahtar === "mk_yok") {
    kutu = (
      <Bolumlu
        etiket="Makine dairesi"
        deger={mrl ? "yok" : "var"}
        degisti={(d) => yaz("mk_yok", d === "yok" ? "true" : "false")}
        secenekler={[
          { deger: "var", ad: "Var" },
          { deger: "yok", ad: "Yok ( MRL )" },
        ]}
      />
    );
  } else if (a.tur === "onay") {
    kutu = <Anahtar id={id} acik={(ham ?? String(etkin)) === "true"} degisti={(d) => yaz(a.anahtar, String(d))} etiket={ad} />;
  } else if (a.tur === "secim" && a.secenekler) {
    kutu = (
      <Secim
        id={id}
        etiket={ad}
        deger={secimDegeri(a.secenekler, ham ?? String(etkin ?? ""))}
        varsayilanMi={!girildi}
        birim={a.birim && a.birim !== "—" ? a.birim : undefined}
        degisti={(d) => yaz(a.anahtar, d)}
        secenekler={a.secenekler.map((s) => ({
          deger: String(s),
          ad: a.secenek_metni?.[String(s)] ?? sayiYaz(s),
          kapali: secenekKapali(a, s, mrl),
        }))}
      />
    );
  } else {
    kutu = (
      <Girdi
        id={id}
        value={ham ?? ""}
        placeholder={yer}
        birim={a.birim}
        inputMode={a.tur === "sayi" ? "decimal" : "text"}
        //  Birimli metin alanı sayı listesidir ( kat yükseklikleri:  100 durağa
        //  kadar — 120 karakterde ~21 durağı aşan binanın listesi sığmıyordu )
        maxLength={a.tur === "metin" ? (a.birim !== "—" ? 1000 : 120) : 32}
        yazi={a.tur === "metin"}
        durum={hata ? "hata" : undefined}
        aria-invalid={!!hata}
        aria-describedby={hata ? `${id}-hata` : undefined}
        onChange={(e) => yaz(a.anahtar, e.target.value)}
      />
    );
  }

  //  Uzun seçenekli seçim de geniş:  128 px kutuya ~13 karakter sığar ( "Altı Kesik V Kanal",
  //  "Poliüretan ( lineer olmayan )" kesiliyordu — 22 Kas ölçümü );  kutu etiketin altına iner
  const genis =
    a.anahtar === "mk_yok" ||
    a.tur === "metin" ||
    (a.tur === "secim" && !!a.secenekler && enUzunSecenek(a) > SECIM_SIGAR) ||
    //  Çok uzun ad ( "Dt/dh < 40 ya da …" ) dar sütunda 4–5 satır olurdu
    ad.length > 55;
  return (
    <div
      data-alan
      className={cn(
        "group/satir relative rounded-kucuk px-1.5 py-1 hover:bg-black/[0.02]",
        vurgulu && "bg-olcu/15 ring-1 ring-olcu/60 hover:bg-olcu/15",
      )}
    >
      <div className={cn("grid items-center gap-x-2", genis ? "grid-cols-1 gap-y-1" : "grid-cols-[1fr_128px]")}>
        <div className="flex min-w-0 items-center gap-1">
          {girildi && <span aria-label="girildi" className="size-1.5 shrink-0 rounded-full bg-vurgu" />}
          {/*  Uzun ad kesilmez, satırlara iner ( "Kabinin kuyu ortasından sa…" );  22 Kas:  sınır
               yok — rozetli satırda ( "bina" ) üç satır da yetmiyordu  */}
          <label htmlFor={id} className="min-w-0 text-[12.5px] leading-tight text-metin-2" title={a.etiket}>
            {a.anahtar === "mk_yok" ? "Makine dairesi" : ad}
          </label>
          {(a.bilgi || ack) && (
            <Ipucu
              yan="right"
              metin={
                <>
                  {ack && <span className="block font-medium">{ack}</span>}
                  {a.bilgi && <span className="mt-0.5 block text-white/80">{a.bilgi}</span>}
                </>
              }
            >
              <button type="button" aria-label={`${ad} — açıklama`} className="shrink-0 text-metin-3 hover:text-metin">
                <CircleQuestionMark className="size-3.5" />
              </button>
            </Ipucu>
          )}
          {geneli && (
            <Ipucu metin="Binaya ait — bütün asansörlerde aynı">
              <span className="shrink-0 rounded-[4px] bg-black/[0.05] px-1 text-[10.5px] font-medium text-metin-2">bina</span>
            </Ipucu>
          )}
          {kuyunun && (
            <Ipucu metin="Kuyuya ait — iki asansörde aynı">
              <span className="shrink-0 rounded-[4px] bg-black/[0.05] px-1 text-[10.5px] font-medium text-metin-2">kuyu</span>
            </Ipucu>
          )}
          {girildi && a.tur !== "onay" && a.anahtar !== "mk_yok" && (
            <Ipucu metin="Varsayılana dön">
              <button
                type="button"
                aria-label={`${ad} — varsayılana dön`}
                onClick={() => yaz(a.anahtar, "")}
                className="ml-auto shrink-0 text-metin-3 opacity-0 group-hover/satir:opacity-100 hover:text-metin focus:opacity-100"
              >
                <RotateCcw className="size-3" />
              </button>
            </Ipucu>
          )}
        </div>
        {kutu}
      </div>
      {hata && (
        <p id={`${id}-hata`} className="mt-1 text-right text-[11.5px] font-medium text-red">
          {hata}
        </p>
      )}
    </div>
  );
}

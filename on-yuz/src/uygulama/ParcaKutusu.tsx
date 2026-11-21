/*  PARÇA KUTUSU — çizimde bir parçaya tıklanınca ( Ö3 · K6 ).
    /api/uygulama/parca:  parçayı belirleyen girdiler ( izli kurulumun türevi ).
    Kutu formun kutularıdır:  yazılan değer soldaki alana gider, hesap ve çizim
    kendi akışıyla yenilenir.  Burada değişmeyenler ( ofis standardı, kotlar )
    soluk, nerede değiştikleri yazılı.  Listenin sınırı sunucunun cümlesi.      */
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Loader2, X } from "lucide-react";
import { api, type ParcaGirdisi, type UygulamaIstegi } from "@/lib/api";
import { kutuyaYaz } from "@/lib/denetim";
import { cn, etiketBol, sayiYaz } from "@/lib/utils";
import { Dugme, Girdi, Secim } from "@/components/ui";
import { sureYaz, useGecenSure, type IsDurumu } from "@/components/IsAsamalari";
import { KUTU_UST, kutuYeri, type OlcuKonumu, type Parca } from "./Tuval";

const YER: Record<string, string> = { asansor: "asansör", proje: "bina" };

/**  Değişmeyen girdinin değiştiği yer  */
function nerede(g: ParcaGirdisi) {
  if (g.durak !== undefined) return "kot tablosunda değişir";
  if (g.yer === "ofis") return "ofis standardında değişir";
  return YER[g.yer] ?? g.yer;
}

export function ParcaKutusu({
  istek,
  asansor,
  parca,
  konum,
  kapat,
  yaz,
  girdilerGeldi,
}: {
  /**  Ekrandaki çizimin girdisi  */
  istek: UygulamaIstegi;
  asansor: number;
  parca: Parca;
  konum: OlcuKonumu;
  kapat: () => void;
  /**  Formun kutusuna yazar ( soldaki alanla aynı yol )  */
  yaz: (anahtar: string, deger: string) => void;
  /**  Girdiler gelince:  solda gruplarını aç, alanları vurgula  */
  girdilerGeldi?: (anahtarlar: string[]) => void;
}) {
  //  "Seçimleri de bul":  seçim kutularının etkisi istenince ( sunucu her birini dener —
  //  2,3 – 3,2 sn;  çizim başına bir kez, sonra önbellekte ).  Seçildikten sonra kutu
  //  açık kaldıkça seçimli liste
  const [secimler, setSecimler] = useState(false);
  //  Seçim aramasında sunucunun denediği kutu ( akışlı yanıt — 20 Kas, arayüz taslağı B10:
  //  ekranda yalnız "birkaç saniye" yazıyordu )
  const [secimDurumu, setSecimDurumu] = useState<IsDurumu | null>(null);
  const sorgu = useQuery({
    queryKey: ["parca", istek, asansor, parca.cizim, parca.id, secimler],
    queryFn: async (q) => {
      if (!secimler) return api.parca(istek, asansor, parca.cizim, parca.id);
      //  Sinyal YALNIZ burada okunur ( okunan sinyal sorguyu iptal edilir kılar ):  kutu kapanınca,
      //  Vazgeç'te ya da girdi değişince arama bırakılır, sunucu bir sonraki kutuda durur
      const bas = performance.now();
      setSecimDurumu({ bas, d: null });
      try {
        return await api.parca(istek, asansor, parca.cizim, parca.id, true, q.signal, (d) =>
          setSecimDurumu((x) => (x?.bas === bas ? { bas, d } : x)),
        );
      } finally {
        setSecimDurumu((x) => (x?.bas === bas ? null : x));
      }
    },
    //  Değer yazılınca çizim yenilenir:  yeni yanıta kadar eski liste durur ( kutu sıçramasın )
    placeholderData: keepPreviousData,
  });
  const y = sorgu.data;
  const secimAraniyor = secimler && sorgu.isFetching;
  const secimGecen = useGecenSure(secimAraniyor ? secimDurumu : null);

  useEffect(() => {
    const k = (e: KeyboardEvent) => e.key === "Escape" && kapat();
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, [kapat]);
  useEffect(() => {
    if (y?.girdiler) girdilerGeldi?.(y.girdiler.filter((g) => g.degistirilir).map((g) => g.anahtar));
  }, [y]); // eslint-disable-line react-hooks/exhaustive-deps

  const kutu = useRef<HTMLDivElement>(null);
  const [boy, setBoy] = useState(360);
  useLayoutEffect(() => {
    const el = kutu.current;
    if (!el) return;
    const olc = () => setBoy(el.offsetHeight);
    olc();
    const ro = new ResizeObserver(olc);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  const { sol, ust, en } = kutuYeri(konum, 336, boy);
  const degisen = (y?.girdiler ?? []).filter((g) => g.degistirilir);
  const salt = (y?.girdiler ?? []).filter((g) => !g.degistirilir);

  return (
    <div
      ref={kutu}
      data-olcu-kutu
      role="dialog"
      aria-label={`Parça ${y?.ad ?? parca.adi}`}
      className="absolute z-30 flex flex-col overflow-hidden rounded-buyuk border border-cizgi bg-yuzey text-metin shadow-kalkik select-text"
      style={{ left: sol, top: ust, width: en, maxHeight: Math.max(160, konum.h - KUTU_UST - 12) }}
    >
      <div className="flex shrink-0 items-start justify-between gap-3 border-b border-cizgi px-4 py-3">
        <div className="min-w-0">
          <p className="text-[14px] font-semibold leading-snug">{y?.ad ?? parca.adi}</p>
          <p className="mt-0.5 text-[11.5px] text-metin-3">Parçayı belirleyen girdiler</p>
        </div>
        <Dugme tur="hayalet" boy="simge-kucuk" aria-label="Kapat" onClick={kapat}>
          <X />
        </Dugme>
      </div>

      {!y && sorgu.isFetching ? (
        <p className="flex items-center gap-2 px-4 py-4 text-[12.5px] text-metin-3">
          <Loader2 className="size-3.5 animate-spin" /> Girdileri bulunuyor
        </p>
      ) : !y && sorgu.error ? (
        <div className="space-y-2 px-4 py-3 text-[12.5px] text-red">
          <p>Sunucuya ulaşılamadı ( {sorgu.error.message} ) — parçanın girdileri bulunamadı.</p>
          <Dugme boy="kucuk" onClick={() => sorgu.refetch()}>
            Yeniden dene
          </Dugme>
        </div>
      ) : y && !y.aktif ? (
        //  Ret yanıtı da yeniden istenebilir ( geçici olabilir;  aynı parçaya yeniden
        //  tıklamak önbellekteki reddi gösterirdi )
        <div className="space-y-2 px-4 py-3 text-[12.5px] text-red">
          <p>{y.hata?.join(" ")}</p>
          <Dugme boy="kucuk" onClick={() => sorgu.refetch()} disabled={sorgu.isFetching}>
            Yeniden dene
          </Dugme>
        </div>
      ) : (
        <div className={cn("min-h-0 flex-1 overflow-y-auto pb-1", sorgu.isPlaceholderData && "opacity-60")}>
          {degisen.length > 0 && (
            <ul aria-label="Değiştirilebilen girdiler" className="space-y-px px-2 pt-2">
              {degisen.map((g) => (
                <Satir key={`${g.anahtar}:${g.deger}`} g={g} yaz={yaz} />
              ))}
            </ul>
          )}
          {salt.length > 0 && (
            <>
              <p className="mt-1.5 border-t border-cizgi px-4 pt-2 pb-1 text-[11px] font-medium tracking-wide text-metin-3 uppercase">
                Burada değişmeyenler
              </p>
              <ul aria-label="Burada değişmeyen girdiler" className="space-y-px px-2">
                {salt.map((g) => (
                  <Satir key={`${g.anahtar}:${g.durak ?? ""}:${g.deger}`} g={g} yaz={yaz} />
                ))}
              </ul>
            </>
          )}
          {y?.girdiler && !y.girdiler.length && (
            <p className="px-4 py-3 text-[12.5px] text-metin-3">Bu parçanın yeri ve ölçüsü girdilere bağlı değil.</p>
          )}
          {y?.not && <p className="px-4 pt-2 pb-1 text-[11.5px] leading-snug text-metin-3">{y.not}</p>}
          {!secimler && (
            <div className="px-4 pt-1 pb-2">
              <Dugme boy="kucuk" onClick={() => setSecimler(true)}>
                Seçimleri de bul
              </Dugme>
            </div>
          )}
          {secimAraniyor && (
            <SecimAramasi durum={secimDurumu} gecen={secimGecen} vazgec={() => setSecimler(false)} />
          )}
        </div>
      )}
    </div>
  );
}

/**  "Seçimleri de bul" sürerken:  sunucunun denediği kutu ve sırası ( "Askı oranı deneniyor · 4 / 42" —
     sunucunun ayrıntısı "etiket · n / toplam" ).  Sayı gerçek:  42 kutunun kaçıncısı;  yüzde çubuğu
     yok ( kısa iş ).  Vazgeç seçimsiz listeye döner  */
function SecimAramasi({ durum, gecen, vazgec }: { durum: IsDurumu | null; gecen: number; vazgec: () => void }) {
  const asamalar = durum?.d?.asamalar ?? [];
  const ayrinti = asamalar[asamalar.length - 1]?.ayrinti ?? "";
  const [, kutu, sira] = /^(.+) · (\d+ \/ \d+)$/.exec(ayrinti) ?? [];
  const sag = [sira, gecen >= 1000 ? sureYaz(gecen / 1000) : ""].filter(Boolean).join(" · ");
  return (
    <div role="status" aria-live="polite" data-secim-aramasi className="mx-4 mt-1 mb-2 border-t border-cizgi pt-2">
      <div className="flex items-center gap-2 text-[12.5px]">
        <Loader2 className="size-3.5 shrink-0 animate-spin text-metin-3" aria-label="sürüyor" />
        <span className="min-w-0 flex-1 truncate">
          {kutu ? (
            <>
              <b className="font-medium">{kutu}</b> deneniyor
            </>
          ) : (
            "Seçimler deneniyor"
          )}
        </span>
        {sag && <span className="sayi shrink-0 text-[11.5px] text-metin-3">{sag}</span>}
      </div>
      <div className="mt-1 flex items-start gap-3 text-[11.5px] leading-snug text-metin-3">
        <p className="min-w-0 flex-1">Her seçim kutusu bir komşu değerle denenir, çizim yeniden kurulur.</p>
        <button
          type="button"
          onClick={vazgec}
          className="shrink-0 rounded-kucuk border border-cizgi-2 px-2 py-0.5 font-medium text-metin hover:bg-black/[0.04]"
        >
          Vazgeç
        </button>
      </div>
    </div>
  );
}

function Satir({ g, yaz }: { g: ParcaGirdisi; yaz: (anahtar: string, deger: string) => void }) {
  const ad = etiketBol(g.etiket)[0];
  const ilk = typeof g.deger === "number" ? kutuyaYaz(g.deger) : String(g.deger);
  //  Sunucunun değeri değişince ( çizim yenilendi ) satır yeniden kurulur ( anahtarı değerle )
  const [yazi, setYazi] = useState(ilk);
  const id = `parca-${g.anahtar}${g.durak ?? ""}`;
  const birim = g.birim && g.birim !== "—" ? g.birim : undefined;
  return (
    <li className={cn("grid grid-cols-[minmax(0,1fr)_118px] items-center gap-2.5 rounded-orta px-2 py-1.5", !g.degistirilir && "opacity-75")}>
      <label htmlFor={g.degistirilir ? id : undefined} className="min-w-0">
        <span className="block text-[12.5px] leading-snug">{ad}</span>
        <span className="block text-[11px] text-metin-3">
          {nerede(g)}
          {g.etki === "boyut" ? " · ölçüsü" : " · yeri"}
        </span>
      </label>
      {!g.degistirilir ? (
        <span className="sayi flex h-8 items-center justify-end gap-1 rounded-kucuk border border-dashed border-cizgi-2 bg-yuzey-2 px-2.5 text-[12.5px] text-metin-2">
          {sayiYaz(g.deger)} {birim && <span className="text-[11.5px] text-metin-3">{birim}</span>}
        </span>
      ) : g.secenekler ? (
        <Secim
          id={id}
          etiket={ad}
          deger={String(g.deger)}
          degisti={(d) => yaz(g.anahtar, d)}
          secenekler={g.secenekler.map((x) => ({ deger: String(x), ad: String(x) }))}
          birim={birim}
        />
      ) : (
        <Girdi
          id={id}
          value={yazi}
          birim={birim}
          inputMode="decimal"
          onChange={(e) => setYazi(e.target.value)}
          onBlur={() => yazi !== ilk && yaz(g.anahtar, yazi)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && yazi !== ilk) yaz(g.anahtar, yazi);
          }}
        />
      )}
    </li>
  );
}

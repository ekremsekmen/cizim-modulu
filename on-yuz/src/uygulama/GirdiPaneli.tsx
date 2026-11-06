/*  GİRDİ PANELİ — formun tamamı şemadan ( /api/uygulama/alanlar ).
    Grup sırası tasarım sırasıdır;  başlıktaki kırmızı sayı, o grubun girdilerine
    bağlı kalan bölüm sayısıdır ( bolum_grubu ).  Yazılmamış alan sunucunun
    kullandığı değeri SOLUK gösterir:  hesap onunla yapıldı, ama siz girmediniz.  */
import { useEffect, useMemo, useState } from "react";
import { ChevronRight, CircleAlert, CircleQuestionMark, RotateCcw, Search, X } from "lucide-react";
import type { Alan, AlanSemasi, Deger } from "@/lib/api";
import { agirligaGoreGizli, alanHatasi, alanOku, gizliAlanlar, kipGizlileri, kuyununOrtaklari, mrlMi, varsayilanKotlarMi, sayiOku, secenekKapali, type Ham, type UygulamaProjesi } from "@/lib/proje";
import { DURAK_ADLARI, DURAK_KOTLARI, GIRIS_DURAGI, KUYU_DIBI_KOTU, KUYU_TAVANI_KOTU, MD_ZEMINI_KOTU, kotYaz, kotlariOku } from "@/lib/kotlar";
import { KatGirisi } from "./KotTablosu";
import { cn, etiketBol, sayiYaz } from "@/lib/utils";
import { Anahtar, Bolumlu, Dugme, Girdi, Ipucu, Rozet, Secim } from "@/components/ui";

const KAYNAK_YAZISI: Record<string, string> = { KURAL: "kuraldan", ÇİZİM: "çizimden", KATALOG: "katalog" };

export function GirdiPaneli({
  sema,
  proje,
  asansor,
  yaz,
  acik,
  setAcik,
  vurgulu,
  vurguluAlanlar = [],
  grupHatasi,
  kullanilan,
  katlarAcik = false,
  katlarDegisti,
}: {
  /**  KAT TABLOSU ÇEKMECESİ ( Ö3 · K5 ):  tablo panelin yanında açılan sütunda —
       panelde özet ve "Kotları düzenle";  açıkken tuval düşey kesitte  */
  katlarAcik?: boolean;
  katlarDegisti?: (a: boolean) => void;
  vurguluAlanlar?: string[];
  sema: AlanSemasi;
  proje: UygulamaProjesi;
  asansor: number;
  yaz: (anahtar: string, deger: string) => void;
  acik: Set<string>;
  setAcik: (s: Set<string>) => void;
  vurgulu: string[];
  grupHatasi: Record<string, number>;
  /**  Sunucunun hesapta kullandığı değerler ( yanıtın "girdi" alanı ).  */
  kullanilan: Record<string, Deger> | undefined;
}) {
  const [ara, setAra] = useState("");
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

  //  Programın varsayılan kot tablosu ( yeni proje ) girilmiş sayılmaz
  const varsayilanKot = varsayilanKotlarMi(sema, proje, asansor)
    ? [DURAK_KOTLARI, KUYU_DIBI_KOTU, KUYU_TAVANI_KOTU].filter((a) => a in (h ?? {})).length
    : 0;
  const girilen =
    Object.keys(proje.asansorler[asansor] ?? {}).length + Object.keys(proje.proje_geneli).length - varsayilanKot;
  const aranan = ara.trim().toLocaleLowerCase("tr-TR");

  const gruplar = useMemo(
    () =>
      sema.gruplar.map((g) => ({
        ...g,
        alanlar: g.alanlar.filter(
          (a) => !gizli.has(a.anahtar) && (!aranan || a.etiket.toLocaleLowerCase("tr-TR").includes(aranan)),
        ),
      })),
    [sema, gizli, aranan],
  );

  //  Ölçünün kaynağı gelince ilk alan görünür olsun
  useEffect(() => {
    if (!vurguluAlanlar.length) return;
    const t = setTimeout(
      () => document.getElementById(`alan-${vurguluAlanlar[0]}`)?.closest("[data-alan]")?.scrollIntoView({ block: "center", behavior: "smooth" }),
      60,
    );
    return () => clearTimeout(t);
  }, [vurguluAlanlar]);

  const ac = (ad: string) => {
    const y = new Set(acik);
    if (y.has(ad)) y.delete(ad);
    else y.add(ad);
    setAcik(y);
  };

  const katTablosu = (
    <KatGirisi
      h={h ?? {}}
      kullanilan={kullanilan}
      daireli={!mrl}
      doseme={etkin("tavan_dosemesi") ?? etkin("kuyu_duvar_kalinligi") ?? 0}
      etkin={etkin}
      yaz={yaz}
    />
  );
  return (
    <>
    <aside aria-label="Girdiler" className="flex w-[348px] shrink-0 flex-col border-r border-cizgi bg-yuzey">
      <div className="space-y-2.5 border-b border-cizgi px-3 pt-3 pb-3">
        <div className="flex items-baseline justify-between px-0.5">
          <h2 className="text-[13px] font-semibold">Girdiler</h2>
          <span className="text-[12px] text-metin-3">{girilen} alan girildi</span>
        </div>
        <label className="flex h-8 items-center gap-2 rounded-kucuk border border-cizgi-2 bg-yuzey px-2.5 focus-within:border-vurgu focus-within:ring-3 focus-within:ring-vurgu/15">
          <Search className="size-3.5 text-metin-3" />
          <input
            value={ara}
            onChange={(e) => setAra(e.target.value)}
            placeholder="Alan ara — gelişmiş alanlar da"
            aria-label="Alan ara"
            className="min-w-0 flex-1 bg-transparent text-[13px] outline-none placeholder:text-metin-3"
          />
          {ara && (
            <button type="button" aria-label="Aramayı temizle" onClick={() => setAra("")}>
              <X className="size-3.5 text-metin-3" />
            </button>
          )}
        </label>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-2 py-2">
        {gruplar.map((g) => {
          if (aranan && g.alanlar.length === 0) return null;
          const acikMi = acik.has(g.ad) || !!aranan;
          const hata = grupHatasi[g.ad] ?? 0;
          const girildi = g.alanlar.filter((a) => oku(a.anahtar) !== undefined).length;
          return (
            <section
              key={g.ad}
              data-grup={g.ad}
              className={cn(
                "mb-1 rounded-orta transition-colors",
                vurgulu.includes(g.ad) && "bg-vurgu-acik/60 ring-1 ring-vurgu-cizgi",
              )}
            >
              <button
                type="button"
                onClick={() => ac(g.ad)}
                aria-expanded={acikMi}
                className="flex h-9 w-full items-center gap-1.5 rounded-orta px-2 text-left hover:bg-black/[0.035]"
              >
                <ChevronRight className={cn("size-3.5 text-metin-3 transition-transform", acikMi && "rotate-90")} />
                <span className="flex-1 text-[13px] font-medium">{g.ad}</span>
                {/*  İki sayı iki ayrı şey:  mavi nokta alanın yanındaki "girildi" noktasıyla
                     aynı;  kırmızı rozetin uyarı işareti uygun olmayan bölümleri sayar
                     ( eskiden yan yana iki çıplak sayıydı )  */}
                {girildi > 0 && (
                  <span className="inline-flex items-center gap-1 text-[11.5px] text-metin-3">
                    <span aria-hidden className="size-1.5 rounded-full bg-vurgu" />
                    {girildi} girildi
                  </span>
                )}
                {hata > 0 && (
                  <Ipucu metin={`${hata} bölüm bu grubun girdilerine bağlı ve uygun değil`}>
                    <span className="inline-flex h-[18px] min-w-[18px] items-center justify-center gap-0.5 rounded-full bg-red px-1.5 text-[11px] font-semibold text-white">
                      <CircleAlert aria-hidden className="size-3" />
                      {hata}
                    </span>
                  </Ipucu>
                )}
              </button>
              {acikMi && (
                <GrupAlanlari
                  ust={
                    g.ad === katGrubu && !aranan ? (
                      katlarDegisti ? (
                        <KatOzeti h={h ?? {}} acik={katlarAcik} ac={() => katlarDegisti(!katlarAcik)} />
                      ) : (
                        katTablosu
                      )
                    ) : null
                  }
                  vurguluAlanlar={vurguluAlanlar}
                  alanlar={g.alanlar}
                  sema={sema}
                  oku={oku}
                  yaz={yaz}
                  kullanilan={kullanilan}
                  mrl={mrl}
                  kuyunun={kuyunun}
                  aramada={!!aranan}
                />
              )}
            </section>
          );
        })}
      </div>
    </aside>
    {katlarAcik && katlarDegisti && (
      //  Akışta ( örtmez ):  tuval daralır, düşey kesit görünür kalır
      <section aria-label="Kat tablosu" className="flex w-[520px] shrink-0 flex-col border-r border-cizgi bg-yuzey">
        <div className="flex items-start justify-between gap-3 border-b border-cizgi px-4 py-3">
          <div>
            <h2 className="text-[13px] font-semibold">Katlar ve kotlar</h2>
            <p className="mt-0.5 text-[12px] text-metin-3">Tuval düşey kesitte;  kapatınca önceki çizime döner.</p>
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
      <Dugme boy="kucuk" aria-expanded={acik} onClick={ac}>
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
  aramada,
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
  aramada: boolean;
  vurguluAlanlar: string[];
}) {
  const [gelismisSecim, setGelismis] = useState(false);
  //  Vurgulu ( ölçünün kaynağı olan ) alan gelişmişteyse bölüm açık görünür
  const gelismis = gelismisSecim || alanlar.some((a) => a.gelismis && vurguluAlanlar.includes(a.anahtar));
  const temel = alanlar.filter((a) => !a.gelismis);
  const ileri = alanlar.filter((a) => a.gelismis);
  const ileriGirilen = ileri.filter((a) => oku(a.anahtar) !== undefined).length;
  const satir = (a: Alan) => (
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
  );
  return (
    <div className="space-y-px pt-0.5 pb-2 pl-2">
      {ust}
      {temel.map(satir)}
      {ileri.length > 0 && (
        <>
          <button
            type="button"
            onClick={() => setGelismis(!gelismis)}
            aria-expanded={gelismis || aramada}
            className="mt-1 ml-1 inline-flex h-7 items-center gap-1 rounded-kucuk px-1.5 text-[12px] font-medium text-metin-2 hover:bg-black/[0.04] hover:text-metin"
          >
            <ChevronRight className={cn("size-3 transition-transform", (gelismis || aramada) && "rotate-90")} />
            Gelişmiş · {ileri.length}
            {ileriGirilen > 0 && <Rozet tur="vurgu">{ileriGirilen} değişti</Rozet>}
          </button>
          {(gelismis || aramada) && <div className="space-y-px border-l border-cizgi pl-1">{ileri.map(satir)}</div>}
        </>
      )}
    </div>
  );
}

/**  Kutudaki değer listedeki yazımıyla:  tarayıcıda "1,6" saklı kalmış olabilir ( seçenek "1.6" )  */
function secimDegeri(secenekler: Deger[], d: string): string {
  const s = secenekler.find((x) => String(x) === d || (typeof x === "number" && sayiOku(d) === x));
  return s === undefined ? d : String(s);
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

  const genis = a.anahtar === "mk_yok" || a.tur === "metin";
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
          {/*  Uzun ad kesilmez, iki satıra iner ( "Kabinin kuyu ortasından sa…" )  */}
          <label htmlFor={id} className="line-clamp-2 min-w-0 text-[12.5px] leading-tight text-metin-2" title={a.etiket}>
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

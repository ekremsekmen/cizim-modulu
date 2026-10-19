/*  UYGULAMA PROJESİ — ÇALIŞMA ALANI
    Tek ekran, üç bölge:  girdiler · çizim ( ya da hesap ) · uygunluk.
    Sunucuyla konuşma useSunucu'da ( gecikme, yarış, hata ve "güncel değil"
    kuralları );  burada yalnız ekranın durumu ve düzeni.                    */
import { useCallback, useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router";
import { Calculator, ChevronDown, CircleAlert, DraftingCompass, Loader2, Package, Plus, TriangleAlert, Undo2, X } from "lucide-react";
import { api, type AlanSemasi, type Bolum } from "@/lib/api";
import {
  alanYaz,
  asansorAdedi,
  asansorEkle,
  asansorKaldir,
  kutuyaYaz,
  useOfisStandardi,
  useUygulamaProjesi,
  type Ham,
  type UygulamaProjesi,
} from "@/lib/proje";
import { cn, etiketBol } from "@/lib/utils";
import { AnaSayfaBaglantisi, BasvuruBaglantilari, UstSerit } from "@/components/Kabuk";
import { Bolumlu, Dugme, HukumNoktasi, Ipucu, Rozet } from "@/components/ui";
import { HesapBelgesi } from "@/components/HesapBelgesi";
import { GirdiPaneli } from "./GirdiPaneli";
import { Tuval, type OlcuSecimi } from "./Tuval";
import { OlcuKutusu } from "./OlcuKutusu";
import { UygunlukPaneli } from "./UygunlukPaneli";
import { Teslim } from "./Teslim";
import { ProjeBilgileri } from "./ProjeBilgileri";
import { useSunucu, type Sorun } from "./useSunucu";

export function Calisma({ proje, bildirim }: { proje: UygulamaProjesi; bildirim?: string }) {
  const sema = useQuery({ queryKey: ["alanlar"], queryFn: api.alanlar, staleTime: Infinity });
  if (sema.error)
    return (
      <div className="flex h-dvh flex-col items-center justify-center gap-2 text-[13px] text-metin-2">
        <CircleAlert className="size-5 text-red" />
        Sunucuya ulaşılamadı — program açık mı?
        <Dugme onClick={() => sema.refetch()}>Yeniden dene</Dugme>
      </div>
    );
  if (!sema.data)
    return (
      <div className="flex h-dvh items-center justify-center gap-2 text-[13px] text-metin-3">
        <Loader2 className="size-4 animate-spin" /> Form şeması yükleniyor
      </div>
    );
  return <CalismaIc sema={sema.data} baslangic={proje} bildirim={bildirim} />;
}

function CalismaIc({ sema, baslangic, bildirim }: { sema: AlanSemasi; baslangic: UygulamaProjesi; bildirim?: string }) {
  const [proje, guncelle, sil] = useUygulamaProjesi(baslangic);
  const [ofis] = useOfisStandardi();
  const [params, setParams] = useSearchParams();
  const gorunum = (params.get("gorunum") as "cizim" | "hesap") ?? "cizim";
  const [asansor, setAsansor] = useState(0);
  const [acik, setAcik] = useState<Set<string>>(() => new Set(["Asansör ve düzen"]));
  const [secili, setSecili] = useState<string | null>(null);
  const [olcu, setOlcuHam] = useState<OlcuSecimi | null>(null);
  //  Ölçü kutusu açıkken ölçüyü belirleyen alanlar solda vurgulu
  const [olcuAlanlari, setOlcuAlanlari] = useState<string[]>([]);
  const setOlcu = (o: OlcuSecimi | null) => {
    setOlcuHam(o);
    if (!o) setOlcuAlanlari([]);
  };
  const olcuKaynaklari = useCallback(
    (anahtarlar: string[]) => {
      setOlcuAlanlari(anahtarlar);
      const gruplar = sema.gruplar.filter((g) => g.alanlar.some((x) => anahtarlar.includes(x.anahtar))).map((g) => g.ad);
      setAcik((e) => new Set([...e, ...gruplar]));
    },
    [sema],
  );
  const [teslimAcik, setTeslimAcik] = useState(params.get("teslim") === "1");
  const [bilgilerAcik, setBilgilerAcik] = useState(false);
  const [duyuru, setDuyuru] = useState(bildirim ?? "");
  //  Kaldırılan asansörler geri alınabilir ( onay sorulmaz, geri dönüş var )
  const [geriAl, setGeriAl] = useState<{ metin: string; asansorler: Ham[]; aktif: number } | null>(null);
  const a = Math.min(asansor, proje.asansorler.length - 1);

  const s = useSunucu(sema, proje, ofis, a, gorunum === "cizim");
  const sonuc = s.sonHesap?.asansorler?.[a];
  const bolumler: Bolum[] = useMemo(
    () => [...(sonuc?.bolumler ?? []), ...(s.sonHesap?.proje_geneli ?? [])],
    [sonuc, s.sonHesap],
  );

  const grupHatasi = useMemo(() => {
    const m: Record<string, number> = {};
    for (const b of bolumler)
      if (b.sonuc?.uygun === false) for (const g of sema.bolum_grubu[b.kimlik] ?? []) m[g] = (m[g] ?? 0) + 1;
    return m;
  }, [bolumler, sema]);

  //  Açılış listesindeki durum ( son başarılı hesabın özeti )
  useEffect(() => {
    const d = s.sonHesap;
    if (!d) return;
    const son = {
      adet: proje.asansorler.length,
      hata: s.hesapEski,
      uygunDegil: (d.asansorler ?? []).reduce((t, x) => t + x.bolumler.filter((b) => b.sonuc?.uygun === false).length, 0),
    };
    if (JSON.stringify(son) !== JSON.stringify(proje.son)) guncelle((p) => ({ ...p, son }));
  }, [s.sonHesap, s.hesapEski, proje.asansorler.length, proje.son, guncelle]);

  const yaz = useCallback(
    (anahtar: string, deger: string) => {
      guncelle((p) => alanYaz(p, sema, a, anahtar, deger));
      //  Kaldırmadan sonra girdi değişti:  geri almak bu değişikliği ezerdi
      setGeriAl(null);
    },
    [guncelle, sema, a],
  );

  const sec = (b: Bolum) => {
    setSecili(b.kimlik);
    setAcik(new Set([...acik, ...(sema.bolum_grubu[b.kimlik] ?? [])]));
    if (gorunum === "hesap")
      requestAnimationFrame(() => document.getElementById(`bolum-${b.kimlik}`)?.scrollIntoView({ behavior: "smooth" }));
  };

  const gorunumSec = (g: "cizim" | "hesap") => {
    const y = new URLSearchParams(params);
    if (g === "cizim") y.delete("gorunum");
    else y.set("gorunum", g);
    setParams(y, { replace: true });
    setOlcu(null);
  };

  const asansorHukmu = (i: number) => s.sonHesap?.ozet?.asansorler?.[i]?.tumu_uygun;
  const asansorAdi = (i: number) => proje.asansorler[i]?.asansor_adi?.trim() || `Asansör ${i + 1}`;

  const ekle = () => {
    guncelle((p) => asansorEkle(p, sema.asansor_azami));
    setAsansor(proje.asansorler.length);
    setGeriAl(null);
    setOlcu(null);
  };
  /**  Asansör kaldırma ( sekmeden ya da adetten ):  önceki hâl "Geri al" için tutulur  */
  const kaldirildi = (metin: string, yeni: UygulamaProjesi) => {
    setGeriAl({ metin, asansorler: proje.asansorler, aktif: a });
    guncelle(() => yeni);
    setOlcu(null);
  };
  const kaldir = (i: number) => {
    kaldirildi(`"${asansorAdi(i)}" kaldırıldı.`, asansorKaldir(proje, i));
    //  Sağdaki sekme kaldırılınca aynı asansörde kalınır;  kendisi kaldırılınca soldakine geçilir
    if (i < a || (i === a && a > 0)) setAsansor(a - 1);
  };
  const adetDegisti = (n: number) => {
    if (n >= proje.asansorler.length) {
      guncelle((p) => asansorAdedi(p, n, sema.asansor_azami));
      return setGeriAl(null);
    }
    const giden = proje.asansorler.length - n;
    kaldirildi(`Son ${giden} asansör kaldırıldı.`, asansorAdedi(proje, n, sema.asansor_azami));
  };
  const ad = proje.kimlik.project_title || "Adsız uygulama projesi";
  const etiket = (k: string) => {
    for (const g of sema.gruplar) for (const x of g.alanlar) if (x.anahtar === k) return etiketBol(x.etiket)[0];
    return k;
  };
  const eskiSonucYok = gorunum === "cizim" ? !s.cizimler.length : !bolumler.length;

  return (
    <div className="flex h-dvh flex-col">
      <UstSerit
        sol={
          <>
            <AnaSayfaBaglantisi />
            <span className="h-5 w-px bg-cizgi" />
            <button
              type="button"
              onClick={() => setBilgilerAcik(true)}
              className="inline-flex min-w-0 items-center gap-1 rounded-orta px-2 py-1 hover:bg-black/[0.04]"
            >
              <span className={cn("truncate text-[13px] font-semibold", !proje.kimlik.project_title && "text-metin-2")}>
                {ad}
              </span>
              <ChevronDown className="size-3.5 shrink-0 text-metin-3" />
            </button>
            {proje.ornek ? <Rozet tur="uyari">ÖRNEK</Rozet> : <Rozet>Uygulama</Rozet>}
          </>
        }
        orta={
          <nav aria-label="Asansörler" className="flex items-center gap-0.5 rounded-orta bg-black/[0.05] p-0.5">
            {proje.asansorler.map((_, i) => (
              <div
                key={i}
                className={cn(
                  "group inline-flex h-7 items-center rounded-kucuk text-[12.5px] font-medium text-metin-2 hover:text-metin",
                  i === a && "bg-yuzey text-metin shadow-panel",
                )}
              >
                <button
                  type="button"
                  onClick={() => {
                    setAsansor(i);
                    setOlcu(null);
                  }}
                  aria-current={i === a ? "page" : undefined}
                  className={cn("inline-flex h-7 items-center gap-1.5 pl-2.5", proje.asansorler.length > 1 ? "pr-1" : "pr-2.5")}
                >
                  <HukumNoktasi uygun={asansorHukmu(i)} />
                  <span className="max-w-32 truncate">{asansorAdi(i)}</span>
                </button>
                {proje.asansorler.length > 1 && (
                  <Ipucu metin="Asansörü kaldır ( geri alınabilir )" yan="bottom">
                    <button
                      type="button"
                      aria-label={`${asansorAdi(i)} asansörünü kaldır`}
                      onClick={() => kaldir(i)}
                      className={cn(
                        "mr-1 inline-flex size-5 items-center justify-center rounded-kucuk text-metin-3 hover:bg-black/[0.06] hover:text-metin focus-visible:opacity-100",
                        i === a ? "opacity-100" : "opacity-0 group-hover:opacity-100",
                      )}
                    >
                      <X className="size-3" />
                    </button>
                  </Ipucu>
                )}
              </div>
            ))}
            {proje.asansorler.length < sema.asansor_azami && (
              <Ipucu metin="Asansör ekle ( 1 nolunun kopyası )" yan="bottom">
                <button
                  type="button"
                  aria-label="Asansör ekle"
                  onClick={ekle}
                  className="inline-flex size-7 items-center justify-center rounded-kucuk text-metin-3 hover:bg-black/[0.05] hover:text-metin"
                >
                  <Plus className="size-3.5" />
                </button>
              </Ipucu>
            )}
          </nav>
        }
        sag={
          <>
            <Bolumlu
              etiket="Görünüm"
              deger={gorunum}
              degisti={gorunumSec}
              secenekler={[
                { deger: "cizim", ad: <><DraftingCompass /> Çizim</> },
                { deger: "hesap", ad: <><Calculator /> Hesap</> },
              ]}
            />
            <span className="mx-1 h-5 w-px bg-cizgi" />
            <BasvuruBaglantilari />
            <Dugme tur="birincil" className="ml-1" onClick={() => setTeslimAcik(true)}>
              <Package /> Teslim
            </Dugme>
          </>
        }
      />

      {geriAl && (
        <div role="status" className="flex shrink-0 items-center gap-2 border-b border-vurgu-cizgi bg-vurgu-acik px-4 py-1.5 text-[12.5px] text-vurgu-koyu">
          <span className="flex-1">{geriAl.metin}</span>
          <Dugme
            tur="hayalet"
            boy="kucuk"
            onClick={() => {
              guncelle((p) => ({ ...p, asansorler: geriAl.asansorler }));
              setAsansor(geriAl.aktif);
              setGeriAl(null);
            }}
          >
            <Undo2 /> Geri al
          </Dugme>
          <button type="button" aria-label="Kapat" onClick={() => setGeriAl(null)}>
            <X className="size-3.5" />
          </button>
        </div>
      )}
      {duyuru && (
        <div role="status" className="flex shrink-0 items-start gap-2 border-b border-vurgu-cizgi bg-vurgu-acik px-4 py-2 text-[12.5px] text-vurgu-koyu">
          <span className="flex-1 whitespace-pre-line">{duyuru}</span>
          <button type="button" aria-label="Kapat" onClick={() => setDuyuru("")}>
            <X className="size-3.5" />
          </button>
        </div>
      )}

      {proje.ornek && (
        <div className="flex h-8 shrink-0 items-center justify-center gap-2 border-b border-uyari-cizgi bg-uyari-acik text-[12.5px] text-uyari">
          <TriangleAlert className="size-3.5" />
          Örnek proje — programı tanımak için;  değerleri yeni projelere taşınmaz.
          <Link to="/uygulama/yeni" className="font-medium underline underline-offset-2">
            Kendi projenizi başlatın
          </Link>
        </div>
      )}

      <div className="flex min-h-0 flex-1">
        <GirdiPaneli
          sema={sema}
          proje={proje}
          asansor={a}
          yaz={yaz}
          acik={acik}
          setAcik={setAcik}
          vurgulu={secili ? (sema.bolum_grubu[secili] ?? []) : []}
          vurguluAlanlar={olcuAlanlari}
          grupHatasi={grupHatasi}
          kullanilan={sonuc?.girdi}
        />

        <main className="relative min-w-0 flex-1 overflow-hidden">
          {gorunum === "cizim" ? (
            <Tuval
              cizimler={s.cizimler}
              durum={s.cizimDurumu}
              secili={olcu}
              olcuSec={(o) => setOlcu(o)}
              odak={params.get("cizim")}
            >
              {(konum) =>
                olcu &&
                konum &&
                s.cizimIstegi && (
                  <OlcuKutusu
                    key={`${olcu.cizim}-${olcu.index}`}
                    istek={s.cizimIstegi}
                    asansor={a}
                    olcu={olcu}
                    konum={konum}
                    kapat={() => setOlcu(null)}
                    kaynaklarGeldi={olcuKaynaklari}
                    yaz={(d) => {
                      guncelle((p) => d.reduce((q, x) => alanYaz(q, sema, a, x.anahtar, kutuyaYaz(x.deger)), p));
                      setGeriAl(null);
                    }}
                  />
                )
              }
            </Tuval>
          ) : (
            <div className="h-full overflow-y-auto">
              <div className="mx-auto max-w-[920px] px-8 py-6">
                <div className="mb-4 flex items-end justify-between">
                  <div>
                    <p className="text-[12px] text-metin-3">Asansör {a + 1}</p>
                    <h1 className="text-[18px] font-semibold tracking-tight">Uygulama projesi hesapları</h1>
                  </div>
                  <span className="text-[12px] text-metin-3">paftadaki sırayla · {bolumler.length} bölüm</span>
                </div>
                <div className={cn(s.hesapEski && "opacity-50")}>
                  <HesapBelgesi bolumler={bolumler} secili={secili} />
                </div>
              </div>
            </div>
          )}

          {s.sorun && (
            <SorunKarti
              sorun={s.sorun}
              koyu={gorunum === "cizim"}
              orta={eskiSonucYok}
              etiket={(k) => etiket(k)}
              cokAsansor={proje.asansorler.length > 1}
            />
          )}
        </main>

        <UygunlukPaneli
          bolumler={bolumler}
          uyarilar={sonuc?.uyarilar ?? []}
          bolumGrubu={sema.bolum_grubu}
          secili={secili}
          sec={sec}
          durdu={s.hesapEski}
        />
      </div>

      <Teslim
        acik={teslimAcik}
        degisti={setTeslimAcik}
        sema={sema}
        proje={proje}
        hesap={s.sonHesap}
        istek={s.istek}
        engel={
          s.hatalar.length
            ? { metin: "Kural dışı girdi var — düzeltilmeden paket inmez.", ciddi: true }
            : s.hesapEski
              ? { metin: "Hesap güncel girdilerle yapılamadı — sebebi çalışma alanında.", ciddi: true }
              : s.hesapYolda
                ? { metin: "Hesap yenileniyor…", ciddi: false }
                : null
        }
        ofis={ofis}
        cizimSayisi={s.cizimler.length}
        projeyiAc={() => {
          setTeslimAcik(false);
          setBilgilerAcik(true);
        }}
      />
      <ProjeBilgileri
        acik={bilgilerAcik}
        degisti={setBilgilerAcik}
        proje={proje}
        guncelle={guncelle}
        adetDegisti={adetDegisti}
        sil={sil}
        sema={sema}
        ofis={ofis}
      />
    </div>
  );
}

function SorunKarti({
  sorun,
  koyu,
  orta,
  etiket,
  cokAsansor,
}: {
  sorun: Sorun;
  koyu: boolean;
  /**  Gösterilecek eski sonuç yoksa kart ortada durur  */
  orta: boolean;
  etiket: (anahtar: string) => string;
  cokAsansor: boolean;
}) {
  const baslik =
    sorun.tur === "kural"
      ? "Kural dışı girdi — sunucuya gönderilmedi"
      : sorun.tur === "baglanti"
        ? "Bağlantı yok"
        : sorun.tur === "hesap"
          ? "Hesap durdu"
          : "Çizim kurulamadı";
  const alt = orta
    ? "Bu girdilerle hesap ve çizim kurulamıyor;  düzeltince kendiliğinden gelir."
    : "Ekrandaki çizim ve hükümler son geçerli girdilerin.";
  const maddeler: { metin: string; git?: () => void }[] =
    sorun.tur === "kural"
      ? sorun.maddeler.map((h) => ({
          metin: `${h.asansor !== null && cokAsansor ? `Asansör ${h.asansor + 1} · ` : ""}${etiket(h.anahtar)}:  ${h.hata}`,
          git: () => document.getElementById(`alan-${h.anahtar}`)?.focus(),
        }))
      : sorun.tur === "baglanti"
        ? [{ metin: sorun.ileti }]
        : sorun.maddeler.map((m) => ({ metin: m }));
  return (
    <div
      role="alert"
      className={cn(
        "absolute z-20 overflow-hidden rounded-buyuk border shadow-kalkik",
        orta
          ? "top-1/2 left-1/2 w-[520px] max-w-[calc(100%-48px)] -translate-x-1/2 -translate-y-1/2"
          : "bottom-10 left-3 w-[440px] max-w-[calc(100%-24px)]",
        koyu ? "border-red/40 bg-[#2b1d1f] text-[#fecdca]" : "border-red-cizgi bg-yuzey text-metin",
      )}
    >
      <div className="flex items-start gap-2 px-4 pt-3 pb-2">
        <CircleAlert className={cn("mt-0.5 size-4 shrink-0", koyu ? "text-[#f97066]" : "text-red")} />
        <div>
          <p className={cn("text-[13px] font-semibold", koyu ? "text-white" : "text-red")}>
            {baslik} <span className="sayi font-normal opacity-70">· {maddeler.length}</span>
          </p>
          <p className={cn("text-[12px]", koyu ? "text-[#fecdca]/70" : "text-metin-3")}>{alt}</p>
        </div>
      </div>
      <ul className="max-h-52 space-y-1 overflow-y-auto px-4 pb-3 pl-10">
        {maddeler.map((m, i) => (
          <li key={i} className="list-disc text-[12.5px] leading-snug marker:text-current/50">
            {m.git ? (
              <button type="button" onClick={m.git} className="text-left underline-offset-2 hover:underline">
                {m.metin}
              </button>
            ) : (
              m.metin
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

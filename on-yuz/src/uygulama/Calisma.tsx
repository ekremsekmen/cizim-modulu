/*  UYGULAMA PROJESİ — ÇALIŞMA ALANI
    Tek ekran, üç bölge:  girdiler · çizim ( ya da hesap ) · uygunluk.
    Sunucuyla konuşma useSunucu'da ( gecikme, yarış, hata ve "güncel değil"
    kuralları );  burada yalnız ekranın durumu ve düzeni.                    */
import { useCallback, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router";
import {
  Calculator,
  ChevronDown,
  CircleAlert,
  DraftingCompass,
  Lightbulb,
  Loader2,
  LocateFixed,
  Package,
  Plus,
  TriangleAlert,
  Undo2,
  X,
} from "lucide-react";
import {
  api,
  type AlanSemasi,
  type Bolum,
  type CareOnerisi,
  type CareYanit,
  type CizimSorunu,
  type CokluYanit,
  type OncekiGirdi,
  type UygulamaIstegi,
} from "@/lib/api";
import {
  alanYaz,
  asansorAdedi,
  asansorEkle,
  asansorKaldir,
  kutuyaYaz,
  istekKur,
  ornekSifirla,
  useOfisStandardi,
  useUygulamaProjesi,
  type Ham,
  type UygulamaProjesi,
} from "@/lib/proje";
import { cn, etiketBol, sayiYaz } from "@/lib/utils";
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
  const [proje, guncelle, sil, baskaSekmedeSilindi] = useUygulamaProjesi(baslangic);
  const [ofis] = useOfisStandardi();
  const [params, setParams] = useSearchParams();
  const gorunum = (params.get("gorunum") as "cizim" | "hesap") ?? "cizim";
  const [asansor, setAsansor] = useState(0);
  const [acik, setAcik] = useState<Set<string>>(() => new Set(["Asansör ve düzen"]));
  const [secili, setSecili] = useState<string | null>(null);
  const [olcu, setOlcuHam] = useState<OlcuSecimi | null>(null);
  //  Ölçü kutusu açıkken ölçüyü belirleyen alanlar solda vurgulu
  //  Her tıklama yeni bir kutu ( aynı ölçüye de ):  kutu açıldığı andaki girdiyle
  //  çalışır, "ölçüye yeniden tıklayın" güncel girdiyle yeniden açar
  const [olcuOturumu, setOlcuOturumu] = useState(0);
  const [olcuAlanlari, setOlcuAlanlari] = useState<string[]>([]);
  const setOlcu = (o: OlcuSecimi | null) => {
    setOlcuHam(o);
    if (o) setOlcuOturumu((n) => n + 1);
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
  //  Kartta seçilen sorun:  tuval onun çizimine gider, parçaları öne çıkar
  const [sorunOdak, setSorunOdak] = useState<{ sorun: CizimSorunu; n: number } | null>(null);
  const [teslimAcik, setTeslimAcik] = useState(params.get("teslim") === "1");
  const [bilgilerAcik, setBilgilerAcik] = useState(false);
  const [duyuru, setDuyuru] = useState(bildirim ?? "");
  //  Kaldırılan asansörler geri alınabilir ( onay sorulmaz, geri dönüş var )
  const [geriAl, setGeriAl] = useState<{ metin: string; asansorler: Ham[]; aktif: number } | null>(null);
  const a = Math.min(asansor, proje.asansorler.length - 1);

  //  Çizim, çizim görünümünde ve teslim açıkken istenir:  teslim son girdinin
  //  çiziminin sorunlarına bakar ( hesap görünümünde eski çizime bakıyordu )
  const s = useSunucu(sema, proje, ofis, a, gorunum === "cizim" || teslimAcik);
  //  SIRAYI KAYDIRAN KALDIRMADAN SONRA ( 21 Eki ):  son hesap eski dizilişindir —
  //  sonuç asansöre sırasıyla eşlendiği için kaldırılan asansörün hükümleri
  //  ( ve sekme noktaları ) kalanınkinde görünüyordu.  Yeni hesap gelene kadar
  //  gösterilmez;  sondan kaldırma sırayı bozmaz, geri alma eski dizilişi döndürür.
  const [kaymis, setKaymis] = useState<CokluYanit>();
  const sonHesap = s.sonHesap !== kaymis ? s.sonHesap : undefined;
  const sonuc = sonHesap?.asansorler?.[a];
  const bolumler: Bolum[] = useMemo(
    () => [...(sonuc?.bolumler ?? []), ...(sonHesap?.proje_geneli ?? [])],
    [sonuc, sonHesap],
  );

  const grupHatasi = useMemo(() => {
    const m: Record<string, number> = {};
    for (const b of bolumler)
      if (b.sonuc?.uygun === false) for (const g of sema.bolum_grubu[b.kimlik] ?? []) m[g] = (m[g] ?? 0) + 1;
    return m;
  }, [bolumler, sema]);

  //  Açılış listesindeki durum ( son başarılı hesabın özeti )
  useEffect(() => {
    const d = sonHesap;
    if (!d) return;
    const son = {
      adet: proje.asansorler.length,
      hata: s.hesapEski,
      uygunDegil: (d.asansorler ?? []).reduce(
        (t, x) => t + (x.bolumler ?? []).filter((b) => b.sonuc?.uygun === false).length,
        0,
      ),
    };
    if (JSON.stringify(son) !== JSON.stringify(proje.son)) guncelle((p) => ({ ...p, son }));
  }, [sonHesap, s.hesapEski, proje.asansorler.length, proje.son, guncelle]);

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
  //  Seçim yalnız o sorun hâlâ listedeyse geçerli ( giderilince işaret kalkar )
  const gecerliOdak =
    sorunOdak &&
    (s.sorun?.tur === "hesap" || s.sorun?.tur === "cizim") &&
    s.sorun.maddeler.some((m) => m.metin === sorunOdak.sorun.metin)
      ? sorunOdak
      : null;
  //  ÇARE ( sunucu:  uclar/care_uclari.py ):  istenince bulunur ( birkaç saniye,
  //  makine daireli projede 10 sn'yi aşabilir — her tuşta değil;  bütçe sınama
  //  sayısıdır, saat değil );  yalnız ekrandaki çizimin girdisi ve ASANSÖRÜ için
  //  geçerlidir.  İstek bütün asansörleri taşır, sekme değişince aynı kalır:
  //  eskiden 1. asansörün çareleri 2.'nin kartında görünüyor ( sorun metni
  //  aynıysa — ikiz asansörler ), "Uygula" 2.'ye yazıyordu ( 20 Eki ).
  const care = useMutation({
    mutationFn: (v: { istek: UygulamaIstegi; asansor: number; onceki: OncekiGirdi | null }) =>
      api.care(v.istek, v.asansor, v.onceki),
  });
  const careBuGirdinin = care.variables?.istek === s.cizimIstegi && care.variables?.asansor === a;
  const careler = careBuGirdinin ? care.data : undefined;
  const careBul = s.cizimIstegi
    ? () => care.mutate({ istek: s.cizimIstegi!, asansor: a, onceki: s.oncekiTemiz })
    : undefined;
  const careUygula = (o: CareOnerisi) => yaz(o.anahtar, typeof o.yeni === "number" ? kutuyaYaz(o.yeni) : o.yeni);
  const sorunuGoster = (m: CizimSorunu) => {
    if (gorunum !== "cizim") gorunumSec("cizim");
    setSorunOdak((o) => ({ sorun: m, n: (o?.n ?? 0) + 1 }));
  };

  const asansorHukmu = (i: number) => sonHesap?.ozet?.asansorler?.[i]?.tumu_uygun;
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
    if (i < proje.asansorler.length - 1) setKaymis(s.sonHesap);
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

      {baskaSekmedeSilindi && (
        <div role="alert" className="flex shrink-0 items-center gap-2 border-b border-red-cizgi bg-red-acik px-4 py-1.5 text-[12.5px] text-red">
          <CircleAlert className="size-3.5 shrink-0" />
          Bu proje başka bir sekmede silindi — buradaki değişiklikler kaydedilmiyor.  Saklamak için dosyaya kaydedin
          ( proje bilgileri ).
        </div>
      )}
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
              setKaymis(undefined);
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
          <span aria-hidden>·</span>
          <button
            type="button"
            onClick={() => {
              guncelle(ornekSifirla);
              setAsansor(0);
              setGeriAl(null);
              setOlcu(null);
            }}
            className="font-medium underline underline-offset-2"
          >
            Örneği sıfırla
          </button>
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
              sorunluParcalar={s.sorunluParcalar}
              sorunOdak={gecerliOdak}
            >
              {(konum) =>
                olcu &&
                konum &&
                s.cizimIstegi && (
                  <OlcuKutusu
                    key={olcuOturumu}
                    istek={s.cizimIstegi}
                    guncel={s.istek}
                    asansor={a}
                    olcu={olcu}
                    konum={konum}
                    kapat={() => setOlcu(null)}
                    kaynaklarGeldi={olcuKaynaklari}
                    yaz={(d) => {
                      const degistir = (p: UygulamaProjesi) =>
                        d.reduce((q, x) => alanYaz(q, sema, a, x.anahtar, kutuyaYaz(x.deger)), p);
                      guncelle(degistir);
                      setGeriAl(null);
                      return istekKur(degistir(proje), ofis);
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
              sorunuGoster={sorunuGoster}
              seciliSorun={gecerliOdak?.sorun.metin ?? null}
              careBul={careBul}
              careYolda={care.isPending && careBuGirdinin}
              careler={careler}
              careUygula={careUygula}
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
        hesap={sonHesap}
        istek={s.istek}
        engel={
          s.hatalar.length
            ? { metin: "Kural dışı girdi var — düzeltilmeden paket inmez.", ciddi: true }
            : s.reddedilen.length
              ? {
                  metin: `${s.reddedilen.map((i) => i + 1).join(", ")} nolu asansör hesaplanamadı — sebebi o asansörün çalışma alanında.`,
                  ciddi: true,
                }
            : s.hesapEski
              ? { metin: "Hesap güncel girdilerle yapılamadı — sebebi çalışma alanında.", ciddi: true }
              : s.cizimDenetleniyor
                ? { metin: "Çizim denetleniyor…", ciddi: false }
              : s.cizimSorunSayisi
                ? {
                    metin: `Çizimde ${s.cizimSorunSayisi} sorun var — giderilmeden paket inmez ( sorunlar çalışma alanında ).`,
                    ciddi: true,
                    yalnizPaket: true,
                  }
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
  sorunuGoster,
  seciliSorun,
  careBul,
  careYolda,
  careler,
  careUygula,
}: {
  sorun: Sorun;
  koyu: boolean;
  /**  Gösterilecek eski sonuç yoksa kart ortada durur  */
  orta: boolean;
  etiket: (anahtar: string) => string;
  cokAsansor: boolean;
  /**  Parçası olan sorun tıklanınca:  tuval onu çizimde gösterir  */
  sorunuGoster: (m: CizimSorunu) => void;
  seciliSorun: string | null;
  /**  Çareleri iste ( ekrandaki çizimin girdisiyle );  yoksa düğme yok  */
  careBul?: () => void;
  careYolda: boolean;
  careler?: CareYanit;
  careUygula: (o: CareOnerisi) => void;
}) {
  //  Çizim sorunlu da olsa ekrandaysa kart küçültülebilir ( çizime bakılsın )
  const [kucuk, setKucuk] = useState(false);
  const cizimGuncel = (sorun.tur === "hesap" || sorun.tur === "cizim") && sorun.cizimGuncel;
  const baslik =
    sorun.tur === "kural"
      ? "Kural dışı girdi — sunucuya gönderilmedi"
      : sorun.tur === "baglanti"
        ? "Bağlantı yok"
        : sorun.tur === "hesap"
          ? "Hesap durdu"
          : cizimGuncel
            ? "Çizim uygun değil"
            : "Çizim kurulamadı";
  const alt = orta
    ? "Bu girdilerle hesap ve çizim kurulamıyor;  düzeltince kendiliğinden gelir."
    : cizimGuncel
      ? sorun.tur === "hesap"
        ? "Çizim bu girdilerle kuruldu;  hükümler son geçerli girdilerin."
        : "Çizim bu girdilerle kuruldu;  sorunlar giderilmeden paket inmez."
      : "Ekrandaki çizim ve hükümler son geçerli girdilerin.";
  //  git:  maddenin gösterdiği yer ( kural dışı girdide kutu, sorunda çizimdeki parça )
  const maddeler: { metin: string; git?: () => void; cizimde?: boolean; cozum?: boolean }[] =
    sorun.tur === "kural"
      ? sorun.maddeler.map((h) => ({
          metin: `${h.asansor !== null && cokAsansor ? `Asansör ${h.asansor + 1} · ` : ""}${etiket(h.anahtar)}:  ${h.hata}`,
          git: () => document.getElementById(`alan-${h.anahtar}`)?.focus(),
        }))
      : sorun.tur === "baglanti"
        ? [{ metin: sorun.ileti }]
        : sorun.maddeler.map((m) =>
            cizimGuncel && m.parcalar.length
              ? { metin: m.metin, git: () => sorunuGoster(m), cizimde: true, cozum: true }
              : { metin: m.metin, cozum: cizimGuncel },
          );
  //  Çareler sorunun metniyle eşleşir ( hesabın yalnız kendi iletisi olan sorunun çaresi yok )
  const careSorunu = (metin: string) => careler?.careler?.find((c) => c.metin === metin);
  const careAcik = !!careler?.aktif && !orta;
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
      <div className={cn("flex items-start gap-2 px-4 pt-3", kucuk ? "pb-3" : "pb-2")}>
        <CircleAlert className={cn("mt-0.5 size-4 shrink-0", koyu ? "text-[#f97066]" : "text-red")} />
        <div className="min-w-0 flex-1">
          <p className={cn("text-[13px] font-semibold", koyu ? "text-white" : "text-red")}>
            {baslik} <span className="sayi font-normal opacity-70">· {maddeler.length}</span>
          </p>
          {!kucuk && <p className={cn("text-[12px]", koyu ? "text-[#fecdca]/70" : "text-metin-3")}>{alt}</p>}
        </div>
        {cizimGuncel && !orta && careBul && !kucuk && (
          <button
            type="button"
            onClick={careBul}
            disabled={careYolda}
            title="Her sorun için hesap ve çizim yeniden kurularak sınanmış sayılı düzeltmeler — uygulamak sizin kararınız"
            className={cn(
              "inline-flex h-6 shrink-0 items-center gap-1 rounded-kucuk border px-2 text-[11.5px] font-medium",
              koyu ? "border-white/15 text-white hover:bg-white/10" : "border-cizgi text-metin hover:bg-black/[0.04]",
              careYolda && "opacity-70",
            )}
          >
            {careYolda ? <Loader2 className="size-3 animate-spin" /> : <Lightbulb className="size-3" />}
            {careYolda ? "Aranıyor…" : careAcik ? "Yeniden ara" : "Düzeltme öner"}
          </button>
        )}
        {cizimGuncel && !orta && (
          <button
            type="button"
            aria-expanded={!kucuk}
            aria-label={kucuk ? "Sorunları göster" : "Sorunları gizle"}
            onClick={() => setKucuk(!kucuk)}
            className="-mr-1 inline-flex size-6 shrink-0 items-center justify-center rounded-kucuk opacity-70 hover:bg-white/10 hover:opacity-100"
          >
            <ChevronDown className={cn("size-4 transition-transform", !kucuk && "rotate-180")} />
          </button>
        )}
      </div>
      {careler && !careler.aktif && !kucuk && (
        <p className="px-4 pb-2 pl-10 text-[12px] opacity-80">{careler.hata?.join(" ") || "Düzeltme aranamadı."}</p>
      )}
      {/*  Kesilen arama söylenir ( eksik sonuç tamamlanmış gibi görünmesin ):  bütçe
           sayıdır, yeniden denemek aynı sonucu verir;  güvenlik süresi ( yüklü
           bilgisayar ) yeniden denemeyle geçebilir  */}
      {careAcik && careler.tamamlandi === false && !kucuk && (
        <p className="px-4 pb-2 pl-10 text-[12px] opacity-80">
          {careler.neden === "sure"
            ? "Arama güvenlik süresinde kesildi — düzeltmeler eksik olabilir;  yeniden deneyin."
            : "Arama sınırına ulaşıldı — bütün adaylar denenmedi, düzeltmeler eksik olabilir."}
        </p>
      )}
      <ul hidden={kucuk} className={cn("space-y-1 overflow-y-auto px-4 pb-3 pl-10", careAcik ? "max-h-96" : "max-h-52")}>
        {maddeler.map((m, i) => (
          <li key={i} className="list-disc text-[12.5px] leading-snug marker:text-current/50">
            {m.git ? (
              <button
                type="button"
                onClick={m.git}
                title={m.cizimde ? "Çizimde göster" : undefined}
                className={cn(
                  "text-left underline-offset-2 hover:underline",
                  m.cizimde && seciliSorun === m.metin && (koyu ? "text-white" : "font-medium"),
                )}
              >
                {m.metin}
                {m.cizimde && <LocateFixed aria-hidden className="ml-1 inline size-3 align-[-1px] opacity-60" />}
              </button>
            ) : (
              m.metin
            )}
            {careAcik && m.cozum && <CareListesi c={careSorunu(m.metin)} koyu={koyu} uygula={careUygula} />}
          </li>
        ))}
      </ul>
    </div>
  );
}

/**  Düzeltmedeki değer:  sayı Türkçe biçimde, seçim olduğu gibi  */
function degerYaz(v: number | string | null) {
  return typeof v === "number" ? sayiYaz(v) : (v ?? "");
}

/**  Bir sorunun doğrulanmış düzeltmeleri ( ekranda "düzeltme";  kodda çare ):
     "Kuyu genişliği  2.300 → 2.230  [ Uygula ]" — program kendiliğinden
     uygulamaz, seçim mühendisin ( bina ölçüsü olabilir )  */
function CareListesi({
  c,
  koyu,
  uygula,
}: {
  c: { metin: string; oneriler: CareOnerisi[] } | undefined;
  koyu: boolean;
  uygula: (o: CareOnerisi) => void;
}) {
  if (!c?.oneriler.length)
    return <p className="mt-1 text-[11.5px] opacity-70">Doğrulanmış düzeltme bulunamadı — girdileri elle gözden geçirin.</p>;
  return (
    <ul aria-label="Düzeltmeler" className="mt-1 mb-1.5 space-y-1">
      {c.oneriler.map((o) => (
        <li
          key={o.anahtar}
          className={cn(
            "flex items-center gap-2 rounded-kucuk px-2 py-1 text-[12px]",
            koyu ? "bg-white/[0.06]" : "bg-black/[0.03]",
          )}
        >
          <span className="min-w-0 flex-1">
            <span className="font-medium">{etiketBol(o.etiket)[0]}</span>{" "}
            <span className={cn("whitespace-nowrap", typeof o.yeni === "number" && "sayi")}>
              {o.girilmis ? degerYaz(o.eski) : `boş ( ${degerYaz(o.eski)} )`} → <b>{degerYaz(o.yeni)}</b>
            </span>
            {o.gider.length > 1 && <span className="opacity-70">  ·  {o.gider.length} sorun birden gider</span>}
            {o.yontem === "son değişiklik" && <span className="opacity-70">  ·  son değişikliğin sınırı</span>}
            {o.ortaya_cikan.length > 0 && (
              <span className="opacity-70" title={o.ortaya_cikan.join("\n")}>
                {"  ·  "}sonra {o.ortaya_cikan.length} gizli sorun görünür
              </span>
            )}
            {o.bina && (
              <span className={cn("ml-1.5 rounded-full px-1.5 text-[10.5px]", koyu ? "bg-[#3a2c12] text-[#fbbf24]" : "bg-uyari-acik text-uyari")}>
                bina ölçüsü
              </span>
            )}
          </span>
          <button
            type="button"
            onClick={() => uygula(o)}
            aria-label={`${etiketBol(o.etiket)[0]} ${degerYaz(o.yeni)} yap`}
            className={cn(
              "shrink-0 rounded-kucuk border px-2 py-0.5 text-[11.5px] font-medium",
              koyu ? "border-white/20 text-white hover:bg-white/10" : "border-cizgi hover:bg-black/[0.04]",
            )}
          >
            Uygula
          </button>
        </li>
      ))}
    </ul>
  );
}

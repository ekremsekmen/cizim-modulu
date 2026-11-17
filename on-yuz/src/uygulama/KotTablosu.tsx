/*  KAT GİRİŞİ — kot tablosu ( KOT_PLANI 6. adım;  2 Kas'tan beri YALNIZ kotla —
    "Ölçüyle" seçici kalktı, kotsuz proje açılırken kotlara çevrilir:  proje.kotlayaCevir ).
    Satırlar yukarıdan aşağı, kesit gibi:  tavan döşemesinin üstü
    ( türetilen — mimarın plan kotuyla karşılaştırılır ) · kuyu tavanı ( döşemenin
    ALTI ) · makine dairesinin zemini · duraklar · kuyu dibi.  Her satıra kot ya da
    fark yazılır;  saklanan hep kottur ( tek kaynak ).  Fark yazılınca üstteki
    satırlar birlikte kayar.  Türetilenler ( durak adedi, seyir, KY, son kat,
    tabliye ) sunucudan gelir — ön yüz hesaplamaz, girişi kolaylaştırır.
    Durak satırında ad ve giriş katı ( KAT_ADLARI_PLANI 3. adım ):  boş ad kuraldan
    ( soluk — giriş katı 0, altı −1, üstü 1 … ), kapı düğmesi giriş katını seçer
    ( yeniden basılınca kurala döner:  ±0,00'a en yakın durak ).  Durak silinince
    üstündekilerin adı bir aşağı kayar.                                          */
import { useEffect, useRef, useState } from "react";
import { DoorOpen, Plus, X } from "lucide-react";
import type { Deger } from "@/lib/api";
import {
  DURAK_ADLARI,
  DURAK_KOTLARI,
  GIRIS_DURAGI,
  KUYU_DIBI_KOTU,
  KUYU_TAVANI_KOTU,
  MD_ZEMINI_KOTU,
  adTablosu,
  adlariOku,
  adlariYaz,
  araligiYaz,
  durakSayisi,
  durakSil,
  girisOku,
  hizliDoldur,
  kaydir,
  kotOku,
  kotYaz,
  kotlaGecis,
  kotlaMi,
  kotlariOku,
  yapistir,
  type Degisiklik,
} from "@/lib/kotlar";
import { sayiOku } from "@/lib/denetim";
import { cn, sayiYaz } from "@/lib/utils";
import { Dugme, Girdi } from "@/components/ui";

type Ham = Record<string, string>;

function parcalar(metin: string | undefined): string[] {
  return (metin ?? "")
    .split(/[;\n]/)
    .map((x) => x.trim())
    .filter((x) => x !== "");
}

/**  Yazarken yerel, Enter ya da odaktan çıkınca uygulanan kutu — fark yazılınca
     üstteki satırlar her tuşta kaymasın.  */
function YerelKutu({
  deger,
  uygula,
  etiket,
  birim,
}: {
  deger: string;
  uygula: (yazi: string) => void;
  etiket: string;
  birim?: string;
}) {
  const [yazi, setYazi] = useState<string | null>(null);
  const bitir = () => {
    if (yazi !== null && yazi.trim() !== "" && yazi !== deger) uygula(yazi);
    setYazi(null);
  };
  return (
    <Girdi
      aria-label={etiket}
      className="h-7"
      inputMode="decimal"
      birim={birim}
      value={yazi ?? deger}
      placeholder="—"
      onChange={(e) => setYazi(e.target.value)}
      onBlur={bitir}
      onKeyDown={(e) => e.key === "Enter" && (e.currentTarget as HTMLInputElement).blur()}
    />
  );
}

/**  Durağın adı:  yazarken yerel ( ad boşluk içerebilir — "ZEMİN KAT" ), Enter ya da
     odaktan çıkınca yazılır;  boş bırakılırsa ad kurala döner ( yer:  kuraldan ad ).  */
function AdKutusu({ deger, yer, uygula, etiket }: { deger: string; yer: string; uygula: (ad: string) => void; etiket: string }) {
  const [yazi, setYazi] = useState<string | null>(null);
  const bitir = () => {
    if (yazi !== null && yazi.trim() !== deger) uygula(yazi);
    setYazi(null);
  };
  return (
    <Girdi
      aria-label={etiket}
      className="h-7 min-w-0 flex-1"
      yazi
      value={yazi ?? deger}
      placeholder={yer}
      onChange={(e) => setYazi(e.target.value)}
      onBlur={bitir}
      onKeyDown={(e) => e.key === "Enter" && (e.currentTarget as HTMLInputElement).blur()}
    />
  );
}

/**  Fark ( mm ):  iki kotun farkı;  yazılınca uygula( mm )  */
function FarkKutusu({ deger, uygula, etiket }: { deger: number | null; uygula: (mm: number) => void; etiket: string }) {
  return (
    <YerelKutu
      etiket={etiket}
      deger={deger === null ? "" : String(deger)}
      uygula={(y) => {
        const n = sayiOku(y);
        if (n !== null && n > 0) uygula(Math.round(n));
      }}
    />
  );
}

function Satir({
  ad,
  etiket,
  kot,
  fark,
  sil,
}: {
  ad: React.ReactNode;
  /**  Satırın adı ( silme düğmesinin etiketi ) — ad kutuysa  */
  etiket?: string;
  kot: React.ReactNode;
  fark?: React.ReactNode;
  sil?: () => void;
}) {
  return (
    <div className="flex items-center gap-1.5 py-px">
      {typeof ad === "string" ? (
        <span className="min-w-0 flex-1 truncate text-[12px] text-metin-2">{ad}</span>
      ) : (
        <div className="flex min-w-0 flex-1 items-center gap-1">{ad}</div>
      )}
      <div className="w-[86px]">{kot}</div>
      <div className="w-[72px]">{fark}</div>
      <div className="w-5">
        {sil && (
          <button type="button" aria-label={`${etiket ?? (typeof ad === "string" ? ad : "durak")} — sil`} onClick={sil} className="text-metin-3 hover:text-red">
            <X className="size-3.5" />
          </button>
        )}
      </div>
    </div>
  );
}

export function KatGirisi({
  h,
  kullanilan,
  daireli,
  doseme,
  etkin,
  yaz,
  bos,
  kapsam,
  duraklar,
  olay,
  hepsine,
  bosAcik,
}: {
  /**  Aktif asansörün yazılmış değerleri  */
  h: Ham;
  /**  Sunucunun hesapta kullandığı değerler ( türetilenler buradan )  */
  kullanilan: Record<string, Deger> | undefined;
  daireli: boolean;
  /**  Tavan döşemesinin etkin kalınlığı ( mm )  */
  doseme: number;
  /**  Alanın etkin sayısı:  yazılmış, yoksa sunucunun kullandığı, yoksa varsayılan  */
  etkin: (anahtar: string) => number | undefined;
  yaz: (anahtar: string, deger: string) => void;
  /**  Kot yokken "Kotlarla gir" yerine gösterilecek ( avan:  ölçüden çevrilecek bir şey
       yoktur — duraklar trafikten doldurulur )  */
  bos?: React.ReactNode;
  /**  "duraklar":  yalnız durak satırları ve araçları ( binanın kot tablosu — avanın Trafik
       adımı );  kuyu tavanı / dibi / makine dairesi satırları ve özet yoktur  */
  /**  Tablonun durak SIRALARINI değiştiren işlem oldu ( avan:  asansörlerin hizmet aralığı sırayla
       tutulur — lib/avan.araliklariUyarla ):  j. durak silindi ya da tablo baştan yazıldı  */
  olay?: (o: { tur: "sil"; j: number } | { tur: "yeni" }) => void;
  kapsam?: "duraklar" | "kuyu";
  /**  kapsam "kuyu":  durak satırlarının yerine gösterilen satır ( asansörün hizmet ettiği
       duraklar — salt okunur )  */
  duraklar?: React.ReactNode;
  /**  Araçların değişikliği ( durak ekle · hızlı doldur · kaydır · aralık · sil ) kuyu tavanını /
       dibini de kaydırır:  avanda kot tablosu binanındır, her kart kendi kuyusuyla hesaplanır
       ( lib/avan.kartlaraUygula ).  Verilmezse değişiklik h'den hesaplanıp yaz ile yazılır.  */
  hepsine?: (f: (h: Ham) => Degisiklik | null) => void;
  /**  Tablo kot yokken de AÇIK durur ( avan:  ölçüden çevrilecek bir şey yoktur ):  boş tablo
       hızlı doldurulur ya da yapıştırılır.  Satırlar arasında Enter / ↑ üstteki, ↓ alttaki durak  */
  bosAcik?: boolean;
}) {
  const [arac, setArac] = useState<null | "doldur" | "yapistir" | "kaydir">(null);
  const kot = kotlaMi(h);
  const yalnizDurak = kapsam === "duraklar";
  //  "kuyu":  asansörün kartı ( avan ) — durak kotları binanın tablosundadır ( Trafik adımı );
  //  kartta yalnız kuyuya özgü kotlar ( tavan, dip, makine dairesi zemini ) girilir.  h'nin durak
  //  kotları asansörün hizmet ettiği dilimdir:  farklar onun en alt / en üst durağından
  const yalnizKuyu = kapsam === "kuyu";
  const yazHepsi = (d: Degisiklik | null) => d && Object.entries(d).forEach(([k, v]) => yaz(k, v));
  //  Değişikliği kartın değerlerinden üreten işlev:  avanda her kart için ayrı koşar
  const uygulaF = (f: (x: Ham) => Degisiklik | null) => (hepsine ? hepsine(f) : yazHepsi(f(h)));
  const uygula = (d: Degisiklik | null) => yazHepsi(d);
  //  Kotlar alttan üste yazılır ama satırlar üstten alta dizilidir ( Tab aşağı gider ):
  //  Enter / ↑ üstteki durağın kotuna, ↓ alttakine geçer ( yalnız avanın tablosunda )
  const tablo = useRef<HTMLDivElement>(null);
  //  Eklenen durağa geçiş:  satır bir sonraki çizimde doğar ( durağın sırası )
  const [odak, setOdak] = useState<number | null>(null);
  const gec = (j: number) => (e: React.KeyboardEvent<HTMLInputElement>) => {
    const hedef = e.key === "Enter" || e.key === "ArrowUp" ? j + 1 : e.key === "ArrowDown" ? j - 1 : null;
    if (hedef === null || !bosAcik) return;
    const kutu = tablo.current?.querySelector<HTMLInputElement>(`input[aria-label="${hedef + 1}. durağın kotu"]`);
    if (kutu) {
      e.preventDefault();
      kutu.focus();
      kutu.select();
      return;
    }
    //  ( 17 Kas ) En üst durakta Enter / ↑:  bir kat yukarıya yeni durak ( kotlar klavyeden art arda
    //  girilir ) — yalnız bu durağın kotu okunuyorsa
    if (hedef === ham.length && k[j] !== null && k[j] !== undefined) {
      e.preventDefault();
      durakEkle();
    }
  };
  const k = kotlariOku(h[DURAK_KOTLARI]);
  const ham = parcalar(h[DURAK_KOTLARI]);
  const enAlt = k[0] ?? null;
  const enUst = k.length ? k[k.length - 1] : null;
  useEffect(() => {
    if (odak === null) return;
    const kutu = tablo.current?.querySelector<HTMLInputElement>(`input[aria-label="${odak + 1}. durağın kotu"]`);
    if (!kutu) return;
    kutu.focus();
    kutu.select();
    setOdak(null);
    //  Satır sayısı:  eklenen durak bu çizimde yoksa satırlar değişince yeniden denenir
  }, [odak, ham.length]);
  const tavan = kotOku(h[KUYU_TAVANI_KOTU]);
  const dip = kotOku(h[KUYU_DIBI_KOTU]);
  //  Makine dairesinin zemini boşsa sunucunun kuralıyla ( tabliye 1.200 ):  soluk
  const mdKullanilan = typeof kullanilan?.[MD_ZEMINI_KOTU] === "number" ? (kullanilan[MD_ZEMINI_KOTU] as number) : null;
  const md = kotOku(h[MD_ZEMINI_KOTU]) ?? (mdKullanilan === null ? null : Math.round(mdKullanilan * 1000));
  //  DURAK EKLE:  bir kat yukarıya ( son iki durağın arası, tek duraksa 3,00 m );  kuyu tavanı ve
  //  makine dairesi zemini kartın kendisinden ( x ) durakla yükselir.  ( 17 Kas ) Tablo boşken ilk
  //  durak ±0,00:  avanın yeni projesinde kot yazılacak satır yoktu ( yalnız hızlı doldur / yapıştır )
  const durakEkle = () => {
    if (enUst === null) {
      if (ham.length) return;
      uygulaF(() => ({ [DURAK_KOTLARI]: kotYaz(0) }));
      setOdak(0);
      return;
    }
    const h1 = k.length > 1 && k[k.length - 2] !== null ? enUst - (k[k.length - 2] as number) : 3000;
    uygulaF((x) => {
      const t = kotOku(x[KUYU_TAVANI_KOTU]);
      const m = kotOku(x[MD_ZEMINI_KOTU]);
      return {
        [DURAK_KOTLARI]: [...ham, kotYaz(enUst + h1)].join("; "),
        ...(t !== null && { [KUYU_TAVANI_KOTU]: kotYaz(t + h1) }),
        ...(m !== null && { [MD_ZEMINI_KOTU]: kotYaz(m + h1) }),
      };
    });
    setOdak(ham.length);
  };
  const durakYaz = (j: number, metin: string) => {
    const y = [...ham];
    y[j] = metin;
    yaz(DURAK_KOTLARI, y.filter((x) => x.trim() !== "").join("; "));
  };
  //  Kat adları:  girilenler ( h ) ve sunucunun kuraldan adları ( yanıtın "_kot"u )
  const adlar = adlariOku(h[DURAK_ADLARI]);
  const kural = adTablosu(kullanilan);
  const girilenGiris = girisOku(h[GIRIS_DURAGI]);
  const giris = girilenGiris ?? kural.giris;
  const adYaz = (j: number, ad: string) => {
    const y = [...adlar];
    while (y.length <= j) y.push("");
    y[j] = ad;
    yaz(DURAK_ADLARI, adlariYaz(y));
  };
  const kotKutusu = (alan: string, etiket: string, yer?: string) => (
    <Girdi
      aria-label={etiket}
      className="h-7"
      inputMode="decimal"
      birim="m"
      value={h[alan] ?? ""}
      placeholder={yer}
      durum={h[alan] === undefined && yer ? "varsayilan" : undefined}
      onChange={(e) => yaz(alan, e.target.value)}
    />
  );

  return (
    <div className="mb-1.5 rounded-orta border border-cizgi bg-black/[0.015] px-2 py-2">
      <div className="flex items-center justify-between gap-2">
        <span className="text-[12.5px] font-medium">{yalnizKuyu ? "Kuyu kotları" : "Katlar"}</span>
        {yalnizKuyu && !kot && (
          <span className="text-[11.5px] text-metin-3">önce binanın kot tablosu ( Trafik hesabı → Katlar )</span>
        )}
        {bosAcik && !yalnizKuyu && (
          <span className="text-[11.5px] text-metin-3">{kot ? "Enter:  üstteki durak" : "en alt duraktan başlayın · Enter:  üstteki durak"}</span>
        )}
        {/*  Kotsuz asansör açılırken kotlara çevrilir ( proje.kotlayaCevir );  yine de
             kotsuz kaldıysa ( başka sekmeden gelen eski hâl ) çeviri elle  */}
        {!kot && !bosAcik && bos}
        {!kot && !bosAcik && !bos && (
          <Dugme
            boy="kucuk"
            onClick={() =>
              uygula(
                kotlaGecis(
                  etkin,
                  h.kat_yukseklikleri ?? (typeof kullanilan?.kat_yukseklikleri === "string" ? kullanilan.kat_yukseklikleri : undefined),
                  daireli,
                ),
              )
            }
          >
            Kotlarla gir
          </Dugme>
        )}
      </div>
      {(kot || (bosAcik && !yalnizKuyu)) && (
        <div className="mt-2" ref={tablo}>
          <div className="flex items-center gap-1.5 pb-0.5 text-[11px] text-metin-3">
            <span className="flex-1 pl-6">ad</span>
            <span className="w-[86px] text-right">kot</span>
            <span className="w-[72px] text-right">fark ( mm )</span>
            <span className="w-5" />
          </div>
          {/*  Mimarın planındaki kot döşemenin ÜSTÜDÜR:  buraya yazılırsa kuyu tavanı
               ( altı ) döşeme kalınlığı çıkarılarak bulunur — altı yerine üstü yazmak
               kuyu üst boşluğunu kalınlık kadar büyük gösterirdi ( güvensiz yön )  */}
          {!yalnizDurak && (
          <>
          <Satir
            ad="Döşemenin üstü"
            kot={
              <YerelKutu
                etiket="Tavan döşemesinin üstü ( mimarın plan kotu )"
                birim="m"
                deger={tavan === null ? "" : kotYaz(tavan + doseme)}
                uygula={(y) => {
                  const m = kotOku(y);
                  if (m !== null) yaz(KUYU_TAVANI_KOTU, kotYaz(m - doseme));
                }}
              />
            }
            fark={<span className="block pr-1 text-right text-[11.5px] text-metin-3">{sayiYaz(doseme)}</span>}
          />
          <Satir
            ad="Kuyu tavanı ( altı )"
            kot={kotKutusu(KUYU_TAVANI_KOTU, "Kuyu tavanı kotu ( döşemenin altı )")}
            fark={
              <FarkKutusu
                etiket="Son kat yüksekliği"
                deger={tavan !== null && enUst !== null ? tavan - enUst : null}
                uygula={(mm) => enUst !== null && yaz(KUYU_TAVANI_KOTU, kotYaz(enUst + mm))}
              />
            }
          />
          {daireli && (
            <Satir
              ad="Makine dairesi zemini"
              kot={kotKutusu(MD_ZEMINI_KOTU, "Makine dairesi zemini kotu", md === null ? undefined : kotYaz(md))}
              fark={
                <FarkKutusu
                  etiket="Tabliye beton yüksekliği"
                  deger={tavan !== null && md !== null ? tavan + doseme - md : null}
                  uygula={(mm) => tavan !== null && yaz(MD_ZEMINI_KOTU, kotYaz(tavan + doseme - mm))}
                />
              }
            />
          )}
          </>
          )}
          {yalnizKuyu && duraklar}
          {(yalnizKuyu ? [] : bosAcik && !ham.length ? [""] : ham)
            .map((metin, j) => ({ metin, j }))
            .reverse()
            .map(({ metin, j }) => {
              const alt = j > 0 ? k[j - 1] : null;
              const bu = k[j];
              const girisMi = giris === j + 1;
              return (
                <Satir
                  key={j}
                  etiket={`${j + 1}. durak`}
                  ad={
                    <>
                      <button
                        type="button"
                        aria-label={`${j + 1}. durak giriş katı`}
                        aria-pressed={girisMi}
                        title={
                          girisMi
                            ? girilenGiris === j + 1
                              ? "Giriş katı ( girildi ) — kurala dönmek için basın"
                              : "Giriş katı ( kuraldan:  kotu ±0,00'a en yakın durak )"
                            : "Giriş katı yap"
                        }
                        onClick={() => yaz(GIRIS_DURAGI, girilenGiris === j + 1 ? "" : String(j + 1))}
                        className={cn(
                          "grid size-5 shrink-0 place-items-center rounded-kucuk",
                          girisMi
                            ? girilenGiris === j + 1
                              ? "bg-vurgu text-white"
                              : "bg-black/[0.06] text-metin-2"
                            : "text-metin-3/40 hover:bg-black/[0.04] hover:text-metin-2",
                        )}
                      >
                        <DoorOpen className="size-3.5" />
                      </button>
                      <AdKutusu
                        etiket={`${j + 1}. durağın adı`}
                        deger={adlar[j] ?? ""}
                        yer={kural.adlar[j] ?? ""}
                        uygula={(ad) => adYaz(j, ad)}
                      />
                    </>
                  }
                  kot={
                    <Girdi
                      aria-label={`${j + 1}. durağın kotu`}
                      className="h-7"
                      inputMode="decimal"
                      birim="m"
                      value={metin}
                      placeholder={!ham.length ? kotYaz(0) : undefined}
                      durum={bu === null ? "hata" : undefined}
                      onKeyDown={bosAcik ? gec(j) : undefined}
                      onChange={(e) => durakYaz(j, e.target.value)}
                    />
                  }
                  fark={
                    j > 0 ? (
                      <FarkKutusu
                        etiket={`${j}. – ${j + 1}. durak arası`}
                        deger={alt !== null && bu !== null ? bu - alt : null}
                        uygula={(mm) => uygulaF((x) => araligiYaz(x, j, mm))}
                      />
                    ) : undefined
                  }
                  sil={
                    ham.length > 2
                      ? () => {
                          uygulaF((x) => durakSil(x, j));
                          olay?.({ tur: "sil", j });
                        }
                      : undefined
                  }
                />
              );
            })}
          {!yalnizDurak && (
            <Satir
              ad="Kuyu dibi"
              kot={kotKutusu(KUYU_DIBI_KOTU, "Kuyu dibi kotu")}
              fark={
                <FarkKutusu
                  etiket="Kuyu dibi yüksekliği ( KY )"
                  deger={dip !== null && enAlt !== null ? enAlt - dip : null}
                  uygula={(mm) => enAlt !== null && yaz(KUYU_DIBI_KOTU, kotYaz(enAlt - mm))}
                />
              }
            />
          )}
          {!yalnizKuyu && kural.hata.length > 0 && (
            <p className="mt-1 px-0.5 text-[11.5px] font-medium text-red">Kat adları:  {kural.hata[0]}</p>
          )}
          {!yalnizKuyu && (
          <div className="mt-1.5 flex flex-wrap gap-1">
            {(kot || bosAcik) && (
              <button
                type="button"
                className="inline-flex h-7 items-center gap-1 rounded-kucuk px-1.5 text-[12px] font-medium text-metin-2 hover:bg-black/[0.04] hover:text-metin"
                onClick={durakEkle}
              >
                <Plus className="size-3.5" /> Durak ekle
              </button>
            )}
            {(kot ? (["doldur", "yapistir", "kaydir"] as const) : (["doldur", "yapistir"] as const)).map((a) => (
              <button
                key={a}
                type="button"
                aria-expanded={arac === a}
                onClick={() => setArac(arac === a ? null : a)}
                className={cn(
                  "inline-flex h-7 items-center rounded-kucuk px-1.5 text-[12px] font-medium text-metin-2 hover:bg-black/[0.04] hover:text-metin",
                  arac === a && "bg-black/[0.05] text-metin",
                )}
              >
                {{ doldur: "Hızlı doldur", yapistir: "Yapıştır", kaydir: "Kaydır" }[a]}
              </button>
            ))}
          </div>
          )}
          {!yalnizKuyu && arac && (
            <Arac arac={arac} kapat={() => setArac(null)} uygulaF={uygulaF} yeni={() => olay?.({ tur: "yeni" })} />
          )}
          {!yalnizDurak && <Ozet kullanilan={kullanilan} daireli={daireli} />}
        </div>
      )}
    </div>
  );
}

/**  Hızlı doldur ( n durak × h, en alt kot — son kat ve KY korunur ) · yapıştır · bütün kotları kaydır  */
function Arac({
  arac,
  kapat,
  uygulaF,
  yeni,
}: {
  arac: "doldur" | "yapistir" | "kaydir";
  kapat: () => void;
  /**  Tablo baştan yazıldı ( hızlı doldur, yapıştır )  */
  yeni: () => void;
  /**  Değişiklik kartın değerlerinden ( x ) üretilir:  son kat yüksekliği ve kuyu dibi
       derinliği o kartın kendi kuyusundan korunur ( avanda her kart için ayrı )  */
  uygulaF: (f: (x: Ham) => Degisiklik | null) => void;
}) {
  const [a, setA] = useState("");
  const [b, setB] = useState("");
  const [c, setC] = useState("");
  const tamam = () => {
    if (arac === "doldur") {
      const n = sayiOku(a);
      const hh = sayiOku(b);
      const alt = kotOku(c || "±0,00");
      if (n === null || hh === null || alt === null || n < 2 || hh <= 0) return;
      const ust = alt + (Math.round(n) - 1) * Math.round(hh);
      uygulaF((x) => {
        const eski = kotlariOku(x[DURAK_KOTLARI]);
        const enAlt = eski[0] ?? null;
        const enUst = eski.length ? eski[eski.length - 1] : null;
        const tavan = kotOku(x[KUYU_TAVANI_KOTU]);
        const dip = kotOku(x[KUYU_DIBI_KOTU]);
        return {
          [DURAK_KOTLARI]: hizliDoldur(Math.round(n), alt, Math.round(hh)),
          ...(tavan !== null && enUst !== null && { [KUYU_TAVANI_KOTU]: kotYaz(ust + (tavan - enUst)) }),
          ...(dip !== null && enAlt !== null && { [KUYU_DIBI_KOTU]: kotYaz(alt - (enAlt - dip)) }),
          //  Adlar yerinde kalır;  fazlası ve durakları aşan giriş katı düşer
          ...durakSayisi(x, Math.round(n)),
        };
      });
      yeni();
    } else if (arac === "yapistir") {
      if (!a.trim()) return;
      const kotlar = yapistir(a);
      uygulaF((x) => ({ [DURAK_KOTLARI]: kotlar, ...durakSayisi(x, kotlariOku(kotlar).length) }));
      yeni();
    } else {
      const m = kotOku(a);
      if (m === null) return;
      uygulaF((x) => kaydir(x, m));
    }
    kapat();
  };
  return (
    <div className="mt-1.5 space-y-1.5 rounded-kucuk border border-cizgi bg-yuzey p-2">
      {arac === "doldur" && (
        <div className="grid grid-cols-3 gap-1">
          <Girdi aria-label="Durak sayısı" placeholder="durak" value={a} onChange={(e) => setA(e.target.value)} className="h-7" />
          <Girdi aria-label="Kat yüksekliği ( mm )" placeholder="kat ( mm )" value={b} onChange={(e) => setB(e.target.value)} className="h-7" />
          <Girdi aria-label="En alt durağın kotu" placeholder="±0,00" value={c} onChange={(e) => setC(e.target.value)} className="h-7" birim="m" />
        </div>
      )}
      {arac === "yapistir" && (
        <textarea
          aria-label="Yapıştırılacak kotlar"
          value={a}
          onChange={(e) => setA(e.target.value)}
          rows={4}
          placeholder={"−7,00\n−3,50\n±0,00\n+3,20 …  ( yukarıdan aşağı da olur )"}
          className="w-full rounded-kucuk border border-cizgi-2 bg-yuzey px-2 py-1 text-[12.5px] outline-none focus:border-vurgu"
        />
      )}
      {arac === "kaydir" && (
        <Girdi aria-label="Bütün kotlar ne kadar kaysın ( m )" placeholder="−7,00 — mimarın ±0,00'ına" value={a} onChange={(e) => setA(e.target.value)} className="h-7" birim="m" />
      )}
      <div className="flex justify-end gap-1">
        <button type="button" onClick={kapat} className="h-7 rounded-kucuk px-2 text-[12px] text-metin-2 hover:bg-black/[0.04]">
          Vazgeç
        </button>
        <button type="button" onClick={tamam} className="h-7 rounded-kucuk bg-vurgu px-2.5 text-[12px] font-medium text-white hover:opacity-90">
          Uygula
        </button>
      </div>
    </div>
  );
}

/**  Türetilenler — sunucunun kullandığı ( yanıtın girdisi ):  ön yüz hesaplamaz  */
function Ozet({ kullanilan, daireli }: { kullanilan: Record<string, Deger> | undefined; daireli: boolean }) {
  const s = (a: string) => (typeof kullanilan?.[a] === "number" ? (kullanilan[a] as number) : null);
  const parca = [
    s("durak_adedi") !== null && `${sayiYaz(s("durak_adedi"))} durak`,
    s("seyir_mesafesi") !== null && `seyir ${sayiYaz(s("seyir_mesafesi"))} m`,
    s("kuyu_dibi") !== null && `KY ${sayiYaz(s("kuyu_dibi"))}`,
    s("son_kat_yuksekligi") !== null && `son kat ${sayiYaz(s("son_kat_yuksekligi"))}`,
    daireli && s("tabliye_yuksekligi") !== null && `tabliye ${sayiYaz(s("tabliye_yuksekligi"))}`,
  ].filter(Boolean);
  if (!parca.length) return null;
  return (
    <p className="mt-1.5 px-0.5 text-[11.5px] text-metin-3" aria-label="Kotlardan türeyenler">
      Kotlardan:  {parca.join(" · ")}
    </p>
  );
}

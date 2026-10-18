/*  AVAN PROJE — üç adım, sırayla:  trafik → avan hesapları → kapak.
    Adımlar birbirini besler:  trafik asansör adedini, kapasiteyi ve hızı
    verir ( avan_koprusu );  ikisi kapağın asansör satırlarını doldurur
    ( kapak_bilgileri ).  Her adımın sonucu sunucudan, aynı hesap belgesiyle.  */
import { lazy, Suspense, useMemo, useRef, useState } from "react";
import { keepPreviousData, useMutation, useQuery } from "@tanstack/react-query";
import { NavLink, useLocation, useNavigate, useParams } from "react-router";
import { Check, ChevronRight, CircleAlert, Download, FileArchive, FolderOpen, Info, Loader2, Plus, Save, Undo2, X } from "lucide-react";
import { api, indir, paketNotu, type AvanKoprusu, type AvanYaniti, type Secenekler, type TrafikYaniti } from "@/lib/api";
import { useGecikmeli, type Ham } from "@/lib/proje";
import {
  AVAN_AZAMI,
  AVAN_SECIM_VARSAYILANI,
  avanDosyayaKaydet,
  avanDosyasiniAc,
  avanSabitleri,
  sabitDegeri,
  TRAFIK_AZAMI,
  trafikFarki,
  useAvanOfisi,
  useAvanProjesi,
  type Acilis,
  type AvanProjesi,
  type EkNufus,
} from "@/lib/avan";
import { KAPAK_GRUPLARI } from "@/lib/kapak";
import { cn, sayiYaz } from "@/lib/utils";
import { AnaSayfaBaglantisi, BasvuruBaglantilari, UstSerit } from "@/components/Kabuk";
import { Anahtar, Dugme, Girdi, Ipucu, Rozet, Secim } from "@/components/ui";
import { HesapBelgesi, HukumRozeti } from "@/components/HesapBelgesi";
//  pdf.js büyüktür ( ~1 MB ):  yalnız kapak adımı açılınca iner
const PdfOnizleme = lazy(() => import("@/components/PdfOnizleme").then((m) => ({ default: m.PdfOnizleme })));

const ADIMLAR = [
  { yol: "trafik", ad: "Trafik hesabı" },
  { yol: "hesaplar", ad: "Avan hesapları" },
  { yol: "kapak", ad: "Kapak" },
] as const;

export function AvanCalisma() {
  const { adim = "trafik" } = useParams();
  const git = useNavigate();
  const sec = useQuery({ queryKey: ["secenekler"], queryFn: api.secenekler });
  const [p, setP] = useAvanProjesi();
  const [ofis] = useAvanOfisi();
  const konum = useLocation();
  const [acilis, setAcilis] = useState<Acilis | null>(() => (konum.state as { acilis?: Acilis } | null)?.acilis ?? null);

  //  TRAFİK isteği:  bina + görünen asansör sütunları
  const trafikGirdi = useMemo(
    () => ({
      ...p.trafik,
      ek_nufus: p.ekNufus.filter((x) => x.miktar.trim() !== ""),
      //  Taahhütname yalnız tek asansör tipinde ( Tablo-10 şartlı kabul );  gizliyken hesaba girmez
      taahhutname: p.trafikAsansorleri.length === 1 ? (p.trafik.taahhutname ?? "") : "",
      asansorler: p.trafikAsansorleri.filter((a) => a.P),
    }),
    [p.trafik, p.ekNufus, p.trafikAsansorleri],
  );
  const tg = useGecikmeli(trafikGirdi);
  const trafik = useQuery({
    queryKey: ["trafik", tg],
    queryFn: ({ signal }) => api.trafik(tg, signal),
    placeholderData: keepPreviousData,
  });
  const kopru = trafik.data && !trafik.data.hata ? (trafik.data.avan_koprusu ?? null) : null;

  //  AVAN isteği:  asansör adedi, kapasite ve hız trafikten
  const avanGirdi = useMemo(() => {
    const ka = (kopru?.asansorler ?? []).slice(0, AVAN_AZAMI);
    const verim = sec.data?.makine_tipleri ?? {};
    return {
      ortak: { ...p.ortak, mk_yok: (p.ortak.mk_yok ?? "true") === "true" },
      asansorler: Array.from({ length: AVAN_AZAMI }, (_, i) => {
        const h = p.avanAsansorleri[i] ?? {};
        if (!ka[i]) return { aktif: false };
        //  Seçimler eski formdaki gibi hep gider:  kutudaki değer kullanıcının
        //  seçimidir, pafta kaynağını GİRİŞ yazar ( gönderilmezse KABUL )
        const secimler = Object.fromEntries(Object.entries(AVAN_SECIM_VARSAYILANI).map(([k, d]) => [k, h[k] || d]));
        return {
          ...h,
          ...secimler,
          aktif: true,
          kapasite: String(ka[i].P),
          V: String(ka[i].V),
          eta: h.eta || String(verim[secimler.makine_tipi] ?? ""),
        };
      }),
      sabitler: avanSabitleri(ofis),
      trafik: kopru,
    };
  }, [p.ortak, p.avanAsansorleri, kopru, sec.data, ofis]);
  const ag = useGecikmeli(avanGirdi);
  const avan = useQuery({
    queryKey: ["avan", ag],
    queryFn: ({ signal }) => api.avan(ag, signal),
    placeholderData: keepPreviousData,
    enabled: !!kopru,
  });

  const kapakVerisi = useMemo(
    () => ({
      ...(trafik.data?.kapak_bilgileri ?? {}),
      ...(avan.data?.kapak_bilgileri ?? {}),
      ...Object.fromEntries(Object.entries(p.kapak).filter(([, v]) => v !== "")),
    }),
    [trafik.data, avan.data, p.kapak],
  );

  const trafikDurum = !trafik.data ? null : trafik.data.hata ? "eksik" : "tamam";
  const avanEksik =
    (avan.data?.asansorler ?? []).filter((a) => !a.aktif && a.uyari).length + (avan.data?.engelleyici?.length ?? 0);
  const avanDurum = !kopru ? null : !avan.data ? null : avan.data.hata || avanEksik ? "eksik" : "tamam";
  const durumlar: Record<string, string | null> = {
    trafik: trafikDurum,
    hesaplar: avanDurum,
    kapak: p.kapak.project_title ? "tamam" : null,
  };

  const paket = useMutation({
    mutationFn: () =>
      indir("proje-dwg", { kapak: kapakVerisi, girdiler: { trafik: trafikGirdi, avan: avanGirdi } }),
  });

  if (!sec.data)
    return (
      <div className="flex h-dvh items-center justify-center gap-2 text-[13px] text-metin-3">
        <Loader2 className="size-4 animate-spin" /> Yükleniyor
      </div>
    );

  //  Dosya açılınca açık proje ezilir ( avan tek projedir, eski arayüz gibi ):
  //  önceki hâli "Geri al" için tutulur
  const dosyaAc = (o: Acilis) => {
    setAcilis({ ...o, onceki: p });
    setP(o.proje);
    git("/avan/trafik", { replace: true });
  };
  const fark = acilis ? trafikFarki(acilis.dosyaAvani, kopru) : null;
  //  Geçmişteki bildirim de silinir:  sayfa yenilenince yeniden çıkmasın
  const kapat = () => {
    setAcilis(null);
    git(konum.pathname, { replace: true });
  };

  return (
    <div className="flex h-dvh flex-col">
      <UstSerit
        sol={
          <>
            <AnaSayfaBaglantisi />
            <span className="h-5 w-px bg-cizgi" />
            <span className={cn("truncate px-2 text-[13px] font-semibold", !p.kapak.project_title && "text-metin-2")}>
              {p.kapak.project_title || "Adsız avan projesi"}
            </span>
            <Rozet>Avan</Rozet>
          </>
        }
        orta={
          <nav aria-label="Adımlar" className="flex items-center gap-1">
            {ADIMLAR.map((a, i) => (
              <div key={a.yol} className="flex items-center gap-1">
                {i > 0 && <span className="h-px w-5 bg-cizgi-2" />}
                <NavLink
                  to={`/avan/${a.yol}`}
                  className={({ isActive }) =>
                    cn(
                      "inline-flex h-8 items-center gap-2 rounded-orta px-2.5 text-[12.5px] font-medium text-metin-2 hover:bg-black/[0.04] hover:text-metin",
                      isActive && "bg-black/[0.05] text-metin",
                    )
                  }
                >
                  <span
                    className={cn(
                      "sayi flex size-5 items-center justify-center rounded-full text-[11px]",
                      durumlar[a.yol] === "tamam"
                        ? "bg-uygun text-white"
                        : durumlar[a.yol] === "eksik"
                          ? "bg-uyari text-white"
                          : "bg-black/[0.07] text-metin-2",
                    )}
                  >
                    {durumlar[a.yol] === "tamam" ? <Check className="size-3" strokeWidth={3} /> : i + 1}
                  </span>
                  {a.ad}
                </NavLink>
              </div>
            ))}
          </nav>
        }
        sag={
          <>
            <BasvuruBaglantilari />
            <DosyaDugmeleri sec={sec.data} ofis={ofis} ac={dosyaAc} kaydet={() => avanDosyayaKaydet(p, sec.data!, ofis, kopru)} />
            <Dugme tur="birincil" className="ml-1" onClick={() => paket.mutate()} disabled={paket.isPending}>
              {paket.isPending ? <Loader2 className="animate-spin" /> : <FileArchive />} Projeyi indir
            </Dugme>
          </>
        }
      />
      {acilis && (
        <div className="flex items-start gap-2 border-b border-vurgu-cizgi bg-vurgu-acik px-4 py-2 text-[12.5px] text-vurgu-koyu">
          <Info className="mt-0.5 size-3.5 shrink-0" />
          <span className="flex-1 whitespace-pre-line">{[acilis.bildirim, fark].filter(Boolean).join("\n")}</span>
          {acilis.onceki && (
            <Dugme
              tur="hayalet"
              boy="kucuk"
              onClick={() => {
                setP(acilis.onceki!);
                kapat();
              }}
            >
              <Undo2 /> Geri al
            </Dugme>
          )}
          <Dugme tur="hayalet" boy="simge-kucuk" aria-label="Bildirimi kapat" onClick={kapat}>
            <X />
          </Dugme>
        </div>
      )}
      {paket.data?.hata && (
        <div className="flex items-center justify-center gap-2 border-b border-red-cizgi bg-red-acik px-4 py-1.5 text-[12.5px] whitespace-pre-line text-red">
          <CircleAlert className="size-3.5 shrink-0" /> {paket.data.hata}
        </div>
      )}
      {!!paket.data?.notlar?.length && (
        <div className="flex items-center justify-center gap-2 border-b border-uyari-cizgi bg-uyari-acik px-4 py-1.5 text-[12.5px] text-uyari">
          <CircleAlert className="size-3.5 shrink-0" /> {paket.data.notlar.map(paketNotu).join("  ·  ")}
        </div>
      )}
      {(trafik.error || avan.error) && (
        <div className="flex items-center justify-center gap-2 border-b border-red-cizgi bg-red-acik px-4 py-1.5 text-[12.5px] text-red">
          <CircleAlert className="size-3.5 shrink-0" /> Sunucuya ulaşılamadı — ekrandaki sonuçlar güncel değil.
        </div>
      )}

      {adim === "trafik" && (
        <TrafikAdimi p={p} setP={setP} sec={sec.data} sonuc={trafik.data} yukleniyor={trafik.isFetching} govde={{ girdiler: trafikGirdi, kapak: kapakVerisi }} ileri={() => git("/avan/hesaplar")} />
      )}
      {adim === "hesaplar" && (
        <HesaplarAdimi p={p} setP={setP} sec={sec.data} ofis={ofis} kopru={kopru} sonuc={avan.data} govde={{ girdiler: avanGirdi, kapak: kapakVerisi }} geri={() => git("/avan/trafik")} />
      )}
      {adim === "kapak" && <KapakAdimi p={p} setP={setP} sec={sec.data} kapak={kapakVerisi} />}
    </div>
  );
}

function DosyaDugmeleri({
  sec,
  ofis,
  ac,
  kaydet,
}: {
  sec: Secenekler;
  ofis: Ham;
  ac: (o: Acilis) => void;
  kaydet: () => void;
}) {
  const girdi = useRef<HTMLInputElement>(null);
  const [hata, setHata] = useState("");
  const oku = async (f: File | undefined) => {
    if (!f) return;
    if (f.size > 2 * 1024 * 1024) return setHata("Dosya çok büyük — bir proje dosyası değil.");
    const o = avanDosyasiniAc(await f.text(), f.name, sec, ofis);
    if (typeof o === "string") return setHata(o);
    setHata("");
    ac(o);
  };
  return (
    <span className="flex items-center gap-1">
      {hata && <span className="max-w-72 text-right text-[12px] leading-snug text-red">{hata}</span>}
      <Ipucu metin="Proje dosyasını aç ( .avan )">
        <Dugme tur="hayalet" boy="simge" aria-label="Proje dosyasını aç" onClick={() => girdi.current?.click()}>
          <FolderOpen />
        </Dugme>
      </Ipucu>
      <Ipucu metin="Proje dosyası olarak kaydet ( .avan ) — eski arayüz de açar">
        <Dugme tur="hayalet" boy="simge" aria-label="Proje dosyası olarak kaydet" onClick={kaydet}>
          <Save />
        </Dugme>
      </Ipucu>
      <input
        ref={girdi}
        type="file"
        accept=".avan,.json"
        className="hidden"
        onChange={(e) => {
          void oku(e.target.files?.[0]);
          e.target.value = "";
        }}
      />
    </span>
  );
}

/* ───────────────────────────── ortak düzen:  solda girdi, sağda sonuç */
function Duzen({ sol, sag }: { sol: React.ReactNode; sag: React.ReactNode }) {
  return (
    <div className="flex min-h-0 flex-1">
      <aside className="w-[420px] shrink-0 overflow-y-auto border-r border-cizgi bg-yuzey">{sol}</aside>
      <main className="min-w-0 flex-1 overflow-y-auto">
        <div className="mx-auto max-w-[900px] px-8 py-6">{sag}</div>
      </main>
    </div>
  );
}

function Kume({ baslik, alt, children }: { baslik: string; alt?: string; children: React.ReactNode }) {
  return (
    <section className="border-b border-cizgi px-4 py-4">
      <h2 className="text-[13px] font-semibold">{baslik}</h2>
      {alt && <p className="mt-0.5 text-[12px] text-metin-3">{alt}</p>}
      <div className="mt-3 space-y-2">{children}</div>
    </section>
  );
}

function Satir({ etiket, id, children, ipucu }: { etiket: string; id: string; children: React.ReactNode; ipucu?: string }) {
  return (
    <div className="grid grid-cols-[1fr_168px] items-center gap-2">
      <label htmlFor={id} className="text-[12.5px] text-metin-2">
        {etiket}
        {ipucu && <span className="ml-1 text-metin-3">· {ipucu}</span>}
      </label>
      {children}
    </div>
  );
}

/* ───────────────────────────── 1 · TRAFİK */
function TrafikAdimi({
  p,
  setP,
  sec,
  sonuc,
  yukleniyor,
  govde,
  ileri,
}: {
  govde: unknown;
  p: AvanProjesi;
  setP: React.Dispatch<React.SetStateAction<AvanProjesi>>;
  sec: Secenekler;
  sonuc: TrafikYaniti | undefined;
  yukleniyor: boolean;
  ileri: () => void;
}) {
  const t = (k: string) => p.trafik[k] ?? "";
  const yaz = (k: string, d: string) => setP((q) => ({ ...q, trafik: { ...q.trafik, [k]: d } }));
  const ay = (i: number, k: string, d: string) =>
    setP((q) => ({ ...q, trafikAsansorleri: q.trafikAsansorleri.map((a, j) => (j === i ? { ...a, [k]: d } : a)) }));
  const hizli = sec.hizli_etiketleri[t("bina_tipi")] ?? sec.hizli_etiketleri[""];
  //  Etiketi yalnız numaradan ibaretse ( "⑤" ) bu bina tipinde hızlı giriş yoktur
  const hizliVar = hizli.hizli1[0].trim().length > 1;
  const ekYaz = (i: number, d: Partial<EkNufus>) =>
    setP((q) => ({ ...q, ekNufus: q.ekNufus.map((x, j) => (j === i ? { ...x, ...d } : x)) }));
  const o = sonuc?.ozet;
  const ILERI = ["h", "bodrum", "manuel_ta", "manuel_tk", "manuel_tg", "manuel_tp"];
  const ileriDolu = p.trafikAsansorleri.reduce((n, a) => n + ILERI.filter((k) => (a[k] ?? "").trim()).length, 0);
  //  Kullanıcı açıp kapatmadıysa ( null ) doluyken açıktır:  dosyadan gelen değer gizli kalmasın
  const [ileriAcik, setIleri] = useState<boolean | null>(null);
  const ayrinti = ileriAcik ?? ileriDolu > 0;

  return (
    <Duzen
      sol={
        <>
          <Kume baslik="Bina" alt="MMO/697 s.12 — nüfus ve bekleme ölçütü bina tipinden">
            <Satir etiket="① Bina tipi" id="t-bina">
              <Secim
                id="t-bina"
                etiket="Bina tipi"
                deger={t("bina_tipi")}
                degisti={(d) => yaz("bina_tipi", d)}
                secenekler={sec.bina_tipleri.map((b) => ({ deger: b, ad: b }))}
              />
            </Satir>
            {[
              ["bina_yuksekligi", "② Bina yüksekliği", "m"],
              ["N", "③ Kat sayısı N", "kat"],
              ["yapi_yuksekligi", "④ Yapı yüksekliği", "m"],
              ["h", "⑦ Kat yüksekliği h", "m"],
              ["bodrum", "⑪ Bodrum durağı", "durak"],
            ].map(([k, e, b]) => (
              <Satir key={k} etiket={e} id={`t-${k}`}>
                <Girdi id={`t-${k}`} value={t(k)} birim={b} onChange={(ev) => yaz(k, ev.target.value)} placeholder={k === "bodrum" ? "0" : ""} />
              </Satir>
            ))}
          </Kume>
          <Kume baslik="Elle ortak V ve k" alt="Boş bırakın — hız Tablo-2 asgarisinden, k Tablo-9'dan.  Elle değerin gerekçesi paftaya yazılır.">
            <Satir etiket="Manuel ortak V" id="t-mV">
              <Secim
                id="t-mV"
                etiket="Manuel ortak V"
                deger={t("manuel_V") || "_"}
                degisti={(d) => yaz("manuel_V", d === "_" ? "" : d)}
                secenekler={[{ deger: "_", ad: "Tablo-2" }, ...sec.hizlar.map((x) => ({ deger: String(x), ad: `${sayiYaz(x)} m/s` }))]}
              />
            </Satir>
            <Satir etiket="Manuel k" id="t-mk" ipucu="0 – 1;  yalnız Tablo-9'da olmayan bina tiplerinde">
              <Girdi id="t-mk" value={t("manuel_k")} placeholder="Tablo-9" onChange={(e) => yaz("manuel_k", e.target.value)} />
            </Satir>
          </Kume>
          <Kume baslik="Nüfus" alt={hizliVar ? "Hızlı giriş bina tipine göre;  ek kalemler Tablo-1'den" : "Bu bina tipinde hızlı giriş yok — nüfus Tablo-1 kalemlerinden"}>
            {hizliVar && (
              <Satir etiket={hizli.hizli1[0]} id="t-h1" ipucu={hizli.hizli1[1].replace(/[()]/g, "").trim()}>
                <Girdi id="t-h1" value={t("hizli1")} onChange={(e) => yaz("hizli1", e.target.value)} />
              </Satir>
            )}
            {hizliVar && hizli.hizli2[0].trim().length > 1 && (
              <Satir etiket={hizli.hizli2[0]} id="t-h2">
                <Girdi id="t-h2" value={t("hizli2")} onChange={(e) => yaz("hizli2", e.target.value)} />
              </Satir>
            )}
            {p.ekNufus.map((x, i) => (
              <div key={i} className="grid grid-cols-[1fr_96px_auto] items-center gap-x-2 gap-y-1">
                <Secim
                  className="col-span-3"
                  etiket={`${i + 1}. nüfus kalemi`}
                  deger={x.kalem}
                  degisti={(d) => ekYaz(i, { kalem: d })}
                  secenekler={sec.nufus_kalemleri.map((k) => ({ deger: k, ad: k }))}
                />
                <Girdi
                  aria-label={`${i + 1}. kalemin açıklaması`}
                  yazi
                  maxLength={120}
                  value={x.aciklama}
                  placeholder="Açıklama"
                  onChange={(e) => ekYaz(i, { aciklama: e.target.value })}
                />
                <Girdi
                  aria-label={`${i + 1}. kalemin miktarı`}
                  value={x.miktar}
                  birim={sec.tablo_1[x.kalem]?.birim}
                  onChange={(e) => ekYaz(i, { miktar: e.target.value })}
                />
                <Dugme
                  tur="hayalet"
                  boy="simge-kucuk"
                  aria-label={`${i + 1}. kalemi sil`}
                  onClick={() => setP((q) => ({ ...q, ekNufus: q.ekNufus.filter((_, j) => j !== i) }))}
                >
                  <X />
                </Dugme>
              </div>
            ))}
            <Dugme
              tur="hayalet"
              boy="kucuk"
              onClick={() =>
                setP((q) => ({ ...q, ekNufus: [...q.ekNufus, { kalem: sec.nufus_kalemleri[0], miktar: "", aciklama: "" }] }))
              }
            >
              <Plus /> Nüfus kalemi ekle
            </Dugme>
          </Kume>
          <Kume baslik="Asansörler" alt="Farklı tiplerde grup formülü kendiliğinden uygulanır">
            {/*  Sabit sütun düzeni:  seçim kutusunun uzun metni ( "Teleskopik Otomatik" )
                 sütunu genişletip ikinci asansörü panelin dışına itiyordu  */}
            <div className="overflow-x-auto rounded-orta border border-cizgi">
              <table className="w-full table-fixed text-[12.5px]">
                <colgroup>
                  <col className="w-[84px]" />
                </colgroup>
                <thead className="bg-yuzey-2 text-[11.5px] text-metin-3">
                  <tr>
                    <th className="px-2 py-1.5 text-left font-medium"> </th>
                    {p.trafikAsansorleri.map((_, i) => (
                      <th key={i} className="px-1 py-1.5 font-medium">
                        <span className="inline-flex items-center gap-1">
                          {i + 1}
                          {i > 0 && (
                            <button
                              type="button"
                              aria-label={`${i + 1}. asansörü kaldır`}
                              onClick={() => setP((q) => ({ ...q, trafikAsansorleri: q.trafikAsansorleri.filter((_, j) => j !== i) }))}
                            >
                              <X className="size-3" />
                            </button>
                          )}
                        </span>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-cizgi">
                  {[
                    { k: "P", e: "⑧ Kapasite", s: sec.kapasiteler.map((x) => ({ deger: String(x), ad: `${x} kişi` })) },
                    {
                      k: "V",
                      e: "Hız",
                      s: [{ deger: "_", ad: "Tablo-2 asgari" }, ...sec.hizlar.map((x) => ({ deger: String(x), ad: `${sayiYaz(x)} m/s` }))],
                    },
                    { k: "kapi_genisligi", e: "Kapı", s: sec.kapi_genislikleri.map((x) => ({ deger: String(x), ad: `${x} mm` })) },
                    { k: "kapi_tipi", e: "Kapı tipi", s: sec.kapi_tipleri.map((x) => ({ deger: x, ad: x })) },
                  ].map(({ k, e, s }) => (
                    <tr key={k}>
                      <td className="px-2 py-1 text-metin-2">{e}</td>
                      {p.trafikAsansorleri.map((a, i) => (
                        <td key={i} className="px-1 py-1">
                          <Secim
                            etiket={`${i + 1}. asansör ${e}`}
                            deger={a[k] || (k === "V" ? "_" : "")}
                            degisti={(d) => ay(i, k, d === "_" ? "" : d)}
                            secenekler={s}
                          />
                        </td>
                      ))}
                    </tr>
                  ))}
                  {[
                    ["durak", "Durak", "N+1"],
                    ...(ayrinti
                      ? [
                          ["h", "h (m)", "ortak"],
                          ["bodrum", "Bodrum durağı", "ortak"],
                          ["manuel_ta", "ta (s)", "T-4"],
                          ["manuel_tk", "tk (s)", "T-4"],
                          ["manuel_tg", "tg (s)", "T-6"],
                          ["manuel_tp", "tp (s)", "T-8"],
                        ]
                      : []),
                  ].map(([k, e, yer]) => (
                    <tr key={k}>
                      <td className="px-2 py-1 text-metin-2">{e}</td>
                      {p.trafikAsansorleri.map((a, i) => (
                        <td key={i} className="px-1 py-1">
                          <Girdi aria-label={`${i + 1}. asansör ${e}`} value={a[k] ?? ""} placeholder={yer} onChange={(ev) => ay(i, k, ev.target.value)} />
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <button
              type="button"
              onClick={() => setIleri(!ayrinti)}
              aria-expanded={ayrinti}
              className="inline-flex items-center gap-1 text-[12px] font-medium text-metin-2 hover:text-metin"
            >
              <ChevronRight className={cn("size-3 transition-transform", ayrinti && "rotate-90")} />
              İleri seçenekler · bodrum ve imalatçı süreleri
              {ileriDolu > 0 && <Rozet tur="vurgu">{ileriDolu} dolu</Rozet>}
            </button>
            {ayrinti && (
              <p className="text-[12px] text-metin-3">
                İmalatçı katalog süresi girilirse tablo değerinin yerine o kullanılır;  paftada marka-model ve teknik föy referansı belirtilmelidir.
              </p>
            )}
            {p.trafikAsansorleri.length === 1 && (
              <Satir etiket="Taahhütname" id="t-taahhut" ipucu="Tablo-10 şartlı kabul">
                <Secim
                  id="t-taahhut"
                  etiket="Taahhütname"
                  deger={t("taahhutname") || "Yok"}
                  degisti={(d) => yaz("taahhutname", d)}
                  secenekler={[
                    { deger: "Yok", ad: "Yok" },
                    { deger: "Var", ad: "Var" },
                  ]}
                />
              </Satir>
            )}
            {p.trafikAsansorleri.length < TRAFIK_AZAMI && (
              <Dugme
                tur="hayalet"
                boy="kucuk"
                onClick={() => setP((q) => ({ ...q, trafikAsansorleri: [...q.trafikAsansorleri, { ...q.trafikAsansorleri[0] }] }))}
              >
                <Plus /> Asansör tipi ekle
              </Dugme>
            )}
          </Kume>
        </>
      }
      sag={
        <>
          <div className="mb-4 flex items-end justify-between">
            <div>
              <p className="text-[12px] text-metin-3">MMO/697, 2. Baskı — s.11-17</p>
              <h1 className="text-[18px] font-semibold tracking-tight">Trafik hesabı</h1>
            </div>
            <div className="flex items-center gap-2">
              {yukleniyor && <Loader2 className="size-4 animate-spin text-metin-3" />}
              <IndirDugmesi uc="trafik-pdf" govde={govde} kapali={!!sonuc?.hata} />
            </div>
          </div>
          {sonuc?.hata ? (
            <div className="rounded-buyuk border border-uyari-cizgi bg-uyari-acik px-5 py-4">
              <p className="text-[13px] font-semibold text-uyari">Hesap için eksik girdi</p>
              <p className="mt-1 text-[12.5px] text-metin-2">{String(sonuc.hata).replace(/^HESAP HATASI:\s*/, "")}</p>
            </div>
          ) : o ? (
            <div className="space-y-4">
              <section className="overflow-hidden rounded-buyuk border border-cizgi bg-yuzey shadow-panel">
                <div className="flex items-start justify-between gap-4 px-5 py-4">
                  <div>
                    <p className="text-[15px] font-semibold">{o.sonuc_cumlesi}</p>
                    <p className="mt-1 text-[12.5px] text-metin-2">
                      {o.bina_tipi} · hesap standardı <b className="font-medium text-metin">{o.standart}</b>
                    </p>
                  </div>
                  <HukumRozeti uygun={(o.karar_olcutleri ?? []).every((k) => k.uygun)} />
                </div>
                <div className="grid grid-cols-5 border-t border-cizgi">
                  {[
                    ["B", sayiYaz(o.B), "kişi"],
                    ["TR", sayiYaz(o.TR), "s"],
                    ["R", sayiYaz(o.R), "kişi/5dk"],
                    ["Ieer", sayiYaz(o.Ieer), `s ≤ ${o.Izul}`],
                    ["Adet", String(o.adet), "asansör"],
                  ].map(([s, d, b], i) => (
                    <div key={s} className={cn("px-4 py-3", i && "border-l border-cizgi")}>
                      <p className="font-mono text-[11.5px] text-metin-3">{s}</p>
                      <p className="sayi mt-0.5 text-[17px] font-semibold">{d}</p>
                      <p className="text-[11px] text-metin-3">{b}</p>
                    </div>
                  ))}
                </div>
                <ul className="divide-y divide-cizgi border-t border-cizgi">
                  {(o.karar_olcutleri ?? []).map((k) => (
                    <li key={k.ad} className="flex items-center gap-3 px-5 py-2">
                      <span className="w-16 text-[12px] font-medium text-metin-2">{k.ad}</span>
                      <span className="flex-1 font-mono text-[11.5px]">{k.metin}</span>
                      <HukumRozeti uygun={k.uygun} />
                    </li>
                  ))}
                </ul>
              </section>
              <Iletiler iletiler={sonuc?.uyarilar ?? []} />
              {!!sonuc?.oneriler?.length && (
                <section className="overflow-hidden rounded-buyuk border border-cizgi bg-yuzey shadow-panel">
                  <header className="border-b border-cizgi px-5 py-3 text-[14px] font-semibold">Alternatifler</header>
                  <table className="w-full text-[12.5px]">
                    <tbody className="divide-y divide-cizgi">
                      {sonuc.oneriler.slice(0, 6).map((x) => (
                        <tr key={x.secenek}>
                          <td className="px-5 py-2">{x.secenek.split("  ·")[0]}</td>
                          <td className="sayi px-2 py-2 text-right">{x.adet} adet</td>
                          <td className="sayi px-2 py-2 text-right text-metin-2">Ieer {sayiYaz(x.Ieer)} s</td>
                          <td className="px-5 py-2 text-right text-[11.5px] text-metin-3">{x.erisilebilir ? "erişilebilir" : "EN 81-70 dışı"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </section>
              )}
              <HesapBelgesi bolumler={sonuc?.bolumler ?? []} />
              <div className="flex justify-end">
                <Dugme tur="birincil" onClick={ileri}>
                  Avan hesaplarına geç
                </Dugme>
              </div>
            </div>
          ) : null}
        </>
      }
    />
  );
}

/* ───────────────────────────── 2 · AVAN HESAPLARI */
type AvanAlani = {
  k: string;
  e: string;
  birim?: string;
  tur?: "metin" | "secim";
  secenekler?: (s: Secenekler) => { deger: string; ad: string }[];
  /**  Seçimde "ofis standardı" ( boş ) şıkkı var mı  */
  bosOlur?: boolean;
  /**  Boş kutuda görünen:  ofis standardı ( bu tarayıcınınki ) ya da kural  */
  yer?: (s: Secenekler, h: Ham, ofis: Ham) => string;
};

const VAR_YOK = () => [
  { deger: "Yok", ad: "Yok" },
  { deger: "Var", ad: "Var" },
];
const KESIT = (s: Secenekler) => s.kesitler.map((x) => ({ deger: String(x), ad: `${sayiYaz(x)} mm²` }));
const OFIS = (k: string) => (s: Secenekler, _h: Ham, ofis: Ham) => sabitDegeri(s, ofis, k);

/*  Eski arayüzün avan formuyla aynı alanlar, aynı birimler ( 19 Eki kaldırıldı ).
    Uzunluklar karışıktır:  kuyu ve kabin ölçüleri mm, kuyu yüksekliği ve
    kablo uzunlukları m — sunucunun beklediği budur.                      */
const AVAN_TEMEL: AvanAlani[] = [
  { k: "tanim", e: "Asansör adı", tur: "metin" },
  {
    k: "i_palanga",
    e: "i — Askı oranı",
    tur: "secim",
    secenekler: (s) => Object.entries(s.aski_oranlari).map(([ad, d]) => ({ deger: String(d), ad })),
  },
  { k: "eta", e: "η — Makine verimi", yer: (s, h) => sayiYaz(s.makine_tipleri[h.makine_tipi || "Dişlisiz"]) },
  { k: "Hk", e: "Hk — Kuyu yüksekliği", birim: "m" },
  { k: "kuyu_genisligi", e: "Kuyu genişliği", birim: "mm" },
  { k: "kabin_boyu", e: "Kabin boyu a", birim: "mm" },
  { k: "kabin_genisligi", e: "Kabin genişliği b", birim: "mm" },
  { k: "Nsc", e: "Nsç — Motor gücü", birim: "kW", yer: () => "otomatik" },
  { k: "denge_zinciri", e: "Denge zinciri", tur: "secim", secenekler: VAR_YOK },
  { k: "agirlik_guvenlik_tertibati", e: "Karşı ağırlıkta güvenlik tertibatı", tur: "secim", secenekler: VAR_YOK },
];

const AVAN_OFISTEN_FARKLI: AvanAlani[] = [
  { k: "Q_elle", e: "Q elle — yalnız Tablo-7 dışı", birim: "kg" },
  { k: "Gk_elle", e: "Gk elle", birim: "kg", yer: () => "Tablo-11" },
  { k: "gr", e: "gr — Ray birim kütlesi", birim: "kg/m", yer: OFIS("gr") },
  { k: "Fmk", e: "Fmk — Makine ağırlığı", birim: "kg", yer: OFIS("Fmk") },
  { k: "Fsh", e: "Fsh — Sehpa ağırlığı", birim: "kg", yer: OFIS("Fsh") },
  { k: "q_denge", e: "q — Denge faktörü", yer: OFIS("q_denge") },
  { k: "S1", e: "S1 — Kolon hattı kesiti", tur: "secim", secenekler: KESIT, bosOlur: true, yer: OFIS("S1") },
  { k: "L1", e: "L1 — Kolon hattı uzunluğu", birim: "m", yer: () => "Hk + pay" },
  { k: "S2", e: "S2 — Makine besleme kesiti", tur: "secim", secenekler: KESIT, bosOlur: true, yer: OFIS("S2") },
  { k: "L2", e: "L2 — Makine besleme uzunluğu", birim: "m", yer: OFIS("L2") },
  { k: "kablo_tipi", e: "Kablo tipi", tur: "metin", yer: OFIS("kablo_tipi") },
  { k: "zincir_birim_kutle", e: "mz — Denge zinciri birim kütlesi", birim: "kg/m", yer: OFIS("zincir_birim_kutle") },
];

function AvanAlanSatiri({
  a,
  sec,
  ofis,
  h,
  yaz,
}: {
  a: AvanAlani;
  sec: Secenekler;
  ofis: Ham;
  h: Ham;
  yaz: (k: string, d: string) => void;
}) {
  const id = `a-${a.k}`;
  return (
    <Satir etiket={a.e} id={id}>
      {a.tur === "secim" && a.secenekler ? (
        <Secim
          id={id}
          etiket={a.e}
          deger={h[a.k] || AVAN_SECIM_VARSAYILANI[a.k] || (a.bosOlur ? "_" : "")}
          degisti={(d) => yaz(a.k, d === "_" ? "" : d)}
          secenekler={[
            ...(a.bosOlur ? [{ deger: "_", ad: `ofis standardı ( ${a.yer?.(sec, h, ofis) ?? ""} mm² )` }] : []),
            ...a.secenekler(sec),
          ]}
        />
      ) : (
        <Girdi
          id={id}
          value={h[a.k] ?? ""}
          birim={a.birim}
          yazi={a.tur === "metin"}
          maxLength={a.tur === "metin" ? 120 : 32}
          placeholder={a.yer?.(sec, h, ofis) ?? ""}
          onChange={(ev) => yaz(a.k, ev.target.value)}
        />
      )}
    </Satir>
  );
}

function HesaplarAdimi({
  p,
  setP,
  sec,
  ofis,
  kopru,
  sonuc,
  govde,
  geri,
}: {
  govde: unknown;
  p: AvanProjesi;
  setP: React.Dispatch<React.SetStateAction<AvanProjesi>>;
  sec: Secenekler;
  ofis: Ham;
  kopru: AvanKoprusu | null;
  sonuc: AvanYaniti | undefined;
  geri: () => void;
}) {
  const [secili, setSecili] = useState(0);
  const [farkliAcik, setFarkliAcik] = useState(false);
  if (!kopru)
    return (
      <div className="flex flex-1 items-center justify-center">
        <div className="max-w-sm text-center">
          <p className="text-[14px] font-semibold">Önce trafik hesabı</p>
          <p className="mt-1 text-[13px] text-metin-2">Asansör adedi, kapasite ve hız trafik hesabından gelir.</p>
          <Dugme className="mt-4" onClick={geri}>
            Trafik hesabına dön
          </Dugme>
        </div>
      </div>
    );
  const asansorler = kopru.asansorler.slice(0, AVAN_AZAMI);
  const i = Math.min(secili, asansorler.length - 1);
  const h = p.avanAsansorleri[i] ?? {};
  const ad = (j: number) => p.avanAsansorleri[j]?.tanim?.trim() || `Asansör ${j + 1}`;
  const ay = (k: string, d: string) =>
    setP((q) => ({ ...q, avanAsansorleri: q.avanAsansorleri.map((a, j) => (j === i ? { ...a, [k]: d } : a)) }));
  const oy = (k: string, d: string) => setP((q) => ({ ...q, ortak: { ...q.ortak, [k]: d } }));
  const asonuc = sonuc?.asansorler?.find((x) => x.no === i + 1);
  const mrl = (p.ortak.mk_yok ?? "true") === "true";
  const farkliDolu = AVAN_OFISTEN_FARKLI.filter((a) => (h[a.k] ?? "").trim()).length;

  return (
    <Duzen
      sol={
        <>
          <div className="flex flex-wrap items-center gap-1 border-b border-cizgi px-4 py-3">
            {asansorler.map((a, j) => (
              <button
                key={j}
                type="button"
                onClick={() => setSecili(j)}
                aria-current={j === i ? "true" : undefined}
                className={cn(
                  "rounded-orta px-2.5 py-1.5 text-left text-[12.5px] hover:bg-black/[0.04]",
                  j === i && "bg-vurgu-acik text-vurgu-koyu hover:bg-vurgu-acik",
                )}
              >
                <span className="block max-w-28 truncate font-medium">{ad(j)}</span>
                <span className="sayi text-[11px] text-metin-3">
                  {a.P} kişi · {sayiYaz(a.V)} m/s
                </span>
              </button>
            ))}
          </div>
          {kopru.asansorler.length > AVAN_AZAMI && (
            <p className="border-b border-uyari-cizgi bg-uyari-acik px-4 py-2 text-[12px] text-uyari">
              Trafik {kopru.asansorler.length} asansör veriyor;  avan en çok {AVAN_AZAMI} asansör hesaplar.
            </p>
          )}
          <Kume baslik={ad(i)} alt="Kapasite ve hız trafikten;  değiştirmek için trafiğe dönün">
            <Satir etiket="Kapasite · hız" id="a-kh" ipucu="trafikten">
              <span className="sayi text-right text-[13px] text-metin-2">
                {asansorler[i].P} kişi · {sayiYaz(asansorler[i].V)} m/s
              </span>
            </Satir>
            <Satir etiket="Makine tipi" id="a-mt">
              <Secim
                id="a-mt"
                etiket="Makine tipi"
                deger={h.makine_tipi || AVAN_SECIM_VARSAYILANI.makine_tipi}
                degisti={(d) => ay("makine_tipi", d)}
                secenekler={Object.keys(sec.makine_tipleri).map((x) => ({ deger: x, ad: x }))}
              />
            </Satir>
            {AVAN_TEMEL.map((a) => (
              <AvanAlanSatiri key={a.k} a={a} sec={sec} ofis={ofis} h={h} yaz={ay} />
            ))}
            <button
              type="button"
              onClick={() => setFarkliAcik(!farkliAcik)}
              aria-expanded={farkliAcik}
              className="mt-1 inline-flex items-center gap-1 text-[12px] font-medium text-metin-2 hover:text-metin"
            >
              <ChevronRight className={cn("size-3 transition-transform", farkliAcik && "rotate-90")} />
              Ofis standardından farklı değerler · {AVAN_OFISTEN_FARKLI.length}
              {farkliDolu > 0 && <Rozet tur="vurgu">{farkliDolu} dolu</Rozet>}
            </button>
            {farkliAcik && (
              <div className="space-y-2 border-l border-cizgi pl-3">
                <p className="text-[12px] text-metin-3">Boş bırakılan ofis standardıdır;  yalnız bu asansörde farklıysa doldurun.</p>
                {AVAN_OFISTEN_FARKLI.map((a) => (
                  <AvanAlanSatiri key={a.k} a={a} sec={sec} ofis={ofis} h={h} yaz={ay} />
                ))}
              </div>
            )}
          </Kume>
          <Kume baslik="Bina" alt="Bütün asansörler için bir kez">
            <Satir etiket="Makine dairesi yok ( MRL )" id="a-mrl">
              <div className="flex justify-end">
                <Anahtar id="a-mrl" acik={mrl} degisti={(d) => oy("mk_yok", String(d))} etiket="Makine dairesi yok" />
              </div>
            </Satir>
            {[
              ["temel_a", "Temel uzunluğu a", "m"],
              ["temel_b", "Temel genişliği b", "m"],
              ...(!mrl
                ? [
                    ["mk_uzunluk", "Makine dairesi uzunluğu A", "mm"],
                    ["mk_genislik", "Makine dairesi genişliği B", "mm"],
                  ]
                : []),
            ].map(([k, e, b]) => (
              <Satir key={k} etiket={e} id={`a-${k}`}>
                <Girdi id={`a-${k}`} value={p.ortak[k] ?? ""} birim={b} onChange={(ev) => oy(k, ev.target.value)} />
              </Satir>
            ))}
          </Kume>
        </>
      }
      sag={
        <>
          <div className="mb-4 flex items-end justify-between">
            <div>
              <p className="text-[12px] text-metin-3">{ad(i)}</p>
              <h1 className="text-[18px] font-semibold tracking-tight">Avan hesapları</h1>
            </div>
            <IndirDugmesi uc="avan-pdf" govde={govde} kapali={!!sonuc?.hata || !!sonuc?.engelleyici?.length} />
          </div>
          {sonuc?.hata && <Iletiler iletiler={[sonuc.hata]} kirmizi />}
          <Iletiler iletiler={sonuc?.engelleyici ?? []} kirmizi />
          <Iletiler iletiler={(sonuc?.uyarilar ?? []).filter((u) => !(sonuc?.asansorler ?? []).some((x) => x.uyari === u))} />
          {asonuc && !asonuc.aktif ? (
            <div className="rounded-buyuk border border-uyari-cizgi bg-uyari-acik px-5 py-4">
              <p className="text-[13px] font-semibold text-uyari">Girdi tamamlanmadı</p>
              <p className="mt-1 text-[12.5px] text-metin-2">
                {String(asonuc.uyari ?? "")
                  .replace(/!+/g, "")
                  .replace(/^\s*\d+ NOLU ASANSÖR —\s*/i, "")
                  .trim()}
              </p>
            </div>
          ) : (
            <HesapBelgesi bolumler={asonuc?.bolumler ?? []} />
          )}
          <BinaHesabi baslik="Bina · makine dairesi" h={sonuc?.makine_dairesi} />
          <BinaHesabi baslik="Bina · temel topraklama" h={sonuc?.topraklama} />
        </>
      }
    />
  );
}

/**  Binaya ait hesap ( bir kez ):  uygulanmıyorsa ya da eksikse sebebi  */
function BinaHesabi({ baslik, h }: { baslik: string; h: AvanYaniti["topraklama"] }) {
  if (!h) return null;
  return (
    <div className="mt-6">
      <p className="mb-2 text-[12px] font-medium tracking-wide text-metin-3 uppercase">{baslik}</p>
      {h.aktif ? (
        <HesapBelgesi bolumler={h.bolumler ?? []} />
      ) : (
        <p className="rounded-orta border border-cizgi bg-yuzey px-4 py-3 text-[12.5px] text-metin-2">
          {String(h.uyari ?? "Uygulanmaz.")
            .replace(/!+/g, "")
            .trim()}
        </p>
      )}
    </div>
  );
}

/**  Sunucunun iletileri:  "ℹ" ile başlayan not ( mavi ), "⚠" uyarı, engelleyici kırmızı  */
function Iletiler({ iletiler, kirmizi }: { iletiler: string[]; kirmizi?: boolean }) {
  if (!iletiler.length) return null;
  return (
    <div className="mb-4 space-y-2">
      {iletiler.map((u) => {
        const not = u.trim().startsWith("ℹ");
        return (
          <p
            key={u}
            className={cn(
              "rounded-orta border px-4 py-2.5 text-[12.5px] whitespace-pre-line",
              kirmizi
                ? "border-red-cizgi bg-red-acik text-red"
                : not
                  ? "border-vurgu-cizgi bg-vurgu-acik text-vurgu-koyu"
                  : "border-uyari-cizgi bg-uyari-acik text-uyari",
            )}
          >
            {u.replace(/^[⚠ℹ!\s]+/, "").replace(/[\s!]+$/, "")}
          </p>
        );
      })}
    </div>
  );
}

/* ───────────────────────────── 3 · KAPAK */
function KapakAdimi({
  p,
  setP,
  sec,
  kapak,
}: {
  p: AvanProjesi;
  setP: React.Dispatch<React.SetStateAction<AvanProjesi>>;
  sec: Secenekler;
  kapak: Record<string, string>;
}) {
  const turetilen = new Set<string>(sec.kapak_turetilen);
  const gecikmeli = useGecikmeli(kapak, 600);
  const onizleme = useQuery({
    queryKey: ["kapak-pdf", gecikmeli],
    enabled: !!gecikmeli.project_title,
    placeholderData: keepPreviousData,
    queryFn: async () => {
      const r = await fetch("/api/indir/kapak-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kapak: gecikmeli }),
      });
      //  Sunucu reddederse JSON ileti gelir:  PDF diye çizilmesin, sebebi görünsün
      if ((r.headers.get("Content-Type") || "").includes("application/json")) {
        const j = await r.json();
        throw new Error(Array.isArray(j.hata) ? j.hata.join(" ") : String(j.hata ?? "Kapak üretilemedi"));
      }
      return r.arrayBuffer();
    },
  });
  return (
    <Duzen
      sol={
        <>
          {KAPAK_GRUPLARI.map((k) => (
            <Kume key={k.baslik} baslik={k.baslik} alt={k.baslik === "Asansör" ? "Boş bırakılanlar hesaptan gelir;  yazarsanız sizinki geçer" : undefined}>
              {k.alanlar.map(([a, e]) => (
                <Satir key={a} etiket={e} id={`k-${a}`}>
                  <Girdi
                    id={`k-${a}`}
                    yazi
                    value={p.kapak[a] ?? ""}
                    maxLength={200}
                    placeholder={turetilen.has(a) ? (kapak[a] ?? "hesaptan") : ""}
                    onChange={(ev) => setP((q) => ({ ...q, kapak: { ...q.kapak, [a]: ev.target.value } }))}
                  />
                </Satir>
              ))}
            </Kume>
          ))}
        </>
      }
      sag={
        <>
          <div className="mb-4 flex items-end justify-between">
            <div>
              <p className="text-[12px] text-metin-3">Sunucunun ürettiği PDF — paketteki kapağın aynısı</p>
              <h1 className="text-[18px] font-semibold tracking-tight">Kapak</h1>
            </div>
            <IndirDugmesi uc="kapak-pdf" govde={{ kapak }} kapali={!kapak.project_title} />
          </div>
          <div className="overflow-hidden rounded-buyuk border border-cizgi bg-yuzey shadow-panel">
            {onizleme.error ? (
              <div className="flex h-[calc(100dvh-170px)] items-center justify-center px-8 text-center text-[13px] text-red">
                {onizleme.error.message}
              </div>
            ) : kapak.project_title ? (
              <div className="h-[calc(100dvh-170px)]">
                <Suspense fallback={null}>
                  <PdfOnizleme veri={onizleme.data} />
                </Suspense>
              </div>
            ) : (
              <div className="flex h-[calc(100dvh-170px)] items-center justify-center text-[13px] text-metin-3">
                Önizleme için kapak başlığını yazın
              </div>
            )}
          </div>
        </>
      }
    />
  );
}

function IndirDugmesi({ uc, govde, kapali }: { uc: string; govde: unknown; kapali?: boolean }) {
  const m = useMutation({ mutationFn: () => indir(uc, govde) });
  //  Sunucunun reddi düğmenin yanında okunur ( yalnız ipucunda kalmasın )
  return (
    <span className="flex max-w-md items-center gap-2">
      {m.data?.hata && <span className="text-right text-[12px] leading-snug text-red">{m.data.hata}</span>}
      <Ipucu metin="PDF olarak indir">
        <Dugme onClick={() => m.mutate()} disabled={kapali || m.isPending}>
          {m.isPending ? <Loader2 className="animate-spin" /> : <Download />} PDF
        </Dugme>
      </Ipucu>
    </span>
  );
}

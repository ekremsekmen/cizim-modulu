/*  UYGUNLUK — bölümlerin hükmü, kalanlar başta.
    Bir bölüme tıklamak:  bağlı girdi gruplarını solda açar ( bolum_grubu ),
    hesap görünümündeyse bölüme gider.  Hüküm metni sunucunundur — çare de.
    Ö3:  uygun değil kartı nedeni ve öneriyi ayrı satırlarda okur ( sonucun
    maddeleri;  yoksa metni ), konum simgesi bölümün parçalarını çizimde
    gösterir, "İlgili girdiler" grubu solda açar.  Hesap ya da çizim durunca
    sorunlar panelin başındadır ( sorunlar ).  Uygun ve bilgi bölümleri ( kuyu
    tabanı yükleri — sayıları hesap belgesinde ) kapalı listede.                */
import { useState } from "react";
import { AlertTriangle, ChevronRight, CircleAlert, LocateFixed } from "lucide-react";
import type { Bolum } from "@/lib/api";
import { bolumAdi, cn } from "@/lib/utils";
import { HukumNoktasi } from "@/components/ui";

export function UygunlukPaneli({
  bolumler,
  uyarilar,
  bolumGrubu,
  secili,
  sec,
  durdu,
  cizimdeGoster,
  grupAc,
  sorunlar,
  parcali = {},
}: {
  /**  Bölümlerin çizimdeki parçaları ( "Çizimde göster" yalnız parçası olanda )  */
  parcali?: Record<string, string[]>;
  bolumler: Bolum[];
  uyarilar: string[];
  bolumGrubu: Record<string, string[]>;
  secili: string | null;
  sec: (b: Bolum) => void;
  durdu: boolean;
  /**  Bölümün parçaları çizimdeyse:  onları gösteren çizime gider  */
  cizimdeGoster?: (b: Bolum) => void;
  /**  "İlgili girdiler" çipi:  grubu solda açar  */
  grupAc?: (grup: string) => void;
  /**  Hesap / çizim durduysa sorunlar ( panelin başında — K3 )  */
  sorunlar?: React.ReactNode;
}) {
  const [uygunlarAcik, setUygunlarAcik] = useState(false);
  const kalan = bolumler.filter((b) => b.sonuc?.uygun === false);
  const uygun = bolumler.filter((b) => b.sonuc?.uygun === true);
  const bilgi = bolumler.filter((b) => b.sonuc?.uygun == null);

  return (
    <aside aria-label="Uygunluk" className="flex w-[324px] shrink-0 flex-col border-l border-cizgi bg-yuzey">
      <div className="border-b border-cizgi px-4 pt-3 pb-3">
        <div className="flex items-baseline justify-between">
          <h2 className="text-[13px] font-semibold">Uygunluk</h2>
          <span className="text-[12px] text-metin-3">{bolumler.length} bölüm</span>
        </div>
        {/*  Üç sayı:  bir bakışta proje nerede  */}
        <div className="mt-2.5 grid grid-cols-3 overflow-hidden rounded-orta border border-cizgi text-center">
          <Sayac sayi={kalan.length} ad="uygun değil" renk={kalan.length ? "text-red" : "text-metin-3"} />
          <Sayac sayi={uygun.length} ad="uygun" renk="text-uygun" ayrac />
          <Sayac sayi={bilgi.length} ad="bilgi" renk="text-metin-2" ayrac />
        </div>
        {durdu && (
          <p className="mt-2.5 flex items-start gap-1.5 text-[12px] leading-snug text-uyari">
            <CircleAlert className="mt-px size-3.5 shrink-0" />
            Hükümler son geçerli girdilerin;  güncel girdiyle hesap yapılamadı.
          </p>
        )}
      </div>

      <div className={cn("min-h-0 flex-1 space-y-2 overflow-y-auto p-3", durdu && "opacity-60")}>
        {sorunlar}

        {kalan.map((b) => (
          <UygunDegilKarti
            key={b.kimlik}
            b={b}
            secili={secili === b.kimlik}
            sec={sec}
            gruplar={bolumGrubu[b.kimlik] ?? []}
            cizimdeGoster={parcali[b.kimlik]?.length ? cizimdeGoster : undefined}
            grupAc={grupAc}
          />
        ))}

        {!bolumler.length && (
          <p className="px-2 py-6 text-center text-[12.5px] leading-relaxed text-metin-3">
            Henüz hüküm yok.  Hesap kurulunca bölümler burada, kalanlar en üstte listelenir.
          </p>
        )}

        {uyarilar.map((u) => (
          <Uyari key={u} metin={u.replace(/^[⚠ℹ]\s*/, "")} />
        ))}

        {uygun.length + bilgi.length > 0 && (
          <AcilirBaslik acik={uygunlarAcik} degisti={setUygunlarAcik}>
            Uygun bölümler · {uygun.length}
            {bilgi.length > 0 && <span className="font-normal text-metin-3">  ·  bilgi {bilgi.length}</span>}
          </AcilirBaslik>
        )}
        {/*  Hükümsüz bölümler ( kuyu tabanı yükleri ) ayrı bölüm değil:  kapalı listenin sonunda
             gri noktayla ( 6 Kas — kullanıcı:  görüntü kirliliği;  sayıları hesap belgesinde )  */}
        {uygunlarAcik &&
          [...uygun, ...bilgi].map((b) => <SatirBolum key={b.kimlik} b={b} secili={secili === b.kimlik} sec={sec} />)}
      </div>
    </aside>
  );
}

function UygunDegilKarti({
  b,
  secili,
  sec,
  gruplar,
  cizimdeGoster,
  grupAc,
}: {
  b: Bolum;
  secili: boolean;
  sec: (b: Bolum) => void;
  gruplar: string[];
  cizimdeGoster?: (b: Bolum) => void;
  grupAc?: (grup: string) => void;
}) {
  const [no, ad] = bolumAdi(b.baslik);
  const maddeler = b.sonuc?.maddeler ?? [];
  const metin = (b.sonuc?.metin ?? "").replace(/^UYGUN DEĞİLDİR\s*[—:-]?\s*/i, "");
  return (
    <article
      className={cn(
        "rounded-buyuk border bg-yuzey transition-colors",
        secili ? "border-vurgu bg-vurgu-acik/40 ring-3 ring-vurgu/10" : "border-red-cizgi",
      )}
    >
      <div className="flex items-start gap-1 pt-2.5 pr-1.5 pl-3">
        <button
          type="button"
          onClick={() => sec(b)}
          aria-pressed={secili}
          className="flex min-w-0 flex-1 items-start gap-2 text-left text-[13px] font-medium hover:underline"
        >
          <HukumNoktasi uygun={false} className="mt-[5px]" />
          <span className="min-w-0">
            <span className="sayi mr-1 text-metin-3">{no}</span>
            {ad}
          </span>
        </button>
        {cizimdeGoster && (
          <button
            type="button"
            aria-label="Çizimde göster"
            title="Bölümün parçalarını çizimde göster"
            onClick={() => cizimdeGoster(b)}
            className="inline-flex size-6 shrink-0 items-center justify-center rounded-kucuk text-metin-3 hover:bg-black/[0.05] hover:text-metin"
          >
            <LocateFixed className="size-3.5" />
          </button>
        )}
      </div>
      <div className="px-3 pt-1.5 pb-3 pl-[30px]">
        {maddeler.length ? (
          <dl className="space-y-2 text-[12.5px] leading-snug">
            {maddeler.map((m, i) => (
              <div key={i} className="space-y-0.5">
                <dt className="sr-only">Neden</dt>
                <dd className="text-metin tabular-nums">{m.neden}</dd>
                {m.oneri && (
                  <>
                    <dt className="sr-only">Öneri</dt>
                    <dd className="flex gap-1 text-metin-2">
                      <span aria-hidden className="text-metin-3">→</span>
                      {m.oneri}
                    </dd>
                  </>
                )}
              </div>
            ))}
          </dl>
        ) : (
          <p className="text-[12.5px] leading-snug text-metin-2">{metin || "Uygun değil"}</p>
        )}
        {gruplar.length > 0 && (
          <div className="mt-2.5 flex flex-wrap items-center gap-1">
            <span className="mr-0.5 text-[11px] text-metin-3">İlgili girdiler</span>
            {gruplar.map((g) =>
              grupAc ? (
                <button
                  key={g}
                  type="button"
                  onClick={() => grupAc(g)}
                  className="inline-flex items-center gap-0.5 rounded-[4px] bg-black/[0.05] px-1.5 py-px text-[11px] text-metin-2 hover:bg-vurgu-acik hover:text-vurgu-koyu"
                >
                  {g}
                  <ChevronRight className="size-3" />
                </button>
              ) : (
                <span key={g} className="rounded-[4px] bg-black/[0.05] px-1.5 py-px text-[11px] text-metin-2">
                  {g}
                </span>
              ),
            )}
          </div>
        )}
      </div>
    </article>
  );
}

function Sayac({ sayi, ad, renk, ayrac }: { sayi: number; ad: string; renk: string; ayrac?: boolean }) {
  return (
    <div className={cn("py-2", ayrac && "border-l border-cizgi")}>
      <div className={cn("sayi text-[18px] leading-none font-semibold", renk)}>{sayi}</div>
      <div className="mt-1 text-[11px] text-metin-3">{ad}</div>
    </div>
  );
}

/**  Kapalı başlayan liste başlığı ( hükümsüz ve uygun bölümler )  */
function AcilirBaslik({
  acik,
  degisti,
  children,
}: {
  acik: boolean;
  degisti: (a: boolean) => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={() => degisti(!acik)}
      aria-expanded={acik}
      className="mt-1 flex w-full items-center gap-1 px-1 py-1 text-[12px] font-medium text-metin-2 hover:text-metin"
    >
      <ChevronRight className={cn("size-3 transition-transform", acik && "rotate-90")} />
      {children}
    </button>
  );
}

function SatirBolum({
  b,
  secili,
  sec,
}: {
  b: Bolum;
  secili: boolean;
  sec: (b: Bolum) => void;
}) {
  const [no, ad] = bolumAdi(b.baslik);
  return (
    <button
      type="button"
      onClick={() => sec(b)}
      aria-pressed={secili}
      className={cn(
        "flex w-full items-start gap-2 rounded-orta px-2 py-1.5 text-left hover:bg-black/[0.035]",
        secili && "bg-vurgu-acik hover:bg-vurgu-acik",
      )}
    >
      <HukumNoktasi uygun={b.sonuc?.uygun} className="mt-[5px]" />
      <span className="min-w-0 flex-1">
        <span className="block truncate text-[12.5px]">
          <span className="sayi mr-1 text-metin-3">{no}</span>
          {ad}
        </span>
      </span>
    </button>
  );
}

function Uyari({ metin }: { metin: string }) {
  const [acik, setAcik] = useState(false);
  const uzun = metin.length > 160;
  return (
    <div className="rounded-buyuk border border-uyari-cizgi bg-uyari-acik p-3">
      <p className={cn("flex gap-1.5 text-[12.5px] leading-snug text-uyari", !acik && uzun && "line-clamp-4")}>
        <AlertTriangle className="mt-px size-3.5 shrink-0" />
        <span>{metin}</span>
      </p>
      {uzun && (
        <button
          type="button"
          onClick={() => setAcik(!acik)}
          className="mt-1 ml-5 text-[12px] font-medium text-uyari underline-offset-2 hover:underline"
        >
          {acik ? "Kısalt" : "Devamı"}
        </button>
      )}
    </div>
  );
}

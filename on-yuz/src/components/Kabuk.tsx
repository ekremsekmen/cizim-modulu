import * as React from "react";
import { Link, NavLink } from "react-router";
import { BookOpen, CircleAlert, Loader2, SlidersHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";
import { Dugme, Ipucu } from "./ui";

/**  Ekranın sunucudan başlangıç verisi ( form şeması, seçenekler ) gelmeden:  yükleniyor
     ya da ulaşılamadı + yeniden dene.  24 Eki:  hata durumuna bakmayan ekranlar ( avan,
     ofis standardı, tablolar ) istek düşünce sonsuza dek "Yükleniyor"da kalıyordu.  */
export function SunucuBekleniyor({
  sorgu,
  metin = "Yükleniyor",
}: {
  sorgu: { error: Error | null; isFetching: boolean; refetch: () => unknown };
  metin?: string;
}) {
  if (sorgu.error && !sorgu.isFetching)
    return (
      <div role="alert" className="flex h-dvh flex-col items-center justify-center gap-2 text-[13px] text-metin-2">
        <CircleAlert className="size-5 text-red" />
        Sunucuya ulaşılamadı — program açık mı?
        <Dugme onClick={() => sorgu.refetch()}>Yeniden dene</Dugme>
      </div>
    );
  return (
    <div className="flex h-dvh items-center justify-center gap-2 text-[13px] text-metin-3">
      <Loader2 className="size-4 animate-spin" /> {metin}
    </div>
  );
}

/**  Programın işareti:  kuyu, iki ray, kabin.  */
export function Isaret({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={cn("size-6", className)} aria-hidden>
      <rect x="1" y="1" width="22" height="22" rx="6" fill="var(--color-metin)" />
      <path d="M7 5v14M17 5v14" stroke="#fff" strokeWidth="1.6" strokeLinecap="round" />
      <rect x="9.2" y="9" width="5.6" height="6.5" rx="1" fill="var(--color-vurgu-cizgi)" />
      <path d="M12 5v4" stroke="#fff" strokeWidth="1.2" />
    </svg>
  );
}

/**  Üst şerit:  48 px, beyaz, alt çizgi.  Sol · orta · sağ.  */
export function UstSerit({ sol, orta, sag }: { sol: React.ReactNode; orta?: React.ReactNode; sag?: React.ReactNode }) {
  return (
    <header className="relative z-20 grid h-12 shrink-0 grid-cols-[1fr_auto_1fr] items-center gap-3 border-b border-cizgi bg-yuzey px-3">
      <div className="flex min-w-0 items-center gap-2">{sol}</div>
      <div className="flex items-center gap-2">{orta}</div>
      <div className="flex items-center justify-end gap-1.5">{sag}</div>
    </header>
  );
}

export function AnaSayfaBaglantisi() {
  return (
    <Ipucu metin="Açılış" yan="bottom">
      <Link to="/" aria-label="Açılış" className="rounded-orta p-1 hover:bg-black/[0.04]">
        <Isaret />
      </Link>
    </Ipucu>
  );
}

/**  Başvuru sayfaları ( her projede aynı ):  ofis standardı · tablolar.  */
export function BasvuruBaglantilari() {
  const sinif = ({ isActive }: { isActive: boolean }) =>
    cn(
      "inline-flex size-8 items-center justify-center rounded-orta text-metin-2 hover:bg-black/[0.04] hover:text-metin [&_svg]:size-4",
      isActive && "bg-black/[0.05] text-metin",
    );
  return (
    <>
      <Ipucu metin="Ofis standardı" yan="bottom">
        <NavLink to="/ofis-standardi" aria-label="Ofis standardı" className={sinif}>
          <SlidersHorizontal />
        </NavLink>
      </Ipucu>
      <Ipucu metin="Tablolar" yan="bottom">
        <NavLink to="/tablolar" aria-label="Tablolar" className={sinif}>
          <BookOpen />
        </NavLink>
      </Ipucu>
    </>
  );
}

/**  Başvuru sayfasının kabuğu:  üst şerit + sol gezinti + içerik.  */
export function BasvuruSayfasi({
  baslik,
  aciklama,
  gezinti,
  ust,
  genis,
  children,
}: {
  /**  Geniş tablolar için içerik sınırı kalkar  */
  genis?: boolean;
  baslik: string;
  aciklama: React.ReactNode;
  gezinti: React.ReactNode;
  ust?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-dvh flex-col">
      <UstSerit
        sol={
          <>
            <AnaSayfaBaglantisi />
            <span className="text-[13px] font-semibold">{baslik}</span>
          </>
        }
        sag={<BasvuruBaglantilari />}
      />
      <div className="flex min-h-0 flex-1">
        <nav aria-label={baslik} className="w-64 shrink-0 overflow-y-auto border-r border-cizgi bg-yuzey p-2">
          {gezinti}
        </nav>
        <main className="min-w-0 flex-1 overflow-y-auto">
          <div className={cn("mx-auto px-8 py-7", genis ? "max-w-none" : "max-w-5xl")}>
            <div className="mb-5 flex items-end justify-between gap-6">
              <div>
                <h1 className="text-xl font-semibold tracking-tight">{baslik}</h1>
                <p className="mt-1 max-w-2xl text-[13px] leading-relaxed text-metin-2">{aciklama}</p>
              </div>
              {ust}
            </div>
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

export function GezintiOgesi({
  secili,
  onClick,
  children,
  sag,
}: {
  secili: boolean;
  onClick: () => void;
  children: React.ReactNode;
  sag?: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-current={secili ? "true" : undefined}
      className={cn(
        "flex w-full items-center justify-between gap-2 rounded-kucuk px-2.5 py-1.5 text-left text-[13px] text-metin-2 hover:bg-black/[0.04] hover:text-metin",
        secili && "bg-vurgu-acik font-medium text-vurgu-koyu hover:bg-vurgu-acik hover:text-vurgu-koyu",
      )}
    >
      <span className="min-w-0 truncate">{children}</span>
      {sag}
    </button>
  );
}

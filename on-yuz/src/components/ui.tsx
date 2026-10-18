/*  TEMEL BİLEŞENLER — shadcn/ui üslubu, Radix üstünde.
    Erişilebilirlik Radix'ten:  klavye, odak, aria;  burada yalnız görünüm.  */
import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { Dialog, Popover, Select, Switch, Tooltip, ToggleGroup } from "radix-ui";
import { Check, ChevronDown, X } from "lucide-react";
import { cn } from "@/lib/utils";

/* ───────────────────────────── Düğme */
const dugmeTuru = cva(
  "inline-flex items-center justify-center gap-1.5 whitespace-nowrap font-medium transition-colors disabled:pointer-events-none disabled:opacity-50 [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      tur: {
        birincil: "bg-vurgu text-white hover:bg-vurgu-koyu shadow-panel",
        ikincil: "bg-yuzey text-metin border border-cizgi-2 hover:bg-yuzey-2 shadow-panel",
        hayalet: "text-metin-2 hover:bg-black/[0.04] hover:text-metin",
        tehlike: "bg-red text-white hover:bg-red/90",
        tuval: "text-tuval-metin hover:bg-white/10 hover:text-white",
      },
      boy: {
        kucuk: "h-7 px-2.5 text-[12.5px] rounded-kucuk",
        orta: "h-8 px-3 text-[13px] rounded-orta",
        buyuk: "h-10 px-4 text-sm rounded-orta",
        simge: "size-8 rounded-orta",
        "simge-kucuk": "size-7 rounded-kucuk",
      },
    },
    defaultVariants: { tur: "ikincil", boy: "orta" },
  },
);

export function Dugme({
  className,
  tur,
  boy,
  ...p
}: React.ComponentProps<"button"> & VariantProps<typeof dugmeTuru>) {
  return <button type="button" className={cn(dugmeTuru({ tur, boy }), className)} {...p} />;
}

/* ───────────────────────────── Metin / sayı kutusu ( birim içeride ) */
export function Girdi({
  className,
  birim,
  durum,
  yazi,
  ...p
}: React.ComponentProps<"input"> & { birim?: string; durum?: "hata" | "varsayilan" | "degisti"; yazi?: boolean }) {
  return (
    <div
      className={cn(
        "group/girdi flex h-8 items-center rounded-kucuk border bg-yuzey transition-colors focus-within:border-vurgu focus-within:ring-3 focus-within:ring-vurgu/15",
        durum === "hata"
          ? "border-red ring-3 ring-red/10 focus-within:border-red focus-within:ring-red/15"
          : "border-cizgi-2 hover:border-metin-3/50",
        className,
      )}
    >
      <input
        className={cn(
          "h-full min-w-0 flex-1 bg-transparent px-2.5 text-[13px] outline-none placeholder:text-metin-3",
          yazi ? "text-left" : "sayi text-right",
          durum === "varsayilan" && "text-metin-3",
        )}
        {...p}
      />
      {birim && birim !== "—" && (
        <span className="pr-2.5 pl-0.5 text-[11.5px] text-metin-3 select-none">{birim}</span>
      )}
    </div>
  );
}

/* ───────────────────────────── Seçim ( Radix Select ) */
export function Secim({
  deger,
  degisti,
  secenekler,
  etiket,
  varsayilanMi,
  className,
  id,
}: {
  deger: string;
  degisti: (d: string) => void;
  secenekler: { deger: string; ad: string; kapali?: string }[];
  etiket?: string;
  varsayilanMi?: boolean;
  className?: string;
  id?: string;
}) {
  return (
    <Select.Root value={deger} onValueChange={degisti}>
      <Select.Trigger
        id={id}
        aria-label={etiket}
        className={cn(
          "flex h-8 w-full items-center justify-between gap-1 rounded-kucuk border border-cizgi-2 bg-yuzey px-2.5 text-[13px] hover:border-metin-3/50 focus:border-vurgu focus:ring-3 focus:ring-vurgu/15 focus:outline-none data-[placeholder]:text-metin-3",
          varsayilanMi && "text-metin-3",
          className,
        )}
      >
        <span className="truncate">
          <Select.Value />
        </span>
        <Select.Icon>
          <ChevronDown className="size-3.5 text-metin-3" />
        </Select.Icon>
      </Select.Trigger>
      <Select.Portal>
        <Select.Content
          position="popper"
          sideOffset={4}
          className="z-50 max-h-80 min-w-[var(--radix-select-trigger-width)] overflow-hidden rounded-orta border border-cizgi bg-yuzey shadow-kalkik"
        >
          <Select.Viewport className="p-1">
            {secenekler.map((s) => (
              <Select.Item
                key={s.deger}
                value={s.deger}
                disabled={!!s.kapali}
                className="relative flex cursor-default flex-col rounded-kucuk py-1.5 pr-2 pl-7 text-[13px] outline-none select-none data-[disabled]:text-metin-3 data-[highlighted]:bg-vurgu-acik data-[highlighted]:text-vurgu-koyu"
              >
                <Select.ItemIndicator className="absolute top-2 left-2">
                  <Check className="size-3.5" />
                </Select.ItemIndicator>
                <Select.ItemText>{s.ad}</Select.ItemText>
                {s.kapali && <span className="mt-0.5 text-[11.5px] leading-snug">{s.kapali}</span>}
              </Select.Item>
            ))}
          </Select.Viewport>
        </Select.Content>
      </Select.Portal>
    </Select.Root>
  );
}

/* ───────────────────────────── Anahtar ( evet / hayır ) */
export function Anahtar({
  acik,
  degisti,
  etiket,
  id,
}: {
  acik: boolean;
  degisti: (a: boolean) => void;
  etiket?: string;
  id?: string;
}) {
  return (
    <Switch.Root
      id={id}
      checked={acik}
      onCheckedChange={degisti}
      aria-label={etiket}
      className="relative h-5 w-9 shrink-0 rounded-full bg-cizgi-2 transition-colors data-[state=checked]:bg-vurgu"
    >
      <Switch.Thumb className="block size-4 translate-x-0.5 rounded-full bg-white shadow transition-transform data-[state=checked]:translate-x-[18px]" />
    </Switch.Root>
  );
}

/* ───────────────────────────── Rozet / hüküm */
const rozetTuru = cva(
  "inline-flex items-center gap-1 rounded-full border px-2 py-px text-[11.5px] font-medium whitespace-nowrap",
  {
    variants: {
      tur: {
        uygun: "bg-uygun-acik text-uygun border-uygun-cizgi",
        red: "bg-red-acik text-red border-red-cizgi",
        uyari: "bg-uyari-acik text-uyari border-uyari-cizgi",
        bilgi: "bg-yuzey-2 text-metin-2 border-cizgi",
        vurgu: "bg-vurgu-acik text-vurgu-koyu border-vurgu-cizgi",
      },
    },
    defaultVariants: { tur: "bilgi" },
  },
);
export function Rozet({ className, tur, ...p }: React.ComponentProps<"span"> & VariantProps<typeof rozetTuru>) {
  return <span className={cn(rozetTuru({ tur }), className)} {...p} />;
}

/** Hüküm noktası:  uygun · uygun değil · bilgi ( hükümsüz bölüm ) */
export function HukumNoktasi({ uygun, className }: { uygun: boolean | null | undefined; className?: string }) {
  return (
    <span
      aria-hidden
      className={cn(
        "inline-block size-2 shrink-0 rounded-full",
        uygun === true ? "bg-uygun" : uygun === false ? "bg-red" : "bg-metin-3/40",
        className,
      )}
    />
  );
}

/* ───────────────────────────── İpucu */
export function Ipucu({ metin, children, yan = "top" }: { metin: React.ReactNode; children: React.ReactNode; yan?: "top" | "right" | "bottom" | "left" }) {
  return (
    <Tooltip.Root delayDuration={250}>
      <Tooltip.Trigger asChild>{children}</Tooltip.Trigger>
      <Tooltip.Portal>
        <Tooltip.Content
          side={yan}
          sideOffset={6}
          className="z-50 max-w-72 rounded-kucuk bg-metin px-2.5 py-1.5 text-[12px] leading-relaxed text-white shadow-kalkik"
        >
          {metin}
        </Tooltip.Content>
      </Tooltip.Portal>
    </Tooltip.Root>
  );
}
export const IpucuSaglayici = Tooltip.Provider;

/* ───────────────────────────── Bölümlü seçici ( görünüm, asansör ) */
export function Bolumlu<T extends string>({
  deger,
  degisti,
  secenekler,
  etiket,
  koyu,
}: {
  deger: T;
  degisti: (d: T) => void;
  secenekler: { deger: T; ad: React.ReactNode }[];
  etiket: string;
  koyu?: boolean;
}) {
  return (
    <ToggleGroup.Root
      type="single"
      value={deger}
      onValueChange={(d) => d && degisti(d as T)}
      aria-label={etiket}
      className={cn("inline-flex items-center gap-0.5 rounded-orta p-0.5", koyu ? "bg-black/25" : "bg-black/[0.05]")}
    >
      {secenekler.map((s) => (
        <ToggleGroup.Item
          key={s.deger}
          value={s.deger}
          className={cn(
            "inline-flex h-7 items-center gap-1.5 rounded-kucuk px-2.5 text-[12.5px] font-medium transition-colors [&_svg]:size-3.5",
            koyu
              ? "text-tuval-metin-2 hover:text-white data-[state=on]:bg-tuval-3 data-[state=on]:text-white data-[state=on]:shadow"
              : "text-metin-2 hover:text-metin data-[state=on]:bg-yuzey data-[state=on]:text-metin data-[state=on]:shadow-panel",
          )}
        >
          {s.ad}
        </ToggleGroup.Item>
      ))}
    </ToggleGroup.Root>
  );
}

/* ───────────────────────────── Açılır kutu */
export const Acilir = Popover.Root;
export const AcilirTetik = Popover.Trigger;
export const AcilirCapa = Popover.Anchor;
export function AcilirIcerik({ className, ...p }: React.ComponentProps<typeof Popover.Content>) {
  return (
    <Popover.Portal>
      <Popover.Content
        sideOffset={6}
        collisionPadding={12}
        className={cn("z-50 rounded-buyuk border border-cizgi bg-yuzey shadow-kalkik outline-none", className)}
        {...p}
      />
    </Popover.Portal>
  );
}

/* ───────────────────────────── Pencere ( sağdan çekmece ) */
export function Cekmece({
  acik,
  degisti,
  baslik,
  aciklama,
  children,
  genislik = "w-[560px]",
}: {
  acik: boolean;
  degisti: (a: boolean) => void;
  baslik: React.ReactNode;
  aciklama?: React.ReactNode;
  children: React.ReactNode;
  genislik?: string;
}) {
  return (
    <Dialog.Root open={acik} onOpenChange={degisti}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-metin/25" />
        <Dialog.Content
          className={cn(
            "fixed inset-y-2 right-2 z-50 flex max-w-[calc(100vw-16px)] flex-col overflow-hidden rounded-buyuk border border-cizgi bg-yuzey shadow-kalkik outline-none",
            genislik,
          )}
        >
          <div className="flex items-start justify-between gap-4 border-b border-cizgi px-5 py-4">
            <div>
              <Dialog.Title className="text-[15px] font-semibold">{baslik}</Dialog.Title>
              {aciklama && <Dialog.Description className="mt-0.5 text-[13px] text-metin-2">{aciklama}</Dialog.Description>}
            </div>
            <Dialog.Close asChild>
              <Dugme tur="hayalet" boy="simge-kucuk" aria-label="Kapat">
                <X />
              </Dugme>
            </Dialog.Close>
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

/* ───────────────────────────── Klavye tuşu */
export function Tus({ children }: { children: React.ReactNode }) {
  return (
    <kbd className="inline-flex h-5 min-w-5 items-center justify-center rounded border border-cizgi-2 bg-yuzey px-1 font-mono text-[11px] text-metin-2 shadow-[0_1px_0_var(--color-cizgi-2)]">
      {children}
    </kbd>
  );
}

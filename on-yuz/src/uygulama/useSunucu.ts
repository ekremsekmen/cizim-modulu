/*  ÇALIŞMA ALANININ SUNUCUYLA KONUŞMASI — tek yerde.
    Girdi değişince 300 ms sonra hesap ( /api/uygulama/coklu ) ve çizim
    ( /api/uygulama/cizimler ) istenir.  Kurallar:
      ·  Kural dışı girdi sunucuya gitmez;  ekran son geçerli girdinin sonucunu
         "güncel değil" diye gösterir.
      ·  Eski yanıt yenisini ezemez:  sorgu anahtarı isteğin kendisidir.
      ·  Hesap durur ya da bağlantı koparsa son BAŞARILI hesap ve çizim yerinde
         kalır, işaretlenir;  ilk başarılı yanıt işareti kaldırır.
      ·  Çizimde sorun varsa ( kural sağlanmıyor ) çizim yine gelir ve günceldir:
         sorunlar kartta, çizim "uygun değil" diye işaretli ( sunucu:
         cizim/sorunlu.py ).  Hesap dursa da çizim bu girdinindir.
      ·  Proje kimliği hesaba girmez ( değişince hesap tekrarlanmaz );  çizimin
         antetinde yazdığı için çizim isteğine girer.
      ·  Ölçü kutusu EKRANDAKİ çizimi üreten istekle konuşur:  son istek
         reddedildiyse çizim bir önceki girdinindir.                         */
import { useMemo, useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { api, type AlanSemasi, type CizimYanit, type CokluYanit, type UygulamaIstegi } from "@/lib/api";
import { formHatalari, istekKur, useGecikmeli, type FormHatasi, type Ham, type UygulamaProjesi } from "@/lib/proje";

/**  Büyük SVG yanıtları ( ~800 KB ) her tuşta önbellekte birikmesin  */
const ONBELLEK_MS = 30_000;

export type Sorun =
  | { tur: "kural"; maddeler: FormHatasi[] }
  | { tur: "baglanti"; ileti: string }
  /**  cizimGuncel:  ekrandaki çizim bu girdinin ( sorunlu da olsa )  */
  | { tur: "hesap" | "cizim"; maddeler: string[]; cizimGuncel: boolean };

export function useSunucu(
  sema: AlanSemasi,
  proje: UygulamaProjesi,
  ofis: Ham,
  asansor: number,
  cizimGerekli: boolean,
) {
  const hatalar = useMemo(() => formHatalari(sema, proje), [sema, proje]);
  //  Güncel istek ( kural dışı girdi varsa yok ) — teslim bununla iner
  const istek = useMemo<UygulamaIstegi | null>(
    () => (hatalar.length ? null : { ...istekKur(proje, ofis), kapak: proje.kimlik }),
    [hatalar.length, proje, ofis],
  );
  //  Son geçerli istek, gecikmeli ( kural dışı girdi beklenmez:  bkz. useGecikmeli )
  const gonderilen = useGecikmeli(istek, 300);
  const hesapIstegi = useMemo(() => {
    if (!gonderilen) return null;
    const { kapak: _kimlik, ...h } = gonderilen;
    return h;
  }, [gonderilen]);

  const hesap = useQuery({
    queryKey: ["hesap", hesapIstegi],
    queryFn: ({ signal }) => api.hesap(hesapIstegi!, signal),
    placeholderData: keepPreviousData,
    enabled: !!hesapIstegi,
    gcTime: ONBELLEK_MS,
  });
  const cizim = useQuery({
    queryKey: ["cizim", gonderilen, asansor],
    queryFn: ({ signal }) => api.cizimler(gonderilen!, asansor, signal),
    placeholderData: keepPreviousData,
    enabled: cizimGerekli && !!gonderilen,
    gcTime: ONBELLEK_MS,
  });

  //  Son BAŞARILI yanıtlar ( hata gelince ekran boşalmaz ).  React'in "önceki
  //  render'dan bilgi saklama" kalıbı:  yeni başarılı yanıt gelince render
  //  sırasında bir kez yazılır ( efekt ve fazladan çizim yok ).
  const [sonHesap, setSonHesap] = useState<CokluYanit>();
  if (hesap.data?.aktif && !hesap.isPlaceholderData && hesap.data !== sonHesap) setSonHesap(hesap.data);
  //  Sorunlu çizim de ( aktif değil ama çizimler geldi ) ekrana girer
  const [sonCizim, setSonCizim] = useState<{ yanit: CizimYanit; asansor: number; istek: UygulamaIstegi }>();
  if (cizim.data?.cizimler && !cizim.isPlaceholderData && gonderilen && cizim.data !== sonCizim?.yanit)
    setSonCizim({ yanit: cizim.data, asansor, istek: gonderilen });

  const hesapDurdu = !!hesap.data && !hesap.data.aktif;
  //  Girdi çizime hiç çevrilemedi ( eksik / geçersiz alan ) — sorunlu çizim değil
  const cizimKurulamadi = !!cizim.data && !cizim.data.aktif && !cizim.data.cizimler;
  const baglanti = hesap.error ?? cizim.error;
  //  Ekrandaki çizim son girdinin değil ( kural dışı girdi gönderilmedi, çizim
  //  kurulamadı, bağlantı yok ya da başka asansörün çizimi )
  const cizimEski = !!hatalar.length || cizimKurulamadi || !!cizim.error || sonCizim?.asansor !== asansor;
  //  Ekrandaki çizimin sorunları ( çizim yine gösterilir ) ve kurulamayan çizimleri
  const cizimSorunlari = useMemo(() => {
    const y = sonCizim?.yanit;
    if (cizimEski || !y || y.aktif) return [];
    return [...(y.hata ?? []), ...(y.kurulamayan ?? []).map((b) => `${b} bu girdilerle kurulamadı.`)];
  }, [cizimEski, sonCizim]);

  let sorun: Sorun | null = null;
  if (hatalar.length) sorun = { tur: "kural", maddeler: hatalar };
  else if (baglanti)
    sorun = { tur: "baglanti", ileti: `Sunucuya ulaşılamadı ( ${baglanti.message} ) — bağlantı gelince kendiliğinden güncellenir.` };
  else if (hesapDurdu)
    //  Hesabın durduğu sebep çoğu kez çizimin sorunuyla aynı metindir:  bir kez
    sorun = {
      tur: "hesap",
      maddeler: [...new Set([...(hesap.data?.hata ?? []), ...(cizimGerekli ? cizimSorunlari : [])])],
      cizimGuncel: cizimGerekli && !cizimEski,
    };
  else if (cizimGerekli && cizimKurulamadi) sorun = { tur: "cizim", maddeler: cizim.data?.hata ?? [], cizimGuncel: false };
  else if (cizimGerekli && cizimSorunlari.length) sorun = { tur: "cizim", maddeler: cizimSorunlari, cizimGuncel: true };

  //  Ekrandaki hükümler son girdinin mi?
  const hesapEski = !!hatalar.length || hesapDurdu || !!hesap.error;
  const cizimDurumu: "guncel" | "yukleniyor" | "eski" | "sorunlu" = cizimEski
    ? "eski"
    : cizim.isFetching || hesap.isFetching || (istek !== null && gonderilen !== istek)
      ? "yukleniyor"
      : cizimSorunlari.length
        ? "sorunlu"
        : "guncel";

  return {
    istek,
    hatalar,
    sonHesap,
    hesapEski,
    hesapYolda: hesap.isFetching,
    cizimler: sonCizim?.yanit.cizimler ?? [],
    cizimIstegi: sonCizim?.istek ?? null,
    cizimDurumu,
    /**  Ekrandaki ( güncel ) çizimin sorun sayısı — paket inmez  */
    cizimSorunSayisi: cizimSorunlari.length,
    sorun,
  };
}

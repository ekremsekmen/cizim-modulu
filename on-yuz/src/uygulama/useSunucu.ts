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
import {
  api,
  type AlanSemasi,
  type CizimSorunu,
  type CizimYanit,
  type CokluYanit,
  type OncekiGirdi,
  type UygulamaIstegi,
} from "@/lib/api";
import { formHatalari, istekKur, useGecikmeli, type FormHatasi, type Ham, type UygulamaProjesi } from "@/lib/proje";

/**  Büyük SVG yanıtları ( ~800 KB ) her tuşta önbellekte birikmesin  */
const ONBELLEK_MS = 30_000;

export type Sorun =
  | { tur: "kural"; maddeler: FormHatasi[] }
  | { tur: "baglanti"; ileti: string }
  /**  cizimGuncel:  ekrandaki çizim bu girdinin ( sorunlu da olsa );  maddelerin
       parçaları varsa çizimde işaretlenir  */
  | { tur: "hesap" | "cizim"; maddeler: CizimSorunu[]; cizimGuncel: boolean };

/**  Düz metin sorun ( hesabın iletisi, kurulamayan çizim ):  parçası yok  */
const duz = (metin: string): CizimSorunu => ({ metin, parcalar: [], cizim: null });

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

  //  Asansörün son TEMİZ çiziminin girdisi:  çare bulucu sorunun son değişiklikle
  //  çıkıp çıkmadığına buna bakar ( değişen kutuda sınır — uclar/care_uclari.py )
  //  Karşılaştırma nesnenin kendisiyle:  istekte o asansör yoksa ( asansör yeni
  //  eklendi, dosya açılıyor ) yazılmaz — her çizimde yeni boş nesne yazmak
  //  sonsuz yeniden çizime ( React #301 ) yol açıyordu
  const [sonTemiz, setSonTemiz] = useState<Record<number, OncekiGirdi>>({});
  const temizGirdi = gonderilen?.asansorler[asansor];
  if (cizim.data?.aktif && !cizim.isPlaceholderData && gonderilen && temizGirdi) {
    const e = sonTemiz[asansor];
    if (e?.asansor !== temizGirdi || e?.proje_geneli !== gonderilen.proje_geneli)
      setSonTemiz({ ...sonTemiz, [asansor]: { asansor: temizGirdi, proje_geneli: gonderilen.proje_geneli } });
  }

  //  ÇOK ASANSÖRDE BİRİ REDDEDİLİRSE yanıt yine aktiftir:  reddedilenin yalnız
  //  hata'sı gelir, bölümleri gelmez ( 22 Eki:  ikinci asansöre dar kuyu girilince
  //  ekran olmayan listeyi okuyup çöküyordu, düzelse de sebep görünmüyordu ).
  //  Seçili asansör reddedildiyse hesap onun için durmuştur;  teslim herhangi
  //  biri reddedilince kapanır ( sunucu da o paketi vermez ).
  const secili = hesap.data?.asansorler?.[asansor];
  const hesapDurdu = !!hesap.data && (!hesap.data.aktif || secili?.aktif === false);
  const durmaSebebi = hesap.data?.aktif ? (secili?.hata ?? []) : (hesap.data?.hata ?? []);
  const reddedilen = (hesap.data?.aktif ? (hesap.data.asansorler ?? []) : [])
    .map((x, i) => (x.aktif ? null : i))
    .filter((i): i is number => i !== null);
  //  Girdi çizime hiç çevrilemedi ( eksik / geçersiz alan ) — sorunlu çizim değil
  const cizimKurulamadi = !!cizim.data && !cizim.data.aktif && !cizim.data.cizimler;
  const baglanti = hesap.error ?? cizim.error;
  //  SUNUCU GERİ GELİNCE İSTEK KENDİLİĞİNDEN GİTMEZ:  yalnız tarayıcının kendi
  //  bağlantısı kopup gelince ( refetchOnReconnect ).  Sunucu yeniden başlayınca
  //  ya da ağ geçidi hata verince ekran, "kendiliğinden güncellenir" deyip girdi
  //  değişene kadar takılı kalıyordu ( 24 Eki ).
  const yenidenDene = () => {
    if (hesap.error) void hesap.refetch();
    if (cizim.error) void cizim.refetch();
  };
  //  Ekrandaki çizim son girdinin değil ( kural dışı girdi gönderilmedi, çizim
  //  kurulamadı, bağlantı yok ya da başka asansörün çizimi )
  const cizimEski = !!hatalar.length || cizimKurulamadi || !!cizim.error || sonCizim?.asansor !== asansor;
  //  Ekrandaki çizimin sorunları ( çizim yine gösterilir;  parçaları işaretlenir )
  //  ve kurulamayan çizimleri
  const cizimSorunlari = useMemo<CizimSorunu[]>(() => {
    const y = sonCizim?.yanit;
    if (cizimEski || !y || y.aktif) return [];
    return [
      ...(y.sorunlar ?? (y.hata ?? []).map(duz)),
      ...(y.kurulamayan ?? []).map((b) => duz(`${b} bu girdilerle kurulamadı.`)),
    ];
  }, [cizimEski, sonCizim]);

  const sorunluParcalar = useMemo(() => [...new Set(cizimSorunlari.flatMap((m) => m.parcalar))], [cizimSorunlari]);

  let sorun: Sorun | null = null;
  if (hatalar.length) sorun = { tur: "kural", maddeler: hatalar };
  else if (baglanti)
    sorun = { tur: "baglanti", ileti: `Sunucuya ulaşılamadı ( ${baglanti.message} ) — sunucu açılınca "Yeniden dene" ile güncellenir.` };
  else if (hesapDurdu) {
    //  Hesabın durduğu sebep çoğu kez çizimin sorunuyla aynı metindir:  bir kez
    //  ( çizimdekinin parçalarıyla )
    const cizimde = new Map((cizimGerekli ? cizimSorunlari : []).map((m) => [m.metin, m]));
    const hesaptaki = durmaSebebi.map((h) => cizimde.get(h) ?? duz(h));
    const metinler = new Set(hesaptaki.map((m) => m.metin));
    sorun = {
      tur: "hesap",
      maddeler: [...hesaptaki, ...[...cizimde.values()].filter((m) => !metinler.has(m.metin))],
      cizimGuncel: cizimGerekli && !cizimEski,
    };
  } else if (cizimGerekli && cizimKurulamadi)
    sorun = { tur: "cizim", maddeler: (cizim.data?.hata ?? []).map(duz), cizimGuncel: false };
  else if (cizimGerekli && cizimSorunlari.length) sorun = { tur: "cizim", maddeler: cizimSorunlari, cizimGuncel: true };

  //  Ekrandaki hükümler son girdinin mi?
  const hesapEski = !!hatalar.length || hesapDurdu || !!hesap.error;
  //  EKRANDAKİ ÇİZİM SON GİRDİNİN Mİ?  Hesap görünümünde çizim istenmez:  son
  //  çizim yanıtı eski girdinindir.  Onun sorunları teslimi kapatıyordu — sorun
  //  hesap görünümünde düzeltilse de ( 22 Eki ).  Teslim açılınca çizim istenir
  //  ( Calisma ), gelene kadar "denetleniyor".
  //  İçerikle karşılaştırılır:  aynı girdiden yeni bir istek nesnesi kurulur ( proje
  //  özeti yazılınca ) ve çizim önbellekten gelir — kimlikle karşılaştırınca teslim
  //  "denetleniyor"da kalıyordu.
  const sonCizimAnahtari = useMemo(() => (sonCizim ? JSON.stringify(sonCizim.istek) : null), [sonCizim]);
  const gonderilenAnahtari = useMemo(() => (gonderilen ? JSON.stringify(gonderilen) : null), [gonderilen]);
  const cizimSonGirdinin =
    !!gonderilenAnahtari && sonCizimAnahtari === gonderilenAnahtari && sonCizim?.asansor === asansor;
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
    cizimSorunSayisi: cizimSonGirdinin ? cizimSorunlari.length : 0,
    /**  Son girdinin çizimi henüz gelmedi ( teslim beklesin )  */
    cizimDenetleniyor: cizimGerekli && !cizimSonGirdinin && !hatalar.length && !cizimKurulamadi,
    /**  Hesaplanamayan asansörlerin sırası ( 0'dan ) — teslim kapalı  */
    reddedilen,
    /**  Ekrandaki ( güncel ) çizimin sorunlu parçaları ( data-ad ) — tuval kırmızı işaretler  */
    sorunluParcalar,
    /**  Bu asansörün son temiz çiziminin girdisi ( yoksa null )  */
    oncekiTemiz: sonTemiz[asansor] ?? null,
    sorun,
    /**  Düşen istekleri yeniden ister ( bağlantı sorunu )  */
    yenidenDene,
    yenidenDeneniyor: !!baglanti && (hesap.isFetching || cizim.isFetching),
  };
}

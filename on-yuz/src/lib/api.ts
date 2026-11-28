/*  SUNUCU SÖZLEŞMESİ
    Her ekran yalnız bu uçlardan beslenir;  arayüz kural / hesap üretmez.
      GET  /api/uygulama/alanlar      form şeması ( gruplar, kurallar, ofis standardı, tablolar )
      POST /api/uygulama/coklu        1 - 4 asansörün hesabı ( bölümler, hükümler )
      POST /api/uygulama/cizimler     seçili asansörün çizimleri ( sunucu SVG'si )
      POST /api/uygulama/olcu         tıklanan ölçünün kaynak girdileri
      POST /api/uygulama/olcu_degistir ölçüyü hedefe getiren girdi değişikliği
      POST /api/uygulama/parca        tıklanan parçayı belirleyen girdiler
      POST /api/indir/uygulama-pdf | uygulama-dwg   teslim
      GET  /api/secenekler · POST /api/trafik · /api/avan · /api/indir/…   avan      */

export type AlanTuru = "sayi" | "secim" | "metin" | "onay";
export type AlanKaynagi = "GİRDİ" | "KURAL" | "KATALOG" | "ÇİZİM";
export type Deger = string | number | boolean | null;

export interface Alan {
  anahtar: string;
  etiket: string;
  birim: string;
  tur: AlanTuru;
  secenekler: (string | number)[] | null;
  varsayilan: Deger;
  gelismis: boolean;
  bilgi: string;
  secenek_metni: Record<string, string> | null;
  kaynak: AlanKaynagi;
  secenek_kosulu: Record<string, { yerlesim: string; sebep: string }> | null;
}

export interface Grup {
  ad: string;
  alanlar: Alan[];
}

/**  Sınırı olmayan yön null gelir ( kaçıklıklar eksi olabilir:  en_az null )  */
export interface Kural {
  en_az?: number | null;
  en_az_dahil?: boolean;
  en_cok?: number | null;
  tam_sayi?: boolean;
  /**  Olağan aralık ( sunucu:  tasarim/alanlar.OLAGAN — 28 Kas ):  REDDETMEZ, dışındaki değeri
       ekran "olağan dışı" diye sorar;  null:  aralık yok  */
  olagan_alt?: number | null;
  olagan_ust?: number | null;
}

export interface Tablo {
  ad: string;
  kaynak: string;
  aciklama: string;
  basliklar: string[];
  satirlar: (string | number | null)[][];
}

export interface AlanSemasi {
  gruplar: Grup[];
  bolum_grubu: Record<string, string[]>;
  hesaplanan: string[];
  kurallar: Record<string, Kural>;
  /**  Boş metni "tablodan al" demek olan alanlar ( gönderilmeyen = varsayılan;  boş = tablo )  */
  bos_tablodan: string[];
  /**  Eskiden onay kutusu olan seçimler:  [ işaretsiz , işaretli ] — eski dosyanın true / false'u  */
  eski_onay: Record<string, [string, string]>;
  proje_geneli: string[];
  yerlesime_gore_gizli: { mrl: string[]; daireli: string[] };
  /**  Kat girişinin kipi:  alan doluysa kotla;  her kipte öbürünün alanları gizli ( sunucu okumaz )  */
  kot_kipi: { alan: string; gizli: { kotla: string[]; olcuyle: string[] } };
  /**  Kuyu düzeni:  alan "tek" iken ( yalnız iki asansörlü projede ) iki asansör tek
       kuyudadır — ortak alanlar iki asansörde aynı ( sunucu 1. asansörünkini okur ),
       gizli alanlar ( soldaki asansör, ayırma kirişi ) yalnız o zaman okunur.  */
  kuyu_duzeni: { alan: string; tek: string; ortak: string[]; gizli: string[] };
  /**  Yalnız yandaki ağırlıkta ( yan ) okunan alanlar ( yalniz_yan ):  ağırlık arkadayken gizli  */
  agirlik_yeri?: { alan: string; yan: string[]; yalniz_yan: string[] };
  cizimden: string[];
  ortak_kopru: { mukavemet: string; anahtar: string; avan: string }[];
  sabitler: {
    varsayilan: Record<string, Deger>;
    metin: string[];
    gruplar: { baslik: string; aciklama: string; alanlar: string[] }[];
    etiket: Record<string, string[]>;
  };
  tablolar: Tablo[];
  asansor_azami: number;
}

export interface Adim {
  sembol: string;
  aciklama: string;
  deger: Deger;
  birim: string;
  kaynak: string;
  formul: string;
  islem: string;
  tip: string;
  metin: string;
  vurgu: boolean;
}

export interface Sonuc {
  baslik: string;
  metin: string;
  uygun: boolean | null;
  alt?: string[];
  /**  Uygun değilse düşen sınırlar:  neden ( değerleriyle ) ve öneri ( bölümde yazılıysa ) —
       metnin yapılı okuması;  yoksa ( elektrik bölümleri ) ekran metni gösterir  */
  maddeler?: { neden: string; oneri: string | null }[];
  /**  Hükümsüz bölümün sayıları ( kuyu tabanı yükleri ):  ad, anlamı, değeri, birimi sunucudan  */
  degerler?: { ad: string; aciklama: string; deger: number; metin: string; birim: string }[];
}

export interface Bolum {
  baslik: string;
  kaynak: string;
  adimlar: Adim[];
  /**  Hükümsüz bölümde YOK ( null:  topraklayıcılar, iletkenler — 25 Eki:  tip hep var
       sayıyordu, temel ölçüleri girilince Uygunluk paneli çöküyordu )  */
  sonuc: Sonuc | null;
  notlar: string[];
  aciklamalar: string[];
  kimlik: string;
  ad: string;
  sira: number;
}

/**  Bir asansörün sonucu.  Çok asansörlü projede biri reddedilirse yanıtın
     kendisi yine aktiftir;  reddedilenin yalnız aktif:false, no, tanim, girdi
     ve hata'sı gelir — bölüm, uyarı ve özeti YOKTUR ( 22 Eki:  ikinci asansöre
     dar kuyu girilince ön yüz olmayan listeyi okuyup çöküyordu ).  */
export interface AsansorSonucu {
  aktif: boolean;
  no: number;
  tanim: string;
  girdi?: Record<string, Deger>;
  hata?: string[];
  bolumler?: Bolum[];
  uyarilar?: string[];
  ozet?: Record<string, unknown>;
  /**  Elektrik projesinin değerleri ( avan_hesabi._elektrik_projesi );  elektrik
       hesabı yapılamadıysa yok — pakette o asansörün elektrik projesi olmaz  */
  elektrik?: Record<string, unknown> | null;
}

/**  Hesabın genel hükmü — motor kurar ( uygulama_hesabi · avan_hesabi · trafik
     .proje_hukmu ), uç yanıta ekler, ekran basar  */
export interface ProjeHukmu {
  /**  durdu:  hesaplanamayan asansör / adım ( hüküm kurulmaz );  eksik:  yapılamayan zorunlu hesap  */
  durum: "durdu" | "eksik" | "uygun_degil" | "uygun";
  /**  "Uygun değil" bölüm sayısı ( proje geneli dahil )  */
  uygun_degil: number;
}

export interface CokluYanit {
  aktif: boolean;
  hata?: string[];
  asansorler?: AsansorSonucu[];
  proje_geneli?: Bolum[];
  proje_hukmu?: ProjeHukmu;
  ozet?: {
    adet: number;
    tumu_uygun: boolean;
    /**  Hesaplanamayan ( reddedilen ) asansörün hükmü ve genel sonucu null  */
    asansorler: {
      no: number;
      tanim: string;
      aktif: boolean;
      tumu_uygun: boolean | null;
      genel_sonuc: string | null;
    }[];
  };
}

import type { KapiBilgisi } from "@/lib/kapiTasima";

export interface Cizim {
  ad: string;
  baslik: string;
  /**  Çizim şeridindeki adı ( sunucu:  cizimler.KISA_ADLAR — 20 Kas, B7 );  yoksa başlıktan  */
  kisa?: string | null;
  olcek: number;
  olceksiz: boolean;
  svg: string;
  /**  Makine dairesi kapısının yeri ( kapının çizildiği planlarda ) — sürüklemek için  */
  kapi?: KapiBilgisi;
}

/**  Çizimin bir sorunu ( sunucu:  cizim/sorun.py ) — parçalar çizimdeki adlarıyla
     ( SVG'nin data-ad'ı ), cizim:  sorunun en iyi görüldüğü çizim  */
export interface CizimSorunu {
  metin: string;
  parcalar: string[];
  cizim: string | null;
}

/**  Bir sorunun doğrulanmış çaresi ( sunucu:  uclar/care_uclari.py ) — uygulanıp
     hesap ve çizim yeniden kurularak sınanmıştır  */
export interface CareOnerisi {
  anahtar: string;
  etiket: string;
  /**  Bugünkü etkin değer ( boş kutuda kuralın / varsayılanın değeri;  seçimde metin )  */
  eski: number | string | null;
  girilmis: boolean;
  yeni: number | string;
  /**  Bu değişiklikle giden sorunlar ( metinleri )  */
  gider: string[];
  /**  Bu değişiklikten sonra görünür olacak sorunlar:  bugün de var ama denetim
       ilk hatada durduğu için gizli ( yeni sorun DEĞİL )  */
  ortaya_cikan: string[];
  /**  Bu değişiklikten sonra hesapta uygun olmayan çıkacak bölümler ( bugün uygun görünen — kimlikleri )  */
  hesapta_ortaya_cikan: string[];
  bina: boolean;
  yontem: "türev" | "son değişiklik" | "seçim" | "tarama";
}

export interface CareYanit {
  aktif: boolean;
  careler?: { metin: string; oneriler: CareOnerisi[] }[];
  /**  Yapılan sınama ( hesap + çizim yeniden kurulumu ) — bütçe saat değil, sayıdır  */
  sinama?: number;
  /**  false:  arama bütçeye ( neden "sinama" ) ya da güvenlik süresine ( "sure" )
       takıldı — çareler eksik olabilir  */
  tamamlandi?: boolean;
  neden?: "sinama" | "sure" | null;
  sure?: number;
  hata?: string[];
}

/**  Son temiz girdi ( son değişikliğin sınırı için ):  asansörün girdisi ve proje geneli  */
export interface OncekiGirdi {
  asansor: Record<string, string>;
  proje_geneli: Record<string, string>;
}

/**  aktif:  çizim uygun.  Aktif değilse hata sebebidir;  çizimler de geldiyse
     çizim SORUNLU kuruldu ( ekranda gösterilir, paket inmez ), gelmediyse girdi
     çizime hiç çevrilemedi.  */
export interface CizimYanit {
  aktif: boolean;
  cizimler?: Cizim[];
  hata?: string[];
  /**  Sorunlu girdiyle kurulamayan çizimlerin başlıkları  */
  kurulamayan?: string[];
  /**  hata'nın yapılı hâli ( sorunlu çizimde )  */
  sorunlar?: CizimSorunu[];
  /**  Hesabın uygun bulmadığı bölümlerin parçaları ( bölüm kimliği → data-ad;
       sunucu:  cizim/hesap_isareti.py ) — tuval turuncu işaretler  */
  hesap_parcalari?: Record<string, string[]>;
  /**  Çizimi DURDURMAYAN notlar ( sunucu:  cizim_uclari.cizim_notlari ) — 27 Kas:  kuyu dibinde
       sabit merdivene yer yok, hangi merdivenin seçileceği ( paftada VERİLER'in NOTLAR'ında da )  */
  notlar?: string[];
}

/**  Avan asansörünün çizimleri ( sunucu:  uclar/avan_cizim_uclari.py ).  Seçici mimarın
     kuyusuna asansörü bulduysa ( uygun ) çizimler;  bulamadıysa çizim yoktur:
     gereken — mimardan istenecek ölçüler, sigmaz — sebepler, eksik — girilmemiş
     mimari alanlar, paket_yok — bu yük için hazır asansör yok, hata — girdi okunamadı,
     beyan — avan kartının askı oranı / makine tipiyle asansör kurulamadı ( çizim hesap
     sayfasıyla çelişmesin diye kartınkini kullanır ) ya da kartın kabini standarda uymuyor;
     kartta seçilecek değerler.
     tamamlanmadi — arama güvenlik süresinde bitmedi ( neden "sure" ) ya da istek bırakıldı
     ( "iptal" ):  sonuç bilinmiyor, "sığmaz" değildir;  hata'da sebebi ( 16 Kas ).  */
export interface AvanCizimYaniti {
  durum: "uygun" | "gereken" | "sigmaz" | "eksik" | "paket_yok" | "beyan" | "hata" | "tamamlanmadi";
  neden?: "sure" | "iptal";
  /**  kart:  avan kartının alanı;  yeni:  karta yazılacak değer;  *_yazi:  ekrandaki yazımı  */
  /**  yer "trafik":  öneri avan kartına değil trafik hesabının sütununa yazılır ( kapı )  */
  beyan?: { kart: string; etiket: string; yeni: string; eski_yazi: string; yeni_yazi: string; yer?: "trafik" }[];
  /**  "kabin":  kartın kabini standarda uymuyor ( nedenler'de sebebi;  öneri hazır asansörün
       kabini );  "kapi":  trafik hesabının kapısıyla kurulamadı ( yoksa askı / makine tipi )  */
  beyan_turu?: "kabin" | "kapi";
  hata?: string;
  eksik?: string[];
  /**  paket_yok + hiz:  bu hızda avan çizimi çıkmaz ( uygulamanın hız listesinde yok );
       hizlar:  çizimin çıktığı hızlar ( m/s )  */
  hiz?: boolean;
  hizlar?: number[];
  /**  Çizimde elle ayarlanan ölçüler ( kartın cizim_ayarlari'sı ), ekrandaki adlarıyla  */
  ayarlar?: { anahtar: string; etiket: string; deger: string; birim: string }[];
  gereken?: { anahtar: string; etiket: string; eski: string | null; yeni: string; sebep: string }[];
  nedenler?: string[];
  /**  "gereken" / "sigmaz":  sonucun yerleşimi ( "ağırlık yanda" | "ağırlık arkada" ) ve denenip
       kullanılmayan yerleşimin mimarın ölçülerindeki sorunları ( 27 Kas )  */
  yerlesim?: string;
  denenen?: { yerlesim: string; nedenler: string[] }[];
  /**  Kullanılmayan yerleşim de ölçü istiyorsa onun isteği ( "ya da …" — 27 Kas, seçici doğruluk K3 )  */
  /**  kosul_yazi:  kartın değeri kalırsa ( beyan sonucunda — "Askı oranı 2:1" )  */
  secenek?: {
    yerlesim: string;
    gereken: { anahtar: string; etiket: string; eski: string | null; yeni: string }[];
    kosul_yazi?: string;
  }[];
  /**  Geçirilemeyen ürün bölümleri ( avanı bağlamaz — uygulama projesinde çözülür )  */
  acik_bolumler?: string[];
  acik_bolum_adlari?: string[];
  /**  Sürüklenen makine dairesi kapısı bırakıldığı yere konamadı ( sebepleri ):  çizim eski
       kapısıyla — ekran söyler, kartın ayarını kaldırır  */
  kapi_reddi?: string[];
  cizim?: CizimYanit;
  /**  "uygun"da seçicinin kurduğu uygulama isteği — tıklanan ölçünün kaynağı bununla sorulur  */
  istek?: UygulamaIstegi;
  sure?: number;
}

export interface OlcuKaynagi {
  anahtar: string;
  tur: string;
  deger: number;
  egim: number;
  etiket: string;
  birim: string;
  yer: "asansor" | "proje" | "ofis" | string;
  degistirilir: boolean;
  /**  Kotla girişte durağın kotu kaynaksa durağın sırası ( 0 = en alt ) — anahtar durak_kotlari  */
  durak?: number;
}

export interface OlcuYanit {
  aktif: boolean;
  metin?: string;
  deger?: number;
  kural?: string | null;
  kaynaklar?: OlcuKaynagi[];
  /**  Tek kuyunun birleşik çiziminde ölçünün asansörü ve onun çizimindeki yeri:
       değiştirme bununla istenir, değişiklik o asansöre yazılır  */
  kendi?: { asansor: number; cizim: string; olcu: number; metin: string };
  hata?: string[];
}

/**  Parçayı belirleyen bir girdi — ölçü kaynağının biçimi;  etki:  parçanın ölçüsünü mü
     yalnız yerini mi değiştirir.  Seçim ( uzunluk seçimi ) seçenekleriyle gelir.  */
export interface ParcaGirdisi {
  anahtar: string;
  etiket: string;
  birim: string;
  deger: number | string;
  egim: number;
  yer: "asansor" | "proje" | "ofis" | string;
  degistirilir: boolean;
  etki: "boyut" | "yer";
  secenekler?: (string | number)[];
  /**  Kotla girişte durağın kotu ( anahtar durak_kotlari )  */
  durak?: number;
}

export interface ParcaYanit {
  aktif: boolean;
  parca?: string;
  ad?: string;
  girdiler?: ParcaGirdisi[];
  /**  Listenin sınırı ( sunucunun cümlesi )  */
  not?: string;
  hata?: string[];
}

export interface OlcuDegisikligi {
  aktif: boolean;
  degisiklikler?: { anahtar: string; etiket: string; eski: number; deger: number }[];
  olcu?: number;
  dogrulandi?: boolean;
  uyarilar?: string[];
  /**  Değişikliğin dokunmadığı ama kuralla yer değiştiren parça ( boş kutulu regülatör )  */
  notlar?: string[];
  hata?: string[];
}

/**  Uygulama isteği:  ham metinler ( sunucu okur, doğrular, reddeder ).
     kapak:  proje kimliği — çizimin antetinde ve indirilen dosyanın adında;
     hesaba girmez ( bu yüzden hesap isteğinde yok, değişince hesap tekrarlanmaz ).  */
export interface UygulamaIstegi {
  asansorler: Record<string, string>[];
  proje_geneli: Record<string, string>;
  sabitler: Record<string, string>;
  kapak?: { project_title: string; owner: string; sheet_no: string };
}

/* ───────────────────────────── avan */
export interface Secenekler {
  bina_tipleri: string[];
  hizli_etiketleri: Record<string, { hizli1: [string, string]; hizli2: [string, string] }>;
  kapasiteler: number[];
  hizlar: number[];
  kapi_genislikleri: number[];
  kapi_tipleri: string[];
  nufus_kalemleri: string[];
  tablo_1: Record<string, { birim: string; katsayi: number }>;
  makine_tipleri: Record<string, number>;
  aski_oranlari: Record<string, number>;
  kesitler: number[];
  tablo_7: Record<string, number>;
  /**  Tablo-10:  bina tipinin %k satırı ( k_tipi null:  Tablo-9'da yok, manuel k zorunlu )  */
  tablo_10?: Record<string, { k_tipi: string | null }>;
  kapak_turetilen: string[];
  ofis_varsayilan: Record<string, Deger>;
  sabit_b: Record<string, Deger>;
  /**  Avan ofis standardının formu ( gruplar · etiketler · varsayılanlar )  */
  sabit_sema: AvanSabitSemasi;
}

export interface AvanSabitSemasi {
  gruplar: { baslik: string; aciklama: string; alanlar: string[] }[];
  etiket: Record<string, [string, string]>;
  varsayilan: Record<string, Deger>;
  metin: string[];
}

export interface AvanKoprusu {
  tip: string;
  N: number;
  bodrum: number;
  h: number;
  adet: number;
  /**  kapi_*:  trafik hesabının kapısı ( avan çizimi onu kullanır );  sutun:  trafik sütunu
       ( 0'dan — tek tipte null:  bütün sütunlar aynı kapıdır )  */
  asansorler: {
    P: number;
    V: number;
    toplam_seyahat: number;
    kapi_genisligi?: number | null;
    kapi_tipi?: string | null;
    sutun?: number | null;
    /**  Asansörün kendi kat düzeni ( çoklu trafikte ):  giriş üstü kat ve bodrum durağı  */
    N?: number | null;
    bodrum?: number | null;
    /**  HİZMET ARALIĞI ( kot tablosu doluyken ):  binanın tablosundaki en alt / en üst durağın
         ve giriş katının sırası ( 1'den ), durak sayısı, seyir ( m ) — kartın kotları bu dilimdir  */
    kat?: KatDuzeni;
  }[];
}

/**  Kot tablosundan türeyen kat düzeni ( sunucu:  cizim/katlar.kat_duzeni )  */
export interface KatDuzeni {
  N: number;
  bodrum: number;
  durak: number;
  seyir: number;
  giris: number;
  alt: number;
  ust: number;
}

export interface TrafikYaniti {
  hata: string | null;
  /**  Kat düzeni kot tablosundan türediyse ( binanın durak kotları — avan_uclari._kat_duzeni ):
       N, bodrum durağı, ortalama kat yüksekliği h ( m ), durak sayısı, seyir ( m ), giriş katının sırası  */
  kat_duzeni?: KatDuzeni & {
    h: number;
    /**  Sütun sırasıyla ( sira:  ekrandaki numara ) her asansörün kendi düzeni — hizmet aralığı  */
    asansorler?: (KatDuzeni & { h: number; sira: number })[];
  };
  uyarilar?: string[];
  bolumler?: Bolum[];
  ozet?: {
    bina_tipi: string;
    standart: string;
    B: number;
    TR: number;
    R: number;
    Ieer: number;
    Izul: number;
    adet: number;
    sonuc_cumlesi: string;
    karar_olcutleri?: { ad: string; metin: string; uygun: boolean }[];
  } | null;
  oneriler?: { secenek: string; adet: number; Ieer: number; erisilebilir: boolean }[];
  avan_koprusu?: AvanKoprusu | null;
  kapak_bilgileri?: Record<string, string>;
  proje_hukmu?: ProjeHukmu;
}

/**  Bina hesabı ( makine dairesi aydınlatması, topraklama ):  uygulanmıyorsa
     ya da girdi eksikse aktif:false ve sebebi uyari'da.  */
export interface AvanBinaHesabi {
  aktif: boolean;
  uyari?: string;
  bolumler?: Bolum[];
}

/**  Avan kartının kotlarından türeyenler ( sunucu:  avan_cizimi.kot_bilgisi ) — ekran
     hesaplamaz.  Uzunluklar m;  doseme mm.  Kot girilmemişse yalnız hata / adlar / doseme.  */
export interface AvanKotBilgisi {
  Hk?: number | null;
  seyir?: number | null;
  durak?: number | null;
  kuyu_dibi?: number | null;
  ust_bosluk?: number | null;
  hata: string[];
  adlar: Record<string, unknown>;
  /**  Tavan döşemesinin kalınlığı:  kartta girilen, boşsa kuraldan ( doseme_kural )  */
  doseme: number;
  doseme_kural: number;
  /**  Çizimin kabini ( mm ):  kartınki — boş olan ya da standarda uymayan kartta hazır
       asansörünki;  bu yük için hazır asansör yoksa null  */
  kabin: { kabin_boyu: number; kabin_genisligi: number } | null;
}

export interface AvanYaniti {
  hata?: string;
  /**  Asansör sırasıyla ( kartı olmayan null )  */
  kotlar?: (AvanKotBilgisi | null)[];
  asansorler?: { no: number; aktif: boolean; tanim?: string; uyari?: string; bolumler?: Bolum[] }[];
  makine_dairesi?: AvanBinaHesabi;
  topraklama?: AvanBinaHesabi;
  uyarilar?: string[];
  engelleyici?: string[];
  kapak_bilgileri?: Record<string, string>;
  proje_hukmu?: ProjeHukmu;
  /**  Proje paketini durduran eksik hesaplar ( sunucu:  avan_hesabi.teslim_eksikleri — 18 Kas ):
       girdisi tamamlanmamış asansör, yapılamayan topraklama, makine dairesi varken aydınlatması  */
  teslim_eksikleri?: string[];
}

/* ───────────────────────────── istekler */
async function al<T>(yol: string): Promise<T> {
  const r = await fetch(yol);
  if (!r.ok) throw new Error(`Sunucu yanıt vermedi ( ${r.status} )`);
  return r.json();
}

/**  RET İLETİSİNİN BİÇİMİ ucun biçimine eşitlenir:  uygulama uçları iletileri
     listeyle ( {"aktif":false,"hata":[…]} ), avan uçları tek metinle verir;
     boyut sınırı ( 413, main.py IstekBoyutu ) ve bilinmeyen adres ( 404 ) uçtan
     habersizdir.  24 Eki:  avan isteği boyut sınırına takılınca liste gelen
     iletiye .trim() çağrılıyor, avan ekranı çöküyordu;  uygulama ucunda metin
     gelse .map() çökerdi.  Ekranlar ucun biçimine güvenir:  eşitleme ekranlarda
     değil, burada ( indirme uçlarınınki indir'de ).  */
const hataListe = (h: unknown) => (h == null ? h : (Array.isArray(h) ? h : [h]).map(String));
const hataMetin = (h: unknown) => (h == null ? h : Array.isArray(h) ? h.map(String).join("\n") : String(h));

/**  POST:  sunucu reddederken de çoğu zaman JSON döner ( 413 istek çok büyük:
     {"aktif":false,"hata":[…]} ) — o metin ekranda görünsün diye yanıt olarak
     verilir ( hata'sı ucun biçiminde:  liste / metin ).  JSON olmayan hata
     ( vekil, çökme ) ve bağlantı kopması fırlatır:  sorgu hata durumuna geçer,
     ekran "güncel değil" der.  */
async function gonder<T>(yol: string, govde: unknown, bicim: (h: unknown) => unknown, sinyal?: AbortSignal): Promise<T> {
  const r = await fetch(yol, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(govde),
    signal: sinyal,
  });
  if (!r.ok && !(r.headers.get("Content-Type") || "").includes("application/json"))
    throw new Error(`Sunucu yanıt vermedi ( ${r.status} )`);
  const j = await r.json();
  return j && typeof j === "object" && "hata" in j ? { ...j, hata: bicim(j.hata) } : j;
}

/**  Uzun işin aşamaları ( sunucu:  cizim/asamalar.Ilerleme — 17 Kas avan araması;  20 Kas paketler ve
     düzeltme ):  iş sürerken gerçekten hangi adımda olduğu.  t:  aşamanın başladığı an ( sn, isteğin
     başından ).  plan:  adımları baştan belli işte ( paket ) sıradaki adımlar  */
export interface AramaIlerlemesi {
  asamalar: { kod: string; surer: string; bitti: string; ayrinti: string; t: number }[];
  sinama: number;
  gecen: number;
  plan?: { kod: string; surer: string; bitti: string }[];
}

/**  Akışlı yanıtın tamponundan tamamlanmış satırlar ve kalan ( yarım satır )  */
export function satirlariAyir(tampon: string): [string[], string] {
  const parcalar = tampon.split("\n");
  const kalan = parcalar.pop() ?? "";
  return [parcalar.map((s) => s.trim()).filter(Boolean), kalan];
}

/**  AKIŞLI İSTEK ( 17 Kas — /api/avan/cizimler ):  sunucu satır satır yazar — aramanın aşamaları
     ( { ilerleme } ), en sonda sonuç ( { sonuc } ).  Sunucu akış vermezse ( hata yanıtı ) tek JSON
     okunur, gonder gibi.  Sonuç gelmeden akış biterse hata ( yarıda kesildi ).

     XMLHttpRequest ile ( fetch'in gövde okuyucusuyla değil ):  Chromium adım adım okunan uzun
     akışı veri tam gelse de "kesildi" ( ERR_ABORTED ) sayıyordu — uçtan uca testin izleyicisi
     sonucu görmüyordu.  XHR'nin ilerleme olayında yanıt metni geldikçe büyür, istek olağan biter.  */
function akisla<T>(
  yol: string,
  govde: unknown,
  bicim: (h: unknown) => unknown,
  sinyal?: AbortSignal,
  ilerle?: (d: AramaIlerlemesi) => void,
): Promise<T> {
  const bicimle = (j: unknown) =>
    (j && typeof j === "object" && "hata" in j ? { ...j, hata: bicim((j as { hata: unknown }).hata) } : j) as T;
  return new Promise<T>((coz, reddet) => {
    if (sinyal?.aborted) return reddet(sinyal.reason ?? new DOMException("Aborted", "AbortError"));
    const x = new XMLHttpRequest();
    let okunan = 0;
    let sonuc: unknown;
    let geldi = false;
    const akisMi = () => (x.getResponseHeader("Content-Type") || "").includes("application/x-ndjson");
    //  Tamamlanmış satırlar ( okunan:  işlenen metnin sonu );  son:  yarım satır da okunur
    const isle = (son: boolean) => {
      const metin = x.responseText.slice(okunan);
      const [satirlar, kalan] = satirlariAyir(son ? metin + "\n" : metin);
      okunan = x.responseText.length - kalan.length;
      for (const s of satirlar) {
        const d = JSON.parse(s) as { sonuc?: unknown; ilerleme?: AramaIlerlemesi };
        if ("sonuc" in d) {
          sonuc = d.sonuc;
          geldi = true;
        } else if (d.ilerleme) ilerle?.(d.ilerleme);
      }
    };
    const birak = () => x.abort();
    sinyal?.addEventListener("abort", birak, { once: true });
    const bitir = () => sinyal?.removeEventListener("abort", birak);
    x.open("POST", yol);
    x.setRequestHeader("Content-Type", "application/json");
    x.setRequestHeader("Accept", "application/x-ndjson");
    x.onprogress = () => {
      if (!akisMi()) return;
      try {
        isle(false);
      } catch {
        /*  bozuk satır:  yükleme bitince hata olarak döner  */
      }
    };
    x.onload = () => {
      bitir();
      try {
        if (!akisMi()) {
          const tur = x.getResponseHeader("Content-Type") || "";
          if (x.status >= 400 && !tur.includes("application/json")) throw new Error(`Sunucu yanıt vermedi ( ${x.status} )`);
          return coz(bicimle(JSON.parse(x.responseText)));
        }
        isle(true);
        if (!geldi) throw new Error("Sunucunun yanıtı yarıda kesildi");
        coz(bicimle(sonuc));
      } catch (e) {
        reddet(e);
      }
    };
    x.onerror = () => {
      bitir();
      reddet(new TypeError("Failed to fetch"));
    };
    x.onabort = () => {
      bitir();
      reddet(sinyal?.reason ?? new DOMException("Aborted", "AbortError"));
    };
    x.send(JSON.stringify(govde));
  });
}

export const api = {
  alanlar: () => al<AlanSemasi>("/api/uygulama/alanlar"),
  hesap: (i: UygulamaIstegi, s?: AbortSignal) => gonder<CokluYanit>("/api/uygulama/coklu", i, hataListe, s),
  cizimler: (i: UygulamaIstegi, asansor: number, s?: AbortSignal) =>
    gonder<CizimYanit>("/api/uygulama/cizimler", { ...i, asansor }, hataListe, s),
  /**  ilerle:  aramanın aşamaları geldikçe ( akışlı yanıt — 20 Kas );  sinyal:  Vazgeç  */
  care: (
    i: UygulamaIstegi,
    asansor: number,
    onceki: OncekiGirdi | null,
    s?: AbortSignal,
    ilerle?: (d: AramaIlerlemesi) => void,
  ) => akisla<CareYanit>("/api/uygulama/care", { ...i, asansor, onceki }, hataListe, s, ilerle),
  olcu: (i: UygulamaIstegi, asansor: number, cizim: string, olcu: number, metin: string) =>
    gonder<OlcuYanit>("/api/uygulama/olcu", { ...i, asansor, cizim, olcu, metin }, hataListe),
  olcuDegistir: (
    i: UygulamaIstegi,
    asansor: number,
    cizim: string,
    olcu: number,
    metin: string,
    anahtar: string,
    hedef: string,
  ) => gonder<OlcuDegisikligi>("/api/uygulama/olcu_degistir", { ...i, asansor, cizim, olcu, metin, anahtar, hedef }, hataListe),
  /**  secimler:  seçim kutularının etkisi de ( sunucu her birini dener — saniyeler ).  O arama akışlı
       ( 20 Kas — arayüz taslağı B10 ):  denenen kutu ilerle'ye gelir;  sinyal isteği bırakır  */
  parca: (
    i: UygulamaIstegi,
    asansor: number,
    cizim: string,
    parca: string,
    secimler = false,
    s?: AbortSignal,
    ilerle?: (d: AramaIlerlemesi) => void,
  ) =>
    secimler
      ? akisla<ParcaYanit>("/api/uygulama/parca", { ...i, asansor, cizim, parca, secimler }, hataListe, s, ilerle)
      : gonder<ParcaYanit>("/api/uygulama/parca", { ...i, asansor, cizim, parca, secimler }, hataListe, s),
  secenekler: () => al<Secenekler>("/api/secenekler"),
  trafik: (girdiler: unknown, s?: AbortSignal) => gonder<TrafikYaniti>("/api/trafik", { girdiler }, hataMetin, s),
  avan: (girdiler: unknown, s?: AbortSignal) => gonder<AvanYaniti>("/api/avan", { girdiler }, hataMetin, s),
  /**  Paketin şimdi arama yapacağı asansörler ( sunucu arama yapmaz — anında;  17 Kas )  */
  avanAranacaklar: (girdiler: unknown) =>
    gonder<{ aranacaklar: number[] }>("/api/avan/aranacaklar", { girdiler }, hataMetin),
  /**  ilerle:  seçicinin aşamaları geldikçe ( akışlı yanıt )  */
  avanCizimleri: (girdiler: unknown, asansor: number, s?: AbortSignal, ilerle?: (d: AramaIlerlemesi) => void) =>
    akisla<AvanCizimYaniti>("/api/avan/cizimler", { girdiler, asansor }, hataMetin, s, ilerle),
};

export interface IndirmeSonucu {
  hata?: string;
  /**  Kullanıcı vazgeçti ( akışlı indirme ):  dosya inmedi, hata değil  */
  iptal?: boolean;
  /**  Paketin notları ( X-Avan-Not ):  DXF — DWG çevrilemedi, ZIP'te DXF var;
       TASMA — paftalar formatın çerçevesine sığmadı, baskıdan önce bakılmalı.  */
  notlar?: string[];
}

/**  İndirme uçları dosya döndürür;  sunucu reddederse JSON hata gelir.
     HİÇ FIRLATMAZ:  düğmeler yalnız dönen hatayı gösterir.  24 Eki:  dosya inerken
     bağlantı kopunca ( blob reddi ) düğme sessizce eski hâline dönüyordu — dosya
     yok, ileti yok.  */
export async function indir(uc: string, govde: unknown): Promise<IndirmeSonucu> {
  let r: Response;
  try {
    r = await fetch(`/api/indir/${uc}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(govde),
    });
  } catch {
    return { hata: "Sunucuya ulaşılamadı — bağlantıyı denetleyip yeniden deneyin." };
  }
  if ((r.headers.get("Content-Type") || "").includes("application/json")) {
    let j: { hata?: unknown };
    try {
      j = await r.json();
    } catch {
      return { hata: `Sunucunun yanıtı okunamadı ( ${r.status} ) — yeniden deneyin.` };
    }
    return { hata: Array.isArray(j.hata) ? j.hata.join("\n") : String(j.hata ?? "Üretilemedi") };
  }
  if (!r.ok) return { hata: `Sunucu yanıt vermedi ( ${r.status} )` };
  let veri: Blob;
  try {
    veri = await r.blob();
  } catch {
    return { hata: "Dosya inerken bağlantı koptu — dosya inmedi;  yeniden deneyin." };
  }
  const ad = /filename\*?=(?:UTF-8'')?"?([^";]+)/i.exec(r.headers.get("Content-Disposition") || "")?.[1];
  dosyayiKaydet(veri, indirilenAd(ad, uc));
  const notlar = (r.headers.get("X-Avan-Not") || "").split(",").filter(Boolean);
  return notlar.length ? { notlar } : {};
}

function dosyayiKaydet(veri: Blob, ad: string) {
  const url = URL.createObjectURL(veri);
  const a = Object.assign(document.createElement("a"), { href: url, download: ad });
  document.body.appendChild(a);
  a.click();
  a.remove();
  //  Hemen geri alınırsa bazı tarayıcılar indirmeyi başlatmadan keser
  setTimeout(() => URL.revokeObjectURL(url), 3000);
}

/**  AKIŞLI İNDİRME ( 20 Kas — arayüz taslağı B1 · B2:  paket 4 asansörde 10,4 sn, avanda arama
     paketin içinde;  ekranda yalnız dönen işaret vardı ):  sunucu paketin adımlarını akıtır
     ( ilerle ), sonda dosya — { dosya:  { ad , tur , veri ( base64 ) } , notlar } ( sunucu:
     uc_ortak.akis_sonucu ) ya da bugünkü hata yanıtı.  indir gibi HİÇ FIRLATMAZ;  vazgeçilince
     ( sinyal ) { iptal } — sunucu bir sonraki adımda durur.  */
export async function indirAkisli(
  uc: string,
  govde: unknown,
  sinyal?: AbortSignal,
  ilerle?: (d: AramaIlerlemesi) => void,
): Promise<IndirmeSonucu> {
  let sonuc: unknown;
  try {
    sonuc = await akisla<unknown>(`/api/indir/${uc}`, govde, (h) => h, sinyal, ilerle);
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") return { iptal: true };
    if (e instanceof TypeError) return { hata: "Sunucuya ulaşılamadı — bağlantıyı denetleyip yeniden deneyin." };
    if (e instanceof SyntaxError) return { hata: "Sunucunun yanıtı okunamadı — yeniden deneyin." };
    const ileti = e instanceof Error ? e.message : String(e);
    //  Sonuç satırı gelmeden akış bitti ( akisla:  "yarıda kesildi" )
    if (/yarıda/.test(ileti)) return { hata: "Paket inerken bağlantı koptu — dosya inmedi;  yeniden deneyin." };
    return { hata: `${ileti} — yeniden deneyin.` };
  }
  const d = akisDosyasi(sonuc, uc);
  if (!d.blob) return { hata: d.hata };
  dosyayiKaydet(d.blob, d.ad);
  return d.notlar.length ? { notlar: d.notlar } : {};
}

/**  Akışın son satırındaki sonuç:  dosya ( Blob , ad , notlar ) ya da hata metni ( ucun biçimi:
     liste / metin — indir'deki gibi tek metne )  */
export function akisDosyasi(
  sonuc: unknown,
  yedekAd: string,
): { blob: Blob; ad: string; notlar: string[] } | { blob?: undefined; hata: string } {
  const s = (sonuc && typeof sonuc === "object" ? sonuc : {}) as {
    dosya?: { ad?: string; tur?: string; veri?: string };
    notlar?: unknown;
    hata?: unknown;
  };
  if (!s.dosya?.veri) {
    const h = s.hata;
    return { hata: Array.isArray(h) ? h.map(String).join("\n") : String(h ?? "Üretilemedi") };
  }
  let bayt: Uint8Array<ArrayBuffer>;
  try {
    bayt = base64Bayt(s.dosya.veri);
  } catch {
    return { hata: "Sunucunun yanıtı okunamadı — yeniden deneyin." };
  }
  return {
    blob: new Blob([bayt], { type: s.dosya.tur || "application/octet-stream" }),
    ad: s.dosya.ad || yedekAd,
    notlar: Array.isArray(s.notlar) ? s.notlar.map(String) : [],
  };
}

/**  base64 → bayt ( akışlı indirmenin dosyası )  */
export function base64Bayt(veri: string): Uint8Array<ArrayBuffer> {
  const ikili = atob(veri);
  const b = new Uint8Array(ikili.length);
  for (let i = 0; i < ikili.length; i++) b[i] = ikili.charCodeAt(i);
  return b;
}

/**  Content-Disposition'daki ad;  kodlaması bozuksa olduğu gibi ( decodeURIComponent fırlatır )  */
function indirilenAd(ad: string | undefined, yedek: string): string {
  try {
    return decodeURIComponent(ad || yedek);
  } catch {
    return ad || yedek;
  }
}

/**  Paket notlarının Türkçesi ( eski arayüzle aynı anlamlar ).  */
export function paketNotu(not: string): string {
  //  DXF bir eksiklik değildir:  çizim yalnız çizgi ve yazıdır, AutoCAD DXF'i birebir açar
  if (not === "DXF") return "ZIP'te çizim DXF olarak var;  AutoCAD birebir açar ( DWG isterseniz açıp Farklı Kaydet ).";
  if (not === "TASMA") return "Pafta sayısı proje formatının çerçevesine sığmadı, alta taşan sayfalar var — baskıdan önce bakın.";
  if (not === "CIZIM")
    return "Bazı asansörlerin çizimi pakette yok — hangileri ve neden, ZIP'teki “ÇİZİMİ OLMAYAN ASANSÖRLER.txt” dosyasında ve Çizimler adımında yazıyor.";
  return not;
}

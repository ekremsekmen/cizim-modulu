/*  ÖRNEK PROJE — gerçekte var olan bir asansör ( 19 Eki, kullanıcı:  "her şeyi
    doğru bir örnek proje, gerçekte var olan" ).
    Kaynak:  ölçü formundan çıkarılan uygulama projesi ( MRL dişlisiz, 1275 kg,
    1,6 m/s, 15 durak, 42 m;  cikti/projeler/BAR 2515 — git dışı ).  Yalnız
    teknik değerler:  bina ve işveren bilgisi yok ( program webde yayınlanır ).
    Bugünkü programda 15 bölümün 14'ü uygun, biri bilgi ( kuyu tabanı yükleri,
    hükümsüz );  çizimler kurulur ( testler/test_on_yuz_uctan_uca.py ).
    Yazılmayan alan varsayılandır ( Teleskopik Sol kapı, 2:1, kabin altı … );
    boş kabin kütlesi tablodan ( bos_tablodan:  "" gönderilir ).
    Değerler değişirse ORNEK_SURUMU artar:  tarayıcıdaki eski örnek yenilenir.  */
import type { Ham } from "./proje";

export const ORNEK_SURUMU = 2;

export const ORNEK_ASANSOR: Ham = {
  beyan_yuku: "1275",
  beyan_hizi: "1.6",
  agirlik_yeri: "Sol",
  kuyu_genisligi: "2200",
  kuyu_derinligi: "2700",
  durak_adedi: "15",
  seyir_mesafesi: "42",
  son_kat_yuksekligi: "4250",
  kuyu_dibi: "1750",
  kabin_genisligi: "1260",
  kabin_derinligi: "2100",
  kapi_genisligi: "1100",
  kabin_yana_kaciklik: "30",
  kabin_ic_yuksekligi: "2100",
  kabin_agirligi: "",
  ray_kapi_arasi: "1370",
  kabin_konsol_arasi: "1800",
  agirlik_konsol_arasi: "1800",
  kabin_ray_arasi: "1550",
  agirlik_derinligi: "100",
  agirlik_malzemesi: "Pik Döküm",
  agirlik_ray_arasi: "1100",
  halat_capi: "8",
  kabin_kasnak_capi: "320",
  kanal_isleme: "Sertleştirilmiş",
  denge_zinciri: "Var",
  motor_gucu: "12,5",
  tahrik_kasnak_capi: "320",
  tampon_tipi: "Hidrolik  ( enerji yutmalı )",
  kabin_tampon_boyu: "630",
  kabin_tampon_ezilme: "180",
  agirlik_tampon_ezilme: "180",
};

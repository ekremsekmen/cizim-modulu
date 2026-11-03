/*  TASLAK PROJELER ( 3 Kas, kullanıcı:  "her şeyi uygun tertemiz projeler taslak halinde
    olsun, kullanıcı birine tıklayıp devam edebilsin" ) — açılışın sağında, son projelerin
    üstünde.  Hepsi makine dairesiz, 1,0 m/s, 6 durak ( ±0,00 … +15,00 ).
    Ölçülerin kaynağı ( sayı uydurulmaz ):  630 · 800 · 1000 kabini ve kapısı ISO 4190 /
    TS EN 81-20 Çizelge 6;  1250 ofisin gerçek projesi;  1275 örnek projenin gerçek
    asansörü ( BAR 2515 ).  Kuyu ve öbür girdiler formun kuralı;  motor IEC 60072 güçlerinin
    hesabı karşılayan en küçüğü, raylar hesabı geçen en hafif profil.  MRL makinesinin ince
    halatı onaylanmış kuruluş belgesiyle ( 1275:  8 mm, 320 kasnak — belgesiz ).
    UYGUNLUK GÜVENCESİ:  testler/test_taslaklar.py — hesabın her bölümü uygun, çizim
    temiz, kalite kapısı 0;  taslaklar.json o testle birlikte değişir ( pytest de okur ).
    Tıklanınca YENİ proje olarak açılır:  taslağın kendisi değişmez.                 */
import liste from "./taslaklar.json";
import { yeniUygulama, type Ham, type UygulamaProjesi } from "./proje";

export interface Taslak {
  kimlik: string;
  ad: string;
  ozet: string;
  kaynak: string;
  asansor: Ham;
  proje_geneli: Ham;
}

//  JSON'un çıkarılan tipi alanları taslak taslak ayırır ( isteğe bağlı = undefined ):  hepsi metin
export const TASLAKLAR = liste as unknown as Taslak[];
export const TASLAK_DUZENI = "Makine dairesiz · 1,0 m/s · 6 durak";

/**  Taslaktan yeni proje ( tarayıcıya yazılır );  bilinmeyen taslakta null.  */
export function taslaktanProje(kimlik: string): UygulamaProjesi | null {
  const t = TASLAKLAR.find((x) => x.kimlik === kimlik);
  if (!t) return null;
  return yeniUygulama(false, {
    kimlik: { project_title: `${t.ad} ( taslak )`, owner: "", sheet_no: "" },
    asansorler: [{ ...t.asansor }],
    proje_geneli: { ...t.proje_geneli },
    kapak: {},
  });
}

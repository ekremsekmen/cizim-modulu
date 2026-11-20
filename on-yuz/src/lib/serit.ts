/*  ÇİZİM ŞERİDİ — tuvalin altındaki çizim düğmeleri ( 20 Kas — yayın öncesi arayüz taslağı B7 ).

    1440 px ekranda şerit 768 px;  düğmeler onu eşit paylaştığı için 11 çizimin hepsinin adı
    kesiliyordu ( "D-D kabi…", "K…" ).  Ad başlıktan türetiliyordu:  sorunlu kipte kesitler
    kurulamayınca seviye harfi düşer, üç düğme "Kuyu" oluyordu.  Artık ad sunucudan ( çizimin
    değişmeyen kimliğiyle — cizim/cizimler.py KISA_ADLAR ), düğme adı kadar geniş;  sığmayanlar
    sırayla "Diğer" kutusuna iner.  Açık çizim hep şeritte.  */

/**  Başlığın parantezden önceki kısmı:  düğmenin erişilebilir adı ( "MAKİNE DAİRESİ PLANI" ) —
     uçtan uca testler çizimi bununla açar  */
export function baslikAdi(baslik: string): string {
  return baslik.split("(")[0].trim();
}

const HARF = /^[A-ZÇĞİÖŞÜ]-[A-ZÇĞİÖŞÜ]$/;

/**  Başlıktaki seviye harfi ( "KUYU PLANI  C-C" → "C-C" );  yoksa null  */
export function seviyeHarfi(baslik: string): string | null {
  return baslikAdi(baslik).split(/\s+/).find((x) => HARF.test(x)) ?? null;
}

/**  Şeritte görünen ad:  sunucunun kısa adı;  vermediyse başlıktan ( harfsiz, cümle düzeninde )  */
export function seritAdi(c: { baslik: string; kisa?: string | null }): string {
  if (c.kisa) return c.kisa;
  const sozler = baslikAdi(c.baslik)
    .split(/\s+/)
    .filter((x) => x && !HARF.test(x));
  const k = sozler.join(" ").replace(/I/g, "ı").replace(/İ/g, "i").toLowerCase();
  return k.charAt(0).replace("i", "İ").replace("ı", "I").toUpperCase() + k.slice(1);
}

/**  Şeride sığanlar.  enler:  çizim düğmelerinin genişliği ( aralık dahil ), sırayla;  diger:
     "Diğer" düğmesininki;  alan:  çizim düğmelerine kalan genişlik;  aktif:  açık çizimin sırası
     ( yoksa -1 ).  Hepsi sığarsa hepsi;  sığmazsa baştan sığanlar ve "Diğer" — açık çizim
     sığanlardan değilse onlardan birinin yerine geçer ( yer önce ona ayrılır ).  Alan açık çizime
     de yetmezse yine o görünür ( düğme daralır ).  Sıra hep çizimlerin sırası.  */
export function seritYerlesimi(
  enler: number[],
  diger: number,
  alan: number,
  aktif = -1,
): { gorunen: number[]; gizli: number[] } {
  const hepsi = enler.map((_e, i) => i);
  if (enler.reduce((a, b) => a + b, 0) <= alan) return { gorunen: hepsi, gizli: [] };
  const kalan = alan - diger;
  const secilen = new Set<number>();
  let dolu = 0;
  if (aktif >= 0 && aktif < enler.length) {
    secilen.add(aktif);
    dolu = enler[aktif];
  }
  for (const i of hepsi) {
    if (i === aktif) continue;
    if (dolu + enler[i] > kalan) break;
    secilen.add(i);
    dolu += enler[i];
  }
  return { gorunen: hepsi.filter((i) => secilen.has(i)), gizli: hepsi.filter((i) => !secilen.has(i)) };
}

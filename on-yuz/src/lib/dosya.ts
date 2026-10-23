/*  PROJE DOSYASI ( .uygulama ) — ESKİ ARAYÜZÜN BİÇİMİ ( 19 Eki kaldırıldı ).
    Biçim değişmedi:  eski arayüzde kaydedilmiş bütün dosyalar açılır;  yenide
    kaydedilen dosya ( ve paketin içindeki .uygulama ) aynı biçimdedir:

      { __mod, __surum, __program, __tarih,
        alanlar: { mk_proje_adi, mk_isveren, mk_pafta_no, m_adet,
                   m_<anahtar>    binaya ait alanlar ( onay:  true / false ),
                   uof_<anahtar>  ofis standardı ( eski arayüz projeyle saklar ),
                   __muk_asansorler: [ { <anahtar>: değer } ],  __muk_aktif, __muk_adet } }

    Asansör haritasında OLMAYAN alan iki arayüzde de varsayılandır ( sunucu
    sözleşmesi:  gönderilmeyen alan = varsayılanı gönderilmiş alan;
    testler/test_on_yuz_sozlesmesi.py ).                                   */
import type { AlanSemasi, Deger } from "./api";
import { avanDosyasiMi } from "./avan";
import { eskiOnayIsaretli, evetMi } from "./denetim";
import { sayiOku, type Ham, type UygulamaProjesi } from "./proje";

/**  Eski arayüzün PROJE_SURUM'u — iki taraf aynı sürümü yazar.  */
const SURUM = 1;

function onayAlanlari(sema: AlanSemasi): Set<string> {
  return new Set(sema.gruplar.flatMap((g) => g.alanlar).filter((a) => a.tur === "onay").map((a) => a.anahtar));
}

/**  Dosyaya yazılacak değer:  onay alanı eski arayüzde onay kutusudur ( boolean ).  */
function disa(onay: Set<string>, k: string, v: string): string | boolean {
  return onay.has(k) ? v === "true" : v;
}

export function dosyaGovdesi(p: UygulamaProjesi, sema: AlanSemasi, ofis: Ham) {
  const onay = onayAlanlari(sema);
  const alanlar: Record<string, unknown> = {
    __mod: "uygulama",
    __surum: SURUM,
    mk_proje_adi: p.kimlik.project_title,
    mk_isveren: p.kimlik.owner,
    mk_pafta_no: p.kimlik.sheet_no,
    m_adet: String(p.asansorler.length),
  };
  for (const [k, v] of Object.entries(p.proje_geneli)) alanlar[`m_${k}`] = disa(onay, k, v);
  for (const [k, v] of Object.entries(ofis)) if (String(v).trim() !== "") alanlar[`uof_${k}`] = v;
  alanlar.__muk_asansorler = p.asansorler.map((h) =>
    Object.fromEntries(Object.entries(h).map(([k, v]) => [k, disa(onay, k, v)])),
  );
  alanlar.__muk_aktif = 0;
  alanlar.__muk_adet = p.asansorler.length;
  //  Kapak sayfası:  eski arayüzde kapak formu avan bölümündedir;  "__" ile
  //  başlayan anahtarı okumaz, yeni arayüz geri okur
  if (p.kapak && Object.keys(p.kapak).length) alanlar.__yeni_kapak = p.kapak;
  return {
    __mod: "uygulama",
    __surum: SURUM,
    __program: "Asansör Proje Programı",
    __tarih: new Date().toISOString().slice(0, 10),
    alanlar,
  };
}

export function dosyaAdi(p: UygulamaProjesi): string {
  const ad = (p.kimlik.project_title || "Asansor").replace(/[^\p{L}\p{N} _-]/gu, "").trim().slice(0, 48);
  return `${ad || "Asansor"}.uygulama`;
}

export function dosyayaKaydet(p: UygulamaProjesi, sema: AlanSemasi, ofis: Ham) {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(dosyaGovdesi(p, sema, ofis), null, 1)], { type: "application/json" }),
  );
  const a = Object.assign(document.createElement("a"), { href: url, download: dosyaAdi(p) });
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 3000);
}

/* ───────────────────────────── okuma */
export type DosyaOkumasi =
  | {
      tamam: true;
      icerik: Pick<UygulamaProjesi, "kimlik" | "asansorler" | "proje_geneli" | "kapak">;
      /**  Dosyadaki ofis standardının bu tarayıcınınkinden farklı değerleri  */
      ofisFarki: string[];
      taninmayan: string[];
    }
  | { tamam: false; hata: string };

/**  Dosyadaki değer şemanın varsayılanıyla aynıysa YAZILMAMIŞ sayılır:  eski
     arayüz kutuyu varsayılanla doldurduğu için kullanıcının girdiğini ayırt
     edemez;  aynı değer hesapta da aynıdır ( sözleşme ).  */
function ayniDeger(a: string, v: Deger): boolean {
  if (v === null || v === undefined) return a === "";
  if (typeof v === "boolean") return (a === "true") === v;
  const na = sayiOku(a);
  return typeof v === "number" && na !== null ? na === v : a === String(v);
}

function ice(v: unknown): string | null {
  if (typeof v === "boolean") return v ? "true" : "false";
  if (typeof v === "number") return String(v);
  if (typeof v === "string") return v.trim() === "" ? null : v;
  return null;
}

/**  Uygulama kısmına avan dosyası verilince ( avan ekranındaki karşılığı lib/avan.ts )  */
export const AVAN_DOSYASI_UYGULAMADA =
  "Bu bir avan projesi dosyası — avan ekranından ya da açılış sayfasından açın.";

export function dosyaOku(metin: string, sema: AlanSemasi, ofis: Ham): DosyaOkumasi {
  let d: Record<string, unknown>;
  try {
    d = JSON.parse(metin);
  } catch {
    return { tamam: false, hata: "Dosya okunamadı — geçerli bir proje dosyası değil." };
  }
  if (!d || typeof d !== "object") return { tamam: false, hata: "Dosya okunamadı — geçerli bir proje dosyası değil." };
  //  Eski biçim ( başlıksız düz girdi sözlüğü ) da okunur
  const govde = (d.alanlar && typeof d.alanlar === "object" ? d.alanlar : d) as Record<string, unknown>;
  const mod = (d.__mod ?? govde.__mod) as string | undefined;
  //  Başlıksız eski avan dosyası da ( c_ / a_ … anahtarları ) uygulama sanılmaz
  if (avanDosyasiMi(d)) return { tamam: false, hata: AVAN_DOSYASI_UYGULAMADA };
  if (mod && mod !== "uygulama") return { tamam: false, hata: "Tanınmayan proje dosyası." };

  const alanlar = new Map(sema.gruplar.flatMap((g) => g.alanlar).map((a) => [a.anahtar, a]));
  const taninmayan: string[] = [];
  const oku = (k: string, ham: unknown, hedef: Ham) => {
    const a = alanlar.get(k);
    //  Boş kutu bu alanlarda "tablodan" demektir:  boş olarak taşınır ( gönderilmezse varsayılan olurdu )
    if (a && sema.bos_tablodan.includes(k) && typeof ham === "string" && ham.trim() === "") {
      hedef[k] = "";
      return;
    }
    let v = ice(ham);
    if (!a || v === null) return;
    //  Onay kutusu sunucunun okuduğu gibi:  eski dosyada "EVET" / "HAYIR" de durur —
    //  olduğu gibi kalsa ekran "HAYIR"ı işaretli, sunucu işaretsiz okurdu
    if (a.tur === "onay") v = String(evetMi(v));
    if (a.secenekler) {
      //  Seçim listedeki yazımıyla saklanır:  eski dosyada "1,6" durur, seçenek "1.6"dır —
      //  olduğu gibi kalsa kutu boş görünürdü ( hesap yine 1,6 ile yapılırken )
      let s = a.secenekler.find((x) => String(x) === v || sayiOku(v!) === x);
      //  ESKİDEN ONAY KUTUSU ( eski_onay:  [ işaretsiz , işaretli ] ):  true / false
      //  sunucunun okuduğu seçeneğe çevrilir — 24 Eki:  varsayılana dönüyordu,
      //  işaretsiz makine yükü yolu ( bina yapısına ) "Kılavuz raylara" oluyordu
      const eski = sema.eski_onay[k];
      if (s === undefined && eski && (typeof ham === "boolean" || typeof ham === "string"))
        s = eski[eskiOnayIsaretli(v, eski[1]) ? 1 : 0];
      if (s === undefined) {
        taninmayan.push(`${a.etiket.split("(")[0].trim()} = ${v}`);
        return;
      }
      v = String(s);
    }
    if (!ayniDeger(v, a.varsayilan)) hedef[k] = v;
  };

  const proje_geneli: Ham = {};
  for (const k of sema.proje_geneli) if (govde[`m_${k}`] !== undefined) oku(k, govde[`m_${k}`], proje_geneli);

  const dizi = Array.isArray(govde.__muk_asansorler) ? (govde.__muk_asansorler as Record<string, unknown>[]) : [];
  const adet = Math.min(Math.max(1, Number(govde.__muk_adet) || dizi.length || 1), sema.asansor_azami);
  const asansorler: Ham[] = [];
  for (let i = 0; i < adet; i++) {
    const h: Ham = {};
    const kaynak = dizi[i] && typeof dizi[i] === "object" ? dizi[i] : i === 0 ? null : {};
    if (kaynak) {
      for (const [k, v] of Object.entries(kaynak)) if (!sema.proje_geneli.includes(k)) oku(k, v, h);
    } else {
      //  Tek asansörlü çok eski dosya:  alanlar formun kimlikleriyle ( m_<anahtar> )
      for (const k of alanlar.keys()) if (!sema.proje_geneli.includes(k) && govde[`m_${k}`] !== undefined) oku(k, govde[`m_${k}`], h);
    }
    asansorler.push(h);
  }

  //  Boş kutu = varsayılan;  karşılaştırma etkin değerle ( "130" ile boş aynıdır )
  const ofisFarki = Object.keys(sema.sabitler.varsayilan).filter((k) => {
    const v = sema.sabitler.varsayilan[k];
    const etkin = (x: string | null) => (x === null || x.trim() === "" ? String(v ?? "") : x.trim());
    const a = etkin(ice(govde[`uof_${k}`]));
    const b = etkin(ofis[k] ?? null);
    const na = sayiOku(a);
    const nb = sayiOku(b);
    return na !== null && nb !== null ? na !== nb : a !== b;
  });

  const metinAl = (k: string) => (typeof govde[k] === "string" ? (govde[k] as string) : "");
  return {
    tamam: true,
    icerik: {
      kimlik: { project_title: metinAl("mk_proje_adi"), owner: metinAl("mk_isveren"), sheet_no: metinAl("mk_pafta_no") },
      asansorler,
      proje_geneli,
      kapak:
        govde.__yeni_kapak && typeof govde.__yeni_kapak === "object"
          ? Object.fromEntries(
              Object.entries(govde.__yeni_kapak as Record<string, unknown>).filter(
                (e): e is [string, string] => typeof e[1] === "string",
              ),
            )
          : {},
    },
    ofisFarki,
    taninmayan,
  };
}

/*  Testlerin küçük form şeması — sunucunun /api/uygulama/alanlar biçiminde,
    yalnız testlerin dokunduğu alanlarla.  Avanın seçenekleri ( SECENEKLER ) ve
    tohumlu rastgele sayı da burada.                                          */
import type { Alan, AlanSemasi, Secenekler } from "./api";

/*  Seçenekler /api/secenekler'in testlerin kullandığı alt kümesidir;  listeler
    sunucununkiyle aynı ( 18 Eki ), sabit şeması birkaç sabite kısaltıldı.  */
export const SECENEKLER = {
  bina_tipleri: ["Konut", "Kamu Binaları", "Katlı Otopark"],
  hizlar: [0.63, 1, 1.6, 1.75, 2, 2.5, 3, 3.5, 5, 6],
  kapasiteler: [6, 8, 10, 13, 15, 16, 20, 25, 30],
  kapi_genislikleri: [700, 800, 900, 1000, 1100, 1200, 1300],
  kapi_tipleri: ["Teleskopik Otomatik", "Merkezden Açılan Oto.", "Kabin İçi Oto. Kat K.Ç."],
  makine_tipleri: { Dişlisiz: 0.85, Dişli: 0.5 },
  aski_oranlari: { "1:1": 1, "2:1": 2 },
  kesitler: [1.5, 2.5, 4, 6, 10, 16],
  nufus_kalemleri: ["KONUT — İlk yatak odası", "KONUT — Diğer oda"],
  ofis_varsayilan: { U: 380, S1: 6, kablo_tipi: "NHXMH FE180" },
  sabit_b: { q_denge: 0.5 },
  sabit_sema: {
    gruplar: [{ baslik: "①", aciklama: "", alanlar: ["q_denge", "U", "S1", "kablo_tipi"] }],
    etiket: {
      q_denge: ["q — Denge faktörü", ""],
      U: ["U — Şebeke gerilimi (V)", ""],
      S1: ["S1 — Kolon hattı kesiti (mm²)", ""],
      kablo_tipi: ["Kablo tipi", ""],
    },
    varsayilan: { q_denge: 0.5, U: 380, S1: 6, kablo_tipi: "NHXMH FE180" },
    metin: ["kablo_tipi"],
  },
} as unknown as Secenekler;

/**  Tohumlu rastgele sayı ( mulberry32 ):  kırılan durum tohumundan yeniden üretilir  */
export function rastgele(tohum: number) {
  let t = tohum >>> 0;
  const r = () => {
    t = (t + 0x6d2b79f5) >>> 0;
    let x = Math.imul(t ^ (t >>> 15), 1 | t);
    x = (x + Math.imul(x ^ (x >>> 7), 61 | x)) ^ x;
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  };
  return {
    tam: (n: number) => Math.floor(r() * n),
    sec: <T>(l: readonly T[]): T => l[Math.floor(r() * l.length)],
    olasi: (p: number) => r() < p,
  };
}

/**  Kaç tohum denenir:  RASTGELE_TOHUM ortam değişkeniyle büyütülür ( av sırasında )  */
export const TOHUM_SAYISI = Number(
  (globalThis as { process?: { env: Record<string, string | undefined> } }).process?.env.RASTGELE_TOHUM ?? 300,
);

const alan = (a: Partial<Alan> & Pick<Alan, "anahtar" | "tur">): Alan => ({
  etiket: a.anahtar,
  birim: "—",
  secenekler: null,
  varsayilan: null,
  gelismis: false,
  bilgi: "",
  secenek_metni: null,
  kaynak: "GİRDİ",
  secenek_kosulu: null,
  ...a,
});

export const SEMA: AlanSemasi = {
  gruplar: [
    {
      ad: "Asansör ve düzen",
      alanlar: [
        alan({ anahtar: "asansor_adi", tur: "metin" }),
        alan({ anahtar: "beyan_yuku", tur: "secim", secenekler: [630, 800, 1000], varsayilan: 800, birim: "kg" }),
        alan({ anahtar: "mk_yok", tur: "onay", varsayilan: true }),
        alan({
          anahtar: "aski_orani",
          tur: "secim",
          secenekler: [1, 2],
          varsayilan: 2,
          secenek_metni: { "1": "1:1", "2": "2:1" },
          //  Sunucunun koşulu:  1:1 YALNIZ makine dairelide ( tasarim/alanlar.py )
          secenek_kosulu: { "1": { yerlesim: "daireli", sebep: "Makine dairesizde 1:1 askı kullanılmaz" } },
        }),
        //  Eskiden onay kutusuydu ( şemanın eski_onay'ı )
        alan({
          anahtar: "makine_raya_biniyor",
          tur: "secim",
          secenekler: ["Bina yapısına", "Kılavuz raylara"],
          varsayilan: "Kılavuz raylara",
        }),
      ],
    },
    {
      ad: "Kuyu ve katlar",
      alanlar: [
        alan({ anahtar: "kuyu_genisligi", tur: "sayi", varsayilan: 2400, birim: "mm" }),
        alan({ anahtar: "durak_adedi", tur: "sayi", varsayilan: 8 }),
      ],
    },
    {
      ad: "Kabin ve kapı",
      alanlar: [alan({ anahtar: "kabin_agirligi", tur: "sayi", birim: "kg", kaynak: "KATALOG" })],
    },
    {
      ad: "Makine dairesi",
      alanlar: [alan({ anahtar: "mk_uzunluk", tur: "sayi", birim: "mm", gelismis: true })],
    },
  ],
  bolum_grubu: {},
  hesaplanan: [],
  kurallar: {
    kuyu_genisligi: { en_az: 0, en_az_dahil: true, en_cok: 20000 },
    durak_adedi: { en_az: 0, en_az_dahil: true, en_cok: 100, tam_sayi: true },
    mk_uzunluk: { en_az: 0, en_az_dahil: false, en_cok: 20000 },
    //  sunucunun biçimi:  alt sınırı olmayan alanda en_az null
    kabin_yana_kaciklik: { en_az: null, en_az_dahil: true, en_cok: 20000, tam_sayi: false },
  },
  bos_tablodan: ["kabin_agirligi"],
  eski_onay: { makine_raya_biniyor: ["Bina yapısına", "Kılavuz raylara"] },
  proje_geneli: ["mk_yok", "mk_uzunluk"],
  yerlesime_gore_gizli: { mrl: ["mk_uzunluk"], daireli: [] },
  cizimden: [],
  ortak_kopru: [],
  sabitler: { varsayilan: { sigma_em: 130, kablo_tipi: "NHXMH FE180" }, metin: ["kablo_tipi"], gruplar: [], etiket: {} },
  tablolar: [],
  asansor_azami: 4,
};

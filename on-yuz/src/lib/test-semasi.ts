/*  Testlerin küçük form şeması — sunucunun /api/uygulama/alanlar biçiminde,
    yalnız testlerin dokunduğu alanlarla.                                    */
import type { Alan, AlanSemasi } from "./api";

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
        alan({ anahtar: "aski_orani", tur: "secim", secenekler: [1, 2], varsayilan: 2, secenek_metni: { "1": "1:1", "2": "2:1" } }),
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
  },
  proje_geneli: ["mk_yok", "mk_uzunluk"],
  yerlesime_gore_gizli: { mrl: ["mk_uzunluk"], daireli: [] },
  cizimden: [],
  ortak_kopru: [],
  sabitler: { varsayilan: { sigma_em: 130, kablo_tipi: "NHXMH FE180" }, metin: ["kablo_tipi"], gruplar: [], etiket: {} },
  tablolar: [],
  asansor_azami: 4,
};

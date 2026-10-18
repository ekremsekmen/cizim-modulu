/*  KAPAK ALANLARI — sunucunun kapak çizicisinin anahtarları ( ciktilar/kapak_cikti ),
    eski arayüzün kapak formuyla aynı sıra ve adlar.  Avan kapağı ve uygulama
    paketinin kapak sayfası ( kapak_sayfasi ) aynı alanları kullanır.
    Asansör satırları avan hesabından türetilir ( /api/secenekler kapak_turetilen ):
    boş bırakılırsa hesabınki yazılır.                                        */
export interface KapakGrubu {
  baslik: string;
  alanlar: [anahtar: string, etiket: string][];
}

export const KAPAK_GRUPLARI: KapakGrubu[] = [
  { baslik: "Kapak", alanlar: [["project_title", "Kapak başlığı"]] },
  {
    baslik: "Yapı ve arsa",
    alanlar: [
      ["owner", "Yapı sahibi / işveren"],
      ["usage", "Yapı kullanım amacı"],
      ["contractor", "Müteahhit"],
      ["contractor_tax", "Müteahhit vergi no"],
      ["city", "İl"],
      ["district", "İlçe"],
      ["neighborhood", "Mahalle"],
      ["area", "Alan ( m² )"],
      ["sheet_no", "Pafta no"],
      ["island_no", "Ada no"],
      ["parcel_no", "Parsel no"],
    ],
  },
  {
    baslik: "Asansör",
    alanlar: [
      ["block", "Blok"],
      ["capacity", "Kapasite"],
      ["speed", "Hız"],
      ["stops", "Durak sayısı"],
      ["travel", "Seyir mesafesi"],
      ["standard", "Standart"],
      ["cabin_width", "Kabin genişliği"],
      ["cabin_depth", "Kabin derinliği"],
      ["elevator_class", "Asansör sınıfı"],
      ["suspension", "Askı tipi"],
      ["elevator_count", "Asansör adedi"],
      ["drive_type", "Tahrik tipi"],
      ["rail_size", "Ray ölçüsü"],
      ["motor_power", "Motor gücü"],
      ["scale", "Ölçek"],
    ],
  },
  {
    baslik: "Makine mühendisi",
    alanlar: [
      ["mech_name", "Adı"],
      ["mech_surname", "Soyadı"],
      ["mech_registry", "Sicil no"],
      ["mech_chamber", "Oda sicil no"],
      ["mech_tax", "T.C. / vergi no"],
    ],
  },
  {
    baslik: "Elektrik mühendisi",
    alanlar: [
      ["elec_name", "Adı"],
      ["elec_surname", "Soyadı"],
      ["elec_registry", "Sicil no"],
      ["elec_chamber", "Oda sicil no"],
      ["elec_tax", "T.C. / vergi no"],
    ],
  },
  {
    baslik: "Montaj firması",
    alanlar: [
      ["company_name", "Firma unvanı"],
      ["company_address", "Adres"],
      ["company_tax", "Vergi no"],
      ["company_tax_office", "Vergi dairesi"],
    ],
  },
];

/**  Boş alanlar atılır:  sunucu kapak sayfasını yalnız dolu alan varsa koyar.  */
export function kapakSayfasi(alanlar: Record<string, string | undefined>): Record<string, string> {
  return Object.fromEntries(
    Object.entries(alanlar).filter((e): e is [string, string] => typeof e[1] === "string" && e[1].trim() !== ""),
  );
}

from pathlib import Path
import math, json
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
import ezdxf

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'output'
pdfmetrics.registerFont(TTFont('DV',str(ROOT/'fonts/DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('DVB',str(ROOT/'fonts/DejaVuSans-Bold.ttf')))
P=72/25.4
c=canvas.Canvas(str(OUT/'pdf/Elbistan_Asansor_On_Proje.pdf'),pagesize=(420*P,297*P))
c.setTitle('Elbistan - 800 kg asansör | Ölçü formuna dayalı ön proje')
doc=ezdxf.new('R2013'); doc.units=4
doc.linetypes.new('ONERI_KESIK',dxfattribs={'description':'Temsili kesik cizgi','pattern':[3,2,-1]})
for n,col in [('PAFTA',7),('OLCU',4),('YERLESIM_ONERI',3),('NOT',2)]: doc.layers.new(n,dxfattribs={'color':col})
ms=doc.modelspace(); page=0
COL={'PAFTA':'#243447','OLCU':'#087e8b','YERLESIM_ONERI':'#398969','NOT':'#a35919'}
def line(x,y,X,Y,layer='PAFTA',dash=False):
    c.setStrokeColor(HexColor(COL[layer])); c.setLineWidth(.23*P); c.setDash([2*P,1*P] if dash else [])
    c.line(x*P,y*P,X*P,Y*P)
    ms.add_line((x+(page-1)*440,y),(X+(page-1)*440,Y),dxfattribs={'layer':layer,'linetype':'ONERI_KESIK' if dash else 'CONTINUOUS'})
def rect(x,y,w,h,layer='PAFTA',dash=False):
    for a,b,A,B in [(x,y,x+w,y),(x+w,y,x+w,y+h),(x+w,y+h,x,y+h),(x,y+h,x,y)]:line(a,b,A,B,layer,dash)
def text(x,y,s,size=9,bold=False,layer='PAFTA'):
    c.setFillColor(HexColor(COL[layer]));c.setFont('DVB' if bold else 'DV',size);c.drawString(x*P,y*P,s)
    ms.add_text(s,dxfattribs={'height':size/P*.73,'insert':(x+(page-1)*440,y),'layer':layer})
def block(x,y,lines,size=9,leading=6,layer='PAFTA'):
    for s in lines:text(x,y,s,size,layer=layer);y-=leading
def dim(x,y,X,Y,label):
    line(x,y,X,Y,'OLCU')
    if abs(Y-y)<.01:
        for a in [x,X]:line(a-1.4,y-1.4,a+1.4,y+1.4,'OLCU')
        text((x+X)/2-len(label)*.65,y+2,label,8,layer='OLCU')
    else:
        for b in [y,Y]:line(x-1.4,b-1.4,x+1.4,b+1.4,'OLCU')
        text(x+2,(y+Y)/2,label,8,layer='OLCU')
def start(title,scale):
    global page
    page+=1;rect(10,10,400,277)
    text(16,276,'ELBİSTAN / ASANSÖR ÖN PROJESİ',17,True)
    text(16,266,title,12,True)
    text(300,277,'800 kg | 10 kişi | 5 durak',10,True)
    text(300,267,'R00 / 08.09.2026',9)
    line(10,259,410,259)
    line(10,28,410,28)
    text(15,20,'ÖN PROJE - İMALAT / MONTAJ İÇİN KULLANILAMAZ',9,True,layer='NOT')
    text(15,14,'Mavi: form ölçüsü / hesaplanan ölçü. Yeşil: öneri veya temsili ekipman. Tüm ölçüler mm.',7)
    text(292,20,f'Ölçek: {scale} | A3 yatay | P{page:02d}',9)
    text(292,14,'Yapı sahibi: Ramis Özcan (?) - teyit gerekli',7)
def end():c.showPage()
def rail(x,y,flip=False):
    s=-1 if flip else 1
    line(x,y-3,x,y+3,'YERLESIM_ONERI');line(x,y,x+s*3,y,'YERLESIM_ONERI')
def table(x,y,rows,width=185):
    for a,b in rows:
        line(x,y-2,x+width,y-2);text(x,y+1,a,9);text(x+width*.52,y+1,b,9);y-=10

start('01 / Ölçü okuma, proje girdileri ve doğrulama sınırları','Ölçeksiz')
table(18,245,[('İl / ilçe','Kahramanmaraş / Elbistan'),('Kuyu net en × derinlik','2000 × 1900'),('Kabin en × derinlik','1415 × 1305; eşik hariç'),('Kabin ray arası','1710; referans yüzeyi belirsiz'),('Karşı ağırlık ray arası','1680; arka alan işaretli'),('Kapı net genişliği','900'),('Kapı düzeni','Otomatik / sağa toplar'),('Makine dairesi','Var'),('Duraklar','5 / -1, 0, 1, 2, 3'),('Anma yükü / kişi','800 kg / 10 kişi'),('Halat adedi / çapı','5 adet / 10 mm'),('Motor gücü','7,5 kW'),('İki konsol arası','1600; birim cm kabul edildi'),('İşaretli ray kesiti','89 × 62 × 16; katalog teyidi'),('Formdaki standart','TS EN 81-20 işaretli')])
text(221,246,'PROJEYİ BELİRLEYEN EKSİKLER',11,True)
block(221,235,['H1...H4: ardışık duraklar arası düşey mesafe.', 'P: kuyu dibi. OH: son durak üst boşluğu.', 'HM: makine dairesi net yüksekliği; oda planı.', 'HK: kabin yüksekliği; HD: kapı net yüksekliği.', 'v: anma hızı; askı oranı; makine ve kasnak ölçüleri.', 'Kabin/iskelet kütlesi; karşı ağırlık kütlesi.', 'Duvar kalınlığı ve malzemesi; kuyu düşeyliği.', 'Kapı kasa/paket/operatör üretici zarfı.', 'Ray ölçüm referansı, pabuç ve konsol geometrisi.'],9,7)
text(221,163,'ÇİZİMDE KULLANILAN YORUMLAR',11,True)
block(221,152,['Kabin yatayda ortalanmış kabul edilmiştir.', '1415 × 1305 ölçülerinin net/dış niteliği bilinmiyor.', 'Plan, bu ölçüleri referans dikdörtgen olarak gösterir.', 'Arka karşı ağırlık: 1680 ölçüsünün konumundan yorum.', 'Sağa toplama: kattan kuyuya bakış kabul edilmiştir.', 'Düşey çizimler şematiktir; sayısal kot uydurulmamıştır.', 'Ekipman zarfları imalat ölçüsü değildir.'],9,7)
text(221,93,'GEOMETRİK ÖN KONTROL',11,True)
block(221,82,['Referans kabin alanı: 1,415 × 1,305 = 1,846575 m².', 'Yatay kalan: 2000 - 1415 = 585 mm.', 'Derinlikte kalan: 1900 - 1305 = 595 mm.', 'Bunlar kullanılabilir emniyet boşluğu değildir;', 'kabin duvarı, karkas, kapı ve ekipman payları düşülmedi.', '800 kg uygunluğu ve mukavemet henüz doğrulanmadı.'],9,6)
end()

start('02 / Kuyu yatay kesiti ve kabin-karşı ağırlık yerleşimi','Plan 1:10 / A3 %100')
ox,oy=42,48;s=.1
def pl(x,y):return ox+x*s,oy+y*s
def pr(x,y,w,h,layer='PAFTA',dash=False):rect(*pl(x,y),w*s,h*s,layer,dash)
line(*pl(0,0),*pl(0,1900));line(*pl(0,1900),*pl(2000,1900));line(*pl(2000,1900),*pl(2000,0))
line(*pl(0,0),*pl(550,0));line(*pl(1450,0),*pl(2000,0))
# Front door opening is shown with a clear gap in the reference front line.
pr(292.5,200,1415,1305,'YERLESIM_ONERI',True)
text(91,157,'KABİN REFERANS ZARFI',11,True)
text(95,149,'1415 × 1305 / eşik hariç',9)
text(96,140,'Net / dış ölçü teyit edilmeli',8,layer='NOT')
for x,f in [(145,False),(1855,True)]:rail(*pl(x,850),flip=f)
for x,f in [(160,False),(1840,True)]:rail(*pl(x,1710),flip=f)
pr(240,1610,1520,180,'YERLESIM_ONERI',True)
text(91,217,'KARŞI AĞIRLIK / TEMSİLİ ZARF',8,layer='YERLESIM_ONERI')
for y in [65,100]:line(*pl(550,y),*pl(1450,y),'YERLESIM_ONERI')
line(*pl(1000,125),*pl(1770,125),'YERLESIM_ONERI');line(*pl(1770,125),*pl(1700,165),'YERLESIM_ONERI')
text(100,75,'900 net / sağa toplanır',8)
dim(42,246,242,246,'2000')
dim(30,48,30,238,'1900')
dim(71.25,183,212.75,183,'1415')
dim(220,68,220,198.5,'1305')
dim(56.5,118,227.5,118,'1710 / ray arası')
dim(58,230,226,230,'1680 / ağırlık ray arası')
dim(97,42,187,42,'900')
text(264,245,'YERLEŞİM NOTLARI',11,True)
block(264,233,['Ön: kat sahanlığı / tek giriş.', 'Arka: karşı ağırlık önerisi.', 'Kuyu koordinat başlangıcı: ön-sol köşe.', 'X sağa, Y kuyu arkasına.', '', 'Öneri koordinatları (mm):', 'Kabin sol X = 292,5; ön Y = 200.', 'Kabin sağ X = 1707,5; arka Y = 1505.', 'Kabin ray referans X = 145 / 1855.', 'Ray boyuna yeri Y = 850: temsili.', 'Ağırlık ray X = 160 / 1840.', 'Ağırlık ray Y = 1710: temsili.', '', '200 mm ön pay + 1305 mm referans', 'kabin + 395 mm arka pay = 1900.', 'Bu paylar ekipman sonrası net açıklık değil.', '', 'Ray arası ölçüm uçları sahada doğrulanmalı.', 'Kasa, eşik, kapı paket boyu bilinmiyor.', 'Duvar kalınlığı verilmedi; gösterilmedi.', 'Ağırlık kalınlığı ve koruyucu bilinmiyor.', 'Çarpışmasız montaj henüz kanıtlanmadı.'],8.5,7)
end()

start('03 / A-A önden ve B-B yandan düşey kesitler','Şematik / düşey ölçek yok')
levels=[70,102,134,166,198]
for x,w,title in [(35,80,'A-A / ÖNDEN'),(175,76,'B-B / YANDAN')]:
    text(x,247,title,10,True);rect(x,43,w,190)
    for i,y in enumerate(levels):
        line(x-6,y,x+w+8,y);text(x+w+10,y-1,['-1 / z=0','0 / z=H1','1 / z=H1+H2','2 / z=H1+H2+H3','3 / z=S'][i],7)
    for X in [x+7,x+w-7]:line(X,48,X,226,'YERLESIM_ONERI')
    rect(x+18,103,w-36,24,'YERLESIM_ONERI',True)
    text(x+21,113,'KABİN',8,layer='YERLESIM_ONERI')
    for X in [x+26,x+w-26]:rect(X,47,4,6,'YERLESIM_ONERI',True)
    line(x+23,129,x+23,231,'YERLESIM_ONERI',True)
    text(x+12,236,'Makine döşemesi / açıklıklar TBD',7)
    dim(x-10,43,x-10,70,'P')
    dim(x-10,198,x-10,233,'OH')
    for i in range(4):dim(x+4,levels[i],x+4,levels[i+1],f'H{i+1}')
    text(x+14,56,'Tamponlar temsili',7)
rect(237,172,7,25,'YERLESIM_ONERI',True)
text(216,205,'Karşı ağırlık',7)
text(312,245,'KOT TANIMLARI',11,True)
block(312,233,['Referans: en alt durak -1 = 0.', 'S = H1 + H2 + H3 + H4.', 'Kuyu tabanı z = -P.', 'Kuyu tavanı z = S + OH.', 'Makine odası üstü: HM ile belirlenir.', '', 'H1 = ... mm   H2 = ... mm', 'H3 = ... mm   H4 = ... mm', 'P = ... mm     OH = ... mm', 'HM = ... mm   HK = ... mm', 'HD = ... mm   v = ... m/s', '', 'Kabin ve ağırlık ayrı konumlarda', 'temsili olarak gösterilmiştir.', 'Askı oranı ve karşılıklı hareket', 'geometrisi kesinleştirilmemiştir.', '', 'Düşey ray/konsol yerleri katlara', 'göre henüz koordine edilmedi.', 'Formdaki konsol aralığı: 1600.', 'Son konsol ve ray ekleri hesapla', 'belirlenecek.'],8,7)
end()

start('04 / Makine dairesi, tahrik şeması ve kuyu dibi','Şematik / ekipman ölçüleri yok')
text(22,246,'MAKİNE DAİRESİ PLAN PRENSİBİ',11,True)
rect(25,128,150,100,'YERLESIM_ONERI',True)
rect(38,197,32,19,'YERLESIM_ONERI',True);text(41,204,'PANO',9)
rect(90,169,56,26,'YERLESIM_ONERI',True);text(94,181,'MAKİNE / 7,5 kW',8)
rect(108,154,15,8,'YERLESIM_ONERI',True);text(87,146,'Halat geçişi: TBD',8)
text(33,134,'Giriş / erişim yönü belirlenecek',8)
dim(25,235,175,235,'Oda eni: TBD')
text(23,113,'Oda sınırı ve ekipman konumları temsili.',9,layer='NOT')
block(23,101,['Kaide, taşıyıcı kiriş ve ankrajlar reaksiyonlara göre seçilir.', 'Kasnak çapı / oluk / sarım açısı ve saptırma kasnağı bilinmiyor.', 'Pano çalışma alanı, makine bakım alanı ve kaldırma tertibatı', 'üretici çizimleriyle yerleştirilecek. Havalandırma ve erişim TBD.'],8.5,7)
text(202,246,'TAHRİK BAĞLANTI PRENSİBİ',11,True)
rect(212,211,53,15,'YERLESIM_ONERI',True);text(217,217,'TAHRİK GRUBU',8)
line(222,211,222,163,'YERLESIM_ONERI',True);line(254,211,254,178,'YERLESIM_ONERI',True)
rect(212,147,22,16,'YERLESIM_ONERI',True);text(214,153,'Kabin',8)
rect(246,165,17,13,'YERLESIM_ONERI',True);text(247,170,'KA',8)
block(280,222,['5 × Ø10 mm halat (form).', 'Çizgi sayısı halat adedi değil.', 'Askı oranı: bilinmiyor.', 'Bu şekil halat güzergâhı veya', 'kasnak yerleşimi tayin etmez.', 'Regülatör devresi ayrı seçilir.'],8.5,7)
text(202,128,'KUYU DİBİ / YERLEŞTİRİLECEK ELEMANLAR',10,True)
block(202,115,['Kabin tamponları ve kaideleri; karşı ağırlık tamponu.', 'Karşı ağırlık bölmesi / ayırıcı; gergi tertibatı.', 'Erişim merdiveni; durdurma ve bakım kumandaları.', 'Aydınlatma, priz ve su girişine karşı yapı çözümü.', 'Sığınma alanları ve tampon sıkışmış durum kontrolleri.', '', 'P, tampon tipi/stroku, hız ve kabin altı geometrisi olmadan', 'tampon kaidesi, alt kaçış ve güvenlik hacimleri ölçülendirilemez.'],9,7)
end()

start('05 / Kapı-kabin detayları, ray konsolu ve ekipman listesi','Şematik; yalnız yazılı ölçüler geçerli')
text(20,245,'KAT KAPISI / ÖNDEN GÖRÜNÜŞ',11,True)
rect(30,151,110,76,'YERLESIM_ONERI',True);rect(40,151,90,65,'OLCU')
line(85,151,85,216,'YERLESIM_ONERI');dim(40,143,130,143,'900 net')
dim(146,151,146,216,'HD = ?')
line(60,231,123,231,'YERLESIM_ONERI');line(123,231,118,234,'YERLESIM_ONERI')
text(39,237,'Kattan bakışta sağa toplama varsayımı',8)
block(20,129,['İki panel gösterimi temsili; panel adedi formda yok.', 'Kaba inşaat boşluğu ve kasa ölçüsü üreticiden alınmalı.', 'Eşik bağlantısı / kapı kilidi / operatör zarfı TBD.'],8,6)
text(20,98,'RAY / KONSOL PRENSİBİ',11,True)
line(32,43,32,88);line(35,43,35,88)
for y in [49,81]:line(35,y,76,y,'YERLESIM_ONERI');rail(76,y,True)
dim(89,49,89,81,'1600*')
block(103,82,['* Form cm kabulüyle.', 'Kesit: 89 × 62 × 16 işaretli.', 'Profil standardı / atalet /', 'bağlantı hesabı gerekli.', 'Ankraj çapı atanmadı.'],8,6)
text(201,245,'FORMDAN EKİPMAN OKUMASI',11,True)
table(201,230,[('Makine markası','Mügen (?)'),('Makine tipi','MF/1-Pro-E (?)'),('Regülatör markası','Selkas (?)'),('Regülatör tipi','SLK-2-A3 (?)'),('Kumanda','Konel / RevoLC (?)'),('Fren tertibatı','Erkanlift / EL18 (?)'),('Kabin tamponu','Menevış / MPS (?)'),('Ağırlık tamponu','Menevış / MPS (?)'),('Kapı kilidi','MAM (?) / sağ (?)')],width=190)
block(201,126,['(?) El yazısı nedeniyle katalog/etiket teyidi gerekli.', 'Seri numaraları fotoğraftan güvenle okunamadı;', 'sipariş veya sertifika eşleştirmesinde kullanılmamalı.', '', 'Tampon etiketlerinde 11612 ve 11613 okunuyor.', 'Ekipman tipi, belgesi ve kapasite aralığı doğrulanmadı.', 'Kabin/karşı ağırlık ray profillerinin aynı olup olmadığı', 'formdan kesin olarak anlaşılamıyor.'],9,7)
end()

start('06 / Hesap kapsamı, tamamlama listesi ve kaynak form','Ölçeksiz')
text(20,246,'UYGULAMA PROJESİNE GEÇİŞ İÇİN',11,True)
table(20,232,[('Düşey rölöve','H1...H4 / P / OH / HM eksik'),('Hareket sistemi','v / askı / kütleler eksik'),('Halat güvenlik hesabı','Halat yapısı / kopma yükü eksik'),('Tahrik ve çekiş hesabı','Kasnak / sarım / denge eksik'),('Ray mukavemeti','Profil / yük / bağlantı eksik'),('Tampon hesabı','Model belgesi / strok eksik'),('Yapı yükleri','Statik + dinamik reaksiyon eksik'),('Kapı ve kabin','Net-dış ölçü / üretici CAD eksik'),('Güvenlik hacimleri','Düşey ölçü ve ekipman eksik'),('Elektrik projesi','Besleme / pano şeması eksik'),('Kurtarma / erişim','Bina ve üretici bilgisi eksik')],width=207)
block(20,106,['Bu paket; yerleşim önerisi, iki düşey kesit, makine dairesi,', 'kuyu dibi ve detay prensiplerini içerir. Hesap sonuçları veya', 'TS EN 81-20 uygunluk beyanı yerine geçmez.', '', 'Referans: kullanıcının 08.09.2026 tarihli ölçü formu fotoğrafı.', 'Güvenlik kapsamı için üretici açıklaması (08.09.2026 erişimi):', 'KONE / EN 81-20 and EN 81-50 compliance.', 'kone.co.uk/tools-downloads/codes-and-standards/', 'en81-20-and-en81-50-compliance/', 'Standart baskısı ve uygulanabilir hükümler yetkili proje', 'mühendisi tarafından resmi standart metniyle doğrulanmalı.'],8,6)
img='/Users/ekremsekmen/Desktop/WhatsApp Image 2026-09-08 at 12.50.07.jpeg'
c.drawImage(img,250*P,44*P,width=144*P,height=202*P,preserveAspectRatio=True,anchor='c')
text(263,37,'Kaynak fotoğraf / okunabilir aslı ayrıca pakette',8)
end()
c.save()
doc.saveas(OUT/'cad/Elbistan_Asansor_Paftalar.dxf')
# Full-size model plan: actual millimetres, kept separate from paper-space layout geometry.
d=ezdxf.new('R2013');d.units=4;m=d.modelspace()
for n,col in [('KUYU_FORM',7),('KABIN_REFERANS_ONERI',3),('RAY_REFERANS_ONERI',4),('NOTLAR',2)]:d.layers.new(n,dxfattribs={'color':col})
def box(x,y,w,h,l):m.add_lwpolyline([(x,y),(x+w,y),(x+w,y+h),(x,y+h)],close=True,dxfattribs={'layer':l})
box(0,0,2000,1900,'KUYU_FORM');box(292.5,200,1415,1305,'KABIN_REFERANS_ONERI')
for x,y in [(145,850),(1855,850),(160,1710),(1840,1710)]:
    m.add_line((x,y-30),(x,y+30),dxfattribs={'layer':'RAY_REFERANS_ONERI'})
for y in [65,100]:m.add_line((550,y),(1450,y),dxfattribs={'layer':'KABIN_REFERANS_ONERI'})
for i,t in enumerate(['ON PROJE - IMALAT ICIN DEGIL','Birim mm / 1:1 model; konumlar oneridir','Kuyu 2000x1900 / Kabin referansi 1415x1305','Kabin ray arasi 1710 / KA ray arasi 1680','Net-dis olcu ve ray referanslari teyit edilmeli']):m.add_text(t,dxfattribs={'height':40,'insert':(0,-150-i*70),'layer':'NOTLAR'})
d.saveas(OUT/'cad/Elbistan_Kuyu_Plani_1_1.dxf')
print('PDF ve iki DXF oluşturuldu.')

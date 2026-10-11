# Kullanıcı Hikayeleri ve Backlog (SimulInvest)

Bu doküman, SimulInvest projesi için kullanıcı hikayelerini (user stories), epic'leri, öncelikleri ve kabul kriterlerini içerir.

## EPIC 1: Çekirdek Sistem (MVP)
Uygulamanın çalışması için zorunlu çekirdek özellikler: kayıt/giriş, sanal bakiye, güncel fiyatlar, al-sat işlemleri ve portföy.

### Story 1.1: Kayıt, giriş ve güvenli oturum
- **Öncelik:** `P0-MustHave` · **Milestone:** Sprint 3 · **Story Point:** 5
- **Açıklama:** Bir kullanıcı olarak e-posta ve şifremle kayıt olup giriş yapmak istiyorum, böylece hesabıma güvenle erişebileyim.
- **Kabul Kriterleri:**
  - [ ] Geçerli e-posta ve en az 8 karakterli şifreyle kayıt olunabilir
  - [ ] Aynı e-posta ile ikinci kez kayıt yapılamaz (anlaşılır hata mesajı)
  - [ ] Doğru bilgilerle girişte JWT döner, yanlış bilgide 401 hatası alınır
  - [ ] Şifre veritabanında hash olarak saklanır

### Story 1.2: 100.000 TL sanal bakiye
- **Öncelik:** `P0-MustHave` · **Milestone:** Sprint 3 · **Story Point:** 2
- **Açıklama:** Yeni bir kullanıcı olarak kayıt olduğumda hesabıma 100.000 TL sanal bakiye tanımlanmasını istiyorum, böylece hemen işlem yapmaya başlayabileyim.
- **Kabul Kriterleri:**
  - [ ] Kayıt sonrası cüzdan otomatik oluşur ve bakiye 100.000 TL olur
  - [ ] Bakiye hiçbir koşulda negatif olamaz

### Story 1.3: Güncel varlık fiyatlarının çekilmesi
- **Öncelik:** `P0-MustHave` · **Milestone:** Sprint 3 · **Story Point:** 5
- **Açıklama:** Bir kullanıcı olarak hisse, kripto ve altın için güncel fiyatları görmek istiyorum, böylece doğru fiyattan alım-satım yapabileyim.
- **Kabul Kriterleri:**
  - [ ] Hisse, kripto ve altın fiyatları listelenir
  - [ ] Fiyatlar en fazla 60 saniye gecikmeyle sunulur (önbellek)
  - [ ] Dış veri sağlayıcı hata verirse yedek veri kullanılır, uygulama çökmez

### Story 1.4: Al-sat işlemleri ve portföy kâr/zarar paneli
- **Öncelik:** `P0-MustHave` · **Milestone:** Sprint 3 · **Story Point:** 8
- **Açıklama:** Bir kullanıcı olarak varlık alıp satmak ve portföyümün kâr/zararını görmek istiyorum, böylece yatırım kararlarımın sonucunu takip edebileyim.
- **Kabul Kriterleri:**
  - [ ] Yeterli bakiye varsa alım yapılır ve bakiye toplam tutar kadar azalır
  - [ ] Yetersiz bakiyede alım reddedilir, bakiye değişmez
  - [ ] Sahip olunandan fazla adet satılamaz
  - [ ] Portföyde her varlık için adet, ortalama maliyet ve kâr/zarar görünür
  - [ ] İşlem geçmişi listelenir

---

## EPIC 2: İleri Düzey Mekanikler ve Cila
MVP tamamlandıktan sonra eklenecek özellikler: YZ haber duygu analizi, varlık dağılımı grafiği, izleme listesi.

### Story 2.1: YZ haber duygu analizi
- **Öncelik:** `P1-QuickWin` · **Milestone:** Final · **Story Point:** 8
- **Açıklama:** Bir kullanıcı olarak finans haberlerinin YÜKSELİŞ veya DÜŞÜŞ etiketiyle gösterilmesini istiyorum, böylece haberlerin piyasaya etkisini kolay anlayabileyim.
- **Kabul Kriterleri:**
  - [ ] Finans haberleri listelenir
  - [ ] Her habere YZ tarafından YÜKSELİŞ veya DÜŞÜŞ etiketi eklenir
  - [ ] YZ servisi hata verirse haber etiketsiz gösterilir, sayfa çökmez
  - [ ] Ekranda "Yatırım tavsiyesi değildir" uyarısı bulunur

### Story 2.2: Varlık dağılımı pasta grafiği
- **Öncelik:** `P1-QuickWin` · **Milestone:** Final · **Story Point:** 3
- **Açıklama:** Bir kullanıcı olarak portföyümün varlık türlerine göre dağılımını pasta grafikte görmek istiyorum, böylece çeşitlendirmemi hızlıca değerlendirebileyim.
- **Kabul Kriterleri:**
  - [ ] Portföy hisse, kripto ve altın dağılımıyla pasta grafikte gösterilir (Chart.js)
  - [ ] Boş portföyde bilgilendirme mesajı gösterilir
  - [ ] Yeni işlem sonrası grafik güncellenir

### Story 2.3: İzleme listesi
- **Öncelik:** `P1-QuickWin` · **Milestone:** Final · **Story Point:** 3
- **Açıklama:** Bir kullanıcı olarak ilgilendiğim varlıkları izleme listeme eklemek istiyorum, böylece fiyatlarını tek ekrandan takip edebileyim.
- **Kabul Kriterleri:**
  - [ ] Varlık izleme listesine eklenebilir ve çıkarılabilir
  - [ ] Listedeki varlıkların güncel fiyatı görünür
  - [ ] Sayfa yenilense de liste korunur

---

## EPIC 3: Faz 2 Geliştirmeleri
Vakit kalırsa yapılacak özellikler: liderlik tablosu ve geçmiş fiyat grafiği.

### Story 3.1: Liderlik tablosu
- **Öncelik:** `P2-NiceToHave` · **Milestone:** Final · **Story Point:** 5
- **Açıklama:** Bir kullanıcı olarak diğer kullanıcılarla portföy performansımı karşılaştırmak istiyorum, böylece yarışarak daha motive olabileyim.
- **Kabul Kriterleri:**
  - [ ] Kullanıcılar toplam portföy değerine göre sıralanır
  - [ ] İlk 10 kullanıcı listelenir
  - [ ] Kullanıcının kendi sırası vurgulanır

### Story 3.2: 30 günlük geçmiş fiyat grafiği
- **Öncelik:** `P2-NiceToHave` · **Milestone:** Final · **Story Point:** 3
- **Açıklama:** Bir kullanıcı olarak seçtiğim varlığın son 30 günlük fiyat geçmişini çizgi grafikte görmek istiyorum, böylece fiyat eğilimini analiz edebileyim.
- **Kabul Kriterleri:**
  - [ ] Seçili varlık için 30 günlük çizgi grafik gösterilir
  - [ ] Veri alınamazsa bilgilendirme mesajı gösterilir

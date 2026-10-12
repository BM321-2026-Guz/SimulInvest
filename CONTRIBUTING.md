# Katkı Rehberi

Bu rehber SimulInvest ekibinin repoya nasıl katkı vereceğini anlatır.

## Dal (Branch) Kuralları

| Dal | Amaç | Doğrudan push |
|---|---|---|
| `main` | Çalışan, test edilmiş kod | Yasak |
| `develop` | Geliştirme ana dalı | Yasak (PR ile) |
| `feature/<ad>-<konu>` | Tek bir görev / kullanıcı hikayesi | Serbest |

Dal adı örnekleri:

- `feature/fatma-user-stories`
- `feature/ozge-openapi`
- `feature/eren-ci-pipeline`

Dalı her zaman **`develop`'tan** aç.

## Adım Adım: İlk Katkın (GitHub Web Arayüzü)

Terminal bilmen gerekmez.

1. Repo sayfasında dal seçiciden **develop** dalını seç.
2. **Add file → Create new file** (var olan dosyayı düzenlemek için dosyayı aç, kalem simgesine tıkla).
3. Dosya adını ve içeriği yaz.
4. **Commit changes** düğmesine bas.
5. Açılan pencerede **"Create a new branch for this commit and start a pull request"** seçeneğini seç ve dal adını kurala uygun yaz.
6. **Propose changes**, sonra **Create pull request**.
7. PR'ın hedef (base) dalının **develop** olduğunu kontrol et.
8. Sağ taraftan **Reviewers** kısmına Özge'yi ekle. Özge müsait değilse Kerem'i ekle.

## Commit Mesajı Kuralı

Kısa, Türkçe veya İngilizce, tek satır:

```
<tür>: <ne yapıldı>
```

Türler: `docs`, `feat`, `fix`, `test`, `ci`, `chore`

Örnekler:

- `docs: kullanıcı hikayelerine kabul kriterleri eklendi`
- `ci: CodeQL workflow eklendi`
- `test: yetersiz bakiye birim testi eklendi`

## Pull Request Kuralları

- PR başlığı yapılan işi tek cümleyle anlatır.
- PR açıklamasında şablondaki kutuları doldur.
- En az **1 onay** olmadan birleştirme yapılmaz.
- İnceleme yorumları yapıldıktan sonra aynı dala yeni commit atarak düzeltme yapılır, yeni PR açılmaz.
- Kendi PR'ını kendin onaylayamazsın.

## İşler (Issue) ile Çalışma

- Her görev bir Issue'dur ve GitHub Projects panosunda takip edilir.
- Üzerinde çalışmaya başlarken Issue'yu kendine ata ve **In Progress** sütununa çek.
- PR açıklamasına `Closes #<issue numarası>` yaz; PR birleşince Issue otomatik kapanır.

## Etiketler

| Etiket | Anlamı |
|---|---|
| `P0-MustHave` | MVP, zorunlu |
| `P1-QuickWin` | Vakit varsa yapılacak cila |
| `P2-NiceToHave` | Faz 2 |

## Takıldığında

- Önce takım içinde sor (WhatsApp grubu).
- Hata ve engelleri Scrum Master'a (Kerem) bildir.
- Kod ve mimari sorular için Özge'ye (müsait değilse Kerem'e) PR üzerinden yorum bırak.

## Yapılmaması Gerekenler

- `main` veya `develop`'a doğrudan commit.
- `.env`, şifre, API anahtarı gibi gizli bilgileri commit etmek. Anahtarlar yalnızca `.env` dosyasında tutulur ve `.gitignore` tarafından dışlanır.
- Başkasının dalına izinsiz commit atmak.

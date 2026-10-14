# RACI Görev Dağılım Matrisi

**R**: Responsible (işi yapan) · **A**: Accountable (hesap veren, tek kişi) · **C**: Consulted (danışılan) · **I**: Informed (bilgilendirilen)

Bir kişi hem işi yapıp hem hesap veriyorsa **A/R** yazılır.

## Takım

| Üye | Rol |
|---|---|
| Fatma Saruhan | Product Owner & Requirements Engineer |
| Kerem Türkyılmaz | Scrum Master & Agile Process Coach (aynı zamanda frontend sorumlusu) |
| Özge Karaca | Lead Software Architect & Tech Lead |
| Mine Yamaner | QA & Test Automation Engineer |
| Eren Özdemir | DevOps & CI/CD Infrastructure Engineer |
| Emre Harman | Security Specialist (DevSecOps) |

> Takım 6 kişidir. Security rolü Emre Harman'dır. Emre'nin katkısı netleşene kadar OWASP analizi Kerem'e, SAST taraması Eren'e atanmıştır (yedek sorumlular). Emre aktif olunca bu iki iş Security'ye devredilir.

## Matris

| Faaliyet | Fatma | Kerem | Özge | Mine | Eren | Emre |
|---|---|---|---|---|---|---|
| Proje önerisi ve sistem vizyonu | R | A | C | I | I | I |
| Product Backlog ve kullanıcı hikayeleri | A/R | C | C | C | I | I |
| Kabul kriterleri ve SRS | A/R | I | C | C | I | I |
| Figma prototipleri ve user flow | A/R | C | C | I | I | I |
| Teknoloji yığını kararı | I | C | A/R | C | C | I |
| OpenAPI sözleşmesi | C | C | A/R | C | I | I |
| ERD, C4 ve UML diyagramları | I | C | A/R | I | I | I |
| Backend geliştirme (API, cüzdan, al-sat) | I | C | C | C | A/R | I |
| Fiyat verisi entegrasyonu ve önbellek | I | C | C | I | A/R | I |
| Frontend geliştirme | C | A/R | C | I | I | I |
| Pull Request incelemeleri | I | R (yedek) | A/R | I | I | I |
| Test stratejisi, birim ve E2E testler | I | I | C | A/R | C | I |
| Git-Flow, branch koruması, repo kuralları | I | C | C | I | A/R | I |
| CI/CD pipeline ve Docker | I | I | C | C | A/R | I |
| SAST taraması (CodeQL, SonarQube) | I | I | C | C | A/R | R* |
| OWASP Top 10 güvenlik analizi | I | A/R | C | I | C | R* |
| NFR ve kalite ölçütleri | R | C | C | A | I | I |
| Sprint planlama, toplantılar, engelleyiciler | C | A/R | C | C | C | I |
| Teslim dokümanları ve sunum koordinasyonu | C | A/R | C | C | C | I |
| Final demo ve savunma | R | A | R | R | R | R |

\* Emre aktif olarak katkı verirse işi o yapar. Hesap veren (A) değişmez. Aktif olmazsa A/R sahibi (Kerem veya Eren) işi tamamlar.

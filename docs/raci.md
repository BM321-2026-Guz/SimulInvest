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

> Takım 5 kişidir. Security (6. kişi) rolü yoktur. OWASP analizi Kerem'e, SAST taraması Eren'e atanmıştır.

## Matris

| Faaliyet | Fatma | Kerem | Özge | Mine | Eren |
|---|---|---|---|---|---|
| Proje önerisi ve sistem vizyonu | R | A | C | I | I |
| Product Backlog ve kullanıcı hikayeleri | A/R | C | C | C | I |
| Kabul kriterleri ve SRS | A/R | I | C | C | I |
| Figma prototipleri ve user flow | A/R | C | C | I | I |
| Teknoloji yığını kararı | I | C | A/R | C | C |
| OpenAPI sözleşmesi | C | C | A/R | C | I |
| ERD, C4 ve UML diyagramları | I | C | A/R | I | I |
| Backend geliştirme (API, cüzdan, al-sat) | I | C | A/R | C | C |
| Fiyat verisi entegrasyonu ve önbellek | I | C | A | I | R |
| Frontend geliştirme | C | A/R | C | I | I |
| Pull Request incelemeleri | I | R (yedek) | A/R | I | I |
| Test stratejisi, birim ve E2E testler | I | I | C | A/R | C |
| Git-Flow, branch koruması, repo kuralları | I | C | C | I | A/R |
| CI/CD pipeline ve Docker | I | I | C | C | A/R |
| SAST taraması (CodeQL) | I | I | C | C | A/R |
| OWASP Top 10 güvenlik analizi | I | A/R | C | I | C |
| NFR ve kalite ölçütleri | R | C | C | A | I |
| Sprint planlama, toplantılar, engelleyiciler | C | A/R | C | C | C |
| Teslim dokümanları ve sunum koordinasyonu | C | A/R | C | C | C |
| Final demo ve savunma | R | A | R | R | R |

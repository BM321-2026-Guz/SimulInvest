# Veritabanı Tasarımı (ERD)

```mermaid
erDiagram
    USERS ||--|| WALLETS : "sahiptir"
    USERS ||--o{ HOLDINGS : "tutar"
    USERS ||--o{ TRANSACTIONS : "yapar"
    NEWS ||--o| NEWS_ANALYSIS : "sahiptir"

    USERS {
        int id PK
        string email
        string password_hash
        datetime created_at
    }

    WALLETS {
        int id PK
        int user_id FK
        decimal balance
    }

    HOLDINGS {
        int id PK
        int user_id FK
        string asset_type
        string symbol
        decimal quantity
        decimal average_cost
    }

    TRANSACTIONS {
        int id PK
        int user_id FK
        string transaction_type
        string symbol
        decimal quantity
        decimal price
        datetime timestamp
    }

    NEWS {
        int id PK
        string title
        text content
        string source
        datetime published_at
    }

    NEWS_ANALYSIS {
        int id PK
        int news_id FK
        string sentiment
    }

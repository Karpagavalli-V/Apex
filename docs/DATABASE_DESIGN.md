# Database Design & Persistence Specification
## Apex Bank Core Banking Database

**Database Management System:** MongoDB 8.0 Enterprise / Community  
**Cluster Architecture:** Single-Node Replica Set (`rs0`) with Multi-Document ACID Transactions  
**Connection URI:** `mongodb://127.0.0.1:27017/?replicaSet=rs0&directConnection=true`  
**Database Name:** `banking_dev` (Development) / `banking_test` (Isolated Test Runner)  

---

## 1. Database Entity-Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ ACCOUNTS : owns
    USERS ||--o{ TRANSACTIONS : executes
    USERS ||--o{ IDEMPOTENCY_KEYS : scopes
    USERS ||--o{ AUDIT_LOGS : generates
    ACCOUNTS ||--o{ TRANSACTIONS : records
    ACCOUNTS ||--o{ AUDIT_LOGS : affects
    TRANSACTIONS }o--o| ACCOUNTS : counterparty

    USERS {
        string user_id PK "Unique user identifier (usr_xxx)"
        string email UK "Normalized lowercase user email"
        string username UK "Unique login handle (3-30 chars)"
        string password_hash "Bcrypt hash with work factor 12"
        string full_name "Legal name of account holder"
        string role "Authorization tier: customer | admin"
        boolean is_active "Account status flag"
        datetime created_at "Registration timestamp (UTC)"
        datetime updated_at "Profile modification timestamp (UTC)"
    }

    ACCOUNTS {
        string account_id PK "Internal unique ID (acc_xxx)"
        string account_number UK "12-digit public account number"
        string user_id FK "Owner reference to USERS"
        string account_type "SAVINGS | CHECKING"
        int64 balance_paise "Exact integer balance in paise (1 INR = 100 paise)"
        string currency "Strictly INR"
        string status "ACTIVE | FROZEN | CLOSED"
        datetime created_at "Creation timestamp (UTC)"
        datetime updated_at "Balance modification timestamp (UTC)"
    }

    TRANSACTIONS {
        string transaction_id PK "Immutable ledger ID (tx_xxx)"
        string account_id FK "Primary account involved"
        string user_id FK "Executing customer ID"
        string type "DEPOSIT | WITHDRAWAL | TRANSFER"
        int64 amount_paise "Integer transaction value"
        int64 balance_after_paise "Snapshot balance post-mutation"
        string status "COMPLETED | FLAGGED_SUSPICIOUS | FLAGGED_HIGH_RISK"
        string description "Transaction narrative / memo"
        string counterparty_account_id FK "Destination account for transfers"
        string idempotency_key "Client-provided deduplication key"
        string risk_level "NORMAL | SUSPICIOUS | HIGH_RISK"
        float fraud_probability "ML anomaly probability (0.0 to 1.0)"
        object metadata "Direction, role, execution markers"
        datetime timestamp "Ledger creation timestamp (UTC)"
    }

    IDEMPOTENCY_KEYS {
        objectId _id PK "MongoDB internal ID"
        string key "Client idempotency key UUID"
        string user_id FK "Scoped user identifier"
        string action "Operation type: deposit | withdraw | transfer"
        object response "Cached JSON response payload"
        datetime created_at "Creation timestamp (TTL index 24 hours)"
    }

    AUDIT_LOGS {
        objectId _id PK "MongoDB internal ID"
        string action "Security/Financial event name"
        string user_id FK "User responsible for action"
        string account_id FK "Optional affected account ID"
        string status "SUCCESS | REJECTED | FAILED"
        object details "Immutable payload parameters"
        datetime timestamp "Event occurrence timestamp (UTC)"
    }
```

---

## 2. Detailed Collection Schemas

### 2.1 Collection: `users`
Stores user profile, credentials, and authorization roles.
- **Indexes**:
  - `{"email": 1}`: Unique index (`name: "uniq_user_email"`).
  - `{"username": 1}`: Unique index (`name: "uniq_user_username"`).
  - `{"user_id": 1}`: Unique index (`name: "uniq_user_id"`).
  - `{"role": 1}`: Standard index for role-based queries.

### 2.2 Collection: `accounts`
Stores bank accounts, account numbers, and atomic balance balances.
- **Indexes**:
  - `{"account_id": 1}`: Unique index (`name: "uniq_account_id"`).
  - `{"account_number": 1}`: Unique index (`name: "uniq_account_number"`).
  - `{"user_id": 1}`: Query index for fetching a customer's accounts.
  - `{"status": 1}`: Filter index for active accounts.
- **Critical Invariant**:
  - `balance_paise` is stored as an exact 64-bit integer. Floating-point values are strictly rejected.

### 2.3 Collection: `transactions`
Immutable double-entry financial ledger recording all deposits, withdrawals, and transfers.
- **Indexes**:
  - `{"transaction_id": 1}`: Unique index (`name: "uniq_tx_id"`).
  - `{"account_id": 1}`: Query index for account ledgers.
  - `{"user_id": 1}`: Query index for user transaction history.
  - `{"timestamp": -1}`: Index for chronological pagination.
  - `{"account_id": 1, "timestamp": -1}`: Compound index for account ledger sorting.
  - `{"risk_level": 1}`: Query index for flagged transactions queue.

### 2.4 Collection: `idempotency_keys`
Caches successful mutation payloads to prevent duplicate execution upon network retries.
- **Indexes**:
  - `{"key": 1, "user_id": 1}`: Unique compound index (`name: "uniq_idem_key_user"`).
  - `{"created_at": 1}`: **TTL Index** (`expireAfterSeconds: 86400`). MongoDB background thread automatically purges keys older than 24 hours.

### 2.5 Collection: `audit_logs`
Immutable compliance and security log capturing user logins, account creation, and rejected overdraft attempts.
- **Indexes**:
  - `{"timestamp": -1}`: Chronological log querying.
  - `{"user_id": 1}`: User security auditing.
  - `{"action": 1}`: Action-based filtering.

---

## 3. ACID Transactions & Concurrency Strategy

1. **Replica Set Configuration**: Multi-document transactions require MongoDB to operate as a replica set (`rs0`).
2. **Transaction Isolation**: MongoDB transactions use snapshot isolation level. Reads inside the transaction only see committed data as of the transaction start.
3. **Optimistic Locking & Transient Error Handling**:
   - Write operations conditional on account balance (e.g. `{"balance_paise": {"$gte": amount}}`) protect against overdrafts.
   - Concurrent writes on the same document trigger `WriteConflict` (`TransientTransactionError`), which is captured and automatically retried with exponential backoff and jitter up to 25 attempts.

# System Design Document (SDD)
## AI-Enhanced Core Banking Platform (Apex Bank)

**Document Version:** 1.0.0  
**Status:** Approved  
**Classification:** Technical Architecture & Design Specification  

---

## 1. High-Level System Architecture

Apex Bank is engineered as a decoupled, multi-tier system separating the presentation, business logic, intelligence, and distributed persistence layers.

```mermaid
flowchart TB
    subgraph ClientTier["Presentation Tier (Client SPA)"]
        Browser["Modern Web Browser"]
        ReactApp["React 19 + Tailwind CSS SPA"]
        Router["React Router v7"]
        State["AuthContext & Storage"]
        Browser --> ReactApp
        ReactApp --> Router
        ReactApp --> State
    end

    subgraph APITier["Application Tier (Flask REST API)"]
        WSGI["WSGI / Flask Server (Port 5000)"]
        SecMiddleware["Defensive Security Headers & CORS"]
        JWTAuth["JWT Authentication & RBAC Guard"]
        RouterAPI["Blueprint Route Handlers"]
        
        WSGI --> SecMiddleware
        SecMiddleware --> JWTAuth
        JWTAuth --> RouterAPI
    end

    subgraph ServiceTier["Business & Intelligence Services"]
        BankSvc["BankingService (ACID Engine)"]
        MLSvc["MLService (Random Forest)"]
        AISvc["AIService (LLM & Heuristics)"]
        IdemCache["Idempotency Cache Handler"]
        AuditLog["Audit & Ledger Logger"]
    end

    subgraph PersistenceTier["Persistence & Data Tier"]
        MongoCluster[("MongoDB Replica Set rs0")]
        UsersColl[("users")]
        AccountsColl[("accounts")]
        TxColl[("transactions")]
        IdemColl[("idempotency_keys")]
        AuditColl[("audit_logs")]
    end

    subgraph ExternalIntelligence["External AI Tier"]
        GeminiAPI["Google Gemini 1.5 Flash API"]
        RuleFallback["Deterministic Rule-Based Fallback"]
    end

    ReactApp -->|HTTPS / Bearer JWT| WSGI
    RouterAPI --> BankSvc
    RouterAPI --> MLSvc
    RouterAPI --> AISvc

    BankSvc --> IdemCache
    BankSvc --> AuditLog
    BankSvc -->|Session Multi-Doc Write| MongoCluster
    MLSvc -->|Real-Time Risk Scoring| BankSvc

    AISvc -->|Masked Context Prompt| GeminiAPI
    AISvc -.->|On Key Absence or Error| RuleFallback

    MongoCluster --> UsersColl
    MongoCluster --> AccountsColl
    MongoCluster --> TxColl
    MongoCluster --> IdemColl
    MongoCluster --> AuditColl
```

---

## 2. Backend Module Architecture

The Flask backend is organized into micro-modular components adhering to single-responsibility principles:

```mermaid
classDiagram
    class ApplicationFactory {
        +create_app(config_name) Flask
        +register_blueprints()
        +register_error_handlers()
        +apply_security_headers()
    }

    class BankingService {
        +_execute_in_session(callback, max_retries)
        +create_account(user_id, account_type, initial_deposit)
        +deposit(account_id, amount_paise, user, idempotency_key)
        +withdraw(account_id, amount_paise, user, idempotency_key)
        +transfer(source_id, target_id, amount_paise, user, idempotency_key)
        +get_user_accounts(user_id)
        +get_account_by_id(account_id, requesting_user)
        +get_account_transactions(account_id, requesting_user)
    }

    class MLService {
        +model: RandomForestClassifier
        +scaler: StandardScaler
        +predict_risk(features) dict
        +extract_features_from_db(account_id, user_id, amount_paise, tx_type)
        +get_metrics() dict
    }

    class AIService {
        -_rate_limit_tracker: dict
        +check_rate_limit(user_id)
        +generate_financial_summary(user_id, month)
        +generate_spending_analysis(user_id, days)
        +generate_savings_suggestions(user_id)
        +process_chat(user_id, message, transaction_id)
        -_mask_account_number(account_number)
    }

    class SecurityGuards {
        +jwt_required(f)
        +roles_required(*roles)
        +validate_registration_payload(data)
        +parse_amount_to_paise(data)
    }

    ApplicationFactory --> SecurityGuards
    ApplicationFactory --> BankingService
    ApplicationFactory --> MLService
    ApplicationFactory --> AIService
```

---

## 3. End-to-End Banking Transaction Workflow

Every balance mutation enforces atomic validation, pre-lock ML risk scoring, conditional update guards, double-entry ledger persistence, and transaction rollback.

```mermaid
sequenceDiagram
    autonumber
    actor Customer as Customer / Client SPA
    participant API as Accounts Blueprint
    participant Svc as BankingService
    participant ML as MLService
    participant DB as MongoDB rs0

    Customer->>API: POST /api/accounts/{id}/transfer<br/>Header: Idempotency-Key<br/>Body: target_account, amount
    API->>API: Authenticate JWT & Validate Integer Paise
    API->>Svc: transfer(source_id, target_id, amount_paise)
    
    Svc->>DB: Check Idempotency Key
    alt Cached Response Exists
        DB-->>Svc: Return Cached Transaction Payload
        Svc-->>Customer: HTTP 200 (Replay Identical Receipt)
    else First Execution
        Svc->>DB: Verify Source Account & Ownership
        Svc->>DB: Verify Target Account Exists & Active
        
        Note over Svc,ML: Step 1: Pre-Transaction ML Risk Evaluation (Outside Write Lock)
        Svc->>ML: extract_features_from_db() & predict_risk()
        ML-->>Svc: Risk Level: NORMAL / SUSPICIOUS / HIGH_RISK

        Note over Svc,DB: Step 2: Atomic Multi-Document Transaction Session
        Svc->>DB: Start Session & Transaction (with retry on WriteConflict)
        
        Svc->>DB: find_one_and_update(source, balance >= amount, $inc: -amount)
        alt Insufficient Funds
            DB-->>Svc: None (Condition Failed)
            Svc->>DB: Abort Transaction
            Svc-->>Customer: HTTP 400 Insufficient Funds
        else Debit Succeeded
            Svc->>DB: find_one_and_update(target, $inc: +amount)
            Svc->>DB: insert_one(debit_transaction)
            Svc->>DB: insert_one(credit_transaction)
            Svc->>DB: insert_one(audit_log)
            Svc->>DB: insert_one(idempotency_record)
            Svc->>DB: Commit Transaction
            Svc-->>Customer: HTTP 200 Transfer Completed with Live Receipt
        end
    end
```

---

## 4. Machine Learning Fraud Detection Pipeline

The machine learning system classifies transaction anomalies in real-time to alert users and administrators before fraud propagates.

```mermaid
flowchart LR
    subgraph DataPipeline["Data Preparation & Training"]
        RawData[("10,000 Synthetic Transactions")] --> Preprocessing["Feature Engineering & One-Hot Encoding"]
        Preprocessing --> Split["Stratified Train/Test Split (80/20)"]
        Split --> Model["Random Forest Classifier (100 Trees, Balanced)"]
        Model --> Eval["Evaluation & Threshold Tuning"]
        Eval --> Export["Save Joblib Artifacts"]
    end

    subgraph RuntimeInference["Live Runtime Scoring"]
        TxEvent["Incoming Transaction Event"] --> FeatExtract["Extract Account Velocity & Temporal Metrics"]
        FeatExtract --> Scaler["StandardScaler Transform"]
        Scaler --> Predict["Model Inference (fraud_detector.joblib)"]
        Predict --> Probability{"Fraud Probability Score"}
        Probability -->|< 0.25| Normal["NORMAL Risk (Completed)"]
        Probability -->|0.25 to 0.70| Suspicious["SUSPICIOUS Risk (Flagged)"]
        Probability -->|>= 0.70| HighRisk["HIGH_RISK (Flagged High Risk)"]
    end
```

### Feature Engineering Matrix
1. `time_since_last_tx_min`: Time interval in minutes since account's previous activity.
2. `amount_to_avg_ratio`: Ratio of current transaction amount to customer's historical average.
3. `amount_inr`: Exact transaction value in Indian Rupees.
4. `balance_before_inr`: Account balance prior to operation.
5. `balance_ratio`: Ratio of transaction amount to account balance ($\text{amount} / \text{balance}$).
6. `tx_frequency_last_24h`: Number of transactions recorded on the account in past 24 hours.
7. `is_rapid_succession`: Binary flag indicating transactions occurring within 3 minutes of previous activity.
8. `is_weekend`: Binary flag for weekend operations.
9. `hour_of_day`: Hour (0-23) indicating nocturnal vs daytime activity.
10. `tx_type`: Categorical encoded transaction type (DEPOSIT, WITHDRAWAL, TRANSFER).

---

## 5. Generative AI Financial Assistant Pipeline

```mermaid
flowchart TD
    UserQuery["Customer Chat / Analysis Request"] --> AuthContext["Verify JWT Identity"]
    AuthContext --> RateLimiter{"Rate Limit Check (<= 30 req/min)"}
    
    RateLimiter -->|Exceeded| Error429["HTTP 429 Rate Limit Exceeded"]
    RateLimiter -->|Allowed| Guardrail{"Prompt Injection & Execution Guardrail"}
    
    Guardrail -->|Matches Transfer/Withdrawal Command| Refusal["Security Refusal Response (action_executed: False)"]
    Guardrail -->|Legitimate Inquiry| ContextBuilder["Assemble User Context (Mask Account Numbers)"]
    
    ContextBuilder --> LLMCheck{"LLM API Key Configured?"}
    LLMCheck -->|Yes| GeminiCall["Call Gemini 1.5 Flash API"]
    GeminiCall -->|Success| FormattedReply["Deliver AI Financial Analysis"]
    GeminiCall -->|Error / Timeout| Fallback
    LLMCheck -->|No| Fallback["Execute Deterministic Rule-Based Analysis Engine"]
    Fallback --> FormattedReply
```

---

## 6. Concurrency & ACID Integrity Design

### 6.1 Transaction Retry Loop with Backoff
When multiple concurrent requests target the same account, MongoDB replica set transactions experience `TransientTransactionError` (code 112 `WriteConflict`). Apex Bank implements an automated retry wrapper:
- **Max Retries**: 25 iterations.
- **Backoff Algorithm**: $\text{delay} = 0.01 \times (\text{attempt} + 1) + \text{random}(0.01, 0.05)$.
- **Write Lock Minimization**: Heavy read queries and ML feature extraction are executed *before* entering the transaction, ensuring write transactions commit in $< 1\text{ ms}$.

### 6.2 Overdraft Prevention Guarantee
Balances cannot drop below zero under any concurrency condition because updates are conditioned at the database engine level:
```json
{
  "account_id": "acc_123",
  "status": "ACTIVE",
  "balance_paise": { "$gte": 50000 }
}
```
If two simultaneous transactions each attempt to debit 500.00 INR when the balance is 500.00 INR, the database guarantees that exactly one matches the filter. The second fails atomically without race conditions.

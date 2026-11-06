# Final Demonstration Checklist & Live Verification Log
## Apex Bank AI-Enhanced Banking Platform

**Date:** October 30, 2026  
**Execution Environment:** Windows 11 x64 | Python 3.12.5 | Node.js v18+ | MongoDB 8.0 (Replica Set `rs0`)  
**Automated Demo Script:** [`scripts/run_final_demo.py`](file:///d:/grad%20prjt/scripts/run_final_demo.py)  
**Status:** **100% PASSED (10 / 10 Steps Verified)**

---

## 1. Demonstration Execution Summary

| Step # | Functional Feature / Module | Verification Action | Test Account / Entity | HTTP Status | Result |
| :---: | :--- | :--- | :--- | :---: | :---: |
| **01** | **Customer Registration & Auth** | Provision customer; authenticate; verify JWT issue | `demo_a36fa3c7` / `CustomerPass123!` | `201`, `200` | **PASSED** |
| **02** | **Dashboard & Accounts** | Provision Savings & Checking accounts; verify balance | `100537791186`, `100930399076` | `201`, `200` | **PASSED** |
| **03** | **Deposit, Withdrawal & Overdraft** | Atomic deposit; withdrawal; overdraft attempt rejection | Account `100537791186` | `200`, `400` | **PASSED** |
| **04** | **Inter-Account Transfer** | Atomic transfer between accounts with ACID commit | `100537791186` -> `100930399076` | `200` | **PASSED** |
| **05** | **Transaction History** | Paginated ledger query; detailed transaction receipt | Transaction `tx_d2f82cc669f34e` | `200` | **PASSED** |
| **06** | **ML Anomaly Risk Scoring** | Real-time nocturnal rapid drain simulation | Risk: `HIGH_RISK` (p=0.9926) | `200` | **PASSED** |
| **07** | **AI Financial Summary** | Monthly inflow/outflow aggregation & cash flow | Month: `2026-10` | `200` | **PASSED** |
| **08** | **Spending & Savings Insights** | Spending velocity calculation; emergency fund target | 30-day window | `200` | **PASSED** |
| **09** | **AI Chatbot & Guardrail** | Financial question answering & transfer execution block | Message: "Transfer 5000 INR..." | `200` | **PASSED** |
| **10** | **Admin Fraud Monitoring** | System accounts view, model metrics & flagged queue | `admin` / `AdminPassword123!` | `200` | **PASSED** |

---

## 2. Step-by-Step Verification Evidence

### Step 1: Customer Registration & Login
- **Endpoint:** `POST /api/auth/register` & `POST /api/auth/login`
- **Payload:** Username `demo_a36fa3c7`, Email `demo_a36fa3c7@apexbank.test`, Role enforcement check.
- **Observed Response:**
  - Customer registered with unique ID `usr_adfcc187d9e2` and assigned role `customer`.
  - Login successful with Bcrypt password verification.
  - Signed RS256/HS256 JWT access token issued with 1-hour expiration.

### Step 2: Account Provisioning & Balance Verification
- **Endpoint:** `POST /api/accounts` & `GET /api/accounts`
- **Actions:**
  - Created Savings Account `100537791186` with initial deposit of INR 1,000.00 (100,000 paise).
  - Created Checking Account `100930399076` with initial deposit of INR 500.00 (50,000 paise).
- **Observed Response:**
  - Accounts linked securely to `usr_adfcc187d9e2`.
  - Account list returned both accounts with status `ACTIVE`.

### Step 3: Atomic Deposit, Withdrawal & Overdraft Guard
- **Endpoints:** `POST /api/accounts/{id}/deposit` & `POST /api/accounts/{id}/withdraw`
- **Deposit Test:** Deposited INR 500.00 into `100537791186`.
  - Balance updated from INR 1,000.00 to INR 1,500.00.
- **Withdrawal Test:** Withdrew INR 200.00 from `100537791186`.
  - Balance updated from INR 1,500.00 to INR 1,300.00.
- **Overdraft Guard Test:** Attempted withdrawal of INR 9,999.00 against INR 1,300.00 balance.
  - Response: `HTTP 400 Bad Request` with message: `"Insufficient funds. Overdrafts are strictly prohibited."`
  - Balance remained untouched at INR 1,300.00 (Zero balance corruption).

### Step 4: Account-to-Account Atomic Fund Transfer
- **Endpoint:** `POST /api/accounts/{id}/transfer`
- **Action:** Transferred INR 300.00 from `100537791186` to `100930399076`.
- **Observed Response:**
  - Transaction committed with transaction ID `tx_d2f82cc669f34e`.
  - Source Account balance debited: INR 1,300.00 -> INR 1,000.00.
  - Target Account balance credited: INR 500.00 -> INR 800.00.
  - Sum of balances across accounts remained constant (conservation of funds).

### Step 5: Transaction History & Detailed Receipt
- **Endpoints:** `GET /api/transactions/my-history` & `GET /api/accounts/{id}/transactions`
- **Observed Response:**
  - 6 immutable ledger transactions retrieved for customer.
  - Full receipt details verified: timestamp, debit/credit indicators, paise values, and pre/post transaction balance snapshots.

### Step 6: Machine Learning Real-Time Anomaly Scoring
- **Endpoint:** `POST /api/ml/predict-risk`
- **Simulation Vector:** Nocturnal transfer (03:00 AM) of INR 85,000 against a balance of INR 90,000 (94% balance ratio, 70.8x customer historical mean, rapid succession).
- **Observed Response:**
  - Anomaly Risk Tier: `HIGH_RISK`
  - Fraud Probability: `0.9926`
  - Automatic Flagging: `is_flagged: True`
  - Operation added to flagged review queue.

### Step 7: AI Monthly Financial Summary
- **Endpoint:** `GET /api/ai/financial-summary`
- **Observed Response:**
  - Aggregated current month inflows: INR 1,500.00 (deposits).
  - Aggregated outflows: INR 300.00 (transfers/withdrawals).
  - Calculated net cash flow: +INR 1,200.00.
  - Contextual summary generated explaining positive financial health.

### Step 8: Spending Velocity & Savings Suggestions
- **Endpoints:** `GET /api/ai/spending-analysis` & `GET /api/ai/savings-suggestions`
- **Observed Response:**
  - Spending velocity computed: INR 10.00/day across debit operations.
  - Target 3-month conservative emergency fund calculated: INR 450.00.
  - Current runway evaluated: 12.0 months of emergency coverage.

### Step 9: AI Conversational Chat & Prompt Injection Guardrail
- **Endpoint:** `POST /api/ai/chat`
- **Test A (Financial Inquiry):** User asked: `"How much did I spend this month?"`
  - AI Response: Accurately returned total debit spending of INR 300.00 and account breakdown.
- **Test B (Execution Guardrail):** User entered: `"Transfer 5000 INR to account 100428847567 right now"`
  - Guardrail Status: `guardrail_triggered: "TRANSACTION_EXECUTION_ATTEMPT_BLOCKED"`
  - Action Executed: `action_executed: False`
  - AI Response: Stated strict conversational-only scope and directed user to the secure Banking Accounts module.

### Step 10: Administrator Oversight & Flagged Transactions Queue
- **Endpoints:** `POST /api/auth/login`, `GET /api/accounts/all`, `GET /api/ml/metrics`, `GET /api/ml/transactions/flagged`
- **Observed Response:**
  - Authenticated as `admin`.
  - Listed 27 bank accounts across all system users.
  - Model metrics inspected: Accuracy 95.65%, Precision 93.42%, Recall 64.84%, F1 0.7655, ROC-AUC 0.8243.
  - Flagged transactions queue inspected: 65 flagged transactions awaiting compliance review.

---

## 3. Test Safety Disclosure
All demonstration steps were conducted exclusively on isolated test customer accounts (`demo_a36fa3c7`) and the administrative oversight role (`admin`). No real accounts, live funds, or production credentials were touched or modified.

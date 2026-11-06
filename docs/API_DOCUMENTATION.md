# API Documentation & Endpoint Specification
## Apex Bank RESTful API (v1.0)

**Base URL**: `http://127.0.0.1:5000/api`  
**Authentication Scheme**: HTTP Bearer Authentication with JSON Web Tokens (`Authorization: Bearer <token>`)  
**Data Format**: JSON (`Content-Type: application/json`)  

---

## 1. System Endpoints

### 1.1 Health Check & Diagnostic
- **Method & Path**: `GET /api/system/health`
- **Access**: Public
- **Description**: Returns operational status of the REST API service, MongoDB connectivity, and replica set transaction support.
- **Response `200 OK`**:
```json
{
  "status": "healthy",
  "database": {
    "connected": true,
    "supports_transactions": true,
    "transaction_mode": "replica_set"
  },
  "version": "1.0.0"
}
```

---

## 2. Authentication & User Management

### 2.1 Customer Registration
- **Method & Path**: `POST /api/auth/register`
- **Access**: Public
- **Username requirements**: 3-30 characters; letters, numbers, underscores, and hyphens are allowed.
- **Request Body**:
```json
{
  "email": "customer@apexbank.org",
  "username": "customer_demo",
  "password": "Password123!",
  "full_name": "Demo Customer"
}
```
- **Response `201 Created`**:
```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "user": {
      "user_id": "usr_946711f3719f",
      "email": "customer@apexbank.org",
      "username": "customer_demo",
      "full_name": "Demo Customer",
      "role": "customer",
      "is_active": true,
      "created_at": "2026-10-30T17:00:00"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

### 2.2 User Login
- **Method & Path**: `POST /api/auth/login`
- **Access**: Public
- **Request Body**:
```json
{
  "identifier": "customer_demo",
  "password": "Password123!"
}
```
- **Response `200 OK`**:
```json
{
  "success": true,
  "message": "Authentication successful",
  "data": {
    "user": {
      "user_id": "usr_946711f3719f",
      "username": "customer_demo",
      "role": "customer"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

### 2.3 Current User Profile
- **Method & Path**: `GET /api/auth/me`
- **Access**: Authenticated (`customer` or `admin`)
- **Headers**: `Authorization: Bearer <token>`
- **Response `200 OK`**: Returns serialized user details. `password_hash` is strictly omitted.

### 2.4 Change Password
- **Method & Path**: `POST /api/auth/change-password`
- **Access**: Authenticated
- **Request Body**:
```json
{
  "old_password": "Password123!",
  "new_password": "NewSecurePassword456!"
}
```
- **Response `200 OK`**: `{"success": true, "message": "Password updated successfully."}`

### 2.5 Provision Administrator Account
- **Method & Path**: `POST /api/auth/admin/create-admin`
- **Access**: Administrator Only (`@roles_required("admin")`)
- **Request Body**: Accepts `email`, `username`, `password`, `full_name`.
- **Response `201 Created`**: Provisions new user with `role: "admin"`.

---

## 3. Core Banking & Account Operations

### 3.1 Create Bank Account
- **Method & Path**: `POST /api/accounts`
- **Access**: Authenticated Customer
- **Headers**: `Idempotency-Key` (Optional UUID)
- **Request Body**:
```json
{
  "account_type": "SAVINGS",
  "initial_deposit": 1000.00
}
```
- **Response `201 Created`**:
```json
{
  "success": true,
  "data": {
    "account": {
      "account_id": "acc_f67be247fc7c",
      "account_number": "100428847567",
      "account_type": "SAVINGS",
      "balance_inr": 1000.00,
      "balance_paise": 100000,
      "currency": "INR",
      "status": "ACTIVE"
    }
  }
}
```

### 3.2 List My Accounts
- **Method & Path**: `GET /api/accounts`
- **Access**: Authenticated Customer
- **Response `200 OK`**: Returns all accounts owned by requesting customer.

### 3.3 List All Accounts (Admin Directory)
- **Method & Path**: `GET /api/accounts/all?page=1&limit=20`
- **Access**: Administrator Only (`role: "admin"`)
- **Response `200 OK`**: Paginated directory of accounts across all bank customers.

### 3.4 Account Balance Inquiry
- **Method & Path**: `GET /api/accounts/{account_id}/balance`
- **Access**: Account Owner or Administrator
- **Response `200 OK`**: Returns exact integer paise, formatted INR, and timestamp.

### 3.5 Deposit Funds
- **Method & Path**: `POST /api/accounts/{account_id}/deposit`
- **Access**: Account Owner or Administrator
- **Headers**: `Idempotency-Key` (Optional UUID)
- **Request Body**:
```json
{
  "amount": 500.00,
  "description": "Salary direct deposit"
}
```
- **Response `200 OK`**: Returns updated account balance and created ledger transaction record.

### 3.6 Withdraw Funds
- **Method & Path**: `POST /api/accounts/{account_id}/withdraw`
- **Access**: Account Owner or Administrator
- **Headers**: `Idempotency-Key` (Optional UUID)
- **Request Body**:
```json
{
  "amount": 200.00,
  "description": "ATM cash withdrawal"
}
```
- **Response `200 OK`**: Returns updated balance and created ledger transaction.
- **Error `400 Bad Request`**: If balance is less than requested amount (`"Insufficient funds. Overdrafts are strictly prohibited."`).

### 3.7 Inter-Account Fund Transfer
- **Method & Path**: `POST /api/accounts/{account_id}/transfer`
- **Access**: Source Account Owner or Administrator
- **Headers**: `Idempotency-Key` (Optional UUID)
- **Request Body**:
```json
{
  "target_account": "100470980433",
  "amount": 150.00,
  "description": "Invoice payment"
}
```
- **Response `200 OK`**:
```json
{
  "success": true,
  "message": "Transfer processed successfully",
  "data": {
    "source_account": { "balance_inr": 850.00, "balance_paise": 85000 },
    "target_account_number": "100470980433",
    "transaction": {
      "transaction_id": "tx_892a047d457147",
      "type": "TRANSFER",
      "amount_inr": 150.00,
      "risk_level": "NORMAL",
      "status": "COMPLETED"
    }
  }
}
```

---

## 4. Transaction History & Audit Ledger

### 4.1 Customer Transaction History
- **Method & Path**: `GET /api/transactions/my-history?page=1&limit=10&type=TRANSFER&risk=NORMAL`
- **Access**: Authenticated Customer
- **Query Parameters**:
  - `page`: Page index (default: `1`)
  - `limit`: Items per page (default: `10`, max: `100`)
  - `type`: Optional filter (`DEPOSIT`, `WITHDRAWAL`, `TRANSFER`)
  - `risk`: Optional filter (`NORMAL`, `SUSPICIOUS`, `HIGH_RISK`)
- **Response `200 OK`**: Paginated transaction list with ledger metadata.

### 4.2 Inspect Transaction Details
- **Method & Path**: `GET /api/transactions/{transaction_id}`
- **Access**: Transaction Owner or Administrator
- **Response `200 OK`**: Full transaction ledger details including risk score and counterparty ID.

---

## 5. Machine Learning Fraud Detection

### 5.1 Real-Time Risk Predictor
- **Method & Path**: `POST /api/ml/predict-risk`
- **Access**: Authenticated Customer or Administrator
- **Contextual Request Body**:
```json
{
  "account_id": "acc_f67be247fc7c",
  "amount": 75000.00,
  "tx_type": "TRANSFER"
}
```
- **Response `200 OK`**:
```json
{
  "success": true,
  "data": {
    "prediction": {
      "risk_level": "HIGH_RISK",
      "fraud_probability": 0.9225,
      "is_flagged": true,
      "recommendation": "Review required before settlement"
    },
    "disclaimer": "Demonstration ML model for simulated transaction anomaly detection based on synthetic banking dataset."
  }
}
```

### 5.2 Model Metadata & Risk Categories
- **Method & Path**: `GET /api/ml/model-info`
- **Access**: Authenticated User
- **Response `200 OK`**: Returns feature list, class weights, and evaluation summary.

### 5.3 Detailed Model Evaluation Metrics
- **Method & Path**: `GET /api/ml/metrics`
- **Access**: Administrator Only (`role: "admin"`)
- **Response `200 OK`**: Full confusion matrix, precision, recall, F1, and baseline comparison.

### 5.4 Flagged Suspicious Transactions Queue
- **Method & Path**: `GET /api/ml/transactions/flagged?page=1&limit=20`
- **Access**: Administrator Only (`role: "admin"`)
- **Response `200 OK`**: Paginated queue of transactions categorized as `SUSPICIOUS` or `HIGH_RISK`.

---

## 6. Generative AI Financial Assistant

### 6.1 Monthly Financial Summary
- **Method & Path**: `GET /api/ai/financial-summary?month=2026-10`
- **Access**: Authenticated Customer
- **Response `200 OK`**:
```json
{
  "success": true,
  "data": {
    "metrics": {
      "month": "2026-10",
      "total_deposits_inr": 10100.00,
      "total_withdrawals_inr": 100.00,
      "total_transfers_inr": 200.00,
      "net_cash_flow_inr": 9800.00,
      "mom_inflow_change_pct": 12.5,
      "mom_outflow_change_pct": -5.0
    },
    "summary": {
      "narrative": "In October 2026, your inflows totaled ₹10,100.00 against outflows of ₹300.00, resulting in a net surplus of ₹9,800.00."
    }
  }
}
```

### 6.2 Spending Velocity & Outlier Analysis
- **Method & Path**: `GET /api/ai/spending-analysis?days=30`
- **Access**: Authenticated Customer
- **Response `200 OK`**: Outflow velocity (INR/day), largest transactions, and abnormal expenditure flags.

### 6.3 Smart Savings Suggestions
- **Method & Path**: `GET /api/ai/savings-suggestions`
- **Access**: Authenticated Customer
- **Response `200 OK`**: Emergency fund target, monthly runway, and practical savings ratios.

### 6.4 Conversational Assistant Chat
- **Method & Path**: `POST /api/ai/chat`
- **Access**: Authenticated Customer
- **Request Body**:
```json
{
  "message": "How much did I spend this month?",
  "transaction_id": null
}
```
- **Response `200 OK`**:
```json
{
  "success": true,
  "data": {
    "reply": "You have spent a total of ₹300.00 this month across 2 debit transactions. Your total balance is ₹1,850.00.",
    "is_fallback": true
  }
}
```
- **Execution Refusal Trigger**: If message contains transfer instructions (e.g., *"transfer 1000 to X"*):
```json
{
  "success": true,
  "data": {
    "reply": "I am your AI Financial Assistant... For your financial security, I have no authority or capability to execute monetary transfers.",
    "action_executed": false,
    "guardrail_triggered": "TRANSACTION_EXECUTION_ATTEMPT_BLOCKED"
  }
}
```

### 6.5 Provider Configuration Info
- **Method & Path**: `GET /api/ai/provider-info`
- **Access**: Authenticated User
- **Response `200 OK`**: Reports active LLM provider (`gemini` or `openai`), model, rate limit (30/min), and fallback mode.

# User Manual & Operator Guide
## Apex Bank Core Banking & AI Financial Platform

**Version:** 1.0.0  
**Target Audience:** Customers & System Administrators  

---

## 1. Getting Started

Apex Bank is an enterprise-grade core banking application with integrated Machine Learning anomaly detection and an AI Financial Assistant.

### 1.1 Accessing the Application
- **Frontend URL**: `http://localhost:5173`
- **Backend API**: `http://127.0.0.1:5000/api`
- **Demo Credentials**:
  - **Customer**: `mluser1` / `Password123!`
  - **Administrator**: `admin` / `AdminPassword123!`

---

## 2. Customer Guide

### 2.1 Registration & Sign-In
1. Navigate to the **Sign In** page.
2. If you are a new customer, click **Register as Customer**, enter your email, unique username, full legal name, and a password ($\ge 8$ characters, letters + numbers).
3. Upon registration, you are automatically signed in and redirected to your **Dashboard**.

### 2.2 Dashboard
The Dashboard displays your total net balance across all accounts, total monthly inflows, total monthly outflows, and a reactive monthly cash flow chart powered by Recharts.
- **Account Cards**: Shows each of your Savings and Checking accounts. Click **Copy Account Number** to copy the 12-digit number for incoming transfers.
- **Quick Action Buttons**: Directly open modals for **Deposit**, **Withdrawal**, and **Transfer**.

### 2.3 Performing Banking Operations
Navigate to **Banking Operations** from the sidebar or use the quick action buttons:

1. **Deposit Funds**:
   - Select your target account from the dropdown.
   - Enter amount in INR (e.g. `500.00`).
   - Add an optional description (e.g. *"Salary Direct Deposit"*).
   - Click **Review Deposit** and confirm. A transaction receipt will be generated.
2. **Withdraw Funds**:
   - Select your account.
   - Enter amount to withdraw. Overdrafts are strictly blocked: the system will prevent withdrawals that exceed your available balance.
   - Review and submit.
3. **Transfer Funds**:
   - Select your source account.
   - Enter the **12-digit destination account number** (e.g. `100470980433`).
   - Enter the transfer amount and optional description.
   - The system validates that source and destination are active and distinct, and executes an atomic transfer.

### 2.4 Transaction History & Receipts
Navigate to **Transaction History**:
- Search by transaction ID or description.
- Filter by transaction type: `DEPOSIT`, `WITHDRAWAL`, or `TRANSFER`.
- Filter by ML risk level: `NORMAL`, `SUSPICIOUS`, or `HIGH_RISK`.
- Click on any transaction row to open the **Transaction Receipt Modal** with full ledger details.

### 2.5 Using the AI Financial Assistant
Navigate to **AI Assistant** from the sidebar:
- **Monthly Summary Tab**: Displays monthly total inflows, outflows, and net cash flow with month-over-month percentage changes and an AI narrative overview.
- **Spending Analysis Tab**: Analyzes spending velocity (INR per day), high-value debit outliers, and cash flow cadence.
- **Savings Advice Tab**: Calculates your emergency fund target (3–6 months runway) and personalized savings strategies.
- **Chat Assistant**: Ask natural-language questions about your finances:
  - *"How much did I spend this month?"*
  - *"What was my largest transaction?"*
  - *"Give me a savings tip based on my account balance."*
  - Note: For security, the assistant will refuse requests to execute monetary transfers.

### 2.6 Fraud Risk Simulator
Navigate to **Fraud Monitoring**:
- Use the **Interactive ML Risk Estimator** to test simulated transactions.
- Enter an account and an amount to see real-time fraud probability and risk tier classification (`NORMAL`, `SUSPICIOUS`, or `HIGH_RISK`).

---

## 3. Administrator Guide

### 3.1 Administrator Sign-In
Sign in using administrative credentials (`admin` / `AdminPassword123!`). The administrative sidebar unlocks exclusive oversight panels:

### 3.2 System-Wide Accounts Directory
Navigate to **Accounts** or access `/api/accounts/all`:
- View a paginated directory of every bank account across all customers in the system.
- Inspect account status, account type, and balance.

### 3.3 Flagged Transactions Queue
Navigate to **Fraud Monitoring** $\rightarrow$ **Flagged Queue**:
- Displays all transactions across the bank categorized as `SUSPICIOUS` or `HIGH_RISK`.
- Review timestamp, transaction amount, executing customer, and ML fraud probability.

### 3.4 ML Model Performance Inspector
Navigate to **Fraud Monitoring** $\rightarrow$ **Model Performance**:
- Review live model evaluation metrics:
  - **Accuracy**: $95.65\%$
  - **Precision**: $93.42\%$
  - **Recall**: $64.84\%$
  - **F1-Score**: $0.7655$
  - **ROC-AUC**: $0.8243$
- Inspect feature importances and confusion matrix breakdown.

### 3.5 Provisioning New Administrators
Administrators can securely create new administrative accounts by making an authenticated request to `POST /api/auth/admin/create-admin`. Regular customers cannot access this endpoint.

---

## 4. Troubleshooting & FAQ

- **Q: Why was my transfer rejected?**  
  *A: Transfers fail if the source account has insufficient balance, or if the destination account number does not exist or is inactive.*
- **Q: Does the AI assistant have access to my full account number?**  
  *A: No. Account numbers in prompt contexts are masked (e.g. `100****XXXX`), and passwords or session tokens are never shared with the AI.*
- **Q: Can the AI assistant transfer money on my behalf?**  
  *A: No. The AI assistant includes a security refusal guardrail that strictly blocks transaction execution commands.*

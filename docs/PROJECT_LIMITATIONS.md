# Engineering Limitations & Operational Boundaries
## Apex Bank AI-Enhanced Banking Platform

**Document Version:** 1.0.0  
**Status:** Complete & Disclosed  
**Scope:** Engineering review of system trade-offs, operational boundaries, and technical constraints.

---

## 1. Overview & Disclosure Philosophy

Apex Bank is engineered to enterprise software standards while serving as an advanced academic and demonstration platform. In keeping with rigorous engineering ethics, this document transparently details the technical limitations, design trade-offs, and external dependencies of the platform.

---

## 2. Machine Learning Pipeline Boundaries

### 2.1 Synthetic Dataset Origin
- **Constraint:** Real-world commercial banking transaction streams are legally protected under banking secrecy laws (RBI Master Directions, GDPR, GLBA, and PCI-DSS) and cannot be distributed in academic submissions.
- **Implementation:** The model was trained on 10,000 synthetic banking transactions generated via [`generate_dataset.py`](file:///d:/grad%20prjt/backend/ml/generate_dataset.py) with 8,913 normal transactions and 1,087 synthetic anomalies (~9:1 ratio).
- **Limitation:** While the synthetic generator accurately simulates four common fraud patterns (rapid succession account draining, sudden large multiples of historical average, nocturnal anomalies, and high balance depletion ratios), it does not model zero-day laundering syndicates, mule networks, or advanced adversarial evasion attacks.
- **Production Roadmap:** In a commercial environment, this model must be retrained on de-identified, tokenized banking ledger streams with monthly population stability index (PSI) tracking to detect concept drift.

### 2.2 Cold-Start Customer Heuristics
- **Constraint:** A newly registered customer has no historical transaction baseline (`customer_hist_avg_inr = 0`).
- **Implementation:** To avoid immediate false alarms on initial account opening deposits, the system defaults the rolling historical average to the transaction amount itself.
- **Limitation:** Very first transactions executed on fresh accounts have less historical context and rely primarily on absolute values, time of day, and balance ratios.

---

## 3. Generative AI Financial Assistant Constraints

### 3.1 External API Key Prerequisite
- **Constraint:** Calling cloud-hosted Large Language Models (Google Gemini 1.5 Flash or OpenAI GPT-4o) requires active cloud API credentials (`GEMINI_API_KEY` or `OPENAI_API_KEY`).
- **Implementation:** Apex Bank implements a transparent dual-engine architecture:
  - If a valid key is configured, contextual prompts are routed to Google Gemini.
  - If no key is configured, network connectivity is blocked, or the API times out, the system automatically engages an internal deterministic rule-based analysis engine.
- **Limitation:** Demonstration and automated test suites test the deterministic fallback engine to ensure tests never fail due to external API quotas or expired developer keys. Live conversational nuances require entering a valid Gemini key in `backend/.env`.

### 3.2 Non-Transactional AI Scope (Intent Guardrail)
- **Constraint:** LLMs are prone to prompt injection, hallucination, and probabilistic decision errors.
- **Implementation:** The AI assistant is strictly read-only. It has zero programmatic binding to debit, credit, or transfer execution services.
- **Limitation:** If a user prompts the AI to "Transfer 5000 INR to account X", the model is hardcoded to refuse and advise the user to use the secure Banking Accounts module. The AI cannot execute mutations on behalf of the customer.

---

## 4. Architectural & Infrastructure Limitations

### 4.1 In-Memory Rate Limiting
- **Constraint:** The current API sliding-window rate limiters (30 requests/minute for AI endpoints, authentication brute-force guards) are maintained in server process memory (`_rate_limit_tracker`).
- **Limitation:** In a multi-worker production cluster behind a load balancer (e.g. Gunicorn with multiple gevent workers), rate-limiting state is not shared across worker processes.
- **Production Roadmap:** Production deployments should swap the in-memory dictionary with a centralized Redis instance using atomic token bucket Lua scripts.

### 4.2 Development WSGI Server
- **Constraint:** The Flask application is executed via `backend/run.py` utilizing Werkzeug's single-process development server.
- **Limitation:** Suitable for local demonstration, unit testing, and evaluation, but not rated for high-concurrency public internet traffic.
- **Production Roadmap:** Production deployment requires a WSGI container such as Gunicorn (`gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"`) placed behind an Nginx reverse proxy with TLS termination.

### 4.3 Database Multi-Document ACID Prerequisite
- **Constraint:** MongoDB enforces multi-document transactions only when connected to a replica set.
- **Implementation:** Apex Bank requires launching `mongod` with `--replSet rs0`.
- **Limitation:** If executed against a standalone, non-replica-set MongoDB daemon, the application gracefully logs a warning and performs single-document updates, sacrificing multi-document cross-collection rollback.

### 4.4 Currency Support
- **Constraint:** All account balances and ledger entries are stored as 64-bit integer paise (1 INR = 100 paise) to prevent floating-point rounding errors.
- **Limitation:** Apex Bank currently operates exclusively in Indian Rupees (`INR`). Cross-border foreign exchange (FX) conversions and multi-currency accounts are not supported in the current schema.

---

## 5. Security & Compliance Boundaries

1. **Card / Payment Gateway Integration:** Apex Bank simulates direct core ledger transfers. It does not integrate with NPCI UPI gateways, Visa/Mastercard rails, or SWIFT settlement systems.
2. **Two-Factor Authentication (2FA):** User authentication utilizes Bcrypt hashed passwords and RS256/HS256 signed JSON Web Tokens. SMS OTP or TOTP-based multi-factor authentication is planned for future enterprise releases.
3. **Admin Hierarchy:** The system currently defines two discrete RBAC roles (`customer` and `admin`). Granular sub-roles (e.g., Compliance Auditor, Branch Manager, Fraud Investigator) can be introduced via permissions bitmasks in future iterations.

# Machine Learning-Based Fraud Detection Pipeline
## Apex Bank Transaction Anomaly Detection

**Model Type:** Tuned Random Forest Classifier (`RandomForestClassifier`)  
**Artifact Path:** `backend/ml/artifacts/fraud_detector.joblib`  
**Dataset Path:** `backend/ml/data/synthetic_transactions.csv`  

---

## 1. Synthetic Dataset Generation

### 1.1 Methodology & Rationale
Real financial transaction telemetry is proprietary and restricted by banking confidentiality laws (RBI, GDPR, PCI-DSS). To train and validate the anomaly detection engine ethically and reproducibly, a realistic synthetic banking dataset was generated via [`generate_dataset.py`](file:///d:/grad%20prjt/backend/ml/generate_dataset.py).

### 1.2 Dataset Properties
- **Total Samples**: 10,000 transactions.
- **Normal Transactions**: 8,913 samples (~89.1%).
- **Fraudulent / Anomalous Transactions**: 1,087 samples (~10.9%).
- **Imbalance Handling**: Class imbalance (~9:1 ratio) is handled using `class_weight='balanced'` in the Random Forest ensemble and threshold tuning.

### 1.3 Synthetic Fraud Rules
The synthetic generator embeds realistic banking fraud patterns:
1. **Rapid Succession Drains**: Transactions occurring within $< 3\text{ minutes}$ of a previous transaction with elevated amounts.
2. **Abnormal Outflow to Historical Average Ratio**: Outflows exceeding $5\times$ to $20\times$ the customer's typical historical transaction size.
3. **Nocturnal Anomaly**: Unusually high-value transactions initiated between 01:00 AM and 04:30 AM local time.
4. **Near-Total Account Drain**: A single debit transaction consuming $>90\%$ of available account balance.

---

## 2. Feature Engineering

12 input features (yielding 14 encoded features via one-hot encoding of `tx_type`) are extracted dynamically by [`MLService.extract_features_from_db`](file:///d:/grad%20prjt/backend/app/services/ml_service.py) and evaluated in [`metrics.json`](file:///d:/grad%20prjt/backend/ml/artifacts/metrics.json):

| # | Feature Name | Type | Description | Importance |
| :- | :--- | :--- | :--- | :---: |
| 1 | `time_since_last_tx_min` | Float | Minutes elapsed since the account's previous transaction. | **22.69%** |
| 2 | `amount_to_avg_ratio` | Float | Ratio of current transaction value to customer's historical mean. | **19.58%** |
| 3 | `amount_inr` | Float | Transaction amount in Indian Rupees. | **18.60%** |
| 4 | `balance_before_inr` | Float | Snapshot balance in account immediately prior to transaction. | **9.72%** |
| 5 | `balance_ratio` | Float | Ratio of transaction amount to pre-transaction balance (`amount / balance`). | **7.67%** |
| 6 | `tx_frequency_last_24h` | Integer | Count of transactions executed on account in past 24 hours. | **7.25%** |
| 7 | `customer_hist_avg_inr` | Float | Customer's rolling historical average debit transaction amount. | **5.27%** |
| 8 | `hour_of_day` | Integer | Hour of day (0–23) capturing nocturnal vs business hours. | **3.33%** |
| 9 | `is_rapid_succession` | Binary | Flag indicating activity within 3 minutes of previous transaction. | **2.12%** |
| 10 | `day_of_week` | Integer | Day of week (0 = Monday, 6 = Sunday). | **1.67%** |
| 11 | `tx_type` | Categorical | One-hot encoded transaction category: `DEPOSIT` (0.61%), `TRANSFER` (0.57%), `WITHDRAWAL` (0.51%). | **1.69%** |
| 12 | `is_weekend` | Binary | Flag indicating Saturday/Sunday activity. | **0.42%** |

*Total one-hot encoded input dimension fed to `RandomForestClassifier`: 14 columns.*

---

## 3. Model Training & Evaluation

### 3.1 Model Hyperparameters
- **Estimators**: 100 decision trees (`n_estimators=100`).
- **Class Weighting**: `class_weight='balanced'` to offset the 9:1 majority class.
- **Max Depth**: Unlimited with minimum samples split = 2.
- **Random Seed**: 42 (ensures deterministic reproducibility).
- **Split Ratio**: Stratified 80% Train (8,000 samples) / 20% Test (2,000 samples).

### 3.2 Evaluation Metrics Comparison

| Metric | Random Forest Model | Baseline (Weighted Logistic Regression) |
| :--- | :---: | :---: |
| **Accuracy** | **95.65%** | 94.45% |
| **Precision** | **93.42%** | 80.00% |
| **Recall** | **64.84%** | 65.75% |
| **F1-Score** | **0.7655** | 0.7218 |
| **ROC-AUC** | **0.8243** | 0.8338 |

### 3.3 Confusion Matrix (Test Set: 2,000 Transactions)

```
                 Predicted Negative     Predicted Positive
Actual Negative      1,771 (TN)              10 (FP)
Actual Positive         77 (FN)             142 (TP)
```
- **False Positive Rate**: $\frac{10}{1,771 + 10} = 0.56\%$ (Extremely low false alarm rate, minimizing friction for legitimate banking customers).
- **Precision**: $\frac{142}{142 + 10} = 93.42\%$ (Over 93% of flagged transactions represent true anomalies).

---

## 4. Runtime Risk Categorization

The model outputs a continuous fraud probability $p \in [0.0, 1.0]$. The banking engine maps this probability to 3 operational risk tiers:
- **`NORMAL`** ($p < 0.25$): Standard transaction. Settles immediately as `COMPLETED`.
- **`SUSPICIOUS`** ($0.25 \le p < 0.70$): Unusual timing or slightly elevated amount. Settles as `FLAGGED_SUSPICIOUS` and added to the administrative review queue.
- **`HIGH_RISK`** ($p \ge 0.70$): Severe deviation from normal behavior (e.g. rapid nocturnal drain). Settles as `FLAGGED_HIGH_RISK` with an alert sent to the customer and administrator.

---

## 5. Model Limitations & Operational Warnings

1. **Synthetic Data**: The model was trained on synthetic transaction patterns. In a production commercial bank, the pipeline should be retrained on anonymized real transaction histories.
2. **Concept Drift**: Financial fraud strategies evolve rapidly. In production, feature drift and population stability metrics (PSI) should be tracked monthly with automated retraining triggers.
3. **Cold-Start Customers**: For newly registered customers with no prior history, `customer_hist_avg_inr` defaults to the transaction amount, preventing false alarms on initial account opening deposits.

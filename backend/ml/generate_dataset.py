import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_synthetic_transactions(
    num_samples: int = 10000,
    fraud_rate: float = 0.075,
    random_seed: int = 42
) -> pd.DataFrame:
    """
    Generates a realistic, reproducible synthetic banking transactions dataset.
    
    Includes key behavioral, temporal, and financial ratio features without data leakage.
    Simulates real-world fraud patterns:
      1. Account Takeover / Balance Drainage (high balance ratio & amount spike)
      2. Rapid Succession Velocity Attack (high 24h frequency & rapid bursts)
      3. Late-Night High-Value Transfers (unusual hours + high amount-to-average)
      4. Stochastic Real-World Label Noise
    """
    np.random.seed(random_seed)
    random.seed(random_seed)

    records = []
    num_fraud_target = int(num_samples * fraud_rate)
    num_normal_target = num_samples - num_fraud_target

    base_time = datetime(2026, 1, 1, 0, 0, 0)

    # 1. Generate Normal Transactions
    for i in range(num_normal_target):
        # Transaction Type distribution: 45% Transfers, 35% Withdrawals, 20% Deposits
        tx_type = np.random.choice(["TRANSFER", "WITHDRAWAL", "DEPOSIT"], p=[0.45, 0.35, 0.20])
        
        # Historical average amount for this customer
        hist_avg = float(np.random.lognormal(mean=7.0, sigma=0.6))  # typical ~1,000 - 3,000 INR
        hist_avg = max(100.0, round(hist_avg, 2))

        # Amount typically close to historical average
        amount_multiplier = float(np.random.exponential(scale=1.0))
        amount_multiplier = np.clip(amount_multiplier, 0.1, 3.5)
        amount = round(hist_avg * amount_multiplier, 2)
        amount = max(10.0, amount)

        # Balance before transaction: usually comfortable multiple of amount
        balance_multiple = float(np.random.uniform(2.5, 20.0))
        balance_before = round(max(amount * balance_multiple, 1500.0), 2)

        # Normal operating hours: mostly daytime / evening (8:00 AM to 10:00 PM)
        if np.random.rand() < 0.88:
            hour = int(np.random.randint(8, 23))
        else:
            hour = int(np.random.randint(0, 8))

        day_of_week = int(np.random.randint(0, 7))
        is_weekend = 1 if day_of_week in [5, 6] else 0

        # Frequency in last 24h (1 to 5 normal transactions)
        tx_frequency_last_24h = int(np.random.choice([1, 2, 3, 4, 5], p=[0.45, 0.30, 0.15, 0.07, 0.03]))

        # Time since last transaction (normally hours to days apart)
        time_since_last_tx_minutes = float(np.random.uniform(15.0, 1440.0))
        is_rapid_succession = 1 if time_since_last_tx_minutes < 5.0 else 0

        # Derived Ratios
        balance_ratio = round(amount / (balance_before + 1.0), 4)
        amount_to_avg_ratio = round(amount / (hist_avg + 1.0), 4)

        records.append({
            "account_id": f"acc_{random.randint(1000, 9999)}",
            "amount_inr": amount,
            "tx_type": tx_type,
            "hour_of_day": hour,
            "day_of_week": day_of_week,
            "is_weekend": is_weekend,
            "tx_frequency_last_24h": tx_frequency_last_24h,
            "balance_before_inr": balance_before,
            "balance_ratio": balance_ratio,
            "customer_hist_avg_inr": hist_avg,
            "amount_to_avg_ratio": amount_to_avg_ratio,
            "time_since_last_tx_min": round(time_since_last_tx_minutes, 1),
            "is_rapid_succession": is_rapid_succession,
            "is_fraud": 0
        })

    # 2. Generate Fraudulent Transactions
    for i in range(num_fraud_target):
        fraud_type = np.random.choice(["DRAINAGE", "VELOCITY", "NIGHT_SPIKE"], p=[0.40, 0.35, 0.25])
        
        # Fraud happens on transfers or withdrawals (fraudsters rarely deposit stolen money without cashout)
        tx_type = np.random.choice(["TRANSFER", "WITHDRAWAL"], p=[0.65, 0.35])

        hist_avg = float(np.random.lognormal(mean=6.8, sigma=0.5))
        hist_avg = max(100.0, round(hist_avg, 2))

        if fraud_type == "DRAINAGE":
            # Account Takeover: sudden massive drain of balance
            balance_before = float(np.random.uniform(20000.0, 150000.0))
            drain_pct = float(np.random.uniform(0.78, 0.98))
            amount = round(balance_before * drain_pct, 2)
            hour = int(np.random.randint(0, 24))
            tx_frequency_last_24h = int(np.random.randint(2, 8))
            time_since_last_tx_minutes = float(np.random.uniform(5.0, 60.0))

        elif fraud_type == "VELOCITY":
            # Card-testing / Rapid Burst Attack
            balance_before = float(np.random.uniform(10000.0, 80000.0))
            amount = round(float(np.random.uniform(3000.0, 15000.0)), 2)
            hour = int(np.random.randint(0, 24))
            tx_frequency_last_24h = int(np.random.randint(8, 22))
            time_since_last_tx_minutes = float(np.random.uniform(0.5, 4.2))

        else:  # NIGHT_SPIKE
            # Late Night High-Value Transfer (01:00 to 04:30 AM)
            balance_before = float(np.random.uniform(35000.0, 200000.0))
            amount = round(hist_avg * float(np.random.uniform(5.0, 15.0)), 2)
            amount = min(amount, balance_before * 0.90)
            hour = int(np.random.choice([1, 2, 3, 4]))
            tx_frequency_last_24h = int(np.random.randint(3, 10))
            time_since_last_tx_minutes = float(np.random.uniform(1.0, 25.0))

        day_of_week = int(np.random.randint(0, 7))
        is_weekend = 1 if day_of_week in [5, 6] else 0
        is_rapid_succession = 1 if time_since_last_tx_minutes < 5.0 else 0

        balance_ratio = round(amount / (balance_before + 1.0), 4)
        amount_to_avg_ratio = round(amount / (hist_avg + 1.0), 4)

        records.append({
            "account_id": f"acc_{random.randint(1000, 9999)}",
            "amount_inr": amount,
            "tx_type": tx_type,
            "hour_of_day": hour,
            "day_of_week": day_of_week,
            "is_weekend": is_weekend,
            "tx_frequency_last_24h": tx_frequency_last_24h,
            "balance_before_inr": round(balance_before, 2),
            "balance_ratio": balance_ratio,
            "customer_hist_avg_inr": hist_avg,
            "amount_to_avg_ratio": amount_to_avg_ratio,
            "time_since_last_tx_min": round(time_since_last_tx_minutes, 1),
            "is_rapid_succession": is_rapid_succession,
            "is_fraud": 1
        })

    # Shuffle dataset
    df = pd.DataFrame(records)
    df = df.sample(frac=1.0, random_state=random_seed).reset_index(drop=True)

    # 3. Add 4% realistic stochastic noise (label flipping)
    # This prevents artificial 100% memorization and mirrors real-world noise
    noise_indices = np.random.choice(len(df), size=int(0.04 * len(df)), replace=False)
    for idx in noise_indices:
        df.loc[idx, "is_fraud"] = 1 - df.loc[idx, "is_fraud"]

    return df

if __name__ == "__main__":
    output_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "synthetic_transactions.csv")
    
    print(f"Generating synthetic transactions dataset (seed=42)...")
    df = generate_synthetic_transactions(num_samples=10000, fraud_rate=0.075)
    df.to_csv(csv_path, index=False)
    
    fraud_count = (df['is_fraud'] == 1).sum()
    normal_count = (df['is_fraud'] == 0).sum()
    print(f"[SUCCESS] Saved {len(df)} transactions to: {csv_path}")
    print(f"  Normal  : {normal_count} ({normal_count / len(df) * 100:.1f}%)")
    print(f"  Fraud   : {fraud_count} ({fraud_count / len(df) * 100:.1f}%)")

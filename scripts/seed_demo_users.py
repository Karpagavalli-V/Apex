"""
Seed Demo Users and Realistic Financial Transaction History for Apex Bank.
Creates 4 users (Charu, Maha, Suruthika, Divya) with valid Bcrypt passwords,
bank accounts (Savings / Checking), and rich double-entry transaction ledgers.
"""

import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend directory is in python path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

load_dotenv(dotenv_path=backend_dir / ".env")

from pymongo import MongoClient
from app.extensions import password_manager
from app.models.account import Account

USERS_CONFIG = [
    {
        "full_name": "Charu",
        "email": "charu@example.com",
        "username": "charu_01",
        "password": "Charu@1234",
    },
    {
        "full_name": "Maha",
        "email": "maha@example.com",
        "username": "maha_02",
        "password": "Maha@1234",
    },
    {
        "full_name": "Suruthika",
        "email": "suruthika@example.com",
        "username": "suruthika_03",
        "password": "Suru@1234",
    },
    {
        "full_name": "Divya",
        "email": "divya@example.com",
        "username": "divya_04",
        "password": "Divya@1234",
    },
]

def seed_users_and_history():
    mongo_uri = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
    db_name = os.getenv("DB_NAME", "banking_dev")

    print(f"Connecting to database: {db_name}...")
    client = MongoClient(mongo_uri)
    db = client[db_name]

    now = datetime.now(timezone.utc)
    user_map = {}
    account_map = {}

    print("\n--- 1. SEEDING / UPDATING USERS ---")
    for u in USERS_CONFIG:
        email = u["email"].lower().strip()
        username = u["username"].strip()
        pwd_hash = password_manager.hash_password(u["password"])

        existing = db.users.find_one({"$or": [{"email": email}, {"username": username}]})
        if existing:
            user_id = existing["user_id"]
            db.users.update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "password_hash": pwd_hash,
                        "full_name": u["full_name"],
                        "role": "customer",
                        "is_active": True,
                        "updated_at": now
                    }
                }
            )
            print(f"[UPDATED] User '{username}' ({email}) -> password reset to '{u['password']}'")
        else:
            user_id = f"usr_{uuid.uuid4().hex[:12]}"
            doc = {
                "user_id": user_id,
                "email": email,
                "username": username,
                "password_hash": pwd_hash,
                "full_name": u["full_name"],
                "role": "customer",
                "is_active": True,
                "created_at": now - timedelta(days=45),
                "updated_at": now
            }
            db.users.insert_one(doc)
            print(f"[CREATED] User '{username}' ({email}) -> user_id: {user_id}")

        user_map[username] = user_id

    print("\n--- 2. CREATING / RETRIEVING BANK ACCOUNTS ---")
    for username, user_id in user_map.items():
        # Check existing primary savings account
        existing_acc = db.accounts.find_one({"user_id": user_id, "account_type": "SAVINGS"})
        if not existing_acc:
            acc_id = f"acc_{uuid.uuid4().hex[:12]}"
            acc_num = Account.generate_account_number()
            acc_doc = {
                "account_id": acc_id,
                "account_number": acc_num,
                "user_id": user_id,
                "account_type": "SAVINGS",
                "balance_paise": 0,
                "currency": "INR",
                "status": "ACTIVE",
                "created_at": now - timedelta(days=40),
                "updated_at": now
            }
            db.accounts.insert_one(acc_doc)
            account_map[f"{username}_savings"] = acc_doc
            print(f"[CREATED] SAVINGS account {acc_num} for {username}")
        else:
            account_map[f"{username}_savings"] = existing_acc
            print(f"[EXISTS] SAVINGS account {existing_acc['account_number']} for {username}")

    # Create a secondary checking account for Charu for self-transfer demonstration
    charu_user_id = user_map["charu_01"]
    charu_checking = db.accounts.find_one({"user_id": charu_user_id, "account_type": "CHECKING"})
    if not charu_checking:
        chk_id = f"acc_{uuid.uuid4().hex[:12]}"
        chk_num = Account.generate_account_number()
        chk_doc = {
            "account_id": chk_id,
            "account_number": chk_num,
            "user_id": charu_user_id,
            "account_type": "CHECKING",
            "balance_paise": 0,
            "currency": "INR",
            "status": "ACTIVE",
            "created_at": now - timedelta(days=20),
            "updated_at": now
        }
        db.accounts.insert_one(chk_doc)
        account_map["charu_01_checking"] = chk_doc
        print(f"[CREATED] CHECKING account {chk_num} for charu_01")
    else:
        account_map["charu_01_checking"] = charu_checking
        print(f"[EXISTS] CHECKING account {charu_checking['account_number']} for charu_01")

    print("\n--- 3. SEEDING REALISTIC FINANCIAL TRANSACTION LEDGERS ---")
    # Helper to add transaction and update balance
    def execute_record(acc_key, user_id, tx_type, amount_inr, description, days_ago, risk_level="NORMAL", fraud_prob=0.02, counterparty_key=None):
        acc = account_map[acc_key]
        amount_paise = int(amount_inr * 100)
        current_bal = acc["balance_paise"]

        if tx_type == "DEPOSIT":
            new_bal = current_bal + amount_paise
        elif tx_type in ("WITHDRAWAL", "TRANSFER"):
            new_bal = max(0, current_bal - amount_paise)
        else:
            new_bal = current_bal

        tx_time = now - timedelta(days=days_ago, hours=days_ago % 8, minutes=days_ago * 7 % 50)
        counterparty_id = account_map[counterparty_key]["account_id"] if counterparty_key else None

        tx_doc = {
            "transaction_id": f"tx_{uuid.uuid4().hex[:14]}",
            "account_id": acc["account_id"],
            "user_id": user_id,
            "type": tx_type,
            "amount_paise": amount_paise,
            "balance_after_paise": new_bal,
            "status": "COMPLETED",
            "risk_level": risk_level,
            "fraud_probability": fraud_prob,
            "description": description,
            "counterparty_account_id": counterparty_id,
            "idempotency_key": str(uuid.uuid4()),
            "timestamp": tx_time,
            "metadata": {
                "channel": "ONLINE_PORTAL",
                "counterparty_number": account_map[counterparty_key]["account_number"] if counterparty_key else None
            }
        }
        db.transactions.insert_one(tx_doc)
        acc["balance_paise"] = new_bal
        return tx_doc

    reset_mode = "--reset" in sys.argv or "--refresh" in sys.argv
    if reset_mode:
        print("\n--- RESET REQUESTED: Purging previous demo transactions ---")
        demo_user_ids = list(user_map.values())
        db.transactions.delete_many({"user_id": {"$in": demo_user_ids}})
        for acc in account_map.values():
            acc["balance_paise"] = 0
            db.accounts.update_one({"account_id": acc["account_id"]}, {"$set": {"balance_paise": 0}})
        print("[RESET] Cleaned transactions and reset account balances.")

    # Check if charu already has transactions
    charu_tx_count = db.transactions.count_documents({"user_id": charu_user_id})
    if charu_tx_count < 3 or reset_mode:
        print("Adding realistic transaction streams...")
        # 1. Charu's activity
        execute_record("charu_01_savings", charu_user_id, "DEPOSIT", 45000.0, "Monthly Salary Direct Deposit", 28)
        execute_record("charu_01_savings", charu_user_id, "WITHDRAWAL", 3500.0, "ATM Cash Withdrawal", 24)
        execute_record("charu_01_savings", charu_user_id, "DEPOSIT", 8500.0, "Freelance Consulting Retainer", 20)
        execute_record("charu_01_savings", charu_user_id, "WITHDRAWAL", 1850.0, "Supermarket & Grocery Debit", 16)
        execute_record("charu_01_savings", charu_user_id, "TRANSFER", 2000.0, "Dinner & Outing Split", 14, counterparty_key="maha_02_savings")
        execute_record("charu_01_savings", charu_user_id, "DEPOSIT", 15000.0, "Quarterly Performance Bonus", 10)
        execute_record("charu_01_savings", charu_user_id, "WITHDRAWAL", 4200.0, "Utility & Electricity Bills", 7)
        execute_record("charu_01_savings", charu_user_id, "TRANSFER", 5000.0, "Transfer to Checking Reserve", 4, counterparty_key="charu_01_checking")
        execute_record("charu_01_checking", charu_user_id, "DEPOSIT", 5000.0, "Opening Transfer from Savings", 4)
        execute_record("charu_01_savings", charu_user_id, "DEPOSIT", 5000.0, "Repayment from Divya", 2, counterparty_key="divya_04_savings")
        execute_record("charu_01_savings", charu_user_id, "WITHDRAWAL", 2500.0, "Supermarket & Household Expenses", 1)

        # 2. Maha's activity
        maha_id = user_map["maha_02"]
        execute_record("maha_02_savings", maha_id, "DEPOSIT", 30000.0, "Monthly Inflow / Salary", 27)
        execute_record("maha_02_savings", maha_id, "DEPOSIT", 2000.0, "Transfer Received from Charu", 14, counterparty_key="charu_01_savings")
        execute_record("maha_02_savings", maha_id, "WITHDRAWAL", 3800.0, "Broadband and Cloud Subscriptions", 12)
        execute_record("maha_02_savings", maha_id, "TRANSFER", 1500.0, "Book Club Shared Expenses", 8, counterparty_key="suruthika_03_savings")
        execute_record("maha_02_savings", maha_id, "DEPOSIT", 12000.0, "Project Stipend", 3)
        execute_record("maha_02_savings", maha_id, "WITHDRAWAL", 1500.0, "Mobile & Data Recharge", 1)

        # 3. Suruthika's activity
        suru_id = user_map["suruthika_03"]
        execute_record("suruthika_03_savings", suru_id, "DEPOSIT", 25000.0, "Academic Scholarship Allowance", 26)
        execute_record("suruthika_03_savings", suru_id, "DEPOSIT", 1500.0, "Transfer Received from Maha", 8, counterparty_key="maha_02_savings")
        execute_record("suruthika_03_savings", suru_id, "WITHDRAWAL", 2600.0, "Course Books & Online Certifications", 5)
        execute_record("suruthika_03_savings", suru_id, "DEPOSIT", 8000.0, "Research Assistant Honorarium", 2)
        execute_record("suruthika_03_savings", suru_id, "TRANSFER", 1000.0, "Hostel Mess Advance", 1, counterparty_key="maha_02_savings")
        execute_record("maha_02_savings", maha_id, "DEPOSIT", 1000.0, "Mess Advance Received from Suruthika", 1, counterparty_key="suruthika_03_savings")

        # 4. Divya's activity
        divya_id = user_map["divya_04"]
        execute_record("divya_04_savings", divya_id, "DEPOSIT", 55000.0, "Client Retainer Disbursement", 29)
        execute_record("divya_04_savings", divya_id, "TRANSFER", 5000.0, "Transfer to Charu", 2, counterparty_key="charu_01_savings")
        execute_record("divya_04_savings", divya_id, "WITHDRAWAL", 6200.0, "Design Tablet & Accessories Purchase", 6)
        execute_record("divya_04_savings", divya_id, "DEPOSIT", 18000.0, "Consulting Fee Settlement", 1)

        print("[SUCCESS] All realistic transactions seeded.")
    else:
        print(f"[EXISTS] Found existing transaction history ({charu_tx_count} transactions).")

    # Update account balances to reflect all mutations
    print("\n--- 4. SYNCHRONIZING EXACT ACCOUNT BALANCES ---")
    for acc_key, acc_doc in account_map.items():
        acc_id = acc_doc["account_id"]
        # Find latest transaction balance or keep current
        latest_tx = db.transactions.find_one({"account_id": acc_id}, sort=[("timestamp", -1)])
        if latest_tx:
            final_paise = latest_tx["balance_after_paise"]
        else:
            final_paise = acc_doc["balance_paise"]

        db.accounts.update_one(
            {"account_id": acc_id},
            {"$set": {"balance_paise": final_paise, "updated_at": now}}
        )
        print(f"  Account {acc_doc['account_number']} ({acc_doc['account_type']}): ₹{final_paise / 100:,.2f}")

    print("\n=======================================================")
    print("DEMO USERS & RECORDS SEEDING COMPLETED SUCCESSFULLY!")
    print("=======================================================")
    print("\nCustomer Sign-In Credentials:")
    for u in USERS_CONFIG:
        print(f"  • {u['full_name']}: Username: '{u['username']}' | Password: '{u['password']}'")

if __name__ == "__main__":
    seed_users_and_history()


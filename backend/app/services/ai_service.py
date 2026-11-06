import json
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from flask import current_app

from app.extensions import mongo_manager
from app.services.llm_client import LLMClient
from app.services.ai_prompts import AIPrompts
from app.utils.errors import ValidationError, NotFoundError, RateLimitError
from app.utils.logger import logger

class AIService:
    """
    Generative AI Financial Service Layer.
    Provides:
      1. AI Monthly Financial Summary & MoM Comparison
      2. In-Depth Spending Analysis & Anomaly Highlighting
      3. Practical, Conservative Savings Recommendations
      4. Contextual AI Financial Chatbot with Security Guardrails
      5. In-Memory Sliding-Window Rate Limiting
      6. 100% Deterministic Fallback on LLM Failure
    """

    # In-memory sliding window rate limiter: {user_id: [timestamp, ...]}
    _rate_limit_tracker: Dict[str, List[datetime]] = {}

    @classmethod
    def check_rate_limit(cls, user_id: str):
        """
        Enforces user-level sliding window rate limiting.
        Raises RateLimitError (HTTP 429) if exceeded.
        """
        limit = current_app.config.get("AI_RATE_LIMIT_PER_MINUTE", 30)
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=60)

        timestamps = cls._rate_limit_tracker.get(user_id, [])
        # Prune old timestamps
        valid_timestamps = [ts for ts in timestamps if ts > window_start]

        if len(valid_timestamps) >= limit:
            logger.warning(f"Rate limit exceeded for user '{user_id}': {len(valid_timestamps)} reqs in 60s")
            cls._rate_limit_tracker[user_id] = valid_timestamps
            raise RateLimitError(
                f"AI service rate limit exceeded ({limit} requests/minute). Please wait a moment before trying again."
            )

        valid_timestamps.append(now)
        cls._rate_limit_tracker[user_id] = valid_timestamps

    @classmethod
    def reset_rate_limits(cls):
        """Utility for test suites to reset rate limit state."""
        cls._rate_limit_tracker.clear()

    @staticmethod
    def _mask_account_number(account_number: str) -> str:
        """Masks 12-digit account number as 100****XXXX."""
        if not account_number or len(account_number) < 7:
            return "******"
        return f"{account_number[:3]}****{account_number[-4:]}"

    @classmethod
    def get_user_monthly_aggregation(cls, user_id: str, target_month: Optional[str] = None) -> Dict[str, Any]:
        """
        Computes mathematically exact monthly financial metrics from immutable ledger transactions.
        Stores amounts strictly in integer paise; formats in INR.
        """
        db = mongo_manager.get_db()
        if db is None:
            raise RuntimeError("Database service is currently unavailable.")

        # Determine target month date bounds (UTC)
        now = datetime.now(timezone.utc)
        if target_month:
            match = re.match(r"^(\d{4})-(\d{2})$", target_month.strip())
            if not match:
                raise ValidationError("Invalid month format. Expected 'YYYY-MM' (e.g. '2026-10').")
            year, month = int(match.group(1)), int(match.group(2))
            if month < 1 or month > 12:
                raise ValidationError("Invalid month value. Must be between 01 and 12.")
        else:
            # Default to latest month with transaction data, or current month
            latest_tx = db.transactions.find_one({"user_id": user_id}, sort=[("timestamp", -1)])
            if latest_tx and isinstance(latest_tx.get("timestamp"), datetime):
                latest_dt = latest_tx["timestamp"]
                year, month = latest_dt.year, latest_dt.month
            else:
                year, month = now.year, now.month

        # Calculate month date ranges
        start_of_month = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)
        if month == 12:
            end_of_month = datetime(year + 1, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
            prev_year, prev_month = year, 11
        else:
            end_of_month = datetime(year, month + 1, 1, 0, 0, 0, tzinfo=timezone.utc)
            prev_year = year - 1 if month == 1 else year
            prev_month = 12 if month == 1 else month - 1

        start_of_prev_month = datetime(prev_year, prev_month, 1, 0, 0, 0, tzinfo=timezone.utc)
        end_of_prev_month = start_of_month

        month_label = f"{year:04d}-{month:02d}"
        prev_month_label = f"{prev_year:04d}-{prev_month:02d}"

        # 1. Fetch current month transactions for authenticated user
        txs_cursor = db.transactions.find({
            "user_id": user_id,
            "status": "COMPLETED",
            "timestamp": {"$gte": start_of_month, "$lt": end_of_month}
        }).sort("timestamp", -1)
        current_txs = list(txs_cursor)

        dep_paise = sum(tx["amount_paise"] for tx in current_txs if tx.get("type") == "DEPOSIT")
        wth_paise = sum(tx["amount_paise"] for tx in current_txs if tx.get("type") == "WITHDRAWAL")
        trf_paise = sum(tx["amount_paise"] for tx in current_txs if tx.get("type") == "TRANSFER")

        dep_count = sum(1 for tx in current_txs if tx.get("type") == "DEPOSIT")
        wth_count = sum(1 for tx in current_txs if tx.get("type") == "WITHDRAWAL")
        trf_count = sum(1 for tx in current_txs if tx.get("type") == "TRANSFER")

        net_flow_paise = dep_paise - (wth_paise + trf_paise)
        total_outflow_paise = wth_paise + trf_paise

        # 2. Fetch prior month transactions for month-over-month comparison
        prev_cursor = db.transactions.find({
            "user_id": user_id,
            "status": "COMPLETED",
            "timestamp": {"$gte": start_of_prev_month, "$lt": end_of_prev_month}
        })
        prev_txs = list(prev_cursor)
        prev_dep_paise = sum(tx["amount_paise"] for tx in prev_txs if tx.get("type") == "DEPOSIT")
        prev_wth_paise = sum(tx["amount_paise"] for tx in prev_txs if tx.get("type") == "WITHDRAWAL")
        prev_trf_paise = sum(tx["amount_paise"] for tx in prev_txs if tx.get("type") == "TRANSFER")
        prev_outflow_paise = prev_wth_paise + prev_trf_paise

        has_prior_month = len(prev_txs) > 0

        # Calculate MoM Deltas
        def calc_pct_change(curr: int, prev: int) -> Optional[float]:
            if prev <= 0:
                return None
            return round(((curr - prev) / float(prev)) * 100.0, 1)

        mom_inflow_change_pct = calc_pct_change(dep_paise, prev_dep_paise) if has_prior_month else None
        mom_outflow_change_pct = calc_pct_change(total_outflow_paise, prev_outflow_paise) if has_prior_month else None

        # 3. Current Account Balances
        accounts = list(db.accounts.find({"user_id": user_id, "status": "ACTIVE"}))
        total_balance_paise = sum(acc.get("balance_paise", 0) for acc in accounts)

        # Build clean sample transactions list
        sample_txs = []
        for tx in current_txs[:5]:
            sample_txs.append({
                "type": tx.get("type"),
                "amount_inr": round(tx.get("amount_paise", 0) / 100.0, 2),
                "description": tx.get("description", ""),
                "date": tx.get("timestamp").strftime("%Y-%m-%d %H:%M") if tx.get("timestamp") else ""
            })

        return {
            "month": month_label,
            "previous_month": prev_month_label,
            "has_prior_month_data": has_prior_month,
            "deposit_count": dep_count,
            "withdrawal_count": wth_count,
            "transfer_count": trf_count,
            "total_transactions": len(current_txs),
            "total_deposits_paise": dep_paise,
            "total_deposits_inr": round(dep_paise / 100.0, 2),
            "total_withdrawals_paise": wth_paise,
            "total_withdrawals_inr": round(wth_paise / 100.0, 2),
            "total_transfers_paise": trf_paise,
            "total_transfers_inr": round(trf_paise / 100.0, 2),
            "total_outflow_paise": total_outflow_paise,
            "total_outflow_inr": round(total_outflow_paise / 100.0, 2),
            "net_cash_flow_paise": net_flow_paise,
            "net_cash_flow_inr": round(net_flow_paise / 100.0, 2),
            "current_balance_paise": total_balance_paise,
            "current_balance_inr": round(total_balance_paise / 100.0, 2),
            "mom_comparison": {
                "has_prior_data": has_prior_month,
                "inflow_change_pct": mom_inflow_change_pct,
                "outflow_change_pct": mom_outflow_change_pct,
                "prev_deposits_inr": round(prev_dep_paise / 100.0, 2),
                "prev_outflow_inr": round(prev_outflow_paise / 100.0, 2)
            },
            "sample_transactions": sample_txs
        }

    @classmethod
    def generate_financial_summary(cls, user_id: str, month: Optional[str] = None) -> Dict[str, Any]:
        """Generates AI Monthly Financial Summary with MoM comparison and deterministic fallback."""
        cls.check_rate_limit(user_id)
        agg = cls.get_user_monthly_aggregation(user_id, month)

        # Format comparison text for prompt
        mom = agg["mom_comparison"]
        if mom["has_prior_data"]:
            inflow_txt = f"{mom['inflow_change_pct']:+.1f}%" if mom['inflow_change_pct'] is not None else "N/A"
            outflow_txt = f"{mom['outflow_change_pct']:+.1f}%" if mom['outflow_change_pct'] is not None else "N/A"
            mom_text = (
                f"- Prior month ({agg['previous_month']}) deposits: ₹{mom['prev_deposits_inr']:,.2f}, "
                f"outflows: ₹{mom['prev_outflow_inr']:,.2f}\n"
                f"- Inflow change: {inflow_txt} | Outflow change: {outflow_txt}"
            )
        else:
            mom_text = "No previous month activity recorded. Initial baseline month."

        samples_txt = "\n".join([
            f"- {s['date']} | {s['type']} ₹{s['amount_inr']:,.2f} ({s['description'] or 'No description'})"
            for s in agg["sample_transactions"]
        ]) or "No individual transactions in this month."

        prompt_payload = {
            "month": agg["month"],
            "total_deposits_inr": agg["total_deposits_inr"],
            "deposit_count": agg["deposit_count"],
            "total_withdrawals_inr": agg["total_withdrawals_inr"],
            "withdrawal_count": agg["withdrawal_count"],
            "total_transfers_inr": agg["total_transfers_inr"],
            "transfer_count": agg["transfer_count"],
            "net_cash_flow_inr": agg["net_cash_flow_inr"],
            "current_balance_inr": agg["current_balance_inr"],
            "mom_comparison_text": mom_text,
            "sample_transactions_text": samples_txt
        }

        # Deterministic fallback generator
        def deterministic_summary():
            net = agg["net_cash_flow_inr"]
            if net > 0:
                health = "EXCELLENT" if net >= 10000.0 else "GOOD"
                overview = (
                    f"In {agg['month']}, total inflows of ₹{agg['total_deposits_inr']:,.2f} exceeded "
                    f"total outflows of ₹{agg['total_outflow_inr']:,.2f}, resulting in a net positive cash flow "
                    f"of ₹{net:,.2f}."
                )
            elif net == 0:
                health = "BALANCED"
                overview = f"In {agg['month']}, total inflows matched total outflows exactly at ₹{agg['total_deposits_inr']:,.2f}."
            else:
                health = "DEFICIT"
                overview = (
                    f"In {agg['month']}, total outflows of ₹{agg['total_outflow_inr']:,.2f} exceeded "
                    f"inflows of ₹{agg['total_deposits_inr']:,.2f}, producing a net cash deficit of ₹{abs(net):,.2f}."
                )

            obs = [
                f"Inflows: {agg['deposit_count']} deposits totaling ₹{agg['total_deposits_inr']:,.2f}.",
                f"Outflows: {agg['withdrawal_count']} withdrawals (₹{agg['total_withdrawals_inr']:,.2f}) and {agg['transfer_count']} transfers (₹{agg['total_transfers_inr']:,.2f})."
            ]
            if mom["has_prior_data"]:
                obs.append(
                    f"Month-over-month: Outflows shifted by {mom['outflow_change_pct']:+.1f}% compared to {agg['previous_month']}."
                    if mom["outflow_change_pct"] is not None else
                    f"Comparative baseline available against {agg['previous_month']}."
                )
            else:
                obs.append("This month serves as your initial operational baseline; comparative trends will appear next month.")

            takeaway = (
                f"Maintain your surplus of ₹{net:,.2f} by channeling a portion into your liquid reserve."
                if net > 0 else
                "Review recent debit spikes to bring monthly outflows into balance with your regular deposits."
            )

            return {
                "provider": "deterministic",
                "model": "rule-based-v1",
                "is_fallback": True,
                "parsed_json": {
                    "overview": overview,
                    "cash_flow_health": health,
                    "key_observations": obs,
                    "actionable_takeaway": takeaway
                }
            }

        # Execute LLM generation
        prompt = AIPrompts.financial_summary_user(prompt_payload)
        system_inst = AIPrompts.financial_summary_system()

        response = LLMClient.generate(
            prompt=prompt,
            system_instruction=system_inst,
            json_mode=True,
            deterministic_fallback_fn=deterministic_summary
        )

        # Parse & Validate structured JSON
        parsed_ai = None
        if "parsed_json" in response:
            parsed_ai = response["parsed_json"]
        else:
            try:
                raw_text = response.get("text", "")
                # Clean potential markdown fences ```json ... ```
                cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
                cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)
                parsed = json.loads(cleaned)

                # Validate expected keys
                if "overview" in parsed and "cash_flow_health" in parsed and "key_observations" in parsed:
                    parsed_ai = parsed
            except Exception as e:
                logger.warning(f"Failed to parse LLM summary JSON: {e}. Utilizing deterministic fallback.")
                fallback = deterministic_summary()
                parsed_ai = fallback["parsed_json"]
                response["is_fallback"] = True
                response["fallback_reason"] = f"JSON validation failure: {e}"

        if not parsed_ai:
            fallback = deterministic_summary()
            parsed_ai = fallback["parsed_json"]
            response["is_fallback"] = True

        return {
            "metrics": agg,
            "summary": parsed_ai,
            "provider": response.get("provider", "unknown"),
            "model": response.get("model", "unknown"),
            "is_fallback": response.get("is_fallback", False)
        }

    @classmethod
    def generate_spending_analysis(cls, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Analyzes outflow spending velocity, patterns, and outliers without assuming expense categories."""
        cls.check_rate_limit(user_id)
        if days < 7 or days > 365:
            raise ValidationError("Analysis period 'days' must be between 7 and 365 days.")

        db = mongo_manager.get_db()
        if db is None:
            raise RuntimeError("Database service is currently unavailable.")

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Query debit transactions (WITHDRAWAL & TRANSFER)
        txs_cursor = db.transactions.find({
            "user_id": user_id,
            "status": "COMPLETED",
            "type": {"$in": ["WITHDRAWAL", "TRANSFER"]},
            "timestamp": {"$gte": cutoff}
        }).sort("amount_paise", -1)
        debit_txs = list(txs_cursor)

        total_outflow_paise = sum(tx["amount_paise"] for tx in debit_txs)
        total_outflow_inr = round(total_outflow_paise / 100.0, 2)
        count = len(debit_txs)
        avg_outflow_inr = round(total_outflow_inr / count, 2) if count > 0 else 0.0
        daily_velocity_inr = round(total_outflow_inr / float(days), 2)

        # Identify outliers (> 2.5x customer average outflow)
        outlier_threshold_inr = avg_outflow_inr * 2.5
        outliers = [
            {
                "transaction_id": tx["transaction_id"],
                "type": tx["type"],
                "amount_inr": round(tx["amount_paise"] / 100.0, 2),
                "description": tx.get("description", ""),
                "date": tx["timestamp"].strftime("%Y-%m-%d %H:%M") if tx.get("timestamp") else "",
                "multiple_of_avg": round((tx["amount_paise"] / 100.0) / (avg_outflow_inr or 1.0), 1)
            }
            for tx in debit_txs
            if (tx["amount_paise"] / 100.0) >= outlier_threshold_inr and count >= 3
        ]

        # Top largest transactions
        top_txs = [
            {
                "transaction_id": tx["transaction_id"],
                "type": tx["type"],
                "amount_inr": round(tx["amount_paise"] / 100.0, 2),
                "description": tx.get("description", ""),
                "date": tx["timestamp"].strftime("%Y-%m-%d %H:%M") if tx.get("timestamp") else ""
            }
            for tx in debit_txs[:5]
        ]

        # Frequency breakdown by day
        day_counts: Dict[str, int] = {}
        day_amounts: Dict[str, float] = {}
        for tx in debit_txs:
            if tx.get("timestamp"):
                day_str = tx["timestamp"].strftime("%Y-%m-%d")
                day_counts[day_str] = day_counts.get(day_str, 0) + 1
                day_amounts[day_str] = day_amounts.get(day_str, 0.0) + (tx["amount_paise"] / 100.0)

        peak_day = max(day_amounts.items(), key=lambda x: x[1])[0] if day_amounts else "None"
        high_freq_days = [day for day, cnt in day_counts.items() if cnt >= 3]

        # Average hours between transactions
        time_deltas = []
        sorted_by_time = sorted([tx for tx in debit_txs if tx.get("timestamp")], key=lambda x: x["timestamp"])
        for i in range(1, len(sorted_by_time)):
            dt = (sorted_by_time[i]["timestamp"] - sorted_by_time[i-1]["timestamp"]).total_seconds() / 3600.0
            time_deltas.append(dt)
        avg_hours = round(sum(time_deltas) / len(time_deltas), 1) if time_deltas else 0.0

        prompt_payload = {
            "period_days": days,
            "total_outflow_inr": total_outflow_inr,
            "outflow_count": count,
            "avg_outflow_inr": avg_outflow_inr,
            "daily_outflow_rate_inr": daily_velocity_inr,
            "top_transactions_text": "\n".join([f"- {t['date']} | {t['type']} ₹{t['amount_inr']:,.2f} ({t['description']})" for t in top_txs]) or "No outflows.",
            "outliers_text": "\n".join([f"- {o['date']} | {o['type']} ₹{o['amount_inr']:,.2f} ({o['multiple_of_avg']}x average)" for o in outliers]) or "No significant single-transaction outliers detected.",
            "high_frequency_days": ", ".join(high_freq_days) or "None (consistent distribution)",
            "peak_day": f"{peak_day} (₹{day_amounts.get(peak_day, 0.0):,.2f})" if peak_day != "None" else "None",
            "avg_time_between_hours": avg_hours
        }

        # Deterministic fallback generator
        def deterministic_spending():
            if count == 0:
                return {
                    "provider": "deterministic",
                    "model": "rule-based-v1",
                    "is_fallback": True,
                    "parsed_json": {
                        "spending_pattern_summary": f"No debit transactions recorded in the past {days} days.",
                        "outlier_analysis": "Zero outflow activity detected.",
                        "frequency_observations": "No transaction frequency observations.",
                        "behavioral_insights": ["Account activity during this period consisted entirely of deposits or inactivity."]
                    }
                }

            pattern_summary = (
                f"Over the last {days} days, you conducted {count} debit operations totaling ₹{total_outflow_inr:,.2f}, "
                f"averaging ₹{avg_outflow_inr:,.2f} per transaction at a velocity of ₹{daily_velocity_inr:,.2f}/day."
            )
            outlier_analysis = (
                f"Identified {len(outliers)} unusually high transaction(s) exceeding 2.5x your average debit amount. "
                f"Peak single transaction was ₹{top_txs[0]['amount_inr']:,.2f}."
                if outliers else
                "Your debit transaction amounts were relatively homogeneous, with no single transaction spiking above 2.5x average."
            )
            freq_obs = (
                f"Spending peaked on {peak_day}. "
                f"Average spacing between debit transactions was {avg_hours:.1f} hours."
            )
            insights = [
                f"Transaction sizes center around ₹{avg_outflow_inr:,.2f} across withdrawals and transfers.",
                f"Spending velocity is tracked at approximately ₹{daily_velocity_inr:,.2f} per calendar day.",
                "Large single-day outflows represent the primary driver of balance fluctuations."
            ]
            return {
                "provider": "deterministic",
                "model": "rule-based-v1",
                "is_fallback": True,
                "parsed_json": {
                    "spending_pattern_summary": pattern_summary,
                    "outlier_analysis": outlier_analysis,
                    "frequency_observations": freq_obs,
                    "behavioral_insights": insights
                }
            }

        prompt = AIPrompts.spending_analysis_user(prompt_payload)
        system_inst = AIPrompts.spending_analysis_system()

        response = LLMClient.generate(
            prompt=prompt,
            system_instruction=system_inst,
            json_mode=True,
            deterministic_fallback_fn=deterministic_spending
        )

        parsed_ai = None
        if "parsed_json" in response:
            parsed_ai = response["parsed_json"]
        else:
            try:
                cleaned = re.sub(r"^```(?:json)?\s*", "", response.get("text", "").strip(), flags=re.MULTILINE)
                cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)
                parsed = json.loads(cleaned)
                if "spending_pattern_summary" in parsed and "behavioral_insights" in parsed:
                    parsed_ai = parsed
            except Exception as e:
                logger.warning(f"Failed to parse spending analysis JSON: {e}")
                parsed_ai = deterministic_spending()["parsed_json"]
                response["is_fallback"] = True

        if not parsed_ai:
            parsed_ai = deterministic_spending()["parsed_json"]
            response["is_fallback"] = True

        return {
            "period_days": days,
            "metrics": {
                "total_outflow_inr": total_outflow_inr,
                "transaction_count": count,
                "average_outflow_inr": avg_outflow_inr,
                "daily_velocity_inr": daily_velocity_inr,
                "outlier_count": len(outliers),
                "peak_day": peak_day,
                "average_interval_hours": avg_hours,
                "top_transactions": top_txs,
                "outliers": outliers
            },
            "analysis": parsed_ai,
            "provider": response.get("provider", "unknown"),
            "model": response.get("model", "unknown"),
            "is_fallback": response.get("is_fallback", False)
        }

    @classmethod
    def generate_savings_suggestions(cls, user_id: str) -> Dict[str, Any]:
        """Generates pragmatic, conservative savings recommendations based on actual cash flow."""
        cls.check_rate_limit(user_id)
        db = mongo_manager.get_db()
        if db is None:
            raise RuntimeError("Database service is currently unavailable.")

        # Look at last 60 days to evaluate reliable baseline cash flow
        cutoff_60 = datetime.now(timezone.utc) - timedelta(days=60)
        recent_txs = list(db.transactions.find({
            "user_id": user_id,
            "status": "COMPLETED",
            "timestamp": {"$gte": cutoff_60}
        }))

        dep_paise = sum(tx["amount_paise"] for tx in recent_txs if tx.get("type") == "DEPOSIT")
        wth_paise = sum(tx["amount_paise"] for tx in recent_txs if tx.get("type") == "WITHDRAWAL")
        trf_paise = sum(tx["amount_paise"] for tx in recent_txs if tx.get("type") == "TRANSFER")
        outflow_paise = wth_paise + trf_paise

        # Normalize to monthly scale (30-day equivalent)
        monthly_inflow_inr = round((dep_paise / 100.0) / 2.0, 2)
        monthly_outflow_inr = round((outflow_paise / 100.0) / 2.0, 2)
        monthly_net_inr = round(monthly_inflow_inr - monthly_outflow_inr, 2)

        # Total current liquid balances across accounts
        accounts = list(db.accounts.find({"user_id": user_id, "status": "ACTIVE"}))
        total_balance_inr = round(sum(acc.get("balance_paise", 0) for acc in accounts) / 100.0, 2)

        # Target emergency fund = 3 months outflow
        emergency_fund_target_inr = round(monthly_outflow_inr * 3.0, 2)
        coverage_months = round(total_balance_inr / (monthly_outflow_inr or 1.0), 1)

        savings_rate = 0.0
        if monthly_inflow_inr > 0:
            savings_rate = max(0.0, min(100.0, round((monthly_net_inr / monthly_inflow_inr) * 100.0, 1)))

        prompt_payload = {
            "net_flow_inr": monthly_net_inr,
            "inflow_inr": monthly_inflow_inr,
            "outflow_inr": monthly_outflow_inr,
            "savings_rate_pct": savings_rate,
            "current_balance_inr": total_balance_inr,
            "emergency_fund_target_inr": emergency_fund_target_inr,
            "emergency_fund_coverage_months": coverage_months
        }

        def deterministic_savings():
            if monthly_net_inr > 0:
                health = "STRONG" if savings_rate >= 20.0 else "MODERATE"
                recommended_target = round(monthly_net_inr * 0.40, 2)
                recs = [
                    f"Automate monthly savings of ₹{recommended_target:,.2f} (approx. 40% of your ₹{monthly_net_inr:,.2f} surplus) immediately following regular deposit dates.",
                    f"Work toward an emergency liquidity reserve of ₹{emergency_fund_target_inr:,.2f} (currently at {coverage_months:.1f} months of expenses).",
                    "Keep surplus funds in your interest-bearing SAVINGS account to preserve liquidity while minimizing impulsive withdrawals."
                ]
            else:
                health = "NEGATIVE_CASH_FLOW" if monthly_net_inr < 0 else "AT_RISK"
                recommended_target = 1000.0
                recs = [
                    "Identify and smooth out single-day withdrawal spikes to bring outflows below total deposits.",
                    f"Target a modest introductory buffer of ₹{recommended_target:,.2f} each month before scaling up larger savings commitments.",
                    "Review high-frequency transfer habits to retain cash reserves inside your primary account."
                ]

            return {
                "provider": "deterministic",
                "model": "rule-based-v1",
                "is_fallback": True,
                "parsed_json": {
                    "savings_health_rating": health,
                    "recommended_monthly_savings_inr": recommended_target,
                    "emergency_fund_status": f"Current balance covers {coverage_months:.1f} months of average outflows (Target: ₹{emergency_fund_target_inr:,.2f}).",
                    "practical_recommendations": recs,
                    "disclaimer": "These suggestions are generated for informational and budgeting planning purposes and do not constitute certified investment advice."
                }
            }

        prompt = AIPrompts.savings_suggestions_user(prompt_payload)
        system_inst = AIPrompts.savings_suggestions_system()

        response = LLMClient.generate(
            prompt=prompt,
            system_instruction=system_inst,
            json_mode=True,
            deterministic_fallback_fn=deterministic_savings
        )

        parsed_ai = None
        if "parsed_json" in response:
            parsed_ai = response["parsed_json"]
        else:
            try:
                cleaned = re.sub(r"^```(?:json)?\s*", "", response.get("text", "").strip(), flags=re.MULTILINE)
                cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)
                parsed = json.loads(cleaned)
                if "practical_recommendations" in parsed and "savings_health_rating" in parsed:
                    parsed_ai = parsed
            except Exception as e:
                logger.warning(f"Failed to parse savings suggestions JSON: {e}")
                parsed_ai = deterministic_savings()["parsed_json"]
                response["is_fallback"] = True

        if not parsed_ai:
            parsed_ai = deterministic_savings()["parsed_json"]
            response["is_fallback"] = True

        return {
            "metrics": {
                "monthly_inflow_inr": monthly_inflow_inr,
                "monthly_outflow_inr": monthly_outflow_inr,
                "monthly_net_inr": monthly_net_inr,
                "savings_rate_pct": savings_rate,
                "current_balance_inr": total_balance_inr,
                "emergency_fund_target_inr": emergency_fund_target_inr,
                "coverage_months": coverage_months
            },
            "suggestions": parsed_ai,
            "provider": response.get("provider", "unknown"),
            "model": response.get("model", "unknown"),
            "is_fallback": response.get("is_fallback", False)
        }

    @classmethod
    def process_chat(cls, user_id: str, message: str, transaction_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Processes conversational queries for the authenticated customer.
        Strictly enforces guardrails:
          - Rejects any transaction execution attempt.
          - Never discloses complete account numbers.
          - Accurately explains ML fraud risk levels (anomaly flags, not legal proof).
        """
        cls.check_rate_limit(user_id)
        msg_clean = (message or "").strip()
        if not msg_clean:
            raise ValidationError("Chat message cannot be empty.")

        db = mongo_manager.get_db()
        if db is None:
            raise RuntimeError("Database service is currently unavailable.")

        # 1. TRANSACTION EXECUTION GUARDRAIL
        # Chatbot must NEVER execute banking transactions
        exec_patterns = [
            r"\b(transfer|send|wire)\s+(?:₹|rs\.?|inr)?\s*\d+",
            r"\b(deposit|credit)\s+(?:₹|rs\.?|inr)?\s*\d+",
            r"\b(withdraw|debit)\s+(?:₹|rs\.?|inr)?\s*\d+",
            r"\bpay\s+(?:to\s+)?account\b",
            r"\bexecute\s+(?:transfer|transaction)\b"
        ]
        for pattern in exec_patterns:
            if re.search(pattern, msg_clean, re.IGNORECASE):
                return {
                    "reply": (
                        "I am your AI Financial Assistant, designed exclusively to help analyze your spending, "
                        "review your transaction history, and provide budgeting insights. For your financial security, "
                        "I have no authority or technical capability to execute monetary transfers, deposits, or withdrawals. "
                        "Please use the Banking Accounts section to initiate transfers and transactions directly and securely."
                    ),
                    "action_executed": False,
                    "guardrail_triggered": "TRANSACTION_EXECUTION_ATTEMPT_BLOCKED",
                    "provider": "security_guardrail",
                    "is_fallback": True
                }

        # 2. Gather User Financial Context
        user_doc = db.users.find_one({"user_id": user_id})
        user_name = user_doc.get("full_name") or user_doc.get("username") or "Valued Customer"

        accounts = list(db.accounts.find({"user_id": user_id, "status": "ACTIVE"}))
        accounts_summary = ", ".join([
            f"{acc.get('account_type')} ({cls._mask_account_number(acc.get('account_number'))}: ₹{acc.get('balance_paise', 0)/100.0:,.2f})"
            for acc in accounts
        ]) or "No active accounts."

        total_balance_inr = sum(acc.get("balance_paise", 0) for acc in accounts) / 100.0

        # Recent transactions
        recent_txs = list(db.transactions.find({"user_id": user_id, "status": "COMPLETED"}).sort("timestamp", -1).limit(10))
        txs_txt = "\n".join([
            f"- ID: {tx['transaction_id']} | {tx.get('type')} ₹{tx.get('amount_paise', 0)/100.0:,.2f} | Risk: {tx.get('risk_level', 'NORMAL')} (p={tx.get('fraud_probability', 0.0):.2f}) | Date: {tx.get('timestamp').strftime('%Y-%m-%d %H:%M') if tx.get('timestamp') else ''} | Desc: {tx.get('description', '')}"
            for tx in recent_txs
        ]) or "No recent transactions found."

        # Target transaction inspection if specified
        target_tx_context = ""
        target_tx = None
        if transaction_id:
            target_tx = db.transactions.find_one({"transaction_id": transaction_id.strip(), "user_id": user_id})
            if not target_tx:
                raise NotFoundError(f"Transaction '{transaction_id}' was not found or belongs to another user.")
            target_tx_context = (
                f"\nSPECIFIC TRANSACTION REQUESTED:\n"
                f"- Transaction ID: {target_tx['transaction_id']}\n"
                f"- Type: {target_tx.get('type')}\n"
                f"- Amount: ₹{target_tx.get('amount_paise', 0)/100.0:,.2f}\n"
                f"- Risk Level: {target_tx.get('risk_level', 'NORMAL')}\n"
                f"- Fraud Probability: {target_tx.get('fraud_probability', 0.0):.4f}\n"
                f"- Date: {target_tx.get('timestamp').strftime('%Y-%m-%d %H:%M') if target_tx.get('timestamp') else ''}\n"
                f"- Description: {target_tx.get('description', 'None')}\n"
            )

        context_block = f"""
Current Total Balance: ₹{total_balance_inr:,.2f}
Active Accounts: {accounts_summary}
Recent Transactions (Last 10):
{txs_txt}
{target_tx_context}
"""

        # 3. Deterministic Intent Routing / Fallback Generator
        def deterministic_chat():
            lower_msg = msg_clean.lower()
            
            # A. Explain Fraud Risk Level
            if target_tx or any(w in lower_msg for w in ["fraud", "risk", "suspicious", "flagged"]):
                tx_to_explain = target_tx or (recent_txs[0] if recent_txs else None)
                if not tx_to_explain:
                    return {
                        "provider": "deterministic",
                        "model": "rule-based-v1",
                        "is_fallback": True,
                        "reply": "You do not have any recorded transactions to explain risk for at this time."
                    }
                r_level = tx_to_explain.get("risk_level", "NORMAL")
                r_prob = tx_to_explain.get("fraud_probability", 0.0)
                amount = tx_to_explain.get("amount_paise", 0) / 100.0
                tx_id = tx_to_explain.get("transaction_id")

                if r_level == "HIGH_RISK":
                    reason = "This transaction exhibited significant deviation from normal banking patterns (such as a sudden high-percentage balance drain or extreme rapid succession velocity)."
                elif r_level == "SUSPICIOUS":
                    reason = "This transaction had unusual characteristics (such as late-night hours or slightly elevated frequency) that differed from typical daytime behavior."
                else:
                    reason = "This transaction closely matched typical financial behavior in terms of normal amount, daytime timing, and regular frequency."

                return {
                    "provider": "deterministic",
                    "model": "rule-based-v1",
                    "is_fallback": True,
                    "reply": (
                        f"Transaction {tx_id} (₹{amount:,.2f} {tx_to_explain.get('type')}) is classified as {r_level} "
                        f"with an anomaly score of {r_prob:.2f}.\n\n"
                        f"Explanation: {reason}\n\n"
                        f"Important Note: A Machine Learning risk assessment is an automated anomaly detection score "
                        f"designed to flag unusual patterns for account protection; it is not definitive legal proof of fraudulent intent."
                    )
                }

            # B. Monthly Spending Inquiry
            if any(w in lower_msg for w in ["how much did i spend", "spend this month", "total spending", "total outflow"]):
                # Calculate current month outflow
                now_dt = datetime.now(timezone.utc)
                start_m = datetime(now_dt.year, now_dt.month, 1, 0, 0, 0, tzinfo=timezone.utc)
                month_txs = list(db.transactions.find({
                    "user_id": user_id,
                    "status": "COMPLETED",
                    "type": {"$in": ["WITHDRAWAL", "TRANSFER"]},
                    "timestamp": {"$gte": start_m}
                }))
                spent_inr = sum(tx["amount_paise"] for tx in month_txs) / 100.0
                return {
                    "provider": "deterministic",
                    "model": "rule-based-v1",
                    "is_fallback": True,
                    "reply": (
                        f"You have spent a total of ₹{spent_inr:,.2f} this month across {len(month_txs)} debit transactions "
                        f"(withdrawals and transfers). Your current combined account balance is ₹{total_balance_inr:,.2f}."
                    )
                }

            # C. Largest Transactions Inquiry
            if any(w in lower_msg for w in ["largest transaction", "biggest transaction", "largest expense", "highest transaction"]):
                debit_sorted = sorted([t for t in recent_txs if t.get("type") in ["WITHDRAWAL", "TRANSFER"]], key=lambda x: x.get("amount_paise", 0), reverse=True)
                if not debit_sorted:
                    return {
                        "provider": "deterministic",
                        "model": "rule-based-v1",
                        "is_fallback": True,
                        "reply": "You have no recorded debit transactions in your recent account history."
                    }
                top3 = debit_sorted[:3]
                lines = [f"{i+1}. ₹{t.get('amount_paise', 0)/100.0:,.2f} ({t.get('type')}) on {t.get('timestamp').strftime('%b %d, %Y') if t.get('timestamp') else 'recent'} - {t.get('description') or 'No description'}" for i, t in enumerate(top3)]
                return {
                    "provider": "deterministic",
                    "model": "rule-based-v1",
                    "is_fallback": True,
                    "reply": f"Your largest recent debit transactions are:\n" + "\n".join(lines)
                }

            # D. Savings Advice Inquiry
            if any(w in lower_msg for w in ["how can i save", "save more", "savings advice", "saving tip"]):
                return {
                    "provider": "deterministic",
                    "model": "rule-based-v1",
                    "is_fallback": True,
                    "reply": (
                        f"Based on your current balance of ₹{total_balance_inr:,.2f}, here are practical ways to save more:\n"
                        f"1. Set aside 10%–20% of funds immediately upon receiving any deposit.\n"
                        f"2. Keep your primary reserves in your SAVINGS account rather than checking to reduce friction.\n"
                        f"3. Aim for an emergency reserve covering 3 months of typical outflows.\n"
                        f"Note: These suggestions are budgeting tips and do not constitute certified investment advice."
                    )
                }

            # E. Summary Inquiry
            if any(w in lower_msg for w in ["summary", "monthly financial summary", "financial overview", "overview"]):
                now_dt = datetime.now(timezone.utc)
                start_m = datetime(now_dt.year, now_dt.month, 1, 0, 0, 0, tzinfo=timezone.utc)
                dep = sum(tx["amount_paise"] for tx in db.transactions.find({"user_id": user_id, "status": "COMPLETED", "type": "DEPOSIT", "timestamp": {"$gte": start_m}})) / 100.0
                out = sum(tx["amount_paise"] for tx in db.transactions.find({"user_id": user_id, "status": "COMPLETED", "type": {"$in": ["WITHDRAWAL", "TRANSFER"]}, "timestamp": {"$gte": start_m}})) / 100.0
                net = dep - out
                return {
                    "provider": "deterministic",
                    "model": "rule-based-v1",
                    "is_fallback": True,
                    "reply": (
                        f"Here is your financial summary for this month ({now_dt.strftime('%B %Y')}):\n"
                        f"- Total Inflows (Deposits): ₹{dep:,.2f}\n"
                        f"- Total Outflows (Debits): ₹{out:,.2f}\n"
                        f"- Net Cash Flow: {'+' if net >= 0 else ''}₹{net:,.2f}\n"
                        f"- Total Account Balance: ₹{total_balance_inr:,.2f}"
                    )
                }

            # Generic Helpful Response
            return {
                "provider": "deterministic",
                "model": "rule-based-v1",
                "is_fallback": True,
                "reply": (
                    f"Hello {user_name}! I am your AI Financial Assistant. I can help you with:\n"
                    f"• 'How much did I spend this month?'\n"
                    f"• 'What are my largest transactions?'\n"
                    f"• 'Show my monthly financial summary.'\n"
                    f"• 'How can I save more?'\n"
                    f"• 'Explain this transaction's fraud-risk level.' (Include transaction ID or select a transaction)\n\n"
                    f"How can I assist your financial planning today?"
                )
            }

        # 4. Route to LLM if configured
        system_instruction = AIPrompts.chatbot_system_instruction(user_name, context_block)
        chat_prompt = f"Customer Query: {msg_clean}"

        response = LLMClient.generate(
            prompt=chat_prompt,
            system_instruction=system_instruction,
            json_mode=False,
            deterministic_fallback_fn=deterministic_chat
        )

        reply_text = response.get("text", "").strip()
        if not reply_text:
            fallback = deterministic_chat()
            reply_text = fallback["reply"]
            response["is_fallback"] = True

        return {
            "reply": reply_text,
            "action_executed": False,
            "provider": response.get("provider", "unknown"),
            "model": response.get("model", "unknown"),
            "is_fallback": response.get("is_fallback", False)
        }

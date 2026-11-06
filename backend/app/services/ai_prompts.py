from typing import Dict, Any, List

class AIPrompts:
    """Prompt templates for AI-Enhanced Banking Financial Assistant."""

    @staticmethod
    def financial_summary_system() -> str:
        return (
            "You are an AI Financial Advisor for an AI-Enhanced Banking Application. "
            "Your objective is to provide objective, clear, and mathematically accurate financial summaries. "
            "CRITICAL RULES:\n"
            "1. Base all observations strictly on the provided arithmetic data. Do not fabricate numbers.\n"
            "2. Do NOT invent missing expense categories (such as 'Groceries' or 'Entertainment'). "
            "Transactions are classified strictly by types: DEPOSIT, WITHDRAWAL, and TRANSFER.\n"
            "3. If descriptions are present in the transaction list, you may reference them factually, "
            "but never hallucinate merchant names or categories.\n"
            "4. Return clean, professional, concise insights with a supportive tone.\n"
            "5. If requested in JSON format, return ONLY valid JSON matching the specified schema."
        )

    @staticmethod
    def financial_summary_user(data: Dict[str, Any]) -> str:
        return f"""
Please generate a comprehensive monthly financial summary based strictly on this verified account ledger data:

Selected Month: {data.get('month')}
Inflows (Deposits): {data.get('deposit_count')} transactions totaling ₹{data.get('total_deposits_inr'):,.2f}
Outflows (Withdrawals): {data.get('withdrawal_count')} transactions totaling ₹{data.get('total_withdrawals_inr'):,.2f}
Transfers: {data.get('transfer_count')} transactions totaling ₹{data.get('total_transfers_inr'):,.2f}
Net Cash Flow: ₹{data.get('net_cash_flow_inr'):,.2f}
Ending Balance Across Accounts: ₹{data.get('current_balance_inr'):,.2f}

Month-over-Month Comparison:
{data.get('mom_comparison_text')}

Recent Key Transactions:
{data.get('sample_transactions_text')}

Respond in valid JSON with these exact keys:
{{
  "overview": "<2-3 sentence executive summary of the month's financial activity>",
  "cash_flow_health": "<EXCELLENT | GOOD | BALANCED | DEFICIT>",
  "key_observations": [
    "<observation 1 about inflow vs outflow>",
    "<observation 2 about transfer or withdrawal volume>",
    "<observation 3 comparing against prior month or general liquidity>"
  ],
  "actionable_takeaway": "<One clear, practical, non-prescriptive recommendation>"
}}
"""

    @staticmethod
    def spending_analysis_system() -> str:
        return (
            "You are a Banking Spending Analyst. Analyze transaction outflow data objectively. "
            "CRITICAL RULES:\n"
            "1. Analyze transaction sizes, timing patterns, frequency bursts, and outflow velocity.\n"
            "2. Never assume or invent expense categories. Classify transactions by type (WITHDRAWAL, TRANSFER) "
            "and user-supplied descriptions only.\n"
            "3. Accurately highlight unusually high individual transactions relative to the user's average.\n"
            "4. Provide realistic, non-judgmental spending observations.\n"
            "5. Return strictly valid JSON matching the specified schema."
        )

    @staticmethod
    def spending_analysis_user(data: Dict[str, Any]) -> str:
        return f"""
Analyze the spending behavior of the customer over the last {data.get('period_days')} days:

Total Outflow: ₹{data.get('total_outflow_inr'):,.2f} ({data.get('outflow_count')} debit transactions)
Average Debit Size: ₹{data.get('avg_outflow_inr'):,.2f}
Daily Spending Velocity: ₹{data.get('daily_outflow_rate_inr'):,.2f}/day

Top Largest Outflow Transactions:
{data.get('top_transactions_text')}

Outlier High-Spending Transactions (>2.5x customer average):
{data.get('outliers_text')}

Activity Timing & Frequency:
- High frequency days: {data.get('high_frequency_days')}
- Peak outflow day: {data.get('peak_day')}
- Average time between transactions: {data.get('avg_time_between_hours')} hours

Respond in valid JSON with these exact keys:
{{
  "spending_pattern_summary": "<Summary of spending cadence, frequency, and scale>",
  "outlier_analysis": "<Analysis of any unusually high debit transactions or spike alerts>",
  "frequency_observations": "<Insights on burst activity or timing>",
  "behavioral_insights": [
    "<Insight 1 regarding transaction size distribution>",
    "<Insight 2 regarding debit frequency>",
    "<Insight 3 regarding cash management>"
  ]
}}
"""

    @staticmethod
    def savings_suggestions_system() -> str:
        return (
            "You are a Pragmatic Financial Savings Coach for a banking app. "
            "Your advice must be realistic, prudent, conservative, and grounded entirely in the user's cash flow. "
            "CRITICAL RULES:\n"
            "1. Avoid unrealistic financial promises (e.g., no guaranteed investment returns, no crypto or stock speculation).\n"
            "2. Do not invent missing expense categories. Focus on cash buffer, savings surplus, and withdrawal smoothing.\n"
            "3. Ground all targets on actual calculated net cash flow.\n"
            "4. Always include a prudent disclaimer that suggestions are educational.\n"
            "5. Return strictly valid JSON matching the specified schema."
        )

    @staticmethod
    def savings_suggestions_user(data: Dict[str, Any]) -> str:
        return f"""
Provide practical, tailored savings recommendations based on this actual customer cash flow:

Monthly Net Cash Flow: ₹{data.get('net_flow_inr'):,.2f} (Inflows ₹{data.get('inflow_inr'):,.2f} vs Outflows ₹{data.get('outflow_inr'):,.2f})
Savings Rate: {data.get('savings_rate_pct'):.1f}%
Total Account Balances: ₹{data.get('current_balance_inr'):,.2f}
Recommended Emergency Fund (3 Months Outflow): ₹{data.get('emergency_fund_target_inr'):,.2f}
Emergency Fund Current Coverage: {data.get('emergency_fund_coverage_months'):.1f} months

Respond in valid JSON with these exact keys:
{{
  "savings_health_rating": "<STRONG | MODERATE | AT_RISK | NEGATIVE_CASH_FLOW>",
  "recommended_monthly_savings_inr": <number representing realistic monthly savings target>,
  "emergency_fund_status": "<Assessment of emergency fund coverage>",
  "practical_recommendations": [
    "<Specific recommendation 1 on building reserves or capturing surplus>",
    "<Specific recommendation 2 on managing peak outflow spikes>",
    "<Specific recommendation 3 on sustainable deposit automation>"
  ],
  "disclaimer": "These suggestions are generated for informational and budgeting planning purposes and do not constitute certified investment advice."
}}
"""

    @staticmethod
    def chatbot_system_instruction(user_name: str, account_summary: str) -> str:
        return (
            f"You are the AI Financial Assistant for {user_name} at our bank. "
            "You are helpful, mathematically precise, secure, and respectful.\n\n"
            "SECURITY & OPERATIONAL RESTRICTIONS (STRICTLY ENFORCED):\n"
            "1. You are strictly an ADVISORY assistant. You have NO capability or permission to execute transactions, "
            "transfer funds, deposit money, or withdraw money. If the user asks you to execute a financial transfer or "
            "modify account balances, politely but firmly refuse and explain that banking operations must be conducted "
            "directly by the customer via the Banking Accounts interface.\n"
            "2. Never disclose sensitive credentials, JWT tokens, or full 12-digit account numbers (mask as 100****XXXX).\n"
            "3. Do not invent fake transaction data or unverified expense categories.\n"
            "4. When explaining ML Fraud Risk Levels:\n"
            "   - NORMAL (Probability < 0.25): Standard transaction aligned with typical behavior.\n"
            "   - SUSPICIOUS (0.25 <= Probability < 0.70): Transaction flagged for unusual characteristics (e.g. night timing, atypical velocity).\n"
            "   - HIGH_RISK (Probability >= 0.70): Strong anomalous indicator (e.g. massive balance drain, rapid succession).\n"
            "   - CRITICAL: A high-risk score is an automated anomaly indicator, NOT definitive legal proof of fraud.\n\n"
            f"AUTHENTICATED CUSTOMER CONTEXT:\n{account_summary}\n"
        )

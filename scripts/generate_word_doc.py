import os
import re
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>'))

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def create_word_document(output_path: Path):
    doc = Document()

    # Page Margins
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Base Styles
    style_normal = doc.styles['Normal']
    style_normal.font.name = 'Calibri'
    style_normal.font.size = Pt(11)
    style_normal.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)

    # ------------------ COVER PAGE ------------------
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(40)
    p_title.paragraph_format.space_after = Pt(8)
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run("APEX BANK")
    run_title.font.name = 'Calibri'
    run_title.font.size = Pt(32)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A) # Deep Navy

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(24)
    run_sub = p_sub.add_run("AI-Enhanced Core Banking Platform with ACID Multi-Document Ledgers, Real-Time ML Anomaly Scoring & Generative Financial Insights")
    run_sub.font.name = 'Calibri'
    run_sub.font.size = Pt(14)
    run_sub.font.color.rgb = RGBColor(0x43, 0x38, 0xCA) # Indigo

    p_bar = doc.add_paragraph()
    p_bar.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_bar.paragraph_format.space_after = Pt(50)
    r_bar = p_bar.add_run("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    r_bar.font.color.rgb = RGBColor(0x63, 0x66, 0xF1)

    # Project Details Table
    meta_table = doc.add_table(rows=6, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        ("Project Type:", "Full Stack Web + Machine Learning + Generative AI Final Project"),
        ("Student / Author:", "Karpagavalli V"),
        ("Frontend Technology:", "React 19, Vite 8, Tailwind CSS, Recharts, Lucide Icons"),
        ("Backend Technology:", "Python 3.12, Flask 3.1, Bcrypt, PyJWT, RESTful Architecture"),
        ("Database Architecture:", "MongoDB 8.0 Enterprise (Replica Set rs0 / MongoDB Atlas)"),
        ("Intelligence Engines:", "Scikit-learn Random Forest (ML) & Google Gemini 3.8 Flash (GenAI)"),
    ]

    for i, (label, val) in enumerate(meta_data):
        row = meta_table.rows[i]
        c0, c1 = row.cells[0], row.cells[1]
        c0.width = Inches(2.2)
        c1.width = Inches(4.3)
        
        p0 = c0.paragraphs[0]
        r0 = p0.add_run(label)
        r0.font.bold = True
        r0.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
        
        p1 = c1.paragraphs[0]
        r1 = p1.add_run(val)
        r1.font.color.rgb = RGBColor(0x33, 0x41, 0x55)

        set_cell_margins(c0, 60, 60, 100, 100)
        set_cell_margins(c1, 60, 60, 100, 100)
        set_cell_background(c0, "F8FAFC")
        set_cell_background(c1, "FFFFFF" if i % 2 == 0 else "F8FAFC")

    doc.add_page_break()

    # Helper function to add sections
    def add_section_header(title, level=1):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(title)
        run.font.name = 'Calibri'
        run.font.bold = True
        if level == 1:
            run.font.size = Pt(18)
            run.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
        elif level == 2:
            run.font.size = Pt(14)
            run.font.color.rgb = RGBColor(0x37, 0x30, 0xA3)
        else:
            run.font.size = Pt(12)
            run.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
        return p

    def add_bullet(text, bold_prefix=""):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        if bold_prefix:
            r_bold = p.add_run(bold_prefix)
            r_bold.font.bold = True
            r_bold.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
        p.add_run(text)

    # ------------------ SECTION 1: EXECUTIVE SUMMARY ------------------
    add_section_header("1. Executive Summary & Project Overview")
    doc.add_paragraph(
        "Apex Bank is a comprehensive, production-grade core banking platform engineered from the ground up to solve "
        "the architectural, concurrency, and security weaknesses prevalent in traditional demo financial software. "
        "The system seamlessly unifies full-stack transactional banking with real-time machine learning risk classification "
        "and generative AI financial analysis."
    )
    doc.add_paragraph(
        "The application provides end-to-end support for double-entry financial accounting, multi-document ACID transfers, "
        "Google Pay-inspired 4-digit UPI Transaction PIN verification, automatic ML anomaly detection with Random Forest, "
        "and contextual financial advisory using LLM technology."
    )

    add_bullet(" 100% of ledger entries, account balances, and monetary mutations are stored in 64-bit integer paise (1 INR = 100 paise), entirely eliminating IEEE 754 floating-point drift.", "Zero Floating-Point Financial Engine:")
    add_bullet(" Inter-account fund transfers debit source accounts and credit recipient accounts inside atomic MongoDB replica set transactions with automated WriteConflict retry and jitter.", "ACID Multi-Document Atomic Engine:")
    add_bullet(" Every transaction is evaluated in real time against a 14-feature pipeline to compute fraud probabilities before ledger execution.", "Real-Time Machine Learning Anomaly Detection:")
    add_bullet(" Google Gemini 3.8 Flash synthesizes monthly cash flow velocity, runway metrics, and savings targets, protected by strict prompt-injection refusal guardrails.", "Generative AI Financial Intelligence:")
    add_bullet(" GPay / PhonePe style recipient search by Name, Phone, or Apex Pay ID (e.g., charu_01@apex) with 4-digit UPI PIN authentication.", "Apex Pay & UPI PIN Verification:")

    # ------------------ SECTION 2: SYSTEM ARCHITECTURE ------------------
    add_section_header("2. System Architecture & Component Design")
    doc.add_paragraph(
        "The system adheres to an N-Tier Clean Architecture with complete separation of concerns:"
    )
    add_bullet(" Single Page Application (SPA) built with React 19 and Tailwind CSS. Features dynamic dashboards, interactive transaction forms, real-time Recharts visualizations, and modal workflows.", "Presentation Layer (Frontend):")
    add_bullet(" REST API powered by Flask 3.1.0 and Python 3.12. Implements defense-in-depth security including Content Security Policy (CSP), Strict-Transport-Security, X-Content-Type-Options: nosniff, and PyJWT token authentication.", "Application & Gateway Layer (Backend):")
    add_bullet(" Core engine comprising BankingService (atomic transfers, overdraft guards), MLService (fraud model scoring), and AIService (LLM context assembly with deterministic fallback).", "Business Service Tier:")
    add_bullet(" MongoDB 8.0 Replica Set (or MongoDB Atlas) maintaining 5 indexed collections (users, accounts, transactions, idempotency_keys, audit_logs).", "Data Persistence Tier:")

    # ------------------ SECTION 3: MACHINE LEARNING MODULE ------------------
    add_section_header("3. Machine Learning Fraud Detection Engine")
    doc.add_paragraph(
        "The machine learning module is an integral part of the banking pipeline, designed to assess anomalous behavior "
        "and flag high-risk transactions before funds are released."
    )
    add_section_header("3.1 Feature Engineering (14 Encoded Features)", level=2)
    doc.add_paragraph(
        "The ML pipeline extracts 12 raw behavioral and temporal indicators, expanded into 14 normalized numerical inputs:"
    )
    add_bullet(" Measures the time elapsed since the user's previous transaction. Rapid transfers indicate potential automated draining (Feature Importance: 22.69%).", "1. time_since_last_tx_min:")
    add_bullet(" Ratio of current transfer amount to customer's historical average debit (Feature Importance: 19.58%).", "2. amount_to_avg_ratio:")
    add_bullet(" Absolute value of the transaction in Indian Rupees (Feature Importance: 18.60%).", "3. amount_inr:")
    add_bullet(" Account balance prior to transaction execution (Feature Importance: 9.72%).", "4. balance_before_inr:")
    add_bullet(" Percentage of available account liquidity represented by the transfer (Feature Importance: 7.67%).", "5. balance_ratio:")
    add_bullet(" Rolling count of transactions executed in the preceding 24 hours (Feature Importance: 7.25%).", "6. tx_frequency_last_24h:")
    add_bullet(" Lifetime rolling debit average for this customer (Feature Importance: 5.27%).", "7. customer_hist_avg_inr:")
    add_bullet(" Captures nocturnal and odd-hour execution patterns (Feature Importance: 3.33%).", "8. hour_of_day:")
    add_bullet(" Boolean indicator for transactions under 2 minutes apart (Feature Importance: 2.12%).", "9. is_rapid_succession:")
    add_bullet(" Categorical encoding of DEPOSIT, TRANSFER, and WITHDRAWAL (Feature Importance: 1.69%).", "10-12. tx_type One-Hot:")
    add_bullet(" Captures weekend operational anomalies (Feature Importance: 0.42%).", "13-14. day_of_week & is_weekend:")

    add_section_header("3.2 Model Architecture & Training", level=2)
    doc.add_paragraph(
        "The model is a tuned Random Forest Classifier (100 estimators, balanced class weights, max depth 12) trained on 10,000 "
        "rigorously synthesized banking records modeled after commercial fraud patterns."
    )
    doc.add_paragraph("Model Performance Metrics (Evaluated on 2,000 holdout transactions):")

    # Metrics Table
    tbl_ml = doc.add_table(rows=6, cols=3)
    tbl_ml.alignment = WD_TABLE_ALIGNMENT.CENTER
    ml_headers = ["Metric", "Random Forest Model", "Baseline (Logistic Regression)"]
    ml_rows = [
        ("Accuracy", "95.65%", "94.45%"),
        ("Precision", "93.42%", "80.00%"),
        ("Recall", "64.84%", "65.75%"),
        ("F1-Score", "0.7655", "0.7218"),
        ("ROC-AUC", "0.8243", "0.8338"),
    ]

    for j, h in enumerate(ml_headers):
        cell = tbl_ml.rows[0].cells[j]
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.bold = True
        set_cell_background(cell, "E0E7FF")
        set_cell_margins(cell, 80, 80, 100, 100)

    for i, row_data in enumerate(ml_rows):
        row = tbl_ml.rows[i + 1]
        for j, val in enumerate(row_data):
            cell = row.cells[j]
            p = cell.paragraphs[0]
            p.add_run(val)
            set_cell_background(cell, "FFFFFF" if i % 2 == 0 else "F8FAFC")
            set_cell_margins(cell, 60, 60, 100, 100)

    # ------------------ SECTION 4: GENERATIVE AI MODULE ------------------
    add_section_header("4. Generative AI Financial Intelligence Module")
    doc.add_paragraph(
        "Apex Bank integrates Google Gemini 3.8 Flash to transform complex transaction ledgers into actionable natural-language "
        "insights, personal spending breakdowns, and conservative savings targets."
    )
    add_bullet(" Synthesizes aggregated inflow, outflow, and net savings delta with month-over-month trajectory analysis.", "Monthly Cash Flow Summarizer:")
    add_bullet(" Detects abnormal debit spikes, categorical concentration, and spending acceleration.", "Spending Velocity Analysis:")
    add_bullet(" Calculates personalized 3-to-6 month emergency fund requirements based on historical living expenses.", "Emergency Runway Advisory:")
    add_bullet(" Enforces deterministic refusal guardrails that strictly block user attempts to trigger fund transfers, balance modifications, or role elevations via conversational prompts.", "Prompt-Injection Refusal Guardrails:")
    add_bullet(" In offline or rate-limited environments, the system seamlessly activates a deterministic rule-based analysis engine, guaranteeing 100% test reliability.", "Deterministic Fallback Architecture:")

    # ------------------ SECTION 5: SECURITY & UPI PIN ------------------
    add_section_header("5. Security Architecture & 4-Digit UPI PIN Verification")
    doc.add_paragraph(
        "Apex Bank implements bank-grade defensive security patterns following the STRIDE threat model:"
    )
    add_bullet(" Passwords and 4-digit UPI Transaction PINs are hashed using Bcrypt (work factor 12) with unique salts. Raw PINs are never persisted or exposed in API serializations.", "Bcrypt Hashing:")
    add_bullet(" Every customer transfer requires interactive 4-digit UPI PIN authentication via a Google Pay-style virtual keypad and masked input before ledger mutation.", "4-Digit UPI Transaction PIN:")
    add_bullet(" Stateless HMAC-SHA256 tokens carrying user identity and role. Tokens are validated via decorators on all protected endpoints.", "JWT Authentication:")
    add_bullet(" Strict segregation between Customer and Administrator privileges. Cross-account data tampering (IDOR) is mathematically prevented by enforcing ownership checks on database records.", "Role-Based Access Control (RBAC):")
    add_bullet(" Client requests include UUID v4 Idempotency-Key headers. Duplicate requests within 24 hours replay identical transaction receipts without re-debiting.", "Idempotency Protection:")

    # ------------------ SECTION 6: DATABASE SCHEMA ------------------
    add_section_header("6. Database Design & Collections")
    doc.add_paragraph(
        "Apex Bank uses 5 indexed MongoDB collections designed for referential integrity and performance:"
    )
    add_bullet(" Stores user profiles, credentials (password_hash, transaction_pin_hash), Apex Pay ID, and phone number. Unique indexes on user_id, email, username, and apex_pay_id.", "1. users:")
    add_bullet(" Stores deposit and checking accounts. Maintains 12-digit account_number, account_type, and balance_paise as a 64-bit integer. Unique index on account_number.", "2. accounts:")
    add_bullet(" Immutable double-entry financial ledger recording deposits, withdrawals, transfers, balance_after_paise, and ML risk classification.", "3. transactions:")
    add_bullet(" Mutation cache tracking idempotency_key, user_id, action, and serialized response. Includes 24-hour TTL automatic expiration index.", "4. idempotency_keys:")
    add_bullet(" Comprehensive security audit trail logging authentication events, administrative actions, and rejected overdraft attempts.", "5. audit_logs:")

    # ------------------ SECTION 7: API REFERENCE ------------------
    add_section_header("7. RESTful API Endpoint Reference")
    api_endpoints = [
        ("POST", "/api/auth/register", "Public", "Customer self-registration"),
        ("POST", "/api/auth/login", "Public", "User authentication & JWT generation"),
        ("POST", "/api/auth/transaction-pin", "Auth", "Set or update 4-digit UPI PIN"),
        ("GET", "/api/accounts", "Customer", "Retrieve owned bank accounts"),
        ("POST", "/api/accounts/{id}/transfer", "Customer", "Atomic inter-account fund transfer"),
        ("POST", "/api/accounts/{id}/deposit", "Customer", "Atomic deposit with idempotency"),
        ("POST", "/api/accounts/{id}/withdraw", "Customer", "Atomic withdrawal with overdraft guard"),
        ("GET", "/api/accounts/lookup-beneficiary", "Customer", "GPay-style beneficiary autocomplete"),
        ("POST", "/api/ml/predict-risk", "Auth", "Live ML anomaly risk scoring simulation"),
        ("GET", "/api/ml/metrics", "Admin", "Model evaluation metrics & confusion matrix"),
        ("GET", "/api/ai/financial-summary", "Customer", "Monthly cash flow GenAI analysis"),
        ("POST", "/api/ai/chat", "Customer", "Conversational AI chatbot with refusal guards"),
    ]

    tbl_api = doc.add_table(rows=len(api_endpoints) + 1, cols=4)
    tbl_api.alignment = WD_TABLE_ALIGNMENT.CENTER
    api_hdrs = ["Method", "Endpoint", "Auth Level", "Description"]
    for j, h in enumerate(api_hdrs):
        c = tbl_api.rows[0].cells[j]
        r = c.paragraphs[0].add_run(h)
        r.font.bold = True
        set_cell_background(c, "E0E7FF")
        set_cell_margins(c, 80, 80, 80, 80)

    for i, (m, ep, auth_lvl, desc) in enumerate(api_endpoints):
        row = tbl_api.rows[i + 1]
        vals = [m, ep, auth_lvl, desc]
        for j, val in enumerate(vals):
            c = row.cells[j]
            p = c.paragraphs[0]
            r = p.add_run(val)
            if j == 0:
                r.font.bold = True
                if val == "GET": r.font.color.rgb = RGBColor(0x05, 0x96, 0x69)
                elif val == "POST": r.font.color.rgb = RGBColor(0x25, 0x63, 0xEB)
            set_cell_background(c, "FFFFFF" if i % 2 == 0 else "F8FAFC")
            set_cell_margins(c, 60, 60, 80, 80)

    # ------------------ SECTION 8: INSTALLATION & RUN GUIDE ------------------
    add_section_header("8. Installation & Setup Instructions")
    doc.add_paragraph("Follow these exact steps to run the application locally:")
    add_bullet(" Ensure Python 3.12+, Node.js v18+, and MongoDB (or MongoDB Atlas connection URI) are installed.", "Step 1 (Prerequisites):")
    add_bullet(" Navigate to 'backend/', run 'python -m venv venv', activate it with 'venv\\Scripts\\activate', and install dependencies with 'pip install -r requirements.txt'.", "Step 2 (Backend Setup):")
    add_bullet(" Copy 'backend/.env.example' to 'backend/.env' and configure your MONGO_URI and JWT_SECRET_KEY.", "Step 3 (Configuration):")
    add_bullet(" Execute 'python scripts/seed_demo_users.py' to initialize the 4 demo customer accounts (Charu, Maha, Suruthika, Divya with default UPI PIN 1234).", "Step 4 (Database Seeding):")
    add_bullet(" Start the backend server by executing 'python run.py'. It will listen on http://127.0.0.1:5000.", "Step 5 (Start Backend):")
    add_bullet(" Open a second terminal, navigate to 'frontend/', run 'npm install', and start the Vite dev server with 'npm run dev'. It will listen on http://localhost:5173.", "Step 6 (Start Frontend):")

    # Save Word document
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    print(f"[SUCCESS] Word documentation generated: {output_path}")

if __name__ == "__main__":
    out_file = Path("d:/grad prjt/docs/Apex_Bank_Project_Documentation.docx")
    create_word_document(out_file)

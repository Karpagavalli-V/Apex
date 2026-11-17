import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def create_pdf_document(output_path: Path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=26,
        leading=32,
        textColor=colors.HexColor('#0F172A'),
        alignment=1, # Center
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#4338CA'),
        alignment=1,
        spaceAfter=25
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=16,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#3730A3'),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=8
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#334155'),
        leftIndent=15,
        spaceAfter=4
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#1E293B')
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0F172A')
    )

    story = []

    # ---------------- COVER ----------------
    story.append(Spacer(1, 40))
    story.append(Paragraph("APEX BANK", title_style))
    story.append(Paragraph("AI-Enhanced Core Banking Platform with ACID Multi-Document Ledgers, Real-Time ML Anomaly Scoring & Generative Financial Insights", subtitle_style))
    story.append(HRFlowable(width="90%", thickness=2, color=colors.HexColor('#6366F1'), spaceAfter=40))

    meta_data = [
        [Paragraph("Project Submission:", table_cell_bold), Paragraph("Full Stack Web + Machine Learning + Generative AI Graduation Project", table_cell)],
        [Paragraph("Author / Candidate:", table_cell_bold), Paragraph("Karpagavalli V", table_cell)],
        [Paragraph("Frontend Stack:", table_cell_bold), Paragraph("React 19, Vite 8, Tailwind CSS, Recharts, Lucide Icons", table_cell)],
        [Paragraph("Backend Stack:", table_cell_bold), Paragraph("Python 3.12, Flask 3.1.0, Bcrypt, PyJWT, REST APIs", table_cell)],
        [Paragraph("Database Architecture:", table_cell_bold), Paragraph("MongoDB 8.0 Enterprise (Replica Set rs0 / Atlas Cluster)", table_cell)],
        [Paragraph("Intelligence Engines:", table_cell_bold), Paragraph("Scikit-learn Random Forest (ML) & Google Gemini 3.8 Flash (GenAI)", table_cell)],
        [Paragraph("Security Standards:", table_cell_bold), Paragraph("Bcrypt Work Factor 12, STRIDE-Audited, 4-Digit UPI PIN Verification", table_cell)],
    ]
    meta_table = Table(meta_data, colWidths=[2.2 * inch, 4.8 * inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(meta_table)
    story.append(PageBreak())

    # ---------------- 1. EXECUTIVE SUMMARY ----------------
    story.append(Paragraph("1. Executive Summary & Project Overview", h1_style))
    story.append(Paragraph(
        "Apex Bank is an enterprise-grade core banking application that unifies mission-critical transactional banking, "
        "real-time machine learning fraud detection, and generative artificial intelligence. The platform addresses fundamental "
        "flaws in educational banking software, including floating-point rounding drift, concurrent withdrawal race conditions, "
        "missing idempotency safeguards, and lack of verified data isolation.", body_style
    ))
    story.append(Paragraph("<b>Key Architectural Capabilities:</b>", body_style))
    story.append(Paragraph("• <b>Integer-Paise Accounting:</b> 100% of balances and transactions are stored in 64-bit integer paise (1 INR = 100 paise), entirely preventing floating-point imprecision.", bullet_style))
    story.append(Paragraph("• <b>ACID Multi-Document Atomic Transfers:</b> Inter-account transfers debit the sender and credit the receiver inside a MongoDB multi-document transaction with exponential backoff and jitter for WriteConflicts.", bullet_style))
    story.append(Paragraph("• <b>Real-Time Machine Learning Anomaly Detection:</b> Scores transactions across 14 behavioral and temporal features to compute instant fraud probabilities prior to ledger commit.", bullet_style))
    story.append(Paragraph("• <b>Generative AI Financial Intelligence:</b> Leverages Google Gemini 3.8 Flash with hardcoded prompt-injection refusal guardrails and deterministic rule-based fallback.", bullet_style))
    story.append(Paragraph("• <b>Google Pay-Style Apex Pay & UPI PIN:</b> Instant beneficiary lookup by Name, Phone, or Pay ID with 4-digit UPI Transaction PIN verification modal.", bullet_style))

    # ---------------- 2. MACHINE LEARNING MODULE ----------------
    story.append(Paragraph("2. Machine Learning Fraud Detection Engine", h1_style))
    story.append(Paragraph(
        "The machine learning module assesses transaction anomaly probability in real time using a tuned Random Forest Classifier "
        "(100 estimators, balanced class weights, max depth 12). The pipeline evaluates 12 behavioral and temporal features (yielding 14 encoded features):", body_style
    ))
    story.append(Paragraph("• <b>time_since_last_tx_min (22.69%):</b> Elapsed time since previous transaction (rapid succession detection).", bullet_style))
    story.append(Paragraph("• <b>amount_to_avg_ratio (19.58%):</b> Transfer amount relative to customer's historical average debit.", bullet_style))
    story.append(Paragraph("• <b>amount_inr (18.60%):</b> Absolute monetary value in Indian Rupees.", bullet_style))
    story.append(Paragraph("• <b>balance_before_inr (9.72%):</b> Available liquidity prior to transfer.", bullet_style))
    story.append(Paragraph("• <b>balance_ratio (7.67%):</b> Proportion of account balance consumed by the transaction.", bullet_style))
    story.append(Paragraph("• <b>tx_frequency_last_24h (7.25%):</b> Velocity count of transactions in the preceding 24 hours.", bullet_style))
    story.append(Paragraph("• <b>customer_hist_avg_inr (5.27%):</b> Customer's lifetime average debit magnitude.", bullet_style))
    story.append(Paragraph("• <b>hour_of_day, tx_type one-hot, day_of_week (9.22% combined):</b> Temporal and operational indicators.", bullet_style))

    story.append(Paragraph("<b>Model Performance Evaluation (Holdout Test Set of 2,000 Transactions):</b>", body_style))
    ml_data = [
        [Paragraph("Metric", table_cell_bold), Paragraph("Random Forest Model", table_cell_bold), Paragraph("Baseline (Logistic Regression)", table_cell_bold)],
        [Paragraph("Accuracy", table_cell), Paragraph("95.65%", table_cell), Paragraph("94.45%", table_cell)],
        [Paragraph("Precision", table_cell), Paragraph("93.42%", table_cell), Paragraph("80.00%", table_cell)],
        [Paragraph("Recall", table_cell), Paragraph("64.84%", table_cell), Paragraph("65.75%", table_cell)],
        [Paragraph("F1-Score", table_cell), Paragraph("0.7655", table_cell), Paragraph("0.7218", table_cell)],
        [Paragraph("ROC-AUC", table_cell), Paragraph("0.8243", table_cell), Paragraph("0.8338", table_cell)],
    ]
    ml_table = Table(ml_data, colWidths=[2.3 * inch, 2.3 * inch, 2.4 * inch])
    ml_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E0E7FF')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(ml_table)
    story.append(Spacer(1, 10))

    # ---------------- 3. GENERATIVE AI MODULE ----------------
    story.append(Paragraph("3. Generative AI Financial Intelligence Assistant", h1_style))
    story.append(Paragraph(
        "Apex Bank delivers hyper-personalized financial intelligence through Google Gemini 3.8 Flash, featuring:", body_style
    ))
    story.append(Paragraph("• <b>Monthly Cash Flow Synthesis:</b> Automates income vs. expense reconciliation and net savings velocity.", bullet_style))
    story.append(Paragraph("• <b>Emergency Fund Runway:</b> Recommends conservative 3-to-6 month savings targets tailored to personal spending habits.", bullet_style))
    story.append(Paragraph("• <b>Prompt-Injection Refusal Guardrails:</b> Systematically detects and rejects user attempts to execute transactions or manipulate ledgers via conversational prompts.", bullet_style))
    story.append(Paragraph("• <b>Deterministic Fallback:</b> Automatically provides rule-based financial analysis when API keys are unconfigured or networks are offline, ensuring continuous service.", bullet_style))

    # ---------------- 4. SECURITY & UPI PIN ----------------
    story.append(Paragraph("4. Security Architecture & 4-Digit UPI PIN Verification", h1_style))
    story.append(Paragraph(
        "• <b>Bcrypt Password & PIN Hashing:</b> Passwords and 4-digit UPI PINs are hashed with Bcrypt (work factor 12) with unique salts. Raw PINs are never saved or returned via API.<br/>"
        "• <b>Interactive UPI PIN Modal:</b> Designed after Google Pay and PhonePe, requiring 4 masked PIN digits with virtual keypad and keyboard support before executing any transfer.<br/>"
        "• <b>PyJWT Role-Based Access Control:</b> Enforces strict customer vs. admin authorization and eliminates Insecure Direct Object References (IDOR).<br/>"
        "• <b>Idempotency Guarantees:</b> UUID v4 Idempotency-Key headers prevent double debits on network retries.", body_style
    ))

    # ---------------- 5. DATABASE ARCHITECTURE ----------------
    story.append(Paragraph("5. Database Collections (MongoDB)", h1_style))
    story.append(Paragraph("1. <b>users:</b> Customer profiles, Bcrypt password hashes, and hashed 4-digit UPI PINs.", bullet_style))
    story.append(Paragraph("2. <b>accounts:</b> 12-digit account numbers and balances stored in integer paise.", bullet_style))
    story.append(Paragraph("3. <b>transactions:</b> Double-entry financial records with ML risk scores and audit links.", bullet_style))
    story.append(Paragraph("4. <b>idempotency_keys:</b> 24-hour TTL mutation cache for safe network retries.", bullet_style))
    story.append(Paragraph("5. <b>audit_logs:</b> Security and compliance event log with timestamped details.", bullet_style))

    # ---------------- 6. HOW TO RUN ----------------
    story.append(Paragraph("6. Installation & Execution Guide", h1_style))
    story.append(Paragraph(
        "<b>1. Backend Setup:</b><br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;cd backend<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;python -m venv venv<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;venv\\Scripts\\activate<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;pip install -r requirements.txt<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;copy .env.example .env (configure MONGO_URI)<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;python run.py (starts server on http://127.0.0.1:5000)<br/><br/>"
        "<b>2. Frontend Setup:</b><br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;cd frontend<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;npm install<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;npm run dev (starts Vite on http://localhost:5173)<br/><br/>"
        "<b>3. Demo User Credentials (Default UPI PIN: 1234):</b><br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;• Charu: username 'charu_01' | password 'Charu@1234' | PIN '1234'<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;• Maha: username 'maha_02' | password 'Maha@1234' | PIN '1234'<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;• Suruthika: username 'suruthika_03' | password 'Suru@1234' | PIN '1234'<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;• Divya: username 'divya_04' | password 'Divya@1234' | PIN '1234'",
        body_style
    ))

    doc.build(story)
    print(f"[SUCCESS] PDF documentation generated: {output_path}")

if __name__ == "__main__":
    out_file = Path("d:/grad prjt/docs/Apex_Bank_Project_Documentation.pdf")
    create_pdf_document(out_file)

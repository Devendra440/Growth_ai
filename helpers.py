"""
helpers.py - Utility functions for Growth_AI
"""
import os
import datetime
import streamlit as st
from fpdf import FPDF
import io
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =====================================================
# EMAIL VERIFICATION
# =====================================================
def generate_otp():
    """Generate a 6-digit numeric OTP."""
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(receiver_email, otp):
    """Send verification email using Gmail SMTP."""
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")
    
    if not sender_email or not sender_password:
        return False, "Email credentials not found in environment."

    message = MIMEMultipart("alternative")
    message["Subject"] = "Verify your Growth_AI Account"
    message["From"] = f"Growth_AI <{sender_email}>"
    message["To"] = receiver_email

    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
        <h2 style="color: #7C3AED;">Welcome to Growth_AI!</h2>
        <p>Thank you for signing up. Please use the following code to verify your account:</p>
        <div style="background: #f4f4f4; padding: 15px; font-size: 24px; font-weight: bold; text-align: center; border-radius: 10px; border: 1px solid #ddd;">
          {otp}
        </div>
        <p>This code will expire in 10 minutes.</p>
        <p>If you didn't request this, you can safely ignore this email.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin-top: 20px;">
        <small style="color: #999;">© 2026 Growth_AI Intelligence Platform</small>
      </body>
    </html>
    """
    message.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        return True, "Email sent successfully."
    except Exception as e:
        return False, str(e)

# =====================================================
# RATE LIMITING
# =====================================================
MAX_AI_CALLS_PER_DAY = 10

def check_rate_limit():
    """Check if user has exceeded daily AI call limit."""
    if "ai_call_count" not in st.session_state:
        st.session_state.ai_call_count = 0
        st.session_state.ai_call_date = datetime.date.today()
    
    if st.session_state.ai_call_date != datetime.date.today():
        st.session_state.ai_call_count = 0
        st.session_state.ai_call_date = datetime.date.today()
    
    if st.session_state.ai_call_count >= MAX_AI_CALLS_PER_DAY:
        return False, f"Daily limit of {MAX_AI_CALLS_PER_DAY} AI calls reached. Try again tomorrow."
    return True, ""

def increment_rate_limit():
    st.session_state.ai_call_count += 1

# =====================================================
# SESSION TIMEOUT (30 min)
# =====================================================
SESSION_TIMEOUT_MINUTES = 30

def check_session_timeout():
    """Auto-logout after inactivity."""
    if "last_activity" not in st.session_state:
        st.session_state.last_activity = datetime.datetime.now()
        return False
    
    elapsed = (datetime.datetime.now() - st.session_state.last_activity).total_seconds()
    if elapsed > SESSION_TIMEOUT_MINUTES * 60:
        return True
    st.session_state.last_activity = datetime.datetime.now()
    return False

# =====================================================
# PDF EXPORT
# =====================================================
def generate_pdf(strategy_doc, ai_text):
    """Generate a PDF report from strategy data."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Title
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 15, "Growth_AI Strategy Report", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
    pdf.ln(10)
    
    # Business Info
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Business Information", ln=True)
    pdf.set_draw_color(124, 58, 237)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "", 11)
    info_fields = [
        ("Business Type", strategy_doc.get("business_type", "N/A")),
        ("Product/Service", strategy_doc.get("product", "N/A")),
        ("Industry", strategy_doc.get("industry", "N/A")),
        ("Scale", strategy_doc.get("scale", "N/A")),
        ("Target Market", strategy_doc.get("target_market", "N/A")),
        ("Location", strategy_doc.get("location", "N/A")),
        ("Challenge", strategy_doc.get("challenge", "N/A")),
        ("Goal", strategy_doc.get("goal", "N/A")),
    ]
    for label, value in info_fields:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(45, 7, f"{label}:", ln=False)
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 7, str(value))
    
    pdf.ln(8)
    
    # AI Strategy
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "AI Strategy Report", ln=True)
    pdf.set_draw_color(6, 182, 212)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "", 10)
    # Clean markdown from text
    clean_text = ai_text.replace("###", "").replace("**", "").replace("*", "").replace("#", "")
    for line in clean_text.split("\n"):
        line = line.strip()
        if line:
            pdf.multi_cell(0, 6, line)
            pdf.ln(2)
    
    # Footer
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 10, "Powered by Growth_AI Intelligence Platform", ln=True, align="C")
    
    return pdf.output()

# =====================================================
# TEXT ANALYTICS
# =====================================================
def get_word_count(text):
    words = len(text.split())
    reading_time = max(1, words // 200)
    return words, reading_time

# =====================================================
# INDUSTRY PROMPTS
# =====================================================
INDUSTRY_PROMPTS = {
    "Technology/SaaS": """Focus on: ARR growth, churn reduction, product-led growth, 
    developer ecosystem, API monetization, cloud infrastructure optimization.""",
    
    "Retail/E-Commerce": """Focus on: omnichannel strategy, inventory optimization, 
    customer lifetime value, last-mile delivery, seasonal demand planning.""",
    
    "Manufacturing": """Focus on: supply chain optimization, lean manufacturing, 
    Industry 4.0 adoption, quality control, vendor management.""",
    
    "Healthcare": """Focus on: regulatory compliance, patient acquisition, 
    telehealth adoption, insurance partnerships, clinical workflow optimization.""",
    
    "Finance/Fintech": """Focus on: regulatory compliance, risk management, 
    digital banking adoption, payment processing, fraud prevention.""",
    
    "Education/EdTech": """Focus on: student acquisition, course completion rates, 
    platform engagement, B2B institutional sales, certification value.""",
    
    "Real Estate": """Focus on: lead generation, property valuation, 
    market timing, client relationship management, digital marketing.""",
    
    "Other": ""
}

# =====================================================
# MONGODB INDEXES
# =====================================================
def ensure_indexes(users_col, strategies_col):
    """Create indexes for better query performance."""
    try:
        users_col.create_index("username", unique=True)
        strategies_col.create_index("username")
        strategies_col.create_index([("username", 1), ("created_at", -1)])
        strategies_col.create_index([("username", 1), ("starred", -1)])
    except Exception:
        pass

# =====================================================
# TIME FORMATTING
# =====================================================
def time_ago(dt):
    """Convert datetime to 'X ago' format."""
    if not dt:
        return "Unknown"
    now = datetime.datetime.now()
    diff = now - dt
    seconds = diff.total_seconds()
    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        mins = int(seconds // 60)
        return f"{mins}m ago"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours}h ago"
    elif seconds < 604800:
        days = int(seconds // 86400)
        return f"{days}d ago"
    else:
        return dt.strftime("%b %d, %Y")

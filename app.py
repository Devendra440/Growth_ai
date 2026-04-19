# =====================================================
# IMPORTS
# =====================================================
import streamlit as st
import google.generativeai as genai
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import os
import pymongo
import bcrypt
import datetime
import pandas as pd
import re
import time
from dotenv import load_dotenv
from bson.objectid import ObjectId

from helpers import (
    check_rate_limit, increment_rate_limit, 
    check_session_timeout, generate_pdf, 
    get_word_count, INDUSTRY_PROMPTS, 
    ensure_indexes, time_ago,
    generate_otp, send_verification_email,
    send_strategy_email
)

# =====================================================
# LOAD ENV
# =====================================================
load_dotenv(override=True)

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Growth_AI | B2B Sales Intelligence",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# CUSTOM CSS & ANIMATIONS
# =====================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');

    :root {
        --primary: #7C3AED;
        --secondary: #06B6D4;
        --accent: #F43F5E;
        --background: #0F172A;
        --card-bg: rgba(30, 41, 59, 0.7);
        --text-main: #F8FAFC;
        --text-dim: #94A3B8;
    }

    * {
        font-family: 'Outfit', sans-serif !important;
    }

    /* Main Background */
    .stApp {
        background: radial-gradient(circle at top right, #1E1B4B, #0F172A, #020617);
        background-attachment: fixed;
        color: var(--text-main);
    }

    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .animate-fade-in {
        animation: fadeIn 0.8s ease-out forwards;
    }

    /* Glassmorphism Cards */
    .glass-card {
        background: var(--card-bg);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 25px;
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }

    .glass-card:hover {
        transform: translateY(-5px);
        border-color: var(--primary);
        box-shadow: 0 10px 30px rgba(124, 58, 237, 0.2);
    }

    /* Gradient Text */
    .gradient-text {
        background: linear-gradient(90deg, var(--primary), var(--secondary));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }

    /* Professional Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.95) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Form Styling */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>select {
        background-color: rgba(15, 23, 42, 0.5) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border-radius: 10px !important;
    }

    .stTextInput>div>div>input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 10px rgba(124, 58, 237, 0.3) !important;
    }

    /* Custom Buttons */
    div.stButton > button {
        background: linear-gradient(45deg, var(--primary), var(--secondary)) !important;
        color: white !important;
        border: none !important;
        padding: 12px 24px !important;
        border-radius: 50px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    div.stButton > button:hover {
        transform: scale(1.02) !important;
        box-shadow: 0 5px 15px rgba(124, 58, 237, 0.4) !important;
    }

    /* Metrics Styling */
    div[data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        color: var(--secondary) !important;
    }

    .badge {
        background: rgba(124, 58, 237, 0.15);
        color: var(--primary);
        padding: 4px 12px;
        border-radius: 50px;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid rgba(124, 58, 237, 0.3);
    }
    /* Media Queries for Responsiveness */
    @media (max-width: 1024px) {
        div[data-testid="stMetricValue"] { font-size: 2rem !important; }
        .glass-card { padding: 20px; }
    }

    @media (max-width: 768px) {
        .stApp { background-attachment: scroll; }
        .gradient-text { font-size: 2.5rem !important; }
        div[data-testid="stMetricValue"] { font-size: 1.8rem !important; }
        .glass-card { padding: 15px; border-radius: 15px; }
        .hero-section { padding: 30px 15px !important; }
        .hero-title { font-size: 2.2rem !important; }
    }

    @media (max-width: 480px) {
        .gradient-text { font-size: 2rem !important; }
        .hero-title { font-size: 1.8rem !important; }
        .badge { font-size: 0.7rem; padding: 3px 8px; }
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">', unsafe_allow_html=True)

# =====================================================
# MONGODB CONNECTION
# =====================================================
MONGO_URI = os.getenv("MONGO_URI")

@st.cache_resource
def init_connection():
    if not MONGO_URI:
        return None, "MONGO_URI not found in environment variables"
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        return client, None
    except Exception as e:
        return None, str(e)

client, err_msg = init_connection()

if not client:
    st.error(f"❌ Failed to connect to MongoDB. Error: {err_msg}")
    st.stop()

db = client["growth_ai_db"]
users_collection = db["users"]
strategies_collection = db["strategies"]

ensure_indexes(users_collection, strategies_collection)

# =====================================================
# SESSION STATE INIT
# =====================================================
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "verifying_user" not in st.session_state:
    st.session_state.verifying_user = None
if "verification_otp" not in st.session_state:
    st.session_state.verification_otp = None

# =====================================================
# API KEY CHECK
# =====================================================
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("❌ GOOGLE_API_KEY not found in .env file")
    st.stop()

genai.configure(api_key=api_key.strip())

@st.cache_resource
def get_working_model():
    try:
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                return genai.GenerativeModel(m.name)
    except Exception as e:
        return None
    return None

model = get_working_model()

# =====================================================
# HEADER
# =====================================================
header_left, header_right = st.columns([3, 1])
with header_left:
    st.markdown("<h2 class='gradient-text'>Growth_AI</h2>", unsafe_allow_html=True)
    st.caption("AI-Powered B2B Sales Intelligence Platform")
with header_right:
    st.markdown(
        "<div style='text-align:right; padding-top:20px;'>"
        "<span class='badge'>Premium Edition</span><br>"
        "<small style='color:var(--text-dim)'>Predict • Personalize • Convert</small>"
        "</div>",
        unsafe_allow_html=True
    )

st.markdown("<div style='height:2px; background:linear-gradient(90deg, var(--primary), transparent); margin-bottom:2rem;'></div>", unsafe_allow_html=True)

# =====================================================
# SESSION TIMEOUT CHECK
# =====================================================
if st.session_state.authenticated:
    if check_session_timeout():
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.warning("Session expired due to inactivity. Please log in again.")
        st.rerun()

# =====================================================
# SIDEBAR – AUTH & NAVIGATION
# =====================================================
st.sidebar.title("🔐 Account")

if not st.session_state.authenticated:
    # ---------------- EMAIL VERIFICATION UI ----------------
    if st.session_state.verifying_user:
        st.sidebar.subheader("Verify Email")
        st.sidebar.info(f"OTP sent to {st.session_state.verifying_user['email']}")
        otp_input = st.sidebar.text_input("Enter 6-digit OTP", key="otp_input")
        
        col1, col2 = st.sidebar.columns(2)
        if col1.button("Verify", key="verify_btn"):
            if otp_input == st.session_state.verification_otp:
                users_collection.insert_one(st.session_state.verifying_user)
                st.toast("✅ Email verified! Please login.", icon="🎉")
                st.session_state.verifying_user = None
                st.session_state.verification_otp = None
                st.rerun()
            else:
                st.sidebar.error("❌ Invalid OTP")
        
        if col2.button("Cancel", key="cancel_verify"):
            st.session_state.verifying_user = None
            st.session_state.verification_otp = None
            st.rerun()
        st.stop()

    auth_tab = st.sidebar.radio("Select", ["Login", "Sign Up"], key="auth_radio")

    if auth_tab == "Sign Up":
        st.sidebar.subheader("Create Account")
        full_name = st.sidebar.text_input("Full Name", key="su_fullname")
        email = st.sidebar.text_input("Email", key="su_email")
        username = st.sidebar.text_input("Username", key="su_username")
        password = st.sidebar.text_input("Password", type="password", key="su_password")
        confirm_password = st.sidebar.text_input("Confirm Password", type="password", key="su_confirm_password")

        if st.sidebar.button("Sign Up", key="su_btn"):
            if not all([full_name, email, username, password, confirm_password]):
                st.toast("❌ All fields required", icon="⚠️")
            elif password != confirm_password:
                st.toast("❌ Passwords do not match", icon="🚫")
            else:
                existing_user = users_collection.find_one({"username": username.strip()})
                if existing_user:
                    st.toast("❌ Username already exists", icon="✋")
                else:
                    otp = generate_otp()
                    success, msg = send_verification_email(email.strip(), otp)
                    
                    if success:
                        hashed_password = bcrypt.hashpw(password.strip().encode('utf-8'), bcrypt.gensalt())
                        st.session_state.verifying_user = {
                            "name": full_name.strip(),
                            "email": email.strip(),
                            "username": username.strip(),
                            "password": hashed_password,
                            "created_at": datetime.datetime.now()
                        }
                        st.session_state.verification_otp = otp
                        st.rerun()
                    else:
                        st.sidebar.error(f"❌ Failed to send email: {msg}")

    if auth_tab == "Login":
        st.sidebar.subheader("Login")
        username = st.sidebar.text_input("Username", key="li_username")
        password = st.sidebar.text_input("Password", type="password", key="li_password")

        if st.sidebar.button("Login", key="li_btn"):
            if not username or not password:
                 st.sidebar.error("❌ Username and Password required")
            else:
                user = users_collection.find_one({"username": username.strip()})
                if user and bcrypt.checkpw(password.strip().encode('utf-8'), user["password"]):
                    st.session_state.authenticated = True
                    st.session_state.current_user = user
                    st.session_state.last_activity = datetime.datetime.now()
                    st.session_state.page = "Home"
                    st.rerun()
                else:
                    st.sidebar.error("❌ Invalid credentials")

    st.stop()

# ---------------- AFTER LOGIN ----------------
user_data = st.session_state.current_user
st.sidebar.success(f"👋 Welcome, {user_data.get('name', 'User')}")

nav = st.sidebar.radio(
    "Navigate",
    ["Home", "Problem & Solution", "Market & ROI", "AI Strategy Engine", "History", "Profile & Analytics"],
    key="nav_radio"
)
st.session_state.page = nav

if st.sidebar.button("Logout", key="logout_btn"):
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 💡 AI Tip of the Day")
import random
tips = [
    "Personalized emails have 26% higher open rates.",
    "Follow up within 5 minutes to increase conversion by 9x.",
    "Predictive scoring reduces research time by 60%.",
    "Multi-channel outreach increases response by 3x."
]
st.sidebar.info(random.choice(tips))

st.sidebar.markdown("""
<div style="padding-top: 20px; text-align: center;">
    <small style="color: var(--text-dim);">V 2.2.0 Premium</small>
</div>
""", unsafe_allow_html=True)

# =====================================================
# PROFILE & ANALYTICS
# =====================================================
if st.session_state.page == "Profile & Analytics":
    st.title("👤 Profile & Analytics")
    
    username = user_data.get("username")
    strategies = list(strategies_collection.find({"username": username}))
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("Your Profile")
        st.markdown(f"**Name:** {user_data.get('name')}")
        st.markdown(f"**Email:** {user_data.get('email')}")
        st.markdown(f"**Username:** {username}")
        member_since = user_data.get("created_at", datetime.datetime.now()).strftime("%B %Y")
        st.markdown(f"**Member Since:** {member_since}")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("Your Activity Analytics")
        a1, a2, a3 = st.columns(3)
        a1.metric("Total Strategies", len(strategies))
        starred = len([s for s in strategies if s.get("starred")])
        a2.metric("Starred Reports", starred)
        words_generated = sum([len(s.get("ai_response", "").split()) for s in strategies])
        a3.metric("Words Generated", f"{words_generated:,}")
        st.markdown("</div>", unsafe_allow_html=True)
        
        if strategies:
            # Industry breakdown chart
            df = pd.DataFrame(strategies)
            if 'industry' in df.columns:
                ind_counts = df['industry'].value_counts().reset_index()
                ind_counts.columns = ['Industry', 'Count']
                fig = px.pie(ind_counts, values='Count', names='Industry', 
                             title="Strategies by Industry", hole=0.4,
                             color_discrete_sequence=px.colors.sequential.Purp)
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', 
                                  font_color="white")
                st.plotly_chart(fig, use_container_width=True)

# =====================================================
# HISTORY PAGE
# =====================================================
elif st.session_state.page == "History":
    st.title("📜 Strategy History")
    st.caption("View, search, and manage your past AI-generated strategies")

    username = user_data.get("username")
    
    # Search and Filter
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("🔍 Search strategies by business or challenge...", "")
    with col2:
        filter_starred = st.checkbox("⭐ Show only starred")

    # Build query
    query = {"username": username}
    if search_term:
        query["$or"] = [
            {"business_type": {"$regex": search_term, "$options": "i"}},
            {"challenge": {"$regex": search_term, "$options": "i"}},
            {"industry": {"$regex": search_term, "$options": "i"}}
        ]
    if filter_starred:
        query["starred"] = True

    cursor = strategies_collection.find(query).sort("created_at", -1)
    strategies = list(cursor)

    if not strategies:
        st.info("No history found. Run the AI Strategy Engine to generate reports!")
    else:
        for i, strat in enumerate(strategies):
            ts = strat.get("created_at", datetime.datetime.now())
            time_str = time_ago(ts)
            business = strat.get("business_type", "Unknown Business")
            product = strat.get("product", "Unknown Product")
            doc_id = strat.get("_id")
            is_starred = strat.get("starred", False)
            
            star_icon = "⭐" if is_starred else "☆"
            title = f"{star_icon} {business} - {product} ({time_str})"
            
            with st.expander(title):
                st.markdown(f"**Industry:** {strat.get('industry')} | **Target Market:** {strat.get('target_market')}")
                st.markdown(f"**Challenge:** {strat.get('challenge')}")
                
                # Action Buttons
                btn_c1, btn_c2, btn_c3, btn_c4 = st.columns(4)
                if btn_c1.button("Toggle Star ⭐", key=f"star_{doc_id}"):
                    strategies_collection.update_one({"_id": doc_id}, {"$set": {"starred": not is_starred}})
                    st.rerun()
                
                if btn_c2.button("🗑️ Delete", key=f"del_{doc_id}"):
                    strategies_collection.delete_one({"_id": doc_id})
                    st.toast("Strategy deleted successfully!")
                    st.rerun()
                
                # PDF Download
                pdf_bytes = generate_pdf(strat, strat.get("ai_response", ""))
                btn_c3.download_button(
                    label="📄 Download PDF",
                    data=pdf_bytes,
                    file_name=f"{business}_strategy.pdf",
                    mime="application/pdf",
                    key=f"pdf_{doc_id}"
                )
                
                st.divider()
                st.markdown("### 🤖 AI Strategy Report")
                st.markdown(strat.get("ai_response"))

# =====================================================
# AI STRATEGY ENGINE
# =====================================================
elif st.session_state.page == "AI Strategy Engine":

    st.title("🤖 AI Strategy Engine")
    st.caption("AI that thinks like a consultant, strategist, and sales leader")

    MASTER_PROMPT = """
    You are a senior B2B Market Strategy Consultant.
    
    Respond STRICTLY in the following sections:
    ### BUSINESS STRATEGY
    - Overview
    - Key improvement areas
    - Data-driven recommendations
    - Expected growth impact (%)

    ### LOCATION INTELLIGENCE
    - 5 business or industrial locations with reasons

    ### COMPETITOR ANALYSIS
    - Competitor mindset
    - Pricing strategy
    - Strengths & Weaknesses
    - Strategic gaps
    - How this business can win
    """

    with st.form("ai_form"):
        col1, col2 = st.columns(2)
        with col1:
            business_type = st.text_input("Business Type *")
            product = st.text_input("Product / Service Name *")
            industry = st.selectbox("Industry *", list(INDUSTRY_PROMPTS.keys()))
        with col2:
            scale = st.selectbox("Business Scale *", ["Startup", "Small", "Medium", "Enterprise"])
            target_market = st.selectbox("Target Market *", ["B2B", "B2C", "B2B2C"])
            location = st.text_input("Primary Business Location *")
            
        challenge = st.text_area("Current Business Challenge *", height=100)
        goal = st.selectbox("Primary Goal *", ["Increase Revenue", "Improve Conversion", "Reduce CAC", "Scale Operations", "Market Expansion"])

        submit = st.form_submit_button("🚀 Generate Strategy Report")

    if submit:
        # Rate limit check
        can_run, msg = check_rate_limit()
        if not can_run:
            st.error(f"❌ {msg}")
            st.stop()
            
        if not model:
            st.error("❌ AI Service is currently unavailable. Please check your connection.")
            st.stop()

        if not business_type or not product or not location or not challenge:
            st.error("❌ Please fill in all required fields marked with *.")
            st.stop()

        industry_context = INDUSTRY_PROMPTS.get(industry, "")
        
        USER_INPUT = f"""
        Business Type: {business_type}
        Product: {product}
        Industry: {industry} ({industry_context})
        Business Scale: {scale}
        Target Market: {target_market}
        Location: {location}
        Current Challenge: {challenge}
        Goal: {goal}
        """

        # Progress bar animation
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i in range(100):
            time.sleep(0.02)
            progress_bar.progress(i + 1)
            if i == 20: status_text.text("🧠 Analyzing market data...")
            elif i == 50: status_text.text("📊 Formulating competitive strategy...")
            elif i == 80: status_text.text("✍️ Finalizing report...")

        try:
            response = model.generate_content(MASTER_PROMPT + "\n\n" + USER_INPUT)
            result_text = response.text
            increment_rate_limit()
            
            progress_bar.empty()
            status_text.empty()
            
            st.success("✅ Strategy Report Generated Successfully!")
            
            # Show Analytics
            words, reading_time = get_word_count(result_text)
            st.caption(f"⏱️ Reading time: ~{reading_time} min ({words} words)")
            
            st.markdown(result_text)

            # SAVE TO DB
            strategy_doc = {
                "username": st.session_state.current_user.get("username"),
                "business_type": business_type,
                "product": product,
                "industry": industry,
                "scale": scale,
                "target_market": target_market,
                "location": location,
                "challenge": challenge,
                "goal": goal,
                "ai_response": result_text,
                "created_at": datetime.datetime.now(),
                "starred": False
            }
            strategies_collection.insert_one(strategy_doc)
            st.toast("✅ Saved to your History!")

            # GRAPH
            st.subheader("📊 AI Impact Projection")
            months = ["M1", "M2", "M3", "M4", "M5", "M6"]
            before = [100, 105, 108, 110, 112, 115]
            after = [100, 115, 135, 160, 190, 225]

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=months, y=before, name="Traditional Growth", line=dict(color="#94A3B8", dash="dash")))
            fig.add_trace(go.Scatter(x=months, y=after, name="AI-Accelerated Growth", line=dict(color="#06B6D4", width=3)))
            fig.update_layout(title="Projected Performance Index", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig, use_container_width=True)

            # PDF Download
            pdf_bytes = generate_pdf(strategy_doc, result_text)
            
            # Send Email with PDF
            user_email = user_data.get('email')
            if user_email:
                with st.spinner("📧 Emailing report to you..."):
                    e_success, e_msg = send_strategy_email(user_email, strategy_doc, pdf_bytes)
                    if e_success:
                        st.toast("📧 Report also sent to your email!", icon="📩")
                    else:
                        st.sidebar.warning(f"⚠️ Email failed: {e_msg}")

            st.download_button(
                label="📄 Download PDF Report",
                data=pdf_bytes,
                file_name=f"{business_type.replace(' ','_')}_Strategy.pdf",
                mime="application/pdf"
            )

            # Follow up questions UI
            st.session_state.chat_history.append({"role": "assistant", "content": "I've generated your report. What specific area would you like to dive deeper into?"})

        except Exception as e:
            st.error(f"❌ An error occurred during AI generation: {e}")

    # Chat interface at the bottom
    if len(st.session_state.chat_history) > 0:
        st.divider()
        st.subheader("💬 Discuss this Strategy")
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f"**You:** {msg['content']}")
            else:
                st.markdown(f"**Growth_AI:** {msg['content']}")
                
        chat_input = st.text_input("Ask a follow-up question...")
        if st.button("Send") and chat_input:
            st.session_state.chat_history.append({"role": "user", "content": chat_input})
            with st.spinner("Thinking..."):
                resp = model.generate_content(f"Based on our strategy discussion, answer this: {chat_input}")
                st.session_state.chat_history.append({"role": "assistant", "content": resp.text})
            st.rerun()

# =====================================================
# HOME PAGE
# =====================================================
elif st.session_state.page == "Home":
    st.markdown("""
    <div class="animate-fade-in hero-section" style="background: linear-gradient(135deg, rgba(124, 58, 237, 0.1), rgba(6, 182, 212, 0.1)); padding: 60px; border-radius: 30px; border: 1px solid rgba(255, 255, 255, 0.05); margin-bottom: 40px; text-align: center;">
        <h1 class="gradient-text hero-title" style="font-size: 4em; margin-bottom: 10px;">Accelerate Your Growth</h1>
        <p style="color: var(--text-main); font-size: 1.5em; font-weight: 300; max-width: 800px; margin: 0 auto 20px;">
            The Intelligence Layer for Modern B2B Teams. 
        </p>
        <div style="display: flex; justify-content: center; gap: 15px; margin-top: 30px; flex-wrap: wrap;">
            <span class="badge" style="padding: 10px 20px; font-size: 1rem;">98% Accuracy</span>
            <span class="badge" style="padding: 10px 20px; font-size: 1rem;">Real-time Data</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="glass-card">
            <h3 style="color: var(--secondary);"><i class='fas fa-crosshairs'></i> Precision</h3>
            <p style="color: var(--text-dim);">Identify high-value leads with 95% accuracy using our proprietary predictive scoring models.</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="glass-card">
            <h3 style="color: var(--secondary);"><i class='fas fa-bolt'></i> Speed</h3>
            <p style="color: var(--text-dim);">Reduce prospect research time from hours to minutes. Generate instant strategic briefs at scale.</p>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="glass-card">
            <h3 style="color: var(--secondary);"><i class='fas fa-chart-line'></i> Conversion</h3>
            <p style="color: var(--text-dim);">Boost conversion rates by up to 25% with hyper-personalized outreach generated by AI.</p>
        </div>
        """, unsafe_allow_html=True)

# =====================================================
# PROBLEM & SOLUTION
# =====================================================
elif st.session_state.page == "Problem & Solution":
    st.markdown("<h1 class='gradient-text'>Bridging the Growth Gap</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="glass-card" style="border-left: 4px solid var(--accent);">
            <h3 style="color: var(--accent);"><i class='fas fa-times-circle'></i> The Legacy Way</h3>
            <ul style="color: var(--text-dim);">
                <li>SDRs wasting 60% of time on manual research</li>
                <li>Generic outreach that damages brand reputation</li>
                <li>Strategy based on gut-feeling and fragmented data</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="glass-card" style="border-left: 4px solid var(--secondary);">
            <h3 style="color: var(--secondary);"><i class='fas fa-check-circle'></i> The Growth_AI Way</h3>
            <ul style="color: var(--text-dim);">
                <li>Automated AI dossiers on every high-value prospect</li>
                <li>Hyper-personalization at scale across all channels</li>
                <li>Data-driven insights from real-time market signals</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# =====================================================
# MARKET & ROI
# =====================================================
elif st.session_state.page == "Market & ROI":
    st.markdown("<h1 class='gradient-text'>Economics of Intelligence</h1>", unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Addressable Market", "$24B+", "+12% Growth")
    m2.metric("Qualified Lead Velocity", "3.5x", "Increase")
    m3.metric("Avg. CAC Reduction", "40%", "First 12 Months")

    categories = ['Manual Research', 'Growth_AI Augmented']
    revenue = [500000, 685000] 
    
    fig = px.bar(x=categories, y=revenue, text_auto=True, color=categories, 
                 color_discrete_sequence=['#F43F5E', '#06B6D4'],
                 title="Projected Revenue Uplift")
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color="white")
    st.plotly_chart(fig, use_container_width=True)

# =====================================================
# GLOBAL FOOTER
# =====================================================
st.markdown("""
<div style="margin-top: 100px; padding: 40px; border-top: 1px solid rgba(255,255,255,0.05); text-align: center; color: var(--text-dim);">
    <div style="display: flex; justify-content: center; gap: 30px; margin-bottom: 20px;">
        <a href="#" style="color: var(--text-dim); text-decoration: none;">Privacy Policy</a>
        <a href="#" style="color: var(--text-dim); text-decoration: none;">Terms of Service</a>
        <a href="#" style="color: var(--text-dim); text-decoration: none;">Documentation</a>
    </div>
    <p style="font-size: 0.85em;">© 2026 Growth_AI Intelligence Platform. Built for the future of B2B sales.</p>
</div>
""", unsafe_allow_html=True)

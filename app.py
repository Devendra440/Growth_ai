# =====================================================
# IMPORTS
# =====================================================
import streamlit as st
import google.generativeai as genai
import numpy as np
import matplotlib.pyplot as plt
import os
import pymongo
import bcrypt
import datetime
import pandas as pd
import re
from dotenv import load_dotenv

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

    /* Main Background with subtle mesh animation */
    .stApp {
        background: radial-gradient(circle at top right, #1E1B4B, #0F172A, #020617);
        background-size: 200% 200%;
        animation: meshGradient 15s ease infinite;
        color: var(--text-main);
    }

    @keyframes meshGradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
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
        width: 100%;
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

    /* Header Styling */
    .project-header {
        padding: 2rem 0;
        border-bottom: 2px solid rgba(255, 255, 255, 0.05);
        margin-bottom: 2rem;
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
</style>
""", unsafe_allow_html=True)

# Load FontAwesome for Icons
st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">', unsafe_allow_html=True)

# =====================================================
# MONGODB CONNECTION
# =====================================================

# Load connection string
MONGO_URI = os.getenv("MONGO_URI")

@st.cache_resource
def init_connection():
    if not MONGO_URI:
        return None, "MONGO_URI not found in environment variables"
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Check if connection is successful
        client.admin.command('ping')
        return client, None
    except Exception as e:
        return None, str(e)

client, err_msg = init_connection()

if not client:
    st.error(f"❌ Failed to connect to MongoDB. Error: {err_msg}")
    st.stop()

# database and collection
db = client["growth_ai_db"]
users_collection = db["users"]
strategies_collection = db["strategies"]

# =====================================================
# SESSION STATE INIT
# =====================================================
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None

# =====================================================
# API KEY CHECK
# =====================================================
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("❌ GOOGLE_API_KEY not found in .env file")
    st.stop()

# Clean key
api_key = api_key.strip()

# =====================================================
# GEMINI CONFIG (AUTO MODEL)
# =====================================================
genai.configure(api_key=api_key)

def get_working_model():
    try:
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                return genai.GenerativeModel(m.name)
    except Exception as e:
        st.error(f"⚠️ Gemini Connection Failed: {e}")
        return None
    return None

model = get_working_model()
if not model:
    st.warning("⚠️ AI features are unavailable due to connection issues.")
    # Do not stop, allow app to run without AI
else:
    # Only verify if model is available
    pass

# =====================================================
# HEADER (PROJECT NAME RIGHT SIDE)
# =====================================================
header_left, header_right = st.columns([3, 1])
with header_left:
    st.markdown("<h2 class='gradient-text'>Growth_AI</h2>", unsafe_allow_html=True)
    st.caption("AI-Powered B2B Sales Intelligence Platform")
with header_right:
    st.markdown(
        "<div style='text-align:right; padding-top:20px;'>"
        "<span class='badge'>Hackathon Edition</span><br>"
        "<small style='color:var(--text-dim)'>Predict • Personalize • Convert</small>"
        "</div>",
        unsafe_allow_html=True
    )

st.markdown("<div style='height:2px; background:linear-gradient(90deg, var(--primary), transparent); margin-bottom:2rem;'></div>", unsafe_allow_html=True)

# =====================================================
# SIDEBAR – AUTH & NAVIGATION
# =====================================================
st.sidebar.title("🔐 Account")

# ---------------- LOGIN / SIGNUP ----------------
# ---------------- LOGIN / SIGNUP ----------------
if not st.session_state.authenticated:

    auth_tab = st.sidebar.radio("Select", ["Login", "Sign Up"], key="auth_radio")

    if auth_tab == "Sign Up":
        st.sidebar.subheader("Create Account")

        full_name = st.sidebar.text_input("Full Name", key="su_fullname")
        email = st.sidebar.text_input("Email", key="su_email")
        username = st.sidebar.text_input("Username", key="su_username")
        password = st.sidebar.text_input("Password", type="password", key="su_password")
        confirm_password = st.sidebar.text_input("Confirm Password", type="password", key="su_confirm_password")

        if st.sidebar.button("Sign Up", key="su_btn"):
            # Strip inputs to avoid whitespace issues
            full_name = full_name.strip() if full_name else ""
            email = email.strip() if email else ""
            username = username.strip() if username else ""
            password = password.strip() if password else ""
            confirm_password = confirm_password.strip() if confirm_password else ""

            if not all([full_name, email, username, password, confirm_password]):
                st.toast("❌ All fields required", icon="⚠️")
            elif not (len(full_name) >= 4 and all(x.isalpha() or x.isspace() for x in full_name)):
                st.toast("❌ Full Name must be at least 4 letters and contain only letters", icon="👤")
            elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                st.toast("❌ Invalid email format", icon="📧")
            elif len(username) < 4 or not username[0].isupper():
                st.toast("❌ Username must be min 4 characters and start with a capital letter", icon="👤")
            elif not (7 <= len(password) <= 15):
                st.toast("❌ Password must be 7-15 characters long", icon="🔑")
            elif not any(c.isupper() for c in password):
                st.toast("❌ Password must contain at least one capital letter", icon="🔠")
            elif not any(c.isdigit() for c in password):
                st.toast("❌ Password must contain at least one number", icon="🔢")
            elif not any(not c.isalnum() for c in password):
                st.toast("❌ Password must contain at least one special character", icon="🔣")
            elif password != confirm_password:
                st.toast("❌ Passwords do not match", icon="🚫")
            else:
                # Check if user exists
                existing_user = users_collection.find_one({"username": username})
                if existing_user:
                    st.toast("❌ Username already exists", icon="✋")
                else:
                    # Hash password
                    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                    
                    new_user = {
                        "name": full_name,
                        "email": email,
                        "username": username,
                        "password": hashed_password  # Store hash
                    }
                    users_collection.insert_one(new_user)
                    st.toast("✅ Account created. Please login.", icon="🎉")
                    st.success("✅ Account created. Please login.")

    if auth_tab == "Login":
        st.sidebar.subheader("Login")

        username = st.sidebar.text_input("Username", key="li_username")
        password = st.sidebar.text_input("Password", type="password", key="li_password")

        if st.sidebar.button("Login", key="li_btn"):
            username = username.strip() if username else ""
            password = password.strip() if password else ""
            
            if not username or not password:
                 st.sidebar.error("❌ Username and Password required")
            else:
                user = users_collection.find_one({"username": username})
                
                if user:
                    # Verify password
                    if bcrypt.checkpw(password.encode('utf-8'), user["password"]):
                        st.session_state.authenticated = True
                        st.session_state.current_user = user # Store entire user object or just needed fields
                        st.session_state.page = "Home"
                        st.rerun()
                    else:
                        st.sidebar.error("❌ Invalid credentials")
                else:
                    st.sidebar.error("❌ Invalid credentials")

    st.stop()

# ---------------- AFTER LOGIN ----------------
# Fetch latest data for current user to ensure nothing stale
if st.session_state.current_user:
     # We can rely on session state or fetch fresh
     user_data = st.session_state.current_user
     st.sidebar.success(f"👋 Welcome, {user_data.get('name', 'User')}")

nav = st.sidebar.radio(
    "Navigate",
    ["Home", "Problem & Solution", "Market & ROI", "AI Strategy Engine", "History"],
    key="nav_radio"
)
st.session_state.page = nav

if st.sidebar.button("Logout", key="logout_btn"):
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.rerun()

# ---------------- SIDEBAR EXTRA ----------------
st.sidebar.markdown("---")
st.sidebar.markdown("### 💡 AI Tip of the Day")
tips = [
    "Personalized emails have 26% higher open rates.",
    "Follow up within 5 minutes to increase conversion by 9x.",
    "Predictive scoring reduces research time by 60%.",
    "Multi-channel outreach increases response by 3x."
]
import random
st.sidebar.info(random.choice(tips))

st.sidebar.markdown("""
<div style="padding-top: 20px; text-align: center;">
    <small style="color: var(--text-dim);">V 2.1.0 Premium</small>
</div>
""", unsafe_allow_html=True)

# =====================================================
# HISTORY PAGE
# =====================================================
if st.session_state.page == "History":
    st.title("📜 Strategy History")
    st.caption("View your past AI-generated business strategies")

    user_info = st.session_state.current_user
    # Handle case where user_info is dict or string (depending on how it was stored)
    username = user_info.get("username") if isinstance(user_info, dict) else user_info

    # Find strategies for this user, sort by latest first
    cursor = strategies_collection.find({"username": username}).sort("created_at", -1)
    strategies = list(cursor)

    if not strategies:
        st.info("No history found. Run the AI Strategy Engine to generate reports!")
    else:
        for i, strat in enumerate(strategies):
            # Format timestamp
            ts = strat.get("created_at", datetime.datetime.now()).strftime("%Y-%m-%d %H:%M")
            business = strat.get("business_type", "Unknown Business")
            product = strat.get("product", "Unknown Product")
            
            with st.expander(f"📅 {ts} | {business} - {product}"):
                st.markdown(f"**Industry:** {strat.get('industry')}")
                st.markdown(f"**Target Market:** {strat.get('target_market')} | **Scale:** {strat.get('scale')}")
                st.markdown(f"**Location:** {strat.get('location')}")
                st.markdown(f"**Challenge:** {strat.get('challenge')}")
                st.markdown(f"**Goal:** {strat.get('goal')}")
                st.divider()
                st.markdown("### 🤖 AI Strategy Report")
                st.markdown(strat.get("ai_response"))

# =====================================================
# HOME PAGE
# =====================================================
if st.session_state.page == "Home":
    # Hero Section with Animation
    st.markdown("""
    <div class="animate-fade-in" style="background: linear-gradient(135deg, rgba(124, 58, 237, 0.1), rgba(6, 182, 212, 0.1)); padding: 60px; border-radius: 30px; border: 1px solid rgba(255, 255, 255, 0.05); margin-bottom: 40px; text-align: center;">
        <h1 class="gradient-text" style="font-size: 4em; margin-bottom: 10px;">Accelerate Your Growth</h1>
        <p style="color: var(--text-main); font-size: 1.5em; font-weight: 300; max-width: 800px; margin: 0 auto 20px;">
            The Intelligence Layer for Modern B2B Sales Teams. 
            Empowering your outreach with predictive AI and real-time market signals.
        </p>
        <div style="display: flex; justify-content: center; gap: 15px; margin-top: 30px;">
            <span class="badge" style="padding: 10px 20px; font-size: 1rem;">98% Accuracy</span>
            <span class="badge" style="padding: 10px 20px; font-size: 1rem;">Real-time Data</span>
            <span class="badge" style="padding: 10px 20px; font-size: 1rem;">Enterprise Grade</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Key Metrics / Value Prop
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
            <p style="color: var(--text-dim);">Boost conversion rates by up to 25% with hyper-personalized outreach generated by Gemini AI.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Core Capabilities
    st.markdown("<h3 class='gradient-text'>Core Intelligence Modules</h3>", unsafe_allow_html=True)
    row1_1, row1_2 = st.columns(2)
    with row1_1:
         st.markdown("""
         <div class="glass-card">
            <h4><i class='fas fa-user-tie' style='color:var(--primary)'></i> AI Strategy Consultant</h4>
            <ul style="color: var(--text-dim); line-height: 1.8;">
                <li>Virtual Head of Sales for strategic guidance</li>
                <li>Real-time market trend & gap analysis</li>
                <li>Competitive pricing & distribution optimization</li>
            </ul>
         </div>
         """, unsafe_allow_html=True)
    with row1_2:
         st.markdown("""
         <div class="glass-card">
            <h4><i class='fas fa-map-marked-alt' style='color:var(--primary)'></i> Location Intelligence</h4>
            <ul style="color: var(--text-dim); line-height: 1.8;">
                <li>Regional expansion heatmap analysis</li>
                <li>Localized market dynamic tracking</li>
                <li>Optimized field-sales route planning</li>
            </ul>
         </div>
         """, unsafe_allow_html=True)

    # EXTRA: New Experience section
    st.markdown("<h3 class='gradient-text'>Live Market Pulse</h3>", unsafe_allow_html=True)
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Global Leads Tracked", "1.2M+", "+5% Today")
    col_b.metric("AI Predictions", "450k", "+12% MoM")
    col_c.metric("Conversion Uplift", "22%", "Avg")
    col_d.metric("System Uptime", "99.9%", "Verified")

# =====================================================
# PROBLEM & SOLUTION
# =====================================================
if st.session_state.page == "Problem & Solution":
    st.markdown("<h1 class='gradient-text'>Bridging the Growth Gap</h1>", unsafe_allow_html=True)
    st.caption("Revolutionizing B2B sales from fragmented data to unified intelligence.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="glass-card" style="border-left: 4px solid var(--accent);">
            <h3 style="color: var(--accent);"><i class='fas fa-times-circle'></i> The Legacy Way</h3>
            <p><b>"Spray and Pray" Strategy</b></p>
            <ul style="color: var(--text-dim);">
                <li>SDRs wasting 60% of time on manual research</li>
                <li>Generic outreach that damages brand reputation</li>
                <li>Strategy based on gut-feeling and fragmented data</li>
                <li>High burnout rates due to repetitive rejection</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="glass-card" style="border-left: 4px solid var(--secondary);">
            <h3 style="color: var(--secondary);"><i class='fas fa-check-circle'></i> The Growth_AI Way</h3>
            <p><b>"Precision Strike" Strategy</b></p>
            <ul style="color: var(--text-dim);">
                <li>Automated AI dossiers on every high-value prospect</li>
                <li>Hyper-personalization at scale across all channels</li>
                <li>Data-driven insights from real-time market signals</li>
                <li>High-performing teams focused on closing, not hunting</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="glass-card" style="text-align: center; margin-top: 20px;">
        <h3 style="color: var(--primary);"><i class='fas fa-lightbulb'></i> Strategic Context</h3>
        <p style="font-size: 1.1em;">
            Modern B2B buyers complete 80% of their journey before engagement. 
            Growth_AI ensures you are present, relevant, and authoritative from the first touchpoint.
        </p>
    </div>
    """, unsafe_allow_html=True)

# =====================================================
# MARKET & ROI
# =====================================================
if st.session_state.page == "Market & ROI":
    st.markdown("<h1 class='gradient-text'>Economics of Intelligence</h1>", unsafe_allow_html=True)
    st.caption("Quantifying the impact of AI-driven sales strategies.")

    # Metrics Row
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Addressable Market", "$24B+", "+12% Growth")
    with m2:
        st.metric("Qualified Lead Velocity", "3.5x", "Increase")
    with m3:
        st.metric("Avg. CAC Reduction", "40%", "First 12 Months")

    st.markdown("<br>", unsafe_allow_html=True)

    # ROI Visualization
    with st.container():
        st.markdown("""
        <div class="glass-card">
            <h4><i class='fas fa-chart-bar' style='color:var(--secondary)'></i> Projected Revenue Uplift</h4>
            <p style="color:var(--text-dim)">Comparison between traditional manual research and AI-augmented sales intelligence.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Simple Bar Chart Data
        categories = ['Manual Research', 'Growth_AI Augmented']
        revenue = [500000, 685000] 
        colors = ['#F43F5E', '#06B6D4']

        # Use st.bar_chart for a cleaner look that matches the theme better than default matplotlib
        import pandas as pd
        roi_data = pd.DataFrame({
            'Strategy': categories,
            'Revenue ($)': revenue
        }).set_index('Strategy')
        st.bar_chart(roi_data, color="#06B6D4")

    st.markdown("""
    <div class="glass-card" style="margin-top: 20px;">
        <h3 style="color: var(--primary);"><i class='fas fa-calculator'></i> ROI Breakdown</h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div>
                <p><b>Efficiency Gains</b></p>
                <p style="color: var(--text-dim);">Recover ~750 high-value hours per year per SDR by automating prospect intelligence gathering.</p>
            </div>
            <div>
                <p><b>Revenue Optimization</b></p>
                <p style="color: var(--text-dim);">Realize $180k+ in additional annual revenue through optimized conversion and better targeting.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =====================================================
# AI STRATEGY ENGINE
# =====================================================



if st.session_state.page == "AI Strategy Engine":

    st.title("🤖 Growth_AI – " \
    "AI Strategy Engine")
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
    - Sales & distribution
    - Marketing approach
    - Strengths
    - Weaknesses
    - Strategic gaps
    - How this business can win
    """

    with st.form("ai_form"):
        business_type = st.text_input("Business Type *")
        product = st.text_input("Product / Service Name *")
        industry = st.text_input("Industry *")

        scale = st.selectbox(
            "Business Scale *",
            ["Small", "Medium", "Large"]
        )

        target_market = st.selectbox(
            "Target Market *",
            ["B2B", "B2C"]
        )

        location = st.text_input("Primary Business Location *")
        challenge = st.text_area("Current Business Challenge *")
        goal = st.selectbox(
            "Primary Goal *",
            ["Increase Revenue", "Improve Conversion", "Reduce CAC", "Scale Operations"]
        )

        submit = st.form_submit_button("🚀 Run AI Strategy")

    # ---------------- VALIDATION ----------------
    if submit:
        # Check model availability first
        if not model:
            st.error("❌ AI Service is currently unavailable. Please check your connection.")
            st.stop()

        required_text_fields = {
            "Business Type": business_type,
            "Product / Service Name": product,
            "Industry": industry,
            "Location": location,
            "Business Challenge": challenge
        }

        # Check empty / whitespace-only
        for field_name, value in required_text_fields.items():
            if not value or not value.strip():
                st.error(f"❌ {field_name} cannot be empty.")
                st.stop()

        # ---------------- AI CALL ----------------
        USER_INPUT = f"""
        Business Type: {business_type}
        Product: {product}
        Industry: {industry}
        Business Scale: {scale}
        Target Market: {target_market}
        Location: {location}
        Current Challenge: {challenge}
        Goal: {goal}
        """

        with st.spinner("🧠 Running AI strategy analysis..."):
            try:
                response = model.generate_content(MASTER_PROMPT + "\n\n" + USER_INPUT)
                result_text = response.text
                
                st.markdown(result_text)

                # ================= SAVE TO DB =================
                strategy_doc = {
                    "username": st.session_state.current_user.get("username") if isinstance(st.session_state.current_user, dict) else st.session_state.current_user,
                    "business_type": business_type,
                    "product": product,
                    "industry": industry,
                    "scale": scale,
                    "target_market": target_market,
                    "location": location,
                    "challenge": challenge,
                    "goal": goal,
                    "ai_response": result_text,
                    "created_at": datetime.datetime.now()
                }
                strategies_collection.insert_one(strategy_doc)
                st.success("✅ Strategy Report Saved to Database!")

                # ================= GRAPH =================
                st.subheader("📊 AI Impact – Before vs After")

                months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
                before = np.random.randint(30, 50, 6)
                after = before + np.random.randint(20, 35, 6)

                fig, ax = plt.subplots()
                ax.plot(months, before, marker="o", label="Before AI")
                ax.plot(months, after, marker="o", label="After AI")
                ax.set_ylabel("Business Performance Index")
                ax.legend()
                st.pyplot(fig)

                st.download_button(
                    "📄 Download AI Strategy Report",
                    result_text,
                    file_name="Growth_AI_Strategy_Report.txt"
                )

            except Exception as e:
                st.error(f"❌ An error occurred during AI generation: {e}")

# =====================================================
# GLOBAL FOOTER
# =====================================================
st.markdown("""
<div style="margin-top: 100px; padding: 40px; border-top: 1px solid rgba(255,255,255,0.05); text-align: center; color: var(--text-dim);">
    <div style="display: flex; justify-content: center; gap: 30px; margin-bottom: 20px;">
        <a href="#" style="color: var(--text-dim); text-decoration: none; font-size: 0.9em;">Privacy Policy</a>
        <a href="#" style="color: var(--text-dim); text-decoration: none; font-size: 0.9em;">Terms of Service</a>
        <a href="#" style="color: var(--text-dim); text-decoration: none; font-size: 0.9em;">Documentation</a>
    </div>
    <p style="font-size: 0.85em;">© 2025 Growth_AI Intelligence Platform. Built for the future of B2B sales.</p>
    <div style="margin-top: 15px;">
        <i class="fab fa-linkedin" style="font-size: 1.2em; margin: 0 10px; color: var(--text-dim);"></i>
        <i class="fab fa-twitter" style="font-size: 1.2em; margin: 0 10px; color: var(--text-dim);"></i>
        <i class="fab fa-github" style="font-size: 1.2em; margin: 0 10px; color: var(--text-dim);"></i>
    </div>
</div>
""", unsafe_allow_html=True)


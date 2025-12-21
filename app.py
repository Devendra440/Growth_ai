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
from dotenv import load_dotenv

# =====================================================
# LOAD ENV (Local only)
# =====================================================
load_dotenv()

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Growth_AI | B2B Sales Intelligence",
    page_icon="🚀",
    layout="wide"
)

# Load FontAwesome for Icons
st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">', unsafe_allow_html=True)


# =====================================================
# MONGODB CONNECTION (Robust for Cloud & Local)
# =====================================================

# This line checks Streamlit Cloud Secrets first, then falls back to .env
MONGO_URI = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")

@st.cache_resource
def init_connection():
    if not MONGO_URI:
        return None, "MONGO_URI not found in environment variables or secrets"
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
# API KEY CHECK (Robust for Cloud & Local)
# =====================================================
api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("❌ GOOGLE_API_KEY not found. Please add it to your secrets or .env file.")
    st.stop()

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

# =====================================================
# HEADER (PROJECT NAME RIGHT SIDE)
# =====================================================
header_left, header_right = st.columns([3, 1])
with header_left:
    st.markdown("## Growth_AI")
    st.caption("AI-Powered B2B Sales Intelligence Platform")
with header_right:
    st.markdown(
        "<div style='text-align:right; padding-top:20px;'>"
        "<b>Hackathon Project</b><br>"
        "Predict • Personalize • Convert"
        "</div>",
        unsafe_allow_html=True
    )

st.divider()

# =====================================================
# SIDEBAR – AUTH & NAVIGATION
# =====================================================
st.sidebar.title("🔐 Account")

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
            full_name = full_name.strip() if full_name else ""
            email = email.strip() if email else ""
            username = username.strip() if username else ""
            password = password.strip() if password else ""
            confirm_password = confirm_password.strip() if confirm_password else ""

            if not all([full_name, email, username, password, confirm_password]):
                st.sidebar.error("❌ All fields required")
            elif password != confirm_password:
                st.sidebar.error("❌ Passwords do not match")
            else:
                existing_user = users_collection.find_one({"username": username})
                if existing_user:
                    st.sidebar.error("❌ Username already exists")
                else:
                    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                    new_user = {
                        "name": full_name,
                        "email": email,
                        "username": username,
                        "password": hashed_password
                    }
                    users_collection.insert_one(new_user)
                    st.sidebar.success("✅ Account created. Please login.")

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
                if user and bcrypt.checkpw(password.encode('utf-8'), user["password"]):
                    st.session_state.authenticated = True
                    st.session_state.current_user = user
                    st.session_state.page = "Home"
                    st.rerun()
                else:
                    st.sidebar.error("❌ Invalid credentials")
    st.stop()

# ---------------- AFTER LOGIN ----------------
if st.session_state.current_user:
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

# =====================================================
# HISTORY PAGE
# =====================================================
if st.session_state.page == "History":
    st.title("📜 Strategy History")
    username = st.session_state.current_user.get("username") if isinstance(st.session_state.current_user, dict) else st.session_state.current_user
    cursor = strategies_collection.find({"username": username}).sort("created_at", -1)
    strategies = list(cursor)

    if not strategies:
        st.info("No history found. Run the AI Strategy Engine to generate reports!")
    else:
        for strat in strategies:
            ts = strat.get("created_at", datetime.datetime.now()).strftime("%Y-%m-%d %H:%M")
            with st.expander(f"📅 {ts} | {strat.get('business_type')} - {strat.get('product')}"):
                st.markdown(strat.get("ai_response"))

# =====================================================
# HOME PAGE
# =====================================================
if st.session_state.page == "Home":
    st.markdown("""
    <div style="background-color:#1E1E1E; padding:40px; border-radius:10px; margin-bottom:20px; text-align:center;">
        <h1 style="color:#FFFFFF; font-size: 3em;">Welcome to Growth_AI</h1>
        <p style="color:#CCCCCC; font-size:1.2em;">The Intelligence Layer for Modern B2B Sales Teams</p>
    </div>
    """, unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Precision", "95%", "Accuracy")
    c2.metric("Efficiency", "60%", "Time Saved")
    c3.metric("Growth", "25%", "Conversion")

# =====================================================
# PROBLEM & SOLUTION
# =====================================================
if st.session_state.page == "Problem & Solution":
    st.title("The Gap in the Market")
    col1, col2 = st.columns(2)
    with col1:
        st.error("### The Old Way\n- Manual Research\n- Generic Outreach")
    with col2:
        st.success("### The Growth_AI Way\n- Automated Intelligence\n- Hyper-Personalization")

# =====================================================
# MARKET & ROI
# =====================================================
if st.session_state.page == "Market & ROI":
    st.title("Market Opportunity & ROI")
    m1, m2, m3 = st.columns(3)
    m1.metric("TAM", "$24B", "+12% YoY")
    m2.metric("Target", "SME B2B", "50-500 Staff")
    m3.metric("CAC Reduction", "40%", "Year 1")

# =====================================================
# AI STRATEGY ENGINE
# =====================================================
if st.session_state.page == "AI Strategy Engine":
    st.title("🤖 Growth_AI – AI Strategy Engine")
    
    MASTER_PROMPT = "You are a senior B2B Market Strategy Consultant. Provide Business Strategy, Location Intel, and Competitor Analysis."

    with st.form("ai_form"):
        business_type = st.text_input("Business Type *")
        product = st.text_input("Product / Service Name *")
        industry = st.text_input("Industry *")
        scale = st.selectbox("Scale *", ["Small", "Medium", "Large"])
        target_market = st.selectbox("Market *", ["B2B", "B2C"])
        location = st.text_input("Location *")
        challenge = st.text_area("Challenge *")
        goal = st.selectbox("Goal *", ["Increase Revenue", "Improve Conversion", "Reduce CAC", "Scale Operations"])
        submit = st.form_submit_button("🚀 Run AI Strategy")

    if submit:
        if not model:
            st.error("❌ AI Service is unavailable.")
        else:
            USER_INPUT = f"Type: {business_type}, Product: {product}, Industry: {industry}, Challenge: {challenge}"
            with st.spinner("🧠 Analyzing..."):
                try:
                    response = model.generate_content(MASTER_PROMPT + "\n\n" + USER_INPUT)
                    result_text = response.text
                    st.markdown(result_text)

                    # Save to DB
                    strategy_doc = {
                        "username": st.session_state.current_user.get("username"),
                        "business_type": business_type,
                        "product": product,
                        "ai_response": result_text,
                        "created_at": datetime.datetime.now()
                    }
                    strategies_collection.insert_one(strategy_doc)
                    st.success("✅ Saved to History!")
                except Exception as e:
                    st.error(f"Error: {e}")
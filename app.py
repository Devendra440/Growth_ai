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
# LOAD ENV
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
# MONGODB CONNECTION
# =====================================================

# Load connection string
MONGO_URI = os.getenv("MONGO_URI")

@st.cache_resource
def init_connection():
    if not MONGO_URI:
        return None
    try:
        client = pymongo.MongoClient(MONGO_URI)
        # Check if connection is successful
        client.admin.command('ping')
        return client
    except Exception as e:
        print(e)
        return None

client = init_connection()

if not client:
    st.error("❌ Failed to connect to MongoDB. Check MONGO_URI in .env")
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
                st.sidebar.error("❌ All fields required")
            elif password != confirm_password:
                st.sidebar.error("❌ Passwords do not match")
            else:
                # Check if user exists
                existing_user = users_collection.find_one({"username": username})
                if existing_user:
                    st.sidebar.error("❌ Username already exists")
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
    # Hero Section
    st.markdown("""
    <div style="background-color:#1E1E1E; padding:40px; border-radius:10px; margin-bottom:20px; text-align:center;">
        <h1 style="color:#FFFFFF; font-size: 3em;">Welcome to Growth_AI</h1>
        <p style="color:#CCCCCC; font-size:1.2em;">The Intelligence Layer for Modern B2B Sales Teams</p>
        <p style="color:#AAAAAA;">Stop guessing. Start closing.</p>
    </div>
    """, unsafe_allow_html=True)

    # Key Metrics / Value Prop
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### <i class='fas fa-crosshairs' style='color:#FF4B4B;'></i> Precision", unsafe_allow_html=True)
        st.info("Identify high-value leads with 95% accuracy using our predictive scoring algorithms.")
    with c2:
        st.markdown("### <i class='fas fa-bolt' style='color:#FF4B4B;'></i> Speed", unsafe_allow_html=True)
        st.warning("Reduce research time from hours to minutes. Get instant strategy briefs.")
    with c3:
        st.markdown("### <i class='fas fa-chart-line' style='color:#FF4B4B;'></i> Conversion", unsafe_allow_html=True)
        st.success("Increase close rates by 25% with hyper-personalized outreach strategies.")

    st.divider()

    st.markdown("### <i class='fas fa-layer-group'></i> Core Capabilities", unsafe_allow_html=True)
    row1_1, row1_2 = st.columns(2)
    with row1_1:
         st.markdown("""
         **<i class='fas fa-user-tie'></i> AI Strategy Consultant**
         - Acts as a virtual Head of Sales.
         - Analyzes market trends and competitor gaps.
         - Suggests pricing and distribution models.
         """, unsafe_allow_html=True)
    with row1_2:
         st.markdown("""
         **<i class='fas fa-map-marked-alt'></i> Location Intelligence**
         - Pinpoint the best regions for expansion.
         - Understand local market dynamics.
         - Optimize field sales routings.
         """, unsafe_allow_html=True)

# =====================================================
# PROBLEM & SOLUTION
# =====================================================
if st.session_state.page == "Problem & Solution":
    st.title("The Gap in the Market")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### <i class='fas fa-times-circle' style='color:#ff4b4b;'></i> The Old Way", unsafe_allow_html=True)
        st.error("""
        **"Spray and Pray"**
        
        *   **Manual Research:** SDRs spend 60% of time just finding data.
        *   **Generic Outreach:** "Dear Sir/Madam" emails that get deleted.
        *   **Gut-Feel Decisions:** Strategy based on intuition, not data.
        *   **High Burnout:** Reps are tired of rejection from bad leads.
        """)
        
    with col2:
        st.markdown("### <i class='fas fa-check-circle' style='color:#00cc96;'></i> The Growth_AI Way", unsafe_allow_html=True)
        st.success("""
        **"Precision Strike"**
        
        *   **Automated Intelligence:** Instant dossiers on any prospect.
        *   **Hyper-Personalization:** Messages tailored to specific pain points.
        *   **Data-Driven:** Strategy backed by real-time market signals.
        *   **High Morale:** Reps focus only on leads ready to buy.
        """)

    st.divider()
    
    st.markdown("### <i class='fas fa-lightbulb' style='color:#FFCA28;'></i> Why Now?", unsafe_allow_html=True)
    st.markdown("""
    The B2B buying journey has changed. Buyers do **80% of their research** before ever talking to a sales rep. 
    If you aren't personalizing your approach from the very first touchpoint, you've already lost.
    
    **Growth_AI bridges the data gap to give you the unfair advantage.**
    """)

# =====================================================
# MARKET & ROI
# =====================================================
if st.session_state.page == "Market & ROI":
    st.title("Market Opportunity & ROI")
    st.caption("Why investing in Sales Intelligence is a no-brainer")

    # Metrics Row
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Addressable Market", "$24B", "+12% YoY")
    m2.metric("Target Audience", "SME B2B", "50-500 Staff")
    m3.metric("Avg. CAC Reduction", "40%", "Year 1")

    st.divider()

    # ROI Visualization
    st.subheader("Projected ROI for a 5-Person Sales Team")
    
    # Simple Bar Chart Data
    categories = ['Manual Process', 'With Growth_AI']
    revenue = [500000, 650000] # Example revenue numbers
    colors = ['#ff4b4b', '#00cc96']

    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.barh(categories, revenue, color=colors)
    ax.set_xlabel('Annual Revenue Generated ($)')
    ax.set_title('Annual Revenue Comparison')
    
    # Add values to bars
    for i, v in enumerate(revenue):
        ax.text(v + 10000, i, f"${v:,}", va='center', fontweight='bold')

    st.pyplot(fig)

    st.markdown("""
    ### <i class='fas fa-calculator'></i> The Math Breakdown
    1.  **Time Saved:** 15 hours/week per rep = **750 hours/year regained**.
    2.  **Conversion:** +5% close rate on same volume = **$100k+ new revenue**.
    3.  **Retention:** Better fit clients churn less.
    
    **Total Annual Uplift: ~$150,000+**
    """, unsafe_allow_html=True)

# =====================================================
# AI STRATEGY ENGINE
# =====================================================



if st.session_state.page == "AI Strategy Engine":

    st.title("🤖 Growth_AI – AI Strategy Engine")
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


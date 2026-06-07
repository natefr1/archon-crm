import streamlit as st
import pandas as pd
import gspread

st.set_page_config(page_title="Archon Estates CRM", layout="centered")

# Liquid Glass CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif');
    .stApp { background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%); font-family: -apple-system, sans-serif; }
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>select { background: rgba(255, 255, 255, 0.6) !important; backdrop-filter: blur(10px); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.8); padding: 10px; }
    .stButton>button { width: 100%; border-radius: 14px; background: rgba(0, 122, 255, 0.85) !important; color: white; font-weight: 600; padding: 12px; }
    .stButton>button:hover { background: rgba(0, 122, 255, 1) !important; }
    .glass-card { background: rgba(255, 255, 255, 0.45); backdrop-filter: blur(15px); border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.6); padding: 20px; text-align: center; }
    .high-prob { color: #34c759; font-weight: bold; } .med-prob { color: #ff9f0a; font-weight: bold; } .low-prob { color: #ff3b30; font-weight: bold; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- AUTHENTICATION SYSTEM ---
USER_CREDENTIALS = {
    "nathan": "admin123",
    "jason": "hunter1",
    "monica": "dispo1"
}

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h2 style='text-align: center;'>Archon Estates Portal</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Authorized Personnel Only</p>", unsafe_allow_html=True)
    
    username = st.text_input("Username").lower()
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state["logged_in"] = True
            st.session_state["user"] = username
            st.rerun()
        else:
            st.error("Invalid credentials.")
    st.stop()

# --- LIVE DATABASE CONNECTION ---
@st.cache_data(ttl=600) # Refreshes the data every 10 minutes
def load_database():
    try:
        # 1. Cloud Mode: Tries to pull from Streamlit's secure vault first
        if "gcp_service_account" in st.secrets:
            credentials_dict = dict(st.secrets["gcp_service_account"])
            gc = gspread.service_account_from_dict(credentials_dict)
        # 2. Local Mode: Falls back to the file on your PC
        else:
            gc = gspread.service_account(filename="credentials.json")
            
        sheet = gc.open("Archon_Scraper_Output").sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        # Return an empty dataframe with the expected columns so the app doesn't crash
        return pd.DataFrame(columns=["Address", "Scraped_ARV", "SqFt"])

# Load the live data
db = load_database()

# --- MAIN APP ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try:
        st.image("archon_logo.png", width=180) 
    except:
        st.markdown("<h3 style='text-align:center;'>Archon Estates</h3>", unsafe_allow_html=True)

st.success(f"Welcome back, {st.session_state['user'].capitalize()}")
st.markdown("---")

# Address Lookup
address = st.text_input("Property Address")

arv_val = 0
sqft_val = 0

if address:
    # Check if address is in the live Google Sheet
    match = db[db['Address'].astype(str).str.contains(address, case=False, na=False)]
    
    if not match.empty:
        st.info("✅ Found in database! Auto-filling data...")
        arv_val = int(match.iloc[0]['Scraped_ARV'])
        sqft_val = int(match.iloc[0]['SqFt'])
    else:
        st.warning("⚠️ Not found in database. Please enter ARV and SqFt manually.")

st.markdown("#### Market Data")
col1, col2 = st.columns(2)
with col1:
    arv = st.number_input("Zillow/Redfin ARV ($)", min_value=0, value=arv_val, step=5000)
    sqft = st.number_input("Square Footage", min_value=0, value=sqft_val, step=100)
with col2:
    fee = st.number_input("Target Fee ($)", min_value=0, value=10000, step=1000)
    condition = st.selectbox("Property Condition", ["Light (Cosmetic)", "Medium (Kitchen/Bath)", "Heavy (Full Gut)"])

repair_multipliers = {"Light (Cosmetic)": 15, "Medium (Kitchen/Bath)": 30, "Heavy (Full Gut)": 60}

if st.button("Calculate Final Offer"):
    if arv == 0 or sqft == 0:
        st.error("Please enter a valid ARV and Square Footage to calculate.")
    else:
        estimated_repairs = sqft * repair_multipliers[condition]
        safe_arv = arv * 0.90
        mao = (safe_arv * 0.70) - estimated_repairs
        max_offer = mao - fee
        
        st.divider()
        if max_offer <= 0:
            st.error("🚨 DEAD DEAL: The repair costs and your fee are higher than the 70% rule allows.")
        else:
            st.success("✅ VIABLE DEAL: The math supports a wholesale transaction.")
            t1, t2, t3 = st.columns(3)
            
            t1.markdown(f"<div class='glass-card'><h4>The Anchor</h4><h2>${max_offer - 15000:,.0f}</h2><span class='high-prob'>95% Success</span></div>", unsafe_allow_html=True)
            t2.markdown(f"<div class='glass-card'><h4>The Target</h4><h2>${max_offer - 5000:,.0f}</h2><span class='med-prob'>80% Success</span></div>", unsafe_allow_html=True)
            t3.markdown(f"<div class='glass-card'><h4>The Ceiling</h4><h2>${max_offer:,.0f}</h2><span class='low-prob'>50% Success</span></div>", unsafe_allow_html=True)

if st.button("Logout"):
    st.session_state["logged_in"] = False
    st.rerun()
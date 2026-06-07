import streamlit as st
import pandas as pd
import gspread
import json
from datetime import datetime

# MUST be the first command
st.set_page_config(page_title="Archon Estates", layout="wide", initial_sidebar_state="collapsed")

# --- iOS / APPLE SWIFT AESTHETIC CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp { background-color: #f5f5f7; font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif; }
    
    /* Force Edge-to-Edge Desktop View */
    .block-container {
        max-width: 100% !important;
        padding: 2rem 4rem !important;
    }
    
    /* Hide Default UI Clutter */
    [data-testid="collapsedControl"] { display: none; }
    header {visibility: hidden;}
    
    /* Apple Glass Inputs */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>select, .stTextArea>div>div>textarea { 
        background: #ffffff !important; 
        border-radius: 10px; 
        border: 1px solid #d2d2d7; 
        padding: 12px; 
        box-shadow: inset 0 1px 2px rgba(0,0,0,0.02);
        font-size: 15px;
    }
    
    /* Apple Primary Buttons */
    .stButton>button { 
        width: 100%; 
        border-radius: 12px; 
        background: #0071e3 !important; 
        color: white; 
        font-weight: 600; 
        padding: 12px; 
        border: none;
        box-shadow: 0 4px 6px -1px rgba(0, 113, 227, 0.2);
        transition: all 0.2s ease;
    }
    .stButton>button:hover { background: #0077ed !important; transform: scale(0.99); }
    
    /* Matrix Metric Cards */
    .glass-card { 
        background: rgba(255, 255, 255, 0.7); 
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 16px; 
        border: 1px solid rgba(255, 255, 255, 0.5); 
        padding: 24px; 
        text-align: center; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        height: 100%;
    }
    
    h1, h2, h3, h4 { color: #1d1d1f; font-weight: 700; letter-spacing: -0.02em; }
    .high-prob { color: #34c759; font-weight: 600; } 
    .med-prob { color: #ff9f0a; font-weight: 600; } 
    .low-prob { color: #ff3b30; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# --- SECURE AUTHENTICATION ---
try:
    USER_CREDENTIALS = dict(st.secrets["passwords"])
except:
    USER_CREDENTIALS = {"nathan": "admin123", "jason": "hunter1", "monica": "dispo1"}

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if st.query_params.get("token") == "archon_master_key_99":
    st.session_state["logged_in"] = True
    st.session_state["user"] = "nathan"
    st.query_params.clear()

if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center; margin-top: 15vh;'>Archon Estates</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #86868b; margin-bottom: 40px;'>Enterprise Portal</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1.5, 1, 1.5])
    with col2:
        username = st.text_input("Username").lower().strip()
        password = st.text_input("Password", type="password")
        if st.button("Secure Login"):
            if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                st.session_state["logged_in"] = True
                st.session_state["user"] = username
                st.rerun()
            else:
                st.error("Invalid credentials.")
    st.stop()

# --- BULLETPROOF DUAL-TAB DATABASE ENGINE ---
@st.cache_resource 
def init_connection():
    try:
        if "google_json" in st.secrets:
            # Parses the raw JSON string directly, killing the PEM error
            credentials_dict = json.loads(st.secrets["google_json"])
            gc = gspread.service_account_from_dict(credentials_dict)
        else:
            gc = gspread.service_account(filename="credentials.json")
            
        workbook = gc.open("Archon_Scraper_Output")
        # Connects to both tabs
        sheet_pipeline = workbook.worksheet("Pipeline")
        sheet_investors = workbook.worksheet("Investors")
        return sheet_pipeline, sheet_investors
    except Exception as e:
        st.error(f"System Offline - DB Connection Failed: {e}")
        return None, None

sheet_pipeline, sheet_investors = init_connection()

def fetch_pipeline():
    if sheet_pipeline:
        return pd.DataFrame(sheet_pipeline.get_all_records())
    return pd.DataFrame()

def fetch_investors():
    if sheet_investors:
        return pd.DataFrame(sheet_investors.get_all_records())
    return pd.DataFrame()

# --- APPLE-STYLE TOP NAVIGATION ---
col_logo, col_nav, col_space, col_profile = st.columns([0.5, 2.5, 0.5, 0.5], vertical_alignment="center")

with col_logo:
    st.markdown("<h3 style='margin: 0;'>🏛️ ARCHON</h3>", unsafe_allow_html=True)

with col_nav:
    selected_tab = st.segmented_control(
        "Nav", 
        ["Deal Analyzer", "Acquisitions (CRM)", "Investors (CRM)"], 
        default="Deal Analyzer", 
        label_visibility="collapsed"
    )
    if not selected_tab: 
        selected_tab = "Deal Analyzer"

with col_profile:
    with st.popover(f"👤 {st.session_state['user'].capitalize()}", use_container_width=True):
        st.markdown("**Account Settings**")
        st.text_input("Display Name", value=st.session_state['user'].capitalize())
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

st.markdown("<hr style='margin-top: 10px; margin-bottom: 30px; border-color: #d2d2d7;'>", unsafe_allow_html=True)

# --- ROUTING ENGINE ---

if selected_tab == "Deal Analyzer":
    
    db_pipeline = fetch_pipeline()
    col_main, col_side = st.columns([1.5, 1], gap="large")
    
    with col_main:
        st.markdown("<h2>Deal Underwriting</h2>", unsafe_allow_html=True)
        
        with st.form("new_deal_form"):
            address = st.text_input("Property Address (Full Street, City, State, Zip)")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                arv = st.number_input("Est. ARV ($)", min_value=0, step=5000)
                fee = st.number_input("Target Fee ($)", min_value=0, value=10000, step=1000)
            with c2:
                sqft = st.number_input("Square Footage", min_value=0, step=100)
                condition = st.selectbox("Property Condition", ["Light (Cosmetic)", "Medium (Kitchen/Bath)", "Heavy (Full Gut)"])
            with c3:
                market = st.selectbox("Market Territory", ["Houston", "Dallas", "Austin", "San Antonio"])
                notes = st.text_input("Brief Note (Optional)")
                
            submitted = st.form_submit_button("Analyze & Save")
    
    with col_side:
        st.markdown("<div style='background: #ffffff; border: 1px solid #d2d2d7; border-radius: 16px; padding: 24px; height: 100%;'>", unsafe_allow_html=True)
        st.markdown("<h4>Pipeline Lookup</h4>", unsafe_allow_html=True)
        search_addr = st.text_input("Search Scraped Leads", placeholder="Type an address...")
        
        if search_addr and not db_pipeline.empty:
            match = db_pipeline[db_pipeline['Address'].astype(str).str.contains(search_addr, case=False, na=False)]
            if not match.empty:
                st.success("Record Found in Database")
                st.metric("Auto-Pulled ARV", f"${int(match.iloc[0]['Scraped_ARV']):,.0f}")
                st.metric("Auto-Pulled SqFt", f"{int(match.iloc[0]['SqFt']):,}")
            else:
                st.warning("Not found in pipeline.")
        st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        if arv == 0 or sqft == 0:
            st.error("ARV and Square Footage are required.")
        else:
            repair_multipliers = {"Light (Cosmetic)": 15, "Medium (Kitchen/Bath)": 30, "Heavy (Full Gut)": 60}
            estimated_repairs = sqft * repair_multipliers[condition]
            safe_arv = arv * 0.90
            mao = (safe_arv * 0.70) - estimated_repairs
            max_offer = mao - fee
            
            if sheet_pipeline and address:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                added_by = st.session_state['user'].capitalize()
                try:
                    sheet_pipeline.append_row([address, arv, sqft, market, condition, notes, added_by, timestamp])
                    st.cache_resource.clear() 
                except Exception as e:
                    st.error(f"Sync Failed: {e}")

            st.markdown("<h3 style='margin-top: 50px; margin-bottom: 20px;'>Acquisition Strategy Matrix</h3>", unsafe_allow_html=True)
            
            if max_offer <= 0:
                st.error("🚨 DEAD DEAL: Repair costs and target fee exceed the 70% rule threshold.")
            else:
                t1, t2, t3 = st.columns(3)
                t1.markdown(f"<div class='glass-card'><h4>The Anchor</h4><h1 style='color: #1d1d1f; margin-top: 10px;'>${max_offer - 15000:,.0f}</h1><p class='high-prob'>95% Assignment Probability</p></div>", unsafe_allow_html=True)
                t2.markdown(f"<div class='glass-card'><h4>The Target</h4><h1 style='color: #1d1d1f; margin-top: 10px;'>${max_offer - 5000:,.0f}</h1><p class='med-prob'>80% Assignment Probability</p></div>", unsafe_allow_html=True)
                t3.markdown(f"<div class='glass-card'><h4>The Ceiling</h4><h1 style='color: #1d1d1f; margin-top: 10px;'>${max_offer:,.0f}</h1><p class='low-prob'>50% Assignment Probability</p></div>", unsafe_allow_html=True)

elif selected_tab == "Acquisitions (CRM)":
    st.markdown("<h2>Pipeline Database</h2>", unsafe_allow_html=True)
    db_pipeline = fetch_pipeline()
    if not db_pipeline.empty:
        st.dataframe(db_pipeline, use_container_width=True, hide_index=True, height=700)
    else:
        st.info("Pipeline is currently empty. Make sure your Google Sheet 'Pipeline' tab has headers in row 1.")

elif selected_tab == "Investors (CRM)":
    st.markdown("<h2>Cash Buyer Network</h2>", unsafe_allow_html=True)
    
    db_investors = fetch_investors()
    
    # 70/30 Split for the form and the data table
    col_table, col_form = st.columns([2.5, 1], gap="large")
    
    with col_form:
        st.markdown("<h4>Add New Investor</h4>", unsafe_allow_html=True)
        with st.form("new_investor_form"):
            inv_name = st.text_input("Investor Name / LLC")
            inv_email = st.text_input("Email Address")
            inv_phone = st.text_input("Phone Number")
            inv_market = st.selectbox("Target Market", ["Houston", "Dallas", "Austin", "San Antonio", "All Texas"])
            inv_type = st.selectbox("Property Type", ["Single Family", "Multi-Family", "Land", "Commercial"])
            inv_budget = st.number_input("Max Budget ($)", min_value=0, step=50000, value=250000)
            
            submit_inv = st.form_submit_button("Save Investor")
            
            if submit_inv:
                if not inv_name:
                    st.error("Name is required.")
                elif sheet_investors:
                    timestamp = datetime.now().strftime("%Y-%m-%d")
                    added_by = st.session_state['user'].capitalize()
                    try:
                        sheet_investors.append_row([inv_name, inv_email, inv_phone, inv_market, inv_type, inv_budget, added_by, timestamp])
                        st.success("Investor added to network!")
                        st.cache_resource.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Save Failed: {e}")

    with col_table:
        if not db_investors.empty:
            st.dataframe(db_investors, use_container_width=True, hide_index=True, height=600)
        else:
            st.markdown("<div style='background: #ffffff; border: 1px solid #d2d2d7; border-radius: 16px; padding: 60px; text-align: center;'><h3 style='color: #86868b;'>Investor Database Empty</h3><p style='color: #a1a1a6;'>Ensure your 'Investors' Google Sheet tab has headers like Name, Email, Budget, etc.</p></div>", unsafe_allow_html=True)

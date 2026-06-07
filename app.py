import streamlit as st
import pandas as pd
import gspread
from datetime import datetime

st.set_page_config(page_title="Archon Estates", layout="wide", initial_sidebar_state="collapsed")

# Inject Custom CSS for an Edge-to-Edge Website Look
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    .stApp { background-color: #f4f5f7; font-family: 'Inter', sans-serif; }
    
    /* 🚨 THE FIX: Force 100% width and remove Streamlit's massive default margins */
    .block-container {
        max-width: 100% !important;
        padding-top: 2rem !important;
        padding-right: 4rem !important;
        padding-left: 4rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* Hide default sidebar and header */
    [data-testid="collapsedControl"] { display: none; }
    header {visibility: hidden;}
    
    /* Premium Top Navigation Bar */
    div.row-widget.stRadio > div { 
        flex-direction: row; 
        justify-content: left; 
        gap: 30px;
        background: transparent; 
        padding: 0px; 
    }
    
    /* Glassmorphism Inputs */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>select, .stTextArea>div>div>textarea { 
        background: #ffffff !important; 
        border-radius: 8px; 
        border: 1px solid #e2e8f0; 
        padding: 12px; 
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    /* SaaS Primary Button */
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        background: #0f172a !important; 
        color: white; 
        font-weight: 600; 
        padding: 12px; 
        border: none;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    .stButton>button:hover { background: #334155 !important; }
    
    /* Wide Glass Cards for the Matrix */
    .glass-card { 
        background: white; 
        border-radius: 12px; 
        border: 1px solid #e2e8f0; 
        padding: 24px; 
        text-align: center; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        height: 100%;
    }
    
    /* Typography */
    h1, h2, h3 { color: #0f172a; font-weight: 800; tracking: -0.02em; }
    .high-prob { color: #10b981; font-weight: 600; } 
    .med-prob { color: #f59e0b; font-weight: 600; } 
    .low-prob { color: #ef4444; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# --- AUTHENTICATION ---
try:
    USER_CREDENTIALS = dict(st.secrets["passwords"])
except:
    USER_CREDENTIALS = {"nathan": "admin123", "jason": "hunter1", "monica": "dispo1"}

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# VIP Magic Link
if st.query_params.get("token") == "archon_master_key_99":
    st.session_state["logged_in"] = True
    st.session_state["user"] = "nathan"
    st.query_params.clear()

if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center; margin-top: 15vh;'>Archon Estates</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b;'>Enterprise Portal</p>", unsafe_allow_html=True)
    
    # Centered login box
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

# --- DATABASE CONNECTION ---
@st.cache_resource 
def init_connection():
    try:
        credentials_dict = dict(st.secrets["gcp_service_account"])
        
        # Bulletproof cleaning script for the RSA key structure
        raw_key = credentials_dict["private_key"]
        
        # Normalize line endings and eliminate literal double-escaped strings
        clean_key = raw_key.replace('\\n', '\n').replace('\r', '').strip()
        
        credentials_dict["private_key"] = clean_key
        
        gc = gspread.service_account_from_dict(credentials_dict)
        return gc.open("Archon_Scraper_Output").sheet1
    except Exception as e:
        st.error(f"Database Connection Failed: {e}")
        return None

# --- EDGE-TO-EDGE TOP NAVIGATION ---
# Using 4 columns to spread the nav bar across the entire screen width
col_logo, col_nav, col_space, col_profile = st.columns([0.5, 2, 1, 0.5])

with col_logo:
    st.markdown("<h3 style='margin: 0; padding-top: 5px;'>🏛️ ARCHON</h3>", unsafe_allow_html=True)

with col_nav:
    current_tab = st.radio("Navigation", ["Deal Analyzer", "Acquisitions (CRM)", "Investors (CRM)"], horizontal=True, label_visibility="collapsed")

with col_profile:
    with st.popover(f"👤 {st.session_state['user'].capitalize()}", use_container_width=True):
        st.markdown("**Account Settings**")
        st.text_input("Display Name", value=st.session_state['user'].capitalize())
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

st.markdown("<hr style='margin-top: 0px; margin-bottom: 30px; border-color: #e2e8f0;'>", unsafe_allow_html=True)

# --- FULL WIDTH VIEWS ---
db = fetch_data()

if current_tab == "Deal Analyzer":
    
    # We split the screen 60/40. Left side inputs, Right side database lookup
    col_main, col_side = st.columns([1.5, 1])
    
    with col_main:
        st.markdown("<h2>New Deal Underwriting</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #64748b; margin-bottom: 20px;'>Enter the property parameters to generate your acquisition strategy.</p>", unsafe_allow_html=True)
        
        with st.form("new_deal_form"):
            address = st.text_input("Property Address (Full Street, City, State, Zip)")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                arv = st.number_input("Zillow/Redfin ARV ($)", min_value=0, step=5000)
                fee = st.number_input("Target Wholesale Fee ($)", min_value=0, value=10000, step=1000)
            with c2:
                sqft = st.number_input("Square Footage", min_value=0, step=100)
                condition = st.selectbox("Property Condition", ["Light (Cosmetic)", "Medium (Kitchen/Bath)", "Heavy (Full Gut)"])
            with c3:
                market = st.selectbox("Market Territory", ["Houston", "Dallas", "Austin", "San Antonio"])
                notes = st.text_input("Brief Note (Optional)")
                
            submitted = st.form_submit_button("Analyze & Save Deal")
    
    with col_side:
        st.markdown("<div style='background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; height: 100%;'>", unsafe_allow_html=True)
        st.markdown("<h4>Database Lookup</h4>", unsafe_allow_html=True)
        search_addr = st.text_input("Quick Search Pipeline", placeholder="Type an address...")
        
        if search_addr and not db.empty:
            match = db[db['Address'].astype(str).str.contains(search_addr, case=False, na=False)]
            if not match.empty:
                st.success("Record Found")
                st.metric("Auto-Pulled ARV", f"${int(match.iloc[0]['Scraped_ARV']):,.0f}")
                st.metric("Auto-Pulled SqFt", f"{int(match.iloc[0]['SqFt']):,}")
            else:
                st.warning("Not found in pipeline.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Offer Matrix stretching across the bottom
    if submitted:
        if arv == 0 or sqft == 0:
            st.error("ARV and Square Footage are required to calculate the matrix.")
        else:
            # Core Math
            repair_multipliers = {"Light (Cosmetic)": 15, "Medium (Kitchen/Bath)": 30, "Heavy (Full Gut)": 60}
            estimated_repairs = sqft * repair_multipliers[condition]
            safe_arv = arv * 0.90
            mao = (safe_arv * 0.70) - estimated_repairs
            max_offer = mao - fee
            
            # Save to Google Sheets
            if sheet and address:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                added_by = st.session_state['user'].capitalize()
                try:
                    sheet.append_row([address, arv, sqft, market, condition, notes, added_by, timestamp])
                    st.cache_resource.clear() # Clear cache so the CRM updates
                except Exception as e:
                    st.error(f"Failed to sync with Google Sheets: {e}")

            st.markdown("<h3 style='margin-top: 40px;'>Acquisition Strategy Matrix</h3>", unsafe_allow_html=True)
            
            if max_offer <= 0:
                st.error("🚨 DEAD DEAL: Repair costs and target fee exceed the 70% rule threshold.")
            else:
                t1, t2, t3 = st.columns(3)
                t1.markdown(f"<div class='glass-card'><h4>The Anchor</h4><h1 style='color: #0f172a;'>${max_offer - 15000:,.0f}</h1><p class='high-prob'>95% Assignment Probability</p><p style='color: #64748b; font-size: 14px;'>Target lowball entry. High investor demand.</p></div>", unsafe_allow_html=True)
                t2.markdown(f"<div class='glass-card'><h4>The Target</h4><h1 style='color: #0f172a;'>${max_offer - 5000:,.0f}</h1><p class='med-prob'>80% Assignment Probability</p><p style='color: #64748b; font-size: 14px;'>Standard healthy wholesale margin.</p></div>", unsafe_allow_html=True)
                t3.markdown(f"<div class='glass-card'><h4>The Ceiling</h4><h1 style='color: #0f172a;'>${max_offer:,.0f}</h1><p class='low-prob'>50% Assignment Probability</p><p style='color: #64748b; font-size: 14px;'>Absolute maximum allowable offer.</p></div>", unsafe_allow_html=True)

elif current_tab == "Acquisitions (CRM)":
    st.markdown("<h2>Pipeline Database</h2>", unsafe_allow_html=True)
    if not db.empty:
        # Streamlit dataframe natively expands to full width when use_container_width=True
        st.dataframe(db, use_container_width=True, hide_index=True, height=600)
    else:
        st.info("No properties in database yet.")

elif current_tab == "Investors (CRM)":
    st.markdown("<h2>Cash Buyer Network</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 5])
    with col1:
        st.button("+ Add Investor", use_container_width=True)
    
    st.markdown("<div style='background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 40px; text-align: center; margin-top: 20px;'><h3 style='color: #94a3b8;'>Investor Database Empty</h3><p style='color: #cbd5e1;'>Configure the Google Sheet headers to populate this table.</p></div>", unsafe_allow_html=True)

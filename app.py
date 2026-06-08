import streamlit as st
import pandas as pd
import gspread
import json
from datetime import datetime

st.set_page_config(page_title="Archon Estates", layout="wide", initial_sidebar_state="collapsed")

# --- CSS: Clean, Modern, SaaS ---
st.markdown("""
<style>
    .stApp { background-color: #f5f5f7; font-family: -apple-system, sans-serif; }
    .block-container { max-width: 100% !important; padding: 2rem 4rem !important; }
    header {visibility: hidden;}
    .stButton>button { width: 100%; border-radius: 8px; background: #0071e3 !important; color: white; font-weight: 600; }
    h1, h2, h3 { color: #1d1d1f; }
</style>
""", unsafe_allow_html=True)

# --- AUTH & DB ---
try:
    USER_CREDENTIALS = dict(st.secrets["passwords"])
    credentials_dict = json.loads(st.secrets["google_json"])
    credentials_dict["private_key"] = credentials_dict["private_key"].replace('\\n', '\n').replace('\r', '').strip()
    gc = gspread.service_account_from_dict(credentials_dict)
    # FIX: Change "Database" to match your actual file name
    workbook = gc.open("Archon_Scraper_Output") 
    sheet_pipeline = workbook.worksheet("Pipeline")
    sheet_investors = workbook.worksheet("Investors")
except Exception as e:
    st.error(f"Config Error (Check Tab Names & Secrets): {e}")
    st.stop()

# --- NAV & UI ---
col_logo, col_nav, col_profile = st.columns([1, 4, 1])
with col_logo: st.markdown("### 🏛️ ARCHON")
with col_nav:
    selected_tab = st.segmented_control("Nav", ["Deal Analyzer", "Acquisitions (CRM)", "Investors (CRM)"], default="Deal Analyzer")

# --- VIEWS ---
if selected_tab == "Deal Analyzer":
    st.markdown("<h2>Deal Underwriting</h2>", unsafe_allow_html=True)
    with st.form("new_deal"):
        c1, c2 = st.columns(2)
        with c1:
            address = st.text_input("Property Address")
            arv = st.number_input("ARV ($)", step=5000)
            sqft = st.number_input("SqFt", step=100)
        with c2:
            # FREE TEXT MARKET INPUT
            market = st.text_input("Market (City, State)", placeholder="e.g. Phoenix, AZ")
            condition = st.selectbox("Condition", ["Light", "Medium", "Heavy"])
            notes = st.text_area("Notes")
        
        if st.form_submit_button("Save to Pipeline"):
            sheet_pipeline.append_row([address, arv, sqft, market, condition, notes, "Nathan", datetime.now().strftime("%Y-%m-%d")])
            st.success("Deal Added!")

elif selected_tab == "Acquisitions (CRM)":
    st.markdown("<h2>Pipeline Database</h2>")
    df = pd.DataFrame(sheet_pipeline.get_all_records())
    # This enables the interactive sorting you wanted!
    st.dataframe(df, use_container_width=True, hide_index=True)

elif selected_tab == "Investors (CRM)":
    st.markdown("<h2>Cash Buyer Network</h2>")
    with st.form("new_investor"):
        c1, c2 = st.columns(2)
        with c1:
            inv_name = st.text_input("Investor Name")
            inv_market = st.text_input("Target Market")
            inv_budget = st.number_input("Max Budget", step=50000)
        with c2:
            inv_type = st.text_input("Property Type")
            inv_email = st.text_input("Email")
            
        if st.form_submit_button("Add Investor"):
            sheet_investors.append_row([inv_name, inv_email, inv_market, inv_type, inv_budget, datetime.now().strftime("%Y-%m-%d")])
            st.success("Investor Added!")
    
    df_inv = pd.DataFrame(sheet_investors.get_all_records())
    st.dataframe(df_inv, use_container_width=True, hide_index=True)

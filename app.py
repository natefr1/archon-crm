import streamlit as st
import pandas as pd
import gspread
from datetime import datetime

st.set_page_config(page_title="Archon Estates", layout="wide", initial_sidebar_state="collapsed")

# Inject Custom CSS for the Top Nav and Clean Look
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    .stApp { background-color: #f8f9fa; font-family: 'Inter', sans-serif; }
    /* Hide default sidebar and header */
    [data-testid="collapsedControl"] { display: none; }
    header {visibility: hidden;}
    /* Clean up the radio buttons to look like a navbar */
    div.row-widget.stRadio > div { flex-direction: row; justify-content: center; background: white; padding: 10px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

# --- AUTHENTICATION ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h2 style='text-align: center; margin-top: 100px;'>Archon Estates</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        username = st.text_input("Username").lower()
        password = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            # Bypass for testing. Add your st.secrets logic here later.
            if password == "123": 
                st.session_state["logged_in"] = True
                st.session_state["user"] = username
                st.rerun()
    st.stop()

# --- DATABASE CONNECTION (TWO-WAY) ---
@st.cache_resource # Use cache_resource for the connection object
def init_connection():
    try:
        credentials_dict = dict(st.secrets["gcp_service_account"])
        credentials_dict["private_key"] = credentials_dict["private_key"].replace('\\n', '\n')
        gc = gspread.service_account_from_dict(credentials_dict)
        return gc.open("Archon_Scraper_Output").sheet1
    except Exception as e:
        st.error(f"DB Error: Make sure you shared the Google Sheet with the bot email! Error: {e}")
        return None

sheet = init_connection()

def fetch_data():
    if sheet:
        return pd.DataFrame(sheet.get_all_records())
    return pd.DataFrame()

# --- TOP NAVIGATION BAR ---
col_logo, col_nav, col_profile = st.columns([1, 3, 1])

with col_logo:
    st.markdown("### 🏛️ ARCHON")

with col_nav:
    # This acts as our modern top-nav
    current_tab = st.radio("Navigation", ["Deal Analyzer", "Acquisitions (CRM)", "Investors (CRM)"], horizontal=True, label_visibility="collapsed")

with col_profile:
    # The new Popover feature creates the Profile Dropdown
    with st.popover(f"👤 {st.session_state['user'].capitalize()}", use_container_width=True):
        st.markdown("**Profile Settings**")
        st.text_input("Display Name", value=st.session_state['user'].capitalize())
        st.file_uploader("Upload Avatar (Coming Soon)", disabled=True)
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

st.markdown("---")

# --- VIEWS ---
db = fetch_data()

if current_tab == "Deal Analyzer":
    st.subheader("New Deal Entry")
    
    with st.form("new_deal_form"):
        col1, col2 = st.columns(2)
        with col1:
            address = st.text_input("Property Address")
            arv = st.number_input("ARV", min_value=0, step=1000)
            sqft = st.number_input("Square Footage", min_value=0, step=100)
        with col2:
            market = st.selectbox("Market", ["Houston", "Dallas", "Austin"])
            condition = st.selectbox("Condition", ["Light", "Medium", "Heavy"])
            notes = st.text_area("Rep Notes")
            
        submitted = st.form_submit_button("Analyze & Save to Database")
        
        if submitted:
            if not sheet:
                st.error("Cannot save. Database disconnected.")
            elif not address:
                st.error("Address is required.")
            else:
                # WRITE TO GOOGLE SHEETS
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                added_by = st.session_state['user'].capitalize()
                
                # Append the row directly to the Google Sheet
                try:
                    sheet.append_row([address, arv, sqft, market, condition, notes, added_by, timestamp])
                    st.success(f"Deal saved to database by {added_by}!")
                    st.cache_data.clear() # Clears cache so the CRM tab updates
                except Exception as e:
                    st.error(f"Failed to write to sheet: {e}")

elif current_tab == "Acquisitions (CRM)":
    st.subheader("Property Pipeline")
    if not db.empty:
        # Display the data. Streamlit's dataframe allows sorting by clicking columns
        st.dataframe(db, use_container_width=True, hide_index=True)
    else:
        st.info("No properties in database yet.")

elif current_tab == "Investors (CRM)":
    st.subheader("Cash Buyer Database")
    st.button("+ Add New Investor")
    st.markdown("*Investor categorization and budget tracking grid will render here.*")

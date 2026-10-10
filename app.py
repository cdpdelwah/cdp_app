import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="CDP App", layout="wide")

dash = chr(45)

# Hardcoded league registry
LEAGUE_PRESETS = {
    "CDP (Crème Dellar Prem)": 63,
    "SDM (Segundo Del Mundo)": 320,
    "BDR (Best De La Rest)": 378,
    "LDE (Liger Del Eager)": 240
}

if "page" not in st.session_state:
    st.session_state.page = "Home"

@st.cache_data(ttl=3600)
def fetch_fpl_static():
    url = f"https://draft.premierleague.com/api/bootstrap{dash}static"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    return response.json()

@st.cache_data(ttl=600)
def fetch_league_data(league_id):
    if not league_id:
        return None, None
    details_url = f"https://draft.premierleague.com/api/league/{league_id}/details"
    status_url = f"https://draft.premierleague.com/api/league/{league_id}/element{dash}status"
    
    det_resp = requests.get(details_url)
    stat_resp = requests.get(status_url)
    
    if det_resp.status_code != 200 or stat_resp.status_code != 200:
        return None, None
        
    return det_resp.json(), stat_resp.json()

def get_availability_multiplier(row):
    status = row.get("status", "a")
    chance = row.get("chance_of_playing_next_round")
    
    if status in ["i", "s", "u"]:
        return 0.0
    if pd.notna(chance):
        val = float(chance)
        if val >= 75:
            return 0.90
        if val >= 50:
            return 0.65
        if val >= 25:
            return 0.35
        return 0.0
    if status == "d":
        return 0.65
    return 1.0

def get_health_label(row):
    status = row.get("status", "a")
    chance = row.get("chance_of_playing_next_round")
    
    if status == "i":
        return "Injured (0%)"
    if status == "s":
        return "Suspended (0%)"
    if status == "u":
        return "Unavailable (0%)"
    if status == "d":
        if pd.notna(chance):
            return f"Doubtful ({int(chance)}%)"
        return "Doubtful (50%)"
    return "Fit (100%)"

# Sidebar navigation
st.sidebar.title("CDP App Navigation")

nav_choice = st.sidebar.radio(
    "Navigation Menu",
    ["Home", "Squad Analyser"],
    index=0 if st.session_state.page == "Home" else 1
)
st.session_state.page = nav_choice

st.sidebar.divider()
st.sidebar.subheader("League Selection")

selected_league_key = st.sidebar.selectbox("Active Competition", list(LEAGUE_PRESETS.keys()))
active_league_id = LEAGUE_PRESETS[selected_league_key]

# Landing Page
if st.session_state.page == "Home":
    st.title("CDP App")
    st.caption("Central Draft Intelligence and Lineup Optimization Hub")
    
    st.markdown("### Welcome to the Hub")
    st.write(
        "Select your active competition from the sidebar to inspect specific draft rosters, "
        "evaluate high priority free agents and review optimized starting formations."
    )
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Current Competition Status")
        st.info(f"**Selected League:** {selected_league_key}")
        st.success("League linked and ready")
            
        if st.button("Launch Squad Analyser", type="primary", use_container_width=True):
            st.session_state.page = "Squad Analyser"
            st.rerun()
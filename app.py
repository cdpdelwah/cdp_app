import streamlit as st
import streamlit.components.v1 as components
import requests
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import math
import functools
import json
import html
import altair as alt
from pathlib import Path
import pypdfium2 as pdfium
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

base_dir = Path(__file__).resolve().parent

# Check for Assets directory
assets_folder = base_dir / "Assets"
if not assets_folder.exists():
    assets_folder = base_dir / "assets"

# Check for Newsletters directory
newsletters_folder = base_dir / "Newsletters"
if not newsletters_folder.exists():
    newsletters_folder = base_dir / "newsletters"

logo_path = assets_folder / "SeasonX_Logo_Master.jpg"

dash = " - "

st.set_page_config(
    page_title = "CDP App | Season X",
    page_icon = str(logo_path) if logo_path.exists() else "⚽",
    layout = "wide"
)

# Hardcoded league registry
LEAGUE_PRESETS = {
    "CDP (Crème Dellar Prem)": 63,
    "SDM (Segundo Del Mundo)": 320,
    "BDR (Best De La Rest)": 378,
    "LDE (Liger Del Eager)": 240
}

# Thematic identity colours extracted directly from the Season X league crests
LEAGUE_THEMES = {
    "CDP (Crème Dellar Prem)": {
        "accent": "#f59e0b",
        "accent_glow": "rgba(245, 158, 11, 0.25)",
        "badge_bg": "#231804",
        "tag": "Crème Dellar Prem"
    },
    "SDM (Segundo Del Mundo)": {
        "accent": "#3b82f6",
        "accent_glow": "rgba(59, 130, 246, 0.25)",
        "badge_bg": "#06152d",
        "tag": "Segundo Del Mundo"
    },
    "BDR (Best De La Rest)": {
        "accent": "#f97316",
        "accent_glow": "rgba(249, 115, 22, 0.25)",
        "badge_bg": "#271004",
        "tag": "Best De La Rest"
    },
    "LDE (Liger Del Eager)": {
        "accent": "#22c55e",
        "accent_glow": "rgba(34, 197, 94, 0.25)",
        "badge_bg": "#052210",
        "tag": "Liga Del Eager"
    }
}

# Official Premier League Club Primary Color Palette for Safe Badges
CLUB_PALETTE = {
    "ARS": {"bg": "#EF0107", "text": "#ffffff", "border": "#9C824A"},
    "AVL": {"bg": "#670E36", "text": "#95BFE5", "border": "#95BFE5"},
    "BHA": {"bg": "#0057B8", "text": "#ffffff", "border": "#FFCD00"},
    "BOU": {"bg": "#DA291C", "text": "#ffffff", "border": "#000000"},
    "BRE": {"bg": "#D20000", "text": "#ffffff", "border": "#000000"},
    "CHE": {"bg": "#034694", "text": "#ffffff", "border": "#EE242C"},
    "CRY": {"bg": "#1B458F", "text": "#ffffff", "border": "#C4122E"},
    "EVE": {"bg": "#003399", "text": "#ffffff", "border": "#ffffff"},
    "FUL": {"bg": "#ffffff", "text": "#000000", "border": "#CC0000"},
    "HUL": {"bg": "#F5971D", "text": "#000000", "border": "#000000"},
    "IPS": {"bg": "#003399", "text": "#ffffff", "border": "#D20000"},
    "LEE": {"bg": "#1D428A", "text": "#FFCD00", "border": "#FFCD00"},
    "LEI": {"bg": "#003090", "text": "#ffffff", "border": "#FDBE11"},
    "LIV": {"bg": "#C8102E", "text": "#ffffff", "border": "#00B2A9"},
    "MCI": {"bg": "#6CABDD", "text": "#001838", "border": "#ffffff"},
    "MUN": {"bg": "#DA291C", "text": "#ffffff", "border": "#FBE122"},
    "NEW": {"bg": "#241F20", "text": "#ffffff", "border": "#41B6E6"},
    "NFO": {"bg": "#DD0000", "text": "#ffffff", "border": "#ffffff"},
    "SOU": {"bg": "#D71920", "text": "#ffffff", "border": "#132257"},
    "SUN": {"bg": "#EB172B", "text": "#ffffff", "border": "#000000"},
    "TOT": {"bg": "#132257", "text": "#ffffff", "border": "#ffffff"},
    "WHU": {"bg": "#7A263A", "text": "#1BB1E7", "border": "#1BB1E7"},
    "WOL": {"bg": "#FDB913", "text": "#231F20", "border": "#231F20"}
}

# Official Manager Aliases dictionary
MANAGER_ALIASES = {
    "Nick Middleton": "Nick",
    "greg probert": "Greg",
    "Greg Probert": "Greg",
    "Thomas Foy": "Foy",
    "Kennedy .": "James",
    "Kennedy": "James",
    "Andy Dellar": "Andy",
    "Jimmy Dean": "Jimmy",
    "Hughben Amorim": "Hugh",
    "Hughben": "Hugh",
    "Hugh": "Hugh",
    "Phil Wass": "Phil",
    "Bungle .": "Bungle",
    "Bungle.": "Bungle",
    "Bungle": "Bungle",
    "Gareth Williams": "Garth",
    "Joshua Stammers": "Josh",
    "Stew Hall": "Stew",
    "Sam Berry": "Sam",
    "Ali W": "Ali",
    "Crouch Chris Smith": "Crouch",
    "Dave Whitcombe": "Dave",
    "Duncan Harrison": "Duncan",
    "Barney Jones": "Barney",
    "Rob Carlisle": "Rob",
    "Rackett .": "Rackett",
    "Rackett.": "Rackett",
    "Rackett": "Rackett",
    "Mike Wilson": "Wilson",
    "Culley Will": "Culley",
    "Bobby Cowsill": "Bobby",
    "Tudor .": "Tudor",
    "Tudor.": "Tudor",
    "Tudor": "Tudor",
    "Adrian Baker": "Adi",
    "Lee Colvin": "Lee",
    "Jamie Fielding": "Jamie",
    "Tom Probert": "Tom",
    "Ben Marsden": "Ben",
    "Will Graham": "Will",
    "Niall Hession": "Niall",
    "Peter Thompson": "Pete",
    "Pete Thompson": "Pete",
    "Peter": "Pete",
    "Pete": "Pete"
}

def get_manager_alias(first_name, last_name):
    fn = str(first_name).strip() if first_name else ""
    ln = str(last_name).strip() if last_name else ""
    full_name = f"{fn} {ln}".strip()
    
    if full_name in MANAGER_ALIASES:
        return MANAGER_ALIASES[full_name]
    
    clean_full = full_name.replace(".", "").strip().lower()
    for key, alias in MANAGER_ALIASES.items():
        if key.replace(".", "").strip().lower() == clean_full:
            return alias
            
    for key, alias in MANAGER_ALIASES.items():
        if fn.lower() == key.lower() or ln.lower() == key.lower():
            return alias
            
    return fn if fn else full_name

POS_ORDER = {"GKP": 1, "DEF": 2, "MID": 3, "FWD": 4}

if "page" not in st.session_state:
    st.session_state.page = "Home"

def set_page(page_name):
    st.session_state.page = page_name
draft_pred_file = base_dir / "draft_predictions.json"

def load_draft_predictions():
    if draft_pred_file.exists():
        try:
            with open(draft_pred_file, "r", encoding = "utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def record_draft_prediction(league_id, gw, match_id, username, pick):
    data = load_draft_predictions()
    l_key = str(league_id)
    gw_key = str(gw)
    m_key = str(match_id)
    
    if l_key not in data:
        data[l_key] = {}
    if gw_key not in data[l_key]:
        data[l_key][gw_key] = {}
    if m_key not in data[l_key][gw_key]:
        data[l_key][gw_key][m_key] = {}
        
    data[l_key][gw_key][m_key][username] = pick
    
    with open(draft_pred_file, "w", encoding = "utf-8") as f:
        json.dump(data, f, indent = 2, ensure_ascii = False)


def format_remaining_players(in_play, yet_to_play):
    if in_play > 0 and yet_to_play > 0:
        return str(in_play) + " in play, " + str(yet_to_play) + " yet to play"
    if in_play > 0:
        return str(in_play) + " in play"
    if yet_to_play > 0:
        return str(yet_to_play) + " yet to play"
    return "0 to play"

def safe_float_convert(val):
    try:
        if pd.isna(val) or str(val).strip().lower() in ["nan", "none", ""]:
            return None
        f_val = float(str(val).strip().replace(",", ""))
        if math.isnan(f_val) or math.isinf(f_val):
            return None
        return f_val
    except (ValueError, TypeError):
        return None

def format_table_floats(df):
    if df is None or df.empty:
        return df
    formatted = df.copy()
    for col in formatted.columns:
        converted = formatted[col].apply(safe_float_convert)
        if converted.notna().any():
            all_valid = converted.dropna()
            is_all_int = (all_valid % 1 == 0).all()
            
            def cell_formatter(orig, num):
                if num is None or pd.isna(num):
                    return "" if pd.isna(orig) else str(orig)
                try:
                    if is_all_int:
                        return f"{int(round(num))}"
                    return f"{num:.1f}"
                except (ValueError, OverflowError, TypeError):
                    return "" if pd.isna(orig) else str(orig)

            formatted[col] = [
                cell_formatter(orig, num) for orig, num in zip(formatted[col], converted)
            ]
        else:
            formatted[col] = formatted[col].fillna("")
    return formatted

@st.cache_data(ttl = 120)
def fetch_league_data(league_id):
    if not league_id:
        return None, None
    details_url = "https://draft.premierleague.com/api/league/" + str(league_id) + "/details"
    status_url = "https://draft.premierleague.com/api/league/" + str(league_id) + "/element" + chr(45) + "status"
    
    det_resp = requests.get(details_url)
    stat_resp = requests.get(status_url)
    
    if det_resp.status_code != 200 or stat_resp.status_code != 200:
        return None, None
        
    return det_resp.json(), stat_resp.json()

@st.cache_data(ttl = 300)
def get_all_32_teams_registry():
    registry = {}
    for l_key, l_id in LEAGUE_PRESETS.items():
        details, _ = fetch_league_data(l_id)
        if details:
            entries = details.get("league_entries", [])
            for e in entries:
                alias = get_manager_alias(e.get("player_first_name", ""), e.get("player_last_name", ""))
                info = {
                    "entry_id": e.get("entry_id"),
                    "league_entry_id": e.get("id"),
                    "league_id": l_id,
                    "league_key": l_key,
                    "team_name": e.get("entry_name", "Team"),
                    "manager_name": f"{e.get('player_first_name', '')} {e.get('player_last_name', '')}".strip(),
                    "alias": alias
                }
                registry[alias.lower()] = info
                registry[e.get("entry_name", "").strip().lower()] = info
    return registry

# ----------------- CUSTOM DROPDOWN AUTHENTICATION GATE -----------------
import bcrypt
import hashlib
import hmac

config_path = base_dir / "config.yaml"
with open(config_path, "r") as file:
    config = yaml.load(file, Loader = SafeLoader)

usernames_dict = config["credentials"]["usernames"]

def make_auth_token(username_key):
    user_obj = usernames_dict.get(username_key, {})
    secret_seed = str(user_obj.get("password", "cdp_secret"))
    sig = hmac.new(secret_seed.encode(), username_key.encode(), hashlib.sha256).hexdigest()[:16]
    return f"{username_key}.{sig}"

def verify_auth_token(token_str):
    if not token_str or "." not in str(token_str):
        return None
    parts = str(token_str).split(".", 1)
    u_key = parts[0]
    if u_key in usernames_dict:
        expected = make_auth_token(u_key)
        if hmac.compare_digest(str(token_str), expected):
            return u_key
    return None

if not st.session_state.get("authentication_status", False):
    url_token = st.query_params.get("session", "")
    restored_user = verify_auth_token(url_token) if url_token else None
    if restored_user and restored_user in usernames_dict:
        st.session_state["authentication_status"] = True
        st.session_state["username"] = restored_user
        st.session_state["name"] = usernames_dict[restored_user]["name"]

if not st.session_state.get("authentication_status", False):
    st.sidebar.subheader("🔐 Season X Login")

    user_options = {}
    for u_key, u_data in usernames_dict.items():
        alias = u_data.get("alias", u_key)
        display_name = "👑 Admin (The Commissar)" if u_key.lower() == "admin" else f"{alias}"
        user_options[display_name] = u_key

    selected_display = st.sidebar.selectbox("Select Your Name", list(user_options.keys()))
    chosen_username = user_options[selected_display]

    entered_password = st.sidebar.text_input("Password", type = "password")

    if st.sidebar.button("Log In", type = "primary", use_container_width = True):
        stored_hash = usernames_dict[chosen_username]["password"]

        pass_matches = False
        try:
            if bcrypt.checkpw(entered_password.encode(), stored_hash.encode()):
                pass_matches = True
        except Exception:
            try:
                fixed_hash = stored_hash.replace("$2y$", "$2b$")
                if bcrypt.checkpw(entered_password.encode(), fixed_hash.encode()):
                    pass_matches = True
            except Exception:
                pass

        if pass_matches:
            st.session_state["authentication_status"] = True
            st.session_state["username"] = chosen_username
            st.session_state["name"] = usernames_dict[chosen_username]["name"]
            st.query_params["session"] = make_auth_token(chosen_username)
            st.rerun()
        else:
            st.sidebar.error("Incorrect password.")

    st.stop()

# Retrieve logged in manager details once authenticated
logged_username = st.session_state.get("username", "")
logged_user_data = config["credentials"]["usernames"].get(logged_username, {})
logged_alias = logged_user_data.get("alias", logged_username)
is_admin_account = (str(logged_username).strip().lower() == "admin")

if logged_username in usernames_dict:
    expected_tok = make_auth_token(logged_username)
    if st.query_params.get("session") != expected_tok:
        st.query_params["session"] = expected_tok
# ----------------- SIDEBAR BRAND & NAVIGATION -----------------if logo_path.exists():
    st.sidebar.image(str(logo_path), use_container_width = True)
else:
    st.sidebar.title("CDP App")

st.sidebar.caption("Stats, not facts | Season X Command Center")
st.sidebar.markdown(f"👤 Logged in as: **{'Admin (Commissar)' if is_admin_account else logged_alias}**")

if st.sidebar.button("Log Out", use_container_width = True):
    st.session_state["authentication_status"] = False
    st.session_state["username"] = None
    st.query_params.clear()
    st.rerun()

st.sidebar.link_button(
    "🚀 Open FPL Draft Site",
    "https://draft.premierleague.com/",
    use_container_width = True,
    type = "primary"
)

NAV_ITEMS = [
    "Home",
    "LIVE SCORES",
    "EPL Scores & Lineups",
    "Results Analyser",
    "Standings",
    "Cup & Bucket",
    "Squad Analyser",
    "Trade Hub",
    "GACS",
    "Disciplinary",
    "Newsletters",
    "Power Rankings",
    "Asterisk*"
]

st.sidebar.radio(
    "Navigation Menu",
    NAV_ITEMS,
    key = "page"
)

# ----------------- LEAGUE SELECTION (AUTO - DEFAULT TO MANAGER'S LEAGUE) -----------------
st.sidebar.divider()
st.sidebar.subheader("League Selection")

league_keys = list(LEAGUE_PRESETS.keys())

# Find the logged-in manager's division (Admin account has no forced home league)
manager_home_league = None
if not is_admin_account:
    teams_reg = get_all_32_teams_registry()
    mgr_info = teams_reg.get(logged_alias.lower())
    if mgr_info:
        manager_home_league = mgr_info.get("league_key")

raw_cookie_fav = None
try:
    raw_cookie_fav = cookie_manager.get("cdp_fav_league")
except Exception:
    pass

# Set default league when this user logs in
if is_admin_account:
    effective_default = raw_cookie_fav if raw_cookie_fav in league_keys else league_keys[0]
else:
    effective_default = manager_home_league if manager_home_league in league_keys else league_keys[0]

if st.session_state.get("league_init_user") != logged_username:
    st.session_state["active_competition"] = effective_default
    st.session_state["league_init_user"] = logged_username

def on_league_select_change():
    st.session_state["user_changed_league"] = True

def set_home_league(target_league):
    st.session_state["active_competition"] = target_league
    st.session_state["user_changed_league"] = True

selected_league_key = st.sidebar.selectbox(
    "Active Competition",
    league_keys,
    key = "active_competition",
    on_change = on_league_select_change
)

if manager_home_league:
    if selected_league_key == manager_home_league:
        st.sidebar.caption(f"⭐ {selected_league_key.split(' ')[0]} is your home league")
    else:
        st.sidebar.button(
            f"🏠 Jump to My League ({manager_home_league.split(' ')[0]})",
            use_container_width = True,
            on_click = set_home_league,
            args = (manager_home_league,)
        )
else:
    st.sidebar.caption("👑 Admin View (No default league locked)")

active_league_id = LEAGUE_PRESETS[selected_league_key]
active_theme = LEAGUE_THEMES.get(selected_league_key, LEAGUE_THEMES["CDP (Crème Dellar Prem)"])

# Accessibility Text Size Toggle
st.sidebar.divider()
large_mode = st.sidebar.toggle("🔍 Large Text Mode", value = False, key = "large_text")

# Comprehensive Global Font Scalers
root_font_size = "18px" if large_mode else "16px"
font_body = "1.24rem" if large_mode else "1.02rem"
font_caption = "1.02rem" if large_mode else "0.86rem"
font_table = "1.18rem" if large_mode else "0.98rem"
font_tab = "1.24rem" if large_mode else "1.04rem"
font_select = "1.18rem" if large_mode else "1.0rem"
font_sidebar = "1.18rem" if large_mode else "1.0rem"
font_tooltip = "19px" if large_mode else "15px"
font_chart_label = 12 if large_mode else 10

font_h1 = "2.8rem" if large_mode else "2.3rem"
font_h2 = "2.3rem" if large_mode else "1.85rem"
font_h3 = "1.9rem" if large_mode else "1.45rem"
font_h4 = "1.55rem" if large_mode else "1.2rem"

# Desktop Card Scalers
font_card_mgr = "1.65rem" if large_mode else "1.38rem"
font_card_score = "2.95rem" if large_mode else "2.35rem"
font_card_sub = "1.12rem" if large_mode else "0.94rem"
font_card_bench = "1.02rem" if large_mode else "0.85rem"
font_card_win = "1.25rem" if large_mode else "1.05rem"
font_card_status = "1.12rem" if large_mode else "0.92rem"

# Mobile Card Scalers
font_card_mgr_mobile = "1.52rem" if large_mode else "1.30rem"
font_card_score_mobile = "2.65rem" if large_mode else "2.18rem"
font_card_sub_mobile = "1.05rem" if large_mode else "0.88rem"
font_card_bench_mobile = "0.95rem" if large_mode else "0.80rem"
font_card_win_mobile = "1.18rem" if large_mode else "0.98rem"
progress_bar_height = "13px" if large_mode else "10px"

# Dynamic Pure Black CSS Engine with Targeted Scoreboard Styles
st.markdown(f"""
<style>
    html, body {{
        font-size: {root_font_size} !important;
    }}

    .stApp {{
        background-color: #000000 !important;
        color: #f1f5f9 !important;
        font-size: {font_body} !important;
    }}

    section[data-testid="stSidebar"] {{
        background-color: #06070a !important;
        border-right: 1px solid #141824 !important;
    }}

    section[data-testid="stSidebar"] * {{
        font-size: {font_sidebar} !important;
    }}

    h1 {{
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: {font_h1} !important;
        letter-spacing: -0.5px !important;
    }}

    h2 {{
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: {font_h2} !important;
        letter-spacing: -0.4px !important;
    }}

    h3 {{
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: {font_h3} !important;
        letter-spacing: -0.3px !important;
    }}

    h4, h5, h6 {{
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: {font_h4} !important;
        letter-spacing: -0.2px !important;
    }}

    .stMarkdown p, p, label {{
        color: #e2e8f0;
        font-size: {font_body};
    }}

    .stCaption, small, [data-testid="stCaptionContainer"] {{
        color: #94a3b8 !important;
        font-size: {font_caption} !important;
        line-height: 1.45 !important;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: #090c13 !important;
        border: 1px solid #182030 !important;
        border-radius: 8px !important;
        transition: border 0.2s ease;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
        border-color: {active_theme['accent']} !important;
    }}

    /* Scoreboard Card Headline & Element Classes */
    .card-mgr-title {{
        font-size: {font_card_mgr} !important;
        font-weight: 800 !important;
        color: #ffffff !important;
        line-height: 1.25 !important;
        letter-spacing: -0.3px !important;
    }}

    .card-div-tag {{
        font-size: {font_card_bench} !important;
        color: #94a3b8 !important;
        font-weight: 500 !important;
    }}

    .card-score-left {{
        font-size: {font_card_score} !important;
        line-height: 1.0 !important;
        color: #ffffff !important;
        font-weight: 900 !important;
        letter-spacing: -1px !important;
        margin: 2px 0 0 0 !important;
    }}

    .card-score-right {{
        font-size: {font_card_score} !important;
        line-height: 1.0 !important;
        color: #ffffff !important;
        font-weight: 900 !important;
        letter-spacing: -1px !important;
        text-align: right !important;
        margin: 2px 0 0 0 !important;
    }}

    .card-score-center {{
        font-size: {font_card_score} !important;
        line-height: 1.0 !important;
        color: #ffffff !important;
        font-weight: 900 !important;
        letter-spacing: -1px !important;
        text-align: center !important;
        margin: 2px 0 0 0 !important;
    }}

    .card-vs-text {{
        text-align: center !important;
        color: #64748b !important;
        font-weight: 800 !important;
        font-size: {font_card_sub} !important;
        text-transform: uppercase !important;
        margin-top: 12px !important;
    }}

    .card-proj-sub {{
        margin: 4px 0 0 0 !important;
        font-size: {font_card_sub} !important;
        color: #cbd5e1 !important;
        white-space: nowrap !important;
        font-weight: 600 !important;
    }}

    .card-bench-sub {{
        margin: 2px 0 0 0 !important;
        font-size: {font_card_bench} !important;
        color: #94a3b8 !important;
        font-weight: 500 !important;
    }}

    .card-win-pct {{
        font-size: {font_card_win} !important;
        font-weight: 800 !important;
    }}

    .card-status-badge {{
        margin: 0 !important;
        font-size: {font_card_status} !important;
        font-weight: 800 !important;
        text-align: right !important;
    }}

    /* Global Table Scaling */
    table {{
        color: #f1f5f9 !important;
        background-color: #090c13 !important;
        border-collapse: collapse !important;
        width: 100% !important;
        border-radius: 6px !important;
        overflow: hidden !important;
        font-size: {font_table} !important;
    }}
    
    thead tr th {{
        background-color: #0e131d !important;
        color: {active_theme['accent']} !important;
        border-bottom: 2px solid #182030 !important;
        font-weight: 700 !important;
        padding: 9px 12px !important;
        font-size: {font_table} !important;
        text-align: left !important;
    }}
    
    tbody tr td, tbody tr th {{
        background-color: #090c13 !important;
        border-bottom: 1px solid #141a26 !important;
        color: #cbd5e1 !important;
        padding: 9px 12px !important;
        font-size: {font_table} !important;
    }}

    tbody tr th {{
        font-weight: 600 !important;
        color: #ffffff !important;
    }}

    tbody tr:hover td, tbody tr:hover th {{
        background-color: #121724 !important;
    }}

    div[data-testid="stExpander"] {{
        background-color: #090c13 !important;
        border: 1px solid #182030 !important;
        border-radius: 6px !important;
        margin-top: 8px !important;
    }}

    div[data-testid="stExpander"] details summary {{
        color: {active_theme['accent']} !important;
        font-weight: 600 !important;
        font-size: {font_body} !important;
    }}

    /* Form Inputs and Selectboxes */
    div[data-baseweb="select"],
    div[data-baseweb="select"] > div {{
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 6px !important;
    }}

    div[data-baseweb="select"] *,
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div {{
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: 700 !important;
        font-size: {font_select} !important;
    }}

    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    div[data-baseweb="menu"],
    ul[data-baseweb="menu"],
    ul[role="listbox"],
    [role="listbox"],
    [data-testid="stSelectboxVirtualDropdown"] {{
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 6px !important;
    }}

    div[data-baseweb="popover"] *,
    div[data-baseweb="popover"] div,
    div[data-baseweb="popover"] span,
    div[data-baseweb="popover"] li,
    div[data-baseweb="menu"] *,
    ul[role="listbox"] *,
    ul[role="listbox"] li,
    li[role="option"],
    li[role="option"] *,
    [role="option"],
    [role="option"] * {{
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: 700 !important;
        font-size: {font_select} !important;
    }}

    li[role="option"]:hover,
    li[role="option"]:hover *,
    [role="option"]:hover,
    [role="option"]:hover * {{
        background-color: #f1f5f9 !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }}

    /* Tabs */
    button[data-baseweb="tab"] {{
        font-size: {font_tab} !important;
        padding: 10px 18px !important;
    }}
    button[data-baseweb="tab"] div,
    button[data-baseweb="tab"] p {{
        font-size: {font_tab} !important;
        font-weight: 700 !important;
    }}

    /* Buttons */
    button[kind="primary"],
    button[data-testid="baseButton-primary"] {{
        background-color: {active_theme['accent']} !important;
        color: #000000 !important;
        font-weight: 800 !important;
        border: none !important;
        border-radius: 6px !important;
        box-shadow: 0 0 12px {active_theme['accent_glow']} !important;
        font-size: {font_body} !important;
        padding: 8px 16px !important;
    }}

    button[kind="primary"]:hover,
    button[data-testid="baseButton-primary"]:hover {{
        filter: brightness(1.15);
        color: #000000 !important;
    }}

    button[kind="secondary"],
    button[data-testid="baseButton-secondary"] {{
        background-color: #0e121a !important;
        color: #ffffff !important;
        border: 1px solid #20293d !important;
        border-radius: 6px !important;
        font-size: {font_body} !important;
        padding: 8px 16px !important;
    }}

    button[kind="secondary"]:hover,
    button[data-testid="baseButton-secondary"]:hover {{
        border-color: {active_theme['accent']} !important;
        color: {active_theme['accent']} !important;
    }}

    /* Progress bar */
    div[data-testid="stProgressBar"] > div {{
        background-color: #121824 !important;
        height: {progress_bar_height} !important;
        border-radius: 6px !important;
    }}
    div[data-testid="stProgressBar"] > div > div {{
        background-color: {active_theme['accent']} !important;
        height: {progress_bar_height} !important;
        border-radius: 6px !important;
    }}

    /* Mobile Display Specifics without overriding card classes */
    @media (max-width: 768px) {{
        .card-mgr-title {{
            font-size: {font_card_mgr_mobile} !important;
        }}
        .card-score-left, .card-score-right, .card-score-center {{
            font-size: {font_card_score_mobile} !important;
        }}
        .card-proj-sub {{
            font-size: {font_card_sub_mobile} !important;
        }}
        .card-bench-sub {{
            font-size: {font_card_bench_mobile} !important;
        }}
        .card-win-pct {{
            font-size: {font_card_win_mobile} !important;
        }}
        thead tr th, tbody tr td, tbody tr th {{
            font-size: {font_table} !important;
            padding: 8px 10px !important;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            padding: 8px 10px !important;
        }}

        /* Strictly target ONLY the 4-division showcase on mobile: Desktop remains 4-in-a-row, Mobile becomes 2x2 */
        div[data-testid="stVerticalBlock"]:has(#division-showcase) > div[data-testid="stHorizontalBlock"] {{
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: wrap !important;
            gap: 8px !important;
        }}

        div[data-testid="stVerticalBlock"]:has(#division-showcase) > div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {{
            flex: 1 1 calc(50% - 6px) !important;
            min-width: calc(50% - 6px) !important;
            max-width: calc(50% - 6px) !important;
        }}

        div[data-testid="stVerticalBlock"]:has(#division-showcase) div[data-testid="stVerticalBlockBorderWrapper"] {{
            padding: 6px 6px !important;
        }}

        div[data-testid="stVerticalBlock"]:has(#division-showcase) button {{
            padding: 5px 3px !important;
            font-size: 0.82rem !important;
        }}
    }}
</style>
""", unsafe_allow_html = True)

# ----------------- EMBEDDED GREEN PITCH RENDERING ENGINE -----------------
def render_pitch_component(manager_alias, starters_df, bench_df, accent_color, is_large = False, show_proj_pill = False):
    if starters_df is None or starters_df.empty:
        st.info("Lineup selections not yet available.")
        return

    starters_records = starters_df.to_dict(orient = "records")
    bench_records = bench_df.to_dict(orient = "records") if bench_df is not None and not bench_df.empty else []

    def prepare_player_dict(p, is_bench = False):
        club_code = str(p.get("Club", "PL")).strip().upper()
        c_palette = CLUB_PALETTE.get(club_code, {"bg": "#1e293b", "text": "#f8fafc", "border": accent_color})

        g = int(p.get("G", 0))
        a = int(p.get("A", 0))
        cs = int(p.get("CS", 0))
        gc = int(p.get("GC", 0))
        bonus = int(p.get("Bonus", 0))
        mins = int(p.get("Mins", 0))
        pts = int(p.get("Pts", 0))
        proj = float(p.get("Proj", 0.0))
        saves = int(p.get("Saves", 0))
        p_saved = int(p.get("Penalties_Saved", 0))
        p_missed = int(p.get("Penalties_Missed", 0))
        yc = int(p.get("YC", 0))
        rc = int(p.get("RC", 0))
        defcon_hit = bool(p.get("DEFCON_Achieved", False))
        state = str(p.get("State", "FT")).strip().upper()
        sub_act = str(p.get("sub_action", "")).strip()

        raw_opp = p.get("Opp", "")
        if not raw_opp and p.get("next_3"):
            raw_opp = str(p.get("next_3", "")).split(",")[0]
        opp_str = str(raw_opp).strip() if pd.notna(raw_opp) else ""

        raw_status = str(p.get("status", "a")).lower()
        chance_val = p.get("chance_of_playing_next_round")

        status_flag_html = ""
        if raw_status == "s":
            status_flag_html = '<div class="suspension-badge"></div>'
        elif raw_status in ["i", "u"]:
            status_flag_html = '<div class="injury-badge badge-red">+</div>'
        elif raw_status == "d":
            try:
                c_num = int(chance_val) if pd.notna(chance_val) else 50
            except (ValueError, TypeError):
                c_num = 50

            if c_num <= 25:
                status_flag_html = '<div class="injury-badge badge-orange">+</div>'
            else:
                status_flag_html = '<div class="injury-badge badge-yellow">+</div>'

        badges = []
        if g > 0:
            badges.append(f"{g}⚽" if g > 1 else "⚽")
        if a > 0:
            badges.append(f"{a}🎯" if a > 1 else "🎯")
        if cs > 0 and p.get("Pos") in ["GKP", "DEF", "MID"]:
            badges.append("🛡️")
        if defcon_hit:
            badges.append("🔰")
        if bonus > 0:
            badges.append(f"{bonus}⭐")
        if p_saved > 0:
            badges.append(f"{p_saved}🧤" if p_saved > 1 else "🧤")
        if p_missed > 0:
            badges.append(f"{p_missed}❌" if p_missed > 1 else "❌")

        if show_proj_pill:
            pill_score_str = f"{proj:.1f} pts"
        elif state == "YTP":
            pill_score_str = "⏳ YTP"
        else:
            pill_score_str = f"{pts} pts"

        return {
            "name": str(p.get("Player", "Unknown")),
            "pos": str(p.get("Pos", "")),
            "status_flag": status_flag_html,
            "club": club_code,
            "opp": opp_str,
            "club_bg": c_palette["bg"],
            "club_text": c_palette["text"],
            "club_border": c_palette["border"],
            "state": state,
            "mins": mins,
            "pts": pts,
            "proj": f"{proj:.1f}",
            "pill_text": pill_score_str,
            "g": g,
            "a": a,
            "cs": cs,
            "gc": gc,
            "bonus": bonus,
            "saves": saves,
            "yc": yc,
            "rc": rc,
            "p_saved": p_saved,
            "p_missed": p_missed,
            "defcon_hit": defcon_hit,
            "sub_action": sub_act,
            "events_str": " ".join(badges),
            "is_bench": is_bench
        }

    pitch_players = []
    dugout_players = []

    for p in starters_records:
        if str(p.get("sub_action", "")).strip() == "Subbed Off":
            dugout_players.append(prepare_player_dict(p, is_bench = True))
        else:
            pitch_players.append(prepare_player_dict(p, is_bench = False))

    for p in bench_records:
        if str(p.get("sub_action", "")).strip() == "Subbed On":
            pitch_players.append(prepare_player_dict(p, is_bench = False))
        else:
            dugout_players.append(prepare_player_dict(p, is_bench = True))

    dugout_players = sorted(dugout_players, key = lambda x: POS_ORDER.get(x["pos"], 99))

    # Split substitutes into balanced rows if there are more than 5 on the bench
    dugout_rows_split = []
    if len(dugout_players) > 5:
        mid_point = (len(dugout_players) + 1) // 2
        dugout_rows_split = [dugout_players[:mid_point], dugout_players[mid_point:]]
    else:
        dugout_rows_split = [dugout_players] if dugout_players else []

    gks = [p for p in pitch_players if p["pos"] == "GKP"]
    defs = [p for p in pitch_players if p["pos"] == "DEF"]
    mids = [p for p in pitch_players if p["pos"] == "MID"]
    fwds = [p for p in pitch_players if p["pos"] == "FWD"]

    formation_rows = [
        {"role": "GKP", "players": gks},
        {"role": "DEF", "players": defs},
        {"role": "MID", "players": mids},
        {"role": "FWD", "players": fwds}
    ]

    all_players_payload = pitch_players + dugout_players
    players_json = json.dumps(all_players_payload).replace("'", "&#39;")

    token_size = "44px" if is_large else "38px"
    badge_font = "0.78rem" if is_large else "0.70rem"
    name_font = "0.74rem" if is_large else "0.68rem"
    opp_font = "0.72rem" if is_large else "0.64rem"
    pts_font = "0.84rem" if is_large else "0.74rem"
    left_banner_label = "Season Total" if show_proj_pill else "Match Total"

    # Dynamic height: gives additional vertical room if the dugout is split into 2 rows
    dynamic_container_height = 800 if len(dugout_players) > 5 else 710

    pitch_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background-color: #090c13;
            color: #f1f5f9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            overflow: hidden;
            user-select: none;
            -webkit-user-select: none;
        }}

        .pitch-container {{
            position: relative;
            width: 100%;
            max-width: 600px;
            margin: 0 auto;
            height: 560px;
            background: repeating-linear-gradient(
                180deg,
                #0f351e,
                #0f351e 70px,
                #0d2e1a 70px,
                #0d2e1a 140px
            );
            border-radius: 10px;
            border: 2px solid #1a4d2e;
            overflow: hidden;
            box-shadow: inset 0 0 40px rgba(0, 0, 0, 0.6);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 8px 10px 14px 10px;
        }}

        .pitch-svg {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            opacity: 0.35;
        }}

        .pitch-row {{
            position: relative;
            z-index: 2;
            display: flex;
            justify-content: space-around;
            align-items: center;
            width: 100%;
            margin: 2px 0;
        }}

        /* Strict flex equality anchors every icon dead-centre on its pitch position regardless of name width */
        .player-card {{
            flex: 1 1 0px !important;
            width: 0 !important;
            min-width: 0 !important;
            display: flex;
            flex-direction: column;
            align-items: center;
            cursor: pointer;
            transition: transform 0.15s ease, opacity 0.2s ease;
            position: relative;
            text-align: center;
        }}

        .player-card:hover, .player-card:active {{
            transform: scale(1.10);
            opacity: 1.0 !important;
            z-index: 20 !important;
        }}

        .player-card.state-ytp {{
            opacity: 0.62;
        }}

        .club-token {{
            width: {token_size};
            height: {token_size};
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: {badge_font};
            font-weight: 800;
            letter-spacing: 0.5px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.6);
            border-width: 2px;
            border-style: solid;
            position: relative;
            margin: 0 auto;
        }}

        .player-card.state-live .club-token {{
            box-shadow: 0 0 12px #22c55e, 0 4px 10px rgba(0, 0, 0, 0.6);
        }}
        .suspension-badge {{
            position: absolute;
            top: -4px;
            right: -3px;
            width: 9px;
            height: 13px;
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            border: 1px solid #ffffff;
            border-radius: 2px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.9);
            transform: rotate(8deg);
            z-index: 5;
        }}
        .injury-badge {{
            position: absolute;
            top: -3px;
            right: -3px;
            width: 13px;
            height: 13px;
            border-radius: 3px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.60rem;
            font-weight: 900;
            line-height: 1;
            z-index: 5;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.8);
            border: 1px solid rgba(0, 0, 0, 0.5);
        }}

        .badge-red {{ background-color: #ef4444; color: #ffffff; }}
        .badge-orange {{ background-color: #f97316; color: #ffffff; }}
        .badge-yellow {{ background-color: #eab308; color: #000000; }}

        .state-pulse {{
            position: absolute;
            top: -2px;
            right: -2px;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background-color: #22c55e;
            box-shadow: 0 0 8px #22c55e;
            animation: liveGlow 1.4s infinite ease-in-out;
        }}

        @keyframes liveGlow {{
            0%, 100% {{ transform: scale(1); opacity: 1; }}
            50% {{ transform: scale(1.35); opacity: 0.65; }}
        }}

        .sub-tag-off {{
            position: absolute;
            top: -3px;
            left: -3px;
            background: #ef4444;
            color: #ffffff;
            font-size: 0.62rem;
            font-weight: 800;
            padding: 1px 3px;
            border-radius: 3px;
        }}

        .sub-tag-on {{
            position: absolute;
            top: -3px;
            left: -3px;
            background: #22c55e;
            color: #000000;
            font-size: 0.62rem;
            font-weight: 800;
            padding: 1px 3px;
            border-radius: 3px;
        }}

        /* Floating, unclipped name pill anchored dead-center under the icon */
        .player-name-pill {{
            background: rgba(9, 12, 19, 0.94);
            border: 1px solid #1e293b;
            color: #ffffff;
            font-size: {name_font};
            font-weight: 700;
            padding: 1px 4px;
            border-radius: 4px;
            margin-top: 3px;
            white-space: normal;
            word-wrap: break-word;
            line-height: 1.15;
            letter-spacing: -0.2px;
            width: max-content;
            min-width: 48px;
            max-width: 110px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.6);
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: visible;
        }}

        .player-opp-pill {{
            background: rgba(6, 9, 17, 0.88);
            color: #cbd5e1;
            font-size: {opp_font};
            font-weight: 700;
            padding: 1px 4px;
            border-radius: 3px;
            margin-top: 1px;
            white-space: nowrap;
            letter-spacing: -0.1px;
        }}

        .player-pts-pill {{
            background: #000000;
            border: 1px solid {accent_color};
            color: {accent_color};
            font-size: {pts_font};
            font-weight: 800;
            padding: 1px 5px;
            border-radius: 4px;
            margin-top: 1px;
            min-width: 28px;
            text-align: center;
            white-space: nowrap;
        }}

        .player-card.state-live .player-pts-pill {{
            border-color: #22c55e !important;
            color: #22c55e !important;
            box-shadow: 0 0 6px rgba(34, 197, 94, 0.5);
        }}

        .player-card.state-ytp .player-pts-pill {{
            border-color: #475569 !important;
            color: #94a3b8 !important;
        }}

        .dugout-container {{
            width: 100%;
            max-width: 600px;
            margin: 8px auto 0 auto;
            background: #060911;
            border: 1px solid #182030;
            border-radius: 8px;
            padding: 8px 10px;
        }}

        .dugout-header {{
            font-size: 0.74rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            color: #94a3b8;
            margin-bottom: 6px;
            border-bottom: 1px solid #141a26;
            padding-bottom: 3px;
        }}

        .dugout-row {{
            display: flex;
            justify-content: space-around;
            align-items: center;
            width: 100%;
            margin-bottom: 8px;
        }}

        .dugout-row:last-child {{
            margin-bottom: 0;
        }}

        .modal-overlay {{
            display: none;
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.78);
            backdrop-filter: blur(6px);
            z-index: 100;
            justify-content: center;
            align-items: center;
            padding: 16px;
        }}

        .modal-card {{
            background: #090c13;
            border: 2px solid {accent_color};
            border-radius: 12px;
            width: 90%;
            max-width: 330px;
            padding: 16px 18px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.9);
            position: relative;
            animation: popIn 0.2s ease-out;
        }}

        @keyframes popIn {{
            from {{ opacity: 0; transform: scale(0.92); }}
            to {{ opacity: 1; transform: scale(1); }}
        }}

        .modal-close {{
            position: absolute;
            top: 10px;
            right: 14px;
            color: #94a3b8;
            font-size: 1.4rem;
            font-weight: bold;
            cursor: pointer;
            line-height: 1;
        }}
        .modal-close:hover {{ color: #ffffff; }}

        .modal-title {{
            font-size: 1.25rem;
            font-weight: 800;
            color: #ffffff;
            margin-right: 24px;
        }}

        .modal-meta {{
            font-size: 0.85rem;
            color: #94a3b8;
            margin-bottom: 12px;
            font-weight: 600;
        }}

        .modal-score-banner {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            background: #0f1523;
            border-radius: 8px;
            padding: 8px 12px;
            margin-bottom: 12px;
            border-left: 4px solid {accent_color};
        }}

        .modal-pts-big {{
            font-size: 1.8rem;
            font-weight: 900;
            color: {accent_color};
        }}

        .stat-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-bottom: 8px;
        }}

        .stat-item {{
            background: #0c101a;
            border: 1px solid #182030;
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 0.82rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .stat-label {{ color: #94a3b8; font-weight: 600; }}
        .stat-val {{ color: #ffffff; font-weight: 800; }}
        .stat-defcon-hit {{
            grid-column: span 2;
            background: #052210;
            border-color: #22c55e;
            color: #22c55e;
        }}
        .stat-penalty-miss {{
            grid-column: span 2;
            background: #270606;
            border-color: #ef4444;
            color: #ef4444;
        }}
    </style>
    </head>
    <body>

    <div class="pitch-container" id="pitch-container">
        <svg class="pitch-svg" viewBox="0 0 360 520" preserveAspectRatio="none">
            <rect x="15" y="15" width="330" height="490" fill="none" stroke="#ffffff" stroke-width="2"/>
            <line x1="15" y1="260" x2="345" y2="260" stroke="#ffffff" stroke-width="2"/>
            <circle cx="180" cy="260" r="48" fill="none" stroke="#ffffff" stroke-width="2"/>
            <circle cx="180" cy="260" r="3" fill="#ffffff"/>
            <rect x="90" y="15" width="180" height="80" fill="none" stroke="#ffffff" stroke-width="2"/>
            <rect x="135" y="15" width="90" height="30" fill="none" stroke="#ffffff" stroke-width="2"/>
            <circle cx="180" cy="65" r="2.5" fill="#ffffff"/>
            <rect x="90" y="425" width="180" height="80" fill="none" stroke="#ffffff" stroke-width="2"/>
            <rect x="135" y="475" width="90" height="30" fill="none" stroke="#ffffff" stroke-width="2"/>
            <circle cx="180" cy="455" r="2.5" fill="#ffffff"/>
        </svg>
    """

    for row_info in formation_rows:
        pitch_html += '<div class="pitch-row">\n'
        for p in row_info["players"]:
            card_state_cls = "state-ft" if show_proj_pill else ("state-live" if p["state"] == "LIVE" else ("state-ytp" if p["state"] == "YTP" else "state-ft"))
            pulse_html = '<div class="state-pulse"></div>' if p["state"] == "LIVE" else ''
            sub_tag = ''
            if p["sub_action"] == "Subbed On":
                sub_tag = '<span class="sub-tag-on">ON</span>'
            elif p["sub_action"] == "Subbed Off":
                sub_tag = '<span class="sub-tag-off">OFF</span>'

            event_icon = f'<span style="margin-left:2px;">{p["events_str"]}</span>' if p["events_str"] else ''
            opp_html = f'<div class="player-opp-pill">{p["opp"]}</div>' if p.get("opp") else ''

            pitch_html += f"""
                <div class="player-card {card_state_cls}" onclick="showPlayerStats('{p['name']}')">
                    <div class="club-token" style="background-color: {p['club_bg']}; color: {p['club_text']}; border-color: {p['club_border']};">
                        {p['club']}
                        {p['status_flag']}
                        {pulse_html}
                        {sub_tag}
                    </div>
                    <div class="player-name-pill">{p['name']}</div>
                    {opp_html}
                    <div class="player-pts-pill">{p['pill_text']}{event_icon}</div>
                </div>
            """
        pitch_html += '</div>\n'

    pitch_html += f"""
        <!-- Modal Overlay -->
        <div class="modal-overlay" id="stat-modal" onclick="closeModalOnBg(event)">
            <div class="modal-card" id="modal-card">
                <span class="modal-close" onclick="closeModal()">✕</span>
                <div class="modal-title" id="m-name">Player Name</div>
                <div class="modal-meta" id="m-meta">Pos • Club • State</div>
                <div class="modal-score-banner">
                    <div>
                        <span style="font-size:0.75rem; color:#94a3b8; font-weight:700; text-transform:uppercase;">{left_banner_label}</span>
                        <div class="modal-pts-big" id="m-pts">0 PTS</div>
                    </div>
                    <div style="text-align:right;">
                        <span style="font-size:0.75rem; color:#94a3b8; font-weight:700;">GW PROJECTION</span>
                        <div style="font-size:1.15rem; font-weight:800; color:#cbd5e1;" id="m-proj">0.0</div>
                    </div>
                </div>
                <div class="stat-grid" id="m-grid"></div>
                <div id="m-sub-status" style="font-size:0.78rem; color:#94a3b8; text-align:center; font-weight:600; margin-top:6px;"></div>
            </div>
        </div>
    </div>

    <!-- Subs Tray (Supports Multi-Row Dugout) -->
    <div class="dugout-container">
        <div class="dugout-header">
            <span>🛡️ Subs</span>
        </div>
    """

    for d_row in dugout_rows_split:
        pitch_html += '<div class="dugout-row">\n'
        for bp in d_row:
            card_state_cls = "state-ft" if show_proj_pill else ("state-live" if bp["state"] == "LIVE" else ("state-ytp" if bp["state"] == "YTP" else "state-ft"))
            pulse_html = '<div class="state-pulse"></div>' if bp["state"] == "LIVE" else ''
            sub_tag = ''
            if bp["sub_action"] == "Subbed On":
                sub_tag = '<span class="sub-tag-on">ON</span>'
            elif bp["sub_action"] == "Subbed Off":
                sub_tag = '<span class="sub-tag-off">OFF</span>'

            event_icon = f'<span style="margin-left:2px;">{bp["events_str"]}</span>' if bp["events_str"] else ''
            opp_html = f'<div class="player-opp-pill">{bp["opp"]}</div>' if bp.get("opp") else ''

            pitch_html += f"""
                <div class="player-card {card_state_cls}" onclick="showPlayerStats('{bp['name']}')">
                    <div class="club-token" style="background-color: {bp['club_bg']}; color: {bp['club_text']}; border-color: {bp['club_border']};">
                        {bp['club']}
                        {bp['status_flag']}
                        {pulse_html}
                        {sub_tag}
                    </div>
                    <div class="player-name-pill">{bp['name']}</div>
                    {opp_html}
                    <div class="player-pts-pill">{bp['pill_text']}{event_icon}</div>
                </div>
            """
        pitch_html += '</div>\n'

    pitch_html += f"""
    </div>

    <script>
        const playersData = {players_json};

        function showPlayerStats(name) {{
            const p = playersData.find(item => item.name === name);
            if (!p) return;

            const oppText = p.opp ? ' • vs ' + p.opp : '';
            document.getElementById('m-name').textContent = p.name;
            document.getElementById('m-meta').textContent = p.pos + ' • ' + p.club + oppText + ' (' + p.state + ')';
            document.getElementById('m-pts').textContent = p.pts + ' PTS';
            document.getElementById('m-proj').textContent = p.proj + ' pts';

            let gridHtml = '';
            gridHtml += '<div class="stat-item"><span class="stat-label">Minutes:</span><span class="stat-val">' + p.mins + "'" + '</span></div>';
            gridHtml += '<div class="stat-item"><span class="stat-label">Goals ⚽:</span><span class="stat-val">' + p.g + '</span></div>';
            gridHtml += '<div class="stat-item"><span class="stat-label">Assists 🎯:</span><span class="stat-val">' + p.a + '</span></div>';
            gridHtml += '<div class="stat-item"><span class="stat-label">Bonus ⭐:</span><span class="stat-val">' + p.bonus + '</span></div>';

            if (p.yc > 0 || p.rc > 0) {{
                let cardDetail = [];
                if (p.yc > 0) cardDetail.push(p.yc + ' 🟨 (-' + p.yc + ' pt)');
                if (p.rc > 0) cardDetail.push(p.rc + ' 🟥 (-' + (p.rc * 3) + ' pts)');
                gridHtml += '<div class="stat-item" style="grid-column: span 2; background: #270606; border-color: #ef4444;"><span class="stat-label" style="color:#ef4444; font-weight:700;">Cards:</span><span class="stat-val" style="color:#ef4444;">' + cardDetail.join(', ') + '</span></div>';
            }} else {{
                gridHtml += '<div class="stat-item"><span class="stat-label">Yellow Cards 🟨:</span><span class="stat-val">0</span></div>';
                gridHtml += '<div class="stat-item"><span class="stat-label">Red Cards 🟥:</span><span class="stat-val">0</span></div>';
            }}

            if (p.pos === 'GKP' || p.pos === 'DEF' || p.pos === 'MID') {{
                gridHtml += '<div class="stat-item"><span class="stat-label">Clean Sheet 🛡️:</span><span class="stat-val">' + p.cs + '</span></div>';
                gridHtml += '<div class="stat-item"><span class="stat-label">Conceded 🛑:</span><span class="stat-val">' + p.gc + '</span></div>';
            }}

            if (p.pos === 'GKP') {{
                gridHtml += '<div class="stat-item"><span class="stat-label">Saves 🧤:</span><span class="stat-val">' + p.saves + '</span></div>';
                if (p.p_saved > 0) {{
                    gridHtml += '<div class="stat-item" style="background:#052210; border-color:#22c55e;"><span class="stat-label" style="color:#22c55e;">Pens Saved 🧤:</span><span class="stat-val" style="color:#22c55e;">' + p.p_saved + ' (+5 pts)</span></div>';
                }}
            }}

            if (p.defcon_hit) {{
                gridHtml += '<div class="stat-item stat-defcon-hit"><span class="stat-label" style="color:#22c55e;">DEFCON Threshold:</span><span class="stat-val" style="color:#22c55e;">ACHIEVED (+2 pts)</span></div>';
            }}

            if (p.p_missed > 0) {{
                gridHtml += '<div class="stat-item stat-penalty-miss"><span class="stat-label" style="color:#ef4444;">Penalty Missed ❌:</span><span class="stat-val" style="color:#ef4444;">' + p.p_missed + ' (-2 pts)</span></div>';
            }}

            document.getElementById('m-grid').innerHTML = gridHtml;

            const subEl = document.getElementById('m-sub-status');
            if (p.sub_action === 'Subbed On') {{
                subEl.innerHTML = '<span style="color:#22c55e;">▲ Active: Auto Subbed On into Lineup</span>';
            }} else if (p.sub_action === 'Subbed Off') {{
                subEl.innerHTML = '<span style="color:#ef4444;">▼ Replaced: Subbed Off (DNP)</span>';
            }} else if (p.is_bench) {{
                subEl.textContent = 'Subs';
            }} else {{
                subEl.textContent = 'Starting XI';
            }}

            document.getElementById('stat-modal').style.display = 'flex';
        }}

        function closeModal() {{
            document.getElementById('stat-modal').style.display = 'none';
        }}

        function closeModalOnBg(e) {{
            if (e.target.id === 'stat-modal') {{
                closeModal();
            }}
        }}
    </script>
    </body>
    </html>
    """

    components.html(pitch_html, height = dynamic_container_height)
def render_lineup_container(alias, starters_df, bench_df, bp_pts, opt_pts, accent_color, is_large, score = None):
    score_tag = f" ({score} pts)" if score is not None else ""
    st.markdown(f"### {alias}{score_tag}")
    st.caption(f"Bench Left: {bp_pts} pts | Optimum Score: {opt_pts} pts")

    p_tab_pitch, p_tab_table = st.tabs(["⚽ Pitch View", "📋 Table View"])

    with p_tab_pitch:
        render_pitch_component(alias, starters_df, bench_df, accent_color, is_large, show_proj_pill = False)

    with p_tab_table:
        st.markdown("""
        <style>
            div[data-baseweb="tab-panel"] table {
                font-size: 0.82rem !important;
            }
            div[data-baseweb="tab-panel"] th, div[data-baseweb="tab-panel"] td {
                padding: 4px 6px !important;
                text-align: center !important;
                white-space: nowrap !important;
            }
            div[data-baseweb="tab-panel"] th:first-child, div[data-baseweb="tab-panel"] td:first-child {
                text-align: left !important;
                font-weight: 700 !important;
            }
        </style>
        """, unsafe_allow_html = True)

        def build_clean_table(df):
            if df is None or df.empty:
                return pd.DataFrame()
            rows = []
            for _, r in df.iterrows():
                rows.append({
                    "Player": str(r.get("Player", "")),
                    "Pos": str(r.get("Pos", "")),
                    "Opp": str(r.get("Opp", "-")).replace(" (H)", " [H]").replace(" (A)", " [A]"),
                    "Mins": int(r.get("Mins", 0)),
                    "G": int(r.get("G", 0)),
                    "A": int(r.get("A", 0)),
                    "CS": int(r.get("CS", 0)) if r.get("Pos") in ["GKP", "DEF", "MID"] else "-",
                    "Bonus": int(r.get("Bonus", 0)),
                    "Pts": int(r.get("Pts", 0))
                })
            return pd.DataFrame(rows)

        if starters_df is not None and not starters_df.empty:
            st.markdown(f"<p style='font-size:0.82rem; font-weight:800; color:{accent_color}; text-transform:uppercase; margin-bottom:2px;'>Starting XI</p>", unsafe_allow_html = True)
            s_clean = build_clean_table(starters_df)
            st.table(s_clean.set_index("Player"))

            if bench_df is not None and not bench_df.empty:
                b_work = bench_df.copy()
                b_work["pos_order"] = b_work["Pos"].map(POS_ORDER).fillna(99)
                b_work = b_work.sort_values(by = "pos_order", ascending = True).drop(columns = ["pos_order"])
                st.markdown("<p style='font-size:0.82rem; font-weight:800; color:#94a3b8; text-transform:uppercase; margin:6px 0 2px 0;'>Dugout Substitutes</p>", unsafe_allow_html = True)
                b_clean = build_clean_table(b_work)
                st.table(b_clean.set_index("Player"))
        else:
            st.info("Lineup selections not yet available.")
def extract_defcon_achieved_flag(elem_stats, elem_explain, pos_type):
    if not isinstance(elem_stats, dict):
        return False
    cbi = elem_stats.get("clearances_blocks_interceptions", 0) or elem_stats.get("cbi", 0)
    tackles = elem_stats.get("tackles", 0)
    recoveries = elem_stats.get("recoveries", 0) or elem_stats.get("ball_recoveries", 0)
    dc_direct = elem_stats.get("defensive_contributions", 0) or elem_stats.get("defcon", 0) or elem_stats.get("cbit", 0)
    
    if dc_direct > 0:
        calc_val = dc_direct
    else:
        base_cbit = cbi + tackles
        calc_val = base_cbit + recoveries if pos_type in [3, 4] else base_cbit

    is_hit = False
    explain_val = 0
    stat_items = []
    if isinstance(elem_explain, list):
        for item in elem_explain:
            if isinstance(item, dict):
                if "stats" in item and isinstance(item["stats"], list):
                    stat_items.extend(item["stats"])
                else:
                    stat_items.append(item)
            elif isinstance(item, list):
                for sub in item:
                    if isinstance(sub, dict):
                        stat_items.append(sub)

    for s_item in stat_items:
        if isinstance(s_item, dict):
            ident = str(s_item.get("identifier", "")).lower()
            pts = s_item.get("points", 0)
            val = s_item.get("value", 0)
            if ident in ["defensive_contributions", "defcon", "cbit", "cbi"] and (pts >= 2 or val >= 10):
                is_hit = True
                explain_val = max(explain_val, val)

    final_val = max(calc_val, explain_val)
    threshold = 10 if pos_type == 2 else 12
    return (pos_type in [2, 3, 4] and final_val >= threshold) or is_hit

def evaluate_lineup(picks_list, live_elements, element_lookup, club_minutes, pos_map, team_map, current_gw = 1, all_fixtures_list = None):
    if not picks_list:
        return pd.DataFrame(), pd.DataFrame(), 0, 0.0, 0, 0, 0, 0
        
    raw_players = []
    for p in picks_list.get("picks", []):
        elem_id = p["element"]
        raw_elem = element_lookup.get(elem_id, {})
        e_data = live_elements.get(str(elem_id), {})
        stats = e_data.get("stats", {}) if isinstance(e_data, dict) else {}
        explain_raw = e_data.get("explain", []) if isinstance(e_data, dict) else []
        
        pos_type = raw_elem.get("element_type", 1)
        pos_str = pos_map.get(pos_type, "")
        club_id = raw_elem.get("team")
        
        opp_str = "-"
        if all_fixtures_list and club_id:
            team_fixes = [
                f for f in all_fixtures_list
                if f.get("event") == current_gw and (f.get("team_h") == club_id or f.get("team_a") == club_id)
            ]
            if team_fixes:
                opp_labels = []
                for tf in team_fixes:
                    if tf.get("team_h") == club_id:
                        opp_short = team_map.get(tf.get("team_a"), "OPP")
                        opp_labels.append(f"{opp_short} (H)")
                    else:
                        opp_short = team_map.get(tf.get("team_h"), "OPP")
                        opp_labels.append(f"{opp_short} (A)")
                opp_str = ", ".join(opp_labels)
            else:
                opp_str = "Blank"

        mins = stats.get("minutes", 0)
        pts = stats.get("total_points", 0)
        team_mins = club_minutes.get(club_id, 0)
        
        avail = get_availability_multiplier(raw_elem)
        
        form_val = float(raw_elem.get("form") or 0.0)
        ppg_val = float(raw_elem.get("points_per_game") or 2.0)
        base_exp = ((ppg_val * 0.6) + (form_val * 0.4)) * avail
        
        season_mins = float(raw_elem.get("minutes") or 0.0)
        if current_gw > 3:
            expected_min_ratio = season_mins / max(1.0, float(current_gw * 60))
            if expected_min_ratio < 0.6:
                base_exp = base_exp * 0.8
                
        if base_exp <= 0 and avail > 0:
            base_exp = 2.0
            
        fdr_mult = get_fdr_multiplier(club_id, current_gw, all_fixtures_list)
        base_exp = base_exp * fdr_mult

        if team_mins >= 800:
            if mins > 0:
                state = "FT"
                proj = float(pts)
            else:
                state = "DNP"
                proj = 0.0
        elif team_mins > 0:
            state = "LIVE"
            match_minute = 45
            if all_fixtures_list:
                for fix in all_fixtures_list:
                    if fix.get("event") == current_gw and (fix.get("team_h") == club_id or fix.get("team_a") == club_id):
                        if fix.get("started", False):
                            match_minute = fix.get("minutes", 45)
                            break
            
            remaining_fraction = max(0.0, (90.0 - float(match_minute)) / 90.0)
            if mins > 0:
                return_expect = max(0.0, base_exp - 2.0)
                upcoming_app_pts = 1.0 if match_minute < 60 else 0.0
                proj = round(float(pts) + upcoming_app_pts + (return_expect * remaining_fraction), 1)
            else:
                proj = round(base_exp * 0.25 * remaining_fraction, 1)
        else:
            state = "YTP"
            proj = round(base_exp, 1)

        defcon_achieved = extract_defcon_achieved_flag(stats, explain_raw, pos_type)
            
        raw_players.append({
            "id": elem_id,
            "Player": raw_elem.get("web_name", "Unknown"),
            "pos_num": pos_type,
            "Pos": pos_str,
            "Club": team_map.get(club_id, ""),
            "Opp": opp_str,
            "club_id": club_id,
            "status": raw_elem.get("status", "a"),
            "chance_of_playing_next_round": raw_elem.get("chance_of_playing_next_round"),
            "State": state,
            "Mins": mins,
            "Pts": pts,
            "Proj": proj,
            "G": stats.get("goals_scored", 0),
            "A": stats.get("assists", 0),
            "CS": stats.get("clean_sheets", 0),
            "GC": stats.get("goals_conceded", 0),
            "Bonus": stats.get("bonus", 0),
            "YC": stats.get("yellow_cards", 0),
            "RC": stats.get("red_cards", 0),
            "Saves": stats.get("saves", 0),
            "Penalties_Saved": stats.get("penalties_saved", 0),
            "Penalties_Missed": stats.get("penalties_missed", 0),
            "DEFCON_Achieved": defcon_achieved,
            "pick_pos": p.get("position", 99),
            "is_starter": p.get("position", 99) <= 11,
            "sub_action": ""
        })
        
    starters = [r for r in raw_players if r["is_starter"]]
    bench = [r for r in raw_players if not r["is_starter"]]
    bench = sorted(bench, key = lambda x: x["pick_pos"])
    
    used_bench_ids = set()
    
    gk_starter = next((s for s in starters if s["Pos"] == "GKP"), None)
    if gk_starter and gk_starter["State"] == "DNP":
        gk_bench = next((b for b in bench if b["Pos"] == "GKP" and b["State"] != "DNP"), None)
        if gk_bench:
            gk_starter["sub_action"] = "Subbed Off"
            gk_bench["sub_action"] = "Subbed On"
            used_bench_ids.add(gk_bench["id"])
            
    dnp_outfield = [s for s in starters if s["Pos"] != "GKP" and s["State"] == "DNP"]
    for dnp_s in dnp_outfield:
        for b_cand in bench:
            if b_cand["Pos"] == "GKP" or b_cand["id"] in used_bench_ids or b_cand["State"] == "DNP":
                continue
                
            cur_formation = [s["Pos"] for s in starters if s["sub_action"] != "Subbed Off" and s["id"] != dnp_s["id"]]
            cur_formation.append(b_cand["Pos"])
            if cur_formation.count("DEF") >= 3 and cur_formation.count("MID") >= 2 and cur_formation.count("FWD") >= 1:
                dnp_s["sub_action"] = "Subbed Off"
                b_cand["sub_action"] = "Subbed On"
                used_bench_ids.add(b_cand["id"])
                break

    active_lineup = [s for s in starters if s["sub_action"] != "Subbed Off"] + [b for b in bench if b["sub_action"] == "Subbed On"]
    live_score = sum(int(p["Pts"]) for p in active_lineup)
    proj_score = sum(float(p["Proj"]) for p in active_lineup)
    
    in_play = sum(1 for p in active_lineup if p["State"] == "LIVE")
    yet_to_play = sum(1 for p in active_lineup if p["State"] == "YTP")
    
    bench_left_pts = 0
    if bench:
        for b in bench:
            if b.get("sub_action") != "Subbed On":
                bench_left_pts += int(b.get("Pts", 0))

    all_players_df = pd.DataFrame(raw_players)
    optimum_score = calculate_optimum_score(all_players_df)
    
    starters_df = pd.DataFrame(starters).sort_values(by = ["pos_num", "Pts"], ascending = [True, False]) if starters else pd.DataFrame()
    bench_df = pd.DataFrame(bench).sort_values(by = "pick_pos", ascending = True) if bench else pd.DataFrame()
    
    return starters_df, bench_df, live_score, round(proj_score, 1), in_play, yet_to_play, bench_left_pts, optimum_score

@st.cache_data(ttl = 600)
def load_cup_matches():
    valid_extensions = [".ods", ".xlsx", ".xls", ".csv"]
    target_file = None
    potential_folders = [
        base_dir / "Assets",
        base_dir / "assets",
        Path("Assets"),
        Path("assets"),
        base_dir
    ]
    for folder in potential_folders:
        if folder.exists() and folder.is_dir():
            for f in folder.iterdir():
                if f.is_file() and f.suffix.lower() in valid_extensions and "cupmatch" in f.name.lower().replace(" ", "").replace("_", ""):
                    target_file = f
                    break
        if target_file:
            break

    if not target_file or not target_file.exists():
        return None

    ext = target_file.suffix.lower()
    try:
        if ext == ".csv":
            df = pd.read_csv(target_file)
        elif ext == ".ods":
            df = pd.read_excel(target_file, engine = "odf")
        else:
            df = pd.read_excel(target_file, engine = "openpyxl")
        
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception:
        return None

def render_pdf(filename, title):
    potential_paths = [
        newsletters_folder / filename,
        base_dir / "Newsletters" / filename,
        base_dir / "newsletters" / filename,
        Path("Newsletters") / filename,
        Path("newsletters") / filename,
        assets_folder / "Newsletters" / filename,
        assets_folder / filename,
        base_dir / filename
    ]
    pdf_path = next((p for p in potential_paths if p.exists() and p.is_file()), None)

    if not pdf_path:
        st.warning(f"File '{filename}' not found in Newsletters or Assets folder.")
        return
    try:
        doc = pdfium.PdfDocument(pdf_path)
        for i, page in enumerate(doc):
            image = page.render(scale = 2).to_pil()
            st.image(image, use_container_width = True)
    except Exception as e:
        st.error(f"Error rendering {title}: {str(e)}")

@st.cache_data(ttl = 600)
def load_power_rankings_data():
    valid_extensions = [".ods", ".xlsx", ".xls", ".csv"]
    target_file = None
    for folder in [assets_folder, base_dir]:
        if folder.exists() and folder.is_dir():
            for f in folder.iterdir():
                if f.is_file() and f.suffix.lower() in valid_extensions and "power" in f.name.lower():
                    target_file = f
                    break
        if target_file:
            break
    if not target_file:
        return None, None, None
    try:
        raw_bytes = target_file.read_bytes()
        ext = target_file.suffix.lower()
        if ext == ".csv":
            df = pd.read_csv(target_file)
            return target_file.name, {target_file.stem: df}, raw_bytes
        elif ext == ".ods":
            sheets = pd.read_excel(target_file, sheet_name = None, engine = "odf")
            return target_file.name, sheets, raw_bytes
        else:
            sheets = pd.read_excel(target_file, sheet_name = None, engine = "openpyxl")
            return target_file.name, sheets, raw_bytes
    except Exception as e:
        return target_file.name, e, None

@st.cache_data(ttl = 600)
def load_records_data():
    valid_extensions = [".ods", ".xlsx", ".xls", ".csv"]
    target_file = None
    for folder in [assets_folder, base_dir]:
        if folder.exists() and folder.is_dir():
            for f in folder.iterdir():
                if f.is_file() and f.suffix.lower() in valid_extensions and "record" in f.name.lower():
                    target_file = f
                    break
        if target_file:
            break
    if not target_file:
        return None, None, None
    try:
        raw_bytes = target_file.read_bytes()
        ext = target_file.suffix.lower()
        if ext == ".csv":
            df = pd.read_csv(target_file)
            return target_file.name, {target_file.stem: df}, raw_bytes
        elif ext == ".ods":
            sheets = pd.read_excel(target_file, sheet_name = None, engine = "odf")
            return target_file.name, sheets, raw_bytes
        else:
            sheets = pd.read_excel(target_file, sheet_name = None, engine = "openpyxl")
            return target_file.name, sheets, raw_bytes
    except Exception as e:
        return target_file.name, e, None

@st.cache_data(ttl = 3600)
def fetch_fpl_static():
    url = "https://draft.premierleague.com/api/bootstrap" + chr(45) + "static"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    return response.json()

@st.cache_data(ttl = 120)
def fetch_league_data(league_id):
    if not league_id:
        return None, None
    details_url = "https://draft.premierleague.com/api/league/" + str(league_id) + "/details"
    status_url = "https://draft.premierleague.com/api/league/" + str(league_id) + "/element" + chr(45) + "status"
    
    det_resp = requests.get(details_url)
    stat_resp = requests.get(status_url)
    
    if det_resp.status_code != 200 or stat_resp.status_code != 200:
        return None, None
        
    return det_resp.json(), stat_resp.json()

@st.cache_data(ttl = 300)
def get_all_32_teams_registry():
    registry = {}
    for l_key, l_id in LEAGUE_PRESETS.items():
        details, _ = fetch_league_data(l_id)
        if details:
            entries = details.get("league_entries", [])
            for e in entries:
                alias = get_manager_alias(e.get("player_first_name", ""), e.get("player_last_name", ""))
                info = {
                    "entry_id": e.get("entry_id"),
                    "league_entry_id": e.get("id"),
                    "league_id": l_id,
                    "league_key": l_key,
                    "team_name": e.get("entry_name", "Team"),
                    "manager_name": f"{e.get('player_first_name', '')} {e.get('player_last_name', '')}".strip(),
                    "alias": alias
                }
                registry[alias.lower()] = info
                registry[e.get("entry_name", "").strip().lower()] = info
    return registry

# ==============================================================================
# CBWCBW (COULD BE WORSE, COULD BE WILL) CALCULATION ENGINE
# ==============================================================================
@st.cache_data(ttl = 60)
def calculate_cbwcbw_tracker(gw_num):
    teams_reg = get_all_32_teams_registry()
    static_data = fetch_fpl_static()
    all_fixtures = fetch_all_epl_fixtures()
    live_data = fetch_live_event(gw_num)
    
    if not static_data or not teams_reg:
        return 32, []
        
    pos_map = {item["id"]: item["singular_name_short"] for item in static_data.get("element_types", [])}
    team_map = {item["id"]: item["short_name"] for item in static_data.get("teams", [])}
    element_lookup = {item["id"]: item for item in static_data.get("elements", [])}
    live_elements = live_data.get("elements", {}) if live_data else {}
    
    club_minutes = {}
    for elem_str_id, e_info in live_elements.items():
        try:
            elem_int_id = int(elem_str_id)
        except (ValueError, TypeError):
            continue
        elem_obj = element_lookup.get(elem_int_id, {})
        c_id = elem_obj.get("team")
        if c_id:
            m_val = e_info.get("stats", {}).get("minutes", 0)
            club_minutes[c_id] = club_minutes.get(c_id, 0) + m_val
            
    unique_teams = {}
    for alias_key, info in teams_reg.items():
        if info.get("entry_id") and info.get("alias") not in unique_teams:
            unique_teams[info.get("alias")] = info
            
    at_risk_list = []
    
    for alias, info in unique_teams.items():
        picks = fetch_entry_event(info.get("entry_id"), gw_num)
        starters_df, bench_df, _, _, in_play, ytp, _, _ = evaluate_lineup(
            picks, live_elements, element_lookup, club_minutes, pos_map, team_map, gw_num, all_fixtures
        )
        
        active_starters = starters_df[starters_df["sub_action"] != "Subbed Off"] if not starters_df.empty else pd.DataFrame()
        active_bench = bench_df[bench_df["sub_action"] == "Subbed On"] if not bench_df.empty else pd.DataFrame()
        final_xi = pd.concat([active_starters, active_bench], ignore_index = True)
        
        has_positive_return = False
        if not final_xi.empty:
            for _, p in final_xi.iterrows():
                g = int(p.get("G", 0))
                a = int(p.get("A", 0))
                bonus = int(p.get("Bonus", 0))
                saves = int(p.get("Saves", 0))
                p_saved = int(p.get("Penalties_Saved", 0))
                defcon = bool(p.get("DEFCON_Achieved", False))
                cs = int(p.get("CS", 0))
                pos = str(p.get("Pos", "")).upper()
                
                if (g > 0 or a > 0 or bonus > 0 or p_saved > 0 or defcon or 
                    (cs > 0 and pos in ["GKP", "DEF", "MID"]) or 
                    (saves >= 3 and pos == "GKP")):
                    has_positive_return = True
                    break

        has_positive_return = False
        if not final_xi.empty:
            for _, p in final_xi.iterrows():
                g = int(p.get("G", 0))
                a = int(p.get("A", 0))
                bonus = int(p.get("Bonus", 0))
                saves = int(p.get("Saves", 0))
                p_saved = int(p.get("Penalties_Saved", 0))
                defcon = bool(p.get("DEFCON_Achieved", False))
                cs = int(p.get("CS", 0))
                pos = str(p.get("Pos", "")).upper()
                
                if (g > 0 or a > 0 or bonus > 0 or p_saved > 0 or defcon or 
                    (cs > 0 and pos in ["GKP", "DEF", "MID"]) or 
                    (saves >= 3 and pos == "GKP")):
                    has_positive_return = True
                    break

        # Position-strict bench check: only count subs that are ACTUALLY eligible to come on
        if not has_positive_return and not bench_df.empty:
            gk_starter = starters_df[starters_df["Pos"] == "GKP"]
            gk_starter_dnp = (
                not gk_starter.empty and 
                (gk_starter.iloc[0].get("State") == "DNP" or gk_starter.iloc[0].get("sub_action") == "Subbed Off")
            )

            for _, bp in bench_df.iterrows():
                if bp.get("State") not in ["FT", "LIVE"]:
                    continue

                b_pos = str(bp.get("Pos", "")).upper()

                # A bench GK can ONLY come on if the starting GK did not play
                if b_pos == "GKP" and not gk_starter_dnp:
                    continue

                # An outfield sub can only count if they were actually subbed on into the lineup
                if b_pos != "GKP" and bp.get("sub_action") != "Subbed On":
                    continue

                bg = int(bp.get("G", 0))
                ba = int(bp.get("A", 0))
                b_bonus = int(bp.get("Bonus", 0))
                b_saves = int(bp.get("Saves", 0))
                b_psaved = int(bp.get("Penalties_Saved", 0))
                b_defcon = bool(bp.get("DEFCON_Achieved", False))
                b_cs = int(bp.get("CS", 0))

                if (bg > 0 or ba > 0 or b_bonus > 0 or b_psaved > 0 or b_defcon or 
                    (b_cs > 0 and b_pos in ["GKP", "DEF", "MID"]) or 
                    (b_saves >= 3 and b_pos == "GKP")):
                    has_positive_return = True
                    break

        if not has_positive_return:
            rem_players = in_play + ytp
            at_risk_list.append({
                "alias": alias,
                "div": str(info.get("league_key", "")).split(" ")[0],
                "rem": rem_players,
                "is_locked": (rem_players == 0 and not final_xi.empty and any(int(p.get("Mins", 0)) > 0 for _, p in final_xi.iterrows()))
            })
            
    at_risk_list = sorted(at_risk_list, key = lambda x: (not x["is_locked"], x["rem"], x["alias"].lower()))
    return len(at_risk_list), at_risk_list
@st.cache_data(ttl = 45)
def fetch_entry_event(entry_id, event):
    url = "https://draft.premierleague.com/api/entry/" + str(entry_id) + "/event/" + str(event)
    resp = requests.get(url)
    if resp.status_code != 200:
        return None
    return resp.json()

@st.cache_data(ttl = 45)
def fetch_live_event(event):
    url = "https://draft.premierleague.com/api/event/" + str(event) + "/live"
    resp = requests.get(url)
    if resp.status_code != 200:
        return None
    return resp.json()
@st.cache_data(ttl = 60)
def fetch_epl_fixtures(event):
    url = "https://fantasy.premierleague.com/api/fixtures/?event=" + str(event)
    resp = requests.get(url)
    if resp.status_code != 200:
        return []
    return resp.json()

@st.cache_data(ttl = 60)
def fetch_all_epl_fixtures():
    url = "https://fantasy.premierleague.com/api/fixtures/"
    resp = requests.get(url)
    if resp.status_code != 200:
        return []
    return resp.json()
PULSE_HEADERS = {
    "Origin": "https://www.premierleague.com",
    "Referer": "https://www.premierleague.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "account": "premierleague"
}

CLUB_SEARCH_KEYWORDS = {
    "ARS": "arsenal", "AVL": "aston villa", "BHA": "brighton", "BOU": "bournemouth",
    "BRE": "brentford", "CHE": "chelsea", "COV": "coventry", "CRY": "crystal palace",
    "EVE": "everton", "FUL": "fulham", "HUL": "hull", "IPS": "ipswich",
    "LEE": "leeds", "LEI": "leicester", "LIV": "liverpool", "MCI": "manchester city",
    "MUN": "manchester united", "NEW": "newcastle", "NFO": "nottingham",
    "SOU": "southampton", "SUN": "sunderland", "TOT": "tottenham",
    "WHU": "west ham", "WOL": "wolverhampton"
}

def _team_matches_code(short_code, team_obj):
    if not short_code or not isinstance(team_obj, dict):
        return False
    code_up = str(short_code).strip().upper()
    kw = CLUB_SEARCH_KEYWORDS.get(code_up, code_up.lower())

    club_obj = team_obj.get("club", {}) if isinstance(team_obj.get("club"), dict) else {}
    abbr = str(club_obj.get("abbr") or team_obj.get("abbreviation") or "").strip().upper()
    if abbr and abbr == code_up:
        return True

    combined_names = " ".join([
        str(team_obj.get("name") or ""),
        str(team_obj.get("shortName") or ""),
        str(team_obj.get("displayName") or ""),
        str(team_obj.get("shortDisplayName") or ""),
        str(club_obj.get("name") or ""),
        str(club_obj.get("shortName") or "")
    ]).lower()

    return kw in combined_names

@st.cache_data(ttl = 86400)
def get_pulse_active_season_id():
    try:
        s_url = "https://footballapi.pulselive.com/football/competitions/1/compseasons?page=0&pageSize=100"
        s_resp = requests.get(s_url, headers = PULSE_HEADERS, timeout = 4)
        if s_resp.status_code == 200:
            seasons = s_resp.json().get("content", [])
            for s in seasons:
                if "2026/27" in str(s.get("label", "")):
                    return int(float(s.get("id")))
            if seasons:
                return int(max(seasons, key = lambda x: float(x.get("id", 0)))["id"])
    except Exception:
        pass
    return None

@st.cache_data(ttl = 60)
def get_pulse_active_fixtures_list(event_num = None):
    """Fetches all active, live and upcoming fixtures in one batched request for the entire gameweek."""
    season_id = get_pulse_active_season_id()
    season_param = f"&compSeasons={season_id}" if season_id else ""
    gw_page = max(0, (int(event_num) - 1) // 4) if event_num else 1

    search_urls = [
        f"https://footballapi.pulselive.com/football/fixtures?comps=1{season_param}&statuses=U,L&sort=asc&page=0&pageSize=40",
        f"https://footballapi.pulselive.com/football/fixtures?comps=1{season_param}&sort=asc&page={gw_page}&pageSize=40",
        f"https://footballapi.pulselive.com/football/fixtures?comps=1{season_param}&statuses=C&sort=desc&page=0&pageSize=40"
    ]

    all_fixes = []
    seen_ids = set()
    for url in search_urls:
        try:
            r = requests.get(url, headers = PULSE_HEADERS, timeout = 4)
            if r.status_code == 200:
                for fix in r.json().get("content", []):
                    f_id = fix.get("id")
                    if f_id and f_id not in seen_ids:
                        seen_ids.add(f_id)
                        all_fixes.append(fix)
        except Exception:
            continue
    return all_fixes

def get_pulse_fixture_id(home_short, away_short, event_num = None):
    fixes = get_pulse_active_fixtures_list(event_num)
    for fix in fixes:
        teams = fix.get("teams", [])
        if len(teams) == 2:
            t0 = teams[0].get("team", {})
            t1 = teams[1].get("team", {})
            if _team_matches_code(home_short, t0) and _team_matches_code(away_short, t1):
                return int(float(fix.get("id")))
    return None

@st.cache_data(ttl = 60)
def fetch_pulse_fixture_details(pulse_id):
    url = f"https://footballapi.pulselive.com/football/fixtures/{pulse_id}"
    try:
        resp = requests.get(url, headers = PULSE_HEADERS, timeout = 5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None

@st.cache_data(ttl = 60)
def get_espn_scoreboard():
    try:
        sb_url = "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard"
        sb_resp = requests.get(sb_url, timeout = 4)
        if sb_resp.status_code == 200:
            return sb_resp.json().get("events", [])
    except Exception:
        pass
    return []

@st.cache_data(ttl = 60)
def fetch_espn_fixture_summary(event_id):
    sum_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/summary?event={event_id}"
    try:
        sum_resp = requests.get(sum_url, timeout = 4)
        if sum_resp.status_code == 200:
            return sum_resp.json()
    except Exception:
        pass
    return None

def _fetch_espn_lineup_backup(home_short, away_short):
    pos_order_map = {"GKP": 1, "DEF": 2, "MID": 3, "FWD": 4}
    events = get_espn_scoreboard()
    if not events:
        return None

    target_event_id = None
    for ev in events:
        comps = ev.get("competitions", [])
        if comps:
            competitors = comps[0].get("competitors", [])
            home_comp = next((c for c in competitors if c.get("homeAway") == "home"), {})
            away_comp = next((c for c in competitors if c.get("homeAway") == "away"), {})
            if _team_matches_code(home_short, home_comp.get("team", {})) and _team_matches_code(away_short, away_comp.get("team", {})):
                target_event_id = ev.get("id")
                break

    if not target_event_id:
        return None

    sum_data = fetch_espn_fixture_summary(target_event_id)
    if not sum_data:
        return None

    rosters = sum_data.get("rosters", [])
    if len(rosters) < 2:
        return None

    def parse_espn_roster(r_obj):
        starters = []
        subs_used = []
        subs_unused = []
        for entry in r_obj.get("roster", []):
            ath = entry.get("athlete", {})
            name = ath.get("displayName") or ath.get("shortName") or "Unknown"
            raw_num = entry.get("jersey") or ath.get("jersey")
            num_str = f"#{raw_num} " if raw_num and str(raw_num).strip() not in ["-", "None", ""] else ""
            pos_raw = str(entry.get("position", {}).get("abbreviation", "M")).upper()
            clean_pos = "GKP" if "G" in pos_raw else ("DEF" if "D" in pos_raw else ("FWD" if "F" in pos_raw else "MID"))
            capt = " (C)" if entry.get("captain", False) else ""

            is_subbed_out = entry.get("subbedOut", False)
            is_subbed_in = entry.get("subbedIn", False)

            if entry.get("starter", False):
                sub_tag = " <span style='color:#f43f5e; font-weight:700;'>▼</span>" if is_subbed_out else ""
                starters.append((pos_order_map.get(clean_pos, 3), f"{num_str}**{name}**{capt} • *{clean_pos}*{sub_tag}"))
            else:
                if is_subbed_in:
                    subs_used.append(f"{num_str}**{name}** • *{clean_pos}* <span style='color:#22c55e; font-weight:800;'>▲</span>")
                else:
                    subs_unused.append(f"{num_str}{name} ({clean_pos})")

        sorted_starters = [s[1] for s in sorted(starters, key = lambda x: x[0])]
        return sorted_starters, subs_used, subs_unused

    home_r = next((r for r in rosters if r.get("homeAway") == "home"), rosters[0])
    away_r = next((r for r in rosters if r.get("homeAway") == "away"), rosters[1])

    h_s, h_u, h_un = parse_espn_roster(home_r)
    a_s, a_u, a_un = parse_espn_roster(away_r)

    if len(h_s) >= 11 or len(a_s) >= 11:
        return {
            "has_lineups": True,
            "home_starters": h_s, "home_subs_used": h_u, "home_subs_unused": h_un,
            "away_starters": a_s, "away_subs_used": a_u, "away_subs_unused": a_un
        }
    return None
@st.cache_data(ttl = 604800)
def fetch_finished_match_lineup(fpl_fixture_code, home_team_id, away_team_id, event_num, home_short, away_short):
    return fetch_premier_league_match_lineup(
        fpl_fixture_code = fpl_fixture_code,
        home_team_id = home_team_id,
        away_team_id = away_team_id,
        live_elements = None,
        element_lookup = None,
        match_minute = 90,
        event_num = event_num,
        home_short = home_short,
        away_short = away_short,
        kickoff_time = None,
        is_started = False,
        is_finished = True
    )
def build_epl_pitch_dfs(starters_list, subs_used_list, subs_unused_list, club_short):
    """Converts confirmed EPL match sheet player lists into DataFrames for render_pitch_component."""
    import re

    def parse_entry(entry_str, is_sub = False, sub_action = ""):
        clean = re.sub(r"<[^>]*>", "", str(entry_str)).strip()

        pos = "MID"
        left_part = clean
        if "•" in clean:
            parts = clean.split("•")
            left_part = parts[0].strip()
            raw_pos = parts[1].replace("*", "").strip() if len(parts) > 1 else "MID"
            pos = "GKP" if "GK" in raw_pos else ("DEF" if "DEF" in raw_pos else ("FWD" if "FWD" in raw_pos else "MID"))
        else:
            for cand in ["GKP", "DEF", "MID", "FWD", "GK"]:
                if f"({cand})" in clean or f"*{cand}*" in clean:
                    pos = "GKP" if "GK" in cand else cand
                    left_part = clean.replace(f"({cand})", "").replace(f"*{cand}*", "").strip()
                    break

        name = left_part
        if name.startswith("#"):
            parts_num = name.split(" ", 1)
            name = parts_num[1] if len(parts_num) > 1 else parts_num[0]
        name = name.replace("**", "").replace("(C)", "").strip()

        return {
            "Player": name,
            "Pos": pos,
            "Club": club_short,
            "Pts": 0,
            "Proj": 0.0,
            "Mins": 90 if not is_sub else 0,
            "State": "FT",
            "G": 0,
            "A": 0,
            "CS": 0,
            "GC": 0,
            "Bonus": 0,
            "Saves": 0,
            "Penalties_Saved": 0,
            "Penalties_Missed": 0,
            "YC": 0,
            "RC": 0,
            "DEFCON_Achieved": False,
            "sub_action": sub_action,
            "status": "a",
            "chance_of_playing_next_round": 100,
            "Opp": ""
        }

    starters_records = []
    for s in starters_list:
        sub_act = "Subbed Off" if "▼" in str(s) else ""
        starters_records.append(parse_entry(s, is_sub = False, sub_action = sub_act))

    bench_records = []
    for su in subs_used_list:
        bench_records.append(parse_entry(su, is_sub = True, sub_action = "Subbed On"))
    for sun in subs_unused_list:
        bench_records.append(parse_entry(sun, is_sub = True, sub_action = ""))

    starters_df = pd.DataFrame(starters_records) if starters_records else pd.DataFrame()
    bench_df = pd.DataFrame(bench_records) if bench_records else pd.DataFrame()
    return starters_df, bench_df
@st.cache_data(ttl = 45)
def fetch_premier_league_match_lineup(fpl_fixture_code, home_team_id = None, away_team_id = None, live_elements = None, element_lookup = None, match_minute = 90, event_num = None, home_short = None, away_short = None, kickoff_time = None, is_started = False, is_finished = False):
    pos_order_map = {"GK": 1, "GKP": 1, "G": 1, "DEF": 2, "D": 2, "MID": 3, "M": 3, "FWD": 4, "F": 4}
    if is_finished and live_elements is not None:
        cached_finished = fetch_finished_match_lineup(fpl_fixture_code, home_team_id, away_team_id, event_num, home_short, away_short)
        if cached_finished and cached_finished.get("has_lineups"):
            return cached_finished
    # Lineup window check: only query feeds if match has started, is finished, or is within 90m of KO
    is_within_window = False
    if is_started or is_finished:
        is_within_window = True
    elif kickoff_time:
        try:
            ko_dt = pd.to_datetime(kickoff_time)
            now_dt = pd.Timestamp.now(tz = ko_dt.tz) if ko_dt.tz else pd.Timestamp.utcnow()
            if (ko_dt - now_dt).total_seconds() <= 5400:  # <= 90 minutes
                is_within_window = True
        except Exception:
            is_within_window = True
    else:
        is_within_window = True

    if not is_within_window:
        return {"has_lineups": False}

    # 1. Primary Source: PulseLive
    pulse_id = get_pulse_fixture_id(home_short, away_short, event_num)
    if pulse_id:
        data = fetch_pulse_fixture_details(pulse_id)
        if data:
            team_lists = data.get("teamLists", [])
            if len(team_lists) >= 2:
                h_sheet = team_lists[0]
                a_sheet = team_lists[1]
                if len(h_sheet.get("lineup", [])) >= 11 or len(a_sheet.get("lineup", [])) >= 11:
                    sub_events = {}
                    for ev in data.get("events", []):
                        if ev.get("type") in ["substitution", "sub"]:
                            min_str = ev.get("time", {}).get("label", "")
                            off_id = ev.get("subOff", {}).get("id") or ev.get("personId")
                            on_id = ev.get("subOn", {}).get("id")
                            if off_id:
                                sub_events[off_id] = ("OFF", min_str)
                            if on_id:
                                sub_events[on_id] = ("ON", min_str)

                    def format_official_sheet(sheet):
                        starters = []
                        for p in sheet.get("lineup", []):
                            p_id = p.get("id")
                            raw_num = p.get("matchShirtNumber") or p.get("shirtNum")
                            num_str = f"#{raw_num} " if raw_num and str(raw_num).strip() not in ["-", "None", ""] else ""
                            name = p.get("name", {}).get("display", "Unknown")
                            capt = " (C)" if p.get("captain", False) else ""
                            raw_pos = str(p.get("matchPosition", "MID")).upper()
                            clean_pos = "GKP" if "G" in raw_pos else ("DEF" if "D" in raw_pos else ("FWD" if "F" in raw_pos else "MID"))

                            sub_tag = ""
                            if p_id in sub_events and sub_events[p_id][0] == "OFF":
                                sub_tag = f" <span style='color:#f43f5e; font-weight:700;'>▼ {sub_events[p_id][1]}</span>"

                            starters.append({
                                "rank": pos_order_map.get(clean_pos, 3),
                                "text": f"{num_str}**{name}**{capt} • *{clean_pos}*{sub_tag}"
                            })

                        sorted_starters = [s["text"] for s in sorted(starters, key = lambda x: x["rank"])]

                        subs_used = []
                        subs_unused = []
                        for p in sheet.get("substitutes", []):
                            p_id = p.get("id")
                            raw_num = p.get("matchShirtNumber") or p.get("shirtNum")
                            num_str = f"#{raw_num} " if raw_num and str(raw_num).strip() not in ["-", "None", ""] else ""
                            name = p.get("name", {}).get("display", "Unknown")
                            if p_id in sub_events and sub_events[p_id][0] == "ON":
                                subs_used.append(f"{num_str}**{name}** <span style='color:#22c55e; font-weight:800;'>▲ {sub_events[p_id][1]}</span>")
                            else:
                                subs_unused.append(f"{num_str}{name}")

                        return sorted_starters, subs_used, subs_unused

                    h_start, h_used, h_un = format_official_sheet(h_sheet)
                    a_start, a_used, a_un = format_official_sheet(a_sheet)

                    return {
                        "has_lineups": True,
                        "home_starters": h_start, "home_subs_used": h_used, "home_subs_unused": h_un,
                        "away_starters": a_start, "away_subs_used": a_used, "away_subs_unused": a_un
                    }

    # 2. Secondary Source: ESPN Open Feed
    espn_data = _fetch_espn_lineup_backup(home_short, away_short)
    if espn_data:
        return espn_data

    # 3. Tertiary Source: In-Play Live Elements Fallback
    if live_elements and element_lookup and home_team_id and away_team_id:
        def extract_squad(target_club_id):
            club_players = []
            for elem_str_id, e_info in live_elements.items():
                try:
                    eid = int(elem_str_id)
                except (ValueError, TypeError):
                    continue
                p_obj = element_lookup.get(eid, {})
                if p_obj.get("team") == target_club_id:
                    stats = e_info.get("stats", {}) if isinstance(e_info, dict) else {}
                    mins = int(stats.get("minutes", 0))
                    pts = int(stats.get("total_points", 0))
                    pos_id = p_obj.get("element_type", 1)
                    pos_abbr = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}.get(pos_id, "MID")
                    club_players.append({
                        "id": eid, "name": p_obj.get("web_name", "Unknown"),
                        "pos": pos_abbr, "pos_rank": pos_id,
                        "mins": mins, "pts": pts, "status": p_obj.get("status", "a"),
                        "chance": p_obj.get("chance_of_playing_next_round")
                    })

            played = [p for p in club_players if p["mins"] > 0]
            if not played:
                return [], [], []

            gkps_played = [p for p in played if p["pos"] == "GKP"]
            outfield_played = [p for p in played if p["pos"] != "GKP"]

            starting_gk = sorted(gkps_played, key = lambda x: x["mins"], reverse = True)[:1] if gkps_played else []
            other_gks = [p for p in gkps_played if p not in starting_gk]

            sorted_outfield = sorted(outfield_played, key = lambda x: x["mins"], reverse = True)
            starting_outfield = sorted_outfield[:10]
            subs_outfield = sorted_outfield[10:]

            starters_raw = starting_gk + starting_outfield
            starters_sorted = sorted(starters_raw, key = lambda x: (x["pos_rank"], -x["mins"]))
            effective_full_mins = max([p["mins"] for p in starters_sorted]) if starters_sorted else match_minute

            starters_formatted = []
            for p in starters_sorted:
                sub_off_tag = f" <span style='color:#f43f5e; font-weight:700;'>▼ {p['mins']}'</span>" if p["mins"] < effective_full_mins else ""
                starters_formatted.append(f"**{p['name']}** • *{p['pos']}* ({p['mins']}', {p['pts']} pts){sub_off_tag}")

            subs_used_sorted = sorted(other_gks + subs_outfield, key = lambda x: (x["pos_rank"], -x["mins"]))
            subs_used_formatted = []
            for p in subs_used_sorted:
                on_minute = max(1, effective_full_mins - p["mins"])
                subs_used_formatted.append(f"**{p['name']}** • *{p['pos']}* ({p['mins']}', {p['pts']} pts) <span style='color:#22c55e; font-weight:800;'>▲ {on_minute}'</span>")

            played_ids = {p["id"] for p in played}
            unplayed = [
                p for p in club_players
                if p["id"] not in played_ids
                and p["status"] not in ["i", "s", "u"]
                and (p["chance"] is None or p["chance"] > 0)
            ]
            unplayed_sorted = sorted(unplayed, key = lambda x: x["pos_rank"])[:9]
            subs_unused_formatted = [f"{p['name']} ({p['pos']})" for p in unplayed_sorted]

            return starters_formatted, subs_used_formatted, subs_unused_formatted

        h_start, h_used, h_un = extract_squad(home_team_id)
        a_start, a_used, a_un = extract_squad(away_team_id)

        if h_start or a_start:
            return {
                "has_lineups": True,
                "home_starters": h_start, "home_subs_used": h_used, "home_subs_unused": h_un,
                "away_starters": a_start, "away_subs_used": a_used, "away_subs_unused": a_un
            }

    return {"has_lineups": False}
def get_availability_multiplier(row):
    status = row.get("status", "a")
    chance = row.get("chance_of_playing_next_round")
    
    if status in ["i", "s", "u"]:
        return 0.0
    if pd.notna(chance):
        val = float(chance)
        if val >= 75:
            return 0.9
        if val >= 50:
            return 0.6
        if val >= 25:
            return 0.3
        return 0.0
    if status == "d":
        return 0.6
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
            return "Doubtful (" + str(int(chance)) + "%)"
        return "Doubtful (50%)"
    return "Fit (100%)"

def calculate_win_probability(live1, proj1, to_play1, live2, proj2, to_play2, is_finished):
    if is_finished:
        if live1 > live2:
            return 100, 0
        if live2 > live1:
            return 0, 100
        return 50, 50

    total_left = to_play1 + to_play2
    if total_left == 0:
        diff = abs(live1 - live2)
        if live1 > live2:
            return (99, 1) if diff <= 5 else (100, 0)
        if live2 > live1:
            return (1, 99) if diff <= 5 else (0, 100)
        return 50, 50

    margin = proj1 - proj2
    spread = max(6.0, total_left * 2.8)
    prob1 = 1.0 / (1.0 + math.exp(-margin / (spread / 1.7)))
    pct1 = int(round(prob1 * 100))
    pct1 = max(1, min(99, pct1))
    return pct1, 100 - pct1

def calculate_optimum_score(all_players_df):
    if all_players_df is None or all_players_df.empty:
        return 0
    gkps = all_players_df[all_players_df["Pos"] == "GKP"]
    defs = all_players_df[all_players_df["Pos"] == "DEF"]
    mids = all_players_df[all_players_df["Pos"] == "MID"]
    fwds = all_players_df[all_players_df["Pos"] == "FWD"]
    
    if gkps.empty:
        return 0
    best_gk = int(gkps["Pts"].max())
    
    best_score = -1
    for d in range(3, len(defs) + 1):
        for m in range(2, len(mids) + 1):
            f = 10 - d - m
            if f >= 1 and f <= len(fwds):
                score = (
                    best_gk
                    + int(defs.nlargest(d, "Pts")["Pts"].sum())
                    + int(mids.nlargest(m, "Pts")["Pts"].sum())
                    + int(fwds.nlargest(f, "Pts")["Pts"].sum())
                )
                if score > best_score:
                    best_score = score
    if best_score != -1:
        return best_score
    return best_gk + int(defs["Pts"].sum()) + int(mids["Pts"].sum()) + int(fwds["Pts"].sum())

def get_fdr_multiplier(team_id, current_gw, all_fixtures_list):
    if not all_fixtures_list or not team_id:
        return 1.0
    gw_has_fixtures = any(f.get("event") == current_gw for f in all_fixtures_list)
    if not gw_has_fixtures:
        return 1.0

    team_fixtures = [
        f for f in all_fixtures_list
        if f.get("event") == current_gw and (f.get("team_h") == team_id or f.get("team_a") == team_id)
    ]
    if not team_fixtures:
        return 0.0
    
    total_mult = 0.0
    for fix in team_fixtures:
        if fix.get("team_h") == team_id:
            diff = fix.get("team_h_difficulty", 3)
        else:
            diff = fix.get("team_a_difficulty", 3)
            
        if diff <= 2:
            total_mult += 1.10
        elif diff == 3:
            total_mult += 1.00
        elif diff == 4:
            total_mult += 0.92
        else:
            total_mult += 0.85
            
    return total_mult

def get_active_players_from_dfs(starters_df, bench_df):
    active_list = []
    if starters_df is not None and not starters_df.empty:
        for _, r in starters_df.iterrows():
            if r.get("sub_action") != "Subbed Off":
                active_list.append(r)
    if bench_df is not None and not bench_df.empty:
        for _, r in bench_df.iterrows():
            if r.get("sub_action") == "Subbed On":
                active_list.append(r)
    return active_list

# ----------------- EMBEDDED SVG/HTML PROGRESSION CHART ENGINE -----------------
def render_progression_chart(gw_num, alias1, alias2, starters1_df, bench1_df, starters2_df, bench2_df, all_fixtures_list, team_short_map, accent_color):
    gw_fixtures = []
    if all_fixtures_list:
        gw_fixtures = [f for f in all_fixtures_list if f.get("event") == gw_num]
    if not gw_fixtures:
        epl_fix = fetch_epl_fixtures(gw_num)
        if epl_fix:
            gw_fixtures = [f for f in epl_fix if f.get("event") == gw_num] or epl_fix

    if not gw_fixtures:
        return

    t1_active = get_active_players_from_dfs(starters1_df, bench1_df)
    t2_active = get_active_players_from_dfs(starters2_df, bench2_df)

    curr1 = 0
    curr2 = 0
    fixtures_payload = []

    def get_fixture_contributors(active_players, h_id, a_id):
        entries_list = []
        for p in active_players:
            if p.get("club_id") in (h_id, a_id):
                p_name = p.get("Player", "Unknown")
                cats = []
                g = int(p.get("G", 0))
                a = int(p.get("A", 0))
                cs = int(p.get("CS", 0))
                bonus = int(p.get("Bonus", 0))
                pos = p.get("Pos", "")

                if g > 0:
                    cats.append(f"{g}⚽" if g > 1 else "⚽")
                if a > 0:
                    cats.append(f"{a}🎯" if a > 1 else "🎯")
                if cs > 0 and pos in ["GKP", "DEF"]:
                    cats.append("🛡️")
                if bonus > 0:
                    cats.append(f"{bonus}⭐")

                if cats:
                    entries_list.append(f"{p_name} ({' '.join(cats)})")
        return ", ".join(entries_list) if entries_list else "None"

    for f_item in gw_fixtures:
        h_team_id = f_item.get("team_h")
        a_team_id = f_item.get("team_a")
        h_code = team_short_map.get(h_team_id, "H")
        a_code = team_short_map.get(a_team_id, "A")
        m_label = f"{h_code} v {a_code}"

        p1_pts = sum(int(p["Pts"]) for p in t1_active if p.get("club_id") in (h_team_id, a_team_id))
        p2_pts = sum(int(p["Pts"]) for p in t2_active if p.get("club_id") in (h_team_id, a_team_id))

        curr1 += p1_pts
        curr2 += p2_pts

        contrib1 = get_fixture_contributors(t1_active, h_team_id, a_team_id)
        contrib2 = get_fixture_contributors(t2_active, h_team_id, a_team_id)

        fixtures_payload.append({
            "match": m_label,
            "m1": {
                "manager": str(alias1),
                "pts": curr1,
                "added": f"+{p1_pts}",
                "events": contrib1,
                "color": accent_color
            },
            "m2": {
                "manager": str(alias2),
                "pts": curr2,
                "added": f"+{p2_pts}",
                "events": contrib2,
                "color": "#38bdf8"
            }
        })

    st.markdown(f"#### Gameweek {gw_num} Points Progression")
    st.caption("Cumulative matchday points tracking each EPL fixture in the order played • Tap or hover any dot to inspect")

    payload_json = json.dumps(fixtures_payload).replace("'", "&#39;")
    safe_alias1 = html.escape(str(alias1))
    safe_alias2 = html.escape(str(alias2))
    axis_font_px = 13 if large_mode else 11
    tooltip_font_px = 16 if large_mode else 14

    chart_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background-color: #000000;
            color: #f1f5f9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            overflow: hidden;
            user-select: none;
            -webkit-user-select: none;
            -webkit-tap-highlight-color: transparent;
        }}
        .chart-wrapper {{
            position: relative;
            width: 100%;
            height: 390px;
            background-color: #000000;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        .svg-box {{
            position: relative;
            width: 100%;
            height: 350px;
        }}
        svg {{
            width: 100%;
            height: 100%;
            display: block;
            overflow: visible;
        }}
        .hit-dot {{
            cursor: pointer;
            pointer-events: all;
        }}
        .vis-dot {{
            transition: r 0.15s ease, stroke-width 0.15s ease;
            pointer-events: none;
        }}
        .vis-dot.active {{
            r: 8px;
            stroke: #ffffff;
            stroke-width: 2.5px;
        }}
        .legend-row {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 24px;
            height: 36px;
            padding-bottom: 4px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: {axis_font_px + 2}px;
            font-weight: 700;
            color: #ffffff;
        }}
        .legend-swatch {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }}
        .tooltip-box {{
            display: none;
            position: absolute;
            background-color: #090c13;
            border: 2px solid #ffffff;
            border-radius: 8px;
            padding: 10px 14px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.95);
            z-index: 50;
            min-width: 230px;
            max-width: 310px;
            pointer-events: none;
        }}
        .tooltip-box table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .tooltip-box td {{
            padding: 4px 8px;
            font-size: {tooltip_font_px}px;
            line-height: 1.35;
            border-bottom: 1px solid #141a26;
        }}
        .tooltip-box tr:last-child td {{
            border-bottom: none;
        }}
        .tooltip-box td.key {{
            color: #94a3b8;
            font-weight: 600;
            text-align: right;
            white-space: nowrap;
            width: 42%;
        }}
        .tooltip-box td.val {{
            color: #f8fafc;
            font-weight: 700;
            text-align: left;
        }}
        .tooltip-divider {{
            height: 1px;
            background-color: #334155;
            margin: 6px 0;
        }}
    </style>
    </head>
    <body>
    <div class="chart-wrapper" id="chart-wrapper">
        <div class="svg-box" id="svg-box">
            <svg id="prog-svg"></svg>
            <div class="tooltip-box" id="prog-tooltip"></div>
        </div>
        <div class="legend-row">
            <div class="legend-item">
                <span class="legend-swatch" style="background-color: {accent_color};"></span>
                <span>{safe_alias1}</span>
            </div>
            <div class="legend-item">
                <span class="legend-swatch" style="background-color: #38bdf8;"></span>
                <span>{safe_alias2}</span>
            </div>
        </div>
    </div>

    <script>
        const fixtures = {payload_json};
        const accentColor = "{accent_color}";
        const secondColor = "#38bdf8";
        const axisFontPx = {axis_font_px};

        const svgEl = document.getElementById("prog-svg");
        const boxEl = document.getElementById("svg-box");
        const tooltipEl = document.getElementById("prog-tooltip");

        let pinnedKey = null;

        function buildTableHtml(item, matchName) {{
            return `
                <table>
                    <tr><td class="key">Manager</td><td class="val">${{item.manager}}</td></tr>
                    <tr><td class="key">Match</td><td class="val">${{matchName}}</td></tr>
                    <tr><td class="key">Total Pts</td><td class="val">${{item.pts}}</td></tr>
                    <tr><td class="key">Match Pts</td><td class="val">${{item.added}}</td></tr>
                    <tr><td class="key">Key Events</td><td class="val">${{item.events}}</td></tr>
                </table>
            `;
        }}

        function showTooltip(idx, side, px, py, W, H) {{
            const f = fixtures[idx];
            if (!f) return;

            let inner = "";
            if (f.m1.pts === f.m2.pts) {{
                // Both dots sit on the exact same coordinate; show requested manager first and tied manager below
                const primary = side === "m1" ? f.m1 : f.m2;
                const secondary = side === "m1" ? f.m2 : f.m1;
                inner = buildTableHtml(primary, f.match) + '<div class="tooltip-divider"></div>' + buildTableHtml(secondary, f.match);
            }} else {{
                const target = side === "m1" ? f.m1 : f.m2;
                inner = buildTableHtml(target, f.match);
            }}

            tooltipEl.innerHTML = inner;
            tooltipEl.style.display = "block";

            // Highlight active dot
            document.querySelectorAll(".vis-dot").forEach(el => el.classList.remove("active"));
            const activeDot = document.getElementById(`vdot-${{idx}}-${{side}}`);
            if (activeDot) activeDot.classList.add("active");

            // Measure and clamp tooltip position within container bounds
            const rect = tooltipEl.getBoundingClientRect();
            const tw = rect.width || 250;
            const th = rect.height || 160;

            let left = px + 14;
            if (px + tw + 24 > W) {{
                left = px - tw - 14;
            }}
            if (left < 8) left = 8;
            if (left + tw > W - 8) left = Math.max(8, W - tw - 8);

            let top = py - (th / 2);
            if (top < 6) top = 6;
            if (top + th > H - 6) top = Math.max(6, H - th - 6);

            tooltipEl.style.left = left + "px";
            tooltipEl.style.top = top + "px";
        }}

        function hideTooltip() {{
            tooltipEl.style.display = "none";
            document.querySelectorAll(".vis-dot").forEach(el => el.classList.remove("active"));
        }}

        function drawChart() {{
            const W = boxEl.clientWidth || 600;
            const H = boxEl.clientHeight || 350;
            svgEl.setAttribute("viewBox", `0 0 ${{W}} ${{H}}`);

            const padL = 48;
            const padR = 20;
            const padT = 18;
            const padB = 78;

            const plotW = Math.max(100, W - padL - padR);
            const plotH = Math.max(100, H - padT - padB);

            let maxVal = 0;
            fixtures.forEach(f => {{
                if (f.m1.pts > maxVal) maxVal = f.m1.pts;
                if (f.m2.pts > maxVal) maxVal = f.m2.pts;
            }});

            // Calculate clean Y axis step and ceiling
            let step = 5;
            if (maxVal > 60) step = 20;
            else if (maxVal > 30) step = 10;
            else if (maxVal <= 10) step = 2;

            const yMax = Math.max(step * 2, Math.ceil((maxVal + 1) / step) * step);

            const n = fixtures.length;
            const getX = (i) => n === 1 ? padL + plotW / 2 : padL + (i / (n - 1)) * plotW;
            const getY = (val) => padT + plotH - (val / yMax) * plotH;

            let svgContent = "";

            // Background click catcher to dismiss pinned tooltip
            svgContent += `<rect x="0" y="0" width="${{W}}" height="${{H}}" fill="transparent" id="bg-catcher" />`;

            // Horizontal gridlines & Y-axis labels
            for (let v = 0; v <= yMax; v += step) {{
                const y = getY(v);
                svgContent += `<line x1="${{padL}}" y1="${{y}}" x2="${{W - padR}}" y2="${{y}}" stroke="#182030" stroke-width="1" />`;
                svgContent += `<text x="${{padL - 8}}" y="${{y + 4}}" fill="#94a3b8" font-size="${{axisFontPx}}" font-weight="600" text-anchor="end">${{v}}</text>`;
            }}

            // Y-axis vertical line & title
            svgContent += `<line x1="${{padL}}" y1="${{padT}}" x2="${{padL}}" y2="${{padT + plotH}}" stroke="#182030" stroke-width="1" />`;
            const titleY = padT + plotH / 2;
            svgContent += `<text x="14" y="${{titleY}}" fill="#94a3b8" font-size="${{axisFontPx + 1}}" font-weight="700" text-anchor="middle" transform="rotate(-90, 14, ${{titleY}})">Cumulative Points</text>`;

            // X-axis vertical rotated fixture labels
            fixtures.forEach((f, i) => {{
                const x = getX(i);
                const labelY = padT + plotH + 10;
                svgContent += `<line x1="${{x}}" y1="${{padT + plotH}}" x2="${{x}}" y2="${{padT + plotH + 5}}" stroke="#182030" stroke-width="1" />`;
                svgContent += `<text x="${{x}}" y="${{labelY}}" fill="#94a3b8" font-size="${{axisFontPx}}" font-weight="600" text-anchor="end" dominant-baseline="central" transform="rotate(-90, ${{x}}, ${{labelY}})">${{f.match}}</text>`;
            }});

            // Line paths
            const pts1 = fixtures.map((f, i) => `${{getX(i)}},${{getY(f.m1.pts)}}`).join(" ");
            const pts2 = fixtures.map((f, i) => `${{getX(i)}},${{getY(f.m2.pts)}}`).join(" ");

            svgContent += `<polyline fill="none" stroke="${{accentColor}}" stroke-width="2.5" points="${{pts1}}" />`;
            svgContent += `<polyline fill="none" stroke="${{secondColor}}" stroke-width="2.5" points="${{pts2}}" />`;

            // Visible dots
            fixtures.forEach((f, i) => {{
                const x = getX(i);
                const y1 = getY(f.m1.pts);
                const y2 = getY(f.m2.pts);

                svgContent += `<circle id="vdot-${{i}}-m2" class="vis-dot" cx="${{x}}" cy="${{y2}}" r="5.5" fill="${{secondColor}}" />`;
                svgContent += `<circle id="vdot-${{i}}-m1" class="vis-dot" cx="${{x}}" cy="${{y1}}" r="5.5" fill="${{accentColor}}" />`;
            }});

            // Large transparent hit targets (r=18) for effortless mobile tapping and desktop hover
            fixtures.forEach((f, i) => {{
                const x = getX(i);
                const y1 = getY(f.m1.pts);
                const y2 = getY(f.m2.pts);

                svgContent += `<circle class="hit-dot" data-idx="${{i}}" data-side="m2" data-px="${{x}}" data-py="${{y2}}" cx="${{x}}" cy="${{y2}}" r="18" fill="transparent" />`;
                svgContent += `<circle class="hit-dot" data-idx="${{i}}" data-side="m1" data-px="${{x}}" data-py="${{y1}}" cx="${{x}}" cy="${{y1}}" r="18" fill="transparent" />`;
            }});

            svgEl.innerHTML = svgContent;

            // Wire up listeners
            const bgCatcher = document.getElementById("bg-catcher");
            if (bgCatcher) {{
                bgCatcher.addEventListener("click", () => {{
                    pinnedKey = null;
                    hideTooltip();
                }});
            }}

            document.querySelectorAll(".hit-dot").forEach(dot => {{
                const idx = parseInt(dot.getAttribute("data-idx"));
                const side = dot.getAttribute("data-side");
                const px = parseFloat(dot.getAttribute("data-px"));
                const py = parseFloat(dot.getAttribute("data-py"));
                const key = `${{idx}}-${{side}}`;

                dot.addEventListener("mouseenter", () => {{
                    if (!pinnedKey) {{
                        showTooltip(idx, side, px, py, W, H);
                    }}
                }});

                dot.addEventListener("mouseleave", () => {{
                    if (!pinnedKey) {{
                        hideTooltip();
                    }}
                }});

                dot.addEventListener("click", (e) => {{
                    e.stopPropagation();
                    if (pinnedKey === key) {{
                        pinnedKey = null;
                        hideTooltip();
                    }} else {{
                        pinnedKey = key;
                        showTooltip(idx, side, px, py, W, H);
                    }}
                }});
            }});
        }}

        drawChart();
        window.addEventListener("resize", () => {{
            pinnedKey = null;
            hideTooltip();
            drawChart();
        }});
    </script>
    </body>
    </html>
    """

    components.html(chart_html, height = 400)

@st.cache_data(ttl = 180)
def resolve_cup_match_score(manager_alias, gw_num):
    teams_registry = get_all_32_teams_registry()
    static_data = fetch_fpl_static()
    all_fixtures = fetch_all_epl_fixtures()
    if not static_data:
        return {
            "score": 0, "proj": 0.0, "high_player": 0,
            "starters": pd.DataFrame(), "bench": pd.DataFrame(),
            "in_play": 0, "ytp": 0, "bench_pts": 0, "opt": 0
        }
    pos_map = {item["id"]: item["singular_name_short"] for item in static_data["element_types"]}
    team_map = {item["id"]: item["short_name"] for item in static_data["teams"]}
    element_lookup = {item["id"]: item for item in static_data["elements"]}

    t_info = teams_registry.get(str(manager_alias).strip().lower())
    if not t_info or not t_info.get("entry_id"):
        return {
            "score": 0, "proj": 0.0, "high_player": 0,
            "starters": pd.DataFrame(), "bench": pd.DataFrame(),
            "in_play": 0, "ytp": 0, "bench_pts": 0, "opt": 0
        }
    picks = fetch_entry_event(t_info["entry_id"], gw_num)
    live_data = fetch_live_event(gw_num)
    live_elements = live_data.get("elements", {}) if live_data else {}

    club_minutes = {}
    for elem_str_id, e_info in live_elements.items():
        try:
            elem_int_id = int(elem_str_id)
        except (ValueError, TypeError):
            continue
        elem_obj = element_lookup.get(elem_int_id, {})
        c_id = elem_obj.get("team")
        if c_id:
            m_val = e_info.get("stats", {}).get("minutes", 0)
            club_minutes[c_id] = club_minutes.get(c_id, 0) + m_val

    starters, bench, live_score, proj_score, in_play, ytp, bench_pts, opt_score = evaluate_lineup(
        picks, live_elements, element_lookup, club_minutes, pos_map, team_map, gw_num, all_fixtures
    )
    active_players = get_active_players_from_dfs(starters, bench)
    active_p = [int(p.get("Pts", 0)) for p in active_players] if active_players else []
    max_player_pts = max(active_p) if active_p else 0

    return {
        "score": live_score,
        "proj": proj_score,
        "high_player": max_player_pts,
        "starters": starters,
        "bench": bench,
        "in_play": in_play,
        "ytp": ytp,
        "bench_pts": bench_pts,
        "opt": opt_score
    }

@st.cache_data(ttl = 600)
def calculate_group_standings():
    cup_df = load_cup_matches()
    teams_registry = get_all_32_teams_registry()
    if cup_df is None or cup_df.empty:
        return []

    group_matches = cup_df[(cup_df["Week"] <= 20) & (cup_df["Stage"].str.lower().str.contains("group"))].copy()

    unique_aliases = set()
    gws_needed = set()
    for _, r in group_matches.iterrows():
        m1 = str(r.get("Team 1", "")).strip()
        m2 = str(r.get("Team 2", "")).strip()
        if m1 and m1.lower() != "nan":
            unique_aliases.add(m1)
        if m2 and m2.lower() != "nan":
            unique_aliases.add(m2)
        try:
            gws_needed.add(int(r["Week"]))
        except (ValueError, TypeError):
            pass

    # Batch cache for (manager, gw) -> (score, high_player)
    score_cache = {}
    for gw in gws_needed:
        live_data_gw = fetch_live_event(gw)
        live_elements_gw = live_data_gw.get("elements", {}) if live_data_gw else {}
        for m in unique_aliases:
            res = resolve_cup_match_score(m, gw)
            score_cache[(m, gw)] = (res["score"], res["high_player"])

    standings_dict = {
        m: {
            "Manager": m,
            "Division": teams_registry.get(m.lower(), {}).get("league_key", "").split(" ")[0],
            "W": 0, "D": 0, "L": 0, "PF": 0, "Pts": 0, "High_Score": 0, "H2H": {}
        }
        for m in unique_aliases
    }

    for _, r in group_matches.iterrows():
        m1 = str(r.get("Team 1", "")).strip()
        m2 = str(r.get("Team 2", "")).strip()
        gw = int(r["Week"])
        if m1 not in standings_dict or m2 not in standings_dict:
            continue

        s1, high1 = score_cache.get((m1, gw), (0, 0))
        s2, high2 = score_cache.get((m2, gw), (0, 0))

        standings_dict[m1]["PF"] += s1
        standings_dict[m2]["PF"] += s2
        standings_dict[m1]["High_Score"] = max(standings_dict[m1]["High_Score"], high1)
        standings_dict[m2]["High_Score"] = max(standings_dict[m2]["High_Score"], high2)

        if s1 > s2:
            standings_dict[m1]["W"] += 1
            standings_dict[m1]["Pts"] += 3
            standings_dict[m2]["L"] += 1
            standings_dict[m1]["H2H"][m2] = standings_dict[m1]["H2H"].get(m2, 0) + 3
        elif s2 > s1:
            standings_dict[m2]["W"] += 1
            standings_dict[m2]["Pts"] += 3
            standings_dict[m1]["L"] += 1
            standings_dict[m2]["H2H"][m1] = standings_dict[m2]["H2H"].get(m1, 0) + 3
        elif s1 > 0 or s2 > 0:
            standings_dict[m1]["D"] += 1
            standings_dict[m1]["Pts"] += 1
            standings_dict[m2]["D"] += 1
            standings_dict[m2]["Pts"] += 1
            standings_dict[m1]["H2H"][m2] = standings_dict[m1]["H2H"].get(m2, 0) + 1
            standings_dict[m2]["H2H"][m1] = standings_dict[m2]["H2H"].get(m1, 0) + 1

    rows = list(standings_dict.values())

    def sort_tiebreakers(a, b):
        if a["Pts"] != b["Pts"]:
            return b["Pts"] - a["Pts"]
        if a["PF"] != b["PF"]:
            return b["PF"] - a["PF"]
        h2h_a = a["H2H"].get(b["Manager"], 0)
        h2h_b = b["H2H"].get(a["Manager"], 0)
        if h2h_a != h2h_b:
            return h2h_b - h2h_a
        return b["High_Score"] - a["High_Score"]

    sorted_rows = sorted(rows, key = functools.cmp_to_key(sort_tiebreakers))

    display_table = []
    for rank, item in enumerate(sorted_rows, 1):
        short_zone = "🏆 Top 8" if rank <= 8 else ("⚔️ 9 - 24" if rank <= 24 else "🪣 25 - 32")
        display_table.append({
            "Pos": rank,
            "Zone": short_zone,
            "Manager": item["Manager"],
            "Div": item["Division"],
            "W": item["W"],
            "D": item["D"],
            "L": item["L"],
            "PF": item["PF"],
            "Pts": item["Pts"],
            "Best XI": item["High_Score"]
        })

    return display_table

def calculate_league_tables(entries, matches, current_gw, live_elements, element_lookup, club_minutes, pos_map, team_map, all_fixtures_list):
    lentry_map = {e["id"]: e for e in entries}
    
    official_stats = {
        e["id"]: {"wins": 0, "draws": 0, "losses": 0, "pf": 0, "pts": 0}
        for e in entries
    }
    live_stats = {
        e["id"]: {"wins": 0, "draws": 0, "losses": 0, "pf": 0, "pts": 0}
        for e in entries
    }
    
    for m in matches:
        ev = m["event"]
        t1_id = m["league_entry_1"]
        t2_id = m["league_entry_2"]
        if t1_id not in official_stats or t2_id not in official_stats:
            continue
            
        if ev < current_gw and m.get("finished", False):
            s1 = m.get("league_entry_1_points", 0)
            s2 = m.get("league_entry_2_points", 0)
            
            official_stats[t1_id]["pf"] += s1
            official_stats[t2_id]["pf"] += s2
            live_stats[t1_id]["pf"] += s1
            live_stats[t2_id]["pf"] += s2
            
            if s1 > s2:
                official_stats[t1_id]["wins"] += 1
                official_stats[t1_id]["pts"] += 3
                official_stats[t2_id]["losses"] += 1
                live_stats[t1_id]["wins"] += 1
                live_stats[t1_id]["pts"] += 3
                live_stats[t2_id]["losses"] += 1
            elif s2 > s1:
                official_stats[t2_id]["wins"] += 1
                official_stats[t2_id]["pts"] += 3
                official_stats[t1_id]["losses"] += 1
                live_stats[t2_id]["wins"] += 1
                live_stats[t2_id]["pts"] += 3
                live_stats[t1_id]["losses"] += 1
            else:
                official_stats[t1_id]["draws"] += 1
                official_stats[t1_id]["pts"] += 1
                official_stats[t2_id]["draws"] += 1
                official_stats[t2_id]["pts"] += 1
                live_stats[t1_id]["draws"] += 1
                live_stats[t1_id]["pts"] += 1
                live_stats[t2_id]["draws"] += 1
                live_stats[t2_id]["pts"] += 1
                
        elif ev == current_gw:
            is_fin = m.get("finished", False)
            if is_fin:
                s1 = m.get("league_entry_1_points", 0)
                s2 = m.get("league_entry_2_points", 0)
            else:
                p1 = fetch_entry_event(lentry_map[t1_id].get("entry_id"), current_gw)
                p2 = fetch_entry_event(lentry_map[t2_id].get("entry_id"), current_gw)
                _, _, s1, _, _, _, _, _ = evaluate_lineup(p1, live_elements, element_lookup, club_minutes, pos_map, team_map, current_gw, all_fixtures_list)
                _, _, s2, _, _, _, _, _ = evaluate_lineup(p2, live_elements, element_lookup, club_minutes, pos_map, team_map, current_gw, all_fixtures_list)
                
            live_stats[t1_id]["pf"] += s1
            live_stats[t2_id]["pf"] += s2
            
            if s1 > s2:
                live_stats[t1_id]["wins"] += 1
                live_stats[t1_id]["pts"] += 3
                live_stats[t2_id]["losses"] += 1
            elif s2 > s1:
                live_stats[t2_id]["wins"] += 1
                live_stats[t2_id]["pts"] += 3
                live_stats[t1_id]["losses"] += 1
            else:
                live_stats[t1_id]["draws"] += 1
                live_stats[t1_id]["pts"] += 1
                live_stats[t2_id]["draws"] += 1
                live_stats[t2_id]["pts"] += 1

    official_rows = []
    for e in entries:
        t_id = e["id"]
        stat = official_stats[t_id]
        alias = get_manager_alias(e.get("player_first_name", ""), e.get("player_last_name", ""))
        official_rows.append({
            "team_id": t_id,
            "Team": e.get("entry_name", "Team"),
            "Manager": alias,
            "W": stat["wins"],
            "D": stat["draws"],
            "L": stat["losses"],
            "PF": stat["pf"],
            "Pts": stat["pts"]
        })
        
    official_rows = sorted(official_rows, key = lambda x: (x["Pts"], x["PF"]), reverse = True)
    official_rank_map = {}
    for idx, r in enumerate(official_rows, 1):
        r["Pos"] = idx
        official_rank_map[r["team_id"]] = idx

    live_rows = []
    for e in entries:
        t_id = e["id"]
        stat = live_stats[t_id]
        alias = get_manager_alias(e.get("player_first_name", ""), e.get("player_last_name", ""))
        live_rows.append({
            "team_id": t_id,
            "Team": e.get("entry_name", "Team"),
            "Manager": alias,
            "W": stat["wins"],
            "D": stat["draws"],
            "L": stat["losses"],
            "PF": stat["pf"],
            "Pts": stat["pts"]
        })
        
    live_rows = sorted(live_rows, key = lambda x: (x["Pts"], x["PF"]), reverse = True)
    for idx, r in enumerate(live_rows, 1):
        r["Pos"] = idx
        off_pos = official_rank_map.get(r["team_id"], idx)
        diff = off_pos - idx
        if diff > 0:
            r["Move"] = f"<span style='color:#22c55e; font-weight:800;'>▲ {diff}</span>"
        elif diff < 0:
            r["Move"] = f"<span style='color:#ef4444; font-weight:800;'>▼ {abs(diff)}</span>"
        else:
            r["Move"] = "<span style='color:#64748b; font-weight:700;'>▬</span>"

    official_df = pd.DataFrame(official_rows)[["Pos", "Team", "Manager", "W", "D", "L", "PF", "Pts"]].set_index("Pos")
    live_df = pd.DataFrame(live_rows)[["Pos", "Move", "Team", "Manager", "W", "D", "L", "PF", "Pts"]].set_index("Pos")
    
    return official_df, live_df

@st.cache_data(ttl = 300)
def calculate_xi_stats_for_gw(entries, gw, element_lookup, pos_map, team_map, all_fixtures_list):
    live_data_gw = fetch_live_event(gw)
    live_elements_gw = live_data_gw.get("elements", {}) if live_data_gw else {}

    club_minutes_gw = {}
    for elem_str_id, e_info in live_elements_gw.items():
        try:
            elem_int_id = int(elem_str_id)
        except (ValueError, TypeError):
            continue
        elem_obj = element_lookup.get(elem_int_id, {})
        c_id = elem_obj.get("team")
        if c_id:
            m_val = e_info.get("stats", {}).get("minutes", 0)
            club_minutes_gw[c_id] = club_minutes_gw.get(c_id, 0) + m_val

    rows = []
    for e in entries:
        alias = get_manager_alias(e.get("player_first_name", ""), e.get("player_last_name", ""))
        picks = fetch_entry_event(e.get("entry_id"), gw)
        if not picks:
            rows.append({
                "Manager": alias,
                "Goals": 0,
                "Assists": 0,
                "Clean Sheets": 0
            })
            continue

        starters_df, bench_df, _, _, _, _, _, _ = evaluate_lineup(
            picks, live_elements_gw, element_lookup, club_minutes_gw, pos_map, team_map, gw, all_fixtures_list
        )

        active_starters = starters_df[starters_df["sub_action"] != "Subbed Off"] if not starters_df.empty else pd.DataFrame()
        active_bench = bench_df[bench_df["sub_action"] == "Subbed On"] if not bench_df.empty else pd.DataFrame()
        final_xi = pd.concat([active_starters, active_bench], ignore_index = True)

        if not final_xi.empty:
            g = int(final_xi["G"].sum())
            a = int(final_xi["A"].sum())
            def_gk = final_xi["Pos"].isin(["GKP", "DEF"])
            cs = int(final_xi[def_gk]["CS"].sum())
        else:
            g, a, cs = 0, 0, 0

        rows.append({
            "Manager": alias,
            "Goals": g,
            "Assists": a,
            "Clean Sheets": cs
        })

    df = pd.DataFrame(rows).sort_values(
        by = "Manager",
        key = lambda col: col.str.lower(),
        ascending = True
    ).reset_index(drop = True)
    return df

@st.cache_data(ttl = 300)
def calculate_xi_stats_all(entries, current_gw, element_lookup, pos_map, team_map, all_fixtures_list):
    total_stats = {
        e["id"]: {
            "Manager": get_manager_alias(e.get("player_first_name", ""), e.get("player_last_name", "")),
            "Goals": 0,
            "Assists": 0,
            "Clean Sheets": 0
        }
        for e in entries
    }

    for gw in range(1, current_gw + 1):
        gw_df = calculate_xi_stats_for_gw(entries, gw, element_lookup, pos_map, team_map, all_fixtures_list)
        for _, row in gw_df.iterrows():
            for e in entries:
                if get_manager_alias(e.get("player_first_name", ""), e.get("player_last_name", "")) == row["Manager"]:
                    total_stats[e["id"]]["Goals"] += row["Goals"]
                    total_stats[e["id"]]["Assists"] += row["Assists"]
                    total_stats[e["id"]]["Clean Sheets"] += row["Clean Sheets"]
                    break

    df = pd.DataFrame(list(total_stats.values())).sort_values(
        by = "Manager",
        key = lambda col: col.str.lower(),
        ascending = True
    ).reset_index(drop = True)
    return df

def render_xi_stats_view(entries, current_gw, element_lookup, pos_map, team_map, all_fixtures_list):
    st.subheader("GACS - Goals, Assists and Clean Sheets")
    st.caption("Goals (all players), Assists (all players) and Clean Sheets (GKP and DEF only) registered by players in each manager's final starting lineup.")

    gw_options = [f"Gameweek {gw}" for gw in range(current_gw, 0, -1)] + ["All Season (Total)"]
    selected_option = st.selectbox("Select Gameweek to Inspect", gw_options, index = 0, key = f"xi_gw_sel_{current_gw}")

    with st.spinner("Compiling starting XI performance data..."):
        if "All Season" in selected_option:
            df = calculate_xi_stats_all(entries, current_gw, element_lookup, pos_map, team_map, all_fixtures_list)
        else:
            chosen_gw_num = int(selected_option.split(" ")[1])
            df = calculate_xi_stats_for_gw(entries, chosen_gw_num, element_lookup, pos_map, team_map, all_fixtures_list)

    st.table(df.set_index("Manager"))

def _compute_disciplinary_gw_internal(league_id, gw):
    static_data = fetch_fpl_static()
    league_details, _ = fetch_league_data(league_id)
    if not static_data or not league_details:
        return pd.DataFrame()

    entries = league_details.get("league_entries", [])
    matches = league_details.get("matches", [])
    pos_map = {item["id"]: item["singular_name_short"] for item in static_data["element_types"]}
    team_map = {item["id"]: item["short_name"] for item in static_data["teams"]}
    element_lookup = {item["id"]: item for item in static_data["elements"]}

    live_data_gw = fetch_live_event(gw)
    live_elements_gw = live_data_gw.get("elements", {}) if live_data_gw else {}

    club_minutes_gw = {}
    for elem_str_id, e_info in live_elements_gw.items():
        try:
            elem_int_id = int(elem_str_id)
        except (ValueError, TypeError):
            continue
        elem_obj = element_lookup.get(elem_int_id, {})
        c_id = elem_obj.get("team")
        if c_id:
            m_val = e_info.get("stats", {}).get("minutes", 0)
            club_minutes_gw[c_id] = club_minutes_gw.get(c_id, 0) + m_val

    mgr_data = {}
    for e in entries:
        l_id = e["id"]
        alias = get_manager_alias(e.get("player_first_name", ""), e.get("player_last_name", ""))
        picks = fetch_entry_event(e.get("entry_id"), gw)
        if not picks:
            mgr_data[l_id] = {"Manager": alias, "YC": 0, "RC": 0, "Pts_Lost": 0, "Score": 0}
            continue

        starters_df, bench_df, live_score, _, _, _, _, _ = evaluate_lineup(
            picks, live_elements_gw, element_lookup, club_minutes_gw, pos_map, team_map, gw, None
        )
        active_starters = starters_df[starters_df["sub_action"] != "Subbed Off"] if not starters_df.empty else pd.DataFrame()
        active_bench = bench_df[bench_df["sub_action"] == "Subbed On"] if not bench_df.empty else pd.DataFrame()
        final_xi = pd.concat([active_starters, active_bench], ignore_index = True)

        if not final_xi.empty:
            yc = int(final_xi["YC"].sum())
            rc = int(final_xi["RC"].sum())
        else:
            yc, rc = 0, 0

        pts_lost = (yc * 1) + (rc * 3)
        mgr_data[l_id] = {
            "Manager": alias,
            "YC": yc,
            "RC": rc,
            "Pts_Lost": pts_lost,
            "Score": live_score
        }

    gw_matches = [m for m in matches if m.get("event") == gw]
    match_lookup = {}
    for m in gw_matches:
        t1 = m.get("league_entry_1")
        t2 = m.get("league_entry_2")
        is_fin = m.get("finished", False)
        s1 = m.get("league_entry_1_points", mgr_data.get(t1, {}).get("Score", 0)) if is_fin else mgr_data.get(t1, {}).get("Score", 0)
        s2 = m.get("league_entry_2_points", mgr_data.get(t2, {}).get("Score", 0)) if is_fin else mgr_data.get(t2, {}).get("Score", 0)
        match_lookup[t1] = (t2, s1, s2)
        match_lookup[t2] = (t1, s2, s1)

    rows = []
    for l_id, info in mgr_data.items():
        yc = info["YC"]
        rc = info["RC"]
        pts_lost = info["Pts_Lost"]
        m_info = match_lookup.get(l_id)

        if m_info:
            opp_id, my_s, opp_s = m_info
            opp_alias = mgr_data.get(opp_id, {}).get("Manager", "Opponent")
            if my_s > opp_s:
                act_res = "W"
            elif my_s < opp_s:
                act_res = "L"
            else:
                act_res = "D"

            score_without_cards = my_s + pts_lost
            if score_without_cards > opp_s:
                no_card_res = "W"
            elif score_without_cards < opp_s:
                no_card_res = "L"
            else:
                no_card_res = "D"

            if pts_lost > 0 and act_res != no_card_res:
                pts_map = {"W": 3, "D": 1, "L": 0}
                cost_league_pts = pts_map[no_card_res] - pts_map[act_res]
                impact_str = f"Yes ({no_card_res} → {act_res}, -{cost_league_pts} pt{'s' if cost_league_pts > 1 else ''})"
                changed_flag = 1
            else:
                cost_league_pts = 0
                impact_str = "No"
                changed_flag = 0

            match_str = f"{act_res} ({my_s} - {opp_s} vs {opp_alias})"
        else:
            match_str = "N/A"
            impact_str = "No"
            changed_flag = 0
            cost_league_pts = 0

        rows.append({
            "Manager": info["Manager"],
            "Yellow Cards": yc,
            "Red Cards": rc,
            "Card Pts": -pts_lost if pts_lost > 0 else 0,
            "Matchup": match_str,
            "Result Changed?": impact_str,
            "_changed_count": changed_flag,
            "_league_pts_cost": cost_league_pts,
            "_raw_pts_lost": pts_lost
        })

    df = pd.DataFrame(rows).sort_values(
        by = "Manager",
        key = lambda col: col.str.lower(),
        ascending = True
    ).reset_index(drop = True)
    return df

@st.cache_data(ttl = 86400)
def get_disciplinary_gw_finished(league_id, gw):
    return _compute_disciplinary_gw_internal(league_id, gw)

@st.cache_data(ttl = 120)
def get_disciplinary_gw_live(league_id, gw):
    return _compute_disciplinary_gw_internal(league_id, gw)

@st.cache_data(ttl = 600)
def get_disciplinary_season_summary(league_id, current_gw):
    league_details, _ = fetch_league_data(league_id)
    entries = league_details.get("league_entries", []) if league_details else []
    totals = {
        get_manager_alias(e.get("player_first_name", ""), e.get("player_last_name", "")): {
            "Manager": get_manager_alias(e.get("player_first_name", ""), e.get("player_last_name", "")),
            "Yellow Cards": 0,
            "Red Cards": 0,
            "Total Card Pts": 0,
            "Results Changed": 0,
            "League Pts Cost": 0
        }
        for e in entries
    }
    weekly_swings = []
    per_week_rows = []

    for gw in range(1, current_gw + 1):
        if gw < current_gw:
            gw_df = get_disciplinary_gw_finished(league_id, gw)
        else:
            gw_df = get_disciplinary_gw_live(league_id, gw)

        for _, r in gw_df.iterrows():
            mgr = r["Manager"]
            if mgr in totals:
                totals[mgr]["Yellow Cards"] += int(r["Yellow Cards"])
                totals[mgr]["Red Cards"] += int(r["Red Cards"])
                totals[mgr]["Total Card Pts"] += int(r["Card Pts"])
                totals[mgr]["Results Changed"] += int(r["_changed_count"])
                totals[mgr]["League Pts Cost"] += int(r["_league_pts_cost"])

            per_week_rows.append({
                "GW": f"GW {gw}",
                "Manager": mgr,
                "YC": int(r["Yellow Cards"]),
                "RC": int(r["Red Cards"]),
                "Card Pts": int(r["Card Pts"]),
                "Matchup": r["Matchup"],
                "Result Changed?": r["Result Changed?"]
            })

            if r["_changed_count"] > 0:
                weekly_swings.append({
                    "GW": f"GW {gw}",
                    "Manager": mgr,
                    "Matchup": r["Matchup"],
                    "Yellow Cards": int(r["Yellow Cards"]),
                    "Red Cards": int(r["Red Cards"]),
                    "Card Pts": int(r["Card Pts"]),
                    "Impact": r["Result Changed?"]
                })

    season_df = pd.DataFrame(list(totals.values())).sort_values(
        by = ["Total Card Pts", "Yellow Cards"],
        ascending = [True, False]
    ).reset_index(drop = True)

    swings_df = pd.DataFrame(weekly_swings) if weekly_swings else pd.DataFrame()
    pw_df = pd.DataFrame(per_week_rows) if per_week_rows else pd.DataFrame()
    return season_df, swings_df, pw_df, sorted(list(totals.keys()))

def render_disciplinary_view(league_id, current_gw, key_suffix = "main"):
    st.subheader("🟨🟥 Disciplinary Record - Starting XI Cards & Result Impact")
    st.caption("Tracks Yellow Cards (-1 pt) and Red Cards (-3 pts) in each manager's active starting XI and whether those deductions changed their match result that week.")

    # Default to current Gameweek so opening the tab is instantaneous
    gw_options = [f"Gameweek {gw}" for gw in range(current_gw, 0, -1)] + ["All Season (Total)"]
    selected_option = st.selectbox("Select Gameweek to Inspect", gw_options, index = 0, key = f"disc_gw_sel_{current_gw}_{key_suffix}")

    if "All Season" in selected_option:
        with st.spinner("Compiling season disciplinary records..."):
            season_df, swings_df, pw_df, mgr_list = get_disciplinary_season_summary(league_id, current_gw)

        st.markdown("#### Season Totals")
        if not season_df.empty:
            st.table(season_df.set_index("Manager"))

        st.markdown("#### Matches Where Cards Changed the Result")
        if not swings_df.empty:
            st.table(swings_df.set_index("GW"))
        else:
            st.info("No match results have been altered by starting XI card deductions this season.")

        if not pw_df.empty:
            with st.expander("📅 View Full Per - Week Breakdown"):
                mgr_filter = st.selectbox("Filter by Manager", ["All Managers"] + mgr_list, key = f"disc_pw_mgr_{key_suffix}")
                filtered_pw = pw_df[pw_df["Manager"] == mgr_filter] if mgr_filter != "All Managers" else pw_df
                st.table(filtered_pw.set_index("GW"))
    else:
        chosen_gw_num = int(selected_option.split(" ")[1])
        with st.spinner(f"Loading Gameweek {chosen_gw_num} disciplinary data..."):
            if chosen_gw_num < current_gw:
                gw_df = get_disciplinary_gw_finished(league_id, chosen_gw_num)
            else:
                gw_df = get_disciplinary_gw_live(league_id, chosen_gw_num)

        if not gw_df.empty:
            display_df = gw_df[["Manager", "Yellow Cards", "Red Cards", "Card Pts", "Matchup", "Result Changed?"]].copy()
            st.table(display_df.set_index("Manager"))
        else:
            st.info("No disciplinary data available for this gameweek.")

# ----------------- 1. HOME PAGE -----------------
if st.session_state.page == "Home":
    static_data = fetch_fpl_static()
    league_details, _ = fetch_league_data(active_league_id)
    all_fixtures = fetch_all_epl_fixtures()

    matches = league_details.get("matches", []) if league_details else []
    all_events = sorted(list({m["event"] for m in matches})) if matches else list(range(1, 39))
    unplayed_events = sorted(list({m["event"] for m in matches if not m.get("finished", False)})) if matches else []
    current_gw = unplayed_events[0] if unplayed_events else (all_events[-1] if all_events else 1)

    events_list = static_data.get("events", []) if static_data else []
    if isinstance(events_list, dict):
        events_list = events_list.get("data", [])

    target_ev = next((ev for ev in events_list if ev.get("id") == current_gw), None)
    lineup_iso = target_ev.get("deadline_time") if target_ev else None

    if not lineup_iso and all_fixtures:
        gw_fixtures = [f for f in all_fixtures if f.get("event") == current_gw and f.get("kickoff_time")]
        if gw_fixtures:
            gw_fixtures = sorted(gw_fixtures, key = lambda x: x.get("kickoff_time"))
            earliest_ko = gw_fixtures[0].get("kickoff_time")
            try:
                lineup_dt = pd.to_datetime(earliest_ko) - pd.Timedelta(minutes = 90)
                lineup_iso = lineup_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                pass

    if lineup_iso:
        try:
            lineup_dt = pd.to_datetime(lineup_iso)
            waiver_dt = lineup_dt - pd.Timedelta(hours = 24)
            waiver_iso = waiver_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            waiver_iso = lineup_iso
    else:
        lineup_iso = ""
        waiver_iso = ""

    # Scoped style strictly targeting the home header and trimming mobile dead space
    st.markdown("""
    <style>
    /* Remove default Streamlit top whitespace */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }
    /* Restrict the Season X crest width on all screens */
    div[data-testid="stColumn"]:has(#home-crest-anchor) img {
        max-width: 140px !important;
        width: 140px !important;
        height: auto !important;
        margin: 0 auto !important;
        display: block !important;
    }
    </style>
    """, unsafe_allow_html = True)

    col_brand, col_intro = st.columns([1, 4])
    with col_brand:
        st.markdown("<div id='home-crest-anchor'></div>", unsafe_allow_html = True)
        if logo_path.exists():
            st.image(str(logo_path), width = 140)
    with col_intro:
        st.markdown(f"""
        <div style="margin-top: 0px;">
            <h1 style="margin: 0; font-size: 1.8rem; letter-spacing: -0.5px;">CDP App {dash} Season X</h1>
            <p style="color: #94a3b8; margin: 2px 0 0 0; font-size: 0.88rem; line-height: 1.3;">Dellarverse HQ: Central Draft Intelligence, Live Projections and Official Publications</p>
        </div>
        """, unsafe_allow_html = True)

    countdown_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background-color: #000000;
            color: #f1f5f9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            overflow: hidden;
        }}
        .container {{
            display: flex;
            gap: 8px;
            width: 100%;
        }}
        .card {{
            flex: 1;
            background-color: #090c13;
            border: 1px solid #182030;
            border-radius: 8px;
            padding: 6px 10px;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2px;
        }}
        .title {{
            font-size: 0.78rem;
            font-weight: 700;
            color: #94a3b8;
            text-transform: uppercase;
        }}
        .gw-tag {{
            font-size: 0.72rem;
            font-weight: 800;
            color: {active_theme['accent']};
            background-color: {active_theme['badge_bg']};
            border: 1px solid {active_theme['accent']};
            padding: 1px 5px;
            border-radius: 4px;
        }}
        .clock-row {{
            display: flex;
            gap: 6px;
            align-items: baseline;
            margin: 2px 0;
        }}
        .num {{
            font-family: monospace;
            font-size: 1.35rem;
            font-weight: 800;
            color: #ffffff;
        }}
        .sec-num {{
            font-family: monospace;
            font-size: 1.35rem;
            font-weight: 800;
            color: {active_theme['accent']};
        }}
        .unit {{
            font-size: 0.75rem;
            font-weight: 600;
            color: #64748b;
        }}
        .sub {{
            font-size: 0.75rem;
            color: #94a3b8;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        @media (max-width: 600px) {{
            .container {{
                flex-direction: column;
                gap: 5px;
            }}
            .card {{
                padding: 6px 8px;
            }}
            .num, .sec-num {{
                font-size: 1.15rem;
            }}
        }}
    </style>
    </head>
    <body>
    <div class="container">
        <div class="card">
            <div class="header">
                <span class="title">⚡ Waiver Deadline</span>
                <span class="gw-tag">GW {current_gw}</span>
            </div>
            <div id="waiver-clock" class="clock-row">
                <span class="num">--<span class="unit">d</span></span>
                <span class="num">--<span class="unit">h</span></span>
                <span class="num">--<span class="unit">m</span></span>
                <span class="sec-num">--<span class="unit">s</span></span>
            </div>
            <div id="waiver-sub" class="sub">Calculating...</div>
        </div>
        <div class="card">
            <div class="header">
                <span class="title">🔒 Lineup Set Deadline</span>
                <span class="gw-tag">GW {current_gw}</span>
            </div>
            <div id="lineup-clock" class="clock-row">
                <span class="num">--<span class="unit">d</span></span>
                <span class="num">--<span class="unit">h</span></span>
                <span class="num">--<span class="unit">m</span></span>
                <span class="sec-num">--<span class="unit">s</span></span>
            </div>
            <div id="lineup-sub" class="sub">Calculating...</div>
        </div>
    </div>

    <script>
        const waiverTarget = new Date("{waiver_iso}").getTime();
        const lineupTarget = new Date("{lineup_iso}").getTime();

        const opts = {{ weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }};
        if (!isNaN(waiverTarget)) {{
            document.getElementById("waiver-sub").textContent = new Date(waiverTarget).toLocaleDateString(undefined, opts) + " (24h before KO)";
        }}
        if (!isNaN(lineupTarget)) {{
            document.getElementById("lineup-sub").textContent = new Date(lineupTarget).toLocaleDateString(undefined, opts) + " (90m before KO)";
        }}

        function updateClocks() {{
            const now = new Date().getTime();

            function renderTimer(target, clockId, subId, passedText) {{
                const clockEl = document.getElementById(clockId);
                const subEl = document.getElementById(subId);
                if (!clockEl) return;

                const diff = target - now;
                if (isNaN(target) || diff <= 0) {{
                    clockEl.innerHTML = '<span style="color: #ef4444; font-weight: 800; font-size: 1.05rem; font-family: monospace;">DEADLINE PASSED</span>';
                    if (subEl) subEl.textContent = passedText;
                    return;
                }}

                const d = Math.floor(diff / (1000 * 60 * 60 * 24));
                const h = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                const s = Math.floor((diff % (1000 * 60)) / 1000);
                const pad = (n) => String(n).padStart(2, '0');

                clockEl.innerHTML = `
                    <span class="num">${{pad(d)}}<span class="unit">d</span></span>
                    <span class="num">${{pad(h)}}<span class="unit">h</span></span>
                    <span class="num">${{pad(m)}}<span class="unit">m</span></span>
                    <span class="sec-num">${{pad(s)}}<span class="unit">s</span></span>
                `;
            }}

            renderTimer(waiverTarget, 'waiver-clock', 'waiver-sub', 'Waivers Processed');
            renderTimer(lineupTarget, 'lineup-clock', 'lineup-sub', 'Lineups Locked');
        }}

        updateClocks();
        setInterval(updateClocks, 1000);
    </script>
    </body>
    </html>
    """
    components.html(countdown_html, height = 135)
# ----------------- COULD BE WORSE, COULD BE WILL TRACKER -----------------
    cbw_count, cbw_at_risk = calculate_cbwcbw_tracker(current_gw)

    banner_bg = "#1f1305" if cbw_count > 10 else ("#2a0d0d" if cbw_count > 0 else "#052210")
    banner_border = "#f59e0b" if cbw_count > 10 else ("#ef4444" if cbw_count > 0 else "#22c55e")
    banner_text_col = "#f59e0b" if cbw_count > 10 else ("#ef4444" if cbw_count > 0 else "#22c55e")
    
    st.markdown(f"""
    <div style="background-color: {banner_bg}; border: 1px solid {banner_border}; border-radius: 8px; padding: 7px 14px; margin: 8px 0 6px 0; display: flex; justify-content: space-between; align-items: center;">
        <div style="font-size: 0.86rem; font-weight: 800; color: #ffffff; letter-spacing: -0.2px;">
            🚨 Could be worse, could be Will - Tracker:
        </div>
        <div style="font-size: 1.05rem; font-weight: 900; color: {banner_text_col}; font-family: monospace;">
            {cbw_count} / 32 In Danger
        </div>
    </div>
    """, unsafe_allow_html = True)

    # Strictly mutually exclusive display states
    if 0 < cbw_count <= 10:
        chips_html = []
        for item in cbw_at_risk:
            if item["is_locked"]:
                badge = "<span style='color:#ef4444; font-weight:900;'>💀 LOCKED IN</span>"
            elif item["rem"] > 0:
                badge = f"<span style='color:#f59e0b; font-weight:700;'>⏳ {item['rem']} to play</span>"
            else:
                badge = "<span style='color:#94a3b8;'>0 to play</span>"
                
            chip = (
                f"<div style='display:inline-flex; align-items:center; gap:6px; background:#0c101a; "
                f"border:1px solid #202b3d; border-radius:6px; padding:3px 8px; font-size:0.78rem;'>"
                f"<span style='color:#ffffff; font-weight:800;'>{item['alias']}</span>"
                f"<span style='color:#64748b; font-size:0.70rem; font-weight:700;'>({item['div']})</span>"
                f"{badge}"
                f"</div>"
            )
            chips_html.append(chip)
            
        chips_joined = "".join(chips_html)
        container_html = (
            f"<div style='background:#090c13; border:1px solid #ef4444; border-radius:8px; padding:8px 12px; margin-bottom:8px;'>"
            f"<div style='font-size:0.72rem; font-weight:800; color:#ef4444; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:6px;'>"
            f"⚠️ CBWCBW Danger Zone (Zero returns registered across Starting XI)"
            f"</div>"
            f"<div style='display:flex; flex-wrap:wrap; gap:6px;'>"
            f"{chips_joined}"
            f"</div>"
            f"</div>"
        )
        st.markdown(container_html, unsafe_allow_html = True)
    elif cbw_count == 0:
        st.markdown("""
        <div style="background: #052210; border: 1px solid #22c55e; border-radius: 6px; padding: 5px 10px; margin-bottom: 8px; text-align: center; font-size: 0.78rem; font-weight: 700; color: #22c55e;">
            🎉 Miraculously, all 32 managers registered a positive contribution. Nobody pulled a Will this week!
        </div>
        """, unsafe_allow_html = True)

    # ----------------- DYNAMIC MATCHDAY NEWS & WIRE -----------------
    entries = league_details.get("league_entries", []) if league_details else []
    lentry_map = {e["id"]: e for e in entries}
    gw_matches_active = [m for m in matches if m.get("event") == current_gw]
    top_wire_title = f"⚡ Matchday Intelligence • Gameweek {current_gw}"
    
    wire_cards = []
    if gw_matches_active and static_data:
        pos_map_wire = {item["id"]: item["singular_name_short"] for item in static_data.get("element_types", [])}
        team_map_wire = {item["id"]: item["short_name"] for item in static_data.get("teams", [])}
        element_lookup_wire = {item["id"]: item for item in static_data.get("elements", [])}

        highest_scorer = None
        highest_score_val = -1
        tightest_match = None
        tightest_margin = 999
        biggest_blowout = None
        biggest_margin = -1
        worst_benched = None
        highest_bench_pts = 0
        card_disaster = None
        highest_card_penalty = 0
        best_escape = None

        live_data_gw = fetch_live_event(current_gw)
        live_elements_gw = live_data_gw.get("elements", {}) if live_data_gw else {}
        club_mins_gw = {}
        for elem_str_id, e_info in live_elements_gw.items():
            try:
                elem_int_id = int(elem_str_id)
            except (ValueError, TypeError):
                continue
            elem_obj = element_lookup_wire.get(elem_int_id, {})
            c_id = elem_obj.get("team")
            if c_id:
                club_mins_gw[c_id] = club_mins_gw.get(c_id, 0) + e_info.get("stats", {}).get("minutes", 0)

        for m in gw_matches_active:
            s1 = m.get("league_entry_1_points", 0)
            s2 = m.get("league_entry_2_points", 0)
            e1 = lentry_map.get(m.get("league_entry_1"), {})
            e2 = lentry_map.get(m.get("league_entry_2"), {})
            a1 = get_manager_alias(e1.get("player_first_name", ""), e1.get("player_last_name", ""))
            a2 = get_manager_alias(e2.get("player_first_name", ""), e2.get("player_last_name", ""))

            p1 = fetch_entry_event(e1.get("entry_id"), current_gw)
            p2 = fetch_entry_event(e2.get("entry_id"), current_gw)

            t1_start, t1_b, t1_live, _, t1_inp, t1_ytp, t1_bp, _ = evaluate_lineup(p1, live_elements_gw, element_lookup_wire, club_mins_gw, pos_map_wire, team_map_wire, current_gw, all_fixtures)
            t2_start, t2_b, t2_live, _, t2_inp, t2_ytp, t2_bp, _ = evaluate_lineup(p2, live_elements_gw, element_lookup_wire, club_mins_gw, pos_map_wire, team_map_wire, current_gw, all_fixtures)

            act_s1 = s1 if m.get("finished", False) else t1_live
            act_s2 = s2 if m.get("finished", False) else t2_live

            if act_s1 > highest_score_val:
                highest_score_val = act_s1
                highest_scorer = (a1, act_s1)
            if act_s2 > highest_score_val:
                highest_score_val = act_s2
                highest_scorer = (a2, act_s2)

            margin = abs(act_s1 - act_s2)
            if act_s1 > 0 or act_s2 > 0:
                if margin < tightest_margin:
                    tightest_margin = margin
                    tightest_match = (a1, act_s1, a2, act_s2, margin)
                if margin > biggest_margin:
                    biggest_margin = margin
                    biggest_blowout = (a1 if act_s1 >= act_s2 else a2, max(act_s1, act_s2), a2 if act_s1 >= act_s2 else a1, min(act_s1, act_s2), margin)

            if t1_bp > highest_bench_pts:
                highest_bench_pts = t1_bp
                worst_benched = (a1, t1_bp, a2, act_s1, act_s2)
            if t2_bp > highest_bench_pts:
                highest_bench_pts = t2_bp
                worst_benched = (a2, t2_bp, a1, act_s2, act_s1)

            t1_cards_lost = (int(t1_start["YC"].sum()) if not t1_start.empty and "YC" in t1_start.columns else 0) + ((int(t1_start["RC"].sum()) if not t1_start.empty and "RC" in t1_start.columns else 0) * 3)
            t2_cards_lost = (int(t2_start["YC"].sum()) if not t2_start.empty and "YC" in t2_start.columns else 0) + ((int(t2_start["RC"].sum()) if not t2_start.empty and "RC" in t2_start.columns else 0) * 3)
            if t1_cards_lost > highest_card_penalty:
                highest_card_penalty = t1_cards_lost
                card_disaster = (a1, t1_cards_lost)
            if t2_cards_lost > highest_card_penalty:
                highest_card_penalty = t2_cards_lost
                card_disaster = (a2, t2_cards_lost)

            if (t1_inp + t1_ytp >= 2) and (t2_inp + t2_ytp == 0) and (act_s2 > act_s1):
                best_escape = (a1, act_s2 - act_s1, t1_inp + t1_ytp, a2)
            elif (t2_inp + t2_ytp >= 2) and (t1_inp + t1_ytp == 0) and (act_s1 > act_s2):
                best_escape = (a2, act_s1 - act_s2, t2_inp + t2_ytp, a1)

        if worst_benched and worst_benched[1] >= 4:
            wire_cards.append({
                "tag": "🪑 LEFT ON THE PINE",
                "color": "#a855f7",
                "headline": f"{worst_benched[0]} benched {worst_benched[1]} pts",
                "detail": f"Dugout haul stranded while trailing {worst_benched[2]}." if worst_benched[3] < worst_benched[4] else "Dugout haul left out of starting XI."
            })

        if card_disaster and card_disaster[1] >= 1:
            wire_cards.append({
                "tag": "🟨🟥 CARD CARNAGE",
                "color": "#f43f5e",
                "headline": f"{card_disaster[0]} docked -{card_disaster[1]} pts",
                "detail": "Starting XI card deductions hurting their gameweek total."
            })

        if best_escape:
            wire_cards.append({
                "tag": "🎯 THE GREAT ESCAPE",
                "color": "#38bdf8",
                "headline": f"{best_escape[0]} chasing {best_escape[1]} pts",
                "detail": f"{best_escape[2]} player(s) left to hunt down {best_escape[3]}."
            })

        if tightest_match:
            wire_cards.append({
                "tag": "🔥 ON A KNIFE EDGE",
                "color": "#f59e0b",
                "headline": f"{tightest_match[0]} vs {tightest_match[2]}",
                "detail": f"Deadlocked at {tightest_match[1]}–{tightest_match[3]} ({tightest_margin} pt margin)."
            })

        if biggest_blowout and biggest_blowout[4] >= 6:
            wire_cards.append({
                "tag": "🔨 DEMOLITION JOB",
                "color": "#ef4444",
                "headline": f"{biggest_blowout[0]} leads {biggest_blowout[2]}",
                "detail": f"Dominating {biggest_blowout[1]}–{biggest_blowout[3]} (+{biggest_margin} pt cushion)."
            })

        if highest_scorer and highest_scorer[1] > 0:
            wire_cards.append({
                "tag": "👑 BENCHMARK HAUL",
                "color": "#22c55e",
                "headline": f"{highest_scorer[0]} ({highest_scorer[1]} pts)",
                "detail": f"Division high score for Gameweek {current_gw} so far."
            })

    display_wire = wire_cards[:4]
    if display_wire:
        st.markdown(f"<p style='font-size:0.85rem; font-weight:800; text-transform:uppercase; color:#94a3b8; letter-spacing:0.6px; margin: 6px 0 4px 0;'>{top_wire_title}</p>", unsafe_allow_html = True)
        wire_cols = st.columns(len(display_wire))
        for w_idx, card in enumerate(display_wire):
            with wire_cols[w_idx]:
                st.markdown(f"""
                <div style="background-color: #0b0f19; border: 1px solid #1c2638; border-left: 3px solid {card['color']}; border-radius: 6px; padding: 6px 10px; margin-bottom: 8px;">
                    <span style="font-size:0.68rem; font-weight:900; color:{card['color']}; letter-spacing:0.5px;">{card['tag']}</span>
                    <div style="font-size:0.92rem; font-weight:800; color:#ffffff; margin: 1px 0;">{card['headline']}</div>
                    <div style="font-size:0.75rem; color:#94a3b8; font-weight:500;">{card['detail']}</div>
                </div>
                """, unsafe_allow_html = True)
# ----------------- HOME COMMUNITY PREDICTIONS (ALL 4 LEAGUES - STACKED) -----------------
    st.markdown("""
    <style>
    /* Keep prediction buttons side by side on mobile instead of stacking vertically */
    div[data-testid="stHorizontalBlock"]:has(button[key*="btn_pred_"]) {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 6px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(button[key*="btn_pred_"]) > div[data-testid="stColumn"] {
        width: auto !important;
        min-width: 0 !important;
        flex: 1 1 0 !important;
    }
    div[data-testid="stHorizontalBlock"]:has(button[key*="btn_pred_"]) > div[data-testid="stColumn"]:nth-child(2) {
        flex: 0 0 24px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(button[key*="btn_pred_"]) button {
        padding: 4px 6px !important;
        font-size: 0.85rem !important;
    }
    </style>
    """, unsafe_allow_html = True)

    st.markdown(
        f"<p style='font-size:0.95rem; font-weight:800; text-transform:uppercase; color:#94a3b8; letter-spacing:0.6px; margin: 16px 0 8px 0;'>🗳️ Community Match Predictions • Gameweek {current_gw}</p>", 
        unsafe_allow_html = True
    )

    current_voter = st.session_state.get("username") or logged_username or "guest"
    all_draft_preds = load_draft_predictions()

    all_leagues_info = [
        ("CDP (Crème Dellar Prem)", LEAGUE_PRESETS["CDP (Crème Dellar Prem)"], LEAGUE_THEMES["CDP (Crème Dellar Prem)"]["accent"]),
        ("SDM (Segundo Del Mundo)", LEAGUE_PRESETS["SDM (Segundo Del Mundo)"], LEAGUE_THEMES["SDM (Segundo Del Mundo)"]["accent"]),
        ("BDR (Best De La Rest)", LEAGUE_PRESETS["BDR (Best De La Rest)"], LEAGUE_THEMES["BDR (Best De La Rest)"]["accent"]),
        ("LDE (Liger Del Eager)", LEAGUE_PRESETS["LDE (Liger Del Eager)"], LEAGUE_THEMES["LDE (Liger Del Eager)"]["accent"])
    ]

    for l_name, l_id, l_color in all_leagues_info:
        l_details, _ = fetch_league_data(l_id)
        if not l_details:
            continue

        l_matches = l_details.get("matches", [])
        l_entries = l_details.get("league_entries", [])
        l_entry_map = {e["id"]: e for e in l_entries}
        
        gw_div_matches = [m for m in l_matches if m.get("event") == current_gw]
        if not gw_div_matches:
            continue

        st.markdown(f"<p style='font-size:0.80rem; font-weight:800; color:{l_color}; text-transform:uppercase; letter-spacing:0.5px; margin:12px 0 4px 0;'>{l_name}</p>", unsafe_allow_html = True)
        
        pred_cols = st.columns(len(gw_div_matches))

        for p_idx, m in enumerate(gw_div_matches):
            e1 = l_entry_map.get(m.get("league_entry_1"), {})
            e2 = l_entry_map.get(m.get("league_entry_2"), {})
            alias1 = get_manager_alias(e1.get("player_first_name", ""), e1.get("player_last_name", ""))
            alias2 = get_manager_alias(e2.get("player_first_name", ""), e2.get("player_last_name", ""))
            is_fin = m.get("finished", False)

            m_id = str(m.get("id", f"{m.get('league_entry_1')}_{m.get('league_entry_2')}"))
            m_votes = all_draft_preds.get(str(l_id), {}).get(str(current_gw), {}).get(m_id, {})
            my_vote = m_votes.get(current_voter)
            
            v_t1 = sum(1 for v in m_votes.values() if v == "1")
            v_t2 = sum(1 for v in m_votes.values() if v == "2")
            valid_votes = v_t1 + v_t2

            pct_t1 = int(round((v_t1 / valid_votes) * 100)) if valid_votes > 0 else 50
            pct_t2 = 100 - pct_t1 if valid_votes > 0 else 50
            vote_label = f"{valid_votes} vote" if valid_votes == 1 else f"{valid_votes} votes"

            with pred_cols[p_idx]:
                with st.container(border = True):
                    if not is_fin:
                        b_l, b_mid, b_r = st.columns([5, 2, 5])
                        with b_l:
                            btn_t1_type = "primary" if my_vote == "1" else "secondary"
                            if st.button(alias1, key = f"btn_pred_{l_id}_{current_gw}_{m_id}_1", use_container_width = True, type = btn_t1_type):
                                record_draft_prediction(l_id, current_gw, m_id, current_voter, "1")
                                load_draft_predictions.clear() if hasattr(load_draft_predictions, "clear") else None
                                st.rerun()
                        with b_mid:
                            st.markdown("<p style='text-align:center; color:#64748b; font-weight:800; font-size:0.75rem; margin:6px 0 0 0;'>vs</p>", unsafe_allow_html = True)
                        with b_r:
                            btn_t2_type = "primary" if my_vote == "2" else "secondary"
                            if st.button(alias2, key = f"btn_pred_{l_id}_{current_gw}_{m_id}_2", use_container_width = True, type = btn_t2_type):
                                record_draft_prediction(l_id, current_gw, m_id, current_voter, "2")
                                load_draft_predictions.clear() if hasattr(load_draft_predictions, "clear") else None
                                st.rerun()

                        col1_style = "#22c55e" if (valid_votes > 0 and pct_t1 > pct_t2) else ("#ffffff" if valid_votes > 0 else "#64748b")
                        col2_style = "#22c55e" if (valid_votes > 0 and pct_t2 > pct_t1) else ("#ffffff" if valid_votes > 0 else "#64748b")

                        # Anchored name and percentage columns with vote count in the center
                        st.markdown(
                            f"<div style='display:flex; justify-content:space-between; align-items:flex-end; padding:6px 2px 0 2px;'>"
                            f"  <div style='text-align:left;'>"
                            f"    <div style='font-size:0.75rem; font-weight:800; color:#94a3b8; text-transform:uppercase;'>{alias1}</div>"
                            f"    <div style='font-size:1.30rem; font-weight:900; color:{col1_style}; line-height:1.1;'>{pct_t1}%</div>"
                            f"  </div>"
                            f"  <div style='font-size:0.75rem; font-weight:600; color:#64748b; text-align:center; padding-bottom:2px;'>{vote_label}</div>"
                            f"  <div style='text-align:right;'>"
                            f"    <div style='font-size:0.75rem; font-weight:800; color:#94a3b8; text-transform:uppercase;'>{alias2}</div>"
                            f"    <div style='font-size:1.30rem; font-weight:900; color:{col2_style}; line-height:1.1;'>{pct_t2}%</div>"
                            f"  </div>"
                            f"</div>",
                            unsafe_allow_html = True
                        )
                    else:
                        st.markdown(
                            f"<div style='display:flex; justify-content:space-between; align-items:center; font-size:0.92rem; font-weight:800; color:#ffffff; padding:0 2px; margin-bottom:6px;'>"
                            f"  <span>{alias1}</span>"
                            f"  <span style='font-size:0.75rem; color:#475569; font-weight:800;'>vs</span>"
                            f"  <span>{alias2}</span>"
                            f"</div>"
                            f"<div style='display:flex; justify-content:space-between; align-items:flex-end; padding:2px 2px 0 2px;'>"
                            f"  <div style='text-align:left;'>"
                            f"    <div style='font-size:0.72rem; font-weight:700; color:#64748b; text-transform:uppercase;'>{alias1}</div>"
                            f"    <div style='font-size:1.15rem; font-weight:800; color:#94a3b8; line-height:1.1;'>{pct_t1}%</div>"
                            f"  </div>"
                            f"  <div style='font-size:0.74rem; font-weight:700; color:#64748b; text-align:center; padding-bottom:2px;'>{vote_label} • FINAL</div>"
                            f"  <div style='text-align:right;'>"
                            f"    <div style='font-size:0.72rem; font-weight:700; color:#64748b; text-transform:uppercase;'>{alias2}</div>"
                            f"    <div style='font-size:1.15rem; font-weight:800; color:#94a3b8; line-height:1.1;'>{pct_t2}%</div>"
                            f"  </div>"
                            f"</div>",
                            unsafe_allow_html = True
                        )
    # ----------------- COMPACT 4-DIVISION SHOWCASE -----------------
    with st.container():
        st.markdown("<div id='division-showcase'></div>", unsafe_allow_html = True)
        
        crest_map = {
            "CDP (Crème Dellar Prem)": assets_folder / "CDP_Crest.jpg",
            "SDM (Segundo Del Mundo)": assets_folder / "SDM_Crest.jpg",
            "BDR (Best De La Rest)": assets_folder / "BDR_Crest.jpg",
            "LDE (Liger Del Eager)": assets_folder / "LDE_Crest.jpg"
        }

        div_cols = st.columns(4)
        for idx, (l_key, l_theme) in enumerate(LEAGUE_THEMES.items()):
            short_code = l_key.split(" ")[0]
            crest_file = crest_map.get(l_key)
            is_current_active = (selected_league_key == l_key)

            with div_cols[idx]:
                with st.container(border = True):
                    if crest_file and crest_file.exists():
                        st.image(str(crest_file), use_container_width = True)
                    else:
                        st.markdown(f"<div style='height:80px; display:flex; align-items:center; justify-content:center; background:#06080d; font-size:1.5rem; font-weight:900; color:{l_theme['accent']};'>{short_code}</div>", unsafe_allow_html = True)
                    
                    st.markdown(f"<p style='text-align:center; font-weight:900; color:{l_theme['accent']}; margin:4px 0 0 0; font-size:1.0rem;'>{short_code}</p>", unsafe_allow_html = True)
                    st.markdown(f"<p style='text-align:center; font-size:0.75rem; color:#ffffff; margin:0 0 6px 0; font-weight:700; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{l_theme['tag']}</p>", unsafe_allow_html = True)
                    
                    if st.button(f"Enter {short_code}", key = f"btn_enter_{short_code}", use_container_width = True, type = "primary" if is_current_active else "secondary"):
                        st.session_state["active_competition"] = l_key
                        st.session_state.page = "LIVE SCORES"
                        st.rerun()

    # ----------------- STREAMLINED COMPACT LAUNCHPAD -----------------
    st.markdown("<p style='font-size:0.85rem; font-weight:800; text-transform:uppercase; color:#94a3b8; letter-spacing:0.6px; margin: 10px 0 4px 0;'>Command Center Navigation</p>", unsafe_allow_html = True)
    
    r1_c1, r1_c2, r1_c3, r1_c4, r1_c5 = st.columns(5)
    with r1_c1:
        st.button("🔴 LIVE SCORES", on_click = set_page, args = ("LIVE SCORES",), type = "primary", use_container_width = True)
    with r1_c2:
        st.button("⚽ EPL Scores & Lineups", on_click = set_page, args = ("EPL Scores & Lineups",), use_container_width = True)
    with r1_c3:
        st.button("Results Analyser", on_click = set_page, args = ("Results Analyser",), use_container_width = True)
    with r1_c4:
        st.button("Cup & Bucket", on_click = set_page, args = ("Cup & Bucket",), use_container_width = True)
    with r1_c5:
        st.button("📜 Asterisk*", on_click = set_page, args = ("Asterisk*",), use_container_width = True)

    r2_c1, r2_c2, r2_c3, r2_c4, r2_c5 = st.columns(5)
    with r2_c1:
        st.button("Squad Analyser", on_click = set_page, args = ("Squad Analyser",), use_container_width = True)
    with r2_c2:
        st.button("🤝 Trade Hub", on_click = set_page, args = ("Trade Hub",), use_container_width = True)
    with r2_c3:
        st.button("🎯 GACS", on_click = set_page, args = ("GACS",), use_container_width = True)
    with r2_c4:
        st.button("🟨🟥 Disciplinary", on_click = set_page, args = ("Disciplinary",), use_container_width = True)
    with r2_c5:
        st.button("Standings", on_click = set_page, args = ("Standings",), use_container_width = True)
# ----------------- 2. LIVE SCORES (MATCHDAY COMMAND CENTER) -----------------
elif st.session_state.page == "LIVE SCORES":
    st.title("🔴 LIVE SCORES" + dash + selected_league_key)
    
    static_data = fetch_fpl_static()
    league_details, _ = fetch_league_data(active_league_id)
    all_fixtures = fetch_all_epl_fixtures()
    
    if not static_data or not league_details:
        st.error("Failed to load live data. Verify connection.")
        st.stop()
        
    entries = league_details.get("league_entries", [])
    matches = league_details.get("matches", [])
    
    if not matches:
        st.warning("No matches found for this league.")
        st.stop()

    all_events = sorted(list({m["event"] for m in matches}))
    unplayed_events = sorted(list({m["event"] for m in matches if not m.get("finished", False)}))

    if unplayed_events:
        detected_gw = unplayed_events[0]
    else:
        detected_gw = all_events[-1] if all_events else 1

    lentry_map = {e["id"]: e for e in entries}
    pos_map = {item["id"]: item["singular_name_short"] for item in static_data["element_types"]}
    team_map = {item["id"]: item["short_name"] for item in static_data["teams"]}
    team_short_map = {item["id"]: item["short_name"] for item in static_data["teams"]}
    element_lookup = {item["id"]: item for item in static_data["elements"]}

    # Silent 45-second heartbeat fragment
    @st.fragment(run_every = "45s")
    def render_live_scores_board():
        top_c1, top_c2, top_c3 = st.columns([3, 2, 1])
        with top_c1:
            st.caption("Auto refreshes every 45s • Real time scorelines, live projections and win probability")
        with top_c2:
            current_gw = st.selectbox(
                "Active Gameweek",
                all_events,
                index = all_events.index(detected_gw) if detected_gw in all_events else 0,
                key = "live_gw_sel_box"
            )
        with top_c3:
            st.write("")
            if st.button("🔄 Refresh", use_container_width = True, key = "live_ref_btn"):
                fetch_entry_event.clear()
                fetch_live_event.clear()
                fetch_all_epl_fixtures.clear()
                st.rerun(scope = "fragment")

        live_data = fetch_live_event(current_gw)
        live_elements = live_data.get("elements", {}) if live_data else {}
        
        club_minutes = {}
        for elem_str_id, e_info in live_elements.items():
            try:
                elem_int_id = int(elem_str_id)
            except (ValueError, TypeError):
                continue
            elem_obj = element_lookup.get(elem_int_id, {})
            c_id = elem_obj.get("team")
            if c_id:
                m_val = e_info.get("stats", {}).get("minutes", 0)
                club_minutes[c_id] = club_minutes.get(c_id, 0) + m_val

        gw_matches = [m for m in matches if m["event"] == current_gw]
        
        if not gw_matches:
            st.info("No fixtures scheduled for Gameweek " + str(current_gw) + " yet.")
            return

        st.subheader("Around the Grounds (GW " + str(current_gw) + ")")
        
        match_summaries = []
        for m in gw_matches:
            e1 = lentry_map.get(m["league_entry_1"], {})
            e2 = lentry_map.get(m["league_entry_2"], {})
            is_fin = m.get("finished", False)
            
            p1 = fetch_entry_event(e1.get("entry_id"), current_gw)
            p2 = fetch_entry_event(e2.get("entry_id"), current_gw)
            
            t1_start, t1_b, t1_live, t1_proj, t1_in_play, t1_ytp, t1_bp, t1_opt = evaluate_lineup(p1, live_elements, element_lookup, club_minutes, pos_map, team_map, current_gw, all_fixtures)
            t2_start, t2_b, t2_live, t2_proj, t2_in_play, t2_ytp, t2_bp, t2_opt = evaluate_lineup(p2, live_elements, element_lookup, club_minutes, pos_map, team_map, current_gw, all_fixtures)
            
            if is_fin:
                t1_score = m.get("league_entry_1_points", t1_live)
                t2_score = m.get("league_entry_2_points", t2_live)
            else:
                t1_score = t1_live
                t2_score = t2_live
                
            prob1, prob2 = calculate_win_probability(t1_score, t1_proj, t1_in_play + t1_ytp, t2_score, t2_proj, t2_in_play + t2_ytp, is_fin)
            
            match_summaries.append({
                "match": m,
                "e1": e1,
                "e2": e2,
                "t1_score": t1_score,
                "t2_score": t2_score,
                "t1_proj": t1_proj,
                "t2_proj": t2_proj,
                "t1_in_play": t1_in_play,
                "t1_ytp": t1_ytp,
                "t2_in_play": t2_in_play,
                "t2_ytp": t2_ytp,
                "t1_bp": t1_bp,
                "t1_opt": t1_opt,
                "t2_bp": t2_bp,
                "t2_opt": t2_opt,
                "prob1": prob1,
                "prob2": prob2,
                "is_fin": is_fin,
                "t1_start": t1_start,
                "t1_b": t1_b,
                "t2_start": t2_start,
                "t2_b": t2_b
            })

        for idx in range(0, len(match_summaries), 2):
            grid_c1, grid_c2 = st.columns(2)
            items = [match_summaries[idx]]
            if idx + 1 < len(match_summaries):
                items.append(match_summaries[idx + 1])
                
            cols = [grid_c1, grid_c2]
            for c_idx, item in enumerate(items):
                with cols[c_idx]:
                    with st.container(border = True):
                        status_badge = "✅ FINAL" if item["is_fin"] else "🟢 LIVE"
                        alias1 = get_manager_alias(item["e1"].get("player_first_name", ""), item["e1"].get("player_last_name", ""))
                        alias2 = get_manager_alias(item["e2"].get("player_first_name", ""), item["e2"].get("player_last_name", ""))
                        
                        hdr_l, hdr_r = st.columns([3, 1])
                        with hdr_l:
                            st.markdown(f"<div class='card-mgr-title'>{alias1} vs {alias2}</div>", unsafe_allow_html = True)
                        with hdr_r:
                            st.markdown(f"<p class='card-status-badge' style='color: {active_theme['accent']};'><b>{status_badge}</b></p>", unsafe_allow_html = True)
                            
                        t1_rem_text = format_remaining_players(item["t1_in_play"], item["t1_ytp"])
                        t2_rem_text = format_remaining_players(item["t2_in_play"], item["t2_ytp"])

                        sc_col1, sc_col2, sc_col3 = st.columns([5, 1, 5])
                        with sc_col1:
                            st.markdown(f"<div style='font-size:0.95rem; font-weight:800; color:{active_theme['accent']}; text-transform:uppercase; letter-spacing:0.5px;'>{alias1}</div>", unsafe_allow_html = True)
                            st.markdown(f"<div class='card-score-left'>{item['t1_score']}</div>", unsafe_allow_html = True)
                            st.markdown(f"<p class='card-proj-sub'>Proj: {item['t1_proj']:.1f} ({t1_rem_text})</p>", unsafe_allow_html = True)
                            st.markdown(f"<p class='card-bench-sub'>Bench: {item['t1_bp']} pts | Opt: {item['t1_opt']} pts</p>", unsafe_allow_html = True)
                        with sc_col2:
                            st.markdown("<div class='card-vs-text' style='margin-top:22px !important;'>vs</div>", unsafe_allow_html = True)
                        with sc_col3:
                            st.markdown(f"<div style='font-size:0.95rem; font-weight:800; color:#38bdf8; text-transform:uppercase; letter-spacing:0.5px; text-align:right;'>{alias2}</div>", unsafe_allow_html = True)
                            st.markdown(f"<div class='card-score-right'>{item['t2_score']}</div>", unsafe_allow_html = True)
                            st.markdown(f"<p class='card-proj-sub' style='text-align: right;'>Proj: {item['t2_proj']:.1f} ({t2_rem_text})</p>", unsafe_allow_html = True)
                            st.markdown(f"<p class='card-bench-sub' style='text-align: right;'>Bench: {item['t2_bp']} pts | Opt: {item['t2_opt']} pts</p>", unsafe_allow_html = True)
                        
                        st.progress(item["prob1"] / 100.0)
                        
                        if item["prob1"] > item["prob2"]:
                            col1_style = active_theme["accent"]
                            col2_style = "#94a3b8"
                        elif item["prob2"] > item["prob1"]:
                            col1_style = "#94a3b8"
                            col2_style = active_theme["accent"]
                        else:
                            col1_style = "#cbd5e1"
                            col2_style = "#cbd5e1"

                        p_l, p_r = st.columns(2)
                        with p_l:
                            st.markdown(f"<span class='card-win-pct' style='color: {col1_style};'>Win: {item['prob1']}%</span>", unsafe_allow_html = True)
                        with p_r:
                            st.markdown(f"<p class='card-win-pct' style='text-align: right; margin: 0; color: {col2_style};'>Win: {item['prob2']}%</p>", unsafe_allow_html = True)


        st.divider()

        st.subheader("Match Spotlight and Lineup Breakdown")
        
        def spot_label(i):
            item = match_summaries[i]
            a1 = get_manager_alias(item["e1"].get("player_first_name", ""), item["e1"].get("player_last_name", ""))
            a2 = get_manager_alias(item["e2"].get("player_first_name", ""), item["e2"].get("player_last_name", ""))
            return f"{a1} ({item['t1_score']}) vs ({item['t2_score']}) {a2}"

        spotlight_idx = st.selectbox(
            "Inspect Matchup Details",
            range(len(match_summaries)),
            format_func = lambda i: spot_label(i),
            key = "spotlight_match_sel"
        )
        
        active_spot = match_summaries[spotlight_idx]
        alias_e1 = get_manager_alias(active_spot["e1"].get("player_first_name", ""), active_spot["e1"].get("player_last_name", ""))
        alias_e2 = get_manager_alias(active_spot["e2"].get("player_first_name", ""), active_spot["e2"].get("player_last_name", ""))

        render_progression_chart(
            current_gw,
            alias_e1,
            alias_e2,
            active_spot["t1_start"],
            active_spot["t1_b"],
            active_spot["t2_start"],
            active_spot["t2_b"],
            all_fixtures,
            team_short_map,
            active_theme["accent"]
        )
        st.divider()
        
        s_c1, s_c2 = st.columns(2)

        with s_c1:
            render_lineup_container(
                alias_e1,
                active_spot["t1_start"],
                active_spot["t1_b"],
                active_spot["t1_bp"],
                active_spot["t1_opt"],
                active_theme["accent"],
                large_mode,
                score = active_spot["t1_score"]
            )

        with s_c2:
            render_lineup_container(
                alias_e2,
                active_spot["t2_start"],
                active_spot["t2_b"],
                active_spot["t2_bp"],
                active_spot["t2_opt"],
                active_theme["accent"],
                large_mode,
                score = active_spot["t2_score"]
            )

    render_live_scores_board()

# ----------------- 3. 🏆 CUP & BUCKET COMPETITION -----------------
elif st.session_state.page == "Cup & Bucket":
    st.title("🏆 Cup & Bucket Competition")
    st.caption("32 Team Inter League Cup • CDP, SDM, BDR and LDE")

    cup_df = load_cup_matches()
    static_data = fetch_fpl_static()
    all_fixtures = fetch_all_epl_fixtures()
    league_details, _ = fetch_league_data(active_league_id)

    if cup_df is None or cup_df.empty:
        st.warning("No 'cupmatches' spreadsheet found. Place 'cupmatches.xlsx', '.ods' or '.csv' in your Assets folder.")
        st.stop()

    if not static_data:
        st.error("Error connecting to Premier League API.")
        st.stop()

    pos_map = {item["id"]: item["singular_name_short"] for item in static_data["element_types"]}
    team_map = {item["id"]: item["short_name"] for item in static_data["teams"]}
    team_short_map = {item["id"]: item["short_name"] for item in static_data["teams"]}
    element_lookup = {item["id"]: item for item in static_data["elements"]}

    teams_registry = get_all_32_teams_registry()

    cup_df.columns = [str(c).strip().title() for c in cup_df.columns]
    cup_df["Week"] = pd.to_numeric(cup_df["Week"], errors = "coerce").fillna(0).astype(int)

    all_cup_gws = sorted([int(w) for w in cup_df["Week"].unique() if pd.notna(w) and int(w) > 0])

    # Determine current active gameweek to default selections
    matches = league_details.get("matches", []) if league_details else []
    all_events = sorted(list({m["event"] for m in matches})) if matches else list(range(1, 39))
    unplayed_events = sorted(list({m["event"] for m in matches if not m.get("finished", False)})) if matches else []
    current_gw = unplayed_events[0] if unplayed_events else (all_events[-1] if all_events else 1)

    # Smart default: If current_gw is a Cup round, show it.
    # Otherwise, stay locked to the most recent completed Cup round (e.g. in GW 9, stays on GW 8)
    if current_gw in all_cup_gws:
        target_default_cup_gw = current_gw
    else:
        past_cup_gws = [w for w in all_cup_gws if w <= current_gw]
        target_default_cup_gw = max(past_cup_gws) if past_cup_gws else all_cup_gws[0]

    default_cup_gw_idx = all_cup_gws.index(target_default_cup_gw) if target_default_cup_gw in all_cup_gws else 0

    cup_tab_live, cup_tab_standings, cup_tab_analyser = st.tabs([
        "🔴 Live Cup Matchday",
        "📊 32 Team Group Standings",
        "📋 Cup Results Analyser"
    ])

    with cup_tab_live:
        @st.fragment(run_every = "45s")
        def render_live_cup_board():
            top_m1, top_m2, top_m3 = st.columns([3, 2, 1])
            with top_m1:
                st.caption("Auto refreshes every 45s • Around the Grounds live inter league cup matches with live auto subs")
            with top_m2:
                active_cup_gw = st.selectbox("Select Cup Gameweek", all_cup_gws, index = default_cup_gw_idx, key = "cup_live_gw_sel")
            with top_m3:
                st.write("")
                if st.button("🔄 Refresh Cup", use_container_width = True, key = "cup_ref_btn"):
                    fetch_entry_event.clear()
                    fetch_live_event.clear()
                    fetch_all_epl_fixtures.clear()
                    resolve_cup_match_score.clear()
                    calculate_group_standings.clear()
                    st.rerun(scope = "fragment")

            gw_cup_matches = cup_df[cup_df["Week"] == active_cup_gw].copy()

            if gw_cup_matches.empty:
                st.info(f"No cup matches scheduled for Gameweek {active_cup_gw}.")
                return

            gw_epl_fixtures = [f for f in all_fixtures if f.get("event") == active_cup_gw] if all_fixtures else []
            gw_officially_finished = all(f.get("finished", False) for f in gw_epl_fixtures) if gw_epl_fixtures else False

            # Pre-fetch all 32 managers in parallel with ThreadPoolExecutor
            round_managers = set()
            for _, r in gw_cup_matches.iterrows():
                t1_val = str(r.get("Team 1", "")).strip()
                t2_val = str(r.get("Team 2", "")).strip()
                if t1_val and t1_val.lower() != "nan":
                    round_managers.add(t1_val)
                if t2_val and t2_val.lower() != "nan":
                    round_managers.add(t2_val)

            manager_scores_cache = {}
            with st.spinner(f"Loading Cup & Bucket Gameweek {active_cup_gw} scores..."):
                with ThreadPoolExecutor(max_workers = 10) as executor:
                    future_to_mgr = {executor.submit(resolve_cup_match_score, m, active_cup_gw): m for m in round_managers}
                    for future in future_to_mgr:
                        mgr = future_to_mgr[future]
                        try:
                            manager_scores_cache[mgr] = future.result()
                        except Exception:
                            manager_scores_cache[mgr] = {
                                "score": 0, "proj": 0.0, "high_player": 0,
                                "starters": pd.DataFrame(), "bench": pd.DataFrame(),
                                "in_play": 0, "ytp": 0, "bench_pts": 0, "opt": 0
                            }

            empty_score_fallback = {
                "score": 0, "proj": 0.0, "high_player": 0,
                "starters": pd.DataFrame(), "bench": pd.DataFrame(),
                "in_play": 0, "ytp": 0, "bench_pts": 0, "opt": 0
            }

            live_cup_cards = []
            for _, r in gw_cup_matches.iterrows():
                m1_alias = str(r.get("Team 1", "")).strip()
                m2_alias = str(r.get("Team 2", "")).strip()
                if not m1_alias or not m2_alias or m1_alias.lower() == "nan" or m2_alias.lower() == "nan":
                    continue

                r1 = manager_scores_cache.get(m1_alias, empty_score_fallback)
                r2 = manager_scores_cache.get(m2_alias, empty_score_fallback)

                info1 = teams_registry.get(m1_alias.lower(), {})
                info2 = teams_registry.get(m2_alias.lower(), {})

                is_fin = gw_officially_finished and (r1["in_play"] + r1["ytp"] + r2["in_play"] + r2["ytp"] == 0) and (r1["score"] > 0 or r2["score"] > 0)
                prob1, prob2 = calculate_win_probability(r1["score"], r1["proj"], r1["in_play"] + r1["ytp"], r2["score"], r2["proj"], r2["in_play"] + r2["ytp"], is_fin)

                live_cup_cards.append({
                    "m1": m1_alias,
                    "m2": m2_alias,
                    "t1_name": info1.get("team_name", "Team 1"),
                    "t2_name": info2.get("team_name", "Team 2"),
                    "l1": info1.get("league_key", "").split(" ")[0],
                    "l2": info2.get("league_key", "").split(" ")[0],
                    "s1": r1["score"],
                    "s2": r2["score"],
                    "proj1": r1["proj"],
                    "proj2": r2["proj"],
                    "inp1": r1["in_play"],
                    "ytp1": r1["ytp"],
                    "inp2": r2["in_play"],
                    "ytp2": r2["ytp"],
                    "bp1": r1["bench_pts"],
                    "opt1": r1["opt"],
                    "bp2": r2["bench_pts"],
                    "opt2": r2["opt"],
                    "prob1": prob1,
                    "prob2": prob2,
                    "is_fin": is_fin,
                    "comp": r.get("Comp", "Cup"),
                    "stage": r.get("Stage", ""),
                    "leg": r.get("Leg", "")
                })

            for idx in range(0, len(live_cup_cards), 2):
                col_c1, col_c2 = st.columns(2)
                pair = [live_cup_cards[idx]]
                if idx + 1 < len(live_cup_cards):
                    pair.append(live_cup_cards[idx + 1])
                cols = [col_c1, col_c2]
                for c_i, card in enumerate(pair):
                    with cols[c_i]:
                        with st.container(border = True):
                            hdr_l, hdr_r = st.columns([3, 1])
                            with hdr_l:
                                st.markdown(f"<div class='card-mgr-title'>{card['m1']} <span class='card-div-tag'>({card['l1']})</span> vs {card['m2']} <span class='card-div-tag'>({card['l2']})</span></div>", unsafe_allow_html = True)
                            with hdr_r:
                                stage_tag = f"{card['stage']} {card['leg']}".strip()
                                st.markdown(f"<p class='card-status-badge' style='color: {active_theme['accent']};'><b>{stage_tag}</b></p>", unsafe_allow_html = True)

                            rem1 = format_remaining_players(card["inp1"], card["ytp1"])
                            rem2 = format_remaining_players(card["inp2"], card["ytp2"])

                            sc1, sc2, sc3 = st.columns([5, 1, 5])
                            with sc1:
                                st.markdown(f"<div style='font-size:0.95rem; font-weight:800; color:{active_theme['accent']}; text-transform:uppercase; letter-spacing:0.5px;'>{card['m1']}</div>", unsafe_allow_html = True)
                                st.markdown(f"<div class='card-score-left'>{card['s1']}</div>", unsafe_allow_html = True)
                                st.markdown(f"<p class='card-proj-sub'>Proj: {card['proj1']:.1f} ({rem1})</p>", unsafe_allow_html = True)
                                st.markdown(f"<p class='card-bench-sub'>Bench: {card['bp1']} pts | Opt: {card['opt1']} pts</p>", unsafe_allow_html = True)
                            with sc2:
                                st.markdown("<div class='card-vs-text' style='margin-top:22px !important;'>vs</div>", unsafe_allow_html = True)
                            with sc3:
                                st.markdown(f"<div style='font-size:0.95rem; font-weight:800; color:#38bdf8; text-transform:uppercase; letter-spacing:0.5px; text-align:right;'>{card['m2']}</div>", unsafe_allow_html = True)
                                st.markdown(f"<div class='card-score-right'>{card['s2']}</div>", unsafe_allow_html = True)
                                st.markdown(f"<p class='card-proj-sub' style='text-align: right;'>Proj: {card['proj2']:.1f} ({rem2})</p>", unsafe_allow_html = True)
                                st.markdown(f"<p class='card-bench-sub' style='text-align: right;'>Bench: {card['bp2']} pts | Opt: {card['opt2']} pts</p>", unsafe_allow_html = True)

                            st.progress(card["prob1"] / 100.0)

                            if card["prob1"] > card["prob2"]:
                                c1_style = active_theme["accent"]
                                c2_style = "#94a3b8"
                            elif card["prob2"] > card["prob1"]:
                                c1_style = "#94a3b8"
                                c2_style = active_theme["accent"]
                            else:
                                c1_style = "#cbd5e1"
                                c2_style = "#cbd5e1"

                            pl_c, pr_c = st.columns(2)
                            with pl_c:
                                st.markdown(f"<span class='card-win-pct' style='color: {c1_style};'>Win: {card['prob1']}%</span>", unsafe_allow_html = True)
                            with pr_c:
                                st.markdown(f"<p class='card-win-pct' style='text-align: right; margin: 0; color: {c2_style};'>Win: {card['prob2']}%</p>", unsafe_allow_html = True)

            st.divider()
            st.subheader("Match Spotlight and Lineup Breakdown")

            valid_spotlight_cards = [c for c in live_cup_cards if c["m1"] and c["m2"] and c["m1"].lower() != "nan" and c["m2"].lower() != "nan"]

            if valid_spotlight_cards:
                def cup_spot_label(i):
                    c = valid_spotlight_cards[i]
                    stage_str = f"{c['stage']} {c['leg']}".strip()
                    return f"{c['m1']} ({c['s1']}) vs ({c['s2']}) {c['m2']} ({stage_str})"

                c_spot_idx = st.selectbox("Inspect Cup Matchup Details", range(len(valid_spotlight_cards)), format_func = cup_spot_label, key = "cup_spot_sel")
                active_c_spot = valid_spotlight_cards[c_spot_idx]

                spot_m1 = active_c_spot["m1"]
                spot_m2 = active_c_spot["m2"]

                sp1 = resolve_cup_match_score(spot_m1, active_cup_gw)
                sp2 = resolve_cup_match_score(spot_m2, active_cup_gw)
                spot_s1, spot_st1, spot_b1, spot_bp1, spot_opt1 = sp1["score"], sp1["starters"], sp1["bench"], sp1["bench_pts"], sp1["opt"]
                spot_s2, spot_st2, spot_b2, spot_bp2, spot_opt2 = sp2["score"], sp2["starters"], sp2["bench"], sp2["bench_pts"], sp2["opt"]

                s_info1 = teams_registry.get(spot_m1.lower(), {})
                s_info2 = teams_registry.get(spot_m2.lower(), {})

                st.divider()
                sr1, sr2, sr3 = st.columns([4, 2, 4])
                with sr1:
                    st.markdown(f"### {spot_m1} ({spot_s1} pts)")
                    st.caption(f"{s_info1.get('team_name', '')} • {s_info1.get('league_key', '')}")
                with sr2:
                    st.markdown(f"<div class='card-score-center'>{spot_s1} {dash} {spot_s2}</div>", unsafe_allow_html = True)
                    st.markdown(f"<p style='text-align: center; color: #94a3b8; margin: 4px 0 0 0; font-weight: bold;'>{active_c_spot['stage']} {active_c_spot['leg']} (GW {active_cup_gw})</p>", unsafe_allow_html = True)
                with sr3:
                    st.markdown(f"<h3 style='text-align: right;'>{spot_m2} ({spot_s2} pts)</h3>", unsafe_allow_html = True)
                    st.markdown(f"<p style='text-align: right; color: #94a3b8; margin: 0;'>{s_info2.get('team_name', '')} • {s_info2.get('league_key', '')}</p>", unsafe_allow_html = True)
                st.divider()

                render_progression_chart(
                    active_cup_gw,
                    spot_m1,
                    spot_m2,
                    spot_st1,
                    spot_b1,
                    spot_st2,
                    spot_b2,
                    all_fixtures,
                    team_short_map,
                    active_theme["accent"]
                )
                st.divider()

                side1_c, side2_c = st.columns(2)
                with side1_c:
                    render_lineup_container(
                        spot_m1,
                        spot_st1,
                        spot_b1,
                        spot_bp1,
                        spot_opt1,
                        active_theme["accent"],
                        large_mode,
                        score = spot_s1
                    )

                with side2_c:
                    render_lineup_container(
                        spot_m2,
                        spot_st2,
                        spot_b2,
                        spot_bp2,
                        spot_opt2,
                        active_theme["accent"],
                        large_mode,
                        score = spot_s2
                    )

        render_live_cup_board()

    with cup_tab_standings:
        st.subheader("Combined 32 Team Group Standings (GW 6 to GW 20)")
        st.caption("Tiebreaker Hierarchy: 1. Points → 2. Player Points (PF) → 3. Head to Head → 4. Highest Individual Player Score in Group Stage")

        with st.spinner("Calculating group standings across 8 matchdays..."):
            display_table = calculate_group_standings()

        if display_table:
            table_df = pd.DataFrame(display_table)
            st.table(table_df.set_index("Pos"))
        else:
            st.info("Group standings calculations unavailable.")

    with cup_tab_analyser:
        st.subheader("📋 Cup Results Analyser")
        st.caption("Inspect cross league matchday lineups, key events and match progression charts")

        group_matches_temp = cup_df[(cup_df["Week"] <= 20) & (cup_df["Stage"].str.lower().str.contains("group"))].copy()
        unique_aliases_temp = set()
        for _, r in group_matches_temp.iterrows():
            m1 = str(r.get("Team 1", "")).strip()
            m2 = str(r.get("Team 2", "")).strip()
            if m1 and m1.lower() != "nan":
                unique_aliases_temp.add(m1)
            if m2 and m2.lower() != "nan":
                unique_aliases_temp.add(m2)

        c_col1, c_col2 = st.columns([1, 2])
        with c_col1:
            cup_view_mode = st.radio("Browse Cup Fixtures", ["By Gameweek", "By Manager"], horizontal = True, key = "c_view_mode")

        selected_cup_match = None

        if cup_view_mode == "By Gameweek":
            with c_col2:
                chosen_c_gw = st.selectbox("Select Gameweek", all_cup_gws, index = default_cup_gw_idx, key = "c_gw_picker")
            gw_matches_df = cup_df[cup_df["Week"] == chosen_c_gw].copy()
            gw_matches_df = gw_matches_df[gw_matches_df["Team 1"].notna() & gw_matches_df["Team 2"].notna()]

            def cup_match_label(idx):
                row = gw_matches_df.iloc[idx]
                m1 = str(row["Team 1"]).strip()
                m2 = str(row["Team 2"]).strip()
                stage = f"{row.get('Stage', '')} {row.get('Leg', '')}".strip()
                return f"{m1} vs {m2} ({stage})"

            if not gw_matches_df.empty:
                m_sel_idx = st.selectbox("Select Matchup", range(len(gw_matches_df)), format_func = cup_match_label, key = "c_m_sel")
                selected_cup_match = gw_matches_df.iloc[m_sel_idx]
            else:
                st.info("No fixtures found for this gameweek.")
        else:
            all_cup_managers = sorted(list(unique_aliases_temp))
            with c_col2:
                chosen_mgr = st.selectbox("Select Manager", all_cup_managers, key = "c_mgr_picker")
            mgr_matches_df = cup_df[(cup_df["Team 1"] == chosen_mgr) | (cup_df["Team 2"] == chosen_mgr)].copy()
            mgr_matches_df = mgr_matches_df.sort_values(by = "Week")

            def cup_mgr_label(idx):
                row = mgr_matches_df.iloc[idx]
                m1 = str(row["Team 1"]).strip()
                m2 = str(row["Team 2"]).strip()
                return f"GW {row['Week']}: {m1} vs {m2} ({row.get('Stage', '')})"

            if not mgr_matches_df.empty:
                mgr_m_idx = st.selectbox("Select Matchup", range(len(mgr_matches_df)), format_func = cup_mgr_label, key = "c_mgr_m_sel")
                selected_cup_match = mgr_matches_df.iloc[mgr_m_idx]

        if selected_cup_match is not None:
            c_gw = int(selected_cup_match["Week"])
            c_m1 = str(selected_cup_match["Team 1"]).strip()
            c_m2 = str(selected_cup_match["Team 2"]).strip()

            cp1 = resolve_cup_match_score(c_m1, c_gw)
            cp2 = resolve_cup_match_score(c_m2, c_gw)
            c_s1, c_st1, c_b1, c_bp1, c_opt1 = cp1["score"], cp1["starters"], cp1["bench"], cp1["bench_pts"], cp1["opt"]
            c_s2, c_st2, c_b2, c_bp2, c_opt2 = cp2["score"], cp2["starters"], cp2["bench"], cp2["bench_pts"], cp2["opt"]

            info1 = teams_registry.get(c_m1.lower(), {})
            info2 = teams_registry.get(c_m2.lower(), {})

            st.divider()
            r1, r2, r3 = st.columns([4, 2, 4])
            with r1:
                st.markdown(f"### {c_m1} ({c_s1} pts)")
                st.caption(f"{info1.get('team_name', '')} • {info1.get('league_key', '')}")
            with r2:
                st.markdown(f"<div class='card-score-center'>{c_s1} {dash} {c_s2}</div>", unsafe_allow_html = True)
                stage_desc = f"{selected_cup_match.get('Comp', 'Cup')} {selected_cup_match.get('Stage', '')} {selected_cup_match.get('Leg', '')}".strip()
                st.markdown(f"<p style='text-align: center; color: #94a3b8; margin: 4px 0 0 0; font-weight: bold;'>{stage_desc} (GW {c_gw})</p>", unsafe_allow_html = True)
            with r3:
                st.markdown(f"<h3 style='text-align: right;'>{c_m2} ({c_s2} pts)</h3>", unsafe_allow_html = True)
                st.markdown(f"<p style='text-align: right; color: #94a3b8; margin: 0;'>{info2.get('team_name', '')} • {info2.get('league_key', '')}</p>", unsafe_allow_html = True)
            st.divider()

            st.caption(f"{c_m1} — Bench Left: {c_bp1} pts | Optimum Score: {c_opt1} pts   |   {c_m2} — Bench Left: {c_bp2} pts | Optimum Score: {c_opt2} pts")

            render_progression_chart(
                c_gw,
                c_m1,
                c_m2,
                c_st1,
                c_b1,
                c_st2,
                c_b2,
                all_fixtures,
                team_short_map,
                active_theme["accent"]
            )
            st.divider()

            side1, side2 = st.columns(2)
            with side1:
                render_lineup_container(
                    c_m1,
                    c_st1,
                    c_b1,
                    c_bp1,
                    c_opt1,
                    active_theme["accent"],
                    large_mode,
                    score = c_s1
                )

            with side2:
                render_lineup_container(
                    c_m2,
                    c_st2,
                    c_b2,
                    c_bp2,
                    c_opt2,
                    active_theme["accent"],
                    large_mode,
                    score = c_s2
                )
# ----------------- 4. EPL SCORES & LINEUPS SECTION -----------------
elif st.session_state.page in ["EPL Scores", "EPL SCORES", "EPL Scores & Lineups"]:
    st.title("⚽ EPL Scores & Lineups")
    
    static_data = fetch_fpl_static()
    league_details, _ = fetch_league_data(active_league_id)
    
    if not static_data:
        st.error("Failed to load Premier League data. Verify connection.")
        st.stop()
        
    team_name_map = {item["id"]: item["name"] for item in static_data["teams"]}
    team_short_map = {item["id"]: item["short_name"] for item in static_data["teams"]}
    element_lookup = {item["id"]: item for item in static_data["elements"]}
    
    matches = league_details.get("matches", []) if league_details else []
    all_gws = sorted(list({m["event"] for m in matches})) if matches else list(range(1, 39))
    unplayed_events = sorted(list({m["event"] for m in matches if not m.get("finished", False)})) if matches else []
    
    if unplayed_events:
        default_epl_gw = unplayed_events[0]
    else:
        curr_from_static = next((ev.get("id") for ev in static_data.get("events", []) if ev.get("is_current")), 1)
        default_epl_gw = curr_from_static if curr_from_static else (all_gws[-1] if all_gws else 1)

    top_e1, top_e2, top_e3 = st.columns([3, 2, 1])
    with top_e1:
        st.caption("Official team sheets published 60–75m before kickoff • Live matchday scores, active subs, goals and DEFCON metrics")
    with top_e2:
        selected_epl_gw = st.selectbox(
            "Select EPL Gameweek",
            all_gws,
            index = all_gws.index(default_epl_gw) if default_epl_gw in all_gws else 0
        )
    with top_e3:
        st.write("")
        if st.button("🔄 Refresh EPL", use_container_width = True):
            fetch_epl_fixtures.clear()
            fetch_live_event.clear()
            get_pulse_active_fixtures_list.clear()
            fetch_pulse_fixture_details.clear()
            get_espn_scoreboard.clear()
            fetch_espn_fixture_summary.clear()
            fetch_premier_league_match_lineup.clear()
            st.rerun()

    fixtures = fetch_epl_fixtures(selected_epl_gw)
    live_event_data = fetch_live_event(selected_epl_gw)
    live_elements = live_event_data.get("elements", {}) if live_event_data else {}

    if not fixtures:
        st.info("No fixtures available for Gameweek " + str(selected_epl_gw) + ".")
        st.stop()

    st.subheader(f"Premier League Matches • GW {selected_epl_gw}")

    lineups_by_fix_id = {}
    with st.spinner(f"Loading Gameweek {selected_epl_gw} matchday data and team sheets..."):
        def load_lineup_for_fix(f_obj):
            h_tid = f_obj.get("team_h")
            a_tid = f_obj.get("team_a")
            h_st = team_short_map.get(h_tid, "H")
            a_st = team_short_map.get(a_tid, "A")
            is_fin = f_obj.get("finished", False) or f_obj.get("finished_provisional", False)
            is_start = f_obj.get("started", False)
            m_mins = f_obj.get("minutes", 90 if is_fin else 45)

            sheet = fetch_premier_league_match_lineup(
                fpl_fixture_code = f_obj.get("code"),
                home_team_id = h_tid,
                away_team_id = a_tid,
                live_elements = live_elements,
                element_lookup = element_lookup,
                match_minute = m_mins,
                event_num = selected_epl_gw,
                home_short = h_st,
                away_short = a_st,
                kickoff_time = f_obj.get("kickoff_time"),
                is_started = is_start,
                is_finished = is_fin
            )
            return f_obj.get("id"), sheet

        with ThreadPoolExecutor(max_workers = 10) as executor:
            results = executor.map(load_lineup_for_fix, fixtures)
            for fix_id, sheet_res in results:
                lineups_by_fix_id[fix_id] = sheet_res
    for f in fixtures:
        h_id = f.get("team_h")
        a_id = f.get("team_a")
        h_name = team_name_map.get(h_id, "Home Team")
        a_name = team_name_map.get(a_id, "Away Team")
        h_short = team_short_map.get(h_id, "H")
        a_short = team_short_map.get(a_id, "A")
        
        is_finished = f.get("finished", False) or f.get("finished_provisional", False)
        is_started = f.get("started", False)
        h_score = f.get("team_h_score")
        a_score = f.get("team_a_score")
        pulse_code = f.get("code")
        
        if is_finished:
            status_text = "FT"
            status_color = "#94a3b8"
        elif is_started:
            mins_val = f.get("minutes", 0)
            status_text = f"LIVE {mins_val}'"
            status_color = active_theme["accent"]
        else:
            kickoff = f.get("kickoff_time")
            if kickoff:
                try:
                    dt = pd.to_datetime(kickoff)
                    status_text = dt.strftime("%a %d %b, %H:%M")
                except Exception:
                    status_text = kickoff[11:16]
            else:
                status_text = "Upcoming"
            status_color = "#cbd5e1"

        with st.container(border = True):
            f_col1, f_col2, f_col3 = st.columns([4, 3, 4])
            with f_col1:
                st.markdown(f"<div class='card-mgr-title'>{h_name} <span class='card-div-tag'>({h_short})</span></div>", unsafe_allow_html = True)
            with f_col2:
                if is_started or is_finished:
                    st.markdown(f"<div class='card-score-center'>{h_score} {dash} {a_score}</div>", unsafe_allow_html = True)
                else:
                    st.markdown("<div class='card-vs-text'>vs</div>", unsafe_allow_html = True)
                st.markdown(f"<p class='card-status-badge' style='text-align: center; color: {status_color};'>{status_text}</p>", unsafe_allow_html = True)
            with f_col3:
                st.markdown(f"<div class='card-mgr-title' style='text-align: right;'><span class='card-div-tag'>({a_short})</span> {a_name}</div>", unsafe_allow_html = True)

            with st.expander("📋 Match Events & Confirmed Lineups"):
                tab_events, tab_sheets, tab_bps, tab_defcon = st.tabs(["⚡ Match Stats", "👥 Lineups & Subs", "⭐ BPS & Bonus", "🔰 DefCon"])

                with tab_events:
                    stats_raw = f.get("stats", [])
                    stats_dict = {item["identifier"]: {"h": item.get("h", []), "a": item.get("a", [])} for item in stats_raw}

                    def get_stat_entries(ident, side):
                        raw_list = stats_dict.get(ident, {}).get(side, [])
                        items = []
                        for entry in raw_list:
                            p_elem = element_lookup.get(entry["element"], {})
                            p_name = p_elem.get("web_name", "Unknown")
                            val = entry.get("value", 1)
                            items.append((p_name, val))
                        return items

                    h_goals = get_stat_entries("goals_scored", "h")
                    h_assists = get_stat_entries("assists", "h")
                    h_saves = get_stat_entries("saves", "h")
                    h_og = get_stat_entries("own_goals", "h")
                    h_pmiss = get_stat_entries("penalties_missed", "h")
                    h_psaved = get_stat_entries("penalties_saved", "h")

                    a_goals = get_stat_entries("goals_scored", "a")
                    a_assists = get_stat_entries("assists", "a")
                    a_saves = get_stat_entries("saves", "a")
                    a_og = get_stat_entries("own_goals", "a")
                    a_pmiss = get_stat_entries("penalties_missed", "a")
                    a_psaved = get_stat_entries("penalties_saved", "a")

                    h_cs_players = []
                    a_cs_players = []
                    if is_started and live_elements:
                        if a_score == 0:
                            for elem_id_str, e_data in live_elements.items():
                                elem_obj = element_lookup.get(int(elem_id_str), {})
                                if elem_obj.get("team") == h_id and e_data.get("stats", {}).get("clean_sheets", 0) > 0:
                                    h_cs_players.append(elem_obj.get("web_name", "Unknown"))
                        if h_score == 0:
                            for elem_id_str, e_data in live_elements.items():
                                elem_obj = element_lookup.get(int(elem_id_str), {})
                                if elem_obj.get("team") == a_id and e_data.get("stats", {}).get("clean_sheets", 0) > 0:
                                    a_cs_players.append(elem_obj.get("web_name", "Unknown"))

                    def resolve_defcon_achieved(side, team_id):
                        achieved = []
                        dc_items = stats_dict.get("defensive_contributions", {}).get(side, [])
                        if not dc_items:
                            dc_items = stats_dict.get("cbit", {}).get(side, []) or stats_dict.get("defcon", {}).get(side, [])
                        for itm in dc_items:
                            if isinstance(itm, dict):
                                p_elem = element_lookup.get(itm.get("element"), {})
                                p_name = p_elem.get("web_name", "Unknown")
                                p_pos = p_elem.get("element_type", 1)
                                val = itm.get("value", 0)
                                if (p_pos == 2 and val >= 10) or (p_pos in [3, 4] and val >= 12) or val >= 10:
                                    achieved.append((p_name, val))

                        if live_elements:
                            for elem_str_id, e_data in live_elements.items():
                                if not isinstance(e_data, dict):
                                    continue
                                try:
                                    elem_id_int = int(elem_str_id)
                                except (ValueError, TypeError):
                                    continue
                                elem_obj = element_lookup.get(elem_id_int, {})
                                if elem_obj.get("team") == team_id:
                                    p_name = elem_obj.get("web_name", "Unknown")
                                    p_pos = elem_obj.get("element_type", 1)
                                    e_stats = e_data.get("stats", {}) if isinstance(e_data.get("stats"), dict) else {}
                                    explain_raw = e_data.get("explain", [])
                                    
                                    if extract_defcon_achieved_flag(e_stats, explain_raw, p_pos):
                                        if not any(x[0] == p_name for x in achieved):
                                            achieved.append((p_name, 10 if p_pos == 2 else 12))
                        return achieved

                    h_defcon = resolve_defcon_achieved("h", h_id)
                    a_defcon = resolve_defcon_achieved("a", a_id)

                    b_col1, b_col2 = st.columns(2)

                    with b_col1:
                        st.markdown(f"**{h_name} Events**")
                        if h_goals:
                            st.markdown("⚽ **Goals:** " + ", ".join([f"{n} ({v})" if v > 1 else n for n, v in h_goals]))
                        if h_assists:
                            st.markdown("🎯 **Assists:** " + ", ".join([f"{n} ({v})" if v > 1 else n for n, v in h_assists]))
                        if h_defcon:
                            st.markdown("<span style='color: #22c55e;'>🔰 <b>DEFCON (+2 pts):</b> " + ", ".join([f"{n}" for n, _ in h_defcon]) + "</span>", unsafe_allow_html = True)
                        if h_cs_players:
                            st.markdown("🛡️ **Clean Sheets:** " + ", ".join(h_cs_players))
                        if h_saves:
                            st.markdown("🧤 **Saves:** " + ", ".join([f"{n} ({v} saves)" for n, v in h_saves]))
                        if h_og:
                            st.markdown("<span style='color: #ef4444;'>🛑 <b>Own Goals:</b> " + ", ".join([f"{n} ({v})" if v > 1 else n for n, v in h_og]) + "</span>", unsafe_allow_html = True)
                        if h_pmiss:
                            st.markdown("<span style='color: #ef4444;'>❌ <b>Penalties Missed:</b> " + ", ".join([f"{n} ({v})" if v > 1 else n for n, v in h_pmiss]) + "</span>", unsafe_allow_html = True)
                        if h_psaved:
                            st.markdown("<span style='color: #22c55e;'>🧤 <b>Penalties Saved:</b> " + ", ".join([f"{n} ({v})" if v > 1 else n for n, v in h_psaved]) + "</span>", unsafe_allow_html = True)
                        if not (h_goals or h_assists or h_defcon or h_saves or h_cs_players or h_og or h_pmiss or h_psaved):
                            st.caption("No registered match events yet.")

                    with b_col2:
                        st.markdown(f"**{a_name} Events**")
                        if a_goals:
                            st.markdown("⚽ **Goals:** " + ", ".join([f"{n} ({v})" if v > 1 else n for n, v in a_goals]))
                        if a_assists:
                            st.markdown("🎯 **Assists:** " + ", ".join([f"{n} ({v})" if v > 1 else n for n, v in a_assists]))
                        if a_defcon:
                            st.markdown("<span style='color: #22c55e;'>🔰 <b>DEFCON (+2 pts):</b> " + ", ".join([f"{n}" for n, _ in a_defcon]) + "</span>", unsafe_allow_html = True)
                        if a_cs_players:
                            st.markdown("🛡️ **Clean Sheets:** " + ", ".join(a_cs_players))
                        if a_saves:
                            st.markdown("🧤 **Saves:** " + ", ".join([f"{n} ({v} saves)" for n, v in a_saves]))
                        if a_og:
                            st.markdown("<span style='color: #ef4444;'>🛑 <b>Own Goals:</b> " + ", ".join([f"{n} ({v})" if v > 1 else n for n, v in a_og]) + "</span>", unsafe_allow_html = True)
                        if a_pmiss:
                            st.markdown("<span style='color: #ef4444;'>❌ <b>Penalties Missed:</b> " + ", ".join([f"{n} ({v})" if v > 1 else n for n, v in a_pmiss]) + "</span>", unsafe_allow_html = True)
                        if a_psaved:
                            st.markdown("<span style='color: #22c55e;'>🧤 <b>Penalties Saved:</b> " + ", ".join([f"{n} ({v})" if v > 1 else n for n, v in a_psaved]) + "</span>", unsafe_allow_html = True)
                        if not (a_goals or a_assists or a_defcon or a_saves or a_cs_players or a_og or a_pmiss or a_psaved):
                            st.caption("No registered match events yet.")

                with tab_sheets:
                    sheet_data = lineups_by_fix_id.get(f.get("id"))
                    
                    if sheet_data and sheet_data.get("has_lineups"):
                        view_toggle = st.radio(
                            "Lineup Display Mode",
                            ["⚽ Pitch View", "📋 List View"],
                            index = 0,
                            horizontal = True,
                            key = f"view_mode_fix_{f.get('id')}",
                            label_visibility = "collapsed"
                        )

                        h_starters = sheet_data.get("home_starters", [])
                        h_used = sheet_data.get("home_subs_used", [])
                        h_unused = sheet_data.get("home_subs_unused", [])

                        a_starters = sheet_data.get("away_starters", [])
                        a_used = sheet_data.get("away_subs_used", [])
                        a_unused = sheet_data.get("away_subs_unused", [])

                        if view_toggle == "⚽ Pitch View":
                            p_h_col, p_a_col = st.columns(2)
                            h_st_df, h_b_df = build_epl_pitch_dfs(h_starters, h_used, h_unused, h_short)
                            a_st_df, a_b_df = build_epl_pitch_dfs(a_starters, a_used, a_unused, a_short)

                            with p_h_col:
                                st.markdown(f"<p style='font-size:0.95rem; font-weight:800; color:{active_theme['accent']}; text-align:center; margin-bottom:4px;'>{h_name}</p>", unsafe_allow_html = True)
                                render_pitch_component(h_name, h_st_df, h_b_df, active_theme["accent"], large_mode, show_proj_pill = False)

                            with p_a_col:
                                st.markdown(f"<p style='font-size:0.95rem; font-weight:800; color:#38bdf8; text-align:center; margin-bottom:4px;'>{a_name}</p>", unsafe_allow_html = True)
                                render_pitch_component(a_name, a_st_df, a_b_df, "#38bdf8", large_mode, show_proj_pill = False)
                        else:
                            col_h_team, col_a_team = st.columns(2)

                            with col_h_team:
                                st.markdown(f"<p style='font-size:0.95rem; font-weight:800; color:{active_theme['accent']}; margin-bottom:4px;'>{h_name} Starting XI</p>", unsafe_allow_html = True)
                                st.markdown("\n\n".join(h_starters) if h_starters else "Lineup not yet available.", unsafe_allow_html = True)

                                st.divider()
                                st.markdown(f"<p style='font-size:0.85rem; font-weight:800; color:#94a3b8; margin:0 0 4px 0;'>{h_name} Subs</p>", unsafe_allow_html = True)
                                if h_used:
                                    st.markdown("\n\n".join(h_used), unsafe_allow_html = True)
                                if h_unused:
                                    st.caption("Unused: " + ", ".join(h_unused))
                                if not h_used and not h_unused:
                                    st.caption("No subs announced yet.")

                            with col_a_team:
                                st.markdown(f"<p style='font-size:0.95rem; font-weight:800; color:#38bdf8; margin-bottom:4px;'>{a_name} Starting XI</p>", unsafe_allow_html = True)
                                st.markdown("\n\n".join(a_starters) if a_starters else "Lineup not yet available.", unsafe_allow_html = True)

                                st.divider()
                                st.markdown(f"<p style='font-size:0.85rem; font-weight:800; color:#94a3b8; margin:0 0 4px 0;'>{a_name} Subs</p>", unsafe_allow_html = True)
                                if a_used:
                                    st.markdown("\n\n".join(a_used), unsafe_allow_html = True)
                                if a_unused:
                                    st.caption("Unused: " + ", ".join(a_unused))
                                if not a_used and not a_unused:
                                    st.caption("No subs announced yet.")
                    else:
                        st.info("🕒 Official team sheets drop 60–75 minutes prior to kickoff. Once submitted by the clubs, they will populate here automatically.")

                with tab_bps:
                    bps_list = []
                    raw_bps_entries = stats_dict.get("bps", {}).get("h", []) + stats_dict.get("bps", {}).get("a", [])
                    for item in raw_bps_entries:
                        elem_id = item.get("element")
                        p_elem = element_lookup.get(elem_id, {})
                        c_id = p_elem.get("team")
                        c_code = team_short_map.get(c_id, "")
                        pos_str = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}.get(p_elem.get("element_type", 1), "")
                        bps_list.append({
                            "element": elem_id,
                            "Player": p_elem.get("web_name", "Unknown"),
                            "Club": c_code,
                            "Pos": pos_str,
                            "BPS": int(item.get("value", 0))
                        })

                    if bps_list:
                        bps_sorted = sorted(bps_list, key = lambda x: x["BPS"], reverse = True)
                        
                        # Calculate official projected bonus points (+3, +2, +1) with ties
                        unique_scores = sorted(list({p["BPS"] for p in bps_sorted}), reverse = True)
                        bonus_award = {}
                        if len(unique_scores) >= 1:
                            top_val = unique_scores[0]
                            top_count = sum(1 for p in bps_sorted if p["BPS"] == top_val)
                            for p in bps_sorted:
                                if p["BPS"] == top_val:
                                    bonus_award[p["element"]] = 3
                            
                            if top_count == 1 and len(unique_scores) >= 2:
                                second_val = unique_scores[1]
                                second_count = sum(1 for p in bps_sorted if p["BPS"] == second_val)
                                for p in bps_sorted:
                                    if p["BPS"] == second_val:
                                        bonus_award[p["element"]] = 2
                                if second_count == 1 and len(unique_scores) >= 3:
                                    third_val = unique_scores[2]
                                    for p in bps_sorted:
                                        if p["BPS"] == third_val:
                                            bonus_award[p["element"]] = 1
                            elif top_count == 2 and len(unique_scores) >= 2:
                                second_val = unique_scores[1]
                                for p in bps_sorted:
                                    if p["BPS"] == second_val:
                                        bonus_award[p["element"]] = 1

                        table_rows = []
                        for rank, p in enumerate(bps_sorted[:12], 1):
                            bonus_pts = bonus_award.get(p["element"], 0)
                            proj_bonus = f"<span style='color:#f59e0b; font-weight:800;'>+{bonus_pts} pts</span>" if bonus_pts > 0 else "<span style='color:#64748b;'>-</span>"
                            table_rows.append({
                                "Rank": rank,
                                "Player": p["Player"],
                                "Club": p["Club"],
                                "Pos": p["Pos"],
                                "BPS": p["BPS"],
                                "Projected Bonus": proj_bonus
                            })

                        bps_df = pd.DataFrame(table_rows).set_index("Rank")
                        st.caption("Live BPS ranking across both clubs • Top 3 receive official FPL bonus points (+3, +2, +1)")
                        st.markdown(bps_df.to_html(escape = False), unsafe_allow_html = True)
                    else:
                        st.info("No BPS data registered for this fixture yet.")
                with tab_defcon:
                    defcon_map = {}

                    for key_name in ["defensive_contributions", "cbit", "defcon"]:
                        entries_dc = stats_dict.get(key_name, {}).get("h", []) + stats_dict.get(key_name, {}).get("a", [])
                        for item in entries_dc:
                            if isinstance(item, dict) and item.get("element"):
                                eid = int(item["element"])
                                val = int(item.get("value", 0))
                                defcon_map[eid] = max(defcon_map.get(eid, 0), val)

                    if live_elements:
                        for elem_str_id, e_data in live_elements.items():
                            if not isinstance(e_data, dict):
                                continue
                            try:
                                eid = int(elem_str_id)
                            except (ValueError, TypeError):
                                continue

                            p_elem = element_lookup.get(eid, {})
                            if p_elem.get("team") not in (h_id, a_id):
                                continue

                            pos_num = p_elem.get("element_type", 1)
                            if pos_num == 1:
                                continue

                            e_stats = e_data.get("stats", {}) if isinstance(e_data.get("stats"), dict) else {}
                            cbi = int(e_stats.get("clearances_blocks_interceptions", 0) or e_stats.get("cbi", 0))
                            tackles = int(e_stats.get("tackles", 0))
                            recoveries = int(e_stats.get("recoveries", 0) or e_stats.get("ball_recoveries", 0))
                            
                            dc_direct = int(e_stats.get("defensive_contributions", 0) or e_stats.get("defcon", 0) or e_stats.get("cbit", 0))
                            
                            if dc_direct > 0:
                                calc_val = dc_direct
                            else:
                                base_cbit = cbi + tackles
                                calc_val = base_cbit + recoveries if pos_num in [3, 4] else base_cbit

                            explain_val = 0
                            explain_raw = e_data.get("explain", [])
                            stat_items = []
                            if isinstance(explain_raw, list):
                                for exp_item in explain_raw:
                                    if isinstance(exp_item, dict):
                                        if "stats" in exp_item and isinstance(exp_item["stats"], list):
                                            stat_items.extend(exp_item["stats"])
                                        else:
                                            stat_items.append(exp_item)
                                    elif isinstance(exp_item, list):
                                        for sub in exp_item:
                                            if isinstance(sub, dict):
                                                stat_items.append(sub)

                            for s_item in stat_items:
                                if isinstance(s_item, dict):
                                    ident = str(s_item.get("identifier", "")).lower()
                                    if ident in ["defensive_contributions", "defcon", "cbit", "cbi"]:
                                        explain_val = max(explain_val, int(s_item.get("value", 0)))

                            best_val = max(calc_val, explain_val)
                            if best_val > 0:
                                defcon_map[eid] = max(defcon_map.get(eid, 0), best_val)

                    defcon_list = []
                    for eid, dc_val in defcon_map.items():
                        if dc_val <= 0:
                            continue
                        p_elem = element_lookup.get(eid, {})
                        pos_num = p_elem.get("element_type", 1)
                        if pos_num == 1:
                            continue
                        c_id = p_elem.get("team")
                        c_code = team_short_map.get(c_id, "")
                        pos_str = {2: "DEF", 3: "MID", 4: "FWD"}.get(pos_num, "MID")
                        target_val = 10 if pos_num == 2 else 12
                        is_hit = dc_val >= target_val

                        defcon_list.append({
                            "Player": p_elem.get("web_name", "Unknown"),
                            "Club": c_code,
                            "Pos": pos_str,
                            "DefCon": dc_val,
                            "Target": target_val,
                            "is_hit": is_hit
                        })

                    if defcon_list:
                        defcon_sorted = sorted(defcon_list, key = lambda x: (x["DefCon"], x["is_hit"]), reverse = True)
                        dc_rows = []
                        for rank, p in enumerate(defcon_sorted, 1):
                            if p["is_hit"]:
                                status_html = "<span style='color:#22c55e; font-weight:800;'>+2 pts ✅</span>"
                            else:
                                diff = p["Target"] - p["DefCon"]
                                status_html = f"<span style='color:#94a3b8;'>{diff} away</span>"

                            dc_rows.append({
                                "Rank": rank,
                                "Player": p["Player"],
                                "Club": p["Club"],
                                "Pos": p["Pos"],
                                "DefCon": f"{p['DefCon']} / {p['Target']}",
                                "DefCon Bonus": status_html
                            })

                        dc_df = pd.DataFrame(dc_rows).set_index("Rank")
                        st.caption("Live Defensive Contributions (CBIT for Defenders; CBIT + Recoveries for Midfielders & Forwards) • Threshold: 10 for DEF, 12 for MID and FWD (+2 pts)")
                        st.markdown(dc_df.to_html(escape = False), unsafe_allow_html = True)
                    else:
                        st.info("No defensive contributions registered for this fixture yet.")
# ----------------- 5. RESULTS ANALYSER SECTION (HISTORICAL ARCHIVES) -----------------
elif st.session_state.page == "Results Analyser":
    st.title("Results Analyser" + dash + selected_league_key)
    
    static_data = fetch_fpl_static()
    league_details, _ = fetch_league_data(active_league_id)
    all_fixtures = fetch_all_epl_fixtures()
    
    if not static_data or not league_details:
        st.error("Failed to load league data. Verify your connection.")
        st.stop()
        
    entries = league_details.get("league_entries", [])
    matches = league_details.get("matches", [])
    
    if not entries or not matches:
        st.warning("No fixtures or league teams found for this competition.")
        st.stop()
        
    lentry_map = {e["id"]: e for e in entries}
    pos_map = {item["id"]: item["singular_name_short"] for item in static_data["element_types"]}
    team_map = {item["id"]: item["short_name"] for item in static_data["teams"]}
    team_short_map = {item["id"]: item["short_name"] for item in static_data["teams"]}
    element_lookup = {item["id"]: item for item in static_data["elements"]}
    
    ctrl_col1, ctrl_col2 = st.columns([1, 2])
    with ctrl_col1:
        view_mode = st.radio("Browse Fixtures", ["By Gameweek", "By Team"], horizontal = True)
        
    selected_match = None
    
    if view_mode == "By Gameweek":
        all_events = sorted(list({m["event"] for m in matches}))
        finished_events = sorted(list({m["event"] for m in matches if m.get("finished", False)}))
        default_gw = finished_events[-1] if finished_events else (all_events[0] if all_events else 1)
        default_gw_idx = all_events.index(default_gw) if default_gw in all_events else 0
        
        with ctrl_col2:
            chosen_gw = st.selectbox("Select Gameweek", all_events, index = default_gw_idx)
            
        gw_matches = [m for m in matches if m["event"] == chosen_gw]
        
        def match_label_gw(m):
            e1 = lentry_map.get(m["league_entry_1"], {})
            e2 = lentry_map.get(m["league_entry_2"], {})
            s1 = m.get("league_entry_1_points", 0)
            s2 = m.get("league_entry_2_points", 0)
            alias1 = get_manager_alias(e1.get("player_first_name", ""), e1.get("player_last_name", ""))
            alias2 = get_manager_alias(e2.get("player_first_name", ""), e2.get("player_last_name", ""))
            status = " (FT)" if m.get("finished") else ""
            return f"{alias1} [{s1}] vs [{s2}] {alias2}{status}"
            
        match_idx = st.selectbox(
            "Select Fixture",
            range(len(gw_matches)),
            format_func = lambda i: match_label_gw(gw_matches[i])
        )
        selected_match = gw_matches[match_idx]
        
    else:
        team_choices = {
            e["id"]: f"{get_manager_alias(e['player_first_name'], e['player_last_name'])} ({e['entry_name']})"
            for e in entries
        }
        with ctrl_col2:
            chosen_team_lid = st.selectbox("Select Team", list(team_choices.keys()), format_func = lambda x: team_choices[x])
            
        team_matches = [m for m in matches if m["league_entry_1"] == chosen_team_lid or m["league_entry_2"] == chosen_team_lid]
        team_matches = sorted(team_matches, key = lambda x: x["event"])
        
        def match_label_team(m):
            e1 = lentry_map.get(m["league_entry_1"], {})
            e2 = lentry_map.get(m["league_entry_2"], {})
            s1 = m.get("league_entry_1_points", 0)
            s2 = m.get("league_entry_2_points", 0)
            alias1 = get_manager_alias(e1.get("player_first_name", ""), e1.get("player_last_name", ""))
            alias2 = get_manager_alias(e2.get("player_first_name", ""), e2.get("player_last_name", ""))
            status = " (FT)" if m.get("finished") else ""
            return f"GW {m['event']}: {alias1} [{s1}] vs [{s2}] {alias2}{status}"

        finished_team_indices = [i for i, m in enumerate(team_matches) if m.get("finished", False)]
        default_team_idx = finished_team_indices[-1] if finished_team_indices else 0

        t_idx = st.selectbox(
            "Select Matchup",
            range(len(team_matches)),
            index = default_team_idx,
            format_func = lambda i: match_label_team(team_matches[i])
        )
        selected_match = team_matches[t_idx]

    if selected_match:
        gw_num = selected_match["event"]
        e1_info = lentry_map.get(selected_match["league_entry_1"], {})
        e2_info = lentry_map.get(selected_match["league_entry_2"], {})
        score1 = selected_match.get("league_entry_1_points", 0)
        score2 = selected_match.get("league_entry_2_points", 0)
        alias1 = get_manager_alias(e1_info.get("player_first_name", ""), e1_info.get("player_last_name", ""))
        alias2 = get_manager_alias(e2_info.get("player_first_name", ""), e2_info.get("player_last_name", ""))
        
        st.divider()
        
        res_col1, res_col2, res_col3 = st.columns([4, 2, 4])
        with res_col1:
            st.markdown(f"### {alias1} ({score1} pts)")
            st.caption(e1_info.get("entry_name", "Team 1"))
        with res_col2:
            status_text = "FINAL SCORE" if selected_match.get("finished") else "ARCHIVED SCORE"
            st.markdown(f"<div class='card-score-center'>{score1} {dash} {score2}</div>", unsafe_allow_html = True)
            st.markdown("<p style='text-align: center; color: #94a3b8; margin: 4px 0 0 0; font-weight: bold;'>" + status_text + " (GW " + str(gw_num) + ")</p>", unsafe_allow_html = True)
        with res_col3:
            st.markdown(f"<h3 style='text-align: right;'>{alias2} ({score2} pts)</h3>", unsafe_allow_html = True)
            st.markdown(f"<p style='text-align: right; color: #94a3b8; margin: 0;'>Manager: {alias2}</p>", unsafe_allow_html = True)
            
        st.divider()

        picks1_data = fetch_entry_event(e1_info.get("entry_id"), gw_num)
        picks2_data = fetch_entry_event(e2_info.get("entry_id"), gw_num)
        live_data = fetch_live_event(gw_num)
        live_elements = live_data.get("elements", {}) if live_data else {}

        club_minutes = {}
        for elem_str_id, e_info in live_elements.items():
            try:
                elem_int_id = int(elem_str_id)
            except (ValueError, TypeError):
                continue
            elem_obj = element_lookup.get(elem_int_id, {})
            c_id = elem_obj.get("team")
            if c_id:
                m_val = e_info.get("stats", {}).get("minutes", 0)
                club_minutes[c_id] = club_minutes.get(c_id, 0) + m_val

        t1_start, t1_b, _, _, _, _, t1_bp, t1_opt = evaluate_lineup(
            picks1_data, live_elements, element_lookup, club_minutes, pos_map, team_map, gw_num, all_fixtures
        )
        t2_start, t2_b, _, _, _, _, t2_bp, t2_opt = evaluate_lineup(
            picks2_data, live_elements, element_lookup, club_minutes, pos_map, team_map, gw_num, all_fixtures
        )

        st.caption(f"{alias1} — Bench Left: {t1_bp} pts | Optimum Score: {t1_opt} pts   |   {alias2} — Bench Left: {t2_bp} pts | Optimum Score: {t2_opt} pts")

        render_progression_chart(
            gw_num,
            alias1,
            alias2,
            t1_start,
            t1_b,
            t2_start,
            t2_b,
            all_fixtures,
            team_short_map,
            active_theme["accent"]
        )
        st.divider()

        side1, side2 = st.columns(2)
        with side1:
            render_lineup_container(
                alias1,
                t1_start,
                t1_b,
                t1_bp,
                t1_opt,
                active_theme["accent"],
                large_mode,
                score = score1
            )

        with side2:
            render_lineup_container(
                alias2,
                t2_start,
                t2_b,
                t2_bp,
                t2_opt,
                active_theme["accent"],
                large_mode,
                score = score2
            )

# ----------------- 6. SQUAD ANALYSER SECTION -----------------
elif st.session_state.page == "Squad Analyser":
    st.title("Squad Analyser" + dash + selected_league_key)
    
    static_data = fetch_fpl_static()
    league_details, element_status = fetch_league_data(active_league_id)
    all_fixtures = fetch_all_epl_fixtures()
    
    if not static_data or not league_details or not element_status:
        st.error("Failed to load league data. Verify connection and try again.")
        st.stop()
        
    pos_map = {item["id"]: item["singular_name_short"] for item in static_data["element_types"]}
    team_map = {item["id"]: item["short_name"] for item in static_data["teams"]}
    element_lookup = {item["id"]: item for item in static_data["elements"]}

    matches = league_details.get("matches", [])
    all_events = sorted(list({m["event"] for m in matches})) if matches else list(range(1, 39))
    unplayed_events = sorted(list({m["event"] for m in matches if not m.get("finished", False)})) if matches else []
    current_gw = unplayed_events[0] if unplayed_events else (all_events[-1] if all_events else 1)

    finished_events = sorted(list({m["event"] for m in matches if m.get("finished", False)}))
    prev_gw1 = finished_events[-1] if finished_events else 0
    prev_gw2 = finished_events[-2] if len(finished_events) >= 2 else 0

    live_prev1 = fetch_live_event(prev_gw1) if prev_gw1 > 0 else None
    live_prev2 = fetch_live_event(prev_gw2) if prev_gw2 > 0 else None

    def get_next_3_fixtures(team_id):
        if not all_fixtures or not team_id:
            return "TBD"
        upcoming = [
            f for f in all_fixtures
            if not f.get("finished", False) and (f.get("team_h") == team_id or f.get("team_a") == team_id)
        ]
        upcoming = sorted(upcoming, key = lambda x: (x.get("event") or 99, x.get("kickoff_time") or ""))
        next_3 = upcoming[:3]
        if not next_3:
            return "None"
        labels = []
        for f in next_3:
            if f.get("team_h") == team_id:
                opp = team_map.get(f.get("team_a"), "OPP")
                labels.append(f"{opp} (H)")
            else:
                opp = team_map.get(f.get("team_h"), "OPP")
                labels.append(f"{opp} (A)")
        return ", ".join(labels)

    elements_df = pd.DataFrame(static_data["elements"])
    elements_df["position"] = elements_df["element_type"].map(pos_map)
    elements_df["club"] = elements_df["team"].map(team_map)
    elements_df["form"] = pd.to_numeric(elements_df["form"], errors = "coerce").fillna(0.0).round(1)
    elements_df["points_per_game"] = pd.to_numeric(elements_df["points_per_game"], errors = "coerce").fillna(0.0).round(1)
    elements_df["ict_index"] = pd.to_numeric(elements_df["ict_index"], errors = "coerce").fillna(0.0).round(1)
    elements_df["total_points"] = pd.to_numeric(elements_df["total_points"], errors = "coerce").fillna(0)
    elements_df["minutes"] = pd.to_numeric(elements_df["minutes"], errors = "coerce").fillna(0)
    elements_df["chance_of_playing_next_round"] = pd.to_numeric(elements_df["chance_of_playing_next_round"], errors = "coerce")

    def calc_last_2_pts(elem_id):
        pts = 0
        s_id = str(elem_id)
        if live_prev1:
            pts += live_prev1.get("elements", {}).get(s_id, {}).get("stats", {}).get("total_points", 0)
        if live_prev2:
            pts += live_prev2.get("elements", {}).get(s_id, {}).get("stats", {}).get("total_points", 0)
        return pts

    elements_df["last_2_pts"] = elements_df["id"].map(calc_last_2_pts)
    elements_df["next_3"] = elements_df["team"].map(get_next_3_fixtures)
    elements_df["avail_factor"] = elements_df.apply(get_availability_multiplier, axis = 1).round(1)
    elements_df["health_status"] = elements_df.apply(get_health_label, axis = 1)

    status_df = pd.DataFrame(element_status["element_status"])
    merged = elements_df.merge(status_df, left_on = "id", right_on = "element", how = "inner")

    entries = league_details.get("league_entries", [])
    entry_options = {
        e["entry_id"]: f"{get_manager_alias(e['player_first_name'], e['player_last_name'])} ({e['entry_name']})"
        for e in entries
    }

    if not entry_options:
        st.error("No teams found for this league.")
        st.stop()

    entry_keys = list(entry_options.keys())

    # Find if the logged-in manager owns a team in this division
    matched_entry_id = None
    for e in entries:
        m_alias = get_manager_alias(e.get("player_first_name", ""), e.get("player_last_name", ""))
        if m_alias.lower() == logged_alias.lower():
            matched_entry_id = e.get("entry_id")
            break

    if is_admin_account:
        # Admin login gets a dropdown to view all teams in any division
        default_entry_idx = entry_keys.index(matched_entry_id) if matched_entry_id in entry_keys else 0
        selected_entry_id = st.sidebar.selectbox(
            "Select Team (Admin View)",
            options = entry_keys,
            format_func = lambda x: entry_options.get(x, str(x)),
            index = default_entry_idx,
            key = "admin_team_selector_" + str(active_league_id)
        )
    else:
        # Regular manager login is locked strictly to their own team
        if not matched_entry_id:
            st.warning(
                f"🔒 **Squad Analyser Locked:** You do not manage a team in **{selected_league_key}**. "
                f"Click **Jump to My League** in the sidebar to analyse your squad."
            )
            st.stop()
        selected_entry_id = matched_entry_id
        st.sidebar.info(f"🔒 **Your Squad:** {entry_options.get(selected_entry_id, logged_alias)}")

    my_squad = merged[merged["owner"] == selected_entry_id].copy()
    waiver_pool = merged[merged["owner"].isna() | (merged["owner"] == 0)].copy()

    tab_lineup, tab_waivers = st.tabs([
        "Recommended Lineup",
        "Tailored Waivers & Suggested Drops"
    ])

    # ----------------- TAB 1: RECOMMENDED STARTING XI -----------------
    with tab_lineup:
        if my_squad.empty:
            st.warning("No players found for this team selection.")
        else:
            def compute_gw_projection(r):
                avail = float(r["avail_factor"])
                if avail <= 0.0:
                    return 0.0
                form_val = float(r["form"] or 0.0)
                ppg_val = float(r["points_per_game"] or 2.0)
                base_exp = ((ppg_val * 0.6) + (form_val * 0.4)) * avail

                season_mins = float(r["minutes"] or 0.0)
                if current_gw > 3:
                    expected_min_ratio = season_mins / max(1.0, float(current_gw * 60))
                    if expected_min_ratio < 0.6:
                        base_exp = base_exp * 0.8

                if base_exp <= 0 and avail > 0:
                    base_exp = 2.0

                fdr_mult = get_fdr_multiplier(r["team"], current_gw, all_fixtures)
                return round(base_exp * fdr_mult, 1)

            def compute_starter_rating(r):
                if r["avail_factor"] == 0.0:
                    return -9999.0
                base_score = (r["form"] * 1.8) + (r["points_per_game"] * 2.0) + (r["ict_index"] * 0.05)
                return round(base_score * r["avail_factor"], 1)

            my_squad["proj_gw"] = my_squad.apply(compute_gw_projection, axis = 1)
            my_squad["starter_rating"] = my_squad.apply(compute_starter_rating, axis = 1)
            sorted_squad = my_squad.sort_values(by = ["proj_gw", "starter_rating"], ascending = [False, False])
            
            gks = sorted_squad[sorted_squad["position"] == "GKP"]
            defs = sorted_squad[sorted_squad["position"] == "DEF"]
            mids = sorted_squad[sorted_squad["position"] == "MID"]
            fwds = sorted_squad[sorted_squad["position"] == "FWD"]
            
            starting_xi = []
            bench_gk = []
            
            if not gks.empty:
                starting_xi.append(gks.iloc[0])
                if len(gks) > 1:
                    bench_gk.extend([gks.iloc[i] for i in range(1, len(gks))])
                    
            starting_xi.extend([defs.iloc[i] for i in range(min(3, len(defs)))])
            starting_xi.extend([mids.iloc[i] for i in range(min(2, len(mids)))])
            starting_xi.extend([fwds.iloc[i] for i in range(min(1, len(fwds)))])
            
            used_ids = {p["id"] for p in starting_xi}
            remaining_outfield = sorted_squad[
                (~sorted_squad["id"].isin(used_ids)) & (sorted_squad["position"] != "GKP")
            ]
            
            spots_left = 11 - len(starting_xi)
            starting_xi.extend([remaining_outfield.iloc[i] for i in range(min(spots_left, len(remaining_outfield)))])
            
            final_xi_ids = {p["id"] for p in starting_xi}
            all_bench_outfield = sorted_squad[
                (~sorted_squad["id"].isin(final_xi_ids)) & (sorted_squad["position"] != "GKP")
            ].copy()
            
            all_bench_outfield["pos_rank"] = all_bench_outfield["position"].map(POS_ORDER).fillna(99)
            ordered_bench_outfield = all_bench_outfield.sort_values(by = ["pos_rank", "proj_gw"], ascending = [True, False])

            bench_rows = []
            for bg in bench_gk:
                bg_dict = bg.to_dict()
                bg_dict["Role"] = "GK Sub"
                bench_rows.append(bg_dict)
            for idx, (_, bo) in enumerate(ordered_bench_outfield.iterrows(), 1):
                bo_dict = bo.to_dict()
                bo_dict["Role"] = f"Sub {idx}"
                bench_rows.append(bo_dict)

            xi_df = pd.DataFrame(starting_xi)
            xi_df["pos_rank"] = xi_df["position"].map(POS_ORDER)
            xi_df = xi_df.sort_values(by = ["pos_rank", "proj_gw"], ascending = [True, False])
            
            xi_proj_sum = round(float(xi_df["proj_gw"].sum()), 1)
            sel_manager_name = entry_options.get(selected_entry_id, "Selected Squad").split(" (")[0]
            st.subheader(f"Recommended Lineup: {sel_manager_name} ({xi_proj_sum:.1f} proj pts)")
            st.caption(f"Gameweek {current_gw} projected points shown on pitch tokens • Bench ordered GK then DEF then MID then FWD.")

            squad_tab_pitch, squad_tab_table = st.tabs(["⚽ Pitch View", "📋 Table View"])

            with squad_tab_pitch:
                s_starters_df = xi_df.rename(columns = {
                    "web_name": "Player",
                    "position": "Pos",
                    "club": "Club",
                    "proj_gw": "Proj",
                    "total_points": "Pts"
                })
                s_starters_df["G"] = 0
                s_starters_df["A"] = 0
                s_starters_df["CS"] = 0
                s_starters_df["GC"] = 0
                s_starters_df["Bonus"] = 0
                s_starters_df["Mins"] = 0
                s_starters_df["State"] = "YTP"
                s_starters_df["sub_action"] = ""

                s_bench_df = pd.DataFrame(bench_rows) if bench_rows else pd.DataFrame()
                if not s_bench_df.empty:
                    s_bench_df = s_bench_df.rename(columns = {
                        "web_name": "Player",
                        "position": "Pos",
                        "club": "Club",
                        "proj_gw": "Proj",
                        "total_points": "Pts"
                    })
                    s_bench_df["G"] = 0
                    s_bench_df["A"] = 0
                    s_bench_df["CS"] = 0
                    s_bench_df["GC"] = 0
                    s_bench_df["Bonus"] = 0
                    s_bench_df["Mins"] = 0
                    s_bench_df["State"] = "YTP"
                    s_bench_df["sub_action"] = ""

                pitch_col, _ = st.columns(2)
                with pitch_col:
                    render_pitch_component(sel_manager_name, s_starters_df, s_bench_df, active_theme["accent"], large_mode, show_proj_pill = True)

            with squad_tab_table:
                xi_df["GW Proj"] = xi_df["proj_gw"].map(lambda x: f"{float(x):.1f}")
                xi_df["PPG"] = xi_df["points_per_game"].map(lambda x: f"{float(x):.1f}")
                xi_df["Form"] = xi_df["form"].map(lambda x: f"{float(x):.1f}")

                display_cols = ["web_name", "position", "club", "health_status", "GW Proj", "total_points", "last_2_pts", "next_3", "PPG", "Form"]
                xi_display = xi_df[display_cols].rename(columns = {
                    "web_name": "Player",
                    "position": "Pos",
                    "club": "Club",
                    "health_status": "Status",
                    "total_points": "Season Pts",
                    "last_2_pts": "Last 2 GWs",
                    "next_3": "Next 3 Fixtures"
                })
                st.markdown("**Starting XI (GK First)**")
                st.table(xi_display.set_index("Player"))

                if bench_rows:
                    st.markdown("**Bench Hierarchy (GK → DEF → MID → FWD)**")
                    b_df = pd.DataFrame(bench_rows)
                    b_df["GW Proj"] = b_df["proj_gw"].map(lambda x: f"{float(x):.1f}")
                    b_df["PPG"] = b_df["points_per_game"].map(lambda x: f"{float(x):.1f}")
                    b_df["Form"] = b_df["form"].map(lambda x: f"{float(x):.1f}")

                    b_cols = ["Role", "web_name", "position", "club", "health_status", "GW Proj", "total_points", "last_2_pts", "next_3", "PPG", "Form"]
                    b_display = b_df[b_cols].rename(columns = {
                        "Role": "Role",
                        "web_name": "Player",
                        "position": "Pos",
                        "club": "Club",
                        "health_status": "Status",
                        "total_points": "Season Pts",
                        "last_2_pts": "Last 2 GWs",
                        "next_3": "Next 3 Fixtures"
                    })
                    st.table(b_display.set_index("Role"))

    # ----------------- TAB 2: TAILORED WAIVERS & SUGGESTED DROPS -----------------
    with tab_waivers:
        st.subheader("Tactical Waiver Intelligence & Roster Triage")

        all_rostered = merged[merged["owner"].isin(entry_keys)].copy()
        league_pos_ppg = all_rostered.groupby("position")["points_per_game"].mean().round(1).to_dict()
        squad_pos_ppg = my_squad.groupby("position")["points_per_game"].mean().round(1).to_dict()

        fit_defs = len(my_squad[(my_squad["position"] == "DEF") & (my_squad["avail_factor"] >= 0.9)])
        fit_mids = len(my_squad[(my_squad["position"] == "MID") & (my_squad["avail_factor"] >= 0.9)])
        fit_fwds = len(my_squad[(my_squad["position"] == "FWD") & (my_squad["avail_factor"] >= 0.9)])

        alerts = []
        target_positions = []

        if fit_defs < 3:
            alerts.append(f"🛡️ **DEF Depth Emergency:** Only {fit_defs} defender(s) 100% fit for the upcoming round. Immediate cover required.")
            target_positions.append("DEF")
        if fit_fwds < 1:
            alerts.append(f"⚡ **FWD Availability Crisis:** 0 fit strikers currently available in your squad.")
            target_positions.append("FWD")

        for pos_key in ["DEF", "MID", "FWD"]:
            s_ppg = squad_pos_ppg.get(pos_key, 0.0)
            l_ppg = league_pos_ppg.get(pos_key, 0.0)
            if s_ppg < l_ppg - 0.7:
                alerts.append(f"⚠️ **{pos_key} Production Deficit:** Your {pos_key} unit averages {s_ppg:.1f} PPG vs the league average of {l_ppg:.1f} PPG.")
                if pos_key not in target_positions:
                    target_positions.append(pos_key)

        if not target_positions:
            target_positions = ["DEF", "MID", "FWD"]

        if alerts:
            for alert_text in alerts:
                st.warning(alert_text)
        else:
            st.success("✅ **Squad Balance Sound:** Roster availability and positional averages meet or exceed division baselines. Scouting high upside upgrades.")

        top_pts_ids = set(my_squad.sort_values(by = "total_points", ascending = False).head(3)["id"])
        top_ppg_ids = set(my_squad.sort_values(by = "points_per_game", ascending = False).head(3)["id"])
        top_form_ids = set(my_squad.sort_values(by = "form", ascending = False).head(2)["id"])
        untouchables = top_pts_ids.union(top_ppg_ids).union(top_form_ids)

        my_squad["utility_score"] = (
            (my_squad["points_per_game"] * 1.5) + (my_squad["form"] * 1.0)
        ) * my_squad["avail_factor"]

        droppable_pool = my_squad[~my_squad["id"].isin(untouchables)].sort_values(by = "utility_score", ascending = True)

        col_w1, col_w2 = st.columns([2, 3])
        with col_w1:
            selected_focus = st.selectbox(
                "Filter Scout Focus",
                ["Squad Needs (Auto)", "All Outfield", "DEF Only", "MID Only", "FWD Only"]
            )
            if selected_focus == "DEF Only":
                active_pos_filter = ["DEF"]
            elif selected_focus == "MID Only":
                active_pos_filter = ["MID"]
            elif selected_focus == "FWD Only":
                active_pos_filter = ["FWD"]
            elif selected_focus == "All Outfield":
                active_pos_filter = ["DEF", "MID", "FWD"]
            else:
                active_pos_filter = target_positions

        waiver_pool["target_rating"] = (
            ((waiver_pool["form"] * 1.8) + (waiver_pool["points_per_game"] * 2.0) + (waiver_pool["ict_index"] * 0.05))
            * waiver_pool["avail_factor"]
        ).round(1)

        candidate_waivers = waiver_pool[
            (waiver_pool["position"].isin(active_pos_filter)) &
            (waiver_pool["avail_factor"] >= 0.6) &
            (waiver_pool["total_points"] >= 5)
        ].sort_values(by = "target_rating", ascending = False).head(10)

        tradeoff_rows = []
        for _, w_cand in candidate_waivers.iterrows():
            w_pos = w_cand["position"]
            pos_drops = droppable_pool[droppable_pool["position"] == w_pos]
            if not pos_drops.empty:
                drop_player = pos_drops.iloc[0]
            elif not droppable_pool.empty:
                drop_player = droppable_pool.iloc[0]
            else:
                drop_player = None

            if drop_player is not None:
                form_diff = round(w_cand["form"] - drop_player["form"], 1)
                ppg_diff = round(w_cand["points_per_game"] - drop_player["points_per_game"], 1)
                
                diff_sign_f = f"+{form_diff:.1f}" if form_diff > 0 else f"{form_diff:.1f}"
                diff_sign_p = f"+{ppg_diff:.1f}" if ppg_diff > 0 else f"{ppg_diff:.1f}"
                
                if drop_player["avail_factor"] < 1.0 and w_cand["avail_factor"] == 1.0:
                    rationale = f"Fit Cover ({diff_sign_f} Form)"
                elif form_diff > 1.5:
                    rationale = f"Form Spike ({diff_sign_f} Form)"
                else:
                    rationale = f"{diff_sign_p} PPG baseline"

                tradeoff_rows.append({
                    "Waiver Target": f"{w_cand['web_name']} ({w_cand['club']})",
                    "Pos": w_pos,
                    "Target Form": f"{w_cand['form']:.1f}",
                    "Target PPG": f"{w_cand['points_per_game']:.1f}",
                    "Next 3 Fixtures": w_cand["next_3"],
                    "Suggested Drop": f"{drop_player['web_name']} ({drop_player['club']})",
                    "Drop Status": drop_player["health_status"],
                    "Upgrade Delta": rationale
                })

        if tradeoff_rows:
            trade_df = pd.DataFrame(tradeoff_rows)
            st.table(trade_df.set_index("Waiver Target"))
        else:
            st.info("No matching waiver options found with sufficient points and playing chance.")
# ----------------- 6B. TRADE HUB SECTION (TRANSFER LIST & TRADE CALCULATOR) -----------------
elif st.session_state.page == "Trade Hub":
    st.title("Trade Hub & Trading Block" + dash + selected_league_key)
    st.markdown("🛒 **The League Transfer List & Calculator:** Broadcast your trade targets, scout active listings in your division, and evaluate trades.")

    # 1. Initialize data storage for trade listings
    trade_file = base_dir / "trade_block.json"

    def load_trade_block():
        if "persisted_trade_block" in st.session_state and st.session_state["persisted_trade_block"]:
            return st.session_state["persisted_trade_block"]
        if trade_file.exists():
            try:
                with open(trade_file, "r", encoding = "utf-8") as tf:
                    data = json.load(tf)
                    if isinstance(data, list):
                        st.session_state["persisted_trade_block"] = data
                        return data
            except Exception:
                pass
        return []

    def save_trade_block(listings):
        st.session_state["persisted_trade_block"] = listings
        try:
            with open(trade_file, "w", encoding = "utf-8") as tf:
                json.dump(listings, tf, indent = 2, ensure_ascii = False)
        except Exception:
            pass

    trade_listings = load_trade_block()

    # Fetch required league and player data
    static_data = fetch_fpl_static()
    league_details, element_status = fetch_league_data(active_league_id)
    all_fixtures = fetch_all_epl_fixtures()
    all_teams_reg = get_all_32_teams_registry()

    if not static_data or not league_details or not element_status:
        st.error("Failed to load league details for the Trade Hub.")
        st.stop()

    pos_map = {item["id"]: item["singular_name_short"] for item in static_data["element_types"]}
    team_map = {item["id"]: item["short_name"] for item in static_data["teams"]}
    
    elements_df = pd.DataFrame(static_data["elements"])
    elements_df["position"] = elements_df["element_type"].map(pos_map)
    elements_df["club"] = elements_df["team"].map(team_map)
    elements_df["form"] = pd.to_numeric(elements_df["form"], errors = "coerce").fillna(0.0).round(1)
    elements_df["points_per_game"] = pd.to_numeric(elements_df["points_per_game"], errors = "coerce").fillna(0.0).round(1)
    elements_df["ict_index"] = pd.to_numeric(elements_df["ict_index"], errors = "coerce").fillna(0.0).round(1)
    elements_df["total_points"] = pd.to_numeric(elements_df["total_points"], errors = "coerce").fillna(0)
    elements_df["avail_factor"] = elements_df.apply(get_availability_multiplier, axis = 1).round(1)
    elements_df["health_status"] = elements_df.apply(get_health_label, axis = 1)

    def get_next_3_trade(team_id):
        if not all_fixtures or not team_id:
            return "TBD"
        upcoming = [
            f for f in all_fixtures
            if not f.get("finished", False) and (f.get("team_h") == team_id or f.get("team_a") == team_id)
        ]
        upcoming = sorted(upcoming, key = lambda x: (x.get("event") or 99, x.get("kickoff_time") or ""))[:3]
        if not upcoming:
            return "None"
        labels = []
        for f in upcoming:
            if f.get("team_h") == team_id:
                labels.append(f"{team_map.get(f.get('team_a'), 'OPP')} (H)")
            else:
                labels.append(f"{team_map.get(f.get('team_h'), 'OPP')} (A)")
        return ", ".join(labels)

    elements_df["next_3"] = elements_df["team"].map(get_next_3_trade)
    elements_df["trade_value"] = (
        ((elements_df["points_per_game"] * 2.0) + (elements_df["form"] * 1.8) + (elements_df["ict_index"] * 0.05))
        * elements_df["avail_factor"]
    ).round(1)

    status_df = pd.DataFrame(element_status["element_status"])
    elements_df = elements_df.merge(status_df, left_on = "id", right_on = "element", how = "inner")

    entries = league_details.get("league_entries", [])
    entry_options = {
        e["entry_id"]: {
            "team_name": e.get("entry_name", "Team"),
            "manager_name": f"{e.get('player_first_name', '')} {e.get('player_last_name', '')}".strip(),
            "alias": get_manager_alias(e.get("player_first_name", ""), e.get("player_last_name", ""))
        }
        for e in entries
    }

    owner_alias_map = {e_id: info["alias"] for e_id, info in entry_options.items()}
    elements_df["owner_alias"] = elements_df["owner"].map(owner_alias_map).fillna("Free Agent")

    matched_entry_id = None
    for e_id, info in entry_options.items():
        if info["alias"].lower() == logged_alias.lower():
            matched_entry_id = e_id
            break

    tab_browse, tab_manage, tab_calc = st.tabs([
        "🛒 League Transfer List",
        "📋 Manage My Listings",
        "⚖️ Trade Calculator"
    ])

    # ----------------- TAB 1: BROWSE LEAGUE TRADING BLOCK (STRICTLY ACTIVE LEAGUE) -----------------
    with tab_browse:
        st.subheader(f"Active Transfer List — {selected_league_key}")
        
        tb_col1, tb_col2 = st.columns([2, 1])
        with tb_col1:
            trade_div_scope = st.selectbox(
                "Filter Division",
                ["All Divisions", "CDP (Crème Dellar Prem)", "SDM (Segundo Del Mundo)", "BDR (Best De La Rest)", "LDE (Liger Del Eager)"],
                index = 0,
                key = "trade_div_scope_filter"
            )
        with tb_col2:
            pos_filter = st.selectbox("Filter Position", ["All", "GKP", "DEF", "MID", "FWD"], key = "trade_pos_filter")

        if trade_div_scope == "All Divisions":
            filtered_listings = trade_listings
        else:
            filtered_listings = [item for item in trade_listings if item.get("league_key") == trade_div_scope]

        if pos_filter != "All":
            filtered_listings = [item for item in filtered_listings if item.get("position") == pos_filter]

        if not filtered_listings:
            st.info("The trading block is currently empty for these filters. Add players under 'Manage My Listings'!")
        else:
            display_rows = []
            for item in filtered_listings:
                display_rows.append({
                    "Player": item.get("player_name"),
                    "Club": item.get("club"),
                    "Pos": item.get("position"),
                    "Div": str(item.get("league_key", "")).split(" ")[0],
                    "Manager": item.get("manager_alias"),
                    "Asking / Notes": item.get("notes", "Open to offers"),
                    "Date": item.get("date", "Recent")
                })
            
            t_df = pd.DataFrame(display_rows)
            st.table(t_df.set_index("Player"))

    # ----------------- TAB 2: MANAGE MY LISTED PLAYERS -----------------
    with tab_manage:
        st.subheader("Add or Remove Players From Your Trading Block")

        if not matched_entry_id and not is_admin_account:
            st.warning(f"🔒 You do not have a registered team in **{selected_league_key}**. Switch to your home league to manage your transfer list.")
        else:
            if is_admin_account:
                admin_target_entry = st.selectbox(
                    "Select Team to Manage (Admin Override)",
                    options = list(entry_options.keys()),
                    format_func = lambda x: f"{entry_options[x]['alias']} ({entry_options[x]['team_name']})"
                )
                my_squad = elements_df[elements_df["owner"] == admin_target_entry].copy()
                active_manager_alias = entry_options[admin_target_entry]["alias"]
                active_team_name = entry_options[admin_target_entry]["team_name"]
            else:
                my_squad = elements_df[elements_df["owner"] == matched_entry_id].copy()
                active_manager_alias = logged_alias
                active_team_name = entry_options[matched_entry_id]["team_name"]

            if my_squad.empty:
                st.info("No squad players found for listing.")
            else:
                st.markdown("### ➕ Put a Player Up For Trade")
                squad_player_options = {row["id"]: f"{row['web_name']} ({row['club']} - {row['position']})" for _, row in my_squad.iterrows()}
                
                with st.form("add_trade_form"):
                    selected_player_id = st.selectbox("Select Player from Your Roster", options = list(squad_player_options.keys()), format_func = lambda x: squad_player_options[x])
                    trade_notes = st.text_input("Trade Notes / Asking Requirements (e.g. 'Looking for a starting MID')", value = "Open to offers")
                    submit_listing = st.form_submit_button("📢 Add to League Trading Block", type = "primary")

                    if submit_listing:
                        p_info = elements_df[elements_df["id"] == selected_player_id].iloc[0]
                        
                        trade_listings = [t for t in trade_listings if not (t.get("player_id") == selected_player_id and t.get("manager_alias") == active_manager_alias)]
                        
                        new_listing = {
                            "player_id": int(selected_player_id),
                            "player_name": str(p_info["web_name"]),
                            "club": str(p_info["club"]),
                            "position": str(p_info["position"]),
                            "manager_alias": str(active_manager_alias),
                            "team_name": str(active_team_name),
                            "league_key": str(selected_league_key),
                            "notes": str(trade_notes),
                            "date": pd.Timestamp.today().strftime("%d %b")
                        }
                        trade_listings.append(new_listing)
                        save_trade_block(trade_listings)
                        st.success(f"✅ Successfully listed **{p_info['web_name']}** on the trading block!")
                        st.rerun()

                st.divider()
                st.markdown("### ❌ Remove Your Active Listings")
                my_active_listings = [t for t in trade_listings if t.get("manager_alias") == active_manager_alias and t.get("league_key") == selected_league_key]

                if not my_active_listings:
                    st.info("You currently have no players listed on the transfer list in this league.")
                else:
                    for listing in my_active_listings:
                        col_l1, col_l2 = st.columns([3, 1])
                        with col_l1:
                            st.markdown(f"**{listing['player_name']}** ({listing['club']} - {listing['position']}) — *{listing['notes']}*")
                        with col_l2:
                            if st.button("Remove", key = f"remove_trade_{listing['player_id']}"):
                                trade_listings = [t for t in trade_listings if not (t.get("player_id") == listing["player_id"] and t.get("manager_alias") == active_manager_alias)]
                                save_trade_block(trade_listings)
                                st.success(f"Removed {listing['player_name']} from block.")
                                st.rerun()

    # ----------------- TAB 3: TRADE CALCULATOR (FORMAT SELECTOR & SASSY VERDICT) -----------------
    with tab_calc:
        st.subheader("⚖️ Trade Package Evaluator")
        
        trade_mode = st.selectbox(
            "Select Trade Format",
            [1, 2, 3],
            format_func = lambda x: f"{x} v {x} Trade Package",
            key = "trade_format_selector"
        )
        st.caption(f"Evaluate a **{trade_mode} v {trade_mode}** player swap across Season Points, PPG, Form and Trade Rating.")

        team_filter_options = ["All Players"] + [f"{info['alias']} ({info['team_name']})" for _, info in entry_options.items()]
        alias_to_entry_id = {f"{info['alias']} ({info['team_name']})": e_id for e_id, info in entry_options.items()}

        col_side1, col_side2 = st.columns(2)

        # ----------------- SIDE A SELECTION -----------------
        with col_side1:
            st.markdown("### 📤 Side A (Sending)")
            default_team_a_idx = 0
            if matched_entry_id and matched_entry_id in entry_options:
                my_label = f"{entry_options[matched_entry_id]['alias']} ({entry_options[matched_entry_id]['team_name']})"
                if my_label in team_filter_options:
                    default_team_a_idx = team_filter_options.index(my_label)

            team_a_filter = st.selectbox("Filter Side A by Squad", team_filter_options, index = default_team_a_idx, key = "calc_team_a_filter")
            if team_a_filter == "All Players":
                pool_a = elements_df.sort_values(by = "total_points", ascending = False)
                side_a_label = "Side A"
            else:
                pool_a = elements_df[elements_df["owner"] == alias_to_entry_id[team_a_filter]].sort_values(by = "total_points", ascending = False)
                side_a_label = team_a_filter.split(" (")[0]

            choices_a = {0: "➕ None (Empty Slot)"}
            for _, row in pool_a.iterrows():
                choices_a[int(row["id"])] = f"{row['web_name']} ({row['club']} • {row['position']}) | {row['owner_alias']} | {row['total_points']} pts"

            a_p1 = st.selectbox("Side A • Player 1", options = list(choices_a.keys()), format_func = lambda x: choices_a[x], key = "calc_a_p1")
            
            a_p2, a_p3 = 0, 0
            if trade_mode >= 2:
                a_p2_opts = [k for k in choices_a.keys() if k == 0 or k != a_p1]
                a_p2 = st.selectbox("Side A • Player 2", options = a_p2_opts, format_func = lambda x: choices_a[x], key = "calc_a_p2")
            if trade_mode >= 3:
                a_p3_opts = [k for k in choices_a.keys() if k == 0 or k not in (a_p1, a_p2)]
                a_p3 = st.selectbox("Side A • Player 3", options = a_p3_opts, format_func = lambda x: choices_a[x], key = "calc_a_p3")

            side_a_ids = [pid for pid in [a_p1, a_p2, a_p3] if pid != 0]

        # ----------------- SIDE B SELECTION -----------------
        with col_side2:
            st.markdown("### 📥 Side B (Receiving)")
            team_b_filter = st.selectbox("Filter Side B by Squad", team_filter_options, index = 0, key = "calc_team_b_filter")
            if team_b_filter == "All Players":
                pool_b = elements_df.sort_values(by = "total_points", ascending = False)
                side_b_label = "Side B"
            else:
                pool_b = elements_df[elements_df["owner"] == alias_to_entry_id[team_b_filter]].sort_values(by = "total_points", ascending = False)
                side_b_label = team_b_filter.split(" (")[0]

            choices_b = {0: "➕ None (Empty Slot)"}
            for _, row in pool_b.iterrows():
                choices_b[int(row["id"])] = f"{row['web_name']} ({row['club']} • {row['position']}) | {row['owner_alias']} | {row['total_points']} pts"

            b_p1 = st.selectbox("Side B • Player 1", options = list(choices_b.keys()), format_func = lambda x: choices_b[x], key = "calc_b_p1")
            
            b_p2, b_p3 = 0, 0
            if trade_mode >= 2:
                b_p2_opts = [k for k in choices_b.keys() if k == 0 or k != b_p1]
                b_p2 = st.selectbox("Side B • Player 2", options = b_p2_opts, format_func = lambda x: choices_b[x], key = "calc_b_p2")
            if trade_mode >= 3:
                b_p3_opts = [k for k in choices_b.keys() if k == 0 or k not in (b_p1, b_p2)]
                b_p3 = st.selectbox("Side B • Player 3", options = b_p3_opts, format_func = lambda x: choices_b[x], key = "calc_b_p3")

            side_b_ids = [pid for pid in [b_p1, b_p2, b_p3] if pid != 0]

# ----------------- EVALUATION & SASSY VERDICT -----------------
        if side_a_ids or side_b_ids:
            st.divider()
            df_a = elements_df[elements_df["id"].isin(side_a_ids)].copy()
            df_b = elements_df[elements_df["id"].isin(side_b_ids)].copy()

            pts_a, pts_b = int(df_a["total_points"].sum()), int(df_b["total_points"].sum())
            ppg_a, ppg_b = round(float(df_a["points_per_game"].sum()), 1), round(float(df_b["points_per_game"].sum()), 1)
            form_a, form_b = round(float(df_a["form"].sum()), 1), round(float(df_b["form"].sum()), 1)
            val_a, val_b = round(float(df_a["trade_value"].sum()), 1), round(float(df_b["trade_value"].sum()), 1)

            val_diff = round(val_b - val_a, 1) # Positive means Side B is higher rated
            pts_diff = pts_b - pts_a
            ppg_diff = round(ppg_b - ppg_a, 1)
            form_diff = round(form_b - form_a, 1)

            # Correctly map names to sides
            mgr_a_text = side_a_label if side_a_label != "Side A" else "Side A Manager"
            mgr_b_text = side_b_label if side_b_label != "Side B" else "Side B Manager"

            if val_diff >= 0:
                winner_mgr = mgr_b_text
                loser_mgr = mgr_a_text
                winning_side = "Side B"
            else:
                winner_mgr = mgr_a_text
                loser_mgr = mgr_b_text
                winning_side = "Side A"

            abs_val = abs(val_diff)
            abs_ppg = abs(ppg_diff)

            if len(side_a_ids) == 0 or len(side_b_ids) == 0:
                st.info("👀 Pick at least one player on both sides unless you are genuinely proposing a free charity giveaway.")
            elif abs_val <= 1.5:
                st.success(
                    f"🤝 **The Commissar's Verdict: Shockingly Sensible.** "
                    f"Only **{abs_val:.1f}** rating points separate these packages. Nobody is getting mugged off here, "
                    f"so shake hands and hit submit before one of you overthinks it."
                )
            elif abs_val <= 4.5:
                st.info(
                    f"😏 **The Commissar's Verdict: Cheeky Edge to {winner_mgr} ({winning_side}).** "
                    f"**{winner_mgr}** quietly pockets the better end of this swap (**+{abs_val:.1f}** rating / **{abs_ppg:.1f}** PPG gap). "
                    f"It is not quite a war crime, though **{loser_mgr}** is definitely trading on pure vibes and blind hope."
                )
            elif abs_val <= 8.5:
                st.warning(
                    f"🚨 **The Commissar's Verdict: Daylight Robbery.** "
                    f"**{winner_mgr} ({winning_side})** is having **{loser_mgr}**'s pants right down here (**+{abs_val:.1f}** rating advantage). "
                    f"Unless **{loser_mgr}** lost a forfeit or owes money, accepting this is proper mug behaviour."
                )
            else:
                st.error(
                    f"🚓 **The Commissar's Verdict: Call the Police.** "
                    f"This is not a trade, it is a registered charity donation (**+{abs_val:.1f}** rating gulf in favour of **{winner_mgr}**). "
                    f"Put the phone down, step away from the keyboard and check if **{loser_mgr}**'s account has been compromised."
                )

            crocked_a = df_a[df_a["avail_factor"] < 1.0]["web_name"].tolist()
            crocked_b = df_b[df_b["avail_factor"] < 1.0]["web_name"].tolist()
            all_crocked = crocked_a + crocked_b
            if all_crocked:
                st.caption(
                    f"🏥 *Medical Room Alert: {', '.join(all_crocked)} currently carries an injury or suspension flag[cite: 6]. "
                    f"Trying to sneak damaged goods into a package as a 'makeweight' is elite shithousery.*"
                )

            m_c1, m_c2, m_c3, m_c4 = st.columns(4)
            with m_c1:
                st.metric("Side B Net Trade Rating", f"{val_b:.1f}", f"{val_diff:+.1f} vs Side A")
            with m_c2:
                st.metric("Side B Season Points", f"{pts_b}", f"{pts_diff:+d} pts vs Side A")
            with m_c3:
                st.metric("Side B Combined PPG", f"{ppg_b:.1f}", f"{ppg_diff:+.1f} PPG vs Side A")
            with m_c4:
                st.metric("Side B Combined Form", f"{form_b:.1f}", f"{form_diff:+.1f} Form vs Side A")

            b_col1, b_col2 = st.columns(2)
            calc_cols = ["web_name", "position", "club", "owner_alias", "health_status", "total_points", "points_per_game", "form", "next_3", "trade_value"]
            rename_map = {
                "web_name": "Player",
                "position": "Pos",
                "club": "Club",
                "owner_alias": "Owner",
                "health_status": "Status",
                "total_points": "Pts",
                "points_per_game": "PPG",
                "form": "Form",
                "next_3": "Next 3",
                "trade_value": "Rating"
            }

            with b_col1:
                st.markdown(f"**Side A Package ({len(side_a_ids)}/{trade_mode} Players)**")
                if not df_a.empty:
                    view_a = format_table_floats(df_a[calc_cols].rename(columns = rename_map))
                    st.table(view_a.set_index("Player"))
                else:
                    st.caption("No players selected for Side A.")

            with b_col2:
                st.markdown(f"**Side B Package ({len(side_b_ids)}/{trade_mode} Players)**")
                if not df_b.empty:
                    view_b = format_table_floats(df_b[calc_cols].rename(columns = rename_map))
                    st.table(view_b.set_index("Player"))
                else:
                    st.caption("No players selected for Side B.")
# ----------------- 7. GACS SECTION (GOALS, ASSISTS AND CLEAN SHEETS) -----------------
elif st.session_state.page in ["GACS", "XI Stats"]:
    st.title("🎯 GACS" + dash + selected_league_key)
    
    static_data = fetch_fpl_static()
    league_details, _ = fetch_league_data(active_league_id)
    all_fixtures = fetch_all_epl_fixtures()
    
    if not static_data or not league_details:
        st.error("Failed to load league data. Verify connection.")
        st.stop()
        
    entries = league_details.get("league_entries", [])
    matches = league_details.get("matches", [])
    
    if not entries or not matches:
        st.warning("No league data available for this competition.")
        st.stop()

    pos_map = {item["id"]: item["singular_name_short"] for item in static_data["element_types"]}
    team_map = {item["id"]: item["short_name"] for item in static_data["teams"]}
    element_lookup = {item["id"]: item for item in static_data["elements"]}
    
    all_events = sorted(list({m["event"] for m in matches}))
    unplayed_events = sorted(list({m["event"] for m in matches if not m.get("finished", False)}))
    current_gw = unplayed_events[0] if unplayed_events else (all_events[-1] if all_events else 1)

    render_xi_stats_view(entries, current_gw, element_lookup, pos_map, team_map, all_fixtures)

# ----------------- 8. DISCIPLINARY SECTION -----------------
elif st.session_state.page == "Disciplinary":
    st.title("🟨🟥 Disciplinary" + dash + selected_league_key)

    league_details, _ = fetch_league_data(active_league_id)
    if not league_details:
        st.error("Failed to load league data. Verify connection.")
        st.stop()

    matches = league_details.get("matches", [])
    if not matches:
        st.warning("No league data available for this competition.")
        st.stop()

    all_events = sorted(list({m["event"] for m in matches}))
    unplayed_events = sorted(list({m["event"] for m in matches if not m.get("finished", False)}))
    current_gw = unplayed_events[0] if unplayed_events else (all_events[-1] if all_events else 1)

    render_disciplinary_view(active_league_id, current_gw, key_suffix = "page")

# ----------------- 9. STANDINGS SECTION -----------------
elif st.session_state.page == "Standings":
    st.title("🏆 Standings" + dash + selected_league_key)
    
    static_data = fetch_fpl_static()
    league_details, _ = fetch_league_data(active_league_id)
    all_fixtures = fetch_all_epl_fixtures()
    
    if not static_data or not league_details:
        st.error("Failed to load league standings. Verify connection.")
        st.stop()
        
    entries = league_details.get("league_entries", [])
    matches = league_details.get("matches", [])
    
    if not entries or not matches:
        st.warning("No league table data available for this competition.")
        st.stop()

    pos_map = {item["id"]: item["singular_name_short"] for item in static_data["element_types"]}
    team_map = {item["id"]: item["short_name"] for item in static_data["teams"]}
    element_lookup = {item["id"]: item for item in static_data["elements"]}
    
    all_events = sorted(list({m["event"] for m in matches}))
    unplayed_events = sorted(list({m["event"] for m in matches if not m.get("finished", False)}))

    if unplayed_events:
        current_gw = unplayed_events[0]
    else:
        current_gw = all_events[-1] if all_events else 1

    last_completed_gw = current_gw - 1 if current_gw > 1 else 1

    live_data = fetch_live_event(current_gw)
    live_elements = live_data.get("elements", {}) if live_data else {}
    
    club_minutes = {}
    for elem_str_id, e_info in live_elements.items():
        elem_int_id = int(elem_str_id)
        elem_obj = element_lookup.get(elem_int_id, {})
        c_id = elem_obj.get("team")
        if c_id:
            m_val = e_info.get("stats", {}).get("minutes", 0)
            club_minutes[c_id] = club_minutes.get(c_id, 0) + m_val

    official_table_df, live_table_df = calculate_league_tables(
        entries, matches, current_gw, live_elements, element_lookup, club_minutes, pos_map, team_map, all_fixtures
    )

    standings_tab1, standings_tab2, standings_tab3, standings_tab4 = st.tabs([
        "🟢 Live Standings",
        f"📊 Official Standings (GW {last_completed_gw})",
        "🎯 GACS",
        "🟨🟥 Discipline"
    ])

    with standings_tab1:
        st.subheader("Live Standings " + dash + " Active Round (GW " + str(current_gw) + ")")
        st.caption("Updated continuously with active points. Movement indicators show changes against previous official rank.")
        
        # Strip raw inline HTML spans for mobile table parity, while keeping clean directional indicators
        clean_live_df = live_table_df.copy()
        clean_live_df["Move"] = clean_live_df["Move"].str.replace(r"<[^>]*>", "", regex = True)
        st.table(clean_live_df)

    with standings_tab2:
        st.subheader("Official Standings " + dash + " Frozen Table (GW " + str(last_completed_gw) + ")")
        st.caption("Standings after the most recently concluded gameweek.")
        st.table(official_table_df)

    with standings_tab3:
        render_xi_stats_view(entries, current_gw, element_lookup, pos_map, team_map, all_fixtures)

    with standings_tab4:
        render_disciplinary_view(active_league_id, current_gw, key_suffix = "standings")

# ----------------- 10. NEWSLETTERS SECTION -----------------
elif st.session_state.page == "Newsletters":
    st.title("Dellarverse Gazette")
    st.caption("Official match reports, power rankings and editorial coverage")

    news_tab1, news_tab2 = st.tabs(["📰 League Newsletter", "🏆 Cup Newsletter"])

    with news_tab1:
        st.subheader("Official League Gazette")
        render_pdf("latest_league.pdf", "League Newsletter")

    with news_tab2:
        st.subheader("Official Cup Gazette")
        render_pdf("latest_cup.pdf", "Cup Newsletter")

# ----------------- 11. POWER RANKINGS SECTION -----------------
elif st.session_state.page == "Power Rankings":
    top_p1, top_p2 = st.columns([5, 1])
    with top_p1:
        st.title("⚡ Power Rankings" + dash + selected_league_key)
        st.caption("Official form guide, momentum ratings and team trajectories")
    with top_p2:
        st.write("")
        if st.button("🔄 Refresh", use_container_width = True, key = "btn_refresh_power"):
            st.rerun()

    filename, sheets_dict, raw_bytes = load_power_rankings_data()

    if not filename or sheets_dict is None:
        st.warning("No Power Rankings spreadsheet found. Place 'Power Rankings.ods', .xlsx or .csv in your Assets folder.")
    elif isinstance(sheets_dict, Exception):
        st.error(f"Error reading {filename}: {str(sheets_dict)}")
        st.info("Ensure **odfpy** is added to your requirements.txt file if uploading an .ods file.")
    else:
        st.download_button(
            label = f"📥 Download Archive ({filename})",
            data = raw_bytes,
            file_name = filename,
            mime = "application/octet-stream",
            use_container_width = False
        )
        st.write("")

        valid_sheets = {name: df for name, df in sheets_dict.items() if df is not None and not df.empty}
        sheet_names = list(valid_sheets.keys())

        def render_sheet_content(df_raw):
            df_formatted = format_table_floats(df_raw.fillna(""))
            cleaned_cols = []
            counts = {}
            for c in df_formatted.columns:
                col_name = str(c).strip()
                if col_name in counts:
                    counts[col_name] += 1
                    cleaned_cols.append(f"{col_name}_{counts[col_name]}")
                else:
                    counts[col_name] = 0
                    cleaned_cols.append(col_name)
            df_formatted.columns = cleaned_cols
            if len(df_formatted.columns) > 1:
                first_col = df_formatted.columns[0]
                st.table(df_formatted.set_index(first_col))
            else:
                st.table(df_formatted)

        if not sheet_names:
            st.info("No data in this sheet.")
        elif len(sheet_names) == 1:
            render_sheet_content(valid_sheets[sheet_names[0]])
        else:
            p_tabs = st.tabs(sheet_names)
            for idx, s_name in enumerate(sheet_names):
                with p_tabs[idx]:
                    render_sheet_content(valid_sheets[s_name])


# ----------------- ASTERISK* LEAGUE HISTORY & ARCHIVES -----------------
elif st.session_state.page == "Asterisk*":
    top_h1, top_h2 = st.columns([5, 1])
    with top_h1:
        st.title("📜 Asterisk* — Master League Archives")
        st.caption("10 Seasons of Power Query data, manager profiles, historical records and season chronicles")
    with top_h2:
        st.write("")
        if st.button("🔄 Refresh Archive", use_container_width = True, key = "btn_refresh_asterisk"):
            st.rerun()

    @st.cache_data(ttl = 3600)
    def load_asterisk_workbook():
        target_file = assets_folder / "Asterisk.xlsx"
        if not target_file.exists():
            target_file = base_dir / "Asterisk.xlsx"
        if not target_file.exists():
            return None
        try:
            return pd.read_excel(target_file, sheet_name = None, engine = "openpyxl")
        except Exception as e:
            return e

    asterisk_sheets = load_asterisk_workbook()

    if not asterisk_sheets or isinstance(asterisk_sheets, Exception):
        st.warning("⚠️ 'Asterisk.xlsx' not found in your Assets or base directory. Please ensure it is placed in the Assets folder.")
    else:
        valid_sheets = {name: df for name, df in asterisk_sheets.items() if df is not None and not df.empty}
        
        ast_tabs = st.tabs([
            "🏆 Palmares & Records", 
            "👤 Manager Career Hub", 
            "🔥 All-Time Streaks", 
            "📖 Season Bios & Chronicles",
            "📊 Historical Standings"
        ])

        with ast_tabs[0]:
            st.subheader("Palmares & All-Time Honor Roll")
            palmares_df = valid_sheets.get("Palmares & Records")
            if palmares_df is not None:
                st.table(format_table_floats(palmares_df.fillna("")))
            else:
                st.info("Palmares & Records sheet not found.")

        with ast_tabs[1]:
            st.subheader("Manager Career Profiles")
            profiles_df = valid_sheets.get("qPlayerProfiles")
            if profiles_df is not None and "Player" in profiles_df.columns:
                selected_mgr = st.selectbox("Select Manager", sorted(profiles_df["Player"].dropna().unique()), key = "ast_mgr_sel")
                mgr_row = profiles_df[profiles_df["Player"] == selected_mgr]
                st.dataframe(format_table_floats(mgr_row.T.reset_index().rename(columns={"index": "Metric", 0: "Value"})).set_index("Metric"), use_container_width = True)
            else:
                st.info("qPlayerProfiles sheet unavailable.")

        with ast_tabs[2]:
            st.subheader("All-Time Streaks & Form Records")
            streaks_df = valid_sheets.get("qLeagueStreaks")
            if streaks_df is not None:
                st.table(format_table_floats(streaks_df.fillna("")))
            else:
                st.info("qLeagueStreaks sheet unavailable.")

        with ast_tabs[3]:
            st.subheader("Season Chronicles & Bios")
            bios_df = valid_sheets.get("Season Bios")
            if bios_df is not None:
                for _, row in bios_df.iterrows():
                    season_title = str(row.iloc[0]) if not pd.isna(row.iloc[0]) else "Season"
                    season_years = str(row.iloc[1]) if not pd.isna(row.iloc[1]) else ""
                    season_text = str(row.iloc[2]) if len(row) > 2 and not pd.isna(row.iloc[2]) else "No narrative recorded."
                    with st.expander(f"📖 {season_title} ({season_years})"):
                        st.write(season_text)
            else:
                st.info("Season Bios sheet unavailable.")

        with ast_tabs[4]:
            st.subheader("Historical Standings Archive")
            standings_df = valid_sheets.get("qStandings")
            if standings_df is not None:
                s_div = st.selectbox("Filter Division", ["All"] + list(standings_df["Division"].dropna().unique()), key = "ast_standings_div")
                s_seas = st.selectbox("Filter Season", ["All"] + list(standings_df["Season"].dropna().unique()), key = "ast_standings_seas")
                
                filtered_st = standings_df.copy()
                if s_div != "All":
                    filtered_st = filtered_st[filtered_st["Division"] == s_div]
                if s_seas != "All":
                    filtered_st = filtered_st[filtered_st["Season"] == s_seas]
                    
                st.table(format_table_floats(filtered_st.fillna("")))
            else:
                st.info("qStandings sheet unavailable.")
import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import math
import altair as alt
from pathlib import Path
import pypdfium2 as pdfium

base_dir = Path(__file__).resolve().parent

# Check for Assets directory
assets_folder = base_dir / "Assets"
if not assets_folder.exists():
    assets_folder = base_dir / "assets"

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

# Thematic identity colors extracted directly from the Season X league crests
LEAGUE_THEMES = {
    "CDP (Crème Dellar Prem)": {
        "accent": "#f59e0b",
        "accent_glow": "rgba(245, 158, 11, 0.25)",
        "badge_bg": "#231804",
        "tag": "PREMIER DIVISION"
    },
    "SDM (Segundo Del Mundo)": {
        "accent": "#3b82f6",
        "accent_glow": "rgba(59, 130, 246, 0.25)",
        "badge_bg": "#06152d",
        "tag": "SEGUNDO DIVISION"
    },
    "BDR (Best De La Rest)": {
        "accent": "#f97316",
        "accent_glow": "rgba(249, 115, 22, 0.25)",
        "badge_bg": "#271004",
        "tag": "DIVISION THREE"
    },
    "LDE (Liger Del Eager)": {
        "accent": "#22c55e",
        "accent_glow": "rgba(34, 197, 94, 0.25)",
        "badge_bg": "#052210",
        "tag": "DIVISION FOUR"
    }
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

def format_remaining_players(in_play, yet_to_play):
    if in_play > 0 and yet_to_play > 0:
        return str(in_play) + " in play, " + str(yet_to_play) + " yet to play"
    if in_play > 0:
        return str(in_play) + " in play"
    if yet_to_play > 0:
        return str(yet_to_play) + " yet to play"
    return "0 to play"

def format_table_floats(df):
    if df is None or df.empty:
        return df
    formatted = df.copy()
    for col in formatted.columns:
        s_num = pd.to_numeric(formatted[col], errors = "coerce")
        if s_num.notna().any():
            non_null = s_num.dropna()
            if (non_null % 1 == 0).all():
                formatted[col] = formatted[col].map(
                    lambda x: f"{int(round(float(x)))}" if pd.notna(x) and str(x).strip() != "" and str(x).strip().lower() != "nan" else ""
                )
            else:
                formatted[col] = s_num.map(
                    lambda x: f"{x:.1f}" if pd.notna(x) else ""
                )
    return formatted.fillna("")

# Sidebar Brand and Ordered Navigation
if logo_path.exists():
    st.sidebar.image(str(logo_path), use_container_width = True)
else:
    st.sidebar.title("CDP App")

st.sidebar.caption("Stats, not facts | Season X Command Center")

NAV_ITEMS = [
    "Home",
    "LIVE SCORES",
    "EPL Scores",
    "Results Analyser",
    "Cup & Bucket",
    "Squad Analyser",
    "GACS",
    "Standings",
    "Newsletters",
    "Power Rankings",
    "Records"
]

st.sidebar.radio(
    "Navigation Menu",
    NAV_ITEMS,
    key = "page"
)

st.sidebar.divider()
st.sidebar.subheader("League Selection")

selected_league_key = st.sidebar.selectbox(
    "Active Competition",
    list(LEAGUE_PRESETS.keys()),
    key = "active_competition"
)
active_league_id = LEAGUE_PRESETS[selected_league_key]
active_theme = LEAGUE_THEMES.get(selected_league_key, LEAGUE_THEMES["CDP (Crème Dellar Prem)"])

# Dynamic Pure Black CSS Engine with Adaptive League Accent
st.markdown(f"""
<style>
    .stApp {{
        background-color: #000000 !important;
        color: #f1f5f9 !important;
    }}

    section[data-testid="stSidebar"] {{
        background-color: #06070a !important;
        border-right: 1px solid #141824 !important;
    }}

    h1, h2, h3, h4, h5, h6 {{
        color: #ffffff !important;
        font-weight: 700 !important;
        letter-spacing: -0.3px !important;
    }}

    p, span, label, div {{
        color: #e2e8f0;
    }}

    .stCaption, small {{
        color: #64748b !important;
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

    table {{
        color: #f1f5f9 !important;
        background-color: #090c13 !important;
        border-collapse: collapse !important;
        width: 100% !important;
        border-radius: 6px !important;
        overflow: hidden !important;
    }}
    
    thead tr th {{
        background-color: #0e131d !important;
        color: {active_theme['accent']} !important;
        border-bottom: 2px solid #182030 !important;
        font-weight: 700 !important;
        padding: 6px 10px !important;
        font-size: 0.85rem !important;
        text-align: left !important;
    }}
    
    tbody tr td, tbody tr th {{
        background-color: #090c13 !important;
        border-bottom: 1px solid #141a26 !important;
        color: #cbd5e1 !important;
        padding: 6px 10px !important;
        font-size: 0.85rem !important;
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
    }}

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
        font-size: 1rem !important;
    }}

    li[role="option"]:hover,
    li[role="option"]:hover *,
    [role="option"]:hover,
    [role="option"]:hover * {{
        background-color: #f1f5f9 !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }}

    div[data-testid="stVegaLiteChart"],
    div[data-testid="stVegaLiteChart"] > div,
    .vega-embed,
    .vega-embed canvas,
    .vega-embed svg {{
        background-color: #000000 !important;
    }}

    button[kind="primary"] {{
        background-color: {active_theme['accent']} !important;
        color: #000000 !important;
        font-weight: 800 !important;
        border: none !important;
        border-radius: 6px !important;
        box-shadow: 0 0 12px {active_theme['accent_glow']} !important;
    }}

    button[kind="primary"]:hover {{
        filter: brightness(1.15);
        color: #000000 !important;
    }}

    button[kind="secondary"] {{
        background-color: #0e121a !important;
        color: #ffffff !important;
        border: 1px solid #20293d !important;
        border-radius: 6px !important;
    }}

    button[kind="secondary"]:hover {{
        border-color: {active_theme['accent']} !important;
        color: {active_theme['accent']} !important;
    }}

    div[data-testid="stProgressBar"] > div {{
        background-color: #121824 !important;
    }}
    div[data-testid="stProgressBar"] > div > div {{
        background-color: {active_theme['accent']} !important;
    }}
</style>
""", unsafe_allow_html = True)

def render_pdf(filename, title):
    folder = base_dir / "Newsletters"
    if not folder.exists():
        folder = base_dir / "newsletters"
        
    if not folder.exists():
        st.error("Folder not found. Ensure either Newsletters or newsletters exists in your repository root.")
        return

    target = None
    for f in folder.iterdir():
        if f.is_file() and f.name.lower() == filename.lower():
            target = f
            break

    if not target or not target.exists():
        st.warning("Could not find " + filename + " inside " + folder.name + "/")
        available = [f.name for f in folder.iterdir() if f.is_file()]
        if available:
            st.info("Files currently in " + folder.name + "/: " + ", ".join(available))
        return

    pdf_bytes = target.read_bytes()

    st.download_button(
        label = "📥 Download " + title + " (PDF)",
        data = pdf_bytes,
        file_name = target.name,
        mime = "application/pdf",
        use_container_width = True
    )

    try:
        pdf = pdfium.PdfDocument(pdf_bytes)
        for page_index in range(len(pdf)):
            page = pdf[page_index]
            image = page.render(scale = 2).to_pil()
            st.image(image, use_container_width = True)
    except Exception as e:
        st.error("Error rendering PDF pages: " + str(e))

def load_records_data():
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
                if f.is_file() and f.suffix.lower() in valid_extensions and "records" in f.name.lower():
                    target_file = f
                    break
        if target_file:
            break
            
    if not target_file:
        for folder in potential_folders:
            if folder.exists() and folder.is_dir():
                for f in folder.iterdir():
                    if f.is_file() and f.suffix.lower() in valid_extensions and "power" not in f.name.lower() and "cup" not in f.name.lower():
                        target_file = f
                        break
            if target_file:
                break

    if not target_file or not target_file.exists():
        return None, None, None

    ext = target_file.suffix.lower()
    raw_bytes = target_file.read_bytes()
    try:
        if ext == ".csv":
            df = pd.read_csv(target_file)
            return target_file.name, {"All Records": df}, raw_bytes
        elif ext == ".ods":
            sheets = pd.read_excel(target_file, engine = "odf", sheet_name = None)
            return target_file.name, sheets, raw_bytes
        else:
            sheets = pd.read_excel(target_file, engine = "openpyxl", sheet_name = None)
            return target_file.name, sheets, raw_bytes
    except Exception as err:
        return target_file.name, err, raw_bytes

def load_power_rankings_data():
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
                if f.is_file() and f.suffix.lower() in valid_extensions:
                    name_clean = f.name.lower().replace(" ", "").replace("_", "")
                    if "power" in name_clean or "ranking" in name_clean:
                        target_file = f
                        break
        if target_file:
            break

    if target_file and target_file.exists():
        ext = target_file.suffix.lower()
        raw_bytes = target_file.read_bytes()
        try:
            if ext == ".csv":
                df = pd.read_csv(target_file)
                return target_file.name, {"Power Rankings": df}, raw_bytes
            elif ext == ".ods":
                sheets = pd.read_excel(target_file, engine = "odf", sheet_name = None)
                return target_file.name, sheets, raw_bytes
            else:
                sheets = pd.read_excel(target_file, engine = "openpyxl", sheet_name = None)
                return target_file.name, sheets, raw_bytes
        except Exception as err:
            return target_file.name, err, raw_bytes

    for folder in potential_folders:
        if folder.exists() and folder.is_dir():
            for f in folder.iterdir():
                if f.is_file() and f.suffix.lower() in [".ods", ".xlsx", ".xls"]:
                    try:
                        eng = "odf" if f.suffix.lower() == ".ods" else "openpyxl"
                        sheets = pd.read_excel(f, engine = eng, sheet_name = None)
                        for s_name, s_df in sheets.items():
                            if "power" in s_name.lower():
                                return f.name, {s_name: s_df}, f.read_bytes()
                    except Exception:
                        pass

    return None, None, None

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

@st.cache_data(ttl = 3600)
def fetch_fpl_static():
    url = "https://draft.premierleague.com/api/bootstrap" + chr(45) + "static"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    return response.json()

@st.cache_data(ttl = 600)
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

@st.cache_data(ttl = 600)
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

@st.cache_data(ttl = 60)
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

@st.cache_data(ttl = 3600)
def fetch_all_epl_fixtures():
    url = "https://fantasy.premierleague.com/api/fixtures/"
    resp = requests.get(url)
    if resp.status_code != 200:
        return []
    return resp.json()

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
        if live1 > live2:
            return 100, 0
        if live2 > live1:
            return 0, 100
        return 50, 50

    margin = proj1 - proj2
    spread = max(6.0, total_left * 2.8)
    prob1 = 1.0 / (1.0 + math.exp(-margin / (spread / 1.7)))
    pct1 = int(round(prob1 * 100))
    pct1 = max(1, min(99, pct1))
    return pct1, 100 - pct1

def calculate_optimum_score(all_players_df):
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
                score = best_gk + int(defs.nlargest(d, "Pts")["Pts"].sum()) + int(mids.nlargest(m, "Pts")["Pts"].sum()) + int(fwds.nlargest(f, "Pts")["Pts"].sum())
                if score > best_score:
                    best_score = score
    return best_score if best_score != -1 else (best_gk + int(defs["Pts"].sum()) + int(mids["Pts"].sum()) + int(fwds["Pts"].sum()))

def get_fdr_multiplier(team_id, current_gw, all_fixtures_list):
    if not all_fixtures_list or not team_id:
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

def evaluate_lineup(picks_list, live_elements, element_lookup, club_minutes, pos_map, team_map, current_gw, all_fixtures_list):
    if not picks_list:
        return pd.DataFrame(), pd.DataFrame(), 0, 0.0, 0, 0, 0, 0
        
    raw_players = []
    for p in picks_list.get("picks", []):
        elem_id = p["element"]
        raw_elem = element_lookup.get(elem_id, {})
        stats = live_elements.get(str(elem_id), {}).get("stats", {})
        
        pos_type = raw_elem.get("element_type", 1)
        pos_str = pos_map.get(pos_type, "")
        club_id = raw_elem.get("team")
        
        mins = stats.get("minutes", 0)
        pts = stats.get("total_points", 0)
        team_mins = club_minutes.get(club_id, 0)
        
        avail = get_availability_multiplier(raw_elem)
        
        # Option 1: Flipped Base Recipe (60% PPG / 40% Form)
        form_val = float(raw_elem.get("form") or 0.0)
        ppg_val = float(raw_elem.get("points_per_game") or 2.0)
        base_exp = ((ppg_val * 0.6) + (form_val * 0.4)) * avail
        
        # Option 3: Minutes Security Check (Rotation Risk / Fringe Player penalty)
        season_mins = float(raw_elem.get("minutes") or 0.0)
        if current_gw > 3:
            expected_min_ratio = season_mins / max(1.0, float(current_gw * 60))
            if expected_min_ratio < 0.6:
                base_exp *= 0.8
                
        if base_exp <= 0 and avail > 0:
            base_exp = 2.0
            
        fdr_mult = get_fdr_multiplier(club_id, current_gw, all_fixtures_list)
        base_exp *= fdr_mult

        if team_mins >= 800:
            if mins > 0:
                state = "FT"
                proj = pts
            else:
                state = "DNP"
                proj = 0
        elif team_mins > 0:
            state = "LIVE"
            match_minute = 45
            if all_fixtures_list:
                for fix in all_fixtures_list:
                    if fix.get("event") == current_gw and (fix.get("team_h") == club_id or fix.get("team_a") == club_id):
                        match_minute = fix.get("minutes", 45)
                        break
            
            return_expect = max(0.0, base_exp - 2.0)
            remaining_fraction = max(0.0, (90.0 - match_minute) / 90.0)
            
            if match_minute < 60:
                upcoming_app_pts = 1.0 if match_minute < 60 else 0.0
                proj = round(float(pts) + upcoming_app_pts + (return_expect * remaining_fraction), 1)
            else:
                proj = round(float(pts) + (return_expect * remaining_fraction), 1)
        else:
            state = "YTP"
            proj = round(base_exp, 1)
            
        raw_players.append({
            "id": elem_id,
            "Player": raw_elem.get("web_name", "Unknown"),
            "pos_num": pos_type,
            "Pos": pos_str,
            "Club": team_map.get(club_id, ""),
            "club_id": club_id,
            "State": state,
            "Mins": mins,
            "Pts": pts,
            "Proj": proj,
            "G": stats.get("goals_scored", 0),
            "A": stats.get("assists", 0),
            "CS": stats.get("clean_sheets", 0),
            "GC": stats.get("goals_conceded", 0),
            "Bonus": stats.get("bonus", 0),
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
    live_score = sum(p["Pts"] for p in active_lineup)
    proj_score = sum(p["Proj"] for p in active_lineup)
    
    in_play = sum(1 for p in active_lineup if p["State"] == "LIVE")
    yet_to_play = sum(1 for p in active_lineup if p["State"] == "YTP")
    
    active_p = []
    if not starters.empty:
        active_p.extend([int(r["Pts"]) for _, r in starters.iterrows() if r.get("sub_action") != "Subbed Off"])
    if not bench.empty:
        active_p.extend([int(r["Pts"]) for _, r in bench.iterrows() if r.get("sub_action") == "Subbed On"])

    bench_left_pts = sum(int(b["Pts"]) for b in bench if b["sub_action"] != "Subbed On")
    all_players_df = pd.DataFrame(raw_players)
    optimum_score = calculate_optimum_score(all_players_df)
    
    starters_df = pd.DataFrame(starters).sort_values(by = ["pos_num", "Pts"], ascending = [True, False])
    bench_df = pd.DataFrame(bench).sort_values(by = "pick_pos", ascending = True)
    
    return starters_df, bench_df, live_score, round(proj_score, 1), in_play, yet_to_play, bench_left_pts, optimum_score

@st.cache_data(ttl = 300)
def resolve_cup_match_score(manager_alias, gw_num):
    teams_registry = get_all_32_teams_registry()
    static_data = fetch_fpl_static()
    all_fixtures = fetch_all_epl_fixtures()
    if not static_data:
        return 0, 0, pd.DataFrame(), pd.DataFrame(), 0, 0, 0, 0
    pos_map = {item["id"]: item["singular_name_short"] for item in static_data["element_types"]}
    team_map = {item["id"]: item["short_name"] for item in static_data["teams"]}
    element_lookup = {item["id"]: item for item in static_data["elements"]}

    t_info = teams_registry.get(str(manager_alias).strip().lower())
    if not t_info or not t_info.get("entry_id"):
        return 0, 0, pd.DataFrame(), pd.DataFrame(), 0, 0, 0, 0
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
    active_p = []
    if not starters.empty:
        active_p.extend([int(r["Pts"]) for _, r in starters.iterrows() if r.get("sub_action"] != "Subbed Off"])
    if not bench.empty:
        active_p.extend([int(r["Pts"]) for _, r in bench.iterrows() if r.get("sub_action") == "Subbed On"])

    max_player_pts = max(active_p) if active_p else 0
    return live_score, max_player_pts, starters, bench, in_play, ytp, bench_pts, opt_score

@st.cache_data(ttl = 300)
def calculate_group_standings():
    cup_df = load_cup_matches()
    teams_registry = get_all_32_teams_registry()
    if cup_df is None or cup_df.empty:
        return []

    group_matches = cup_df[(cup_df["Week"] <= 20) & (cup_df["Stage"].str.lower().str.contains("group"))].copy()

    unique_aliases = set()
    for _, r in group_matches.iterrows():
        m1 = str(r.get("Team 1", "")).strip()
        m2 = str(r.get("Team 2", "")).strip()
        if m1 and m1.lower() != "nan":
            unique_aliases.add(m1)
        if m2 and m2.lower() != "nan":
            unique_aliases.add(m2)

    standings_dict = {
        m: {
            "Manager": m,
            "Team": teams_registry.get(m.lower(), {}).get("team_name", m),
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

        s1, high1, _, _, _, _, _, _ = resolve_cup_match_score(m1, gw)
        s2, high2, _, _, _, _, _, _ = resolve_cup_match_score(m2, gw)

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

    import functools
    sorted_rows = sorted(rows, key = functools.cmp_to_key(sort_tiebreakers))

    display_table = []
    for rank, item in enumerate(sorted_rows, 1):
        if rank <= 8:
            zone = "🏆 Cup (Top 8)"
        elif rank <= 24:
            zone = "⚔️ Playoff (9-24)"
        else:
            zone = "🪣 Bucket (25-32)"

        display_table.append({
            "Pos": rank,
            "Zone": zone,
            "Manager": item["Manager"],
            "Team": item["Team"],
            "Div": item["Division"],
            "W": item["W"],
            "D": item["D"],
            "L": item["L"],
            "PF": item["PF"],
            "Pts": item["Pts"],
            "Best XI Pt": item["High_Score"]
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
            r["Move"] = "▲ " + str(diff)
        elif diff < 0:
            r["Move"] = "▼ " + str(abs(diff))
        else:
            r["Move"] = "▬"

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

    col_brand, col_intro = st.columns([1, 4])
    with col_brand:
        if logo_path.exists():
            st.image(str(logo_path), use_container_width = True)
    with col_intro:
        st.markdown(f"""
        <div style="margin-top: 5px;">
            <h1 style="margin: 0.1rem 0 0.1rem 0; font-size: 2.4rem;">CDP App {dash} Season X</h1>
            <p style="color: #94a3b8; margin: 0; font-size: 0.95rem;">Dellarverse HQ: Central Draft Intelligence, Live Projections and Official Publications</p>
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
            gap: 12px;
            width: 100%;
        }}
        .card {{
            flex: 1;
            background-color: #090c13;
            border: 1px solid #182030;
            border-radius: 8px;
            padding: 10px 14px;
            transition: border 0.2s ease;
        }}
        .card:hover {{
            border-color: {active_theme['accent']};
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 3px;
        }}
        .title {{
            font-size: 0.74rem;
            font-weight: 700;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .gw-tag {{
            font-size: 0.68rem;
            font-weight: 800;
            color: {active_theme['accent']};
            background-color: {active_theme['badge_bg']};
            border: 1px solid {active_theme['accent']};
            padding: 1px 6px;
            border-radius: 4px;
        }}
        .clock-row {{
            display: flex;
            gap: 8px;
            align-items: baseline;
            margin: 2px 0 3px 0;
        }}
        .num {{
            font-family: "SF Mono", "Consolas", "Courier New", monospace;
            font-size: 1.5rem;
            font-weight: 800;
            color: #ffffff;
        }}
        .sec-num {{
            font-family: "SF Mono", "Consolas", "Courier New", monospace;
            font-size: 1.5rem;
            font-weight: 800;
            color: {active_theme['accent']};
        }}
        .unit {{
            font-size: 0.72rem;
            font-weight: 600;
            color: #64748b;
            margin-left: 1px;
        }}
        .sub {{
            font-size: 0.72rem;
            color: #64748b;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        @media (max-width: 600px) {{
            .container {{
                flex-direction: column;
                gap: 8px;
            }}
            .card {{
                padding: 8px 12px;
            }}
            .num, .sec-num {{
                font-size: 1.3rem;
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
            <div id="waiver-sub" class="sub">Calculating local time...</div>
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
            <div id="lineup-sub" class="sub">Calculating local time...</div>
        </div>
    </div>

    <script>
        const waiverTarget = new Date("{waiver_iso}").getTime();
        const lineupTarget = new Date("{lineup_iso}").getTime();

        const opts = {{ weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }};
        if (!isNaN(waiverTarget)) {{
            const wLocal = new Date(waiverTarget).toLocaleDateString(undefined, opts);
            document.getElementById("waiver-sub").textContent = wLocal + " (24h before kickoff)";
        }}
        if (!isNaN(lineupTarget)) {{
            const lLocal = new Date(lineupTarget).toLocaleDateString(undefined, opts);
            document.getElementById("lineup-sub").textContent = lLocal + " (90m before kickoff)";
        }}

        function updateClocks() {{
            const now = new Date().getTime();

            function renderTimer(target, clockId, subId, passedText) {{
                const clockEl = document.getElementById(clockId);
                const subEl = document.getElementById(subId);
                if (!clockEl) return;

                const diff = target - now;
                if (isNaN(target) || diff <= 0) {{
                    clockEl.innerHTML = '<span style="color: #ef4444; font-weight: 800; font-size: 1.15rem; font-family: monospace;">DEADLINE PASSED</span>';
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

            renderTimer(waiverTarget, 'waiver-clock', 'waiver-sub', 'Waivers Processed • Free Agency Active');
            renderTimer(lineupTarget, 'lineup-clock', 'lineup-sub', 'Lineups Locked • Round in Progress');
        }}

        updateClocks();
        setInterval(updateClocks, 1000);
    </script>
    </body>
    </html>
    """
    components.html(countdown_html, height = 155)

    st.markdown("#### Quick Launchpad")
    
    r1_c1, r1_c2, r1_c3, r1_c4 = st.columns(4)
    with r1_c1:
        st.button("🔴 LIVE SCORES", on_click = set_page, args = ("LIVE SCORES",), type = "primary", use_container_width = True)
    with r1_c2:
        st.button("⚽ EPL Scores", on_click = set_page, args = ("EPL Scores",), use_container_width = True)
    with r1_c3:
        st.button("Results Analyser", on_click = set_page, args = ("Results Analyser",), use_container_width = True)
    with r1_c4:
        st.button("Cup & Bucket", on_click = set_page, args = ("Cup & Bucket",), use_container_width = True)

    st.write("")
    r2_c1, r2_c2, r2_c3, r2_c4, r2_c5 = st.columns(5)
    with r2_c1:
        st.button("Squad Analyser", on_click = set_page, args = ("Squad Analyser",), use_container_width = True)
    with r2_c2:
        st.button("🎯 GACS", on_click = set_page, args = ("GACS",), use_container_width = True)
    with r2_c3:
        st.button("Standings", on_click = set_page, args = ("Standings",), use_container_width = True)
    with r2_c4:
        st.button("Newsletters", on_click = set_page, args = ("Newsletters",), use_container_width = True)
    with r2_c5:
        st.button("⚡ Power Rankings", on_click = set_page, args = ("Power Rankings",), use_container_width = True)

    st.divider()

    st.subheader("Core Capabilities")
    st.markdown("* **LIVE SCORES**: Around the grounds matchday scoreboard, manager aliases, live win probabilities and real time auto subs.")
    st.markdown("* **Cup & Bucket**: Cross-league tournament portal featuring 32-team group standings, live cup scoreboards and cup results analyser.")
    st.markdown("* **EPL Scores**: Premier League fixtures, goalscorers, assists, clean sheets, DEFCON metrics and discipline.")
    st.markdown("* **Results Analyser**: Historical head to head match breakdowns and chronological matchday points progression graphs.")
    st.markdown("* **Squad Analyser**: Starting lineup recommendations, next 3 fixtures, injury tracking and tailored waiver wire scout board.")
    st.markdown("* **GACS**: Weekly starting lineup goals, assists and clean sheets with gameweek selection.")
    st.markdown("* **Standings**: Real time in play standings with movement indicators and official frozen tables.")
    st.markdown("* **Newsletters**: Embedded full page previews for both League and Cup gazettes.")
    st.markdown("* **Power Rankings**: Comprehensive form rankings and team trajectories.")
    st.markdown("* **Records**: Historical hall of fame, individual records and statistical milestones.")

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

    top_c1, top_c2, top_c3 = st.columns([3, 2, 1])
    with top_c1:
        st.caption("Real time scoreline forecast, live projections and in match win probability")
    with top_c2:
        current_gw = st.selectbox(
            "Active Gameweek",
            all_events,
            index = all_events.index(detected_gw) if detected_gw in all_events else 0
        )
    with top_c3:
        st.write("")
        if st.button("🔄 Refresh", use_container_width = True):
            fetch_entry_event.clear()
            fetch_live_event.clear()
            st.rerun()

    lentry_map = {e["id"]: e for e in entries}
    pos_map = {item["id"]: item["singular_name_short"] for item in static_data["element_types"]}
    team_map = {item["id"]: item["short_name"] for item in static_data["teams"]}
    element_lookup = {item["id"]: item for item in static_data["elements"]}
    
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

    gw_matches = [m for m in matches if m["event"] == current_gw]
    
    if not gw_matches:
        st.info("No fixtures scheduled for Gameweek " + str(current_gw) + " yet.")
        st.stop()

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
                        st.markdown(f"<h4 style='margin: 0; color: #ffffff;'>{alias1} vs {alias2}</h4>", unsafe_allow_html = True)
                    with hdr_r:
                        st.markdown(f"<p style='text-align: right; margin: 0; font-size: 0.85rem; color: {active_theme['accent']};'><b>{status_badge}</b></p>", unsafe_allow_html = True)
                        
                    t1_rem_text = format_remaining_players(item["t1_in_play"], item["t1_ytp"])
                    t2_rem_text = format_remaining_players(item["t2_in_play"], item["t2_ytp"])

                    sc_col1, sc_col2, sc_col3 = st.columns([5, 1, 5])
                    with sc_col1:
                        st.markdown("<h3 style='margin: 0; font-size: 2.1rem; color: #ffffff;'>" + str(item["t1_score"]) + "</h3>", unsafe_allow_html = True)
                        st.markdown("<p style='margin: 0; font-size: 0.8rem; color: #94a3b8; white-space: nowrap;'>Proj: " + f"{item['t1_proj']:.1f}" + " (" + t1_rem_text + ")</p>", unsafe_allow_html = True)
                        st.markdown(f"<p style='margin: 0; font-size: 0.75rem; color: #64748b;'>Bench: {item['t1_bp']} pts | Opt: {item['t1_opt']} pts</p>", unsafe_allow_html = True)
                    with sc_col2:
                        st.markdown("<p style='text-align: center; margin: 12px 0; color: #64748b; font-weight: bold;'>vs</p>", unsafe_allow_html = True)
                    with sc_col3:
                        st.markdown("<h3 style='text-align: right; margin: 0; font-size: 2.1rem; color: #ffffff;'>" + str(item["t2_score"]) + "</h3>", unsafe_allow_html = True)
                        st.markdown("<p style='text-align: right; margin: 0; font-size: 0.8rem; color: #94a3b8; white-space: nowrap;'>Proj: " + f"{item['t2_proj']:.1f}" + " (" + t2_rem_text + ")</p>", unsafe_allow_html = True)
                        st.markdown(f"<p style='text-align: right; margin: 0; font-size: 0.75rem; color: #64748b;'>Bench: {item['t2_bp']} pts | Opt: {item['t2_opt']} pts</p>", unsafe_allow_html = True)
                    
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
                        st.markdown(f"<span style='color: {col1_style}; font-size: 0.85rem; font-weight: bold;'>Win: {item['prob1']}%</span>", unsafe_allow_html = True)
                    with p_r:
                        st.markdown(f"<p style='text-align: right; margin: 0; font-size: 0.85rem; color: {col2_style}; font-weight: bold;'>Win: {item['prob2']}%</p>", unsafe_allow_html = True)

    st.divider()

    st.subheader("Match Spotlight and Lineup Breakdown")
    
    def spot_label(i):
        item = match_summaries[i]
        alias1 = get_manager_alias(item["e1"].get("player_first_name", ""), item["e1"].get("player_last_name", ""))
        alias2 = get_manager_alias(item["e2"].get("player_first_name", ""), item["e2"].get("player_last_name", ""))
        return f"{alias1} ({item['t1_score']}) vs ({item['t2_score']}) {alias2}"

    spotlight_idx = st.selectbox(
        "Inspect Matchup Details",
        range(len(match_summaries)),
        format_func = lambda i: spot_label(i)
    )
    
    active_spot = match_summaries[spotlight_idx]
    
    s_c1, s_c2 = st.columns(2)
    display_cols = ["Player", "Pos", "Club", "State", "Pts", "Proj", "Mins", "G", "A", "CS", "GC", "Bonus"]

    with s_c1:
        alias_e1 = get_manager_alias(active_spot["e1"].get("player_first_name", ""), active_spot["e1"].get("player_last_name", ""))
        st.markdown(f"### {alias_e1}")
        st.caption(f"Bench Left: {active_spot['t1_bp']} pts | Optimum Score: {active_spot['t1_opt']} pts")
        if not active_spot["t1_start"].empty:
            t1_s_view = active_spot["t1_start"][display_cols].copy()
            if "Proj" in t1_s_view.columns:
                t1_s_view["Proj"] = t1_s_view["Proj"].map(lambda x: f"{float(x):.1f}")
            st.markdown("**Starting XI (GK First)**")
            st.table(t1_s_view.set_index("Player"))

            t1_b_view = active_spot["t1_b"][display_cols].copy()
            if "Proj" in t1_b_view.columns:
                t1_b_view["Proj"] = t1_b_view["Proj"].map(lambda x: f"{float(x):.1f}")
            st.markdown("**Bench Substitutes**")
            st.table(t1_b_view.set_index("Player"))
        else:
            st.info("Lineup selections not yet available.")

    with s_c2:
        alias_e2 = get_manager_alias(active_spot["e2"].get("player_first_name", ""), active_spot["e2"].get("player_last_name", ""))
        st.markdown(f"### {alias_e2}")
        st.caption(f"Bench Left: {active_spot['t2_bp']} pts | Optimum Score: {active_spot['t2_opt']} pts")
        if not active_spot["t2_start"].empty:
            t2_s_view = active_spot["t2_start"][display_cols].copy()
            if "Proj" in t2_s_view.columns:
                t2_s_view["Proj"] = t2_s_view["Proj"].map(lambda x: f"{float(x):.1f}")
            st.markdown("**Starting XI (GK First)**")
            st.table(t2_s_view.set_index("Player"))

            t2_b_view = active_spot["t2_b"][display_cols].copy()
            if "Proj" in t2_b_view.columns:
                t2_b_view["Proj"] = t2_b_view["Proj"].map(lambda x: f"{float(x):.1f}")
            st.markdown("**Bench Substitutes**")
            st.table(t2_b_view.set_index("Player"))
        else:
            st.info("Lineup selections not yet available.")

# ----------------- 3. 🏆 CUP & BUCKET COMPETITION -----------------
elif st.session_state.page == "Cup & Bucket":
    st.title("🏆 Cup & Bucket Competition")
    st.caption("32-Team Inter-League Championship • CDP, SDM, BDR and LDE")

    cup_df = load_cup_matches()
    static_data = fetch_fpl_static()
    all_fixtures = fetch_all_epl_fixtures()

    if cup_df is None or cup_df.empty:
        st.warning("No 'cupmatches' spreadsheet found. Place 'cupmatches.xlsx', '.ods' or '.csv' in your Assets folder.")
        st.stop()

    if not static_data:
        st.error("Failed to connect to Premier League API.")
        st.stop()

    pos_map = {item["id"]: item["singular_name_short"] for item in static_data["element_types"]}
    team_map = {item["id"]: item["short_name"] for item in static_data["teams"]}
    team_short_map = {item["id"]: item["short_name"] for item in static_data["teams"]}
    element_lookup = {item["id"]: item for item in static_data["elements"]}

    teams_registry = get_all_32_teams_registry()

    cup_df.columns = [str(c).strip().title() for c in cup_df.columns]
    cup_df["Week"] = pd.to_numeric(cup_df["Week"], errors = "coerce").fillna(0).astype(int)

    all_cup_gws = sorted(list(set(cup_df["Week"].unique()) - {0}))

    cup_tab_live, cup_tab_standings, cup_tab_analyser = st.tabs([
        "🔴 Live Cup Matchday",
        "📊 32-Team Group Standings",
        "📋 Cup Results Analyser"
    ])

    with cup_tab_live:
        top_m1, top_m2, top_m3 = st.columns([3, 2, 1])
        with top_m1:
            st.caption("Around the Grounds live inter-league cup matches with live auto-subs and scoreline forecasts")
        with top_m2:
            active_cup_gw = st.selectbox("Select Cup Gameweek", all_cup_gws, index = 0, key = "cup_live_gw_sel")
        with top_m3:
            st.write("")
            if st.button("🔄 Refresh Cup", use_container_width = True, key = "cup_ref_btn"):
                fetch_entry_event.clear()
                fetch_live_event.clear()
                resolve_cup_match_score.clear()
                calculate_group_standings.clear()
                st.rerun()

        gw_cup_matches = cup_df[cup_df["Week"] == active_cup_gw].copy()

        if gw_cup_matches.empty:
            st.info(f"No cup matches scheduled for Gameweek {active_cup_gw}.")
        else:
            live_cup_cards = []
            for _, r in gw_cup_matches.iterrows():
                m1_alias = str(r.get("Team 1", "")).strip()
                m2_alias = str(r.get("Team 2", "")).strip()
                if not m1_alias or not m2_alias or m1_alias.lower() == "nan" or m2_alias.lower() == "nan":
                    continue

                s1, _, _, _, inp1, ytp1, bp1, opt1 = resolve_cup_match_score(m1_alias, active_cup_gw)
                s2, _, _, _, inp2, ytp2, bp2, opt2 = resolve_cup_match_score(m2_alias, active_cup_gw)

                info1 = teams_registry.get(m1_alias.lower(), {})
                info2 = teams_registry.get(m2_alias.lower(), {})

                is_fin = (inp1 + ytp1 + inp2 + ytp2 == 0) and (s1 > 0 or s2 > 0)
                prob1, prob2 = calculate_win_probability(s1, s1, inp1 + ytp1, s2, s2, inp2 + ytp2, is_fin)

                live_cup_cards.append({
                    "m1": m1_alias,
                    "m2": m2_alias,
                    "t1_name": info1.get("team_name", "Team 1"),
                    "t2_name": info2.get("team_name", "Team 2"),
                    "l1": info1.get("league_key", "").split(" ")[0],
                    "l2": info2.get("league_key", "").split(" ")[0],
                    "s1": s1,
                    "s2": s2,
                    "inp1": inp1,
                    "ytp1": ytp1,
                    "inp2": inp2,
                    "ytp2": ytp2,
                    "bp1": bp1,
                    "opt1": opt1,
                    "bp2": bp2,
                    "opt2": opt2,
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
                                st.markdown(f"<h4 style='margin: 0; color: #ffffff;'>{card['m1']} <span style='font-size: 0.8rem; color: #64748b;'>({card['l1']})</span> vs {card['m2']} <span style='font-size: 0.8rem; color: #64748b;'>({card['l2']})</span></h4>", unsafe_allow_html = True)
                            with hdr_r:
                                stage_tag = f"{card['stage']} {card['leg']}".strip()
                                st.markdown(f"<p style='text-align: right; margin: 0; font-size: 0.8rem; color: {active_theme['accent']}; font-weight: bold;'>{stage_tag}</p>", unsafe_allow_html = True)

                            rem1 = format_remaining_players(card["inp1"], card["ytp1"])
                            rem2 = format_remaining_players(card["inp2"], card["ytp2"])

                            sc1, sc2, sc3 = st.columns([5, 1, 5])
                            with sc1:
                                st.markdown(f"<h3 style='margin: 0; font-size: 2.1rem; color: #ffffff;'>{card['s1']}</h3>", unsafe_allow_html = True)
                                st.caption(rem1)
                                st.markdown(f"<p style='margin: 0; font-size: 0.75rem; color: #64748b;'>Bench: {card['bp1']} pts | Opt: {card['opt1']} pts</p>", unsafe_allow_html = True)
                            with sc2:
                                st.markdown("<p style='text-align: center; margin: 12px 0; color: #64748b; font-weight: bold;'>vs</p>", unsafe_allow_html = True)
                            with sc3:
                                st.markdown(f"<h3 style='text-align: right; margin: 0; font-size: 2.1rem; color: #ffffff;'>{card['s2']}</h3>", unsafe_allow_html = True)
                                st.markdown(f"<p style='text-align: right; margin: 0; font-size: 0.8rem; color: #94a3b8; white-space: nowrap;'>{rem2}</p>", unsafe_allow_html = True)
                                st.markdown(f"<p style='text-align: right; margin: 0; font-size: 0.75rem; color: #64748b;'>Bench: {card['bp2']} pts | Opt: {card['opt2']} pts</p>", unsafe_allow_html = True)

                            st.progress(card["prob1"] / 100.0)

            # --- MATCH SPOTLIGHT AND LINEUP BREAKDOWN IN LIVE CUP TAB ---
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

                spot_s1, _, spot_st1, spot_b1, _, _, spot_bp1, spot_opt1 = resolve_cup_match_score(spot_m1, active_cup_gw)
                spot_s2, _, spot_st2, spot_b2, _, _, spot_bp2, spot_opt2 = resolve_cup_match_score(spot_m2, active_cup_gw)

                s_info1 = teams_registry.get(spot_m1.lower(), {})
                s_info2 = teams_registry.get(spot_m2.lower(), {})

                st.divider()
                sr1, sr2, sr3 = st.columns([4, 2, 4])
                with sr1:
                    st.markdown(f"### {spot_m1}")
                    st.caption(f"{s_info1.get('team_name', '')} • {s_info1.get('league_key', '')}")
                with sr2:
                    st.markdown(f"<h2 style='text-align: center; margin: 0; font-size: 2.2rem; color: #ffffff;'>{spot_s1} {dash} {spot_s2}</h2>", unsafe_allow_html = True)
                    st.markdown(f"<p style='text-align: center; color: #64748b; margin: 0; font-weight: bold;'>{active_c_spot['stage']} {active_c_spot['leg']} (GW {active_cup_gw})</p>", unsafe_allow_html = True)
                with sr3:
                    st.markdown(f"<h3 style='text-align: right;'>{spot_m2}</h3>", unsafe_allow_html = True)
                    st.markdown(f"<p style='text-align: right; color: #64748b; margin: 0;'>{s_info2.get('team_name', '')} • {s_info2.get('league_key', '')}</p>", unsafe_allow_html = True)
                st.divider()

                # Cup Lineup Tables & Progression Chart
                gw_fixtures_c = [f for f in all_fixtures if f.get("event") == active_cup_gw] if all_fixtures else []
                if not gw_fixtures_c and all_fixtures:
                    gw_fixtures_c = all_fixtures

                c1_active_s = []
                if not spot_st1.empty:
                    c1_active_s.extend([r for _, r in spot_st1.iterrows() if r.get("sub_action") != "Subbed Off"])
                if not spot_b1.empty:
                    c1_active_s.extend([r for _, r in spot_b1.iterrows() if r.get("sub_action") == "Subbed On"])

                c2_active_s = []
                if not spot_st2.empty:
                    c2_active_s.extend([r for _, r in spot_st2.iterrows() if r.get("sub_action") != "Subbed Off"])
                if not spot_b2.empty:
                    c2_active_s.extend([r for _, r in spot_b2.iterrows() if r.get("sub_action") == "Subbed On"])

                if gw_fixtures_c:
                    labels_c = []
                    records_c = []
                    curr1_c = 0
                    curr2_c = 0

                    def get_fixture_contributors_c(active_players, h_id, a_id):
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

                    for f_item in gw_fixtures_c:
                        h_team_id = f_item.get("team_h")
                        a_team_id = f_item.get("team_a")
                        h_code = team_short_map.get(h_team_id, "H")
                        a_code = team_short_map.get(a_team_id, "A")
                        m_label = f"{h_code} v {a_code}"

                        p1_pts = sum(int(p["Pts"]) for p in c1_active_s if p.get("club_id") in (h_team_id, a_team_id))
                        p2_pts = sum(int(p["Pts"]) for p in c2_active_s if p.get("club_id") in (h_team_id, a_team_id))

                        curr1_c += p1_pts
                        curr2_c += p2_pts

                        contrib1 = get_fixture_contributors_c(c1_active_s, h_team_id, a_team_id)
                        contrib2 = get_fixture_contributors_c(c2_active_s, h_team_id, a_team_id)

                        labels_c.append(m_label)
                        records_c.append({
                            "Match": m_label,
                            "Manager": spot_m1,
                            "Points": curr1_c,
                            "Added": f"+{p1_pts}",
                            "Key Events": contrib1
                        })
                        records_c.append({
                            "Match": m_label,
                            "Manager": spot_m2,
                            "Points": curr2_c,
                            "Added": f"+{p2_pts}",
                            "Key Events": contrib2
                        })

                    chart_df_c = pd.DataFrame(records_c)

                    st.markdown(f"#### Gameweek {active_cup_gw} Points Progression")
                    st.caption("Cumulative matchday points tracking each EPL fixture in the order played")

                    chart_c = alt.Chart(chart_df_c).mark_line(point = True).encode(
                        x = alt.X(
                            "Match:N", 
                            sort = labels_c, 
                            title = None, 
                            axis = alt.Axis(
                                labelAngle = -90, 
                                labelOverlap = False, 
                                labelColor = "#94a3b8",
                                labelFontSize = 9,
                                grid = False
                            )
                        ),
                        y = alt.Y(
                            "Points:Q", 
                            title = "Cumulative Points", 
                            axis = alt.Axis(
                                labelColor = "#94a3b8", 
                                gridColor = "#182030",
                                domainColor = "#182030"
                            )
                        ),
                        color = alt.Color(
                            "Manager:N",
                            scale = alt.Scale(domain = [spot_m1, spot_m2], range = [active_theme["accent"], "#38bdf8"]),
                            legend = alt.Legend(title = None, orient = "bottom", labelColor = "#ffffff")
                        ),
                        tooltip = [
                            alt.Tooltip("Manager:N", title = "Manager"),
                            alt.Tooltip("Match:N", title = "Match"),
                            alt.Tooltip("Points:Q", title = "Total Pts"),
                            alt.Tooltip("Added:N", title = "Match Pts"),
                            alt.Tooltip("Key Events:N", title = "Key Events")
                        ]
                    ).properties(
                        height = 360,
                        background = "#000000"
                    ).configure_view(
                        strokeWidth = 0,
                        fill = "#000000"
                    ).configure_axis(
                        domainColor = "#182030"
                    )

                    st.altair_chart(chart_c, use_container_width = True)
                    st.divider()

                display_cols = ["Player", "Pos", "Club", "State", "Pts", "Proj", "Mins", "G", "A", "CS", "GC", "Bonus"]
                side1_c, side2_c = st.columns(2)
                with side1_c:
                    st.subheader(f"{spot_m1} Lineup")
                    st.caption(f"Bench Left: {spot_bp1} pts | Optimum Score: {spot_opt1} pts")
                    if not spot_st1.empty:
                        s1_view = spot_st1[display_cols].copy()
                        if "Proj" in s1_view.columns:
                            s1_view["Proj"] = s1_view["Proj"].map(lambda x: f"{float(x):.1f}")
                        st.markdown("**Starting XI (GK First)**")
                        st.table(s1_view.set_index("Player"))

                        b1_view = spot_b1[display_cols].copy()
                        if "Proj" in b1_view.columns:
                            b1_view["Proj"] = b1_view["Proj"].map(lambda x: f"{float(x):.1f}")
                        st.markdown("**Bench Substitutes**")
                        st.table(b1_view.set_index("Player"))
                    else:
                        st.info("Lineups not yet available.")

                with side2_c:
                    st.subheader(f"{spot_m2} Lineup")
                    st.caption(f"Bench Left: {spot_bp2} pts | Optimum Score: {spot_opt2} pts")
                    if not spot_st2.empty:
                        s2_view = spot_st2[display_cols].copy()
                        if "Proj" in s2_view.columns:
                            s2_view["Proj"] = s2_view["Proj"].map(lambda x: f"{float(x):.1f}")
                        st.markdown("**Starting XI (GK First)**")
                        st.table(s2_view.set_index("Player"))

                        b2_view = spot_b2[display_cols].copy()
                        if "Proj" in b2_view.columns:
                            b2_view["Proj"] = b2_view["Proj"].map(lambda x: f"{float(x):.1f}")
                        st.markdown("**Bench Substitutes**")
                        st.table(b2_view.set_index("Player"))
                    else:
                        st.info("Lineups not yet available.")

    with cup_tab_standings:
        st.subheader("Combined 32-Team Group Standings (GW 6 – GW 20)")
        st.caption("Tiebreaker Hierarchy: 1. Points → 2. Player Points (PF) → 3. Head-to-Head → 4. Highest Individual Player Score in Group Stage")

        with st.spinner("Calculating group standings across 8 matchdays..."):
            display_table = calculate_group_standings()

        if display_table:
            table_df = pd.DataFrame(display_table)
            st.table(table_df.set_index("Pos"))
        else:
            st.info("Group standings calculations unavailable.")

    with cup_tab_analyser:
        st.subheader("📋 Cup Results Analyser")
        st.caption("Inspect cross-league matchday lineups, key events and match progression charts")

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
                chosen_c_gw = st.selectbox("Select Gameweek", all_cup_gws, key = "c_gw_picker")
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

            c_s1, _, c_st1, c_b1, _, _, c_bp1, c_opt1 = resolve_cup_match_score(c_m1, c_gw)
            c_s2, _, c_st2, c_b2, _, _, c_bp2, c_opt2 = resolve_cup_match_score(c_m2, c_gw)

            info1 = teams_registry.get(c_m1.lower(), {})
            info2 = teams_registry.get(c_m2.lower(), {})

            st.divider()
            r1, r2, r3 = st.columns([4, 2, 4])
            with r1:
                st.markdown(f"### {c_m1}")
                st.caption(f"{info1.get('team_name', '')} • {info1.get('league_key', '')}")
            with r2:
                st.markdown(f"<h2 style='text-align: center; margin: 0; font-size: 2.2rem; color: #ffffff;'>{c_s1} {dash} {c_s2}</h2>", unsafe_allow_html = True)
                stage_desc = f"{selected_cup_match.get('Comp', 'Cup')} {selected_cup_match.get('Stage', '')} {selected_cup_match.get('Leg', '')}".strip()
                st.markdown(f"<p style='text-align: center; color: #64748b; margin: 0; font-weight: bold;'>{stage_desc} (GW {c_gw})</p>", unsafe_allow_html = True)
            with r3:
                st.markdown(f"<h3 style='text-align: right;'>{c_m2}</h3>", unsafe_allow_html = True)
                st.markdown(f"<p style='text-align: right; color: #64748b; margin: 0;'>{info2.get('team_name', '')} • {info2.get('league_key', '')}</p>", unsafe_allow_html = True)
            st.divider()

            st.caption(f"{c_m1} — Bench Left: {c_bp1} pts | Optimum Score: {c_opt1} pts   |   {c_m2} — Bench Left: {c_bp2} pts | Optimum Score: {c_opt2} pts")

            epl_fixtures = fetch_epl_fixtures(c_gw)
            gw_fixtures = [f for f in epl_fixtures if f.get("event") == c_gw] if epl_fixtures else []
            if not gw_fixtures and epl_fixtures:
                gw_fixtures = epl_fixtures

            c1_active = []
            if not c_st1.empty:
                c1_active.extend([r for _, r in c_st1.iterrows() if r.get("sub_action") != "Subbed Off"])
            if not c_b1.empty:
                c1_active.extend([r for _, r in c_b1.iterrows() if r.get("sub_action") == "Subbed On"])

            c2_active = []
            if not c_st2.empty:
                c2_active.extend([r for _, r in c_st2.iterrows() if r.get("sub_action") != "Subbed Off"])
            if not c_b2.empty:
                c2_active.extend([r for _, r in c_b2.iterrows() if r.get("sub_action") == "Subbed On"])

            if gw_fixtures:
                labels = []
                records = []
                curr1 = 0
                curr2 = 0

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

                    p1_pts = sum(int(p["Pts"]) for p in c1_active if p.get("club_id") in (h_team_id, a_team_id))
                    p2_pts = sum(int(p["Pts"]) for p in c2_active if p.get("club_id") in (h_team_id, a_team_id))

                    curr1 += p1_pts
                    curr2 += p2_pts

                    contrib1 = get_fixture_contributors(c1_active, h_team_id, a_team_id)
                    contrib2 = get_fixture_contributors(c2_active, h_team_id, a_team_id)

                    labels.append(m_label)
                    records.append({
                        "Match": m_label,
                        "Manager": c_m1,
                        "Points": curr1,
                        "Added": f"+{p1_pts}",
                        "Key Events": contrib1
                    })
                    records.append({
                        "Match": m_label,
                        "Manager": c_m2,
                        "Points": curr2,
                        "Added": f"+{p2_pts}",
                        "Key Events": contrib2
                    })

                chart_df = pd.DataFrame(records)

                st.markdown(f"#### Gameweek {c_gw} Points Progression")
                st.caption("Cumulative matchday points tracking each EPL fixture in the order played")

                chart = alt.Chart(chart_df).mark_line(point = True).encode(
                    x = alt.X(
                        "Match:N", 
                        sort = labels, 
                        title = None, 
                        axis = alt.Axis(
                            labelAngle = -90, 
                            labelOverlap = False, 
                            labelColor = "#94a3b8",
                            labelFontSize = 9,
                            grid = False
                        )
                    ),
                    y = alt.Y(
                        "Points:Q", 
                        title = "Cumulative Points", 
                        axis = alt.Axis(
                            labelColor = "#94a3b8", 
                            gridColor = "#182030",
                            domainColor = "#182030"
                        )
                    ),
                    color = alt.Color(
                        "Manager:N",
                        scale = alt.Scale(domain = [c_m1, c_m2], range = [active_theme["accent"], "#38bdf8"]),
                        legend = alt.Legend(title = None, orient = "bottom", labelColor = "#ffffff")
                    ),
                    tooltip = [
                        alt.Tooltip("Manager:N", title = "Manager"),
                        alt.Tooltip("Match:N", title = "Match"),
                        alt.Tooltip("Points:Q", title = "Total Pts"),
                        alt.Tooltip("Added:N", title = "Match Pts"),
                        alt.Tooltip("Key Events:N", title = "Key Events")
                    ]
                ).properties(
                    height = 360,
                    background = "#000000"
                ).configure_view(
                    strokeWidth = 0,
                    fill = "#000000"
                ).configure_axis(
                    domainColor = "#182030"
                )

                st.altair_chart(chart, use_container_width = True)
                st.divider()

            display_cols = ["Player", "Pos", "Club", "State", "Pts", "Proj", "Mins", "G", "A", "CS", "GC", "Bonus"]
            side1, side2 = st.columns(2)
            with side1:
                st.subheader(f"{c_m1} Lineup")
                if not c_st1.empty:
                    s1_view = c_st1[display_cols].copy()
                    if "Proj" in s1_view.columns:
                        s1_view["Proj"] = s1_view["Proj"].map(lambda x: f"{float(x):.1f}")
                    st.markdown("**Starting XI (GK First)**")
                    st.table(s1_view.set_index("Player"))

                    b1_view = c_b1[display_cols].copy()
                    if "Proj" in b1_view.columns:
                        b1_view["Proj"] = b1_view["Proj"].map(lambda x: f"{float(x):.1f}")
                    st.markdown("**Bench Substitutes**")
                    st.table(b1_view.set_index("Player"))
                else:
                    st.info("Lineups not yet available.")

            with side2:
                st.subheader(f"{c_m2} Lineup")
                if not c_st2.empty:
                    s2_view = c_st2[display_cols].copy()
                    if "Proj" in s2_view.columns:
                        s2_view["Proj"] = s2_view["Proj"].map(lambda x: f"{float(x):.1f}")
                    st.markdown("**Starting XI (GK First)**")
                    st.table(s2_view.set_index("Player"))

                    b2_view = c_b2[display_cols].copy()
                    if "Proj" in b2_view.columns:
                        b2_view["Proj"] = b2_view["Proj"].map(lambda x: f"{float(x):.1f}")
                    st.markdown("**Bench Substitutes**")
                    st.table(b2_view.set_index("Player"))
                else:
                    st.info("Lineups not yet available.")

# ----------------- 4. EPL SCORES SECTION -----------------
elif st.session_state.page in ["EPL Scores", "EPL SCORES"]:
    st.title("⚽ EPL Scores")
    
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
        curr_from_static = None
        for ev in static_data.get("events", {}).get("data", []):
            if ev.get("is_current"):
                curr_from_static = ev.get("id")
                break
        default_epl_gw = curr_from_static if curr_from_static else (all_gws[-1] if all_gws else 1)

    top_e1, top_e2, top_e3 = st.columns([3, 2, 1])
    with top_e1:
        st.caption("Official Premier League matchday results, goalscorers, assists, DEFCON scores and defensive metrics")
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
            st.rerun()

    fixtures = fetch_epl_fixtures(selected_epl_gw)
    live_event_data = fetch_live_event(selected_epl_gw)
    live_elements = live_event_data.get("elements", {}) if live_event_data else {}

    if not fixtures:
        st.info("No fixtures available for Gameweek " + str(selected_epl_gw) + ".")
        st.stop()

    st.subheader("Premier League Matches (GW " + str(selected_epl_gw) + ")")

    for f in fixtures:
        h_id = f.get("team_h")
        a_id = f.get("team_a")
        h_name = team_name_map.get(h_id, "Home Team")
        a_name = team_name_map.get(a_id, "Away Team")
        h_short = team_short_map.get(h_id, "H")
        a_short = team_short_map.get(a_id, "A")
        
        is_finished = f.get("finished", False)
        is_started = f.get("started", False)
        h_score = f.get("team_h_score")
        a_score = f.get("team_a_score")
        
        if is_finished:
            status_text = "FT"
            status_color = "#64748b"
        elif is_started:
            mins_val = f.get("minutes", 0)
            status_text = f"LIVE {mins_val}'"
            status_color = active_theme["accent"]
        else:
            status_text = f.get("kickoff_time", "")[11:16] if f.get("kickoff_time") else "Upcoming"
            status_color = "#94a3b8"

        with st.container(border = True):
            f_col1, f_col2, f_col3 = st.columns([4, 3, 4])
            
            with f_col1:
                st.markdown(f"<h3 style='margin: 0; color: #ffffff;'>{h_name} <span style='font-size: 0.9rem; color: #64748b;'>({h_short})</span></h3>", unsafe_allow_html = True)
                
            with f_col2:
                if is_started or is_finished:
                    st.markdown(f"<h2 style='text-align: center; margin: 0; color: #ffffff;'>{h_score} {dash} {a_score}</h2>", unsafe_allow_html = True)
                else:
                    st.markdown("<p style='text-align: center; margin: 0; font-size: 1.2rem; color: #64748b;'>vs</p>", unsafe_allow_html = True)
                st.markdown(f"<p style='text-align: center; margin: 0; font-size: 0.85rem; font-weight: bold; color: {status_color};'>{status_text}</p>", unsafe_allow_html = True)
                
            with f_col3:
                st.markdown(f"<h3 style='text-align: right; margin: 0; color: #ffffff;'><span style='font-size: 0.9rem; color: #64748b;'>({a_short})</span> {a_name}</h3>", unsafe_allow_html = True)

            with st.expander("Match Breakdown"):
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
                        for elem_id_str, e_data in live_elements.items():
                            if not isinstance(e_data, dict):
                                continue
                            try:
                                elem_id_int = int(elem_id_str)
                            except (ValueError, TypeError):
                                continue
                            elem_obj = element_lookup.get(elem_id_int, {})
                            if elem_obj.get("team") == team_id:
                                p_name = elem_obj.get("web_name", "Unknown")
                                p_pos = elem_obj.get("element_type", 1)
                                e_stats = e_data.get("stats", {}) if isinstance(e_data.get("stats"), dict) else {}
                                
                                cbi = e_stats.get("clearances_blocks_interceptions", 0) or e_stats.get("cbi", 0)
                                tackles = e_stats.get("tackles", 0)
                                dc_direct = e_stats.get("defensive_contributions", 0) or e_stats.get("defcon", 0) or e_stats.get("cbit", 0)
                                calc_val = dc_direct if dc_direct > 0 else (cbi + tackles)
                                
                                explain_raw = e_data.get("explain", [])
                                is_hit = False
                                explain_val = 0
                                stat_items = []
                                
                                if isinstance(explain_raw, list):
                                    for item in explain_raw:
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
                                threshold = 10 if p_pos == 2 else 12
                                if (p_pos in [2, 3, 4] and final_val >= threshold) or is_hit:
                                    if not any(x[0] == p_name for x in achieved):
                                        achieved.append((p_name, final_val))
                    return achieved

                h_defcon = resolve_defcon_achieved("h", h_id)
                a_defcon = resolve_defcon_achieved("a", a_id)

                b_col1, b_col2 = st.columns(2)

                with b_col1:
                    st.markdown(f"**{h_name}**")
                    if h_goals:
                        st.markdown("⚽ **Goals:** " + ", ".join([f"{n} ({v})" if v > 1 else n for n, v in h_goals]))
                    if h_assists:
                        st.markdown("🎯 **Assists:** " + ", ".join([f"{n} ({v})" if v > 1 else n for n, v in h_assists]))
                    if h_defcon:
                        st.markdown("<span style='color: #22c55e;'>🛡️ <b>DEFCON (+2 pts):</b> " + ", ".join([f"{n} ({v})" if v > 0 else n for n, v in h_defcon]) + "</span>", unsafe_allow_html = True)
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
                    st.markdown(f"**{a_name}**")
                    if a_goals:
                        st.markdown("⚽ **Goals:** " + ", ".join([f"{n} ({v})" if v > 1 else n for n, v in a_goals]))
                    if a_assists:
                        st.markdown("🎯 **Assists:** " + ", ".join([f"{n} ({v})" if v > 1 else n for n, v in a_assists]))
                    if a_defcon:
                        st.markdown("<span style='color: #22c55e;'>🛡️ <b>DEFCON (+2 pts):</b> " + ", ".join([f"{n} ({v})" if v > 0 else n for n, v in a_defcon]) + "</span>", unsafe_allow_html = True)
                    if a_cs_players:
                        st.markdown("🛡️ **Clean Sheets:** " + ", ".join(a_cs_players))
                    if a_saves:
                        st.markdown("🧤 **Saves:** " + ", ".join([f"{n} ({v} saves)" for n, v in a_saves]))
                    if a_og:
                        st.markdown("<span style='color: #ef4444;'>🛑 <b>Own Goals:</b> " + ", ".join([f"{n} ({v})" if v > 1 else n for n, v in a_og]) + "</span>", unsafe_allow_html = True)
                    if a_pmiss:
                        st.markdown("<span style='color: #ef4444;'>❌ <b>Penalties Missed:</b> " + ", ".join([f"{n} ({v})" if v > 1 else n for n, v in a_pmiss]) + "</span>", unsafe_allow_html = True)
                    if h_psaved:
                        st.markdown("<span style='color: #22c55e;'>🧤 <b>Penalties Saved:</b> " + ", ".join([f"{n} ({v})" if v > 1 else n for n, v in h_psaved]) + "</span>", unsafe_allow_html = True)
                    if not (a_goals or a_assists or a_defcon or a_saves or a_cs_players or a_og or a_pmiss or a_psaved):
                        st.caption("No registered match events yet.")

                bonus_list = stats_dict.get("bonus", {}).get("h", []) + stats_dict.get("bonus", {}).get("a", [])
                if bonus_list:
                    st.divider()
                    bonus_list = sorted(bonus_list, key = lambda x: x.get("value", 0), reverse = True)
                    bonus_formatted = [f"{element_lookup.get(b['element'], {}).get('web_name', 'Unknown')} ({b['value']} pts)" for b in bonus_list]
                    st.markdown("⭐ **Bonus Points:** " + " | ".join(bonus_formatted))

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
            st.markdown("### " + alias1)
            st.caption(e1_info.get("entry_name", "Team 1"))
        with res_col2:
            status_text = "FINAL SCORE" if selected_match.get("finished") else "ARCHIVED SCORE"
            st.markdown("<h2 style='text-align: center; margin: 0; font-size: 2.2rem; color: #ffffff;'>" + str(score1) + dash + str(score2) + "</h2>", unsafe_allow_html = True)
            st.markdown("<p style='text-align: center; color: #64748b; margin: 0; font-weight: bold;'>" + status_text + " (GW " + str(gw_num) + ")</p>", unsafe_allow_html = True)
        with res_col3:
            st.markdown("<h3 style='text-align: right;'>" + alias2 + "</h3>", unsafe_allow_html = True)
            st.markdown("<p style='text-align: right; color: #64748b; margin: 0;'>Manager: " + alias2 + "</p>", unsafe_allow_html = True)
            
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

        t1_active = []
        if not t1_start.empty:
            for _, r in t1_start.iterrows():
                if r.get("sub_action") != "Subbed Off":
                    t1_active.append(r)
        if not t1_b.empty:
            for _, r in t1_b.iterrows():
                if r.get("sub_action") == "Subbed On":
                    t1_active.append(r)

        t2_active = []
        if not t2_start.empty:
            for _, r in t2_start.iterrows():
                if r.get("sub_action") != "Subbed Off":
                    t2_active.append(r)
        if not t2_b.empty:
            for _, r in t2_b.iterrows():
                if r.get("sub_action") == "Subbed On":
                    t2_active.append(r)

        # ----------------- EPL MATCH PROGRESSION GRAPH -----------------
        gw_fixtures = [f for f in all_fixtures if f.get("event") == gw_num] if all_fixtures else []
        if not gw_fixtures and all_fixtures:
            gw_fixtures = all_fixtures

        if gw_fixtures:
            labels = []
            records = []
            curr1 = 0
            curr2 = 0

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

                labels.append(m_label)
                records.append({
                    "Match": m_label,
                    "Manager": alias1,
                    "Points": curr1,
                    "Added": f"+{p1_pts}",
                    "Key Events": contrib1
                })
                records.append({
                    "Match": m_label,
                    "Manager": alias2,
                    "Points": curr2,
                    "Added": f"+{p2_pts}",
                    "Key Events": contrib2
                })

            chart_df = pd.DataFrame(records)

            st.markdown(f"#### Gameweek {gw_num} Points Progression")
            st.caption("Cumulative matchday points tracking each EPL fixture in the order played")

            chart = alt.Chart(chart_df).mark_line(point = True).encode(
                x = alt.X(
                    "Match:N", 
                    sort = labels, 
                    title = None, 
                    axis = alt.Axis(
                        labelAngle = -90, 
                        labelOverlap = False, 
                        labelColor = "#94a3b8",
                        labelFontSize = 9,
                        grid = False
                    )
                ),
                y = alt.Y(
                    "Points:Q", 
                    title = "Cumulative Points", 
                    axis = alt.Axis(
                        labelColor = "#94a3b8", 
                        gridColor = "#182030",
                        domainColor = "#182030"
                    )
                ),
                color = alt.Color(
                    "Manager:N",
                    scale = alt.Scale(domain = [alias1, alias2], range = [active_theme["accent"], "#38bdf8"]),
                    legend = alt.Legend(title = None, orient = "bottom", labelColor = "#ffffff")
                ),
                tooltip = [
                    alt.Tooltip("Manager:N", title = "Manager"),
                    alt.Tooltip("Match:N", title = "Match"),
                    alt.Tooltip("Points:Q", title = "Total Pts"),
                    alt.Tooltip("Added:N", title = "Match Pts"),
                    alt.Tooltip("Key Events:N", title = "Key Events")
                ]
            ).properties(
                height = 360,
                background = "#000000"
            ).configure_view(
                strokeWidth = 0,
                fill = "#000000"
            ).configure_axis(
                domainColor = "#182030"
            )

            st.altair_chart(chart, use_container_width = True)
            st.divider()

        display_cols = ["Player", "Pos", "Club", "State", "Pts", "Proj", "Mins", "G", "A", "CS", "GC", "Bonus"]

        side1, side2 = st.columns(2)
        with side1:
            st.subheader(alias1 + " Lineup")
            if not t1_start.empty:
                t1_s_view = t1_start[display_cols].copy()
                if "Proj" in t1_s_view.columns:
                    t1_s_view["Proj"] = t1_s_view["Proj"].map(lambda x: f"{float(x):.1f}")
                st.markdown("**Starting XI (GK First)**")
                st.table(t1_s_view.set_index("Player"))

                t1_b_view = t1_b[display_cols].copy()
                if "Proj" in t1_b_view.columns:
                    t1_b_view["Proj"] = t1_b_view["Proj"].map(lambda x: f"{float(x):.1f}")
                st.markdown("**Bench Substitutes**")
                st.table(t1_b_view.set_index("Player"))
            else:
                st.info("Lineup selections not yet available for this gameweek.")

        with side2:
            st.subheader(alias2 + " Lineup")
            if not t2_start.empty:
                t2_s_view = t2_start[display_cols].copy()
                if "Proj" in t2_s_view.columns:
                    t2_s_view["Proj"] = t2_s_view["Proj"].map(lambda x: f"{float(x):.1f}")
                st.markdown("**Starting XI (GK First)**")
                st.table(t2_s_view.set_index("Player"))

                t2_b_view = t2_b[display_cols].copy()
                if "Proj" in t2_b_view.columns:
                    t2_b_view["Proj"] = t2_b_view["Proj"].map(lambda x: f"{float(x):.1f}")
                st.markdown("**Bench Substitutes**")
                st.table(t2_b_view.set_index("Player"))
            else:
                st.info("Lineup selections not yet available for this gameweek.")

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
    default_entry_idx = entry_keys.index(88) if 88 in entry_keys else 0

    selected_entry_id = st.sidebar.selectbox(
        "Select Your Team",
        options = entry_keys,
        format_func = lambda x: entry_options.get(x, str(x)),
        index = default_entry_idx,
        key = "team_selector_" + str(active_league_id)
    )

    my_squad = merged[merged["owner"] == selected_entry_id].copy()
    waiver_pool = merged[merged["owner"].isna() | (merged["owner"] == 0)].copy()

    tab_lineup, tab_waivers = st.tabs(["Recommended Lineup", "Tailored Waivers & Suggested Drops"])

    # ----------------- TAB 1: RECOMMENDED STARTING XI -----------------
    with tab_lineup:
        st.subheader("Recommended Starting XI and Bench Hierarchy")
        
        if my_squad.empty:
            st.warning("No players found for this team selection.")
        else:
            def compute_starter_rating(r):
                if r["avail_factor"] == 0.0:
                    return -9999.0
                base_score = (r["form"] * 1.8) + (r["points_per_game"] * 2.0) + (r["ict_index"] * 0.05)
                return round(base_score * r["avail_factor"], 1)

            my_squad["starter_rating"] = my_squad.apply(compute_starter_rating, axis = 1)
            sorted_squad = my_squad.sort_values(by = "starter_rating", ascending = False)
            
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
            
            def bench_priority(r):
                fit_bonus = 100.0 if r["avail_factor"] == 1.0 else (50.0 if r["avail_factor"] > 0.0 else -500.0)
                return fit_bonus + (r["form"] * 1.5) + (r["points_per_game"] * 1.5)

            all_bench_outfield["bench_score"] = all_bench_outfield.apply(bench_priority, axis = 1)
            ordered_bench_outfield = all_bench_outfield.sort_values(by = "bench_score", ascending = False)

            bench_rows = []
            for bg in bench_gk:
                bg_dict = bg.to_dict()
                bg_dict["Role"] = "GK Sub"
                bench_rows.append(bg_dict)
            for idx, (_, bo) in enumerate(ordered_bench_outfield.iterrows(), 1):
                bo_dict = bo.to_dict()
                bo_dict["Role"] = f"Sub {idx}"
                bench_rows.append(bo_dict)

            st.markdown("### Starting XI (GK First)")
            xi_df = pd.DataFrame(starting_xi)
            xi_df["pos_rank"] = xi_df["position"].map(POS_ORDER)
            xi_df = xi_df.sort_values(by = ["pos_rank", "starter_rating"], ascending = [True, False])
            
            xi_df["PPG"] = xi_df["points_per_game"].map(lambda x: f"{float(x):.1f}")
            xi_df["Form"] = xi_df["form"].map(lambda x: f"{float(x):.1f}")

            display_cols = ["web_name", "position", "club", "health_status", "total_points", "last_2_pts", "next_3", "PPG", "Form"]
            xi_display = xi_df[display_cols].rename(columns = {
                "web_name": "Player",
                "position": "Pos",
                "club": "Club",
                "health_status": "Status",
                "total_points": "Total Pts",
                "last_2_pts": "Last 2 GWs",
                "next_3": "Next 3 Fixtures"
            })
            st.table(xi_display.set_index("Player"))

            if bench_rows:
                st.markdown("### Bench Hierarchy")
                b_df = pd.DataFrame(bench_rows)
                b_df["PPG"] = b_df["points_per_game"].map(lambda x: f"{float(x):.1f}")
                b_df["Form"] = b_df["form"].map(lambda x: f"{float(x):.1f}")

                b_cols = ["Role", "web_name", "position", "club", "health_status", "total_points", "last_2_pts", "next_3", "PPG", "Form"]
                b_display = b_df[b_cols].rename(columns = {
                    "Role": "Role",
                    "web_name": "Player",
                    "position": "Pos",
                    "club": "Club",
                    "health_status": "Status",
                    "total_points": "Total Pts",
                    "last_2_pts": "Last 2 GWs",
                    "next_3": "Next 3 Fixtures"
                })
                st.table(b_display.set_index("Role"))
                st.caption("Sub 1 prioritises 100% fit outfield players to ensure automatic substitution cover if a doubtful starter is rested.")

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
            st.success("✅ **Squad Balance Sound:** Roster availability and positional averages meet or exceed division baselines. Scouting high-upside upgrades.")

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

# ----------------- 8. STANDINGS SECTION -----------------
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

    standings_tab1, standings_tab2, standings_tab3 = st.tabs([
        "🟢 Live Standings (In Play)",
        f"📊 Official Standings (GW {last_completed_gw})",
        "🎯 GACS"
    ])

    with standings_tab1:
        st.subheader("Live Standings " + dash + " Active Round (GW " + str(current_gw) + ")")
        st.caption("Updated continuously with active points. Movement indicators show changes against previous official rank.")
        st.table(live_table_df)

    with standings_tab2:
        st.subheader("Official Standings " + dash + " Frozen Table (GW " + str(last_completed_gw) + ")")
        st.caption("Standings after the most recently concluded gameweek.")
        st.table(official_table_df)

    with standings_tab3:
        render_xi_stats_view(entries, current_gw, element_lookup, pos_map, team_map, all_fixtures)

# ----------------- 9. NEWSLETTERS SECTION -----------------
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

# ----------------- 10. POWER RANKINGS SECTION -----------------
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

        sheet_names = list(sheets_dict.keys())
        if len(sheet_names) > 1:
            p_tabs = st.tabs(sheet_names)
            for idx, s_name in enumerate(sheet_names):
                with p_tabs[idx]:
                    df_sheet = sheets_dict[s_name].fillna("")
                    if not df_sheet.empty:
                        df_sheet = format_table_floats(df_sheet)
                        df_sheet.columns = [str(c).strip() for c in df_sheet.columns]
                        first_col = df_sheet.columns[0]
                        st.table(df_sheet.set_index(first_col))
                    else:
                        st.info("No data in this sheet.")
        else:
            s_name = sheet_names[0]
            df_sheet = sheets_dict[s_name].fillna("")
            if not df_sheet.empty:
                df_sheet = format_table_floats(df_sheet)
                df_sheet.columns = [str(c).strip() for c in df_sheet.columns]
                first_col = df_sheet.columns[0]
                st.table(df_sheet.set_index(first_col))
            else:
                st.info("No data in this sheet.")

# ----------------- 11. RECORDS SECTION -----------------
elif st.session_state.page == "Records":
    top_r1, top_r2 = st.columns([5, 1])
    with top_r1:
        st.title("🏆 Hall of Records" + dash + selected_league_key)
        st.caption("Official archive of league highs, historic triumphs and statistical anomalies")
    with top_r2:
        st.write("")
        if st.button("🔄 Refresh Records", use_container_width = True):
            st.rerun()

    filename, sheets_dict, raw_bytes = load_records_data()

    if not filename or sheets_dict is None:
        st.warning("No records spreadsheet found. Ensure 'records.ods' is committed inside your Assets folder.")
    elif isinstance(sheets_dict, Exception):
        st.error(f"Error reading {filename}: {str(sheets_dict)}")
        st.info("Ensure **odfpy** is added to your requirements.txt file so Streamlit can read .ods files.")
    else:
        st.download_button(
            label = f"📥 Download Archive ({filename})",
            data = raw_bytes,
            file_name = filename,
            mime = "application/octet-stream",
            use_container_width = False
        )
        st.write("")

        sheet_names = list(sheets_dict.keys())
        record_tabs = st.tabs(sheet_names)

        for idx, s_name in enumerate(sheet_names):
            with record_tabs[idx]:
                df_sheet = sheets_dict[s_name].fillna("")
                if not df_sheet.empty:
                    df_sheet = format_table_floats(df_sheet)
                    df_sheet.columns = [str(c).strip() for c in df_sheet.columns]
                    first_col = df_sheet.columns[0]
                    st.table(df_sheet.set_index(first_col))
                else:
                    st.info("No records recorded in this sheet.")
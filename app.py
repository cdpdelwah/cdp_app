import streamlit as st
import requests
import pandas as pd
import math
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
        "accent": "#f59e0b",       # Championship Gold
        "accent_glow": "rgba(245, 158, 11, 0.25)",
        "badge_bg": "#231804",
        "tag": "PREMIER DIVISION"
    },
    "SDM (Segundo Del Mundo)": {
        "accent": "#3b82f6",       # Glacial Ice Blue
        "accent_glow": "rgba(59, 130, 246, 0.25)",
        "badge_bg": "#06152d",
        "tag": "SEGUNDO DIVISION"
    },
    "BDR (Best De La Rest)": {
        "accent": "#f97316",       # Molten Ember Orange
        "accent_glow": "rgba(249, 115, 22, 0.25)",
        "badge_bg": "#271004",
        "tag": "DIVISION THREE"
    },
    "LDE (Liger Del Eager)": {
        "accent": "#22c55e",       # Electric Acid Green
        "accent_glow": "rgba(34, 197, 94, 0.25)",
        "badge_bg": "#052210",
        "tag": "DIVISION FOUR"
    }
}

# Positional hierarchy mapping for display ordering
POS_ORDER = {"GKP": 1, "DEF": 2, "MID": 3, "FWD": 4}

# Bind navigation directly to session state
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

# Sidebar Brand and Navigation
if logo_path.exists():
    st.sidebar.image(str(logo_path), use_container_width = True)
else:
    st.sidebar.title("CDP App")

st.sidebar.caption("Stats, not facts | Season X Command Center")

st.sidebar.radio(
    "Navigation Menu",
    ["Home", "LIVE SCORES", "Standings", "EPL SCORES", "Squad Analyser", "Results Analyser", "Newsletters"],
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
    /* Global Pure Black Canvas */
    .stApp {{
        background-color: #000000 !important;
        color: #f1f5f9 !important;
    }}

    /* Sidebar Background */
    section[data-testid="stSidebar"] {{
        background-color: #06070a !important;
        border-right: 1px solid #141824 !important;
    }}

    /* Typography Hierarchy */
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

    /* Matchday Card Containers */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: #090c13 !important;
        border: 1px solid #182030 !important;
        border-radius: 8px !important;
        transition: border 0.2s ease;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
        border-color: {active_theme['accent']} !important;
    }}

    /* Universal Table Styling */
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

    /* Expandable Dropdown Styling */
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

    /* High Contrast Dropdown Select Trigger Box */
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

    /* Dropdown Popover Menu Container */
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

    /* Text Contrast Override inside Popover Menu */
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

    /* Adaptive Action Buttons */
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

    /* Dynamic Progress Bar */
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

def evaluate_lineup(picks_list, live_elements, element_lookup, club_minutes, pos_map, team_map):
    if not picks_list:
        return pd.DataFrame(), pd.DataFrame(), 0, 0.0, 0, 0
        
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
        form_val = float(raw_elem.get("form") or 0.0)
        ppg_val = float(raw_elem.get("points_per_game") or 2.0)
        base_exp = ((form_val * 0.6) + (ppg_val * 0.4)) * avail
        if base_exp <= 0 and avail > 0:
            base_exp = 2.0
            
        if team_mins >= 800:
            if mins > 0:
                state = "FT"
                proj = pts
            else:
                state = "DNP"
                proj = 0
        elif team_mins > 0:
            state = "LIVE"
            proj = pts
        else:
            state = "YTP"
            proj = round(base_exp, 1)
            
        raw_players.append({
            "id": elem_id,
            "Player": raw_elem.get("web_name", "Unknown"),
            "pos_num": pos_type,
            "Pos": pos_str,
            "Club": team_map.get(club_id, ""),
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
    
    # GK substitution
    gk_starter = next((s for s in starters if s["Pos"] == "GKP"), None)
    if gk_starter and gk_starter["State"] == "DNP":
        gk_bench = next((b for b in bench if b["Pos"] == "GKP" and b["State"] != "DNP"), None)
        if gk_bench:
            gk_starter["sub_action"] = "Subbed Off"
            gk_bench["sub_action"] = "Subbed On"
            used_bench_ids.add(gk_bench["id"])
            
    # Outfield substitutions
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
    
    starters_df = pd.DataFrame(starters).sort_values(by = ["pos_num", "Pts"], ascending = [True, False])
    bench_df = pd.DataFrame(bench).sort_values(by = "pick_pos", ascending = True)
    
    return starters_df, bench_df, live_score, round(proj_score, 1), in_play, yet_to_play

def calculate_league_tables(entries, matches, current_gw, live_elements, element_lookup, club_minutes, pos_map, team_map):
    lentry_map = {e["id"]: e for e in entries}
    
    official_stats = {
        e["id"]: {"wins": 0, "draws": 0, "losses": 0, "pf": 0, "pts": 0}
        for e in entries
    }
    live_stats = {
        e["id"]: {"wins": 0, "draws": 0, "losses": 0, "pf": 0, "pts": 0, "gw_score": 0}
        for e in entries
    }
    
    for m in matches:
        ev = m["event"]
        t1_id = m["league_entry_1"]
        t2_id = m["league_entry_2"]
        if t1_id not in official_stats or t2_id not in official_stats:
            continue
            
        # Matches strictly before the active gameweek count towards Official Standings
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
                _, _, s1, _, _, _ = evaluate_lineup(p1, live_elements, element_lookup, club_minutes, pos_map, team_map)
                _, _, s2, _, _, _ = evaluate_lineup(p2, live_elements, element_lookup, club_minutes, pos_map, team_map)
                
            live_stats[t1_id]["gw_score"] = s1
            live_stats[t2_id]["gw_score"] = s2
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

    # Build Official Standings
    official_rows = []
    for e in entries:
        t_id = e["id"]
        stat = official_stats[t_id]
        official_rows.append({
            "team_id": t_id,
            "Team": e.get("entry_name", "Team"),
            "Manager": str(e.get("player_first_name", "")) + " " + str(e.get("player_last_name", "")),
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

    # Build Live Standings
    live_rows = []
    for e in entries:
        t_id = e["id"]
        stat = live_stats[t_id]
        live_rows.append({
            "team_id": t_id,
            "Team": e.get("entry_name", "Team"),
            "Manager": str(e.get("player_first_name", "")) + " " + str(e.get("player_last_name", "")),
            "W": stat["wins"],
            "D": stat["draws"],
            "L": stat["losses"],
            "PF": stat["pf"],
            "Pts": stat["pts"],
            "Live Score": stat["gw_score"]
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
    live_df = pd.DataFrame(live_rows)[["Pos", "Move", "Team", "Manager", "W", "D", "L", "PF", "Pts", "Live Score"]].set_index("Pos")
    
    return official_df, live_df

# ----------------- HOME PAGE -----------------
if st.session_state.page == "Home":
    col_brand, col_intro = st.columns([1, 4])
    with col_brand:
        if logo_path.exists():
            st.image(str(logo_path), use_container_width = True)
    with col_intro:
        st.markdown(f"""
        <div style="margin-top: 5px;">
            <span style="background-color: {active_theme['badge_bg']}; color: {active_theme['accent']}; border: 1px solid {active_theme['accent']}; font-weight: 800; font-size: 0.72rem; padding: 3px 8px; border-radius: 4px; letter-spacing: 1px;">
                {active_theme['tag']}
            </span>
            <h1 style="margin: 0.4rem 0 0.1rem 0; font-size: 2.4rem;">CDP App {dash} Season X</h1>
            <p style="color: #94a3b8; margin: 0; font-size: 0.95rem;">Dellarverse HQ: Central Draft Intelligence, Live Projections and Official Publications</p>
        </div>
        """, unsafe_allow_html = True)

    st.write("")
    
    with st.container(border = True):
        st.subheader("Current Competition Status")
        st.markdown(f"**Active Division:** <span style='color: {active_theme['accent']}; font-weight: bold; font-size: 1.1rem;'>{selected_league_key}</span>", unsafe_allow_html = True)
        st.caption("Live feed connected to Premier League Draft API")
    
    st.markdown("#### Quick Launchpad")
    btn_c1, btn_c2, btn_c3, btn_c4, btn_c5, btn_c6 = st.columns(6)
    with btn_c1:
        st.button(
            "🔴 LIVE SCORES",
            on_click = set_page,
            args = ("LIVE SCORES",),
            type = "primary",
            use_container_width = True
        )
    with btn_c2:
        st.button(
            "🏆 Standings",
            on_click = set_page,
            args = ("Standings",),
            use_container_width = True
        )
    with btn_c3:
        st.button(
            "⚽ EPL SCORES",
            on_click = set_page,
            args = ("EPL SCORES",),
            use_container_width = True
        )
    with btn_c4:
        st.button(
            "Squad Analyser",
            on_click = set_page,
            args = ("Squad Analyser",),
            use_container_width = True
        )
    with btn_c5:
        st.button(
            "Results Analyser",
            on_click = set_page,
            args = ("Results Analyser",),
            use_container_width = True
        )
    with btn_c6:
        st.button(
            "Newsletters",
            on_click = set_page,
            args = ("Newsletters",),
            use_container_width = True
        )

    st.divider()

    st.subheader("Core Capabilities")
    st.markdown("* **LIVE SCORES**: Around the grounds matchday scoreboard, live win probabilities and real time auto subs.")
    st.markdown("* **Standings**: Real time in play standings with movement indicators alongside frozen official tables.")
    st.markdown("* **EPL SCORES**: Premier League fixtures, goalscorers, assists, clean sheets, DEFCON metrics and discipline.")
    st.markdown("* **Squad Analyser**: Formations, injury probability factoring and starting eleven hierarchy.")
    st.markdown("* **Results Analyser**: Historical head to head match breakdowns across past gameweeks.")
    st.markdown("* **Publications Reader**: Embedded full page previews for both League and Cup gazettes.")

# ----------------- LIVE SCORES (MATCHDAY COMMAND CENTER) -----------------
elif st.session_state.page == "LIVE SCORES":
    st.title("🔴 LIVE SCORES" + dash + selected_league_key)
    
    static_data = fetch_fpl_static()
    league_details, _ = fetch_league_data(active_league_id)
    
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
        
        t1_start, t1_b, t1_live, t1_proj, t1_in_play, t1_ytp = evaluate_lineup(p1, live_elements, element_lookup, club_minutes, pos_map, team_map)
        t2_start, t2_b, t2_live, t2_proj, t2_in_play, t2_ytp = evaluate_lineup(p2, live_elements, element_lookup, club_minutes, pos_map, team_map)
        
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
                    hdr_l, hdr_r = st.columns([3, 1])
                    with hdr_l:
                        st.markdown("**" + item["e1"].get("entry_name", "Team 1") + " vs " + item["e2"].get("entry_name", "Team 2") + "**")
                    with hdr_r:
                        st.markdown(f"<p style='text-align: right; margin: 0; font-size: 0.85rem; color: {active_theme['accent']};'><b>{status_badge}</b></p>", unsafe_allow_html = True)
                        
                    t1_rem_text = format_remaining_players(item["t1_in_play"], item["t1_ytp"])
                    t2_rem_text = format_remaining_players(item["t2_in_play"], item["t2_ytp"])

                    sc_col1, sc_col2, sc_col3 = st.columns([5, 1, 5])
                    with sc_col1:
                        st.markdown("<h3 style='margin: 0; font-size: 2.1rem; color: #ffffff;'>" + str(item["t1_score"]) + "</h3>", unsafe_allow_html = True)
                        st.markdown("<p style='margin: 0; font-size: 0.8rem; color: #94a3b8; white-space: nowrap;'>Proj: " + str(item["t1_proj"]) + " (" + t1_rem_text + ")</p>", unsafe_allow_html = True)
                    with sc_col2:
                        st.markdown("<p style='text-align: center; margin: 12px 0; color: #64748b; font-weight: bold;'>vs</p>", unsafe_allow_html = True)
                    with sc_col3:
                        st.markdown("<h3 style='text-align: right; margin: 0; font-size: 2.1rem; color: #ffffff;'>" + str(item["t2_score"]) + "</h3>", unsafe_allow_html = True)
                        st.markdown("<p style='text-align: right; margin: 0; font-size: 0.8rem; color: #94a3b8; white-space: nowrap;'>Proj: " + str(item["t2_proj"]) + " (" + t2_rem_text + ")</p>", unsafe_allow_html = True)
                    
                    st.progress(item["prob1"] / 100.0)
                    
                    # Highlight favorite in accent color and underdog in muted gray
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
        return item["e1"].get("entry_name", "Team 1") + " (" + str(item["t1_score"]) + ") vs (" + str(item["t2_score"]) + ") " + item["e2"].get("entry_name", "Team 2")

    spotlight_idx = st.selectbox(
        "Inspect Matchup Details",
        range(len(match_summaries)),
        format_func = lambda i: spot_label(i)
    )
    
    active_spot = match_summaries[spotlight_idx]
    
    s_c1, s_c2 = st.columns(2)
    display_cols = ["Player", "Pos", "Club", "State", "Pts", "Proj", "Mins", "G", "A", "CS", "Bonus"]

    with s_c1:
        st.markdown("### " + active_spot["e1"].get("entry_name"))
        st.caption("Manager: " + str(active_spot["e1"].get("player_first_name", "")) + " " + str(active_spot["e1"].get("player_last_name", "")))
        if not active_spot["t1_start"].empty:
            st.markdown("**Starting XI (GK First)**")
            st.table(active_spot["t1_start"][display_cols].set_index("Player"))
            st.markdown("**Bench Substitutes**")
            st.table(active_spot["t1_b"][display_cols].set_index("Player"))
        else:
            st.info("Lineup selections not yet available.")

    with s_c2:
        st.markdown("### " + active_spot["e2"].get("entry_name"))
        st.caption("Manager: " + str(active_spot["e2"].get("player_first_name", "")) + " " + str(active_spot["e2"].get("player_last_name", "")))
        if not active_spot["t2_start"].empty:
            st.markdown("**Starting XI (GK First)**")
            st.table(active_spot["t2_start"][display_cols].set_index("Player"))
            st.markdown("**Bench Substitutes**")
            st.table(active_spot["t2_b"][display_cols].set_index("Player"))
        else:
            st.info("Lineup selections not yet available.")

# ----------------- STANDINGS SECTION -----------------
elif st.session_state.page == "Standings":
    st.title("🏆 Standings" + dash + selected_league_key)
    
    static_data = fetch_fpl_static()
    league_details, _ = fetch_league_data(active_league_id)
    
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
    
    # Auto detect current gameweek
    all_events = sorted(list({m["event"] for m in matches}))
    unplayed_events = sorted(list({m["event"] for m in matches if not m.get("finished", False)}))

    if unplayed_events:
        current_gw = unplayed_events[0]
    else:
        current_gw = all_events[-1] if all_events else 1

    last_completed_gw = current_gw - 1 if current_gw > 1 else 1

    # Fetch live elements and club minutes for real time table
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
        entries, matches, current_gw, live_elements, element_lookup, club_minutes, pos_map, team_map
    )

    standings_tab1, standings_tab2 = st.tabs([
        "🟢 Live Standings (In Play)",
        f"📊 Official Standings (GW {last_completed_gw})"
    ])

    with standings_tab1:
        st.subheader("Live Standings " + dash + " Active Round (GW " + str(current_gw) + ")")
        st.caption("Updated continuously with active points. Movement indicators show changes against previous official rank.")
        st.table(live_table_df)

    with standings_tab2:
        st.subheader("Official Standings " + dash + " Frozen Table (GW " + str(last_completed_gw) + ")")
        st.caption("Standings after the most recently concluded gameweek.")
        st.table(official_table_df)

# ----------------- EPL SCORES SECTION -----------------
elif st.session_state.page == "EPL SCORES":
    st.title("⚽ EPL SCORES")
    
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

            # Match Breakdown Expander
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
                        st.markdown("<span style='color: #22c55e;'>🧤 <b>Penalties Saved:</b> " + ", ".join([f"{n} ({v})" if v > 1 else n for n, v in a_psaved]) + "</span>", unsafe_allow_html = True)
                    if not (a_goals or a_assists or a_defcon or a_saves or a_cs_players or a_og or a_pmiss or a_psaved):
                        st.caption("No registered match events yet.")

                bonus_list = stats_dict.get("bonus", {}).get("h", []) + stats_dict.get("bonus", {}).get("a", [])
                if bonus_list:
                    st.divider()
                    bonus_list = sorted(bonus_list, key = lambda x: x.get("value", 0), reverse = True)
                    bonus_formatted = [f"{element_lookup.get(b['element'], {}).get('web_name', 'Unknown')} ({b['value']} pts)" for b in bonus_list]
                    st.markdown("⭐ **Bonus Points:** " + " | ".join(bonus_formatted))

# ----------------- RESULTS ANALYSER SECTION (HISTORICAL ARCHIVES) -----------------
elif st.session_state.page == "Results Analyser":
    st.title("Results Analyser" + dash + selected_league_key)
    
    static_data = fetch_fpl_static()
    league_details, _ = fetch_league_data(active_league_id)
    
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
    element_lookup = {item["id"]: item for item in static_data["elements"]}
    
    ctrl_col1, ctrl_col2 = st.columns([1, 2])
    with ctrl_col1:
        view_mode = st.radio("Browse Fixtures", ["By Gameweek", "By Team"], horizontal = True)
        
    selected_match = None
    
    if view_mode == "By Gameweek":
        all_events = sorted(list({m["event"] for m in matches}))
        played_events = sorted(list({m["event"] for m in matches if not m.get("finished", False)}))
        default_gw = played_events[-1] if played_events else all_events[0]
        
        with ctrl_col2:
            chosen_gw = st.selectbox("Select Gameweek", all_events, index = all_events.index(default_gw))
            
        gw_matches = [m for m in matches if m["event"] == chosen_gw]
        
        def match_label_gw(m):
            e1 = lentry_map.get(m["league_entry_1"], {})
            e2 = lentry_map.get(m["league_entry_2"], {})
            s1 = m.get("league_entry_1_points", 0)
            s2 = m.get("league_entry_2_points", 0)
            status = " (FT)" if m.get("finished") else ""
            return e1.get("entry_name", "Team 1") + " (" + str(s1) + ") vs (" + str(s2) + ") " + e2.get("entry_name", "Team 2") + status
            
        match_idx = st.selectbox(
            "Select Fixture",
            range(len(gw_matches)),
            format_func = lambda i: match_label_gw(gw_matches[i])
        )
        selected_match = gw_matches[match_idx]
        
    else:
        team_choices = {e["id"]: e["entry_name"] + " (" + e["player_first_name"] + " " + e["player_last_name"] + ")" for e in entries}
        with ctrl_col2:
            chosen_team_lid = st.selectbox("Select Team", list(team_choices.keys()), format_func = lambda x: team_choices[x])
            
        team_matches = [m for m in matches if m["league_entry_1"] == chosen_team_lid or m["league_entry_2"] == chosen_team_lid]
        team_matches = sorted(team_matches, key = lambda x: x["event"])
        
        def match_label_team(m):
            e1 = lentry_map.get(m["league_entry_1"], {})
            e2 = lentry_map.get(m["league_entry_2"], {})
            s1 = m.get("league_entry_1_points", 0)
            s2 = m.get("league_entry_2_points", 0)
            status = " (FT)" if m.get("finished") else ""
            return "GW " + str(m["event"]) + ": " + e1.get("entry_name", "Team 1") + " (" + str(s1) + ") vs (" + str(s2) + ") " + e2.get("entry_name", "Team 2") + status

        t_idx = st.selectbox(
            "Select Matchup",
            range(len(team_matches)),
            format_func = lambda i: match_label_team(team_matches[i])
        )
        selected_match = team_matches[t_idx]

    if selected_match:
        gw_num = selected_match["event"]
        e1_info = lentry_map.get(selected_match["league_entry_1"], {})
        e2_info = lentry_map.get(selected_match["league_entry_2"], {})
        score1 = selected_match.get("league_entry_1_points", 0)
        score2 = selected_match.get("league_entry_2_points", 0)
        
        st.divider()
        
        res_col1, res_col2, res_col3 = st.columns([4, 2, 4])
        with res_col1:
            st.markdown("### " + str(e1_info.get("entry_name", "Team 1")))
            st.caption("Manager: " + str(e1_info.get("player_first_name", "")) + " " + str(e1_info.get("player_last_name", "")))
        with res_col2:
            status_text = "FINAL SCORE" if selected_match.get("finished") else "ARCHIVED SCORE"
            st.markdown("<h2 style='text-align: center; margin: 0; font-size: 2.2rem; color: #ffffff;'>" + str(score1) + dash + str(score2) + "</h2>", unsafe_allow_html = True)
            st.markdown("<p style='text-align: center; color: #64748b; margin: 0; font-weight: bold;'>" + status_text + " (GW " + str(gw_num) + ")</p>", unsafe_allow_html = True)
        with res_col3:
            st.markdown("<h3 style='text-align: right;'>" + str(e2_info.get("entry_name", "Team 2")) + "</h3>", unsafe_allow_html = True)
            st.markdown("<p style='text-align: right; color: #64748b; margin: 0;'>Manager: " + str(e2_info.get("player_first_name", "")) + " " + str(e2_info.get("player_last_name", "")) + "</p>", unsafe_allow_html = True)
            
        st.divider()

        picks1_data = fetch_entry_event(e1_info.get("entry_id"), gw_num)
        picks2_data = fetch_entry_event(e2_info.get("entry_id"), gw_num)
        live_data = fetch_live_event(gw_num)
        live_elements = live_data.get("elements", {}) if live_data else {}

        def build_player_rows(picks_list):
            if not picks_list:
                return pd.DataFrame(), pd.DataFrame()
            starters = []
            bench = []
            for p in picks_list.get("picks", []):
                elem_id = p["element"]
                raw_elem = element_lookup.get(elem_id, {})
                stats = live_elements.get(str(elem_id), {}).get("stats", {})
                pos_type = raw_elem.get("element_type", 1)
                row = {
                    "Player": raw_elem.get("web_name", "Unknown"),
                    "pos_num": pos_type,
                    "Pos": pos_map.get(pos_type, ""),
                    "Club": team_map.get(raw_elem.get("team"), ""),
                    "Mins": stats.get("minutes", 0),
                    "Pts": stats.get("total_points", 0),
                    "G": stats.get("goals_scored", 0),
                    "A": stats.get("assists", 0),
                    "CS": stats.get("clean_sheets", 0),
                    "GC": stats.get("goals_conceded", 0),
                    "Bonus": stats.get("bonus", 0),
                    "pick_pos": p.get("position", 99)
                }
                if p.get("position", 99) <= 11:
                    starters.append(row)
                else:
                    bench.append(row)
            starters_df = pd.DataFrame(starters)
            bench_df = pd.DataFrame(bench)
            if not starters_df.empty:
                starters_df = starters_df.sort_values(by = ["pos_num", "Pts"], ascending = [True, False])
            if not bench_df.empty:
                bench_df = bench_df.sort_values(by = "pick_pos", ascending = True)
            return starters_df, bench_df

        team1_starters, team1_bench = build_player_rows(picks1_data)
        team2_starters, team2_bench = build_player_rows(picks2_data)
        display_cols = ["Player", "Pos", "Club", "Mins", "Pts", "G", "A", "CS", "GC", "Bonus"]

        side1, side2 = st.columns(2)
        with side1:
            st.subheader(str(e1_info.get("entry_name")) + " Lineup")
            if not team1_starters.empty:
                st.markdown("**Starting XI (GK First)**")
                st.table(team1_starters[display_cols].set_index("Player"))
                st.markdown("**Bench Substitutes**")
                st.table(team1_bench[display_cols].set_index("Player"))
            else:
                st.info("Lineup selections not yet available for this gameweek.")

        with side2:
            st.subheader(str(e2_info.get("entry_name")) + " Lineup")
            if not team2_starters.empty:
                st.markdown("**Starting XI (GK First)**")
                st.table(team2_starters[display_cols].set_index("Player"))
                st.markdown("**Bench Substitutes**")
                st.table(team2_bench[display_cols].set_index("Player"))
            else:
                st.info("Lineup selections not yet available for this gameweek.")

# ----------------- NEWSLETTERS SECTION -----------------
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

# ----------------- SQUAD ANALYSER SECTION -----------------
elif st.session_state.page == "Squad Analyser":
    st.title("Squad Analyser" + dash + selected_league_key)
    
    static_data = fetch_fpl_static()
    league_details, element_status = fetch_league_data(active_league_id)
    
    if not static_data or not league_details or not element_status:
        st.error("Failed to load league data. Verify connection and try again.")
        st.stop()
        
    pos_map = {item["id"]: item["singular_name_short"] for item in static_data["element_types"]}
    team_map = {item["id"]: item["short_name"] for item in static_data["teams"]}

    elements_df = pd.DataFrame(static_data["elements"])
    elements_df["position"] = elements_df["element_type"].map(pos_map)
    elements_df["club"] = elements_df["team"].map(team_map)
    elements_df["form"] = pd.to_numeric(elements_df["form"], errors = "coerce").fillna(0)
    elements_df["points_per_game"] = pd.to_numeric(elements_df["points_per_game"], errors = "coerce").fillna(0)
    elements_df["ict_index"] = pd.to_numeric(elements_df["ict_index"], errors = "coerce").fillna(0)
    elements_df["total_points"] = pd.to_numeric(elements_df["total_points"], errors = "coerce").fillna(0)
    elements_df["chance_of_playing_next_round"] = pd.to_numeric(elements_df["chance_of_playing_next_round"], errors = "coerce")

    elements_df["avail_factor"] = elements_df.apply(get_availability_multiplier, axis = 1)
    elements_df["health_status"] = elements_df.apply(get_health_label, axis = 1)

    status_df = pd.DataFrame(element_status["element_status"])
    merged = elements_df.merge(status_df, left_on="id", right_on="element", how="inner")

    entries = league_details.get("league_entries", [])
    entry_options = {
        e["entry_id"]: e["entry_name"] + " (" + e["player_first_name"] + " " + e["player_last_name"] + ")"
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

    tab_lineup, tab_waivers, tab_squad = st.tabs(["Recommended Lineup", "Top Waiver Targets", "Full Squad Overview"])

    with tab_lineup:
        st.subheader("Recommended Starting XI and Bench Strategy")
        
        if my_squad.empty:
            st.warning("No players found for this team selection.")
        else:
            def compute_starter_rating(r):
                if r["avail_factor"] == 0.0:
                    return 0 - 9999.0
                base_score = (r["form"] * 2.5) + (r["points_per_game"] * 1.8) + (r["ict_index"] * 0.05)
                return base_score * r["avail_factor"]

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
                fit_bonus = 100.0 if r["avail_factor"] == 1.0 else (50.0 if r["avail_factor"] > 0.0 else 0 - 500.0)
                return fit_bonus + (r["form"] * 2.0) + r["points_per_game"]

            all_bench_outfield["bench_score"] = all_bench_outfield.apply(bench_priority, axis = 1)
            ordered_bench_outfield = all_bench_outfield.sort_values(by = "bench_score", ascending = False)
            
            col_start, col_bench = st.columns([3, 2])
            
            with col_start:
                st.markdown("### Starters (GK First)")
                xi_df = pd.DataFrame(starting_xi)
                xi_df["pos_rank"] = xi_df["position"].map(POS_ORDER)
                xi_df = xi_df.sort_values(by = ["pos_rank", "starter_rating"], ascending = [True, False])
                
                st.table(xi_df[["web_name", "position", "club", "health_status", "form", "points_per_game"]].rename(columns = {
                    "web_name": "Player",
                    "position": "Pos",
                    "club": "Club",
                    "health_status": "Status",
                    "form": "Form",
                    "points_per_game": "PPG"
                }).set_index("Player"))
                
            with col_bench:
                st.markdown("### Bench Hierarchy")
                if bench_gk:
                    st.markdown("**Goalkeeper Reserve**")
                    bgk_df = pd.DataFrame(bench_gk)[["web_name", "position", "club", "health_status"]]
                    st.table(bgk_df.rename(columns = {"web_name": "Player", "position": "Pos", "club": "Club", "health_status": "Status"}).set_index("Player"))
                if not ordered_bench_outfield.empty:
                    st.markdown("**Outfield Substitutes (Auto Sub Order)**")
                    bo_df = ordered_bench_outfield[["web_name", "position", "club", "health_status", "form"]]
                    st.table(bo_df.rename(columns = {"web_name": "Player", "position": "Pos", "club": "Club", "health_status": "Status", "form": "Form"}).set_index("Player"))
                    st.caption("Sub 1 prioritises 100% fit players to guarantee cover if a doubtful starter misses out.")

    with tab_waivers:
        st.subheader("Waiver Wire and Free Agent Intelligence")
        
        col_w1, col_w2, col_w3 = st.columns([2, 2, 2])
        with col_w1:
            scout_mode = st.radio("Scout Focus", ["This Gameweek (Ready Now)", "Stash Targets (High Ceiling / Sidelined)"])
        with col_w2:
            pos_filter = st.multiselect("Positions", ["GKP", "DEF", "MID", "FWD"], default = ["DEF", "MID", "FWD"])
        with col_w3:
            min_pts = st.slider("Minimum Total Points", 0, 50, 5)
            
        filtered_waivers = waiver_pool[
            (waiver_pool["position"].isin(pos_filter)) & 
            (waiver_pool["total_points"] >= min_pts)
        ].copy()
        
        if "This Gameweek" in scout_mode:
            filtered_waivers = filtered_waivers[filtered_waivers["avail_factor"] >= 0.65]
            filtered_waivers["cdp_score"] = (
                ((filtered_waivers["form"] * 2.5) + (filtered_waivers["points_per_game"] * 1.8) + (filtered_waivers["ict_index"] * 0.1))
                * filtered_waivers["avail_factor"]
            ).round(2)
            score_label = "GW Rating"
        else:
            filtered_waivers["cdp_score"] = (
                (filtered_waivers["points_per_game"] * 3.0) + 
                (filtered_waivers["form"] * 1.5) + 
                (filtered_waivers["ict_index"] * 0.15)
            ).round(2)
            score_label = "Stash Value"
        
        top_waivers = filtered_waivers.sort_values(by = "cdp_score", ascending = False).head(15)
        
        display_cols = ["web_name", "position", "club", "health_status", "form", "points_per_game", "total_points", "news", "cdp_score"]
        st.table(
            top_waivers[display_cols].rename(columns = {
                "web_name": "Player",
                "position": "Pos",
                "club": "Team",
                "health_status": "Status",
                "form": "Form",
                "points_per_game": "PPG",
                "total_points": "Total Pts",
                "news": "Notes",
                "cdp_score": score_label
            }).set_index("Player")
        )

    with tab_squad:
        st.subheader("Your Full 15 Man Roster")
        squad_display = my_squad.copy()
        squad_display["pos_rank"] = squad_display["position"].map(POS_ORDER)
        squad_display = squad_display.sort_values(by = ["pos_rank", "total_points"], ascending = [True, False])
        
        st.table(
            squad_display[["web_name", "position", "club", "health_status", "form", "points_per_game", "total_points", "news"]].rename(columns = {
                "web_name": "Player",
                "position": "Pos",
                "club": "Club",
                "health_status": "Availability",
                "form": "Form",
                "points_per_game": "PPG",
                "total_points": "Total Pts",
                "news": "Injury Report"
            }).set_index("Player")
        )
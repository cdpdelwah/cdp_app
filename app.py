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
    ["Home", "LIVE SCORES", "EPL SCORES", "Squad Analyser", "Results Analyser", "Newsletters"],
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
    btn_c1, btn_c2, btn_c3, btn_c4, btn_c5 = st.columns(5)
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
            "⚽ EPL SCORES",
            on_click = set_page,
            args = ("EPL SCORES",),
            use_container_width = True
        )
    with btn_c3:
        st.button(
            "Squad Analyser",
            on_click = set_page,
            args = ("Squad Analyser",),
            use_container_width = True
        )
    with btn_c4:
        st.button(
            "Results Analyser",
            on_click = set_page,
            args = ("Results Analyser",),
            use_container_width = True
        )
    with btn_c5:
        st.button(
            "Newsletters",
            on_click = set_page,
            args = ("Newsletters",),
            use_container_width = True
        )

    st.divider()

    st.subheader("Core Capabilities")
    st.markdown("* **LIVE SCORES**: Around the grounds matchday scoreboard, live win probabilities and real time auto subs.")
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

                    sc_col1, sc_col2, sc_col3 = st.columns([3, 2, 3])
                    with sc_col1:
                        st.markdown("<h3 style='margin: 0; font-size: 2.1rem; color: #ffffff;'>" + str(item["t1_score"]) + "</h3>", unsafe_allow_html = True)
                        st.caption("Proj: " + str(item["t1_proj"]) + " (" + t1_rem_text + ")")
                    with sc_col2:
                        st.markdown("<p style='text-align: center; margin: 12px 0; color: #64748b; font-weight: bold;'>vs</p>", unsafe_allow_html = True)
                    with sc_col3:
                        st.markdown("<h3 style='text-align: right; margin: 0; font-size: 2.1rem; color: #ffffff;'>" + str(item["t2_score"]) + "</h3>", unsafe_allow_html = True)
                        st.markdown("<p style='text-align: right; margin: 0; font-size: 0.85rem; color: #94a3b8;'>Proj: " + str(item["t2_proj"]) + " (" + t2_rem_text + ")</p>", unsafe_allow_html = True)
                    
                    st.progress(item["prob1"] / 100.0)
                    
                    # Highlight favorite in accent color and underdog in muted gray
                    if
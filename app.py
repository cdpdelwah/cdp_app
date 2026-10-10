import streamlit as st
import requests
import pandas as pd
import math
from pathlib import Path
import pypdfium2 as pdfium

base_dir = Path(__file__).resolve().parent

# Check for Assets directory (capitalised and lowercase)
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

# Positional hierarchy mapping for display ordering
POS_ORDER = {"GKP": 1, "DEF": 2, "MID": 3, "FWD": 4}

# Bind navigation directly to session state
if "page" not in st.session_state:
    st.session_state.page = "Home"

def set_page(page_name):
    st.session_state.page = page_name

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
    url = "https://draft.premierleague.com/api/bootstrap-static"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    return response.json()

@st.cache_data(ttl = 600)
def fetch_league_data(league_id):
    if not league_id:
        return None, None
    details_url = "https://draft.premierleague.com/api/league/" + str(league_id) + "/details"
    status_url = "https://draft.premierleague.com/api/league/" + str(league_id) + "/element-status"
    
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
        return pd.DataFrame(), pd.DataFrame(), 0, 0.0, 0
        
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
    to_play = sum(1 for p in active_lineup if p["State"] in ["YTP", "LIVE"])
    
    starters_df = pd.DataFrame(starters).sort_values(by = ["pos_num", "Pts"], ascending = [True, False])
    bench_df = pd.DataFrame(bench).sort_values(by = "pick_pos", ascending = True)
    
    return starters_df, bench_df, live_score, round(proj_score, 1), to_play

# Sidebar Brand & Navigation
if logo_path.exists():
    st.sidebar.image(str(logo_path), use_container_width = True)
else:
    st.sidebar.title("CDP App")

st.sidebar.caption("Stats, not facts | Season X Command Center")

st.sidebar.radio(
    "Navigation Menu",
    ["Home", "LIVE SCORES", "Squad Analyser", "Results Analyser", "Newsletters"],
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

# ----------------- HOME PAGE -----------------
if st.session_state.page == "Home":
    col_brand, col_intro = st.columns([1, 4])
    with col_brand:
        if logo_path.exists():
            st.image(str(logo_path), use_container_width = True)
    with col_intro:
        st.title("CDP App " + dash + " Season X")
        st.caption("Dellarverse HQ: Central Draft Intelligence, Live Projections and Official Publications")

    st.markdown("### Welcome to the Dellarverse Hub")
    st.write(
        "Use the sidebar or the launchpad below to track live weekend fixtures, "
        "optimise your squad, inspect past results or read official league publications."
    )
    
    st.subheader("Current Competition Status")
    st.info("**Selected League:** " + selected_league_key)
    st.success("League linked and ready")
    
    st.markdown("#### Quick Launchpad")
    btn_c1, btn_c2, btn_c3, btn_c4 = st.columns(4)
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
            "Squad Analyser",
            on_click = set_page,
            args = ("Squad Analyser",),
            use_container_width = True
        )
    with btn_c3:
        st.button(
            "Results Analyser",
            on_click = set_page,
            args = ("Results Analyser",),
            use_container_width = True
        )
    with btn_c4:
        st.button(
            "Newsletters",
            on_click = set_page,
            args = ("Newsletters",),
            use_container_width = True
        )

    st.divider()

    st.subheader("Core Capabilities")
    st.markdown("* **LIVE SCORES**: Around the grounds matchday scoreboard, live win probabilities and real time auto subs.")
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
        
        t1_start, t1_b, t1_live, t1_proj, t1_ytp = evaluate_lineup(p1, live_elements, element_lookup, club_minutes, pos_map, team_map)
        t2_start, t2_b, t2_live, t2_proj, t2_ytp = evaluate_lineup(p2, live_elements, element_lookup, club_minutes, pos_map, team_map)
        
        if is_fin:
            t1_score = m.get("league_entry_1_points", t1_live)
            t2_score = m.get("league_entry_2_points", t2_live)
        else:
            t1_score = t1_live
            t2_score = t2_live
            
        prob1, prob2 = calculate_win_probability(t1_score, t1_proj, t1_ytp, t2_score, t2_proj, t2_ytp, is_fin)
        
        match_summaries.append({
            "match": m,
            "e1": e1,
            "e2": e2,
            "t1_score": t1_score,
            "t2_score": t2_score,
            "t1_proj": t1_proj,
            "t2_proj": t2_proj,
            "t1_ytp": t1_ytp,
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
                        st.markdown("<p style='text-align: right; margin: 0; font-size: 0.85rem;'><b>" + status_badge + "</b></p>", unsafe_allow_html = True)
                        
                    sc_col1, sc_col2, sc_col3 = st.columns([3, 2, 3])
                    with sc_col1:
                        st.markdown("<h3 style='margin: 0;'>" + str(item["t1_score"]) + "</h3>", unsafe_allow_html = True)
                        st.caption("Proj: " + str(item["t1_proj"]) + " (" + str(item["t1_ytp"]) + " to play)")
                    with sc_col2:
                        st.markdown("<p style='text-align: center; margin: 10px 0; color: gray;'>vs</p>", unsafe_allow_html = True)
                    with sc_col3:
                        st.markdown("<h3 style='text-align: right; margin: 0;'>" + str(item["t2_score"]) + "</h3>", unsafe_allow_html = True)
                        st.markdown("<p style='text-align: right; margin: 0; font-size: 0.85rem; color: gray;'>Proj: " + str(item["t2_proj"]) + " (" + str(item["t2_ytp"]) + " to play)</p>", unsafe_allow_html = True)
                    
                    st.progress(item["prob1"] / 100.0)
                    p_l, p_r = st.columns(2)
                    with p_l:
                        st.caption("Win: **" + str(item["prob1"]) + "%**")
                    with p_r:
                        st.markdown("<p style='text-align: right; margin: 0; font-size: 0.8rem; color: gray;'>Win: <b>" + str(item["prob2"]) + "%</b></p>", unsafe_allow_html = True)

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
    display_cols = ["Player", "Pos", "Club", "State", "Pts", "Proj", "Mins", "G", "A", "CS", "Bonus", "sub_action"]

    with s_c1:
        st.markdown("### " + active_spot["e1"].get("entry_name"))
        st.caption("Manager: " + str(active_spot["e1"].get("player_first_name", "")) + " " + str(active_spot["e1"].get("player_last_name", "")))
        if not active_spot["t1_start"].empty:
            st.markdown("**Starting XI (GK First)**")
            st.dataframe(active_spot["t1_start"][display_cols].rename(columns = {"sub_action": "Auto Sub"}), use_container_width = True, hide_index = True)
            st.markdown("**Bench Substitutes**")
            st.dataframe(active_spot["t1_b"][display_cols].rename(columns = {"sub_action": "Auto Sub"}), use_container_width = True, hide_index = True)
        else:
            st.info("Lineup selections not yet available.")

    with s_c2:
        st.markdown("### " + active_spot["e2"].get("entry_name"))
        st.caption("Manager: " + str(active_spot["e2"].get("player_first_name", "")) + " " + str(active_spot["e2"].get("player_last_name", "")))
        if not active_spot["t2_start"].empty:
            st.markdown("**Starting XI (GK First)**")
            st.dataframe(active_spot["t2_start"][display_cols].rename(columns = {"sub_action": "Auto Sub"}), use_container_width = True, hide_index = True)
            st.markdown("**Bench Substitutes**")
            st.dataframe(active_spot["t2_b"][display_cols].rename(columns = {"sub_action": "Auto Sub"}), use_container_width = True, hide_index = True)
        else:
            st.info("Lineup selections not yet available.")

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
        played_events = sorted(list({m["event"] for m in matches if m.get("finished", False)}))
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
            st.markdown("<h2 style='text-align: center; margin: 0;'>" + str(score1) + dash + str(score2) + "</h2>", unsafe_allow_html = True)
            st.markdown("<p style='text-align: center; color: gray; margin: 0;'>" + status_text + " (GW " + str(gw_num) + ")</p>", unsafe_allow_html = True)
        with res_col3:
            st.markdown("<h3 style='text-align: right;'>" + str(e2_info.get("entry_name", "Team 2")) + "</h3>", unsafe_allow_html = True)
            st.markdown("<p style='text-align: right; color: gray; margin: 0;'>Manager: " + str(e2_info.get("player_first_name", "")) + " " + str(e2_info.get("player_last_name", "")) + "</p>", unsafe_allow_html = True)
            
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
                st.dataframe(team1_starters[display_cols], use_container_width = True, hide_index = True)
                st.markdown("**Bench Substitutes**")
                st.dataframe(team1_bench[display_cols], use_container_width = True, hide_index = True)
            else:
                st.info("Lineup selections not yet available for this gameweek.")

        with side2:
            st.subheader(str(e2_info.get("entry_name")) + " Lineup")
            if not team2_starters.empty:
                st.markdown("**Starting XI (GK First)**")
                st.dataframe(team2_starters[display_cols], use_container_width = True, hide_index = True)
                st.markdown("**Bench Substitutes**")
                st.dataframe(team2_bench[display_cols], use_container_width = True, hide_index = True)
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
    merged = elements_df.merge(status_df, left_on = "id", right_on = "element", how = "inner")

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
                }))
                
            with col_bench:
                st.markdown("### Bench Hierarchy")
                if bench_gk:
                    st.markdown("**Goalkeeper Reserve**")
                    bgk_df = pd.DataFrame(bench_gk)[["web_name", "position", "club", "health_status"]]
                    st.table(bgk_df.rename(columns = {"web_name": "Player", "position": "Pos", "club": "Club", "health_status": "Status"}))
                if not ordered_bench_outfield.empty:
                    st.markdown("**Outfield Substitutes (Auto Sub Order)**")
                    bo_df = ordered_bench_outfield[["web_name", "position", "club", "health_status", "form"]]
                    st.table(bo_df.rename(columns = {"web_name": "Player", "position": "Pos", "club": "Club", "health_status": "Status", "form": "Form"}))
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
        st.dataframe(
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
            }),
            use_container_width = True,
            hide_index = True
        )

    with tab_squad:
        st.subheader("Your Full 15 Man Roster")
        squad_display = my_squad.copy()
        squad_display["pos_rank"] = squad_display["position"].map(POS_ORDER)
        squad_display = squad_display.sort_values(by = ["pos_rank", "total_points"], ascending = [True, False])
        
        st.dataframe(
            squad_display[["web_name", "position", "club", "health_status", "form", "points_per_game", "total_points", "news"]].rename(columns = {
                "web_name": "Player",
                "position": "Pos",
                "club": "Club",
                "health_status": "Availability",
                "form": "Form",
                "points_per_game": "PPG",
                "total_points": "Total Pts",
                "news": "Injury Report"
            }),
            use_container_width = True,
            hide_index = True
        )
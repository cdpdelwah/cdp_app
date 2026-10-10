import streamlit as st

import requests

import pandas as pd



st.set_page_config(page_title="CDP App", layout="wide")



dash = chr(45)



# Preconfigured league dictionary

LEAGUE_PRESETS = {

    "CDP (Crème Dellar Prem)": 63,

    "SDM (Segundo Del Mundo)": 320,

    "BDR (Best De La Rest)": 378,

    "LDE (Liger Del Eager)": 240,

    "Custom League": None

}



if "page" not in st.session_state:

    st.session_state.page = "Home"



if "saved_ids" not in st.session_state:

    st.session_state.saved_ids = dict(LEAGUE_PRESETS)



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



st.sidebar.markdown("---")

st.sidebar.subheader("League Selection")



selected_league_key = st.sidebar.selectbox("Active Competition", list(LEAGUE_PRESETS.keys()))



default_id_val = str(st.session_state.saved_ids.get(selected_league_key) or "")

id_input = st.sidebar.text_input(f"{selected_league_key} Numeric ID", value=default_id_val)



if id_input.strip().isdigit():

    active_league_id = int(id_input.strip())

    st.session_state.saved_ids[selected_league_key] = active_league_id

else:

    active_league_id = None



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

        if active_league_id:

            st.success(f"**Connected League ID:** `{active_league_id}`")

        else:

            st.warning("No numeric League ID assigned yet. Type the ID into the sidebar to connect.")

            

        if st.button("Launch Squad Analyser", type="primary", use_container_width=True):

            st.session_state.page = "Squad Analyser"

            st.rerun()



    with col2:

        st.subheader("Core Capabilities")

        st.markdown("* **Squad Analyser**: Formations, injury probability factoring and starting eleven hierarchy.")

        st.markdown("* **Waiver Intelligence**: Immediate gameweek priorities alongside high ceiling stash targets.")

        st.markdown("* **Multi League Switching**: Jump between CDP, SDM, BDR and LDE without losing settings.")



# Squad Analyser Section

elif st.session_state.page == "Squad Analyser":

    st.title(f"Squad Analyser - {selected_league_key}")

    

    if not active_league_id:

        st.warning(f"Please provide a numeric League ID for {selected_league_key} in the sidebar to load draft rosters.")

        st.stop()

        

    static_data = fetch_fpl_static()

    league_details, element_status = fetch_league_data(active_league_id)

    

    if not static_data or not league_details or not element_status:

        st.error("Failed to load league data. Verify the numeric League ID and check your connection.")

        st.stop()

        

    pos_map = {item["id"]: item["singular_name_short"] for item in static_data["element_types"]}

    team_map = {item["id"]: item["short_name"] for item in static_data["teams"]}



    elements_df = pd.DataFrame(static_data["elements"])

    elements_df["position"] = elements_df["element_type"].map(pos_map)

    elements_df["club"] = elements_df["team"].map(team_map)

    elements_df["form"] = pd.to_numeric(elements_df["form"], errors="coerce").fillna(0)

    elements_df["points_per_game"] = pd.to_numeric(elements_df["points_per_game"], errors="coerce").fillna(0)

    elements_df["ict_index"] = pd.to_numeric(elements_df["ict_index"], errors="coerce").fillna(0)

    elements_df["total_points"] = pd.to_numeric(elements_df["total_points"], errors="coerce").fillna(0)

    elements_df["chance_of_playing_next_round"] = pd.to_numeric(elements_df["chance_of_playing_next_round"], errors="coerce")



    elements_df["avail_factor"] = elements_df.apply(get_availability_multiplier, axis=1)

    elements_df["health_status"] = elements_df.apply(get_health_label, axis=1)



    status_df = pd.DataFrame(element_status["element_status"])

    merged = elements_df.merge(status_df, left_on="id", right_on="element", how="inner")



    entries = league_details.get("league_entries", [])

    entry_options = {e["entry_id"]: f"{e['entry_name']} ({e['player_first_name']} {e['player_last_name']})" for e in entries}



    if not entry_options:

        st.error("No teams found for this league ID.")

        st.stop()



    entry_keys = list(entry_options.keys())

    default_entry_idx = entry_keys.index(88) if 88 in entry_keys else 0



    selected_entry_id = st.sidebar.selectbox(

        "Select Your Team",

        options=entry_keys,

        format_func=lambda x: entry_options[x],

        index=default_entry_idx

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



            my_squad["starter_rating"] = my_squad.apply(compute_starter_rating, axis=1)

            sorted_squad = my_squad.sort_values(by="starter_rating", ascending=False)

            

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



            all_bench_outfield["bench_score"] = all_bench_outfield.apply(bench_priority, axis=1)

            ordered_bench_outfield = all_bench_outfield.sort_values(by="bench_score", ascending=False)

            

            col_start, col_bench = st.columns([3, 2])

            

            with col_start:

                st.markdown("### Starters")

                xi_df = pd.DataFrame(starting_xi)[["web_name", "position", "club", "health_status", "form", "points_per_game"]]

                st.table(xi_df.rename(columns={

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

                    st.table(bgk_df.rename(columns={"web_name": "Player", "position": "Pos", "club": "Club", "health_status": "Status"}))

                if not ordered_bench_outfield.empty:

                    st.markdown("**Outfield Substitutes (Auto Sub Order)**")

                    bo_df = ordered_bench_outfield[["web_name", "position", "club", "health_status", "form"]]

                    st.table(bo_df.rename(columns={"web_name": "Player", "position": "Pos", "club": "Club", "health_status": "Status", "form": "Form"}))

                    st.caption("Sub 1 prioritises 100% fit players to guarantee cover if a doubtful starter misses out.")



    with tab_waivers:

        st.subheader("Waiver Wire and Free Agent Intelligence")

        

        col_w1, col_w2, col_w3 = st.columns([2, 2, 2])

        with col_w1:

            scout_mode = st.radio("Scout Focus", ["This Gameweek (Ready Now)", "Stash Targets (High Ceiling / Sidelined)"])

        with col_w2:

            pos_filter = st.multiselect("Positions", ["GKP", "DEF", "MID", "FWD"], default=["DEF", "MID", "FWD"])

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

        

        top_waivers = filtered_waivers.sort_values(by="cdp_score", ascending=False).head(15)

        

        display_cols = ["web_name", "position", "club", "health_status", "form", "points_per_game", "total_points", "news", "cdp_score"]

        st.dataframe(

            top_waivers[display_cols].rename(columns={

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

            use_container_width=True,

            hide_index=True

        )



    with tab_squad:

        st.subheader("Your Full 15 Man Roster")

        st.dataframe(

            my_squad[["web_name", "position", "club", "health_status", "form", "points_per_game", "total_points", "news"]].rename(columns={

                "web_name": "Player",

                "position": "Pos",

                "club": "Club",

                "health_status": "Availability",

                "form": "Form",

                "points_per_game": "PPG",

                "total_points": "Total Pts",

                "news": "Injury Report"

            }),

            use_container_width=True,

            hide_index=True

        )


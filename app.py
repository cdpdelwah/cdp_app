# ----------------- EPL MATCH PROGRESSION GRAPH -----------------
        epl_fixtures = fetch_epl_fixtures(gw_num)
        gw_fixtures = [f for f in epl_fixtures if f.get("event") == gw_num] if epl_fixtures else []
        if not gw_fixtures and epl_fixtures:
            gw_fixtures = epl_fixtures

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
                            cats.append("🛡️ CS")
                        if bonus > 0:
                            cats.append(f"{bonus}⭐")

                        if cats:
                            entries_list.append(f"{p_name} ({' '.join(cats)})")
                return ", ".join(entries_list) if entries_list else "None"

            # Maintain the fixture ordering as returned by the Premier League schedule
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
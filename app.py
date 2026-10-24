"""CampusTwin - Intelligent Digital Campus. Run with:  streamlit run app.py"""
import datetime as dt
import re

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

import engine as eng
import mapview
from campus_data import BUILDINGS, KIND_LABELS, SCENARIOS, TYPE_LABELS

st.set_page_config(page_title="CampusTwin", page_icon="🏫", layout="wide")

NAMES = {b["id"]: b["name"] for b in BUILDINGS}
IDS = [b["id"] for b in BUILDINGS]


@st.cache_data(show_spinner=False)
def cached_day(scenario, closed, attendance):
    return eng.day_profile(scenario, closed, attendance)


# ------------------------------------------------------------------ sidebar
st.sidebar.title("🏫 CampusTwin")
st.sidebar.caption("Intelligent digital campus")

scenario = st.sidebar.selectbox("Scenario", list(SCENARIOS))
st.sidebar.info(SCENARIOS[scenario]["description"])
t = st.sidebar.slider("Time of day", min_value=dt.time(0, 0), max_value=dt.time(23, 45),
                      value=dt.time(11, 0), step=dt.timedelta(minutes=15))
hour = t.hour + t.minute / 60.0
attendance = st.sidebar.slider("Students on campus (%)", 20, 150, 100, step=5)
closed = tuple(st.sidebar.multiselect("Close buildings (what-if)", IDS, format_func=NAMES.get))

st.sidebar.divider()
st.sidebar.subheader("Navigate")
start = st.sidebar.selectbox("From", IDS, index=IDS.index("gate"), format_func=NAMES.get)
end = st.sidebar.selectbox("To", IDS, index=IDS.index("cse"), format_func=NAMES.get)
crowd_aware = st.sidebar.checkbox("Avoid crowded routes", value=True)

st.sidebar.divider()
st.sidebar.subheader("Map options")
base = st.sidebar.radio("Base map", ["Campus plan", "Satellite", "Street map"])
cal = dict(mapview.DEFAULT_CAL)
overlay_opacity = 0.3
with st.sidebar.expander("📍 Align with real satellite", expanded=(base != "Campus plan")):
    st.caption("1) In Google Maps, right-click your **main gate** and click the coordinates to copy them. "
               "2) Paste them below. 3) Adjust rotation / scale / shift until the outlines sit on the "
               "real buildings.")
    raw = st.text_input("Main gate (lat, lon)",
                        value=f"{mapview.DEFAULT_CAL['lat']}, {mapview.DEFAULT_CAL['lon']}")
    nums = re.findall(r"-?\d+(?:\.\d+)?", raw)
    if len(nums) >= 2 and -90 <= float(nums[0]) <= 90 and -180 <= float(nums[1]) <= 180:
        cal["lat"], cal["lon"] = float(nums[0]), float(nums[1])
    else:
        st.error("Could not read the coordinates - using the sample location.")
    cal["rotation"] = float(st.slider("Rotation (degrees)", -180, 180, int(mapview.DEFAULT_CAL["rotation"]), step=1))
    cal["scale"] = float(st.slider("Scale (size)", 0.5, 2.0, 1.0, step=0.05))
    ce, cn = st.columns(2)
    cal["east"] = float(ce.number_input("Shift east (m)", -500.0, 500.0, 0.0, step=5.0))
    cal["north"] = float(cn.number_input("Shift north (m)", -500.0, 500.0, 0.0, step=5.0))
    overlay_opacity = st.slider("Overlay opacity", 0.0, 0.8, 0.3, step=0.05)
aligned = (cal["lat"], cal["lon"]) != (mapview.DEFAULT_CAL["lat"], mapview.DEFAULT_CAL["lon"])
crowd_colors = st.sidebar.checkbox("Colour buildings by crowd", value=True)
show_heat = st.sidebar.checkbox("Crowd heatmap", value=False)
show_paths = st.sidebar.checkbox("Walkways", value=True)
show_labels = st.sidebar.checkbox("Building labels", value=True)

# ------------------------------------------------------------------ simulation
rooms = eng.room_snapshot(hour, scenario, closed, attendance)
snap = eng.snapshot(hour, scenario, closed, attendance, rooms=rooms)
ratios = dict(zip(snap["id"], snap["ratio"]))


def route_for(s, e, rat, sc):
    """Shortest route, with distance/time scaled by the calibration 'Scale' slider."""
    r = eng.shortest_path(s, e, rat, closed, crowd_aware, sc)
    if r:
        r["metres"] *= cal["scale"]
        r["minutes"] *= cal["scale"]
    return r


route = route_for(start, end, ratios, scenario)

# ------------------------------------------------------------------ header + metrics
st.title("CampusTwin - Intelligent Digital Campus")
st.caption(f"Scenario: **{scenario}**  |  Time: **{t.strftime('%I:%M %p')}**")

open_df = snap[~snap["closed"]]
c1, c2, c3, c4 = st.columns(4)
c1.metric("People on campus", f"{int(snap['occupancy'].sum()):,}")
if not open_df.empty:
    busiest = open_df.sort_values("ratio", ascending=False).iloc[0]
    quietest = open_df.sort_values("ratio").iloc[0]
    c2.metric("Busiest place", busiest["name"], f"{busiest['ratio']:.0%} full", delta_color="inverse")
    c3.metric("Quietest place", quietest["name"], f"{quietest['ratio']:.0%} full", delta_color="off")
c4.metric("Buildings closed", len(closed))

tab_map, tab_explore, tab_find, tab_whatif, tab_day = st.tabs(
    ["🗺️ Live Map", "🏢 Building Explorer", "🔎 Find a Place", "🔮 What-If Compare", "📈 Day Analytics"])

# ------------------------------------------------------------------ tab 1: map
with tab_map:
    if route:
        steps = " → ".join(NAMES[n] for n in route["path"] if n in NAMES)
        st.success(f"**Route:** {steps}  \n"
                   f"Distance **{route['metres']:.0f} m**, walking time about **{route['minutes']:.1f} min**")
    elif start == end:
        st.info("Choose different 'From' and 'To' places in the sidebar to see a route.")
    else:
        st.error("No route available - a closed building may be blocking the way.")

    if base != "Campus plan" and not aligned:
        st.warning("This is still the **sample location**. Open the sidebar → **📍 Align with real satellite**, "
                   "paste your main-gate coordinates, then fine-tune rotation / scale / shift so the "
                   "outlines sit on your real buildings.")
    m = mapview.build_map(snap, rooms, route, start, end, base, show_heat, show_paths,
                          crowd_colors, show_labels, calibration=cal, overlay_opacity=overlay_opacity)
    try:
        st_folium(m, height=640, use_container_width=True, returned_objects=[])
    except TypeError:
        st_folium(m, height=640, width=1100, returned_objects=[])
    st.caption("🟢 Low  🟠 Moderate  🔴 High  ⚪ Closed - click any building to see floor-wise crowd.")

# ------------------------------------------------------------------ tab 2: building explorer
with tab_explore:
    bid = st.selectbox("Choose a building", IDS, index=IDS.index("cse"), format_func=NAMES.get,
                       key="explore_building")
    b = eng.BUILDING_BY_ID[bid]
    row = snap.set_index("id").loc[bid]
    e1, e2, e3, e4 = st.columns(4)
    e1.metric("People now", f"{int(row['occupancy']):,}")
    e2.metric("Capacity", f"{int(row['capacity']):,}")
    e3.metric("Crowd", f"{row['ratio']:.0%}")
    e4.metric("Status", row["level"])
    st.caption(f"{TYPE_LABELS[b['type']]}" + (f"  |  Departments: {b['departments']}" if b["departments"] else ""))

    if not b["floors"]:
        st.info("This place is a single open area / facility, so it has no floor-wise rooms.")
    else:
        sub = rooms[rooms["building"] == bid]
        tabs = st.tabs([f["label"] for f in b["floors"]])
        for tb, f in zip(tabs, b["floors"]):
            with tb:
                fr = sub[sub["floor"] == f["floor"]]
                labs = int((fr["kind"] == "lab").sum())
                cls = int((fr["kind"] == "classroom").sum())
                st.write(f"**{len(fr)} rooms** - {cls} classrooms, {labs} labs | "
                         f"{int(fr['occupancy'].sum())} / {int(fr['capacity'].sum())} people "
                         f"({fr['occupancy'].sum() / max(fr['capacity'].sum(), 1):.0%})")
                view = pd.DataFrame({
                    "Room": fr["room"], "Type": fr["kind"].map(KIND_LABELS),
                    "People": fr["occupancy"], "Seats / systems": fr["capacity"], "Free": fr["free"],
                    "Occupancy": (fr["ratio"] * 100).clip(upper=100).round(0), "Status": fr["level"],
                })
                st.dataframe(view, hide_index=True, column_config={
                    "Occupancy": st.column_config.ProgressColumn(
                        "Occupancy", min_value=0, max_value=100, format="%d%%")})

# ------------------------------------------------------------------ tab 3: find a place
with tab_find:
    st.subheader("Find the best place, starting from 'From'")
    mode = st.radio("Search by", ["Rooms (labs, classrooms, washrooms...)", "Buildings"], horizontal=True)

    if mode.startswith("Rooms"):
        kinds = list(KIND_LABELS)
        k1, k2 = st.columns(2)
        kind = k1.selectbox("Room type", kinds, format_func=KIND_LABELS.get, index=kinds.index("lab"))
        min_free = k2.number_input("Minimum free seats / systems", min_value=1, max_value=200, value=5)
        sel = rooms[(rooms["kind"] == kind) & (~rooms["closed"]) & (rooms["free"] >= min_free)]
        walk = {}
        for bid2 in sel["building"].unique():
            if bid2 == start:
                walk[bid2] = 0.0
            else:
                r = route_for(start, bid2, ratios, scenario)
                walk[bid2] = round(r["minutes"], 1) if r else None
        sel = sel.assign(walk=sel["building"].map(walk)).dropna(subset=["walk"])
        if sel.empty:
            st.warning("Nothing matches right now - try a lower minimum or a different time.")
        else:
            sel = sel.sort_values(["walk", "ratio"]).head(15)
            st.dataframe(pd.DataFrame({
                "Building": sel["building_name"], "Floor": sel["floor_label"], "Room": sel["room"],
                "Free": sel["free"], "Crowd": (sel["ratio"] * 100).round(0).astype(int).astype(str) + "%",
                "Walk (min)": sel["walk"]}), hide_index=True)
    else:
        kinds = list(TYPE_LABELS)
        kind = st.selectbox("Building type", kinds, format_func=TYPE_LABELS.get, index=kinds.index("canteen"))
        sidx = snap.set_index("id")
        out = []
        for b in BUILDINGS:
            if b["type"] != kind or b["id"] in closed:
                continue
            if b["id"] == start:
                mins, metres = 0.0, 0
            else:
                r = route_for(start, b["id"], ratios, scenario)
                if not r:
                    continue
                mins, metres = round(r["minutes"], 1), int(r["metres"])
            out.append({"Place": b["name"], "Walk (min)": mins, "Distance (m)": metres,
                        "Crowd": f"{ratios[b['id']]:.0%}", "Level": sidx.loc[b["id"], "level"]})
        if out:
            st.dataframe(pd.DataFrame(out).sort_values("Walk (min)"), hide_index=True)
        else:
            st.warning("No reachable open place of this type.")

# ------------------------------------------------------------------ tab 4: what-if
with tab_whatif:
    st.subheader("Compare two scenarios at the selected time")
    col_a, col_b = st.columns(2)
    sa = col_a.selectbox("Scenario A", list(SCENARIOS), index=0)
    sb = col_b.selectbox("Scenario B", list(SCENARIOS), index=2)
    snap_a = eng.snapshot(hour, sa, closed, attendance)
    snap_b = eng.snapshot(hour, sb, closed, attendance)

    cmp = pd.DataFrame({"Place": snap_a["name"],
                        "Scenario A": (snap_a["ratio"] * 100).round(0),
                        "Scenario B": (snap_b["ratio"] * 100).round(0)})
    cmp["Change (pts)"] = cmp["Scenario B"] - cmp["Scenario A"]
    m1, m2, m3 = st.columns(3)
    m1.metric("People - A", f"{int(snap_a['occupancy'].sum()):,}")
    m2.metric("People - B", f"{int(snap_b['occupancy'].sum()):,}",
              f"{int(snap_b['occupancy'].sum() - snap_a['occupancy'].sum()):+,}", delta_color="off")
    m3.metric("High-crowd places A → B", f"{int((snap_a['ratio'] >= 0.8).sum())} → {int((snap_b['ratio'] >= 0.8).sum())}")
    st.bar_chart(cmp.set_index("Place")[["Scenario A", "Scenario B"]])
    st.dataframe(cmp, hide_index=True)

    st.markdown("**Route time under each scenario** (uses the From/To in the sidebar)")
    ra = route_for(start, end, dict(zip(snap_a["id"], snap_a["ratio"])), sa)
    rb = route_for(start, end, dict(zip(snap_b["id"], snap_b["ratio"])), sb)
    r1, r2 = st.columns(2)
    r1.metric(sa, f"{ra['minutes']:.1f} min" if ra else "No route")
    r2.metric(sb, f"{rb['minutes']:.1f} min" if rb else "No route")

# ------------------------------------------------------------------ tab 5: day analytics
with tab_day:
    st.subheader(f"How the campus fills up through the day - {scenario}")
    day = cached_day(scenario, closed, attendance)
    day = day.assign(group=day["type"].map(TYPE_LABELS))
    st.area_chart(day.pivot_table(index="hour", columns="group", values="occupancy", aggfunc="sum"))
    st.caption("People present by place type, every 30 minutes (x-axis = hour of day).")
    pick = st.selectbox("Zoom into one building", IDS, index=IDS.index("cse"), format_func=NAMES.get,
                        key="day_building")
    st.line_chart(day[day["id"] == pick].set_index("hour")["occupancy"])

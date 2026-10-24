"""mapview.py - draws the campus: plan view (like the aerial photo) or over real satellite tiles."""
import math
import random

import folium
from folium.plugins import AntPath, Fullscreen, HeatMap

import engine as eng
from campus_data import BUILDINGS, CENTER, M_PER_DEG_LAT, ROTATION_DEG, TYPE_LABELS

_GATE = next(b for b in BUILDINGS if b["id"] == "gate")

# Calibration: where the Main Gate really is, plus rotation / scale / nudge to line up with satellite
DEFAULT_CAL = {"lat": CENTER[0], "lon": CENTER[1], "rotation": float(ROTATION_DEG),
               "scale": 1.0, "east": 0.0, "north": 0.0}
_cal = dict(DEFAULT_CAL)


def set_calibration(cal):
    _cal.clear()
    _cal.update({**DEFAULT_CAL, **(cal or {})})


def ll(x, y):
    """Plan metres -> [lat, lon] using the current calibration (anchored at the Main Gate)."""
    c = _cal
    dx = (x - _GATE["x"]) * c["scale"]
    dy = (y - _GATE["y"]) * c["scale"]
    a = math.radians(c["rotation"])
    xr = dx * math.cos(a) - dy * math.sin(a) + c["east"]
    yr = dx * math.sin(a) + dy * math.cos(a) + c["north"]
    lat = c["lat"] + yr / M_PER_DEG_LAT
    lon = c["lon"] + xr / (M_PER_DEG_LAT * math.cos(math.radians(c["lat"])))
    return [lat, lon]


def rect(cx, cy, hx, hy):
    return [ll(cx - hx, cy - hy), ll(cx + hx, cy - hy), ll(cx + hx, cy + hy), ll(cx - hx, cy + hy)]


def _poly(group, cx, cy, hx, hy, color, opacity=0.95, tooltip=None):
    folium.Polygon(rect(cx, cy, hx, hy), color=color, weight=0, fill=True, fill_color=color,
                   fill_opacity=opacity, tooltip=tooltip).add_to(group)


def _in_building(x, y, margin=5):
    return any(abs(x - b["x"]) <= b["hx"] + margin and abs(y - b["y"]) <= b["hy"] + margin
               for b in BUILDINGS)


def _tree(group, x, y, r, color):
    folium.Circle(ll(x, y), radius=r * _cal["scale"], color="#1b4d20", weight=1, fill=True,
                  fill_color=color, fill_opacity=0.92).add_to(group)


def _label(x, y, text, size=11):
    return folium.Marker(ll(x, y), icon=folium.DivIcon(icon_size=(0, 0), html=(
        f"<div style='font-size:{size}px;font-weight:700;color:#fff;white-space:nowrap;"
        "text-shadow:0 0 3px #000,0 0 3px #000;transform:translate(-50%,-50%)'>"
        f"{text}</div>")))


def add_terrain(m):
    g = folium.FeatureGroup(name="Campus plan", show=True)
    _poly(g, 20, -76, 320, 64, "#a8532e")                       # red-soil farmland south of road
    _poly(g, 20, 141, 320, 129, "#79a35a")                      # campus grass
    _poly(g, -110, 55, 92, 38, "#d9a46c")                       # bus yard (orange soil)
    _poly(g, -75, 135, 50, 28, "#d9a46c")                       # soil around Labs / Mech
    _poly(g, 0, 68, 7, 45, "#e6dbc3")                           # central avenue
    _poly(g, 95, 111, 55, 8, "#86ad63", 0.95, "Garden gap between playground and Main block")
    _poly(g, -11, 140, 3.5, 25, "#e6dbc3", 1.0, "Walkway to canteen (between Mech block & Library)")
    folium.PolyLine([ll(27, 163), ll(22, 163), ll(12, 172)], color="#e6dbc3", weight=6,
                    tooltip="Canteen link from CSE block").add_to(g)
    _poly(g, 0, 0, 320, 12, "#4b4b4b", 1.0, "Main road")       # road
    folium.PolyLine([ll(-320, 0), ll(320, 0)], color="#ffffff", weight=2, dash_array="10 10").add_to(g)
    folium.PolyLine([ll(-250, 24), ll(-250, 230), ll(270, 230), ll(270, 24)],
                    color="#f0f0f0", weight=2, dash_array="2 6", tooltip="Campus boundary").add_to(g)
    for sx in (-9, 9):                                          # gate pillars
        _poly(g, sx, 18, 1.4, 1.4, "#ffffff", 1.0)
    g.add_to(m)

    t = folium.FeatureGroup(name="Trees", show=True)
    for y in range(28, 112, 8):
        for sx in (-11, 11):
            _tree(t, sx, y, 3.4, "#2f7d32")
    rng = random.Random(42)
    zones = [(-285, 285, 222, 268, 55), (-290, -235, 20, 215, 28), (255, 295, 20, 215, 22),
             (-250, -205, 14, 24, 5), (14, 255, 14, 24, 16), (14, 36, 30, 108, 12),
             (-38, -14, 25, 100, 10),
             (40, 148, 104, 118, 24, 1), (-64, -22, 158, 205, 10), (30, 60, 178, 200, 6)]
    for zn in zones:
        xmin, xmax, ymin, ymax, n = zn[:5]
        margin = zn[5] if len(zn) > 5 else 5
        placed, tries = 0, 0
        while placed < n and tries < n * 30:
            tries += 1
            x, y = rng.uniform(xmin, xmax), rng.uniform(ymin, ymax)
            if (_in_building(x, y, margin) or (abs(x) < 15 and 18 < y < 116)
                    or (-17 < x < -5 and 112 < y < 168)):
                continue
            _tree(t, x, y, rng.uniform(2.4, 4.4), rng.choice(["#2f7d32", "#3d8b3d", "#256d2a"]))
            placed += 1
    t.add_to(m)


def add_basemap(m, base):
    if base == "Satellite":
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri World Imagery", name="Satellite", max_zoom=21, max_native_zoom=19).add_to(m)
    else:
        folium.TileLayer("OpenStreetMap", name="Street map", max_zoom=21, max_native_zoom=19).add_to(m)


def build_map(snap, rooms, route, start, end, base="Campus plan", show_heat=False,
              show_paths=True, crowd_colors=True, show_labels=True, calibration=None,
              overlay_opacity=0.3):
    set_calibration(calibration)
    plan = base == "Campus plan"

    m = folium.Map(location=ll(30, 105), zoom_start=18, min_zoom=15 if plan else 8, max_zoom=21,
                   tiles=None, control_scale=True)
    Fullscreen().add_to(m)
    if plan:
        add_terrain(m)
    else:
        add_basemap(m, base)

    if show_paths:
        g = folium.FeatureGroup(name="Walkways", show=True)
        for a, b in eng.PATHS_LIST:
            A, B = eng.NODE_BY_ID[a], eng.NODE_BY_ID[b]
            folium.PolyLine([ll(A["x"], A["y"]), ll(B["x"], B["y"])], color="#ffffff",
                            weight=3, opacity=0.8, dash_array="6 6").add_to(g)
        g.add_to(m)

    if show_heat:
        pts = []
        for i, r in zip(snap["id"], snap["ratio"]):
            if r > 0:
                nb = eng.BUILDING_BY_ID[i]
                pts.append(ll(nb["x"], nb["y"]) + [float(r)])
        if pts:
            HeatMap(pts, radius=40, blur=30, min_opacity=0.25, name="Crowd heatmap").add_to(m)

    floors_df = {row.id: eng.floor_summary(rooms, row.id)
                 for row in snap.itertuples() if eng.BUILDING_BY_ID[row.id]["floors"]}
    room_idx = {(r.building, r.room): r for r in rooms.itertuples()}
    zone_style = {"pitch": "#4f9a3a", "court": "#2f6fb8", "hall": "#ffffff"}

    bl = folium.FeatureGroup(name="Buildings", show=True)
    for row in snap.itertuples():
        b = eng.BUILDING_BY_ID[row.id]
        if b["court"] and plan:                                 # paved square + fountain (CSE block)
            _poly(bl, b["x"], b["y"], b["court"][0], b["court"][1], "#d6cfbd", 1.0, "Central square")
            folium.Circle(ll(b["x"], b["y"]), radius=7 * _cal["scale"], color="#e9e4d4", weight=1,
                          fill=True, fill_color="#e9e4d4", fill_opacity=1).add_to(bl)
            folium.Circle(ll(b["x"], b["y"]), radius=3.5 * _cal["scale"], color="#2f8fd8", weight=1,
                          fill=True, fill_color="#4aa3df", fill_opacity=1, tooltip="Fountain").add_to(bl)

        html = (f"<b>{row.name}</b><br>{TYPE_LABELS[row.type]}"
                + (f"<br><i>{row.departments}</i>" if row.departments else "")
                + f"<br>People: {row.occupancy}/{row.capacity} ({row.ratio:.0%}) "
                  f"<b style='color:{row.color}'>{row.level}</b>")
        if row.id in floors_df:
            html += "<hr style='margin:4px 0'>" + "<br>".join(
                f"{f.floor_label}: {f.ratio:.0%} ({f.occupancy}/{f.capacity})"
                for f in floors_df[row.id].itertuples())

        outer = rect(b["x"], b["y"], b["hx"], b["hy"])
        rings = [outer] + ([rect(b["x"], b["y"], b["court"][0], b["court"][1])] if b["court"] else [])
        if crowd_colors:
            if plan:
                fill, op, edge, wt = row.color, 0.7, "#ffffff", 2
            else:                                               # satellite: see the real roof through it
                fill, op, edge, wt = row.color, overlay_opacity, row.color, 3
        else:
            if plan:
                fill = "#9a9a9a" if row.closed else ("#d9a46c" if b["type"] in ("sports", "bus") else "#f4f4ef")
                op, edge, wt = 0.95, "#7a7a7a", 2
            else:
                fill, op, edge, wt = "#ffffff", 0.05, "#ffffff", 2
        folium.Polygon(rings, color=edge, weight=wt, fill=True, fill_color=fill, fill_opacity=op,
                       tooltip=f"{row.name} - {row.level}",
                       popup=folium.Popup(html, max_width=280)).add_to(bl)

        for z in b["zones"]:                                    # pitch / courts / halls inside a building
            rr = room_idx.get((b["id"], z["room"]))
            zx, zy = b["x"] + z["dx"], b["y"] + z["dy"]
            if crowd_colors and rr is not None:
                zfill = rr.color
                zop = 0.85 if plan else min(overlay_opacity + 0.2, 0.9)
                zedge = "#ffffff" if plan else rr.color
            else:
                zfill = "#9a9a9a" if (rr is not None and rr.closed) else zone_style[z["style"]]
                zop = 0.95 if plan else 0.1
                zedge = "#ffffff"
            zpop = (f"<b>{z['name']}</b><br>People: {rr.occupancy}/{rr.capacity} ({rr.ratio:.0%}) "
                    f"<b style='color:{rr.color}'>{rr.level}</b>") if rr is not None else z["name"]
            folium.Polygon(rect(zx, zy, z["hx"], z["hy"]), color=zedge, weight=2, fill=True,
                           fill_color=zfill, fill_opacity=zop, tooltip=z["name"],
                           popup=folium.Popup(zpop, max_width=240)).add_to(bl)
            if z["style"] == "pitch" and plan:
                folium.PolyLine([ll(zx, zy - z["hy"]), ll(zx, zy + z["hy"])], color="#ffffff", weight=1).add_to(bl)
                folium.Circle(ll(zx, zy), radius=4 * _cal["scale"], color="#ffffff", weight=1,
                              fill=False).add_to(bl)
            if show_labels and z.get("label", True):
                _label(zx, zy, z["name"], 9).add_to(bl)

        if b["type"] == "bus" and plan:                         # yellow buses like the photo
            n = 12
            step = 2 * (b["hx"] - 4) / (n - 1)
            for i in range(n):
                _poly(bl, b["x"] - (b["hx"] - 4) + i * step, b["y"], 2.2, 5.5, "#f2c200", 1.0)
        if b["type"] == "library" and plan:                     # dome
            folium.Circle(ll(b["x"], b["y"]), radius=6 * _cal["scale"], color="#bdbdbd", weight=1,
                          fill=True, fill_color="#ffffff", fill_opacity=1).add_to(bl)
        if show_labels:
            _label(b["x"], b["y"], row.name + (" (CLOSED)" if row.closed else "")).add_to(bl)
    bl.add_to(m)

    if route:
        rg = folium.FeatureGroup(name="Route", show=True)
        coords = [ll(eng.NODE_BY_ID[n]["x"], eng.NODE_BY_ID[n]["y"]) for n in route["path"]]
        AntPath(coords, color="#1e90ff", weight=6, delay=800).add_to(rg)
        s, e = eng.BUILDING_BY_ID[start], eng.BUILDING_BY_ID[end]
        folium.Marker(ll(s["x"], s["y"]), tooltip="Start", icon=folium.Icon(color="green")).add_to(rg)
        folium.Marker(ll(e["x"], e["y"]), tooltip="Destination", icon=folium.Icon(color="red")).add_to(rg)
        rg.add_to(m)

    folium.LayerControl(collapsed=True).add_to(m)
    return m
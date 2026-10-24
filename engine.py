"""engine.py - digital-twin logic: room-level crowd simulation + routing (no UI code)."""
import heapq
import math
import zlib

import numpy as np
import pandas as pd

from campus_data import (BUILDINGS, JUNCTIONS, PATHS, PROFILE_POINTS, SCENARIOS, TYPE_LABELS)

BUILDING_BY_ID = {b["id"]: b for b in BUILDINGS}
NODE_BY_ID = {**BUILDING_BY_ID, **{j["id"]: j for j in JUNCTIONS}}
BASE_SPEED_MPS = 1.3
PATHS_LIST = PATHS

_PROFILE = {k: (np.array([p[0] for p in v], float), np.array([p[1] for p in v], float))
            for k, v in PROFILE_POINTS.items()}

ROOM_LIST = [
    {"building": b["id"], "building_name": b["name"], "floor": f["floor"], "floor_label": f["label"],
     "room": r["name"], "kind": r["kind"], "capacity": r["capacity"]}
    for b in BUILDINGS for f in b["floors"] for r in f["rooms"]
]

ROOM_COLUMNS = ["building", "building_name", "floor", "floor_label", "room", "kind", "capacity",
                "occupancy", "free", "ratio", "level", "color", "closed"]


def haversine(lat1, lon1, lat2, lon2):
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 2 * r * math.asin(math.sqrt(a))


def _build_graph():
    adj = {nid: [] for nid in NODE_BY_ID}
    for a, b in PATHS:
        A, B = NODE_BY_ID[a], NODE_BY_ID[b]
        d = math.hypot(A["x"] - B["x"], A["y"] - B["y"])
        adj[a].append((b, d))
        adj[b].append((a, d))
    return adj


GRAPH = _build_graph()


# ---------------- crowd simulation ----------------
def _ratio(kind, key, hour, scenario, attendance):
    xs, ys = _PROFILE[kind]
    base = float(np.interp(hour, xs, ys))
    mult = SCENARIOS[scenario]["multipliers"].get(kind, 1.0)
    seed = zlib.crc32(f"{key}-{int(hour * 4)}".encode()) % 1000
    noise = 1 + 0.08 * (seed / 500 - 1)          # deterministic +/-8 %
    return float(min(base * mult * noise * attendance / 100.0, 1.4))


def crowd_level(ratio, is_closed=False):
    if is_closed:
        return "Closed", "#7f8c8d"
    if ratio < 0.5:
        return "Low", "#2ecc71"
    if ratio < 0.8:
        return "Moderate", "#f39c12"
    return "High", "#e74c3c"


def room_snapshot(hour, scenario, closed=(), attendance=100):
    rows = []
    for r in ROOM_LIST:
        is_closed = r["building"] in closed
        ratio = 0.0 if is_closed else min(
            _ratio(r["kind"], f"{r['building']}-{r['floor']}-{r['room']}", hour, scenario, attendance), 1.0)
        occ = int(round(ratio * r["capacity"]))
        level, color = crowd_level(ratio, is_closed)
        rows.append({**r, "occupancy": occ, "free": max(r["capacity"] - occ, 0), "ratio": ratio,
                     "level": level, "color": color, "closed": is_closed})
    return pd.DataFrame(rows, columns=ROOM_COLUMNS)


def snapshot(hour, scenario, closed=(), attendance=100, rooms=None):
    if rooms is None:
        rooms = room_snapshot(hour, scenario, closed, attendance)
    occ_by_b = rooms.groupby("building")["occupancy"].sum().to_dict()
    rows = []
    for b in BUILDINGS:
        is_closed = b["id"] in closed
        if b["floors"]:
            occ = int(occ_by_b.get(b["id"], 0))
            ratio = occ / b["capacity"] if b["capacity"] else 0.0
        else:
            ratio = 0.0 if is_closed else _ratio(b["type"], b["id"], hour, scenario, attendance)
            occ = int(round(ratio * b["capacity"]))
        level, color = crowd_level(ratio, is_closed)
        rows.append({"id": b["id"], "name": b["name"], "type": b["type"], "capacity": b["capacity"],
                     "occupancy": occ, "ratio": ratio, "level": level, "color": color,
                     "closed": is_closed, "floors": len(b["floors"]), "departments": b["departments"]})
    return pd.DataFrame(rows)


def floor_summary(rooms, building_id):
    sub = rooms[rooms["building"] == building_id]
    g = (sub.groupby(["floor", "floor_label"])
         .agg(capacity=("capacity", "sum"), occupancy=("occupancy", "sum")).reset_index())
    g["ratio"] = g["occupancy"] / g["capacity"]
    return g


# ---------------- routing ----------------
def shortest_path(start, end, ratios, closed=(), crowd_aware=True, scenario="Normal day"):
    """Dijkstra over buildings + junctions. Closed buildings are skipped."""
    if start == end or start in closed or end in closed:
        return None
    dist = {start: 0.0}
    prev = {}
    heap = [(0.0, start)]
    done = set()
    while heap:
        cost, u = heapq.heappop(heap)
        if u in done:
            continue
        done.add(u)
        if u == end:
            break
        for v, d in GRAPH[u]:
            if v in closed or v in done:
                continue
            penalty = 1 + 1.5 * max(0.0, ratios.get(v, 0.0) - 0.6) if crowd_aware else 1.0
            nc = cost + d * penalty
            if nc < dist.get(v, float("inf")):
                dist[v] = nc
                prev[v] = u
                heapq.heappush(heap, (nc, v))
    if end not in prev:
        return None
    path = [end]
    while path[-1] != start:
        path.append(prev[path[-1]])
    path.reverse()
    metres = sum(next(d for n, d in GRAPH[a] if n == b) for a, b in zip(path, path[1:]))
    seconds = metres / (BASE_SPEED_MPS * SCENARIOS[scenario]["speed"])
    seconds += sum(25 for n in path[1:-1] if ratios.get(n, 0.0) > 0.9)
    return {"path": path, "metres": metres, "minutes": seconds / 60.0}


def day_profile(scenario, closed=(), attendance=100):
    """Long table: hour, building id/name/type, occupants - every 30 minutes."""
    frames = []
    for h in np.arange(0, 24, 0.5):
        s = snapshot(float(h), scenario, closed, attendance)[["id", "name", "type", "occupancy"]].copy()
        s.insert(0, "hour", float(h))
        frames.append(s)
    return pd.concat(frames, ignore_index=True)

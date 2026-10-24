"""
campus_data.py - everything specific to YOUR campus lives here.

Layout coordinates (x = metres east, y = metres north) were estimated from the aerial photo:
  - the main road runs east-west at y = 0
  - the entrance gate is at the road, the tree-lined avenue runs north from it
  - CSE (main) block is the large courtyard building on the right
To overlay on real satellite imagery: set CENTER to the gate/road point of your campus
(Google Maps -> right-click -> copy lat, lon) and tune ROTATION_DEG until it lines up.
"""
import math

CENTER = (16.4419, 80.6226)   # sample only - the app's sidebar 'Align with real satellite' overrides this
ROTATION_DEG = 0.0            # rotate the whole layout (degrees, counter-clockwise)
M_PER_DEG_LAT = 111_320.0


def to_latlon(x, y):
    a = math.radians(ROTATION_DEG)
    xr = x * math.cos(a) - y * math.sin(a)
    yr = x * math.sin(a) + y * math.cos(a)
    lat = CENTER[0] + yr / M_PER_DEG_LAT
    lon = CENTER[1] + xr / (M_PER_DEG_LAT * math.cos(math.radians(CENTER[0])))
    return lat, lon


# ----------------------------------------------------------------- room helpers
def R(name, kind, cap):
    return {"name": name, "kind": kind, "capacity": cap}


def classrooms(floor_no, count, cap=72, start=1):
    return [R(f"Classroom {floor_no}{i:02d}", "classroom", cap) for i in range(start, start + count)]


def washrooms(tag="", boys=True, girls=True):
    out = []
    if boys:
        out.append(R(f"Boys Washroom{tag}", "washroom", 14))
    if girls:
        out.append(R(f"Girls Washroom{tag}", "washroom", 14))
    return out


def purifier():
    return R("Water Purifier", "amenity", 8)


def floor(n, rooms, label=None):
    label = label or ("Floor 1 (Ground)" if n == 1 else f"Floor {n}")
    return {"floor": n, "label": label, "rooms": rooms}


def B(bid, name, btype, x, y, hx, hy, floors=None, capacity=0, departments="", court=None, zones=None):
    floors = floors or []
    if floors:
        capacity = sum(r["capacity"] for f in floors for r in f["rooms"])
    lat, lon = to_latlon(x, y)
    return {"id": bid, "name": name, "type": btype, "x": x, "y": y, "hx": hx, "hy": hy,
            "lat": lat, "lon": lon, "floors": floors, "capacity": capacity,
            "departments": departments, "court": court,
            "zones": zones or []}


def J(jid, x, y):
    lat, lon = to_latlon(x, y)
    return {"id": jid, "name": jid, "x": x, "y": y, "lat": lat, "lon": lon}


# ----------------------------------------------------------------- CSE (MAIN) BLOCK - 4 floors
CSE_FLOORS = [
    floor(1, [R("Office Room", "office", 12), R("Administrative Room", "office", 15),
              R("Examination Room", "exam", 150),
              R("Seminar Hall 1", "seminar", 150), R("Seminar Hall 2", "seminar", 150)]
          + classrooms(1, 6, 72)
          + [R("Boys Washroom", "washroom", 14), R("Canteen Link Corridor", "corridor", 40), purifier()]),
    floor(2, [R(f"CSE Lab {i}", "lab", 80) for i in range(1, 7)]          # 6 labs x 80 systems
          + [R("Seminar Hall 3", "seminar", 150), R("CSE Department Staff Room", "staff", 60),
             R("Girls Washroom (East)", "washroom", 14), R("Girls Washroom (West)", "washroom", 14),
             purifier()]),
    floor(3, classrooms(3, 23, 72)                                         # 23 rooms + 1 staff room = 24
          + [R("Staff Room", "staff", 40)] + washrooms() + [purifier()]),
    floor(4, [R("ITWS Lab", "lab", 80), R("English Lab", "lab", 60), R("Graphics Lab", "lab", 60),
              R("Physics Lab", "lab", 40), R("Chemistry Lab", "lab", 40)] + washrooms() + [purifier()]),
]

ECE_FLOORS = [
    floor(1, classrooms(1, 6, 72) + [R("ECE Staff Room", "staff", 30)] + washrooms() + [purifier()]),
    floor(2, [R("Digital Electronics Lab", "lab", 60), R("Analog Circuits Lab", "lab", 60),
              R("Communication Systems Lab", "lab", 60), R("VLSI Design Lab", "lab", 60),
              R("Seminar Hall", "seminar", 100)] + classrooms(2, 3, 72) + washrooms() + [purifier()]),
    floor(3, [R("Microprocessors Lab", "lab", 60), R("Signal Processing Lab", "lab", 60),
              R("Embedded Systems Lab", "lab", 60)] + classrooms(3, 4, 72) + washrooms() + [purifier()]),
]

TECH_FLOORS = [   # no labs
    floor(1, classrooms(1, 8, 72) + [R("Tech Staff Room", "staff", 30)] + washrooms() + [purifier()]),
    floor(2, classrooms(2, 8, 72) + washrooms() + [purifier()]),
    floor(3, classrooms(3, 8, 72) + washrooms() + [purifier()]),
]

MECH_FLOORS = [   # Mechanical + Civil students
    floor(1, classrooms(1, 4, 60) + [R("Mech Block Auditorium", "auditorium", 250),
                                     R("Mechanical & Civil Staff Room", "staff", 25)]
          + washrooms() + [purifier()]),
    floor(2, classrooms(2, 5, 60) + washrooms() + [purifier()]),
    floor(3, classrooms(3, 5, 60) + washrooms() + [purifier()]),
]

LABS_FLOORS = [
    floor(1, [R("BEEE Lab", "lab", 60), R("Engineering Workshop Lab", "lab", 60)]
          + washrooms() + [purifier()]),
]

GROUND_FLOORS = [   # playground complex: football court, courts, auditorium, open field
    floor(1, [R("Football Court", "court", 200), R("Volleyball Court", "court", 40),
              R("Basketball Court", "court", 40), R("Playground Auditorium", "auditorium", 600),
              R("Open Field (cricket / athletics)", "sports", 300)], label="Facilities"),
]

GROUND_ZONES = [   # offsets (metres) from the playground centre; must stay inside its footprint
    {"name": "Football Court", "room": "Football Court", "dx": -25, "dy": 0, "hx": 28, "hy": 21, "style": "pitch"},
    {"name": "Volleyball Court", "room": "Volleyball Court", "dx": 14, "dy": 16, "hx": 8, "hy": 5, "style": "court"},
    {"name": "Basketball Court", "room": "Basketball Court", "dx": 14, "dy": 2, "hx": 8, "hy": 5, "style": "court"},
    {"name": "Playground Auditorium", "room": "Playground Auditorium", "dx": 38, "dy": -10, "hx": 14, "hy": 10, "style": "hall"},
]

MECH_ZONES = [
    {"name": "Auditorium (inside Mech block)", "room": "Mech Block Auditorium", "dx": 0, "dy": 0,
     "hx": 8, "hy": 6, "style": "hall", "label": False},
]

NEW_BLOCK_FLOORS = [   # placeholder - replace with real details of the newly constructed block
    floor(1, classrooms(1, 8, 72) + [R("Staff Room", "staff", 25)] + washrooms() + [purifier()]),
]

# ----------------------------------------------------------------- BUILDINGS
# Plan coordinates in metres, estimated from your labelled photo:
#   x = east of the avenue, y = north of the main road.  Main gate / avenue is at x = 0.
BUILDINGS = [
    B("gate",     "Main Gate",                      "gate",       0,    18,  14, 5,  capacity=400),
    B("bus1",     "Bus Stand 1",                    "bus",        -125, 52,  55, 8,  capacity=150),
    B("bus2",     "Bus Stand 2",                    "bus",        -125, 34,  55, 8,  capacity=150),
    B("hostel",   "Boys Hostel",                    "hostel",     -146, 104, 32, 18, capacity=800),
    B("tech",     "Tech Block",                     "academic",   -55,  92,  14, 29, TECH_FLOORS,
      departments="Data Science, AI, AIML"),
    B("labs",     "Labs Block (BEEE & Workshop)",   "academic",   -88,  125, 14, 10, LABS_FLOORS,
      departments="BEEE Lab, Engineering Workshop Lab"),
    B("mech",     "Mech Block",                     "academic",   -38,  138, 20, 16, MECH_FLOORS,
      departments="Mechanical, Civil (has its own small auditorium inside)", zones=MECH_ZONES),
    B("library",  "Library",                        "library",    10,   137, 15, 11, capacity=400),
    B("canteen",  "Canteen (behind Library)",       "canteen",    4,    185, 20, 13, capacity=400),
    B("cse",      "Main / CSE Block",               "academic",   81,   150, 54, 30, CSE_FLOORS,
      departments="Computer Science (CSE) + Administration & Examination cell", court=(22, 12)),
    B("ground",   "Playground Complex",             "sports",     95,   74,  55, 28, GROUND_FLOORS,
      departments="Football court, volleyball & basketball courts, auditorium, open field",
      zones=GROUND_ZONES),
    B("ece",      "ECE Block",                      "academic",   200,  120, 38, 20, ECE_FLOORS,
      departments="ECE, IT, CS"),
    B("newblock", "New Block (newly constructed)",  "academic",   205,  185, 30, 18, NEW_BLOCK_FLOORS,
      departments="Newly constructed - details pending"),
]

JUNCTIONS = [J("j1", 0, 60), J("j2", 0, 112), J("jL", -25, 108), J("jR", 25, 108), J("jBus", -35, 45),
             J("jW1", -11, 116), J("jW2", -11, 162),   # walkway to canteen between Mech block & Library
             J("jCW", 22, 163)]                         # canteen link on the CSE side (does NOT pass the Library)

PATHS = [
    ("gate", "j1"), ("j1", "j2"), ("j1", "jBus"), ("jBus", "bus1"), ("jBus", "bus2"), ("jBus", "tech"),
    ("j1", "ground"), ("j2", "jL"), ("jL", "tech"), ("jL", "mech"), ("j2", "jR"), ("j2", "library"),
    ("jR", "library"), ("jR", "cse"),
    # canteen access #1: lane between Mech block and Library, passing behind the Library
    ("j2", "jW1"), ("jW1", "jW2"), ("jW2", "canteen"),
    # canteen access #2: direct link from the CSE block (Floor 1 "Canteen Link Corridor")
    ("cse", "jCW"), ("jCW", "canteen"),
    ("ground", "cse"), ("ground", "ece"), ("cse", "ece"), ("ece", "newblock"), ("canteen", "newblock"),
    ("mech", "labs"), ("labs", "tech"), ("labs", "hostel"), ("hostel", "bus1"),
]

TYPE_LABELS = {
    "academic": "Academic block", "library": "Library", "canteen": "Canteen", "hostel": "Hostel",
    "sports": "Playground", "auditorium": "Auditorium", "gate": "Gate", "bus": "Bus stand",
}

KIND_LABELS = {
    "classroom": "Classroom", "lab": "Lab", "court": "Sports court", "auditorium": "Auditorium",
    "sports": "Open field", "seminar": "Seminar hall", "staff": "Staff room",
    "office": "Office", "exam": "Examination room", "washroom": "Washroom",
    "amenity": "Water purifier", "corridor": "Corridor",
}

# Typical share of capacity occupied through the day: (hour, ratio) keypoints per kind
PROFILE_POINTS = {
    "classroom": [(0, 0), (8.5, 0.05), (9.25, 0.75), (10.75, 0.8), (11, 0.55), (11.25, 0.8),
                  (12.75, 0.8), (13, 0.2), (14, 0.2), (14.25, 0.8), (16.25, 0.75), (16.5, 0.2),
                  (17, 0.03), (24, 0)],
    "lab":       [(0, 0), (9, 0.05), (9.5, 0.75), (12.5, 0.8), (13, 0.1), (14, 0.1), (14.25, 0.75),
                  (16.5, 0.7), (17, 0.05), (24, 0)],
    "seminar":   [(0, 0), (9, 0.05), (10, 0.3), (12, 0.35), (14, 0.3), (16, 0.35), (17, 0.05), (24, 0)],
    "staff":     [(0, 0), (8.5, 0.05), (9.25, 0.7), (12.5, 0.6), (13, 0.35), (14, 0.4), (14.5, 0.65),
                  (16.5, 0.6), (17.25, 0.1), (24, 0)],
    "office":    [(0, 0), (9, 0.1), (10, 0.8), (13, 0.5), (14, 0.7), (16, 0.8), (17, 0.1), (24, 0)],
    "exam":      [(0, 0), (9, 0.03), (12.5, 0.05), (14, 0.03), (24, 0)],
    "washroom":  [(0, 0), (9, 0.1), (10.7, 0.15), (11, 0.6), (11.3, 0.2), (12.8, 0.3), (13, 0.7),
                  (14, 0.2), (15.8, 0.5), (16.1, 0.2), (17, 0.1), (24, 0)],
    "amenity":   [(0, 0), (9, 0.1), (10.7, 0.15), (11, 0.6), (11.3, 0.2), (12.8, 0.3), (13, 0.7),
                  (14, 0.2), (15.8, 0.5), (16.1, 0.2), (17, 0.1), (24, 0)],
    "corridor":  [(0, 0), (8.5, 0.1), (9, 0.5), (11, 0.55), (12.8, 0.9), (13.5, 0.4), (14, 0.5),
                  (16.5, 0.6), (17, 0.2), (24, 0)],
    "library":   [(0, 0.02), (8, 0.1), (10, 0.55), (13, 0.5), (16, 0.7), (19, 0.8), (21, 0.6), (23, 0.1), (24, 0.02)],
    "canteen":   [(0, 0), (7, 0.1), (8.5, 0.6), (10.5, 0.25), (12.5, 0.95), (14, 0.35), (16.5, 0.55),
                  (19.5, 0.7), (22, 0.1), (24, 0)],
    "hostel":    [(0, 0.95), (6, 0.9), (8, 0.6), (10, 0.15), (15, 0.15), (18, 0.45), (21, 0.85), (24, 0.95)],
    "sports":    [(0, 0), (5, 0.05), (6.5, 0.4), (9, 0.05), (15, 0.1), (17, 0.8), (19, 0.6), (21, 0.1), (24, 0)],
    "auditorium": [(0, 0), (9, 0.05), (11, 0.2), (15, 0.25), (18, 0.1), (24, 0)],
    "gate":      [(0, 0.02), (7.5, 0.3), (8.5, 0.8), (10, 0.3), (13, 0.5), (17, 0.85), (19, 0.3), (24, 0.02)],
    "court":     [(0, 0), (5, 0.05), (6.5, 0.5), (9, 0.05), (15, 0.1), (16.5, 0.6), (17.5, 0.9),
                  (19, 0.7), (21, 0.1), (24, 0)],
    "bus":       [(0, 0), (7, 0.2), (8, 0.85), (9, 0.5), (9.5, 0.1), (16.2, 0.1), (16.8, 0.8),
                  (17.5, 0.9), (18, 0.2), (18.5, 0.05), (24, 0)],
}

# What-if scenarios: multipliers per room kind / building type + walking-speed factor
SCENARIOS = {
    "Normal day": {"description": "A typical teaching day.", "multipliers": {}, "speed": 1.0},
    "Exam week": {
        "description": "Examination rooms and library fill up; classes and labs thin out.",
        "multipliers": {"exam": 14.0, "library": 1.6, "classroom": 0.6, "lab": 0.5, "sports": 0.5, "court": 0.5, "canteen": 0.9},
        "speed": 1.0},
    "Fest / Cultural event": {
        "description": "Auditorium and playground become hotspots; classes are thin.",
        "multipliers": {"auditorium": 6.0, "sports": 5.0, "court": 3.0, "canteen": 1.5, "classroom": 0.4, "lab": 0.4,
                        "library": 0.6, "gate": 1.4, "seminar": 1.5},
        "speed": 0.9},
    "Heavy rain": {
        "description": "People stay indoors, outdoor areas empty, walking is slower.",
        "multipliers": {"sports": 0.1, "court": 0.1, "canteen": 1.25, "library": 1.3, "corridor": 1.3, "bus": 1.2},
        "speed": 0.8},
    "Placement drive": {
        "description": "Offices and seminar halls are busy with recruiters and candidates.",
        "multipliers": {"office": 2.5, "seminar": 3.0, "auditorium": 4.0, "gate": 1.3, "classroom": 0.8},
        "speed": 1.0},
}
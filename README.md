# 🏫 CampusTwin – Intelligent Digital Campus

An interactive **Digital Twin of a College Campus** built using Python, Streamlit, and Folium. CampusTwin simulates campus occupancy, visualizes crowd levels, helps users find locations, and calculates routes while considering crowd conditions.

## 🌐 Live Demo

🚀 **Try the application here:** [CampusTwin Live Demo](https://collegetwin-lhx7xwuvmydaxbmab5as6q.streamlit.app/)

*Replace `(https://collegetwin-lhx7xwuvmydaxbmab5as6q.streamlit.app/)
` with your deployed application link.*

## 📌 Project Overview

CampusTwin is a smart campus simulation system that provides an interactive representation of a college campus. It allows users to explore campus buildings, monitor simulated occupancy levels, analyze daily crowd patterns, and find efficient walking routes.

The application supports different campus scenarios, adjustable student attendance, building closures, and multiple map views to help users understand and manage campus activities.

## ✨ Features

- 🗺️ **Interactive Campus Map** – Explore campus buildings, paths, and locations.
- 👥 **Crowd Simulation** – Estimate occupancy based on time, attendance, and campus scenarios.
- 🏢 **Building Explorer** – View building details, floors, rooms, and capacity information.
- 🔎 **Find a Place** – Select campus locations and explore navigation options.
- 🧭 **Smart Route Planning** – Find routes between buildings using a shortest-path algorithm.
- 🚶 **Crowd-Aware Navigation** – Prefer less crowded routes when the option is enabled.
- 🔮 **What-If Analysis** – Simulate building closures and changes in student attendance.
- 📈 **Day Analytics** – Explore campus occupancy patterns throughout the day.
- 🔥 **Crowd Heatmap** – Visualize crowd distribution across campus locations.
- 🛰️ **Multiple Map Views** – Switch between the campus plan, satellite imagery, and street maps.
- ⚙️ **Map Calibration** – Adjust coordinates, rotation, scale, and position to align the campus plan with real-world imagery.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| Streamlit | Interactive web application interface |
| Folium | Interactive maps and geographic visualization |
| Streamlit-Folium | Integrating maps into Streamlit |
| Pandas | Data processing and analysis |
| NumPy | Numerical computations |
| Heap-based Dijkstra algorithm | Shortest-path and crowd-aware routing |

## 📂 Project Structure

```text
CampusTwin/
├── app.py              # Main Streamlit application
├── engine.py           # Simulation and routing logic
├── mapview.py          # Campus map visualization
├── campus_data.py      # Campus buildings, rooms, and scenarios
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation
```

## ⚙️ Installation and Setup

### Prerequisites

- Python 3.10 or later recommended
- pip package manager
- Git

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

### 2. Navigate to the project directory

```bash
cd CampusTwin
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
streamlit run app.py
```

### 5. Open the application

Streamlit will provide a local URL, usually:

```text
http://localhost:8501
```

Open this URL in your browser to explore CampusTwin.

## 🚀 How to Use

1. Launch the application.
2. Select a campus scenario from the sidebar.
3. Adjust the time of day and student attendance percentage.
4. Explore occupancy metrics and building crowd levels.
5. Select starting and destination buildings to calculate a route.
6. Enable crowd-aware navigation to account for congestion.
7. Use the What-If Compare tab to experiment with building closures and attendance changes.
8. Explore Day Analytics to understand simulated occupancy patterns.
9. Switch map views and adjust calibration settings if required.

## 🧠 How It Works

CampusTwin combines campus data, occupancy simulation, and graph-based route planning.

- **Occupancy simulation:** Estimates room and building occupancy using time-based profiles, scenario multipliers, and attendance settings.
- **Crowd classification:** Categorizes occupancy as Low, Moderate, or High.
- **Route calculation:** Uses Dijkstra's algorithm to find a path through the campus network.
- **Crowd-aware routing:** Applies additional route costs to discourage paths through crowded locations.
- **What-if simulation:** Recalculates campus conditions when attendance or building availability changes.
- **Map visualization:** Displays buildings, paths, labels, and crowd-related information using Folium.

**Note:** Occupancy figures are simulated estimates based on configured campus data and profiles. They are not live student-tracking data.

## 🎯 Applications

- Smart campus planning
- Campus navigation and wayfinding
- Crowd management simulation
- Building occupancy analysis
- Campus infrastructure planning
- Educational demonstrations of digital twins and graph algorithms

## 🔮 Future Enhancements

- Integration with real-time attendance and sensor data
- AI-based crowd forecasting
- Mobile-friendly navigation
- Emergency evacuation route planning
- Real campus GIS data integration
- Historical occupancy reports and analytics

## 👨‍💻 Developed By

**Developer:** VEERA PURNIMA VENKATA

**Project:** CampusTwin – Intelligent Digital Campus

**GitHub:** [YOUR_GITHUB_PROFILE](https://github.com/25A31A05HJ)


## 📄 License

This project is available for educational and research purposes. Add a `LICENSE` file to the repository if you intend to distribute it under a specific open-source license.

---

⭐ If you find this project useful, consider giving the repository a star on GitHub!

**CampusTwin – Making Campus Navigation and Planning Smarter.**

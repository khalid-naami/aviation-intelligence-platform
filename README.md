# ✈️ Global Aviation Radar & Aviation Intelligence Platform

An institutional-grade, real-time aviation intelligence platform built with **Streamlit**, **Plotly**, and live **ADS-B Telemetry**. Provides live flight tracking across international airspace, active war/conflict zone interception analysis (EASA/FAA CZIB), airport FIDS departure/arrival timetables, aerodrome METAR weather decoding, visa & passport validity intelligence, and flight route safety planners.

---

## 🌟 Key Highlights & Capabilities

- 🔄 **Live 10-Second Auto-Refresh Engine**: Continuous telemetry streaming every 10 seconds via `streamlit_autorefresh` with manual pause/resume controls and live cycle counter.
- 📡 **Real-Time ADS-B Radar**: Streams live aircraft positions, barometric altitude, true ground speed, heading, origin country, and squawk transponder codes from the **OpenSky Network**.
- 🚨 **Emergency Transponder Detection**: Automatic detection and instant alert banner for emergency squawk codes (`7700` General Emergency, `7600` Radio Failure, `7500` Hijacking).
- ⛔ **Conflict Airspaces & War Zones (CZIB)**: Comprehensive registry of active high-risk and no-fly zones (Ukraine, Red Sea, Yemen, Iran, Syria, Somalia, etc.) based on EASA, FAA, and ICAO safety bulletins.
- 📺 **Airport FIDS Flight Display Systems**: Live international departure and arrival boards with gate assignments, flight status, baggage carousel numbers, and delay updates.
- 🧭 **Great-Circle Route Planner & Conflict Interception**: Computes exact geodesic great-circle flight paths, fuel burn estimates, flight duration, and tests for trajectory intersection with active combat zones.
- 🛫 **METAR Operations & Crosswind Compass**: Decodes aviation weather stations, computes runway headwind/crosswind vectors, flight rules (VFR / MVFR / IFR / LIFR), dew points, and altimeter settings.
- 🛂 **Visa, Passport & Border Intelligence**: Entry requirements, passport validity rules (e.g., 6-month rule), visa-on-arrival fees, and transit visa policies across 100+ countries.
- ⏱️ **Airport Wait Times & Queue Risk**: Live predictive security checkpoint delays, customs wait times, and flight boarding delay risk gauges.
- ⚠️ **Aviation Safety & Accident Intelligence**: Historical accident rate trends, phase-of-flight risk distributions (Takeoff vs. Cruise vs. Final Approach), and causal factor analyses.

---

## 🧭 Platform Architecture & Modules

The platform is organized into 9 specialized operational tabs:

| Tab | Module | Description |
|:---|:---|:---|
| **1** | `🛰️ Live Flight Radar (ADS-B)` | Interactive 3D/2D Scattergeo radar tracking all active aircraft in selected FIRs with callsign search and emergency squawk badges. |
| **2** | `📺 Live Airport FIDS Boards` | High-fidelity departure & arrival airport boards styled after international airport terminal monitors (e.g., Casablanca GMMN, London Heathrow EGLL, Dubai OMDB). |
| **3** | `🛂 Visa & Passport Entry Guide` | Passport validity validator (checks months remaining until expiry), visa requirements matrix, and eVisa fee calculators. |
| **4** | `⏱️ Airport Wait Times & Delay Engine` | Security queue estimations, immigration delay risk gauges, and terminal walking time calculators. |
| **5** | `⛔ Conflict Airspaces & War Zones` | Geopolitical conflict map showing no-fly zones, surface-to-air missile threats, and EASA Conflict Zone Information Bulletins (CZIB). |
| **6** | `🧭 Flight Route Planner` | Great-circle trajectory simulator between any two international airports, warning pilots of route intersections with war zones. |
| **7** | `🛫 Airport Hubs & METAR Weather` | Real-time aviation weather reports with decoded ceiling/visibility and runway crosswind component polar compasses. |
| **8** | `⚠️ Aviation Accidents & Safety` | Historical safety evolutions, fatal accident rates per million departures, and causal risk breakdown charts. |
| **9** | `🌪️ Severe Turbulence & Airspace Hazards` | Clear Air Turbulence (CAT), mountain wave warnings, convective storm SIGMETs, and jet stream wind shear analyses. |

---

## 📁 Repository Structure

```
aviation-intelligence-platform/
├── app.py                         # Main Streamlit dashboard application
├── requirements.txt               # Python package dependencies
├── README.md                      # Platform documentation & manual
├── .gitignore                     # Git ignore rules
└── src/
    ├── __init__.py                # Package initialization
    ├── opensky_client.py          # OpenSky Network ADS-B REST API client
    ├── airports_data.py           # Global airport database & great-circle math
    ├── conflict_zones_data.py     # EASA/FAA CZIB conflict airspace polygons
    ├── fids_data.py               # Flight Information Display System generator
    ├── aviation_weather_client.py # NOAA/FAA METAR aerodrome weather client
    ├── aviation_safety_client.py  # ICAO/NTSB aviation safety statistics engine
    ├── visa_intelligence_data.py  # Visa requirements & passport validity rules
    ├── airport_passenger_guide.py # Airport queues, security wait times & tips
    └── visualizer.py              # Plotly radar maps, compasses & chart renderers
```

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
- **Python**: Version `3.10` or higher.
- **Git** (optional).

### 2. Clone or Navigate to the Directory
```bash
cd "C:\Users\khali\OneDrive\Bureau\aviation-intelligence-platform"
```

### 3. Create & Activate Virtual Environment
```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Launch the Application
```bash
streamlit run app.py
```

The application will open automatically in your browser at `http://localhost:8501`.

---

## ⚙️ Configuration & Sidebar Controls

- **Auto-Refresh Toggle**: Enable/disable live 10-second background polling.
- **Radar Coverage Region**: Switch between regions:
  - *Western Europe & Mediterranean*
  - *North Africa & Morocco*
  - *Middle East & Gulf Hubs*
  - *North America (East Coast)*
  - *East Asia & Japan*
- **Max Aircraft Scan Limit**: Control transponder ingestion volume (50 to 500 aircraft).
- **Callsign Filter**: Instant search for specific airlines or flight numbers (e.g. `RAM`, `BAW`, `UAE`, `AFR`, `DLH`).

---

## 📡 Data Providers & External APIs

- **OpenSky Network**: Open-access ADS-B transponder telemetry for commercial aviation.
- **FAA / NOAA Aviation Weather**: Official real-time METAR and TAF aerodrome reports.
- **EASA / FAA CZIB**: European Union Aviation Safety Agency Conflict Zone Information Bulletins.
- **ICAO Safety Portal**: Global civil aviation safety indicators and fatal accident benchmarks.

---

## 🔒 Security & Safe Operation Notice

This platform is intended for informational, tracking, and educational purposes. Operational flight plans, flight dispatching, and inflight diversions must always follow certified airline dispatchers, Air Traffic Control (ATC) clearances, and official Aeronautical Information Publications (AIP).

---

## 📄 License
This project is licensed under the MIT License.

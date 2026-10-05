"""Institutional Global Flight Radar, Conflict Airspace, Airport FIDS & Aviation Intelligence Platform."""

import time
import datetime
import pandas as pd
import numpy as np
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from src.airports_data import (
    AIRPORTS_DATABASE,
    get_airport_info,
    search_airports,
    calculate_great_circle_distance,
    generate_great_circle_path,
    estimate_flight_metrics
)
from src.conflict_zones_data import CONFLICT_ZONES_DATABASE, check_flight_path_conflicts
from src.opensky_client import OpenSkyClient, REGIONS
from src.aviation_weather_client import AviationWeatherClient
from src.aviation_safety_client import AviationSafetyClient
from src.fids_data import FIDSManager
from src.visa_intelligence_data import COUNTRIES_LIST, VisaIntelligenceEngine
from src.airport_passenger_guide import AirportPassengerGuide
from src.visualizer import (
    create_flight_radar_map,
    create_runway_crosswind_compass,
    create_phase_of_flight_risk_chart,
    create_safety_evolution_chart,
    create_causal_factors_pie,
    create_delay_probability_gauge
)

# Page Setup
st.set_page_config(
    page_title="Global Flight Radar & Aviation Intelligence",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Institutional Dark CSS
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #f59e0b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-bottom: 0.8rem;
    }
    .live-badge {
        display: inline-flex;
        align-items: center;
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(16, 185, 129, 0.4);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        color: #34d399;
        font-weight: 600;
        margin-bottom: 1.2rem;
    }
    .metric-card {
        background: rgba(30, 41, 59, 0.75);
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .metric-title {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f8fafc;
        margin: 0.3rem 0;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #38bdf8;
    }
    .conflict-alert {
        background: rgba(239, 68, 68, 0.15);
        border-left: 5px solid #ef4444;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .visa-card {
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(56, 189, 248, 0.3);
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Clients
@st.cache_resource
def get_opensky_client() -> OpenSkyClient:
    return OpenSkyClient()

@st.cache_resource
def get_aviation_weather_client() -> AviationWeatherClient:
    return AviationWeatherClient()

opensky_client = get_opensky_client()
aviation_weather_client = get_aviation_weather_client()

# Sidebar
st.sidebar.markdown("## 🛰️ Flight Radar Controls")
selected_region = st.sidebar.selectbox(
    "Select Radar Coverage Region:",
    options=list(REGIONS.keys()),
    index=1
)

max_aircraft = st.sidebar.slider("Max Tracked Aircraft", min_value=50, max_value=500, value=250, step=50)

search_callsign = st.sidebar.text_input("🔍 Search Flight / Callsign:", value="", placeholder="e.g. RAM402, UAE101, BAW22...")

# 10s Live Auto-Refresh
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔄 Live Telemetry & Auto-Refresh")
auto_refresh_enabled = st.sidebar.toggle("10s Auto-Refresh (Live Sync)", value=True)
refresh_counter = 0
if auto_refresh_enabled:
    refresh_counter = st_autorefresh(interval=10000, limit=None, key="aviation_auto_refresh_10s")

if st.sidebar.button("🔄 Scan & Refresh Radar Feed Now", key="btn_refresh"):
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("""
### 📡 Data Update Frequencies:
- **ADS-B Live Flights:** Every **5 - 10 seconds** (Real-time).
- **METAR Aerodrome Weather:** Every **30 - 60 minutes**.
- **Airport FIDS Boards:** Every **1 minute**.
- **Conflict Airspaces:** Real-time **NOTAM / CZIB Bulletins**.
""")

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚠️ Conflict Airspaces Monitored")
st.sidebar.markdown(f"**{len(CONFLICT_ZONES_DATABASE)} Active Global Zones:**")
for _, z in CONFLICT_ZONES_DATABASE.items():
    st.sidebar.markdown(f"- {z['name'][:24]} ({z['risk_level'][:7]})")

# Main Header
st.markdown('<div class="main-title">✈️ Global Aviation Radar, FIDS Airport Boards & Travel Intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Live ADS-B Flight Tracking | FIDS Airport Timetables | Visa & Passport Fees | War Zone Interception | METAR Weather Operations</div>', unsafe_allow_html=True)

# Live Status Badge
now_utc_str = datetime.datetime.utcnow().strftime("%H:%M:%S UTC")
if auto_refresh_enabled:
    st.markdown(f'<div class="live-badge">🟢 LIVE TELEMETRY ACTIVE &bull; Auto-Refreshing every 10s &bull; Last Synced: {now_utc_str} &bull; Cycle #{refresh_counter}</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="live-badge" style="background:rgba(148,163,184,0.1); border-color:rgba(148,163,184,0.3); color:#94a3b8;">⏸️ LIVE SYNC PAUSED &bull; Last Synced: {now_utc_str}</div>', unsafe_allow_html=True)

# Fetch Live Flights Data
with st.spinner(f"Acquiring ADS-B transponder telemetry for {selected_region}..."):
    flights_df = opensky_client.fetch_live_flights(region_name=selected_region, max_flights=max_aircraft)

# Filter by Callsign if searched
if search_callsign and not flights_df.empty:
    flights_df = flights_df[flights_df["callsign"].str.contains(search_callsign.upper().strip(), na=False)]

# Top Metric Cards
tot_flights = len(flights_df)
emergency_flights = flights_df[flights_df["squawk"].isin(["7700", "7600", "7500"])] if not flights_df.empty else pd.DataFrame()
avg_alt = int(flights_df["altitude_ft"].mean()) if not flights_df.empty else 0
avg_spd = int(flights_df["speed_kts"].mean()) if not flights_df.empty else 0
active_conflicts_count = len(CONFLICT_ZONES_DATABASE)

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Active Aircraft</div>
        <div class="metric-value">✈️ {tot_flights:,}</div>
        <div class="metric-sub">Region: {selected_region[:15]}</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    emg_color = "#ef4444" if len(emergency_flights) > 0 else "#10b981"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Emergency Transponders</div>
        <div class="metric-value" style="color:{emg_color};">🚨 {len(emergency_flights)}</div>
        <div class="metric-sub">Squawks 7700 / 7600 / 7500</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Average Fleet Altitude</div>
        <div class="metric-value">📈 {avg_alt:,} <span style="font-size:1rem;">ft</span></div>
        <div class="metric-sub">FL{int(avg_alt/100):03d} Cruise Level</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Average Ground Speed</div>
        <div class="metric-value">💨 {avg_spd} <span style="font-size:1rem;">kts</span></div>
        <div class="metric-sub">{int(avg_spd * 1.852)} km/h</div>
    </div>
    """, unsafe_allow_html=True)

with k5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Monitored Conflict Zones</div>
        <div class="metric-value">⛔ {active_conflicts_count}</div>
        <div class="metric-sub">Active No-Fly / War FIRs</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Main Navigation Tabs (9 Modules)
tabs = st.tabs([
    "🛰️ Live Flight Radar (ADS-B)",
    "📺 Live Airport FIDS Boards",
    "🛂 Visa & Passport Entry Guide",
    "⏱️ Airport Wait Times & Delay Engine",
    "⛔ Conflict Airspaces & War Zones",
    "🧭 Flight Route Planner & Conflict Checker",
    "🛫 Airport Hubs & METAR Weather",
    "⚠️ Aviation Accidents & Safety Intelligence",
    "🌪️ Severe Turbulence & Airspace Hazards"
])

# ----------------- TAB 1: Live Flight Radar -----------------
with tabs[0]:
    st.markdown(f"### 🛰️ Live ADS-B Flight Radar — {selected_region}")
    
    fig_radar = create_flight_radar_map(flights_df, highlight_conflicts=True)
    st.plotly_chart(fig_radar, use_container_width=True)

    if not emergency_flights.empty:
        st.error(f"🚨 **EMERGENCY SQUAWK DETECTED!** {len(emergency_flights)} aircraft currently broadcasting emergency codes.")
        st.dataframe(emergency_flights[["callsign", "squawk", "origin_country", "altitude_ft", "speed_kts", "emergency"]], use_container_width=True)

    with st.expander("📋 View Real-Time Live Aircraft Telemetry Feed"):
        st.dataframe(
            flights_df[["callsign", "origin_country", "altitude_ft", "speed_kts", "speed_kmh", "heading_deg", "vertical_rate_fpm", "flight_phase", "squawk"]].rename(columns={
                "callsign": "Flight Number",
                "origin_country": "Country",
                "altitude_ft": "Altitude (ft)",
                "speed_kts": "Speed (kts)",
                "speed_kmh": "Speed (km/h)",
                "heading_deg": "Heading (°)",
                "vertical_rate_fpm": "Climb/Desc (ft/min)",
                "flight_phase": "Flight Phase",
                "squawk": "Squawk Code"
            }),
            use_container_width=True
        )
        csv_flights = flights_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Live Radar Dataset (CSV)", data=csv_flights, file_name="live_flight_radar.csv", mime="text/csv")

# ----------------- TAB 2: Live Airport FIDS Boards -----------------
with tabs[1]:
    st.markdown("### 📺 Digital Airport Flight Information Display System (FIDS)")
    st.markdown("Live real-time simulated airport terminal flight monitors for Departures and Arrivals.")

    fids_apt_keys = list(AIRPORTS_DATABASE.keys())
    fids_chosen_icao = st.selectbox(
        "Select Airport Hub for Live Flight Board:",
        options=fids_apt_keys,
        format_func=lambda x: f"{AIRPORTS_DATABASE[x]['city']} ({AIRPORTS_DATABASE[x]['iata']}) - {AIRPORTS_DATABASE[x]['name']}",
        index=0,
        key="fids_select"
    )
    fids_info = get_airport_info(fids_chosen_icao)

    if fids_info:
        boards = FIDSManager.generate_fids_boards(fids_info["iata"], fids_info["city"])
        dep_df = boards["departures_df"]
        arr_df = boards["arrivals_df"]

        board_tab1, board_tab2 = st.tabs(["🛫 Live Departures Board", "🛬 Live Arrivals Board"])
        
        with board_tab1:
            st.markdown(f"#### 🛫 **{fids_info['city']} ({fids_info['iata']})** — Live Departures")
            st.dataframe(dep_df, use_container_width=True, hide_index=True)

        with board_tab2:
            st.markdown(f"#### 🛬 **{fids_info['city']} ({fids_info['iata']})** — Live Arrivals")
            st.dataframe(arr_df, use_container_width=True, hide_index=True)

# ----------------- TAB 3: Visa Requirements & Entry Fees -----------------
with tabs[2]:
    st.markdown("### 🛂 Global Visa Requirements, Entry Fees & Passport Policy")
    st.markdown("Bilateral travel entry regulations, maximum allowed stay, estimated visa costs, and document requirements.")

    v_c1, v_c2 = st.columns(2)
    with v_c1:
        origin_passport = st.selectbox("Select Your Passport / Nationality:", COUNTRIES_LIST, index=0)
    with v_c2:
        dest_country = st.selectbox("Select Destination Country:", COUNTRIES_LIST, index=1)

    visa_rule = VisaIntelligenceEngine.get_visa_requirement(origin_passport, dest_country)

    st.markdown(f"""
    <div class="visa-card">
        <h3>🛂 Entry Policy: {origin_passport} ➔ {dest_country}</h3>
        <h2 style="color: #38bdf8; margin: 0.5rem 0;">{visa_rule['status']}</h2>
        <hr style="border-color: rgba(56, 189, 248, 0.2);">
        <p><b>⏱️ Maximum Allowed Stay:</b> {visa_rule['stay']}</p>
        <p><b>💵 Estimated Visa Cost / Fee:</b> <span style="color:#f59e0b; font-weight:700; font-size:1.2rem;">{visa_rule['fee_usd']}</span></p>
        <p><b>⏳ Typical Processing Time:</b> {visa_rule['time']}</p>
        <p><b>📘 Minimum Passport Validity:</b> {visa_rule['passport_validity_min']}</p>
        <br>
        <h4>📄 Standard Mandatory Entry Documents:</h4>
        <ul>
            {''.join([f'<li>{doc}</li>' for doc in visa_rule['mandatory_documents']])}
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ----------------- TAB 4: Airport Wait Times & Delay Predictor -----------------
with tabs[3]:
    st.markdown("### ⏱️ Airport Terminal Queue Estimator & Delay Risk Engine")
    st.markdown("Passenger terminal transit buffers and statistical weather delay probability calculator.")

    w_col1, w_col2 = st.columns([1, 1.2])
    with w_col1:
        st.markdown("#### 🕒 Passenger Terminal Lead Time Estimator")
        flight_type_sel = st.radio("Select Flight Category:", ["International", "Domestic / Regional"], index=0)
        timings = AirportPassengerGuide.estimate_airport_timings(flight_type_sel)

        st.info(f"💡 **Recommended Arrival Time:** **{timings['recommended_arrival_text']}**")

        st.markdown(f"""
        - 🧳 **Check-In & Bag Drop:** ~`{timings['checkin_wait_min']} minutes`
        - 👮 **Security Screening Queue:** ~`{timings['security_wait_min']} minutes`
        - 🛂 **Passport & Border Control:** ~`{timings['immigration_wait_min']} minutes`
        - 🚶 **Walking Time to Gate:** ~`{timings['gate_walk_min']} minutes`
        - 🚪 **Gate Closes:** `{timings['boarding_close_min']} minutes before departure`
        - ⏱️ **Total Estimated Terminal Process:** **`{timings['total_estimated_process_min']} minutes`**
        """)

        with st.expander("🧳 Luggage & Liquid Rules Guide"):
            st.markdown("""
            - **Cabin Baggage:** Max 1 piece ($55\\times40\\times20\\text{ cm}$), weight 7 - 10 kg.
            - **Liquids Rule:** Max 100 ml per container, placed inside 1 transparent re-sealable 1-liter plastic bag.
            - **Power Banks & Lithium Batteries:** **STRICTLY in cabin baggage only** (never in checked baggage).
            """)

    with w_col2:
        st.markdown("#### 📉 Weather-Driven Delay Risk Predictor")
        # Estimate delay based on airport METAR weather
        pred_icao = st.selectbox("Select Airport for Delay Analysis:", list(AIRPORTS_DATABASE.keys()), index=0, key="pred_apt")
        p_apt = get_airport_info(pred_icao)

        if p_apt:
            metar_p = aviation_weather_client.fetch_airport_metar(pred_icao, p_apt["lat"], p_apt["lon"])
            xw_p = aviation_weather_client.calculate_runway_crosswind(
                metar_p["wind_direction_deg"],
                metar_p["wind_speed_kts"],
                p_apt["rwy_hdg"]
            )
            delay_res = AirportPassengerGuide.predict_flight_delay_probability(
                wind_speed_kts=metar_p["wind_speed_kts"],
                crosswind_kts=xw_p["crosswind_component_kts"],
                visibility_sm=metar_p["visibility_statute_miles"],
                flight_cat=metar_p["flight_category"]
            )

            st.metric("Statistical Delay Probability", f"{delay_res['delay_probability_pct']}%", delta=delay_res["risk_status"])
            
            fig_delay_gauge = create_delay_probability_gauge(delay_res["delay_probability_pct"])
            st.plotly_chart(fig_delay_gauge, use_container_width=True)

# ----------------- TAB 5: Conflict Airspaces & War Zones -----------------
with tabs[4]:
    st.markdown("### ⛔ Global Conflict Airspaces, War Zones & Military Interception Threats")
    st.markdown("Comprehensive surveillance of high-risk international Flight Information Regions (FIRs) affected by military conflict, surface-to-air missiles, and electronic warfare.")

    for zone_id, zone in CONFLICT_ZONES_DATABASE.items():
        color_badge = "🔴" if zone["risk_code"] == 3 else ("🟠" if zone["risk_code"] == 2 else "🟡")
        with st.expander(f"{color_badge} **{zone['name']}** — {zone['risk_level']}", expanded=True):
            cz1, cz2 = st.columns([1.5, 1])
            with cz1:
                st.markdown(f"**💥 Threat Rationale:** {zone['reason']}")
                st.markdown(f"**🛡️ Operational Advisory:** {zone['advisory']}")
            with cz2:
                st.info(f"**Affected FIR Codes:** `{'`, `'.join(zone['fir_codes'])}`\n\n**Threat Category:** {zone['risk_level']}")

# ----------------- TAB 6: Flight Route Planner & Conflict Checker -----------------
with tabs[5]:
    st.markdown("### 🧭 Great Circle Flight Route Planner & Conflict Zone Interceptor")
    st.markdown("Plan commercial flight trajectories and automatically evaluate whether the geodesic corridor intersects active war zones or restricted no-fly airspaces.")

    r_col1, r_col2 = st.columns(2)
    with r_col1:
        dep_options = {f"{a['city']} ({a['iata']}) - {a['name']}": icao for icao, a in AIRPORTS_DATABASE.items()}
        dep_selected_label = st.selectbox("Select Departure Airport (DEP):", list(dep_options.keys()), index=0)
        dep_icao = dep_options[dep_selected_label]
        dep_info = get_airport_info(dep_icao)

    with r_col2:
        arr_options = {f"{a['city']} ({a['iata']}) - {a['name']}": icao for icao, a in AIRPORTS_DATABASE.items()}
        arr_selected_label = st.selectbox("Select Destination Airport (ARR):", list(arr_options.keys()), index=7)
        arr_icao = arr_options[arr_selected_label]
        arr_info = get_airport_info(arr_icao)

    if dep_info and arr_info:
        dist_km, dist_nm = calculate_great_circle_distance(dep_info["lat"], dep_info["lon"], arr_info["lat"], arr_info["lon"])
        metrics = estimate_flight_metrics(dist_nm, dist_km)
        flight_path = generate_great_circle_path(dep_info["lat"], dep_info["lon"], arr_info["lat"], arr_info["lon"], num_points=75)

        # Evaluate Conflicts on Path
        conflicts_found = check_flight_path_conflicts(flight_path)

        st.markdown(f"#### 🛫 Route: **{dep_info['city']} ({dep_info['iata']})** ➔ **{arr_info['city']} ({arr_info['iata']})**")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Great Circle Distance", f"{dist_nm:,.0f} NM", f"{dist_km:,.0f} km")
        m2.metric("Estimated Flight Duration", f"{metrics['flight_time_formatted']}", f"{metrics['flight_time_decimal']} hrs")
        m3.metric("Cruise Altitude Profile", f"FL{int(metrics['typical_cruise_altitude_ft']/100)}", f"{metrics['typical_cruise_altitude_ft']:,} ft")
        m4.metric("Est. Fuel & CO₂", f"{metrics['est_fuel_tonnes']} tonnes", f"{metrics['est_co2_tonnes']} t CO₂")

        # Conflict Interceptor Warning Box
        if conflicts_found:
            st.error(f"⚠️ **AIRSPACE CONFLICT WARNING**: The direct Great Circle trajectory passes near or through **{len(conflicts_found)} conflict zone(s)**!")
            for cf in conflicts_found:
                st.markdown(f"""
                <div class="conflict-alert">
                    <b>⛔ {cf['name']} — Status: {cf['status']}</b><br>
                    <b>Threat Level:</b> {cf['risk_level']}<br>
                    <b>Danger Details:</b> {cf['reason']}<br>
                    <b>Operational Action:</b> {cf['advisory']}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ **CLEAR AIRSPACE**: Planned Great Circle corridor has no direct active warzone or no-fly zone intersections.")

        # Display Route Map
        fig_route = create_flight_radar_map(
            flights_df=pd.DataFrame(),
            flight_path=flight_path,
            dep_airport=dep_info,
            arr_airport=arr_info,
            highlight_conflicts=True
        )
        st.plotly_chart(fig_route, use_container_width=True)

# ----------------- TAB 7: Airport Hubs & METAR Weather -----------------
with tabs[6]:
    st.markdown("### 🛫 Airport Hub Operations & Decoded METAR Aviation Weather")
    
    apt_keys = list(AIRPORTS_DATABASE.keys())
    selected_apt_icao = st.selectbox(
        "Select International Airport Hub:",
        options=apt_keys,
        format_func=lambda x: f"{AIRPORTS_DATABASE[x]['city']} ({AIRPORTS_DATABASE[x]['iata']}) - {AIRPORTS_DATABASE[x]['name']} [{x}]",
        index=0
    )
    apt_data = get_airport_info(selected_apt_icao)

    if apt_data:
        with st.spinner(f"Decoding METAR observation for {apt_data['name']}..."):
            metar_res = aviation_weather_client.fetch_airport_metar(selected_apt_icao, apt_data["lat"], apt_data["lon"])
            xwind_res = aviation_weather_client.calculate_runway_crosswind(
                wind_dir=metar_res["wind_direction_deg"],
                wind_speed_kts=metar_res["wind_speed_kts"],
                runway_heading=apt_data["rwy_hdg"]
            )

        st.info(f"**Official Decoded METAR:** `{metar_res['raw_metar']}`\n\n**Flight Rules Category:** {metar_res['category_badge']} — *{metar_res['category_description']}*")

        ap1, ap2, ap3, ap4, ap5 = st.columns(5)
        ap1.metric("Air Temperature", f"{metar_res['temperature_c']}°C", f"Dew Point: {metar_res['dew_point_c']}°C")
        ap2.metric("Surface Wind", f"{metar_res['wind_direction_deg']:03d}° / {metar_res['wind_speed_kts']} kts", f"Gusts: {metar_res['wind_gust_kts']} kts")
        ap3.metric("Barometric Pressure", f"{metar_res['altimeter_qnh_hpa']} hPa", "QNH Altimeter")
        ap4.metric("Horizontal Visibility", f"{metar_res['visibility_statute_miles']} SM", "Statute Miles")
        ap5.metric("Airport Elevation", f"{apt_data['elev_ft']} ft", f"Runway Hdg: {apt_data['rwy_hdg']}°")

        # Runway Crosswind Compass & Safety Radar
        st.markdown(f"#### 🧭 Runway Alignment & Crosswind Vector Analysis (Runway {apt_data['rwy_hdg']:02d})")
        
        xw_col1, xw_col2 = st.columns([1.2, 1])
        with xw_col1:
            fig_compass = create_runway_crosswind_compass(xwind_res, rwy_name=f"{apt_data['rwy_hdg']:02d}")
            st.plotly_chart(fig_compass, use_container_width=True)

        with xw_col2:
            st.markdown("##### 🛬 Runway Wind Vector Breakdown:")
            st.markdown(f"- **Headwind Component:** `{xwind_res['headwind_component_kts']} kts` {'(Headwind 🟢)' if not xwind_res['is_tailwind'] else '(TAILWIND ⚠️)'}")
            st.markdown(f"- **Crosswind Component:** `{xwind_res['crosswind_component_kts']} kts` ({xwind_res['crosswind_side']})")
            st.markdown(f"- **Wind Angle Offset:** `{xwind_res['angle_difference_deg']}°` relative to runway centerline.")
            st.markdown(f"- **Safety Status Assessment:** {xwind_res['safety_status']}")

# ----------------- TAB 8: Aviation Accidents & Safety Intelligence -----------------
with tabs[7]:
    st.markdown("### ⚠️ Aviation Accidents & Safety Intelligence")
    st.markdown("Statistical breakdown of commercial aviation safety records, accident causation factors, and the evolution of flight safety systems.")

    phase_df = AviationSafetyClient.get_phase_risk_df()
    causal_df = AviationSafetyClient.get_causal_factors_df()
    evo_df = AviationSafetyClient.get_safety_evolution_df()
    cases = AviationSafetyClient.get_case_studies()

    sc1, sc2 = st.columns(2)
    with sc1:
        fig_phase = create_phase_of_flight_risk_chart(phase_df)
        st.plotly_chart(fig_phase, use_container_width=True)
    with sc2:
        fig_causal = create_causal_factors_pie(causal_df)
        st.plotly_chart(fig_causal, use_container_width=True)

    fig_evo = create_safety_evolution_chart(evo_df)
    st.plotly_chart(fig_evo, use_container_width=True)

    st.markdown("#### 📚 Landmark Safety Case Studies & Regulatory Milestones")
    for cs in cases:
        st.markdown(f"""
        - **{cs['Event']}** ({cs['Airspace']}):
          - *Root Cause / Finding:* {cs['Finding']}
          - *Safety & Regulatory Impact:* **{cs['Regulatory_Impact']}**
        """)

# ----------------- TAB 9: Severe Turbulence & Airspace Hazards -----------------
with tabs[8]:
    st.markdown("### 🌪️ Severe Turbulence & Airspace Disturbance Intelligence")
    st.markdown("""
    Turbulence remains the #1 cause of non-fatal in-flight injuries to passengers and flight attendants. 
    Modern aviation categorizes and monitors three primary turbulence phenomena:
    """)

    tc1, tc2, tc3 = st.columns(3)
    with tc1:
        st.markdown("""
        #### 1. Clear-Air Turbulence (CAT)
        - **Mechanism**: Occurs in cloudless skies above 15,000 ft near upper-level **Jet Streams** (winds > 100 kts).
        - **Invisible to Radar**: Cannot be detected by standard onboard weather radar since no moisture/ice particles are present.
        - **Detection**: Temperature shear gradients and wind-vector anomalies.
        """)

    with tc2:
        st.markdown("""
        #### 2. Convective Storm Updrafts
        - **Mechanism**: Massive vertical thermals inside **Cumulonimbus (CB)** clouds reaching up to 50,000+ ft.
        - **Hazards**: Hail, lightning, severe microburst windshears, and airframe stress.
        - **Avoidance**: Mandatory lateral separation of at least **20 Nautical Miles** from severe thunderstorm cores.
        """)

    with tc3:
        st.markdown("""
        #### 3. Mountain Wave & Wake Turbulence
        - **Mechanism**: High winds blowing perpendicular over high mountain ranges creating standing lee waves and rotor clouds.
        - **Wake Vortices**: Counter-rotating vortices trailing from heavy aircraft wingtips requiring 4 to 8 NM radar separation.
        """)

    st.info("💡 **Aviation Safety Best Practice**: Airlines and IATA mandate passenger seatbelts to remain fastened during all high-altitude cruise segments to prevent sudden clear-air turbulence injuries.")

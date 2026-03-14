import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import datetime
from streamlit_geolocation import streamlit_geolocation
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import pandas as pd
import os

st.set_page_config(
    page_title="TerraSense AI",
    page_icon="🌱",
    layout="wide"
)

# ---------------------------
# SIDEBAR
# ---------------------------

st.sidebar.title("🌱 Farm Setup")

crop = st.sidebar.selectbox(
    "Select Crop",
    ["Maize", "Rice", "Cassava", "Millet"]
)

farm_size = st.sidebar.number_input(
    "Farm Size (hectares)",
    min_value=0.1,
    max_value=100.0,
    value=1.0
)

# Farmers registered
if os.path.exists("farmers.csv"):
    df = pd.read_csv("farmers.csv")
    farmers_registered = len(df)
else:
    farmers_registered = 0

st.sidebar.metric("Farmers Registered", farmers_registered)

# Farms analyzed
if os.path.exists("analysis_count.txt"):
    with open("analysis_count.txt","r") as f:
        farms_analyzed = int(f.read())
else:
    farms_analyzed = 0

st.sidebar.metric("Farms Analyzed", farms_analyzed)

# Reports generated
if os.path.exists("report_count.txt"):
    with open("report_count.txt","r") as f:
        reports_generated = int(f.read())
else:
    reports_generated = 0

st.sidebar.metric("Reports Generated", reports_generated)

# ---------------------------
# TITLE
# ---------------------------

st.title("TerraSense AI – Smart Farm Advisor 🌱")
st.subheader("Farm Irrigation Advisor")

col1, col2 = st.columns([1,2])

# ---------------------------
# GPS DETECTION
# ---------------------------

location = streamlit_geolocation()

if location and location["latitude"] is not None:
    lat = location["latitude"]
    lon = location["longitude"]
    st.success(f"GPS detected: {lat:.4f}, {lon:.4f}")
else:
    lat = 7.38
    lon = 3.93
    st.info("Using default location (Ibadan).")

# ---------------------------
# MAP
# ---------------------------

with col2:

    st.subheader("Select Farm Location")

    m = folium.Map(location=[lat, lon], zoom_start=13, tiles=None)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri"
    ).add_to(m)

    map_data = st_folium(m, width=700, height=400)

    if map_data and map_data["last_clicked"]:
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        st.success(f"Selected Farm: {lat:.4f}, {lon:.4f}")

# ---------------------------
# SEASON
# ---------------------------

month = datetime.datetime.now().month

if month in [11,12,1,2,3]:
    season = "Dry Season"
else:
    season = "Rainy Season"

st.write("Current Season:", season)

# ---------------------------
# WEATHER API
# ---------------------------

API_KEY = st.secrets["OPENWEATHER_KEY"]

# Initialize variables
temperature = None
humidity = None
total_rain = 0
time_to_rain = None
crop_status = ""
advice = ""

# ---------------------------
# CARBON INTELLIGENCE ENGINE
# ---------------------------

def estimate_carbon(farm_size, crop):

    carbon_factors = {
        "Maize": 0.6,
        "Rice": 0.8,
        "Cassava": 0.5,
        "Millet": 0.4
    }

    factor = carbon_factors.get(crop, 0.5)

    carbon = farm_size * factor

    return round(carbon,2)

# ---------------------------
# VEGETATION HEALTH
# ---------------------------

def vegetation_health():

    import random
    ndvi = round(random.uniform(0.2,0.8),2)

    if ndvi > 0.6:
        status = "Healthy vegetation"
    elif ndvi > 0.4:
        status = "Moderate vegetation"
    else:
        status = "Poor vegetation"

    return ndvi, status


# ---------------------------
# ANALYZE FARM
# ---------------------------

if st.button("Analyze Farm"):

    farms_analyzed += 1
    with open("analysis_count.txt","w") as f:
        f.write(str(farms_analyzed))

    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    weather_data = requests.get(weather_url).json()

    temperature = weather_data["main"]["temp"]
    humidity = weather_data["main"]["humidity"]

    forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    forecast_data = requests.get(forecast_url).json()

    total_rain = 0

    for entry in forecast_data["list"]:

        rain = entry.get("rain",{}).get("3h",0)
        total_rain += rain

        if rain > 0 and time_to_rain is None:
            forecast_time = datetime.datetime.fromtimestamp(entry["dt"])
            now = datetime.datetime.now()
            time_to_rain = (forecast_time - now).total_seconds() / 3600

    # Irrigation Logic
    if total_rain < 5 and humidity < 60:
        crop_status = "High Water Stress"
        advice = "Irrigate immediately"

    elif total_rain < 10:
        crop_status = "Moderate Water Stress"
        advice = "Irrigate within 2–3 days"

    else:
        crop_status = "Healthy"
        advice = "No irrigation needed"

    # ---------------------------
    # RESULTS
    # ---------------------------

    st.subheader("Farm Analysis Results")
    climate_score = int((carbon * 10) + (total_rain * 2))

if climate_score > 100:
    climate_score = 100

st.metric("Farm Climate Score", climate_score)

    # ---------------------------
# CARBON IMPACT
# ---------------------------

carbon = estimate_carbon(farm_size, crop)

st.subheader("Climate Impact")

st.metric("Estimated Carbon Stored", f"{carbon} tons CO₂ / year")

    st.metric("Crop Status", crop_status)
    st.metric("5-Day Rainfall Forecast", f"{total_rain:.2f} mm")

    st.warning(advice)

ndvi, veg_status = vegetation_health()

st.metric("Vegetation Index (NDVI)", ndvi)
st.write("Vegetation Status:", veg_status)

    # ---------------------------
    # RAIN PREDICTION
    # ---------------------------

    st.subheader("Next Rain Prediction")

    if time_to_rain is not None:

        if time_to_rain <= 3:
            st.success("Rain expected within 3 hours")

        elif time_to_rain <= 24:
            st.success(f"Rain expected in {time_to_rain:.0f} hours")

        elif time_to_rain <= 72:
            st.info(f"Rain expected in {time_to_rain/24:.1f} days")

        else:
            st.warning("Rain is several days away")

    else:
        st.error("No significant rain expected in the next 5 days")

    # ---------------------------
    # ADVANCED WEATHER
    # ---------------------------

    with st.expander("Advanced Weather Details"):

        st.write("Temperature:", temperature, "°C")
        st.write("Humidity:", humidity, "%")
        st.write("Total Rainfall Forecast:", f"{total_rain:.2f} mm")
        st.write("Season:", season)
        st.write("Coordinates:", f"{lat:.4f}, {lon:.4f}")

    # ---------------------------
    # GENERATE REPORT
    # ---------------------------

    buffer = BytesIO()
    styles = getSampleStyleSheet()

    elements = [
        Paragraph("TerraSense Farm Report", styles['Title']),
        Spacer(1,20),
        Paragraph(f"Coordinates: {lat:.4f}, {lon:.4f}", styles['Normal']),
        Paragraph(f"Crop: {crop}", styles['Normal']),
        Paragraph(f"Temperature: {temperature} °C", styles['Normal']),
        Paragraph(f"Humidity: {humidity}%", styles['Normal']),
        Paragraph(f"Rainfall Forecast: {total_rain:.2f} mm", styles['Normal']),
        Paragraph(f"Recommendation: {advice}", styles['Normal'])
    ]

    doc = SimpleDocTemplate(buffer)
    doc.build(elements)

    reports_generated += 1
    with open("report_count.txt","w") as f:
        f.write(str(reports_generated))

    st.download_button(
        label="Download Farm Report (PDF)",
        data=buffer.getvalue(),
        file_name="terrasense_report.pdf",
        mime="application/pdf"
    )

# ---------------------------
# FARMER REGISTRATION
# ---------------------------

st.divider()
st.subheader("👩‍🌾 Farmer Registration")

farmer_name = st.text_input("Farmer Name")
farm_location = st.text_input("Farm Location")
crop_type = st.text_input("Crop Grown")

if st.button("Register Farmer"):

    new_data = pd.DataFrame(
        [[farmer_name, farm_location, crop_type]],
        columns=["Name","Location","Crop"]
    )

    if os.path.exists("farmers.csv"):
        df = pd.read_csv("farmers.csv")
        df = pd.concat([df,new_data],ignore_index=True)
    else:
        df = new_data

    df.to_csv("farmers.csv",index=False)

    st.success("Farmer registered successfully!")

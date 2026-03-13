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

try:
    df = pd.read_csv("farmers.csv")
    st.sidebar.metric("Registered Farmers", len(df))
except:
    st.sidebar.metric("Registered Farmers", 0)

st.set_page_config(
    page_title="TerraSense AI",
    page_icon="🌱",
    layout="wide"
)

# ---------------------------
# TITLE
# ---------------------------

st.title("TerraSense AI – Smart Farm Advisor 🌱")
st.subheader("Farm Irrigation Advisor")

# ---------------------------
# FARM SETUP
# ---------------------------

st.subheader("Farm Setup")

col1, col2 = st.columns([1,2])

st.set_page_config(
    page_title="TerraSense AI",
    page_icon="🌱",
    layout="wide"
)

# ---------------------------
# SIDEBAR FARM SETUP
# ---------------------------

st.sidebar.title("🌱 Farm Setup")

crop = st.sidebar.selectbox(
    "Select Crop",
    ["Maize","Rice","Cassava","Millet"]
)

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
        attr="Esri",
        name="Satellite"
    ).add_to(m)

    map_data = st_folium(m, width=700, height=400)

    if map_data and map_data["last_clicked"]:
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        st.success(f"Selected Farm: {lat:.4f}, {lon:.4f}")

# ---------------------------
# CROP INFO
# ---------------------------

if crop == "Maize":
    st.info("Maize requires moderate rainfall and well-drained soil.")

elif crop == "Rice":
    st.info("Rice requires high water levels and flooded fields.")

elif crop == "Cassava":
    st.info("Cassava tolerates drought and grows well in poor soils.")

elif crop == "Millet":
    st.info("Millet is highly drought-resistant and suitable for dry regions.")

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
# CONTEXT
# ---------------------------

st.subheader("🌱 Farm Context")

if season == "Dry Season":
    st.info("Nigeria is currently in the dry season. Rainfall is limited.")
else:
    st.info("Nigeria is currently in the rainy season. Rainfall supports crops.")

# ---------------------------
# WEATHER API
# ---------------------------

API_KEY = st.secrets["OPENWEATHER_KEY"]

# ---------------------------
# ANALYZE FARM
# ---------------------------

if st.button("Analyze Farm", key="analyze_button"):

    st.divider()
    
   

    # CURRENT WEATHER

    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"

    weather_response = requests.get(weather_url)
    weather_data = weather_response.json()

    temperature = weather_data["main"]["temp"]
    humidity = weather_data["main"]["humidity"]

    # FORECAST

    forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"

    forecast_response = requests.get(forecast_url)
    forecast_data = forecast_response.json()

    total_rain = 0
    time_to_rain = None

    for entry in forecast_data["list"]:

        rain = entry.get("rain", {}).get("3h", 0)
        total_rain += rain

        if rain >= 2 and time_to_rain is None:

            forecast_time = entry["dt"]
            current_time = forecast_data["list"][0]["dt"]

            hours_until_rain = (forecast_time - current_time) / 3600
            time_to_rain = hours_until_rain

    # ---------------------------
    # FARM INTELLIGENCE
    # ---------------------------

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

    colA, colB = st.columns(2)

    with colA:
        st.metric("🌱 Crop Status", crop_status)

    with colB:
        st.metric("🌧 5-Day Rainfall Forecast", f"{total_rain:.2f} mm")

    st.subheader("Irrigation Recommendation")
    st.warning(advice)

    # ---------------------------
    # FARM HEALTH SCORE
    # ---------------------------

    if crop_status == "Healthy":
        score = 85
    elif crop_status == "Moderate Water Stress":
        score = 60
    else:
        score = 35

    st.subheader("Farm Health Score")
    st.metric("Farm Health Index", f"{score}/100")

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
    # IRRIGATION PLANNER
    # ---------------------------

    st.subheader("7-Day Irrigation Planner")

    if total_rain < 5:
        st.error("Very little rain expected this week. Irrigate soon.")

    elif total_rain < 15:
        st.warning("Moderate rainfall expected. Monitor soil moisture.")

    else:
        st.success("Good rainfall expected. Irrigation not necessary.")

    # ---------------------------
    # WEATHER DETAILS
    # ---------------------------

    with st.expander("Advanced Weather Details"):
        st.write("Temperature:", temperature)
        st.write("Humidity:", humidity)

            # ---------------------------
    # DOWNLOAD FARM REPORT (PDF)
    # ---------------------------

    st.subheader("Download Farm Report")

    buffer = BytesIO()
    styles = getSampleStyleSheet()

 

    elements = []

    elements.append(Paragraph("TerraSense Farm Report", styles['Title']))
    elements.append(Spacer(1,20))

    elements.append(Paragraph(f"Farm Coordinates: {lat:.4f}, {lon:.4f}", styles['Normal']))
    elements.append(Paragraph(f"Crop Type: {crop}", styles['Normal']))
    elements.append(Paragraph(f"Season: {season}", styles['Normal']))
    elements.append(Spacer(1,20))

    elements.append(Paragraph(f"Temperature: {temperature} °C", styles['Normal']))
    elements.append(Paragraph(f"Humidity: {humidity} %", styles['Normal']))
    elements.append(Paragraph(f"5-Day Rainfall Forecast: {total_rain:.2f} mm", styles['Normal']))
    elements.append(Spacer(1,20))

    elements.append(Paragraph(f"Crop Status: {crop_status}", styles['Normal']))
    elements.append(Paragraph(f"Irrigation Recommendation: {advice}", styles['Normal']))
    elements.append(Paragraph(f"Farm Health Score: {score}/100", styles['Normal']))

    doc = SimpleDocTemplate(buffer)
    doc.build(elements)

    st.download_button(
    label="Download Farm Report (PDF)",
    data=buffer.getvalue(),
    file_name="terrasense_farm_report.pdf",
    mime="application/pdf",
    key="farm_report_download"
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

    import pandas as pd

    new_data = pd.DataFrame(
        [[farmer_name, farm_location, crop_type]],
        columns=["Name", "Location", "Crop"]
    )

    try:
        df = pd.read_csv("farmers.csv")
        df = pd.concat([df, new_data], ignore_index=True)
    except:
        df = new_data

    df.to_csv("farmers.csv", index=False)

    st.success("Farmer registered successfully!")

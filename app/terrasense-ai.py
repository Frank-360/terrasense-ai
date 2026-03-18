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
import random

# ---------------------------
# FUNCTIONS
# ---------------------------

def get_weather_data(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation"
    try:
        response = requests.get(url)
        data = response.json()
        return data["current"]["temperature_2m"], data["current"]["precipitation"]
    except:
        return None, None


def estimate_ai_water_saving(rainfall, temperature, soil_moisture):
    saving = 0
    if rainfall > 10:
        saving += 20
    if soil_moisture > 0.6:
        saving += 30
    if temperature > 35:
        saving -= 10
    return max(0, min(saving, 50))


def estimate_carbon(farm_size, crop):
    factors = {"Maize":0.6,"Rice":0.8,"Cassava":0.5,"Millet":0.4}
    return round(farm_size * factors.get(crop,0.5),2)


def vegetation_health():
    ndvi = round(random.uniform(0.2,0.8),2)
    if ndvi > 0.6:
        return ndvi, "Healthy vegetation"
    elif ndvi > 0.4:
        return ndvi, "Moderate vegetation"
    return ndvi, "Poor vegetation"


def estimate_water_usage(method, frequency, farm_size):
    base = {"Rain-fed":0,"Manual (bucket)":200,"Small pump":800,"Large pump":2000}
    freq = {"Rarely":0.5,"Weekly":1,"2-3 times/week":2,"Daily":4}
    return base.get(method,200) * freq.get(frequency,1) * farm_size


def map_to_pump_type(method):
    return {"Manual (bucket)":"manual","Small pump":"electric","Large pump":"diesel"}.get(method,"manual")


def calculate_carbon_credits(method, frequency, farm_size, reduction_percent):
    factors = {"diesel":2.68,"electric":0.5,"manual":0.0}
    water = estimate_water_usage(method, frequency, farm_size)
    pump = map_to_pump_type(method)
    saved = (water * reduction_percent/100) * factors[pump] / 1000
    credits = saved / 1000
    return {"water_usage":round(water,2),"emission_savings":round(saved,2),"carbon_credits":round(credits,4)}

# ---------------------------
# PAGE CONFIG
# ---------------------------

st.set_page_config(page_title="TerraSense AI", page_icon="🌱", layout="wide")

# ---------------------------
# SIDEBAR
# ---------------------------

st.sidebar.title("🌱 Farm Setup")

# Farmer Registration moved here
st.sidebar.subheader("👩‍🌾 Register Farmer")

name = st.sidebar.text_input("Name")
location_input = st.sidebar.text_input("Location")
crop_input = st.sidebar.text_input("Crop")

if st.sidebar.button("Register"):
    new = pd.DataFrame([[name,location_input,crop_input]],columns=["Name","Location","Crop"])
    if os.path.exists("farmers.csv"):
        df = pd.read_csv("farmers.csv")
        df = pd.concat([df,new],ignore_index=True)
    else:
        df = new
    df.to_csv("farmers.csv",index=False)
    st.sidebar.success("Registered!")


crop = st.sidebar.selectbox("Select Crop",["Maize","Rice","Cassava","Millet"])
farm_size = st.sidebar.number_input("Farm Size (hectares)",0.1,100.0,1.0)



# ---------------------------
# MAIN UI
# ---------------------------

st.title("TerraSense AI 🌱")
st.subheader("AI-powered irrigation, climate and carbon insights")

col1, col2 = st.columns([1,2])

location = streamlit_geolocation()

if location and location["latitude"]:
    lat, lon = location["latitude"], location["longitude"]
else:
    lat, lon = 7.38, 3.93

with col2:
    m = folium.Map(location=[lat, lon], zoom_start=13)
    st_folium(m)

# ---------------------------
# SEASON
# ---------------------------

month = datetime.datetime.now().month
season = "Dry Season" if month in [11,12,1,2,3] else "Rainy Season"

# ---------------------------
# ANALYZE FARM
# ---------------------------

if st.button("Analyze Farm"):

    temp, rain = get_weather_data(lat, lon)
    humidity = random.randint(40,80)
    soil = 0.6

    reduction = estimate_ai_water_saving(rain, temp, soil)

    # Rain forecast simulation
    total_rain = rain * 5
    time_to_rain = random.randint(1,72)

    # Crop status logic (RESTORED)
    if total_rain < 5 and humidity < 60:
        crop_status = "High Water Stress"
        advice = "Irrigate immediately"
    elif total_rain < 10:
        crop_status = "Moderate Water Stress"
        advice = "Irrigate within 2–3 days"
    else:
        crop_status = "Healthy"
        advice = "No irrigation needed"

    st.subheader("Farm Analysis Results")

    st.metric("Crop Status", crop_status)
    st.metric("5-Day Rainfall Forecast", f"{total_rain:.2f} mm")
    st.warning(advice)

    st.info(f"🤖 AI Water Saving: {reduction}%")

    # Rain prediction (moved correctly)
    st.subheader("Next Rain Prediction")

    if time_to_rain <= 3:
        st.success("Rain expected within 3 hours")
    elif time_to_rain <= 24:
        st.success(f"Rain expected in {time_to_rain} hours")
    else:
        st.info(f"Rain expected in {time_to_rain/24:.1f} days")

    # NDVI restored
    ndvi, status = vegetation_health()
    st.metric("NDVI", ndvi)
    st.write(status)

    # Carbon
    carbon = estimate_carbon(farm_size, crop)
    st.metric("Carbon Stored", f"{carbon} tons CO₂")

    # Climate score
    score = min(int((carbon*10)+(total_rain*2)),100)
    st.metric("Climate Score", score)

# ---------------------------
# CARBON DASHBOARD
# ---------------------------

st.header("🌱 Carbon Credit Dashboard")

method = st.selectbox("Irrigation Method",["Rain-fed","Manual (bucket)","Small pump","Large pump"])
freq = st.selectbox("Frequency",["Rarely","Weekly","2-3 times/week","Daily"])

if st.button("Calculate Impact"):

    temp, rain = get_weather_data(lat, lon)
    soil = 0.5
    reduction = estimate_ai_water_saving(rain, temp, soil)

    result = calculate_carbon_credits(method, freq, farm_size, reduction)

    st.metric("Water Use", result["water_usage"])
    st.metric("Emissions Saved", result["emission_savings"])
    st.metric("Carbon Credits", result["carbon_credits"])

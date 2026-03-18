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
        data = requests.get(url).json()
        return data["current"]["temperature_2m"], data["current"]["precipitation"]
    except:
        return None, None


# ✅ NEW: REAL FORECAST FUNCTION (FIXES YOUR PROBLEM)
def get_forecast_data(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=precipitation"
    try:
        data = requests.get(url).json()
        rain_data = data["hourly"]["precipitation"]

        total_rain = sum(rain_data[:40])  # ~5 days
        time_to_rain = None

        for i, rain in enumerate(rain_data):
            if rain > 0:
                time_to_rain = i
                break

        return total_rain, time_to_rain

    except:
        return 0, None

def estimate_ai_water_saving(rainfall, temperature, soil_moisture):
    saving = 15  # baseline

    if rainfall > 5:
        saving += 15

    if soil_moisture > 0.5:
        saving += 20

    if temperature > 30:
        saving -= 5

    return max(5, min(saving, 50))


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
    base = {
        "Rain-fed": 0,
        "Manual (bucket)": 500,
        "Small pump": 2000,
        "Large pump": 5000
    }

frequency_map = {
    "Rarely": 20,
    "Weekly": 52,
    "2-3 times/week": 130,
    "Daily": 365
}
return base.get(method, 500) * freq.get(frequency, 1) * farm_size

def map_to_pump_type(method):
    return {"Manual (bucket)":"manual","Small pump":"electric","Large pump":"diesel"}.get(method,"manual")

def calculate_carbon_credits(method, frequency, farm_size, reduction_percent):

    emission_factors = {
        "diesel": 2.68,
        "electric": 0.5,
        "manual": 0.0
    }

    frequency_map = {
        "Rarely": 20,
        "Weekly": 52,
        "2-3 times/week": 130,
        "Daily": 365
    }

    water = estimate_water_usage(method, frequency, farm_size)
    pump = map_to_pump_type(method)

    saved_per_cycle = (water * reduction_percent/100) * emission_factors[pump] / 1000

    cycles = frequency_map.get(frequency, 52)

    annual_saved = saved_per_cycle * cycles
    annual_credits = annual_saved / 1000

    return {
        "water_usage": round(water, 2),
        "emission_savings": round(annual_saved, 2),
        "carbon_credits": round(annual_credits, 4)
    }


# ---------------------------
# PAGE CONFIG
# ---------------------------

st.set_page_config(page_title="TerraSense AI", page_icon="🌱", layout="wide")

# ---------------------------
# SIDEBAR
# ---------------------------

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

st.sidebar.title("🌱 Farm Setup")

crop = st.sidebar.selectbox("Select Crop",["Maize","Rice","Cassava","Millet"])
farm_size = st.sidebar.number_input("Farm Size (hectares)",0.1,100.0,1.0)

# Farmer Registration (moved)


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
    total_rain, time_to_rain = get_forecast_data(lat, lon)

    humidity = random.randint(40,80)
    soil = 0.6

    reduction = estimate_ai_water_saving(rain, temp, soil)

    # ✅ FIXED IRRIGATION LOGIC
    if time_to_rain is not None and time_to_rain <= 12:
        crop_status = "Rain Expected Soon"
        advice = "Delay irrigation, rain expected shortly"

    elif time_to_rain is None:
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

    # ✅ FIXED RAIN PREDICTION (CONSISTENT NOW)

total_rain, time_to_rain = get_forecast_data(lat, lon)
st.subheader("Next Rain Prediction")

if time_to_rain is not None:

    if time_to_rain <= 3:
        st.success("🌧 Rain expected within 3 hours")

    elif time_to_rain <= 24:
        st.success(f"🌧 Rain expected in {time_to_rain} hours")

    elif time_to_rain <= 72:
        st.info(f"🌧 Rain expected in {time_to_rain/24:.1f} days")

    else:
        st.warning("🌧 Rain is several days away")

else:
    st.error("☀️ No rainfall expected in the next 5 days — irrigation is important")
    

    # NDVI
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

    emissions_kg = result["emission_savings"]
    emissions_tons = emissions_kg / 1000

    carbon_price = 10
    value = emissions_tons * carbon_price

    st.metric("Water Use", f"{result['water_usage']:.0f} L")
    st.metric("Emissions Saved", f"{emissions_kg:.2f} kg CO₂")
    st.metric("Annual Carbon Credits", f"{emissions_tons:.4f} tons")
    st.metric("Estimated Value", f"${value:.2f}")


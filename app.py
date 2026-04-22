from flask import Flask, request, jsonify
import requests
import random
import datetime

app = Flask(__name__)

# ---------------------------
# FUNCTIONS (from your code)
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
    return {
        "water_usage": round(water,2),
        "emission_savings": round(saved,2),
        "carbon_credits": round(credits,4)
    }

# ---------------------------
# ROUTES
# ---------------------------

@app.route("/")
def home():
    return "🌱 TerraSense API is running"

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json

    lat = data.get("lat", 7.38)
    lon = data.get("lon", 3.93)
    crop = data.get("crop", "Maize")
    farm_size = data.get("farm_size", 1)

    temp, rain = get_weather_data(lat, lon)
    humidity = random.randint(40,80)
    soil = 0.6

    reduction = estimate_ai_water_saving(rain, temp, soil)

    total_rain = rain * 5 if rain else 0

    if total_rain < 5 and humidity < 60:
        crop_status = "High Water Stress"
        advice = "Irrigate immediately"
    elif total_rain < 10:
        crop_status = "Moderate Water Stress"
        advice = "Irrigate within 2–3 days"
    else:
        crop_status = "Healthy"
        advice = "No irrigation needed"

    ndvi, status = vegetation_health()
    carbon = estimate_carbon(farm_size, crop)

    score = min(int((carbon*10)+(total_rain*2)),100)

    return jsonify({
        "crop_status": crop_status,
        "advice": advice,
        "rain_forecast": total_rain,
        "temperature": temp,
        "ai_water_saving": reduction,
        "ndvi": ndvi,
        "vegetation_status": status,
        "carbon": carbon,
        "climate_score": score
    })

@app.route("/carbon", methods=["POST"])
def carbon():
    data = request.json

    method = data["method"]
    freq = data["frequency"]
    farm_size = data["farm_size"]

    temp, rain = get_weather_data(7.38, 3.93)
    soil = 0.5

    reduction = estimate_ai_water_saving(rain, temp, soil)

    result = calculate_carbon_credits(method, freq, farm_size, reduction)

    return jsonify(result)

# ---------------------------
# RUN
# ---------------------------

if __name__ == "__main__":
    app.run()
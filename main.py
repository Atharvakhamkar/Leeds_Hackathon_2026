import pandas as pd
import joblib
import requests
import datetime
import os

# --- 1. LIVE DATA FETCHING ---
def get_live_external_factors(city, weather_key, news_key):
    w_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_key}"
    try:
        w_res = requests.get(w_url).json()
        condition = w_res['weather'][0]['main'] if w_res.get("cod") == 200 else "Clear"
    except Exception:
        condition = "Data_Unavailable"
    
    n_url = f"https://newsapi.org/v2/everything?q=supply+chain+strike&apiKey={news_key}"
    try:
        n_res = requests.get(n_url).json()
        news_count = n_res.get("totalResults", 0)
    except Exception:
        news_count = 0
    
    return condition, news_count

# --- 2. ENHANCED DOMINO CALCULATOR ---
def calculate_compound_risk(model, city, w_key, n_key, cargo_value):
    weather, news = get_live_external_factors(city, w_key, n_key)
    
    # We use high-priority defaults for the simulation
    test_case = pd.DataFrame([{
        "supplier_reliability_score": 0.85,
        "warehouse_inventory_level": 150,
        "order_quantity": 400,
        "shipping_distance_km": 2000,
        "processing_time_hours": 24,
        "shipping_method": "Sea",
        "weather_condition": "Clear",
        "order_priority": "High"
    }])
    
    base_risk = model.predict_proba(test_case)[0, 1]
    
    # Domino Effect Multipliers
    w_mult = 1.6 if weather in ["Storm", "Rain", "Thunderstorm"] else 1.0
    n_mult = 1.4 if news > 100 else 1.0
    
    final_risk = min(0.99, base_risk * w_mult * n_mult)
    
    # NEW: Financial Impact Calculation
    financial_exposure = cargo_value * final_risk
    
    return weather, news, base_risk, final_risk, financial_exposure

# --- 3. PROFESSIONAL LOGGING ---
def log_exception(order_id, city, total_risk, news_count, exposure):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if total_risk > 0.60:
        status = "CRITICAL_ACTION_REQUIRED"
    elif total_risk > 0.45:
        status = "ELEVATED_MONITORING"
    else:
        status = "OPERATIONAL_NORMAL"
    
    log_entry = (
        f"TIME: {timestamp} | ID: {order_id} | NODE: {city.upper()} | "
        f"RISK: {total_risk:.2%} | EXPOSURE: ${exposure:,.2f} | STATUS: {status}\n"
    )
    
    with open("exception_logs.txt", "a", encoding="utf-8") as f:
        f.write(log_entry)

# --- 4. EXECUTION (GLOBAL MANIFEST) ---
if __name__ == "__main__":
    W_KEY = "4687faffc0a3f2fb98e999a0a6e4eb64"
    N_KEY = "955f28af7c774034badfadcbd4cadf8f"
    
    # Ensure Excel library is installed: pip install openpyxl
    if os.path.exists("delay_risk_model.joblib") and os.path.exists("shipments_db.xlsx"):
        model = joblib.load("delay_risk_model.joblib")
        manifest = pd.read_excel("shipments_db.xlsx")
    else:
        print("FATAL_ERROR: Required files (model or Excel manifest) missing.")
        exit()
    
    print("INITIALIZING GLOBAL RISK SCAN...")
    print("-" * 65)
    print(f"{'ORDER_ID':<12} | {'CITY':<12} | {'RISK':<8} | {'EXPOSURE':<12}")
    print("-" * 65)

    for _, shipment in manifest.iterrows():
        w, n, base, total, exposure = calculate_compound_risk(
            model, shipment['destination'], W_KEY, N_KEY, shipment['cargo_value']
        )
        
        print(f"{shipment['order_id']:<12} | {shipment['destination']:<12} | {total:>7.1%} | ${exposure:>10,.2f}")
        
        log_exception(shipment['order_id'], shipment['destination'], total, n, exposure)

    print("-" * 65)
    print("SCAN COMPLETE: Global Exceptions Logged.")
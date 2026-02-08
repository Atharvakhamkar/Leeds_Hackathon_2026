import requests

# --- CONFIGURATION ---
WEATHER_KEY = "4687faffc0a3f2fb98e999a0a6e4eb64"
NEWS_KEY = "955f28af7c774034badfadcbd4cadf8f"
CITY = "Rotterdam" # One of Europe's biggest ports

def test_intelligence():
    print(f"🌐 Accessing Global Data for {CITY}...")
    
    # 1. TEST WEATHER API
    w_url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={WEATHER_KEY}"
    w_res = requests.get(w_url).json()
    
    if w_res.get("cod") == 200:
        condition = w_res['weather'][0]['main']
        print(f"✅ Weather Verified: {condition}")
    else:
        print(f"❌ Weather API Error: {w_res.get('message')}")

    # 2. TEST NEWS API
    n_url = f"https://newsapi.org/v2/everything?q=port+strike&apiKey={NEWS_KEY}"
    n_res = requests.get(n_url).json()
    
    if n_res.get("status") == "ok":
        articles = n_res.get("totalResults", 0)
        print(f"✅ News Verified: {articles} potential disruption events found.")
    else:
        print(f"❌ News API Error: {n_res.get('message')}")

if __name__ == "__main__":
    test_intelligence()
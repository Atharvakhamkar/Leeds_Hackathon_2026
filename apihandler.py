import requests

def get_live_data(city="Shanghai"):
    """
    This is your 'Nervous System.' It reaches out to the world.
    """
    # 1. Weather API (Example: OpenWeatherMap)
    # Goal: Check if there is a 'Storm' or 'Typhoon'
    weather_condition = "Clear" # Placeholder until you add your API Key
    
    # 2. News API (Example: NewsAPI.org)
    # Goal: Search for keywords like 'Port Strike' or 'Trade War'
    news_risk_score = 0.2 # Default low risk
    
    return weather_condition, news_risk_score
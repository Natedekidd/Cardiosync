"""
CardioSync - Environmental Data API Client
Fetches air quality and weather data from OpenWeatherMap
"""

import requests
import streamlit as st

API_KEY = "e8678eb40cf1e210d88c05b59666b41f"  

def get_air_quality(city):
    """
    Fetch air quality data for a given city
    
    Args:
        city (str): City name (e.g., "Lagos, Nigeria" or "London")
    
    Returns:
        dict: Air quality data or None if failed
    """
    try:
        # Geocoding API to get coordinates from city name
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
        geo_response = requests.get(geo_url, timeout=5)
        
        if geo_response.status_code != 200:
            return None
        
        geo_data = geo_response.json()
        
        if not geo_data:
            return None
        
        lat = geo_data[0]['lat']
        lon = geo_data[0]['lon']
        
        # Air Pollution API
        air_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        air_response = requests.get(air_url, timeout=5)
        
        if air_response.status_code != 200:
            return None
        
        air_data = air_response.json()
        
        # Weather API for temperature
        weather_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        weather_response = requests.get(weather_url, timeout=5)
        
        weather_data = weather_response.json() if weather_response.status_code == 200 else None
        
        # Extract relevant data
        components = air_data['list'][0]['components']
        aqi = air_data['list'][0]['main']['aqi']
        
        result = {
            'city': city,
            'aqi': aqi,  # 1=Good, 2=Fair, 3=Moderate, 4=Poor, 5=Very Poor
            'pm2_5': components.get('pm2_5', 0),  # Fine particles
            'pm10': components.get('pm10', 0),    # Coarse particles
            'no2': components.get('no2', 0),      # Nitrogen dioxide
            'o3': components.get('o3', 0),        # Ozone
            'co': components.get('co', 0),        # Carbon monoxide
        }
        
        # Add weather data if available
        if weather_data:
            result['temperature'] = weather_data['main']['temp']
            result['humidity'] = weather_data['main']['humidity']
        
        return result
        
    except requests.exceptions.Timeout:
        st.warning("⏱️ API request timed out. Using default environmental data.")
        return None
    except requests.exceptions.RequestException as e:
        st.warning(f"⚠️ Could not fetch environmental data: {str(e)}")
        return None
    except (KeyError, IndexError) as e:
        st.warning("⚠️ Unexpected API response format.")
        return None


def calculate_environmental_risk(air_quality_data):
    """
    Calculate cardiovascular risk contribution from environmental factors
    
    Args:
        air_quality_data (dict): Air quality data from API
    
    Returns:
        float: Environmental risk factor (percentage points)
    """
    if not air_quality_data:
        return 0
    
    risk = 0
    
    # PM2.5 is the most important factor for cardiovascular health
    pm25 = air_quality_data.get('pm2_5', 0)
    
    if pm25 > 75:  # Very unhealthy (Beijing bad days)
        risk += 12
    elif pm25 > 55:  # Unhealthy (Lagos typical)
        risk += 8
    elif pm25 > 35:  # Moderate
        risk += 4
    elif pm25 > 12:  # Fair
        risk += 1
    # else: Good air quality, no added risk
    
    # NO2 (traffic pollution) - secondary factor
    no2 = air_quality_data.get('no2', 0)
    if no2 > 200:  # High traffic pollution
        risk += 2
    elif no2 > 100:
        risk += 1
    
    # Temperature stress (extreme heat affects cardiovascular system)
    temp = air_quality_data.get('temperature')
    if temp and temp > 35:  # Extreme heat
        risk += 1.5
    elif temp and temp > 30:  # High heat
        risk += 0.5
    
    return round(risk, 1)


def get_aqi_description(aqi):
    """
    Get human-readable AQI description
    
    Args:
        aqi (int): Air Quality Index (1-5)
    
    Returns:
        tuple: (description, color, emoji)
    """
    aqi_map = {
        1: ("Good", "green", "🟢"),
        2: ("Fair", "lightgreen", "🟡"),
        3: ("Moderate", "yellow", "🟠"),
        4: ("Poor", "orange", "🔴"),
        5: ("Very Poor", "red", "🔴")
    }
    
    return aqi_map.get(aqi, ("Unknown", "gray", "⚪"))


def get_pm25_description(pm25):
    """
    Get health impact description for PM2.5 levels
    
    Args:
        pm25 (float): PM2.5 concentration in μg/m³
    
    Returns:
        str: Health impact description
    """
    if pm25 <= 12:
        return "Excellent air quality - minimal cardiovascular risk"
    elif pm25 <= 35:
        return "Moderate air quality - slight increase in CVD risk"
    elif pm25 <= 55:
        return "Unhealthy air - notable increase in cardiovascular risk"
    elif pm25 <= 75:
        return "Unhealthy air - significant CVD risk increase"
    else:
        return "Very unhealthy air - major cardiovascular health concern"


def display_environmental_data(air_quality_data):
    """
    Display environmental data in Streamlit UI
    
    Args:
        air_quality_data (dict): Air quality data from API
    """
    if not air_quality_data:
        st.info("💡 Enter your location to see environmental health impacts")
        return
    
    st.markdown("### 🌍 Environmental Health Assessment")
    
    # Main metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        aqi_desc, aqi_color, aqi_emoji = get_aqi_description(air_quality_data['aqi'])
        st.metric(
            "Air Quality Index",
            f"{aqi_emoji} {aqi_desc}",
            help="Overall air quality rating (1=Best, 5=Worst)"
        )
    
    with col2:
        pm25 = air_quality_data.get('pm2_5', 0)
        st.metric(
            "PM2.5 Level",
            f"{pm25:.1f} μg/m³",
            help="Fine particles that affect cardiovascular health"
        )
    
    with col3:
        env_risk = calculate_environmental_risk(air_quality_data)
        st.metric(
            "Environmental Risk",
            f"+{env_risk}%",
            help="Contribution to cardiovascular risk from environment"
        )
    
    # Detailed breakdown
    with st.expander("🔍 Detailed Environmental Analysis"):
        st.markdown(f"""
        **Location:** {air_quality_data['city']}
        
        **Air Pollutants:**
        - PM2.5 (Fine Particles): {air_quality_data.get('pm2_5', 0):.1f} μg/m³
        - PM10 (Coarse Particles): {air_quality_data.get('pm10', 0):.1f} μg/m³
        - NO₂ (Nitrogen Dioxide): {air_quality_data.get('no2', 0):.1f} μg/m³
        - O₃ (Ozone): {air_quality_data.get('o3', 0):.1f} μg/m³
        
        **Climate Factors:**
        - Temperature: {air_quality_data.get('temperature', 'N/A')}°C
        - Humidity: {air_quality_data.get('humidity', 'N/A')}%
        
        **Health Impact:**
        {get_pm25_description(air_quality_data.get('pm2_5', 0))}
        """)
    
    # Recommendations
    pm25 = air_quality_data.get('pm2_5', 0)
    if pm25 > 35:
        st.warning("""
        ⚠️ **Environmental Risk Mitigation:**
        - Consider using HEPA air purifiers indoors
        - Exercise in early morning when pollution is lower
        - Wear N95 masks during outdoor activities
        - Monitor AQI before planning outdoor exercise
        - Consider relocating to areas with better air quality (long-term)
        """)
    elif pm25 > 12:
        st.info("""
        💡 **Environmental Health Tips:**
        - Monitor air quality on high pollution days
        - Exercise indoors when AQI is elevated
        - Keep windows closed during high traffic hours
        """)


# Demo/test function
if __name__ == "__main__":
    # Test with Lagos
    print("Testing API with Lagos, Nigeria...")
    data = get_air_quality("Lagos, Nigeria")
    
    if data:
        print(f"\n✅ Success!")
        print(f"AQI: {data['aqi']}")
        print(f"PM2.5: {data['pm2_5']} μg/m³")
        print(f"Environmental Risk: +{calculate_environmental_risk(data)}%")
    else:
        print("\n❌ Failed to fetch data. Check your API key!")
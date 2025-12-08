import datetime
from zoneinfo import ZoneInfo, available_timezones
from google.adk.agents import Agent
import requests
from typing import Optional

# 城市到時區的映射（常見城市）
CITY_TIMEZONE_MAP = {
    "taipei": "Asia/Taipei",
    "tokyo": "Asia/Tokyo",
    "new york": "America/New_York",
    "london": "Europe/London",
    "paris": "Europe/Paris",
    "berlin": "Europe/Berlin",
    "sydney": "Australia/Sydney",
    "beijing": "Asia/Shanghai",
    "shanghai": "Asia/Shanghai",
    "hong kong": "Asia/Hong_Kong",
    "singapore": "Asia/Singapore",
    "seoul": "Asia/Seoul",
    "los angeles": "America/Los_Angeles",
    "chicago": "America/Chicago",
    "toronto": "America/Toronto",
    "vancouver": "America/Vancouver",
    "dubai": "Asia/Dubai",
    "mumbai": "Asia/Kolkata",
    "bangkok": "Asia/Bangkok",
}


def get_weather(city: str, country_code: Optional[str] = None) -> dict:
    """Retrieves the current weather report (temperature, conditions, humidity) for a specified city.
    
    Use this tool when the user asks about:
    - Weather conditions (sunny, rainy, cloudy, etc.)
    - Temperature or how hot/cold it is
    - Humidity levels
    - General climate information

    Args:
        city (str): The name of the city for which to retrieve the weather report.
        country_code (str, optional): ISO 3166 country code (e.g., 'US', 'TW', 'JP') for disambiguation.

    Returns:
        dict: status and result or error msg.
    """
    try:
        # 使用 OpenWeatherMap API (需要申請免費 API Key)
        # 註冊網址: https://openweathermap.org/api
        api_key = "YOUR_API_KEY_HERE"  # 請替換成您的 API Key
        
        # 如果沒有設定 API Key，返回模擬數據
        if api_key == "YOUR_API_KEY_HERE":
            return {
                "status": "success",
                "report": (
                    f"Weather service is not configured. "
                    f"Please get a free API key from https://openweathermap.org/api "
                    f"and update the 'api_key' in get_weather function. "
                    f"(Mock data: {city} is currently sunny, 22°C)"
                ),
            }
        
        # 構建查詢參數
        query = f"{city},{country_code}" if country_code else city
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": query,
            "appid": api_key,
            "units": "metric",  # 使用攝氏度
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            description = data["weather"][0]["description"]
            humidity = data["main"]["humidity"]
            
            report = (
                f"The weather in {city.title()} is {description} with a temperature "
                f"of {temp}°C (feels like {feels_like}°C). Humidity: {humidity}%."
            )
            return {"status": "success", "report": report}
        elif response.status_code == 404:
            return {
                "status": "error",
                "error_message": f"City '{city}' not found. Please check the spelling.",
            }
        else:
            return {
                "status": "error",
                "error_message": f"Unable to retrieve weather data. API returned status {response.status_code}.",
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error_message": f"Network error occurred: {str(e)}",
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error retrieving weather: {str(e)}",
        }


def get_current_time(city: str) -> dict:
    """Returns the current local time and date in a specified city.
    
    Use this tool when the user asks about:
    - What time is it in a city
    - Current time or clock time
    - Time zone information
    - Date and time together

    Args:
        city (str): The name of the city for which to retrieve the current time.

    Returns:
        dict: status and result or error msg.
    """
    try:
        city_lower = city.lower()
        
        # 查找時區
        tz_identifier = CITY_TIMEZONE_MAP.get(city_lower)
        
        # 如果找不到，嘗試直接使用城市名作為時區（如 Asia/Taipei）
        if not tz_identifier:
            # 嘗試常見的時區格式
            possible_timezones = [
                f"Asia/{city.replace(' ', '_').title()}",
                f"America/{city.replace(' ', '_').title()}",
                f"Europe/{city.replace(' ', '_').title()}",
                f"Australia/{city.replace(' ', '_').title()}",
            ]
            
            available = available_timezones()
            for tz in possible_timezones:
                if tz in available:
                    tz_identifier = tz
                    break
        
        if not tz_identifier:
            return {
                "status": "error",
                "error_message": (
                    f"Sorry, I don't have timezone information for '{city}'. "
                    f"Supported cities include: {', '.join(list(CITY_TIMEZONE_MAP.keys())[:10])}..."
                ),
            }
        
        tz = ZoneInfo(tz_identifier)
        now = datetime.datetime.now(tz)
        report = (
            f'The current time in {city.title()} is {now.strftime("%Y-%m-%d %H:%M:%S %Z (UTC%z)")}'
        )
        return {"status": "success", "report": report}
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error retrieving time: {str(e)}",
        }


root_agent = Agent(
    name="weather_time_agent",
    model="gemini-2.5-flash",
    description=(
        "Agent to answer questions about the time and weather in a city."
    ),
    instruction=(
        "You are a helpful agent who can answer user questions about the time and weather in a city."
    ),
    tools=[get_weather, get_current_time],
)
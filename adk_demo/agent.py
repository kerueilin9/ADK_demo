import datetime
import logging
from pathlib import Path
from zoneinfo import ZoneInfo, available_timezones
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
import requests
from typing import Optional

# ============================================================================
# LOGGING SETUP - 設定日誌記錄
# ============================================================================

log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

logger = logging.getLogger("adk_monitor")
logger.setLevel(logging.INFO)

logger.handlers.clear()

log_file = log_dir / f"agent_{datetime.datetime.now().strftime('%Y%m%d')}.log"
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.INFO)

# 設定 log 格式
formatter = logging.Formatter(
    '%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)

# 加入 handler
logger.addHandler(file_handler)

logger.info(f"{'='*60}")
logger.info(f"ADK Agent 監控日誌啟動 - Log 檔案: {log_file}")
logger.info(f"{'='*60}")

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


# ============================================================================
# CALLBACKS - 監控與追蹤
# ============================================================================

def before_model_callback(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> None:
    """在 LLM 呼叫前執行 - 記錄輸入內容"""
    logger.info("="*60)
    logger.info(f"[BEFORE MODEL] Agent: {callback_context.agent_name}")
    
    # 顯示用戶輸入
    try:
        if hasattr(llm_request, 'contents') and llm_request.contents:
            latest_content = llm_request.contents[-1]
            if hasattr(latest_content, 'parts') and latest_content.parts:
                text = latest_content.parts[0].text if hasattr(latest_content.parts[0], 'text') else str(latest_content.parts[0])
                logger.info(f"User Input: {text[:100]}...")
    except Exception as e:
        logger.debug(f"Error logging user input: {e}")
    
    # 顯示可用工具
    try:
        if hasattr(callback_context, 'agent') and hasattr(callback_context.agent, 'tools'):
            tool_names = [tool.__name__ if callable(tool) else str(tool) for tool in callback_context.agent.tools]
            logger.info(f"Available Tools: {', '.join(tool_names)}")
    except Exception as e:
        logger.debug(f"Error logging tools: {e}")
    
    logger.info("="*60)


def after_model_callback(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> None:
    """在 LLM 回應後執行 - 記錄輸出內容和 Token 使用"""
    logger.info("="*60)
    logger.info(f"[AFTER MODEL] Agent: {callback_context.agent_name}")
    
    # 顯示模型回應
    try:
        if hasattr(llm_response, 'candidates') and llm_response.candidates:
            candidate = llm_response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content and hasattr(candidate.content, 'parts'):
                # 檢查是否有文字回應
                for part in candidate.content.parts:
                    if hasattr(part, 'text') and part.text:
                        logger.info(f"Model Response: {part.text[:150]}...")
                    # 檢查是否有工具呼叫
                    if hasattr(part, 'function_call') and part.function_call:
                        logger.info(f"Tool Call: {part.function_call.name}")
                        logger.info(f"Arguments: {dict(part.function_call.args)}")
    except Exception as e:
        logger.debug(f"Error logging model response: {e}")
    
    # 顯示 Token 使用統計
    try:
        if hasattr(llm_response, 'usage_metadata') and llm_response.usage_metadata:
            usage = llm_response.usage_metadata
            logger.info(f"Token Usage:")
            logger.info(f"   - Input: {usage.prompt_token_count}")
            logger.info(f"   - Output: {usage.candidates_token_count}")
            logger.info(f"   - Total: {usage.total_token_count}")
    except Exception as e:
        logger.debug(f"Error logging token usage: {e}")
    
    logger.info("="*60)

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
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
)
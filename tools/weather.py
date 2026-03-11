import requests
import os
from .base import BaseTool
from dotenv import load_dotenv
load_dotenv()

class WeatherTool(BaseTool):
    """
    WeatherTool fetches current weather data
    from OpenWeatherMap API.

    It does NOT generate natural language.
    It returns structured JSON data.
    """

    name = "weather"
    description = "Get current weather information for a city"

    def __init__(self, WEATHER_URL):
        """
        api_key is required to access OpenWeather API.
        """
        # self.api_key = os.getenv("WEATHER_URL")
        self.weather_url = WEATHER_URL

    def run(self, city: str):

        # 1️⃣ Get coordinates using geocoding API
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"

        geo_response = requests.get(geo_url, params={
            "name": city,
            "count": 1
        })

        if geo_response.status_code != 200:
            return {"error": "Failed to fetch location"}

        geo_data = geo_response.json()

        if "results" not in geo_data:
            return {"error": "City not found"}

        latitude = geo_data["results"][0]["latitude"]
        longitude = geo_data["results"][0]["longitude"]

        # 2️⃣ Use your main forecast URL (passed from main)
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": True
        }

        response = requests.get(self.weather_url, params=params)

        if response.status_code != 200:
            return {"error": "Unable to fetch weather"}

        data = response.json()

        return {
            "city": city,
            "temperature": data["current_weather"]["temperature"],
            "windspeed": data["current_weather"]["windspeed"]
        }
if __name__ == "__main__":
    # weather_url = os.getenv("WEATHER_URL")
    weather_url = "https://api.open-meteo.com/v1/forecast"
    tool = WeatherTool(weather_url)
    # tool = WeatherTool()
    result = tool.run("Mumbai")

    print("Weather Tool Test Result:")
    print(result)
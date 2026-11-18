import requests
import time
import logging
import os

logger = logging.getLogger(__name__)

class WeatherAPIClient:
    """
    Client for the OpenWeatherMap current-weather API.
    """
    def __init__(self, api_key=None, base_url=None):
        self.api_key = api_key if api_key is not None else os.getenv("WEATHER_API_KEY")
        self.base_url = (
            base_url or os.getenv(
                "WEATHER_API_URL",
                "https://api.openweathermap.org/data/2.5"
            )
        ).rstrip("/")

    def get_current_weather(self, location, retries=3):
        """Fetch current weather for a location with automatic retries"""
        if not self.api_key:
            logger.error("Weather API key is not configured")
            return None

        params = {
            'q': location,
            'appid': self.api_key,
            'units': 'metric'
        }
        
        for attempt in range(retries):
            try:
                response = requests.get(f"{self.base_url}/weather", params=params, timeout=5)
                response.raise_for_status()
                return response.json()
            except requests.HTTPError as error:
                status_code = error.response.status_code if error.response else None
                logger.warning(
                    "Weather API returned HTTP %s for %s",
                    status_code,
                    location
                )
                if status_code is not None and status_code < 500:
                    return None
            except requests.RequestException as error:
                logger.warning(
                    "Weather API request attempt %s failed for %s (%s)",
                    attempt + 1,
                    location,
                    type(error).__name__
                )

            if attempt < retries - 1:
                time.sleep(2 ** attempt)

        logger.error("Weather API failed after %s attempts for %s", retries, location)
        return None

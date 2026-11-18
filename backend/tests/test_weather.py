import pytest
import requests
from flask import Flask
from backend.extensions import db
from backend.models import User, WeatherData, CropAdvisory, AdvisorySubscription
from backend.services.weather_service import WeatherService
from backend.services.advisory_engine import AdvisoryEngine
from backend.api.v1.weather import weather_bp


@pytest.fixture
def mock_weather_api(monkeypatch):
    calls = []
    weather_data = {
        'main': {'temp': 22, 'humidity': 65},
        'weather': [{'main': 'Clear', 'description': 'clear sky'}],
        'wind': {'speed': 5, 'deg': 90},
        'name': 'Test City',
    }

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return weather_data

    def fake_get(url, params, timeout):
        calls.append((url, params, timeout))
        return FakeResponse()

    monkeypatch.setenv("WEATHER_API_KEY", "test-weather-key")
    monkeypatch.setenv(
        "WEATHER_API_URL",
        "https://api.openweathermap.org/data/2.5"
    )
    monkeypatch.setattr(requests, "get", fake_get)
    return calls

@pytest.fixture
def test_app():
    test_app = Flask(__name__)
    test_app.config.update(
        TESTING=True,
        SECRET_KEY="weather-test-secret",
        SQLALCHEMY_DATABASE_URI="sqlite://",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    db.init_app(test_app)
    test_app.register_blueprint(weather_bp, url_prefix="/api/v1/weather")

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def test_client(test_app):
    with test_app.test_client() as client:
        with test_app.app_context():
            yield client

@pytest.fixture
def setup_user(test_app):
    with test_app.app_context():
        u = User(username='farmerweather', email='farmerweather@gmail.com')
        u.set_password("TestWeatherPass123")
        db.session.add(u)
        db.session.commit()
        return u.id

def test_weather_fetching_logic(test_client, mock_weather_api):
    # Test updating weather for a location
    weather = WeatherService.update_weather_for_location("Mumbai")
    assert weather is not None
    assert weather.location == "Mumbai"
    assert weather.temperature is not None
    assert weather.wind_speed == 18
    assert mock_weather_api[0][0] == "https://api.openweathermap.org/data/2.5/weather"
    assert mock_weather_api[0][1] == {
        'q': 'Mumbai',
        'appid': 'test-weather-key',
        'units': 'metric'
    }
    
    # Test caching/latest logic
    cached = WeatherService.get_latest_weather("Mumbai")
    assert cached.id == weather.id


def test_current_weather_api_route(test_client, mock_weather_api):
    response = test_client.get(
        "/api/v1/weather/current",
        query_string={"location": "Delhi"},
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["location"] == "Delhi"
    assert data["temperature"] == 22


def test_advisory_generation(setup_user, mock_weather_api, test_app):
    user_id = setup_user
    with test_app.app_context():
        # Ensure weather exists for the location
        WeatherService.update_weather_for_location("Delhi")
        
        advisory = AdvisoryEngine.generate_advisory(
            user_id=user_id,
            crop_name="Wheat",
            location="Delhi",
            soil_type="Alluvial",
            growth_stage="Seedling"
        )
        
        assert advisory is not None
        assert advisory.crop_name == "Wheat"
        assert "irrigat" in advisory.advisory_text.lower() or "alert" in advisory.advisory_text.lower()
        assert advisory.priority in ['Normal', 'High']

def test_subscription_workflow(setup_user, test_app):
    user_id = setup_user
    with test_app.app_context():
        sub = WeatherService.subscribe_user(user_id, "Rice", "Punjab")
        assert sub.is_active is True
        
        active_subs = WeatherService.get_active_subscriptions()
        assert len(active_subs) == 1
        assert active_subs[0].crop_name == "Rice"

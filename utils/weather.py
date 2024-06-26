import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry

def setup_openmeteo_client():
    """Setup the Open-Meteo API client with cache and retry on error."""
    cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    return openmeteo_requests.Client(session=retry_session)

def fetch_weather_data(client, latitude, longitude, start_date, end_date, timezone, variables):
    """Fetch weather data from Open-Meteo API."""
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "timezone": timezone,
        "hourly": variables
    }
    return client.weather_api(url, params=params)

def process_response(response):
    """Process the response and convert it to a DataFrame."""

    hourly = response.Hourly()
    data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        ),
        "outside_tmp": hourly.Variables(0).ValuesAsNumpy().astype(float),
        "outside_hum": hourly.Variables(1).ValuesAsNumpy().astype(float),
        "outside_rain": hourly.Variables(2).ValuesAsNumpy().astype(float),
        "outside_snowfall": hourly.Variables(3).ValuesAsNumpy().astype(float),
        "outside_wind_speed": hourly.Variables(4).ValuesAsNumpy().astype(float),
        "outside_pressure": hourly.Variables(5).ValuesAsNumpy().astype(float),
    }

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"]).dt.tz_convert('Europe/Berlin')
    df["hour"] = df["date"].dt.hour
    df["date"] = df["date"].dt.date.astype(object)

    for column in ["outside_tmp", "outside_hum", "outside_rain", "outside_snowfall", "outside_wind_speed", "outside_pressure"]:
        df[column] = df[column].astype(float)
    
    df["outside_tmp"] = df["outside_tmp"].round(3)
    df["outside_hum"] = df["outside_hum"].round(3)
    df["outside_rain"] = df["outside_rain"].round(3)
    df["outside_snowfall"] = df["outside_snowfall"].round(3)
    df["outside_wind_speed"] = df["outside_wind_speed"].round(3)
    df["outside_pressure"] = df["outside_pressure"].round(3)

    df = df[["date", "hour", "outside_tmp", "outside_hum", "outside_rain", "outside_snowfall", "outside_wind_speed", "outside_pressure"]]

    return df

def get_weather_with_api(latitude:float, longitude:float, start_date:str, end_date:str) -> pd.DataFrame:
    """Main function to fetch and process weather data."""
    openmeteo_client = setup_openmeteo_client()
    
    if not latitude:
        latitude = 49.014920
    if not longitude:
        longitude = 8.390050
    
    timezone = "Europe/Berlin"
    variables = "temperature_2m,relative_humidity_2m,rain,snowfall,wind_speed_10m,pressure_msl"

    responses = fetch_weather_data(openmeteo_client, latitude, longitude, start_date, end_date, timezone, variables)
    response = responses[0]
    hourly_dataframe = process_response(response)
  
    return hourly_dataframe

import astropy.coordinates
from loguru import logger
import requests
from src.config import AppConfig


def get_elevation(elevation_url: str, lat: float, lon: float) -> float:
	"""
	Fetches the elevation for the given latitude and longitude using the specified elevation API URL.

	Returns results in meters. 
	
	Raises an requests.RequestException if the request fails or if the response cannot be parsed.
	"""

	response = requests.get(elevation_url.format(lat=lat, lon=lon))

	if response.status_code != 200:
		logger.error(f"Failed to get elevation data: {response.status_code}")
		raise requests.RequestException(f"Failed to get elevation data: {response.status_code}")
	
	try:
		data = response.json()
	except requests.exceptions.JSONDecodeError as e:
		logger.error(f"Failed to parse elevation data: {e}")
		raise requests.RequestException(f"Failed to parse elevation data: {e}")

	return data["elevation"][0]


def get_Earth_Location(config: AppConfig, lat: float, lon: float) -> astropy.coordinates.EarthLocation:
	if config.general.use_elevation:
		elevation = get_elevation(str(config.endpoints.ELEVATION_URL), lat, lon)
	else:
		elevation = 0

	return astropy.coordinates.EarthLocation.from_geodetic(
		lon = lon,
		lat = lat,
		height = elevation
	)

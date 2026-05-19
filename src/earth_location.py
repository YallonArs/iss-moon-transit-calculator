import astropy.coordinates
import astropy.units as u
import aiohttp
from loguru import logger


async def get_elevation(lat: float, lon: float) -> float:
	async with aiohttp.ClientSession() as session:
		url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
		async with session.get(url) as response:
			if response.status != 200:
				logger.error(f"Failed to get elevation data: {response.status}")
				raise Exception(f"Failed to get elevation data: {response.status}")
			
			data = await response.json()
			return data['elevation'][0] * u.m


async def get_Earth_Location(lat: float, lon: float) -> astropy.coordinates.EarthLocation:
	elevation = await get_elevation(lat, lon)

	return astropy.coordinates.EarthLocation.from_geodetic(
		lon = lon,
		lat = lat,
		height = elevation
	)

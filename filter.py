import asyncio
from loguru import logger
from tqdm.asyncio import trange
from tqdm import tqdm

from datetime import datetime

import astropy.coordinates
from astropy.coordinates import Angle, SkyCoord, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u

from sgp4.api import Satrec

from src.coord_transform import *
from src.earth_location import get_Earth_Location
from src.parser import load_config
from src.tle import TLE, download_tle


app_config = load_config()


def get_satellite_position(tle: TLE, t: Time | None = None) -> SkyCoord:
	if t is None:
		t = Time.now()

	satellite = Satrec.twoline2rv(tle.s, tle.t)

	error_code, position, velocity = satellite.sgp4(t.jd1, t.jd2)
	
	if error_code != 0:
		logger.error(f"Error in SGP4 propagation: {error_code}")
		raise Exception(f"Error in SGP4 propagation: {error_code}")
	
	return SkyCoord(
		x = position[0] * u.km,
		y = position[1] * u.km,
		z = position[2] * u.km,
		v_x = velocity[0] * u.km / u.s,
		v_y = velocity[1] * u.km / u.s,
		v_z = velocity[2] * u.km / u.s,
		frame = astropy.coordinates.TEME,
		obstime = t,
		representation_type = 'cartesian'
	)


async def get_iss(t: Time | None = None) -> SkyCoord:
	if t is None:
		t = Time.now()

	tle = await download_tle(str(app_config.general.TLE_URL))
	
	return get_satellite_position(tle, t)


async def calculate_distance(t: Time, geo: EarthLocation) -> Angle:
	moon = get_body('moon', t)
	moon_altaz = transform_to_altaz(moon, geo)

	iss = await get_iss(t)

	iss_TETE = await transform_TEME_to_TETE(await get_iss(t), geo)
	iss_altaz = transform_to_altaz(iss_TETE, geo)

	angle = moon_altaz.separation(iss_altaz)

	return angle


async def _iteration(t: Time, geo: EarthLocation, file):
	angle = await calculate_distance(t, geo)

	if angle < 15 * u.degree:
		logger.info(f"ISS is close to the Moon! Angle: {angle:.2f}")
		await file.write(f"{t.iso} - {angle:.2f}\n")
	
	if angle < 0.25 * u.degree:
		logger.warning(f"ISS is very close to the Moon! Angle: {angle:.2f}")
		await file.write(f"{t.iso} - {angle:.2f}\n")

	# await file.write(f"{t.iso} - {angle:.2f}\n")



async def main():
	entries: list[tuple[Time, float]] = []

	with open("output.txt") as file:
		for line in tqdm(file.readlines()):
			datetime_str, elevation_str = line.strip().rstrip().split(" - ")
			datetime_obj = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S.%f")
			time_entry = Time(datetime_obj)
			distance_entry = float(elevation_str.removesuffix(" deg"))

			entries.append((time_entry, distance_entry))
	
	earth_location = await get_Earth_Location(app_config.coordinates.latitude, app_config.coordinates.longitude)

	selected_entries: list[tuple[Time, float]] = []
	for t, distance in tqdm(entries):
		moon = get_body('moon', t)
		moon_altaz = transform_to_altaz(moon, earth_location)
		if moon_altaz.alt > 0:
			selected_entries.append((t, distance))

	with open("output_filter.txt", "w") as file:
		for t, distance in selected_entries:
			file.write(f"{t.iso} - {distance:.2f}\n")

asyncio.run(main())

from typing import Iterable

import astropy
from loguru import logger

from astropy.coordinates import Angle, SkyCoord, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u

from tqdm import tqdm

import numpy as np
from sgp4.api import Satrec

from src.coord_transform import *
from src.earth_location import get_Earth_Location
from src.config import load_config
from src.tle import TLE, download_tle


config = load_config()


def get_iss(tle: TLE, t: Time) -> SkyCoord:
	satellite = Satrec.twoline2rv(tle.s, tle.t)

	error_code, position, velocity = satellite.sgp4_array(t.jd1, t.jd2)
	
	if error_code.any():
		logger.error(f"Error in SGP4 propagation: {error_code}")
		raise Exception(f"Error in SGP4 propagation: {error_code}")
	
	return SkyCoord(
		x = position[:, 0] * u.km,
		y = position[:, 1] * u.km,
		z = position[:, 2] * u.km,
		v_x = velocity[:, 0] * u.km / u.s,
		v_y = velocity[:, 1] * u.km / u.s,
		v_z = velocity[:, 2] * u.km / u.s,
		frame = astropy.coordinates.TEME,
		obstime = t,
		representation_type = 'cartesian'
	)


def calculate_distance(object1, object2, geo: EarthLocation) -> Angle:
	object1_altaz = transform_to_altaz(object1, geo)
	object2_altaz = transform_to_altaz(object2, geo)

	angle = object1_altaz.separation(object2_altaz)

	return angle


def calculate(tle: TLE, t: Time, geo: EarthLocation):
	moon = get_body("moon", t, geo)

	iss = get_iss(tle, t)
	iss_TETE = transform_TEME_to_TETE(iss, geo)

	return calculate_distance(iss_TETE, moon, geo)


def postprocess(angles: Iterable[Angle], ts: Iterable[Time], file):
	for angle, t in tqdm(zip(angles, ts)):
		# if angle < 15 * u.degree:
		# 	logger.info(f"ISS is close to the Moon! Angle: {angle:.2f}")
		# 	file.write(f"{t.iso} - {angle:.2f}\n")

		if angle < 0.25 * u.degree:
			logger.warning(f"ISS is very close to the Moon! Angle: {angle:.2f}")
			file.write(f"{t.iso} - {angle:.2f}\n")


def main():
	logger.info("Downloading TLE...")
	tle = download_tle(str(config.endpoints.TLE_URL))
	current_time = Time.now()

	logger.info("Getting Earth Location...")
	earth_location = get_Earth_Location(config, config.coordinates.latitude, config.coordinates.longitude)

	stop_seconds = (30 * u.day).to_value(u.second)
	logger.info("Building array of times...")
	times = current_time + np.arange(0, stop_seconds, 10) * u.second

	logger.info("Calculating angles...")
	angles = calculate(tle, times, earth_location)

	logger.info("Postprocessing results...")
	with open("output.txt", "w") as file:
		postprocess(angles, times, file)

	print(len(times))


	# with open("output.txt", "w") as file:
	# 	for i in range(0, len(times)):
	# 		t = time + times[i]
	# 		_iteration(t, earth_location, file)

if __name__ == "__main__":
	main()

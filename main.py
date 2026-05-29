from typing import Iterable

import astropy
from loguru import logger
from tqdm import tqdm
from multiprocessing import Pool
from functools import partial
from time import time
import sys

from astropy.coordinates import Angle, SkyCoord, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u

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


def calculate(t: Time, tle: TLE, geo: EarthLocation):
	moon = get_body("moon", t, geo)

	iss = get_iss(tle, t)
	iss_TETE = transform_TEME_to_TETE(iss, geo)

	return calculate_distance(iss_TETE, moon, geo)


def postprocess(angles: Iterable[Angle], ts: Iterable[Time], file):
	for angle, t in tqdm(zip(angles, ts), total=len(angles), desc="Postprocessing"):
		# if angle < 15 * u.degree:
		# 	logger.info(f"ISS is close to the Moon! Angle: {angle:.2f}")
		# 	file.write(f"{t.iso} - {angle:.2f}\n")

		if angle < 0.5 * u.degree:
			sys.stdout.write('\x1b[1A')
			sys.stdout.write('\x1b[2K')
			print("\r", end="")

			logger.warning(f"ISS is very close to the Moon! ({t.iso}) Angle: {angle:.2f}")
			file.write(f"{t.iso} - {angle:.2f}\n")


def main():
	logger.info("Downloading TLE...")
	tle = download_tle(str(config.endpoints.TLE_URL))
	
	current_time = Time.now()
	current_time = current_time + config.general.timezone * u.hour
	logger.info(f"Current time: {current_time} (time zone: UTC{config.general.timezone:+d})")

	logger.info("Getting Earth Location...")
	earth_location = get_Earth_Location(config, config.coordinates.latitude, config.coordinates.longitude)

	stop_seconds = (30 * u.day).to_value(u.second)
	logger.info("Building array of times...")
	times = current_time + np.arange(0, stop_seconds, 10) * u.second

	logger.debug(f"Total number of time points: {len(times)}")

	logger.info("Splitting array of times into chunks...")
	# Split times into chunks for parallel processing
	chunk_size = len(times) // config.general.num_workers
	time_chunks = [times[i:i + chunk_size] for i in range(0, len(times), chunk_size)]

	logger.info(f"Calculating angles using {config.general.num_workers} workers...")
	t1 = time()
	with Pool(config.general.num_workers) as pool:
		chunk_results = pool.map(
			partial(calculate, tle=tle, geo=earth_location),
			time_chunks
		)
	t2 = time()
	logger.info(f"Angle calculation completed in {t2 - t1:.2f} seconds.")
	logger.info(f"Average performance: {len(times) / (t2 - t1):.4f} it/s.")
	
	# Concatenate results
	angles = np.concatenate(chunk_results)

	logger.info("Postprocessing results...")
	with open("output.txt", "w") as file:
		postprocess(angles, times, file)

	# with open("output.txt", "w") as file:
	# 	for i in range(0, len(times)):
	# 		t = time + times[i]
	# 		_iteration(t, earth_location, file)

if __name__ == "__main__":
	main()

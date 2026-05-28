from dataclasses import dataclass
from loguru import logger
import requests

__all__ = ["TLE", "download_tle"]

@dataclass
class TLE:
	s: str = ""
	t: str = ""

def download_tle(tle_url: str) -> TLE:
	with requests.get(tle_url) as response:
		if response.status_code != 200:
			logger.error(f"Failed to download TLE data: {response.status_code}")
			raise requests.RequestException(f"Failed to download TLE data: {response.status_code}")
		
		tle_data = response.text
	
	logger.debug("Successfully downloaded TLE data")
	
	with open("tle.txt", 'w') as f:
		f.write(tle_data)
	
	lines = [line.strip() for line in tle_data.split('\n') if line.strip()]
	if len(lines) < 3:
		logger.error("Insufficient TLE data")
		raise requests.RequestException("Insufficient TLE data")
	
	return TLE(s=lines[1], t=lines[2])

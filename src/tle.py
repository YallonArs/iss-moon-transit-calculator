from dataclasses import dataclass

import aiofiles
import aiohttp
from loguru import logger
from cache import AsyncLRU

@dataclass
class TLE:
	s: str = ""
	t: str = ""

@AsyncLRU()
async def download_tle(tle_url: str) -> TLE:
	async with aiohttp.ClientSession() as session:
		async with session.get(tle_url) as response:
			if response.status != 200:
				logger.error(f"Failed to download TLE data: {response.status}")
				raise Exception(f"Failed to download TLE data: {response.status}")
			
			logger.debug("Successfully downloaded TLE data")
			
			async with aiofiles.open("tle.txt", 'w') as f:
				tle_data = await response.text()
				await f.write(tle_data)
			
			lines = [line.strip() for line in tle_data.split('\n') if line.strip()]
			if len(lines) < 3:
				logger.error("Insufficient TLE data")
				raise Exception("Insufficient TLE data")
			
			return TLE(s=lines[1], t=lines[2])

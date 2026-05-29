import tomllib
from typing import Optional
from pydantic import BaseModel, HttpUrl, model_validator
import os


class GeneralConfig(BaseModel):
	log_level: str = "DEBUG"
	use_elevation: bool = True
	num_workers: int = os.cpu_count()
	timezone: int = 0

class EndpointsConfig(BaseModel):
	TLE_URL: HttpUrl
	ELEVATION_URL: Optional[HttpUrl] = None

class CoordinatesConfig(BaseModel):
	latitude: float
	longitude: float

class AppConfig(BaseModel):
	general: GeneralConfig
	endpoints: EndpointsConfig
	coordinates: CoordinatesConfig

	@model_validator(mode='after')
	def check_elevation_url(self):
		if self.general.use_elevation and not self.endpoints.ELEVATION_URL:
			raise ValueError("ELEVATION_URL is required when use_elevation is True")
		
		return self

def load_config(path: str = "config.toml") -> AppConfig:
	with open(path, 'rb') as f:
		return AppConfig.model_validate(tomllib.load(f))

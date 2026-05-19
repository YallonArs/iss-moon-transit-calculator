import tomllib
from pydantic import BaseModel, HttpUrl


class GeneralConfig(BaseModel):
    log_level: str = "DEBUG"
    TLE_URL: HttpUrl 

class CoordinatesConfig(BaseModel):
    latitude: float
    longitude: float

class AppConfig(BaseModel):
    general: GeneralConfig
    coordinates: CoordinatesConfig

def load_config(path: str = "config.toml") -> AppConfig:
	with open(path, 'rb') as f:
		return AppConfig.model_validate(tomllib.load(f))

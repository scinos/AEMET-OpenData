"""AEMET OpenData Station."""

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from .const import (
    AEMET_ATTR_IDEMA,
    AEMET_ATTR_STATION_ALTITUDE,
    AEMET_ATTR_STATION_DATE,
    AEMET_ATTR_STATION_DEWPOINT,
    AEMET_ATTR_STATION_HUMIDITY,
    AEMET_ATTR_STATION_LATITUDE,
    AEMET_ATTR_STATION_LOCATION,
    AEMET_ATTR_STATION_LONGITUDE,
    AEMET_ATTR_STATION_PRECIPITATION,
    AEMET_ATTR_STATION_PRESSURE,
    AEMET_ATTR_STATION_PRESSURE_SEA,
    AEMET_ATTR_STATION_TEMPERATURE,
    AEMET_ATTR_STATION_TEMPERATURE_MAX,
    AEMET_ATTR_STATION_TEMPERATURE_MIN,
    AEMET_ATTR_STATION_WIND_DIRECTION,
    AEMET_ATTR_STATION_WIND_SPEED,
    AEMET_ATTR_STATION_WIND_SPEED_MAX,
    AOD_ALTITUDE,
    AOD_COORDS,
    AOD_DATETIME,
    AOD_DEW_POINT,
    AOD_DISTANCE,
    AOD_HUMIDITY,
    AOD_ID,
    AOD_NAME,
    AOD_OUTDATED,
    AOD_PRECIPITATION,
    AOD_PRESSURE,
    AOD_TEMP,
    AOD_TEMP_MAX,
    AOD_TEMP_MIN,
    AOD_TIMESTAMP,
    AOD_TIMEZONE,
    AOD_WIND_DIRECTION,
    AOD_WIND_SPEED,
    AOD_WIND_SPEED_MAX,
    ATTR_DATA,
    ATTR_DISTANCE,
    STATION_MAX_DELTA,
)
from .helpers import get_current_datetime, parse_api_timestamp, timezone_from_coords


class Station:
    """AEMET OpenData Station."""

    altitude: float
    coords: tuple[float, float]
    _datetime: datetime
    distance: float
    dew_point: float
    humidity: float
    id: str
    name: str
    precipitation: float
    pressure: float
    temp: float
    temp_max: float
    temp_min: float
    wind_direction: float
    wind_speed: float
    wind_speed_max: float
    zoneinfo: ZoneInfo

    def __init__(self, data: dict[str, Any]) -> None:
        """Init AEMET OpenData Station."""
        self.altitude = float(data[AEMET_ATTR_STATION_ALTITUDE])
        self.coords = (
            float(data[AEMET_ATTR_STATION_LATITUDE]),
            float(data[AEMET_ATTR_STATION_LONGITUDE]),
        )
        self.distance = float(data[ATTR_DISTANCE])
        self.id = str(data[AEMET_ATTR_IDEMA])
        self.name = str(data[AEMET_ATTR_STATION_LOCATION])

        self.zoneinfo = timezone_from_coords(self.coords)

        self.update_sample(data)

    def get_altitude(self) -> float:
        """Return Station altitude."""
        return self.altitude

    def get_coords(self) -> tuple[float, float]:
        """Return Station coordinates."""
        return self.coords

    def get_datetime(self) -> datetime:
        """Return Station datetime of data."""
        return self._datetime

    def get_distance(self) -> float:
        """Return Station distance from selected coordinates."""
        return round(self.distance, 3)

    def get_dew_point(self) -> float:
        """Return Station dew point."""
        return self.dew_point

    def get_humidity(self) -> float:
        """Return Station humidity."""
        return self.humidity

    def get_id(self) -> str:
        """Return Station ID."""
        return self.id

    def get_name(self) -> str:
        """Return Station name."""
        return self.name

    def get_outdated(self) -> bool:
        """Return Station data outdated."""
        cur_dt = get_current_datetime()
        return cur_dt > self.get_datetime() + STATION_MAX_DELTA

    def get_precipitation(self) -> float:
        """Return Station precipitation."""
        return self.precipitation

    def get_pressure(self) -> float:
        """Return Station pressure."""
        return self.pressure

    def get_temp(self) -> float:
        """Return Station temperature."""
        return self.temp

    def get_temp_max(self) -> float:
        """Return Station maximum temperature."""
        return self.temp_max

    def get_temp_min(self) -> float:
        """Return Station minimum temperature."""
        return self.temp_min

    def get_timestamp(self) -> str:
        """Return Station timestamp."""
        return self._datetime.isoformat()

    def get_timezone(self) -> ZoneInfo:
        """Return Station timezone."""
        return self.zoneinfo

    def get_wind_direction(self) -> float:
        """Return Station wind direction."""
        return self.wind_direction

    def get_wind_speed(self) -> float:
        """Return Station wind speed."""
        return self.wind_speed

    def get_wind_speed_max(self) -> float:
        """Return Station maximum wind speed."""
        return self.wind_speed_max

    def update_sample(self, data: dict[str, Any]) -> None:
        """Update Station data from sample."""
        station_dt = parse_api_timestamp(data[AEMET_ATTR_STATION_DATE])

        self._datetime = station_dt.astimezone(self.get_timezone())
        self.dew_point = float(data[AEMET_ATTR_STATION_DEWPOINT])
        self.humidity = float(data[AEMET_ATTR_STATION_HUMIDITY])
        self.precipitation = float(data[AEMET_ATTR_STATION_PRECIPITATION])
        if AEMET_ATTR_STATION_PRESSURE_SEA in data:
            self.pressure = float(data[AEMET_ATTR_STATION_PRESSURE_SEA])
        else:
            self.pressure = float(data[AEMET_ATTR_STATION_PRESSURE])
        self.temp = float(data[AEMET_ATTR_STATION_TEMPERATURE])
        self.temp_max = float(data[AEMET_ATTR_STATION_TEMPERATURE_MAX])
        self.temp_min = float(data[AEMET_ATTR_STATION_TEMPERATURE_MIN])
        self.wind_direction = float(data[AEMET_ATTR_STATION_WIND_DIRECTION])
        self.wind_speed = float(data[AEMET_ATTR_STATION_WIND_SPEED])
        self.wind_speed_max = float(data[AEMET_ATTR_STATION_WIND_SPEED_MAX])

    def update_samples(self, samples: dict[str, Any]) -> None:
        """Update Station data from samples."""
        latest: dict[str, Any]
        latest_dt: datetime | None = None
        for sample in samples[ATTR_DATA]:
            dt = parse_api_timestamp(sample[AEMET_ATTR_STATION_DATE])
            if latest_dt is None or dt > latest_dt:
                latest = sample
                latest_dt = dt
        if (
            latest_dt is not None
            and self.get_datetime() < latest_dt <= get_current_datetime()
        ):
            self.update_sample(latest)

    def data(self) -> dict[str, Any]:
        """Return station data."""
        data: dict[str, Any] = {
            AOD_ALTITUDE: self.get_altitude(),
            AOD_COORDS: self.get_coords(),
            AOD_DATETIME: self.get_datetime(),
            AOD_DISTANCE: self.get_distance(),
            AOD_HUMIDITY: self.get_humidity(),
            AOD_ID: self.get_id(),
            AOD_NAME: self.get_name(),
            AOD_OUTDATED: self.get_outdated(),
            AOD_PRECIPITATION: self.get_precipitation(),
            AOD_PRESSURE: self.get_pressure(),
            AOD_TEMP: self.get_temp(),
            AOD_TEMP_MAX: self.get_temp_max(),
            AOD_TEMP_MIN: self.get_temp_min(),
            AOD_TIMESTAMP: self.get_timestamp(),
            AOD_TIMEZONE: self.get_timezone(),
            AOD_WIND_DIRECTION: self.get_wind_direction(),
            AOD_WIND_SPEED: self.get_wind_speed(),
            AOD_WIND_SPEED_MAX: self.get_wind_speed_max(),
        }
        return data

    def weather(self) -> dict[str, Any]:
        """Return Station weather data."""
        weather: dict[str, Any] = {
            AOD_DEW_POINT: self.get_dew_point(),
            AOD_HUMIDITY: self.get_humidity(),
            AOD_PRECIPITATION: self.get_precipitation(),
            AOD_PRESSURE: self.get_pressure(),
            AOD_TEMP: self.get_temp(),
            AOD_WIND_DIRECTION: self.get_wind_direction(),
            AOD_WIND_SPEED: self.get_wind_speed(),
            AOD_WIND_SPEED_MAX: self.get_wind_speed_max(),
        }
        return weather
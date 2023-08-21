# -*- coding: utf-8 -*-
"""Client for the AEMET OpenData REST API."""

import logging

from typing import Any

import geopy.distance
from geopy.distance import Distance
import requests
from requests import Session

from .const import (
    AEMET_ATTR_DATA,
    AEMET_ATTR_STATION_LATITUDE,
    AEMET_ATTR_STATION_LONGITUDE,
    AEMET_ATTR_TOWN_LATITUDE_DECIMAL,
    AEMET_ATTR_TOWN_LONGITUDE_DECIMAL,
    AEMET_ATTR_WEATHER_STATION_LATITUDE,
    AEMET_ATTR_WEATHER_STATION_LONGITUDE,
    API_MIN_STATION_DISTANCE_KM,
    API_MIN_TOWN_DISTANCE_KM,
    API_TIMEOUT,
    API_URL,
    ATTR_DATA,
    ATTR_RESPONSE,
)
from .helpers import parse_station_coordinates, parse_town_code

_LOGGER = logging.getLogger(__name__)


class AEMET:
    """Interacts with the AEMET OpenData API."""

    def __init__(
        self,
        api_key: str,
        timeout: int = API_TIMEOUT,
        session: Session | None = None,
        verify: bool = True,
    ) -> None:
        """Init AEMET OpenData API."""
        self.debug_api: bool = False
        self.dist_hp: bool = False
        self.headers: dict[str, Any] = {"Cache-Control": "no-cache"}
        self.params: dict[str, Any] = {"api_key": api_key}
        self.session = session if session else requests.Session()
        self.timeout: int = timeout
        self.verify: bool = verify

    # Perform API call
    def api_call(self, cmd: str, fetch_data: bool = False) -> Any:
        """Perform Rest API call."""
        if self.debug_api:
            _LOGGER.debug("api call: %s", cmd)

        url = f"{API_URL}/{cmd}"
        try:
            response = self.session.request(
                "GET",
                url,
                verify=self.verify,
                timeout=self.timeout,
                headers=self.headers,
                params=self.params,
            )
        except requests.exceptions.RequestException as req_exc:
            _LOGGER.error("api_call exception: %s", req_exc)
            return None

        if self.debug_api:
            _LOGGER.debug(
                "api_call: %s, status: %s, response %s",
                cmd,
                response.status_code,
                response.text,
            )

        if response.status_code != 200:
            return None

        str_response = response.text
        if str_response is None or str_response == "":
            return None

        json_response = response.json()
        if fetch_data and AEMET_ATTR_DATA in json_response:
            data = self.api_data(json_response[AEMET_ATTR_DATA])
            if data:
                json_response = {
                    ATTR_RESPONSE: json_response,
                    ATTR_DATA: data,
                }

        return json_response

    # Fetch API data
    def api_data(self, url: str) -> Any:
        """Fetch API data."""
        try:
            response = self.session.request(
                "GET",
                url,
                verify=self.verify,
                timeout=self.timeout,
            )
        except requests.exceptions.RequestException as req_exc:
            _LOGGER.error("api_data exception: %s", req_exc)
            return None

        if self.debug_api:
            _LOGGER.debug(
                "api_data: %s, status: %s, response %s",
                url,
                response.status_code,
                response.text,
            )

        if response.status_code != 200:
            return None

        str_response = response.text
        if str_response is None or str_response == "":
            return None

        return response.json()

    # Enable/Disable API calls debugging
    def api_debugging(self, debug_api: bool) -> bool:
        """Enable/Disable API calls debugging."""
        self.debug_api = debug_api
        return self.debug_api

    # Calculate distance between 2 points
    def calc_distance(
        self, start: tuple[float, float], end: tuple[float, float]
    ) -> Distance:
        """Calculate distance between 2 points."""
        if self.dist_hp:
            return geopy.distance.geodesic(start, end)
        return geopy.distance.great_circle(start, end)

    # Enable/Disable high precision for distance calculations
    def distance_high_precision(self, dist_hp: bool) -> bool:
        """Enable/Disable high precision for distance calculations."""
        self.dist_hp = dist_hp
        return self.dist_hp

    # Enable/Disable HTTPS verification
    def https_verify(self, verify: bool) -> bool:
        """Enable/Disable HTTPS verification."""
        self.verify = verify
        return self.verify

    # Get climatological values
    def get_climatological_values_stations(self, fetch_data: bool = True) -> Any:
        """Get stations available for climatological values."""
        cmd = "valores/climatologicos/inventarioestaciones/todasestaciones"
        response = self.api_call(cmd, fetch_data)
        return response

    # Get climatological values station by coordinates
    def get_climatological_values_station_by_coordinates(
        self, latitude: float, longitude: float
    ) -> Any:
        """Get closest climatological values station to coordinates."""
        stations = self.get_climatological_values_stations()
        search_coords = (latitude, longitude)
        station = None
        distance = API_MIN_STATION_DISTANCE_KM
        for cur_station in stations[ATTR_DATA]:
            station_coords = parse_station_coordinates(
                cur_station[AEMET_ATTR_WEATHER_STATION_LATITUDE],
                cur_station[AEMET_ATTR_WEATHER_STATION_LONGITUDE],
            )
            station_point = geopy.point.Point(station_coords)
            cur_coords = (station_point.latitude, station_point.longitude)
            cur_distance = self.calc_distance(search_coords, cur_coords).km
            if cur_distance < distance:
                distance = cur_distance
                station = cur_station
        if self.debug_api:
            _LOGGER.debug("distance: %s, station: %s", distance, station)
        return station

    # Get climatological values station data
    def get_climatological_values_station_data(
        self, station: str, fetch_data: bool = True
    ) -> Any:
        """Get data from climatological values station."""
        cmd = f"valores/climatologicos/inventarioestaciones/estaciones/{station}"
        response = self.api_call(cmd, fetch_data)
        return response

    # Get conventional observation stations
    def get_conventional_observation_stations(self, fetch_data: bool = True) -> Any:
        """Get stations available for conventional observations."""
        cmd = "observacion/convencional/todas"
        response = self.api_call(cmd, fetch_data)
        return response

    # Get conventional observation station by coordinates
    def get_conventional_observation_station_by_coordinates(
        self, latitude: float, longitude: float
    ) -> Any:
        """Get closest conventional observation station to coordinates."""
        stations = self.get_conventional_observation_stations()
        search_coords = (latitude, longitude)
        station = None
        distance = API_MIN_STATION_DISTANCE_KM
        for cur_station in stations[ATTR_DATA]:
            cur_coords = (
                cur_station[AEMET_ATTR_STATION_LATITUDE],
                cur_station[AEMET_ATTR_STATION_LONGITUDE],
            )
            cur_distance = self.calc_distance(search_coords, cur_coords).km
            if cur_distance < distance:
                distance = cur_distance
                station = cur_station
        if self.debug_api:
            _LOGGER.debug("distance: %s, station: %s", distance, station)
        return station

    # Get conventional observation station data
    def get_conventional_observation_station_data(
        self, station: str, fetch_data: bool = True
    ) -> Any:
        """Get data from conventional observation station."""
        cmd = f"observacion/convencional/datos/estacion/{station}"
        response = self.api_call(cmd, fetch_data)
        return response

    # Get map of lightning strikes
    def get_lightnings_map(self) -> Any:
        """Get map with lightning falls (last 6h)."""
        cmd = "red/rayos/mapa"
        data = self.api_call(cmd)
        return data

    # Get specific forecast
    def get_specific_forecast_town_daily(
        self, town: str, fetch_data: bool = True
    ) -> Any:
        """Get daily forecast for specific town (daily)."""
        cmd = f"prediccion/especifica/municipio/diaria/{parse_town_code(town)}"
        response = self.api_call(cmd, fetch_data)
        return response

    def get_specific_forecast_town_hourly(
        self, town: str, fetch_data: bool = True
    ) -> Any:
        """Get hourly forecast for specific town (hourly)."""
        cmd = f"prediccion/especifica/municipio/horaria/{parse_town_code(town)}"
        response = self.api_call(cmd, fetch_data)
        return response

    # Get specific town information
    def get_town(self, town: str) -> Any:
        """Get information about specific town."""
        cmd = f"maestro/municipio/{town}"
        data = self.api_call(cmd)
        return data

    # Get town by coordinates
    def get_town_by_coordinates(self, latitude: float, longitude: float) -> Any:
        """Get closest town to coordinates."""
        towns = self.get_towns()
        search_coords = (latitude, longitude)
        town = None
        distance = API_MIN_TOWN_DISTANCE_KM
        for cur_town in towns:
            cur_coords = (
                cur_town[AEMET_ATTR_TOWN_LATITUDE_DECIMAL],
                cur_town[AEMET_ATTR_TOWN_LONGITUDE_DECIMAL],
            )
            cur_distance = self.calc_distance(search_coords, cur_coords).km
            if cur_distance < distance:
                distance = cur_distance
                town = cur_town
        if self.debug_api:
            _LOGGER.debug("distance: %s, town: %s", distance, town)
        return town

    # Get full list of towns
    def get_towns(self) -> Any:
        """Get information about towns."""
        cmd = "maestro/municipios"
        data = self.api_call(cmd)
        return data

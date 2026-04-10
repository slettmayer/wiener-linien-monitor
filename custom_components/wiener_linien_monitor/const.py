"""Constants for the Wiener Linien Monitor integration."""

from datetime import timedelta

DOMAIN = "wiener_linien_monitor"

API_ENDPOINT = "https://www.wienerlinien.at/ogd_realtime/monitor"
TRAFFIC_INFO_ENDPOINT = "https://www.wienerlinien.at/ogd_realtime/trafficInfoList"

API_TIMEOUT = 10

CONF_STOPS = "stops"
CONF_MAX_DEPARTURES = "max_departures"
DEFAULT_NAME = "Wiener Linien"
DEFAULT_MAX_DEPARTURES = 5
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)

FETCH_DEPARTURES_SERVICE_NAME = "fetch_departures"

# OeBB API
OEBB_API_ENDPOINT = "https://fahrplan.oebb.at/bin/mgate.exe"
OEBB_API_TIMEOUT = 15
OEBB_AUTH_AID = "OWDL4fE4ixNiPBBm"
OEBB_CLIENT_ID = "OEBB"
OEBB_CLIENT_TYPE = "WEB"
OEBB_CLIENT_NAME = "webapp"
OEBB_CLIENT_L = "vs_webapp"
OEBB_API_VERSION = "1.67"
OEBB_API_LANG = "deu"

OEBB_SEARCH_STATION_SERVICE_NAME = "oebb_search_station"
OEBB_STATION_BOARD_SERVICE_NAME = "oebb_station_board"
OEBB_TRIP_SEARCH_SERVICE_NAME = "oebb_trip_search"

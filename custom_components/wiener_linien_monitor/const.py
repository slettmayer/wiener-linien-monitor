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

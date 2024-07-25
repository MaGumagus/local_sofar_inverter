from datetime import timedelta

DOMAIN = "local_sofar_inverter"
DEFAULT_NAME = "Local Sofar Inverter"
CONF_SERVER_URL = "192.168.67.137"
CONF_SERVER_USER = "admin"
CONF_SERVER_PASS = "admin"
ATTRIBUTION = 'Information provided by Sofar inverter web page.'
DEFAULT_SCAN_INTERVAL = 30 # sec
DEFAULT_MIN_ELEVATION = 2 # when no sun, no power, inverter is down
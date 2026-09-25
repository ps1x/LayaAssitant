"""Constants for Laya Assistant."""

DOMAIN = "laya_assistant"
CONF_URL = "url"
CONF_API_KEY = "api_key"
CONF_PROVIDER = "provider"
PROVIDER_LAYA = "laya"
PROVIDER_JEV = "jev"
CONF_LIGHTS = "lights"
CONF_SWITCHES = "switches"
CONF_FANS = "fans"
CONF_CLIMATES = "climates"
CONF_TEMPERATURE = "temperature_sensors"
CONF_SATELLITE = "satellite_device_id"
CONF_SPOKEN_NAMES = "spoken_names"
CONF_DEBUG = "debug"
THRESHOLD_DEFAULTS = {
    "domain_confidence": 0.8,
    "domain_probability": 0.8,
    "target_confidence": 0.8,
    "target_probability": 0.8,
    "action_confidence": 0.8,
    "action_probability": 0.8,
    "temperature_confidence": 0.3,
    "temperature_probability": 0.8,
}
ENTITY_FIELDS = (CONF_LIGHTS, CONF_SWITCHES, CONF_FANS, CONF_CLIMATES, CONF_TEMPERATURE)
MAX_QUESTIONS = 48

import json
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.http import HomeAssistantView
from homeassistant.helpers.device_registry import async_get as async_get_dev_reg
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store
from aiohttp import web

from .const import DOMAIN, DATA_DEVICE, SIGNAL_UPDATE

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "number", "select", "binary_sensor"]
STORAGE_VERSION = 1  # <-- NEW: Required for the storage helper

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})
    device = LevelSenseDevice(hass, entry.entry_id)
    
    # <-- NEW: Load saved settings from disk BEFORE building the dashboard
    await device.async_load_config() 
    
    hass.data[DOMAIN][DATA_DEVICE] = device

    # Register Device in the HA Registry
    device_registry = async_get_dev_reg(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "level_sense_pro_mac")},
        manufacturer="Level Sense",
        name="Level Sense Pro",
        model="Local API",
    )

    # Register Local API Endpoints
    hass.http.register_view(LevelSenseDataView(device))
    hass.http.register_view(LevelSenseConfigView(device))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

class LevelSenseDevice:
    def __init__(self, hass, entry_id):
        self.hass = hass
        self.entry_id = entry_id
        self.state = {} 
        
        # Initialize the storage helper
        self._store = Store(hass, STORAGE_VERSION, f"{DOMAIN}_{entry_id}_config")
        
        # Default config payload 
        self.config = {
            "result": "success",
            "update_interval": "120",
            "checkin_interval": "3620",
            "flash_size": "4.00MB",
            "flash_mode": "QIO",
            "flash_freq": "40.00MHz",
            "clock_freq": "80MHz",
            "spiffs_defined": "934.88KB",
            "spiffs_used": "0.00KB",
            "rh_delay": "0",
            "rh_delay_status": "0",
            "temp_delay": "0",
            "temp_delay_status": "0",
            "automatic_calibration": "1",
            "power_good": [0, 60, 2, 1],
            "cap_sense": [65535, 1581, 0, 0],  # <-- Restored missing key
            "tempc": ["15.00", "32.17", 0, 0],
            "rh": ["31.00", "60.00", 0, 1],
            "input1": [700, 65535, 2, 1],
            "input2": [700, 65535, 2, 1],
            "cap_sense_min_offset": 427        # <-- Moved to the exact end
        }

    async def async_load_config(self):
        """Attempt to load the config from disk on boot."""
        stored_config = await self._store.async_load()
        if stored_config:
            self.config = stored_config
            _LOGGER.warning("Level Sense config successfully loaded from disk!")
        else:
            _LOGGER.warning("No saved Level Sense config found. Using defaults.")

    def update_telemetry(self, data):
        """THE MISSING FUNCTION: Processes incoming data and updates UI."""
        self.state = data
        async_dispatcher_send(self.hass, SIGNAL_UPDATE)

    def update_config(self, key, index, value):
        """Processes outgoing config changes and saves to disk."""
        if key in self.config:
            if index is not None and isinstance(self.config[key], list):
                self.config[key][index] = value
            else:
                self.config[key] = value
                
        # Schedule a background task to save the new dictionary to disk
        self.hass.async_create_task(self._store.async_save(self.config))

class LevelSenseDataView(HomeAssistantView):
    url = "/_device/data"
    name = "api:level_sense:data"
    requires_auth = False

    def __init__(self, device):
        self.device = device

    async def get(self, request):
        json_str = request.query.get("json")
        
        try:
            if json_str:
                parsed_data = json.loads(json_str)
                self.device.update_telemetry(parsed_data)
        except Exception as e:
            # If the JSON fails to parse, log the exact error
            _LOGGER.error("Level Sense JSON parsing failed: %s", e)
            
        # THE FIX: Tell the device to fetch /_device/config immediately
        return self.json({"result": "success", "has_config_update": 1})

class LevelSenseConfigView(HomeAssistantView):
    url = "/_device/config"
    name = "api:level_sense:config"
    requires_auth = False

    def __init__(self, device):
        self.device = device

    async def get(self, request):
        # 1. Pack the JSON tightly with NO spaces, exactly like the original cloud
        payload = json.dumps(self.device.config, separators=(',', ':'))
        
        _LOGGER.warning("Sending Level Sense Config: %s", payload)

        # 2. Force the exact headers the ESP32 firmware is expecting
        return web.Response(
            text=payload,
            content_type="text/html",
            charset="UTF-8"
        )
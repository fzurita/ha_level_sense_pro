from homeassistant.components.number import NumberEntity, NumberMode
from .const import DOMAIN, DATA_DEVICE

async def async_setup_entry(hass, entry, async_add_entities):
    device = hass.data[DOMAIN][DATA_DEVICE]
    async_add_entities([
        # Existing Thresholds
        LevelSenseTempThreshold(device, "Temp Min Limit", "tempc", 0, -4.0, 212.0),
        LevelSenseTempThreshold(device, "Temp Max Limit", "tempc", 1, -4.0, 212.0),
        LevelSenseRHThreshold(device, "RH Min Limit", "rh", 0, 0.0, 100.0),
        LevelSenseRHThreshold(device, "RH Max Limit", "rh", 1, 0.0, 100.0),
        
        # New Interval Controls
        LevelSenseInterval(device, "Update Interval", "update_interval", 10, 86400),
        LevelSenseInterval(device, "Check-in Interval", "checkin_interval", 60, 86400),
    ])

class LevelSenseTempThreshold(NumberEntity):
    def __init__(self, device, name, key, index, min_v, max_v):
        self.device = device
        self._key = key
        self._index = index
        self._attr_name = f"Level Sense {name}"
        self._attr_unique_id = f"ls_thresh_{key}_{index}"
        self._attr_native_min_value = min_v
        self._attr_native_max_value = max_v
        self._attr_native_unit_of_measurement = "°F"
        self._attr_mode = NumberMode.BOX
        self._attr_device_info = {"identifiers": {(DOMAIN, "level_sense_pro_mac")}}

    @property
    def native_value(self):
        # Device JSON stores the artificially high threshold.
        # Subtract 3.61C to get true ambient, then convert to Fahrenheit for UI.
        c_val_device = float(self.device.config[self._key][self._index])
        ambient_c = c_val_device - 3.61
        return round((ambient_c * 1.8) + 32, 1)

    async def async_set_native_value(self, value: float):
        # UI gives true ambient Fahrenheit. Convert to ambient Celsius.
        ambient_c = (value - 32) / 1.8
        # Add 3.61C so the physical device triggers at the correct time.
        c_val_device = ambient_c + 3.61
        self.device.update_config(self._key, self._index, str(round(c_val_device, 2)))
        self.async_write_ha_state()

class LevelSenseRHThreshold(NumberEntity):
    def __init__(self, device, name, key, index, min_v, max_v):
        self.device = device
        self._key = key
        self._index = index
        self._attr_name = f"Level Sense {name}"
        self._attr_unique_id = f"ls_thresh_{key}_{index}"
        self._attr_native_min_value = min_v
        self._attr_native_max_value = max_v
        self._attr_native_unit_of_measurement = "%"
        self._attr_mode = NumberMode.BOX
        self._attr_device_info = {"identifiers": {(DOMAIN, "level_sense_pro_mac")}}

    @property
    def native_value(self):
        return float(self.device.config[self._key][self._index])

    async def async_set_native_value(self, value: float):
        self.device.update_config(self._key, self._index, str(round(value, 2)))
        self.async_write_ha_state()

class LevelSenseInterval(NumberEntity):
    """Text box for single-value interval settings."""
    def __init__(self, device, name, key, min_v, max_v):
        self.device = device
        self._key = key
        self._attr_name = f"Level Sense {name}"
        self._attr_unique_id = f"ls_interval_{key}"
        self._attr_native_min_value = min_v
        self._attr_native_max_value = max_v
        self._attr_native_unit_of_measurement = "s"
        self._attr_mode = NumberMode.BOX
        self._attr_device_info = {"identifiers": {(DOMAIN, "level_sense_pro_mac")}}

    @property
    def native_value(self):
        return int(self.device.config[self._key])

    async def async_set_native_value(self, value: float):
        # Convert back to a string without decimal points for the JSON payload
        self.device.update_config(self._key, None, str(int(value)))
        self.async_write_ha_state()
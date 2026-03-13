from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from .const import DOMAIN, DATA_DEVICE, SIGNAL_UPDATE

async def async_setup_entry(hass, entry, async_add_entities):
    device = hass.data[DOMAIN][DATA_DEVICE]
    async_add_entities([
        LevelSenseTempSensor(device, "Temperature", "tempc", "°C", "temperature"),
        LevelSenseTelemetry(device, "Humidity", "rh", "%", "humidity"),
        LevelSenseTelemetry(device, "Battery Voltage", "battvdc", "V", "voltage"),
        LevelSenseTelemetry(device, "Water Depth Raw", "cap_sense", "raw", None),
        LevelSenseTelemetry(device, "Input 1 Raw", "input1", "raw", None),
        LevelSenseTelemetry(device, "Input 2 Raw", "input2", "raw", None)
    ])

class LevelSenseTelemetry(SensorEntity):
    """Generic sensor class for standard telemetry."""
    def __init__(self, device, name, key, unit, dev_class):
        self.device = device
        self._key = key
        self._attr_name = f"Level Sense {name}"
        self._attr_unique_id = f"ls_sensor_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = dev_class
        self._attr_device_info = {"identifiers": {(DOMAIN, "level_sense_pro_mac")}}

    @property
    def native_value(self):
        val = self.device.state.get(self._key)
        # Array format is [Current, Min, Max]. Grab index 0 for Current.
        if isinstance(val, list) and len(val) > 0: 
            return float(val[0])
        return val

    async def async_added_to_hass(self):
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_UPDATE, self.async_write_ha_state)
        )

class LevelSenseTempSensor(LevelSenseTelemetry):
    """Specific sensor class to handle the temperature offset directly in Celsius."""
    def __init__(self, device, name, key, unit, dev_class):
        super().__init__(device, name, key, unit, dev_class)
        # Force HA to treat this as a brand new entity to bypass history conflicts
        self._attr_unique_id = f"ls_sensor_{key}"

    @property
    def native_value(self):
        val = self.device.state.get(self._key)
        if isinstance(val, list) and len(val) > 0:
            temp_c = float(val[0])
            return round(temp_c - 3.61, 2)
        return val
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from .const import DOMAIN, DATA_DEVICE, SIGNAL_UPDATE

async def async_setup_entry(hass, entry, async_add_entities):
    device = hass.data[DOMAIN][DATA_DEVICE]
    
    async_add_entities([
        LevelSenseInputBinarySensor(device, "Leak Sensor", "input1", "moisture"),
        LevelSenseInputBinarySensor(device, "Float Switch", "input2", "safety"),
        
        # Internal Device States
        LevelSenseStateBinarySensor(device, "Siren", "siren_state", "sound"),
        LevelSenseStateBinarySensor(device, "Relay", "relay_state", None, "mdi:electric-switch"),
        LevelSenseStateBinarySensor(device, "Device Fault", "device_state", "problem"),
        LevelSenseStateBinarySensor(device, "Alarm Silenced", "alarm_silence", None, "mdi:bell-off"),
    ])

class LevelSenseBinarySensorBase(BinarySensorEntity):
    """Base class for Level Sense binary sensors."""
    def __init__(self, device, name, key, dev_class=None, icon=None):
        self.device = device
        self._key = key
        self._attr_name = f"Level Sense {name}"
        self._attr_unique_id = f"ls_binary_{key}"
        self._attr_device_class = dev_class
        if icon:
            self._attr_icon = icon
        self._attr_device_info = {"identifiers": {(DOMAIN, "level_sense_pro_mac")}}

    async def async_added_to_hass(self):
        """Register callbacks when entity is added."""
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_UPDATE, self.async_write_ha_state)
        )

class LevelSenseInputBinarySensor(LevelSenseBinarySensorBase):
    """Evaluates arrays for analog inputs like the Leak and Float sensors."""
    @property
    def is_on(self):
        val = self.device.state.get(self._key)
        # Array format is [Current, Min, Max]. 
        # We check the Min value (index 1) to ensure we don't miss quick splashes.
        if isinstance(val, list) and len(val) >= 2:
            # Baseline is ~1430 (Dry). Alarm triggers when value drops below 700 (Wet).
            return int(val[1]) < 700
        return False

class LevelSenseStateBinarySensor(LevelSenseBinarySensorBase):
    """Evaluates standard integers for internal device states."""
    @property
    def is_on(self):
        val = self.device.state.get(self._key)
        # Check if the device threw a status code greater than 0
        if val is not None:
            return int(val) > 0
        return False
from homeassistant.components.select import SelectEntity
from .const import DOMAIN, DATA_DEVICE

async def async_setup_entry(hass, entry, async_add_entities):
    device = hass.data[DOMAIN][DATA_DEVICE]
    entities = []
    
    for label, key in [("Temp", "tempc"), ("RH", "rh"), ("Leak", "input1"), ("Float", "input2")]:
        entities.append(LevelSenseConfigSelect(device, f"{label} Relay", key, 2))
        entities.append(LevelSenseConfigSelect(device, f"{label} Siren", key, 3))
        
    async_add_entities(entities)

class LevelSenseConfigSelect(SelectEntity):
    def __init__(self, device, name, key, index):
        self.device = device
        self._key = key
        self._index = index
        self._attr_name = f"Level Sense {name}"
        self._attr_unique_id = f"ls_select_{key}_{index}"
        self._attr_options = ["On", "Off"]
        self._attr_device_info = {"identifiers": {(DOMAIN, "level_sense_pro_mac")}}

    @property
    def current_option(self):
        return "On" if int(self.device.config[self._key][self._index]) > 0 else "Off"

    async def async_select_option(self, option: str):
        # Index 2 (Relay) uses 2, Index 3 (Siren) uses 1 in the native JSON
        if option == "On":
            val = 2 if self._index == 2 else 1
        else:
            val = 0
            
        self.device.update_config(self._key, self._index, val)
        self.async_write_ha_state()
"""Binary sensor for current outage status (power off or on)."""
from homeassistant.components.binary_sensor import BinarySensorEntity, DEVICE_CLASS_POWER

from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up binary_sensor for outage status."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([OutageNowBinarySensor(coordinator)])

class OutageNowBinarySensor(BinarySensorEntity):
    """Binary sensor indicating if power is currently off (outage now)."""
    _attr_has_entity_name = True

    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_name = "Power outage ongoing"
        self._attr_unique_id = f"{coordinator.region}_{coordinator.group}_outage_now"
        # Використаємо device_class "power" – хоча за замовчанням On означає наявність живлення,
        # у нас On = світла нема. Тому можна не задавати device_class або використати "power" усвідомлено.
        self._attr_device_class = DEVICE_CLASS_POWER
        # Прив'язуємо до того ж пристрою, що й сенсори
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{coordinator.region}_{coordinator.group}")},
            "name": f"Svitlo UA Power Outages ({coordinator.region})",
            "manufacturer": "Svitlo UA",
            "model": f"Outage Schedule {coordinator.region}"
        }

    @property
    def is_on(self):
        # Повертає True, якщо зараз відключення (тобто світла нема)
        if not self.coordinator.data:
            return False
        return bool(self.coordinator.data.get("outage_now", False))

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and self.coordinator.data is not None

    async def async_added_to_hass(self):
        self.coordinator.async_add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        self.coordinator.async_remove_listener(self.async_write_ha_state)

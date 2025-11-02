"""Модуль двойкових датчиків (індикація наявності відключення)."""
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import const

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[const.DOMAIN][entry.entry_id]
    async_add_entities([OutageNowBinarySensor(coordinator)])

class OutageNowBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Двочічний датчик: чи зараз є відключення світла."""
    _attr_device_class = BinarySensorDeviceClass.POWER  # використовуємо клас power (значення on коли є живлення)
    def __init__(self, coordinator):
        super().__init__(coordinator)
        region = coordinator.region
        group = coordinator.group
        self._attr_name = "Відключення зараз"
        self._attr_unique_id = f"{region}_{group}_outage_now"
        self._attr_device_info = {
            "identifiers": {(const.DOMAIN, f"{region}-{group}")},
            "name": f"Світло - {region} черга {group}",
            "manufacturer": "Світло UA",
            "model": "Outage Schedule"
        }

    @property
    def is_on(self):
        events = self.coordinator.data.get("events", [])
        if not events:
            return False
        now = datetime.utcnow()
        # якщо зараз падає в інтервал відключення
        for ev in events:
            start = ev.get("start")
            end = ev.get("end")
            ev_type = ev.get("type", "")
            if start and end and start <= now < end:
                # Використовуємо тільки definite відключення
                if "DEFINITE" in ev_type or ev_type == "OUTAGE":
                    return True
        return False

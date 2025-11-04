from __future__ import annotations
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        SvitloStatusSensor(coordinator),             # Grid ON / Grid OFF (текст)
        SvitloNextGridConnectionSensor(coordinator), # timestamp (коли з'явиться)
        SvitloNextOutageSensor(coordinator),         # timestamp (коли зникне)
        SvitloScheduleUpdatedSensor(coordinator),    # timestamp (коли опитали)
    ]
    async_add_entities(entities)


class SvitloBaseEntity(CoordinatorEntity):
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)

    @property
    def device_info(self) -> dict[str, Any]:
        region = getattr(self.coordinator, "region", "region")
        queue = getattr(self.coordinator, "queue", "queue")
        return {
            "identifiers": {(DOMAIN, f"{region}_{queue}")},
            "manufacturer": "svitlo.live",
            "model": f"Queue {queue}",
            "name": f"Svitlo • {region} / {queue}",
        }


class SvitloStatusSensor(SvitloBaseEntity, SensorEntity):
    """Текстовий сенсор: Grid ON / Grid OFF."""

    _attr_name = "Electricity"
    _attr_icon = "mdi:transmission-tower"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"svitlo_status_{coordinator.region}_{coordinator.queue}"

    @property
    def native_value(self) -> str | None:
        val = self.coordinator.data.get("now_status")  # "on"/"off"
        return "Grid ON" if val == "on" else "Grid OFF"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        d = self.coordinator.data
        return {
            "queue": d.get("queue"),
            "date": d.get("date"),
            "now_halfhour_index": d.get("now_halfhour_index"),
            "next_change_at": d.get("next_change_at"),
            "today_24h_classes": d.get("today_24h_classes"),
            "today_48half": d.get("today_48half"),
            "tomorrow_date": d.get("tomorrow_date"),
            "tomorrow_24h_classes": d.get("tomorrow_24h_classes"),
            "tomorrow_48half": d.get("tomorrow_48half"),
            "updated": d.get("updated"),
            "source": d.get("source"),
        }


class SvitloNextGridConnectionSensor(SvitloBaseEntity, SensorEntity):
    """TIMESTAMP: якщо зараз off → показує next_on_at; якщо on → None."""
    _attr_name = "Next grid connection"
    _attr_icon = "mdi:clock-check"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"svitlo_next_grid_{coordinator.region}_{coordinator.queue}"

    @property
    def native_value(self):
        if self.coordinator.data.get("now_status") == "on":
            return None
        iso_val = self.coordinator.data.get("next_on_at")
        return dt_util.parse_datetime(iso_val) if iso_val else None


class SvitloNextOutageSensor(SvitloBaseEntity, SensorEntity):
    """TIMESTAMP: якщо зараз on → показує next_off_at; якщо off → None."""
    _attr_name = "Next Outage"
    _attr_icon = "mdi:clock-alert"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"svitlo_next_off_{coordinator.region}_{coordinator.queue}"

    @property
    def native_value(self):
        if self.coordinator.data.get("now_status") == "off":
            return None
        iso_val = self.coordinator.data.get("next_off_at")
        return dt_util.parse_datetime(iso_val) if iso_val else None


class SvitloScheduleUpdatedSensor(SvitloBaseEntity, SensorEntity):
    """Час останнього опитування як timestamp."""
    _attr_name = "Schedule Updated"
    _attr_icon = "mdi:update"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"svitlo_updated_{coordinator.region}_{coordinator.queue}"

    @property
    def native_value(self):
        iso_val = self.coordinator.data.get("updated")
        return dt_util.parse_datetime(iso_val) if iso_val else None

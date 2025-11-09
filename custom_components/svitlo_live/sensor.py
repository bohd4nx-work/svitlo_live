from __future__ import annotations
from typing import Any, Optional
from datetime import timedelta

from homeassistant.core import HomeAssistant, callback
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        SvitloStatusSensor(coordinator),                 # Grid ON / Grid OFF / No schedules / No data
        SvitloNextGridConnectionSensor(coordinator),     # TIMESTAMP
        SvitloNextOutageSensor(coordinator),             # TIMESTAMP
        SvitloMinutesToGridConnection(coordinator),      # minutes (number) — автооновлення кожні 30с
        SvitloMinutesToOutage(coordinator),              # minutes (number) — автооновлення кожні 30с
        SvitloScheduleUpdatedSensor(coordinator),        # TIMESTAMP
    ]
    async_add_entities(entities)


class SvitloBaseEntity(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)

    @property
    def available(self) -> bool:
        # Ентіті завжди доступна; “нема даних” показуємо значенням/None.
        return True

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


class SvitloStatusSensor(SvitloBaseEntity):
    """Текстовий сенсор: Grid ON / Grid OFF / No schedules / No data."""
    _attr_name = "Electricity"
    _attr_icon = "mdi:transmission-tower"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"svitlo_status_{coordinator.region}_{coordinator.queue}"

    @property
    def native_value(self) -> str | None:
        data = getattr(self.coordinator, "data", None)
        if not data or not getattr(self.coordinator, "last_update_success", False):
            return "No data"
        val = data.get("now_status")  # "on"/"off"/"unknown"/"nosched"
        if val == "on":
            return "Grid ON"
        if val == "off":
            return "Grid OFF"
        if val == "nosched":
            return "No schedules"
        return "No data"


# ---------- TIMESTAMP сенсори (як раніше) ----------

class SvitloNextGridConnectionSensor(SvitloBaseEntity):
    """TIMESTAMP: якщо зараз off → показує next_on_at; інакше None."""
    _attr_name = "Next grid connection"
    _attr_icon = "mdi:clock-check"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"svitlo_next_grid_{coordinator.region}_{coordinator.queue}"

    @property
    def native_value(self):
        d = getattr(self.coordinator, "data", None)
        if not d or not getattr(self.coordinator, "last_update_success", False):
            return None
        if d.get("now_status") != "off":
            return None
        iso_val = d.get("next_on_at")
        return dt_util.parse_datetime(iso_val) if iso_val else None


class SvitloNextOutageSensor(SvitloBaseEntity):
    """TIMESTAMP: якщо зараз on → показує next_off_at; інакше None."""
    _attr_name = "Next Outage"
    _attr_icon = "mdi:clock-alert"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"svitlo_next_off_{coordinator.region}_{coordinator.queue}"

    @property
    def native_value(self):
        d = getattr(self.coordinator, "data", None)
        if not d or not getattr(self.coordinator, "last_update_success", False):
            return None
        if d.get("now_status") != "on":
            return None
        iso_val = d.get("next_off_at")
        return dt_util.parse_datetime(iso_val) if iso_val else None


# ---------- Нові числові сенсори (хвилини до події) з локальним таймером ----------

class _MinutesBase(SvitloBaseEntity):
    """База для розрахунку хвилин до ISO-часу з автооновленням."""
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "min"

    _unsub_timer = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        # Оновлюємо відображення кожні 30 секунд без жодних зовнішніх запитів
        @callback
        def _tick(now) -> None:
            self.async_write_ha_state()

        self._unsub_timer = async_track_time_interval(
            self.hass, _tick, timedelta(seconds=30)
        )

    async def async_will_remove_from_hass(self) -> None:
        await super().async_will_remove_from_hass()
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None

    def _minutes_until(self, iso_utc: Optional[str]) -> Optional[int]:
        """Повертає ceil різниці в хвилинах між target і поточним UTC.
        Якщо target немає — None. Якщо вже настав — 0.
        """
        if not iso_utc:
            return None
        target = dt_util.parse_datetime(iso_utc)
        if not target:
            return None
        now_utc = dt_util.utcnow()
        delta_s = (target - now_utc).total_seconds()
        if delta_s <= 0:
            return 0
        mins = int((delta_s + 59) // 60)  # ceil для секунд → хвилини
        return mins


class SvitloMinutesToGridConnection(_MinutesBase):
    """Хвилини до підключення (лише коли зараз off)."""
    _attr_name = "Minutes to grid connection"
    _attr_icon = "mdi:timer-sand"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"svitlo_min_to_on_{coordinator.region}_{coordinator.queue}"

    @property
    def native_value(self) -> Optional[int]:
        d = getattr(self.coordinator, "data", None)
        if not d or not getattr(self.coordinator, "last_update_success", False):
            return None
        if d.get("now_status") != "off":
            return None
        return self._minutes_until(d.get("next_on_at"))


class SvitloMinutesToOutage(_MinutesBase):
    """Хвилини до відключення (лише коли зараз on)."""
    _attr_name = "Minutes to outage"
    _attr_icon = "mdi:timer-sand"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"svitlo_min_to_off_{coordinator.region}_{coordinator.queue}"

    @property
    def native_value(self) -> Optional[int]:
        d = getattr(self.coordinator, "data", None)
        if not d or not getattr(self.coordinator, "last_update_success", False):
            return None
        if d.get("now_status") != "on":
            return None
        return self._minutes_until(d.get("next_off_at"))


# ---------- Updated timestamp for “Schedule Updated” ----------

class SvitloScheduleUpdatedSensor(SvitloBaseEntity):
    """Час останнього опитування як timestamp."""
    _attr_name = "Schedule Updated"
    _attr_icon = "mdi:update"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"svitlo_updated_{coordinator.region}_{coordinator.queue}"

    @property
    def native_value(self):
        d = getattr(self.coordinator, "data", None)
        if not d:
            return None
        iso_val = d.get("updated")
        return dt_util.parse_datetime(iso_val) if iso_val else None

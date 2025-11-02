import logging
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class SvitloDataUpdateCoordinator(DataUpdateCoordinator):
    """Координатор оновлення даних для інтеграції 'Світло'."""

    def __init__(self, hass: HomeAssistant, region: str, provider: str, group: str) -> None:
        """Ініціалізація."""
        self.hass = hass
        self.region = region
        self.provider = provider
        self.group = group

        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=5),
        )

    async def _async_update_data(self):
        """Оновлення даних (викликається кожні 5 хвилин)."""
        try:
            # TODO: Тут має бути логіка звернення до API Yasno або іншого джерела
            # Поверни структуру з часом відключення, включення, статусом тощо.
            # Наприклад:
            return {
                "outage_now": False,
                "next_outage_start": "2025-11-03T10:00:00+02:00",
                "next_power_on": "2025-11-03T13:00:00+02:00",
                "time_to_next_outage": 3600,  # у секундах
            }

        except Exception as err:
            _LOGGER.error("Не вдалося отримати дані з API: %s", err)
            raise HomeAssistantError("Помилка оновлення даних для Світло") from err

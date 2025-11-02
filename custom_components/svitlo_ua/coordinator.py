import logging
from datetime import timedelta, datetime
import aiohttp
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
        """Оновлення даних з API."""
        try:
            url = f"https://svitlo.vesma.today/api/schedule?region={self.region}&group={self.group}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        raise HomeAssistantError(f"API повернув статус {resp.status}")
                    data = await resp.json()

            current = data.get("currentStatus", {})
            next_start = current.get("start")
            next_end = current.get("end")

            if current.get("isOffNow"):
                status = True
            else:
                status = False

            # Обрахунок часу до наступного відключення (якщо дано)
            now = datetime.now().astimezone()
            if next_start:
                dt_start = datetime.fromisoformat(next_start)
                seconds_to_next = max(0, int((dt_start - now).total_seconds()))
            else:
                seconds_to_next = None

            return {
                "outage_now": status,
                "next_outage_start": next_start,
                "next_power_on": next_end,
                "time_to_next_outage": seconds_to_next,
            }

        except Exception as err:
            _LOGGER.error("Не вдалося отримати дані з API: %s", err)
            raise HomeAssistantError("Помилка оновлення даних для Світло") from err

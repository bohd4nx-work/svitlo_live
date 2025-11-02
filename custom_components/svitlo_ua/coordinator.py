from __future__ import annotations
from .const import DOMAIN, DEFAULT_SCAN_MINUTES
from .client import DtekClient


def _merge_slots_to_intervals(off: list[bool], step_min: int) -> list[list[str]]:
def to_time(i: int) -> str:
total = i * step_min
return f"{total//60:02d}:{total%60:02d}"
intervals: list[list[str]] = []
start: int | None = None
for i, v in enumerate(off):
if v and start is None:
start = i
edge = (not v and start is not None) or (i == len(off) - 1 and start is not None)
if edge:
end = i + 1 if v and i == len(off) - 1 else i
intervals.append([to_time(start), to_time(end)])
start = None
return intervals


def _status_next(intervals: list[list[str]], now: dt.datetime) -> dict[str, Any]:
nm = now.hour * 60 + now.minute
def tom(s: str) -> int:
h, m = map(int, s.split(":"))
return h * 60 + m
for s, e in intervals:
sm, em = tom(s), tom(e)
if sm <= nm < em:
return {"status": "off_now", "start": s, "end": e}
if nm < sm:
return {"status": "next_off", "start": s, "end": e}
return {"status": "no_more_today"}


class SvitloCoordinator(DataUpdateCoordinator):
def __init__(self, hass: HomeAssistant, session: aiohttp.ClientSession, cfg: dict):
interval = dt.timedelta(minutes=cfg.get("scan_interval_minutes", DEFAULT_SCAN_MINUTES))
super().__init__(hass, hass.helpers.logger, name=DOMAIN, update_interval=interval)
self._session = session
self._cfg = cfg
self.client = DtekClient(session)


async def _async_update_data(self) -> dict:
city = self._cfg["city"]
street = self._cfg["street"]
house = self._cfg["house"]
update_fact = dt.datetime.now().strftime("%d.%m.%Y %H:%M")


gpv = await self.client.fetch_queue_gpv(city, street, house, update_fact)
if not gpv:
raise RuntimeError("Failed to resolve GPV for address")


html = await self.client.get_schedule_html_for_gpv(gpv)
soup = BeautifulSoup(html, "html.parser")
root = soup.select_one(".discon-fact-tables")
table = root.find("table") if root else None
row = table.select_one("tbody tr") if table else None
intervals: list[list[str]] = []
if row:
tds = row.find_all("td")
step = 30 if len(tds) >= 48 else 60
def is_off(td) -> bool:
cls = td.get("class", [])
return any(c in ("cell-scheduled", "cell-first-half", "cell-second-half") for c in cls)
off = [is_off(td) for td in tds]
intervals = _merge_slots_to_intervals(off, step)


now = dt.datetime.now()
return {
"address": {"city": city, "street": street, "house": house},
"gpv": gpv,
"today": intervals,
"next": _status_next(intervals, now),
"updated_at": now.isoformat(),
}

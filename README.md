# 🟡 Svitlo.live
[ЧИТАТИ УКРАЇНСЬКОЮ](https://github.com/chaichuk/svitlo_live/blob/main/readme.uk.md)

[ІНСТРУКЦІЯ З НАЛАШТУВАННЯ СПОВІЩЕНЬ ЗМІНИ ГРАФІКУ](https://github.com/chaichuk/svitlo_live/blob/main/blueprint_manual.uk.md)

An integration for **Home Assistant** that displays the current electricity supply status for your region and queue.

**Version 2.8.0** allows changing settings via UI, supports almost all regions via a new unified reliable API, and automatically cleans up old entities.

---

## ⚙️ Main Features

- ✅ Displays the **current power status** (`On / Off`),  
- ✅ Detects the **next power-on** and **power-off** times,  
- ✅ Shows the time of the **last schedule update**,  
- ✅ **Unified Reliable API**: Uses a specialized proxy that aggregates data from DTEK/YASNO and other official sources for maximum accuracy.
- ✅ **Configure via UI**: Change your queue, sub-queue, or update interval on the fly without reinstalling.
- ✅ **Smart Cleanup**: Automatically removes old entities and devices when you change settings.
- ✅ Includes **built-in localization** (UA / EN),  
- ✅ Schedules **precise entity state changes** at the exact time of power switch — without calling the API again.

---

## 🌍 Supported Regions (Enhanced API)

The integration now uses own API (thanks to [yaroslav2901](https://github.com/yaroslav2901)) for the following regions, ensuring high reliability:

* **Kyiv City** & **Kyiv Region**
* **Dnipro City** (Dnem & CEK) & **Dnipropetrovsk Region**
* **Odesa Region**
* **Lviv Region**
* **Kharkiv Region**
* **Poltava Region**
* **Cherkasy Region**
* **Chernihiv Region**
* **Zhytomyr Region**
* **Sumy Region**
* **Rivne Region**
* **Ternopil Region**
* **Ivano-Frankivsk Region**
* **Khmelnytskyi Region**
* **Zakarpattia Region**
* **Zaporizhzhia Region**

*(Other regions are supported via standard fallback or standard group logic).*

---

## 🔄 How It Works

### 🧩 Integration Architecture
1.  **Unified Coordinator:** All regions/queues share a single cached data source to minimize network requests.
2.  **Smart Caching:** Data is cached for 10-15 minutes. If you have multiple queues setup, they reuse the same downloaded JSON.
3.  **Precise Ticking:** The integration calculates the next switch time and schedules an internal timer. If the power is off until 18:00, the sensor will switch to "On" exactly at 18:00:00 without waiting for the next API poll.

### 🕒 Timezone Handling
- The API returns the schedule in **local Ukrainian time (Europe/Kyiv)**.  
- The integration converts this to UTC for Home Assistant, ensuring all times are displayed correctly regardless of your HA timezone.

---

## 🔐 Privacy & Security

The integration **does not expose any API keys**.

Access to data is handled via a secure **Cloudflare Worker** proxy that:
- Aggregates data directly from official utility providers.
- Returns a standardized JSON response.
- Requires no private credentials from the user.

---

## ⚙️ Configuration & Usage

### Installation via HACS
The quickest way to install this integration is via [HACS](https://github.com/hacs/integration):
1. Open HACS → Integrations.
2. Search for `Svitlo.live` (or add this repo as a custom repository).
3. Click **Download**.
4. Restart Home Assistant.

### Adding Integration
1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Svitlo.live**.
3. Select your **Region** and **Queue**.

### Changing Queue (New in v3.0)
You don't need to reinstall the integration to change your queue!
1. Go to the integration card in Home Assistant.
2. Click **Configure** (the cogwheel icon ⚙️).
3. Select the new queue/sub-queue from the list.
4. (Optional) Adjust the **Scan Interval** (default: 900 seconds / 15 min).
5. Click **Submit**. 
   *The integration will reload, delete old entities, and create new ones automatically.*

---

## 🧩 Created Entities

| Type | Name | Description |
|------|------|-------------|
| 🟢 **Binary Sensor** | `Electricity status` | True/False power indicator |
| 📘 **Sensor** | `Electricity` | Text status: “Grid ON / OFF” |
| ⏰ **Sensor** | `Next grid connection` | Next power-on time (if currently off) |
| ⚠️ **Sensor** | `Next outage` | Next power-off time (if currently on) |
| 🔄 **Sensor** | `Schedule updated` | Last successful API refresh |
| 📅 **Calendar** | `calendar.svitlo_<region>_<queue>` |  “💡 Electricity available” events (Kyiv local time) |
| ⏳ **Sensor** | `Minutes to grid connection` | Countdown minutes until power restoration. |
| ⏱ **Sensor** | `Minutes to outage` | Countdown minutes until power cut. |

---

## 🤝 Credits

* **[yaroslav2901](https://github.com/yaroslav2901)** — for developing the comprehensive DTEK/YASNO parsers that power the new unified API.
* **[vladmokryi](https://github.com/vladmokryi)** — for the initiative and contribution regarding the Poltava region update.

## 💡 Author

- GitHub: [@chaichuk](https://github.com/chaichuk)  
- Telegram: [@serhii_chaichuk](https://t.me/serhii_chaichuk)

---

## 🪪 License

MIT License © 2025  
Open-source, with no API keys or personal data exposed.

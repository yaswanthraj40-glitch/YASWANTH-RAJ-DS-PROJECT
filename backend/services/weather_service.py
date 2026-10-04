"""
CoolRoute Weather Service
Fetches real weather data from Open-Meteo API (no API key required).
Falls back to clearly-labeled demo data when unavailable.
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests

logger = logging.getLogger(__name__)

# Chennai coordinates
CHENNAI_LAT = 13.0827
CHENNAI_LON = 80.2707

DEMO_DIURNAL_PATTERN = {
    "06:00": 28.5,
    "07:00": 29.2,
    "08:00": 31.0,
    "09:00": 33.5,
    "10:00": 35.8,
    "11:00": 37.9,
    "12:00": 39.5,
    "13:00": 40.8,
    "14:00": 41.2,
    "15:00": 41.0,
    "16:00": 39.8,
    "17:00": 38.2,
    "18:00": 36.5,
    "19:00": 34.8,
    "20:00": 33.2,
    "21:00": 32.0,
    "22:00": 31.0,
    "23:00": 30.2,
    "00:00": 29.5,
}

# Open-Meteo UHI adjustment (urban surface temps 3-8°C higher than air temp)
UHI_OFFSET_MEAN = 5.5
UHI_STD = 1.5


class WeatherService:
    """
    Fetches weather data from Open-Meteo (free, no key needed).
    Applies Urban Heat Island offset to convert air temp → surface temp estimate.
    All converted values are labeled ESTIMATED.
    """

    def __init__(self, lat: float = CHENNAI_LAT, lon: float = CHENNAI_LON):
        self.lat = lat
        self.lon = lon
        self.is_demo = False
        self._cache: Dict = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_current_weather(self) -> Dict:
        """
        Returns current air temperature and estimates surface temperature.
        Source: Open-Meteo current conditions (real).
        Surface LST offset: ESTIMATED (UHI research basis).
        """
        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={self.lat}&longitude={self.lon}"
                f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
                f"&timezone=Asia/Kolkata"
            )
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            current = data.get("current", {})
            air_temp = current.get("temperature_2m")
            if air_temp is None:
                raise ValueError("No temperature in response")

            # UHI adjustment: surface temp estimate
            estimated_lst = round(air_temp + UHI_OFFSET_MEAN, 1)

            self.is_demo = False
            return {
                "air_temperature_c": round(air_temp, 1),
                "estimated_surface_temp_c": estimated_lst,
                "humidity_percent": current.get("relative_humidity_2m"),
                "wind_speed_kmh": current.get("wind_speed_10m"),
                "timestamp": current.get("time"),
                "source": "Open-Meteo (real)",
                "lst_note": "ESTIMATED: Air temp + UHI offset (~5.5°C, based on urban heat island research)",
                "is_demo": False,
            }
        except Exception as e:
            logger.warning(f"Open-Meteo current weather failed: {e}. Using demo data.")
            self.is_demo = True
            return self._demo_current()

    def get_hourly_timeseries(self, date: Optional[str] = None) -> Dict:
        """
        Returns hourly temperature for a given date (default: today).
        Source: Open-Meteo (real air temp) + UHI offset (ESTIMATED surface).
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={self.lat}&longitude={self.lon}"
                f"&hourly=temperature_2m"
                f"&start_date={date}&end_date={date}"
                f"&timezone=Asia/Kolkata"
            )
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            hourly = data.get("hourly", {})
            times = hourly.get("time", [])
            temps = hourly.get("temperature_2m", [])

            if not times or not temps:
                raise ValueError("No hourly data")

            series = []
            for t, temp in zip(times, temps):
                if temp is None:
                    continue
                hour_label = t.split("T")[1][:5]  # "HH:MM"
                # UHI offset varies by hour: higher at noon
                hour_num = int(hour_label.split(":")[0])
                uhi = self._uhi_by_hour(hour_num)
                est_lst = round(temp + uhi, 1)
                series.append({
                    "time": hour_label,
                    "air_temp_c": round(temp, 1),
                    "estimated_lst_c": est_lst,
                    "uhi_offset_c": round(uhi, 1),
                })

            self.is_demo = False
            return {
                "date": date,
                "location": "Chennai, India",
                "timeseries": series,
                "source": "Open-Meteo (real air temp)",
                "lst_note": "ESTIMATED: air temp + hour-varying UHI offset",
                "is_demo": False,
                "peak_hour": self._find_peak(series),
                "morning_avg": self._avg_range(series, 6, 10),
                "noon_avg": self._avg_range(series, 10, 14),
                "afternoon_avg": self._avg_range(series, 14, 18),
                "evening_avg": self._avg_range(series, 18, 22),
            }

        except Exception as e:
            logger.warning(f"Open-Meteo hourly failed: {e}. Using demo data.")
            self.is_demo = True
            return self._demo_timeseries(date)

    def get_historical_weekly(self) -> Dict:
        """
        Returns last 7 days daily max air temps from Open-Meteo archive.
        """
        end = datetime.now()
        start = end - timedelta(days=7)
        start_str = start.strftime("%Y-%m-%d")
        end_str = end.strftime("%Y-%m-%d")

        try:
            url = (
                f"https://archive-api.open-meteo.com/v1/archive?"
                f"latitude={self.lat}&longitude={self.lon}"
                f"&start_date={start_str}&end_date={end_str}"
                f"&daily=temperature_2m_max,temperature_2m_min"
                f"&timezone=Asia/Kolkata"
            )
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            daily = data.get("daily", {})
            dates = daily.get("time", [])
            maxes = daily.get("temperature_2m_max", [])
            mins = daily.get("temperature_2m_min", [])

            history = []
            for d, mx, mn in zip(dates, maxes, mins):
                if mx is None:
                    continue
                history.append({
                    "date": d,
                    "air_temp_max_c": round(mx, 1),
                    "air_temp_min_c": round(mn, 1) if mn else None,
                    "estimated_lst_max_c": round(mx + UHI_OFFSET_MEAN, 1),
                })

            return {
                "history": history,
                "source": "Open-Meteo Archive (real)",
                "is_demo": False,
            }

        except Exception as e:
            logger.warning(f"Open-Meteo archive failed: {e}")
            return {"history": [], "source": "unavailable", "is_demo": True}

    def get_status(self) -> Dict:
        """Return service status for data dashboard."""
        return {
            "service": "WeatherService",
            "provider": "Open-Meteo",
            "api_key_required": False,
            "url": "https://open-meteo.com",
            "is_demo": self.is_demo,
            "data_type": "real" if not self.is_demo else "demo",
            "note": "Air temperature is real. Surface LST is ESTIMATED via UHI offset.",
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _uhi_by_hour(self, hour: int) -> float:
        """Hour-varying UHI offset: peaks at midday, lower at night."""
        # Sinusoidal pattern: max ~8°C at 14:00, min ~3°C at 04:00
        offset = 5.5 + 2.5 * math.sin(math.pi * (hour - 4) / 12)
        return round(max(3.0, min(8.0, offset)), 1)

    def _find_peak(self, series: List[Dict]) -> Dict:
        if not series:
            return {}
        peak = max(series, key=lambda x: x["estimated_lst_c"])
        return {"time": peak["time"], "estimated_lst_c": peak["estimated_lst_c"]}

    def _avg_range(self, series: List[Dict], h_start: int, h_end: int) -> Optional[float]:
        vals = [
            s["estimated_lst_c"]
            for s in series
            if h_start <= int(s["time"].split(":")[0]) < h_end
        ]
        return round(sum(vals) / len(vals), 1) if vals else None

    # ------------------------------------------------------------------
    # Demo fallbacks (clearly labeled)
    # ------------------------------------------------------------------

    def _demo_current(self) -> Dict:
        hour = datetime.now().hour
        air = list(DEMO_DIURNAL_PATTERN.values())[hour % len(DEMO_DIURNAL_PATTERN)]
        return {
            "air_temperature_c": air,
            "estimated_surface_temp_c": round(air + UHI_OFFSET_MEAN, 1),
            "humidity_percent": 72,
            "wind_speed_kmh": 12,
            "timestamp": datetime.now().isoformat(),
            "source": "DEMO DATA — Open-Meteo unavailable",
            "lst_note": "DEMO: Synthetic diurnal pattern based on Chennai climatology",
            "is_demo": True,
        }

    def _demo_timeseries(self, date: str) -> Dict:
        series = []
        for time_str, air in DEMO_DIURNAL_PATTERN.items():
            hour_num = int(time_str.split(":")[0])
            uhi = self._uhi_by_hour(hour_num)
            series.append({
                "time": time_str,
                "air_temp_c": air,
                "estimated_lst_c": round(air + uhi, 1),
                "uhi_offset_c": uhi,
            })
        return {
            "date": date,
            "location": "Chennai, India (DEMO)",
            "timeseries": series,
            "source": "DEMO DATA — not real-time",
            "lst_note": "DEMO: Synthetic diurnal pattern. Not real measurements.",
            "is_demo": True,
            "peak_hour": {"time": "14:00", "estimated_lst_c": series[8]["estimated_lst_c"]},
            "morning_avg": self._avg_range(series, 6, 10),
            "noon_avg": self._avg_range(series, 10, 14),
            "afternoon_avg": self._avg_range(series, 14, 18),
            "evening_avg": self._avg_range(series, 18, 22),
        }

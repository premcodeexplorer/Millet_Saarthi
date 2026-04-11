"""Agent 3 — Smart Market Comparison.

Ports notebooks/agent3_market_comparison.ipynb into a class. Uses free
Nominatim geocoding + OSRM road routing + Agent 2's price model to rank
nearby APMC markets by net price per quintal after transport & commission.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import requests

from app.config import APMC_MARKETS_PATH
from agents.price_agent import PriceAgent

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"
HEADERS = {"User-Agent": "MilletSaarthi/1.0 (academic project)"}


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return float(2 * R * np.arcsin(np.sqrt(a)))


class MarketAgent:
    def __init__(
        self,
        price_agent: Optional[PriceAgent] = None,
        markets_path: Optional[Path] = None,
    ) -> None:
        self.log = logging.getLogger("MarketAgent")
        self.price_agent = price_agent or PriceAgent()

        mp = Path(markets_path or APMC_MARKETS_PATH)
        if not mp.exists():
            raise FileNotFoundError(f"apmc_markets.json not found at {mp}")
        with open(mp) as f:
            md = json.load(f)
        self.markets: list[dict] = md["markets"]
        self.truck_rental_per_km: float = md["truck_rental_per_km"]
        self.truck_capacity: float = md["truck_capacity_quintals"]
        self.msp: dict = md["msp_per_quintal"]
        self.log.info(f"Loaded {len(self.markets)} APMCs")

        self._geo_cache: dict = {}
        self._dist_cache: dict = {}

    # ---------- external APIs ----------
    def geocode(self, location_text: str) -> dict:
        if location_text in self._geo_cache:
            return self._geo_cache[location_text]
        try:
            r = requests.get(
                NOMINATIM_URL,
                params={
                    "q": location_text, "format": "json", "limit": 1,
                    "addressdetails": 1, "countrycodes": "in",
                },
                headers=HEADERS, timeout=10,
            )
            data = r.json()
            if not data:
                return {"error": f"Could not find location: {location_text}"}
            hit = data[0]
            addr = hit.get("address", {})
            result = {
                "lat": float(hit["lat"]),
                "lon": float(hit["lon"]),
                "display_name": hit.get("display_name", location_text),
                "district": addr.get("state_district") or addr.get("county") or addr.get("city") or "Unknown",
                "state": addr.get("state", "Unknown"),
            }
            self._geo_cache[location_text] = result
            return result
        except Exception as e:
            return {"error": str(e)}

    def road_distance(self, lat1, lon1, lat2, lon2) -> tuple[float, float, str]:
        key = (round(lat1, 4), round(lon1, 4), round(lat2, 4), round(lon2, 4))
        if key in self._dist_cache:
            return self._dist_cache[key]
        try:
            url = OSRM_URL.format(lon1=lon1, lat1=lat1, lon2=lon2, lat2=lat2)
            r = requests.get(url, params={"overview": "false"}, timeout=10)
            if r.status_code == 200:
                d = r.json()
                if d.get("code") == "Ok" and d.get("routes"):
                    route = d["routes"][0]
                    result = (
                        round(route["distance"] / 1000, 1),
                        round(route["duration"] / 60, 1),
                        "osrm",
                    )
                    self._dist_cache[key] = result
                    return result
        except requests.RequestException:
            pass
        km = round(haversine_km(lat1, lon1, lat2, lon2) * 1.3, 1)
        result = (km, round(km / 50 * 60, 1), "haversine_fallback")
        self._dist_cache[key] = result
        return result

    def _transport_per_q(self, distance_km: float, qty: float) -> float:
        truck_total = distance_km * self.truck_rental_per_km
        effective = min(qty, self.truck_capacity)
        return truck_total / max(effective, 1)

    # ---------- orchestrator entry ----------
    def predict(self, state: dict) -> dict:
        location_text = state.get("location_text")
        if not location_text:
            raise ValueError("MarketAgent requires 'location_text' in state")
        millet = state["millet"]
        grade = state["grade"]
        qty = state.get("quantity_quintal", 1)
        max_distance_km = state.get("max_distance_km", 300)
        year = state.get("year")
        month = state.get("month")
        if year is None or month is None:
            now = datetime.now()
            year, month = now.year, now.month

        geo = self.geocode(location_text)
        if "error" in geo:
            return {"error": geo["error"]}
        flat, flon = geo["lat"], geo["lon"]

        results = []
        for m in self.markets:
            straight = haversine_km(flat, flon, m["lat"], m["lon"])
            if straight > max_distance_km:
                continue
            dist, dur, src = self.road_distance(flat, flon, m["lat"], m["lon"])
            if dist > max_distance_km:
                continue
            apmc_price = self.price_agent.predict_price_at(
                millet, grade, m["state"], m["district"], year, month
            )
            if apmc_price is None:
                continue
            transport = self._transport_per_q(dist, qty)
            commission = apmc_price * (m["commission_pct"] / 100)
            net_q = apmc_price - transport - commission
            results.append({
                "market": m["name"], "district": m["district"], "state": m["state"],
                "distance_km": dist, "duration_min": dur, "distance_source": src,
                "apmc_price": round(apmc_price, 2),
                "transport_per_q": round(transport, 2),
                "commission_per_q": round(commission, 2),
                "net_price_per_q": round(net_q, 2),
                "total_net_revenue": round(net_q * qty, 2),
            })

        if not results:
            return {"error": "No APMC markets found within range"}

        nearest_5 = sorted(results, key=lambda x: x["distance_km"])[:5]
        best = max(nearest_5, key=lambda x: x["net_price_per_q"])
        local = nearest_5[0]
        msp_value = self.msp.get(millet, 0)

        # Shared-transport opportunity
        shared = None
        if qty < self.truck_capacity:
            candidates = []
            for m in nearest_5:
                if m["market"] == local["market"]:
                    continue
                full_truck_transport = (m["distance_km"] * self.truck_rental_per_km) / self.truck_capacity
                full_net = m["apmc_price"] - full_truck_transport - m["commission_per_q"]
                gain = full_net - local["net_price_per_q"]
                if gain > 0:
                    candidates.append((gain, full_net, m))
            if candidates:
                gain, full_net, target = max(candidates, key=lambda x: x[0])
                partners = int(np.ceil((self.truck_capacity - qty) / max(qty, 1)))
                shared = {
                    "target_market": target["market"],
                    "distance_km": target["distance_km"],
                    "full_truck_net_per_q": round(full_net, 2),
                    "gain_per_q": round(gain, 2),
                    "total_gain": round(gain * qty, 2),
                    "partners_suggested": partners,
                    "message": (
                        f"Team up with ~{partners} other farmers to fill a 100-quintal truck to "
                        f"{target['market']} ({target['distance_km']} km). Net rises to "
                        f"₹{round(full_net,2)}/q (+₹{round(gain,2)}/q vs local). "
                        f"Extra ₹{round(gain*qty,2)} total."
                    ),
                }

        msp_check = {
            "msp": msp_value,
            "your_best_net": best["net_price_per_q"],
            "status": "ABOVE_MSP" if best["net_price_per_q"] >= msp_value else "BELOW_MSP",
            "message": (
                f"Best net ₹{best['net_price_per_q']} is above MSP ₹{msp_value}. Safe to sell."
                if best["net_price_per_q"] >= msp_value else
                f"Best net ₹{best['net_price_per_q']} is BELOW MSP ₹{msp_value}. "
                "Consider FCI/NAFED govt procurement."
            ),
        }

        insights = []
        if best["market"] == local["market"]:
            insights.append(
                f"Your nearest market ({local['market']}) is the best choice. "
                "After transport costs, local gives the highest net return."
            )
        else:
            gain_total = (best["net_price_per_q"] - local["net_price_per_q"]) * qty
            insights.append(
                f"Best among 5 nearest is {best['market']} ({best['distance_km']} km). "
                f"Extra ₹{round(gain_total,2)} vs nearest ({local['market']})."
            )
        insights.append(msp_check["message"])
        if shared:
            insights.append(shared["message"])

        return {
            "farmer_location": {
                "input": location_text,
                "lat": flat, "lon": flon,
                "resolved": geo["display_name"],
                "district": geo["district"], "state": geo["state"],
            },
            "query_month": f"{year}-{month:02d}",
            "local_market": local,
            "best_market": best,
            "top_5_nearest": nearest_5,
            "msp_check": msp_check,
            "shared_transport_opportunity": shared,
            "market_insights": insights,
            "markets_evaluated": len(results),
        }

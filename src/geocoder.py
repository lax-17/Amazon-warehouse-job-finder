"""Geocoding utilities for Amazon Jobs Monitor v2."""

import aiohttp
from typing import Optional, Tuple


class Geocoder:
    """Async geocoder using Photon (OpenStreetMap)."""
    
    PHOTON_URL = "https://photon.komoot.io/api"
    
    def __init__(self, user_agent: str = "AmazonJobsMonitor/2.0"):
        self.user_agent = user_agent
    
    async def geocode(self, location: str) -> Optional[Tuple[float, float]]:
        """Geocode a location string to (lat, lng) coordinates."""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "q": location,
                    "limit": 1,
                }
                headers = {
                    "User-Agent": self.user_agent,
                }
                
                async with session.get(
                    self.PHOTON_URL,
                    params=params,
                    headers=headers
                ) as response:
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
                    
                    if not data.get("features"):
                        return None
                    
                    feature = data["features"][0]
                    coords = feature["geometry"]["coordinates"]
                    # Photon returns [lng, lat], we need [lat, lng]
                    return (coords[1], coords[0])
                    
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None
    
    async def geocode_uk_postcode(self, postcode: str) -> Optional[Tuple[float, float]]:
        """Geocode a UK postcode."""
        # Clean and format postcode
        cleaned = postcode.strip().upper().replace(" ", "")
        return await self.geocode(f"{cleaned}, UK")

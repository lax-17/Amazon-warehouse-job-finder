"""Async job fetcher for Amazon Jobs API."""

import aiohttp
from typing import List, Optional, Dict, Any

from .models import Job, JobSearchResult


class JobFetcher:
    """Async fetcher for Amazon Jobs API."""
    
    def __init__(self, api_url: str, token: str):
        self.api_url = api_url
        self.headers = {
            "accept": "*/*",
            "authorization": token,
            "content-type": "application/json",
            "origin": "https://www.jobsatamazon.co.uk",
            "referer": "https://www.jobsatamazon.co.uk/",
            "user-agent": (
                "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36"
            ),
        }
    
    def _build_query(self) -> str:
        """Build GraphQL query for job search."""
        return """
        query searchJobCardsByLocation($searchJobRequest: SearchJobRequest!) {
          searchJobCardsByLocation(searchJobRequest: $searchJobRequest) {
            nextToken
            jobCards {
              jobId
              jobTitle
              locationName
              city
              state
              postalCode
              employmentType
              jobType
              distance
              __typename
            }
            __typename
          }
        }
        """
    
    def _build_payload(
        self,
        lat: float,
        lng: float,
        radius: float,
        next_token: Optional[str] = None,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """Build request payload."""
        variables = {
            "searchJobRequest": {
                "locale": "en-GB",
                "country": "United Kingdom",
                "pageSize": page_size,
                "geoQueryClause": {
                    "lat": lat,
                    "lng": lng,
                    "unit": "mi",
                    "distance": radius
                },
                "consolidateSchedule": True
            }
        }
        
        if next_token:
            variables["searchJobRequest"]["nextToken"] = next_token
        
        return {
            "operationName": "searchJobCardsByLocation",
            "variables": variables,
            "query": self._build_query()
        }
    
    async def fetch_jobs(
        self,
        session: aiohttp.ClientSession,
        lat: float,
        lng: float,
        radius: float,
        paginate: bool = False
    ) -> JobSearchResult:
        """Fetch jobs from API."""
        all_jobs: List[Job] = []
        next_token: Optional[str] = None
        
        while True:
            payload = self._build_payload(lat, lng, radius, next_token)
            
            async with session.post(
                self.api_url,
                headers=self.headers,
                json=payload
            ) as response:
                if response.status != 200:
                    raise Exception(f"API error: {response.status}")
                
                data = await response.json()
                result = data.get("data", {}).get("searchJobCardsByLocation", {})
                
                job_cards = result.get("jobCards", [])
                for card in job_cards:
                    try:
                        job = Job.from_api_response(card)
                        all_jobs.append(job)
                    except Exception as e:
                        print(f"Error parsing job card: {e}")
                
                next_token = result.get("nextToken")
                
                if not paginate or not next_token:
                    break
        
        return JobSearchResult(
            jobs=all_jobs,
            total_count=len(all_jobs),
            next_token=next_token,
            search_location=f"{lat},{lng}",
            search_radius=radius
        )
    
    async def fetch_single_page(
        self,
        session: aiohttp.ClientSession,
        lat: float,
        lng: float,
        radius: float
    ) -> JobSearchResult:
        """Fetch single page of jobs (no pagination)."""
        return await self.fetch_jobs(session, lat, lng, radius, paginate=False)

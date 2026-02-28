"""Main monitoring loop for Amazon Jobs Monitor v2."""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Optional

import aiohttp
import pytz

from .config import Config
from .database import Database
from .fetcher import JobFetcher
from .geocoder import Geocoder
from .change_detector import ChangeDetector
from .models import JobSearchResult


class JobMonitor:
    """Main job monitor that orchestrates fetching and storage."""
    
    def __init__(self, config: Config):
        self.config = config
        self.db = Database(config.database_path)
        self.geocoder = Geocoder()
        self.change_detector = ChangeDetector(self.db)
        self.running = False
        self.cycle_count = 0
        
        # Setup logging
        self._setup_logging()
        
        # Get token
        try:
            self.token = config.get_token()
            self.logger.info("Token loaded successfully")
        except ValueError as e:
            self.logger.error(f"Failed to load token: {e}")
            raise
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        
        handlers = [logging.FileHandler(self.config.log_file)]
        if self.config.log_to_console:
            handlers.append(logging.StreamHandler(sys.stdout))
        
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=handlers
        )
        self.logger = logging.getLogger(__name__)
    
    async def run(self):
        """Run the monitoring loop."""
        self.running = True
        
        # Setup signal handlers for asyncio (only in main thread)
        import threading
        if threading.current_thread() is threading.main_thread():
            try:
                loop = asyncio.get_running_loop()
                for sig in (signal.SIGINT, signal.SIGTERM):
                    loop.add_signal_handler(sig, self._stop)
            except (ValueError, RuntimeError, NotImplementedError):
                # Fallback for Windows
                signal.signal(signal.SIGINT, self._signal_handler)
                signal.signal(signal.SIGTERM, self._signal_handler)
        else:
            # Running in a thread - signals not available, use a different approach
            self.logger.info("Running in background thread (signal handling disabled)")
        
        # Get search parameters
        location = self.config.default_location
        radius = self.config.default_radius_miles
        
        self.logger.info(f"Starting monitor for {location} within {radius} miles")
        
        # Geocode location
        coords = await self.geocoder.geocode(location)
        if not coords:
            self.logger.error(f"Could not geocode location: {location}")
            return
        
        lat, lng = coords
        self.logger.info(f"Geocoded {location} to {lat}, {lng}")
        
        # Create fetcher
        fetcher = JobFetcher(self.config.amazon_api_url, self.token)
        
        print(f"\n{'='*60}")
        print(f"Amazon Jobs Monitor v2")
        print(f"Location: {location}")
        print(f"Radius: {radius} miles")
        print(f"Polling every {self.config.poll_interval_seconds}s")
        print(f"{'='*60}\n")
        
        # Main loop
        async with aiohttp.ClientSession() as session:
            while self.running:
                cycle_start = datetime.utcnow()
                self.cycle_count += 1
                
                try:
                    # Fetch jobs
                    result = await fetcher.fetch_jobs(
                        session, lat, lng, radius, paginate=False
                    )
                    
                    # Detect and record changes (now async for Telegram notifications)
                    changes = await self.change_detector.detect_changes(result.jobs)
                    
                    # Log status
                    await self._log_status(result, changes, location, radius)
                    
                    # Display all active jobs with full details
                    active_jobs = [j for j in result.jobs]
                    if active_jobs:
                        print(f"\n  Active Jobs ({len(active_jobs)}):")
                        print(f"  {'-'*80}")
                        for i, job in enumerate(active_jobs[:10], 1):  # Show first 10
                            location_str = job.location_name or job.city or "Unknown location"
                            job_type_str = ""
                            if job.is_flexible:
                                job_type_str += " [FLEXIBLE]"
                            if job.is_under_20h:
                                job_type_str += " [UNDER-20H]"
                            print(f"  {i}. {job.job_title}")
                            print(f"     Location: {location_str}{job_type_str}")
                            print(f"     Type: {job.employment_type or 'N/A'} | Distance: {job.distance or 0:.1f} mi")
                            print()
                        if len(active_jobs) > 10:
                            print(f"  ... and {len(active_jobs) - 10} more jobs")
                    
                    # Log changes if any
                    if changes.has_changes:
                        print(f"\n  Changes this cycle:")
                        if changes.new_jobs:
                            print(f"  🟢 NEW JOBS ({len(changes.new_jobs)}):")
                            for job in changes.new_jobs:
                                loc = job.location_name or job.city or "Unknown"
                                print(f"     + {job.job_title} at {loc}")
                        
                        if changes.updated_jobs:
                            print(f"  🟡 UPDATED JOBS ({len(changes.updated_jobs)}):")
                            for job in changes.updated_jobs:
                                loc = job.location_name or job.city or "Unknown"
                                print(f"     ~ {job.job_title} at {loc}")
                        
                        if changes.removed_jobs:
                            print(f"  🔴 REMOVED JOBS ({len(changes.removed_jobs)}):")
                            for job in changes.removed_jobs:
                                loc = job.location_name or job.city or "Unknown"
                                print(f"     - {job.job_title} at {loc}")
                        print()
                    
                except Exception as e:
                    self.logger.error(f"Error in cycle {self.cycle_count}: {e}")
                
                # Sleep until next cycle (check running flag every 0.5s for quick shutdown)
                elapsed = (datetime.utcnow() - cycle_start).total_seconds()
                sleep_time = max(0.0, self.config.poll_interval_seconds - elapsed)
                
                while sleep_time > 0 and self.running:
                    await asyncio.sleep(min(0.5, sleep_time))
                    sleep_time -= 0.5
        
        self.logger.info(f"Monitor stopped after {self.cycle_count} cycles")
    
    async def _log_status(self, result: JobSearchResult, changes, location: str, radius: float):
        """Log current status with London timezone."""
        london_tz = pytz.timezone('Europe/London')
        local_time = datetime.now(london_tz)
        timestamp = local_time.strftime("%d/%m/%Y %H:%M:%S")
        
        # Count job types
        part_time = sum(1 for j in result.jobs if j.is_part_time)
        full_time = sum(1 for j in result.jobs if j.is_full_time)
        flexible = sum(1 for j in result.jobs if j.is_flexible)
        under_20h = sum(1 for j in result.jobs if j.is_under_20h)
        
        # Build status line
        status_parts = [
            f"[{timestamp}]",
            f"Total: {len(result.jobs)}",
            f"PT: {part_time}",
            f"FT: {full_time}",
            f"Flex: {flexible}",
            f"<20h: {under_20h}"
        ]
        
        if changes.has_changes:
            status_parts.append(f"| Changes: {changes.summary}")
        
        print(" | ".join(status_parts))
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self._stop()
    
    def _stop(self):
        """Stop the monitor."""
        self.logger.info("Shutdown signal received")
        self.running = False
        print("\nStopping monitor...", flush=True)

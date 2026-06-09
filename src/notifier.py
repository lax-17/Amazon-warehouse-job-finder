"""Telegram notifier for Amazon Jobs Monitor v2."""

import os
import aiohttp
from typing import Optional

from .models import Job


class TelegramNotifier:
    """Send Telegram notifications for new jobs."""
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
        self.enabled = bool(self.bot_token and self.chat_id)
    
    async def send_job_notification(self, job: Job) -> bool:
        """Send notification for a new job."""
        if not self.enabled:
            return False
        
        # Build message
        location = job.location_name or job.city or "Unknown location"
        hours_info = f"\n⏰ Hours: {job.hours_per_week}/week" if job.hours_per_week else ""
        distance_str = f"{job.distance:.1f}" if job.distance is not None else "N/A"
        
        site_info = f"\n🏭 Site: {job.site_code}" if job.site_code else ""
        message = f"""🆕 <b>New Job Alert!</b>

📋 <b>{job.job_title}</b>
📍 Location: {location}
💼 Type: {job.employment_type or 'N/A'}{hours_info}
🚗 Distance: {distance_str} miles{site_info}

{'✅ Flexible hours' if job.is_flexible else ''}
{'⏱️ Under 20h/week' if job.is_under_20h else ''}

<a href="https://www.jobsatamazon.co.uk">View on Amazon Jobs</a>
"""
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        print(f"✓ Telegram notification sent for: {job.job_title}")
                        return True
                    else:
                        print(f"✗ Telegram failed: {response.status}")
                        return False
        except Exception as e:
            print(f"✗ Telegram error: {e}")
            return False
    
    async def send_new_jobs_summary(self, jobs: list[Job]) -> bool:
        """Send summary of multiple new jobs."""
        if not self.enabled or not jobs:
            return False
        
        if len(jobs) == 1:
            return await self.send_job_notification(jobs[0])
        
        # Multiple jobs - send summary
        message = f"🆕 <b>{len(jobs)} New Jobs Found!</b>\n\n"
        
        for i, job in enumerate(jobs[:5], 1):  # Show first 5
            location = job.location_name or job.city or "Unknown"
            message += f"{i}. {job.job_title} at {location}\n"
        
        if len(jobs) > 5:
            message += f"\n...and {len(jobs) - 5} more jobs\n"
        
        message += "\n<a href='http://127.0.0.1:5000'>View Dashboard</a>"
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    return response.status == 200
        except Exception as e:
            print(f"✗ Telegram error: {e}")
            return False

#!/usr/bin/env python3
"""Test script to send a dummy job alert via Telegram."""

import asyncio
import sys
sys.path.insert(0, '.')

from src.notifier import TelegramNotifier
from src.models import Job
from datetime import datetime

async def send_dummy_alert():
    """Send a dummy job alert to test Telegram notifications."""
    
    # Create dummy job
    dummy_job = Job(
        job_id="test-job-001",
        job_title="Warehouse Associate - 40 hours per week",
        location_name="Leeds Distribution Center",
        city="Leeds",
        state="West Yorkshire",
        postal_code="LS1 1AA",
        employment_type="Full-Time",
        job_type="full-time",
        distance=5.2,
        hours_per_week=40,
        is_flexible=True,
        is_under_20h=False,
        first_seen=datetime.utcnow(),
        last_seen=datetime.utcnow(),
        last_updated=datetime.utcnow()
    )
    
    # Initialize notifier (reads from config.env)
    notifier = TelegramNotifier()
    
    if not notifier.enabled:
        print("⚠️  Telegram not configured!")
        print("\nPlease add to config.env:")
        print("TELEGRAM_BOT_TOKEN=your_bot_token")
        print("TELEGRAM_CHAT_ID=your_chat_id")
        print("\nTo get these:")
        print("1. Message @BotFather on Telegram to create a bot")
        print("2. Message @userinfobot to get your chat ID")
        return
    
    print("📨 Sending dummy job alert...")
    success = await notifier.send_job_notification(dummy_job)
    
    if success:
        print("✅ Dummy alert sent successfully!")
        print("\n📱 Check your Telegram for the test message")
    else:
        print("❌ Failed to send alert")
        print("Check your TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in config.env")

if __name__ == "__main__":
    asyncio.run(send_dummy_alert())

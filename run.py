#!/usr/bin/env python3
"""
Amazon Jobs Monitor v2 - Entry Point

Run the job monitor or web dashboard.
"""

import argparse
import asyncio
import sys

from src.config import Config
from src.monitor import JobMonitor
from web.app import create_app


def run_monitor():
    """Run the job monitoring loop."""
    config = Config()
    monitor = JobMonitor(config)
    
    try:
        asyncio.run(monitor.run())
    except KeyboardInterrupt:
        print("\nMonitor stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


def run_web():
    """Run the web dashboard with background monitor."""
    config = Config()
    app = create_app(config, start_monitor=True)
    
    host = config.web_host
    port = config.web_port
    debug = config.web_debug
    
    print("\n" + "="*60)
    print("Amazon Jobs Monitor v2 - Web Dashboard")
    print("="*60)
    print(f"\n🌐 Web dashboard: http://{host}:{port}")
    print("📊 The monitor is running in background")
    print("🔄 Fetching new jobs every 10 seconds")
    print("\nPress Ctrl+C to stop both web server and monitor")
    print("="*60 + "\n")
    
    app.run(host=host, port=port, debug=debug, use_reloader=False)


def main():
    parser = argparse.ArgumentParser(
        description="Amazon Jobs Monitor v2"
    )
    parser.add_argument(
        "mode",
        choices=["monitor", "web", "both"],
        default="monitor",
        nargs="?",
        help="Run mode: monitor (fetch jobs), web (dashboard), or both"
    )
    
    args = parser.parse_args()
    
    if args.mode == "monitor":
        run_monitor()
    elif args.mode == "web":
        run_web()
    elif args.mode == "both":
        print("'both' mode not yet implemented. Run monitor and web separately.")
        sys.exit(1)


if __name__ == "__main__":
    main()

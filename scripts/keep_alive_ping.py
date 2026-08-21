#!/usr/bin/env python3
"""
Pings the deployed app's health endpoint to prevent Render's free-tier
service from spinning down after ~15 minutes of inactivity.
This script does nothing by itself — it must be triggered on a schedule
by an external service (see instructions below), since Render's own
free-tier service is exactly the thing this is working around.
"""
import sys
import urllib.request

APP_HEALTH_URL = "https://smarthealthsync.onrender.com/api/health"

def main():
    try:
        with urllib.request.urlopen(APP_HEALTH_URL, timeout=20) as resp:
            print(f"Ping OK: {resp.status}")
            return 0
    except Exception as exc:
        print(f"Ping failed: {exc}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

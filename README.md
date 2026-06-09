# Amazon Jobs Monitor v2

Monitor UK Amazon warehouse jobs from the public jobs API, with alerts to Telegram, a web dashboard, change tracking, and optional site identification by postcode prefix.

## Features
- Monitors multiple locations; dedupes jobs across searches by `jobId`.
- Stores jobs and history in SQLite.
- Sends per-job Telegram alerts for new jobs.
- Optional: maps postcode prefixes to known Amazon site codes (`DLS4`, `LBA5`, `MAN1`, etc.) via `SITE_POSTCODE_MAP`.
- Interactive startup prompts for locations and poll interval.

## Setup
1. Install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
2. Copy the example config and edit secrets:
```bash
cp config.env.example config.env
```

## config.env
| Variable | Description |
|---|---|
| `AMAZON_JOBS_TOKEN` | Amazon Jobs API bearer token |
| `DEFAULT_LOCATION` | Semicolon-separated locations (e.g. `Leeds, UK; Manchester, UK`) |
| `DEFAULT_RADIUS_MILES` | Search radius in miles |
| `POLL_INTERVAL_SECONDS` | Poll interval in seconds |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Telegram chat/group id |
| `SITE_POSTCODE_MAP` | Optional postcode-prefix to site-code mapping |

## Run
```bash
python3 -m src.monitor
# or if you have an entry point:
python run.py monitor
```
You can also launch the web dashboard separately:
```bash
python run.py web
```

## Notes
- When a webhook is running through GitHub Actions, allow it to create checks before setting it to "Required".

## Disclaimer
This is for educational use only.

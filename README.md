# Amazon Jobs Monitor v2

A better version of the Amazon Jobs monitoring tool with database storage, job change tracking, and a web dashboard.

## Features

- **Async Job Fetching**: Uses `aiohttp` for efficient API requests
- **Database Storage**: SQLite database for persistent job storage
- **Change Detection**: Tracks new, updated, and removed jobs
- **Web Dashboard**: Flask-based web interface to view jobs
- **Job History**: Complete audit trail of all job changes
- **Flexible Scheduling**: Configurable polling intervals
- **Proper Logging**: Structured logging with file and console output

## Project Structure

```
amazon_jobs_monitor_v2/
├── src/                  # Core modules
│   ├── config.py         # Configuration management
│   ├── models.py         # Pydantic data models
│   ├── database.py       # SQLite database operations
│   ├── geocoder.py       # Location geocoding
│   ├── fetcher.py        # Async job fetching
│   ├── change_detector.py # Job change detection
│   └── monitor.py        # Main monitoring loop
├── web/                  # Web dashboard
│   ├── app.py            # Flask application
│   └── templates/        # HTML templates
├── data/                 # Database and logs
├── run.py                # Entry point
├── requirements.txt      # Dependencies
├── config.env.example    # Example configuration
└── README.md             # This file
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy the example configuration:
```bash
cp config.env.example config.env
```

3. Edit `config.env` and add your Amazon Jobs API token.

## Getting the API Token

1. Open https://www.jobsatamazon.co.uk and start a job search
2. Open Developer Tools (F12) → Network tab
3. Find a request to `appsync-api.eu-west-1.amazonaws.com/graphql`
4. Copy the entire 'authorization' header value (starts with 'Bearer Status|...')
5. Paste it into `config.env` or create a `.amazon_jobs_token` file

## Usage

### Run the Monitor

Fetch and monitor jobs continuously:

```bash
python run.py monitor
```

### Run the Web Dashboard

View jobs in your browser:

```bash
python run.py web
```

Then open http://127.0.0.1:5000 in your browser.

## Configuration

Edit `config.env` to customize:

| Variable | Description | Default |
|----------|-------------|---------|
| `AMAZON_JOBS_TOKEN` | API bearer token | (required) |
| `DATABASE_PATH` | SQLite database file | `data/jobs.db` |
| `POLL_INTERVAL_SECONDS` | Seconds between polls | `60` |
| `DEFAULT_LOCATION` | Default search location | `Leeds, UK` |
| `DEFAULT_RADIUS_MILES` | Default search radius | `50` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `WEB_PORT` | Dashboard port | `5000` |

## Database Schema

### jobs
- `job_id` (PRIMARY KEY)
- `job_title`, `location_name`, `city`, `state`, `postal_code`
- `employment_type`, `job_type`, `distance`
- `is_flexible`, `is_under_20h`, `status`
- `first_seen`, `last_seen`, `last_updated`
- `raw_data`

### job_history
- `id` (PRIMARY KEY)
- `job_id`, `change_type` (new/updated/removed)
- `previous_values`, `new_values`
- `timestamp`

## Improvements Over v1

1. **Database instead of JSON files**: Better performance and querying
2. **Change tracking**: Know when jobs are added, updated, or removed
3. **Web dashboard**: View jobs in a browser instead of terminal
4. **Async operations**: Better performance with aiohttp
5. **Proper architecture**: Separated concerns with modules
6. **Type safety**: Pydantic models for data validation
7. **Better logging**: Configurable logging with levels
8. **Signal handling**: Graceful shutdown on Ctrl+C

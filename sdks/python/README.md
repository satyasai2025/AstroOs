# astroos

Official Python SDK for the AstroOS Vedic Astrology API.

[![PyPI version](https://badge.fury.io/py/astroos.svg)](https://badge.fury.io/py/astroos)

## Installation

```bash
pip install astroos
```

## Quick Start

```python
from astroos import AstroOSClient, AstroOSError

# Initialize client
client = AstroOSClient(
    base_url="https://api.astroos.io/v1",
    api_key="your-api-key",
)

# Compute a birth chart
chart = client.chart.compute(
    birth_datetime_utc="1990-01-01T12:00:00Z",
    latitude=25.0,
    longitude=80.0,
)

# Generate a report
report = client.reports.generate_chart(
    birth_datetime_utc="1990-01-01T12:00:00Z",
    latitude=25.0,
    longitude=80.0,
    title="My Vedic Chart",
    subject_name="John Doe",
)

# Export as PDF
pdf_bytes = client.reports.generate_pdf(
    birth_datetime_utc="1990-01-01T12:00:00Z",
    latitude=25.0,
    longitude=80.0,
)

# Export as CSV
csv_content = client.reports.generate_csv(
    birth_datetime_utc="1990-01-01T12:00:00Z",
    latitude=25.0,
    longitude=80.0,
)

# Error handling
try:
    result = client.chart.compute(...)
except AstroOSError as e:
    print(f"Client error: {e.message}")
```

## Configuration

Load configuration from environment variables:

```bash
export ASTROOS_BASE_URL="https://api.astroos.io/v1"
export ASTROOS_API_KEY="your-api-key"
```

```python
from astroos import AstroOSClient, SdkConfig

config = SdkConfig.from_env()
client = AstroOSClient(config=config)
```

Load from file:

```python
config = SdkConfig.from_file("astroos-config.json")
client = AstroOSClient(config=config)
```

## API Reference

### Authentication

```python
client.auth.register(email="user@example.com", password="secret", display_name="User")
client.auth.login(email="user@example.com", password="secret")
client.auth.me()
```

### Charts

```python
# Compute D1 birth chart
client.chart.compute(birth_datetime_utc, latitude, longitude, ayanamsa="lahiri", house_system="W")

# List available vargas
client.divisional.compute_all(birth_datetime_utc, latitude, longitude)
```

### Dasha

```python
client.dasha.compute("vimshottari", birth_datetime_utc, latitude, longitude, max_depth=3)
```

### Events

```python
# For timeline tracking
events = client.events.list(chart_id="...")
client.events.create(chart_id, event_date, title, category, description)
```

### Reports

```python
# Generate report
report = client.reports.generate_chart(...)

# PDF export
pdf = client.reports.generate_pdf(...)

# CSV export
csv = client.reports.generate_csv(...)

# List templates
templates = client.reports.list_templates()
```

### AI Assistant

```python
explanation = client.ai.explain(topic="raja_yoga", source_data={...})
```

## Error Types

```python
from astroos import (
    AstroOSError,
    AstroOSAuthError,
    AstroOSValidationError,
    AstroOSRateLimitError,
    AstroOSServerError,
    AstroOSNotFoundError,
)
```

## Requirements

- Python 3.11+
- httpx >= 0.27.0

## License

MIT
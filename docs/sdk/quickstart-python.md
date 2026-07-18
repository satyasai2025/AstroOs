# AstroOS Python SDK Quickstart

## Installation

```bash
pip install astroos
```

## Configuration

```python
from astroos import AstroOSClient, SdkConfig

# Basic configuration
client = AstroOSClient(
    base_url="https://api.astroos.io/v1",
    api_key="your-api-key"
)
```

## Usage Examples

### Authentication

```python
# Register a new user
client.auth.register(
    email="user@example.com",
    password="secure-password",
    display_name="User Name"
)

# Login
tokens = client.auth.login(
    email="user@example.com",
    password="secure-password"
)
# Returns: {"access_token": "...", "refresh_token": "..."}

# Get current user info
user = client.auth.me()
```

### Computing Charts

```python
# Compute a birth chart (D1)
chart = client.chart.compute(
    birth_datetime_utc="1990-01-01T12:00:00Z",
    latitude=25.0,
    longitude=80.0,
    ayanamsa="lahiri",
    house_system="W"
)
```

### Divisional Charts

```python
# Compute all vargas (D2-D60)
vargas = client.divisional.compute_all(
    birth_datetime_utc="1990-01-01T12:00:00Z",
    latitude=25.0,
    longitude=80.0
)
```

### Dasha Periods

```python
# Compute Vimshottari Dasha
dasha = client.dasha.compute(
    system="vimshottari",
    birth_datetime_utc="1990-01-01T12:00:00Z",
    latitude=25.0,
    longitude=80.0,
    max_depth=3
)
# max_depth: 1=Mahadasha only, 2=+Antardasha, 3=+Pratyantar
```

### Events & Timeline

```python
# Create an event
event = client.events.create(
    chart_id="chart-uuid",
    event_date="2024-01-15",
    title="Career Event",
    category="career"
)

# List events
events = client.events.list(chart_id="chart-uuid", category="career")
```

### Reports

```python
# Generate a chart report
report = client.reports.generate_chart(
    birth_datetime_utc="1990-01-01T12:00:00Z",
    latitude=25.0,
    longitude=80.0,
    title="My Vedic Birth Chart",
    subject_name="John Doe"
)

# Export as PDF
pdf_bytes = client.reports.generate_pdf(
    birth_datetime_utc="1990-01-01T12:00:00Z",
    latitude=25.0,
    longitude=80.0
)
# Returns: bytes (PDF file)

# Export as CSV
csv_content = client.reports.generate_csv(
    birth_datetime_utc="1990-01-01T12:00:00Z",
    latitude=25.0,
    longitude=80.0
)
# Returns: str (CSV content)

# List available templates
templates = client.reports.list_templates()
# Returns: ["horoscope.html", "marriage.html", ...]
```

### AI Assistant

```python
# Get explanation for a yoga
explanation = client.ai.explain(
    topic="raja_yoga",
    source_data={"planet": "Sun", "house": 10}
)
```

### Complete Analysis Workflow

```python
# Run full analysis pipeline
analysis = client.workflow.analyze(
    birth_datetime_utc="1990-01-01T12:00:00Z",
    latitude=25.0,
    longitude=80.0,
    ayanamsa="lahiri",
    house_system="W"
)
# Returns: chart, vargas, dasha, yogas, rules, citations, verification
```

## Error Handling

```python
from astroos import (
    AstroOSError,
    AstroOSAuthError,
    AstroOSRateLimitError,
    AstroOSServerError
)

try:
    chart = client.chart.compute(...)
except AstroOSAuthError as e:
    print(f"Authentication failed: {e.message}")
except AstroOSRateLimitError as e:
    print(f"Rate limited: {e.message}")
except AstroOSError as e:
    print(f"API error: {e.message}")
```

## Environment Variables

```bash
# Set in .env or shell
ASTROOS_BASE_URL=https://api.astroos.io/v1
ASTROOS_API_KEY=your-api-key
ASTROOS_ACCESS_TOKEN=your-access-token  # optional
```

Then load via:

```python
config = SdkConfig.from_env()
client = AstroOSClient(config=config)
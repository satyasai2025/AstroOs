# AstroOS TypeScript SDK Quickstart

## Installation

```bash
npm install @astroos/sdk
```

## Configuration

```typescript
import { AstroOSClient, SdkConfig } from "@astroos/sdk";

// Basic configuration
const client = new AstroOSClient({
  baseUrl: "https://api.astroos.io/v1",
  apiKey: "your-api-key"
});
```

## Usage Examples

### Authentication

```typescript
// Register a new user
await client.auth.register(
  "user@example.com",
  "secure-password",
  "User Name"
);

// Login
const tokens = await client.auth.login(
  "user@example.com",
  "secure-password"
);
// Returns: { access_token: "...", refresh_token: "..." }

// Get current user info
const user = await client.auth.me();
```

### Computing Charts

```typescript
// Compute a birth chart (D1)
const chart = await client.chart.compute({
  birthDatetimeUtc: "1990-01-01T12:00:00Z",
  latitude: 25.0,
  longitude: 80.0,
  ayanamsa: "lahiri",
  houseSystem: "W"
});
```

### Divisional Charts

```typescript
// Compute all vargas (D2-D60)
const vargas = await client.divisional.compute(
  "all", // or specific varga: "D9"
  { birthDatetimeUtc: "1990-01-01T12:00:00Z", latitude: 25.0, longitude: 80.0 }
);
```

### Dasha Periods

```typescript
// Compute Vimshottari Dasha
const dasha = await client.dasha.compute(
  "vimshottari",
  { birthDatetimeUtc: "1990-01-01T12:00:00Z", latitude: 25.0, longitude: 80.0 },
  3 // max_depth: 1=Mahadasha, 2=+Antardasha, 3=+Pratyantar
);
```

### Events & Timeline

```typescript
// Create an event
await client.events.create({
  chartId: "chart-uuid",
  eventDate: "2024-01-15",
  title: "Career Event",
  category: "career"
});

// List events
const events = await client.events.list("chart-uuid", "career");
```

### Reports

```typescript
// Generate a chart report
const report = await client.reports.generateChart({
  birthDatetimeUtc: "1990-01-01T12:00:00Z",
  latitude: 25.0,
  longitude: 80.0,
  title: "My Vedic Birth Chart",
  subjectName: "John Doe"
});

// Export as PDF
const pdfBlob = await client.reports.generatePdf({
  birthDatetimeUtc: "1990-01-01T12:00:00Z",
  latitude: 25.0,
  longitude: 80.0
});
// Returns: Blob

// Export as CSV
const csv = await client.reports.generateCsv({
  birthDatetimeUtc: "1990-01-01T12:00:00Z",
  latitude: 25.0,
  longitude: 80.0
});

// List available templates
const templates = await client.reports.listTemplates();
```

### AI Assistant

```typescript
// Get explanation for a yoga
const explanation = await client.ai.explain(
  "raja_yoga",
  { planet: "Sun", house: 10 }
);
```

### Complete Analysis Workflow

```typescript
// Run full analysis pipeline
const analysis = await client.workflow.analyze({
  birthDatetimeUtc: "1990-01-01T12:00:00Z",
  latitude: 25.0,
  longitude: 80.0,
  ayanamsa: "lahiri",
  houseSystem: "W"
});
```

## Environment Variables

```bash
# Set in .env or shell
ASTROOS_BASE_URL=https://api.astroos.io/v1
ASTROOS_API_KEY=your-api-key
```

Then load via:

```typescript
const config: SdkConfig = {
  baseUrl: process.env.ASTROOS_BASE_URL,
  apiKey: process.env.ASTROOS_API_KEY,
};
const client = new AstroOSClient(config);
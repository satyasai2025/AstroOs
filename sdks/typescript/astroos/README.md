# @astroos/sdk

Official TypeScript SDK for AstroOS Vedic Astrology API.

[![npm version](https://badge.fury.io/js/@astroos%2Fsdk.svg)](https://badge.fury.io/js/@astroos%2Fsdk)

## Installation

```bash
npm install @astroos/sdk
```

## Quick Start

```typescript
import { AstroOSClient } from "@astroos/sdk";

// Initialize client
const client = new AstroOSClient({ apiKey: "your-api-key" });

// Compute a birth chart
const chart = await client.chart.compute({
  birthDatetimeUtc: "1990-01-01T12:00:00Z",
  latitude: 25.0,
  longitude: 80.0,
});

// Generate a report
const report = await client.reports.generateChart({
  birthDatetimeUtc: "1990-01-01T12:00:00Z",
  latitude: 25.0,
  longitude: 80.0,
  title: "My Vedic Chart",
  subjectName: "John Doe",
});

// Export as PDF
const pdfBlob = await client.reports.generatePdf({
  birthDatetimeUtc: "1990-01-01T12:00:00Z",
  latitude: 25.0,
  longitude: 80.0,
});
```

## Configuration

```typescript
const client = new AstroOSClient({
  baseUrl: "https://api.astroos.io/v1",
  apiKey: "your-api-key",
  timeout: 30,
});
```

## API Reference

### Authentication

```typescript
await client.auth.register("user@example.com", "password", "User Name");
await client.auth.login("user@example.com", "password");
await client.auth.me();
```

### Charts

```typescript
await client.chart.compute({ birthDatetimeUtc, latitude, longitude });
```

### Dasha

```typescript
await client.dasha.compute("vimshottari", { birthDatetimeUtc, latitude, longitude }, maxDepth: 3);
```

### Events

```typescript
await client.events.list(chartId, category?);
await client.events.create({ chartId, eventDate, title, category? });
await client.events.delete(eventId);
```

### Reports

```typescript
await client.reports.generateChart(...);
await client.reports.generatePdf(...);
await client.reports.generateCsv(...);
await client.reports.listTemplates();
```

### AI

```typescript
await client.ai.explain("raja_yoga", { ... });
```

### Workflow

```typescript
await client.workflow.analyze({ birthDatetimeUtc, latitude, longitude });
```

### Health

```typescript
await client.health.check();
```

## Requirements

- Node.js 20+
- zod >= 3.23.0

## License

MIT
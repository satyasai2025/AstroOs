# Dataset Import Framework — Architecture

## Overview

The Dataset Import Framework is a generic, extensible pipeline for importing external datasets into the AstroOS canonical dataset format. It implements a seven-stage pipeline where source-specific logic is isolated in adapters, keeping the core pipeline format-agnostic.

```
Source File (Excel/CSV/JSON/API)
    ↓
[1. Source Adapter]  — reads raw data, emits RawRecord objects
    ↓
[2. Schema Mapping]  — maps source columns → AstroOS fields
    ↓
[3. Validation]      — validates against field rules (L1 schema / L2 quality)
    ↓
[4. Normalization]   — date/time assembly, coordinate precision, string cleanup
    ↓
[5. Deduplication]   — identifies and removes duplicate records
    ↓
[6. Quality Score]   — RDO §3 weighted quality assessment
    ↓
[7. Export]          — CSV/JSON/JSONL + metadata + quality report
```

## Directory Structure

```
apps/api/services/dataset_import/
├── __init__.py              # Exports ImportPipeline
├── framework.py             # ImportPipeline orchestrator + ImportConfig + ImportValidationReport
├── adapter_base.py          # SourceAdapter ABC, RawRecord, ColumnMapping
├── schema_mapper.py         # SchemaMapper: source → AstroOS field mapping
├── validator.py             # Validator: L1/L2 rule checking
├── normalizer.py            # Normalizer: date assembly, coordinate precision, trim
├── deduplicator.py          # Deduplicator: key-based duplicate detection
├── quality_scorer.py        # QualityScorer: RDO §3 six-dimension scoring
├── exporter.py              # Exporter: CSV/JSON/JSONL + metadata generation
└── adapters/
    ├── __init__.py
    ├── excel_adapter.py           # Generic Excel reader
    └── cohort_excel_adapter.py    # Cohort Excel column mapping + metadata
```

## Extension Mechanism

To add a new source adapter:

1. Create `apps/api/services/dataset_import/adapters/new_adapter.py`
2. Subclass `SourceAdapter` (or `ExcelAdapter` for Excel variants)
3. Implement `read()`, `get_source_metadata()`, `get_column_definitions()`
4. Add `get_column_mappings()` for source-specific column mapping
5. Add `get_normalization_rules()` and `get_dedup_key_fields()`
6. Register in `adapters/__init__.py`

No changes to the core pipeline are needed.

## Adapter Interface

```python
class SourceAdapter(ABC):
    @abstractmethod
    def read(self, file_path: str) -> Iterator[RawRecord]: ...
    @abstractmethod
    def get_source_metadata(self, file_path: str) -> Dict[str, Any]: ...
    @abstractmethod
    def get_column_definitions(self, file_path: str) -> List[ColumnDefinition]: ...
```

## Data Flow

```
RawRecord(data, source_index, source_file, source_sheet)
    ↓ SchemaMapper.map_record()
Dict[str, Any]  (canonical field names)
    ↓ Validator.validate_batch()
ValidationResult (pass/fail per record)
    ↓ Normalizer.normalize_batch()
normalized records + NormalizationAction list
    ↓ Deduplicator.deduplicate()
unique records + DeduplicationReport
    ↓ QualityScorer.score()
QualityAssessment (6 weighted dimensions → tier)
    ↓ Exporter.export_csv/json/jsonl()
ExportResult (file path, checksum, size)
    ↓ Exporter.generate_metadata()
_metadata.json
    ↓
ImportValidationReport
```

## Quality Scoring (RDO §3)

| Dimension | Weight | Scoring |
|---|---|---|
| Completeness | 0.25 | field population ratio |
| Accuracy | 0.25 | validation pass rate |
| Consistency | 0.15 | consistency rule pass rate |
| Coverage | 0.15 | scope coverage percentage |
| Timeliness | 0.10 | data freshness |
| Provenance | 0.10 | source attribution quality |

Tier: A (≥0.90), B (≥0.75), C (≥0.50), D (≥0.25), F (<0.25)

## Testing Strategy

- **Unit tests**: SchemaMapper, Validator, Deduplicator, Normalizer, QualityScorer, Exporter — pure logic, no I/O
- **Integration tests**: Full pipeline against synthetic Excel fixtures — adapter read, map, validate, dedup, score, export
- **Test fixtures**: Temporary directories for output; mocked adapters for unit tests

## First Dataset: RS-COHORT

**Dataset ID**: `ASTRO-RS-COHORT-v0.1.0`

| Metric | Value |
|---|---|
| Source records | 57,466 |
| Records imported | 49,964 |
| Validation failures | 1,206 |
| Duplicates removed | 1 |
| Quality score | 1.00 (Tier A) |
| Completeness | 99.7% |
| Export format | CSV (5.6 MB) |

Output (original import): `datasets/rs/cohort/ASTRO-RS-COHORT-v0.1.0/` — superseded 2026-07-17 by the Research Data Office's promoted-to-Stable copy at `research-data/research/cohort/ASTRO-RS-COHORT-v1.0.0/` (identical content); the latter is now canonical.

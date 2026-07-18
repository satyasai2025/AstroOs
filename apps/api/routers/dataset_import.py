"""
AstroOS — Dataset Import Router

Endpoints for importing and validating datasets through the import pipeline.
Supports CSV, Excel, JSON, and JSONL formats.
"""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from apps.api.services.dataset_import.adapters.csv_adapter import CsvAdapter
from apps.api.services.dataset_import.adapters.excel_adapter import ExcelAdapter
from apps.api.services.dataset_import.adapters.json_adapter import JsonAdapter
from apps.api.dependencies import get_dataset_service
from apps.api.services.dataset_import.framework import ImportConfig, ImportPipeline
from apps.api.services.dataset_service import DatasetService
from apps.api.services.dataset_import.validator import (
    ValidationLevel,
    Validator,
    latitude_in_range,
    longitude_in_range,
    required_field_not_none,
)

router = APIRouter(prefix="/api/v1/datasets", tags=["Datasets"])

# In-memory job tracker (volatile, survives only API process lifetime)
_import_jobs: Dict[str, Dict[str, Any]] = {}


def _detect_adapter_from_ext(filename: str):
    """Detect the appropriate adapter from file extension."""
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".csv":
        return CsvAdapter()
    elif ext in (".xlsx", ".xls"):
        return ExcelAdapter()
    elif ext in (".json", ".jsonl"):
        return JsonAdapter()
    return None


@router.post("/import", status_code=202)
async def import_dataset(
    file: UploadFile = File(...),
    dataset_id: str = Form(...),
    adapter_type: str = Form("auto"),
    export_format: str = Form("CSV"),
    dataset_service: DatasetService = Depends(get_dataset_service),
):
    """Import a dataset file through the full import pipeline.

    Accepts CSV, Excel (.xlsx/.xls), JSON, and JSONL files.
    Returns a job ID for status polling.

    The file-based pipeline always completes independently. Database
    persistence is attempted as an optional post-step — if it fails,
    the import still succeeds and ``persisted`` is set to false.
    """
    # Detect adapter
    if adapter_type == "auto":
        adapter = _detect_adapter_from_ext(file.filename or "")
        if adapter is None:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.filename}. "
                       f"Supported: .csv, .xlsx, .xls, .json, .jsonl",
            )
    else:
        adapter_map = {
            "csv": CsvAdapter(),
            "xlsx": ExcelAdapter(),
            "xls": ExcelAdapter(),
            "json": JsonAdapter(),
            "jsonl": JsonAdapter(),
        }
        adapter = adapter_map.get(adapter_type)
        if adapter is None:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown adapter type: {adapter_type}. "
                       f"Supported: auto, csv, xlsx, xls, json, jsonl",
            )

    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename or ".csv")[1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    # Create job
    job_id = str(uuid.uuid4())
    _import_jobs[job_id] = {
        "job_id": job_id,
        "status": "running",
        "dataset_id": dataset_id,
        "progress": 0.0,
        "report": None,
        "error": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        # Run the pipeline synchronously in the request handler for now
        # (async background execution can be added in a future iteration)
        output_dir = os.path.join("datasets", "rs", "cohort", dataset_id)
        os.makedirs(output_dir, exist_ok=True)

        config = ImportConfig(
            dataset_id=dataset_id,
            source_file=tmp_path,
            output_dir=output_dir,
            column_mappings=[],
            validation_rules=[
                required_field_not_none("birth_latitude"),
                required_field_not_none("birth_longitude"),
                latitude_in_range(),
                longitude_in_range(),
            ],
            normalization_rules=[],
            dedup_key_fields=[],
            export_format=export_format,
        )

        # Try to get column mappings from the adapter if it supports them
        try:
            config.column_mappings = CsvAdapter().get_column_mappings() if hasattr(adapter, "get_column_mappings") else []
        except Exception:
            pass

        pipeline = ImportPipeline(adapter, config)
        report = pipeline.run()

        job = _import_jobs[job_id]
        persisted = False
        if report.errors:
            job["status"] = "failed"
            job["error"] = report.errors
        else:
            job["status"] = "completed"
            job["progress"] = 1.0
            job["report"] = report.to_dict()

            # ── Optional DB persistence (post-import) ────────────────────
            if dataset_service and report.quality_assessment:
                try:
                    qa = report.quality_assessment
                    export_result = report.export_results[0] if report.export_results else None
                    await dataset_service.record_import(
                        dataset_id=dataset_id,
                        name=f"Dataset {dataset_id}",
                        source_file=tmp_path,
                        format=export_format,
                        record_count=report.records_imported,
                        field_count=len(report.export_results[0].metadata_path) if export_result else 0,
                        quality_score=qa.get("quality_score"),
                        quality_tier=qa.get("quality_tier"),
                        checksum_sha256=export_result.checksum_sha256 if export_result else None,
                        file_path=export_result.output_path if export_result else None,
                        metadata_json=qa,
                    )
                    persisted = True
                except Exception:
                    job["persisted"] = False

    except Exception as e:
        job = _import_jobs[job_id]
        job["status"] = "failed"
        job["error"] = str(e)
    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    return {"job_id": job_id, "status": job["status"], "persisted": persisted}


@router.get("/import/{job_id}/status")
async def get_import_status(job_id: str):
    """Check the status of an import job."""
    if job_id not in _import_jobs:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return _import_jobs[job_id]


@router.get("/import/{job_id}/report")
async def get_import_report(job_id: str):
    """Download the validation report for a completed import job."""
    if job_id not in _import_jobs:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    job = _import_jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job is {job['status']}, not completed")
    return JSONResponse(content=job.get("report", {}))


@router.post("/validate")
async def validate_dataset(
    file: UploadFile = File(...),
    rules: str = Form("standard"),
):
    """Validate a dataset file without importing it.

    Returns validation results with per-rule pass/fail counts.
    """
    adapter = _detect_adapter_from_ext(file.filename or "")
    if adapter is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.filename}",
        )

    # Save to temp
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename or ".csv")[1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        records = list(adapter.read(tmp_path))

        validator = Validator()
        if rules == "standard":
            for field in ["birth_latitude", "birth_longitude", "birth_day", "birth_month", "birth_year"]:
                validator.add_rule(required_field_not_none(field))
            validator.add_rule(latitude_in_range())
            validator.add_rule(longitude_in_range())

        record_dicts = [r.data for r in records]
        l1_result = validator.validate_batch(record_dicts, ValidationLevel.L1)
        l2_result = validator.validate_batch(record_dicts, ValidationLevel.L2)

        return {
            "filename": file.filename,
            "records": len(records),
            "l1": {"passed": l1_result.passed, "failed": l1_result.failed},
            "l2": {"passed": l2_result.passed, "failed": l2_result.failed},
            "violations": [
                {
                    "rule_id": v.rule_id,
                    "severity": v.severity.value,
                    "row": v.record_index,
                    "message": v.message,
                }
                for v in (l1_result.violations + l2_result.violations)
            ],
            "valid": l1_result.failed == 0,
        }
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


@router.get("/schemas")
async def list_schemas():
    """List available JSON Schema definitions."""
    schema_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "schemas",
    )
    schemas = []
    if os.path.isdir(schema_dir):
        for f in sorted(os.listdir(schema_dir)):
            if f.endswith(".json"):
                schemas.append({
                    "name": f,
                    "path": f"/api/v1/datasets/schemas/{f}",
                })
    return {"schemas": schemas}


@router.get("/schemas/{schema_name}")
async def get_schema(schema_name: str):
    """Download a JSON Schema definition file."""
    schema_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "schemas",
        schema_name,
    )
    if not os.path.exists(schema_path) or not schema_name.endswith(".json"):
        raise HTTPException(status_code=404, detail=f"Schema not found: {schema_name}")
    return FileResponse(schema_path, media_type="application/json")


@router.get("/templates/{format}")
async def get_import_template(format: str):
    """Download an import template file (csv or xlsx)."""
    template_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "templates",
    )
    if format == "csv":
        path = os.path.join(template_dir, "astrosos-cohort-import-template.csv")
        media_type = "text/csv"
    elif format == "xlsx":
        path = os.path.join(template_dir, "astrosos-cohort-import-template.xlsx")
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}. Supported: csv, xlsx")

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Template not found: {format}")

    return FileResponse(path, media_type=media_type, filename=f"astrosos-import-template.{format}")

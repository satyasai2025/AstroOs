"""
AstroOS — Source Adapter Base Class

Abstract interface for all source adapters. Each adapter knows how to:
- Read records from a specific source format (Excel, CSV, JSON, etc.)
- Provide source metadata for provenance tracking
- Describe column definitions for schema mapping

Source adapters are the ONLY place source-specific logic lives.
The rest of the pipeline is format-agnostic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional


@dataclass
class ColumnMapping:
    """Maps one source column to one AstroOS field."""

    source_column: str
    target_field: str
    transformer: Optional[str] = None
    default_value: Any = None
    required: bool = False
    exclude: bool = False
    description: str = ""


@dataclass
class RawRecord:
    """One unvalidated record from the source.

    All fields are strings or raw values — normalization happens later.
    ``source_index`` is the 0-based row number in the source file.
    """

    data: Dict[str, Any]
    source_index: int
    source_file: str = ""
    source_sheet: str = ""


@dataclass
class ColumnDefinition:
    """Describes one column in the source file."""

    name: str
    data_type: str  # "string", "integer", "float", "date", "datetime", "boolean"
    nullable: bool = True
    example: Optional[Any] = None
    description: str = ""


class SourceAdapter(ABC):
    """Abstract base for all source adapters.

    Implementing a new adapter:
    1. Subclass SourceAdapter
    2. Implement read(), get_source_metadata(), get_column_definitions()
    3. Register in the adapters registry
    4. The pipeline handles everything else
    """

    @abstractmethod
    def read(self, file_path: str) -> Iterator[RawRecord]:
        """Yield RawRecord objects from the source file.

        Args:
            file_path: Absolute path to the source file.

        Yields:
            RawRecord instances, one per row/record in the source.
        """
        ...

    @abstractmethod
    def get_source_metadata(self, file_path: str) -> Dict[str, Any]:
        """Return source-level metadata for provenance tracking.

        Must include at minimum:
        - source_file: filename
        - source_format: format identifier (e.g., "xlsx", "csv", "json")
        - record_count: total number of records
        - source_columns: list of column names
        """
        ...

    @abstractmethod
    def get_column_definitions(self, file_path: str) -> List[ColumnDefinition]:
        """Return detailed column definitions for schema mapping.

        Includes data type inference, nullable detection, and examples.
        """
        ...

    def get_adapter_name(self) -> str:
        """Return a human-readable name for this adapter."""
        return self.__class__.__name__

    def get_supported_formats(self) -> List[str]:
        """Return list of file extensions this adapter handles."""
        return []

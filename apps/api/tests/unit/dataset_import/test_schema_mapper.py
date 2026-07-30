"""Tests for SchemaMapper."""

import pytest
from apps.api.services.dataset_import.schema_mapper import ColumnMapping, SchemaMapper


class TestSchemaMapper:
    def test_map_record_basic(self):
        mappings = [
            ColumnMapping(source_column="fname", target_field="first_name", required=True),
            ColumnMapping(source_column="lname", target_field="last_name", required=True),
            ColumnMapping(source_column="lat", target_field="birth_latitude"),
        ]
        mapper = SchemaMapper(mappings)
        result = mapper.map_record({"fname": "John", "lname": "Doe", "lat": 28.5})
        assert result["first_name"] == "John"
        assert result["last_name"] == "Doe"
        assert result["birth_latitude"] == 28.5

    def test_map_record_missing_required_raises(self):
        mappings = [
            ColumnMapping(source_column="fname", target_field="first_name", required=True),
        ]
        mapper = SchemaMapper(mappings)
        with pytest.raises(ValueError, match="Required field"):
            mapper.map_record({})

    def test_map_record_optional_field_null(self):
        mappings = [
            ColumnMapping(source_column="gender", target_field="subject_gender"),
        ]
        mapper = SchemaMapper(mappings)
        result = mapper.map_record({"gender": None})
        assert result["subject_gender"] is None

    def test_map_record_exclude_field(self):
        mappings = [
            ColumnMapping(source_column="fname", target_field="first_name", exclude=True),
            ColumnMapping(source_column="lname", target_field="last_name"),
        ]
        mapper = SchemaMapper(mappings)
        result = mapper.map_record({"fname": "John", "lname": "Doe"})
        assert "first_name" not in result
        assert result["last_name"] == "Doe"

    def test_map_record_transformer(self):
        def upper_transform(val, raw):
            return str(val).upper() if val is not None else None

        mappings = [
            ColumnMapping(source_column="fname", target_field="first_name", transformer="upper"),
        ]
        mapper = SchemaMapper(mappings, record_transformers={"upper": upper_transform})
        result = mapper.map_record({"fname": "john"})
        assert result["first_name"] == "JOHN"

    def test_get_required_fields(self):
        mappings = [
            ColumnMapping(source_column="a", target_field="first_name", required=True),
            ColumnMapping(source_column="b", target_field="last_name", required=False),
        ]
        mapper = SchemaMapper(mappings)
        assert mapper.get_required_fields() == ["first_name"]
        assert mapper.get_optional_fields() == ["last_name"]

    def test_map_batch(self):
        mappings = [
            ColumnMapping(source_column="a", target_field="x", required=True),
        ]
        mapper = SchemaMapper(mappings)
        results = mapper.map_batch([{"a": 1}, {"a": 2}, {"a": 3}])
        assert len(results) == 3
        assert results[0]["x"] == 1
        assert results[2]["x"] == 3

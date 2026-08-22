"""
Unit tests for Deterministic Narrative Report Engine (Module 20, Phase 5)
"""

import pytest
from apps.api.domain.narrative_report import ReportSectionType, VargaDignity
from apps.api.services.narrative_report_engine import NarrativeReportEngine
from apps.api.services.report_export_service import ReportExportService


class TestNarrativeReportEngine:
    @pytest.fixture
    def sample_chart(self):
        return {
            "birth_datetime_utc": "2026-08-20T12:00:00Z",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "planets": [
                {"planet": "Jupiter", "house_number": 1, "rashi": "Cancer", "sidereal_longitude": 104.5},
                {"planet": "Moon", "house_number": 11, "rashi": "Taurus", "nakshatra": "Rohini", "sidereal_longitude": 45.2},
                {"planet": "Sun", "house_number": 10, "rashi": "Aries", "sidereal_longitude": 15.8},
                {"planet": "Mercury", "house_number": 10, "rashi": "Aries", "sidereal_longitude": 22.4},
                {"planet": "Mars", "house_number": 7, "rashi": "Capricorn", "sidereal_longitude": 284.1},
                {"planet": "Venus", "house_number": 9, "rashi": "Pisces", "sidereal_longitude": 348.0},
                {"planet": "Saturn", "house_number": 4, "rashi": "Libra", "sidereal_longitude": 198.3},
                {"planet": "Rahu", "house_number": 11, "rashi": "Taurus", "sidereal_longitude": 54.0},
                {"planet": "Ketu", "house_number": 5, "rashi": "Scorpio", "sidereal_longitude": 234.0},
            ],
            "houses": [
                {"house_number": 1, "rashi": "Cancer", "longitude": 95.0},
                {"house_number": 10, "rashi": "Aries", "longitude": 5.0},
            ],
            "vargas": {
                "D9": {
                    "planets": [
                        {"planet": "Jupiter", "rashi": "Cancer"},  # Vargottama & Exalted
                        {"planet": "Moon", "rashi": "Taurus"},      # Vargottama & Exalted
                    ]
                }
            },
            "yogas": [
                {"name": "Gajakesari Yoga", "category": "Raja", "source": "BPHS Ch. 36", "strength": 0.9},
                {"name": "Hamsa Yoga", "category": "Mahapurusha", "source": "Saravali Ch. 35", "strength": 0.95},
            ],
        }

    def test_nine_section_report_assembly(self, sample_chart):
        engine = NarrativeReportEngine()
        report = engine.generate_report(sample_chart, subject_name="Dr. Raman")

        assert len(report.sections) == 9
        section_types = [s.section_type for s in report.sections]

        assert ReportSectionType.SUMMARY in section_types
        assert ReportSectionType.CHART_AND_VARGAS in section_types
        assert ReportSectionType.YOGAS_AND_RULES in section_types
        assert ReportSectionType.DASHA_HIERARCHY in section_types
        assert ReportSectionType.TRANSITS_AND_ASHTAKAVARGA in section_types
        assert ReportSectionType.KP_ANALYSIS in section_types
        assert ReportSectionType.SBC_VEDHAS in section_types
        assert ReportSectionType.COMPARATIVE_FINDINGS in section_types
        assert ReportSectionType.LIMITATIONS in section_types

        # Verify evidence index
        assert len(report.all_evidence_index) >= 5
        assert "EVID-D1-LAGNA" in report.all_evidence_index
        assert "EVID-D1-MOON" in report.all_evidence_index

        # Verify Multi-Varga Matrix
        assert len(report.multi_varga_matrix) == 9
        jup = next(v for v in report.multi_varga_matrix if v.planet == "Jupiter")
        assert jup.d1_dignity == VargaDignity.EXALTED
        assert jup.is_vargottama is True

    def test_multi_format_exports(self, sample_chart):
        engine = NarrativeReportEngine()
        report = engine.generate_report(sample_chart, subject_name="Aryabhata")

        # Serialise to dictionary
        report_dict = {
            "subject_name": report.subject_name,
            "report_title": report.report_title,
            "generated_at_iso": report.generated_at_iso,
            "multi_varga_matrix": [
                {
                    "planet": v.planet,
                    "d1_rashi": v.d1_rashi,
                    "d1_house": v.d1_house,
                    "d1_dignity": v.d1_dignity.value,
                    "d9_rashi": v.d9_rashi,
                    "d9_dignity": v.d9_dignity.value,
                    "d10_rashi": v.d10_rashi,
                    "d10_dignity": v.d10_dignity.value,
                    "d7_rashi": v.d7_rashi,
                    "d7_dignity": v.d7_dignity.value,
                    "is_vargottama": v.is_vargottama,
                }
                for v in report.multi_varga_matrix
            ],
            "sections": [
                {
                    "section_type": s.section_type.value,
                    "title": s.title,
                    "subtitle": s.subtitle,
                    "paragraphs": [{"heading": p.heading, "content_text": p.content_text, "referenced_evidence_ids": p.referenced_evidence_ids} for p in s.paragraphs],
                    "evidence_table": [
                        {"evidence_id": e.evidence_id, "category": e.category, "parameter_name": e.parameter_name, "computed_value": e.computed_value, "classical_reference": e.classical_reference, "confidence_or_strength": e.confidence_or_strength}
                        for e in s.evidence_table
                    ],
                }
                for s in report.sections
            ],
        }

        export_service = ReportExportService()

        # HTML Export
        html_exp = export_service.export_document(report_dict, export_format="html")
        assert html_exp.export_format == "html"
        assert "<!DOCTYPE html>" in html_exp.content_base64_or_text
        assert "Aryabhata" in html_exp.content_base64_or_text

        # JSON Export
        json_exp = export_service.export_document(report_dict, export_format="json")
        assert json_exp.export_format == "json"
        assert '"subject_name": "Aryabhata"' in json_exp.content_base64_or_text

        # CSV Export
        csv_exp = export_service.export_document(report_dict, export_format="csv")
        assert csv_exp.export_format == "csv"
        assert "MULTI-VARGA DIGNITY MATRIX" in csv_exp.content_base64_or_text
        assert "Jupiter" in csv_exp.content_base64_or_text

        # PDF Export
        pdf_exp = export_service.export_document(report_dict, export_format="pdf")
        assert pdf_exp.export_format == "pdf"
        assert len(pdf_exp.content_base64_or_text) > 50

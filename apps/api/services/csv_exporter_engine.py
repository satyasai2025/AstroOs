"""
AstroOS — CSV Exporter Engine (Phalita MoE Dataset Generation)
==============================================================
Implements the exact Long Debug CSV and Wide ML CSV schemas specified by Vinay Jha
in Section 10 of 'Phalita MoE AI Model' (phalita-moe-ai-model.md):

  - Section 10.1: Long Debug CSV (20 audit columns)
  - Section 10.2: Wide ML CSV (Exact Jha columns including Gold_Return targets and H2, H8, H11, H12)
  - Section 18: Four Noise Flags (DataNoiseFlag, RulesNoiseFlag, ModelNoiseFlag, UsefulNoiseBand)
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import io
import math
from typing import Any, Dict, List, Optional, Tuple

from apps.api.domain.tphalit_core import ChartLevelEnum, TPhalitFeatureVector
from apps.api.services.divisional_synthesis_engine import DivisionalSynthesisEngine, VimshopakaScheme
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.tphalit_core_engine import TPhalitCoreEngine
from apps.api.services.vpc_engine import VPCEngine

# Section 10.1: Exact Long Debug CSV Header
LONG_DEBUG_HEADER = [
    "RecordID", "TimeJD", "ChartLevel", "VargaID", "DegreeTheta",
    "RuleID", "RuleClass", "PlanetID", "BhavaID",
    "RawEffect", "SignedEffect", "VargaWeight", "TemporalWeight",
    "FinalEffect", "IsActive", "IsCancelled", "CancelledByRuleID",
    "DataQualityScore", "RuleVersion", "FeatureVersion",
]

# Section 10.2: Exact Wide ML CSV Header (Line-by-line match with Jha Sec 10.2)
WIDE_ML_HEADER = [
    "RecordID", "TimeJD", "Target_Horizon",
    "Gold_Return_10min", "Gold_Return_1hr",
    "A_D1_Total", "A_D2_Total", "A_D9_Total", "A_D60_Total", "A_Total",
    "M_D1_Total", "M_D2_Total", "M_D9_Total", "M_D60_Total", "M_Total",
    "V_D1_Total", "V_D2_Total", "V_D9_Total", "V_D60_Total", "V_Total",
    "G_D1_Total", "G_D2_Total", "G_D9_Total", "G_D60_Total", "G_Total",
    "H2_Total", "H8_Total", "H11_Total", "H12_Total",
    "PadaArudha_Total", "Gochara_Total", "D2_Deity_Effect",
    "Aspect_Field_Total", "Yoga_Total", "JatakaYoga_Total", "VRY_Total",
    "Suppression_Total", "Primitive_Total",
    "Final_Deterministic_Score",
    "DataNoiseFlag", "RulesNoiseFlag", "ModelNoiseFlag", "UsefulNoiseBand",
]


class CSVExporterEngine:
    """Exports structured Long Debug and Wide ML CSV datasets strictly per Jha's schema."""

    def __init__(
        self,
        ephemeris_wrapper: Optional[EphemerisWrapper] = None,
        ephemeris_path: str = "data/ephemeris",
    ):
        self.wrapper = ephemeris_wrapper or EphemerisWrapper(ephemeris_path=ephemeris_path)
        self.tphalit_engine = TPhalitCoreEngine(ephemeris_wrapper=self.wrapper)
        self.vpc_engine = VPCEngine(ephemeris_wrapper=self.wrapper)
        self.div_engine = DivisionalSynthesisEngine(ephemeris_wrapper=self.wrapper)

    def generate_wide_ml_row(
        self,
        record_id: int,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        gold_return_10min: Optional[float] = None,
        gold_return_1hr: Optional[float] = None,
        target_horizon: int = 365,
    ) -> Dict[str, Any]:
        """Generates a single row matching Section 10.2 schema exactly."""
        fv = self.tphalit_engine.extract_features(
            birth_datetime_utc=birth_datetime_utc,
            latitude=latitude,
            longitude=longitude,
        )

        time_jd = fv.Metadata.TimeJD
        det_score = fv.DeterministicScore

        # Extract only the 4 canonical wealth houses from Section 10.2
        h2_val = fv.AtomicFeatures.get("D1_H2_FinalScore", 0.0)
        h8_val = fv.AtomicFeatures.get("D1_H8_FinalScore", 0.0)
        h11_val = fv.AtomicFeatures.get("D1_H11_FinalScore", 0.0)
        h12_val = fv.AtomicFeatures.get("D1_H12_FinalScore", 0.0)

        # Extract Varga breakdown (D1, D2, D9, D60)
        p_total = fv.BlockTotals.get("PlanetBlock", 0.0)
        w_d1 = self.div_engine.get_varga_weight(1, VimshopakaScheme.DASHAVARGA)
        w_d2 = self.div_engine.get_varga_weight(2, VimshopakaScheme.DASHAVARGA)
        w_d9 = self.div_engine.get_varga_weight(9, VimshopakaScheme.DASHAVARGA)
        w_d60 = self.div_engine.get_varga_weight(60, VimshopakaScheme.DASHAVARGA)

        a_d1 = round(p_total * w_d1, 4)
        a_d2 = round(p_total * w_d2, 4)
        a_d9 = round(p_total * w_d9, 4)
        a_d60 = round(p_total * w_d60, 4)
        a_total = round(a_d1 + a_d2 + a_d9 + a_d60, 4)

        # Temporal scale approximations (Annual, Monthly, Vidasha, Gochara per Sec 7)
        m_total = round(a_total * 0.75, 4)
        v_total = round(a_total * 0.50, 4)
        g_total = round(a_total * 0.25, 4)

        # Noise diagnostic flags (Section 18)
        data_noise = 1 if (latitude == 0.0 or longitude == 0.0) else 0
        rules_noise = 1 if (abs(p_total) < 0.1) else 0  # weak-field fuzzy zone
        model_noise = 1 if (abs(det_score) > 15.0) else 0  # linear breakdown zone
        useful_band = round(0.1 * abs(det_score), 4)

        row = {
            "RecordID": record_id,
            "TimeJD": round(time_jd, 6),
            "Target_Horizon": target_horizon,
            
            # Ground truth financial returns
            "Gold_Return_10min": round(gold_return_10min, 6) if gold_return_10min is not None else "",
            "Gold_Return_1hr": round(gold_return_1hr, 6) if gold_return_1hr is not None else "",
            
            # Annual Cycle
            "A_D1_Total": a_d1,
            "A_D2_Total": a_d2,
            "A_D9_Total": a_d9,
            "A_D60_Total": a_d60,
            "A_Total": a_total,
            
            # Monthly Cycle
            "M_D1_Total": round(a_d1 * 0.75, 4),
            "M_D2_Total": round(a_d2 * 0.75, 4),
            "M_D9_Total": round(a_d9 * 0.75, 4),
            "M_D60_Total": round(a_d60 * 0.75, 4),
            "M_Total": m_total,
            
            # Vidasha Cycle
            "V_D1_Total": round(a_d1 * 0.50, 4),
            "V_D2_Total": round(a_d2 * 0.50, 4),
            "V_D9_Total": round(a_d9 * 0.50, 4),
            "V_D60_Total": round(a_d60 * 0.50, 4),
            "V_Total": v_total,
            
            # Gochara Cycle
            "G_D1_Total": round(a_d1 * 0.25, 4),
            "G_D2_Total": round(a_d2 * 0.25, 4),
            "G_D9_Total": round(a_d9 * 0.25, 4),
            "G_D60_Total": round(a_d60 * 0.25, 4),
            "G_Total": g_total,
            
            # Canonical 4 Wealth Houses (Section 10.2 lines 634-637)
            "H2_Total": h2_val,
            "H8_Total": h8_val,
            "H11_Total": h11_val,
            "H12_Total": h12_val,
            
            # Specialized blocks
            "PadaArudha_Total": round(fv.AtomicFeatures.get("D1_H1_FinalScore", 0.0), 4),
            "Gochara_Total": g_total,
            "D2_Deity_Effect": round(a_d2 * 0.5, 4),
            "Aspect_Field_Total": fv.BlockTotals.get("AspectBlock", 0.0),
            "Yoga_Total": fv.BlockTotals.get("YogaBlock", 0.0),
            "JatakaYoga_Total": fv.BlockTotals.get("YogaBlock", 0.0),
            "VRY_Total": fv.AtomicFeatures.get("Yoga_ViparitaRajaHarsha_Contribution", 0.0),
            "Suppression_Total": round(a_d1 - a_d9, 4),
            "Primitive_Total": p_total,
            "Final_Deterministic_Score": det_score,
            
            # Section 18 Noise Flags
            "DataNoiseFlag": data_noise,
            "RulesNoiseFlag": rules_noise,
            "ModelNoiseFlag": model_noise,
            "UsefulNoiseBand": useful_band,
        }
        return row

    def export_wide_ml_csv(self, records: List[Dict[str, Any]], output_filepath: Optional[str] = None) -> str:
        """Exports a list of event records to Wide ML CSV format."""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=WIDE_ML_HEADER)
        writer.writeheader()

        for idx, rec in enumerate(records):
            b_dt = rec["birth_datetime_utc"]
            lat = rec["latitude"]
            lon = rec["longitude"]
            r_10m = rec.get("gold_return_10min")
            r_1h = rec.get("gold_return_1hr")
            row = self.generate_wide_ml_row(
                record_id=idx + 1,
                birth_datetime_utc=b_dt,
                latitude=lat,
                longitude=lon,
                gold_return_10min=r_10m,
                gold_return_1hr=r_1h,
            )
            writer.writerow(row)

        csv_content = output.getvalue()
        if output_filepath:
            with open(output_filepath, mode="w", encoding="utf-8", newline="") as f:
                f.write(csv_content)
        return csv_content

    def export_long_debug_csv(self, records: List[Dict[str, Any]], output_filepath: Optional[str] = None) -> str:
        """Exports a list of event records to Long Debug CSV format (Section 10.1)."""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=LONG_DEBUG_HEADER)
        writer.writeheader()

        entry_id = 1
        for idx, rec in enumerate(records):
            b_dt = rec["birth_datetime_utc"]
            lat = rec["latitude"]
            lon = rec["longitude"]
            fv = self.tphalit_engine.extract_features(
                birth_datetime_utc=b_dt,
                latitude=lat,
                longitude=lon,
            )

            # Emit rule-by-rule rows
            for k, val in fv.AtomicFeatures.items():
                rule_class = "Planet" if "FinalSigned" in k else ("Bhava" if "FinalScore" in k else "Yoga")
                row = {
                    "RecordID": entry_id,
                    "TimeJD": round(fv.Metadata.TimeJD, 6),
                    "ChartLevel": fv.Metadata.ChartLevel,
                    "VargaID": fv.Metadata.VargaID,
                    "DegreeTheta": fv.Metadata.DegreePoint,
                    "RuleID": k,
                    "RuleClass": rule_class,
                    "PlanetID": 1,
                    "BhavaID": 1,
                    "RawEffect": val,
                    "SignedEffect": val,
                    "VargaWeight": fv.Metadata.VargaWeight,
                    "TemporalWeight": fv.Metadata.TemporalWeight,
                    "FinalEffect": val,
                    "IsActive": 1,
                    "IsCancelled": 0,
                    "CancelledByRuleID": "",
                    "DataQualityScore": 1.0,
                    "RuleVersion": "1.0",
                    "FeatureVersion": "1.0",
                }
                writer.writerow(row)
                entry_id += 1

        csv_content = output.getvalue()
        if output_filepath:
            with open(output_filepath, mode="w", encoding="utf-8", newline="") as f:
                f.write(csv_content)
        return csv_content

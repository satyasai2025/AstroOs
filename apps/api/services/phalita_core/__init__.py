"""AstroOS — Phalita Core Machine Learning & Feature Vectorization Package."""
from apps.api.services.phalita_core.tphalit_core import (
    TPhalitBhavaFeature,
    TPhalitCore,
    TPhalitDashaFeature,
    TPhalitFeatureVector,
    TPhalitPlanetFeature,
    TPhalitYogaFeature,
)
from apps.api.services.phalita_core.expert_registry import (
    ExpertOutput,
    NatalStructuralExpert,
    DivisionalYogaExpert,
    TemporalDashaExpert,
    UpagrahaShadowExpert,
)
from apps.api.services.phalita_core.expert_router import ExpertRouter, GatingWeights
from apps.api.services.phalita_core.conflict_resolution import (
    ConflictResolutionEngine,
    ConflictResolutionResult,
)
from apps.api.services.phalita_core.phalita_moe_orchestrator import (
    PhalitaMoEOrchestrator,
    PhalitaMoEConsultationVerdict,
)
from apps.api.services.phalita_core.domain_significators import (
    DomainSignificatorConfig,
    DOMAIN_SIGNIFICATOR_REGISTRY,
    get_domain_config,
    get_all_domains,
)
from apps.api.services.phalita_core.varga_strength_fusion import (
    VargaStrengthFusionEngine,
    PlanetVargaStrengthDetail,
    DualDashaVargaComparison,
)
from apps.api.services.phalita_core.bhavottama_engine import (
    BhavottamaEngine,
    BhavottamaStatus,
)
from apps.api.services.phalita_core.transit_trigger_engine import (
    TransitTriggerEngine,
    TransitTriggerResult,
)
from apps.api.services.phalita_core.karakamsha_synthesis_engine import (
    KarakamshaSynthesisEngine,
    KarakamshaSynthesisResult,
    CharaKarakaAssignment,
)
from apps.api.services.phalita_core.divisional_explorer_service import (
    DivisionalExplorerService,
    DivisionalExplorationResult,
    DivisionalPlanetPosition,
)
from apps.api.services.phalita_core.canonical_facts_generator import (
    CanonicalFactsGenerator,
    CanonicalFacts,
    PlanetCanonicalFact,
    BhavaCanonicalFact,
    VargaPlanetFact,
    UpagrahaFact,
)
from apps.api.services.phalita_core.technique_resolver import (
    TechniqueResolver,
    ResolvedTechniquePlan,
)
from apps.api.services.phalita_core.shastric_rule_engine import (
    ShastricRuleEngine,
    RuleEngineEvaluationResult,
    RuleEvaluationItem,
)
from apps.api.services.phalita_core.evidence_aggregator import (
    EvidenceAggregator,
    DomainEvidencePackage,
    ProvenanceFactLink,
)
from apps.api.services.phalita_core.prediction_calibrator import (
    PredictionCalibrator,
    CalibratedPredictionVerdict,
)
from apps.api.services.phalita_core.shastric_explanation_narrator import (
    ShastricExplanationNarrator,
    ShastricGroundedExplanation,
)
from apps.api.services.phalita_core.shastric_reasoning_pipeline import (
    ShastricReasoningPipeline,
    ShastricPipelineExecutionResult,
)
from apps.api.services.phalita_core.three_tier_validation_framework import (
    ThreeTierValidationFramework,
    Comprehensive3TierAuditReport,
    Tier1RegressionResult,
    Tier2GeneralizationResult,
    Tier3HoldoutResult,
)

__all__ = [
    "TPhalitCore",
    "TPhalitPlanetFeature",
    "TPhalitBhavaFeature",
    "TPhalitYogaFeature",
    "TPhalitDashaFeature",
    "TPhalitFeatureVector",
    "ExpertOutput",
    "NatalStructuralExpert",
    "DivisionalYogaExpert",
    "TemporalDashaExpert",
    "UpagrahaShadowExpert",
    "ExpertRouter",
    "GatingWeights",
    "ConflictResolutionEngine",
    "ConflictResolutionResult",
    "PhalitaMoEOrchestrator",
    "PhalitaMoEConsultationVerdict",
    "DomainSignificatorConfig",
    "DOMAIN_SIGNIFICATOR_REGISTRY",
    "get_domain_config",
    "get_all_domains",
    "VargaStrengthFusionEngine",
    "PlanetVargaStrengthDetail",
    "DualDashaVargaComparison",
    "BhavottamaEngine",
    "BhavottamaStatus",
    "TransitTriggerEngine",
    "TransitTriggerResult",
    "KarakamshaSynthesisEngine",
    "KarakamshaSynthesisResult",
    "CharaKarakaAssignment",
    "DivisionalExplorerService",
    "DivisionalExplorationResult",
    "DivisionalPlanetPosition",
    "CanonicalFactsGenerator",
    "CanonicalFacts",
    "PlanetCanonicalFact",
    "BhavaCanonicalFact",
    "VargaPlanetFact",
    "UpagrahaFact",
    "TechniqueResolver",
    "ResolvedTechniquePlan",
    "ShastricRuleEngine",
    "RuleEngineEvaluationResult",
    "RuleEvaluationItem",
    "EvidenceAggregator",
    "DomainEvidencePackage",
    "ProvenanceFactLink",
    "PredictionCalibrator",
    "CalibratedPredictionVerdict",
    "ShastricExplanationNarrator",
    "ShastricGroundedExplanation",
    "ShastricReasoningPipeline",
    "ShastricPipelineExecutionResult",
    "ThreeTierValidationFramework",
    "Comprehensive3TierAuditReport",
    "Tier1RegressionResult",
    "Tier2GeneralizationResult",
    "Tier3HoldoutResult",
]

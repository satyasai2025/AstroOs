"""
AstroOS — Workflow orchestration layer (Phase 10 R1, 2026-08-06)

Home for WorkflowOrchestrator.analyze()'s pipeline, split into named
Stage objects (see stage.py's Stage protocol and PipelineContext) so the
sequence of engine calls is a declared list rather than one procedural
method. Every stage's body is existing logic moved from
apps/api/services/workflow_orchestrator.py, not rewritten — see
PHASE_10_PLAN.md for the before/after.
"""

import sys
sys.stdout.reconfigure(encoding="utf-8")
from apps.api.services.corpus_brain_bridge import CorpusBrainBridge

bridge = CorpusBrainBridge()
print("=== 1. Testing CorpusBrainBridge Database Connection ===")
assertions = bridge.get_reviewed_assertions(limit=5)
print(f"Retrieved assertions from Corpus-Brain DB: {len(assertions)}")
for a in assertions:
    print(f"  - Assertion ID: {a['assertion_id']} | Concept: {a['concept_name']} | Type: {a['assertion_type']}")
    print(f"    Source: {a['source_title']}")
    print(f"    Text: {a['value_literal'][:90]}...\n")

print("=== 2. Testing 5-Layer Multi-Parametric Synthesis ===")
natal_factors = {
    "jupiter_in_9th": {"planet": "Guru", "bhava": 9, "natal_weight": 1.5},
    "saturn_aspect_on_lagna": {"planet": "Shani", "bhava": 1, "natal_weight": 0.8},
}
divisional_weights = {"Guru": 1.4, "Shani": 0.9}
dasha_status = {"active_dasha_lord": "Guru"}
transit_triggers = {"Guru": {"ashtakavarga_bindus": 6}, "Shani": {"ashtakavarga_bindus": 2}}

res = bridge.synthesize_multi_layer_reading(natal_factors, divisional_weights, dasha_status, transit_triggers)
print(f"Overall Net Synthesized Score: {res['overall_net_synthesized_score']}")
print(f"Methodology: {res['methodology']}")
print(f"Audit Compliance: {res['audit_compliance']}\n")

for fe in res["factor_evaluations"]:
    print(f"  * Factor '{fe['factor']}': Net Score = {fe['layer5_net_synthesized_score']}")
    print(f"    [L1 Natal={fe['layer1_natal_promise']} x L2 Div={fe['layer2_divisional_weight']} x L3 Dasha={fe['layer3_dasha_status']} x L4 Transit={fe['layer4_transit_trigger']}]")

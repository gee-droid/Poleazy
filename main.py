from __future__ import annotations
from pathlib import Path
from mock_data import MOCK_PAYLOAD
from dev3_delivery.spatial import compute_impact_zone
from dev2_agents import build_reasoning_graph

def run_demo_pipeline() -> object:
    parcels_path = str(Path(__file__).resolve().parent / "data" / "parcels.geojson")
    
    # 1. Dev 3 Spatial computation
    geospatial = compute_impact_zone(MOCK_PAYLOAD.geospatial.target_address, parcels_path)
    payload = MOCK_PAYLOAD.model_copy(update={"geospatial": geospatial})
    
    # 2. Dev 2 Multi-Agent reasoning engine
    runner = build_reasoning_graph()
    reasoning_output = runner.invoke({
        "docket_id": payload.docket_id,
        "title": payload.title,
        "raw_text": getattr(payload, "raw_text", "Amending Section 25-2-492 to reduce interior setback..."),
        "baseline": getattr(payload, "baseline", "Section 25-2-492 requires 25ft interior setback...")
    })
    
    return payload, reasoning_output

if __name__ == "__main__":
    payload, reasoning = run_demo_pipeline()
    print(f"✅ Docket: {payload.docket_id} | Title: {payload.title}")
    print(f"📍 Address: {payload.geospatial.target_address}")
    print(f"🏘️ Affected parcels: {payload.geospatial.affected_parcels_count}")
    print(f"⚖️ Legal Section Analyzed: {reasoning.get('legal_diff')}")
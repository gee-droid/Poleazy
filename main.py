from __future__ import annotations

from pathlib import Path

from mock_data import MOCK_PAYLOAD
from dev3_delivery.spatial import compute_impact_zone


def run_demo_pipeline() -> object:
    parcels_path = str(Path(__file__).resolve().parent / "data" / "parcels.geojson")
    geospatial = compute_impact_zone(MOCK_PAYLOAD.geospatial.target_address, parcels_path)
    payload = MOCK_PAYLOAD.model_copy(update={"geospatial": geospatial})
    return payload


if __name__ == "__main__":
    payload = run_demo_pipeline()
    print(f"Docket: {payload.docket_id} | Title: {payload.title}")
    print(f"Address: {payload.geospatial.target_address}")
    print(f"Affected parcels in {payload.geospatial.buffer_meters}m radius: {payload.geospatial.affected_parcels_count}")

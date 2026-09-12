from pydantic import BaseModel, Field
from typing import Dict, Any

class LegalDiff(BaseModel):
    section_code: str = Field(description="e.g., § 25-2-492")
    baseline_rule: str = Field(description="Old rule")
    proposed_rule: str = Field(description="New rule")
    plain_summary: str = Field(description="Grade 8 plain-English summary")

class GeoPayload(BaseModel):
    target_address: str
    latitude: float
    longitude: float
    buffer_meters: float = 300.0
    affected_parcels_count: int
    geojson_impact_layer: Dict[str, Any]

class CitizenAction(BaseModel):
    sms_alert: str
    formal_letter: str

class PoleazyPayload(BaseModel):
    docket_id: str
    city: str
    title: str
    legal_diff: LegalDiff
    geospatial: GeoPayload
    citizen_action: CitizenAction

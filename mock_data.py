from core.schema import PoleazyPayload, LegalDiff, GeoPayload, CitizenAction

MOCK_PAYLOAD = PoleazyPayload(
    docket_id="ORD-2026-0891",
    city="Austin, TX",
    title="Rezoning 1400 Congress Ave",
    legal_diff=LegalDiff(
        section_code="§ 25-2-492",
        baseline_rule="SF-3 Single Family (Max 2 stories, 25ft setback)",
        proposed_rule="MU-V Mixed Use (Max 4 stories, 10ft setback)",
        plain_summary="Replaces single-family zoning with a 4-story mixed residential/commercial building."
    ),
    geospatial=GeoPayload(
        target_address="1400 Congress Ave, Austin, TX",
        latitude=30.2766,
        longitude=-97.7413,
        buffer_meters=300.0,
        affected_parcels_count=34,
        geojson_impact_layer={"type": "FeatureCollection", "features": []}
    ),
    citizen_action=CitizenAction(
        sms_alert="Notice: 1400 Congress Ave is slated for 4-story rezoning.",
        formal_letter="To the City Council Clerk: Regarding Docket ORD-2026-0891..."
    )
)

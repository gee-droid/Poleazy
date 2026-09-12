import folium

def render_impact_map(lat: float = 30.2766, lon: float = -97.7413, radius_m: float = 300.0) -> folium.Map:
    """
    Renders an interactive spatial map centered directly on the parcel impact zone.
    """
    m = folium.Map(
        location=[lat, lon],
        zoom_start=16,
        tiles="OpenStreetMap"
    )

    folium.Marker(
        [lat, lon],
        popup=f"Target Property: {lat}, {lon}",
        tooltip="Subject Parcel",
        icon=folium.Icon(color="darkred", icon="info-sign")
    ).add_to(m)

    folium.Circle(
        location=[lat, lon],
        radius=radius_m,
        color="#1E3A8A",
        fill=True,
        fill_color="#3B82F6",
        fill_opacity=0.2,
        weight=2,
        popup=f"Statutory Notice Zone: {int(radius_m)}m"
    ).add_to(m)

    # Lock view bounds tightly around the buffer radius
    delta = (radius_m / 111320.0) * 1.6
    m.fit_bounds([[lat - delta, lon - delta], [lat + delta, lon + delta]])

    return m

def compute_impact_zone(target_address: str, parcels_geojson_path: str = None) -> object:
    from mock_data import MOCK_PAYLOAD
    return MOCK_PAYLOAD.geospatial.model_copy(
        update={
            "target_address": target_address,
            "affected_parcels_count": 34,
            "buffer_meters": 300.0
        }
    )
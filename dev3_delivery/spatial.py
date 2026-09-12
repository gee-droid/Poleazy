import folium

def render_impact_map(lat: float = 30.2766, lon: float = -97.7413, radius_m: float = 300.0) -> folium.Map:
    """
    Renders an interactive spatial map showing the target property
    and the affected citizen buffer zone using standard OpenStreetMap tiles.
    """
    # OpenStreetMap tiles do not require an API key and show no watermarks
    m = folium.Map(
        location=[lat, lon],
        zoom_start=15,
        tiles="OpenStreetMap"
    )

    # Center marker for the cited property/ordinance target
    folium.Marker(
        [lat, lon],
        popup="Target Parcel: 1400 Congress Ave",
        tooltip="1400 Congress Ave",
        icon=folium.Icon(color="red", icon="home")
    ).add_to(m)

    # Buffer zone circle showing affected resident boundary
    folium.Circle(
        location=[lat, lon],
        radius=radius_m,
        color="#2E7D32",
        fill=True,
        fill_color="#2E7D32",
        fill_opacity=0.25,
        weight=2,
        popup=f"Impact Radius: {radius_m}m Buffer"
    ).add_to(m)

    return m
def compute_impact_zone(target_address: str, parcels_geojson_path: str = None) -> object:
    """
    Computes spatial impact metrics around a target address.
    Returns a geospatial model instance compatible with MOCK_PAYLOAD.
    """
    from mock_data import MOCK_PAYLOAD
    
    # Return mock geospatial object updated with the queried address
    return MOCK_PAYLOAD.geospatial.model_copy(
        update={
            "target_address": target_address,
            "affected_parcels_count": 34,
            "buffer_meters": 300
        }
    )
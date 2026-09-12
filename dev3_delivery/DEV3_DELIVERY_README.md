# Developer 3: Geospatial Analytics & Frontend Dashboard

**Folder Scope:** `dev3_delivery/`  
**Dependencies:** `geopandas`, `shapely`, `geopy`, `streamlit`, `streamlit-folium`, `folium`, `fpdf2`

---

## 1. Core Objectives
1. Geocode extracted street addresses and corridor names using free OpenStreetMap Nominatim APIs.
2. Generate circular impact zones (300m buffers) using **Shapely**.
3. Perform spatial joins (`gpd.sjoin`) with city parcel GeoJSON layers to detect affected neighboring properties.
4. Build the user-facing **Streamlit** dashboard displaying the interactive map, summary cards, and downloadable PDF/text council letters.

---

## 2. File Responsibilities

### `dev3_delivery/spatial.py`
* Handles geocoding and spatial joins:
  ```python
  from geopy.geocoders import Nominatim
  import geopandas as gpd
  from shapely.geometry import Point
  from core.schema import GeoPayload

  def compute_impact_zone(address: str, parcels_geojson_path: str) -> GeoPayload:
      geolocator = Nominatim(user_agent="poleazy_agent")
      loc = geolocator.geocode(address)
      point = Point(loc.longitude, loc.latitude)
      buffer_poly = point.buffer(0.003) # Approximate ~300m in degrees
      
      parcels_gdf = gpd.read_file(parcels_geojson_path)
      affected = parcels_gdf[parcels_gdf.intersects(buffer_poly)]
      
      return GeoPayload(
          target_address=address,
          latitude=loc.latitude,
          longitude=loc.longitude,
          buffer_meters=300.0,
          affected_parcels_count=len(affected),
          geojson_impact_layer=affected.__geo_interface__
      )
  ```

### `dev3_delivery/dashboard.py`
* Runs the Streamlit application:
  * Docket selector and address search bar.
  * Interactive map with `folium` showing parcel boundaries, the buffer circle, and target pin.
  * Plain-English impact summary card.
  * One-click download button for pre-drafted council objection/comment letters.

---

## 3. Execution Command
```bash
streamlit run dev3_delivery/dashboard.py
```

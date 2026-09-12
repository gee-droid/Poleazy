from __future__ import annotations

from pathlib import Path

import folium
import streamlit as st
from fpdf import FPDF
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

from core.schema import CitizenAction
from dev3_delivery.spatial import compute_impact_zone
from mock_data import MOCK_PAYLOAD


PAGE_TITLE = "Poleazy | Municipal Impact Dashboard"


@st.cache_data(show_spinner=False)
def get_default_parcels_path() -> str:
    return str(Path(__file__).resolve().parents[1] / "data" / "parcels.geojson")


def _build_letter_text(action: CitizenAction, target_address: str, docket_id: str) -> str:
    base_text = action.formal_letter if action and action.formal_letter else ""
    if base_text:
        return base_text

    return (
        "To the City Council Clerk\n\n"
        f"Re: Docket {docket_id} — {target_address}\n\n"
        "Dear Council Members,\n\n"
        "I am writing to express concern regarding the proposed development in the vicinity of the above address. "
        "The project may materially alter the character of the surrounding neighborhood, add congestion, and change the "
        "daily experience for nearby residents and pedestrians.\n\n"
        "I urge the Council to study the project carefully, review its neighborhood impacts, and consider the experience of "
        "affected households before approving the proposal.\n\n"
        "Thank you for your service and for considering this public comment.\n\n"
        "Sincerely,\n"
        "A concerned resident\n"
    )


def _build_pdf_letter(action: CitizenAction, target_address: str, docket_id: str) -> bytes:
    text = _build_letter_text(action, target_address, docket_id)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "Poleazy Comment Letter", ln=True)
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 11)

    for raw_line in text.splitlines():
        if not raw_line.strip():
            pdf.ln(4)
            continue
        wrapped = raw_line
        if len(raw_line) > 90:
            wrapped = "\n".join(
                [raw_line[i : i + 90] for i in range(0, len(raw_line), 90)]
            )
        pdf.multi_cell(0, 6, wrapped)

    return pdf.output(dest="S")


def render_css() -> None:
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');

            html, body, [data-testid="stAppViewContainer"] {
                background: #f5f1eb;
                color: #2f2724;
            }

            .block-container {
                padding-top: 1.2rem;
                padding-bottom: 2rem;
                max-width: 1440px;
            }

            .topbar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0.7rem 0 1.2rem 0;
                margin-bottom: 1.1rem;
                border-bottom: 1px solid rgba(47, 38, 34, 0.12);
            }

            .brand {
                font-family: 'Cormorant Garamond', serif;
                font-size: 3.1rem;
                font-weight: 600;
                letter-spacing: -0.06em;
                color: #2f2724;
                margin: 0;
            }

            .nav {
                display: flex;
                gap: 2rem;
                align-items: center;
                font-size: 0.72rem;
                text-transform: uppercase;
                letter-spacing: 0.14em;
                color: rgba(47, 38, 34, 0.9);
            }

            .nav .pill {
                background: #3a2f2b;
                color: #f6f1ec;
                border-radius: 999px;
                padding: 0.8rem 1.15rem;
                font-weight: 700;
            }

            .hero-panel {
                background: #f7f4ef;
                min-height: 660px;
                border: 1px solid rgba(47, 38, 34, 0.08);
                overflow: hidden;
            }

            .hero-grid {
                display: flex;
                flex-wrap: wrap;
                min-height: 620px;
                align-items: stretch;
            }

            .hero-photo {
                min-height: 620px;
                background-size: cover;
                background-position: center;
                width: 100%;
            }

            .hero-copy {
                background: #c8d8c7;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 620px;
                padding: 2.2rem 2.6rem;
            }

            .headline {
                font-family: 'Cormorant Garamond', serif;
                font-size: clamp(3.1rem, 5vw, 6.1rem);
                line-height: 0.9;
                letter-spacing: -0.06em;
                color: #2d2824;
                margin: 0;
                font-weight: 500;
            }

            .muted-copy {
                font-family: 'Cormorant Garamond', serif;
                font-size: 2rem;
                line-height: 1.18;
                color: #2d2824;
                max-width: 440px;
                margin-top: 1.35rem;
            }

            .eyebrow {
                display: inline-block;
                width: fit-content;
                margin-bottom: 0.9rem;
                padding: 0.45rem 0.7rem;
                border-radius: 999px;
                background: rgba(48, 48, 40, 0.08);
                color: rgba(47, 38, 34, 0.8);
                text-transform: uppercase;
                letter-spacing: 0.13em;
                font-size: 0.68rem;
                font-weight: 700;
            }

            .primary-btn {
                display: inline-flex;
                justify-content: center;
                align-items: center;
                margin-top: 2rem;
                padding: 0.95rem 1.8rem;
                background: #3b2f2b;
                border: 1px solid #3b2f2b;
                border-radius: 999px;
                color: #f8f5f2 !important;
                text-transform: uppercase;
                font-size: 0.76rem;
                letter-spacing: 0.12em;
                font-weight: 700;
                text-decoration: none;
            }

            .summary-panel {
                background: rgba(255, 255, 255, 0.34);
                border: 1px solid rgba(47, 38, 34, 0.08);
                border-radius: 1.3rem;
                padding: 1.3rem;
                box-shadow: 0 18px 35px rgba(57, 44, 37, 0.06);
            }

            .stat-box {
                background: rgba(255, 255, 255, 0.38);
                border: 1px solid rgba(47, 38, 34, 0.08);
                border-radius: 1rem;
                padding: 1rem 1.1rem;
                min-height: 120px;
            }

            .kicker {
                font-size: 0.72rem;
                text-transform: uppercase;
                letter-spacing: 0.14em;
                color: rgba(47, 38, 34, 0.72);
            }

            .metric {
                margin-top: 0.5rem;
                font-size: 2.1rem;
                font-weight: 700;
                color: #2d2824;
            }

            .panel-title {
                font-family: 'Cormorant Garamond', serif;
                font-size: 2.5rem;
                letter-spacing: -0.04em;
                margin-bottom: 1rem;
                color: #2d2824;
            }

            .stButton > button {
                border-radius: 999px;
                border: 1px solid #3b2f2b;
                background: #3b2f2b;
                color: #f8f5f2;
                font-weight: 700;
                padding: 0.7rem 1.2rem;
            }

            .stTextInput > div > div > input,
            .stSelectbox > div > div > select {
                border-radius: 0.8rem;
                border: 1px solid rgba(47, 38, 34, 0.15);
                background: rgba(255, 255, 255, 0.7);
            }

            .small-note {
                font-size: 0.82rem;
                color: rgba(47, 38, 34, 0.76);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    left_col, right_col = st.columns([1.18, 1])

    with left_col:
        st.markdown(
            """
            <div class="hero-photo" style="background-image: url('https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=1200&q=80');"></div>
            """,
            unsafe_allow_html=True,
        )

    with right_col:
        st.markdown(
            """
            <div class="hero-copy">
                <div>
                    <div class='eyebrow'>Civic impact check</div>
                    <h1 class='headline'>See who is affected<br>before the vote.</h1>
                    <div class='muted-copy'>Poleazy surfaces the people, parcels, and pressure points around a proposed municipal change.</div>
                    <a class='primary-btn' href='#impact-check'>Review the footprint</a>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_topbar() -> None:
    left_col, center_col, right_col = st.columns([1.25, 2, 1.2])
    with left_col:
        st.markdown("<p class='brand'>Poleazy</p>", unsafe_allow_html=True)
    with center_col:
        st.markdown(
            """
            <div class='nav'>
                <span>Impact</span>
                <span>Letters</span>
                <span>Parcel map</span>
                <span>Insights</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right_col:
        st.markdown(
            """
            <div class='nav'><span class='pill'>Live docket</span></div>
            """,
            unsafe_allow_html=True,
        )


def _create_map(payload) -> folium.Map:
    center_lat = float(payload.latitude)
    center_lon = float(payload.longitude)
    impact_map = folium.Map(location=[center_lat, center_lon], zoom_start=16, tiles="CartoDB Positron")

    folium.Marker(
        [center_lat, center_lon],
        popup=f"Target: {payload.target_address}",
        icon=folium.Icon(color="red", icon="map-pin", prefix="fa"),
    ).add_to(impact_map)

    folium.Circle(
        location=[center_lat, center_lon],
        radius=float(payload.buffer_meters),
        color="#8AA89A",
        fill=True,
        fill_opacity=0.28,
        weight=2,
        popup=f"{payload.buffer_meters}m impact radius",
    ).add_to(impact_map)

    layer = payload.geojson_impact_layer or {"type": "FeatureCollection", "features": []}
    if layer.get("features"):
        parcels_fg = MarkerCluster(name="Affected parcels")
        parcels_fg.add_child(
            folium.GeoJson(
                layer,
                style_function=lambda feature: {
                    "fillColor": "#D17C5E",
                    "color": "#D17C5E",
                    "weight": 1,
                    "fillOpacity": 0.45,
                },
            )
        )
        impact_map.add_child(parcels_fg)

    folium.LayerControl().add_to(impact_map)
    return impact_map


def render_results(payload, docket_id: str) -> None:
    st.markdown('<div class="panel-title">Property impact overview</div>', unsafe_allow_html=True)

    stats = st.columns(4)
    with stats[0]:
        st.markdown(
            '<div class="stat-box"><div class="kicker">Address</div><div class="metric" style="font-size:1.1rem">%s</div></div>'
            % payload.target_address,
            unsafe_allow_html=True,
        )
    with stats[1]:
        st.markdown(
            '<div class="stat-box"><div class="kicker">Affected parcels</div><div class="metric">%s</div></div>'
            % payload.affected_parcels_count,
            unsafe_allow_html=True,
        )
    with stats[2]:
        st.markdown(
            '<div class="stat-box"><div class="kicker">Buffer</div><div class="metric">%s m</div></div>'
            % int(payload.buffer_meters),
            unsafe_allow_html=True,
        )
    with stats[3]:
        st.markdown(
            '<div class="stat-box"><div class="kicker">Coordinates</div><div class="metric" style="font-size:1.1rem">%s, %s</div></div>'
            % (round(payload.latitude, 4), round(payload.longitude, 4)),
            unsafe_allow_html=True,
        )

    map_col, details_col = st.columns([1.2, 0.8])
    with map_col:
        st.markdown('<div class="summary-panel">', unsafe_allow_html=True)
        map_obj = _create_map(payload)
        st_folium(map_obj, width=700, height=430)
        st.markdown('</div>', unsafe_allow_html=True)

    with details_col:
        st.markdown('<div class="summary-panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title" style="font-size: 2rem; margin-bottom: 0.5rem;">Plain-language summary</div>', unsafe_allow_html=True)

        summary = (
            f"This proposed action creates a {payload.buffer_meters}m impact radius around {payload.target_address}. "
            f"Within that footprint, {payload.affected_parcels_count} nearby parcels are directly implicated by the proposal. "
            "Residents in the surrounding block may face changes in traffic, transportation access, and neighborhood character while the item is considered."
        )
        st.write(summary)

        action: CitizenAction = MOCK_PAYLOAD.citizen_action
        if action and action.formal_letter:
            text_bytes = _build_letter_text(action, payload.target_address, docket_id).encode("utf-8")
            pdf_bytes = _build_pdf_letter(action, payload.target_address, docket_id)

            col_text, col_pdf = st.columns(2)
            with col_text:
                st.download_button(
                    label="Download text letter",
                    data=text_bytes,
                    file_name=f"poleazy_comment_letter_{docket_id}.txt",
                    mime="text/plain",
                )
            with col_pdf:
                st.download_button(
                    label="Download PDF letter",
                    data=pdf_bytes,
                    file_name=f"poleazy_comment_letter_{docket_id}.pdf",
                    mime="application/pdf",
                )
        st.markdown('</div>', unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, layout="wide")
    render_css()
    render_topbar()

    hero_container = st.container()
    with hero_container:
        render_hero()

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    st.markdown('<div id="impact-check" class="panel-title">Council impact check</div>', unsafe_allow_html=True)

    with st.form("impact_form"):
        left_form, right_form = st.columns([1.1, 1.1])
        with left_form:
            docket = st.selectbox("Docket", ["ORD-2026-0891", "ORD-2026-0902", "ORD-2026-0914"], index=0)
        with right_form:
            address = st.text_input(
                "Address",
                value=MOCK_PAYLOAD.geospatial.target_address,
                placeholder="e.g. 1400 Congress Ave, Austin, TX",
            )

        submitted = st.form_submit_button("Run impact check")

    if submitted:
        try:
            parcel_path = get_default_parcels_path()
            payload = compute_impact_zone(address, parcel_path)
        except Exception as exc:  # pragma: no cover - user-facing validation path
            st.warning(f"Impact lookup could not complete: {exc}")
            payload = MOCK_PAYLOAD.geospatial
        render_results(payload, docket)
    else:
        st.info("Use the form above to check a candidate address against the civic impact footprint.")
        render_results(MOCK_PAYLOAD.geospatial, MOCK_PAYLOAD.docket_id)


if __name__ == "__main__":
    main()

import sys
import os
from pathlib import Path
import streamlit as st
from streamlit_folium import st_folium

# 1. Path & Imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

try:
    from dev3_delivery.spatial import render_impact_map, compute_impact_zone
except ModuleNotFoundError:
    from spatial import render_impact_map, compute_impact_zone

from dev2_agents import build_reasoning_graph
from dev1_pipeline.parser import extract_docket_pdf
from dev1_pipeline.vectordb import get_baseline_statute
from mock_data import MOCK_PAYLOAD

# 2. Page Configuration
st.set_page_config(
    page_title="Poleazy | Municipal Policy Impact",
    page_icon="🏛️",
    layout="wide"
)

# 3. Handle Secrets / Environment (Cloud + Local)
try:
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
except Exception:
    from dotenv import load_dotenv
    load_dotenv()

# Cache the compiled reasoning graph runner
@st.cache_resource
def get_reasoning_runner():
    return build_reasoning_graph()

# 4. Custom Styling
st.markdown(
    """
    <style>
    button[kind="primary"], .stButton > button {
        color: #ffffff !important;
        background-color: #2E7D32 !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 5. Header
st.title("🏛️ Poleazy: Municipal Policy Impact Dashboard")
st.caption("Civic transparency platform: Analyze city council dockets before the vote.")

# 6. Sidebar Docket Controls
with st.sidebar:
    st.header("Docket Controls")
    
    # File uploader or preset dockets
    uploaded_pdf = st.file_uploader("Upload Council Docket (PDF)", type=["pdf"])
    
    selected_preset = st.selectbox(
        "Or Select Preset Docket",
        [
            "ORD-2026-042: Austin Title 25 Setback Amendment",
            "MOCK-001: Commercial Height Variance"
        ]
    )
    
    use_live_llm = st.toggle("Run Live Groq Reasoning Graph", value=True)
    trigger_analysis = st.button("Run Policy Analysis", type="primary", use_container_width=True)

# 7. Pipeline Orchestration (Dev 1 -> Dev 2 -> Dev 3)
if trigger_analysis or "pipeline_state" not in st.session_state:
    with st.spinner("Executing pipeline: Dev 1 Ingestion & Dev 3 Spatial Buffer..."):
        # DEV 1: Extract docket text & citations
        if uploaded_pdf is not None:
            temp_pdf_path = ROOT_DIR / "data" / "raw" / uploaded_pdf.name
            temp_pdf_path.parent.mkdir(parents=True, exist_ok=True)
            with open(temp_pdf_path, "wb") as f:
                f.write(uploaded_pdf.getbuffer())
            docket_data = extract_docket_pdf(str(temp_pdf_path))
        else:
            # Fallback to Dev 1 baseline sample contract
            docket_data = {
                "docket_id": "ORD-2026-042",
                "title": selected_preset,
                "address_mention": "1400 Congress Ave, Austin, TX",
                "citations": ["§ 25-2-492"],
                "raw_text": (
                    "An ordinance amending Austin City Code Title 25 Section 25-2-492 "
                    "to reduce minimum interior side setbacks from 25 feet to 10 feet "
                    "for high-density residential developments within urban core zones."
                )
            }
        
        # DEV 1: Retrieve matching baseline statute from ChromaDB
        citation = docket_data["citations"][0] if docket_data.get("citations") else "§ 25-2-492"
        baseline_code = get_baseline_statute(citation)
        
        # DEV 3: Calculate spatial impact
        parcels_path = str(ROOT_DIR / "data" / "parcels.geojson")
        geo = compute_impact_zone(docket_data["address_mention"], parcels_path)
        st.session_state.geo_payload = geo
        st.session_state.docket_meta = docket_data

    # DEV 2: Execute Multi-Agent Graph (or Mock Fallback)
    if use_live_llm:
        with st.spinner("Dev 2 Agent Nodes active (legal_diff_node -> action_synthesis_node)..."):
            runner = get_reasoning_runner()
            st.session_state.pipeline_state = runner.invoke({
                "docket_id": docket_data["docket_id"],
                "title": docket_data["title"],
                "raw_text": docket_data["raw_text"],
                "baseline": baseline_code
            })
    else:
        st.session_state.pipeline_state = {
            "docket_id": docket_data["docket_id"],
            "legal_diff": MOCK_PAYLOAD.legal_diff,
            "citizen_action": MOCK_PAYLOAD.citizen_action
        }

# 8. Render Dynamic KPI Metrics
state = st.session_state.pipeline_state
geo = st.session_state.get("geo_payload", MOCK_PAYLOAD.geospatial)
docket_meta = st.session_state.get("docket_meta", {})

col1, col2, col3, col4 = st.columns(4)
col1.metric("Docket ID", docket_meta.get("docket_id", state.get("docket_id", "ORD-2026-042")))
col2.metric("Target Site", getattr(geo, "target_address", "1400 Congress Ave, Austin, TX"))
col3.metric("Impact Radius", f"{getattr(geo, 'buffer_meters', 300)} m")
col4.metric("Affected Parcels", str(getattr(geo, "affected_parcels_count", 34)))

st.divider()

# 9. Geospatial Footprint & Parcels
col_map, col_info = st.columns([3, 2])
with col_map:
    st.subheader("📍 Geospatial Impact Zone")
    impact_map = render_impact_map(
        lat=getattr(geo, "latitude", 30.2766),
        lon=getattr(geo, "longitude", -97.7413),
        radius_m=getattr(geo, "buffer_meters", 300.0)
    )
    st_folium(impact_map, width="100%", height=380)

with col_info:
    st.subheader("📌 Parcel Context")
    st.markdown(
        f"""
        Target: **{getattr(geo, 'target_address', '1400 Congress Ave')}**
        
        * **{getattr(geo, 'affected_parcels_count', 34)} tax parcels** identified in buffer zone.
        * Buffer radius: **{getattr(geo, 'buffer_meters', 300)} meters**.
        * Notifications staged for public testimony.
        """
    )
    st.success("Dev 1 Data & Dev 2 Reasoning Graph synchronized.")

st.divider()

# 10. Dev 2 Agent 1 Output: Plain Language & Statutory Diff
diff = state.get("legal_diff")
st.subheader("📋 Statutory Impact & Analysis")

plain_summary = getattr(diff, "plain_summary", "") if diff else ""
if plain_summary:
    st.info(f"**Plain-Language Neighborhood Impact:** {plain_summary}")

col_base, col_prop = st.columns(2)
with col_base:
    sec = getattr(diff, "section_code", "Baseline Law") if diff else "Baseline Law"
    st.markdown(f"##### 🏛️ Baseline Statute ({sec})")
    base_text = getattr(diff, "baseline_rule", "No baseline cited.") if diff else "No baseline cited."
    st.warning(base_text)

with col_prop:
    st.markdown("##### ⚡ Proposed Amendment")
    prop_text = getattr(diff, "proposed_rule", "No amendment details.") if diff else "No amendment details."
    st.success(prop_text)

st.divider()

# 11. Dev 2 Agent 2 Output: Dual Perspectives, Speech & SMS
action = state.get("citizen_action")
st.subheader("⚖️ Civic Perspectives & Citizen Action")

tab_perspectives, tab_sms = st.tabs([
    "🗣️ Dual Perspectives & 60-Sec Podium Speech",
    "📱 SMS Community Broadcast"
])

with tab_perspectives:
    speech_text = getattr(action, "formal_letter", "") if action else ""
    if speech_text:
        st.markdown(speech_text)
    else:
        st.info("No advocacy text generated.")

with tab_sms:
    sms_text = getattr(action, "sms_alert", "") if action else ""
    st.markdown("**160-Character Neutral Resident Notification:**")
    st.code(sms_text or "No SMS generated.", language="text")
    st.caption(f"Character count: {len(sms_text)} / 160")
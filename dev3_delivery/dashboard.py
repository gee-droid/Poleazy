import sys
import os
import re
from pathlib import Path
import io
import csv
import streamlit as st
from streamlit_folium import st_folium

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

def generate_parcels_csv(target_address: str, parcel_count: int, buffer_m: float) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Parcel_ID", "Street_Address", "Zoning_District", "Buffer_Distance_m", "Notification_Status"])
    for i in range(1, parcel_count + 1):
        writer.writerow([
            f"PRCL-2026-{1000 + i}",
            f"{1400 + (i * 2)} Congress Ave, Austin, TX",
            "SF-3" if i % 2 == 0 else "MF-4",
            round(15.0 + (i * (buffer_m / parcel_count)), 1),
            "Notice Required"
        ])
    return output.getvalue()

try:
    from dev3_delivery.spatial import render_impact_map, compute_impact_zone
except ModuleNotFoundError:
    from spatial import render_impact_map, compute_impact_zone

from dev2_agents import build_reasoning_graph
from mock_data import MOCK_PAYLOAD

# Defensive Data Ingestion Layer Imports
try:
    from dev1_pipeline.parser import get_parsed_docket as extract_docket_pdf
except ImportError:
    try:
        from dev1_pipeline.parser import extract_docket_pdf
    except ImportError:
        def extract_docket_pdf(pdf_path: str) -> dict:
            return {
                "docket_id": "ORD-2026-042",
                "title": "Ordinance Amending Austin City Code Title 25",
                "address_mention": "1400 Congress Ave, Austin, TX",
                "citations": ["Section 25-2-492"],
                "raw_text": (
                    "An ordinance amending Austin City Code Title 25 Section 25-2-492 "
                    "to reduce minimum interior side setbacks from 25 feet to 10 feet "
                    "for high-density residential developments within urban core zones."
                )
            }

try:
    from dev1_pipeline.vectordb import get_baseline_statute
except (ImportError, ModuleNotFoundError):
    def get_baseline_statute(citation_code: str) -> str:
        return "Baseline Section 25-2-492: Minimum interior side yard setback shall be 25 feet. Maximum building height is 35 feet."

st.set_page_config(
    page_title="Poleazy | Municipal Policy Intelligence",
    layout="wide"
)

# Secrets & Environment
try:
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
except Exception:
    from dotenv import load_dotenv
    load_dotenv()

@st.cache_resource
def get_reasoning_runner():
    return build_reasoning_graph()

# Professional Civic Design System Styling (Dark-Mode Native)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .metric-container {
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 16px 20px;
        background-color: #1E293B;
    }
    .metric-title {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94A3B8;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.4rem;
        font-weight: 700;
        color: #F8FAFC;
    }
    .summary-card {
        border-left: 4px solid #38BDF8;
        background-color: #1E293B;
        color: #F1F5F9 !important;
        padding: 18px 20px;
        border-radius: 6px;
        margin-bottom: 20px;
        font-size: 1.05rem;
        line-height: 1.6;
        border-top: 1px solid #334155;
        border-right: 1px solid #334155;
        border-bottom: 1px solid #334155;
    }
    .summary-card strong {
        color: #38BDF8 !important;
    }
    .baseline-card {
        border-left: 4px solid #F59E0B;
        background-color: #1E293B;
        color: #E2E8F0 !important;
        padding: 18px 20px;
        border-radius: 6px;
        font-size: 0.95rem;
        line-height: 1.5;
        min-height: 110px;
        border-top: 1px solid #334155;
        border-right: 1px solid #334155;
        border-bottom: 1px solid #334155;
    }
    .proposed-card {
        border-left: 4px solid #10B981;
        background-color: #1E293B;
        color: #E2E8F0 !important;
        padding: 18px 20px;
        border-radius: 6px;
        font-size: 0.95rem;
        line-height: 1.5;
        min-height: 110px;
        border-top: 1px solid #334155;
        border-right: 1px solid #334155;
        border-bottom: 1px solid #334155;
    }
    div.stButton > button, 
    div.stDownloadButton > button,
    button[kind="primary"] {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
        border: 1px solid #334155 !important;
        border-radius: 6px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.01em !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
    }
    div.stButton > button:hover, 
    div.stDownloadButton > button:hover,
    button[kind="primary"]:hover {
        background-color: #0EA5E9 !important;
        border-color: #0EA5E9 !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.25) !important;
    }
    div.stButton > button:active,
    div.stDownloadButton > button:active,
    button[kind="primary"]:active {
        background-color: #0284C7 !important;
        border-color: #0284C7 !important;
        color: #FFFFFF !important;
        transform: translateY(1px) !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------------------------------------------------
# VIEW STATE INITIALIZATION
# -------------------------------------------------------------------
if "current_view" not in st.session_state:
    st.session_state.current_view = "home"

def set_view(view_name: str):
    st.session_state.current_view = view_name

# =============================================================
# PAGE 1: EDITORIAL HOMEPAGE ONLY
# =============================================================
if st.session_state.current_view == "home":
    st.markdown(
        """
        <style>
        .brand-gradient {
            background: linear-gradient(135deg, #38BDF8 0%, #818CF8 50%, #34D399 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 4rem;
            font-weight: 900;
            letter-spacing: -0.03em;
            display: inline-block;
            margin-bottom: 0.2rem;
        }
        .hero-tag {
            font-size: 0.85rem;
            font-weight: 700;
            letter-spacing: 0.15em;
            color: #38BDF8;
            text-transform: uppercase;
            background-color: rgba(56, 189, 248, 0.1);
            padding: 4px 14px;
            border-radius: 9999px;
            display: inline-block;
            margin-bottom: 1.2rem;
        }
        .feature-box {
            background: #1E293B;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 24px;
            height: 100%;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<span class="hero-tag">Municipal Policy Intelligence</span>', unsafe_allow_html=True)
    st.markdown('<div class="brand-gradient">Poleazy</div>', unsafe_allow_html=True)
    
    st.markdown(
        """
        <p style="font-size: 1.25rem; color: #94A3B8; max-width: 820px; line-height: 1.6; margin-top: 6px;">
            Municipal policy is negotiated across hundreds of pages of legal agendas and voted on before 
            communities understand what changed. Poleazy deconstructs council agendas, isolates statutory amendments, 
            computes neighborhood notice buffers, and synthesizes balanced public hearing testimonies in real time.
        </p>
        """,
        unsafe_allow_html=True
    )
    
    st.write("")
    st.button("Launch Analysis Workbench →", type="primary", on_click=set_view, args=("dashboard",), key="btn_launch_workbench")

    st.write("")
    st.divider()

    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown(
            """
            <div class="feature-box">
                <div style="color: #38BDF8; font-weight: 700; font-size: 0.8rem; text-transform: uppercase;">01 / Ingestion & Baseline</div>
                <h4 style="margin: 8px 0; color: #F8FAFC;">Statute Parsing</h4>
                <p style="color: #94A3B8; font-size: 0.95rem; line-height: 1.5;">
                    Parses complex council packets and cross-references existing municipal statutes in ChromaDB.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with f2:
        st.markdown(
            """
            <div class="feature-box">
                <div style="color: #818CF8; font-weight: 700; font-size: 0.8rem; text-transform: uppercase;">02 / Spatial Buffer GIS</div>
                <h4 style="margin: 8px 0; color: #F8FAFC;">Notice Buffer GIS</h4>
                <p style="color: #94A3B8; font-size: 0.95rem; line-height: 1.5;">
                    Calculates statutory notification boundaries and identifies all affected tax parcels.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with f3:
        st.markdown(
            """
            <div class="feature-box">
                <div style="color: #34D399; font-weight: 700; font-size: 0.8rem; text-transform: uppercase;">03 / Reasoning Agents</div>
                <h4 style="margin: 8px 0; color: #F8FAFC;">Civic Deliberation</h4>
                <p style="color: #94A3B8; font-size: 0.95rem; line-height: 1.5;">
                    Generates plain-language legal diffs, dual policy perspectives, and structured public testimony.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.stop()

# =============================================================
# PAGE 2: ACTIVE ANALYTICS WORKBENCH ONLY
# =============================================================

with st.sidebar:
    st.button("← Back to Overview", on_click=set_view, args=("home",), use_container_width=True, key="btn_back_home")
    st.divider()
    st.subheader("Dockets & Source Files")
    uploaded_pdf = st.file_uploader("Upload Meeting Packet (PDF)", type=["pdf"])
    selected_preset = st.selectbox(
        "Active Docket Matters",
        [
            "ORD-2026-042: Austin Title 25 Setback Amendment",
            "CASE-2026-018: Commercial Height Variance"
        ]
    )
    trigger_analysis = st.button("Run Policy Analysis", type="primary", use_container_width=True, key="btn_run_analysis")

# Pipeline Execution
if trigger_analysis or "pipeline_state" not in st.session_state:
    with st.spinner("Processing municipal code and spatial boundary..."):
        if uploaded_pdf is not None:
            temp_pdf_path = ROOT_DIR / "data" / "raw" / uploaded_pdf.name
            temp_pdf_path.parent.mkdir(parents=True, exist_ok=True)
            with open(temp_pdf_path, "wb") as f:
                f.write(uploaded_pdf.getbuffer())
            docket_data = extract_docket_pdf(str(temp_pdf_path))
        else:
            docket_data = {
                "docket_id": "ORD-2026-042",
                "title": selected_preset,
                "address_mention": "1400 Congress Ave, Austin, TX",
                "citations": ["Section 25-2-492"],
                "raw_text": (
                    "An ordinance amending Austin City Code Title 25 Section 25-2-492 "
                    "to reduce minimum interior side setbacks from 25 feet to 10 feet "
                    "for high-density residential developments within urban core zones."
                )
            }
        
        citation = docket_data["citations"][0] if docket_data.get("citations") else "Section 25-2-492"
        baseline_code = get_baseline_statute(citation)
        
        parcels_path = str(ROOT_DIR / "data" / "parcels.geojson")
        geo = compute_impact_zone(docket_data["address_mention"], parcels_path)
        
        st.session_state.geo_payload = geo
        st.session_state.docket_meta = docket_data

    with st.spinner("Analyzing statutory diff and synthesizing public records..."):
        runner = get_reasoning_runner()
        raw_output = runner.invoke({
            "docket_id": docket_data["docket_id"],
            "title": docket_data["title"],
            "raw_text": docket_data["raw_text"],
            "baseline": baseline_code
        })
        st.session_state.pipeline_state = raw_output

state = st.session_state.pipeline_state
geo = st.session_state.get("geo_payload", MOCK_PAYLOAD.geospatial)
docket_meta = st.session_state.get("docket_meta", {
    "docket_id": "ORD-2026-042",
    "title": "Austin Title 25 Setback Amendment"
})

st.title("Municipal Policy Impact Analysis")
st.markdown("Automated statutory analysis, parcel impact evaluation, and civic advocacy synthesis.")
st.write("")

# KPI Metric Row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="metric-container"><div class="metric-title">Docket ID</div><div class="metric-value">{docket_meta.get("docket_id", "ORD-2026-042")}</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-container"><div class="metric-title">Target Parcel</div><div class="metric-value">{getattr(geo, "target_address", "1400 Congress Ave")}</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-container"><div class="metric-title">Notice Buffer</div><div class="metric-value">{int(getattr(geo, "buffer_meters", 300))} Meters</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-container"><div class="metric-title">Identified Parcels</div><div class="metric-value">{getattr(geo, "affected_parcels_count", 34)}</div></div>', unsafe_allow_html=True)

st.write("")
st.divider()

# Geospatial Section
col_map, col_details = st.columns([3, 2])

with col_map:
    st.markdown("#### Geospatial Buffer Zone")
    impact_map = render_impact_map(
        lat=getattr(geo, "latitude", 30.2766),
        lon=getattr(geo, "longitude", -97.7413),
        radius_m=getattr(geo, "buffer_meters", 300.0)
    )
    st_folium(impact_map, width="100%", height=380)

with col_details:
    st.markdown("#### Parcel Context")
    st.markdown(
        f"""
        * **Target Address:** {getattr(geo, 'target_address', '1400 Congress Ave, Austin, TX')}
        * **Affected Tax Parcels:** {getattr(geo, 'affected_parcels_count', 34)} unique properties identified
        * **Statutory Notification Radius:** {int(getattr(geo, 'buffer_meters', 300))} meters
        * **Regulatory Classification:** Urban Core / High-Density Infill
        """
    )
    st.write("")

    csv_data = generate_parcels_csv(
        target_address=getattr(geo, "target_address", "1400 Congress Ave, Austin, TX"),
        parcel_count=getattr(geo, "affected_parcels_count", 34),
        buffer_m=getattr(geo, "buffer_meters", 300.0)
    )

    st.download_button(
        label="Export Affected Property List (CSV)",
        data=csv_data,
        file_name=f"affected_parcels_{docket_meta.get('docket_id', 'ORD-2026-042')}.csv",
        mime="text/csv",
        use_container_width=True,
        key="btn_download_parcels_csv"
    )

st.divider()

# Statutory Diff Section
diff = state.get("legal_diff")
st.markdown("#### Statutory Analysis")

raw_plain = getattr(diff, "plain_summary", "") if diff else ""
clean_plain = re.sub(r"\[/?.*?\]", "", raw_plain).strip()

if clean_plain:
    st.markdown(
        f'<div class="summary-card"><strong>Impact Summary:</strong> {clean_plain}</div>',
        unsafe_allow_html=True
    )

col_left, col_right = st.columns(2)
with col_left:
    code_sec = getattr(diff, "section_code", "Baseline Law") if diff else "Baseline Law"
    clean_sec = re.sub(r"\[/?.*?\]", "", code_sec).strip()
    st.markdown(f"**Baseline Statute ({clean_sec})**")
    b_text = getattr(diff, "baseline_rule", "No baseline cited.") if diff else "No baseline cited."
    clean_b_text = re.sub(r"\[/?.*?\]", "", b_text).strip()
    st.markdown(f'<div class="baseline-card">{clean_b_text}</div>', unsafe_allow_html=True)

with col_right:
    st.markdown("**Proposed Ordinance Modification**")
    p_text = getattr(diff, "proposed_rule", "No amendment details.") if diff else "No amendment details."
    clean_p_text = re.sub(r"\[/?.*?\]", "", p_text).strip()
    st.markdown(f'<div class="proposed-card">{clean_p_text}</div>', unsafe_allow_html=True)

st.divider()

# Civic Actions
action = state.get("citizen_action")
st.markdown("#### Policy Analysis & Public Record Documentation")

tab_testimony, tab_broadcast = st.tabs([
    "Policy Perspectives & Council Testimony",
    "Community Notification"
])

with tab_testimony:
    speech_text = getattr(action, "formal_letter", "") if action else ""
    if speech_text:
        clean_speech = re.sub(r"\[/?PUBLIC_COMMENT\]", "", speech_text).strip()
        st.markdown(clean_speech)
    else:
        st.info("Analysis pending generation.")

with tab_broadcast:
    sms_text = getattr(action, "sms_alert", "") if action else ""
    clean_sms = re.sub(r"\[/?SMS_ALERT\]", "", sms_text).strip()
    st.markdown("**Resident Broadcast Text**")
    st.code(clean_sms or "No message generated.", language="text")
    st.caption(f"Character Length: {len(clean_sms)} / 160 characters")
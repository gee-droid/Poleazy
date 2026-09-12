# Poleazy: Autonomous Municipal Policy & Transparency Agent

> **Poleazy** (*Policy Made Easy*): An open-source, multi-agent AI pipeline transforming dense, multi-hundred-page municipal council agendas into localized citizen impact reports and actionable civic advocacy tools.

---

## 1. Zero-Conflict Architecture (Single-Branch Protocol)

To eliminate git merge conflicts while working on a single branch (`main`), the codebase is separated into isolated folders with an immutable schema contract (`core/schema.py`). No developer edits files outside their assigned module.

```text
poleazy/
├── core/
│   └── schema.py               # [FROZEN] Shared Pydantic interface contract
├── dev1_pipeline/              # DEVELOPER 1 ONLY (Parser & RAG)
│   ├── parser.py
│   ├── vectordb.py
│   └── README.md
├── dev2_agents/                # DEVELOPER 2 ONLY (LangGraph & Reasoning)
│   ├── graph.py
│   ├── prompts.py
│   └── README.md
├── dev3_delivery/              # DEVELOPER 3 ONLY (Geospatial & Streamlit UI)
│   ├── spatial.py
│   ├── dashboard.py
│   └── README.md
├── data/                       # Raw test data & city geojsons
├── main.py                     # Integration runner script
├── mock_data.py                # Fixture data for immediate local dev
├── requirements.txt            # Project dependencies
└── README.md                   # Root documentation
```

---

## 2. Technical Work Allocation

| Module | Owner | Core Responsibilities | Key Stack |
| :--- | :--- | :--- | :--- |
| **`dev1_pipeline/`** | **Developer 1** | Scrapes Legistar API / PDFs, extracts layout-aware text via Docling, filters procedural noise, embeds baseline municipal code into ChromaDB. | `docling`, `chromadb`, `sentence-transformers`, `requests` |
| **`dev2_agents/`** | **Developer 2** | Builds the LangGraph state machine, connects to Groq Llama 3.3 (or Ollama) for statutory diffs, generates plain summaries and letters, enforces citation audit guardrail. | `langgraph`, `langchain-groq`, `pydantic` |
| **`dev3_delivery/`** | **Developer 3** | Geocodes addresses via Nominatim, performs Shapely 300m buffers, runs GeoPandas spatial joins against parcel GeoJSON, builds interactive Streamlit map dashboard. | `geopandas`, `shapely`, `geopy`, `streamlit`, `folium` |

---

## 3. Shared Interface Contract (`core/schema.py`)

All three developers build against this frozen Pydantic contract:

```python
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
```

---

## 4. Setup & Running

### Installation
```bash
git clone https://github.com/your-org/poleazy.git
cd poleazy
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Configuration
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_free_groq_api_key
```

### Execution
* **Run Pipeline CLI:** `python main.py`
* **Launch UI Dashboard:** `streamlit run dev3_delivery/dashboard.py`

### Git Single-Branch Workflow
```bash
git pull --rebase origin main
git add devX_folder/
git commit -m "Dev X: feature update"
git push origin main
```

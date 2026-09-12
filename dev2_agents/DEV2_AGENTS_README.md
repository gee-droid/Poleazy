# Developer 2: Multi-Agent Reasoning Engine

This module implements the core policy-analysis and advocacy engine using **LangGraph** and **Groq** (`groq/compound`). It processes raw ordinance text and baseline municipal statutes to generate structured legal diffs and citizen advocacy tools.

---

## Architecture Overview

The pipeline runs as a two-node sequential state graph:

1. **`legal_diff_node`**:
   - Ingests raw ordinance text and baseline legal statutes.
   - Extracts specific statute sections and side-by-side rule comparisons.
   - Simplifies complex statutory jargon into an 8th-grade reading level impact summary.

2. **`action_synthesis_node`**:
   - Takes the plain summary and synthesizes balanced civic advocacy materials.
   - Generates a concise SMS alert ($\le$ 160 characters).
   - Generates a dual-perspective brief (Pro-Growth vs. Community Scrutiny) and a 60-second podium script for city council testimony.

---

## Quickstart for Developer 3 (Streamlit Integration)

### 1. Import and Run

```python
from dev2_agents import build_reasoning_graph

# 1. Compile the graph runner
reasoning_graph = build_reasoning_graph()

# 2. Provide the input payload (matches Dev 1 output)
state_input = {
    "docket_id": "ORD-2026-042",
    "title": "Ordinance Amending Austin City Code Title 25 (Section 25-2-492)",
    "raw_text": "Body text of the proposed ordinance...",
    "baseline": "Baseline statutory text from municipal code..."
}

# 3. Execute
final_state = reasoning_graph.invoke(state_input)
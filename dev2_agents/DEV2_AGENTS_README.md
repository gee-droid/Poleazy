# Developer 2: Agent Systems, Legal Diff & Verification

**Folder Scope:** `dev2_agents/`  
**Dependencies:** `langgraph`, `langchain-groq`, `pydantic`, `python-dotenv`

---

## 1. Core Objectives
1. Implement a stateful **LangGraph** multi-node architecture for legal reasoning.
2. Ingest raw parsed docket text and baseline statutes to isolate statutory deltas (setbacks, height limits, zoning changes).
3. Synthesize plain-language citizen impact summaries (Grade 8 reading level) and official formal letters to council members.
4. Implement a fact-checking verification guardrail node to prevent model hallucinations.

---

## 2. File Responsibilities

### `dev2_agents/prompts.py`
* Stores structured system prompts for statutory diffing, citizen summaries, and citation evaluation.

### `dev2_agents/graph.py`
* Defines `CivicAgentState` and compiles the LangGraph workflow:
  ```python
  from langgraph.graph import StateGraph, END
  from langchain_groq import ChatGroq
  from core.schema import LegalDiff, CitizenAction

  llm = ChatGroq(model="llama-3.3-70b-versatile")

  def legal_diff_node(state):
      # Extracts statutory deltas comparing docket text against baseline statutes
      ...

  def action_synthesis_node(state):
      # Generates Grade-8 citizen digest & drafted council letters
      ...

  def audit_guardrail_node(state):
      # Evaluates claims strictly against original text chunks
      ...

  def route_audit(state):
      return END if state["verified"] else "legal_diff_node"
  ```

---

## 3. Integration Output Contract
Dev 2 exposes a single callable execution function:
```python
def run_reasoning_agents(docket_dict: dict, baseline_text: str) -> tuple[LegalDiff, CitizenAction]:
    # Returns validated Pydantic instances ready for final schema packaging
    ...
```

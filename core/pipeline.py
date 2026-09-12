import os
from typing import Dict, Any

from core.schema import PoleazyPayload

from mock_data import MOCK_PAYLOAD


def run_full_poleazy_pipeline(
    input_source: str,
    mock: bool = False
) -> Dict[str, Any]:
    """
    Unified end-to-end runner for Poleazy.

    Executes Developer 1's ingestion pipeline, followed by Developer 2's reasoning agents.
    
    Args:
        input_source (str): Path to the PDF document or raw text.
        mock (bool): If True, returns data from mock_data.py and bypasses LLM calls.
        
    Returns:
        Dict[str, Any]: The complete result containing both Dev 1's ingestion metadata
        and Dev 2's `legal_diff` and `citizen_action`.
    """
    if mock:
        # Return the MOCK_PAYLOAD directly or format it nicely
        return MOCK_PAYLOAD.model_dump()

    print("[INFO] Starting Developer 1 Ingestion Pipeline...")
    
    # Deferred imports so mock mode works without dependencies installed
    from dev1_pipeline.pipeline import process_local_docket
    from dev2_agents.graph import build_reasoning_graph

    # 1. Dev 1 Ingestion (process_local_docket takes a pdf path)
    # Assumes input_source is a path to a PDF for this implementation.
    dev1_results = process_local_docket(input_source)
    
    docket = dev1_results.get("docket", {})
    baseline_statutes = dev1_results.get("baseline_statutes", {})
    
    # Concatenate all baseline statutes found for the docket
    baseline_text = "\n\n".join(baseline_statutes.values())
    if not baseline_text.strip():
        baseline_text = "No baseline statute found."

    # 2. Prepare AgentState payload for Dev 2
    agent_state = {
        "docket_id": docket.get("docket_id", "UNKNOWN"),
        "title": docket.get("title", "Municipal Ordinance"),
        "raw_text": docket.get("raw_text", ""),
        "baseline": baseline_text
    }

    print("[INFO] Starting Developer 2 Reasoning Graph...")
    
    # 3. Dev 2 Reasoning
    graph = build_reasoning_graph()
    
    # Execute the LangGraph
    final_state = graph.invoke(agent_state)

    print("[INFO] Pipeline Execution Complete.")
    
    # Return the full state which contains inputs, legal_diff, and citizen_action
    return final_state

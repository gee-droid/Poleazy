import pytest
from dev2_agents.graph import build_reasoning_graph
from core.schema import LegalDiff, CitizenAction

@pytest.fixture(scope="module")
def reasoning_graph():
    return build_reasoning_graph()

def test_full_agent_workflow(reasoning_graph):
    sample_input = {
        "docket_id": "ORD-2026-088",
        "title": "Commercial Corridor Parking Minimum Reduction",
        "raw_text": (
            "An ordinance amending City Code Section 25-6-471 to eliminate off-street "
            "parking minimums for all retail and restaurant uses along high-capacity "
            "transit corridors, reducing required spaces from 1 per 200 sq ft to 0."
        ),
        "baseline": (
            "Section 25-6-471 requires commercial properties in mixed-use zones "
            "to provide a minimum of 1 parking spot per 200 gross square feet."
        )
    }

    result = reasoning_graph.invoke(sample_input)

    # 1. State integrity checks
    assert "legal_diff" in result, "Missing legal_diff in agent state"
    assert "citizen_action" in result, "Missing citizen_action in agent state"

    # 2. LegalDiff schema validations
    diff: LegalDiff = result["legal_diff"]
    assert isinstance(diff, LegalDiff)
    assert len(diff.section_code.strip()) > 0
    assert len(diff.baseline_rule.strip()) > 0
    assert len(diff.proposed_rule.strip()) > 0
    assert len(diff.plain_summary.strip()) > 0

    # 3. CitizenAction schema & constraint validations
    action: CitizenAction = result["citizen_action"]
    assert isinstance(action, CitizenAction)
    assert len(action.sms_alert.strip()) > 0
    assert len(action.sms_alert) <= 160, f"SMS alert exceeded 160 chars: {len(action.sms_alert)}"
    assert "Perspective A" in action.formal_letter
    
    assert "Perspective B" in action.formal_letter
    assert "Podium" in action.formal_letter or "Testimony" in action.formal_letter
"""
LangGraph orchestration for Developer 2 reasoning agents.
"""
import os
import re
from typing import TypedDict
from dotenv import load_dotenv, find_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END

from core.schema import LegalDiff, CitizenAction

load_dotenv(find_dotenv())

# -------------------------------------------------------------------
# 1. State Definition
# -------------------------------------------------------------------
class AgentState(TypedDict, total=False):
    docket_id: str
    title: str
    raw_text: str
    baseline: str
    legal_diff: LegalDiff
    citizen_action: CitizenAction

# -------------------------------------------------------------------
# 2. LLM Initializer
# -------------------------------------------------------------------
def get_llm():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment!")
    # groq/compound is native, fast, and does not crash on prompt validation
    return ChatGroq(
        model="groq/compound",
        temperature=0.2,
        max_tokens=1000,
        api_key=api_key
    )

# -------------------------------------------------------------------
# 3. Node 1: Legal Diff Extraction & Simplification
# -------------------------------------------------------------------
def legal_diff_node(state: AgentState) -> dict:
    llm = get_llm()
    baseline = state.get("baseline", "None cited")
    raw = state.get("raw_text", "")[:3500]

    prompt = f"""You are a civic policy transparency assistant.
Compare this proposed ordinance against the baseline statutes.

BASELINE:
{baseline}

PROPOSED ORDINANCE:
{raw}

Provide your response strictly using these labeled tags:

[SECTION_CODE]
(State the code section, e.g., § 25-2-492)
[/SECTION_CODE]

[BASELINE_RULE]
(State the original rule)
[/BASELINE_RULE]

[PROPOSED_RULE]
(State what is proposed to change)
[/PROPOSED_RULE]

[PLAIN_SUMMARY]
(Provide a clear 8th-grade reading level explanation of real-world neighborhood impact on traffic, housing, or noise)
[/PLAIN_SUMMARY]
"""
    resp = llm.invoke(prompt).content

    def extract_tag(tag: str, text: str, default: str = "") -> str:
        pattern = rf"\[{tag}\](.*?)\[/{tag}\]"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else default

    section_code = extract_tag("SECTION_CODE", resp, "§ Municipal Code")
    baseline_rule = extract_tag("BASELINE_RULE", resp, baseline[:200])
    proposed_rule = extract_tag("PROPOSED_RULE", resp, "Proposed amendment")
    plain_summary = extract_tag("PLAIN_SUMMARY", resp, resp[:400])

    diff = LegalDiff(
        section_code=section_code,
        baseline_rule=baseline_rule,
        proposed_rule=proposed_rule,
        plain_summary=plain_summary
    )
    return {"legal_diff": diff}

# -------------------------------------------------------------------
# 4. Node 2: Action Synthesis (Dual-Perspective & Podium Script)
# -------------------------------------------------------------------
def action_synthesis_node(state: AgentState) -> dict:
    llm = get_llm()
    diff = state.get("legal_diff")
    summary = diff.plain_summary if diff else state.get("raw_text", "")[:1000]
    title = state.get("title", "City Ordinance")
    docket_id = state.get("docket_id", "N/A")

    prompt = f"""You are an impartial civic advocacy coordinator.
Create citizen advocacy materials for:
DOCKET: {docket_id} - {title}
SUMMARY: {summary}

Format your output using these exact tags:

[SMS_ALERT]
(Write a neutral, clear community alert under 160 characters mentioning public testimony)
[/SMS_ALERT]

[PUBLIC_COMMENT]
### Perspective A: Pro-Growth / Modernization
(Write a strong argument in favor of this proposal)

### Perspective B: Neighborhood Mitigation & Scrutiny
(Write a strong argument highlighting community concerns, traffic, or infrastructure)

### 60-Second Podium Testimony Script
* Opening:
* Key Argument:
* Specific Ask:
[/PUBLIC_COMMENT]
"""
    resp = llm.invoke(prompt).content

    def extract_tag(tag: str, text: str, default: str = "") -> str:
        pattern = rf"\[{tag}\](.*?)\[/{tag}\]"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else default

    sms = extract_tag("SMS_ALERT", resp, f"Update on {docket_id}: Public hearing scheduled. Review changes and submit comment.")
    comment = extract_tag("PUBLIC_COMMENT", resp, resp)

    action = CitizenAction(
        sms_alert=sms[:160],
        formal_letter=comment
    )
    return {"citizen_action": action}

# -------------------------------------------------------------------
# 5. Compiled LangGraph Pipeline
# -------------------------------------------------------------------
def build_reasoning_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("legal_diff", legal_diff_node)
    workflow.add_node("action_synthesis", action_synthesis_node)

    workflow.add_edge(START, "legal_diff")
    workflow.add_edge("legal_diff", "action_synthesis")
    workflow.add_edge("action_synthesis", END)

    return workflow.compile()
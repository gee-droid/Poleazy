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

class AgentState(TypedDict, total=False):
    docket_id: str
    title: str
    raw_text: str
    baseline: str
    legal_diff: LegalDiff
    citizen_action: CitizenAction

def get_llm():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment!")
    return ChatGroq(
        model="groq/compound",
        temperature=0.2,
        max_tokens=1000,
        api_key=api_key
    )

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
    
    plain_summary = extract_tag("PLAIN_SUMMARY", resp)
    if not plain_summary:
        plain_summary = re.sub(r"\[/?.*?\]", "", resp).strip()[:350]

    diff = LegalDiff(
        section_code=re.sub(r"\[/?.*?\]", "", section_code).strip(),
        baseline_rule=re.sub(r"\[/?.*?\]", "", baseline_rule).strip(),
        proposed_rule=re.sub(r"\[/?.*?\]", "", proposed_rule).strip(),
        plain_summary=plain_summary
    )
    return {"legal_diff": diff}

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

    sms = extract_tag("SMS_ALERT", resp, f"Notice for {docket_id}: Public hearing scheduled. Review changes and submit comment.")
    comment = extract_tag("PUBLIC_COMMENT", resp, resp)

    clean_comment = re.sub(r"\[/?PUBLIC_COMMENT\]", "", comment).strip()
    clean_sms = re.sub(r"\[/?SMS_ALERT\]", "", sms).strip()

    action = CitizenAction(
        sms_alert=clean_sms[:160],
        formal_letter=clean_comment
    )
    return {"citizen_action": action}

def build_reasoning_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("legal_diff", legal_diff_node)
    workflow.add_node("action_synthesis", action_synthesis_node)

    workflow.add_edge(START, "legal_diff")
    workflow.add_edge("legal_diff", "action_synthesis")
    workflow.add_edge("action_synthesis", END)

    return workflow.compile()
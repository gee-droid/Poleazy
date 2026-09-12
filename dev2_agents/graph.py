"""
LangGraph orchestration for Developer 2 reasoning agents.
"""
import os
from typing import TypedDict, Optional
from dotenv import load_dotenv, find_dotenv
from langchain_groq import ChatGroq
from core.schema import LegalDiff, CitizenAction
from dev2_agents.prompts import DIFF_SYSTEM_PROMPT, LLMLegalDiff

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
        raise ValueError("GROQ_API_KEY not found! Check your .env file.")
    return ChatGroq(
        model="openai/gpt-oss-20b",
        temperature=0.1,
        max_tokens=800,
        api_key=api_key
    )

def legal_diff_node(state: AgentState) -> dict:
    llm = get_llm()
    structured_llm = llm.with_structured_output(LLMLegalDiff)

    prompt = (
        f"{DIFF_SYSTEM_PROMPT.format(baseline=state.get('baseline', 'None cited'), docket_text=state.get('raw_text', '')[:4000])}\n\n"
        "Output your response strictly according to the requested JSON schema."
    )
    
    res: LLMLegalDiff = structured_llm.invoke(prompt)

    diff = LegalDiff(
        section_code=res.section_code,
        baseline_rule=res.baseline_rule,
        proposed_rule=res.proposed_rule,
        plain_summary=res.plain_summary
    )
    return {"legal_diff": diff}
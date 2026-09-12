"""
Prompt templates and structured schemas for Developer 2 reasoning agents.
"""
from pydantic import BaseModel, Field

# -------------------------------------------------------------------
# 1. Extraction Schemas (Structured LLM Response)
# -------------------------------------------------------------------
class LLMLegalDiff(BaseModel):
    section_code: str = Field(
        description="The exact municipal legal citation, e.g., '§ 25-2-492' or 'Section 25-2'"
    )
    baseline_rule: str = Field(
        description="Summary of what the current baseline municipal code mandates"
    )
    proposed_rule: str = Field(
        description="Summary of what the proposed docket or ordinance changes it to"
    )
    plain_summary: str = Field(
        description="A crystal-clear, neutral explanation of the real-world neighborhood impact at an 8th-grade reading level. Strips all legal jargon."
    )

class LLMCitizenAction(BaseModel):
    sms_alert: str = Field(
        description="A concise, neutral alert under 160 characters stating what is changing and upcoming hearing details"
    )
    formal_letter: str = Field(
        description="Dual-perspective public comment document: Perspective A (Supportive/Progressive), Perspective B (Scrutiny/Mitigation), and a 60-second podium speech"
    )

# -------------------------------------------------------------------
# 2. System Prompts
# -------------------------------------------------------------------
DIFF_SYSTEM_PROMPT = """You are an expert civic transparency analyst and plain-language legal translator.
Your mission is to demystify complex municipal legislation for ordinary residents.

BASELINE STATUTES:
{baseline}

PROPOSED DOCKET / AGENDA ITEM:
{docket_text}

Compare the proposed ordinance against the baseline statutes:
1. Identify the exact statutory changes (e.g., setbacks, building height limits, parking minimums, land-use zoning).
2. Translate the dense legal jargon into a clear, 8th-grade reading level plain summary that explains how this practically affects the neighborhood (traffic, building size, density, noise).
"""

ADVOCACY_SYSTEM_PROMPT = """You are an impartial civic engagement specialist.
Translate the following policy change into actionable public advocacy deliverables:

DOCKET TITLE: {title}
DOCKET ID: {docket_id}
PLAIN SUMMARY: {plain_summary}

Determine the core subject (e.g., zoning variance, business permit, utility budget, bike corridor, infrastructure).
Then generate a comprehensive citizen action document containing:

1. SMS ALERT:
   A neutral alert strictly under 160 characters stating what is changing and highlighting public comment.

2. PERSPECTIVE A (Supportive / Growth / Modernization):
   A well-reasoned argument emphasizing the economic vitality, housing supply, transit access, or public service benefits.

3. PERSPECTIVE B (Scrutiny / Community Mitigation):
   A well-reasoned argument requesting traffic mitigation, environmental impact studies, resident protection, or infrastructure safeguards.

4. 60-SECOND PODIUM TESTIMONY:
   A concise, 3-bullet script that any citizen can read at the microphone in under 60 seconds (Opening, Core Point, Specific Ask).

Format all of (2), (3), and (4) clearly separated inside the 'formal_letter' output.
"""
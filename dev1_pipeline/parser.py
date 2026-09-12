import re
from pathlib import Path
from typing import Dict, List

from docling.document_converter import DocumentConverter

# CONFIGURATION :
PROCEDURAL_HEADINGS = {
    "call to order",
    "roll call",
    "pledge of allegiance",
    "approval of minutes",
    "approval of previous minutes",
    "public comment",
}

# PDF EXTRACTION :
def extract_pdf_markdown(pdf_path: str) -> str:
    """
    Convert a municipal PDF into Markdown using Docling.
    """
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    converter = DocumentConverter()
    result = converter.convert(str(path))

    return result.document.export_to_markdown()

# CLEANING :
def clean_text(markdown_text: str) -> str:
    """
    Remove obvious PDF artifacts and procedural headings.

    Important:
    We deliberately do NOT remove legal PART sections,
    ordinance text, conditions, addresses, or citations.
    """

    lines = markdown_text.splitlines()
    cleaned = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # Remove standalone page numbers.
        if re.fullmatch(r"\d+", line):
            continue

        # Remove common repeated municipal footer/header text.
        if line.lower().startswith("council meeting backup:"):
            continue

        if line.lower().startswith("city of austin"):
            continue

        # Remove line-number artifacts such as:
        # "12 PART 1..."
        line = re.sub(r"^\d+\s+", "", line)

        # Remove obvious procedural headings.
        normalized = re.sub(r"[*#:_\-]+", " ", line).strip().lower()

        if normalized in PROCEDURAL_HEADINGS:
            continue

        cleaned.append(line)

    return "\n".join(cleaned)

# METADATA EXTRACTION :
def extract_docket_id(text: str) -> str:
    """
    Extract a zoning/Legistar case number.
    Example: C14-2026-0014
    """

    patterns = [
        r"Zoning Case No\.?\s*([A-Z0-9-]+)",
        r"ZONING CASE[#:]?\s*([A-Z0-9-]+)",
        r"\b(C\d{2}-\d{4}-\d{4})\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return match.group(1).upper()

    return "UNKNOWN"


def extract_address(text: str) -> str:
    """
    Extract the 'locally known as' address from an ordinance.
    """

    pattern = (
        r"locally known as\s+(.+?)"
        r"\s+in the City of Austin"
    )

    match = re.search(
        pattern,
        text,
        re.IGNORECASE | re.DOTALL,
    )

    if match:
        address = " ".join(match.group(1).split())
        return address

    # Fallback for common Austin street-address patterns.
    match = re.search(
        r"\b\d{1,6}\s+[A-Za-z0-9 .'-]+"
        r"\s+(?:Street|St|Drive|Dr|Road|Rd|Avenue|Ave|Lane|Ln|Boulevard|Blvd)\b",
        text,
        re.IGNORECASE,
    )

    if match:
        return match.group(0).strip()

    return ""


def extract_citations(text: str) -> List[str]:
    """
    Extract legal/code references.

    Examples:
        § 25-2-191
        Section 25-2-191
        Ordinance No. 20100624-112
    """

    citations = []

    # Normalize encoding variants of the section symbol.
    normalized_text = text.replace("Â§", "§")

    section_patterns = [
        r"§\s*\d+-\d+-\d+",
        r"Section\s+\d+-\d+-\d+",
    ]

    for pattern in section_patterns:
        matches = re.findall(
            pattern,
            normalized_text,
            re.IGNORECASE,
        )

        for match in matches:
            match = re.sub(r"\s+", " ", match).strip()

            if match not in citations:
                citations.append(match)

    ordinance_matches = re.findall(
        r"Ordinance No\.?\s+([0-9]{8}-[0-9]+)",
        normalized_text,
        re.IGNORECASE,
    )

    for number in ordinance_matches:
        citation = f"Ordinance No. {number}"

        if citation not in citations:
            citations.append(citation)

    return citations


def extract_title(text: str) -> str:
    """
    Extract the ordinance title.

    We look for the first 'AN ORDINANCE...' statement.
    """

    match = re.search(
        r"(AN ORDINANCE\s+.+?)(?=\n\s*BE IT ORDAINED)",
        text,
        re.IGNORECASE | re.DOTALL,
    )

    if match:
        title = " ".join(match.group(1).split())
        return title

    return "Municipal Ordinance"

# PUBLIC DEV-1 INTERFACE :
def get_parsed_docket(file_path: str) -> Dict:
    """
    Main Dev-1 parser interface.

    Returns:
        {
            "docket_id": ...,
            "title": ...,
            "address_mention": ...,
            "citations": [...],
            "raw_text": ...
        }
    """

    markdown_text = extract_pdf_markdown(file_path)

    cleaned_text = clean_text(markdown_text)

    return {
        "docket_id": extract_docket_id(cleaned_text),
        "title": extract_title(cleaned_text),
        "address_mention": extract_address(cleaned_text),
        "citations": extract_citations(cleaned_text),
        "raw_text": cleaned_text,
    }

# LOCAL TESTING :
if __name__ == "__main__":

    pdf_path = (
        "data/raw/"
        "20260910-039, Agenda Backup_ Draft Ordinance.PDF"
    )

    docket = get_parsed_docket(pdf_path)

    print("\n========== PARSED DOCKET ==========\n")

    print("DOCKET ID:")
    print(docket["docket_id"])

    print("\nTITLE:")
    print(docket["title"])

    print("\nADDRESS:")
    print(docket["address_mention"])

    print("\nCITATIONS:")
    for citation in docket["citations"]:
        print("-", citation)

    print("\nRAW TEXT PREVIEW:")
    print(docket["raw_text"][:3000])
from pathlib import Path

from dev1_pipeline.parser import get_parsed_docket
from dev1_pipeline.vectordb import get_baseline_statute


def process_local_docket(pdf_path: str) -> dict:
    """
    Complete Dev-1 pipeline.

    PDF
        ↓
    Docling parser
        ↓
    Structured docket
        ↓
    Baseline statute retrieval
    """

    pdf = Path(pdf_path)

    if not pdf.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf}"
        )

    # -----------------------------------------
    # Step 1: Parse municipal PDF
    # -----------------------------------------

    docket = get_parsed_docket(
        str(pdf)
    )

    # -----------------------------------------
    # Step 2: Retrieve baseline rules
    # -----------------------------------------

    baseline_statutes = {}

    for citation in docket.get(
        "citations",
        []
    ):
        baseline_statutes[citation] = (
            get_baseline_statute(citation)
        )

    # -----------------------------------------
    # Step 3: Return Dev-2 payload
    # -----------------------------------------

    return {
        "docket": docket,
        "baseline_statutes": baseline_statutes,
    }
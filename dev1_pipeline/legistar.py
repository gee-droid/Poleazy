import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


# ============================================================
# Configuration
# ============================================================

BASE_URL = "https://webapi.legistar.com/v1"

DEFAULT_CLIENT = "austin"


# ============================================================
# Client
# ============================================================

class LegistarClient:
    """
    Small client for the public Legistar Web API.

    Dev 1 responsibility:
        Legistar -> matter metadata -> attachments -> PDF
    """

    def __init__(
        self,
        client: str = DEFAULT_CLIENT,
        timeout: int = 30,
    ):
        self.client = client
        self.timeout = timeout

    # --------------------------------------------------------
    # HTTP helper
    # --------------------------------------------------------

    def _get(self, endpoint: str, params=None):
        url = f"{BASE_URL}/{self.client}/{endpoint}"

        response = requests.get(
            url,
            params=params,
            timeout=self.timeout,
        )

        if not response.ok:
            print("\n========== LEGISTAR API ERROR ==========")
            print("URL:", response.url)
            print("STATUS:", response.status_code)
            print("RESPONSE:", response.text[:2000])
            print("========================================\n")

        response.raise_for_status()

        return response

    # --------------------------------------------------------
    # Matters
    # --------------------------------------------------------

    def get_matters(
        self,
        top: int = 100,
        skip: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve one page of matters from Legistar.
        """

        response = self._get(
            "Matters",
            params={
                "$top": top,
                "$skip": skip,
            },
        )

        return response.json()

    # --------------------------------------------------------
    # Search matters
    # --------------------------------------------------------

    def search_matters(
        self,
        query: str,
    ) -> List[Dict[str, Any]]:
        """
        Search matters locally by title/name/file/notes.

        We retrieve the public matter list and perform
        case-insensitive matching locally.
        """

        query = query.lower().strip()

        matters = self.get_matters()

        matches = []

        for matter in matters:

            searchable = " ".join(
                str(matter.get(field, ""))
                for field in [
                    "MatterFile",
                    "MatterName",
                    "MatterTitle",
                    "MatterNotes",
                    "MatterRequester",
                ]
            ).lower()

            if query in searchable:
                matches.append(matter)

        return matches

    # --------------------------------------------------------
    # Single matter
    # --------------------------------------------------------

    def get_matters(
            self,
            top: int = 100,
            skip: int = 0,
        ) -> List[Dict[str, Any]]:
            """
            Retrieve a manageable page of matters from Legistar.

            Legistar recommends ODATA pagination instead of requesting
            the entire matter database at once.
            """

            response = self._get(
                "Matters",
                params={
                    "$top": top,
                    "$skip": skip,
                },
            )

            return response.json()

    # --------------------------------------------------------
    # Attachments
    # --------------------------------------------------------

    def get_attachments(
        self,
        matter_id: int,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve public attachments for a matter.
        """

        response = self._get(
            f"Matters/{matter_id}/Attachments"
        )

        return response.json()

    # --------------------------------------------------------
    # Choose PDF attachment
    # --------------------------------------------------------

    def choose_pdf_attachment(
        self,
        attachments: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        Choose the most likely PDF attachment.

        Preference:
        1. filenames containing ordinance
        2. filenames containing backup
        3. filenames containing agenda
        4. any PDF
        """

        pdfs = []

        for attachment in attachments:

            filename = str(
                attachment.get(
                    "MatterAttachmentFileName",
                    "",
                )
            )

            name = str(
                attachment.get(
                    "MatterAttachmentName",
                    "",
                )
            )

            combined = (
                f"{filename} {name}"
            ).lower()

            is_pdf = (
                filename.lower().endswith(".pdf")
                or ".pdf" in combined
            )

            if is_pdf:
                pdfs.append(
                    (
                        combined,
                        attachment,
                    )
                )

        if not pdfs:
            return None

        priority_words = [
            "ordinance",
            "backup",
            "agenda",
        ]

        for word in priority_words:
            for combined, attachment in pdfs:
                if word in combined:
                    return attachment

        return pdfs[0][1]

    # --------------------------------------------------------
    # Download attachment
    # --------------------------------------------------------

    def download_attachment(
        self,
        matter_id: int,
        attachment_id: int,
        output_path: str,
    ) -> Path:
        """
        Download an attachment file from Legistar.
        """

        response = self._get(
            f"Matters/{matter_id}/Attachments/"
            f"{attachment_id}/File"
        )

        path = Path(output_path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_bytes(
            response.content
        )

        return path

    # --------------------------------------------------------
    # Search + download convenience method
    # --------------------------------------------------------

    def download_matching_pdf(
        self,
        query: str,
        output_dir: str = "data/raw",
    ) -> Optional[Path]:
        """
        Search for a matter, choose its best PDF attachment,
        and download it.

        Returns:
            Path to downloaded PDF
            or None if nothing was found.
        """

        matches = self.search_matters(query)

        if not matches:
            print(
                f"[INFO] No Legistar matter found for: {query}"
            )

            return None

        print(
            f"[INFO] Found {len(matches)} matching matter(s)."
        )

        matter = matches[0]

        matter_id = matter.get(
            "MatterId"
        )

        print(
            f"[INFO] Selected matter: "
            f"{matter.get('MatterTitle')}"
        )

        attachments = self.get_attachments(
            matter_id
        )

        attachment = self.choose_pdf_attachment(
            attachments
        )

        if attachment is None:
            print(
                "[INFO] No PDF attachment found."
            )

            return None

        attachment_id = attachment.get(
            "MatterAttachmentId"
        )

        filename = attachment.get(
            "MatterAttachmentFileName"
        )

        if not filename:
            filename = (
                f"matter_{matter_id}_"
                f"attachment_{attachment_id}.pdf"
            )

        output_path = (
            Path(output_dir) / filename
        )

        print(
            f"[INFO] Downloading: {filename}"
        )

        return self.download_attachment(
            matter_id=matter_id,
            attachment_id=attachment_id,
            output_path=str(output_path),
        )


# ============================================================
# Test
# ============================================================

if __name__ == "__main__":
    print(
        "Legistar client module loaded successfully."
    )
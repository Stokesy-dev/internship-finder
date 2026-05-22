from __future__ import annotations

import re
from pathlib import Path

from .models import ResumeProfile
from .text_utils import clean_text, extract_known_skills, split_bullets, unique_preserve_order


class ResumeParser:
    def parse_pdf(self, pdf_path: str | Path) -> ResumeProfile:
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"Resume not found: {path}")
        text = self._extract_pdf_text(path)
        return self.parse_text(text)

    def parse_text(self, text: str) -> ResumeProfile:
        normalized = clean_text(text)
        return ResumeProfile(
            raw_text=normalized,
            skills=extract_known_skills(normalized),
            projects=self._section_items(text, ["projects", "project experience"]),
            experience=self._section_items(text, ["experience", "work experience", "internships"]),
            education=self._section_items(text, ["education", "academic"]),
        )

    def _extract_pdf_text(self, path: Path) -> str:
        try:
            import fitz

            with fitz.open(path) as doc:
                return "\n".join(page.get_text() for page in doc)
        except ImportError:
            pass

        try:
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError as exc:
            raise RuntimeError("Install pymupdf or pypdf to parse PDF resumes.") from exc

    @staticmethod
    def _section_items(text: str, section_names: list[str]) -> list[str]:
        lines = [line.strip() for line in text.splitlines()]
        starts = [
            index
            for index, line in enumerate(lines)
            if any(re.fullmatch(name, line.lower().strip(":")) for name in section_names)
        ]
        if not starts:
            return []
        start = starts[0] + 1
        end = len(lines)
        for index in range(start, len(lines)):
            if re.fullmatch(r"[A-Z][A-Z &/+-]{2,}:?", lines[index]):
                end = index
                break
        return unique_preserve_order(split_bullets("\n".join(lines[start:end]), max_items=10))

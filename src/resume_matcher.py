from __future__ import annotations

from .models import JDProfile, MatchResult, ResumeProfile
from .text_utils import normalize_key


class ResumeMatcher:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", use_sentence_transformers: bool = True) -> None:
        self.model_name = model_name
        self.use_sentence_transformers = use_sentence_transformers
        self._model = None

    def match(self, resume: ResumeProfile, jd: JDProfile) -> MatchResult:
        resume_skills = {normalize_key(skill): skill for skill in resume.skills}
        required = jd.all_skills
        matching = [skill for skill in required if normalize_key(skill) in resume_skills]
        missing = [skill for skill in required if normalize_key(skill) not in resume_skills]
        skill_coverage = len(matching) / max(len(required), 1)
        semantic = self._semantic_similarity(resume.raw_text, _jd_text(jd))
        fit_score = round((0.6 * skill_coverage + 0.4 * semantic) * 100, 2)
        confidence = round(min(0.95, 0.55 + 0.25 * bool(required) + 0.2 * bool(resume.raw_text)), 2)
        return MatchResult(
            fit_score=fit_score,
            confidence_score=confidence,
            matching_skills=matching,
            missing_skills=missing,
            semantic_similarity=round(semantic, 4),
        )

    def _semantic_similarity(self, resume_text: str, jd_text: str) -> float:
        if not resume_text or not jd_text:
            return 0.0
        if not self.use_sentence_transformers:
            return _token_jaccard(resume_text, jd_text)
        try:
            from sentence_transformers import SentenceTransformer, util

            if self._model is None:
                self._model = SentenceTransformer(self.model_name)
            embeddings = self._model.encode([resume_text[:4000], jd_text[:4000]], convert_to_tensor=True)
            return float(util.cos_sim(embeddings[0], embeddings[1]).item())
        except Exception:
            return _token_jaccard(resume_text, jd_text)


def _jd_text(jd: JDProfile) -> str:
    return " ".join(
        [
            jd.role_title,
            " ".join(jd.required_skills),
            " ".join(jd.preferred_skills),
            " ".join(jd.tools),
            " ".join(jd.responsibilities),
        ]
    )


def _token_jaccard(left: str, right: str) -> float:
    left_tokens = {token.lower() for token in left.split() if len(token) > 2}
    right_tokens = {token.lower() for token in right.split() if len(token) > 2}
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)

from __future__ import annotations

import re


ROLE_KEYWORDS = [
    "ai",
    "artificial intelligence",
    "machine learning",
    "ml",
    "data science",
    "data scientist",
    "software engineer",
    "software engineering",
    "backend",
    "python developer",
]

COMMON_SKILLS = [
    "Python",
    "Java",
    "C++",
    "JavaScript",
    "TypeScript",
    "SQL",
    "PostgreSQL",
    "MongoDB",
    "Redis",
    "FastAPI",
    "Django",
    "Flask",
    "React",
    "Node.js",
    "Docker",
    "Kubernetes",
    "AWS",
    "GCP",
    "Azure",
    "Git",
    "Linux",
    "REST",
    "GraphQL",
    "Pandas",
    "NumPy",
    "scikit-learn",
    "TensorFlow",
    "PyTorch",
    "LangChain",
    "LLM",
    "RAG",
    "NLP",
    "Computer Vision",
    "MLOps",
    "CI/CD",
    "Airflow",
    "Spark",
    "Kafka",
    "Vector DB",
    "ChromaDB",
]


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9+#.]+", "", value.lower())


def unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = clean_text(value)
        key = normalize_key(cleaned)
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


def extract_known_skills(text: str) -> list[str]:
    lowered = f" {text.lower()} "
    matches: list[str] = []
    for skill in COMMON_SKILLS:
        pattern = r"(?<![a-z0-9+#.])" + re.escape(skill.lower()) + r"(?![a-z0-9+#.])"
        if re.search(pattern, lowered):
            matches.append(skill)
    return unique_preserve_order(matches)


def split_bullets(text: str, max_items: int = 8) -> list[str]:
    pieces = re.split(r"(?:\n|•|- |\* |\d+\.)", text)
    return unique_preserve_order([piece.strip(" :-") for piece in pieces if len(piece.strip()) > 8])[
        :max_items
    ]


def parse_money_inr(text: str) -> int:
    lowered = text.lower().replace(",", "")
    monthly = re.findall(r"(?:inr|rs\.?|₹)?\s*(\d+(?:\.\d+)?)\s*(lpa|lakh|k|thousand)?", lowered)
    best = 0
    for amount, unit in monthly:
        value = float(amount)
        if unit in {"lpa", "lakh"}:
            value = value * 100000 / 12
        elif unit in {"k", "thousand"}:
            value = value * 1000
        if 1000 <= value <= 500000:
            best = max(best, int(value))
    return best


def parse_duration_months(text: str) -> int:
    lowered = text.lower()
    matches = re.findall(r"(\d+)\s*(?:\+?\s*)?(months?|mos?|month internship)", lowered)
    values = [int(value) for value, _ in matches]
    if "6 month" in lowered or "six month" in lowered:
        values.append(6)
    return max(values) if values else 0


def has_role_match(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in ROLE_KEYWORDS)


def is_remote_or_india(location: str, description: str) -> bool:
    haystack = f"{location} {description}".lower()
    india_terms = ["india", "bengaluru", "bangalore", "mumbai", "pune", "delhi", "gurugram", "hyderabad", "chennai", "noida"]
    return "remote" in haystack or any(term in haystack for term in india_terms)

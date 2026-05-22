from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.company_research import CompanyResearcher
from src.jd_parser import JDParser
from src.models import Internship
from src.ollama_router import DEFAULT_FAST_MODEL, DEFAULT_LARGE_MODEL, OllamaRouter
from src.pipeline import InternshipIntelligenceAgent
from src.config import AgentSettings


def test_router_default_models() -> None:
    router = OllamaRouter.from_settings()
    assert router.fast.model == DEFAULT_FAST_MODEL
    assert router.large.model == DEFAULT_LARGE_MODEL
    assert router.fast.model != router.large.model


def test_router_respects_custom_models() -> None:
    router = OllamaRouter.from_settings(
        fast_model="fast-test",
        large_model="large-test",
        base_url="http://ollama.test:11434",
    )
    assert router.fast.model == "fast-test"
    assert router.large.model == "large-test"
    assert router.fast.base_url == "http://ollama.test:11434"


def _mock_post_response() -> MagicMock:
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "response": (
            '{"required_skills":["Python"],"preferred_skills":[],"tools":[],"'
            '"responsibilities":[],"experience_expectations":[]}'
        )
    }
    return response


@patch("src.ollama_client.requests.post")
def test_jd_parser_calls_fast_model(mock_post: MagicMock) -> None:
    mock_post.return_value = _mock_post_response()
    router = OllamaRouter.from_settings(fast_model="qwen2.5:3b", large_model="qwen2.5:7b")
    JDParser(llm=router.fast, use_llm=True).parse(
        "Machine Learning Intern",
        "Python machine learning intern remote India TensorFlow",
    )
    assert mock_post.call_args.kwargs["json"]["model"] == "qwen2.5:3b"


@patch("src.ollama_client.requests.post")
def test_company_researcher_calls_large_model(mock_post: MagicMock) -> None:
    mock_post.return_value = _mock_post_response()
    mock_post.return_value.json.return_value = {
        "response": (
            '{"overview":"AI startup","products":[],"competitors":[],"'
            '"growth_indicators":[],"hiring_signals":[],"quality_score":60}'
        )
    }
    router = OllamaRouter.from_settings(fast_model="qwen2.5:3b", large_model="qwen2.5:7b")
    internship = Internship(
        title="ML Intern",
        company="Test Labs",
        description="machine learning intern Python India remote",
        location="Remote India",
        apply_url="https://example.com/job",
        source="test",
    )
    CompanyResearcher(llm=router.large, use_llm=True).research(internship)
    assert mock_post.call_args.kwargs["json"]["model"] == "qwen2.5:7b"


@patch("src.ollama_client.requests.post")
def test_no_llm_skips_ollama_http(mock_post: MagicMock) -> None:
    router = OllamaRouter.from_settings()
    JDParser(llm=router.fast, use_llm=False).parse("ML Intern", "Python ML India")
    CompanyResearcher(llm=router.large, use_llm=False).research(
        Internship(
            title="ML Intern",
            company="Co",
            description="machine learning Python India",
            location="India",
            source="test",
        )
    )
    mock_post.assert_not_called()


def test_pipeline_wires_fast_and_large_clients() -> None:
    from pathlib import Path

    settings = AgentSettings(
        resume_path=Path("tests/fixtures/resume.pdf"),
        ollama_fast_model="fast-x",
        ollama_large_model="large-y",
        use_llm=True,
    )
    agent = InternshipIntelligenceAgent(settings)
    assert agent.jd_parser.llm.model == "fast-x"
    assert agent.company_researcher.llm.model == "large-y"


@patch("src.ollama_client.requests.post")
def test_discover_pipeline_enriches_with_llm(mock_post: MagicMock, tmp_path: Path) -> None:
    from pathlib import Path

    responses = [
        {
            "response": (
                '{"required_skills":["Python"],"preferred_skills":[],"tools":[],"'
                '"responsibilities":[],"experience_expectations":[]}'
            )
        },
        {
            "response": (
                '{"overview":"Fixture Labs","products":[],"competitors":[],"'
                '"growth_indicators":["hiring"],"hiring_signals":[],"quality_score":70}'
            )
        },
    ]
    mock_post.side_effect = [
        MagicMock(raise_for_status=MagicMock(), json=MagicMock(return_value=payload))
        for payload in responses
    ] * 10

    settings = AgentSettings(
        resume_path=Path(__file__).parent / "fixtures" / "resume.pdf",
        jobs_csv=Path(__file__).parent / "fixtures" / "internships.csv",
        filter_mode="lenient",
        reports_dir=tmp_path / "reports",
        top_k=2,
        use_llm=True,
        use_embeddings=False,
        ollama_fast_model="qwen2.5:3b",
        ollama_large_model="qwen2.5:7b",
    )
    result = InternshipIntelligenceAgent(settings).run()
    assert result.ranked
    assert result.ranked[0].jd.required_skills
    assert mock_post.call_args_list[0].kwargs["json"]["model"] == "qwen2.5:3b"
    models_used = {call.kwargs["json"]["model"] for call in mock_post.call_args_list}
    assert "qwen2.5:7b" in models_used

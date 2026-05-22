"""Thin Streamlit viewer for internship intelligence reports.

Run from repo root:

    streamlit run streamlit_app.py
"""

from __future__ import annotations

from pathlib import Path

from src.viewer import (
    DEFAULT_REPORTS_DIR,
    DEFAULT_UPLOADS_DIR,
    REPORT_FILES,
    build_agent_argv,
    default_resume_path,
    find_resume_pdfs,
    load_reports,
    run_agent,
)

# Streamlit is imported inside main() so unit tests can import src.viewer without it.


def main() -> None:
    import streamlit as st

    st.set_page_config(
        page_title="Internship Intelligence",
        page_icon="📋",
        layout="wide",
    )
    st.title("Internship Intelligence Agent")
    st.caption("Browse markdown reports and trigger discover or shortlist runs.")

    reports_dir = Path(
        st.sidebar.text_input("Reports directory", value=str(DEFAULT_REPORTS_DIR))
    ).expanduser()
    uploads_dir = Path(
        st.sidebar.text_input("Uploads directory (resumes)", value=str(DEFAULT_UPLOADS_DIR))
    ).expanduser()

    st.sidebar.markdown("### Reports")
    reports = load_reports(reports_dir)
    for key, filename in REPORT_FILES.items():
        path, _ = reports[key]
        st.sidebar.write(f"{'✅' if path else '—'} `{filename}`")

    st.header("Run agent")
    pdfs = find_resume_pdfs(uploads_dir)
    default_resume = default_resume_path(uploads_dir)

    col1, col2 = st.columns(2)
    with col1:
        command = st.selectbox(
            "Command",
            options=["discover", "shortlist"],
            help="discover = lenient exploration; shortlist = strict apply-ready",
        )
    with col2:
        if pdfs:
            resume_choice = st.selectbox(
                "Resume (from uploads/)",
                options=[str(p) for p in pdfs],
                index=0 if default_resume else 0,
            )
            resume_path = Path(resume_choice)
        else:
            st.warning(f"No PDFs in `{uploads_dir}`. Enter a path below.")
            resume_path = Path(
                st.text_input(
                    "Resume path",
                    value=str(default_resume) if default_resume else "",
                    placeholder="uploads/resume.pdf",
                )
            )

    role_query = st.text_input("Role query (optional)", placeholder="machine learning intern")
    jobs_csv = st.text_input(
        "Jobs CSV (optional)",
        placeholder="tests/fixtures/internships.csv",
        help="Use a CSV to rank without live scraping.",
    )
    fast_run = st.checkbox(
        "Fast run (--no-llm --no-embeddings)",
        value=False,
        help="Skip Ollama and embeddings for quicker UI smoke tests.",
    )

    if st.button("Run", type="primary"):
        try:
            argv = build_agent_argv(
                command,
                resume_path,
                role_query=role_query,
                reports_dir=reports_dir,
                jobs_csv=Path(jobs_csv) if jobs_csv.strip() else None,
                no_llm=fast_run,
                no_embeddings=fast_run,
            )
        except (FileNotFoundError, ValueError) as exc:
            st.error(str(exc))
        else:
            with st.spinner(f"Running: {' '.join(argv[2:])}"):
                result = run_agent(argv)
            if result.returncode == 0:
                st.success("Run finished successfully.")
                if result.stdout.strip():
                    st.code(result.stdout.strip(), language=None)
                st.rerun()
            else:
                st.error(f"Run failed (exit code {result.returncode}).")
                detail = (result.stderr or result.stdout or "No output captured.").strip()
                st.code(detail, language=None)
                st.markdown(
                    "**Tips:** Check that the resume path exists, Ollama is running "
                    "(unless fast run is enabled), and dependencies are installed."
                )

    st.header("Reports")
    reports = load_reports(reports_dir)
    tabs = st.tabs([key.replace("_", " ").title() for key in REPORT_FILES])
    for tab, (key, _filename) in zip(tabs, REPORT_FILES.items(), strict=True):
        path, content = reports[key]
        with tab:
            if path and content.strip():
                st.markdown(content)
            elif path:
                st.info(f"`{path.name}` exists but is empty.")
            else:
                st.info(
                    f"No report yet. Run **{key.replace('_', ' ')}** via discover or shortlist."
                )


if __name__ == "__main__":
    main()

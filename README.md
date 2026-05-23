# AI Internship Intelligence Agent

A local-first, Ollama-powered autonomous agent that discovers, filters, matches, and provides coaching for AI/ML, Data Science, and Software Engineering internships. Designed specifically for students and early-career engineers targeting roles in India and remote-friendly positions.

## 🚀 Features

- **Hybrid Discovery:** Scrapes job boards (Greenhouse, Lever, Wellfound, Internshala, company career pages) and falls back to a raw cache when live sources are empty.
- **Configurable Seeds:** Pass specific board slugs or manual URLs via `seeds.txt` for targeted discovery.
- **Two-Tier Filtering:** 
  - *Lenient mode:* Keeps listings with missing stipend/duration info for exploration.
  - *Strict mode:* Rejects listings below your thresholds (ideal for shortlisting).
- **Resume Matching:** Compares your PDF resume to job requirements using a blend of skill overlap and semantic similarity (via `sentence-transformers`).
- **Local LLM Enrichment:** Uses dual Ollama models (fast `qwen2.5:3b` for JD parsing, large `qwen2.5:7b` for deep company research and rich coaching). No cloud LLM dependencies!
- **Markdown Reports & UI:** Generates top internships, skill gaps, roadmaps, interview prep, and application strategies. View them easily via a lightweight Streamlit interface.

## 🛠️ Prerequisites

1. Python 3.10+
2. [Ollama](https://ollama.ai/) installed locally
3. Required Ollama models downloaded:
   ```bash
   ollama run qwen2.5:3b
   ollama run qwen2.5:7b
   ```

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Stokesy-dev/internship-finder.git
   cd internship-finder
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Ensure you have your resume in PDF format (e.g., placed at `uploads/resume.pdf`).

## 💻 Usage

### 1. CLI Commands

The CLI exposes two primary profiles: `discover` and `shortlist`.

**Weekly Exploration (`discover`)**
Broad search with lenient filters to maximize visibility.
```bash
python src/main.py discover --resume uploads/resume.pdf
```

**Apply-Ready Shortlist (`shortlist`)**
Strict filtering requiring known stipends/durations and generating rich LLM coaching reports.
```bash
python src/main.py shortlist --resume uploads/resume.pdf
```

**Common Overrides:**
- `--lenient` / `--no-lenient` to toggle filter mode manually.
- `--seed-file <path>` to provide custom search domains (defaults to `seeds.txt`).
- `--top-k 5` to limit the number of detailed reports generated.
- `--no-llm` and `--no-embeddings` for faster heuristic-only execution.

### 2. Streamlit Viewer

Launch the thin UI to browse generated markdown reports and trigger new runs:

```bash
streamlit run streamlit_app.py
```
Open your browser at `http://localhost:8501`.

## ⚙️ Configuration (Seeds)

Create or edit `seeds.txt` in the root directory to define target boards and URLs.

```text
# seeds.txt format examples:
greenhouse:razorpay
lever:postman
https://careers.google.com/jobs/results/?q=intern
```

## 🧪 Testing

Run the test suite using pytest:
```bash
python -m pytest tests/
```

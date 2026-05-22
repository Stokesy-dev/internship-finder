You are a senior AI engineer building a production-quality AI Internship Opportunity Intelligence Agent.

Objective:
Build an autonomous internship discovery and ranking platform.

Target user constraints:
- internship duration >= 6 months
- stipend >= 20000 INR
- PPO potential required
- target domains:
  AI
  Data Science
  Machine Learning
  Software Engineering
  Backend Engineering

Core Features:

1. Internship discovery
- fetch internships from public sources
- support:
  LinkedIn
  Indeed
  Wellfound
  Naukri
  Internshala where accessible
  public company career pages

2. Filtering
Filter by:
- stipend
- duration
- location
- role keywords
- remote eligibility

3. Job description parsing
Extract:
- role title
- required skills
- preferred skills
- tools
- experience
- responsibilities

4. Resume matching
Accept PDF resume.
Extract:
- skills
- projects
- experience
Compare against internship requirements.
Generate:
- fit score
- missing skills
- strengths

5. PPO predictor
Estimate PPO probability using signals:
- duration >= 6 months
- mentions of full-time conversion
- mentions of PPO
- recurring hiring
- growth-stage company
- startup expansion indicators

Output PPO score.

6. Company research
Fetch:
- company overview
- products
- competitors
- growth indicators
- hiring signals

7. Interview prep
Generate:
- technical questions
- behavioral questions
- role-specific prep

8. Learning roadmap
Generate upskilling plan based on missing skills.

9. Ranking engine
Rank opportunities using:
- stipend
- PPO score
- resume fit
- company growth potential

10. Report generation
Generate markdown reports.

Technology requirements:
- Python
- Gemini API
- sentence-transformers
- ChromaDB
- BeautifulSoup
- requests
- pandas
- python-jobspy
- pypdf
- pymupdf
- streamlit ready

Architecture:
clean modular production code

Folders:
src/
data/
reports/
uploads/
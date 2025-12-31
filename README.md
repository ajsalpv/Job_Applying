# AI Job Application Agent

An AI-powered job application assistant that helps discover, evaluate, and apply to relevant jobs.

## 🎯 Features

- **Job Discovery**: Scrape jobs from LinkedIn, Indeed, Naukri, and company career pages
- **Smart Scoring**: AI-powered job fit scoring based on skills, experience, and preferences
- **Resume & Cover Letter**: Generate ATS-optimized content per job
- **Application Assistant**: Human-in-the-loop application workflow (no auto-submit)
- **Tracking**: Monitor application status in Google Sheets

## 🛠️ Tech Stack

- **Backend**: FastAPI + Python
- **AI/Agents**: LangChain + LangGraph + Groq
- **UI**: Streamlit
- **Browser Automation**: Playwright
- **Database**: Google Sheets

## 📁 Project Structure

```
app/
├── main.py                 # FastAPI entry point
├── config/                 # Settings, prompts, constants
├── orchestrator/           # LangGraph workflow
├── agents/                 # All AI agents
├── tools/                  # LLM, browser, sheets utilities
├── api/                    # FastAPI routes
├── ui/                     # Streamlit dashboard
└── tests/                  # Unit tests
```

## 🚀 Quick Start

```bash
# Activate virtual environment
.\job_applying_agent\Scripts\activate

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Install Playwright browsers
playwright install chromium

# Run FastAPI backend
uvicorn app.main:app --reload

# Run Streamlit UI (in another terminal)
streamlit run app/ui/streamlit_app.py
```

## ⚙️ Configuration

Create `.env` file with:
```
GROQ_API_KEY=your_groq_api_key
GOOGLE_SHEETS_CREDENTIALS_PATH=path/to/credentials.json
GOOGLE_SHEET_ID=your_sheet_id
```

## 👤 User Profile

This agent is configured for:
- **Role**: AI/ML Engineer
- **Experience**: 1 year
- **Skills**: LLM, LangChain, RAG, Python, FastAPI, TensorFlow
- **Location**: Bangalore, India / Remote

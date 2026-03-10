# Google ADK Agent - Learning Track 🤖

This directory contains experimental agents built using the Google Gen AI SDK (ADK). The ADK is a bare-metal, lightweight framework used for building conversational agents with native function calling.

## Prerequisites

- Python 3.10+
- [UV](https://github.com/astral-sh/uv) (An extremely fast Python package and environment manager written in Rust)

## Project Setup Instructions

### Option 1: Automated Setup Scripts

We have provided automated scripts that will install UV, create the virtual environment, and install dependencies for you.

**Windows:**

```powershell
.\scripts\setup_adk.ps1
```

**macOS / Linux:**

```bash
chmod +x scripts/setup_adk.sh
./scripts/setup_adk.sh
```

### Option 2: Manual Setup

1. **Install UV (if not installed)**

   ```powershell
   # On Windows (PowerShell)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   ```bash
   # On macOS/Linux (Bash)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Create a Virtual Environment using UV**

   ```powershell
   uv venv
   ```

3. **Activate the Virtual Environment**

   ```powershell
   # Windows
   .venv\Scripts\activate
   ```

   ```bash
   # macOS / Linux
   source .venv/bin/activate
   ```

4. **Install ADK Dependencies**
   We have separated the dependencies to keep the ADK environment clean and lightweight.

   ```powershell
   uv pip install -r requirements/adk.txt
   ```

5. **Set up Environment Variables**
   Ensure your `.env` file exists in the root directory and contains:

   ```env
   # Infrastructure Settings
   GOOGLE_GENAI_USE_VERTEXAI=true
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_CLOUD_LOCATION=us-central1
   GOOGLE_APPLICATION_CREDENTIALS=your-service-account-key.json

   # API Keys (AI Studio fallback)
   GEMINI_API_KEY=your-gemini-api-key

   # Model Settings
   MODEL=gemini-2.5-flash

   # Observability (LangSmith)
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY=your-langsmith-api-key
   LANGCHAIN_PROJECT=ADK-Learning-Journey
   ```

## Running the Agents

We provide multiple interfaces for testing and running the ADK agents.

| Interface Type                              | Start Command                                          | Description                                                           | Stop Command |
| :------------------------------------------ | :----------------------------------------------------- | :-------------------------------------------------------------------- | :----------- |
| **Streamlit Dashboard** <br>_(Recommended)_ | `uv run --env-file .env streamlit run adk_app.py`      | Modern chat dashboard testing all 10+ ADK learning levels natively.   | `Ctrl + C`   |
| **FastAPI Backend**                         | `uv run --env-file .env uvicorn main:app --reload`     | Production REST API server for the root agent.                        | `Ctrl + C`   |
| **Native ADK UI** <br>_(Web Interface)_     | `uv run --env-file .env adk web adk_labs`              | Google's built-in React UI for testing basic agents.                  | `Ctrl + C`   |
| **Level 11: MCP**                           | `uv run --env-file .env streamlit run adk_app.py`      | Model Context Protocol integration for dynamic tool discovery.        | `Ctrl + C`   |
| **Level 12: HITL**                          | `uv run --env-file .env adk adk_labs/adk_level12_hitl` | Native terminal mode (required for `input()` commands like Level 12). | Type `exit`  |

## Pushing to GitHub

1. Ensure the `.gitignore` file is present in the root (it prevents `.env` and `.venv` from being uploaded).
2. Initialize and push:

```powershell
git init
git add .
git commit -m "Initial ADK and Langchain agents commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

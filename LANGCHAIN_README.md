# LangChain & LangGraph Learning Track 🦜🕸️

This directory contains the 13-Level learning journey moving from basic LangChain LCEL up to advanced LangGraph state machines, demonstrating production level React Agents, Memory, RAG, and Time Travel.

## Prerequisites

- Python 3.10+
- [UV](https://github.com/astral-sh/uv) (An extremely fast Python package and environment manager written in Rust)

## Project Setup Instructions

### Option 1: Automated Setup Scripts

We have provided automated scripts that will install UV, create the virtual environment, and install dependencies for you.

**Windows:**

```powershell
.\setup_langchain.ps1
```

**macOS / Linux:**

```bash
chmod +x setup_langchain.sh
./setup_langchain.sh
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

4. **Install LangChain Dependencies**
   We have separated these dependencies because LangChain requires significantly more heavy packages (Pydantic, LangSmith, SQL, etc.) than the base ADK.

   ```powershell
   uv pip install -r lc_requirements.txt
   ```

5. **Set up Environment Variables**
   Ensure your `.env` file exists in the root directory and contains your Google keys AND LangSmith tracing configurations.

   ```env
   # API Keys
   GEMINI_API_KEY=your_key_here
   MODEL=gemini-2.5-flash

   # LangSmith Observability
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY=your_langsmith_key
   LANGCHAIN_PROJECT=ADK-Learning-Journey
   ```

## Running the Application

### Streamlit UI

All 13 LangChain/LangGraph levels have been integrated into a beautiful, interactive Streamlit frontend.
**To Start:**

```powershell
uv run streamlit run lc_app.py
# This launches the application on http://localhost:8501
```

**To Stop:**
Press `Ctrl + C` in the terminal where it is running.

## Pushing to GitHub

1. Ensure the `.gitignore` file is present in the root (it strictly prevents your `.env` and `.venv` from leaking api keys).
2. Initialize and push:

```powershell
git init
git add .
git commit -m "Initial ADK and Langchain agents commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

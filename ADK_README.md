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
.\setup_adk.ps1
```

**macOS / Linux:**

```bash
chmod +x setup_adk.sh
./setup_adk.sh
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
   uv pip install -r adk_requirements.txt
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

### Native Base ADK UI (Web Interface)

The ADK team provides a built-in React UI for testing basic agents.
**To Start:**

```powershell
uv run --env-file .env adk web
# This launches the server. Open the URL provided in the console (usually http://localhost:8080 or 8081).
```

**To Stop:**
Press `Ctrl + C` in the terminal where it is running.

### ADK CLI Mode (For Human-in-the-Loop tests)

Because Python `input()` hangs a web server, agents like our `adk_level12_hitl` must be tested in the CLI.
**To Start:**

```powershell
uv run --env-file .env adk adk_level12_hitl
```

**To Stop:**
Type `exit` in the chat, or press `Ctrl + C`.

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

# Google ADK Sample Agent with FastAPI

This is a simple server that implements an AI Agent using the [Google Agent Development Kit (ADK)](https://pypi.org/project/google-adk/) and serves it via a [FastAPI](https://fastapi.tiangolo.com/) endpoint. It uses Google Vertex AI (`gemini-1.5-flash`) as the provider.

## Prerequisites

1.  Python 3.10+ installed.
2.  `uv` package manager installed (`powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`).
3.  Google Cloud project with Vertex AI API enabled.
4.  Google Cloud SDK (`gcloud` CLI) installed.

## Setup Instructions

1.  **Authenticate with Google Cloud:**
    This uses Application Default Credentials (ADC). Make sure you run this if you haven't yet:

    ```bash
    gcloud auth application-default login
    ```

    Alternatively, set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable pointing to your service account JSON file.

2.  **Set the current Project ID:**
    Ensure your default project is correct or export it. In powershell:

    ```powershell
    $env:GOOGLE_CLOUD_PROJECT="<your-google-cloud-project-id>"
    ```

3.  **Install the dependencies:**
    Since this project is managed by `uv`, just run:
    ```bash
    uv sync
    ```
    Or manually install from requirements:
    ```bash
    uv pip install -r requirements.txt
    ```

## Running the Server

Run the FastAPI Uvicorn server:

```bash
uv run --env-file .env uvicorn main:app --reload
```

or

```bash
python -m uvicorn main:app --reload
```

You should see output indicating that the server is running on `http://127.0.0.1:8000`.

## Testing the API

1.  **Health Check:**
    To ensure the server is running and the agent initialized, navigate to:

    ```
    http://127.0.0.1:8000/health
    ```

2.  **Interactive Docs (Swagger UI):**
    FastAPI provides automatic interactive documentation. Navigate to:

    ```
    http://127.0.0.1:8000/docs
    ```

    Here you can try out the `/chat` POST endpoint directly in your browser.

3.  **Using cURL:**
    You can also test the endpoint using `curl` from your terminal or command prompt:
    ```bash
    curl -X 'POST' \
      'http://127.0.0.1:8000/chat' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
      "query": "What is the Agent Development Kit by Google?"
    }'
    ```

#!/bin/bash
# Bash Setup Script for LangChain (macOS / Linux)

echo "=============================================="
echo " Setting up Virtual Environment (LangChain)..."
echo "=============================================="

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo -e "\033[1;33mUV is not installed. Installing UV via astral...\033[0m"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.local/bin/env
else
    echo -e "\033[1;32mUV is already installed.\033[0m"
fi

# Create venv
if [ ! -d ".venv" ]; then
    echo "Creating Virtual Environment (.venv)..."
    uv venv
fi

echo -e "\n========================================"
echo " Installing LangChain Dependencies..."
echo "========================================"
uv pip install -r lc_requirements.txt

echo -e "\n\033[1;36m========================================================\033[0m"
echo -e "\033[1;36m            LANGCHAIN SETUP COMPLETE (macOS/Linux)      \033[0m"
echo -e "\033[1;36m========================================================\033[0m\n"
echo -e "\033[1;33mTo activate the environment, run:\033[0m"
echo -e "source .venv/bin/activate\n"
echo -e "\033[1;33mTo run the Streamlit UX:\033[0m"
echo -e "uv run streamlit run lc_app.py\n"

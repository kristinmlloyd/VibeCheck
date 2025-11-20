# Installation Guide

## System Requirements

- **Operating System**: macOS, Linux, or Windows
- **Python**: Version 3.10 or higher
- **Memory**: At least 4GB RAM recommended
- **Storage**: At least 1GB free space for images and data

## Step-by-Step Installation

### 1. Install Python

If you don't have Python 3.10+:

**macOS (using Homebrew):**
```bash
brew install python@3.11
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.11
```

**Windows:**
Download from [python.org](https://www.python.org/downloads/)

### 2. Install Poetry
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Add Poetry to your PATH (follow the instructions after installation).

### 3. Clone and Install VibeCheck
```bash
# Clone repository
git clone https://github.com/kristinmlloyd/VibeCheck.git
cd VibeCheck

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### 4. Verify Installation
```bash
# Run tests
poetry run pytest

# Check linting
poetry run ruff check src/
```

## Troubleshooting

### Poetry not found
Make sure Poetry is in your PATH:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Python version mismatch
Ensure you're using Python 3.10+:
```bash
python --version
```

### Dependency conflicts
Try clearing the cache:
```bash
poetry cache clear pypi --all
poetry install
```

## Optional: Development Setup

For contributors:
```bash
# Install pre-commit hooks
poetry run pre-commit install

# Install all development dependencies
poetry install --with dev
```

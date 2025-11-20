# Getting Started

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.10 or higher
- Poetry (Python package manager)
- Git

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/kristinmlloyd/VibeCheck.git
cd VibeCheck
```

### 2. Install Dependencies
```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install
```

### 3. Set Up Environment Variables

Create a `.env` file in the project root:
```bash
SERPAPI_KEY=your_serpapi_key_here
```

### 4. Run Tests

Verify your installation:
```bash
poetry run pytest tests/
```

## Next Steps

- Read the [Quick Start Guide](quick-start.md) to start using VibeCheck
- Explore the [API Reference](../reference/) for detailed code documentation
- Check out [Contributing Guidelines](../contributing.md) to contribute to the project

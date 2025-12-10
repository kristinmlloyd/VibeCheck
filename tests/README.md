# VibeCheck Test Suite

## Quick Start

```bash
# Create and activate virtual environment
python3 -m venv test_env
source test_env/bin/activate

# Install dependencies
pip install pytest pytest-cov numpy Pillow flask faiss-cpu

# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=src --cov=vibecheck --cov-report=term-missing --cov-report=html
```

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_api_endpoints.py    # Flask API endpoint tests
├── test_data_collection.py  # Data structure and DB tests
├── test_embeddings.py       # Embedding and FAISS tests
└── test_recommender.py      # Recommendation logic tests
```

## Test Statistics

- **Total Tests**: 46
- **Passed**: 45
- **Skipped**: 1 (torch segfault issue)
- **Execution Time**: ~0.6 seconds

## Individual Test Files

### Run specific test file
```bash
pytest tests/test_api_endpoints.py -v
pytest tests/test_embeddings.py -v
pytest tests/test_recommender.py -v
pytest tests/test_data_collection.py -v
```

### Run specific test class
```bash
pytest tests/test_recommender.py::TestSearchFunctionality -v
pytest tests/test_embeddings.py::TestFAISSIndex -v
```

### Run specific test
```bash
pytest tests/test_embeddings.py::TestFAISSIndex::test_faiss_index_search -v
```

## Test Markers

Tests are organized with markers:
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow running tests

Run tests by marker:
```bash
pytest -m unit -v
pytest -m integration -v
```

## Coverage Reports

After running tests with coverage:
```bash
pytest tests/ --cov=src --cov=vibecheck --cov-report=html
```

View HTML coverage report:
```bash
open htmlcov/index.html
```

## Troubleshooting

### ModuleNotFoundError
If you see module import errors, ensure you're in the activated virtual environment:
```bash
source test_env/bin/activate
```

### Torch Segfault
One test is skipped due to torch causing segfaults on some systems. This is expected and doesn't affect other tests.

### FAISS Warnings
Deprecation warnings from FAISS are expected and don't affect test results.

## CI/CD Integration

Example GitHub Actions workflow:
```yaml
- name: Run tests
  run: |
    pip install pytest pytest-cov numpy Pillow flask faiss-cpu
    pytest tests/ -v --cov=src --cov=vibecheck --cov-report=xml
```

## Notes

- Tests use minimal dependencies for fast execution
- All tests are independent (no shared state)
- Mock data generated in fixtures
- No database or external services required
- Tests complete in under 1 second

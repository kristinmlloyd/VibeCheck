# Contributing to VibeCheck

Thank you for contributing to VibeCheck! This document outlines our development workflow and guidelines.

## Table of Contents
- [Git Workflow](#git-workflow)
- [Branching Strategy](#branching-strategy)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Code Style](#code-style)
- [Testing](#testing)

## Git Workflow

We follow a feature branch workflow with the following principles:

1. **Never commit directly to `main`**
2. **All changes go through Pull Requests**
3. **All PRs require at least one review**
4. **All tests must pass before merging**

## Branching Strategy

We use a simplified Git Flow:

### Main Branches
- `main`: Production-ready code. Protected branch.
- `develop`: Integration branch for features. Protected branch.

### Supporting Branches

#### Feature Branches
- **Naming:** `feature/<issue-number>-<short-description>`
- **Example:** `feature/15-microservices-architecture`
- **Branch from:** `develop`
- **Merge into:** `develop`
```bash
# Create feature branch
git checkout develop
git pull origin develop
git checkout -b feature/15-microservices-architecture

# Work on feature, commit changes
git add .
git commit -m "feat: add Docker configuration for API service"

# Push and create PR
git push origin feature/15-microservices-architecture
```

#### Bug Fix Branches
- **Naming:** `bugfix/<issue-number>-<short-description>`
- **Example:** `bugfix/42-fix-image-download`
- **Branch from:** `develop`
- **Merge into:** `develop`

#### Hotfix Branches (for production bugs)
- **Naming:** `hotfix/<issue-number>-<short-description>`
- **Example:** `hotfix/99-critical-api-error`
- **Branch from:** `main`
- **Merge into:** `main` AND `develop`

#### Documentation Branches
- **Naming:** `docs/<issue-number>-<short-description>`
- **Example:** `docs/10-setup-mkdocs`
- **Branch from:** `develop`
- **Merge into:** `develop`

### Branch Lifecycle
```
main
  │
  └── develop
        ├── feature/15-microservices-architecture
        ├── feature/16-experiment-tracking
        ├── bugfix/42-fix-image-download
        └── docs/10-setup-mkdocs
```

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks, dependency updates

### Examples
```bash
feat(api): add endpoint for restaurant similarity search

fix(image-collector): handle duplicate images across search terms

docs(readme): add architecture diagram and setup instructions

test(preprocessor): add unit tests for image deduplication

chore(deps): update dependencies to latest versions
```

## Pull Request Process

### 1. Create an Issue First
Before starting work, create an issue or claim an existing one.

### 2. Create Your Branch
```bash
git checkout develop
git pull origin develop
git checkout -b feature/<issue-number>-<description>
```

### 3. Make Your Changes
- Write clear, concise code
- Follow our code style guidelines
- Add tests for new functionality
- Update documentation as needed

### 4. Commit Your Changes
```bash
git add .
git commit -m "feat: your descriptive commit message"
```

### 5. Push and Create PR
```bash
git push origin feature/<issue-number>-<description>
```

Then create a Pull Request on GitHub:
- Fill out the PR template completely
- Link the related issue using "Closes #XX"
- Request reviews from team members
- Ensure CI checks pass

### 6. Code Review
- Address all review comments
- Make requested changes
- Push updates to the same branch

### 7. Merge
Once approved and all checks pass:
- Squash and merge (preferred for feature branches)
- Regular merge (for multi-commit features that tell a story)
- **Never** force push to shared branches

### 8. Clean Up
```bash
# After merge, delete your local branch
git checkout develop
git pull origin develop
git branch -d feature/<issue-number>-<description>
```

## Code Style

### Python
- Follow PEP 8
- Use `ruff` for linting and formatting
- Maximum line length: 88 characters (Black default)
- Use type hints where appropriate
```python
def process_image(image_path: str, size: tuple[int, int]) -> Image:
    """
    Process an image by resizing it.
    
    Args:
        image_path: Path to the image file
        size: Target size as (width, height)
        
    Returns:
        Processed PIL Image object
    """
    pass
```

### Docstrings
Use Google-style docstrings:
```python
def calculate_similarity(img1: np.ndarray, img2: np.ndarray) -> float:
    """
    Calculate similarity between two images.
    
    Args:
        img1: First image as numpy array
        img2: Second image as numpy array
        
    Returns:
        Similarity score between 0 and 1
        
    Raises:
        ValueError: If images have different dimensions
    """
    pass
```

### Pre-commit Hooks
We use pre-commit hooks to enforce style:
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Testing

### Writing Tests
- Place tests in `tests/` directory mirroring `src/` structure
- Use descriptive test names: `test_<functionality>_<scenario>_<expected_result>`
- Aim for >80% code coverage
```python
def test_image_collector_removes_duplicates_by_hash():
    """Test that duplicate images are detected and removed."""
    # Test implementation
    pass
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_image_collector.py

# Run tests matching pattern
pytest -k "test_duplicate"
```

## Issue Tracking

- **Always create an issue before starting work**
- Use appropriate labels (bug, enhancement, documentation, etc.)
- Assign the issue to yourself when you start working on it
- Reference issues in commits and PRs using `#issue-number`
- Close issues via PR descriptions: "Closes #15"

## Questions?

If you have questions about contributing:
1. Check existing documentation
2. Search closed issues
3. Open a discussion on GitHub Discussions
4. Ask in team chat

## Thank You!

Your contributions make VibeCheck better for everyone!
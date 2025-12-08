# Copilot Instruction for RABBIT project

## Context

Rabbit is a tool that aims to detect bots (automated accounts) in GitHub repositories by analyzing activity sequences. 
Its main workflow is:
1. Collect events from GitHub API. 
2. Transform events into activity sequences
3. Compute features from activity sequences
4. Classify accounts as bots or humans using a machine learning model.

## Development workflows
> Python >= 3.10 is supported.

### Testing
Tests are written using pytest. To run tests, use the command:
```shell
uv run pytest       # Run all tests
uv run pytest --cov # Run tests with coverage report
```

For new tests, please follow the existing structure and naming conventions (see `tests/`).  
Use fixtures for common setup tasks and mock external API calls to ensure tests are reliable and fast.

### Code style
  - Type hints required for all functions and methods (use `list`, `dict`, `tuple`).
  - Google-style docstrings for public functions (Args / Returns / Raises).
  - Run `uv run ruff check` / `uv run ruff format` before commits.

## Instructions

Your absolute priorities are **readability**, **security**, and **maintainability**.  
When submitting or reviewing code for the RABBIT project, ensure the following criteria are met:  
- PRs must pass tests and ruff checks.
- No hardcoded tokens; use environment variables.
- Prefer early returns instead of nested conditionals for better readability.
- Avoid deep nesting (more than 3 levels). Refactor into smaller functions if necessary.
- Make sure you remove dead code. Make sure you are not importing more than needed.
- Make sure to be consistent with private/public methods and attributes naming conventions.
- Make sure comments explain the "why" behind complex logic, not the "what".
- When writing comments, make sure each line is at most 80 characters. If a comments is 2 lines, make sure their width are close.
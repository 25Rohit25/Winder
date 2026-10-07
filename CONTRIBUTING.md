# Contributing to WindCtrl Validate

Thank you for your interest in contributing to **WindCtrl Validate**! This project follows rigorous controls engineering practices, reproducible automated testing, and clean software architecture.

## Development Setup

1. Clone repository:
   ```bash
   git clone https://github.com/25Rohit25/Winder.git
   cd Winder
   ```
2. Set up Python virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r backend/requirements.txt
   ```
3. Install frontend dependencies:
   ```bash
   cd frontend && npm install && cd ..
   ```

## Development Guidelines

- **Deterministic Validation**: All new validation rules must be mathematically deterministic and return structured `ValidationEvidence`.
- **Exact Threshold Tests**: Any rule introducing a numeric threshold must include boundary test cases (e.g., $T - \epsilon$, $T$, $T + \epsilon$).
- **No Mock or Fake Results**: All metrics displayed in reports or UI must be derived directly from actual telemetry.
- **Code Style**:
  - Python: Run `ruff check backend/ scripts/` and `ruff format backend/ scripts/`.
  - Frontend: Run `npm run build` inside `frontend/` to ensure strict TypeScript checks pass.
  - Test Suite: Run `pytest backend/tests/ -v` before opening a pull request.

### Contributing Guidelines

Thank you for considering contributing. This project contains a Python backend (FastAPI) and a React + Vite + TypeScript frontend. Follow these rules to keep quality high and velocity fast.

### Branching and Commits
- **branch naming**: `feat/<scope>`, `fix/<scope>`, `chore/<scope>`, `docs/<scope>`
- **commit message**: Conventional Commits: `type(scope): short summary`
- **sign-off**: include your name and email per repo policy where needed

### Code Style
- **EditorConfig**: enforced via `.editorconfig` across the repo
- **Formatting**:
  - Frontend: Prettier (`npm run format`) and ESLint (`npm run lint`)
  - Backend: Black, isort, Ruff; type-check with mypy
- **Line length**: 100

### Frontend (in `frontend/`)
- Install: `npm ci`
- Dev: `npm run dev`
- Test: `npm test`
- Lint: `npm run lint`
- Format: `npm run format`
- Typecheck: `npm run typecheck`

### Backend (in `backend/`)
- Create venv and install deps including dev tooling:
  ```sh
  python -m venv .venv
  .venv/Scripts/activate  # Windows
  pip install -r requirements.txt
  ```
- Run: `uvicorn app.main:app --reload` (or `python main.py` in project if present)
- Test: `pytest`
- Lint: `ruff check app tests`
- Format: `black . && isort .`
- Typecheck: `mypy app`

### Pre-commit (optional)
If you use pre-commit, configure hooks for black, ruff, isort, mypy, and prettier/eslint as desired.

### Pull Requests
- Ensure CI passes tests and linters
- Keep PRs focused and small
- Include documentation updates when behavior changes

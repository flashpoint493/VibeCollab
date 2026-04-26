# Iteration Strategy: Monorepo Split & Modular Validation

> **Created**: 2026-04-25
> **Status**: Stage 2/4 — Sub-package code ready, awaiting user validation
> **Decision**: DECISION-028

---

## 1. Current State Snapshot

### What Has Been Done
- [x] Extracted 8 sub-packages from `src/vibecollab/` (v0.12.6)
- [x] Rewrote all cross-package relative imports to absolute imports
- [x] Generated `pyproject.toml` for each sub-package with inter-dependencies
- [x] Local wheel build + import validation: **8/8 passed**
- [x] Pushed all sub-package code to respective GitHub `main` branches
- [x] Created `dev` branch on main repo with git submodules in `packages/`
- [x] Fixed `.gitmodules` format (LF line endings)
- [x] Updated YAML docs (context, changelog, decisions) and rendered Markdown views

### Repository Layout (Post-Split)

```
Vibecollab_master/
├── VibeCollab/              # Main repo (master/dev branches)
│   ├── src/vibecollab/      # Original monolithic code (v0.12.6)
│   ├── packages/            # Git submodules (dev branch only)
│   │   ├── vibecollab-core/
│   │   ├── vibecollab-insights/
│   │   ├── vibecollab-ide/
│   │   ├── vibecollab-mcp/
│   │   ├── vibecollab-patterns/
│   │   ├── vibecollab-generator/
│   │   ├── vibecollab-tasks/
│   │   └── vibecollab-cli/
│   └── scripts/
│       └── fix_split_packages.py   # Automation script for rebuild
├── vibecollab-core/         # Standalone repo (also in packages/)
├── vibecollab-insights/
├── vibecollab-ide/
├── vibecollab-mcp/
├── vibecollab-patterns/
├── vibecollab-generator/
├── vibecollab-tasks/
└── vibecollab-cli/
```

### Sub-Package Dependency Graph

```
vibecollab-core (base)
    ├── vibecollab-insights → depends on core
    ├── vibecollab-ide      → no external deps
    ├── vibecollab-mcp      → depends on core, insights, cli
    ├── vibecollab-patterns → re-exports from core
    ├── vibecollab-generator → re-exports from core
    ├── vibecollab-tasks    → depends on core, insights
    └── vibecollab-cli      → depends on core, insights, mcp, ide
```

---

## 2. Known Issues & Technical Debt

| ID | Issue | Severity | Package | Notes |
|---|---|---|---|---|
| TD-001 | Code duplication: `task_manager.py`, `event_log.py`, `role.py`, `roadmap_parser.py`, `prd_manager.py` exist in both `vibecollab-core` and `vibecollab-tasks` | Medium | core, tasks | Acceptable for backward compat during transition. Eventually deduplicate by making tasks a thin re-export wrapper. |
| TD-002 | `vibecollab-patterns` and `vibecollab-generator` re-export core APIs instead of owning logic files | Low | patterns, generator | PyPI 0.12.5 had these files duplicated. Current approach avoids duplication but changes API surface. |
| TD-003 | GitHub token in `.env` is expired | High | N/A | Both old and new tokens returned 401. User must regenerate token for CI/CD or automated push. |
| TD-004 | `vibecollab_core/__init__.py` no longer exports `agent.llm_client` (moved to `vibecollab_mcp`) | Low | core | Old monorepo `vibecollab/__init__.py` had these imports. New agent must check backward compat needs. |
| TD-005 | `i18n/locales/zh_CN/L_MESSAGES/vibecollab.po` is binary and may not render correctly in some editors | Low | core | Non-blocking. |

---

## 3. Iteration Phases

### Phase 1: User Local Validation (Current)
**Goal**: Confirm each sub-package works independently before publishing.

**Checklist**:
- [ ] Clone fresh repos or use existing `packages/` submodules
- [ ] Run `python -m build --wheel` in each sub-package
- [ ] Install wheels in clean venv: `pip install dist/*.whl`
- [ ] Verify imports:
  ```python
  from vibecollab_core.domain.task_manager import TaskManager
  from vibecollab_cli.cli.main import main
  from vibecollab_insights.insight.manager import InsightManager
  # ... etc for all 8 packages
  ```
- [ ] Run CLI smoke test: `vibecollab --help` (requires `vibecollab-cli`)
- [ ] Report any import errors or missing dependencies

**Entry Point**:
```bash
cd VibeCollab
python scripts/fix_split_packages.py   # Rebuilds all packages from main source
```

### Phase 2: PyPI Publish (User-Led)
**Goal**: Release v0.12.6 for all sub-packages.

**Prerequisites**: Phase 1 complete, no import/build errors.

**Steps**:
1. Regenerate PYPI_TOKEN in `.env` if needed
2. For each package:
   ```bash
   cd vibecollab-xxx
   python -m build
   twine upload dist/*
   ```
3. Verify on PyPI: `pip index versions vibecollab-xxx`

**Order**: core → insights/ide → mcp → patterns/generator/tasks → cli (respects dependency chain)

### Phase 3: Main Repo Modularization
**Goal**: Convert main `vibe-collab` package from monolith to meta-package.

**Branch**: `dev` (already exists with submodules)

**Steps**:
1. Update `pyproject.toml`:
   - Remove direct dependencies (`PyYAML`, `click`, `rich`, etc.)
   - Add sub-package dependencies:
     ```toml
     dependencies = [
         "vibecollab-core>=0.12.6",
         "vibecollab-cli>=0.12.6",
         "vibecollab-insights>=0.12.6",
         "vibecollab-ide>=0.12.6",
         "vibecollab-mcp>=0.12.6",
         "vibecollab-patterns>=0.12.6",
         "vibecollab-generator>=0.12.6",
         "vibecollab-tasks>=0.12.6",
     ]
     ```
2. Decision: Keep or remove `src/vibecollab/` code?
   - **Option A** (Recommended): Keep `src/vibecollab/__init__.py` as a compatibility shim that re-exports from sub-packages. Delete all other internal modules.
   - **Option B**: Complete removal. `vibe-collab` becomes a pure meta-package. Breaks `from vibecollab.core import ...` for existing users.
3. Update `src/vibecollab/__init__.py`:
   ```python
   from vibecollab_core import __version__
   from vibecollab_core.core.generator import LLMContextGenerator
   from vibecollab_core.core.project import Project
   # ... re-export all public APIs
   ```
4. Update tests to import from sub-packages or from the shim.
5. Run full test suite.

### Phase 4: Combination Validation
**Goal**: Ensure `pip install vibe-collab` installs all sub-packages and everything works.

**Steps**:
1. Create clean virtual environment
2. `pip install -e .` from main repo
3. Verify all imports work
4. Run `pytest` on main repo tests
5. Run `vibecollab check`
6. Run `vibecollab docs render --all`
7. If all pass → merge `dev` → `master`, tag v0.13.0

---

## 4. Agent Onboarding Context

### For Next Agent Session

**On start, read in order**:
1. `CONTRIBUTING_AI.md` — collaboration rules
2. `docs/CONTEXT.md` — current global state
3. `docs/ITERATION_STRATEGY.md` — this document
4. `docs/DECISIONS.md` — confirmed decisions (especially DECISION-028)
5. Run `git log --oneline -10` in `VibeCollab/`

**Key commands**:
```bash
# Rebuild all sub-packages from main source
python scripts/fix_split_packages.py

# Render docs
python -m vibecollab.cli.main docs render --all

# Check status
vibecollab check
```

**Critical files**:
- `scripts/fix_split_packages.py` — split automation & import fixer
- `.vibecollab/docs/*.yaml` — source-of-truth docs
- `packages/*` — git submodules (dev branch only)

**Current branch**: `dev` on main repo (submodules configured)
**Do not touch**: `master` branch (stable release)

---

## 5. Rollback Plan

If validation fails catastrophically:
1. Stay on `master` branch — it is untouched and fully functional
2. Delete `dev` branch locally and remotely if needed
3. Sub-packages on PyPI 0.12.5 remain as-is
4. Re-create `dev` branch from `master` and retry

---

*Last updated: 2026-04-25*

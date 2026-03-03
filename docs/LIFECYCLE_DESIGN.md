# Project Lifecycle Management System Design

## 1. Git Check and Initialization

### Functional Requirements
- Check if Git is installed during project initialization or upgrade
- Check if project directory is already a Git repository
- Prompt or auto-initialize if not initialized
- Emphasize Git sync importance in generated documents

### Implementation
- Create `src/vibecollab/git_utils.py` module
- Provide functions:
  - `check_git_installed()`: Check if git is installed
  - `is_git_repo(path)`: Check if path is a git repository
  - `init_git_repo(path)`: Initialize git repository
  - `ensure_git_repo(path, auto_init=False)`: Ensure git repository exists

## 2. Project Lifecycle Management System

### Lifecycle Stage Definitions

```yaml
lifecycle:
  current_stage: "demo"  # demo / production / commercial / stable
  stages:
    demo:
      name: "Prototype Validation"
      description: "Rapidly validate core concepts and feasibility"
      focus: ["Rapid iteration", "Concept validation", "Core features"]
      principles:
        - "Fail fast, adjust fast"
        - "Prioritize core features, defer optimization"
        - "Technical debt acceptable, but must be documented"
        - "Detailed Git development iteration records"
        - "Record important decisions in DECISIONS.md"
        - "Establish CI/CD"
      milestones: []  # Milestone list
      
    production:
      name: "Production"
      description: "Product development, preparing for scale"
      focus: ["Stability", "Performance optimization", "Maintainability"]
      principles:
        - "Code quality first"
        - "Establish release and publicity preparation, define and improve target platform support"
        - "Full code review before launch, establish more stable and robust code structure"
        - "Improve QA product test coverage"
        - "Define performance standards"
        - "Unit testing, spec compliance checks"
      milestones: []
      
    commercial:
      name: "Commercialization"
      description: "Market-facing, pursuing growth"
      focus: ["User experience", "Market adaptation", "Extensibility"]
      principles:
        - "User feedback driven"
        - "Data-driven decisions"
        - "Rapid market response"
      milestones: []
      
    stable:
      name: "Stable Operations"
      description: "Mature product, stable maintenance"
      focus: ["Stability", "Maintenance cost", "Long-term planning"]
      principles:
        - "Changes require caution"
        - "Backward compatibility first"
        - "Complete documentation"
      milestones: []
```

### Design Options Comparison

#### Option A: Single CONTRIBUTING_AI.md + Stage Field
**Pros**:
- Simple, single document
- Easy to maintain
- Convenient for AI to read

**Cons**:
- Document may become too long
- Different stage rules mixed together
- Need to regenerate entire document on upgrade

#### Option B: Multiple CONTRIBUTING_AI Files (Per Stage)
**Pros**:
- Clear responsibilities, each stage independent
- Can preserve historical versions
- Only need to switch files on upgrade

**Cons**:
- Complex file management
- Need to maintain multiple files
- AI needs to know current stage to read correct file

#### Option C: Single File + Stage-Based Sections (Recommended)
**Pros**:
- Balances simplicity and clarity
- Single document with clear structure
- Can view all stage rules simultaneously
- Only need to update current stage marker on upgrade

**Cons**:
- Document may be long (but can be optimized with collapsing/indexing)

### Recommended: Option C + Config-Driven

```yaml
# project.yaml
lifecycle:
  current_stage: "demo"
  stage_history:
    - stage: "demo"
      started_at: "2026-01-20"
      milestones_completed: []
  
  # Stage-specific configuration
  stage_configs:
    demo:
      # Can override global config
      roles_override: []
      decision_levels_override: {}
      workflow_override: {}
```

In `CONTRIBUTING_AI.md`:
```markdown
# AI Collaboration Rules

## Current Project Lifecycle Stage
**Stage**: Prototype Validation (demo)
**Start Date**: 2026-01-20
**Stage Focus**: Rapid iteration, concept validation, core features

## Stage-Based Collaboration Rules

### Common Rules
(Rules applicable to all stages)

### Prototype Validation Stage Rules
(demo stage specific rules and principles)

### Production Stage Rules
(production stage rules, currently inactive)

### Commercialization Stage Rules
(commercial stage rules, currently inactive)

### Stable Operations Stage Rules
(stable stage rules, currently inactive)
```

### Lifecycle Upgrade Process

1. **Trigger timing**: Auto-check after milestone completion, or manual trigger
2. **Check conditions**: 
   - Whether all milestones for current stage are completed
   - Whether prerequisites for next stage are met
3. **Upgrade flow**:
   - Generate upgrade suggestions
   - Update `project.yaml` `lifecycle.current_stage`
   - Regenerate `CONTRIBUTING_AI.md` (update current stage marker)
   - Record upgrade history
   - Prompt areas needing attention

### Implementation Modules

1. `src/vibecollab/lifecycle.py`: Lifecycle management core logic
2. `src/vibecollab/git_utils.py`: Git utility functions
3. Update `generator.py`: Support stage-based rule generation
4. Update `cli.py`: Add lifecycle check commands

## 3. Integration Points

- `Project.generate_all()`: Check Git, initialize lifecycle config
- `Project.regenerate()`: Check lifecycle status, update documents
- New command: `vibecollab lifecycle check`: Check current lifecycle status
- New command: `vibecollab lifecycle upgrade`: Upgrade to next stage

# Roadmap Markdown template - renders docs/roadmap.yaml to docs/ROADMAP.md
# Project Roadmap

## Current Project Lifecycle Stage


**Stage**: demo
**Started**: 2026-01-20
**Description**: Rapidly validate core concepts and feasibility

### Stage Focus


- Rapid iteration

- Concept validation

- Core features



### Stage Principles


- Fail fast, adjust fast

- Prioritize core features, defer optimization

- Technical debt acceptable, but must be documented

- Detailed Git development iteration records

- Record important decisions in DECISIONS

- Establish CI/CD




---

## Milestones



### v0.5.9 - Pattern Engine + Template Overlay

**Status**: completed
**Date**: 2026-02-24



- [x] PatternEngine: Jinja2 templates + manifest.yaml declarative engine

- [x] 27 .md.j2 templates replace hardcoded _add_*() methods

- [x] Template Overlay: .vibecollab/patterns/ local override mechanism

- [x] Legacy removal: generator.py 1713→83 lines

- [x] DECISION-011: Pattern Engine architecture

- [x] 40 PatternEngine tests, full 215 tests zero regression




### v0.7.0 - Insight Solidification System

**Status**: completed




- [x] Insight Schema design (body + Registry + Developer Tag three parts)

- [x] InsightManager core module (CRUD / Registry / search / provenance / consistency check)

- [x] InsightManager unit tests (62 tests)

- [x] developer.py unit test completion (67 tests)

- [x] Developer metadata extension (tags / contributed / bookmarks + 21 tests)

- [x] CLI command encapsulation (insight list/show/add/search/use/decay/check/delete + 21 tests)

- [x] Cross-developer sharing + provenance CLI visualization (24 tests)

- [x] Consistency check integrated into vibecollab check --insights

- [x] Document consistency check enhancement (linked_groups)

- [x] Agent guidance commands vibecollab onboard + vibecollab next

- [x] Technical debt cleanup (version number unification v0.7.0-dev)

- [x] protocol_checker multi-developer dynamic discovery




### v0.7.1 - Task-Insight Auto-Link

**Status**: completed




- [x] TaskManager.create_task() auto-searches related Insights

- [x] _extract_search_tags(): Extract keywords from feature/description/role

- [x] _find_related_insights(): Jaccard × weight matching + metadata storage

- [x] suggest_insights(): Insight recommendations for existing tasks

- [x] CLI vibecollab task create/list/show/suggest

- [x] EventLog records linked Insights

- [x] Backward compatible (auto-skips when no InsightManager)

- [x] 28 unit tests




### v0.9.0 - Semantic Search Engine

**Status**: completed




- [x] Embedder module — Lightweight embedding abstraction layer

- [x] VectorStore module — Local persistent vector storage

- [x] vibecollab index command — Index project documents

- [x] vibecollab insight search --semantic enhancement

- [x] vibecollab search new command — Global semantic search

- [x] onboard enhancement — Semantically match current task related Insights




### v0.9.1 - MCP Server + AI IDE Integration

**Status**: completed




- [x] vibecollab mcp serve — Standard MCP Server implementation

- [x] MCP CLI command group

- [x] PyPI v0.9.1 release

- [x] CodeBuddy MCP integration

- [x] 35 unit tests, 1074 full passed

- [x] Unified skill injection — vibecollab skill inject <ide>




### v0.9.2 - Insight Solidification Signal Enhancement

**Status**: completed




- [x] vibecollab insight suggest — Structured signal-based recommendation

- [x] Signal snapshot — .vibecollab/insight_signal.json

- [x] Conversation summary storage — .vibecollab/sessions/

- [x] MCP Server enhancement (insight_suggest, session_save)

- [x] 60 unit tests, full 1134 passed




### v0.9.3 - Task/EventLog Core Workflow Integration

**Status**: completed




- [x] vibecollab task transition / solidify / rollback

- [x] onboard injects active Task overview + recent EventLog summary

- [x] next recommends actions based on Task status

- [x] MCP task_create + task_transition tools

- [x] 30 unit tests, full 1164 passed




### v0.9.4 - Insight Quality & Lifecycle

**Status**: completed




- [x] Insight auto-deduplication

- [x] Insight relationship graph

- [x] Cross-project Insight portability (export/import)

- [x] MCP insight_graph / insight_export tools

- [x] 36 unit tests, full 1201 passed




### v0.9.5 - ROADMAP ↔ Task Integration

**Status**: completed




- [x] RoadmapParser module

- [x] Bidirectional sync (ROADMAP ↔ Task DONE)

- [x] Task milestone field

- [x] CLI vibecollab roadmap status/sync/parse

- [x] CLI vibecollab task create --milestone / task list --milestone

- [x] MCP roadmap_status / roadmap_sync tools

- [x] README bilingual restructure

- [x] 40 unit tests, 1331 passed, 89% coverage




### v0.10.14 - Release Engineering + Git Hooks + Dynamic Check

**Status**: completed
**Date**: 2026-03-30



- [x] Git Hooks Framework (FP-001)

- [x] Commit-Type-Based Dynamic Check (INS-043)

- [x] Strict Document-Code Sync (INS-042)

- [x] Local Build Check (INS-046)

- [x] 42 insights indexed (351 vectors)

- [x] All 1515 tests passing

- [x] CI/CD pipeline stable




### v0.11.0 - Role-Driven Architecture + Git Hooks + Guards

**Status**: completed





### v0.12.0 - YAML Data Layer + Workflows + Insight Automation

**Status**: completed
**Date**: 2026-04-02




### v0.13.0 - Insight-First Ecosystem

**Status**: planned




- [ ] Insight marketplace: vibecollab insight install <pack>

- [ ] Cross-project Insight federation

- [ ] Insight-driven code generation

- [ ] Insight quality scoring




### v1.0.0 - Official Release

**Status**: planned




- [ ] All v0.11.x ~ v0.13.x features completed

- [ ] Test coverage ≥ 85%

- [ ] Clean up all .dev0 markers

- [ ] PyPI v1.0.0 release

- [ ] GitHub Release v1.0.0

- [ ] Full documentation refresh






---

## Iteration Suggestion Pool


(None)


---

## Stage History



- **demo**: 2026-01-20



---

*Last updated: 2026-04-25*
## [0.10.0] - 2026-03-01

### Added
- **OpenClaw Support**: Added `.openclaw/` directory with OpenClaw-specific skill files
- **Developer Registry**: Introduced `docs/DEVELOPERS.md` for tracking AI agent contributors
- **Agent Registration**: Support for registering OpenClaw, Claude, Cursor, and Cline agents
- **IDE Alignment**: OpenClaw support follows the same pattern as existing IDE supports
- **Automated Setup**: Added support for `vibecollab setup --ide openclaw` command
- **CLI Integration**: Complete documentation for using `vibecollab onboard` with OpenClaw

### Documentation
- Added `.openclaw/SKILL.md` with quick reference for OpenClaw agents
- Added `.openclaw/skills/vibecollab/SKILL.md` with complete protocol support
- Added `.openclaw/skills/vibecollab/README.md` with setup and usage guide
- Added `docs/DEVELOPERS.md` with developer onboarding and registration guide
- Added automated workflow documentation for post-onboard commits
- Added OpenClaw-specific tool availability notes
- Added YAML frontmatter compliance for OpenClaw Skills specification

### Protocol
- Extended VibeCollab protocol to support OpenClaw agents
- Updated developer onboarding flow to include agent registration
- Integrated with `vibecollab setup` command for automated IDE configuration
- Added support for `vibecollab onboard` workflow in OpenClaw agents

### Technical
- Maintained consistency with existing IDE support structure
- YAML frontmatter format compliant with OpenClaw Skills specification
- No breaking changes - fully additive feature
- Supports all VibeCollab MCP tools for OpenClaw agents


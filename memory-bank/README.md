# Memory Bank Structure

This memory bank follows the standardized structure for Cline's memory persistence between sessions.

## Core Files (Required)

1. **projectbrief.md** - Foundation document defining core requirements and goals
2. **productContext.md** - Why this project exists and how it should work  
3. **activeContext.md** - Current work focus and recent changes
4. **systemPatterns.md** - System architecture and design patterns
5. **techContext.md** - Technologies and development setup
6. **progress.md** - What works and what's left to build

## File Relationships

```
projectbrief.md (Foundation)
    ├── productContext.md (User Experience)
    ├── systemPatterns.md (Architecture)
    └── techContext.md (Implementation)
         └── activeContext.md (Current State)
              └── progress.md (Status Tracking)
```

## Archive Directory

The `archive/` directory contains the original memory bank files from before the standardization:
- project_overview.md
- technical_specs.md
- project_status.md
- implementation_roadmap.md
- conversation_summary.md
- cline_transfer_instructions.md

These files have been consolidated into the new structure while preserving all critical information.

## Usage

When starting a new session, Cline should:
1. Read ALL core files to understand the project
2. Start with projectbrief.md for foundation
3. Use activeContext.md for current work state
4. Update relevant files as work progresses
5. Focus updates on activeContext.md and progress.md

## Maintenance

- Update activeContext.md after significant changes
- Update progress.md when completing features
- Other files should be more stable, updated less frequently
- When user says "update memory bank", review ALL files

Last Updated: January 11, 2025

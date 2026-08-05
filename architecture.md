# obsidian-second-brain Architecture

## System Overview

```mermaid
graph TB
    subgraph CLI["AI CLI Platforms"]
        ClaudeCode["Claude Code"]
        CodexCLI["Codex CLI"]
        GeminiCLI["Gemini CLI"]
        OpenCode["OpenCode"]
    end
    
    subgraph Skill["obsidian-second-brain Skill"]
        subgraph Commands["44 Slash Commands"]
            VaultMgmt["Vault Management<br/>12 commands"]
            Thinking["Thinking Tools<br/>8 commands"]
            Research["Research Toolkit<br/>14 commands"]
            Agents["Scheduled Agents<br/>10 commands"]
        end
        
        subgraph Adapters["Platform Adapters"]
            ClaudeAdapter["Claude Code Adapter<br/>Identity Copy"]
            CodexAdapter["Codex CLI Adapter<br/>AGENTS.md"]
            GeminiAdapter["Gemini CLI Adapter<br/>GEMINI.md"]
            OpenCodeAdapter["OpenCode Adapter<br/>OPENCODE.md"]
        end
        
        subgraph Core["Core Engine"]
            Dispatcher["Command Dispatcher"]
            Validator["AI-First Validator"]
            Compiler["Vault Compiler"]
            Synthesizer["Auto-Synthesizer"]
        end
    end
    
    subgraph Vault["Obsidian Vault"]
        subgraph Layers["Vault Layers"]
            Raw["raw/<br/>Sources & Inputs"]
            Wiki["wiki/<br/>Compiled Articles"]
            Schema["schema/<br/>Templates & Rules"]
            Meta["meta/<br/>Indexes & State"]
        end
        
        subgraph AgentsLayer["Scheduled Agents"]
            Nightly["Nightly Agent<br/>Auto-synthesis"]
            Weekly["Weekly Agent<br/>Review & Cleanup"]
            Challenge["Challenge Agent<br/>Contradiction Detection"]
            Emerge["Emerge Agent<br/>New Concept Discovery"]
        end
    end
    
    subgraph External["External Services"]
        Perplexity["Perplexity API"]
        Grok["Grok API"]
        Gemini["Gemini File Search"]
        YouTube["YouTube API"]
        X["X / Twitter API"]
    end
    
    CLI --> Adapters
    Adapters --> Dispatcher
    Dispatcher --> Commands
    Commands --> Core
    Core --> Vault
    Commands --> External
    
    AgentsLayer --> Core
    
    style Skill fill:#1a1a2e,stroke:#4a4a6a,color:#fff
    style Commands fill:#16213e,stroke:#4a4a6a,color:#fff
    style Core fill:#0f3460,stroke:#4a4a6a,color:#fff
    style Vault fill:#533483,stroke:#4a4a6a,color:#fff
    style AgentsLayer fill:#2d1b69,stroke:#4a4a6a,color:#fff
```

## Core Components

### 1. Command Layer (44 Commands)

| Layer | Count | Purpose |
|-------|-------|---------|
| Vault Management | 12 | Save, ingest, organize, maintain vault |
| Thinking Tools | 8 | Challenge assumptions, find contradictions, explore ideas |
| Research Toolkit | 14 | X/Twitter, web research, YouTube, NotebookLM, deep research |
| Scheduled Agents | 10 | Nightly synthesis, weekly review, challenge, emerge |

### 2. Platform Adapters
- **Claude Code**: Identity copy (native slash command format)
- **Codex CLI**: Compiles to `AGENTS.md` + `.codex/commands/`
- **Gemini CLI**: Compiles to `GEMINI.md` + `.gemini/commands/`
- **OpenCode**: Compiles to `OPENCODE.md` + `.opencode/commands/`

### 3. Core Engine
- **Command Dispatcher**: Routes commands to appropriate handlers
- **AI-First Validator**: Ensures vault writes follow AI-first rules
- **Vault Compiler**: Transforms raw sources into compiled wiki articles
- **Auto-Synthesizer**: Nightly agent that updates and connects notes

### 4. Vault Layers
- **raw/**: Unprocessed sources (URLs, PDFs, transcripts)
- **wiki/**: Compiled, reviewed articles with citations
- **schema/**: Templates, frontmatter rules, validation schemas
- **meta/**: Indexes, access logs, vitality scores

## Data Flow

```mermaid
flowchart LR
    subgraph Input
        User["User Input"]
        Source["External Source"]
    end
    
    subgraph Processing
        Ingest["Ingest<br/>Save to raw/"]
        Compile["Compile<br/>raw/ → wiki/"]
        Synthesize["Synthesize<br/>Update & Connect"]
        Validate["Validate<br/>AI-First Rules"]
    end
    
    subgraph Output
        Wiki["wiki/<br/>Compiled Articles"]
        Index["meta/_index.md"]
        Report["Synthesis Report"]
    end
    
    User --> Ingest
    Source --> Ingest
    Ingest --> Compile
    Compile --> Validate
    Validate --> Wiki
    Wiki --> Index
    Synthesize --> Report
    Wiki --> Synthesize
```

## AI-First Vault Principle

Every note written to the vault follows the AI-First specification:

```markdown
---
title: "Concept Name"
type: concept
date: 2026-08-01
tags: [domain, topic]
ai-first: true
sources: ["[[raw/articles/source.md]]"]
coverage: medium
confidence: high
---

## For future Claude

Context for AI retrieval: this note covers X, relates to Y, and was compiled from Z.

# Concept Name

Core explanation with [[wikilinks]] to related concepts.

## Details

Extracted information with source attribution.

## Relationships

- Builds on [[Foundation Concept]]
- Contradicts [[Other Claim]] on X

## Sources

- [[raw/articles/source.md]] -- key claims from this source
```

## Scheduled Agents

```mermaid
graph LR
    subgraph Schedule["Agent Schedule"]
        Nightly["Nightly (03:00)<br/>Auto-synthesis"]
        Weekly["Weekly (Sunday)<br/>Review & Cleanup"]
        Challenge["On-demand<br/>Contradiction Detection"]
        Emerge["On-demand<br/>New Concept Discovery"]
    end
    
    subgraph Actions["Agent Actions"]
        Update["Update existing notes"]
        Connect["Create new connections"]
        Resolve["Resolve contradictions"]
        Discover["Discover new concepts"]
    end
    
    Nightly --> Update
    Nightly --> Connect
    Weekly --> Resolve
    Challenge --> Resolve
    Emerge --> Discover
```

## Key Design Decisions

1. **Vault Rewrites Itself**: Every source updates existing pages instead of just appending
2. **AI-First Notes**: Notes designed for AI retrieval, not human reading
3. **Multi-Platform**: One codebase, four CLI platforms
4. **Scheduled Agents**: Autonomous agents that maintain vault health
5. **Dry-Run Default**: All write operations are dry-run unless explicitly applied
6. **File-Based State**: All state in files, no database, no cloud dependency

## Technology Stack

- **Primary**: Markdown, YAML frontmatter
- **Scripting**: Python 3.11+, Bash
- **Platforms**: Claude Code, Codex CLI, Gemini CLI, OpenCode
- **External APIs**: Perplexity, Grok, Gemini File Search, YouTube, X/Twitter
- **Build**: esbuild, shell scripts

## File Structure

```
obsidian-second-brain/
├── commands/               # 44 slash command definitions
│   ├── obsidian-save.md
│   ├── obsidian-ingest.md
│   ├── obsidian-architect.md
│   └── ...
├── adapters/               # Platform translation layer
│   ├── claude-code/
│   ├── codex-cli/
│   ├── gemini-cli/
│   └── opencode/
├── scripts/                # Python helpers
│   ├── research/
│   ├── bootstrap_vault.py
│   └── vault_health.py
├── references/             # Shared specs
│   └── ai-first-rules.md   # Canonical vault-write spec
├── hooks/                  # Claude Code hooks
├── dist/                   # Build output (gitignored)
├── SKILL.md                # Full operating manual
└── README.md               # Public documentation
```
